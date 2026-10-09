#!/bin/bash
#SBATCH --job-name=resume-stage3e-final
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=results/stage3e/final-slurm-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
work_dir=$(mktemp -d /tmp/resume-stage3e-final.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B -m rag.retrieval.validate
.venv/bin/python -B -m rag.retrieval.replay "$work_dir"
.venv/bin/python -B -m rag.retrieval.report
