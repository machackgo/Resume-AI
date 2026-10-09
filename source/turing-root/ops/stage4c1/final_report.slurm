#!/bin/bash
#SBATCH --job-name=resume-stage4c1-final-report
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=results/stage4c1/final-report-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PYTHONPATH=. .venv/bin/python -B ops/stage4c1/final_report.py "$@"
