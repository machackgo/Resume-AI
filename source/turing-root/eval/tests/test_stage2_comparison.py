import hashlib,json,pathlib,shutil,subprocess,sys,tempfile,unittest
from test_metrics import ROOT,DATA,SCHEMA,oracle
from score import score,aggregate
class ComparisonTest(unittest.TestCase):
 def test_comparison_is_read_only_and_preserves_strict_metrics(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);base=root/'baseline';candidate=root/'candidate'
   for run,fenced in [(base,True),(candidate,False)]:
    run.mkdir();snapshot=run/'eval_snapshot'
    for name in ['datasets','schemas','metrics']:shutil.copytree(ROOT/'eval'/name,snapshot/name)
    cfg={k:None for k in ['model_path','quantization','generation_overrides','seed','thinking','dependencies','model_metadata_hashes','weight_manifest','model_class','generation_defaults']};cfg.update(status='complete',load_seconds=1)
    (run/'config.json').write_text(json.dumps(cfg));raw=[];rows=[]
    for c in DATA['cases']:
     p=oracle(c);text=json.dumps(p)
     if fenced:text='```json\n'+text+'\n```'
     raw.append(dict(id=c['id'],text=text,input_tokens=1,output_tokens=1,seconds=1,peak_gpu_bytes=[1],hit_token_limit=False))
     r=score(c,None if fenced else p,SCHEMA);r.update(id=c['id'],json_valid=not fenced);rows.append(r)
    (run/'raw_outputs.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in raw));(run/'metrics.json').write_text(json.dumps(aggregate(rows)))
   hashes=lambda:{str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file()}
   before=hashes()
   subprocess.run([sys.executable,str(ROOT/'eval/runners/compare_stage2.py'),'--baseline',str(base),'--candidate',str(candidate)],check=True,capture_output=True)
   self.assertEqual(before,hashes())
   result=json.loads((candidate/'comparison/comparison.json').read_text())
   self.assertEqual(result['baseline']['strict']['metrics']['deterministic']['schema_valid_rate'],0)
   self.assertEqual(result['baseline']['fence_diagnostic']['metrics']['deterministic']['schema_valid_rate'],1)
   self.assertEqual(result['prompt_engineered']['strict']['metrics']['deterministic']['schema_valid_rate'],1)
   self.assertIsNone(result['baseline']['strict']['promotions']['UNKNOWN']['label_promotion_rate'])
if __name__=='__main__':unittest.main()
