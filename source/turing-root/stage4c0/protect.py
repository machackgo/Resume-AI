"""Read-only verification of inherited manifests; outputs only in Stage 4C-0."""
import hashlib,json,sys
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''): h.update(block)
    return h.hexdigest()

def main():
    root=Path.cwd(); out=root/'results/stage4c0';out.mkdir(parents=True,exist_ok=True)
    phase=sys.argv[1] if len(sys.argv)>1 else 'before'
    paths=['results/stage4b/smoke/combined-protected-manifest.json',
           'results/stage4b/smoke/release-checksums.json']
    if phase!='before': paths.append('results/stage4c0/protected-manifest.json')
    merged={}; reports=[]
    for name in paths:
        manifest=json.loads((root/name).read_text());bad=[]
        for p,v in manifest.items():
            expected=v['sha256'] if isinstance(v,dict) else v
            if p in merged and merged[p]!=expected: raise ValueError('inconsistent inherited manifest '+p)
            merged[p]=expected
            if not (root/p).is_file() or sha(root/p)!=expected: bad.append(p)
        reports.append(dict(manifest=name,files=len(manifest),changed_or_missing=bad))
    report=dict(phase=phase,checks=reports,passed=not any(x['changed_or_missing'] for x in reports))
    (out/(phase+'-protection.json')).write_text(json.dumps(report,indent=2)+'\n')
    if not report['passed']: raise SystemExit('protected artifact mismatch')
    if phase=='before':
        for directory in ['stage4b','adapters/stage4b_smoke']:
            for p in (root/directory).rglob('*'):
                if p.is_file() and '__pycache__' not in p.parts:merged[str(p.relative_to(root))]=sha(p)
        (out/'protected-manifest.json').write_text(json.dumps(merged,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(passed=True,protected_files=len(merged),phase=phase)),flush=True)

if __name__=='__main__': main()
