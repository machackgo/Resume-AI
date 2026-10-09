#!/bin/bash
#SBATCH --job-name=resume-stage3h-prep
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=results/stage3h/prepare-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
work_dir=$(mktemp -d /tmp/resume-stage3h-prep.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B - <<'PY'
from rag.scale.prepare import ROOT,OUT,dump,sha
p=OUT/'preexisting_manifest.json'
if not p.exists():
    files={str(f.relative_to(ROOT)):sha(f) for f in sorted(ROOT.rglob('*')) if f.is_file() and not any(x in f.parts for x in ('.venv','__pycache__','.git','stage3h','scale')) and 'stage3h' not in f.name and f.name!='test_scale.py'}
    dump(p,files);print('Protected',len(files),flush=True)
PY
.venv/bin/python -B -m unittest discover -s tests/rag -v > results/stage3h/initial-stage3-tests.log 2>&1
.venv/bin/python -B -m unittest discover -s eval/tests -v > results/stage3h/initial-stage1-stage2-tests.log 2>&1
.venv/bin/python -B -m rag.scale.prepare "$work_dir"
