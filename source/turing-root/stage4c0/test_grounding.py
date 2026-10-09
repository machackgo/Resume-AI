import copy,unittest,tempfile
from pathlib import Path
from .grounding import validate_claims,validate_scenario,technologies
from .io import strict_json,write_json,read_json

def fixture():
    content='Built FastAPI endpoints for inference; reduced latency by 31%.'
    fact={'fact_id':'F1','event_id':'P1','field':'achievement','value':content,'provenance':'EXTERNAL_OBSERVED'}
    evidence={'evidence_id':'E1','event_id':'P1','content':content,'source_id':'S1','source_type':'github','origin':'externally_observed','trust':'untrusted_data','verification':{'reference_policy':'resolve_supports','meaning':'Exact support only'},'authenticated_attestations':[],'citation_handle':{'source_version':1,'span':[0,len(content)]}}
    oracle={'fact_id':'F1','evidence_ids':['E1'],'event_id':'P1','owner':'synthetic-1','kind':'achievement','action':'built','technologies':['FastAPI'],'numbers':['31%'],'entities':[],'polarity':'positive','provenance':'EXTERNAL_OBSERVED'}
    return {'input':{'profile':{'candidate_id':'synthetic-1','facts':[fact]},'rag':[evidence],'constraints':{'excluded_fact_ids':[]}},'oracle':{'candidate_id':'synthetic-1','facts':[oracle]}}, {'artifact':{'bullets':[{'text':content,'evidence_ids':['E1'],'fact_ids':['F1']}]}}

class GroundingTests(unittest.TestCase):
    def setUp(self):self.s,self.o=fixture()
    def errors(self):return validate_claims(self.s,self.o)['hard_errors']
    def claim(self):return self.o['artifact']['bullets'][0]
    def test_supported_metric(self):self.assertEqual(self.errors(),[])
    def test_wrong_metric(self):self.claim()['text']=self.claim()['text'].replace('31%','40%');self.assertTrue(any('NUMERIC' in e for e in self.errors()))
    def test_invented_metric(self):self.claim()['text']+=' Served 900 users.';self.assertTrue(self.errors())
    def test_technology_injection(self):self.claim()['text']+=' Deployed Kubernetes.';self.assertTrue(any('TECHNOLOGY' in e for e in self.errors()))
    def test_adjacent_cloud(self):self.claim()['text']='Used AWS.';self.assertTrue(self.errors())
    def test_unknown_evidence(self):self.claim()['evidence_ids']=['E2'];self.assertTrue(any('UNKNOWN_EVIDENCE' in e for e in self.errors()))
    def test_unknown_fact(self):self.claim()['fact_ids']=['F2'];self.assertTrue(any('UNKNOWN_FACT' in e for e in self.errors()))
    def test_cross_candidate(self):self.s['oracle']['facts'][0]['owner']='synthetic-2';self.assertTrue(any('CROSS_CANDIDATE' in e for e in self.errors()))
    def test_scope_mismatch(self):self.s['oracle']['candidate_id']='synthetic-2';self.assertTrue(self.errors())
    def test_action_inflation(self):self.claim()['text']='Led FastAPI development.';self.assertTrue(any('ACTION_STRENGTH' in e for e in self.errors()))
    def test_verification_promotion(self):self.claim()['text']='Verified FastAPI experience.';self.assertTrue(any('UNAUTHENTICATED' in e for e in self.errors()))
    def test_duplicate_bullet(self):self.o['artifact']['bullets'].append(copy.deepcopy(self.claim()));self.assertIn('DUPLICATE_BULLET',self.errors())
    def test_user_exclusion(self):self.s['input']['constraints']['excluded_fact_ids']=['F1'];self.assertTrue(any('EXCLUDED_USER' in e for e in self.errors()))
    def test_instruction_not_grounding(self):self.s['oracle']['facts'][0]['polarity']='instruction';self.assertTrue(self.errors())
    def test_negative_not_positive(self):self.s['oracle']['facts'][0]['polarity']='negative';self.assertTrue(self.errors())
    def test_conflict_not_positive(self):self.s['oracle']['facts'][0]['polarity']='conflict';self.assertTrue(self.errors())
    def test_event_mismatch(self):self.s['oracle']['facts'][0]['event_id']='P2';self.assertTrue(self.errors())
    def test_bad_span(self):self.s['input']['rag'][0]['citation_handle']['span'][1]+=1;self.assertTrue(self.errors())
    def test_untrusted_preserved(self):self.s['input']['rag'][0]['trust']='verified';self.assertTrue(self.errors())
    def test_chunk_bound(self):self.s['input']['rag'][0]['content']='x'*641;self.assertTrue(self.errors())
    def test_lora_boundary(self):self.assertEqual(technologies('QLoRA'),{'QLoRA'})
    def test_number_without_unit_not_substitute(self):self.claim()['text']='Reduced latency by 31 milliseconds.';self.assertTrue(any('NUMERIC' in e for e in self.errors()))
    def test_exact_role(self):self.o={'artifact':{'role':{'text':'Staff Engineer','fact_ids':['F1'],'evidence_ids':['E1']}}};self.assertTrue(any('STRUCTURED_FACT' in e for e in self.errors()))
    def test_exact_degree(self):self.o={'artifact':{'degree':{'text':'PhD','fact_ids':['F1'],'evidence_ids':['E1']}}};self.assertTrue(self.errors())
    def test_exact_employer(self):self.o={'artifact':{'organization':{'text':'Invented Corp','fact_ids':['F1'],'evidence_ids':['E1']}}};self.assertTrue(self.errors())
    def test_exact_credential(self):self.o={'artifact':{'certification':{'text':'Invented Certification','fact_ids':['F1'],'evidence_ids':['E1']}}};self.assertTrue(self.errors())
    def test_exact_dates(self):self.o={'artifact':{'start_date':{'text':'2020-01','fact_ids':['F1'],'evidence_ids':['E1']}}};self.assertTrue(self.errors())
    def test_duplicate_keys(self):
        with self.assertRaises(ValueError):strict_json('{"x":1,"x":2}')
    def test_nonfinite_json(self):
        with self.assertRaises(ValueError):strict_json('{"x":NaN}')
    def test_immutable_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'record.json';write_json(p,{'a':1});write_json(p,{'a':1})
            with self.assertRaises(ValueError):write_json(p,{'a':2})
            self.assertEqual(read_json(p),{'a':1})

if __name__=='__main__':unittest.main()
