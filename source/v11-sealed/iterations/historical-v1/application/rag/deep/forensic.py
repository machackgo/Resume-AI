"""Read-only historical reconstruction, before any Stage 3J retrieval changes."""
import json, os, hashlib
from pathlib import Path
from dataclasses import asdict
from rag.component.prepare import ROOT,H,corpus,Scope,MemoryLedger,CLOCK,populate,CandidateEvidenceRetriever,EmbeddingSpace,RetrievalConfig,CitationTextResolver,InformationNeed,NeedType,LocalTransformerProvider,record_from_dict,at_scale,dump
from rag.vectorstore.models import VectorQuery,SearchFilter
from rag.component.retrieve import ComponentRetriever
OUT=ROOT/'results/stage3j'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def main(folder):
    assert os.getenv('SLURM_JOB_ID')
    protected={}
    for name in ('results/stage3h/preexisting_manifest.json','results/stage3i/protected-manifest.json','results/stage3i/final-manifest.json'):
        manifest=json.loads((ROOT/name).read_text());bad=[p for p,h in manifest.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
        assert not bad,(name,bad);protected.update(manifest)
    for base in ('rag','docs','tests','eval','fixtures','results'):
        for p in (ROOT/base).rglob('*'):
            rel=str(p.relative_to(ROOT))
            if p.is_file() and '__pycache__' not in rel and not rel.startswith(('rag/deep/','results/stage3j/','tests/rag/test_deep','docs/stage3j')):protected[rel]=sha(p)
    
    if (OUT/'protected-manifest.json').exists():
        saved=json.loads((OUT/'protected-manifest.json').read_text());assert all(sha(ROOT/p)==h for p,h in saved.items());protected=saved
    else:dump(OUT/'protected-manifest.json',protected)
    dump(OUT/'initial-preservation.json',{'verified':True,'files':len(protected),'slurm_job':os.environ['SLURM_JOB_ID']})
    data=json.loads((H/'dataset.json').read_text());queries=json.loads((ROOT/'results/stage3i/query-vectors.json').read_text())
    provider=LocalTransformerProvider(json.loads((ROOT/'results/stage3c/models.lock.json').read_text())[0],str(ROOT/'models/stage3c'))
    provider.embed_queries=lambda texts:tuple(tuple(queries[t]) for t in texts)
    traces=[]
    for scale in ('SMALL','MEDIUM','LARGE','XL'):
        scope=Scope('synthetic-stage3h','candidate-A');ledger=MemoryLedger(clock=CLOCK)
        docs=at_scale(data,scale);svc,chunks,owners,rebuilt,attest=corpus({'id':'corpus-A','documents':docs},scope,provider,ledger)
        hist=json.loads((H/(scale+'-corpus.json')).read_text());records=[record_from_dict(r) for r in hist['records']]
        for a,b in zip(rebuilt,records):
            assert {k:v for k,v in asdict(a).items() if k!='vector'}=={k:v for k,v in asdict(b).items() if k!='vector'}
            assert max(abs(x-y) for x,y in zip(a.vector,b.vector))<1e-5
        store=populate(folder/scale,svc,chunks,records);space=EmbeddingSpace(provider.config,'title-section-v1');r=CandidateEvidenceRetriever(store,provider,space,svc,[x.record_id for x in records],RetrievalConfig());resolver=CitationTextResolver(store,svc)
        old=next(x for x in json.loads((ROOT/'results/stage3i'/f'{scale}-prepared.json').read_text()) if x['case']['id']=='h06');need=InformationNeed(NeedType.JOB_REQUIREMENT,old['case']['requirement'],'h06');out=ComponentRetriever(r,resolver).retrieve(*scope.key,need,attest)
        assert json.loads(json.dumps(out['context']))==old['contexts']['component']
        gold=[x for x in records if owners[x.chunk_id]=='c04'];active=r._eligible(SearchFilter());components=[]
        for c in out['decomposition']['components']:
            cid=c['component_id'];response=out['traces'][cid];query=response['query']['text'];hits=store.search_vectors(VectorQuery(space,tuple(queries[query]),len(records)))
            ranking=[{'rank':i,'score':hit.score,'document_id':owners[hit.chunk_id],'embedding_id':hit.embedding_id,'evidence_id':hit.evidence_id,'text':active[hit.embedding_id][1].chunk.text} for i,hit in enumerate(hits,1)]
            for g in gold:
                rank=next(x['rank'] for x in ranking if x['embedding_id']==g.record_id)
                raw_in=rank<=20;per_in=any(g.evidence_id in [x['reference']['evidence_id']]+[y['evidence_id'] for y in x['corroborating_references']] for x in response['results']);final=g.evidence_id in out['context']['provenance']
                unique=[]
                for x in ranking[:20]:
                    key=' '.join(x['text'].split())
                    if key not in unique:unique.append(key)
                key=' '.join(active[g.record_id][1].chunk.text.split());group_rank=unique.index(key)+1 if key in unique else None
                components.append({'component':c,'query_plan':response['query'],'query_embedding_config':asdict(provider.config),'gold_rank':rank,'gold_score':ranking[rank-1]['score'],'neighbors':ranking[max(0,rank-4):rank+3],'top10':ranking[:10],'initial_semantic_pool':raw_in,'deduplicated_pool_group_rank':group_rank,'survived_duplicate_grouping':raw_in,'survived_per_component_cutoff':per_in,'survived_component_merge':per_in,'survived_coverage_selection':final and per_in,'survived_global_budget':final and per_in,'reached_qwen':final,'first_loss':'NONE' if final else 'TOP_K_CUTOFF','cutoff_location':None if final else 'per_component_top2_after_grouping' if raw_in else 'initial_semantic_top20','ranking':ranking})
        chains=[]
        for g in gold:
            citation=svc.cite(g.chunk_id,g.chunk_revision_id);ref=r._reference(g.record_id,active[g.record_id]);assert 'implemented' in citation.chunk.text.lower() or 'built' in citation.chunk.text.lower()
            chains.append({'document_id':'c04','embedding':asdict(g),'space_id':space.space_id,'stored_vector':asdict(store.get_embedding(g.record_id)),'retrieval_reference':asdict(ref),'citation':asdict(citation),'canonical_evidence':asdict(citation.chunk.evidence),'source':asdict(citation.source),'original_fixture':next(d for d in docs if d['id']=='c04')})
        trace={'version':'h06-forensic-v1','scale':scale,'requirement':old['case'],'decomposition':out['decomposition'],'gold_chains':chains,'components':components,'frozen_stage3i_replay_exact':True,'final_context':out['context'],'historical_traces':out['traces']};traces.append(trace)
        print(scale,[(c['component']['text'],c['gold_rank'],c['cutoff_location']) for c in components],flush=True);store.close()
    dump(OUT/'h06-forensic-traces.json',traces)
    dump(OUT/'forensic-complete.json',{'trace_sha256':sha(OUT/'h06-forensic-traces.json'),'before_parameter_changes':True,'slurm_job':os.environ['SLURM_JOB_ID'],'diagnosis':'MEDIUM per-component cutoff; LARGE/XL initial semantic cutoff; action preserved. Investigate acronym representation before depth changes.'})
if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
