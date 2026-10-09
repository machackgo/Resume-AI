"""Independent-process saved-vector and real learned-score replay, Stage 3F only."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
from ..retrieval.benchmark import extended_corpus, populate
from ..retrieval.replay import SavedProvider
from ..retrieval import CandidateEvidenceRetriever, RetrievalConfig, InformationNeed, NeedType
from ..vectorstore.models import record_from_dict, EmbeddingSpace
from .base import ScopedReranker, CitationTextResolver, IdentityProvider
from .cross_encoder import LocalCrossEncoder
from .input_builder import build_input
from .prepare import ROOT, OUT

def main(folder):
    if not os.environ.get('SLURM_JOB_ID'): raise RuntimeError('Slurm allocation required')
    artifact=json.loads((OUT/'extended-embeddings.json').read_text())
    records=tuple(record_from_dict(x) for x in artifact['records'])
    saved=SavedProvider(records,json.loads((OUT/'query-vectors.json').read_text()))
    data=json.loads((ROOT/'fixtures/rag/reranking_eval/stage3f_v1.json').read_text())
    service,chunks,owners,recovered,latest=extended_corpus(data,saved)
    assert recovered==records
    store=populate(folder,service,chunks,records)
    retriever=CandidateEvidenceRetriever(store,saved,EmbeddingSpace(records[0].config,records[0].input_strategy),service,[r.record_id for r in records],RetrievalConfig())
    resolver=CitationTextResolver(store,service)
    expected=json.loads((OUT/'candidate-sets.json').read_text())
    responses={}
    for query,old in zip(data['queries'],expected['queries']):
        need=InformationNeed(NeedType.JOB_REQUIREMENT,query['query'],query['id'])
        response=retriever.retrieve(*service.scope.key,need,top_k=20)
        assert json.loads(json.dumps(asdict(response)))==old['response']
        responses[query['id']]=response
    checks=[]
    specs=json.loads((OUT/'models.lock.json').read_text())
    for label,index in (('identity',None),('minilm',0),('tinybert',1)):
        provider=IdentityProvider() if index is None else LocalCrossEncoder(specs[index],ROOT/'models/stage3f')
        original=json.loads((OUT/(label+'.json')).read_text())
        count=0
        for row in original['queries']:
            response=responses[row['id']]; budget=row['requested_candidate_budget']
            result=ScopedReranker(service.scope,response,provider,resolver).rerank(response.query.need,response.results[:budget],budget)
            assert json.loads(json.dumps([asdict(x) for x in result]))==row['results'], (label,row['id'],budget)
            for output_budget in (2,3):
                subset=ScopedReranker(service.scope,response,provider,resolver).rerank(response.query.need,response.results[:budget],output_budget)
                assert [x.original for x in subset]==[x.original for x in result[:output_budget]]
                assert [x.rerank_score for x in subset]==[x.rerank_score for x in result[:output_budget]]
            count+=1
        overflow=None
        if index is not None:
            need=next(iter(responses.values())).query.need
            try: provider.score([build_input(need,'irrelevant '*600)])
            except ValueError: overflow=True
            else: raise AssertionError('silent truncation')
            # Identical texts do not get an implicit origin/trust ranking boost.
            pair=build_input(need,'AWS certificate listed for this candidate.')
            a,b=provider.score([pair,pair]); assert a==b
        checks.append({'label':label,'full_result_replays':count,'top2_top3_prefix_checks':2*count,
                       'bitwise_score_and_order_equal':True,'overlength_rejected':overflow,
                       'identical_text_score_equal':True})
        del provider
    store.close()
    result={'passed':True,'saved_vector_candidate_sets_equal':len(responses),'records_equal':len(records),
            'checks':checks,'slurm_job_id':os.environ['SLURM_JOB_ID']}
    (OUT/'independent-replay.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__': main(Path(sys.argv[1]))
