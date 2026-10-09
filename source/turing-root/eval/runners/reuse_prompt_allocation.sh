#!/bin/bash
# Confirm the existing allocation's GPUs are idle before use; preserves that allocation.
set -euo pipefail
set -C
cd /scratch/mohammedmubashir/resume-ai
allocation=${1:?Usage: bash eval/runners/reuse_prompt_allocation.sh JOB_ID PHASE UNIQUE_RUN_ID}
phase=${2:?smoke or benchmark}
run_id=${3:?unique run ID}
prompt_version=${4:-grounded_v1}
[[ "$run_id" =~ ^[a-zA-Z0-9_-]+$ ]] || exit 2
[[ "$phase" == smoke || "$phase" == benchmark ]] || exit 2
mkdir -p results/prompt_engineered
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
exec /cm/shared/apps/slurm/current/bin/srun --jobid="$allocation" --overlap --ntasks=1 --cpus-per-task=4 --gres=gpu:1 --time=01:00:00 .venv/bin/python -u eval/runners/run_prompt_engineered.py --phase "$phase" --prompt-version "$prompt_version" --run-id "$run_id" > "results/prompt_engineered/${run_id}.log" 2>&1
