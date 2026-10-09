# Resume AI untouched base-model baseline — completed

Run: `base-v1-2325384-eval3`. Eight synthetic cases, 21 requirements, 24 proposed claims, 11 generated bullets. No fine-tuning, RAG, adapters, or weight changes. Minimal task/schema prompt; no few-shot examples. Thinking explicitly disabled, greedy decoding, 1536 output tokens, seed 42.

## Authoritative strict result

JSON validity **0/8**, schema validity **0/8**: every response was wrapped in Markdown fences. Strict requirement, skill, missing-requirement, claim-selection and refusal F1 are all **0** because there are no contract-valid predictions. Strict label/citation accuracy and coverage are also 0. Unsupported-claim and grounded-bullet rates are **undefined**, not zero or perfect, because no bullets pass parsing. All failures remain in `metrics.json`; raw outputs are unchanged. Offline rescoring exactly reproduced these metrics.

## Separate fence-removal diagnostic

These are NOT the strict baseline scores. A diagnostic removes one complete outer Markdown JSON fence without repairing content; all eight then satisfy the schema.

| Metric | Diagnostic result |
|---|---:|
| Requirement precision / recall / F1 | 100% / 95.24% / 97.56% |
| Skill precision / recall / F1 | 84.21% / 100% / 91.43% |
| Missing requirement precision / recall / F1 | 100% / 100% / 100% |
| Requirement support-label accuracy (macro) | 85.42% |
| Proposed-claim support-label accuracy (macro) | 95.83% |
| Requirement / claim exact citation accuracy (macro) | 95.83% / 95.83% |
| Refusal precision / recall / F1 | 100% / 92.86% / 96.30% |
| Citation-and-claim-ID grounded bullets | 10/11 = 90.91% |
| Non-fully-supported cited claim IDs | 1/11 = 9.09% |
| Job requirement coverage proxy (macro, all requirements) | 39.58% |

Low coverage partly reflects deliberate candidate-job mismatches; it is not a target to maximize by fabrication. Missing-requirement success does not imply extraction completeness: automation was omitted from the job analysis, but it was a supported requirement so it did not belong in the missing set.

## Semantic review — qualitative, model judged

The primary engineering assistant reviewed all 11 bullets. **2/11 (18.18%)** contain material unsupported additions; **9/11 (81.82%)** are provisionally grounded. This is a single-assistant judgment, not an independent human evaluation or calibrated automated metric. See `semantic_audit.json` for each bullet, reasoning and borderline wording.

- Success: differentiated JavaScript/Java and Azure/AWS; preserved uncertainty about conflicting Python tenure; refused fabricated MIT PhD, Google employment, AWS expertise, million-user project, and unmeasured 100-hour savings; calculated the supported 60% time reduction.
- Failure: all responses violated the strict JSON contract.
- Failure: unknown Python/certification facts were listed as skills; tutorial-only AWS was also listed as a skill.
- Failure: generic Python experience became “data processing and analysis tasks.” Transaction analysis became “validate data integrity.” Both pass citation proxies despite unsupported prose.
- Rubric limitation: a safe Azure-only bullet cited the compound Azure-and-AWS claim, which the deterministic scorer flags. Citation E1 explaining unmeasured savings is defensible even though the gold exact citation set is empty. Partial-vs-unsupported labels for production ML and tutorial AWS need human calibration. Gold labels were not edited after seeing outputs.

## Execution and reproducibility

Local artifacts identify `Qwen/Qwen3.8-27B`; config architecture is `Qwen3_5ForConditionalGeneration`, actual text loader class `Qwen3_5ForCausalLM`. Existing NF4 4-bit, double quantization, BF16 settings retained. All parameters on cuda:0. CUDA build 13.0, driver 595.71.05. Model load 24.14 seconds; 3336 generated tokens in 352.49 seconds = **9.46 tokens/sec**, including prefill. Peak allocated GPU memory **16.99 GiB**. No output hit the token cap.

Used existing idle allocation **2325384**, account cs541, partition academic, node gpu-4-21. Step **2325384.5**: one A30 24 GB, four CPUs, inherited 64 GB host-memory allocation, completed in **6m24s**, exit 0. Its original bash step remains untouched. New batch job 2325425 was blocked by per-user GPU quota and canceled before running. Earlier steps .3 and .4 failed during metadata handling (missing git executable; absent hf_device_map); both errors were corrected, and their logs retained. No inference ran on a login node.

Relevant warnings: optional causal_conv1d and flash-linear-attention kernels absent; Transformers used correct, slower reference kernels. No dependency installation or environment rebuild performed.

Nine CPU tests pass locally and remotely, covering gold consistency, adversarial scoring, schema rejection, duplicate IDs, missing output, offline rescoring and diagnostic fence handling. Login-node guard verified to reject before importing Torch or creating a run. Original three benchmark script SHA256 values are unchanged. Run contains full prompt/raw text/token IDs, predictions, strict/diagnostic metrics, timings, model/environment/config metadata, source hashes and an eval snapshot. Shard sizes/timestamps recorded; no weight files rewritten or downloaded. No project Git repository was present.

## Next work suggested, not started

First calibrate the evidence rubric (atomic claims, negative evidence citations, tutorial familiarity), then freeze a larger held-out evaluation set. The next model-development stage should test prompt-only JSON compliance, consistency between UNKNOWN labels and skills, and clause-level bullet grounding. Retain this baseline and compare with identical generation settings. Optional kernel acceleration is a separate performance experiment. Do not proceed to RAG or QLoRA based on these small-set scores.
