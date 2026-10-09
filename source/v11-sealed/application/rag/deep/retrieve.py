"""Exact alias normalization and independently bounded deterministic selection."""
from dataclasses import dataclass,asdict,replace
import re,time,hashlib
from rag.domain import Scope,stable_id
from rag.retrieval import CandidateEvidenceRetriever,InformationNeed
from rag.retrieval.models import QueryPlan
from rag.vectorstore.models import SearchFilter,VectorQuery
from rag.component.decompose import RequirementDecomposer
from rag.component.retrieve import fair_merge,messages
from rag.reasoning.contract import from_ranked
from rag.reranking.base import ScopedReranker,IdentityProvider
QUERY_VERSION='focused-exact-acronym-v2'
SELECTOR_VERSION='component-round-robin-audited-v2'

def normalize_query(text):
    # Unambiguous technical acronym only, preserving action, negation, entities,
    # relationships and numeric qualifiers. No requirement ID/evidence access.
    return re.sub(r'\bRAG\b','retrieval augmented generation',' '.join(text.split()))

class QueryRetriever(CandidateEvidenceRetriever):
    def __init__(self,*args,normalize=False,**kwargs):
        super().__init__(*args,**kwargs);self.normalize=normalize
    def retrieve(self,tenant_id,candidate_id,information_need,filters=SearchFilter(),top_k=5):
        text=normalize_query(information_need.text) if self.normalize else information_need.text
        modified=replace(information_need,text=text)
        response=super().retrieve(tenant_id,candidate_id,modified,filters,top_k)
        return response

@dataclass(frozen=True)
class DeepConfig:
    internal_k:int=20
    per_component:int=2
    atomic_budget:int=5
    global_budget:int=5
    minimum_score:float=.2
    normalize:bool=True
    selector_version:str=SELECTOR_VERSION
    def __post_init__(self):
        if type(self.internal_k) is not int or self.internal_k not in (3,5,10,20,40,80):raise ValueError('supported bounded K only')
        if any(type(x) is not int or not 1<=x<=6 for x in (self.per_component,self.atomic_budget,self.global_budget)):raise ValueError('bounded budgets')
        if not 0<=self.minimum_score<=1:raise ValueError('score')

def key(c):return ('alias' if c.normalize else 'original')+'-k'+str(c.internal_k)+'-b'+str(c.global_budget)

def choose(candidates,budget,resolver):
    return fair_merge(candidates,budget,resolver)

class DeepRetriever:
    def __init__(self,retriever,resolver,config):
        self.retriever,self.resolver,self.config=retriever,resolver,config
        if retriever.store.scope!=resolver.scope:raise ValueError('scope mismatch')
        if retriever.config.semantic_budget!=config.internal_k:raise ValueError('internal K mismatch')
        if retriever.normalize!=config.normalize:raise ValueError('query version mismatch')
    def retrieve(self,tenant_id,candidate_id,need,attestations=()):
        scope=Scope(tenant_id,candidate_id)
        if scope!=self.retriever.store.scope:raise ValueError('unauthorized scope')
        t=time.perf_counter();dec=RequirementDecomposer().decompose(need);ds=time.perf_counter()-t
        pools={};traces={};rawhits={};t=time.perf_counter()
        for c in dec.components:
            cn=InformationNeed(need.kind,c.text,c.component_id)
            response=self.retriever.retrieve(*scope.key,cn,top_k=self.config.internal_k)
            validated=ScopedReranker(scope,response,IdentityProvider(),self.resolver).rerank(response.query.need,response.results,len(response.results))
            assert [x.reference for x in validated]==[x.reference for x in response.results]
            pools[c.component_id]=response.results;traces[c.component_id]=asdict(response)
            vector=self.retriever.provider.embed_queries([response.query.text])[0]
            hits=self.retriever.store.search_vectors(VectorQuery(self.retriever.space,tuple(vector),self.config.internal_k)) if response.eligible_count else ()
            rawhits[c.component_id]={h.embedding_id:(i,h.score) for i,h in enumerate(hits,1)}
        rs=time.perf_counter()-t;t=time.perf_counter()
        limit=self.config.atomic_budget if len(dec.components)==1 else self.config.per_component
        candidates={cid:tuple(r for r in rows if r.score>=self.config.minimum_score)[:limit] for cid,rows in pools.items()}
        ranked,mapping,_=choose(candidates,self.config.global_budget,self.resolver)
        selected={ref.embedding_id:i for i,row in enumerate(ranked,1) for ref in (row.reference,)+row.corroborating_references}
        diagnostics=[]
        for cid,rows in pools.items():
            shortlisted={x.reference.embedding_id for x in candidates[cid]}
            for row in rows:
                group=hashlib.sha256(' '.join(self.resolver(row.reference).split()).encode()).hexdigest()
                for j,ref in enumerate((row.reference,)+row.corroborating_references):
                    final=selected.get(ref.embedding_id);sr,score=rawhits[cid][ref.embedding_id]
                    reason=('CORROBORATION' if j else 'COMPONENT_COVERAGE' if row.rank==1 else 'DIRECT_RELEVANCE') if final else 'BELOW_PLAUSIBILITY_FLOOR' if row.score<self.config.minimum_score else 'PER_COMPONENT_CUTOFF' if row.reference.embedding_id not in shortlisted else 'GLOBAL_BUDGET'
                    diagnostics.append(dict(component_ids=[cid],semantic_rank=sr,semantic_score=score,group_rank=row.rank,internal_k=self.config.internal_k,duplicate_group=group,source_id=ref.source_id,evidence_id=ref.evidence_id,embedding_id=ref.embedding_id,status='selected' if final else 'rejected',reason=reason,final_rank=final,duplicate_suppressed=bool(j),trust_category=ref.trust,origin=ref.origin,verification=ref.verification,provenance_handle=asdict(ref)))
        ss=time.perf_counter()-t
        ctx=from_ranked(scope,ranked,self.resolver,attestations)
        for group,meta in zip(ctx['groups'],mapping):
            group['retrieval_membership']=meta['retrieved_for']
            meta['document_evidence_ids']=meta['evidence_ids']
            meta['evidence_ids']=sorted({e['evidence_id'] for e in group['evidence']})
        ctx['component_retrieval']=[{'component_id':c.component_id,'text':c.text,'evidence_ids':sorted({e for m in mapping if c.component_id in m['retrieved_for'] for e in m['evidence_ids']}),'status':'selected_candidates' if any(c.component_id in m['retrieved_for'] for m in mapping) else 'budget_excluded' if candidates[c.component_id] else 'no_plausible_candidate_retrieved'} for c in dec.components]
        ctx['component_notice']='Retrieval membership does not prove support. No plausible candidate means retrieval absence, not contradiction or proof of corpus absence.'
        assert len(ctx['groups'])<=self.config.global_budget
        return dict(context=ctx,decomposition=asdict(dec),traces=traces,mapping=mapping,selector_trace=diagnostics,query_construction_version=QUERY_VERSION if self.config.normalize else "focused-v1",config=asdict(self.config),decomposition_seconds=ds,retrieval_seconds=rs,selector_seconds=ss,merge_seconds=ss,raw_pool_size=sum(len(h) for h in rawhits.values()),distinct_pool_size=len({r.reference.embedding_id for rows in pools.values() for r in rows}))
