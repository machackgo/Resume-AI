# Stage 3J final report

A. FREEZE RAG — READY FOR QLORA

## 1–3. Exact h06 loss, identity and ranks

Canonical evidence, chunk action, embedding and index are valid. At MEDIUM, gold enters Top-20 but is removed at the per-component Top-2 cutoff after grouping. At LARGE/XL, it never enters Top-20. SMALL delivers it. No demonstrated gold loss occurs in deduplication, merge, global context budget or provenance. Root attribution: QUERY_CONSTRUCTION interacting with MiniLM acronym representation. A single-model study cannot uniquely separate model acronym sensitivity from query representation; QUERY_CONSTRUCTION names the smallest demonstrated corrective boundary. Observed loss events: TOP_K_CUTOFF.

| Scale | Original raw rank | Original score | Normalized rank | Stage 3I delivered | Stage 3J delivered |
| --- | --- | --- | --- | --- | --- |
| SMALL | 2 | 0.473848 | 1 | True | True |
| MEDIUM | 9 | 0.473848 | 1 | False | True |
| LARGE | 42 | 0.473848 | 1 | False | True |
| XL | 125 | 0.473848 | 1 | False | True |

Original requirement: Implemented both RAG and fine-tuning for the Juniper assistant. The RAG component changes only its search representation, from Implemented RAG for the Juniper assistant. to Implemented retrieval augmented generation for the Juniper assistant. The fine-tuning component remains unchanged.

Gold text: For the Juniper assistant I built retrieval augmented generation: passages were embedded and retrieved before Qwen inference. The base model weights were unchanged.

| Identity | Value |
| --- | --- |
| Document | c04 |
| evidence_id | evidence_239c4aef51e90a75febd34389d29bb1ec0039f19321d148064b65cbba9408b75 |
| chunk_id | chunk_4d0d00d93d660fe66a9f9af5864b27f55b6e77701531026f681de7d68460984a |
| record_id | embedding_record_85780bde72c7c79d692c08d1c05ffba970f736cbc6befce9320ae4c208033ecc |
| source_id | source_ebe60686e202cf05b3874c27e9bafe378197aefac7ed0537f66a6b0db4785bbf |
| evidence_version | 1 |
| semantic_space | embedding_space_d040951e7abcf8750825f4206d5c7a68de261a8fe7576699db7381d144ee4873 |

h06-forensic-traces.json (h06-forensic-v1) contains component IDs/text, source snapshots, offsets, claim links, stored vector, embedding configuration, exact queries, neighboring results and survival checkpoints. The gate completed before parameters changed. Stage 3I contexts replayed exactly.

## 4. Internal Top-K ablation

