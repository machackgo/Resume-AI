#!/bin/bash
#SBATCH --job-name=resume-stage4c1-train
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --gres=gpu:A30:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --signal=B:USR1@180
#SBATCH --output=results/stage4c1/train-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8
student_pid=''
stop_requested=0
trap 'stop_requested=1; if [ -n "$student_pid" ]; then kill -USR1 "$student_pid" 2>/dev/null || true; fi' USR1 TERM
run_phase() {
 .venv/bin/python -B -m stage4c1.train "$1" "$2" &
 student_pid=$!
 while kill -0 "$student_pid" 2>/dev/null; do
  nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv,noheader >> "results/stage4c1/health-${SLURM_JOB_ID}.csv"
  /cm/shared/apps/slurm/current/bin/squeue -h -j "$SLURM_JOB_ID" -o '%i %T %M %L' >> "results/stage4c1/slurm-health-${SLURM_JOB_ID}.txt"
  df -Pk . >> "results/stage4c1/disk-health-${SLURM_JOB_ID}.txt"
  du -sk "adapters/stage4c1" >> "results/stage4c1/disk-health-${SLURM_JOB_ID}.txt" 2>/dev/null || true
  sleep 30 & wait $! || true
 done
 wait "$student_pid"
}
run_phase "$1" "$2"
if [ "$stop_requested" -eq 0 ] && [ -f "results/stage4c1/$1/engineering_restart_required.json" ] && [ ! -f "results/stage4c1/$1/needs_teacher_review_$(printf '%06d' "$2").json" ]; then
 run_phase "$1" "$2"
fi
