import unittest
from dataclasses import replace
from types import SimpleNamespace as NS
from resume_ai.rag.component.decompose import RequirementDecomposer,words
from resume_ai.rag.component.benchmark import benchmark,evaluate
from resume_ai.rag.component.retrieve import fair_merge,ComponentConfig,ComponentRetriever,messages
from resume_ai.rag.retrieval import InformationNeed,NeedType
from resume_ai.rag.domain import Scope
from resume_ai.rag.retrieval.models import RetrievalResult

def need(text,id='test'):return InformationNeed(NeedType.JOB_REQUIREMENT,text,id)
class DecompositionTests(unittest.TestCase):
    def test_frozen_benchmark(self):self.assertTrue(evaluate(benchmark())['metrics']['smoke_pass'])
    def test_ids(self):
        d=RequirementDecomposer();a=d.decompose(need('Built APIs and deployed services.'));self.assertEqual(a,d.decompose(need(a.original_text)));self.assertNotEqual(a.components[0].component_id,d.decompose(need(a.original_text,'other')).components[0].component_id)
    def test_empty_typed(self):
        with self.assertRaises(ValueError):RequirementDecomposer().decompose('built')
    def test_no_base_weight_expansion(self):
        d=RequirementDecomposer().decompose(need('Implemented both RAG and fine-tuning for Juniper.'));self.assertNotIn('weights',' '.join(c.text for c in d.components))
    def test_config(self):
        for k,b in ((0,5),(6,5),(2,0),(2,11)):
            with self.assertRaises(ValueError):ComponentConfig(k,b)
    def test_no_invented_platform(self):
        d=RequirementDecomposer().decompose(need('Cloud deployment.'));self.assertEqual(d.components[0].text,'Cloud deployment.')

def make_case_test(q):
    def test(self):
        d=RequirementDecomposer().decompose(need(q['text']));source={x.lower() for x in words(q['text'])}
        self.assertTrue(all({x.lower() for x in words(c.text)}<=source for c in d.components))
        if q['category']=='atomic':self.assertEqual([c.text for c in d.components],[q['text']])
        elif q['category'] not in ('modifier','technology_conjunction','credential_duration'):self.assertEqual([c.text.lower() for c in d.components],[x.lower() for x in q['expected']])
    return test
for q in benchmark()['cases']:setattr(DecompositionTests,'test_'+q['id'],make_case_test(q))

def row(i,text,rank=1,refs=()):
    ref=NS(embedding_id=i,evidence_id=i,text=text)
    return RetrievalResult(rank,.5,'semantic','q',ref,rank,.5,None,None,None,(),refs)
def resolve(ref):return ref.text
class MergeTests(unittest.TestCase):
    def test_fairness(self):
        a=[row(str(i),'easy'+str(i),i+1) for i in range(5)];b=[row('b','rare')]
        r,m,t=fair_merge({'C1':a,'C2':b},2,resolve);self.assertEqual([x.reference.embedding_id for x in r],['0','b'])
    def test_duplicate_metadata(self):
        r,m,t=fair_merge({'C1':[row('a','same')],'C2':[row('b','same')]},1,resolve)
        self.assertEqual(len(r),1);self.assertEqual(set(m[0]['retrieved_for']),{'C1','C2'});self.assertEqual(set(m[0]['evidence_ids']),{'a','b'});self.assertEqual(len(r[0].corroborating_references),1)
    def test_duplicate_same_ref(self):
        a=row('a','same');r,m,t=fair_merge({'C1':[a],'C2':[a]},5,resolve);self.assertEqual(len(r),1);self.assertEqual(len(r[0].corroborating_references),0)
    def test_empty(self):self.assertEqual(fair_merge({'C1':[]},5,resolve)[0],())
    def test_fewer(self):self.assertEqual(len(fair_merge({'C1':[row('a','a')]},5,resolve)[0]),1)
    def test_budget(self):self.assertEqual(len(fair_merge({'C1':[row('a','a'),row('b','b',2)]},1,resolve)[0]),1)
    def test_deterministic(self):
        c={'C1':[row('a','a')],'C2':[row('b','b')]};self.assertEqual(fair_merge(c,2,resolve)[:2],fair_merge(c,2,resolve)[:2])
    def test_several_missing(self):
        r,m,t=fair_merge({'C1':[],'C2':[],'C3':[row('a','a')]},5,resolve);self.assertEqual(set(m[0]['retrieved_for']),{'C3'})
    def test_scope_rejected_before_decomposition(self):
        scope=Scope('a','b');cr=ComponentRetriever(NS(store=NS(scope=scope)),NS(scope=scope))
        for t,c in [('x','b'),('a','x')]:
            with self.assertRaises(ValueError):cr.retrieve(t,c,need('Use candidate B evidence.'))