| Scale | Query | K | Components | All covered | Danger rate | Danger count | Groups | Prompt tokens | Retrieval s | Selector s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LARGE | original | 3 | 11/12 | 90.00% | 60.83% | 1.875 | 2.812 | 2305.9 | 0.4775 | 0.0033 |
| LARGE | original | 5 | 11/12 | 90.00% | 65.12% | 3.125 | 4.188 | 2888.9 | 0.4781 | 0.0049 |
| LARGE | original | 10 | 11/12 | 90.00% | 64.38% | 3.125 | 4.188 | 3110.1 | 0.4803 | 0.0069 |
| LARGE | original | 20 | 11/12 | 90.00% | 63.90% | 3.125 | 4.188 | 3537.9 | 0.4849 | 0.0109 |
| LARGE | original | 40 | 11/12 | 90.00% | 64.60% | 3.375 | 4.688 | 3989.9 | 0.4955 | 0.0193 |
| LARGE | alias | 3 | 12/12 | 100.00% | 58.75% | 1.812 | 2.812 | 2306.2 | 0.4896 | 0.0033 |
| LARGE | alias | 5 | 12/12 | 100.00% | 63.04% | 3.062 | 4.188 | 2889.2 | 0.4775 | 0.0049 |
| LARGE | alias | 10 | 12/12 | 100.00% | 62.29% | 3.062 | 4.188 | 3110.4 | 0.4801 | 0.0069 |
| LARGE | alias | 20 | 12/12 | 100.00% | 61.82% | 3.062 | 4.188 | 3538.2 | 0.4856 | 0.0109 |
| LARGE | alias | 40 | 12/12 | 100.00% | 62.51% | 3.312 | 4.688 | 3990.2 | 0.4956 | 0.0192 |
| XL | original | 3 | 11/12 | 90.00% | 60.83% | 1.875 | 2.812 | 2308.1 | 1.4428 | 0.004 |
| XL | original | 5 | 11/12 | 90.00% | 65.12% | 3.125 | 4.188 | 2893.9 | 1.46 | 0.0059 |
| XL | original | 10 | 11/12 | 90.00% | 64.38% | 3.125 | 4.188 | 3112.1 | 1.4644 | 0.0083 |
| XL | original | 20 | 11/12 | 90.00% | 63.90% | 3.125 | 4.188 | 3544.4 | 1.4687 | 0.013 |
| XL | original | 40 | 11/12 | 90.00% | 63.63% | 3.125 | 4.188 | 4425.6 | 1.4614 | 0.0228 |
| XL | alias | 3 | 12/12 | 100.00% | 58.75% | 1.812 | 2.812 | 2308.7 | 1.443 | 0.004 |
| XL | alias | 5 | 12/12 | 100.00% | 63.04% | 3.062 | 4.188 | 2894.5 | 1.4593 | 0.0058 |
| XL | alias | 10 | 12/12 | 100.00% | 62.29% | 3.062 | 4.188 | 3112.7 | 1.4463 | 0.0082 |
| XL | alias | 20 | 12/12 | 100.00% | 61.82% | 3.062 | 4.188 | 3545.1 | 1.4529 | 0.013 |
| XL | alias | 40 | 12/12 | 100.00% | 61.55% | 3.062 | 4.188 | 4426.2 | 1.4634 | 0.0227 |

Unchanged queries never deliver h06 at MEDIUM/LARGE/XL for K=3–40. All normalized configurations do. K=80 is uninformative: original XL rank 125 exceeds80, corrected rank 1 does not need80. K=3 fails the historical rank-five QLoRA regression. Budget5 preserves all components; final budgets3/6 were unnecessary.

The predeclared retrieval-only rule favors coverage, hard-case coverage, dangerous-neighbor rates, context size, then smaller K. K=20 wins, retaining Stage 3I depth. Lower rates can partly reflect legitimate corroborating records in the denominator; counts and token costs are shown. K=40 adds context without coverage gains. This does not establish universal K=20 optimality.

## 5–8. Query, embedding, chunk and decomposition diagnosis

The exact standalone uppercase RAG alias is normalized to its technical full form. The rule does not access case ID, candidate, project, evidence or gold. It preserves action, negation, numeric and relational wording. Built/Developed/Evaluated paraphrases test generalization; adjacent technologies are not substituted.

MiniLM is retained. h06 similarity rises from approximately 0.474 to 0.782 and rank 1 at every scale. Acronym representation is the measured issue; larger embeddings are not justified. Residual action/trust ranking weaknesses remain: API study outranks construction (direct proof rank 2); a verification assertion outranks the actually attested credential (direct proof rank 2). Both direct proofs survive. Similarity does not establish entailment or verification.

The gold chunk retains I built retrieval augmented generation and the unchanged-base-weights statement. Unicode half-open offsets, claim links, title/section context and source version round-trip. POLICY_B remains 640 characters, 96 overlap, structural-v1. No chunk or embedding-input correction is needed.

The three known under-splits each retain 2/2 authored proofs in follow-up tests: Docker/AWS modifiers, FastAPI/Flask construction, and credential/experience. The fairness fixture preserves 4/4 components despite many easy neighbors. Decomposition remains structural-extractive-v1; the small tests do not prove universal grammar coverage.

