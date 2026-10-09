#!/bin/bash
#SBATCH --job-name=resume-3f-final
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=results/stage3f/final-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
work_dir=$(mktemp -d /tmp/resume-stage3f-replay.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B -m rag.reranking.replay "$work_dir"
.venv/bin/python -B -m rag.reranking.validate
