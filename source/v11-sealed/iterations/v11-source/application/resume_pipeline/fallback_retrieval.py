"""Bounded geometric depth expansion after an exhausted licensing pool.

Uses the existing embedding provider, vector store, scoped catalogue, query
relationships, resolver and selector. No source/case-specific query or new fact.
"""
from dataclasses import replace
from rag.deep.retrieve import DeepRetriever, QueryRetriever
from rag.deep.raw import retrieve_text

MAX_RECOVERY_DEPTH=80

def expand_retrieval(engine,scope,requirements,depth=40):
    if scope!=engine.retriever.store.scope:raise ValueError('foreign fallback expansion scope')
    if depth not in (40,80):raise ValueError('unsupported fallback depth')
    if not isinstance(engine,DeepRetriever) or engine.config.internal_k>=depth:return []
    old=engine.retriever
    retriever=QueryRetriever(old.store,old.provider,old.space,old.service,old.catalog,
        replace(old.config,semantic_budget=depth),normalize=old.normalize)
    expanded=DeepRetriever(retriever,engine.resolver,replace(engine.config,internal_k=depth))
    return [dict(requirement_id=r['requirement_id'],retrieval_stage='bounded_fallback_expansion',
                 output=retrieve_text(expanded,*scope.key,r['text'],r['requirement_id'])) for r in requirements]
