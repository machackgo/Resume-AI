# Stage 3C completion report

Stage 3C is complete. Provisional experimental choice: **all-MiniLM-L6-v2 with title-section-v1**, keeping raw-v1 as an ablation. This is a small synthetic screening result, not a production endorsement. Stage 3D has not begun.

## 1. Architecture implemented

Additive provider-independent embedding contracts, exact chunk-revision references, scoped ephemeral cache, versioned input construction, numeric validation, cosine utilities, local encoder and exhaustive in-memory evaluation. See `stage3c_architecture.md` for invariants and commands.

## 2. Files created/modified

No preexisting file was modified. New files:

- `rag/embeddings/__init__.py`
- `rag/embeddings/audit.py`
- `rag/embeddings/base.py`
- `rag/embeddings/benchmark.py`
- `rag/embeddings/cache.py`
- `rag/embeddings/evaluate.slurm`
- `rag/embeddings/evaluation.py`
- `rag/embeddings/input_builder.py`
- `rag/embeddings/integration.py`
- `rag/embeddings/local.py`
- `rag/embeddings/models.py`
- `rag/embeddings/prepare.py`
- `rag/embeddings/similarity.py`
- `rag/embeddings/validate.py`
- `fixtures/rag/embedding_eval/resume_semantics_v1.json`
- `tests/rag/test_embeddings.py`, `tests/rag/test_embedding_eval.py`
- `docs/stage3c_architecture.md`, `docs/stage3c_report.md`
- `results/stage3c/`: model lock/assets hashes, two evaluation reports, 16 input/vector/record exports, unit/regression logs, frozen replay validation, real-model integration checks, Slurm logs, baseline manifest and delivery checksums.
- `models/stage3c/`: two isolated pinned public model snapshots; no existing model changed.

## 3. Embedding record/schema

Frozen dataclass with Scope, chunk ID/revision, evidence/source/version, policy ID, provider/model/revision/dimension/normalization/config, input version/hash, vector, creation timestamp, trust/origin, support IDs and provenance-event IDs. Full lineage resolves through the existing citation API. Verification state remains in authoritative versioned supports rather than a stale copied boolean.

## 4. Provider abstraction

EmbeddingProvider exposes explicit document/query methods and an immutable configuration fingerprint. Core code has no vendor imports. Transformers is isolated in the optional local adapter; no paid API or key is required. Ordered batches are validated before publication.

## 5. Embedding-input strategy

Compared raw-v1 against title-section-v1 using only the existing source title, locator section and chunk text. Security IDs, authority annotations and trust labels are excluded. Prefixes belong to the provider and participate in cache identity. Both strategies preserve untrusted-data status.

## 6. Models evaluated

