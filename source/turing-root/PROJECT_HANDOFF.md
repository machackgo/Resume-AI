# Resume AI — Project Handoff

Transfer context: OpenAI Astra → Claude Opus 5.5, as requested by the project owner. These are handoff role labels, not independently verified provider identities.

Audit date: 2026-10-09. Target: WPI Turing HPC. Canonical project root: `/scratch/mohammedmubashir/resume-ai`; `~/scratch/resume-ai` resolves there for the cluster account. This document records a read-only technical audit plus creation of this file. No training, model inference, feature implementation, model promotion, or GPU allocation was performed.

Evidence notation used throughout:

- **VERIFIED** means directly supported by inspected source, configuration, saved results, manifests, or an audit-time command. Historical results were generally inspected, not rerun. A saved independent assessment establishes the recorded judgment; it does not turn a model-assisted judgment into independently established ground truth.
- **INFERRED** means an architectural interpretation or recommended direction supported by the evidence but not an executed result.
- **UNKNOWN** means evidence was insufficient. Missing measurements are not estimated.
- **REQUIREMENT / FUTURE** identifies the owner's constraints or plans, not existing functionality.

Source references `[E01]`–`[E30]` resolve in section 18. `R:` means a path relative to the canonical Turing root. `V:` means a member of the sealed October 8 validation package, located as described below. Do not interpret `V:` as a root-level project directory.

## 1. Executive Summary

**VERIFIED: Resume AI is in post-validation remediation of its non-agent pipeline. Its latest decision is `VALIDATION_COMPLETE_NOT_READY`, “C — NOT READY / NO-GO FOR AGENT DEVELOPMENT.”** The unchanged 20-original + 10-stress acceptance cohort is complete. Independent review passed 23 cases and failed 7: J02, J04, J07, J11, J13, J19, S04. The final CPU accounting is 534 passed, 1 failed, 46 skip events, and 3 protected-blocked checks. Neither completed Slurm jobs nor valid output schemas satisfy the semantic acceptance gate. [E01–E04]

**The immediate engineering issue is deterministic:** retrieval-discovery membership prematurely rejects a canonical quote/requirement pair, and fallback preserves that bookkeeping rejection as if independent semantic review had rejected it. This causes J11 to emit no resume despite eligible architecture evidence. During this audit, a read-only replay reproduced the three-test boundary suite: 2 passed, 1 failed. No model was loaded. [E05]

The retained model configuration is the untouched local **BASE** at `R:models/Qwen3.8-27B`, with NF4 4-bit inference and no adapter. Despite the directory name, inspected metadata is `qwen3_5` and the recorded text runtime is `Qwen3_5ForCausalLM`. The mixed QLoRA step-124 adapter is a **failed descriptive endpoint**, not an approved model. No trained adapter passed promotion. BASE retention is not a production-readiness claim. [E06–E09]

The actual retriever uses pinned MiniLM embeddings, a candidate-scoped SQLite exact-search reference store, deterministic component retrieval, and the **identity reranker**. PostgreSQL + pgvector is an architectural direction; it is not implemented or verified production infrastructure. Learned rerankers were evaluated and not promoted. [E10–E14]

**Hard development gate:** finish and verify the non-agent pipeline before autonomous agents. The owner also requires thorough learning of agent architecture before implementation. Do not bypass either gate. ULTRON is future planning only.

## 2. Project Objectives

**VERIFIED from the earliest evaluation and later contracts:** Resume AI aims to turn candidate evidence and job requirements into useful, truthful, job-relevant professional materials. It must preserve exact evidence provenance, distinguish supported from missing/conflicting facts, avoid invented skills or achievements, and emit structured, testable outputs. The baseline evaluated requirement extraction, skill extraction, gap identification, support labels, claims, citations, refusals, and resume bullets. [E15]

The professional curriculum subsequently formalized ten task families: job analysis; candidate/job mapping; missing-information identification; resume-content selection; bullet rewriting; full resumes; resume sections; cover letters; application answers; and outreach drafts. These are curriculum/contracts and historical experiments; the latest acceptance pipeline is a narrower extractive resume system. A schema or training example does not establish a working product feature. [E16]

The ordering in the recorded roadmap is truth, job relevance, ATS compatibility, and professional writing. There is no verified universal ATS score or parser guarantee. Candidate ownership, project identity, academic/professional scope, action strength, technology identity, metrics, and requirement coverage must remain explicit. [E16–E17]

**INFERRED:** The intended product can eventually reuse this evidence system with VeriBridge and a broader career workflow. That relationship does not prove live VeriBridge integration or autonomous application execution in Resume AI.

**UNKNOWN:** The original conversation establishing the project, comprehensive user-story backlog, product release criteria beyond preserved stage gates, and a complete author-by-author development chronology are unavailable. This handoff does not reconstruct conversations from filenames.

## 3. Current Architecture

The most recent verified source is the `application/` snapshot within the October 8 semantic-validation package and the identical deployed shard snapshots under `R:work/semantic-contracts-20261008/`. There is **no root-level `resume_pipeline/`** in the inspected root inventory. Running a module from the project root without selecting the correct snapshot risks executing old code or failing imports.

```text
Captured candidate sources + immutable capture hashes
  → scoped canonical evidence ledger + versioned provenance
  → structural chunks, token-fit checks, pinned embeddings
  → candidate-specific SQLite snapshot restored to local temporary storage
Raw job → exact source spans → bounded requirements and semantic relationships
  → component-aware retrieval + exact acronym normalization
  → identity reranker + bounded, provenance-preserving context
  → BASE Qwen quote selection / per-requirement assessment
  → independent claim and requirement licensing with counterevidence
  → bounded reselection / fallback through the same safety boundaries
  → deterministic extractive resume compiler and schema checks
  → raw traces, source-span checks, independent semantic acceptance review
```

“Independent licensing” here means a separate review stage from selection, with deterministic checks and a Qwen review; it does **not** mean an independent model provider or human truth adjudicator. The final saved acceptance audits are a further evaluation layer. [E01, E05, E18]

Core latest modules, all relative to the snapshot's `application/`:

| Module | Responsibility and current evidence |
|---|---|
| `resume_pipeline/runtime.py` | Rehydrates capture evidence; verifies hashes/scope; opens a node-local SQLite copy; builds the frozen retriever; defines BASE Qwen loading. |
| `resume_pipeline/pipeline.py` | Raw-job validation, exact-span requirements, fixed batching, selection, licensing dispatch, fallback, compilation, refusal/error output. |
| `resume_pipeline/context_units.py` | Source-bound units and allowed full quotations; retains canonical references. |
| `resume_pipeline/source_registry.py` | Canonical source binding and resolution. |
| `resume_pipeline/semantic_contracts.py` | Capability/action/technology/event/project compatibility and license conditions. |
| `resume_pipeline/licensing.py` | Review-source assembly, source identity, review parsing, factual/content eligibility and relationship licensing. |
| `resume_pipeline/component_review.py` | Bounded component relationship review. |
| `resume_pipeline/reselection.py` | Pools canonical alternatives and propagates quote/link exclusions; current failing boundary is in `exclusions`. |
| `resume_pipeline/semantic_policy.py` | Candidate ordering and fallback semantic policy. |
| `resume_pipeline/fallback_retrieval.py` | Bounded retrieval expansion. |
| `resume_pipeline/__main__.py` | Single non-agent CLI; exclusive output creation and structured failures. |
| `rag/deep/retrieve.py` | Frozen component retrieval and traceable selection. |

Verified source limits: raw job maximum 262,144 characters; at most 128 requirement fragments; batches of four requirements; at most two selected quotes per initial batch; model input limit 8,192 tokens and output cap 1,536 tokens. `reselection.py` declares two rounds, five context units, and a 128-unit pool limit. Repeated identical requirements within the same heading retain occurrence aliases. Final coverage is conservatively recorded as partially supported when a licensed component exists, rather than claiming the whole conjunction is supported. [E18]

This is a fixed orchestration schedule, not an autonomous agent. No production serving endpoint, browser worker, application-submission agent, or continuously running scheduler was verified.

## 4. Repository Structure

