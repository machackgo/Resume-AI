"""Read-only checks of retained sealed archives and the prior full-v7 outputs."""
import json
import subprocess
from pathlib import Path
from transport import SSH_OPTIONS

D = Path(__file__).resolve().parent
receipts = list(D.parent.glob('resume-ai*-remote-archive-verification.json'))
receipts.append(D/'checkpoint-remote-archive-verification.json')
archives = {}
for path in receipts:
    r = json.loads(path.read_text())
    remote = r.get('remote_archive')
    expected = r.get('expected_sha256', r.get('sha256'))
    if remote and expected:
        assert remote.startswith('/scratch/mohammedmubashir/resume-ai/work/')
        assert len(expected) == 64
        archives[remote] = expected
prior = D.parent/'resume-ai-final-remediation-20261007'
transfer = json.loads((prior/'transfer-full-v7-final.json').read_text())
root = '/scratch/mohammedmubashir/resume-ai/work/final-semantic-remediation-20261007/full-v7/'
raw = {root+k:v for k,v in transfer['remote_hashes'].items()}
spec = {**archives, **raw}
script = '''import json,hashlib
from pathlib import Path
spec=SPEC
actual={}
for name in spec:
 h=hashlib.sha256()
 with Path(name).open('rb') as f:
  for block in iter(lambda:f.read(8388608),b''):h.update(block)
 actual[name]=h.hexdigest()
print(json.dumps(actual))
'''.replace('SPEC',repr(spec))
p = subprocess.run(['ssh',*SSH_OPTIONS,'mohammedmubashir@turing.wpi.edu','python3'],
                   input=script,text=True,capture_output=True,timeout=180)
p.check_returncode()
actual = json.loads(p.stdout)
bad = [k for k,v in spec.items() if actual.get(k)!=v]
result = dict(known_sealed_archives_checked=len(archives),prior_full_v7_files=len(raw),
              mismatches=bad,archives={k:actual[k] for k in archives},
              prior_full_v7_matches=all(actual.get(k)==v for k,v in raw.items()),
              receipt_sources=[str(p) for p in receipts])
print(json.dumps(result,indent=2))
assert not bad
