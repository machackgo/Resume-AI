"""One-time public model acquisition. Pin revisions before any inference."""
import hashlib
import json
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'results/stage3c'
SPECS = [('sentence-transformers/all-MiniLM-L6-v2',256,'',''),
         ('intfloat/e5-small-v2',512,'passage: ','query: ')]


def main():
    lock = OUT/'models.lock.json'
    if lock.exists():
        raise RuntimeError('model lock already exists; never silently repin')
    specs = []
    for model,limit,document,query in SPECS:
        info = HfApi().model_info(model)
        path = Path(snapshot_download(model, revision=info.sha, cache_dir=str(ROOT/'models/stage3c'),
            allow_patterns=['*.json','*.txt','*.safetensors','README.md','LICENSE','LICENSE.txt'],
            ignore_patterns=['onnx/*','openvino/*']))
        files = {str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in path.rglob('*') if p.is_file()}
        specs.append({'model':model,'revision':info.sha,'max_tokens':limit,
                      'document_prefix':document,'query_prefix':query,
                      'license':getattr(info.card_data,'license',None),
                      'download_bytes':sum(p.stat().st_size for p in path.rglob('*') if p.is_file()),
                      'files_sha256':files})
    lock.write_text(json.dumps(specs,indent=2)+'\n')

if __name__=='__main__':
    main()
