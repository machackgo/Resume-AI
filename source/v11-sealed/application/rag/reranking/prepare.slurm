#!/bin/bash
#SBATCH --job-name=resume-3f-prepare
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:25:00
#SBATCH --output=results/stage3f/prepare-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
.venv/bin/python -B -m rag.reranking.prepare
