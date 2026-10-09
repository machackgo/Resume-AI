# Stage 4A — QLoRA dataset and objective design

Status: dataset v1 frozen after all acceptance gates. No Qwen training, adapter creation, optimizer step, GPU request, weight modification, RAG change or Stage 4B execution occurred.

## 1. Frozen Stage 3J reference

`results/stage3j/frozen-rag-configuration.json`, SHA-256 `8b2109ba74d47ee50010c14e6a1bd491970588bb9e39be3c4b267f7d2da5f0c9`. Stage3A canonical evidence; Stage3B 640-character/96-overlap chunks; pinned MiniLM 384-dimensional embeddings; Stage3D vector contract; structural-extractive-v1 decomposition; focused-exact-acronym-v2 queries; internal K=20; compound shortlist=2; atomic shortlist=5; cosine floor=.20; component-round-robin-audited-v2; maximum five groups; identity-v1 reranker; unchanged trust, provenance and tenant/candidate scope. Full configuration remains external and byte-identical.

## 2. Qwen failure taxonomy

`results/stage4a/failure-taxonomy.json` extracts 147 historical failure records from RAG arms with no retrieval loss and matching contextual/full gold. These include repeated needs across scales/arms and are not independent population observations. Stage3J primary evidence arrived correctly: h02 under-recognized deployment; h05/h07 had wrong component judgments; h11–h14 confused related evidence with contradiction. Its report records 12 false contradictions, 52 existing non-entailing citations and two unauthorized-ID occurrences. Stage3J unjustified-partial and explicit injection-success counts were zero; those remain preventive curriculum objectives, not invented Stage3J failures. Historical row text is never copied into generation.

## 3. Training objectives

- **unknown_vs_unsupported** (measured): Missing or adjacent evidence cannot contradict.
- **citation_entailment** (measured): Exact existing IDs must entail the cited atom; quote traceability is insufficient.
- **calibrated_positive** (measured): Direct deployment proof and paraphrased construction merit support.
- **action_strength** (measured): Consumption, study, implementation, deployment and operation are distinct.
- **technology_identity** (measured): Related frameworks, clouds and adaptation methods are not interchangeable.
- **numeric_grounding** (measured): Only exact same-event metrics justify numeric claims.
- **compound_composition** (measured): Preserve component labels and frozen aggregation, including mixed contradiction/support.
- **structured_output** (measured): Strict JSON, unchanged component text/IDs, union citations and nonempty missing_evidence for denials.
- **unjustified_partial** (preventive_and_stage3g): Real supported material parts required; Stage3J count is zero.
- **trust_verification** (preventive): Assertions are not authenticated verification.
- **corroboration** (preventive): Copies are not independent proof and cannot repair missing entailment.
- **untrusted_instructions** (preventive): Instructions in evidence are data; Stage3J had zero explicit attack successes.

## 4. Dataset architecture

1,920 authored synthetic records: 60 substantive scenarios grouped into 12 parent template families, eight contextual variants, four target labels. Each record separates `messages` from `metadata` and a structured `oracle`. Only `messages` may enter future training. Oracle predicates carry event identity, positive/adjacent/denial relation, exact values, source lineage and authenticated verification; no model-generated labels or real profiles are used.

## 5. Input format

The unmodified `rag.component.retrieve.messages` (also used by Stage3J) constructs system/user messages. User JSON retains task need ID, original requirement, authored atomic components, conservative retrieval decomposition, retrieval notice, `UNTRUSTED_RETRIEVED_EVIDENCE`, closing marker and the frozen output schema. Every evidence entry retains source type, acquisition origin, untrusted-data status, verification policy, exact-support attestations, content and version/span citation handle. Synthetic contexts obey exact-text grouping and the five-group/640-character bounds. Optional rank/score/query diagnostics are omitted: no actual vector search occurred and fabricated scores would be misleading. No scope IDs, oracle relations, expected labels, difficulty, secrets or database internals enter model input. As in historical preparation, authored judgment components coexist with conservative retrieval decomposition. Historical records about a different engagement remain active-source text; inactive records are never smuggled past the frozen lifecycle boundary.

## 6. Output format

