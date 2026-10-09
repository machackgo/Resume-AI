"""Prepare actual Stage 3E/F contexts, frozen before Qwen; CPU Slurm."""
from dataclasses import asdict
import json, os, sys, time
from pathlib import Path
from ..domain import Scope, Locator, canonical, ClaimDraft, VerificationRecord, VerificationState
from ..adapters import NormalizedFixtureAdapter
from ..ingestion import MemoryLedger, AnnotatedFixtureExtractor
from ..chunking.chunker import CandidateChunks
from ..chunking.policy import POLICY_B
from ..embeddings.benchmark import CLOCK
from ..embeddings.cache import ChunkEmbedder
from ..embeddings.local import LocalTransformerProvider
from ..retrieval.benchmark import SyntheticAdapter, populate
from ..retrieval import CandidateEvidenceRetriever, RetrievalConfig, InformationNeed, NeedType
from ..vectorstore.models import EmbeddingSpace
from ..reranking.base import CitationTextResolver, ScopedReranker, IdentityProvider
from .contract import ROOT,context,from_ranked,aggregate_labels
OUT=ROOT/'results/stage3g'

def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')

def corpus(case,scope,provider,ledger):
    repo=ledger.for_candidate(scope); svc=CandidateChunks(repo); chunks=[]; owners={}; attestations=[]
    for d in case['documents']:
        key=d.get('source_key',d['id'])
        adapter=NormalizedFixtureAdapter(d.get('source_type','resume'),key,'https://example.invalid/'+key,d['title'],d['text'],Locator('document.v1',canonical({'document_id':key,'section':d['section']})))
        r=repo.ingest(SyntheticAdapter(adapter,d.get('origin','candidate_supplied')),AnnotatedFixtureExtractor((ClaimDraft(d['text'],0,len(d['text']),d['text']),)))
        cs=svc.generate(r.evidence.evidence_id,POLICY_B);chunks.extend(cs);owners.update({c.chunk_id:d['id'] for c in cs})
        if d.get('attested'):
            for s in r.supports:
                attestations.append(VerificationRecord(scope,s.support_id,VerificationState.VERIFIED,'synthetic-authenticated-verifier','fixture://'+case['id']+'/'+d['id'],'exact-content-v1',CLOCK(),'Synthetic attestation of only this exact support and evidence version.'))
    records=ChunkEmbedder(scope,provider,clock=CLOCK).embed(chunks,'title-section-v1')
    return svc,chunks,owners,records,attestations

def contextual_gold(case,ctx,id_to_doc):
    docs={id_to_doc[i] for i in ctx['provenance']}; labels=[]
    for a in case['gold']:
        vals={v for d,v in a['relations'].items() if d in docs}
        labels.append('UNKNOWN' if not vals or ('SUPPORTED' in vals and 'UNSUPPORTED' in vals) else 'SUPPORTED' if 'SUPPORTED' in vals else 'PARTIALLY_SUPPORTED' if 'PARTIALLY_SUPPORTED' in vals else 'UNSUPPORTED')
    return {'label':aggregate_labels(labels),'atoms':dict(zip([a['component_id'] for a in case['gold']],labels))}

