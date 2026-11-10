"""Reference orchestration. Catalogue is trusted ingestion output, never query data.
No private SQL or raw vector rows escape this layer. Rebuild after ingestion.
Caller serializes lifecycle mutation with retrieval (no cross-ledger transaction).
"""
from dataclasses import asdict, replace
from ..domain import Scope
from ..embeddings.cache import ChunkEmbedder
from ..vectorstore.models import ChunkReference, EmbeddingSpace, SearchFilter, VectorQuery
from .models import EvidenceReference, RetrievalResult, RetrievalResponse, RetrievalConfig
from .query import construct
from .lexical import rank, tokens
from .fusion import rrf

class CandidateEvidenceRetriever:
    def __init__(self, store, provider, space, chunk_service, embedding_ids, config=RetrievalConfig()):
        if store.scope!=chunk_service.scope or provider.config!=space.config: raise ValueError('scope/space mismatch')
        self.store,self.provider,self.space,self.service,self.config=store,provider,space,chunk_service,config
        self.resolver=ChunkEmbedder(store.scope,None)
        self.catalog={}
        for key in sorted(set(embedding_ids)):
            stored=store.get_embedding(key)
            if stored is None: raise ValueError('missing or foreign embedding')
            r=stored.record
            if EmbeddingSpace(r.config,r.input_strategy)!=space: raise ValueError('incompatible catalogue space')
            citation=self.resolver.resolve(r,chunk_service)
            self.catalog[key]=(citation,ChunkReference.from_citation(citation))

    def _eligible(self, filters):
        rows={}
        for key,(citation,ref) in self.catalog.items():
            stored=self.store.get_embedding(key)
            if stored is None: continue
            if stored.record.scope!=self.store.scope: raise ValueError('foreign record')
            if filters.state is not None and stored.state!=filters.state: continue
            if any(v is not None and k!='state' and getattr(ref,k)!=v for k,v in asdict(filters).items()): continue
            rows[key]=(stored,citation,ref)
        if len(rows)!=self.store.count(self.space,filters): raise ValueError("catalogue incomplete; rebuild after ingestion")
        return rows

    def _reference(self,key,row):
        stored,citation,ref=row; c=citation.chunk
        return EvidenceReference(ref.scope,key,ref.chunk_id,ref.chunk_revision_id,ref.evidence_id,
            ref.source_id,ref.evidence_version,ref.source_type,citation.source.source_uri,c.evidence.locator,
            c.start,c.end,ref.origin,ref.trust,ref.verification_state,ref.support_ids,
            tuple((x.support.claim_id,x.support.support_id,x.support.relationship.value,x.containment.value) for x in c.claim_links),
            ref.provenance_event_ids,self.space.space_id,stored.state)

    def retrieve(self,tenant_id,candidate_id,information_need,filters=SearchFilter(),top_k=5):
        if Scope(tenant_id,candidate_id)!=self.store.scope: raise ValueError('unauthorized scope')
        if not isinstance(filters,SearchFilter): raise ValueError('typed filters required')
        if type(top_k) is not int or not 0<=top_k<=100: raise ValueError('top_k must be 0..100')
        cfg=self.config; plan=construct(information_need,cfg.expansion)
        rows=self._eligible(filters); semantic=[]; lexical=[]
        if top_k and rows:
            if cfg.strategy!='lexical':
                vectors=tuple(self.provider.embed_queries([plan.text]))
                if len(vectors)!=1 or self.provider.config!=self.space.config: raise ValueError('query provider drift/cardinality')
                hits=self.store.search_vectors(VectorQuery(self.space,tuple(vectors[0]),cfg.semantic_budget,filters))
                # Fail closed on incomplete catalogue; never silently lose best candidates.
                if any(h.embedding_id not in rows for h in hits): raise ValueError('catalogue stale; rebuild after ingestion')
                semantic=[(h.embedding_id,h.score) for h in hits]
            if cfg.strategy!='semantic':
                lexical=rank(plan.text,{k:v[1].chunk.text for k,v in rows.items()})[:cfg.lexical_budget]
        sem={k:(i,s) for i,(k,s) in enumerate(semantic,1)}; lex={k:(i,s) for i,(k,s) in enumerate(lexical,1)}
        ranking=rrf(([k for k,_ in semantic],[k for k,_ in lexical]),cfg.rrf_constant) if cfg.strategy=='hybrid' else semantic if cfg.strategy=='semantic' else lexical
        results=[]; groups={}; caps={}; dup=0; div=0
        for key,score in ranking:
            row=rows[key]; text=row[1].chunk.text
            # Only whitespace normalization: punctuation, negation, numbers and actions stay distinct.
            fingerprint=' '.join(text.split())
            ref=self._reference(key,row)
            if cfg.deduplicate and fingerprint in groups:
                index=groups[fingerprint]; old=results[index]
                results[index]=replace(old,corroborating_references=old.corroborating_references+(ref,)); dup+=1; continue
            if cfg.per_source_cap and caps.get(ref.source_id,0)>=cfg.per_source_cap: div+=1; continue
            if len(results)>=top_k: continue
            sr,ss=sem.get(key,(None,None)); lr,ls=lex.get(key,(None,None))
            groups[fingerprint]=len(results); caps[ref.source_id]=caps.get(ref.source_id,0)+1
            results.append(RetrievalResult(len(results)+1,score,cfg.strategy,plan.query_id,ref,sr,ss,lr,ls,
                score if cfg.strategy=='hybrid' else None,tuple(sorted(set(tokens(plan.text))&set(tokens(text))))))
        return RetrievalResponse(plan,cfg,filters,tuple(results),len(rows),dup,div)
