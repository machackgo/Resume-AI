import copy,hashlib,json,pathlib,sys,tempfile,unittest
from test_metrics import ROOT,DATA,SCHEMA,oracle
from score import score,valid
sys.path.insert(0,str(ROOT/'eval/runners'))
from prompt_contract import build_messages,strict_parse,create_run_dir
from promotions_v1 import promotion_metrics
class Stage2Tests(unittest.TestCase):
 def test_strict_json_and_fences(self):
  p=oracle(DATA['cases'][0]);text=json.dumps(p)
  parsed,error=strict_parse(text);self.assertIsNone(error);self.assertTrue(valid(parsed,SCHEMA))
  for wrapped in ['```json\n'+text+'\n```','Here is JSON: '+text,text+' Done.']:
   parsed,error=strict_parse(wrapped);self.assertIsNotNone(error);self.assertFalse(score(DATA['cases'][0],parsed,SCHEMA)['schema_valid'])
 def test_unknown_and_partial_promotions(self):
  predictions={c['id']:oracle(c) for c in DATA['cases']}
  predictions['unknown']['claims'][0]['label']='SUPPORTED';predictions['unknown']['skills']=['python']
  predictions['partial']['matches'][0]['label']='SUPPORTED';predictions['partial']['skills'].append('production_ml')
  m=promotion_metrics(DATA['cases'],predictions,SCHEMA,valid)
  self.assertEqual(m['UNKNOWN']['labels_promoted_to_supported'],1);self.assertEqual(m['UNKNOWN']['requirement_ids_asserted_as_skills'],1)
  self.assertEqual(m['PARTIALLY_SUPPORTED']['labels_promoted_to_supported'],1);self.assertEqual(m['PARTIALLY_SUPPORTED']['requirement_ids_asserted_as_skills'],1)
 def test_invalid_is_not_zero_promotion_success(self):
  m=promotion_metrics(DATA['cases'],{},SCHEMA,valid)
  self.assertIsNone(m['UNKNOWN']['label_promotion_rate']);self.assertEqual(m['schema_valid_cases'],0)
 def test_unsupported_partial_unknown_bullets(self):
  for case_id,claim_id in [('direct_metrics','C3'),('partial','C1'),('unknown','C1')]:
   c=next(x for x in DATA['cases'] if x['id']==case_id);p=oracle(c);g=next(x for x in c['gold']['claims'] if x['id']==claim_id)
   p['bullets']=[dict(text=g['text'],claim_ids=[claim_id],evidence_ids=g['evidence_ids'])]
   self.assertEqual(score(c,p,SCHEMA)['unsupported_claim_rate'],1)
 def test_prompt_has_no_gold_answers_or_case_ids(self):
  c=copy.deepcopy(DATA['cases'][0]);d=ROOT/'eval/prompts/grounded_v1';a=build_messages(c,SCHEMA,['python'],d)
  c['id']='SECRET_CASE_ID';c['gold']['requirements']=['SECRET_GOLD'];c['gold']['skills']=['SECRET_SKILL'];c['gold']['matches']=[];c['gold']['bullets']=[]
  for item in c['gold']['claims']:item['label']='SECRET_LABEL';item['evidence_ids']=['SECRET_EVIDENCE']
  self.assertEqual(a,build_messages(c,SCHEMA,['python'],d))
  payload=json.loads(a[1]['content']);self.assertEqual(set(payload),{'task_instruction','candidate_evidence','job_description','candidate_request','proposed_claims','vocabulary','output_schema'})
 def test_all_prompt_versions_avoid_benchmark_specific_facts(self):
  for folder in (ROOT/'eval/prompts').glob('grounded_v*'):
   text=(folder/'system.txt').read_text()+(folder/'task.txt').read_text()
   for c in DATA['cases']:
    self.assertNotIn('"id": '+json.dumps(c['id']),text)
    for fact in c['evidence']:self.assertNotIn(fact['text'],text)
   self.assertEqual(build_messages(DATA['cases'][0],SCHEMA,['python'],folder),build_messages(DATA['cases'][0],SCHEMA,['python'],folder))
 def test_original_controlled_files_unchanged(self):
  expected={'eval/datasets/resume_v1.json':'7cb6959f5014d07134dc1d66863f2afd965814229df4a9db08876fde2e6c4e0c','eval/schemas/analysis_v1.json':'9b7a470596f53d94881b258e1ca889f1bf5ed346c02795904e9d2fec07e3fa68','eval/metrics/score.py':'a11a903778032c9cf9404a2414c95f411885e10efddf8b9db3403d356b47bd9e','eval/prompts/base_v1.txt':'ac27a13df38f9a82be43669466dc1d2606e8a056773ce9d54dc7d29e8e597e0f'}
  for path,h in expected.items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
 def test_run_output_is_exclusive_and_reproducible(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=create_run_dir(tmp,'test-run');p.joinpath('raw_outputs.jsonl').write_text('{"preserved":true}\n')
   with self.assertRaises(FileExistsError):create_run_dir(tmp,'test-run')
   self.assertEqual(p.joinpath('raw_outputs.jsonl').read_text(),'{"preserved":true}\n')
   self.assertFalse(pathlib.Path(tmp,'results/baseline').exists())
   for bad in ['../baseline','/tmp/out','..','']:
    with self.assertRaises(ValueError):create_run_dir(tmp,bad)
 def test_smoke_separate_from_benchmark(self):
  smoke=json.loads((ROOT/'eval/experiments/stage2/smoke_v1.json').read_text())
  self.assertFalse({c['id'] for c in smoke['cases']}&{c['id'] for c in DATA['cases']})
if __name__=='__main__':unittest.main()
