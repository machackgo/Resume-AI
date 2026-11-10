# Provenance of the showcase code

The curated package `resume_ai/` was assembled from two sources. Nothing in it was written from
scratch except where a row says **new**. Personal data was never copied. Adaptations are limited to
import paths, file locations, replacing hard-coded candidate data with a `Profile` loaded from JSON,
and removing candidate-specific logic.

| Key | Source | Commit |
|---|---|---|
| **A** | This repository, `source/v11-sealed/application/` (the sealed v11 pipeline snapshot) | `df293c1a27f6f6561752e73f30aed691dc449206` (tag `v11-sealed-20261008`) |
| **B** | This repository, `source/turing-root/fixtures/rag/` (synthetic test fixtures) | `df293c1a27f6f6561752e73f30aed691dc449206` |
| **C** | The author's private `resume-ai-control-center` repository (not published), committed tree only | `80be8976ba284d1fb0797ef9db3c46b3b71016b8` |

Modes: **verbatim** = byte-identical copy. **imports** = only `from rag.` changed to `from resume_ai.rag.`.
**adapted** = changes listed in the notes column and in the module docstring. **new** = written for this showcase.

## `resume_ai/rag/` — from A unless noted

| File | Source path | Mode | Notes |
|---|---|---|---|
| `__init__.py`, `domain.py`, `ingestion.py`, `adapters.py` | `rag/<same>` | verbatim | |
| `chunking/{__init__,models,policy,chunker,metrics,demo}.py` | `rag/chunking/<same>` | verbatim | |
| `embeddings/{__init__,base,models,input_builder,cache,similarity,local}.py` | `rag/embeddings/<same>` | verbatim | `local.py` is the pinned MiniLM provider; needs torch + transformers + a local model |
| `vectorstore/{__init__,base,config,models}.py` | `rag/vectorstore/<same>` | verbatim | |
| `vectorstore/sqlite_reference.py` | `rag/vectorstore/sqlite_reference.py` | adapted | `SCHEMA` path now points next to the module |
| `vectorstore/001_vectorstore_sqlite.sql` | `migrations/001_vectorstore_sqlite.sql` | verbatim | moved into the package |
| `retrieval/{__init__,models,service,lexical,fusion,query,evaluator}.py` | `rag/retrieval/<same>` | verbatim | |
| `reranking/{__init__,base,models,input_builder}.py` | `rag/reranking/<same>` | verbatim | |
| `reasoning/{__init__.py,schema.json,system_v2.txt}` | `rag/reasoning/<same>` | verbatim | |
| `reasoning/contract.py` | `rag/reasoning/contract.py` | adapted | `ROOT` points at the module directory so `schema.json` / `system_v2.txt` resolve inside the package |
| `component/{__init__,retrieve,benchmark}.py` | `rag/component/<same>` | verbatim | |
| `component/decompose.py` | `rag/component/decompose.py` | adapted | `resume_pipeline.semantic_contracts` import now `...grounding.semantic_contracts` |
| `demo.py` | `rag/demo.py` | adapted | fixture paths point at `resume_ai/rag/fixtures/` |
| `fixtures/resume.md`, `fixtures/sources.json` | B: `fixtures/rag/<same>` | verbatim | synthetic (`example.invalid` URLs) |

Not copied from A (kept only in the archive): `rag/{deep,scale,reranking/evaluator…,reasoning/run…,embeddings/benchmark…}`
experiment runners, all `*.slurm` files, `stage4a/4b`, and the GPU pipeline `resume_pipeline/` (except `semantic_contracts.py`).
They depend on Slurm, the Turing cluster layout, local model weights or protected evaluation data.

## `resume_ai/grounding/`

| File | Source | Mode | Notes |
|---|---|---|---|
| `semantic_contracts.py` | A: `resume_pipeline/semantic_contracts.py` | verbatim | |
| `profile.py` | C: `resume_ai/evidence.py` | adapted | Keeps the status lattice (VERIFIED / ATTESTED / IN_PROGRESS / PLANNED / DISPUTED), provenance-per-item rule and derived views. All candidate data and candidate-specific eligibility rules removed; the same schema is loaded from JSON and validated on load. New optional `gaps` / `hard_gaps` fields replace the engine's former hard-coded gap list. |
| `validate.py` | C: `resume_ai/validate.py` | adapted | Same four checks and the same `check_answers` placeholder rule; banned patterns, allowed numbers and evidence come from the `Profile`; candidate-specific allowed tokens and answer filtering removed; numbers are checked in sorted order so reported issues are deterministic. |
| `documents.py` | C: `resume_ai/docs.py` | adapted | DOCX resume and letter builders unchanged in layout; header/roles/items from `Profile`; output filename prefix derived from the profile name (was hard-coded). PDF rendering (LibreOffice / headless Chromium + a macOS Swift PDFKit helper) removed; validation runs on text read back from the DOCX. |

