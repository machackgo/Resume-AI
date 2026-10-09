#!/bin/bash
#SBATCH --job-name=resume-stage3d
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:15:00
#SBATCH --output=results/stage3d/slurm-%j.log
set -euo pipefail
umask 077
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
work_dir=$(mktemp -d /tmp/resume-stage3d.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
.venv/bin/python -B -m rag.vectorstore.replay write "$work_dir/replay"
.venv/bin/python -B -m rag.vectorstore.replay read "$work_dir/replay"
.venv/bin/python -B -m rag.vectorstore.benchmark "$work_dir/scale"
.venv/bin/python -B -m rag.vectorstore.validate
# All connections have closed; archived copies are transport/backups, never live on Ceph.
tar -czf "results/stage3d/closed-databases-${SLURM_JOB_ID}.tar.gz" -C "$work_dir" replay scale
printf '%s\n' 'Stage 3D validation and closed database archive complete.'
