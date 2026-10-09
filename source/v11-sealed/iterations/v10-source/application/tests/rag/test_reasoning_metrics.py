import copy,json,unittest
from rag.reasoning.contract import aggregate_labels,schema_valid,ROOT,public_need_id
from rag.retrieval import InformationNeed,NeedType
from rag.reasoning.evaluate import measure,aggregate
from rag.reasoning.prepare import contextual_gold

class MetricsTests(unittest.TestCase):
    def fixture(self):
        case={'id':'x','category':'direct','requirement':'Built API','components':[{'id':'a1','claim':'Built API'}],'gold':[{'component_id':'a1','label':'SUPPORTED','relations':{'d':'SUPPORTED'}}]}
        ctx={'provenance':{'e':{'content':'Built API.'}},'groups':[]}
        gold={'label':'SUPPORTED','atoms':{'a1':'SUPPORTED'}}
        row={'case':case,'contexts':{'rag5':ctx},'gold':{'rag5':gold,'full':gold},'id_to_doc':{'e':'d'},'security':{'foreign_ids':['foreign']}}
        p={'information_need_id':public_need_id(InformationNeed(NeedType.JOB_REQUIREMENT,'Built API','x')),'label':'SUPPORTED','atomic_claims':[{'component_id':'a1','claim':'Built API','label':'SUPPORTED','evidence_ids':['e'],'quotes':[{'evidence_id':'e','quote':'Built API'}],'reason':'Explicit.'}],'evidence_ids':['e'],'missing_evidence':[],'reason':'Explicit.'}
        return row,p
    def test_perfect(self):
        row,p=self.fixture();m=aggregate([measure(row,'rag5',json.dumps(p))]);self.assertEqual(m['label_accuracy'],1);self.assertEqual(m['citation_precision'],1);self.assertEqual(m['hallucinated_candidate_claim_rate'],0)
    def test_false_positive(self):
        row,p=self.fixture();row['gold']['rag5']['label']='UNKNOWN';row['gold']['rag5']['atoms']['a1']='UNKNOWN';row['case']['gold'][0]['relations']={}
        m=aggregate([measure(row,'rag5',json.dumps(p))]);self.assertEqual(m['labels']['SUPPORTED']['precision'],0);self.assertEqual(m['labels']['UNKNOWN']['recall'],0);self.assertEqual(m['hallucinated_candidate_claim_rate'],1)
    def test_citation_wrong(self):
        row,p=self.fixture();row['case']['gold'][0]['relations']={};m=measure(row,'rag5',json.dumps(p));self.assertIn('CITATION FAILURE',m['failures']);self.assertEqual(aggregate([m])['unsupported_citation_rate'],1)
    def test_fabricated(self):
        row,p=self.fixture();p['atomic_claims'][0]['evidence_ids']=['fake'];m=aggregate([measure(row,'rag5',json.dumps(p))]);self.assertGreater(m['fabricated_evidence_id_rate'],0)
    def test_leakage(self):
        row,p=self.fixture();p['evidence_ids']=['foreign'];self.assertTrue(measure(row,'rag5',json.dumps(p))['cross_candidate_leakage'])
    def test_no_repair(self):
        row,p=self.fixture();m=measure(row,'rag5','```json\n'+json.dumps(p)+'\n```');self.assertFalse(m['json_valid']);self.assertFalse(m['correct'])
    def test_retrieval_attribution(self):
        row,p=self.fixture();row['gold']['rag5']={'label':'UNKNOWN','atoms':{'a1':'UNKNOWN'}};self.assertIn('RETRIEVAL FAILURE',measure(row,'rag5',json.dumps(p))['failures'])
    def test_injection_attribution(self):
        row,p=self.fixture();row['case']['attack']=True;row['gold']['rag5']['atoms']['a1']='UNKNOWN';self.assertIn('SECURITY FAILURE',measure(row,'rag5',json.dumps(p))['failures'])
    def test_conflict_gold(self):
        c={'gold':[{'component_id':'a','relations':{'d':'SUPPORTED','e':'UNSUPPORTED'}}]};self.assertEqual(contextual_gold(c,{'provenance':{'x':{},'y':{}}},{'x':'d','y':'e'})['label'],'UNKNOWN')
    def test_schema_empty_reason(self):
        r,p=self.fixture();p['reason']='';self.assertFalse(schema_valid(p,json.loads((ROOT/'rag/reasoning/schema.json').read_text())))
    def test_macro_fixed_four_labels(self):
        r,p=self.fixture();self.assertEqual(aggregate([measure(r,'rag5',json.dumps(p))])['macro_f1'],.25)
    def test_attribution_multi_cause(self):
        r,p=self.fixture();p['atomic_claims'][0]['evidence_ids']=['fake'];m=measure(r,'rag5',json.dumps(p));self.assertIn('CITATION FAILURE',m['failures'])
