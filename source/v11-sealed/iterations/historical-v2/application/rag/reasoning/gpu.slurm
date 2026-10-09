#!/bin/bash
#SBATCH --job-name=resume-stage3g-qwen
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --gres=gpu:A30:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --output=results/stage3g/gpu-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
# Smoke then wait for reviewed, frozen configuration. No inference on login nodes.
.venv/bin/python -B -m rag.reasoning.run smoke
while [ ! -f results/stage3g/freeze_v2.json ]; do sleep 15; done
.venv/bin/python -B -m rag.reasoning.run benchmark
