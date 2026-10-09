"""Novel semantic failure patterns. Mock decisions test plumbing, not model quality."""
import json,unittest
from test_reranking import Harness
import test_repair
from resume_pipeline.semantic_policy import content_eligibility,metric_resolution,MAX_ATTEMPTS
from resume_pipeline.licensing import event_identity
from resume_pipeline.reselection import exclusions,quote_key

class FinalSemanticTests(Harness,unittest.TestCase):
    pipeline=test_repair.IntegrationTests.pipeline
    def run_pattern(self,reject=(),weak=(),wrong=(),empty=False):
        for i,t in enumerate(['Built Python APIs for Atlas.','Implemented Python APIs for Boreal.','Designed Python APIs for Cedar.']):self.add('novel-'+str(i),t)
        p=self.pipeline();calls=[]
        class Model:
            def token_count(self,m):return len(str(m))//4
            def generate(self,m):
                t=json.loads(m[-1]['content']);calls.append(t)
                if 'claim' in t:
                    claim=t['claim'];blocked=claim in reject;partial=claim in weak;linked=not blocked and claim not in wrong
                    return {'text':json.dumps(dict(support='CONTRADICTED' if blocked else 'PARTIALLY_SUPPORTED' if partial else 'SUPPORTED',eligibility='F' if blocked else 'D' if partial else 'A',event_id=t['event_id'],links=[dict(requirement_id=r['requirement_id'],supported=linked and 'Unsupported' not in r['text'],component=r['text'],reason='Declared synthetic component relation') for r in t['requirements']],evidence_ids=[t['sources'][0]['evidence_id']],counterevidence_ids=[t['sources'][0]['evidence_id']] if blocked else [],reason='Explicit synthetic correction' if blocked else 'Declared synthetic support'))}
                es=[(e,q) for e in t['evidence'] for q in e['allowed_quotes']];es.sort(key=lambda eq:eq[1])
                e,q=es[0];rs=[dict(requirement_id=r['requirement_id'],label='UNSUPPORTED' if 'Unsupported' in r['text'] else 'PARTIALLY_SUPPORTED',evidence_ids=[] if 'Unsupported' in r['text'] else [e['evidence_id']],reason='Synthetic') for r in t['requirements']]
                return {'text':json.dumps(dict(requirements=rs,selected_quotes=[] if empty else [dict(evidence_id=e['evidence_id'],quote=q,requirement_ids=[r['requirement_id'] for r in rs if r['evidence_ids']])]))}
        p.model=Model();return p,calls
    def test_primary_rejected_second_valid(self):
        p,c=self.run_pattern(reject=['Built Python APIs for Atlas.']);r=p.run('Implemented Python APIs.','A')
        self.assertEqual(r['status'],'COMPLETE',r.get('error'));self.assertTrue(r['fallback_attempts']);self.assertNotIn('Built Python APIs for Atlas.',[x['text'] for x in r['resume']['sections'][0]['claims']])
    def test_first_two_rejected_third_valid(self):
        p,c=self.run_pattern();original=p.model.generate;review_count=[]
        def generate(messages):
            out=original(messages);task=json.loads(messages[-1]['content'])
            if 'claim' in task:
                review_count.append(task['claim'])
                if len(review_count)<=2:
                    obj=json.loads(out['text']);obj.update(support='CONTRADICTED',eligibility='F',counterevidence_ids=[task['sources'][0]['evidence_id']],reason='Synthetic explicit correction');out['text']=json.dumps(obj)
            return out
        p.model.generate=generate;r=p.run('Implemented Python APIs.','A')
        self.assertEqual(r['status'],'COMPLETE',r.get('error'));self.assertEqual(len(set(review_count)),3);self.assertEqual(review_count.count(review_count[0]),1);self.assertEqual(review_count.count(review_count[1]),1)
    def test_all_invalid_safe_omission(self):
        p,c=self.run_pattern(empty=True,reject=['Built Python APIs for Atlas.','Implemented Python APIs for Boreal.','Designed Python APIs for Cedar.','Implemented Python APIs with FastAPI.']);r=p.run('Implemented Python APIs.','A')
        self.assertIsNone(r['resume']);self.assertEqual(r['outcome_kind'],'SAFE_ABSTENTION');self.assertLessEqual(r['fallback_pool']['review_calls'],MAX_ATTEMPTS)
    def test_true_detail_not_achievement(self):
        for text in ['The best validation performance occurs at epoch 7.','Batch size: 32.','Random seed: 17.']:
            self.assertEqual(content_eligibility({'text':text,'source_context':None},{})['eligibility'],'C')
    def test_metric_conflict_nonnumeric_policy(self):
        self.assertEqual(metric_resolution([dict(value=500),dict(value=700)])['action'],'OMIT_METRIC')
        base=dict(entity='Atlas',quantity='rows',population='training',stage='filtered',period='2024',qualifiers='',provenance_verified=True)
        self.assertEqual(metric_resolution([dict(base,value=500),dict(base,value=700)])['action'],'OMIT_METRIC')
        self.assertEqual(metric_resolution([dict(base,value=500),dict(base,value=700,population='raw',stage='input')])['action'],'PRESERVE_SCOPED')
    def test_unsupported_requirement_otherwise_valid_resume(self):
        p,c=self.run_pattern();r=p.run('Implemented Python APIs.\nUnsupported quantum networking.','A')
        self.assertEqual(r['status'],'COMPLETE',r.get('error'));self.assertTrue(any(x['label']=='UNSUPPORTED' for x in r['requirement_results']))
    def test_same_skill_distinct_events(self):
        ref=dict(scope={'candidate_id':'A'},source_id='s',source_version=1)
        self.assertNotEqual(event_identity(ref,dict(source_context={'start':10})),event_identity(ref,dict(source_context={'start':80})))
    def test_high_similarity_wrong_event_not_promoted(self):
        wrong='Built Python APIs for Atlas.';p,c=self.run_pattern(wrong=[wrong]);r=p.run('Implemented Python APIs.','A')
        self.assertEqual(r['status'],'COMPLETE');self.assertNotIn(wrong,[x['text'] for x in r['resume']['sections'][0]['claims']])
    def test_weaker_support_never_strengthened(self):
        weak='Built Python APIs for Atlas.';p,c=self.run_pattern(weak=[weak]);r=p.run('Implemented Python APIs.','A')
        self.assertEqual(r['status'],'COMPLETE');self.assertNotIn(weak,[x['text'] for x in r['resume']['sections'][0]['claims']])
    def test_contradicted_candidate_never_revived(self):
        bad='Built Python APIs for Atlas.';p,c=self.run_pattern(reject=[bad]);r=p.run('Implemented Python APIs.','A')
        self.assertEqual(sum(x.get('claim')==bad for x in c),1);self.assertNotIn(bad,[x['text'] for x in r['resume']['sections'][0]['claims']])
    def test_invalid_sibling_does_not_discard_valid_selection(self):
        p,c=self.run_pattern();original=p.model.generate
        def generate(messages):
            o=original(messages);task=json.loads(messages[-1]['content'])
            if 'claim' not in task and not task.get('selection_mode'):
                obj=json.loads(o['text']);q=dict(obj['selected_quotes'][0]);q['quote']='Invented Python achievement.';obj['selected_quotes'].insert(0,q);o['text']=json.dumps(obj)
            return o
        p.model.generate=generate;r=p.run('Implemented Python APIs.','A');self.assertEqual(r['status'],'COMPLETE',r.get('error'));self.assertTrue(any('non-exact' in x.get('reason','') for x in r['claim_reviews']))
    def test_numbered_experiments_preserve_scoped_schema(self):
        from resume_pipeline.context_units import prepare_units
        from types import SimpleNamespace
        from pathlib import Path
        from jsonschema import Draft202012Validator
        source='Individual Project Assignment\n2. Section A - Image Classifier\n2.D Validation Results\nBuilt an image classifier for coursework.\n3. Section B - Audio Classifier\n3.D Validation Results\nBuilt an audio classifier for coursework.\n'
        ledger=SimpleNamespace(evidence=lambda _:SimpleNamespace(normalized_ref='x'),content=lambda _:source.encode())
        ref=dict(scope={'tenant_id':'t','candidate_id':'A'},source_id='s',evidence_id='e',source_version=1,chunk_id='c',start=0,end=len(source))
        units=prepare_units({'original':dict(reference=ref)},ledger);qs=next(iter(units.values()))['allowed_quotes'];self.assertEqual(len(qs),2)
        self.assertNotEqual(event_identity(ref,qs[0]),event_identity(ref,qs[1]))
        schema=json.loads((Path(__file__).resolve().parents[2]/'resume_pipeline/output.schema.json').read_text())['properties']['sections']['items']['properties']['claims']['items']['properties']['source_context']
        for q in qs:
            context=q['source_context'];self.assertTrue(context['document_scope']);Draft202012Validator(schema).validate(context)
            for h in [context]+context['document_scope']:self.assertEqual(source[h['start']:h['end']],h['text'])

    def test_component_projection_retains_full_requirement_and_scope(self):
        from resume_pipeline.component_review import component_requirement
        for text,expected in [('Implemented Python classification using scikit-learn Gradient Boosting.','Implemented Python classification'),('Implemented an HTTP API with FastAPI.','Implemented an HTTP API'),('Implemented APIs using Flask in Boreal.','Implemented APIs using Flask in Boreal.'),('Implemented an API without Flask.','Implemented an API without Flask.')]:
            r=component_requirement(dict(requirement_id='r',text=text));self.assertEqual(r['text'],expected);self.assertEqual(r['full_requirement'],text);self.assertIn(r['text'],text)
    def test_malformed_review_retains_both_raw_traces(self):
        from resume_pipeline.component_review import review_task,ReviewError
        class Model:
            def token_count(self,m):return len(str(m))//4
            def generate(self,m):
                t=json.loads(m[-1]['content']);obj=dict(support='SUPPORTED',event_id=t['event_id'],evidence_ids=['s'],counterevidence_ids=[],reason='Synthetic supported fact')
                if t['requirements']:obj.update(eligibility='A with invalid appended label',links=[dict(requirement_id='r',supported=True,component=t['requirements'][0]['text'],reason='Synthetic link')])
                return {'text':json.dumps(obj)}
        task=dict(event_id='event',claim='Built Python APIs.',requirements=[dict(requirement_id='r',text='Built Python APIs.')],sources=[dict(evidence_id='s',content='Built Python APIs.')])
        with self.assertRaises(ReviewError) as caught:review_task(Model(),task)
        self.assertIn('factual_review',caught.exception.trace)
        self.assertIn('invalid appended label',caught.exception.trace['failed_component_review']['inference']['text'])
    def test_component_decision_binds_immutable_job_span(self):
        from resume_pipeline.component_review import review_task
        class Model:
            def token_count(self,m):return len(str(m))//4
            def generate(self,m):
                t=json.loads(m[-1]['content']);obj=dict(support='SUPPORTED',event_id=t['event_id'],evidence_ids=['s'],counterevidence_ids=[],reason='Synthetic explicit support')
                if t['requirements']:obj.update(eligibility='A',links=[dict(requirement_id='r',supported=True,reason='Supports the provided API component; other technology is uncovered')])
                return {'text':json.dumps(obj)}
        task=dict(event_id='e',claim='Implemented a Python API.',requirements=[dict(requirement_id='r',text='Implemented Python APIs and container deployment.')],sources=[dict(evidence_id='s',content='Implemented a Python API.')])
        r=review_task(Model(),task);self.assertTrue(r['accepted']);self.assertEqual(r['links'][0]['component'],'Implemented Python APIs');self.assertIn(r['links'][0]['component'],task['requirements'][0]['text'])

    def test_second_pass_contradiction_is_globally_excluded(self):
        from resume_pipeline.component_review import review_task
        class Model:
            def token_count(self,m):return len(str(m))//4
            def generate(self,m):
                t=json.loads(m[-1]['content']);o=dict(support='SUPPORTED',event_id=t['event_id'],evidence_ids=['s'],counterevidence_ids=[],reason='Synthetic initial support')
                if t['requirements']:o.update(support='CONTRADICTED',eligibility='A',counterevidence_ids=['s'],links=[dict(requirement_id='r',supported=False,reason='Explicit correction discovered')],reason='Synthetic second-pass factual veto')
                return {'text':json.dumps(o)}
        task=dict(event_id='e',claim='Built Python APIs.',requirements=[dict(requirement_id='r',text='Built Python APIs.')],sources=[dict(evidence_id='s',content='Synthetic assertion and explicit correction')])
        r=review_task(Model(),task);self.assertFalse(r['accepted']);self.assertEqual(r['support'],'SUPPORTED');self.assertTrue(r['relation_veto']);self.assertEqual(r['veto_decision']['support'],'CONTRADICTED');self.assertEqual(r['veto_decision']['counterevidence_ids'],['s'])
        r['quote']=dict(evidence_id='s',quote=task['claim'],requirement_ids=['r'])
        denied,links=exclusions([r],[]);self.assertIn(quote_key(task['claim']),denied)
