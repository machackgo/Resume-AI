"""CPU-only Stage 3I preparation; frozen Stage 3H corpora and controls read only."""
import os,json,time,hashlib,statistics
from pathlib import Path
from dataclasses import asdict
from ..scale.prepare import ROOT,sha
from ..reasoning.prepare import corpus,contextual_gold,dump
from ..scale.dataset import at_scale
from ..domain import Scope
from ..ingestion import MemoryLedger
from ..embeddings.benchmark import CLOCK
from ..embeddings.local import LocalTransformerProvider
from ..retrieval.benchmark import populate
from ..retrieval import CandidateEvidenceRetriever,RetrievalConfig,InformationNeed,NeedType
from ..vectorstore.models import EmbeddingSpace,record_from_dict
from ..reranking.base import CitationTextResolver
from .retrieve import ComponentConfig,ComponentRetriever
from .benchmark import benchmark,evaluate
OUT=ROOT/'results/stage3i';H=ROOT/'results/stage3h'
CONFIGS=[ComponentConfig(1,5,.2),ComponentConfig(2,5,.2),ComponentConfig(2,6,.2),ComponentConfig(3,5,.2),ComponentConfig(5,5,.2)]
def key(cfg):return 'k%d-b%d'%(cfg.per_component,cfg.global_budget)
def coverage(q,ctx,ids,documents):
    docs={ids[e] for e in ctx['provenance']};present={d['id'] for d in documents if not d.get('stale')}
    required=[(a,set(a['relations'])&present) for a in q['gold'] if set(a['relations'])&present]
    survival=[bool(rels&docs) for a,rels in required]
    refs=[e for g in ctx['groups'] for e in g['evidence']];related={d for a in q['gold'] for d in a['relations']};byid={d['id']:d for d in documents}
    dangerous=lambda d:d not in related and (byid[d].get('distractor') in ('adjacent','assertion','training_inference','built_used') or d.startswith('c') and d in {'c06','c11','c13','c14','c15','c16','c17','c18','c22','c23','c24'})
    return dict(required_components=len(required),survived_components=sum(survival),component_survival=sum(survival)/len(survival) if survival else None,all_required_components_covered=all(survival) if survival else None,per_component={a['component_id']:bool(rels&docs) for a,rels in required},overall_relevant_evidence_survival=len(set(q['relevant'])&docs)/len(q['relevant']) if q['relevant'] else None,evidence_groups=len(ctx['groups']),evidence_records=len(refs),dangerous_neighbor_rate=sum(dangerous(ids[e['evidence_id']]) for e in refs)/len(refs) if refs else 0,duplicate_crowding=1-len({e['content'] for e in refs})/len(refs) if refs else 0)
def summarize(rows):
    names=('component_survival','all_required_components_covered','overall_relevant_evidence_survival','evidence_groups','evidence_records','dangerous_neighbor_rate','duplicate_crowding')
    return {k:statistics.mean(r[k] for r in rows if r[k] is not None) if any(r[k] is not None for r in rows) else None for k in names}
