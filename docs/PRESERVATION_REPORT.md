# Resume AI — Preservation Report

Audit date: 2026-10-09. Scope: preservation only. No GPU jobs, training, inference, or writes on Turing
were performed. Turing root: `/scratch/mohammedmubashir/resume-ai` (Ceph scratch, not a Git checkout).

Labels: **VERIFIED** (checked by hash or command in this audit) · **IN PROGRESS** · **EXPERIMENTAL** · **UNKNOWN**.

## 1. Ground truth

| Item | Finding | Label |
|---|---|---|
| Latest verified application revision | v11 semantic-contracts `application/` in the sealed Oct 8 package `resume-ai-semantic-validation-20261008-final.zip` (80,189,386 B, SHA-256 `f284b393b9d6e3ae18de49b994f249f5e43d7f844f6191470bcc83ee01fd3c72`). The local copy matches its recorded hash; all 3,450 manifest members re-verified after extraction. | VERIFIED |
| Its product decision | `VALIDATION_COMPLETE_NOT_READY`: 23/30 cases pass, CPU suite 534 pass / 1 fail. Preserved as verified *source*, not verified *readiness*. | VERIFIED |
| Current development | Another session is running v12 / full-v2 acceptance: Slurm jobs 2354991 and 2354992 RUNNING, 2354993 PENDING (dependency), writing to `work/semantic-contracts-20261008/{historical-v12-shard-*,full-v2-shard-*}`; locally `~/resume-ai-gpu-acceptance-v12-20261009` and `~/resume-ai-p0-discovery-boundary-20261009`. The handoff's "queue empty" is now stale. | IN PROGRESS / EXPERIMENTAL — excluded |
| Historical root source | 400 non-bytecode files across 15 source/doc directories; newest mtime 2026-10-02; identical remote hashes before and after the copy; local copy matches. | VERIFIED |
| Sealed historical releases | `release/resume-ai-stage4c0-v1.tar.gz`, `release/resume-ai-stage4c1-final-report-20261002.tar.gz` (Turing), plus 7 local sealed ZIPs (173 MB total; 6 verify against their `.sha256`, `preagent-acceptance-20261007.zip` had no recorded hash; computed now). | VERIFIED |
| Git | None, on Turing or locally for Resume AI. No commit history exists to recover. | VERIFIED |
| GitHub | `gh` authenticated as **machackgo** (scopes `repo`, `workflow`, `read:org`, `gist`). No repository named `Resume-AI` (or any case variant) exists. | VERIFIED |

## 2. Secret and privacy audit