**VERIFIED:** The Turing tree is not a Git checkout. `git status` returned “not a git repository”; a recursive metadata inventory found no `.git` directory. Branch, HEAD, recent commits, uncommitted diff, and remote origin therefore cannot be reported. Do not invent commit history or initialize Git over frozen artifacts as part of resumption.

The initial inventory recorded 54,414 file entries. Relevant layout:

| Root path | Purpose |
|---|---|
| `.venv/` | Existing Python 3.11.12 environment. |
| `models/Qwen3.8-27B/` | Preserved base checkpoint and tokenizer; architectural identity differs from folder label. |
| `models/stage3c/`, `models/stage3f/` | Pinned embedding and cross-encoder snapshots. |
| `adapters/stage4b_smoke/` | Engineering smoke adapter and integrity metadata. |
| `adapters/stage4c1/run_430001/` | Interleaved and evidence-only saved checkpoints. |
| `datasets/stage4a/`, `datasets/stage4c0/` | Frozen training/evaluation releases and preserved dataset candidates. |
| `rag/` | Root historical ingestion, chunking, embedding, storage, retrieval, reranking, reasoning, scale/component/deep experiments. |
| `migrations/` | SQLite reference schema migration. |
| `contracts/` | Task schemas, rubrics, acceptance rules, curriculum and teacher-routing specifications. |
| `tests/`, `eval/tests/` | RAG and early-stage test suites; newer pipeline tests also live in snapshot applications. |
| `eval/` | Baseline/prompt datasets, prompts, metrics, runners and reports. |
| `stage4a/`, `stage4b/`, `stage4c0/`, `stage4c1/` | Dataset construction, QLoRA engineering, curriculum and controlled experiment code. |
| `results/` | Stage reports, raw outputs, metrics, model configurations, Slurm logs, manifests and preservation receipts. |
| `docs/`, `docs/adr/` | Stage architecture, decisions, limitations and training protocols. |
| `research/`, `scenarios/` | Curriculum research and scenario artifacts. |
| `release/` | Historical immutable release archives. |
| `ops/stage4c1/` | Experiment operational scripts. |
| `work/` | Additive experimental implementations, acceptance snapshots, archives and run-specific source copies. |
| `baseline_test.py`, `reasoning_benchmark.py`, `test_qwen_4bit.py` | Historical model/inference scripts; do not execute on login nodes. |

There is no top-level README. Useful entry documents include `eval/README.md`, `stage4a/README.md`, `stage4b/README.md`, stage reports, and the latest sealed `FINAL_REPORT.txt`. No applicable `AGENTS.md` was found in the remote project/checked ancestors or latest local validation package.

**Critical locations:**

- Latest complete local package inspected: `/Users/mohammedmubashiruddinfaraz/resume-ai-semantic-validation-20261008`.
- Remote latest application example: `R:work/semantic-contracts-20261008/full-v1-shard-0/application/`.
- The five completed acceptance shards are `historical-v11-shard-0`, `historical-v11-shard-1`, and `full-v1-shard-0`, `full-v1-shard-1`, `full-v1-shard-2` under that work parent.
- Sealed final archive: `R:work/semantic-contracts-20261008/archive-semantic-validation-final-20261008T151118Z/resume-ai-semantic-validation-20261008-final.zip`.
- Archive size: **80,189,386 bytes**; SHA-256: `f284b393b9d6e3ae18de49b994f249f5e43d7f844f6191470bcc83ee01fd3c72`. Its full hash was independently recomputed from Turing during this audit. It contains 3,451 members including its manifest. [E19]

## 5. Development History

This is artifact chronology, not Git chronology. Stage completion statements apply at their original boundary; “later stage not started” statements in old reports are historical, not current.

| Stage / period | VERIFIED progression and decision | Evidence |
|---|---|---|
| Baseline, preserved September 26 package | Eight synthetic cases; strict JSON/schema 0/8 due to fenced output. Diagnostic fence removal is separately reported and is not strict success. | E15 |
| Stage 2 | `grounded_v3` achieves 8/8 raw schema-valid outputs on the same tiny set; extraction improves, but some support decisions worsen. Prompt reliability is not evidence-understanding completion. | E15 |
| Stage 3A | Canonical source/evidence/claim/support/event types and scoped in-memory ledger; versioning, deduplication, provenance and trust separation. | E20 |
| Stage 3B | Deterministic structural chunking, exact Unicode offsets and citation round trips; no learned models required. | E20 |
| Stage 3C | Compares MiniLM and E5; provisional MiniLM + title/section integration. | E10 |
| Stage 3D | Persistent SQLite exact-search reference, typed semantic spaces, lifecycle and isolation. PostgreSQL/pgvector explicitly deferred. | E11 |
| Stage 3E | Semantic/BM25/RRF comparison; semantic ordering retained; retrieval relevance never becomes verification. | E12 |
| Stage 3F | Two cross-encoders evaluated; gains on one suite do not overcome coverage/legacy regressions. Identity reranker retained. | E13 |
| Stage 3G | Qwen + retrieved evidence, strict JSON/ID/quote checks, support judgments; stage label semantics change, limiting cross-stage comparison. | E21 |
| Stage 3H | Scale stress reveals compound evidence lost before Qwen; decision: do not freeze RAG yet. | E21 |
| Stage 3I | Structural component retrieval restores one compound failure but leaves the RAG-acronym case unresolved. | E21 |
| Stage 3J | Exact `RAG` → `retrieval augmented generation` query normalization repairs measured retrieval loss; freeze RAG for the subsequent QLoRA experiment. This is not a permanent end-to-end acceptance certificate. | E14 |
| Stage 4A | Frozen synthetic evidence-reasoning curriculum; architecture/tokenization/loss audit. Proposed training settings are not all the settings eventually executed. | E22 |
| Stage 4B | Successful nine-step QLoRA mechanics smoke after memory/diagnostic fixes; save/reload and prepared-base recovery verified. | E08 |
| Stage 4C-0, September 30 | Audited professional curriculum frozen: 149 accepted split records plus six challenge references. | E16 |
| Stage 4C-1, report October 2 | Controlled interleaved versus evidence-only training; final examination completed. Mixed adapters fail selection/promotion; retain BASE. | E07, E09 |
| October 2–3 | Constrained-decoding v1 misses existing runtime rules; v2 fixes structural constraints but semantic grounding still fails. No model promotion. | E23 |
| October 4–5 | Semantic prompting → source-bound spans/routing → evidence-bound plans → licensed-claim enforcement/context closure → deterministic compiler revisions. Each intervention addresses a measured boundary; earlier passes remain development evidence. | E23–E24 |
| October 5 final-development v2 | Adds missing compiler dispatches and source-origin resolution; reports a development freeze, not protected or full end-to-end acceptance. | E24 |
| October 7 | Pre-agent integration/repair/remediation evaluates actual captured evidence. Complete full-v7 still reports NO-GO despite priority-case repairs. | E25 |
| October 8 | Semantic contracts v11, outage recovery, eight historical audits, remaining 22 fresh cases, final 30-case review. Final regression adds a real failure; final decision remains NO-GO. | E01–E05 |

**Resolved engineering issues with bounded evidence:** strict output fences on the Stage 2 set; source-span offsets in the source-bound experiment; missing compiler task dispatches in final-development v2; the Stage 3J acronym retrieval failure; QLoRA 4,608-token memory feasibility using the measured offload/chunked-loss configuration; and network-interrupted result reconciliation without rerunning finished jobs. Their resolution does not establish that all related semantic cases are fixed. [E08, E14–E15, E23–E25]

**Failed or non-promoted experiments:** learned reranker default promotion; Stage 3H/3I RAG freeze; Stage 4C-1 adapter promotion; constrained decoding as a complete semantic remedy; several source/plan/compiler development gates; October 7 and October 8 end-to-end readiness. Preserve their negative results. [E01, E07, E13, E21, E23–E25]

## 6. Completed Milestones

**VERIFIED, within measured scope:**