| Model | Pinned revision | Parameters | Dimension | License | Document / query |
|---|---|---:|---:|---|---|
| sentence-transformers/all-MiniLM-L6-v2 | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` | 22,713,216 | 384 | apache-2.0 | `(empty)` / `(empty)` |
| intfloat/e5-small-v2 | `ffb93f3bd4047442299a41ebb6fa998a38507c52` | 33,360,000 | 384 | mit | `passage: ` / `query: ` |

License and encoder behavior were checked against pinned model cards/assets: [MiniLM](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41) and [E5](https://huggingface.co/intfloat/e5-small-v2/tree/ffb93f3bd4047442299a41ebb6fa998a38507c52). Apache-2.0 and MIT are permissive for future product use subject to their terms; this is not a full downstream license review.

## 7. Selection rationale

Two compact credible open encoders fit the existing Torch/Transformers environment and a CPU allocation. MiniLM tests symmetric sentence encoding; E5 tests asymmetric retrieval prefixes. Both support batches, local/offline inference and 384-dimensional storage. Neither is selected from leaderboard reputation. Both are English-focused; multilingual quality is untested. No extra packages, large-model downloads or GPU allocation were needed.

## 8. Semantic dataset

Frozen `resume-semantics-v1`: 22 queries, 44 non-private synthetic documents, 20 text distinctions and two intentionally indistinguishable metadata-only cases. Covers Python APIs, Docker/Kubernetes, AWS/Azure, FastAPI/Flask, PyTorch/TensorFlow, RAG/fine-tuning, LoRA/QLoRA, PostgreSQL/SQL, deep/classical ML, inference/training, built/used/deployed/designed, authority/verification, familiarity/production and quantified outcomes. A malicious certification instruction is included. Each query has one specified positive and hard negative. Titles are shared within each pair, not answer-bearing labels.

Claims about issuer checks or external observation are synthetic text, not authenticated assertions about anyone. Metadata-only labels are evaluation annotations and do not create verified supports. A second deterministic corpus variant adds routine project prose around each sentence for an exploratory policy test.

## 9–10. Pairwise, hard-negative and ranking results

All 22 queries; short corpus; A and B generate the same 44 semantic inputs. Metrics identify the designated target evidence.

| Model | Input strategy | Recall@1 | Recall@3 | MRR | Hard-negative wins |
|---|---|---:|---:|---:|---:|
| all-MiniLM-L6-v2 | raw-v1 | 59.09% | 90.91% | 0.7652 | 81.82% |
| all-MiniLM-L6-v2 | title-section-v1 | 68.18% | 90.91% | 0.8030 | 86.36% |
| e5-small-v2 | raw-v1 | 63.64% | 81.82% | 0.7554 | 77.27% |
| e5-small-v2 | title-section-v1 | 50.00% | 81.82% | 0.6703 | 72.73% |

Excluding the two deliberately metadata-only cases, MiniLM title-section-v1 achieves **75% Recall@1, 95% Recall@3, 0.8458 MRR and 95% hard-negative wins (19/20)**. E5 raw-v1 achieves **70%, 85%, 0.7960 and 85% (17/20)**. These subset results do not remove the need to handle authority metadata.

Pairwise detail, full 44-source rankings and top-three dangerous neighbors appear in each `modelN-evaluation.json`. All 16 experiments retain input strings, vectors, IDs, exact spans and query vectors in corresponding `*-records.json` exports. No human ordinal similarity scores or STS correlation are claimed.

## 11. Dangerous-neighbor failures

For MiniLM title-section-v1, short corpus:

- **Building versus consuming APIs:** relevant 0.5494 versus hard negative 0.6309; consuming an API ranks first and the intended implementation ranks third.
- **RAG versus fine-tuning:** pairwise positive 0.3287 barely exceeds negative 0.3273, while a used-retrieval-library document ranks first. Winning the designated pair does not guarantee top-one retrieval.
- **Training versus inference:** the training target ranks fourth; an inference-service document ranks first despite the designated training hard negative losing its pair.
- **Certification:** a metadata-only certificate mention ranks first for the verified-AWS query; issuer-confirmation text ranks third. Textual mention cannot establish verification.
- **Metadata-only origin and verification:** identical text ties exactly. Stable ID tie-breaking puts the negative first in a tie; no authority conclusion follows from either ordering.
- **Equivalent alternate evidence:** the QLoRA query retrieves `lora_negative` first; that document actually describes QLoRA. This is a designated-target miss, not a dangerous claim substitution. Symmetric LoRA/QLoRA cases intentionally expose the limitation of single-target judgments.

E5 raw-v1 additionally loses RAG/fine-tuning (0.7909 vs 0.7924) and training/inference (0.7905 vs 0.7992); its training target ranks 13th. E5 with context loses built/used (0.8805 vs 0.8942). Similarity scores have model-specific ranges and are not confidence or verification probabilities.

## 12. Policy A versus Policy B

Short evidence does not cross either limit, so equal scores provide **no policy-selection evidence**. The synthetic long-context probe yields 153 A chunks versus 86 B chunks. The following table includes all 22 queries; metadata-only cases can acquire spurious differences from surrounding filler, so use content-only metrics in the JSON when examining semantic distinctions.

| Model / input | Policy | Recall@1 | Recall@3 | MRR | Hard-negative wins |
|---|---|---:|---:|---:|---:|
| all-MiniLM-L6-v2 / raw-v1 | A | 63.64% | 86.36% | 0.7636 | 72.73% |
| all-MiniLM-L6-v2 / title-section-v1 | A | 68.18% | 86.36% | 0.7947 | 77.27% |
| all-MiniLM-L6-v2 / raw-v1 | B | 54.55% | 81.82% | 0.6966 | 77.27% |
| all-MiniLM-L6-v2 / title-section-v1 | B | 54.55% | 86.36% | 0.7091 | 81.82% |
| e5-small-v2 / raw-v1 | A | 63.64% | 77.27% | 0.7423 | 81.82% |
| e5-small-v2 / title-section-v1 | A | 45.45% | 81.82% | 0.6428 | 77.27% |
| e5-small-v2 / raw-v1 | B | 45.45% | 81.82% | 0.6498 | 63.64% |
| e5-small-v2 / title-section-v1 | B | 45.45% | 81.82% | 0.6367 | 68.18% |

A improves top-one evidence recovery in this probe. MiniLM context has higher hard-negative win rate with B, so there is a tradeoff. Repetitive filler, max-over-chunks scoring and one shared annotation pattern limit generalization. All top-one relevant hits also contained the target sentence. **Do not promote either policy as semantically optimal.** Retain B as the prior structural baseline and A as a serious semantic challenger; use more varied long documents before changing the default. Prior Stage 3B results remain unchanged.

## 13. Speed/resource comparison

CPU-only Slurm job 2328515: cs541 / academic, 4 CPUs, 8 GiB request, 62 seconds total, no GPU, completed exit 0. Each model ran in a separate process. Measured warm short-corpus Policy B timings include construction/validation of embedding records; query timings measure one warm batch.

| Model | Download MiB | Process peak RSS MiB | Raw docs/s | Context docs/s | Queries/s | Load seconds |
|---|---:|---:|---:|---:|---:|
| all-MiniLM-L6-v2 | 87.4 | 749.6 | 446.8 | 323.9 | 341.2 | 24.92 |
| e5-small-v2 | 128.2 | 790.4 | 227.2 | 151.9 | 220.3 | 4.24 |

Slurm batch MaxRSS was 2,339,808 KiB; it is a different scheduler/accounting measure from per-process ru_maxrss above. Cold load includes imports and filesystem cache effects; models loaded sequentially, so cold-load times are not a fair isolated speed contest. Warm timings are small single-run measurements, not production SLOs. CPU details and pip freeze are recorded in each report. MiniLM observed at most 116 tokens and E5 118, below pinned 256/512 limits. Same-batch query reruns had zero max absolute drift.

## 14. Tenant isolation

Tests embed identical text in two candidates and two tenants: vectors and semantic input hashes agree while cache/record IDs differ. Foreign chunks and foreign reference resolution are rejected. Tenant/candidate strings never enter model text. Scoped caching is conservative; no cross-tenant reuse is implemented. Future retrieval must bind scope using trusted authentication.

## 15. Provenance/trust

Every benchmark record round-tripped to its exact chunk revision and original source. Tests check support IDs, events, source IDs, malicious text, unreviewed support state, annotation revision reuse and tampered-reference rejection. No verification promotion occurs. Model output cannot change untrusted-data state; embedding similarity cannot distinguish identical text with different authority.

## 16. Tests and regressions

**125/125 unit/regression tests pass:** 40 Stage 3C, 39 Stage 3B, 27 Stage 3A, 19 prior-stage tests. Frozen Stage 2 replay succeeds, and Stage 3A/3B demos equal their saved results. All **276/276 preexisting files** are byte-identical, including the separately checked 256 pre-3B and 238 Stage 1/2 manifests. Prior benchmark outputs were not rewritten.

Frozen-vector replay reproduced **352 queries across 16 experiments**, including full evidence ordering and pairwise/metric values. Actual local-adapter smoke checks pass for both models (8 checks each): 384 dimensions, unit norm, explicit prefixes, symmetric/asymmetric behavior, empty batch, invalid/overflow rejection and batching agreement. MiniLM batch drift is zero; E5 maximum is 1.0571e-7. Stage 1 historical GPU benchmark scripts are preserved, not rerun; no new Stage 1/2 generative benchmark claims are made.

## 17. Provisional recommendation

Use pinned **all-MiniLM-L6-v2 + title-section-v1** as the first embedding candidate for later authorized experiments. It has the strongest primary-fixture MRR, Recall@3 and hard-negative win rate, fewer parameters and higher measured warm throughput. Keep raw-v1 and E5-small-v2 as controls. This choice is provisional and does not establish semantic entailment, verification safety, multilingual performance or a winning chunk policy.

## 18. Limitations

- Twenty text-distinction queries plus two metadata controls are a screening fixture, not a representative benchmark or independent held-out evaluation. No confidence interval or statistical superiority claim is justified.
- Single designated targets undercount valid alternate evidence (especially LoRA/QLoRA and certificate descriptions). Reported Recall@k is designated-evidence recovery; pairwise judgments remain directly inspectable. Add multi-relevant judgments and independent review before broader model selection.
- Hard-negative flags cover specified negatives, not every possible unsupported top result. Saved full rankings expose additional failures; embeddings do not provide entailment or truth assessment.
- The long-context probe is synthetic and repetitive; title context, claim-aware boundaries and max-over-chunks aggregation affect outcomes. No conclusion about real document chunking is established.
- Inputs and vectors are reproducible in the pinned environment; numerical identity across hardware, library versions or batch shapes is not guaranteed. Model configs and measured tolerances are preserved.
- The cache and ledger references are single-process fixtures; no deployed authentication, durable retrieval API, vector database or operational scale test exists.
- Offline inference is verified after initial public downloads. Exact package versions are captured, but a portable clean-machine dependency lock/wheel mirror is not supplied. The original environment was not changed.

## 19. Exact proposed Stage 3D boundary — NOT STARTED

A separately authorized Stage 3D should evaluate a minimal vector-store adapter for already generated embedding records: scoped upsert/query/delete, dimension/config compatibility, idempotence, source-version freshness, mandatory tenant/candidate filtering and exact citation resolution. Compare its nearest-neighbor results against this in-memory oracle using expanded, reviewed relevance judgments. Keep both A/B chunk inputs and the provisional embedding ablations available. Do not include production retrieval orchestration, hybrid search, reranking, Qwen RAG, QLoRA/fine-tuning or browser/job agents in that boundary without separate authorization.

**Stopped after Stage 3C. No Stage 3D code or vector store was built.**
