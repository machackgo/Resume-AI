import copy,json,unittest
from pathlib import Path
from . import contracts as c
from .io import read_json,read_jsonl,sha_file
from .grounding import validate_scenario
from .scenarios import generate_pilot,generate_pool,generate_challenge

R=Path(__file__).resolve().parents[1]
class ContractTests(unittest.TestCase):
    def test_research_sources(self):
        src=read_jsonl(R/'research/stage4c0/sources.jsonl');self.assertEqual(len(src),len({s['source_id'] for s in src}));self.assertTrue(all(s['verification_status']=='content_verified' for s in src))
    def test_principle_provenance(self):
        src={s['source_id'] for s in read_jsonl(R/'research/stage4c0/sources.jsonl')}
        for f in (R/'research/stage4c0').glob('*principles.json'):
            for p in read_json(f)['principles']:self.assertTrue(p['provenance']);self.assertTrue(all(x['source_id'] in src for x in p['provenance']))
    def test_contract_hashes(self):
        for p,h in read_json(R/'contracts/manifest.v1.json')['files'].items():self.assertEqual(sha_file(R/p),h,p)
    def test_tasks(self):self.assertEqual(len(c.TASKS),10);self.assertEqual(set(c.TASKS),set(c.OUTPUT_SCHEMAS))
    def test_schemas_versioned(self):
        for task,schema in c.OUTPUT_SCHEMAS.items():self.assertIn(c.VERSION,schema['$id']);self.assertTrue(task in schema['$id'])
    def test_rubric_gates(self):self.assertEqual(c.RUBRIC['dimensions']['grounding']['minimum'],4);self.assertTrue(c.RUBRIC['dimensions']['grounding']['hard_gate'])
    def test_revision_bounded(self):self.assertEqual(c.ACCEPTANCE_GATES['max_revisions'],2)
    def test_teacher_prompt(self):self.assertEqual((R/'contracts/prompts/teacher.v1.txt').read_text(),c.TEACHER_SYSTEM)
    def test_critic_prompt(self):self.assertEqual((R/'contracts/prompts/critic.v1.txt').read_text(),c.CRITIC_SYSTEM)
    def test_candidate_job_determinism(self):self.assertEqual(generate_pilot(),generate_pilot());self.assertEqual(generate_pool(),generate_pool());self.assertEqual(generate_challenge(),generate_challenge())
    def test_synthetic_groundtruth(self):
        for s in generate_pilot()+generate_pool()+generate_challenge():self.assertEqual(validate_scenario(s),[],s['scenario_id']);self.assertTrue(s['metadata']['synthetic']);self.assertFalse(s['metadata']['private_data_used'])
    def test_input_schema_and_rag_projection(self):
        for s in generate_pilot()+generate_pool()+generate_challenge():self.assertEqual(c.validate_input(s['input']),[],s['scenario_id'])
    def test_analyze_no_pre_extracted_answers(self):
        for s in generate_pilot()+generate_pool()+generate_challenge():
            if s['input']['task']=='ANALYZE_JOB':self.assertEqual(s['input']['job']['requirements'],[])
    def test_all_tasks_in_pilot(self):self.assertEqual({r['input']['task'] for r in generate_pilot()},set(c.TASKS))
    def test_no_oracle_in_visible(self):
        for s in generate_pilot()+generate_pool()+generate_challenge():self.assertNotIn('oracle',s['input']);self.assertNotIn('expected_status',s['input']);self.assertNotIn('expected_label',json.dumps(s['input']))
    def test_no_teacher_target_at_groundtruth_creation(self):
        for s in generate_pilot()+generate_pool()+generate_challenge():self.assertFalse(s['metadata']['target_exists_at_ground_truth_creation'])
    def test_challenge_candidate_isolation(self):
        regular={s['input']['profile']['candidate_id'] for s in generate_pilot()+generate_pool()}
        self.assertFalse(regular&{s['input']['profile']['candidate_id'] for s in generate_challenge()})
    def test_groups_isolated(self):
        seen={}
        for s in generate_pilot()+generate_pool()+generate_challenge():
            key=s['metadata']['split_group'];self.assertTrue(key not in seen or seen[key]==s['split']);seen[key]=s['split']
    def test_schema_extra_keys_fail(self):
        s=generate_pilot()[0]['input'];s['oracle']={};self.assertTrue(c.validate_input(s))
    def test_schema_unknown_task_fails(self):
        s=generate_pilot()[0]['input'];s['task']='CLICK_SUBMIT';self.assertTrue(c.validate_input(s))
    def test_boolean_not_integer(self):self.assertTrue(c.validate_schema(True,{'type':'integer'}))
    def test_unknown_schema_assertion_fails(self):
        with self.assertRaises(ValueError):c.validate_schema({}, {'unknownAssertion':True})
    def test_project_origin_audited(self):
        paths=dict(c.iter_audit_leaves({'artifact':{'entries':[{'origin':'EMPLOYMENT','title':{'text':'Title','fact_ids':[],'evidence_ids':[]}}]}}));self.assertIn('/artifact/entries/0/origin',paths);self.assertIn('/artifact/entries/0/title/text',paths)

if __name__=='__main__':unittest.main()
