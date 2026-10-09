"""Independent replay of every selected synthetic diagnostic context."""
import os,json,sys
from pathlib import Path
from dataclasses import asdict
from rag.deep.prepare import ROOT,OUT,provider_new,corpus,Scope,MemoryLedger,CLOCK,populate,EmbeddingSpace,RetrievalConfig,CitationTextResolver,InformationNeed,NeedType,dump
from rag.deep.retrieve import DeepConfig,DeepRetriever,QueryRetriever
from rag.deep.run import check_freeze

def main(folder):
    assert os.getenv("SLURM_JOB_ID");check_freeze()
    cfg=DeepConfig(**json.loads((OUT/"config.json").read_text())["selected"])
    rows=json.loads((OUT/"diagnostic-prepared.json").read_text());p,_=provider_new()
    vectors=json.loads((OUT/"query-vectors.json").read_text());fresh=p.embed_queries
    p.embed_queries=lambda texts:tuple(tuple(vectors[t]) if t in vectors else tuple(fresh([t])[0]) for t in texts)
    results=[]
    for row in rows:
        scope=Scope(**row["scope"]);q=row["case"];ledger=MemoryLedger(clock=CLOCK)
        svc,chunks,owners,records,attest=corpus(dict(id=scope.candidate_id,documents=q["documents"]),scope,p,ledger)
        store=populate(folder/scope.candidate_id,svc,chunks,records);resolver=CitationTextResolver(store,svc)
        retriever=QueryRetriever(store,p,EmbeddingSpace(p.config,"title-section-v1"),svc,[r.record_id for r in records],RetrievalConfig(semantic_budget=cfg.internal_k),normalize=cfg.normalize)
        out=DeepRetriever(retriever,resolver,cfg).retrieve(*scope.key,InformationNeed(NeedType.JOB_REQUIREMENT,q["requirement"],q["id"]),attest)
        out=json.loads(json.dumps(out))
        for field in ("context","traces","mapping","selector_trace","decomposition"):
            assert out[field]==row["component"][field],(q["id"],field)
        for eid,v in out["context"]["provenance"].items():
            ref=v["reference"];stored=store.get_embedding(ref["embedding_id"]);c=svc.cite(stored.record.chunk_id,stored.record.chunk_revision_id)
            assert c.chunk.evidence.evidence_id==eid and c.source.source_id==ref["source_id"]
            assert ref["scope"]==asdict(scope) and c.chunk.text==v["content"]
        results.append(dict(id=q["id"],context_exact=True,selector_exact=True,provenance_roundtrips=len(out["context"]["provenance"])))
        store.close()
    dump(OUT/"diagnostic-independent-verification.json",dict(passed=True,cases=len(results),rows=results,slurm_job=os.environ["SLURM_JOB_ID"]))
    print("DIAGNOSTICS INDEPENDENTLY VERIFIED",len(results),flush=True)
if __name__=="__main__":main(Path(sys.argv[1]))
