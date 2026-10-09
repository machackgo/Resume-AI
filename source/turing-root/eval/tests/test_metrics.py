import copy,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'eval/metrics'))
from score import score,valid,aggregate
DATA=json.loads((ROOT/'eval/datasets/resume_v1.json').read_text());SCHEMA=json.loads((ROOT/'eval/schemas/analysis_v1.json').read_text())
def oracle(c):
 g=copy.deepcopy(c['gold']);return dict(requirements=g['requirements'],skills=g['skills'],matches=g['matches'],claims=[{k:v for k,v in x.items() if k!='text'} for x in g['claims']],missing_requirements=[x['requirement'] for x in g['matches'] if x['label']!='SUPPORTED'],bullets=[dict(text=x['text'],claim_ids=[x['id']],evidence_ids=x['evidence_ids']) for x in g['claims'] if x['id'] in g['bullets']],refused_claim_ids=[x['id'] for x in g['claims'] if x['label']!='SUPPORTED'])
class Tests(unittest.TestCase):
 def test_oracles(self):
  for c in DATA['cases']:
   r=score(c,oracle(c),SCHEMA);self.assertTrue(r['schema_valid']);self.assertEqual(r['claims_label_accuracy'],1);self.assertEqual(r['missing_requirements']['f1'],1);self.assertIn(r['grounded_bullet_rate'],[1,None])
 def test_invalid(self):
  for p in [None,[],{},'bad']:
   r=score(DATA['cases'][0],p,SCHEMA);self.assertFalse(r['schema_valid']);self.assertEqual(r['requirements']['recall'],0)
 def test_unsupported(self):
  c=DATA['cases'][0];p=oracle(c);p['bullets']=[dict(text='Managed ten engineers.',claim_ids=['C3'],evidence_ids=[])];r=score(c,p,SCHEMA);self.assertEqual(r['unsupported_claim_rate'],1);self.assertEqual(r['grounded_bullet_rate'],0)
 def test_wrong_citation(self):
  c=DATA['cases'][0];p=oracle(c);p['bullets'][0]['evidence_ids']=['E999'];self.assertLess(score(c,p,SCHEMA)['grounded_bullet_rate'],1)
 def test_duplicate_id(self):
  c=DATA['cases'][0];p=oracle(c);p['claims'].append(dict(id='C1',label='UNKNOWN',evidence_ids=[]));self.assertEqual(score(c,p,SCHEMA)['claims_label_accuracy'],0)
 def test_extra_requirement(self):
  c=DATA['cases'][0];p=oracle(c);p['requirements'].append('phd');self.assertLess(score(c,p,SCHEMA)['requirements']['precision'],1)
 def test_no_vacuous_grounding(self):
  c=DATA['cases'][0];p=oracle(c);p['bullets']=[];r=score(c,p,SCHEMA);self.assertIsNone(r['grounded_bullet_rate']);self.assertEqual(r['bullet_claim_selection']['recall'],0)
 def test_gold_consistency(self):
  for c in DATA['cases']:
   ids={x['id'] for x in c['evidence']}
   for x in c['gold']['claims']+c['gold']['matches']:self.assertTrue(set(x['evidence_ids'])<=ids)
   self.assertEqual(set(c['gold']['requirements']),{x['requirement'] for x in c['gold']['matches']})
if __name__=='__main__':unittest.main()
