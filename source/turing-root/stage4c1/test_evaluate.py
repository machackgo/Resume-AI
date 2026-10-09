import json,copy,unittest
from pathlib import Path
from stage4c1.evaluate import score_evidence,score_professional
class EvalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.a=[json.loads(l) for l in Path('datasets/stage4a/v1/train.jsonl').read_text().splitlines()]
  cls.c=[json.loads(l) for l in Path('datasets/stage4c0/v1/train.jsonl').read_text().splitlines()]
 def test_gold_evidence(self):
  for r in self.a:
   s=score_evidence(r,r['messages'][2]['content']);self.assertTrue(s['schema_valid']);self.assertFalse(s['errors']);self.assertEqual(s['atomic_correct'],s['atomic_total']);self.assertEqual(s['predicted'],s['expected'])
 def test_gold_professional(self):
  for r in self.c:
   s=score_professional(r,r['messages'][2]['content']);self.assertTrue(s['schema_valid']);self.assertFalse(s['errors']);self.assertTrue(s['semantic_critic_pending'])
 def test_invalid_outputs(self):
  for text in ['{}','not json','{"label":"SUPPORTED","label":"UNKNOWN"}','[]','null']:
   self.assertFalse(score_evidence(self.a[0],text)['schema_valid']);self.assertFalse(score_professional(self.c[0],text)['schema_valid'])
 def test_schema_label_cannot_receive_credit(self):
  r=self.a[0];s=score_evidence(r,json.dumps({'label':r['metadata']['expected_label']}));self.assertEqual(s['predicted'],'INVALID');self.assertFalse(s['contract_valid'])
 def test_contract_invalid_cannot_receive_credit(self):
  r=self.a[0];p=json.loads(r['messages'][2]['content']);p['information_need_id']='wrong';s=score_evidence(r,json.dumps(p));self.assertEqual(s['predicted'],'INVALID');self.assertFalse(s['contract_valid']);self.assertEqual(s['atomic_correct'],0)
 def test_fabrication(self):
  r=next(r for r in self.a if r['metadata']['expected_label']=='SUPPORTED');p=json.loads(r['messages'][2]['content']);p['atomic_claims'][0]['evidence_ids']=['invented'];p['evidence_ids']=['invented']
  s=score_evidence(r,json.dumps(p));self.assertGreater(s['fabricated_ids'],0);self.assertLess(s['valid_citations'],s['citations']);self.assertTrue(s['errors'])
 def test_unknown_promotion(self):
  r=next(r for r in self.a if r['metadata']['expected_label']=='UNKNOWN');p=json.loads(r['messages'][2]['content']);p['label']='SUPPORTED';p['atomic_claims'][0]['label']='SUPPORTED'
  s=score_evidence(r,json.dumps(p));self.assertGreater(s['unsupported_positive_atoms'],0);self.assertTrue(s['errors'])
 def test_partial_to_supported_is_overclaim(self):
  # Frozen TRAIN uses PARTIAL at compound aggregate level, not atomic level.
  # This in-memory unit fixture tests the counter boundary, never training data.
  r=copy.deepcopy(next(r for r in self.a if not r['metadata']['compound'] and r['metadata']['expected_label']=='SUPPORTED'))
  gold=json.loads(r['messages'][2]['content']);gold['label']='PARTIALLY_SUPPORTED';gold['atomic_claims'][0]['label']='PARTIALLY_SUPPORTED';gold['missing_evidence']=['Additional required support.'];r['messages'][2]['content']=json.dumps(gold)
  p=copy.deepcopy(gold);p['label']='SUPPORTED';p['atomic_claims'][0]['label']='SUPPORTED'
  s=score_evidence(r,json.dumps(p));self.assertGreater(s['overclaimed_atoms'],0)
  self.assertEqual(score_evidence(r,r['messages'][2]['content'])['overclaimed_atoms'],0)
 def test_application_route(self):
  r=next(r for r in self.c if r['metadata']['task']=='ANSWER_APPLICATION_QUESTION');p=json.loads(r['messages'][2]['content']);p['task']='DRAFT_OUTREACH'
  self.assertFalse(score_professional(r,json.dumps(p))['schema_valid'])
if __name__=='__main__':unittest.main()
