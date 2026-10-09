#!/bin/bash
#SBATCH --job-name=resume-stage4a-verify
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:45:00
#SBATCH --output=results/stage4a/verify-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
export STAGE4A_DATASET="$1"
.venv/bin/python -B -m unittest discover -s tests/stage4a -v > results/stage4a/stage4a-tests.log 2>&1
.venv/bin/python -B -m stage4a.regression
