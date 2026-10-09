#!/bin/bash
#SBATCH --job-name=resume-3f-resources
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
#SBATCH --time=00:05:00
#SBATCH --output=results/stage3f/resources-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
.venv/bin/python -B -m rag.reranking.resources 0
.venv/bin/python -B -m rag.reranking.resources 1
