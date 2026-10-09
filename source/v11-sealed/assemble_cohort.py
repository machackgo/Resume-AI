"""Combine fresh shards only after exact case/input/code/configuration checks."""
import json,hashlib,shutil,sys
from pathlib import Path
D=Path(__file__).resolve().parent;target=D/sys.argv[1];names=sys.argv[2:]
assert names and not target.exists()
inputs={c['id']:c for c in json.loads((D/'inputs/benchmark.json').read_text())['cases']+json.loads((D/'inputs/stress-inputs.json').read_text())}
historical={'J20','J08','S07','J14','J09','J12','J15','S05'}
expected=set(inputs) if target.name.startswith('full-') else historical
baseline=json.loads((D.parent/'resume-ai-final-remediation-20261007/full-v7/production-model-configuration.json').read_text())
code=None;rows=[];seen=set();shards=[]
for name in names:
 run=D/name;manifest=json.loads((D/(name+'-pre-manifest.json')).read_text())
 assert all(v['matches_full_v7'] for v in manifest['inputs'].values())
 if code is None:code=manifest['application']
 else:assert code==manifest['application']
 cfg=json.loads((run/'production-model-configuration.json').read_text());assert cfg==baseline
 controls=json.loads((run/'controlled-review-results.json').read_text());assert len(controls)==8 and all(x['passed'] for x in controls)
 done=json.loads((run/'e2e-execution.json').read_text());assert not done['denied_protected_opens'] and not done['training'] and not done['adapter_promoted']
 assigned=json.loads((run/'assigned-cases.json').read_text());actual=[]
 for p in sorted([*run.glob('case-J*.json'),*run.glob('stress-S*.json')]):
  r=json.loads(p.read_text());cid=r['id'];assert cid not in seen;seen.add(cid);actual.append(cid)
  job_hash=hashlib.sha256(inputs[cid]['job_text'].encode()).hexdigest();assert r['raw_job_sha256']==job_hash
  rows.append(dict(case=cid,source=str(p.relative_to(D)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),raw_job_sha256=job_hash))
 assert set(actual)=={c['id'] for c in assigned['cases']}
 shards.append(dict(run=name,job=done['job'],controls_passed=8))
assert seen==expected,dict(missing=sorted(expected-seen),extra=sorted(seen-expected))
local={str(p.relative_to(D/'application')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (D/'application').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
assert code==local,'Local application differs from inference revision'
target.mkdir()
for row in rows:shutil.copy2(D/row['source'],target/Path(row['source']).name)
(target/'cohort-manifest.json').write_text(json.dumps(dict(cases=rows,shards=shards,application=code,input_count=len(expected),fresh_inference=True,baseline_configuration_unchanged=True),indent=2))
(target/'production-model-configuration.json').write_text(json.dumps(baseline,indent=2))
print('Assembled',len(rows),'unique fresh cases into',target.name)
