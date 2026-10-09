"""Focused regression tests for pre-pilot factual-boundary defects."""
import copy
import unittest
from .test_grounding import fixture
from .grounding import validate_claims, validate_scenario, nonfactual_safe
from .contracts import validate_critic, canonical_hash, text_hash, RUBRIC, iter_audit_leaves


class GroundingHardeningTests(unittest.TestCase):
    def setUp(self):
        self.s,self.o=fixture()
        self.s['input']['job']={'text':'Required: FastAPI.'}

    def errors(self):return validate_claims(self.s,self.o)['hard_errors']
    def claim(self):return self.o['artifact']['bullets'][0]

    def add_fact(self,value,field='achievement',event='P2',fact_id='F2',evidence_id='E2'):
        self.s['input']['profile']['facts'].append(dict(fact_id=fact_id,event_id=event,field=field,value=value,provenance='EXTERNAL_OBSERVED'))
        evidence=copy.deepcopy(self.s['input']['rag'][0])
        evidence.update(evidence_id=evidence_id,event_id=event,content=value,source_id='S'+fact_id)
        evidence['citation_handle']['span']=[0,len(value)]
        self.s['input']['rag'].append(evidence)
        self.s['oracle']['facts'].append(dict(fact_id=fact_id,evidence_ids=[evidence_id],event_id=event,owner='synthetic-1',kind=field,action=None,technologies=[],numbers=[],entities=[],polarity='positive',provenance='EXTERNAL_OBSERVED'))

    def test_hidden_technology_cannot_supply_public_fact(self):
        self.s['oracle']['facts'][0]['technologies'].append('AWS')
        self.claim()['text']='Built an AWS endpoint.'
        self.assertTrue(any('TECHNOLOGY_MISMATCH' in x for x in self.errors()))

    def test_hidden_number_cannot_supply_public_fact(self):
        self.s['oracle']['facts'][0]['numbers'].append('52%')
        self.claim()['text']='Reduced latency by 52%.'
        self.assertTrue(any('NUMERIC_MISMATCH' in x for x in self.errors()))

    def test_entry_event_prevents_metric_transfer(self):
        self.add_fact('Reduced startup delay by 72%.')
        c={'text':'Reduced FastAPI latency by 72%.','fact_ids':['F1','F2'],'evidence_ids':['E1','E2']}
        self.o={'artifact':{'sections':[{'section':'EXPERIENCE','entries':[{'event_id':'P1','bullets':[c]}]}]}}
        self.assertTrue(any('WRONG_EVENT_REFERENCE' in x for x in self.errors()))
        self.assertTrue(any('NUMERIC_MISMATCH' in x for x in self.errors()))

    def test_narrative_event_pool_cannot_fuse_metric_and_technology(self):
        self.add_fact('Reduced startup delay by 72%.')
        self.claim().update(text='Reduced FastAPI latency by 72%.',fact_ids=['F1','F2'],evidence_ids=['E1','E2'])
        self.assertTrue(any('CROSS_EVENT_FACT_FUSION' in x for x in self.errors()))

    def test_distinct_complete_sentences_can_summarize_events(self):
        self.add_fact('Reduced startup delay by 72%.')
        self.claim().update(text='Built FastAPI endpoints for inference; reduced latency by 31%. Reduced startup delay by 72%.',fact_ids=['F1','F2'],evidence_ids=['E1','E2'])
        self.assertEqual(self.errors(),[])

    def test_evidence_only_cannot_reintroduce_excluded_fact(self):
        self.s['input']['constraints']['excluded_fact_ids']=['F1']
        self.claim()['fact_ids']=[]
        self.assertTrue(any('EXCLUDED_USER_FACT' in x for x in self.errors()))

    def test_exact_title_requires_correct_field_kind(self):
        self.add_fact('Research Engineer',field='organization',event='P1')
        self.o={'artifact':{'title':{'text':'Research Engineer','fact_ids':['F2'],'evidence_ids':[]}}}
        self.assertTrue(any('STRUCTURED_FACT_MISMATCH' in x for x in self.errors()))

    def test_exact_field_requires_support_even_without_refs(self):
        self.o={'artifact':{'organization':{'text':'Invented Corp','fact_ids':[],'evidence_ids':[]}}}
        self.assertTrue(any('STRUCTURED_FACT_MISMATCH' in x for x in self.errors()))

    def test_structured_title_accepts_exact_compatible_role(self):
        self.add_fact('Research Engineer',field='role',event='P1')
        self.o={'artifact':{'sections':[{'section':'EXPERIENCE','entries':[{'event_id':'P1','title':{'text':'Research Engineer','fact_ids':['F2'],'evidence_ids':[]}}]}]}}
        self.assertEqual(self.errors(),[])

    def test_verified_label_requires_exact_attestation(self):
        self.s['input']['profile']['facts'][0]['provenance']='AUTHENTICATED'
        self.s['oracle']['facts'][0]['provenance']='AUTHENTICATED'
        self.claim()['text']='Verified FastAPI experience.'
        self.assertTrue(any('UNAUTHENTICATED_VERIFICATION' in x for x in self.errors()))

    def test_exact_attestation_can_support_verification(self):
        self.s['input']['profile']['facts'][0]['provenance']='AUTHENTICATED'
        self.s['oracle']['facts'][0]['provenance']='AUTHENTICATED'
        self.s['input']['rag'][0]['authenticated_attestations']=[dict(attestation_id='A1',source_id='S1',fact_ids=['F1'],policy='exact_fact_ids_only')]
        self.claim()['text']='Verified FastAPI experience.'
        self.assertEqual(self.errors(),[])

    def test_wrong_attestation_source_rejected(self):
        self.s['input']['rag'][0]['authenticated_attestations']=[dict(attestation_id='A1',source_id='other',fact_ids=['F1'],policy='exact_fact_ids_only')]
        self.assertIn('INVALID_AUTHENTICATED_ATTESTATION',self.errors())

    def test_context_facts_cannot_become_resume_biography(self):
        self.add_fact('Synthetic Target Lab',field='company_name',event='context_company')
        self.o={'task':'GENERATE_RESUME','artifact':{'summary':{'text':'Synthetic Target Lab','fact_ids':['F2'],'evidence_ids':[]}}}
        self.assertTrue(any('CONTEXT_TO_CANDIDATE_TRANSFER' in x for x in self.errors()))

    def test_unseen_employer_detected_in_narrative(self):
        self.claim()['text']='Built FastAPI endpoints at Invented Corp.'
        self.assertTrue(any('ENTITY_MISMATCH' in x for x in self.errors()))

    def test_wrong_job_source_quote_rejected(self):
        self.o={'artifact':{'source_span':{'start':0,'end':8,'quote':'Preferred'}}}
        self.assertTrue(any('JOB_SOURCE_SPAN' in x for x in self.errors()))

    def test_correct_job_source_quote(self):
        self.o={'artifact':{'source_span':{'start':0,'end':8,'quote':'Required'}}}
        self.assertEqual(self.errors(),[])

    def test_generic_ability_is_factual_without_keywords(self):
        self.claim().update(text='Experienced problem solver.',fact_ids=[],evidence_ids=[])
        self.assertTrue(any('MISSING_FACTUAL_REFERENCE' in x for x in self.errors()))

    def test_safe_courtesy_can_have_empty_refs(self):
        self.claim().update(text='Thank you for your consideration.',fact_ids=[],evidence_ids=[])
        self.assertEqual(self.errors(),[])
        self.assertFalse(nonfactual_safe('Thank you for recognizing my world-class expertise.'))

    def test_oracle_inventory_must_cover_public_facts(self):
        self.s['oracle']['facts']=[]
        self.assertIn('INCOMPLETE_ORACLE_FACT_INVENTORY',validate_scenario(self.s))

    def test_explicit_negative_can_support_truthful_denial(self):
        self.s['input']['profile']['facts'][0]['value']='The candidate reports no QLoRA adapter-training experience.'
        self.s['oracle']['facts'][0]['polarity']='negative'
        self.claim()['text']='No, I have not trained QLoRA adapters.'
        self.assertEqual(self.errors(),[])

    def test_negative_does_not_license_affirmative_clause(self):
        self.s['input']['profile']['facts'][0]['value']='The candidate reports no QLoRA adapter-training experience.'
        self.s['oracle']['facts'][0]['polarity']='negative'
        self.claim()['text']='I have not used FastAPI but trained QLoRA adapters.'
        self.assertTrue(self.errors())

    def test_denial_and_distinct_supported_positive_sentences(self):
        self.s['input']['profile']['facts'][0]['value']='The candidate reports no QLoRA adapter-training experience.'
        self.s['oracle']['facts'][0]['polarity']='negative'
        self.add_fact('Fine-tuned a transformer with LoRA adapters using BF16 base weights in a graduate lab.',event='P1')
        self.add_fact('Used a four-bit quantized model for inference in a separate summarization experiment.',event='P1',fact_id='F3',evidence_id='E3')
        self.claim().update(text='No. I have not trained QLoRA adapters. In a graduate lab, I fine-tuned a transformer with LoRA adapters using BF16 base weights. I used a four-bit quantized model for inference in a separate summarization experiment.',fact_ids=['F1','F2','F3'],evidence_ids=['E1','E2','E3'])
        self.assertEqual(self.errors(),[])

    def test_denial_sentence_does_not_license_later_affirmative_reuse(self):
        self.s['input']['profile']['facts'][0]['value']='The candidate reports no QLoRA adapter-training experience.'
        self.s['oracle']['facts'][0]['polarity']='negative'
        self.claim()['text']='No. I have not trained QLoRA adapters. I trained QLoRA adapters.'
        self.assertTrue(any('TECHNOLOGY_MISMATCH' in x for x in self.errors()))

    def test_unknown_is_not_denial_evidence(self):
        self.claim()['text']='No. I have not trained QLoRA adapters.'
        self.assertTrue(self.errors())

    def test_critic_cannot_call_generic_ability_nonfactual(self):
        self.claim().update(text='Experienced problem solver.',fact_ids=[],evidence_ids=[])
        critic={'schema_version':'stage4c0-v1','output_sha256':canonical_hash(self.o),'visible_input_sha256':canonical_hash(self.s['input']),
            'leaf_reviews':[{'path':'/artifact/bullets/0/text','text_sha256':text_hash(self.claim()['text']),'verdict':'NONFACTUAL','atoms':[],'issue_codes':[],'assessment':'No check needed.'}],
            'rubric_scores':{k:4 for k in RUBRIC['dimensions']},'rubric_assessments':{k:'Pass.' for k in RUBRIC['dimensions']},
            'decision':'ACCEPT','revision_requests':[],'independence':'fresh_context_no_teacher_rationale_no_hidden_oracle'}
        self.assertTrue(any('cannot bypass grounding' in x for x in validate_critic(critic,self.s['input'],self.o)))

    def test_section_object_is_fully_audited(self):
        out={'artifact':{'section':{'section':'SUMMARY','heading':'Summary','claims':[{'text':'Experienced engineer.','fact_ids':['F1'],'evidence_ids':[]}]}}}
        self.assertEqual(list(iter_audit_leaves(out)),[('/artifact/section/claims/0/text','Experienced engineer.')])

    def test_profile_only_identity_and_rag_action_can_share_claim(self):
        self.add_fact('Research Engineer',field='role',event='P1')
        self.s['oracle']['facts'][1]['evidence_ids']=[]
        self.claim().update(text='Research Engineer who built FastAPI endpoints.',fact_ids=['F1','F2'],evidence_ids=['E1'])
        self.assertEqual(self.errors(),[])

    def test_leading_preposition_is_not_part_of_company_name(self):
        self.add_fact('Synthetic Research Works',field='organization',event='P1')
        self.claim().update(text='At Synthetic Research Works, I built FastAPI endpoints.',fact_ids=['F1','F2'],evidence_ids=['E1','E2'])
        self.assertEqual(self.errors(),[])

    def test_leading_preposition_does_not_hide_invented_company(self):
        self.claim()['text']='At Invented Research Works, I built FastAPI endpoints.'
        self.assertTrue(any('ENTITY_MISMATCH' in x for x in self.errors()))

    def test_bounded_compound_courtesy_and_comma_signoff(self):
        self.assertTrue(nonfactual_safe('Thank you for your time,'))
        self.assertTrue(nonfactual_safe('I would welcome a conversation about how this experience could contribute to the role. Thank you for considering my application.'))
        self.assertFalse(nonfactual_safe('I would welcome a conversation about how my 10 years of expertise could contribute to the role. Thank you for considering my application.'))
        self.assertFalse(nonfactual_safe('Thank you for your time. I led your previous project.'))
        self.assertFalse(nonfactual_safe('Thank you for our prior meeting.'))


if __name__=='__main__':unittest.main()
