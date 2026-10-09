#!/bin/bash
#SBATCH --job-name=resume-stage3i-cpu
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=results/stage3i/prepare-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
work_dir=$(mktemp -d /tmp/resume-stage3i.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B -m unittest discover -s tests/rag -v > results/stage3i/cpu-tests.log 2>&1
.venv/bin/python -B -m unittest discover -s eval/tests -v > results/stage3i/prior-eval-tests.log 2>&1
.venv/bin/python -B -m rag.component.prepare "$work_dir"