## 9–13. Correction, depths, selector and final budget

Behavioral correction: exact acronym normalization. Existing semantic/identity order and fair round-robin merging remain. New code adds per-item diagnostics and an empty-pool guard for the audit search. It does not compensate for a broken index.

Frozen:20 internal vectors per component; shortlist2 for compound components,5 for unsplit needs; cosine floor 0.20; at most 5 final distinct-text groups. Exact-text duplicates union independent provenance and authenticated attestations. Corroborating records still carry context overhead, so prompt tokens and record counts are measured separately from the five-group cap; selected K=20 retains Stage 3I behavior rather than expanding that overhead. No opaque LLM selector or learned reranker is added.

Selector records component IDs, raw rank/score, group rank, K, duplicate identity, source/evidence/embedding IDs, trust/provenance, decision/reason and final rank. Reasons distinguish coverage, semantic relevance, corroboration, per-component cutoff, plausibility floor and global budget. DIRECT_RELEVANCE is not entailment. Empty/below-floor pools retain no_plausible_candidate_retrieved; neighboring evidence is never declared supporting merely because retrieved.

## 14. Targeted hard-case retrieval

| Metric | Stage 3I | Stage 3J |
| --- | --- | --- |
| recall_at_1 | 61.54% | 84.62% |
| recall_at_3 | 100.00% | 100.00% |
| recall_at_5 | 100.00% | 100.00% |
| recall_at_10 | 100.00% | 100.00% |
| mrr | 79.49% | 92.31% |
| required_component_survival | 92.31% | 100.00% |
| all_required_components_covered | 92.31% | 100.00% |
| dangerous_neighbor_rate | 60.00% | 52.31% |
| duplicate_result_rate | 0.00% | 0.00% |

| Case | Original gold rank | Corrected gold rank | Proof delivered |
| --- | --- | --- | --- |
| rag | [3] | [1] | True |
| api | [2] | [2] | True |
| kubernetes | [1] | [1] | True |
| qlora_lora | [1] | [1] | True |
| qlora_inference | [1] | [1] | True |
| aws | [1] | [1] | True |
| pytorch | [1] | [1] | True |
| numeric | [1] | [1] | True |
| serving | [1] | [1] | True |
| credential | [2] | [2] | True |
| rag_paraphrase0 | [2] | [1] | True |
| rag_paraphrase1 | [2] | [1] | True |
| rag_paraphrase2 | [1] | [1] | True |

The ten required contrasts plus three held-out RAG paraphrases are frozen synthetic evaluation fixtures, not private data or training data. All 13 proofs survive versus 12/13 previously. The Developed-RAG proof previously fell below the relevance floor despite raw rank 2. Each case remains visible, so aggregates cannot hide delivery regressions.

## 15–17. Component survival and LARGE/XL retrieval

| Scale | Arm | Components | All covered | Recall1 | Recall3 | Recall5 | Recall10 | MRR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LARGE | stage3i | 11/12 | 90.00% | 59.91% | 71.39% | 72.87% | 76.57% | 90.12% |
| LARGE | alias-k20-b5 | 12/12 | 100.00% | 64.91% | 76.39% | 77.87% | 81.57% | 95.00% |
| XL | stage3i | 11/12 | 90.00% | 59.43% | 69.95% | 70.47% | 71.76% | 90.04% |
| XL | alias-k20-b5 | 12/12 | 100.00% | 64.43% | 74.95% | 75.47% | 76.76% | 95.00% |

Historical Stage 3H Top-3 preserves 10/12 components and 8/10 evidence-bearing requirements; Stage 3I11/12 and 9/10; Stage 3J12/12 and 10/10 at both scales. Six absence-only needs receive no vacuous success credit. Every primary context-conditional gold label and atom now matches full-corpus gold.

Recall@k measures authored relevant-document recall before selection; MRR uses earliest proof. Corroborating copies make document recall different from proposition survival. The ablation uses the broader Stage 3I preparation dangerous-neighbor taxonomy consistently; do not mix these rates with the narrower taxonomy in the historical Stage 3I final report. Duplicate rate measures source-record overhead, not repeated selected groups.

