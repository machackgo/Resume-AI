#!/bin/bash
#SBATCH --job-name=resume-stage4c1-audit
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:30:00
#SBATCH --output=results/stage4c1/preflight-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 CUDA_VISIBLE_DEVICES=''
.venv/bin/python -B -m stage4c1.preflight
