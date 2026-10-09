"""CPU Slurm only. Frozen compatibility and new synthetic discovery judgments."""
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import statistics
import time
from ..adapters import NormalizedFixtureAdapter
from ..domain import Scope, Locator, canonical, ClaimDraft, Origin
from ..ingestion import MemoryLedger, AnnotatedFixtureExtractor
from ..chunking.chunker import CandidateChunks
from ..chunking.policy import POLICY_B
from ..embeddings.benchmark import corpus, CLOCK
from ..embeddings.cache import ChunkEmbedder
from ..embeddings.local import LocalTransformerProvider
from ..vectorstore.models import record_from_dict, EmbeddingSpace, ChunkReference
from ..vectorstore.config import StoreConfig
from ..vectorstore.sqlite_reference import SQLiteVectorStore
from . import *
from .evaluator import metrics, aggregate
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'results/stage3e'

class FrozenQueries:
    def __init__(self,config,queries,vectors): self.config=config; self.lookup=dict(zip(queries,vectors))
    def embed_queries(self,texts): return [self.lookup[t] for t in texts]

class SyntheticAdapter:
    def __init__(self,adapter,origin): self.adapter,self.origin=adapter,origin
    def read(self): return replace(self.adapter.read(),origin=Origin(self.origin))

def extended_corpus(data,provider):
    ledger=MemoryLedger(clock=CLOCK).for_candidate(Scope('synthetic-eval','candidate'))
    service=CandidateChunks(ledger); chunks=[]; owners={}; latest={}
    for i,d in enumerate(data['documents']):
        key=d.get('source_key',d['id']); st=d.get('source_type','resume')
        adapter=NormalizedFixtureAdapter(st,key,'https://example.invalid/'+key,d['title'],d['text'],
            Locator('document.v1',canonical({'document_id':key,'section':d['section']})))
        result=ledger.ingest(SyntheticAdapter(adapter,d.get('origin','candidate_supplied')),
                    AnnotatedFixtureExtractor((ClaimDraft(d['text'],0,len(d['text']),d['text']),)))
        cs=service.generate(result.evidence.evidence_id,POLICY_B); chunks.extend(cs)
        owners.update({c.chunk_id:d['id'] for c in cs}); latest[result.evidence.source_id]=result.evidence.evidence_id
    records=ChunkEmbedder(service.scope,provider,clock=CLOCK).embed(chunks,'title-section-v1')
    return service,chunks,owners,records,latest

def populate(folder,service,chunks,records):
    store=SQLiteVectorStore(StoreConfig(folder),service.scope)
    store.register_chunks([ChunkReference.from_citation(service.cite(c.chunk_id,c.revision_id)) for c in chunks]); store.upsert_embeddings(records)
    for r in sorted(records,key=lambda x:x.evidence_version):
        state=store.get_embedding(r.record_id).state
        if state=='active': continue
        current=next((x.evidence_id for x in records if x.source_id==r.source_id and store.get_embedding(x.record_id).state=='active'),None)
        store.activate_source_version(r.source_id,r.evidence_id,expected_current=current)
    return store

def experiment(label,store,service,records,owners,queries,provider,cfg):
    retriever=CandidateEvidenceRetriever(store,provider,EmbeddingSpace(records[0].config,records[0].input_strategy),service,[r.record_id for r in records],cfg)
    rows=[]; latencies=[]
    for q in queries:
        need=InformationNeed(NeedType(q.get('kind','job_requirement')),q['query'],q['id'])
        start=time.perf_counter(); response=retriever.retrieve(*service.scope.key,need,top_k=100); latencies.append(time.perf_counter()-start)
        ids=[owners[x.reference.chunk_id] for x in response.results]
        texts=[' '.join(service.cite(x.reference.chunk_id,x.reference.chunk_revision_id).chunk.text.split()) for x in response.results]
        sources=[x.reference.source_id for x in response.results]
        scoremap={}
        for id,x in zip(ids,response.results): scoremap[id]=max(scoremap.get(id,float('-inf')),x.score)
        m=metrics(ids,q['relevant'],q['hard_negatives'],texts,sources,scores=scoremap)
        for k in (1,3,5):
            credited={owners[ref.chunk_id] for x in response.results[:k] for ref in (x.reference,)+x.corroborating_references}
            m['grouped_recall_at_'+str(k)]=len(credited & set(q['relevant']))/len(set(q['relevant']))
        rows.append({'id':q['id'],'need':q['query'],'category':q['category'],'expected':q['relevant'],
            'hard_negatives':q['hard_negatives'],'metrics':m,'ranking':ids,'response':asdict(response)})
    output={'label':label,'config':asdict(cfg),'metrics':aggregate([r['metrics'] for r in rows]),'queries':rows,
            'retrieval_seconds':{'median':statistics.median(latencies),'max':max(latencies)},
            'note':'MRR and hard-negative wins are bounded by branch budgets; absent positives do not win.'}
    (OUT/(label+'.json')).write_text(json.dumps(output,indent=2)+'\n'); return output