## `resume_ai/matching/engine.py` — from C: `resume_ai/engine.py` (adapted)

The positive alias table, research-requirement regexes, `skill_match` scoring, `experience_check`, `pick_family`,
`canonical_url` and `fingerprint` are kept. Changes: `skill_match(job, skills, gaps, hard_gaps)` takes the
profile's skill map and declared gaps; the original hard-coded known-gap and hard-gap lists were removed, so a gap
is now a term that maps to a skill the profile does not list or that the profile declares; `experience_check`
reason text made generic; `priority(job, score, deadline_days)` no longer takes an eligibility class.
Candidate-specific eligibility rules removed (including per-employer research and apply-cap groups).

## `resume_ai/tracking/` — from C

| File | Source | Mode | Notes |
|---|---|---|---|
| `tracker.py` | `resume_ai/tracker.py` | adapted | Migrations 1–8 keep their tables, triggers and submission guard; a few columns renamed to neutral names (`eligibility_text`, `eligibility_status`, `eligibility_assessment`, `timing_text`); two migration notes reworded. **Migration 9 is new**: triggers refuse `jobs.application_status = 'submitted'` without a candidate approval row. `assert` checks replaced by `CandidateOnlyStatus` / `ValueError`. `Tracker(path, profile=None, run_id=None)`; candidate-specific eligibility rules removed from `assess()`; `export_for_artifact` renamed `export_job`; apply-cap group removed. |
| `control.py` | `resume_ai/control.py` | verbatim + docstring line | Desired/reported worker state, heartbeat, command queue, browser audit rows. |

## `resume_ai/agents/spec_agent.py` — from C: `resume_ai/overnight.py` (adapted)

`extract_json` and `spec_issues` keep their logic (data from `Profile`). `spec_prompt` keeps the original structure;
candidate-specific writing rules removed and replaced by generic `BASE_RULES` + `profile.writing_rules`. `ClaudeCLI`
keeps the original tool-restricted `claude -p` command and error classification. `generate_spec` condenses the
original retry-with-validator-feedback cycle (spread over queued task attempts) into one function with an injectable
LLM. The other task types and the runner loop are not included.

## Tests

| File | Source | Mode |
|---|---|---|
| `tests/rag/test_{chunking,ingestion,embeddings,vectorstore,retrieval,reranking_security}.py` | A: `tests/rag/<same>` | imports |
| `tests/rag/test_component.py` | A: `tests/rag/test_component.py` | imports; removed the `coverage` tests and the `PreparedArtifactTests` class (they need the excluded Stage 3I experiment modules and result files) |
| `tests/rag/test_reranking.py` | A: `tests/rag/test_reranking.py` | imports; removed `test_fixture_distinctions` (needs a 140 KB evaluation fixture not copied) |
| `tests/test_matching.py`, `test_grounding.py`, `test_tracking.py` | C: `tests/test_core.py` | adapted to the synthetic profile; same assertions where the feature exists, plus new checks (profile-declared gaps, migration-9 trigger, guards under `python -O` in a subprocess) |
| `tests/test_spec_agent.py` | C: `tests/test_overnight.py` | adapted; `generate_spec`, CLI tool-restriction and limit tests are new |
| `tests/test_demo.py`, `tests/conftest.py` | — | new |

Not ported: A's `tests/rag/test_reasoning.py` (needs excluded experiment modules) and the v11 pipeline tests.

## New files

`examples/` (synthetic profile, evidence notes, postings, mock model replies, `run_demo.py` including the demo-only
`HashingEmbeddingProvider`), `README.md`, `docs/ARCHITECTURE.md`, this file, `pyproject.toml`, `requirements.txt`,
`.github/workflows/tests.yml`. `ARCHIVE.md` is the previous top-level `README.md`, renamed, with only its opening sentence rewritten.

## Not included from C and why

Private browser-assist and discovery components, the dashboard, the process supervisor, the command-line tool,
snapshot/export helpers, and everything under `data/`, `packets/` and `frames/` are not included. They operate on
real applications, postings, form answers, screenshots or local machine paths.
