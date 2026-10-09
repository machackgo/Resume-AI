#!/bin/bash
#SBATCH --job-name=resume-stage3h-verify
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=results/stage3h/verify-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
work_dir=$(mktemp -d /tmp/resume-stage3h-verify.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B -m rag.scale.verify "$1" "$work_dir"
.venv/bin/python -B -m rag.scale.diagnose
.venv/bin/python -m pip freeze > results/stage3h/environment-final.txt
