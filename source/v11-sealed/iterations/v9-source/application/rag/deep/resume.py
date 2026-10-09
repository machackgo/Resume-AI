"""Retrieval-only ablations, hard cases and frozen selection before Qwen."""
import os,json,time,statistics,sys,subprocess,re
from pathlib import Path
from dataclasses import asdict,replace
from rag.component.prepare import ROOT,H,corpus,Scope,MemoryLedger,CLOCK,populate,EmbeddingSpace,RetrievalConfig,CitationTextResolver,InformationNeed,NeedType,LocalTransformerProvider,record_from_dict,at_scale,dump,coverage
from rag.component.retrieve import ComponentRetriever
from rag.component.decompose import RequirementDecomposer
from rag.reasoning.prepare import contextual_gold
from rag.vectorstore.models import VectorQuery
from rag.deep.forensic import OUT,sha
from .retrieve import DeepConfig,DeepRetriever,QueryRetriever,normalize_query,key,messages,QUERY_VERSION,SELECTOR_VERSION
from .fixtures import fixtures,supplemental,VERSION
CONFIGS=[DeepConfig(internal_k=k,normalize=n) for n in (False,True) for k in (3,5,10,20,40)]
def provider_new():
    p=LocalTransformerProvider(json.loads((ROOT/'results/stage3c/models.lock.json').read_text())[0],str(ROOT/'models/stage3c'))
    cache=json.loads((ROOT/'results/stage3i/query-vectors.json').read_text());original=p.embed_queries
    def queries(texts):
        for t in texts:
            if t not in cache:cache[t]=original([t])[0]
        return tuple(tuple(cache[t]) for t in texts)
    p.embed_queries=queries
    return p,cache

