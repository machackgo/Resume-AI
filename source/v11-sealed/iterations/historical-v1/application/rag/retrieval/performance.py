"""Local synthetic engineering microbenchmark, not model quality or production scale."""
from dataclasses import asdict
import json
from pathlib import Path
import statistics
import time
from ..embeddings.models import EmbeddingConfig
from .benchmark import extended_corpus, populate, OUT
from . import *
from ..vectorstore.models import EmbeddingSpace
class SyntheticProvider:
    config=EmbeddingConfig('synthetic','constant-384','v1',384,True)
    def embed_documents(self,texts): return [(1.,)+(0.,)*383 for _ in texts]
    def embed_queries(self,texts): return self.embed_documents(texts)
def run(folder):
    rows=[]; provider=SyntheticProvider()
    for n in (100,1000):
        data={'documents':[{'id':str(i),'text':f'Implemented Kubernetes service number {i} using Python API endpoints.','title':'Synthetic engineering','section':'Projects'} for i in range(n)]}
        start=time.perf_counter(); svc,chunks,owners,records,_=extended_corpus(data,provider); materialize=time.perf_counter()-start
        start=time.perf_counter(); store=populate(folder/str(n),svc,chunks,records); indexing=time.perf_counter()-start
        space=EmbeddingSpace(provider.config,'title-section-v1'); ids=[r.record_id for r in records]
        for strategy in ('semantic','lexical','hybrid'):
            start=time.perf_counter(); retriever=CandidateEvidenceRetriever(store,provider,space,svc,ids,RetrievalConfig(strategy=strategy,deduplicate=False)); prep=time.perf_counter()-start
            for k in (1,3,5):
                durations=[]
                for repeat in range(5):
                    start=time.perf_counter(); result=retriever.retrieve(*svc.scope.key,InformationNeed(NeedType.SKILL,'Kubernetes','micro'),top_k=k); durations.append(time.perf_counter()-start)
                    assert len(result.results)==k
                rows.append({'n':n,'strategy':strategy,'top_k':k,'materialize_seconds':materialize,'vector_index_seconds':indexing,'catalogue_prepare_seconds':prep,
                    'median_seconds':statistics.median(durations),'min_seconds':min(durations),'max_seconds':max(durations),'samples':durations})
        store.close()
    (OUT/'performance.json').write_text(json.dumps({'label':'node-local synthetic CPU microbenchmark; constant 384d vectors; excludes real embedding latency; includes lifecycle checks and BM25 preparation per request','rows':rows},indent=2)+'\n')
if __name__=='__main__':
    import sys
    run(Path(sys.argv[1]))