The exact frozen `rag/reasoning/schema.json` is copied as `target-schema.json`. It includes information_need_id, overall label, atomic component_id/claim/label/evidence_ids/quotes/reason, union evidence_ids, missing_evidence and concise overall reason. Quotes are verbatim, citations must entail the exact atom, and UNKNOWN uses empty citations. The inherited rule requiring missing_evidence on explicit denials remains intact; those entries request resolution of the contradictory record. Frozen aggregation: all supported → supported; any supported/partial plus incomplete → partial; otherwise any explicit contradiction → unsupported; otherwise unknown. In particular, support + contradiction remains PARTIALLY_SUPPORTED. No free-form hidden reasoning is generated.

## 7. Chat template

System text is byte-identical `system_v2.txt` / stage3g-v2. The tokenizer is the existing local `models/Qwen3.8-27B`; its actual runtime is Qwen3_5ForCausalLM. No directory/model rename or substitution occurred. Tokenizer config, vocabulary, merges, tokenizer JSON and chat-template file hashes are in the release manifest. `enable_thinking=False`; inference prefix uses `add_generation_prompt=True`; full three-message training rendering uses `False`. Prefix equality is asserted at both text and token level. This tokenizer inserts an empty think block in the assistant prefix even with thinking disabled; it is preserved and masked. No additional special tokens are added.

## 8. Loss masking

Causal next-token loss applies only to assistant JSON and exactly one `<|im_end|>` token. System, user/RAG text, assistant header, empty think block and right padding have labels -100. The formatting newline after im_end is excluded. Labels remain unshifted for the model loss to shift once; a boundary test verifies that the last prompt position predicts the first JSON token. Padding uses the actual tokenizer pad ID with attention_mask=0; it is never inferred from token value. `loss-mask-audit.json` records boundary token strings/labels, EOS IDs and padding tests. This stage constructs arrays only; it never computes model loss or backward gradients.

## 9. Scenario/template families

| Parent family | Split | Examples | Scenarios |
| --- | --- | --- | --- |
| adaptation | train | 160 | 5 |
| api | train | 160 | 5 |
| asserted | validation | 160 | 5 |
| cloud | train | 160 | 5 |
| container | train | 160 | 5 |
| database | train | 160 | 5 |
| framework | train | 160 | 5 |
| lifecycle | train | 160 | 5 |
| numeric | train | 160 | 5 |
| operations | test | 160 | 5 |
| rag | train | 160 | 5 |
| verified | train | 160 | 5 |

Training retains all ten core technology/action/numeric/verification families. Validation holds out assertion-reporting templates; internal TEST holds out observability/automation action templates. This deliberately tests transfer and avoids certificate-name substitutions leaking across splits. All 60 scenario predicates and domain-specific compound companions are explicit in generation_config.json.

## 10. Hard negatives

900 examples (46.875%) have nonempty insufficient/partially sufficient contexts. Contrasts include Docker/Kubernetes, AWS/Azure/GCP, Flask/FastAPI, TensorFlow/PyTorch/JAX, generic SQL/PostgreSQL, API consumption/construction, LoRA/QLoRA, four-bit inference/training, RAG/fine-tuning, study/implementation and deployment/production operation. RELATED never supplies partial credit by itself. Direct paraphrased positives constitute a balanced 25%, so the dataset does not reward universal abstention.

## 11. Counterfactual and numeric pairs

480 scenario groups keep all four labeled variants together. Atomic evidence variants provide controlled support/adjacent/explicit-denial comparisons with the same requested predicate; partial variants add a genuinely supported material component. Compound variants are multi-fact exercises rather than claimed one-fact counterfactuals. Five numeric scenarios cover latency percentage, currency savings, throughput, record counts and team size. Same-event exact values support, generic improvements do not, and explicitly corrected different values contradict. Different-event direct records do not establish a current-event claim.

## 12. Citation design

An independent proposition rule resolves each atom from same-event, same-predicate facts and exact verification state. Positive and contradictory atoms cite a deterministic entailing record with an exact quote; unresolved conflicts cite nothing. The standalone validator checks the frozen schema, every ID and owner, quote membership, citation union, entailment, atomic coverage and frozen aggregation. Renderer/catalog checks also reject edited technologies, actions, numeric literals, provenance and malformed evidence. Mutation tests show that existing but non-entailing IDs are rejected. This is a closed synthetic oracle, not a general natural-language entailment classifier.

