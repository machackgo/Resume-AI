import json,pathlib,shutil,subprocess,sys,tempfile,unittest
from test_metrics import DATA,SCHEMA,ROOT,oracle
from score import score,aggregate
class ArtifactTests(unittest.TestCase):
 def test_rescore_and_fence_diagnostic(self):
  with tempfile.TemporaryDirectory() as temp:
   d=pathlib.Path(temp);snap=d/'eval_snapshot'
   for name in ['datasets','schemas','metrics']:shutil.copytree(ROOT/'eval'/name,snap/name)
   raw=[];rows=[]
   for c in DATA['cases']:
    raw.append(dict(id=c['id'],text='```json\n'+json.dumps(oracle(c))+'\n```'))
    r=score(c,None,SCHEMA);r.update(id=c['id'],json_valid=False);rows.append(r)
   (d/'raw_outputs.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in raw));(d/'metrics.json').write_text(json.dumps(aggregate(rows)))
   for tool in ['rescore.py','diagnose_format.py']:
    subprocess.run([sys.executable,str(ROOT/'eval/runners'/tool),str(d)],check=True,capture_output=True)
   self.assertEqual(json.loads((d/'metrics.recomputed.json').read_text())['deterministic']['schema_valid_rate'],0)
   self.assertEqual(json.loads((d/'format_diagnostic_metrics.json').read_text())['deterministic']['schema_valid_rate'],1)
   raw[0]['text']='```json\n{bad json}\n```';(d/'raw_outputs.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in raw))
   subprocess.run([sys.executable,str(ROOT/'eval/runners/diagnose_format.py'),str(d)],check=True,capture_output=True)
   self.assertEqual(json.loads((d/'format_diagnostic_metrics.json').read_text())['deterministic']['schema_valid_rate'],7/8)
if __name__=='__main__':unittest.main()
