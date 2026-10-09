#!/bin/bash
#SBATCH --job-name=resume-stage3j-verify
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=results/stage3j/verify-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
work_dir=$(mktemp -d /tmp/resume-stage3j-verify.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B -m rag.deep.score "$1"
.venv/bin/python -B -m rag.deep.verify "$1" "$work_dir"
.venv/bin/python -B -m rag.deep.verify_extra "$work_dir/diagnostics"