def main(folder):
    assert os.environ.get('SLURM_JOB_ID')
    OUT.mkdir(exist_ok=True)
    data=json.loads((H/'dataset.json').read_text());bd=benchmark();dump(OUT/'decomposition-dataset.json',bd);be=evaluate(bd);dump(OUT/'decomposition-results.json',be)
    assert be['metrics']['smoke_pass'],be['metrics']
    provider=LocalTransformerProvider(json.loads((ROOT/'results/stage3c/models.lock.json').read_text())[0],str(ROOT/'models/stage3c'))
    queries={};orig=provider.embed_queries;oldqueries=json.loads((H/'query-vectors.json').read_text())
    def audit(texts):
        vs=tuple(tuple(oldqueries[t]) if t in oldqueries else orig([t])[0] for t in texts)
        for t,v in zip(texts,vs):
            if t in queries:assert queries[t]==v
            queries[t]=v
        return vs
    provider.embed_queries=audit
    summary={};allrows={}
    for scale in ('SMALL','MEDIUM','LARGE','XL'):
        t=time.perf_counter();scope=Scope('synthetic-stage3h','candidate-A');ledger=MemoryLedger(clock=CLOCK);docs=at_scale(data,scale)
        svc,chunks,owners,records,attest=corpus({'id':'corpus-A','documents':docs},scope,provider,ledger)
        historical=json.loads((H/(scale+'-corpus.json')).read_text())
        actual=json.loads(json.dumps([asdict(r) for r in records]))
        assert all({k:v for k,v in a.items() if k!='vector'}=={k:v for k,v in b.items() if k!='vector'} for a,b in zip(actual,historical['records']))
        delta=max(abs(v-w) for a,b in zip(actual,historical['records']) for v,w in zip(a['vector'],b['vector']))
        assert delta<1e-5,'unexpected embedding drift'
        records=[record_from_dict(r) for r in historical['records']]
        dump(OUT/(scale+'-vector-reuse.json'),{'reused_frozen_corpus_vectors':len(records),'rebuild_max_absolute_delta':delta,'nonvector_fields_exact':True})
        store=populate(folder/scale,svc,chunks,records);retriever=CandidateEvidenceRetriever(store,provider,EmbeddingSpace(provider.config,'title-section-v1'),svc,[r.record_id for r in records],RetrievalConfig());resolver=CitationTextResolver(store,svc)
        # Populate adversarial B in same root; perfect missing-component evidence.
        fs=Scope(scope.tenant_id,'candidate-B');bsvc,bc,bo,br,ba=corpus({'id':'B','documents':data['foreign_documents']},fs,provider,ledger);bs=populate(folder/scale,bsvc,bc,br)
        assert all(store.get_embedding(r.record_id) is None for r in br)
        old=json.loads((H/(scale+'-prepared.json')).read_text());ids={c.evidence.evidence_id:owners[c.chunk_id] for c in chunks};rows=[];armmetrics={}
        for oldrow in old:
            q=oldrow['case'];need=InformationNeed(NeedType.JOB_REQUIREMENT,q['requirement'],q['id']);variants={};measurements={}
            for cfg in CONFIGS:
                cr=ComponentRetriever(retriever,resolver,cfg);out=cr.retrieve(*scope.key,need,attest);ctx=out['context'];variants[key(cfg)]=out
                for bad in ((scope.tenant_id,'candidate-B'),('foreign-tenant',scope.candidate_id)):
                    try:cr.retrieve(*bad,need)
                    except ValueError:pass
                    else:raise AssertionError('scope override')
                assert not set(ctx['provenance'])&(set(oldrow['security']['foreign_ids'])|set(oldrow['security']['stale_ids']))
                m=coverage(q,ctx,ids,docs);measurements[key(cfg)]=m
                armmetrics.setdefault(key(cfg),[]).append(m)
            for arm in ('rag3','rag5'):armmetrics.setdefault(arm,[]).append(coverage(q,oldrow['contexts'][arm],ids,docs))
            rows.append(dict(case=q,scope=asdict(scope),scale=scale,id_to_doc=ids,security=oldrow['security'],gold={'full':oldrow['gold']['full']},variants=variants,measurements=measurements,control_gold=oldrow['gold']))
        summary[scale]={a:summarize(ms) for a,ms in armmetrics.items()};allrows[scale]=rows
        dump(OUT/(scale+'-retrieval.json'),rows);store.close();bs.close();print(scale,round(time.perf_counter()-t,2),json.dumps(summary[scale]),flush=True)
    dump(OUT/'retrieval-summary.json',summary);dump(OUT/'query-vectors.json',queries)
    # Predeclared retrieval-only lexicographic selection: coverage first, then
    # record count; prefer smaller budgets. No Qwen output used for selection.
    def objective(cfg):
        ms=[summary[s][key(cfg)] for s in ('LARGE','XL')]
        return (-sum(m['all_required_components_covered'] for m in ms),-sum(m['component_survival'] for m in ms),sum(m['evidence_records'] for m in ms),cfg.global_budget,cfg.per_component)
    chosen=min(CONFIGS,key=objective)
    for scale,rows in allrows.items():
        final=[]
        for r in rows:
            out=r['variants'][key(chosen)];ctx=out['context'];r={k:v for k,v in r.items() if k not in ('variants','measurements')}
            r.update(contexts={'component':ctx},component=out);r['gold']['component']=contextual_gold(r['case'],ctx,r['id_to_doc']);final.append(r)
        dump(OUT/(scale+'-prepared.json'),final)
    dump(OUT/'config.json',dict(version='stage3i-v1',selected=asdict(chosen),selection_rule='LARGE/XL all-covered, component survival, evidence records, global budget, component budget; retrieval only',stage3h_dataset_sha256=sha(H/'dataset.json'),decomposer='structural-extractive-v1',component_id='sha256(version,requirement_id,original,order,text)[:16]',component_query='Stage 3E focused-v1; no expansion',merge='round-robin-distinct-text-v1',dedup='whitespace-normalized exact text; union authenticated source references',reranker='Stage 3F identity-v1',context='stage3g-v2 plus retrieval membership; support schema/system unchanged',compatibility='Qwen scoring components remain frozen Stage 3H supplied components; generated retrieval components recorded separately. h06 narrow base-weight interpretation is legacy-only and sensitivity excludes h06.',known_decomposition_limits=be['metrics'],slurm_cpu_job=os.environ['SLURM_JOB_ID']))
    files=list((ROOT/'rag/component').glob('*.py'))+list(OUT.glob('*-prepared.json'))+[OUT/'config.json',OUT/'decomposition-dataset.json',OUT/'query-vectors.json',H/'dataset.json']
    dump(OUT/'retrieval-freeze.json',{'before_any_stage3i_qwen':True,'files':{str(p.relative_to(ROOT)):sha(p) for p in files}})
    print('FROZEN',key(chosen),flush=True)
if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
