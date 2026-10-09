#!/bin/bash
#SBATCH --job-name=resume-prompt-v1
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --gres=gpu:A30:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=results/prompt_engineered/slurm-%j.log
set -euo pipefail
cd /scratch/mohammedmubashir/resume-ai
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
phase=${1:?Pass smoke or benchmark}
prompt_version=${2:-grounded_v1}
exec .venv/bin/python -u eval/runners/run_prompt_engineered.py --phase "$phase" --prompt-version "$prompt_version" --run-id "${prompt_version}-${phase}-${SLURM_JOB_ID}"
