"""Final artifact integrity audit, without loading models or rewriting old stages."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/stage3c'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    validation=json.loads((OUT/'validation.json').read_text())
    assert validation['passed']
    integration=json.loads((OUT/'local_integration.json').read_text())
    assert len(integration)==2 and all(x['passed'] for x in integration)
    manifest=json.loads((OUT/'preexisting_manifest.json').read_text())
    assert all((ROOT/k).is_file() and sha(ROOT/k)==v for k,v in manifest.items())
    assets=[]
    for spec in json.loads((OUT/'models.lock.json').read_text()):
        path=ROOT/'models/stage3c'/('models--'+spec['model'].replace('/','--'))/'snapshots'/spec['revision']
        assert all((path/k).is_file() and sha(path/k)==v for k,v in spec['files_sha256'].items())
        assets.append({'model':spec['model'],'revision':spec['revision'],'verified_files':len(spec['files_sha256'])})
    files=sorted([*(ROOT/'rag/embeddings').glob('*.py'),ROOT/'rag/embeddings/evaluate.slurm',
        *(ROOT/'tests/rag').glob('test_embedding*.py'),*(ROOT/'fixtures/rag/embedding_eval').glob('*.json'),
        *(ROOT/'docs').glob('stage3c*.md'),*OUT.glob('*.json')])
    hashes={str(p.relative_to(ROOT)):sha(p) for p in files if p.name!='final_audit.json'}
    report={'passed':True,'prior_files_unchanged':len(manifest),'models':assets,
            'integration_checks':sum(x['checks'] for x in integration),
            'artifact_hashes':hashes}
    (OUT/'final_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='artifact_hashes'},indent=2))

if __name__=='__main__': main()
