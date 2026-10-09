"""Synthetic license-contract controls; no acceptance answers or protected data."""
import copy,json,unittest
from resume_pipeline.licensing import validate_review,event_identity,procedural,review_sources
import test_repair
from test_repair import Provider
from resume_pipeline.pipeline import requirements

class LicenseContractTests(unittest.TestCase):
    def setUp(self):
        self.task=dict(event_id='event-alpha',requirements=[dict(requirement_id='r1',text='Built Python APIs in Alpha.')],sources=[dict(evidence_id='s1')])
        self.good=dict(support='SUPPORTED',eligibility='A',event_id='event-alpha',links=[dict(requirement_id='r1',supported=True,component='Python APIs',reason='same event')],evidence_ids=['s1'],counterevidence_ids=[],reason='Exact source')
    def test_supported_requires_all_license_dimensions(self):self.assertTrue(validate_review(self.good,self.task))
    def test_contradicted_never_licensed_even_when_reviewer_marks_relevant(self):
        for label in ['CONTRADICTED','PARTIALLY_SUPPORTED','UNSUPPORTED']:
            obj={**self.good,'support':label};self.assertFalse(validate_review(obj,self.task))
    def test_unresolved_counterevidence_vetoes_supported_label(self):
        self.assertFalse(validate_review({**self.good,'counterevidence_ids':['s1']},self.task))
    def test_true_but_irrelevant_weak_and_ineligible_rejected(self):
        for category in 'BCDE':self.assertFalse(validate_review({**self.good,'eligibility':category},self.task))
    def test_same_skill_different_event_rejected(self):
        with self.assertRaisesRegex(ValueError,'changed event'):validate_review({**self.good,'event_id':'event-beta'},self.task)
    def test_shared_keywords_do_not_bypass_link_rejection(self):
        obj=copy.deepcopy(self.good);obj['links'][0]['supported']=False
        self.assertFalse(validate_review(obj,self.task))
    def test_multi_component_requires_exact_component_provenance(self):
        obj=copy.deepcopy(self.good);obj['links'][0]['component']='trained Python model'
        with self.assertRaisesRegex(ValueError,'component span'):validate_review(obj,self.task)
    def test_foreign_citation_rejected(self):
        with self.assertRaisesRegex(ValueError,'foreign evidence'):validate_review({**self.good,'evidence_ids':['foreign']},self.task)
    def test_duplicate_links_and_missing_links_rejected(self):
        for links in [[],self.good['links']*2]:
            with self.assertRaisesRegex(ValueError,'incomplete links'):validate_review({**self.good,'links':links},self.task)
    def test_policy_and_future_work_are_not_achievements(self):
        for text in ['Evaluation must finish first.','We plan to deploy a database.','The engineer should configure alerts.']:
            self.assertTrue(procedural(text))
        self.assertFalse(procedural('Implemented a database service.'))
    def test_source_sections_keep_academic_and_employment_separate(self):
        ref=dict(scope={'candidate_id':'A'},source_id='resume',source_version=1)
        academic=dict(source_context=dict(start=100,text='University course'))
        employment=dict(source_context=dict(start=500,text='Employer'))
        self.assertNotEqual(event_identity(ref,academic),event_identity(ref,employment))
        self.assertNotEqual(event_identity(ref,academic),event_identity({**ref,'scope':{'candidate_id':'B'}},academic))
    def test_similar_project_names_and_duplicate_sources_not_merged(self):
        ref=dict(scope={'candidate_id':'A'},source_id='alpha',source_version=1)
        u=dict(source_context=dict(start=0,text='Alpha'))
        self.assertNotEqual(event_identity(ref,u),event_identity({**ref,'source_id':'alpha-copy'},u))
    def test_long_job_tail_and_duplicate_occurrences_preserved(self):
        raw=('Required Python APIs.\n'*100)+'Required a Rust compiler.'
        job,rows,_=requirements(raw,Provider())
        self.assertEqual(len(rows),101);self.assertEqual(len({r['requirement_id'] for r in rows}),101)
        self.assertEqual(rows[-1]['text'],'Required a Rust compiler.')
        self.assertTrue(all(job[r['start']:r['end']]==r['text'] for r in rows))

class StagedPipelineTests(test_repair.IntegrationTests):
    def test_long_job_processes_all_batches_with_bounded_context(self):
        p=self.pipeline();r=p.run(('Implemented Python APIs.\n'*17),'A')
        self.assertEqual(r['status'],'COMPLETE',r.get('error'))
        self.assertEqual(len(r['requirement_results']),17)
        self.assertEqual(len(r['batch_schedule']),1)
        self.assertEqual(sum(map(len,r['requirement_aliases'].values())),17)
        self.assertLessEqual(r['bounded_context']['input_tokens'],r['bounded_context']['token_limit'])
        self.assertEqual(len(r['resume']['sections'][0]['claims']),1)
        self.assertEqual(len(r['resume']['sections'][0]['claims'][0]['requirement_ids']),17)

    def test_distinct_long_requirements_are_batched_without_tail_loss(self):
        p=self.pipeline();r=p.run('\n'.join('Implemented Python APIs for service '+str(i)+'.' for i in range(17)),'A')
        self.assertEqual(len(r['requirement_results']),17)
        self.assertEqual(len(r['batches']),5)
        self.assertEqual(len({x['requirement_id'] for x in r['requirement_results']}),17)
        self.assertTrue(all(b['bounded_context']['input_tokens']<=b['bounded_context']['token_limit'] for b in r['batches']))
