"""Freeze prior artifacts and acquire two small pinned models in a separate cache."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/stage3f'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def protected_paths():
    for path in ROOT.rglob('*'):
        rel = path.relative_to(ROOT)
        if any(x in rel.parts for x in ('.venv', '__pycache__', '.git')):
            continue
        if any(x in rel.parts for x in ('stage3f', 'reranking', 'reranking_eval')):
            continue
        if 'stage3f' in path.name or path.name.startswith('test_reranking'):
            continue
        if path.is_file():
            yield path

def main():
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('Slurm allocation required')
    OUT.mkdir(exist_ok=True)
    manifest = OUT / 'preexisting_manifest.json'
    if not manifest.exists():
        files = {str(p.relative_to(ROOT)): sha(p) for p in sorted(protected_paths())}
        manifest.write_text(json.dumps(files, indent=2) + '\n')
        print('Frozen', len(files), 'prior files, including existing model assets', flush=True)
    else:
        assert all(sha(ROOT / p) == digest for p, digest in json.loads(manifest.read_text()).items())
    lock = OUT / 'models.lock.json'
    if lock.exists():
        raise RuntimeError('Refusing to repin an existing model lock')
    from huggingface_hub import HfApi, snapshot_download
    specs = []
    for model in ('cross-encoder/ms-marco-MiniLM-L6-v2', 'cross-encoder/ms-marco-TinyBERT-L2-v2'):
        info = HfApi().model_info(model)
        path = Path(snapshot_download(model, revision=info.sha, cache_dir=str(ROOT / 'models/stage3f'),
            allow_patterns=['config.json', 'tokenizer*.json', 'special_tokens_map.json', 'vocab.txt',
                            'model.safetensors', 'README.md', 'LICENSE*']))
        files = {str(p.relative_to(path)): sha(p) for p in path.rglob('*') if p.is_file()}
        spec = {'model': model, 'revision': info.sha, 'max_tokens': 512,
                'license': getattr(info.card_data, 'license', None),
                'download_bytes': sum(p.stat().st_size for p in path.rglob('*') if p.is_file()),
                'files_sha256': files, 'source': 'https://huggingface.co/' + model}
        specs.append(spec)
        print(json.dumps({k: v for k, v in spec.items() if k != 'files_sha256'}), flush=True)
    lock.write_text(json.dumps(specs, indent=2) + '\n')
    (OUT / 'environment.txt').write_text(subprocess.check_output([str(ROOT / '.venv/bin/pip'), 'freeze'], text=True))

if __name__ == '__main__':
    main()
