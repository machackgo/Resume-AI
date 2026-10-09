#!/bin/bash
#SBATCH --job-name=resume-stage3g-prep
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:45:00
#SBATCH --output=results/stage3g/prepare-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
work_dir=$(mktemp -d /tmp/resume-stage3g-prep.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B - <<'PY'
from rag.reasoning.prepare import ROOT,OUT,dump
from rag.reranking.prepare import sha
p=OUT/'preexisting_manifest.json'
if not p.exists():
    files={str(f.relative_to(ROOT)):sha(f) for f in sorted(ROOT.rglob('*')) if f.is_file() and not any(x in f.parts for x in ('.venv','__pycache__','.git','stage3g','reasoning','reasoning_eval')) and 'stage3g' not in f.name and not f.name.startswith('test_reasoning')}
    dump(p,files)
    print('Protected',len(files),'files',flush=True)
PY
.venv/bin/python -B -m rag.reasoning.prepare "$work_dir/prepared"
