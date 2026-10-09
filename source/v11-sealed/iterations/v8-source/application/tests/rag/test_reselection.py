"""Synthetic fallback plumbing tests; semantic model quality is not mocked proof."""
import json,unittest,copy
from test_reranking import Harness
import test_repair
from resume_pipeline.reselection import retrieved_pool,exclusions,quote_key

BAD='Implemented Python APIs using 90 verified records.'
SAFE='Implemented Python APIs with FastAPI.'
POLICY='Deployment must finish before evaluation begins.'

class ReselectionTests(Harness,unittest.TestCase):
    pipeline=test_repair.IntegrationTests.pipeline
    def setup_pipeline(self,mode='contradiction'):
        bad=POLICY if mode=='policy' else BAD
        self.add('earlier-claim',bad)
        self.add('correction','The earlier record count was incorrect; only 70 records were verified.')
        p=self.pipeline();calls=[]
        class Model:
            def token_count(self,messages):return len(str(messages))//4
            def generate(self,messages):
                task=json.loads(messages[-1]['content']);calls.append(task)
                if 'claim' in task:
                    denied=task['claim']==BAD
                    support='CONTRADICTED' if denied else 'PARTIALLY_SUPPORTED' if mode=='weak_alternative' else 'SUPPORTED'
                    link=not denied and mode!='wrong_event'
                    return {'text':json.dumps(dict(support=support,eligibility='E' if denied else 'A',event_id=task['event_id'],links=[dict(requirement_id=r['requirement_id'],supported=link,component=r['text'],reason='Synthetic declared relation') for r in task['requirements']],evidence_ids=[task['sources'][0]['evidence_id']],counterevidence_ids=[task['sources'][-1]['evidence_id']] if denied else [],reason='Explicit correction' if denied else 'Synthetic source-backed alternative'))}
                fallback=task.get('selection_mode')=='fallback'
                wanted=SAFE if fallback else bad
                entries=[e for e in task['evidence'] if wanted in e['allowed_quotes']]
                if not entries:
                    return {'text':json.dumps(dict(requirements=[dict(requirement_id=r['requirement_id'],label='UNKNOWN',evidence_ids=[],reason='No eligible quotation') for r in task['requirements']],selected_quotes=[]))}
                e=entries[0];quote=wanted
                if fallback and mode=='fabricated_alternative':quote='Implemented Python APIs using 75 records.'
                if fallback and mode=='clipped_metric':quote='Implemented Python APIs.'
                return {'text':json.dumps(dict(requirements=[dict(requirement_id=r['requirement_id'],label='PARTIALLY_SUPPORTED',evidence_ids=[e['evidence_id']],reason='Synthetic partial requirement support') for r in task['requirements']],selected_quotes=[dict(evidence_id=e['evidence_id'],quote=quote,requirement_ids=[r['requirement_id'] for r in task['requirements']])]))}
        p.model=Model();return p,calls
    def test_rejected_contradiction_uses_next_grounded_quote(self):
        p,calls=self.setup_pipeline();r=p.run('Implemented Python APIs.','A')
        self.assertEqual(r['status'],'COMPLETE',r.get('error'))
        self.assertEqual([c['text'] for c in r['resume']['sections'][0]['claims']],[SAFE])
        self.assertTrue(any(v.get('support')=='CONTRADICTED' and not v['accepted'] for v in r['claim_reviews']))
        self.assertTrue(any(v.get('accepted') for v in r['claim_reviews']))
        self.assertEqual(len(r['fallback_attempts']),1)
        self.assertIn('initial_requirement_results',r)
        self.assertTrue(r['compiler_valid'])
        for task in calls:
            if task.get('selection_mode')=='fallback':self.assertFalse(any(BAD in e['allowed_quotes'] for e in task['evidence']))
    def test_policy_rejection_preserved_while_alternative_completes(self):
        p,_=self.setup_pipeline('policy');r=p.run('Implemented Python APIs.','A')
        self.assertEqual(r['status'],'COMPLETE',r.get('error'))
        self.assertEqual(r['claim_reviews'][0]['eligibility'],'C')
        self.assertFalse(r['claim_reviews'][0]['accepted'])
        self.assertEqual(r['resume']['sections'][0]['claims'][0]['text'],SAFE)
    def test_metric_is_omitted_only_by_selecting_a_different_whole_quote(self):
        p,_=self.setup_pipeline();r=p.run('Implemented Python APIs.','A')
        self.assertEqual(r['resume']['sections'][0]['claims'][0]['text'],SAFE)
        self.assertNotIn('90',r['resume']['sections'][0]['claims'][0]['text'])
    def test_fallback_cannot_clip_a_metric_bearing_statement(self):
        p,_=self.setup_pipeline('clipped_metric');r=p.run('Implemented Python APIs.','A')
        self.assertEqual(r['status'],'COMPLETE');self.assertEqual([c['text'] for c in r['resume']['sections'][0]['claims']],[SAFE])
        self.assertTrue(all(a['claim_reviews'][0]['quote']['quote'] != 'Implemented Python APIs.' for a in r['fallback_attempts']))
    def test_fallback_cannot_fabricate_metric(self):
        p,calls=self.setup_pipeline('fabricated_alternative');r=p.run('Implemented Python APIs.','A')
        self.assertEqual(r['status'],'COMPLETE');self.assertEqual([c['text'] for c in r['resume']['sections'][0]['claims']],[SAFE]);self.assertFalse(any(t.get('selection_mode')=='fallback' for t in calls))
    def test_fallback_cannot_strengthen_weak_evidence(self):
        p,_=self.setup_pipeline('weak_alternative');r=p.run('Implemented Python APIs.','A')
        self.assertEqual(r['status'],'FAILED');self.assertIsNone(r['resume'])
        self.assertTrue(any(v.get('support')=='PARTIALLY_SUPPORTED' for v in r['claim_reviews']))
    def test_fallback_wrong_event_link_remains_rejected(self):
        p,_=self.setup_pipeline('wrong_event');r=p.run('Implemented Python APIs.','A')
        self.assertEqual(r['status'],'FAILED');self.assertIsNone(r['resume'])
    def test_fallback_context_and_attempts_are_bounded(self):
        p,_=self.setup_pipeline();r=p.run('Implemented Python APIs.','A')
        self.assertLessEqual(len(r['fallback_attempts']),2)
        for a in r['fallback_attempts']:
            self.assertLessEqual(len(a['bounded_context']['evidence_ids']),5)
            self.assertLessEqual(a['bounded_context']['input_tokens'],a['bounded_context']['token_limit'])
    def test_expanded_pool_rejects_foreign_provenance(self):
        p,_=self.setup_pipeline();r=p.run('Implemented Python APIs.','A');bad=copy.deepcopy(r['retrieval'])
        ref=next(iter(bad[0]['output']['context']['provenance'].values()))['reference'];ref['scope']['candidate_id']='B'
        with self.assertRaisesRegex(ValueError,'foreign fallback'):retrieved_pool(bad,p.ledger)
    def test_rejected_duplicate_claim_does_not_get_a_fresh_license(self):
        review=dict(quote=dict(quote=BAD,requirement_ids=['r']),accepted=False,support='CONTRADICTED',eligibility='E')
        texts,_=exclusions([review],[])
        self.assertIn(quote_key('  '+BAD.upper()+'  '),texts)
    def test_link_only_failure_does_not_blacklist_true_fact_for_other_requirement(self):
        review=dict(quote=dict(quote=SAFE,requirement_ids=['r1']),accepted=False,reason='No positive requirement linkage')
        texts,links=exclusions([review],[])
        self.assertNotIn(quote_key(SAFE),texts)
        self.assertIn((quote_key(SAFE),'r1'),links)
        self.assertNotIn((quote_key(SAFE),'r2'),links)
