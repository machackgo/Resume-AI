#!/bin/bash
#SBATCH --job-name=resume-stage4b-final-audit
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --nodelist=gpu-4-23
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:30:00
#SBATCH --output=results/stage4b/final-audit-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=410042 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 STAGE4A_DATASET=datasets/stage4a/v1 CUDA_VISIBLE_DEVICES=''
.venv/bin/python -B -m stage4b.regression
.venv/bin/python -B -m stage4b.verify
.venv/bin/python -B -m stage4b.report