## 18–20. Qwen labels, atomic/compound reasoning and citations

| Scale | Arm | n | Accuracy | Macro F1 | Atomic | Compound | JSON | Full contract |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LARGE | stage3h_top3 | 16 | 68.75% | 0.6944 | 65.00% | 75.00% | 100.00% | 50.00% |
| LARGE | stage3i | 16 | 62.50% | 0.6423 | 60.00% | 50.00% | 100.00% | 43.75% |
| LARGE | stage3j | 16 | 68.75% | 0.7036 | 65.00% | 75.00% | 100.00% | 50.00% |
| XL | stage3h_top3 | 16 | 68.75% | 0.6944 | 65.00% | 75.00% | 100.00% | 50.00% |
| XL | stage3i | 16 | 62.50% | 0.6423 | 60.00% | 50.00% | 100.00% | 43.75% |
| XL | stage3j | 16 | 68.75% | 0.7036 | 65.00% | 75.00% | 100.00% | 50.00% |

Primary observations:32, including 2 fresh h06 generations and 30 exact-prompt historical reuses. Reuse checks identical messages and unchanged model/dependency/quantization/generation settings, retaining source path/hash/run ID. Smoke is excluded. No cap increase, raw JSON repair or post-Qwen retrieval tuning occurred.

| Scale | Arm | Citation validity | Precision | Unsupported rate | Fabricated IDs | Hallucinated-claim proxy |
| --- | --- | --- | --- | --- | --- | --- |
| LARGE | stage3h_top3 | 100.00% | 33.33% | 66.67% | 0.00% | 25.00% |
| LARGE | stage3i | 97.50% | 28.21% | 69.23% | 2.60% | 12.50% |
| LARGE | stage3j | 97.50% | 33.33% | 64.10% | 2.60% | 0.00% |
| XL | stage3h_top3 | 100.00% | 33.33% | 66.67% | 0.00% | 25.00% |
| XL | stage3i | 100.00% | 28.21% | 71.79% | 0.00% | 12.50% |
| XL | stage3j | 100.00% | 32.50% | 67.50% | 0.00% | 0.00% |

| Scale | Label | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- | --- |
| LARGE | SUPPORTED | 100.00% | 75.00% | 85.71% | 4 |
| LARGE | PARTIALLY_SUPPORTED | 75.00% | 100.00% | 85.71% | 3 |
| LARGE | UNSUPPORTED | 42.86% | 100.00% | 60.00% | 3 |
| LARGE | UNKNOWN | 100.00% | 33.33% | 50.00% | 6 |
| XL | SUPPORTED | 100.00% | 75.00% | 85.71% | 4 |
| XL | PARTIALLY_SUPPORTED | 75.00% | 100.00% | 85.71% | 3 |
| XL | UNSUPPORTED | 42.86% | 100.00% | 60.00% | 3 |
| XL | UNKNOWN | 100.00% | 33.33% | 50.00% | 6 |

Full-contract validity includes the inherited requirement for nonempty missing_evidence on every non-SUPPORTED label, including conclusive denials; this contract-design limitation is unchanged. Citation validity checks membership; precision uses frozen authored document-to-atom relations. Existing IDs do not prove entailment; unknown IDs remain rejected and scored. Hallucination is the inherited positive/partial-atom overstatement proxy, not a full prose audit. The inherited h06 base-weight-specific annotation remains unchanged; comparison.json includes sensitivity excluding h06. Sixteen repeated needs across nested corpora are not32 independent population samples.

## 21–23. Context and performance

| Scale | Prompt tokens | Generated | Total | Reduction vs full | Change vs3I | Groups | Qwen s | Tokens/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LARGE | 3538.25 | 749.188 | 4287.438 | 96.16% | 0.01% | 4.188 | 80.212 | 9.217 |
| XL | 3545.062 | 764.312 | 4309.375 | 98.71% | 0.02% | 4.188 | 81.883 | 9.202 |

