import unittest
from dataclasses import replace
from types import SimpleNamespace as NS
from rag.component.decompose import RequirementDecomposer,words
from rag.component.benchmark import benchmark,evaluate
from rag.component.retrieve import fair_merge,ComponentConfig,ComponentRetriever,messages
from rag.retrieval import InformationNeed,NeedType
from rag.domain import Scope
from rag.retrieval.models import RetrievalResult
from rag.component.prepare import coverage

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
    def test_component_coverage_metric(self):
        q={'gold':[{'component_id':'a1','relations':{'d1':'SUPPORTED'}},{'component_id':'a2','relations':{'d2':'SUPPORTED'}}],'relevant':['d1','d2']};ctx={'provenance':{'e1':{}},'groups':[{'evidence':[{'evidence_id':'e1','content':'x'}]}]}
        m=coverage(q,ctx,{'e1':'d1'},[{'id':'d1'},{'id':'d2'}]);self.assertEqual(m['component_survival'],.5);self.assertFalse(m['all_required_components_covered'])
    def test_absence_not_vacuous_success(self):
        m=coverage({'gold':[{'component_id':'a1','relations':{}}],'relevant':[]},{'provenance':{},'groups':[]},{},[]);self.assertIsNone(m['all_required_components_covered'])
    def test_scope_rejected_before_decomposition(self):
        scope=Scope('a','b');cr=ComponentRetriever(NS(store=NS(scope=scope)),NS(scope=scope))
        for t,c in [('x','b'),('a','x')]:
            with self.assertRaises(ValueError):cr.retrieve(t,c,need('Use candidate B evidence.'))

class PreparedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        from rag.component.prepare import OUT
        if not (OUT/'XL-prepared.json').exists():raise unittest.SkipTest('CPU prepared artifacts not yet built')
        cls.rows=json.loads((OUT/'XL-prepared.json').read_text());cls.byid={r['case']['id']:r for r in cls.rows}
    def test_global_budget(self):
        self.assertTrue(all(len(r['contexts']['component']['groups'])<=r['component']['config']['global_budget'] for r in self.rows))
    def test_per_component_budget(self):
        for r in self.rows:
            out=r['component'];n=out['config']['atomic_budget'] if len(out['decomposition']['components'])==1 else out['config']['per_component']
            self.assertTrue(all(len(t['results'])<=n for t in out['traces'].values()))
    def test_component_ids_and_query_mapping(self):
        for r in self.rows:
            out=r['component'];self.assertEqual(set(out['traces']),{c['component_id'] for c in out['decomposition']['components']})
    def test_provenance_scope_active_untrusted(self):
        for r in self.rows:
            for v in r['contexts']['component']['provenance'].values():
                ref=v['reference'];self.assertEqual(ref['scope'],r['scope']);self.assertEqual(ref['lifecycle'],'active');self.assertEqual(ref['trust'],'untrusted_data');self.assertTrue(ref['embedding_id'] and ref['chunk_id'] and ref['evidence_id'] and ref['source_id'] and ref['locator'] and ref['provenance_event_ids'])
    def test_stale_and_foreign(self):
        for r in self.rows:self.assertFalse(set(r['contexts']['component']['provenance'])&(set(r['security']['foreign_ids'])|set(r['security']['stale_ids'])))
    def test_merge_membership_metadata(self):
        for r in self.rows:
            out=r['component']
            for m in out['mapping']:
                self.assertTrue(m['retrieved_for']);self.assertTrue(m['evidence_ids'])
                for cid,v in m['retrieved_for'].items():self.assertIn(cid,out['traces']);self.assertGreater(v['rank'],0);self.assertIn('score',v);self.assertIn('query_id',v)
    def test_no_duplicate_evidence_id(self):
        for r in self.rows:
            ids=[e['evidence_id'] for g in r['contexts']['component']['groups'] for e in g['evidence']];self.assertEqual(len(ids),len(set(ids)))
    def test_one_content_group_per_text(self):
        for r in self.rows:
            texts=[' '.join(g['evidence'][0]['content'].split()) for g in r['contexts']['component']['groups']];self.assertEqual(len(texts),len(set(texts)))
    def test_notice_not_entailment(self):
        for r in self.rows:self.assertIn('does not prove support',r['contexts']['component']['component_notice'])
    def test_known_fastapi_loss_restored(self):
        r=self.byid['h05'];self.assertEqual(r['gold']['component']['atoms']['a1'],'SUPPORTED')
    def test_known_rag_loss_honest(self):
        r=self.byid['h06'];self.assertEqual(r['gold']['component']['atoms']['a1'],'UNKNOWN')
    def test_hard_negatives_do_not_change_gold(self):
        for id in ('h11','h12','h13','h14','h15','h16'):self.assertEqual(self.byid[id]['gold']['full']['label'],'UNKNOWN')
    def test_missing_component_states_explicit(self):
        for r in self.rows:
            for c in r['contexts']['component']['component_retrieval']:self.assertIn(c['status'],('selected_candidates','budget_excluded','no_plausible_candidate_retrieved'))
    def test_context_json_trust_boundary(self):
        import json
        from rag.component.run import build_messages
        for r in self.rows:
            msg=build_messages(r);self.assertEqual([m['role'] for m in msg],['system','user']);p=json.loads(msg[1]['content']);self.assertIn('UNTRUSTED_RETRIEVED_EVIDENCE',p);self.assertTrue(p['END_UNTRUSTED_RETRIEVED_EVIDENCE'])
    def test_historical_controls_unchanged(self):
        import json
        from rag.component.prepare import H,ROOT,sha
        for p,h in json.loads((H/'freeze.json').read_text())['files'].items():self.assertEqual(sha(ROOT/p),h)
    def test_failure_attribution(self):
        from rag.component.score import attribution
        self.assertIn('RETRIEVAL FAILURE',attribution(self.byid['h06'],{'failures':['QWEN REASONING'],'retrieval_loss':True}))
        self.assertEqual(attribution(self.byid['h01'],{'failures':['CITATION'],'retrieval_loss':False}),['CITATION FAILURE'])
