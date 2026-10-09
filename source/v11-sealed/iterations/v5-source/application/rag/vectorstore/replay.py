"""Offline Stage 3C replay only. Evidence aggregation is copied evaluation logic,
not a production retrieval pipeline. Writer and reader are separate processes.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import os
import time
from ..embeddings.benchmark import corpus
from ..embeddings.cache import ChunkEmbedder
from ..embeddings.evaluation import metrics, rank
from ..chunking.policy import POLICY_A, POLICY_B
from .config import StoreConfig
from .models import record_from_dict, ChunkReference, EmbeddingSpace, VectorQuery
from .sqlite_reference import SQLiteVectorStore

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/stage3d'

def experiments():
    for model in (0,1):
        report=json.loads((ROOT/f'results/stage3c/model{model}-evaluation.json').read_text())
        for exp in report['experiments']:
            path=ROOT/'results/stage3c'/exp['artifact']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==exp['artifact_sha256']
            yield exp,json.loads(path.read_text())

def run(mode, root):
    rows=[]
    data=json.loads((ROOT/'fixtures/rag/embedding_eval/resume_semantics_v1.json').read_text())
    for exp,payload in experiments():
        records=[record_from_dict(r) for r in payload['records']]
        space=EmbeddingSpace(records[0].config,records[0].input_strategy)
        config=StoreConfig(root/exp['artifact'].removesuffix('.json'))
        t=time.perf_counter()
        with SQLiteVectorStore(config,records[0].scope) as store:
            reopen=time.perf_counter()-t
            if mode=='write':
                service,chunks,_,_=corpus(data,POLICY_A if exp['chunk_policy']['name']=='small' else POLICY_B,exp['variant']!='short')
                refs=[ChunkReference.from_citation(service.cite(c.chunk_id,c.revision_id)) for c in chunks]
                store.register_chunks(refs)
                t=time.perf_counter(); store.upsert_embeddings(records); insert=time.perf_counter()-t
                t=time.perf_counter(); store.upsert_embeddings(records); duplicate=time.perf_counter()-t
                for r in records:
                    store.activate_source_version(r.source_id,r.evidence_id,expected_current=(r.evidence_id if store.get_embedding(r.record_id).state=='active' else None))
                assert store.count()==len(records)
                rows.append({'artifact':exp['artifact'],'records':len(records),'insert_seconds':insert,
                             'duplicate_upsert_seconds':duplicate,'bytes':store.path.stat().st_size})
            else:
                assert store.count()==len(records) and store.health_check().healthy
                owner={c['chunk_id']:c['source_fixture_id'] for c in payload['chunk_manifest']}
                query_times=[]; max_delta=0.; totals=[]
                for q,qv,expected in zip(payload['queries'],payload['query_vectors'],exp['queries']):
                    t=time.perf_counter(); hits=store.search_vectors(VectorQuery(space,tuple(qv),len(records)))
                    query_times.append(time.perf_counter()-t)
                    oracle=rank(qv,[(r.record_id,r.vector) for r in records])
                    assert [h.embedding_id for h in hits]==[k for k,_ in oracle]
                    max_delta=max(max_delta,max(abs(h.score-v) for h,(_,v) in zip(hits,oracle)))
                    best={}
                    for h in hits:
                        key=owner[h.chunk_id]
                        if key not in best or (-h.score,h.chunk_id)<(-best[key].score,best[key].chunk_id): best[key]=h
                    ranking=sorted(((k,h.score) for k,h in best.items()),key=lambda x:(-x[1],x[0]))
                    assert [k for k,_ in ranking]==[r['id'] for r in expected['ranking']]
                    assert all(v==r['score'] for (_,v),r in zip(ranking,expected['ranking']))
                    result=metrics(ranking,q['relevant']); scores=dict(ranking)
                    result['hard_negative_win_rate']=float(max(scores[k] for k in q['relevant'])-max(scores[k] for k in q['hard_negatives'])>1e-8)
                    assert all(result[k]==expected[k] for k in result)
                    totals.append(result)
                # Every stored record round-trips through Stage 3C's original citation verifier.
                service,chunks,_,_=corpus(data,POLICY_A if exp['chunk_policy']['name']=='small' else POLICY_B,exp['variant']!='short')
                resolver=ChunkEmbedder(service.scope,None)
                for record in records:
                    recovered=store.get_embedding(record.record_id).record
                    assert recovered==record
                    resolver.resolve(recovered,service)
                rows.append({'artifact':exp['artifact'],'records':len(records),'queries':len(totals),
                             'full_chunk_rankings_equal':True,'full_evidence_rankings_equal':True,
                             'maximum_score_delta':max_delta,'metrics':{k:sum(r[k] for r in totals)/len(totals) for k in totals[0]},
                             'reopen_seconds':reopen,'query_mean_seconds':sum(query_times)/len(query_times),
                             'query_max_seconds':max(query_times),'citation_roundtrips':len(records)})
    output={'process_id':os.getpid(),'mode':mode,'experiments':rows,'passed':True}
    (OUT/f'replay_{mode}.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'mode':mode,'experiments':len(rows),'passed':True}))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=('write','read')); p.add_argument('root',type=Path)
    a=p.parse_args(); run(a.mode,a.root)