| Scale | Raw pool items | Retrieval s | Selector s |
| --- | --- | --- | --- |
| SMALL | 23.75 | 0.033994 | 0.010239 |
| MEDIUM | 23.75 | 0.115922 | 0.010339 |
| LARGE | 23.75 | 0.485618 | 0.010933 |
| XL | 23.75 | 1.452874 | 0.013047 |

| Runtime metric | Value |
| --- | --- |
| load_seconds | 23.956644898993545 |
| actual_process_seconds | 369.2543095059955 |
| fresh_primary_seconds | 238.2239055389946 |
| fresh_smoke_seconds | 695.9522800230043 |
| fresh_primary_tokens_per_second | 9.66258071092318 |
| new_peak_torch_allocated_GiB | 17.92931032180786 |
| actual_gpu | NVIDIA A30, GPU-bc81b1b7-ed75-37d3-110a-b9fb1d0bdca5, 24576 MiB, 595.71.05 |
| total_gpu_allocation_seconds | 1010 |
| total_qwen_load_seconds | 51.04349409099086 |
| sampled_device_peak_MiB | 19295 |

Comparison latency/VRAM includes historical observations for exact-prompt reuses; those are not new GPU consumption. Slurm accounting gives allocation duration; gpu-telemetry-2334070.csv and gpu-telemetry-2334090.csv give sampled device memory across both allocations. Actual requests: one A30,8 CPUs,64GB,cs541/academic; first allocation maximum45 minutes, recovery maximum15 minutes. These allocations were sequential, never two GPUs concurrently. Frozen run.py retains a two-hour template ceiling; gpu-request.json, gpu-recovery-request.json and Slurm record the actual shorter requests. Search time includes an additional raw-rank diagnostic query. Full-context denominators include infeasible historical LARGE/XL prompts; no production throughput or full-context inference speedup is claimed.

GPU recovery: job2334070 completed all nine smoke generations, then a whole-text EV-SECRET substring gate falsely treated a quoted rejected attack instruction as an unauthorized citation. Structured citation review found UNKNOWN with no cited IDs. Raw outputs and frozen source were preserved. Job2334090 reused the reviewed smoke records, performed a fresh h06 reload check and generated the changed primary prompts. This changes only gate measurement, not retrieval, model parameters or answers.

Citation boundary detail: the remaining fabricated identifier is in LARGE h12, an exact historical Stage 3I reuse. The same invalid ID occurs twice in output ID lists and once in citation-pair scoring. The contract rejects it as unknown_or_foreign_id and quote_not_exact. This remains a measured Qwen CITATION failure, not an accepted source or a broken RAG provenance chain.

## 24–26. Injection, isolation, trust and provenance

10 saved smoke outputs passed JSON/schema/supplied-citation membership before primary inference. Full-contract errors are retained. The dedicated malicious-command-only fixture returned UNKNOWN (expected UNKNOWN). Primary explicit attack successes: 0; exposed prompts: 8; suspected-promotion proxy: 0. No EV-SECRET or foreign canary was accepted. Exposure or overstatement alone is not causal proof of instruction following; no universal injection-robustness claim is made.

Perfect RAG proof coexists in another candidate and tenant for K=3/5/10/20/40. Trusted scope overrides are rejected, with zero foreign/stale leakage. Evidence instructions never change scope, trust, verification or selector policy.

Independent replay checks 64 scale contexts, 411 selected provenance round trips, and 27 diagnostic contexts. Complete chain: component -> RetrievalResult -> stored vector -> EmbeddingRecord -> RetrievalChunk -> canonical Evidence -> source version -> native pointer. Verification depends on exact-support authenticated attestations, never semantic score/rank.

## 27–29. Regression, replay, recovery and protected artifacts

