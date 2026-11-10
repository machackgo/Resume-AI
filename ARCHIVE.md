# Resume AI — Preserved Source Snapshot

Archived research snapshot (v11, Oct 2026), kept for provenance.
This snapshot holds **source code, documentation, and provenance only**. Model weights, adapters,
training states, datasets, raw evaluation outputs, and candidate evidence are stored elsewhere and
are referenced here by SHA-256 (see `docs/PRESERVATION_REPORT.md`).

## Status of what is in this repository

| Path | Content | Status |
|---|---|---|
| `source/v11-sealed/` | Code, harness scripts, and non-private reports from the sealed October 8 semantic-validation package (`resume-ai-semantic-validation-20261008-final.zip`, SHA-256 `f284b393…3fc72`). `application/` is the latest **verified** pipeline revision (v11). `iterations/*/application` holds the v1–v11 source lineage. | VERIFIED source; pipeline decision is **NOT READY / NO-GO** (23/30 cases pass; see `FINAL_REPORT.txt`) |
| `source/turing-root/` | Historical project root from the cluster scratch workspace: `rag/`, `stage4a/`, `stage4b/`, `stage4c0/`, `stage4c1/`, `eval/`, `contracts/`, `docs/`, `tests/`, `migrations/`, `ops/`, `scenarios/`, `research/`, `fixtures/`, `PROJECT_HANDOFF.md` | VERIFIED byte-identical to Turing (400 files, hashed before and after copy) |
| `provenance/` | Base-model lock (Qwen/Qwen3.8-27B @ `1d4bf0f2`), adapter checksums (32 checkpoints), RAG model locks, venv package freeze, sealed-archive hashes, exclusion list, per-file `SOURCE_SHA256SUMS.txt` | VERIFIED |
| `docs/` | Preservation report, restoration runbook, verification checklist | — |
| `tools/verify_snapshot.py` | Re-verifies source, base model, and adapters against the recorded hashes | — |

**Not in this snapshot:** v12 / full-v2 work that was running on Turing on 2026-10-09 (EXPERIMENTAL, unfinished).

## Quick verification

```bash
python3 tools/verify_snapshot.py
```

There is no single root entry point. The current pipeline lives in `source/v11-sealed/application/`
(`python -B -m resume_pipeline …`, GPU-only, see `docs/RESTORE.md`). The `source/turing-root/`
tree is the historical stage-by-stage code and must not be confused with it.