1. Evidence representation, candidate scope, exact provenance and version history are implemented and historically tested.
2. Structural chunking and model-specific embedding fit checks exist; no silent embedding truncation is allowed.
3. Pinned local embeddings, persistent exact vector search and candidate isolation are implemented.
4. Retrieval/reranking ablations and compound/scale failure analysis are complete.
5. A Stage 3J RAG configuration was frozen for controlled model experiments.
6. Evidence and professional training curricula, split manifests, exclusion policies and model-evaluation gates were created.
7. QLoRA update mechanics, adapter-only saving, reload equality, and prepared-base recovery were demonstrated.
8. Controlled training and the final Stage 4C-1 examination were completed; the negative promotion decision is final for that experiment.
9. Deterministic source binding/licensed compilation and a fixed non-agent resume pipeline exist in versioned work snapshots.
10. The latest 30-case acceptance evaluation and all five Slurm jobs completed; final artifacts were sealed and transferred.

**Not completed:** a passing non-agent semantic acceptance gate; production deployment; a verified PostgreSQL/pgvector adapter; comprehensive job-description understanding; broadly accepted professional generation across all ten tasks; autonomous agents; ULTRON. Historical unit-test totals and isolated development freezes do not override these gaps.

## 7. Model and QLoRA Details

### Base identity and inference

| Field | VERIFIED value / limitation |
|---|---|
| Local identifier | `R:models/Qwen3.8-27B` — preserve this existing path. |
| On-disk architecture | `Qwen3_5ForConditionalGeneration`; `model_type=qwen3_5`; checkpoint includes vision metadata. |
| Loaded text architecture | Saved runtime `Qwen3_5ForCausalLM`; no vision inference established in these runs. |
| Text parameter count | 26,895,998,464, from saved architecture audit. Full checkpoint including vision: 27,781,427,952. |
| Structure | 64 text layers: 48 linear-attention and 16 full-attention; hidden 5,120; intermediate 17,408; vocabulary 248,320. |
| Context | Configured 262,144; current operational input cap 8,192. Configured capacity is not demonstrated usable context on an A30. |
| Quantization | bitsandbytes NF4, 4-bit, double quantization, BF16 compute/model dtype, uint8 quantized storage. |
| Device / attention | Latest loader explicitly uses CUDA device 0 and SDPA. Historical scripts may have requested automatic placement. |
| Decoding | Greedy; no sampling; maximum 1,536 generated tokens; cache enabled; thinking disabled. |
| Current runtime seed | 410042 in `BaseQwen`; earlier baseline seed 42; Stage 4C-1 training seed 430001. |
| Tokenizer | Qwen2Tokenizer; pad token `<|endoftext|>` ID 248044; runtime EOS `<|im_end|>` ID 248046; unchanged local chat template. |
| Chat-template SHA-256 | `c3cf9e34abf4f9e36c2d72165aa9c132d3e2a725b6c2586aaa3a8af9d7a81041`. |
| Weights / gradients | Latest inference loads no adapter, freezes all parameters and uses inference mode. |

The nested text configuration has a different EOS field from the tokenizer; follow the verified runtime's explicit stop IDs, not a guess from one config field. No tokens were added in the smoke setup. **UNKNOWN:** an independently established upstream repository/revision for the base checkpoint. The folder name cannot establish that it is a public “Qwen3.8” release. Do not silently substitute or redownload a differently named model. [E06, E08, E18]

### QLoRA mechanics and executed settings

- Rank 8, alpha 16, dropout 0.05, bias none, task `CAUSAL_LM`; targets `q_proj`, `k_proj`, `v_proj`, `o_proj` in the 16 full-attention layers: 64 modules and 128 trainable matrices.
- 5,242,880 trainable parameters, 0.019493% of the frozen text base. Linear-attention and MLP modules were inspected but not trained in this configuration.
- PagedAdamW8bit; learning rate 5e-5; constant scheduler, no warmup; microbatch 1; gradient accumulation 2. Smoke optimizer: betas 0.9/0.999, epsilon 1e-8, weight decay 0.01, gradient clipping 1.
- Tensor maximum 4,608; maximum active example length 4,233; dynamic batching, no truncation or packing. Assistant JSON plus one end-of-message token supervised; prompt/system/user/header/empty-thinking/padding positions masked with -100. Causal shift applied once.
- Non-reentrant gradient checkpointing; saved activations offloaded to pinned CPU memory; explicit k-bit preparation keeps large embeddings/head BF16 and upcasts one-dimensional parameters. Vocabulary loss is evaluated in 64 supervised-position chunks. This custom engine is material to feasibility; generic trainer substitution is not equivalent.
- Stage 4A's earlier accumulation-16/two-epoch suggestion was a proposal. It must not be described as executed Stage 4C-1 training. [E08–E09, E22]

### Datasets and training history

| Release / run | Actual scope |
|---|---|
| `datasets/stage4a/v1/` | 1,920 authored synthetic evidence examples: train 1,600, validation 160, test 160. Four balanced labels; 60 scenarios and 12 parent template families. Grouped split isolation, historical exclusion and token audits preserved. |
| `datasets/stage4c0/v1/` | 149 professional examples: 119 train, 14 validation, 16 test; six accepted challenge references. Ten challenge inputs preserved; four references quarantined/unscored. Separate 18-example pilot excluded from SFT. |
| Stage 4B smoke | 17 TRAIN examples, one pass, nine optimizer updates. Fixed TRAIN probe teacher-forced loss 0.20622908 → 0.14515381; optimization check, not held-out accuracy. |
| Stage 4C-1 mixed | 124 updates; 247 unique examples = 128 evidence + 119 professional; 110,147 supervised tokens = 55,032 evidence + 55,115 professional. No repeated professional exposure. |
| Stage 4C-1 evidence-only | 131 updates; 262 unique evidence examples; 110,055 supervised tokens. Exposure differs from mixed by 92 tokens. |

Teacher interventions/configuration changes were not introduced during the controlled run; the final report records zero corrective examples. Some curriculum/critic artifacts requested Astra, but provider model identity was not independently attested. Protected final answers must not become corrective training data or justify retuning the same final examination. [E07–E09, E16, E22]

### Checkpoints and selection

| Location | Status |
|---|---|
| `adapters/stage4b_smoke/` | Saved engineering adapter; mechanics proof only. |
| `adapters/stage4c1/run_430001/interleaved/checkpoint_000124/` | Failed descriptive mixed endpoint. Manifest digest `6adcf247534bea658551fdac142d5d7266936c6c651a5d0af37a20e0d6e6ba57`. |
| `adapters/stage4c1/run_430001/evidence_only/checkpoint_000131/` | Matched evidence-only comparator. Manifest digest `e6dbded09c4d787f8952f9235e36ae416e12d1bbfdcf2b07977f8aeb3c705734`. |
| Other checkpoint directories | Retained intermediate/initial checkpoints. Final audit historically verified 31 checkpoint manifests. Do not delete, merge, overwrite or reinterpret them as promoted. |

**Best verified retained configuration: BASE with no adapter. There is no approved “best trained checkpoint.”** The mixed adapter's evidence accuracy improved, but professional/schema/fidelity and validation gates failed. Preserve that distinction. Current evidence does not isolate a model-reasoning bottleneck under fully correct inputs; QLoRA retraining is not justified. [E07, E09, E26]

## 8. RAG Architecture