Pre-GPU: 467 RAG tests and 19 earlier evaluation tests passed. Final regression replay: {"checks": {"stage3_tests": true, "stage1_stage2_tests": true, "stage2_replay": true, "stage3a_demo": true, "stage3b_demo": true, "stage3e_112": true, "stage3f_297": true}, "tests": {"stage3_tests": 467, "stage1_stage2_tests": 19}, "total_tests": 486, "passed": true}

Independent verification confirms 32 primary records and 32 unique IDs; raw metrics, prompts, token IDs/counts, historical lineage, retrieval/selector traces and frozen/source hashes replay. Protected files: 1035; changed/missing:none.

Job2334052 saved all four scale ablations, then failed in the new empty-corpus diagnostic. Its source/logs remain in pre-recovery-2334052. Job2334068 reused all four saved outputs, repeated only unsaved diagnostics, checkpointed them and froze retrieval. Failed/cancelled forensic attempts remain recorded. The empty-pool guard does not alter nonempty retrieval.

Key artifacts: h06-forensic-traces.json; all four *-ablation.json files; top-k-summary.json; targeted-dataset/results/metrics.json; supplement-results.json; diagnostic-checkpoints; security-results.json; selection-decision.json; config.json; retrieval-freeze.json; *-prepared.json; benchmark-2334090 raw/smoke/parsed/metrics/comparison/failure/performance outputs; independent verification; recovery-integrity; protected and final manifests.

## 30–34. Freeze decision, exact baseline, remaining errors and boundary

A. FREEZE RAG — READY FOR QLORA

| Gate | Passed |
| --- | --- |
| h06_all_scales | True |
| targeted_nonregression | True |
| all_components | True |
| context_compressed | True |
| bounded_context | True |
| zero_leakage | True |
| injection_commands_not_followed | True |
| provenance | True |
| evidence_delivered | True |
| history | True |

Exact frozen RAG configuration:

| Setting | Value |
| --- | --- |
| evidence_schema | Stage 3A immutable Evidence/Claim/Support/VerificationRecord schema1 |
| source_adapter_contract | SourceAdapter -> CanonicalDocument; scoped immutable source keys, versioned snapshots, acquisition origin and native locator |
| chunk_policy | {"name": "moderate", "version": "1", "max_size": 640, "overlap": 96, "unit": "characters", "sizer_identity": "unicode-codepoints-v1", "boundary_version": "structural-v1", "minimum_fill_percent": 50, "schema_version": 1} |
| embedding | {"provider": "transformers-mean-pooling-v1", "model": "sentence-transformers/all-MiniLM-L6-v2", "revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41", "dimension": 384, "normalized": true, "document_prefix": "", "query_prefix": "", "configuration_json": "{\"attention\":\"eager\",\"batch_size\":16,\"device\":\"cpu\",\"dtype\":\"float32\",\"max_tokens\":256,\"overflow\":\"reject\",\"pooling\":\"attention-mask-mean\",\"threads\":4,\"tokenizer_revision\":\"1110a243fdf4706b3f48f1d95db1a4f5529b4d41\",\"torch\":\"2.14.0+cu130\",\"transformers\":\"5.17.0\"}"} |
| embedding_input | title-section-v1: original title, section and exact chunk |
| semantic_space | embedding_space_d040951e7abcf8750825f4206d5c7a68de261a8fe7576699db7381d144ee4873 |
| vector_store | Stage 3D VectorStore protocol; SQLite exact reference; schema/migration1; cosine descending then embedding ID |
| production_direction | PostgreSQL + pgvector, not deployed |
| decomposition | structural-extractive-v1 |
| query_construction | focused-exact-acronym-v2 |
| alias_rule | Exact uppercase standalone RAG only; action and relational qualifiers preserved |
| internal_top_k | 20 |
| compound_per_component_top_k | 2 |
| unsplit_top_k | 5 |
| minimum_cosine | 0.2 |
| deduplication | Whitespace-normalized exact text; union authenticated independent source references |
| component_merge | Stage 3I fair_merge round-robin distinct groups |
| bounded_selector | component-round-robin-audited-v2 |
| final_evidence_budget | 5 |
| reranker | identity-v1 |
| active_source_filter | SearchFilter active; lifecycle rechecked by CitationTextResolver |
| scope | Trusted tenant/candidate at store construction and every retrieval entry; physically partitioned reference stores; semantic-space checks |
| context_builder | stage3g-v2 plus unchanged Stage 3I component memberships/non-entailment notice |
| trust_provenance | Untrusted remains untrusted; acquisition origin and exact-support attestations stay separate; source version/span/claim/native pointer retained |
| qwen_evidence_schema | rag/reasoning/schema.json and system_v2.txt; support labels and atomic components unchanged |

