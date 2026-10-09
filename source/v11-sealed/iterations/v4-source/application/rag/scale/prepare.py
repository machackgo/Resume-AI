"""Build one shared corpus per scale; unchanged retrieval and reasoning context."""
import json,os,time,hashlib
from dataclasses import asdict
from pathlib import Path
from .dataset import dataset,at_scale
from ..reasoning.prepare import corpus,contextual_gold,dump,ROOT
from ..reasoning.contract import context,from_ranked
from ..domain import Scope
from ..ingestion import MemoryLedger
from ..embeddings.benchmark import CLOCK
from ..embeddings.local import LocalTransformerProvider
from ..embeddings.cache import ChunkEmbedder
from ..retrieval.benchmark import populate
from ..retrieval import CandidateEvidenceRetriever,RetrievalConfig,InformationNeed,NeedType
from ..retrieval.models import RetrievalResult
from ..vectorstore.models import EmbeddingSpace,SearchFilter
from ..reranking.base import CitationTextResolver
OUT=ROOT/'results/stage3h'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build_scale(data,scale,provider,folder):
    start=time.perf_counter();scope=Scope('synthetic-stage3h','candidate-A');ledger=MemoryLedger(clock=CLOCK)
    case={'id':'corpus-A','documents':at_scale(data,scale)}
    svc,chunks,owners,records,attest=corpus(case,scope,provider,ledger)
    store=populate(folder,svc,chunks,records);space=EmbeddingSpace(provider.config,'title-section-v1')
    retriever=CandidateEvidenceRetriever(store,provider,space,svc,[r.record_id for r in records],RetrievalConfig())
    resolver=CitationTextResolver(store,svc);active=retriever._eligible(SearchFilter())
    # Full-context enumeration is explicitly NOT semantic selection. The same validated
    # catalogue/reference factory supplies all active refs in original source order.
    fullrows=[RetrievalResult(i+1,0.,'full-enumeration-v1','full',retriever._reference(r.record_id,active[r.record_id]),None,None,None,None,None,()) for i,r in enumerate(records) if r.record_id in active]
    full=from_ranked(scope,fullrows,resolver,attest)
    ids={c.evidence.evidence_id:owners[c.chunk_id] for c in chunks}
    stale=[r.evidence_id for r in records if store.get_embedding(r.record_id).state!='active']
    fs=Scope(scope.tenant_id,'candidate-B');bsvc,bc,bo,br,ba=corpus({'id':'B','documents':data['foreign_documents']},fs,provider,ledger)
    bs=populate(folder,bsvc,bc,br);foreign=[r.evidence_id for r in br]
    # Both candidates coexist in the same node-local store root, physically separate files.
    assert all(store.get_embedding(r.record_id) is None for r in br)
    denied=0
    for r in br:
        try:store.upsert_embeddings([r])
        except ValueError:denied+=1
        else:raise AssertionError('foreign write permitted')
    prepared=[]
    for q in data['needs']:
        need=InformationNeed(NeedType.JOB_REQUIREMENT,q['requirement'],q['id']);t=time.perf_counter()
        response=retriever.retrieve(*scope.key,need,top_k=20);elapsed=time.perf_counter()-t
        try:retriever.retrieve(*fs.key,need)
        except ValueError:denied+=1
        else:raise AssertionError('foreign scope permitted')
        variants={'full':full};ranks={}
        for n in (1,3,5):
            variants['rag'+str(n)],ranked=context(scope,response,resolver,n,attest)
            ranks[str(n)]=[owners[x.reference.chunk_id] for x in ranked]
        for ctx in variants.values():
            assert not (set(stale)|set(foreign))&set(ctx['provenance'])
        prepared.append({'case':q,'scope':asdict(scope),'contexts':variants,'rankings':ranks,'id_to_doc':ids,
            'gold':{k:contextual_gold(q,c,ids) for k,c in variants.items()},
            'security':{'foreign_rejected':True,'foreign_ids':foreign,'stale_ids':stale},
            'response':asdict(response),'retrieval_seconds':elapsed,'scale':scale})
    for r in records:ChunkEmbedder(scope,None).resolve(store.get_embedding(r.record_id).record,svc)
    meta={'scale':scale,'active_chunks':len(active),'stored_chunks':len(chunks),'stale_chunks':len(stale),'foreign_chunks':len(bc),
          'provenance_roundtrips':len(records),'security_rejections':denied,'seconds':time.perf_counter()-start,
          'embedding_config':asdict(provider.config),'retrieval_config':asdict(RetrievalConfig()),
          'records':[asdict(r) for r in records],'owners':owners,'attestations':[asdict(a) for a in attest]}
    store.close();bs.close();return prepared,meta

def main(folder):
    assert os.getenv('SLURM_JOB_ID')
    OUT.mkdir(exist_ok=True)
    data=dataset();dump(OUT/'dataset.json',data)
    provider=LocalTransformerProvider(json.loads((ROOT/'results/stage3c/models.lock.json').read_text())[0],str(ROOT/'models/stage3c'))
    queries={};original=provider.embed_queries
    def audit(texts):
        vs=original(texts)
        for t,v in zip(texts,vs):
            if t in queries:assert queries[t]==v
            queries[t]=v
        return vs
    provider.embed_queries=audit
    for scale in data['scales']:
        rows,meta=build_scale(data,scale,provider,folder/scale)
        # Avoid replicating large full contexts sixteen times on disk.
        full=rows[0]['contexts']['full'];dump(OUT/(scale+'-full.json'),full)
        for r in rows:del r['contexts']['full']
        dump(OUT/(scale+'-prepared.json'),rows);dump(OUT/(scale+'-corpus.json'),meta)
        print(scale,meta['active_chunks'],round(meta['seconds'],2),flush=True)
    dump(OUT/'query-vectors.json',queries)
def load_rows(scale):
    rows=json.loads((OUT/(scale+'-prepared.json')).read_text());full=json.loads((OUT/(scale+'-full.json')).read_text())
    for r in rows:r['contexts']['full']=full
    return rows
if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