| Pipeline boundary | Implementation, verification and limitations |
|---|---|
| Data ingestion | `rag/adapters.py`, `rag/ingestion.py`, `rag/domain.py`: plain/local text and normalized captures with scoped deterministic IDs and event history. Earlier demonstrations use synthetic normalized web/PDF/repository forms. Latest `CaptureAdapter` loads existing actual capture artifacts and checks capture hashes; it is not proof of a general production crawler or PDF parser. |
| Canonical evidence | Scope contains tenant and candidate IDs; evidence/source/version/content hash/native locator/trust are retained. Claims, supports and verification are distinct from unreviewed source assertions. Canonical MemoryLedger is an in-memory reference, rehydrated from frozen captures. |
| Chunking | `CandidateChunks`; structural policy B: 640 Unicode characters, overlap 96; policy A 320/48 retained as ablation. Exact half-open normalized offsets and citation resolution; embedding fitting accounts for actual tokenizer budget. |
| Embeddings | Pinned MiniLM, 384 dimensions, masked mean pooling, L2 normalization, float32 CPU, batch 16, four threads in provider. `title-section-v1` input construction; no query/document prefix. Token limit 256; oversized inputs rejected rather than silently truncated. |
| Storage | SQLite exact reference with binary64 vectors, typed semantic-space identity, scope binding, lifecycle filtering, transactions and migration 001. Matching dimensions alone do not make MiniLM and E5 compatible. No ANN or production PostgreSQL adapter verified. |
| Retrieval | Semantic cosine default; BM25 and equal-weight RRF remain ablations. Deep path: internal K=20, minimum score 0.2, per-component shortlist 2, atomic shortlist 5, maximum five distinct groups, deterministic round-robin selection. |
| Query construction | Conservative structural decomposition and exact RAG acronym expansion; preserve the original requirement and trace the transformed search query. Discovery associations are not factual licenses. |
| Reranking | `ScopedReranker` verifies scope/provenance. Identity ordering retained. Two learned cross-encoders exist for experiments and are not production defaults. Pair budget 512; no silent truncation. |
| Context | Canonical citation handles, source/version/spans, allowed source-authored quotations, requirement relationships and counterevidence. Fixed context budgets and typed project/event identities. Raw retrieved text is untrusted data. |
| Qwen inference | Frozen BASE selects/assesses bounded inputs. Separate license reviews validate claims/relationships; model-generated support labels alone cannot establish truth. |
| Grounded output | Extractive compiler emits unchanged licensed source claims, provenance and requirement bindings; unsafe or insufficient cases may refuse. Full factual and licensing acceptance is still incomplete. |
| Evaluation | Exact hashes, raw prompts/token traces, canonical-source checks, controls, test logs and independent per-case multidimensional reviews. Current gate failed despite healthy mechanical checks. |

Exact pinned identifiers:

| Role | Identifier | Revision |
|---|---|---|
| Retained embedding | `sentence-transformers/all-MiniLM-L6-v2` | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` |
| Embedding ablation | `intfloat/e5-small-v2` | `ffb93f3bd4047442299a41ebb6fa998a38507c52` |
| Reranker experiment | `cross-encoder/ms-marco-MiniLM-L6-v2` | `233902d25c440f23af6f7d6e94d2946bac0bee0a` |
| Reranker experiment | `cross-encoder/ms-marco-TinyBERT-L2-v2` | `81d1926f67cb8eee2c2be17ca9f793c7c3bd20cc` |

E5 also has 384 dimensions, with `passage: ` and `query: ` prefixes and 512-token budget. Its vectors cannot be relabeled as MiniLM vectors. Locks include per-file hashes. [E10, E13]

**Storage operation:** scratch is documented as Ceph. The current runtime opens the immutable snapshot read-only, checks its scope, backs it up to a temporary local SQLite file, and uses that local file for the live connection. File mode is 0600; cleanup occurs on close. Do not open a writable live SQLite database directly on shared scratch. PostgreSQL roles/RLS/pgvector indexes remain unverified future work. [E11, E18]

**Known retrieval/grounding failures:** semantically adjacent technologies, API consumption versus implementation, plans versus completed work, compound evidence displaced by distractors, source attribution/alias/version ambiguity, generic monitoring wrongly covering detailed counters/latency predicates, and valid evidence blocked by discovery metadata. High recall, an exact quote, or valid citation IDs do not prove claim entailment or requirement coverage.

## 9. Evaluation Results

All results below are historical saved measurements except the explicitly identified audit-time CPU replay. They are not new inference results. Do not compare incompatible suites as a continuous performance curve.

### Early baseline and retrieval

| Evaluation | Recorded metric | Scope / qualification |
|---|---|---|
| Untouched baseline | Strict JSON/schema 0/8 | All outputs fenced; fence-removal diagnostic must remain separate. |
| Stage 2 grounded_v3 | Schema 8/8 | Same eight cases; support-label errors remain. |
| Stage 3C MiniLM title-section | Recall@1 68.18%; Recall@3 90.91%; MRR 0.8030; hard-negative wins 86.36% | Small synthetic short-corpus screening; not broad production evidence. |
| Stage 3C MiniLM raw | Recall@1 59.09%; Recall@3 90.91%; MRR 0.7652 | Same screening comparison. |
| Stage 3F identity | MRR 0.8232; Recall@3 0.8703 | Extended reranking suite. |
| Stage 3F MiniLM cross-encoder | MRR 0.8859; Recall@3 0.8301 | Better MRR but worse coverage; not promoted. |
| Stage 3F TinyBERT | MRR 0.8631; Recall@3 0.7998 | Not promoted. |
| Stage 3J LARGE/XL component retrieval | 12/12 material components; 100% all-required coverage among the evidence-bearing needs | Repair of the measured component-retrieval benchmark; does not mean perfect overall Qwen reasoning. |
| Stage 3J LARGE/XL Qwen | 68.75% context-label accuracy; macro F1 0.7036 | 16 cases per scale; residual semantic/citation errors persisted. |

Source reports and machine-readable embedding/reranker artifacts were inspected. Stage 3G changed the missing-evidence label semantics relative to Stage 2. Stage 3H's full-context control was infeasible at larger scales; no large-scale full-context accuracy superiority is established. Exact learned-score replay has also varied across CPU families, so historical logs preserve such failures. [E10, E13–E15, E21]

### Stage 4C-1 held-out model comparison

| Metric | BASE | Mixed step 124 |
|---|---:|---:|
| Evidence TEST strict accuracy, n=160 | 43.75% | 80.00% |
| Evidence macro F1 | 0.4758 | 0.7986 |
| Atomic accuracy | 39.38% | 83.75% |
| Strict contracts | 121/160 | 157/160 |
| Fabricated ID occurrences | 3 | 0 |
| Overclaimed atoms | 74 | 21 |
| UNKNOWN/UNSUPPORTED → SUPPORTED errors | 1 | 5 |
| Professional TEST schema validity, n=16 | 0/16 | 1/16 |
| Professional primary quality, scale 0–4 | 0.0000 | 0.2500 |
| Professional factual-critical cases | 8/16 | 5/16 |

Evidence strict accuracy difference +36.25 percentage points; recorded paired 95% bootstrap interval [0.25625, 0.4625] in proportion units; improved/regressed/unchanged 74/16/70. Professional evidence-only comparator: schema 0/16, primary quality 0/4, factual-critical cases 7/16. All three arms failed grounding-safe status. Numeric-category evidence examples were absent (0/0), so numeric perfection cannot be inferred. Historical RAG comparison had 32 LARGE/XL observations from 16 unique cases; contract/termination gate failed despite improved context accuracy. [E07, E09]

### Latest full-v1 cohort on unchanged full-v7 inputs

| Measure | VERIFIED saved value |
|---|---:|
| Cases | 30: 20 original + 10 stress |
| Independently passed / failed | 23 / 7 |
| Runtime COMPLETE / FAILED | 22 / 8 |
| Correct unsupported-input refusals among runtime failures | 6 |
| Unusable positive-evidence resumes | 2: J04 and J11 |
| Substantive claim occurrences / unique claim IDs | 23 / 10 |
| SUPPORTED / PARTIALLY SUPPORTED | 19 / 4 |
| UNSUPPORTED / CONTRADICTED final claims | 0 / 0 |
| Strong achievements / valid narrow bullets | 7 / 16 |
| Correct project/event / cross-project contamination | 23 / 0 |
| Broad capability compatible / incompatible | 23 / 0 |
| Invalid detailed requirement license | 1, J02 |
| Runtime controls passed / failed | 40 / 0 |
| Mechanical failures | 0 |
| Canonical context/source-span checks | 2,684 |
| Model calls | 215 |
| Maximum model input | 8,191 of 8,192 tokens |
| Length terminations | None reported in final audit |
| Final regression | 534 passed, 1 failed, 46 skip events, 3 protected-blocked |

The 170 omitted/unsupported requirement occurrences and 28 partially supported occurrences count repeated raw requirements, not unique unsupported corpus capabilities. Zero fully supported occurrences in the pipeline coverage summary follows its conservative component-coverage accounting. The separate relationship audit uses more specific classifications; do not collapse these different metrics. [E02–E04, E18]

Eight fresh historical v11 cases were reused because code, inputs, BASE configuration and review provenance matched; 22 remaining cases were generated in the three full-v1 shards. Previous full-v7 outputs are baseline, not current acceptance outputs. Do not add historical and current cohort numerators or regenerate completed same-revision cases. [E01, E03]

**Test-accounting correction:** 46 skips include 44 individual tests and two class-setup skip events. There were 582 test executions but 584 outcome entries. Three protected-blocked checks are separate and never passes. The original passing base suite has 532 passes; the post-validation boundary regression adds 2 passes and 1 failure. Earlier summary arithmetic undercounted passes by two; corrected final accounting supersedes it without editing raw logs. [E04]

**Audit-time verification:** locally imported the existing `DiscoveryLicenseBoundary` test class without invoking its artifact-writing main routine. Result: three tests, two passes, one failure, zero errors. The failing assertion reproduces a requirement link excluded before independent licensing. This establishes the small deterministic failure; it does not rerun or certify the full suite. [E05]

## 10. Known Bugs and Limitations

| Priority | Finding / first failing boundary | Evidence and implications |
|---|---|---|
| P0 | J11: `_assess_selection` / `exclusions` treats discovery membership as a license prerequisite. | Selector chooses a canonical architecture quote; membership check rejects its target association; fallback retains the unlicensed rejection. Resume is empty. New general CPU regression fails. |
| P0 | J02: requirement-specificity licensing. | Broad OBSERVABILITY compatibility permits detailed request-counter/latency coverage without exact packed supporting anchors. The final quote itself is factual; its requirement license is invalid. |
| P1 | J07/J13/J19/S04: project aliases, linked repository and service/model version scope. | Four claim occurrences remain partially supported. Explicit provenance relationships and relevant limiting/future-work evidence are not reconciled adequately in bounded review context. These are not proven contradictions across unknown versions. |
| P1 | J04: content eligibility and positive-evidence recovery. | Generic setup/unsupported pgvector assertions are correctly withheld, but implementation artifacts yield no usable substantial extractive resume claim. Safe omission alone is not positive-case success. |
| P2 | J14 duplicate supported wording. | Minor presentation issue; do not weaken provenance to deduplicate it prematurely. |
| P2 | Operational/documentation ambiguity. | Root historical code versus current work snapshots; stale interruption note; no Git history or root dependency lock. |

Sources: [E01, E05, E27]. Remediation must preserve factual rejection, contradiction blocking, tenant/candidate scope, exact spans and source identity. In particular, fixing the discovery bug must not grant a license merely because a quote was retrieved or selected.

Other limitations: small synthetic evaluation sets; model-assisted semantic judgments; no production concurrency/security validation; no established production SLA or latency distribution; no verified remote vector database; no GPU-size extrapolation; extraction-based requirement parsing is not a comprehensive semantic job parser. Public repository content alone does not establish personal authorship, employment, leadership, production deployment, or certification. Legacy skipped tests need their required artifacts and execution environment, not a false “all green” summary.

## 11. Current Development State

- **Exact stage:** semantic-contract remediation v11, full acceptance validation completed, current gate failed. Non-agent pipeline implemented in a bounded research form; not verified ready for autonomous agents or production.
- **Last completed substantive task:** reconciliation and independent audit of the entire unchanged 30-case cohort, final regression/accounting correction, integrity verification, and sealing/uploading the final October 8 package.
- **Last verified successful tests:** the historical pre-inference CPU suite recorded 532 passes with skips/protected blocks; all 40 runtime controls passed. During this audit, the contradiction-preservation and scoped independent-link-rejection tests passed. The three-test suite itself failed.
- **Latest experiment:** v11 semantic-contract source, five matched shards, BASE-only inference. All five Slurm jobs are now independently confirmed COMPLETED, exit 0:0.
- **Current unresolved issue:** discovery metadata incorrectly becomes rejection authority; other licensing/scope/content issues remain as listed above.
- **Blocker:** `final-regression-gate.json` is false and full semantic acceptance is false. This is a software/validation blocker, not a presently demonstrated missing-GPU or failed-network blocker.
- **Training decision:** no demonstrated residual model bottleneck under fully correct semantic context; do not retrain or promote adapters.
- **Queue at audit:** the account's `squeue` query returned no jobs. This is a point-in-time observation, not a future resource guarantee.

**Stale notes:** `V:RESUME_NEXT.txt` still says reconnect and recover S07/job 2351801. Final `WORK_STATE.json`, `FINAL_REPORT.txt`, completed cohort and archive receipt supersede that interruption note. `remaining: []` in WORK_STATE means the validation work was finished, not that engineering blockers disappeared. Staged historical-v10 shards were not submitted; do not treat them as executed experiments. [E01, E19, E28]

## 12. Environment and GPU Requirements

**VERIFIED live environment:** Python 3.11.12, GCC 13.2.0 build; isolated project `.venv` with system-site-packages disabled. Package versions were read through `importlib.metadata`, without importing/loading model libraries:

| Package | Installed version |
|---|---|
| torch | 2.14.0 |
| transformers | 5.17.0 |
| accelerate | 1.15.0 |
| bitsandbytes | 0.50.2 |
| tokenizers | 0.23.2 |
| peft | 0.21.0 |
| datasets | 5.0.1 |
| trl | 1.13.0 |
| numpy | 2.4.6 |
| jsonschema | Not installed; project has its own schema validation. |

The venv base executable is recorded in `.venv/pyvenv.cfg` under the cluster Spack Python installation. Saved model configuration's `transformers_version=5.8.0.dev0` is checkpoint metadata, not the live installed version. Saved smoke artifacts record torch CUDA 13.0. No clean-environment rebuild was attempted; no root-level dependency lock was found. Existing manifests and environment snapshots are the reproducibility evidence; blindly reinstalling “latest” packages would invalidate it. [E06, E08, E29]

**Environment variable names only:** `PYTHONDONTWRITEBYTECODE`, `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`, `TOKENIZERS_PARALLELISM`, `OMP_NUM_THREADS`, `RESUME_REPAIR_RUN_DIR`, `ACCEPTANCE_SHARD`, `ACCEPTANCE_SHARDS`, `RESUME_AI_VECTOR_ROOT`, `SLURM_JOB_ID`, `SLURM_STEP_ID`, `USER`, `HOME`. The first group controls bytecode/offline/thread behavior, the next group selects run/shard/storage locations, and Slurm/user names are execution context. No credential values or secret-bearing environment dumps are needed. Values should be obtained from the appropriate inspected run wrapper; this document intentionally lists variable names without assignments.

**Services and access:** SSH access to Turing; institution network/VPN as needed; Slurm; local cached model assets. Latest inference is configured for offline local model loading. No paid model API, production PostgreSQL service, pgvector extension, browser service, or external vector service is needed for the recorded BASE acceptance path. Historical source collection involved external repositories; frozen replay uses saved captures. Production service requirements remain future work.

**Measured GPU feasibility, not universal minima:** historical successful runs used one NVIDIA A30 (24 GiB nominal; smoke measured 23.598 GiB usable), 8 CPU cores, 64 GB host RAM. Smoke peak allocated VRAM 19.950 GiB; overall peak reserved 21.912 GiB. Mixed training phase peak reserved 21.4609375 GiB; evidence-only 21.990234375 GiB. The 4,608-token training feasibility depends on chunked loss and pinned-CPU saved activations; unchunked attempts OOMed. These figures are not an 8,192-token inference peak measurement. Exact latest inference peak VRAM was not established in this audit. [E08–E09]

Historical training wrappers specify account `cs541`, partition `academic`, one A30, 8 CPUs, 64G. Latest acceptance wrappers request partition `academic`, one generic GPU, 8 CPUs, 64G and four hours; they omit an explicit account. Do not silently rewrite these as identical allocation specifications. Live `module load slurm` exposes `/cm/shared/apps/slurm/current/bin/sbatch`. Capacity, fair-share and GPU type must be checked before a future authorized run.

## 13. Reproduction Instructions

These commands are documentation, not authorization to start new inference/training. This audit ran only read-only inspection, hashing, scheduler queries and the tiny CPU regression. Current failed gates prohibit staging fresh acceptance inference until repaired in a new working package.

### Connect and inspect without loading a model

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 mohammedmubashir@turing.wpi.edu
cd /scratch/mohammedmubashir/resume-ai
pwd -P
.venv/bin/python -B --version
module load slurm
squeue -h -u mohammedmubashir -o '%i %T %j'
sacct -n -j 2351800,2351801,2351871,2351872,2351873 --format=JobID,State,ExitCode,Elapsed -P
```

