#!/bin/bash
#SBATCH --job-name=resume-stage4c0-protect
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --output=results/stage4c0/protect-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
.venv/bin/python -B -m stage4c0.protect before
