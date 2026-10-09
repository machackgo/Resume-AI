"""Package new Stage4B artifacts only after successful independent verification."""
import json,tarfile,re
from pathlib import Path
from stage4b.prepare import sha
R=Path.cwd();O=R/'results/stage4b/smoke';A=R/'adapters/stage4b_smoke'
assert json.loads((O/'independent-verification.json').read_text())['passed']
combined=json.loads((O/'protected-manifest.json').read_text())
for historical in ['results/stage4a/protected-manifest.json','results/stage4a/final-manifest.json']:
 for p,h in json.loads((R/historical).read_text()).items():
  assert p not in combined or combined[p]==h
  combined[p]=h
assert len(combined)==json.loads((O/'protected-verification.json').read_text())['files']
(O/'combined-protected-manifest.json').write_text(json.dumps(combined,sort_keys=True,indent=2)+'\n')
counts={}
for name in ['stage4b-tests','stage4a-tests','stage3_tests','stage1_stage2_tests']:
 log=(O/(name+'.log')).read_text();assert log.rstrip().endswith('OK');counts[name]=int(re.search(r'Ran (\d+) tests?',log).group(1))
(O/'test-results.json').write_text(json.dumps(dict(counts=counts,total=sum(counts.values()),passed=True,gpu_integration='runtime assertions and independent-verification.json'),sort_keys=True,indent=2)+'\n')
paths=[]
for folder in ['stage4b','results/stage4b','adapters/stage4b_smoke']:
 paths.extend(p for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='release-checksums.json')
manifest={str(p.relative_to(R)):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)}
(O/'release-checksums.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
archive=R/'results/stage4b-release-v1.tar.gz';assert not archive.exists()
with tarfile.open(archive,'w:gz') as t:
 for folder in ['stage4b','results/stage4b','adapters/stage4b_smoke']:t.add(R/folder,arcname=folder,filter=lambda i:None if '__pycache__' in i.name else i)
archive.with_suffix(archive.suffix+'.sha256').write_text(sha(archive)+'  '+archive.name+'\n')
print('Stage4B packaged',archive,'files',len(manifest),'tests',sum(counts.values()),flush=True)
