#!/bin/bash
#SBATCH --job-name=resume-stage3i-verify
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=results/stage3i/verify-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
work_dir=$(mktemp -d /tmp/resume-stage3i-verify.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B -m rag.component.score results/stage3i/benchmark-2333661 > results/stage3i/scoring.log
.venv/bin/python -B -m rag.component.verify results/stage3i/benchmark-2333661 "$work_dir"