## 13. Trust, corroboration and security

240 records (12.5%) contain untrusted commands, including requests to output SUPPORTED or use candidate B. They remain quoted evidence data and are never cited as factual proof. No foreign evidence entry is included; ownership mutation tests reject it. Candidate assertions are not independent verification, and source type never creates an attestation. Duplicate copies preserve one lineage and do not become independent proofs. Separately observed records retain independent lineage; neither repetition nor corroboration repairs a missing predicate. Unresolved direct conflicts yield UNKNOWN. Authenticity is simulated by the trusted generator for synthetic examples only.

## 14. Generation and revision history

Seed 410042 and explicit Python templates; no generative model is used. Candidate-01 established the initial token distribution. Candidate-02 strengthened schema validation without changing messages. Candidate-03 added domain-specific companion claims and five-group contexts. Candidate-04 grouped certificate/tool substitutions at the parent-template boundary and enforced the 4,608-token limit. Candidate-05 bounded percentage reductions to physically meaningful values, added three-supported/one-missing compound patterns, and removed ambiguous negative wording from adjacent RAG evidence. Earlier candidates and diagnostic logs remain as development history, not frozen training releases. No rejected example is silently repaired; systemic changes are recorded in generation-revisions.json. Deterministic tests compare every regenerated record and stable ID.

## 15. Total examples

1920. The measured coverage supports a compact first experiment; multiplying near-identical paraphrases would add volume more than independent information. This is an initial synthetic curriculum, not a claim that 1,920 examples are sufficient for deployment.

## 16. TRAIN

1600 examples, 50 scenarios, 10 parent templates (83.333%). Only this split receives future optimizer updates.

## 17. VALIDATION

160 examples, five scenarios, one held-out parent template (8.333%). Used for future selection/checking; never trained.

## 18. TEST

160 examples, five scenarios, one held-out parent template (8.333%). Locked for final Stage4D use. Ratios favor whole-family isolation over forced 80/10/10. Internal held-out splits are intentionally narrow domain-transfer probes; they cannot replace the broader historical external suite.

## 19. Label distribution

| Label | All | Train | Validation | Test |
| --- | --- | --- | --- | --- |
| PARTIALLY_SUPPORTED | 480 | 400 | 40 | 40 |
| SUPPORTED | 480 | 400 | 40 | 40 |
| UNKNOWN | 480 | 400 | 40 | 40 |
| UNSUPPORTED | 480 | 400 | 40 | 40 |

Atomic/compound: {'False': 720, 'True': 1200}. All four labels are balanced within every split. Numeric cases: {'False': 1760, 'True': 160}. Citation atoms: {'cited': 2040, 'uncited': 1800}. Domain/action/trust distributions are fully enumerated in statistics.json; trust tags can overlap and are not exclusive counts.

## 20. Scenario distribution

60 scenario families × 32 examples; 12 parent template families × 160 examples. No parent accounts for more than 8.333% of the whole dataset (10% of TRAIN). Source shapes span zero through five evidence groups: {'0': 60, '1': 300, '2': 660, '3': 420, '4': 240, '5': 240}. Exact per-scenario/domain/action distributions are in statistics.json and generation_config.json.

## 21. Difficulty distribution

| Difficulty | Count |
| --- | --- |
| ADVERSARIAL | 240 |
| EASY | 180 |
| HARD | 1140 |
| MEDIUM | 360 |

Difficulty is metadata only, assigned from evidence context and ambiguity. It is a sampling/analysis heuristic, not an empirically measured Qwen difficulty score.

## 22. Measured tokenizer statistics

| Tokens | Mean | Median | p90 | p95 | Maximum | Volume |
| --- | --- | --- | --- | --- | --- | --- |
| input_tokens | 2042.64 | 1952.0 | 2895 | 2928 | 3073 | 3921878 |
| target_tokens | 450.33 | 408.5 | 711 | 966 | 1170 | 864633 |
| total_tokens | 2492.97 | 2407.0 | 3474 | 3870 | 4233 | 4786511 |

Counts include the real chat-template prefix and supervised assistant end token. Token analysis is CPU-only and uses the local tokenizer, not a character estimate.

