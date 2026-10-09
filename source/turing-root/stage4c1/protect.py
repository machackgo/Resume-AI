"""Post-experiment protected-file verification, without rewriting old artifacts."""
import json,datetime
from pathlib import Path
from stage4c1.evaluate import sha,write
R=Path.cwd()
def main():
    assert (R/'results/stage4c1/development_frozen.json').exists()
    sources=[('results/stage4a/final-manifest.json',R,None),
             ('results/stage4c0/protected-manifest.json',R,None),
             ('results/stage4b/smoke/release-checksums.json',R,None),
             ('datasets/stage4c0/v1/checksums.json',R/'datasets/stage4c0/v1',None),
             ('datasets/stage4c0/v1/audits/factory-freeze-v2.json',R,'sha256')]
    reports=[]
    archives={'release/resume-ai-stage4c0-v1.tar.gz':'3e3f452ec32471ec2d22c6552e1743e86c179e0cec18f70128a2a2348fc4147d',
              'results/stage4a-release-v1.tar.gz':'3c84bbd04035357161267095b9b2feccae5178f8541378eb832ae9466945ea18'}
    reports.append({'manifest':'explicit frozen archive hashes','files':len(archives),'changed_or_missing':[p for p,h in archives.items() if not (R/p).is_file() or sha(R/p)!=h]})
    for source,base,key in sources:
        manifest=json.loads((R/source).read_text());manifest=manifest[key] if key else manifest
        bad=[]
        for name,v in manifest.items():
            expected=v['sha256'] if isinstance(v,dict) else v;p=base/name
            if not p.is_file() or sha(p)!=expected:bad.append(name)
        reports.append({'manifest':source,'files':len(manifest),'changed_or_missing':bad})
    a=R/'datasets/stage4a/v1';bad=[];count=0
    for line in (a/'checksums.sha256').read_text().splitlines():
        h,p=line.split('  ',1);count+=1
        if not (a/p).is_file() or sha(a/p)!=h:bad.append(p)
    reports.append({'manifest':'datasets/stage4a/v1/checksums.sha256','files':count,'changed_or_missing':bad})
    result={'passed':all(not x['changed_or_missing'] for x in reports),'checks':reports,
            'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    write(R/'results/stage4c1/final_protection.json',result)
    print(json.dumps(result,indent=2));assert result['passed'],'HARD ARTIFACT INTEGRITY FAILURE'
if __name__=='__main__':main()
