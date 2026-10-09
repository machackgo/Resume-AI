"""Read-only frozen release audit; outputs exclusively in Stage 4C-1."""
import hashlib,json,datetime,traceback
from pathlib import Path
R=Path.cwd(); O=R/'results/stage4c1/preflight'; O.mkdir(parents=True,exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(n,v): (O/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
report={'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':False,'checks':[],'optimizer_steps':0}
def check(name,items,base=R):
 bad=[]
 for p,v in items.items():
  h=v['sha256'] if isinstance(v,dict) else v
  if not (base/p).is_file() or sha(base/p)!=h:bad.append(p)
 report['checks'].append({'name':name,'files':len(items),'changed_or_missing':bad});save('integrity.json',report)
 if bad:raise RuntimeError('HARD INTEGRITY FAILURE: '+name+' '+str(bad))
try:
 check('archives',{'release/resume-ai-stage4c0-v1.tar.gz':'3e3f452ec32471ec2d22c6552e1743e86c179e0cec18f70128a2a2348fc4147d','results/stage4a-release-v1.tar.gz':'3c84bbd04035357161267095b9b2feccae5178f8541378eb832ae9466945ea18'})
 for name in ['results/stage4a/final-manifest.json','results/stage4c0/protected-manifest.json','results/stage4b/smoke/release-checksums.json']:
  check(name,json.loads((R/name).read_text()))
 a=R/'datasets/stage4a/v1'; c=R/'datasets/stage4c0/v1'
 check('stage4a dataset',{p:h for h,p in (line.split('  ',1) for line in (a/'checksums.sha256').read_text().splitlines())},a)
 check('stage4c0 dataset',json.loads((c/'checksums.json').read_text()),c)
 check('stage4c0 factory',json.loads((c/'audits/factory-freeze-v2.json').read_text())['sha256'])
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(R/'models/Qwen3.8-27B',local_files_only=True)
 from stage4a.validate import validate_release
 av=validate_release(a,tok);save('stage4a-validation.json',av)
 from stage4c0.validate import validate_records
 rows=[json.loads(l) for l in (c/'records.jsonl').read_text().splitlines()]
 cv=validate_records(rows,tok,historical_root=R,provenance_root=c/'provenance');save('stage4c0-validation.json',cv)
 if not cv['passed']:raise RuntimeError('Stage4C0 validation failed: '+str(cv['errors']))
 report['passed']=True
except Exception as e:
 report['error']=str(e);report['traceback']=traceback.format_exc()
finally:
 report['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat();save('integrity.json',report)
 print(json.dumps(report,indent=2),flush=True)
if not report['passed']:raise SystemExit(1)