Run module setup in a login shell if a noninteractive SSH command does not expose `module`. Do not weaken host-key checks or copy credential files. The existing venv is the verified runtime; environment recreation from scratch is UNKNOWN until separately tested with pinned artifacts.

### Obtain the latest application and evidence

Use the verified final ZIP from section 4. List it before extraction; extract into a **new, empty working directory**, preserving the sealed original. Its top-level member layout can be inspected with Python's `zipfile` CLI or a ZIP reader. Retain `SHA256SUMS.json`, baseline manifests, raw results and all per-case audits. The recorded local package is a convenience access point, not the only copy.

The development source must be this package's `application/`, not root `rag/` by accident. The current remote shard application can be compared against `V:full-v1-shard-0-pre-manifest.json`; all 131 local Python source files matched that live snapshot during this audit. Existing artifact hashes are more authoritative than modification timestamps.

### Reproduce the current deterministic failure without artifact writes

The following exact local command was exercised during this audit. It imports the test module, avoiding its `__main__` routine, which otherwise attempts exclusive writes into the sealed package. `-B` prevents bytecode creation. A nonzero result is expected on the current source.

```bash
/Users/mohammedmubashiruddinfaraz/resume-ai-repair-acceptance-20261007/.venv/bin/python -B - <<'PY'
import sys
import unittest
from pathlib import Path
package = Path('/Users/mohammedmubashiruddinfaraz/resume-ai-semantic-validation-20261008')
sys.path.insert(0, str(package))
from test_discovery_license_boundary import DiscoveryLicenseBoundary
result = unittest.TextTestRunner(verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(DiscoveryLicenseBoundary)
)
raise SystemExit(0 if result.wasSuccessful() else 1)
PY
```

On Turing, first extract the sealed package into a fresh destination, then use the project `.venv/bin/python -B` and that destination in the same import-only recipe. This adaptation is source-supported but was not executed remotely during this audit. Three expected outcomes: discovery-bookkeeping test fails; factual-contradiction and independent-link-rejection preservation tests pass.

For broad CPU reproduction, inspect `V:run_tests.py` and `V:REPRODUCE.txt` in the fresh copy. The historical commands are `python run_tests.py`, `python refresh_cpu_gate.py`, and `python build_manifest.py`, using the intended environment. They write artifacts and must not run in the sealed package. Preserve protected-read boundaries and report blocked/skipped checks separately. Heavy CPU embedding preparation/replay belongs in a CPU Slurm allocation; a historical CPU audit used account cs541, partition academic, two CPUs and 8 GB.

### Model loading and CLI contract — future gated execution only

`BaseQwen` loads the local tokenizer and base checkpoint with local-files-only mode, 4-bit NF4/double quantization, BF16, CUDA:0, SDPA, no adapter, frozen parameters and thinking disabled. The CLI source accepts exactly:

```text
python -B -m resume_pipeline
  --root /scratch/mohammedmubashir/resume-ai
  --kb <verified knowledge-base directory>
  --job-file <raw job text file>
  --profile-file <candidate profile JSON>
  --output <new output JSON path>
```

This is a signature template, not a ready-to-run invocation. Run from the selected snapshot's `application/` or set its import path in a reviewed fresh wrapper. Profile requires nonempty `candidate_id` and `name`, and the candidate must match the KB's bound scope. KB requires `candidate_sources.json`, `embedding-records.json`, and exactly one scoped SQLite snapshot in `candidate-vector-store/`. Output creation is exclusive. Inspect the latest `__main__.py` before execution. Do not invoke this on a login node.

### Acceptance execution after repair and passing prerequisites

The preserved harness documents this sequence: fresh package and run names → CPU gate bound to exact source hashes → input integrity checks → fresh historical controls/cases → independent historical review → passing historical gate → unchanged full-suite completion → independent semantic and mechanical audits → final regression and preservation → new sealed archive. Historical helper filenames include `stage_historical.py`, `sync_historical.py`, `assemble_cohort.py`, `summarize_independent.py`, and `prepare_full.py`. Their arguments and output paths must be reviewed in the new package; do not reuse old v11/full-v1 output directories.

Submit only a newly reviewed wrapper through `sbatch`; query state with `squeue`/`sacct`. Never use `sbatch` on the old completed wrappers merely to “verify” them. The existing full-v1 wrapper is a resource/configuration reference, not a rerun command. Reuse old cases only when code, inputs and configuration are identical and the reuse gate verifies their hashes. A code repair invalidates unchanged-source reuse for affected acceptance claims. No new inference may be staged while the corrected final regression gate is false.

Preserve offline/cache behavior and run-directory selection from the relevant wrapper; variable names are in section 12. Scope for future acceptance must be authorized separately from this audit. **Do not execute `stage4c1/train.slurm` or training modules as part of reproduction.**

## 14. Remaining Tasks

Prioritized engineering backlog, **recommended / not performed**:

| Order | Task | Completion evidence required |
|---|---|---|
| 1 | Repair discovery-versus-independent-license lifecycle in a fresh source copy. | Existing three-test boundary regression passes; initial selection and fallback share the corrected distinction; contradiction/identity/provenance/eligibility vetoes preserved. |
| 2 | Enforce detailed requirement entailment beyond broad capability type. | General counterexample tests for specific predicates versus generic evidence; exact same-event supporting anchors required; partial coverage/omission retained when not supported. |
| 3 | Resolve project aliases and repository/service/model-version scope only through explicit provenance. | Tests for same-project aliases, unrelated entities, differing versions, future-work limitations and unresolved scope; narrowing or omission when ambiguous. |
| 4 | Investigate J04 positive-evidence recovery. | Bounded source-to-capability representation or other separately reviewed remedy; cannot promote code/setup facts into candidate achievements. |
| 5 | Run full deterministic and integrity gates on the changed revision. | Exact pass/fail/skip/protected-block accounting; no weakened tests or changed benchmark inputs. |
| 6 | Conduct a controlled, authorized BASE acceptance run under Slurm when prerequisites pass. | Source/input/model manifests, controls, raw outputs, independently reviewed requirements/claims/omissions, and non-agent gate satisfied. |
| 7 | Consolidate operational entry points and reproduction documentation in a new version. | Clear active source location, dependency snapshot and durable version-control strategy; preserved immutable history. |
| 8 | Only after non-agent acceptance: teach and review agent architecture with the owner. | Owner understands state, tools, control loops, permissions, evaluation, failure recovery, costs and observability; explicit agreement on a bounded initial agent. |

No evidence justifies immediate retraining, learned reranker promotion, new vector infrastructure, or expanded autonomous scope. Those are not substitutes for the demonstrated deterministic defects.

## 15. Immediate Next Action

**In a new working package copied from the sealed October 8 source, reproduce and then repair the discovery/independent-licensing boundary.** Start with:

- `V:test_discovery_license_boundary.py` and its recorded failing result;
- `V:new-fallback-forensic-J11.json`;
- `application/resume_pipeline/pipeline.py`, `_assess_selection` (current source around lines 205–237);
- `application/resume_pipeline/reselection.py`, `exclusions` (around lines 18–33);
- `application/resume_pipeline/semantic_policy.py`, candidate ranking/fallback relationships.

Desired invariant: discovery membership may influence ranking, but cannot reject an otherwise eligible canonical pair before independent licensing. Only an actual independently evaluated rejection should create the corresponding semantic exclusion; genuine factual contradiction remains blocked. Avoid case-ID branches, benchmark-specific wording, loosened truth gates, or automatic acceptance of model selections.

Acceptance for this first repair is the general regression plus targeted positive/negative lifecycle tests and unchanged safety invariants. It does **not** close J02, scope/version issues, J04, or the full non-agent readiness gate. Do CPU work first; do not rerun completed inference or retrain to diagnose this known deterministic failure.

## 16. Development Safety Rules

