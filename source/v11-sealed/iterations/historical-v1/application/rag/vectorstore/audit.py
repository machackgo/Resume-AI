"""Final delivery integrity and closed-snapshot restore smoke check."""
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
from .config import StoreConfig
from .models import record_from_dict, EmbeddingSpace, VectorQuery
from .sqlite_reference import SQLiteVectorStore

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/stage3d'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''): h.update(part)
    return h.hexdigest()

def main():
    validation=json.loads((OUT/'validation.json').read_text()); assert validation['passed']
    manifest=json.loads((OUT/'preexisting_manifest.json').read_text())
    assert all((ROOT/k).is_file() and sha(ROOT/k)==v for k,v in manifest.items())
    archives=sorted(OUT.glob('closed-databases-*.tar.gz')); assert archives
    archive=archives[-1]
    name='model0-short-moderate-title-section-v1-records'
    payload=json.loads((ROOT/f'results/stage3c/{name}.json').read_text())
    record=record_from_dict(payload['records'][0]); space=EmbeddingSpace(record.config,record.input_strategy)
    with tarfile.open(archive) as tar:
        files=[m for m in tar.getmembers() if m.isfile() and m.name.endswith('.sqlite3')]
        assert len(files)==20
        members={m.name:hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in files}
        selected=[m for m in files if '/'+name+'/' in m.name]; assert len(selected)==1
        with tempfile.TemporaryDirectory(prefix='stage3d-restore-') as folder:
            root=Path(folder); path=root/Path(selected[0].name).name
            path.write_bytes(tar.extractfile(selected[0]).read()); path.chmod(0o600)
            with SQLiteVectorStore(StoreConfig(root),record.scope) as store:
                assert store.health_check().healthy and store.count()==44
                assert store.get_embedding(record.record_id).record==record
                hits=store.search_vectors(VectorQuery(space,tuple(payload['query_vectors'][0]),44))
                assert len(hits)==44
    files=[* (ROOT/'rag/vectorstore').glob('*.py'),ROOT/'rag/vectorstore/validate.slurm',
           ROOT/'migrations/001_vectorstore_sqlite.sql',ROOT/'tests/rag/test_vectorstore.py',
           ROOT/'docs/adr/vector_store_selection.md',* (ROOT/'docs').glob('stage3d*.md'),
           *OUT.glob('*')]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(files) if p.is_file() and p.name!='final_audit.json'}
    report={'passed':True,'protected_files_unchanged':len(manifest),
            'closed_archive':str(archive.relative_to(ROOT)), 'closed_databases':len(members),
            'snapshot_restore':{'passed':True,'records':44,'read_and_search':True},
            'snapshot_database_sha256':members,'artifact_sha256':hashes}
    (OUT/'final_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('artifact_sha256','snapshot_database_sha256')},indent=2))

if __name__=='__main__': main()
