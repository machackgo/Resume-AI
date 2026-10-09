#!/bin/bash
#SBATCH --job-name=resume-stage3h-qwen
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --gres=gpu:A30:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=results/stage3h/gpu-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
.venv/bin/python -m pip freeze > results/stage3h/environment-initial.txt
.venv/bin/python -B -m unittest discover -s tests/rag -v > results/stage3h/prefreeze-tests.log 2>&1
nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu --format=csv -l 10 > "results/stage3h/gpu-telemetry-$SLURM_JOB_ID.csv" &
monitor_pid=$!
trap 'kill "$monitor_pid" 2>/dev/null || true' EXIT
.venv/bin/python -B -m rag.scale.run
