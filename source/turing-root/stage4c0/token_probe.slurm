#!/bin/bash
#SBATCH --job-name=resume-stage4c0-tokens
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=results/stage4c0/tokens-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2 CUDA_VISIBLE_DEVICES=''
.venv/bin/python -B -m stage4c0.token_probe "$1" "$2"
