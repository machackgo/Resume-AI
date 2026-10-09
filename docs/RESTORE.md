# Disaster Recovery Runbook

Goal: rebuild Resume AI on new GPU infrastructure from GitHub + Hugging Face + upstream models.
Each step names its verification. A step is not complete until its check passes.

| # | Step | Command / action | Verification |
|---|---|---|---|
| 1 | Clone | `gh repo clone machackgo/Resume-AI && cd Resume-AI` | `git log -1` shows the recorded snapshot commit (see `docs/VERIFY.md`) |
| 2 | Checkout verified revision | `git checkout <snapshot-commit-or-tag v11-sealed-20261008>` | `python3 tools/verify_snapshot.py` reports 3013/3013 |
| 3 | Python environment | Python **3.11.12**; `python -m venv .venv && .venv/bin/pip install -r provenance/environment/requirements-turing-venv.freeze.txt` (CUDA-matched torch wheel; Turing used CUDA 13.0) | `pip check`; versions equal the freeze; record `nvidia-smi` and torch CUDA build |
| 4 | Base model | `hf download Qwen/Qwen3.8-27B --revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0 --local-dir models/Qwen3.8-27B` | `python3 tools/verify_snapshot.py --model-dir models/Qwen3.8-27B` (18/18 shards + tokenizer) |
| 5 | Adapters + training states | `hf download machackgo/resume-ai-adapters --local-dir adapters` (after backup exists) | `python3 tools/verify_snapshot.py --adapters-dir adapters`; manifests equal `provenance/adapter-inventory.json` |
| 6 | RAG assets | Embedder `sentence-transformers/all-MiniLM-L6-v2@1110a243…` (and ablations per `provenance/rag-models.*.lock.json`); knowledge base = `inputs/` from the sealed v11 ZIP (restricted artifact store) | ZIP SHA-256 equals `provenance/sealed-archives.json`; sealed `SHA256SUMS.json` 3450/3450 |
| 7 | External services | None required for the recorded BASE path (offline HF; SQLite snapshot copied to local temp). Set `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, run wrapper variables per `source/v11-sealed/*.sbatch`. No secrets in repo. | Wrapper dry review; no network required at inference |
| 8 | Checksums | Steps 2, 4, 5, 6 | all pass |
| 9 | CPU regression | Copy `source/v11-sealed` to a fresh dir; import-only `DiscoveryLicenseBoundary` recipe (`PROJECT_HANDOFF.md` §13), then `run_tests.py` in the fresh copy | Expected on v11: boundary 2 pass / 1 fail; suite 534 pass, 1 fail, 46 skips, 3 protected-blocked |
| 10 | GPU smoke | One A30-class (≥24 GB) GPU: load BASE NF4 via `resume_pipeline.runtime.BaseQwen`, one short greedy generation; then load `checkpoint_000124` with PEFT and check adapter fingerprint | Loads without missing/unexpected keys; peak VRAM ≈ historical (< 22 GiB) |
| 11 | Resume training (only if separately authorized) | `stage4c1/train.py` resume path loads `adapter_model.safetensors` + `training_state.pt` | Its built-in asserts: optimizer/scheduler fingerprint equality, `resume_verified_*.json` written |

## What cannot be restored today

- Adapters, training states, datasets, results, completed work packages: **not yet off Turing**. Steps 5, 6 (restricted part), and 11 are blocked until the HF / second-copy backup is done.
- Bit-exact environment: never rebuilt from the freeze. Step 3 is unproven.
- v12 / full-v2 experiments: not preserved (in progress at snapshot time).
- Upstream withdrawal of Qwen3.8-27B would break step 4 unless a private mirror exists.
