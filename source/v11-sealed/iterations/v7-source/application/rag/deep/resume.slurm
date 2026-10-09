#!/bin/bash
#SBATCH --job-name=resume-stage3j-cpu
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=results/stage3j/resume-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
work_dir=$(mktemp -d /tmp/resume-stage3j-prepare.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B -m rag.deep.resume "$work_dir"
