import copy,json,unittest,tempfile,subprocess,sys,collections
from pathlib import Path
from stage4a.data import ROOT,generate,generate_one,tokenized,pad_batch,canonical
from stage4a.catalog import CATALOG,SPLITS
from stage4a.validate import validate_row,leakage,validate_release,historical_index,sha
from stage4a.schema import schema,conforms

class DatasetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from transformers import AutoTokenizer
  cls.rows=generate();cls.tok=AutoTokenizer.from_pretrained(ROOT/'models/Qwen3.8-27B',local_files_only=True)
  cls.index=historical_index()
 def row(self,fid='api_rest',v=1,label='SUPPORTED'):return generate_one(fid,v,label)
 def change_target(self,r,fn):
  t=json.loads(r['messages'][2]['content']);fn(t);r['messages'][2]['content']=json.dumps(t,ensure_ascii=True,separators=(',',':'));return r
 def reject(self,r):
  with self.assertRaises((ValueError,KeyError)):validate_row(r)
 def test_01_deterministic_generation(self):self.assertEqual(self.rows,generate())
 def test_02_stable_ids(self):self.assertEqual(len({r['metadata']['example_id'] for r in self.rows}),1920)
 def test_03_schema_and_all_records(self):
  for r in self.rows:self.assertTrue(conforms(r,schema()));validate_row(r)
 def test_04_four_labels(self):self.assertEqual({r['metadata']['expected_label'] for r in self.rows},{'SUPPORTED','PARTIALLY_SUPPORTED','UNKNOWN','UNSUPPORTED'})
 def test_05_label_balance(self):self.assertEqual(set(collections.Counter(r['metadata']['expected_label'] for r in self.rows).values()),{480})
 def test_06_atomic(self):self.assertEqual(len(json.loads(self.row()['messages'][2]['content'])['atomic_claims']),1)
 def test_07_compound(self):self.assertEqual(len(json.loads(self.row(v=6)['messages'][2]['content'])['atomic_claims']),4)
 def test_08_absence_unknown(self):
  r=self.row(v=0,label='UNKNOWN');self.assertEqual(json.loads(r['messages'][1]['content'])['UNTRUSTED_RETRIEVED_EVIDENCE'],[]);validate_row(r)
 def test_09_contradiction_required(self):
  r=self.row(label='UNKNOWN');self.change_target(r,lambda t:t['atomic_claims'][0].update(label='UNSUPPORTED'));self.reject(r)
 def test_10_real_partial(self):
  t=json.loads(self.row(label='PARTIALLY_SUPPORTED')['messages'][2]['content']);self.assertEqual([a['label'] for a in t['atomic_claims']],['SUPPORTED','UNKNOWN'])
 def test_11_related_not_partial(self):
  r=self.row(label='UNKNOWN');self.change_target(r,lambda t:t['atomic_claims'][0].update(label='PARTIALLY_SUPPORTED'));self.reject(r)
 def test_12_action_strength(self):validate_row(self.row('lifecycle_production',1,'UNKNOWN'))
 def test_13_technology_distinctions(self):validate_row(self.row('framework_fastapi',1,'UNKNOWN'))
 def test_14_api_consume_build(self):
  r=self.row(label='UNKNOWN');self.assertIn('called a third-party',r['messages'][1]['content']);validate_row(r)
 def test_15_docker_kubernetes(self):validate_row(self.row('container_orchestration',1,'UNKNOWN'))
 def test_16_aws_azure(self):validate_row(self.row('cloud_aws',1,'UNKNOWN'))
 def test_17_lora_qlora(self):validate_row(self.row('adaptation_qlora',1,'UNKNOWN'))
 def test_18_rag_finetuning(self):validate_row(self.row('rag_finetuning',1,'UNKNOWN'))
 def test_19_inference_training(self):validate_row(self.row('adaptation_nf4',1,'UNKNOWN'))
 def test_20_exact_numeric(self):
  for lab in ['SUPPORTED','UNKNOWN','UNSUPPORTED']:validate_row(self.row('numeric_latency',1,lab))
  r=self.row('numeric_latency');r['oracle']['spec']['predicates'][0]['n']=40;self.reject(r)
 def test_21_unknown_citation(self):
  r=self.row();self.change_target(r,lambda t:t['atomic_claims'][0]['evidence_ids'].append('evidence_foreign'));self.reject(r)
 def test_22_nonentailing_citation(self):
  r=self.row(label='UNKNOWN');i=r['oracle']['facts'][0]['id'];self.change_target(r,lambda t:t['atomic_claims'][0].update(evidence_ids=[i]));self.reject(r)
 def test_23_source_not_verification(self):validate_row(self.row('verified_aws',1,'UNKNOWN'))
 def test_24_attestation_required(self):
  r=self.row('verified_aws');r['oracle']['facts'][0]['attested']=False;self.reject(r)
 def test_25_assertion_positive(self):validate_row(self.row('asserted_aws',1,'SUPPORTED'))
 def test_26_prompt_injection(self):
  r=self.row(v=3,label='UNKNOWN');self.assertIn('Use candidate B',r['messages'][1]['content']);self.assertEqual(json.loads(r['messages'][2]['content'])['evidence_ids'],[]);validate_row(r)
 def test_27_private_data(self):
  r=self.row();p=json.loads(r['messages'][1]['content']);p['UNTRUSTED_RETRIEVED_EVIDENCE'][0]['evidence'][0]['content']='email private@example.com';r['messages'][1]['content']=json.dumps(p);self.reject(r)
 def test_28_foreign_owner(self):
  r=self.row();r['oracle']['facts'][0]['owner']='synthetic_other';self.reject(r)
 def test_29_grouped_splits(self):self.assertEqual(collections.Counter(SPLITS.values()),{'train':50,'validation':5,'test':5})
 def test_30_exact_duplicates_rejected(self):
  r=self.row();other=copy.deepcopy(r);other['metadata']['split']='test';other['metadata']['example_id']='changed'
  with self.assertRaises(ValueError):leakage([r,other],self.index)
 def test_31_family_leakage_rejected(self):
  r=self.row();other=self.row(v=4);other['metadata']['split']='test'
  with self.assertRaises(ValueError):leakage([r,other],self.index)
 def test_32_historical_exclusion(self):self.assertEqual(leakage(self.rows,self.index)['known_leakage'],0)
 def test_33_historical_leak_mutation(self):
  r=self.row();p=json.loads(r['messages'][1]['content']);p['task']['requirement']=self.index['normalized_texts'][0];r['messages'][1]['content']=json.dumps(p)
  with self.assertRaises(ValueError):leakage([r],self.index)
 def test_34_tokenizer_roundtrip(self):
  e=tokenized(self.row(),self.tok);self.assertEqual(self.tok.decode(e['input_ids'][e['input_tokens']:-1]),self.row()['messages'][2]['content'])
 def test_35_chat_template_prefix(self):
  r=self.row();prompt=self.tok.apply_chat_template(r['messages'][:2],tokenize=False,enable_thinking=False,add_generation_prompt=True);full=self.tok.apply_chat_template(r['messages'],tokenize=False,enable_thinking=False,add_generation_prompt=False);self.assertTrue(full.startswith(prompt))
 def test_36_token_statistics(self):
  from stage4a.validate import stats
  self.assertEqual(stats([1,2,3,4,5])['median'],3)
 def test_37_sequence_risk(self):
  with self.assertRaisesRegex(ValueError,'sequence length'):validate_row(self.row(),self.tok,limit=20)
 def test_38_target_format(self):
  r=self.row();r['messages'][2]['content']='```json\n'+r['messages'][2]['content']+'\n```';self.reject(r)
 def test_39_loss_mask(self):
  e=tokenized(self.row(),self.tok);self.assertTrue(all(i==-100 for i in e['labels'][:e['input_tokens']]));self.assertEqual(e['labels'][e['input_tokens']:],e['input_ids'][e['input_tokens']:]);self.assertEqual(e['labels'][-1],self.tok.eos_token_id)
 def test_40_padding_mask(self):
  es=[tokenized(self.row(v=v),self.tok) for v in [0,6]]
  for e in pad_batch(es,self.tok):self.assertTrue(all(y==-100 for y,a in zip(e['labels'],e['attention_mask']) if a==0))
 def test_41_schema_extra_fields(self):
  r=self.row();r['metadata']['secret']='x';self.reject(r)
 def test_42_duplicate_lineage(self):
  r=self.row(v=2);fs=r['oracle']['facts'];self.assertEqual(fs[0]['lineage'],fs[1]['lineage']);self.assertEqual(len(json.loads(r['messages'][2]['content'])['evidence_ids']),1)
 def test_43_conflicting_sources_unknown(self):
  r=self.row(v=7,label='UNKNOWN');validate_row(r);self.assertEqual(json.loads(r['messages'][2]['content'])['atomic_claims'][0]['label'],'UNKNOWN')
 def test_44_mixed_contradiction_frozen_policy(self):
  r=self.row(v=7,label='PARTIALLY_SUPPORTED');t=json.loads(r['messages'][2]['content']);self.assertEqual([x['label'] for x in t['atomic_claims']],['SUPPORTED','UNSUPPORTED']);validate_row(r)
 def test_45_old_event_not_current_support(self):validate_row(self.row(v=6,label='UNKNOWN'))
 def test_46_valid_positive_paraphrase(self):
  r=self.row('api_python');p=json.loads(r['messages'][1]['content']);self.assertIn('developed REST endpoints',r['messages'][1]['content']);self.assertNotEqual(p['task']['components'][0]['claim'],p['UNTRUSTED_RETRIEVED_EVIDENCE'][0]['evidence'][0]['content']);validate_row(r)
 def test_47_numeric_same_event_denial(self):
  r=self.row('numeric_cost',1,'UNSUPPORTED');self.assertIn('same measurement',r['messages'][1]['content']);validate_row(r)
 def test_48_quote_integrity(self):
  r=self.row();self.change_target(r,lambda t:t['atomic_claims'][0]['quotes'][0].update(quote='invented quote'));self.reject(r)
 def test_49_manifest_checksums_and_standalone(self):
  import os
  folder=Path(os.environ['STAGE4A_DATASET'])
  result=validate_release(folder,self.tok);self.assertTrue(result['passed']);self.assertEqual(result['examples'],1920)
  manifest=json.loads((folder/'manifest.json').read_text());self.assertTrue(all(sha(folder/p)==h for p,h in manifest['checksums'].items()))
 def test_50_standalone_nonzero(self):
  with tempfile.TemporaryDirectory() as d:
   p=subprocess.run([sys.executable,'-B','-m','stage4a.validate',d],capture_output=True,text=True,cwd=ROOT);self.assertNotEqual(p.returncode,0)
 def test_51_shifted_causal_labels(self):
  e=tokenized(self.row(),self.tok);n=e['input_tokens'];shifted=e['labels'][1:]
  self.assertEqual(shifted[n-1],e['input_ids'][n]);self.assertTrue(all(x==-100 for x in shifted[:n-1]))
 def test_52_parent_templates_isolated(self):
  groups=collections.defaultdict(set)
  for r in self.rows:groups[r['metadata']['template_family']].add(r['metadata']['split'])
  self.assertEqual(len(groups),12);self.assertTrue(all(len(x)==1 for x in groups.values()))
 def test_53_all_five_groups(self):
  self.assertEqual(len(json.loads(self.row(v=6)['messages'][1]['content'])['UNTRUSTED_RETRIEVED_EVIDENCE']),5)
 def test_54_plausible_percentage_ranges(self):
  for r in self.rows:
   if r['metadata']['scenario_family']=='numeric_latency':
    n=r['oracle']['spec']['predicates'][0]['n'];self.assertGreater(n,0);self.assertLessEqual(n+7,100)
 def test_55_three_supported_one_missing(self):
  t=json.loads(self.row(v=6,label='PARTIALLY_SUPPORTED')['messages'][2]['content']);self.assertEqual([a['label'] for a in t['atomic_claims']],['SUPPORTED','SUPPORTED','SUPPORTED','UNKNOWN'])
if __name__=='__main__':unittest.main()