def build(case,provider,folder,ledger=None):
    ledger=ledger or MemoryLedger(clock=CLOCK); scope=Scope('synthetic-stage3g',case['id'])
    svc,chunks,owners,records,attest=corpus(case,scope,provider,ledger)
    store=populate(folder,svc,chunks,records)
    # Empty stores still carry the pinned semantic space from the provider.
    space=EmbeddingSpace(provider.config,'title-section-v1')
    retriever=CandidateEvidenceRetriever(store,provider,space,svc,[r.record_id for r in records],RetrievalConfig())
    need=InformationNeed(NeedType.JOB_REQUIREMENT,case['requirement'],case['id'])
    started=time.perf_counter(); response=retriever.retrieve(*scope.key,need,top_k=20); elapsed=time.perf_counter()-started
    resolver=CitationTextResolver(store,svc)
    variants={}; rankings={}
    for n in (1,3,5):
        ctx,ranked=context(scope,response,resolver,n,attest);variants['rag'+str(n)]=ctx;rankings[str(n)]=[owners[x.reference.chunk_id] for x in ranked]
    # No-RAG control: all active evidence in source order, independently of semantic ranking.
    # Obtain canonical refs through public lexical retrieval across focused per-source filters.
    from ..vectorstore.models import SearchFilter
    from ..retrieval.models import RetrievalResponse
    active=[]
    for r in records:
        if store.get_embedding(r.record_id).state!='active':continue
        rr=retriever.retrieve(*scope.key,need,SearchFilter(source_id=r.source_id),top_k=100)
        active.extend(x for x in rr.results if x.reference.embedding_id==r.record_id)
    # Each item must remain an authentic Stage 3E result while assembling full context.
    fullgroups=[];fullprov={}
    for row in active:
        rr=RetrievalResponse(response.query,response.config,response.filters,( __import__('dataclasses').replace(row,rank=1),),1,0,0)
        cc,_=context(scope,rr,resolver,1,attest)
        for g in cc['groups']:
            # Avoid duplicate refs when grouped corpus has corroboration.
            g={'evidence':[e for e in g['evidence'] if e['evidence_id'] not in fullprov]}
            if g['evidence']:fullgroups.append(g)
        fullprov.update(cc['provenance'])
    variants['full']={'version':'stage3g-v2','groups':fullgroups,'provenance':fullprov}
    ids={c.evidence.evidence_id:owners[c.chunk_id] for c in chunks}
    security={'foreign_rejected':None,'foreign_ids':[],'stale_ids':[r.evidence_id for r in records if store.get_embedding(r.record_id).state!='active']}
    if case.get('foreign_documents'):
        foreign=dict(case,documents=case['foreign_documents']); fs=Scope(scope.tenant_id,'candidate-B')
        bsvc,bc,bo,br,ba=corpus(foreign,fs,provider,ledger);bs=populate(folder,bsvc,bc,br)
        security['foreign_ids']=[r.evidence_id for r in br]
        try: retriever.retrieve(*fs.key,need)
        except ValueError: security['foreign_rejected']=True
        else: raise AssertionError('scope override permitted')
        assert all(store.get_embedding(r.record_id) is None for r in br)
        assert not set(security['foreign_ids'])&set(variants['rag5']['provenance'])
        bs.close()
    for ctx in variants.values():assert not set(security['stale_ids'])&set(ctx['provenance'])
    output={'case':case,'scope':asdict(scope),'contexts':variants,'rankings':rankings,'id_to_doc':ids,
            'gold':{k:contextual_gold(case,c,ids) for k,c in variants.items()},'security':security,
            'response':asdict(response),'records':[asdict(r) for r in records],
            'reranked':[asdict(x) for x in context(scope,response,resolver,5,attest)[1]],'retrieval_seconds':elapsed}
    store.close();return output

def main(folder):
    if not os.getenv('SLURM_JOB_ID'):raise RuntimeError('Slurm required')
    spec=json.loads((ROOT/'results/stage3c/models.lock.json').read_text())[0]
    provider=LocalTransformerProvider(spec,str(ROOT/'models/stage3c'))
    queries={};embed=provider.embed_queries
    def audited(texts):
        vectors=embed(texts);queries.update(dict(zip(texts,vectors)));return vectors
    provider.embed_queries=audited
    cases=json.loads((ROOT/'fixtures/rag/reasoning_eval/stage3g_v1.json').read_text())['cases']
    rows=[build(c,provider,folder/c['id']) for c in cases]
    dump(OUT/'prepared.json',rows);dump(OUT/'query-vectors.json',queries)
    print('Prepared',len(rows),'cases',flush=True)
    for r in rows:
        if r['case']['category']=='rank5':print(r['rankings'],flush=True)
if __name__=='__main__':main(Path(sys.argv[1]))
