#!/bin/bash
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --gres=gpu:A30:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --job-name=resume-s4c1-exam
#SBATCH --output=results/stage4c1/exam-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
.venv/bin/python -B -m stage4c1.final_exam "$1"
