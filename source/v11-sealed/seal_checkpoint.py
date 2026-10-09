"""Immutable local checkpoint of incomplete validation; never an acceptance pass."""
import json,hashlib,zipfile,datetime
from pathlib import Path
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
local=json.loads((D/'integrity-local-checkpoint.json').read_text())
assert not local['mismatches'] and local['archive_matches']
assert all(not v['mismatches'] for v in local['local_frozen'].values())
assert all(not v['mismatches'] for v in local['prior_history'])
assert json.loads((D/'WORK_STATE.json').read_text())['state']=='BLOCKED_NETWORK_CHECKPOINT_NOT_ACCEPTED'
assert not json.loads((D/'historical-progress.json').read_text())['all_complete']
app={str(p.relative_to(D/'application')):sha(p) for p in (D/'application').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
assert app==json.loads((D/'cpu-gate.json').read_text())['application']
for p in D.rglob('*'):
 assert not p.is_symlink(),p
 assert not any(x in p.parts for x in ['fixtures','protected_evaluation','heldout','holdout','eval_snapshot']),p
files={str(p.relative_to(D)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
with (D/'SHA256SUMS.json').open('x') as f:json.dump(dict(algorithm='SHA-256',status='INCOMPLETE_NETWORK_BLOCKED_CHECKPOINT',excludes=['SHA256SUMS.json'],files=files),f,indent=2)
archive=D.parent/(D.name+'-network-blocked-checkpoint.zip')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(D.rglob('*')):
  if p.is_file():z.write(p,D.name+'/'+str(p.relative_to(D)))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(files)+1
 for name,meta in files.items():assert hashlib.sha256(z.read(D.name+'/'+name)).hexdigest()==meta['sha256'],name
 assert hashlib.sha256(z.read(D.name+'/SHA256SUMS.json')).hexdigest()==sha(D/'SHA256SUMS.json')
h=sha(archive)
with Path(str(archive)+'.sha256').open('x') as f:f.write(h+'  '+archive.name+'\n')
meta=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=h,package_files=len(files)+1,manifest_files=len(files),manifest_sha256=sha(D/'SHA256SUMS.json'),created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),zip_crc_check='PASS',every_member_sha256_check='PASS',status='INCOMPLETE_NETWORK_BLOCKED_CHECKPOINT',verdict='C — NOT READY / NO-GO FOR AGENT DEVELOPMENT',acceptance_passed=False,full_acceptance_executed=False,remote_upload_verified=False,remote_upload_blocker='Turing/network connection unavailable')
with (D.parent/(archive.stem+'-archive-metadata.json')).open('x') as f:json.dump(meta,f,indent=2)
print(json.dumps(meta,indent=2))