## 23. Sequence length recommendation

Use max_length=4608 with dynamic padding and no truncation. Maximum measured total is 4233. Nine examples exceed 4096; all are identified in results/stage4a/sequence-risk.json with their split, input/target counts and reason. They have four supported components, five groups and citation/quote overhead. None exceeds 4608 or the frozen 1536 assistant-output cap. Sequence length must not be reduced by silently dropping components or evidence; Stage4B must demonstrate memory feasibility for the longest examples.

## 24. Leakage analysis

Known leakage: zero. Exact and normalized context duplication, scenario IDs, candidate entities and parent-template IDs are split-isolated. Technology-substitution siblings share a parent group. Cross-split substantive-predicate token Jaccard maximum: 0.14285714285714285; review threshold .85. Common JSON/schema text, IDs and entities are excluded from that template comparison. Historical five-gram overlap maximum: 0.0. Lexical thresholds are practical audits, not proofs of semantic independence; generic reasoning operators and some companion predicates intentionally recur.

## 25. Historical benchmark exclusion

The release contains 1621 normalized historical fingerprints with original file SHA-256 hashes in historical-exclusion.json. Requirements, atomic claims and evidence from Stage3G–3J datasets and prepared fixtures are checked. There are zero exact/normalized benchmark collisions and zero high-overlap historical matches. No external benchmark is present in TRAIN, VALIDATION or internal TEST. Historical taxonomy records live only in results/stage4a, never in model messages.

