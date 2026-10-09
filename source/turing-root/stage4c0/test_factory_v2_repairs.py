import copy,unittest
from .test_grounding import fixture
from .grounding import validate_claims,action_mismatches,nonfactual_safe
from .compatibility import ORIGIN_TO_FROZEN

class FactoryRepairTests(unittest.TestCase):
    def setup_credential(self):
        s,_=fixture();f=s['input']['profile']['facts'][0];f.update(field='credential',value='Certificate of Completion in Backend Systems (non-degree)')
        s['input']['rag']=[];s['oracle']['facts'][0].update(kind='credential',evidence_ids=[],action=None,technologies=[],numbers=[],entities=[])
        out={'artifact':{'sections':[{'section':'EDUCATION','entries':[{'event_id':'P1','title':{'text':f['value'],'fact_ids':['F1'],'evidence_ids':[]}}]}]}}
        return s,out
    def test_exact_nondegree_education_credential_allowed(self):
        s,o=self.setup_credential();self.assertEqual(validate_claims(s,o)['hard_errors'],[])
    def test_nondegree_not_promoted_to_degree(self):
        s,o=self.setup_credential();o['artifact']['sections'][0]['entries'][0]['title']['text']='Bachelor of Science in Computer Science'
        self.assertTrue(validate_claims(s,o)['hard_errors'])
    def test_education_credential_not_employment_title(self):
        s,o=self.setup_credential();o['artifact']['sections'][0]['section']='EXPERIENCE'
        self.assertTrue(validate_claims(s,o)['hard_errors'])
    def test_education_credential_wrong_event_rejected(self):
        s,o=self.setup_credential();o['artifact']['sections'][0]['entries'][0]['event_id']='FOREIGN'
        self.assertTrue(validate_claims(s,o)['hard_errors'])
    def test_history_origin_is_only_synthetic_not_verified(self):
        self.assertEqual(ORIGIN_TO_FROZEN['synthetic_authored_history_record'],'synthetic_fixture')
    def test_explicit_instrument_using_with_paraphrase(self):
        self.assertEqual(action_mismatches('Fine-tuned a model using QLoRA.',[{'field':'claim','value':'Fine-tuned a model with QLoRA.'}]),set())
    def test_studied_instrument_does_not_license_using(self):
        self.assertIn('used',action_mismatches('Built a service using Kubernetes.',[{'field':'claim','value':'Built a service; studied Kubernetes.'}]))
    def test_training_noun_with_matching_education(self):
        self.assertEqual(action_mismatches('Analyst with training in statistics and public policy.',[{'field':'degree','value':'Bachelor of Science in Statistics'},{'field':'degree','value':'Master of Public Policy'}]),set())
    def test_unestablished_training_domain_rejected(self):
        self.assertIn('trained',action_mismatches('Training in machine learning.',[{'field':'degree','value':'Bachelor of Science in Statistics'}]))
    def test_degree_does_not_license_model_training(self):
        self.assertIn('trained',action_mismatches('Trained a model in statistics.',[{'field':'degree','value':'Bachelor of Science in Statistics'}]))
    def test_api_consumption_entails_same_api_use(self):
        self.assertEqual(action_mismatches('This describes client-side API use.',[{'field':'claim','value':'Consumed a REST API from a Python client.'}]),set())
    def test_api_study_does_not_entail_use(self):
        self.assertIn('used',action_mismatches('This describes API use.',[{'field':'claim','value':'Studied a REST API.'}]))
    def test_conditional_courtesy_no_new_facts(self):
        self.assertTrue(nonfactual_safe('Would you be available for a brief conversation about the role?'))
        self.assertTrue(nonfactual_safe('Would you be available for a brief conversation about how this experience might fit the team’s needs?'))
        self.assertTrue(nonfactual_safe('I would welcome an opportunity to discuss these contributions and the role. Thank you for your consideration.'))
    def test_courtesy_cannot_hide_inflation_or_referral(self):
        self.assertFalse(nonfactual_safe('Would you be open to a brief conversation about my extensive leadership and the role?'))
        self.assertFalse(nonfactual_safe('I would welcome an opportunity to discuss these contributions and the role. Your colleague referred me.'))

if __name__=='__main__':unittest.main()
