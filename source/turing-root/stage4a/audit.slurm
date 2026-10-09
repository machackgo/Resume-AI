#!/bin/bash
#SBATCH --job-name=resume-stage4a-release-audit
#SBATCH --account=cs541
#SBATCH --partition=academic
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:10:00
#SBATCH --output=results/stage4a/release-audit-%j.log
set -euo pipefail
cd "$HOME/scratch/resume-ai"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
.venv/bin/python -B -m stage4a.validate datasets/stage4a/v1 > results/stage4a/independent-validation.json
.venv/bin/python -B - <<'PY'
import json,hashlib
from pathlib import Path
root=Path.cwd()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((root/'results/stage4a/final-manifest.json').read_text())
bad=[p for p,h in m.items() if sha(root/p)!=h]
assert not bad,bad
release=root/'datasets/stage4a/v1'
for line in (release/'checksums.sha256').read_text().splitlines():
 h,name=line.split('  ',1);assert sha(release/name)==h
assert json.loads((root/'results/stage4a/independent-validation.json').read_text())['passed']
(root/'results/stage4a/delivery-audit.json').write_text(json.dumps(dict(passed=True,final_manifest_files=len(m),changed=[],independent_validator_passed=True,release_manifest_sha256=sha(release/'manifest.json'),all_release_checksums_valid=True),indent=2)+'\n')
print('INDEPENDENT FROZEN RELEASE AUDIT PASSED')
PY