## 26. Standalone validation

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m stage4a.validate datasets/stage4a/v1` parses the existing release without regenerating it; it exits nonzero on any failure. It validates all 1,920 records, frozen message/schema compatibility, domain/action/numeric/trust logic, ownership, citations, grouping, historical fingerprints, token lengths and file/source checksums. Both candidate and final frozen-release validations are retained as JSON. The validator accepts only the explicit authored synthetic grammar; it is intentionally fail-closed.

## 27. Representative inspection

`datasets/stage4a/v1/inspection.md` and inspection-samples.json contain 35 authored samples with exact evidence and full structured targets: all labels; Kubernetes/Docker; AWS/Azure; API construction/consumption; LoRA/QLoRA and four-bit inference; RAG/fine-tuning; numbers; independently verified versus asserted credentials; deployment positives; four-component partial support; mixed support/denial; unresolved conflict; duplicate lineage; and malicious evidence. Manual inspection found the need for parent-family split strengthening and realistic compound/five-group contexts before the final freeze. Optional new base-Qwen replay was deliberately deferred: no GPU was allocated and no new model accuracy is claimed.

## 28. Synthetic limitations and curriculum

Language and denial phrasing remain repetitive; formal predicate rules simplify natural ambiguity; source authentication is synthetic; only eight context patterns and three companion-claim slots per domain are modeled. Shuffled order, paraphrased positives, varied ordering/source origin, distractors, conflicting and historical-event records, injection and exact duplicates reduce but do not eliminate shortcuts. Parent-group isolation prevents trivial substitution leakage. Start with shuffled mixed training and natural balanced sampling; no label weights or phased curriculum are justified by these counts. Track later results by label, scenario, difficulty, source/trust and length; add genuinely new authored templates only as a new version, never tune individual final-test examples.

## 29. QLoRA versus ordinary LoRA

Ordinary BF16 LoRA would require approximately 50.1 GiB for the frozen text weights alone, exceeding an A30’s 24 GiB before activations or adapters. Existing NF4 inference works, so QLoRA is the practical direction. NF4 and double quantization compress the frozen base; paging can moderate optimizer spikes but cannot remove activation cost. See [QLoRA paper](https://arxiv.org/abs/2305.14314) and [PEFT quantization guidance](https://huggingface.co/docs/peft/developer_guides/quantization). QLoRA adds quantization/backward complexity and can be slower than BF16 LoRA; neither stability nor training fit has been measured here.

## 30. Actual target modules and parameter counts

Safetensors headers and an empty meta-device runtime independently agree on 26895998464 text parameters; the full checkpoint has 27781427952 including vision. Runtime Qwen3_5ForCausalLM uses 48 linear-attention and 16 full-attention layers. Available projections: q_proj/k_proj/v_proj/o_proj; in_proj_qkv/in_proj_z/in_proj_a/in_proj_b/out_proj; gate_proj/up_proj/down_proj. q_proj includes a gate and is not inferred from a generic Qwen recipe.

| Scope | r | Modules | Adapter parameters | % text base |
| --- | --- | --- | --- | --- |
| full_attention_only | 8 | 64 | 5242880 | 0.0195 |
| full_attention_only | 16 | 64 | 10485760 | 0.039 |
| full_attention_only | 32 | 64 | 20971520 | 0.078 |
| hybrid_attention | 8 | 304 | 23760896 | 0.0883 |
| hybrid_attention | 16 | 304 | 47521792 | 0.1767 |
| hybrid_attention | 32 | 304 | 95043584 | 0.3534 |
| hybrid_attention_and_mlp | 8 | 496 | 58363904 | 0.217 |
| hybrid_attention_and_mlp | 16 | 496 | 116727808 | 0.434 |
| hybrid_attention_and_mlp | 32 | 496 | 233455616 | 0.868 |

Propose rank-8 hybrid attention + MLP (496 exact module paths recorded). Full-attention-only reaches only 16 layers. Hybrid-attention-only is a lower-memory ablation; MLP inclusion follows the broad projection coverage used in QLoRA practice. Exclude embeddings, lm_head, vision, convolution and normalization. These are arithmetic counts, not instantiated adapters.

## 31. Rank, alpha, dropout

Initial r=8, alpha=16, dropout=.05, bias=none, task_type=CAUSAL_LM. Compare r=16/alpha=32 only if validation and measured headroom justify it; .00–.05 dropout is a small-data stability range. Rank8 gives 58363904 prospective trainable parameters (0.217%). No adapter parameters were allocated. All exact runtime paths are in proposed-stage4b-config.json; Stage4B must verify the trainable-name/count audit.

## 32. Quantization proposal

Reuse proven bitsandbytes NF4, double quantization, uint8 storage and BF16 compute. Enable non-reentrant gradient checkpointing and disable inference KV cache during training. Installed PEFT preparation casts non-Params4bit BF16/FP16 tensors to FP32. That can upcast the large input embedding and output head and materially increase memory. Stage4B must inspect this transition, and any deliberate retention of frozen embeddings/head in BF16 requires finite-gradient and loss-equivalence checks; no precision change is made in Stage4A.

## 33. Optimizer, learning rate and schedule

Provisional paged_adamw_8bit, LR 5e-5 (compare at most 1e-4 after a stable smoke run), linear decay, 5% warmup, weight decay .01 and gradient clipping 1.0. Lower initial LR limits overshooting a small, structured dataset. Validate optimizer state dtype/paging in the installed bitsandbytes build; paging does not guarantee fit. Versions: accelerate=1.15.0, bitsandbytes=0.50.2, datasets=5.0.1, peft=0.21.0, tokenizers=0.23.2, torch=2.14.0, transformers=5.17.0, trl=1.13.0. These are proposed starting values, not a tuned optimum.

## 34. Batch, accumulation and steps

Microbatch1, accumulation16, effective batch16. TRAIN has 1600 examples, so 100 optimizer steps per epoch and 200 for a provisional two epochs; no steps have run. Train total token volume per epoch: 3991217; supervised target volume: 721031. Validate every 50 steps, checkpoint each 100 steps, keep two checkpoints, choose only with VALIDATION. Fixed balanced sampling and seed410042 suffice. Gradient accumulation changes effective batch, not per-example activation memory.

## 35. Sequence, packing and objective execution

4,608 maximum total tokens; dynamically right-pad and bucket by measured length; no packing initially. Packing unrelated candidate conversations risks cross-example attention and incorrect label boundaries and offers limited value at microbatch1. Any future packing requires separate attention and masking equivalence tests. Loss is token-normalized over unmasked assistant targets; verify accumulation normalization so variable target lengths do not accidentally change example weighting. Generation remains the frozen inference template with thinking disabled and 1536 output cap.

## 36. One-A30 feasibility estimate

| Component | Estimated GiB |
| --- | --- |
| nf4_double_quantized_projection_payload | 11.702 |
| nonquantized_bf16 | 4.741 |
| nonquantized_fp32 | 9.483 |
| estimated_base_preserving_bf16 | 16.443 |
| estimated_base_default_peft_fp32 | 21.184 |
| rank8_fp32_adapter_weights | 0.217 |
| rank8_fp32_gradients | 0.217 |
| rank8_adamw32_moments | 0.435 |
| rank8_adamw8_moments_lower_bound | 0.109 |
| checkpoint_layer_boundary_activations | 2.812 |
| full_bf16_logits | 2.131 |
| full_fp32_logits | 4.263 |
| bf16_ordinary_lora_base | 50.098 |
| historical_inference_peak_torch_allocated | 17.929 |
| historical_free_after_load | 6.619 |

The NF4 payload estimate uses about .516 bytes per quantized projection parameter and excludes allocator/quantizer implementation details. BF16 base plus rank8 adapters/states, checkpoint boundaries, full-vocabulary logits, attention/backward temporaries and CUDA workspaces can exceed 24 GiB. Default PEFT FP32 upcasting leaves still less headroom. BF16-preserved base with compatible chunked/fused loss and measured checkpoint behavior may fit, but is unproven. Standard full-logit/default-upcast training is a high OOM risk. Stage4B must measure load → preparation → forward → backward → optimizer peaks, allocated/reserved/device memory, paging and tokens/sec on the longest records. If it cannot fit safely, report the blocker and evaluate an explicitly justified memory strategy; do not truncate data or assume successful inference proves training feasibility.

## 37. Stage 4A tests

55 tests pass. Coverage includes deterministic generation/IDs, strict schema, all labels/balance, atomic and compound composition, every required technology/action contrast, numbers, citations/quotes, verification, injection, privacy/ownership, grouped splits/duplicates/historical exclusion, tokenizer/chat compatibility, sequence risk, causal loss/padding masks, manifest/checksums and standalone failure exits. No training test or optimizer is executed.

## 38. Historical regression tests

486 prior tests pass (467 Stage3, 19 Stage1/2), with unchanged frozen Stage2 replay, Stage3A/B demos, Stage3E 112-case replay and Stage3F 297 learned/identity replay configurations. The first Stage3F exact-score replay failed on compute-3-04; differences were recorded rather than weakening equality. The complete original replay then ran CPU-only on gpu-4-23, the historical Stage3J verification node, without a GPU allocation. This is a hardware-sensitive bitwise reproducibility limit, not evidence that the frozen identity RAG was changed. Previous failed-attempt logs remain preserved.

## 39. Protected artifacts

1179 Stage1–3J files, including weights, embedding assets and historical caches, remain byte-identical: zero changed/missing. The inherited Stage3J protected and final manifests were verified before work; Stage4A’s superset protection manifest was verified again after regressions. All new data, tests, source, logs and reports use Stage4A paths. Python bytecode writes were disabled; the existing environment was not replaced.

## 40. Manifest and checksums

`datasets/stage4a/v1/manifest.json` records version, UTC generation/freeze timestamps, seed, generator/schema/frozen-contract identities, tokenizer/template hashes, split/label/scenario/difficulty counts, token statistics, historical exclusion fingerprints, generator/source hashes and SHA-256 for every release payload. `checksums.sha256` anchors manifest and payloads; `results/stage4a/final-manifest.json` covers Stage4A source, tests, documentation and acceptance artifacts. Reproduction creates a new destination; existing v1 is never overwritten. Reproduced JSONL bytes must match; timestamps naturally differ.

## 41. Exact next-stage boundary

Stage4A ends here. Stage4B is limited to a separately authorized configuration/compatibility/memory smoke experiment using TRAIN and VALIDATION; it must validate module selection, masks, precision, finite gradients and one-A30 headroom before full training. Stage4C would train on TRAIN and select with VALIDATION. Stage4D alone opens internal TEST and frozen historical Stage3G–3J external benchmarks, ideally supplemented with separately authored unseen challenges frozen before training decisions. Do not tune Stage4C repeatedly against those final sets. This report and JSON configuration are proposals only: no Stage4B job, SFT, LoRA/QLoRA training, adapters, weight changes or downstream application workflows were started.

