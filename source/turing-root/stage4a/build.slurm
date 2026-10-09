#!/bin/bash
#SBATCH --job-name=resume-stage4a-build
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=results/stage4a/build-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
.venv/bin/python -B -m stage4a.runtime_inspect
.venv/bin/python -B -m stage4a.build "$1"
.venv/bin/python -B -m stage4a.validate "$1" > results/stage4a/candidate-validation.json
