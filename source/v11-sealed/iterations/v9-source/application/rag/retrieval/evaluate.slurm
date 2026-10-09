#!/bin/bash
#SBATCH --job-name=resume-stage3e
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=results/stage3e/slurm-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
work_dir=$(mktemp -d /tmp/resume-stage3e.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B -m rag.retrieval.validate
.venv/bin/python -B -m rag.retrieval.benchmark "$work_dir/quality"
.venv/bin/python -B -m rag.retrieval.performance "$work_dir/performance"
tar -czf "results/stage3e/closed-databases-${SLURM_JOB_ID}.tar.gz" -C "$work_dir" quality performance