The next coding agent must:

1. Preserve existing base weights, adapters, checkpoints and their manifests; never merge, replace or silently promote a model.
2. Preserve all datasets, evaluation inputs, raw outputs, benchmark reports, failed attempts and sealed archives.
3. Use new working copies and exclusive output paths. Avoid deletion, cleanup of “old” checkpoints, destructive sync, in-place reformatting or reset operations.
4. Never run Qwen inference, training or GPU-intensive work on login nodes. Request resources through Slurm; release allocations when complete.
5. Avoid retraining unless an independently demonstrated model limitation remains after correcting the pipeline and a separate training protocol is authorized.
6. Verify changes through reproducible tests, source/input hashes and appropriate acceptance evaluation; preserve previously working functionality.
7. Never fabricate metrics or describe schema validity, job exit status, no unsupported final claims, or high retrieval scores as full semantic acceptance.
8. Keep protected evaluation data and final answers out of training, tuning and case-specific rules. Preserve protected-read guards; blocked tests are not passes.
9. Keep environment variables/credentials out of reports except variable names. Do not publish candidate evidence or credentials.
10. Distinguish public project evidence from personally verified achievements. Preserve project, event, version, academic scope, numbers and uncertainty.
11. Do not loosen factual or safety gates to recover an empty resume. Correct the earliest faulty boundary and document remaining failures.
12. Finish and verify the non-agent pipeline before autonomous agents. The owner's agent-architecture learning requirement is a separate prerequisite, even after tests pass.
13. Do not implement ULTRON, browser agents, outreach sending, or application submission under this handoff/audit scope.

## 17. Future ULTRON Integration

**FUTURE PLAN / INFERRED DESIGN ONLY:** ULTRON is the owner's planned platform for Qwen core intelligence, distillation, QLoRA, RAG, tool orchestration, evaluation, inference serving and controlled self-improvement. None of the following is a completed Resume AI integration.

| Future ULTRON component | Potential Resume AI interface | Required gate |
|---|---|---|
| Qwen intelligence / serving | Versioned request/response contract around approved BASE or a later promoted model. | Non-agent acceptance, serving resource measurements, traceable model/version routing. |
| RAG / memory | Reuse canonical scope, evidence/source revisions, citations and semantic-space identity. | Production persistence and authorization tests; evidence access distinct from model memory. |
| Tool orchestration | Expose deterministic ingestion, retrieval, validation and rendering as bounded tools. | Explicit permissions, argument schemas, idempotence, error contracts and audit logs. |
| Distillation / QLoRA | Curated authorized examples with provenance and split isolation. | No final-test leakage, separate training protocol, held-out evaluation and rollback. |
| Evaluation | Shared artifact manifests, negative controls and semantic acceptance gates. | Independent evaluation remains outside the runtime's authority to approve itself. |
| Controlled self-improvement | Proposal → sandboxed change → tests → independent review → explicit promotion. | Frozen references, rollback, resource/cost limits and human-controlled approval boundaries. |

Before implementing agents, teach the owner the difference between a fixed workflow and an agent; state and memory; planning versus execution; tool authority and prompt injection; bounded retries; checkpoint/recovery; human review; observability; evaluation; and model/data promotion. Then design one bounded use case only after Resume AI's non-agent pipeline is accepted. ULTRON planning must not reinterpret the current failed gate as readiness.

## 18. Evidence and Source File References

All references below were checked for existence against the live Turing inventory or the local sealed package, whose full remote archive digest was independently verified. `V:` files are members of that package; `R:` files are relative to the Turing root. Directory references identify code/artifact groups and are not claims that every byte of every large artifact was read.

### E01 — Latest final decision and completed state

- `V:FINAL_REPORT.txt`
- `V:WORK_STATE.json`

### E02 — Final acceptance metrics, exact case pass/fail and dimensions

- `V:full-v1-acceptance-metrics.json`
- `V:independent-multidimensional-audit-final.json`

### E03 — Cohort identity, inputs and historical reuse

- `V:completed-case-manifest.json`
- `V:full-v1-shard-0-pre-manifest.json`
- `V:historical-gate.json`

### E04 — Corrected final CPU accounting and failed gate

- `V:final-regression-accounting.json`
- `V:regression-accounting-correction.json`
- `V:final-regression-gate.json`
- `V:final-cpu-console.txt`

### E05 — Reproducible discovery-license failure

- `V:test_discovery_license_boundary.py`
- `V:discovery-license-regression-results.json`
- `V:new-fallback-forensic-J11.json`

### E06 — Base architecture, tokenizer and actual inference configuration

- `R:models/Qwen3.8-27B/config.json`
- `R:models/Qwen3.8-27B/tokenizer_config.json`
- `R:work/semantic-contracts-20261008/full-v1-shard-0/production-model-configuration.json`

### E07 — Controlled final model decision and aggregate comparison

- `R:results/stage4c1/FINAL_REPORT_20261002.txt`
- `R:results/stage4c1/final_promotion.json`
- `R:results/stage4c1/final_comparison.json`
- `R:results/stage4c1/selection_decision.json`

### E08 — QLoRA smoke mechanics, memory, failed attempts and reload

- `R:results/stage4b/smoke/report.md`
- `R:stage4b/engine.py`
- `R:adapters/stage4b_smoke/adapter_config.json`
- `R:results/stage4b/smoke/memory_metrics.jsonl`

### E09 — Controlled training config, actual phase exposures and adapter metadata

- `R:stage4c1/training_config.json`
- `R:stage4c1/train.py`
- `R:stage4c1/train.slurm`
- `R:results/stage4c1/interleaved/phase_report_000124.json`
- `R:results/stage4c1/evidence_only/phase_report_000131.json`
- `R:adapters/stage4c1/run_430001/evidence_only/checkpoint_000131/adapter_config.json`

### E10 — Embedding identity and measurements

- `R:results/stage3c/models.lock.json`
- `R:results/stage3c/model0-evaluation.json`
- `R:docs/stage3c_report.md`
- `V:application/rag/embeddings/local.py`

### E11 — Storage decision and implemented reference

- `R:docs/adr/vector_store_selection.md`
- `R:docs/stage3d_report.md`
- `R:migrations/001_vectorstore_sqlite.sql`
- `V:application/rag/vectorstore/sqlite_reference.py`

### E12 — Retrieval variants and default

- `R:docs/stage3e_report.md`
- `V:application/rag/retrieval/service.py`
- `V:application/rag/retrieval/models.py`

### E13 — Reranker identities, non-promotion and metrics

- `R:results/stage3f/models.lock.json`
- `R:docs/stage3f_report.md`
- `R:results/stage3f/identity.json`
- `R:results/stage3f/minilm.json`
- `R:results/stage3f/tinybert.json`

### E14 — Frozen component retrieval and acronym repair

- `R:docs/stage3j_report.md`
- `R:results/stage3j/frozen-rag-configuration.json`
- `V:application/rag/deep/retrieve.py`

### E15 — Original baseline and prompt engineering

- `R:results/baseline/base-v1-2325384-eval3/summary.md`
- `R:results/prompt_engineered/grounded-v3-benchmark-2325384-1/report.md`
- `R:eval/README.md`

### E16 — Professional curriculum and task scope

- `R:docs/STAGE4C0_FINAL_REPORT.md`
- `R:datasets/stage4c0/v1/statistics.json`
- `R:datasets/stage4c0/v1/manifest.json`
- `R:docs/curriculum_design.md`

### E17 — Recorded long-term roadmap

- `R:stage4b/ROADMAP.md`
- `R:docs/future_training_and_evaluation.md`

### E18 — Latest implemented runtime and licensing pipeline

- `V:application/resume_pipeline/runtime.py`
- `V:application/resume_pipeline/pipeline.py`
- `V:application/resume_pipeline/licensing.py`
- `V:application/resume_pipeline/reselection.py`
- `V:application/resume_pipeline/semantic_contracts.py`
- `V:application/resume_pipeline/__main__.py`
- `V:application/resume_pipeline/output.schema.json`

### E19 — Sealed package and archive provenance

