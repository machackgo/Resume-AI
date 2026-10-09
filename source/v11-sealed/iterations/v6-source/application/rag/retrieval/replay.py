"""Independent saved-vector replay through the final public retrieval API."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from .benchmark import OUT, ROOT, extended_corpus, populate, experiment
from . import RetrievalConfig
from ..vectorstore.models import record_from_dict
class SavedProvider:
    def __init__(self,records,queries):
        self.config=records[0].config
        self.docs={r.input_hash:r.vector for r in records}; self.queries=queries
    def embed_documents(self,texts): return [self.docs[hashlib.sha256(t.encode()).hexdigest()] for t in texts]
    def embed_queries(self,texts): return [self.queries[t] for t in texts]
def main(folder):
    records=[record_from_dict(x) for x in json.loads((OUT/'extended-embeddings.json').read_text())['records']]
    provider=SavedProvider(records,json.loads((OUT/'query-vectors.json').read_text()))
    data=json.loads((ROOT/'fixtures/rag/retrieval_eval/stage3e_v1.json').read_text())
    svc,chunks,owners,recovered,_=extended_corpus(data,provider)
    assert recovered==tuple(records)
    store=populate(folder,svc,chunks,recovered)
    checks=[]
    for label in ('semantic','lexical','hybrid','semantic-dedup'):
        expected=json.loads((OUT/('extended-'+label+'.json')).read_text())
        config=RetrievalConfig(**expected['config'])
        if label=='semantic-dedup': assert config==RetrievalConfig()
        actual=experiment('replay-'+label,store,svc,recovered,owners,data['queries'],provider,config)
        assert actual['metrics']==expected['metrics'] and json.loads(json.dumps(actual['queries']))==expected['queries']
        checks.append(label)
    store.close()
    (OUT/'saved-vector-replay.json').write_text(json.dumps({'passed':True,'strategies':checks,'queries_per_strategy':len(data['queries']),'records_equal':len(records),'default_equals_measured_semantic_dedup':True},indent=2)+'\n')
if __name__=='__main__': main(Path(sys.argv[1]))