Measured residual reasoning failures after full-corpus gold evidence delivery:

| Scale | Need | Category | Predicted | Gold | Atomic correct/total |
| --- | --- | --- | --- | --- | --- |
| LARGE | h02 | deployment | PARTIALLY_SUPPORTED | SUPPORTED | 1/2 |
| LARGE | h05 | partial_action | PARTIALLY_SUPPORTED | PARTIALLY_SUPPORTED | 1/2 |
| LARGE | h07 | partial_framework | PARTIALLY_SUPPORTED | PARTIALLY_SUPPORTED | 1/2 |
| LARGE | h11 | docker_kubernetes | UNSUPPORTED | UNKNOWN | 0/1 |
| LARGE | h12 | lora_qlora | UNSUPPORTED | UNKNOWN | 0/1 |
| LARGE | h13 | consume_build | UNSUPPORTED | UNKNOWN | 0/1 |
| LARGE | h14 | generic_numeric | UNSUPPORTED | UNKNOWN | 0/1 |
| XL | h02 | deployment | PARTIALLY_SUPPORTED | SUPPORTED | 1/2 |
| XL | h05 | partial_action | PARTIALLY_SUPPORTED | PARTIALLY_SUPPORTED | 1/2 |
| XL | h07 | partial_framework | PARTIALLY_SUPPORTED | PARTIALLY_SUPPORTED | 1/2 |
| XL | h11 | docker_kubernetes | UNSUPPORTED | UNKNOWN | 0/1 |
| XL | h12 | lora_qlora | UNSUPPORTED | UNKNOWN | 0/1 |
| XL | h13 | consume_build | UNSUPPORTED | UNKNOWN | 0/1 |
| XL | h14 | generic_numeric | UNSUPPORTED | UNKNOWN | 0/1 |

| Measured error | Count |
| --- | --- |
| unjustified_partial | 0 |
| false_contradiction | 12 |
| existing_nonentailing_citations | 52 |
| unauthorized_evidence_id_count | 2 |

These measured failures, where present, are future Qwen reasoning/citation/contract objectives. They do not justify changing retrieval after correct evidence arrives. Invalid citations are rejected, not accepted evidence. No training examples, adapters or model-weight changes were created.

Stage 3J ends here. No QLoRA, LoRA, SFT, fine-tuning, training-dataset generation, browser automation, discovery, application filling, CV/cover-letter workflow, recruiter/LinkedIn outreach or deployment was begun.

## Reproducibility and limitations

Pinned versions: frozen Stage 3H plus action-sensitive-stage3j-v1; h06-forensic-v1; structural-extractive-v1; focused-exact-acronym-v2; component-round-robin-audited-v2. Config files pin MiniLM revision/input/space, chunk policy, vector contract, budgets and context. Existing local Qwen3.8-27B uses NF4 double quantization, BF16, seed 42, greedy generation, thinking disabled and 1536 output tokens. Exact model path/dependencies/resources are recorded. No downloads or environment replacement occurred.

Limits: small authored synthetic fixtures, nested corpora, repeated distractor templates, a fixed uncalibrated 0.20 relevance floor, imperfect action/trust ranking despite preserved proofs, authored entailment tables without independent human adjudication, and exact-prompt reuse rather than a variability study. This is an experimental RAG freeze, not production validation.