- `V:SHA256SUMS.json`
- `V:archive-destination.json`
- `R:work/semantic-contracts-20261008/archive-semantic-validation-final-20261008T151118Z/resume-ai-semantic-validation-20261008-final.zip`
- `R:work/semantic-contracts-20261008/archive-semantic-validation-final-20261008T151118Z/resume-ai-semantic-validation-20261008-final-archive-metadata.json`

### E20 — Evidence and chunking history

- `R:docs/stage3a_report.md`
- `R:docs/stage3b_report.md`
- `V:application/rag/domain.py`
- `V:application/rag/ingestion.py`
- `V:application/rag/chunking/policy.py`

### E21 — Reasoning, scale and partial component repair

- `R:docs/stage3g_report.md`
- `R:docs/stage3h_report.md`
- `R:docs/stage3i_report.md`

### E22 — Evidence curriculum and proposed versus actual training

- `R:docs/stage4a_report.md`
- `R:datasets/stage4a/v1/statistics.json`
- `R:datasets/stage4a/v1/manifest.json`

### E23 — Post-training constrained/semantic/source-bound experiments

- `R:results/constrained_generation/v2-20261003/REPORT.txt`
- `R:results/semantic_grounding/v1.1-20261004/REPORT.txt`
- `R:results/source_bound/v1-20261004/REPORT.txt`
- `R:results/evidence_bound_planner/v1-20261004/REPORT.txt`
- `R:results/licensed_claims/v1-20261004/REPORT.txt`

### E24 — Deterministic final-development compiler iterations

- `R:results/final_development/v1-20261005/REPORT.txt`
- `R:results/final_development/v2-20261005/REPORT.txt`

### E25 — October 7 predecessor / current comparison

- `V:before-after-metrics.json`
- `V:failure_root_cause_matrix.json`
- `V:forensics/`

### E26 — Current model/training decision

- `V:model-decision.json`

### E27 — Remaining root causes and detailed case audits

- `V:remaining-root-cause-blockers.json`
- `V:new-specificity-forensic-J02.json`
- `V:specificity-contract-diagnostics.json`
- `V:qa-source-scope-review.json`
- `V:independent-full-v1-J04-audit.json`
- `V:independent-full-v1-J07-audit.json`
- `V:independent-full-v1-J13-audit.json`

### E28 — Stale interruption note and completed job accounting

- `V:RESUME_NEXT.txt`
- `V:final-slurm-accounting.json`
- `V:network-recovery-reconciliation.json`

### E29 — Environment and reproduction source

- `R:.venv/pyvenv.cfg`
- `R:results/stage4b/smoke/environment-cpu.json`
- `V:REPRODUCE.txt`
- `V:run_tests.py`
- `V:full-v1-shard-0.sbatch`

### E30 — Preservation and mechanical verification

- `V:final-verification.json`
- `V:application-continuation-integrity.json`
- `V:protected-metadata-final.json`
- `V:final-regression-gate.json`

### Audit verification and evidence limits

Audit-time checks established the live root, absence of Git metadata, Python/package versions and Slurm availability. Source inspection covered the historical architecture/training scripts and the latest pipeline. Model weights were not loaded; dataset contents were not regenerated. The latest package's 3,450 manifest-covered files all matched SHA-256, and all 131 Python application sources matched the corresponding live full-v1-shard-0 snapshot. The 80,189,386-byte final ZIP matched its recorded full SHA-256 on Turing. The 30-case table was recounted directly: 23 passes and exactly the seven failures listed in section 9. Embedding/reranker figures were checked against their machine-readable metrics; training exposure/configuration and final promotion were checked against JSON artifacts, not inferred from filenames.

Live scheduler accounting confirmed:

| Job | Role | State / exit | Elapsed |
|---|---|---|---|
| 2351800 | Historical v11 shard 0 | COMPLETED / 0:0 | 00:17:39 |
| 2351801 | Historical v11 shard 1 | COMPLETED / 0:0 | 00:25:50 |
| 2351871 | Remaining full-v1 shard 0 | COMPLETED / 0:0 | 00:55:45 |
| 2351872 | Remaining full-v1 shard 1 | COMPLETED / 0:0 | 01:03:35 |
| 2351873 | Remaining full-v1 shard 2 | COMPLETED / 0:0 | 00:54:03 |

The complete historical test suites, full fresh inference, all historical raw semantic judgments and every large model-weight hash were not independently rerun/re-adjudicated during this handoff. Saved results remain evidence with their stated scope. The latest source/hash comparison is stronger than a report-only assumption but not a new full acceptance run. No internet facts or current vendor/model-release claims were needed for this repository audit.

Preservation verification compares initial/final metadata for every preexisting remote file (size, nanosecond modification time and mode), plus SHA-256 for the 5,754 eligible small source/document/script files inventoried before writing. This is not a claim to have independently rehashed all model weights. Immediately before delivery, all 54,414 preexisting file metadata records and 5,754 selected source/document/script hashes matched the initial inventory. The only intended new project file is `PROJECT_HANDOFF.md`; a final post-write comparison is required by the delivery routine and any discrepancy stops delivery verification.

## 19. Open Questions

1. What is the original upstream identity/revision of the locally named Qwen checkpoint? Architecture is established; upstream provenance is not.
2. What explicit project aliases and service/model-version relationships should resolve the four partially supported QA-related claims? Use canonical evidence; do not assume same-version contradiction or identity.
3. How can substantial implementation evidence be represented for J04 without treating configuration/code presence as personal achievement? No verified remedy exists yet.
4. What clean-install dependency manifest and cluster module recipe reproduce the entire current environment? Live versions are known; a clean rebuild has not been tested.
5. Which currently skipped historical tests should be made available under a permissible artifact layout, and which protected checks must remain separately blocked?
6. What are the approved production data-retention, authorization, availability, concurrency and latency requirements? No deployment acceptance evidence was found.
7. Is the product's next release limited to extractive resumes, or must all ten professional tasks pass a new integrated gate? Curriculum breadth does not settle product scope.
8. How should version control be introduced without changing sealed snapshots? No Git commit history is available to recover from this tree.
9. What level of independent human review will be required beyond recorded model-assisted semantic audits before real candidate-facing release?
10. After non-agent acceptance, what learning sequence and bounded agent use case does the owner want? Do not infer authorization for agents from this handoff.

## 20. Instructions for Claude Opus 5.5

Read sections 1, 10, 11 and 15 first. Then inspect E01–E05 and the latest source snapshot. Treat this handoff as an index to evidence, not permission to override manifests, preserved negative decisions or the owner's development gate.

1. Reconfirm access, current root, queue and whether any new work exists after this audit. If the tree has changed, reconcile its evidence before assuming this is still the latest state.
2. Verify the sealed final package and source/input bindings. Preserve it. Work in a new copy of the v11 application; never edit the frozen package or root historical artifacts as a shortcut.
3. Do not restart completed jobs, re-author benchmark inputs, regenerate datasets, re-download the base under a different name, or promote the step-124 adapter.
4. Reproduce the known deterministic failure and fix the earliest discovery/licensing boundary first, preserving semantic rejection and every scope/provenance/contradiction gate. Document the change against general invariants, not case IDs.
5. Address remaining specificity, version/scope and positive-evidence recovery failures in the prioritized order, with bounded general tests and immutable experiment results.
6. Re-run appropriate CPU tests and integrity gates. Separate passes, failures, skips and protected blocks. Only proceed to authorized Slurm inference when the exact changed-source prerequisites pass.
7. Independently review the full non-agent output contract: factual entailment, content eligibility, project/event identity, detailed requirement licensing, useful positive-case recovery and correct abstention. Passing syntax or zero final unsupported claims is insufficient.
8. Keep BASE and adapters immutable. Do not train unless a separate evidence-backed, authorized training plan is justified. Do not use protected final answers as training corrections.
9. Keep autonomous agents and ULTRON out of the implementation until the non-agent pipeline is verified and the owner has learned agent architecture thoroughly. Then obtain a clearly scoped next development instruction.
10. End each development stage with exact source/input/model hashes, commands, measured outcomes, unresolved defects, resource accounting and the next bounded task. Report UNKNOWN when evidence is absent; never invent improvements or completion.

The handoff's immediate recommendation is a CPU-first deterministic licensing repair, not a new model experiment or agent build.
