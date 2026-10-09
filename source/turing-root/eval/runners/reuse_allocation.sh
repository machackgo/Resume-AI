#!/bin/bash
# Run only after checking the allocation's GPUs are idle. Does not end allocation.
set -euo pipefail
cd /scratch/mohammedmubashir/resume-ai
allocation=${1:?Usage: bash eval/runners/reuse_allocation.sh JOB_ID RUN_ID}
run_id=${2:?Provide a unique run ID}
mkdir -p results/baseline
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
exec /cm/shared/apps/slurm/current/bin/srun --jobid="$allocation" --overlap --ntasks=1 --cpus-per-task=4 --gres=gpu:1 --time=01:00:00 .venv/bin/python -u eval/runners/run_baseline.py --run-id "$run_id" > "results/baseline/${run_id}.log" 2>&1
