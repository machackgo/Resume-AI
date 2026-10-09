from dataclasses import replace
import unittest
from test_reranking import Harness, Scores
from rag.domain import Scope
from rag.reranking.base import ScopedReranker, IdentityProvider
from rag.vectorstore.models import SearchFilter

class SecurityTests(Harness,unittest.TestCase):
    def test_foreign_tenant(self): self.foreign(Scope('other','A'))
    def test_foreign_candidate(self): self.foreign(Scope('tenant','B'))
    def foreign(self,scope):
        r=self.two(); row=replace(r.results[0],reference=replace(r.results[0].reference,scope=scope))
        with self.assertRaises(ValueError): self.bound(r).rerank(self.need,(row,),1)
        with self.assertRaises(ValueError): self.bound(replace(r,results=(replace(row,rank=1),)))
    def test_unseen_same_candidate(self):
        r=self.two(); b=self.bound(r); self.add('new','Built production REST APIs in Kubernetes.')
        new=self.response(); unseen=next(x for x in new.results if x.reference.embedding_id not in b.allowed)
        with self.assertRaises(ValueError): b.rerank(self.need,(unseen,),1)
    def test_provider_cannot_introduce_evidence(self):
        r=self.two()
        with self.assertRaises(ValueError): self.bound(r,Scores([r.results[1],r.results[0]])).rerank(self.need,r.results,2)
    def test_corroborating_scope(self):
        r=self.two(); row=r.results[0]
        row=replace(row,corroborating_references=(replace(row.reference,scope=Scope('tenant','B')),))
        with self.assertRaises(ValueError): self.bound(replace(r,results=(row,)))
    def test_need_mismatch(self):
        r=self.two()
        with self.assertRaises(ValueError): self.bound(r).rerank(replace(self.need,requirement_id='other'),r.results,2)
    def test_query_forgery(self):
        r=self.two()
        with self.assertRaises(ValueError): self.bound(replace(r,query=replace(r.query,query_id='forged')))
    def test_modified_retrieval_score(self):
        r=self.two()
        with self.assertRaises(ValueError): self.bound(r).rerank(self.need,(replace(r.results[0],score=99.),),1)
    def test_modified_trust(self):
        r=self.two(); row=replace(r.results[0],reference=replace(r.results[0].reference,trust='verified'))
        with self.assertRaises(ValueError): self.bound(r).rerank(self.need,(row,),1)
        with self.assertRaises(ValueError): self.bound(replace(r,results=(row,))).rerank(self.need,(row,),1)
    def test_modified_space(self):
        r=self.two(); row=replace(r.results[0],reference=replace(r.results[0].reference,semantic_space_id='other'))
        with self.assertRaises(ValueError): self.bound(replace(r,results=(row,))).rerank(self.need,(row,),1)
    def test_modified_locator(self):
        r=self.two(); row=replace(r.results[0],reference=replace(r.results[0].reference,start=999))
        with self.assertRaises(ValueError): self.bound(replace(r,results=(row,))).rerank(self.need,(row,),1)
    def test_stale_after_retrieval(self):
        self.add('resume','Built production REST APIs.'); r=self.response(); b=self.bound(r)
        self.add('resume','Interested in APIs.')
        with self.assertRaises(ValueError): b.rerank(self.need,r.results,1)
    def test_deleted_after_retrieval(self):
        r=self.two(); b=self.bound(r); self.store.delete_source(r.results[0].reference.source_id)
        with self.assertRaises(ValueError): b.rerank(self.need,r.results,2)
    def test_purged_after_retrieval(self):
        r=self.two(); b=self.bound(r); self.store.delete_embeddings([r.results[0].reference.embedding_id],purge=True)
        with self.assertRaises(ValueError): b.rerank(self.need,r.results,2)
    def test_history_rejected(self):
        r=self.two()
        with self.assertRaises(ValueError): self.bound(replace(r,filters=SearchFilter(state='superseded')))
    def test_no_search_during_reranking(self):
        r=self.two()
        def forbidden(*args,**kwargs): raise AssertionError('unrestricted search')
        self.store.search_vectors=forbidden
        self.assertEqual(len(self.bound(r).rerank(self.need,r.results,2)),2)
    def test_bound_scope(self):
        r=self.two()
        with self.assertRaises(ValueError): ScopedReranker(Scope('tenant','B'),r,IdentityProvider(),self.resolver)
    def test_mixed_space(self):
        r=self.two(); rows=(r.results[0],replace(r.results[1],reference=replace(r.results[1].reference,semantic_space_id='other')))
        with self.assertRaises(ValueError): self.bound(replace(r,results=rows))
    def test_corrupt_group(self):
        r=self.two(); row=replace(r.results[0],corroborating_references=(r.results[1].reference,))
        with self.assertRaises(ValueError): self.bound(replace(r,results=(row,))).rerank(self.need,(row,),1)
