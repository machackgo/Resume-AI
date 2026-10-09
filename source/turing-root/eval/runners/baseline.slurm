#!/bin/bash
#SBATCH --job-name=resume-baseline
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --gres=gpu:A30:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=results/baseline/slurm-%j.log
set -euo pipefail
cd /scratch/mohammedmubashir/resume-ai
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4
exec .venv/bin/python -u eval/runners/run_baseline.py --run-id "base-v1-${SLURM_JOB_ID}"
