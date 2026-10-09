#!/bin/bash
#SBATCH --job-name=resume-stage3f
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:25:00
#SBATCH --output=results/stage3f/evaluate-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
work_dir=$(mktemp -d /tmp/resume-stage3f.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B -m rag.reranking.validate --no-audit
.venv/bin/python -B -m rag.reranking.evaluator "$work_dir/identity"
.venv/bin/python -B -m rag.reranking.evaluator "$work_dir/minilm" 0
.venv/bin/python -B -m rag.reranking.evaluator "$work_dir/tinybert" 1
tar -czf "results/stage3f/closed-databases-${SLURM_JOB_ID}.tar.gz" -C "$work_dir" .
