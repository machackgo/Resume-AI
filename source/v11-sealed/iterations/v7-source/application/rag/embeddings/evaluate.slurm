#!/bin/bash
#SBATCH --job-name=resume-stage3c
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=results/stage3c/slurm-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONHASHSEED=0
.venv/bin/python -B -u -m rag.embeddings.benchmark --model-index 0
.venv/bin/python -B -u -m rag.embeddings.benchmark --model-index 1