def measure(q,out,ids,docs,tok,rankings):
    ctx=out['context'];q=dict(q,relevant=q.get('relevant',[d for a in q['gold'] for d in a['relations']]))
    m=coverage(q,ctx,ids,docs)
    refs=[r for g in ctx['groups'] for r in g['evidence']]
    if 'dangerous' in q:m['dangerous_neighbor_rate']=sum(ids[r['evidence_id']] in q['dangerous'] for r in refs)/len(refs) if refs else 0
    m['dangerous_neighbor_count']=round(m['dangerous_neighbor_rate']*len(refs));m['duplicate_result_rate']=m['duplicate_crowding']
    m.update(retrieval_seconds=out['retrieval_seconds'],selector_seconds=out.get('selector_seconds',out['merge_seconds']),candidate_pool_size=out.get('raw_pool_size',sum(len(t['results']) for t in out['traces'].values())),distinct_candidate_pool_size=out.get('distinct_pool_size'),final_evidence_count=len(ctx['groups']))
    msg=messages(InformationNeed(NeedType.JOB_REQUIREMENT,q['requirement'],q['id']),q['components'],ctx)
    rendered=tok.apply_chat_template(msg,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    m['prompt_tokens']=len(tok(rendered,add_special_tokens=False)['input_ids']);m['evidence_tokens']=len(tok(json.dumps(ctx['groups'],ensure_ascii=True),add_special_tokens=False)['input_ids'])
    ranks=[];component_metrics=[]
    dec=out['decomposition']['components'];present={d['id'] for d in docs if not d.get('stale') and d['id']!='stale'}
    for i,a in enumerate(q['gold']):
        gold=set(a['relations'])&present
        if not gold:continue
        comps=[dec[i]] if len(dec)==len(q['gold']) else dec
        combined=[rankings[c['component_id']] for c in comps]
        best=min((r['rank'] for ranking in combined for r in ranking if r['document_id'] in gold),default=None)
        ranks.append(best);detail={'gold_component':a['component_id'],'gold_documents':sorted(gold),'best_gold_raw_rank':best}
        for k in (1,3,5,10):detail['recall_at_'+str(k)]=len({r['document_id'] for ranking in combined for r in ranking[:k]}&gold)/len(gold)
        detail['proof_hit_in_pool']=any(r['document_id'] in gold for ranking in combined for r in ranking[:out['config'].get('internal_k',20)])
        component_metrics.append(detail)
    m['component_metrics']=component_metrics;m['gold_ranks']=ranks
    for k in (1,3,5,10):m['recall_at_'+str(k)]=statistics.mean(x['recall_at_'+str(k)] for x in component_metrics) if component_metrics else None
    m['mrr']=statistics.mean(1/r if r else 0 for r in ranks) if ranks else None
    m['per_component_pool_recall']=statistics.mean(x['proof_hit_in_pool'] for x in component_metrics) if component_metrics else None
    return m

def rankings_for(need,retriever,owners,records,cache):
    out={}
    for c in RequirementDecomposer().decompose(need).components:
        text=normalize_query(c.text) if retriever.normalize else c.text
        if text not in cache:
            v=retriever.provider.embed_queries([text])[0]
            hits=retriever.store.search_vectors(VectorQuery(retriever.space,tuple(v),len(records))) if records else ()
            cache[text]=[dict(rank=i,score=h.score,embedding_id=h.embedding_id,evidence_id=h.evidence_id,document_id=owners[h.chunk_id]) for i,h in enumerate(hits,1)]
        out[c.component_id]=cache[text]
    return out

def aggregate(rows):
    numeric=('recall_at_1','recall_at_3','recall_at_5','recall_at_10','mrr','per_component_pool_recall','dangerous_neighbor_rate','dangerous_neighbor_count','duplicate_result_rate','final_evidence_count','prompt_tokens','candidate_pool_size','retrieval_seconds','selector_seconds')
    result={k:statistics.mean(r[k] for r in rows if r.get(k) is not None) if any(r.get(k) is not None for r in rows) else None for k in numeric}
    required=sum(r['required_components'] for r in rows);survived=sum(r['survived_components'] for r in rows);bearing=[r for r in rows if r['required_components']]
    result.update(required_components=required,survived_components=survived,required_component_survival=survived/required if required else None,all_required_components_covered=sum(r['all_required_components_covered'] for r in bearing)/len(bearing) if bearing else None,evidence_bearing_requirements=len(bearing))
    return result

def main(folder):
    assert os.getenv('SLURM_JOB_ID')
    gate=json.loads((OUT/'forensic-complete.json').read_text());assert sha(OUT/'h06-forensic-traces.json')==gate['trace_sha256']
    assert not (OUT/'retrieval-freeze.json').exists(),'never overwrite a frozen experiment'
    data=json.loads((H/'dataset.json').read_text());p,queries=provider_new()
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'models/Qwen3.8-27B',local_files_only=True)
    frozen=fixtures();sup=supplemental();assert json.loads((OUT/"targeted-dataset.json").read_text())=={"version":VERSION,"cases":frozen};assert json.loads((OUT/"supplement-dataset.json").read_text())==sup
    allrows={};summary={};hardrows=[];supprows=[];security=[]
    workloads=[(s,at_scale(data,s),None) for s in ('SMALL','MEDIUM','LARGE','XL')]+[('hard-'+q['id'],q['documents'],q) for q in frozen]+[('supp-'+q['id'],q['documents'],q) for q in sup]
    checkpoints=OUT/"diagnostic-checkpoints";checkpoints.mkdir(exist_ok=True)
    recovered={}
    for label,docs,fixture in workloads:
        if fixture is None and (OUT/f"{label}-ablation.json").exists():
            path=OUT/f"{label}-ablation.json";rows=json.loads(path.read_text());assert len(rows)==16
            allrows[label]=rows;summary[label]={k:aggregate([r["measurements"][k] for r in rows]) for k in rows[0]["measurements"]}
            for r in rows:
                for out in r["variants"].values():
                    assert not (set(r["security"]["foreign_ids"] )|set(r["security"]["stale_ids"]))&set(out["context"]["provenance"])
            recovered[str(path.relative_to(ROOT))]=sha(path)
            security.append(dict(corpus=label,tested_k=[3,5,10,20,40],cross_candidate_leakage=0,cross_tenant_leakage=0,stale_leakage=0,deterministic=True,foreign_perfect_evidence=True,recovered_from_job="2334052",note="Saved contexts audited; full independent replay follows."))
            print("RECOVERED",label,"without rerunning",flush=True);continue
        if (checkpoints/(label+".json")).exists():
            saved=json.loads((checkpoints/(label+".json")).read_text());security.append(saved["security"])
            if label.startswith("hard-"):hardrows+=saved["rows"]
            else:supprows+=saved["rows"]
            print("RECOVERED",label,"checkpoint",flush=True);continue
        scale=label if fixture is None else 'DIAGNOSTIC';scope=Scope('synthetic-stage3h' if fixture is None else 'synthetic-stage3j','candidate-A' if fixture is None else label);ledger=MemoryLedger(clock=CLOCK)
        svc,chunks,owners,records,attest=corpus({'id':'corpus-A' if fixture is None else label,'documents':docs},scope,p,ledger)
        if fixture is None:
            hist=json.loads((H/f'{scale}-corpus.json').read_text())['records']
            assert len(records)==len(hist)
            assert all({k:v for k,v in json.loads(json.dumps(asdict(a))).items() if k!='vector'}=={k:v for k,v in b.items() if k!='vector'} for a,b in zip(records,hist))
            assert max(abs(x-y) for a,b in zip(records,hist) for x,y in zip(a.vector,b['vector']))<1e-5
            records=[record_from_dict(r) for r in hist]
        store=populate(folder/label,svc,chunks,records);resolver=CitationTextResolver(store,svc);space=EmbeddingSpace(p.config,'title-section-v1');ids={c.evidence.evidence_id:owners[c.chunk_id] for c in chunks};cache={}
        oldrows=json.loads((ROOT/'results/stage3i'/f'{scale}-prepared.json').read_text()) if fixture is None else [dict(case=fixture,scale=scale,scope=asdict(scope),gold={})]
        # Perfect evidence exists only in a different candidate/tenant; physically
        # coexists in the store root. No scope is ever sourced from query text.
        foreign_ids=[];foreignstores=[]
        for fs in (Scope(scope.tenant_id,'candidate-B'),Scope('other-tenant',scope.candidate_id)):
            fdoc=dict(id='perfect',title='Activity record',section='Experience',text='Implemented retrieval augmented generation for the Juniper assistant. CANARY_B_7391.')
            fsvc,fc,fo,fr,fa=corpus({'id':'foreign','documents':[fdoc]},fs,p,ledger);fstore=populate(folder/label,fsvc,fc,fr);foreignstores.append(fstore);foreign_ids.extend(r.evidence_id for r in fr)
            assert all(store.get_embedding(r.record_id) is None for r in fr)
        stale=[r.evidence_id for r in records if store.get_embedding(r.record_id).state!='active'];rows=[];buckets={}
        retrievers={key(cfg):QueryRetriever(store,p,space,svc,[r.record_id for r in records],RetrievalConfig(semantic_budget=cfg.internal_k),normalize=cfg.normalize) for cfg in CONFIGS}
        baseline=QueryRetriever(store,p,space,svc,[r.record_id for r in records],RetrievalConfig(),normalize=False)
        for old in oldrows:
            q=old['case'];need=InformationNeed(NeedType.JOB_REQUIREMENT,q['requirement'],q['id']);variants={};measurements={}
            for cfg in CONFIGS:
                retriever=retrievers[key(cfg)];engine=DeepRetriever(retriever,resolver,cfg);out=engine.retrieve(*scope.key,need,attest)
                rank=rankings_for(need,retriever,owners,records,cache);m=measure(q,out,ids,docs,tok,rank)
                m['h06_gold_rank']=next((r['rank'] for r in next(iter(rank.values())) if r['document_id']=='c04'),None) if q['id']=='h06' else None
                m['h06_gold_survived']=any(ids[e]=='c04' for e in out['context']['provenance']) if q['id']=='h06' else None
                assert not (set(foreign_ids)|set(stale))&set(out['context']['provenance'])
                for bad in ((scope.tenant_id,'candidate-B'),('other-tenant',scope.candidate_id)):
                    try:engine.retrieve(*bad,need)
                    except ValueError:pass
                    else:raise AssertionError('scope bypass')
                variants[key(cfg)]=out;measurements[key(cfg)]=m;buckets.setdefault(key(cfg),[]).append(m)
            baseout=ComponentRetriever(baseline,resolver).retrieve(*scope.key,need,attest);baserank=rankings_for(need,baseline,owners,records,cache)
            if fixture is None:assert json.loads(json.dumps(baseout['context']))==old['contexts']['component']
            bm=measure(q,baseout,ids,docs,tok,baserank);measurements['stage3i']=bm;buckets.setdefault('stage3i',[]).append(bm)
            if fixture is None:full=old['gold']['full']
            else:
                # Full gold from fixture relations, excluding stale versions.
                vals=[];atoms={}
                from rag.reasoning.contract import aggregate_labels
                for a in q['gold']:
                    labels=set(a['relations'].values());v='SUPPORTED' if 'SUPPORTED' in labels else 'UNSUPPORTED' if 'UNSUPPORTED' in labels else 'UNKNOWN';atoms[a['component_id']]=v;vals.append(v)
                full=dict(label=aggregate_labels(vals),atoms=atoms)
            rows.append(dict(case=q,scale=scale,scope=asdict(scope),id_to_doc=ids,security={'foreign_ids':foreign_ids,'stale_ids':stale,'foreign_rejected':True},gold={'full':full},variants=variants,measurements=measurements,baseline=baseout))
        for cfg in CONFIGS:
            # Actual repeated engine execution, including ranking and selector.
            first=rows[0];need=InformationNeed(NeedType.JOB_REQUIREMENT,first['case']['requirement'],first['case']['id']);repeat=DeepRetriever(retrievers[key(cfg)],resolver,cfg).retrieve(*scope.key,need,attest)
            for field in ('context','traces','mapping','selector_trace'):assert repeat[field]==first['variants'][key(cfg)][field]
        security.append(dict(corpus=label,tested_k=[3,5,10,20,40],cross_candidate_leakage=0,cross_tenant_leakage=0,stale_leakage=0,deterministic=True,foreign_perfect_evidence=True))
        if fixture is None:
            allrows[scale]=rows;summary[scale]={k:aggregate(v) for k,v in buckets.items()};dump(OUT/f'{scale}-ablation.json',rows)
        elif label.startswith('hard-'):hardrows+=rows
        else:supprows+=rows
        if fixture is not None:dump(checkpoints/(label+".json"),{"rows":rows,"security":security[-1]})
        store.close()
        for s in foreignstores:s.close()
        print('RETRIEVAL',label,'complete',flush=True)
    dump(OUT/"recovery-integrity.json",{"recovered_scale_artifacts":recovered,"unchanged":all(sha(ROOT/p)==h for p,h in recovered.items()),"repeated_only_unsaved_diagnostics":True})
    for rows in allrows.values():
        for r in rows:
            for out in r["variants"].values():
                for trace in out["traces"].values():p.embed_queries([trace["query"]["text"]])
    hardmetrics={k:aggregate([r['measurements'][k] for r in hardrows]) for k in ['stage3i']+[key(c) for c in CONFIGS]}
    dump(OUT/'top-k-summary.json',summary);dump(OUT/'targeted-results.json',hardrows);dump(OUT/'targeted-metrics.json',hardmetrics);dump(OUT/'supplement-results.json',supprows);dump(OUT/'security-results.json',security);dump(OUT/'query-vectors.json',queries)
    # Freeze only after retrieval metrics and legacy regression constraints.
    eligible=[]
    for c in CONFIGS:
        k=key(c);h=hardmetrics[k];hb=hardmetrics['stage3i']
        regressions=[r['case']['id'] for r in hardrows+supprows if r['measurements'][k]['survived_components']<r['measurements']['stage3i']['survived_components']]
        if not regressions and h['required_component_survival']>=hb['required_component_survival']:eligible.append(c)
    assert eligible,'No nonregressing configuration'
    def objective(c):
        ms=[summary[s][key(c)] for s in ('LARGE','XL')];h=hardmetrics[key(c)]
        return (-sum(m['required_component_survival'] for m in ms),-sum(m['all_required_components_covered'] for m in ms),-h['required_component_survival'],h['dangerous_neighbor_rate'],sum(m['dangerous_neighbor_rate'] for m in ms),sum(m['prompt_tokens'] for m in ms),c.internal_k)
    selected=min(eligible,key=objective);dump(OUT/'selection-decision.json',{'rule':'coverage, hard-case coverage, hard-case danger, scale danger, context tokens, smaller K; hard/supplement coverage regressions excluded','objectives':{key(c):objective(c) for c in eligible},'selected':key(selected),'no_qwen_outputs_used':True})
    for scale,rows in allrows.items():
        final=[]
        for r in rows:
            out=r['variants'][key(selected)];v={k:v for k,v in r.items() if k not in ('variants','measurements','baseline')};v.update(contexts={'component':out['context']},component=out,metrics=r['measurements'][key(selected)]);v['gold']['component']=contextual_gold(v['case'],out['context'],v['id_to_doc']);final.append(v)
        dump(OUT/f'{scale}-prepared.json',final)
    dump(OUT/'diagnostic-prepared.json',[dict(case=r['case'],scale=r['scale'],scope=r['scope'],id_to_doc=r['id_to_doc'],security=r['security'],gold=dict(r['gold'],component=contextual_gold(r['case'],r['variants'][key(selected)]['context'],r['id_to_doc'])),contexts={'component':r['variants'][key(selected)]['context']},component=r['variants'][key(selected)]) for r in hardrows+supprows])
    config=dict(version='stage3j-v1',selected=asdict(selected),query_construction=QUERY_VERSION if selected.normalize else 'focused-v1',decomposition='structural-extractive-v1',embedding_config=asdict(p.config),embedding_input='title-section-v1',semantic_space_id=space.space_id,selector=SELECTOR_VERSION,reranker='identity-v1',context='stage3g-v2 plus unchanged Stage3I component metadata',chunk='Stage3B POLICY_B unchanged',dataset=VERSION,slurm_cpu_job=os.environ['SLURM_JOB_ID'],output_cap=1536,alias_policy='Exact uppercase standalone RAG only; action and relational qualifiers preserved',not_entailment='Semantic selection is relevance only, trust never promoted',internal_k80_not_tested='Unnormalized XL rank125 cannot be recovered at80; normalized rank1 makes80 uninformative')
    dump(OUT/'config.json',config)
    print('SELECTED',key(selected),json.dumps(summary['XL'][key(selected)]),flush=True)
    # Tests run after artifacts exist but before the freeze/GPU gate.
    checks={}
    for name,args in {'stage3-tests':['-m','unittest','discover','-s','tests/rag','-v'],'stage1-stage2-tests':['-m','unittest','discover','-s','eval/tests','-v']}.items():
        run=subprocess.run([sys.executable,'-B',*args],capture_output=True,text=True);(OUT/(name+'.log')).write_text(run.stdout+run.stderr);checks[name]=run.returncode==0
    dump(OUT/'cpu-test-status.json',checks);assert all(checks.values()),checks
    files=list((ROOT/'rag/deep').glob('*.py'))+[ROOT/'rag/deep/experiment_design.json',OUT/'config.json',OUT/'targeted-dataset.json',OUT/'supplement-dataset.json',OUT/'query-vectors.json',OUT/'h06-forensic-traces.json']+list(OUT.glob('*-prepared.json'))
    dump(OUT/'retrieval-freeze.json',{'before_any_stage3j_qwen':True,'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'selected':key(selected),'slurm_job':os.environ['SLURM_JOB_ID']})
    print('FROZEN',key(selected),flush=True)
if __name__=='__main__':main(Path(sys.argv[1]))