| Check | Result |
|---|---|
| gitleaks 8.30.1 over both staging trees | sealed-v11: 0 findings. turing-root: 1 finding (`generic-api-key` at `docs/stage3a_architecture.md:56`), confirmed **false positive**: the prose word "authentication" followed by "revocation/expiry". |
| gitleaks over the assembled repo **Git history** (commit `82156ea` before amend) | 13 findings, all reviewed **false positives**: 12 SHA-256 file digests under `tokenizer*.json` keys in `provenance/rag-models.*.lock.json`, and the prose hit above. Narrow allowlists in `.gitleaks.toml`, scoped to the `generic-api-key` rule only (canary tests confirmed GitHub-PAT and generic secrets planted in the same files are still detected); re-scan is clean. |
| Credential-bearing filenames (`.env`, `*.pem`, `id_rsa`, `.netrc`, `*credential*`) | None found outside `.venv` and models. |
| Phone numbers | None found. |
| Email addresses | Only the owner's WPI address, and only inside `inputs/candidate_sources.json` (excluded). Other matches were code decorators (`@app.get`) or `example.invalid`. |
| **Candidate personal data** | The "candidate" is the owner. `inputs/` contains full text of 2 personal resumes (`Resume_Mubashir_Faraz_v3.docx`, `Mohammed_Faraz_Master_Resume.docx`), 5 WPI coursework reports (one is a **group project**, so it may contain classmates' names), VeriBridge docs, and captures of 41 `machackgo` GitHub repositories. A 60-character shingle scan found verbatim private resume/report text in **44 review/audit files**. No code file contains it. **All 44 files and all evidence-bearing directories are excluded** (`provenance/excluded-files.json`). |
| Vector store | `inputs/candidate-vector-store/scope_1e86…sqlite3` (embeddings and text of the evidence above): excluded, category E. |
| Datasets (`datasets/stage4a`, `stage4c0`) | Manifest declares "original synthetic demonstrations, no real private candidate data"; no owner-name hits. Some curriculum/critic content was requested from a third-party model (Astra): check provider terms before any **public** release. |
| Usernames / paths | `/scratch/mohammedmubashir`, `/Users/mohammedmubashiruddinfaraz` appear in code and docs. Acceptable for a private repo. |

## 3. Proposed GitHub inventory (`machackgo/Resume-AI`, PRIVATE)

3,013 source files (~24.7 MB) plus provenance/docs/tools. Every file is listed with its SHA-256 in `provenance/SOURCE_SHA256SUMS.txt`.

| Area | Files | Notes |
|---|---:|---|
| `source/v11-sealed/application/` | 195 | latest verified pipeline: `resume_pipeline/`, `rag/`, `stage4b/`, migrations, schema |
| `source/v11-sealed/iterations/*/application` | 2,136 | v1–v11 code lineage (heavy duplication; Git deduplicates blobs) |
| `source/v11-sealed/*` top level | ~280 | harness `.py`, `.sbatch`, `FINAL_REPORT.txt`, `REPRODUCE.txt`, gates, metrics JSON < 300 KB, minus the 44 private-text files |
| `source/turing-root/` | 400 | historical root source, docs, contracts, tests, scenarios, `PROJECT_HANDOFF.md`, `.venv/pyvenv.cfg` |
| Excluded | 46 | 44 private-text files, 2 binary release tarballs |

Explicitly **not** pushed: weights, adapters, `training_state.pt`, datasets, SQLite stores, raw case outputs/traces, `remote-run-auxiliary/`, `forensics/`, `inputs/`, `.venv`, bytecode, v12/full-v2 work.

## 4. Model and artifact inventory

Sizes come from Ceph `rbytes` (no full reads). Hashes come from existing manifests cross-checked in this audit; nothing large was re-hashed during the GPU jobs.

| ID | Location (Turing root) | Size | SHA-256 / identity | Class | Destination | Status |
|---|---|---:|---|---|---|---|
| Base Qwen3.8-27B | `models/Qwen3.8-27B` (18 shards) | 55.6 GB | **`Qwen/Qwen3.8-27B` @ `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`**, Apache-2.0, ungated. All 18 local shard SHA-256 (computed Oct 3) equal upstream LFS SHA-256 (queried today). | A | none; re-download by revision | VERIFIED re-downloadable. Resolves handoff Open Question 1 |
| Tokenizer/config/chat template | same dir | 23 MB | `tokenizer.json` sha256 matches upstream; chat template `c3cf9e34…`; in lock file | A | GitHub (`provenance/`) for config + index | VERIFIED |
| Stage 4C-1 checkpoints | `adapters/stage4c1/run_430001/{interleaved,evidence_only}/checkpoint_*` (31) | 977 MB | `provenance/adapter-inventory.json`; 224/224 files match the Oct 3 frozen manifest | **B + C**: each holds LoRA weights (21 MB) **and** `training_state.pt` (11 MB: PagedAdamW8bit state, scheduler, Python/Torch/CUDA RNG, plan/config hashes) | HF private model repo | NOT YET BACKED UP |
| Mixed step-124 (failed endpoint) | `…/interleaved/checkpoint_000124` | 32 MB | adapter `cc4f…`; manifest digest `6adcf247…` | B, C | HF (priority 1) | NOT YET BACKED UP |
| Evidence-only step-131 | `…/evidence_only/checkpoint_000131` | 32 MB | manifest digest `e6dbded0…` | B, C | HF (priority 1) | NOT YET BACKED UP |
| Stage 4B smoke adapter | `adapters/stage4b_smoke` | 21 MB | in inventory | B | HF | NOT YET BACKED UP |
| Embeddings MiniLM / E5 | `models/stage3c` | 226 MB | pinned revisions `1110a243…` / `ffb93f3b…`, present upstream (Apache-2.0 / MIT) | A | optional HF mirror | VERIFIED re-downloadable |
| Rerankers MiniLM-CE / TinyBERT | `models/stage3f` | 110 MB | `233902d2…` / `81d1926f…`, present upstream (Apache-2.0) | A | optional HF mirror | VERIFIED re-downloadable |
| Training/eval datasets | `datasets/stage4a` (v1 + 5 candidates), `datasets/stage4c0/v1` | 173 MB | per-release `manifest.json` | B (synthetic, self-authored) | HF private dataset | NOT YET BACKED UP |
| Experiment results | `results/` (stage reports, metrics, raw outputs, Slurm logs) | 546 MB | per-stage manifests | B | HF private dataset | NOT YET BACKED UP (only the handful of decision/lock files are in GitHub) |
| Completed work packages | `work/` minus v12/full-v2 | ~1.52 GB | per-package manifests | B; contains candidate evidence → E | HF private dataset (gated on approval) | NOT YET BACKED UP |
| Sealed ZIPs (local Mac) | `~/resume-ai-*.zip` ×7 | 173 MB | `provenance/sealed-archives.json` | B; contain candidate evidence → E | HF private dataset | LOCAL ONLY (1 copy on the Mac + Turing originals) |
| Candidate evidence / vector store | `inputs/`, `candidate-vector-store/*.sqlite3` | ~19 MB | in sealed manifests | **E**: owner PII + coursework | owner decision | NOT YET BACKED UP off-Turing except inside local ZIPs |
| RAG embeddings/index | `inputs/embedding-records.json`, scoped SQLite | in sealed ZIP | sealed manifest | D (regenerable from captures + pinned MiniLM) and E | with sealed ZIP | LOCAL ONLY |
| Python venv | `.venv` | 6.3 GB | `provenance/environment/requirements-turing-venv.freeze.txt` (83 pins, Python 3.11.12) | D (rebuild; cluster CUDA wheels make the bytes non-portable) | GitHub (freeze) | VERIFIED freeze captured |
| v12 / full-v2 runs | `work/semantic-contracts-20261008/{historical-v12-*,full-v2-*}` | 180 MB, growing | — | EXPERIMENTAL | after the other session seals them | BLOCKED (active) |

**Unique data to preserve off-Turing:** about 3.4 GB (adapters 1.0 + datasets 0.17 + results 0.55 + completed work 1.52 + ZIPs 0.17), or 3.8 GB with an optional RAG model mirror. The base model (55.6 GB) and venv (6.3 GB) do not need copying.

## 5. Hugging Face backup architecture (proposed, not executed)

- **`machackgo/resume-ai-adapters`** (private *model* repo). Layout mirrors `adapters/`, so `checkpoint_*` dirs keep `adapter_model.safetensors` + `training_state.pt` + configs + `checksums.json`. Model card states the base `Qwen/Qwen3.8-27B@1d4bf0f2`, the GitHub source commit, and "NOT PROMOTED". Each upload is one HF commit; tag `stage4c1-run430001-final`.
- **`machackgo/resume-ai-artifacts`** (private *dataset* repo): `datasets/`, `results/`, `work/` (completed only), `sealed-archives/*.zip`. Subfolder `restricted/` holds category-E items only if you approve.
- `.pt` pickles are flagged as unsafe by HF scanners; that is expected for `training_state.pt`. Never load them from untrusted sources.
- **Licensing:** Qwen is Apache-2.0, so publishing derived adapters is permitted (keep the LICENSE and NOTICE). MiniLM/E5/cross-encoders are Apache/MIT. The datasets are self-authored synthetic, but third-party-model-generated curriculum text needs a provider-terms check **before any public release**; private storage is fine.
- **University:** Turing is a WPI resource. The artifacts are your own coursework/research products, with no export-controlled models. Check the WPI ARC acceptable-use policy and any course-project data rules. The group-project PDF may contain classmates' content: keep it in `restricted/` or omit it.
- **Storage:** about 3.4–3.8 GB, well within HF private storage. Check your quota at hf.co/settings/storage.
- **Blocker:** `hf auth whoami` shows *Not logged in*. You would need to run `! hf auth login` yourself (token never shown to me).
- **Defense in depth (recommended):** follow 3-2-1. Copy (1) Turing originals, (2) the Mac, (3) HF, plus optionally an external drive or Google Drive for the restricted ZIPs. HF should not be the only off-cluster copy of PII.

## 6. Why GitHub alone is not enough (and other fundamentals)

- **GitHub is for text history, not tensors.** Git stores every version of every file forever and diffs line by line. Multi-GB binaries break that (100 MB file limit, LFS quotas), and code alone cannot reproduce learned behaviour.
- **Model weights** are the learned function: billions of numbers set by training. The base Qwen weights are someone else's training run and can be re-downloaded by revision hash. Your contribution is the *delta*.
- **LoRA adapters** store that delta compactly. Instead of changing a 5120×5120 matrix W, training learns two thin matrices B (5120×8) and A (8×5120) so that the effective weight is W + (α/r)·BA. You trained 5.24 M parameters (0.019 % of the base) in 64 attention projections, which is why each adapter is 21 MB. An adapter is only meaningful on top of the *exact* base revision it was trained against, which is why the base lock records `1d4bf0f2`.
- **Optimizer states** matter for *resuming*, not for inference. AdamW keeps running first and second moments per parameter. Restarting from weights alone resets them, so the next updates behave differently. `training_state.pt` also stores scheduler and RNG states, and `train.py` asserts fingerprint equality on restore. With it you can continue step-for-step; without it you can only start a new run from the adapter.
- **Reproducible environments:** results depend on library versions (torch 2.14, transformers 5.17, peft 0.21, bitsandbytes 0.50.2), CUDA, and hardware. The freeze file pins Python packages. CUDA/driver/GPU class (A30) must be recorded separately. NF4 kernels and float ordering can make bit-exact replay hardware-dependent.
- **Source ↔ model linkage:** a model version is only interpretable with the code that trained it, the data it saw, the base it sits on, and the evaluator that judged it. Here that chain is: GitHub commit (code) → `training_config.json` + `plan_sha256` (data order) → base lock (weights) → adapter checksum → result manifests.
- **Restoration testing:** an upload exit code proves bytes left the machine, not that they can be retrieved, are complete, and still work. Only download + hash compare + load + smoke test proves recoverability.

## 7. Remaining risks

1. **Unique artifacts exist only on Turing:** adapters (incl. training states), datasets, results, and completed work (~3.3 GB). This is the highest risk.
2. Sealed ZIPs exist only on Turing + one Mac disk. No off-site copy.
3. The active v12 work will change the "latest" state. It needs its own sealing and a follow-up backup once the other session finishes.
4. The environment has never been rebuilt from the freeze. Reproducibility is UNKNOWN until tested.
5. Upstream Qwen could be withdrawn or made gated. Mitigation: optionally mirror the 55.6 GB base privately; that is a cost/benefit decision for you.
6. HF CLI not authenticated. PII placement policy undecided.
7. `PROJECT_HANDOFF.md` still lists the base upstream as UNKNOWN and the queue as empty. Both are superseded by this report.
