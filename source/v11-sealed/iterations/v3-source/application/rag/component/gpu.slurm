#!/bin/bash
#SBATCH --job-name=resume-stage3i-qwen
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --gres=gpu:A30:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=10:00:00
#SBATCH --output=results/stage3i/gpu-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
.venv/bin/python -m pip freeze > results/stage3i/environment.txt
nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu --format=csv -l 10 > "results/stage3i/gpu-telemetry-$SLURM_JOB_ID.csv" &
monitor_pid=$!
trap 'kill "$monitor_pid" 2>/dev/null || true' EXIT
.venv/bin/python -B -m rag.component.run
