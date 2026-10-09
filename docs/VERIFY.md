# Verification Checklist

A backup is VERIFIED only after an independent retrieval plus a hash comparison. Upload success is not evidence.

## A. Before publication (local)
- [ ] `gitleaks dir .` and `gitleaks git .` → no findings other than the documented false positive
- [ ] `python3 tools/verify_snapshot.py` → 3013/3013
- [ ] No file > 5 MB; no `*.safetensors`, `*.pt`, `*.sqlite3`, `*.zip`, `*.tar.gz` tracked: `git ls-files | grep -E '\.(safetensors|pt|sqlite3|zip|tar\.gz)$'` is empty
- [ ] Private-text shingle scan of tracked files → 0 hits

## B. GitHub (after push)
- [ ] `gh repo view machackgo/Resume-AI --json visibility,owner` → `PRIVATE`, `machackgo`
- [ ] `git ls-remote origin main` equals the local `git rev-parse HEAD`
- [ ] Fresh clone into an empty temp dir → `git fsck --full` clean → `tools/verify_snapshot.py` 3013/3013 → `git rev-parse HEAD` equals the recorded commit
- [ ] Annotated tag `v11-sealed-20261008` present remotely

## C. Hugging Face (after upload, when approved)
- [ ] Repos are private (`hf repo info` / API `private: true`)
- [ ] Download to an empty dir → `verify_snapshot.py --adapters-dir` all match; dataset files equal `sealed-archives.json` and per-package manifests
- [ ] Record HF commit SHAs in `provenance/` and commit to GitHub (links source revision ↔ artifact revision)

## D. Restoration correctness (on future GPU infra)
- [ ] `docs/RESTORE.md` steps 1–10 pass; CPU regression reproduces the recorded counts exactly
- [ ] Adapter loads onto base `1d4bf0f2` with no missing/unexpected LoRA keys
- [ ] Training-state restore passes `train.py` fingerprint asserts (dry resume, zero optimizer steps)