def main(folder):
    if not os.environ.get('SLURM_JOB_ID'): raise RuntimeError('Slurm compute allocation required')
    data=json.loads((ROOT/'fixtures/rag/embedding_eval/resume_semantics_v1.json').read_text())
    artifact=ROOT/'results/stage3c/model0-short-moderate-title-section-v1-records.json'
    frozen=json.loads(artifact.read_text()); records=[record_from_dict(r) for r in frozen['records']]
    service,chunks,owners,_=corpus(data,POLICY_B)
    provider=FrozenQueries(records[0].config,[q['query'] for q in frozen['queries']],frozen['query_vectors'])
    store=populate(folder/'frozen',service,chunks,records); summary=[]
    for strategy in ('semantic','lexical','hybrid'):
        report=experiment('compatible-'+strategy,store,service,records,owners,data['queries'],provider,RetrievalConfig(strategy=strategy,deduplicate=False,semantic_budget=100,lexical_budget=100))
        summary.append({k:report[k] for k in ('label','metrics','config','retrieval_seconds')})
        if strategy=='semantic':
            old=json.loads((ROOT/'results/stage3c/model0-evaluation.json').read_text())
            exp=next(x for x in old['experiments'] if x['artifact']==artifact.name)
            for actual,expected in zip(report['queries'],exp['queries']):
                normalized=sorted(zip(actual['ranking'],[x['semantic_score'] for x in actual['response']['results']]),key=lambda x:(-x[1],x[0]))
                assert normalized==[(x['id'],x['score']) for x in expected['ranking']]
            (OUT/'stage3c_compatibility.json').write_text(json.dumps({'scores_and_evidence_tie_order_equal':True,'queries':22,'stage3c_metrics':exp['metrics'],'stage3e_embedding_id_tie_order_metrics':report['metrics']},indent=2)+'\n')
    store.close()
    spec=json.loads((ROOT/'results/stage3c/models.lock.json').read_text())[0]
    start=time.perf_counter(); provider=LocalTransformerProvider(spec,str(ROOT/'models/stage3c')); load=time.perf_counter()-start
    query_audit={}; original_queries=provider.embed_queries
    def audited_queries(texts):
        values=original_queries(texts)
        for t,v in zip(texts,values):
            if t in query_audit: assert query_audit[t]==v
            query_audit[t]=v
        return values
    provider.embed_queries=audited_queries
    extended=json.loads((ROOT/'fixtures/rag/retrieval_eval/stage3e_v1.json').read_text())
    start=time.perf_counter(); service,chunks,owners,records,latest=extended_corpus(extended,provider); embedding=time.perf_counter()-start
    start=time.perf_counter(); store=populate(folder/'extended',service,chunks,records); preparation=time.perf_counter()-start
    configs=[(s,RetrievalConfig(strategy=s,deduplicate=False)) for s in ('semantic','lexical','hybrid')]
    configs += [('semantic-dedup',RetrievalConfig(strategy='semantic',deduplicate=True)),('semantic-diverse',RetrievalConfig(strategy='semantic',deduplicate=True,per_source_cap=1))]
    configs += [('hybrid-expanded',RetrievalConfig(strategy='hybrid',deduplicate=False,expansion=True)),('hybrid-dedup',RetrievalConfig(strategy='hybrid',deduplicate=True)),
                ('hybrid-diverse',RetrievalConfig(strategy='hybrid',deduplicate=True,per_source_cap=1))]
    configs += [('hybrid-budget-'+str(k),RetrievalConfig(strategy='hybrid',deduplicate=False,semantic_budget=k,lexical_budget=k)) for k in (5,10,40)]
    for label,cfg in configs:
        report=experiment('extended-'+label,store,service,records,owners,extended['queries'],provider,cfg)
        assert all(x['reference']['evidence_id']==latest[x['reference']['source_id']] for q in report['queries'] for x in q['response']['results'])
        summary.append({k:report[k] for k in ('label','metrics','config','retrieval_seconds')})
    from ..vectorstore.models import SearchFilter
    history=CandidateEvidenceRetriever(store,provider,EmbeddingSpace(records[0].config,records[0].input_strategy),service,[r.record_id for r in records],RetrievalConfig(strategy='lexical'))
    historical=history.retrieve(*service.scope.key,InformationNeed(NeedType.EXPERIENCE,'Kubernetes','audit'),SearchFilter(state='superseded'))
    assert historical.results and all(owners[x.reference.chunk_id]=='stale_v1' for x in historical.results)
    (OUT/'lifecycle-and-provenance.json').write_text(json.dumps({'historical_response':asdict(historical),'active_version_checks_passed':True,'resolved_records':len(records),'origin_counts':{origin:sum(r.origin==origin for r in records) for origin in sorted(set(r.origin for r in records))},'all_untrusted':all(r.trust=='untrusted_data' for r in records)},indent=2)+'\n')
    for r in records: ChunkEmbedder(service.scope,None).resolve(store.get_embedding(r.record_id).record,service)
    (OUT/'extended-embeddings.json').write_text(json.dumps({'records':[asdict(r) for r in records],'owners':owners},indent=2)+'\n')
    store.close()
    (OUT/'query-vectors.json').write_text(json.dumps(query_audit,indent=2)+'\n')
    (OUT/'comparison.json').write_text(json.dumps({'experiments':summary,'frozen_rankings_and_scores_equal':True,
        'frozen_queries':len(data['queries']),'extended_queries':len(extended['queries']),'extended_chunks':len(chunks),
        'citation_roundtrips':len(records),'model_load_seconds':load,'embedding_and_chunking_seconds':embedding,
        'vector_preparation_seconds':preparation,'slurm_job_id':os.environ['SLURM_JOB_ID'],
        'config':asdict(provider.config),'dataset_sha256':hashlib.sha256((ROOT/'fixtures/rag/retrieval_eval/stage3e_v1.json').read_bytes()).hexdigest()},indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
