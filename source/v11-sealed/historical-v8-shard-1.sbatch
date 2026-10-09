#!/bin/bash
#SBATCH --job-name=semantic-contracts-history
#SBATCH --partition=academic
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/mohammedmubashir/resume-ai/work/semantic-contracts-20261008/historical-v8-shard-1/historical-%j.log
set -euo pipefail
cd /scratch/mohammedmubashir/resume-ai
export RESUME_REPAIR_RUN_DIR=/scratch/mohammedmubashir/resume-ai/work/semantic-contracts-20261008/historical-v8-shard-1
export HISTORICAL_SHARD=1
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
.venv/bin/python -B -c 'import json,pathlib,os; assert json.loads((pathlib.Path(os.environ["RESUME_REPAIR_RUN_DIR"])/"cpu-gate.json").read_text())["passed"]'
.venv/bin/python -B "$RESUME_REPAIR_RUN_DIR/run_historical_shard.py"
