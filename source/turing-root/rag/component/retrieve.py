"""Bounded component retrieval over unchanged Stage 3E + identity reranker."""
from dataclasses import dataclass,asdict,replace
import time
from ..domain import Scope
from ..retrieval import InformationNeed
from ..reranking.base import ScopedReranker,IdentityProvider
from ..reasoning.contract import from_ranked,messages as original_messages
from .decompose import RequirementDecomposer
@dataclass(frozen=True)
class ComponentConfig:
    per_component:int=2
    global_budget:int=5
    minimum_score:float=.20
    atomic_budget:int=5
    version:str='component-round-robin-v1'
    def __post_init__(self):
        if type(self.per_component) is not int or not 1<=self.per_component<=5:raise ValueError('component budget')
        if type(self.global_budget) is not int or not 1<=self.global_budget<=10:raise ValueError('global budget')
        if type(self.atomic_budget) is not int or not 1<=self.atomic_budget<=5:raise ValueError('atomic budget')
        if not 0<=self.minimum_score<=1:raise ValueError('threshold')

def fair_merge(candidates,budget,resolver):
    """Round-robin distinct-text groups. All retrieved metadata/provenance is
    unioned before selection, so budget cannot discard later duplicate metadata.
    Retrieval membership is a search trace, never a support judgment.
    """
    groups={};orders={};start=time.perf_counter()
    for cid,rows in candidates.items():
        orders[cid]=[]
        for row in rows:
            key=' '.join(resolver(row.reference).split());orders[cid].append(key)
            if key not in groups:groups[key]={'row':row,'retrieved_for':{},'refs':{}}
            g=groups[key];g['retrieved_for'][cid]={'rank':row.rank,'score':row.score,'query_id':row.query_id}
            for ref in (row.reference,)+row.corroborating_references:
                assert ' '.join(resolver(ref).split())==key
                g['refs'][ref.embedding_id]=ref
    chosen=[]
    for depth in range(max((len(v) for v in orders.values()),default=0)):
        for cid,keys in orders.items():
            if depth<len(keys) and keys[depth] not in chosen and len(chosen)<budget:chosen.append(keys[depth])
    result=[];metadata=[]
    for key in chosen:
        g=groups[key];row=g['row'];refs=g['refs']
        result.append(replace(row,corroborating_references=tuple(v for k,v in sorted(refs.items()) if k!=row.reference.embedding_id)))
        metadata.append({'retrieved_for':g['retrieved_for'],'evidence_ids':sorted({r.evidence_id for r in refs.values()})})
    return tuple(result),metadata,time.perf_counter()-start

class ComponentRetriever:
    def __init__(self,retriever,resolver,config=ComponentConfig()):
        self.retriever,self.resolver,self.config=retriever,resolver,config
        if retriever.store.scope!=resolver.scope:raise ValueError('scope mismatch')
    def retrieve(self,tenant_id,candidate_id,need,attestations=()):
        scope=Scope(tenant_id,candidate_id)
        if scope!=self.retriever.store.scope:raise ValueError('unauthorized scope')
        t=time.perf_counter();dec=RequirementDecomposer().decompose(need);decomp_seconds=time.perf_counter()-t
        traces={};candidates={};t=time.perf_counter()
        budget=self.config.atomic_budget if len(dec.components)==1 else self.config.per_component
        for c in dec.components:
            cn=InformationNeed(need.kind,c.text,c.component_id)
            response=self.retriever.retrieve(tenant_id,candidate_id,cn,top_k=budget)
            ranked=ScopedReranker(scope,response,IdentityProvider(),self.resolver).rerank(cn,response.results,budget)
            # Use authentic Stage 3E rows after validating identity reranking.
            assert [x.reference for x in ranked]==[x.reference for x in response.results]
            candidates[c.component_id]=tuple(x for x in response.results if x.score>=self.config.minimum_score)
            traces[c.component_id]=asdict(response)
        retrieval_seconds=time.perf_counter()-t
        ranked,mapping,merge_seconds=fair_merge(candidates,self.config.global_budget,self.resolver)
        ctx=from_ranked(scope,ranked,self.resolver,attestations)
        for group,meta in zip(ctx['groups'],mapping):group['retrieval_membership']=meta['retrieved_for']
        ctx['component_retrieval']=[{'component_id':c.component_id,'text':c.text,'evidence_ids':sorted({e for m in mapping if c.component_id in m['retrieved_for'] for e in m['evidence_ids']}),'status':'selected_candidates' if any(c.component_id in m['retrieved_for'] for m in mapping) else 'budget_excluded' if candidates[c.component_id] else 'no_plausible_candidate_retrieved'} for c in dec.components]
        ctx['component_notice']='Retrieval membership does not prove support. No plausible candidate means retrieval absence, not contradiction or proof of corpus absence.'
        return {'context':ctx,'decomposition':asdict(dec),'traces':traces,'mapping':mapping,'config':asdict(self.config),'decomposition_seconds':decomp_seconds,'retrieval_seconds':retrieval_seconds,'merge_seconds':merge_seconds}

def messages(need,components,ctx):
    import json
    result=original_messages(need,components,ctx)
    p=json.loads(result[1]['content'])
    p['task']['retrieval_components']=ctx['component_retrieval']
    p['task']['retrieval_notice']=ctx['component_notice']
    result[1]['content']=json.dumps(p,ensure_ascii=True)
    return result
