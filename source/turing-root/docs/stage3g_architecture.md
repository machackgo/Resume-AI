# Stage 3G architecture and pre-registered experiment

Stage 3G only. No training, QLoRA, optimization-stage work, external tools, applications or outreach.

The trusted application supplies a Scope and InformationNeed. CandidateEvidenceRetriever uses semantic retrieval, internal budget 20, exact duplicate grouping, no query expansion and no source caps. ScopedReranker with IdentityProvider preserves retrieval ordering; context() chooses five groups. CitationTextResolver re-resolves every representative and corroborating reference through the active stored vector, embedding record, chunk/revision, canonical evidence, source/version and native locator. Lifecycle and ownership failures stop construction.

The generator sees a system contract and a JSON user payload containing the requirement, material component slots, UNTRUSTED_RETRIEVED_EVIDENCE, an explicit end marker and the JSON schema. Content is JSON escaped; embedded role strings cannot create chat messages. Tenant/candidate IDs, vector scores and irrelevant embedding metadata stay out of model context. Evidence IDs, source type, origin, untrusted-data status, exact-support attestation metadata when supplied, content and version/span remain. Evidence IDs are opaque citation handles. Descriptive requirement IDs, native pointer/source keys and original attestation references are blinded or excluded from model input. Full native pointers and exact original attestations stay in provenance sidecars. Repeated canonical evidence IDs with different chunk content fail closed rather than becoming ambiguous citations; multi-chunk support needs a later extension.

The model has no tools, retrieval callback, scope-selection API or authority to verify facts. Delimiters are instruction-boundary aids, not a formal guarantee of prompt-injection immunity. Deterministic checks guard ownership, active provenance, schema, IDs, quotes, atomic coverage and aggregate consistency; semantic entailment is not guaranteed by matching a quote.

VerificationRecords are supplied by the trusted application, tied to exact support IDs (which bind evidence versions), and checked for scope. Synthetic verified cases exercise this interface. They are not real VeriBridge attestations and do not implement a production verifier/authentication service. A source label, statement that a credential is verified, or an unreviewed canonical claim never promotes its own trust.

## Output contract

schema.json is versioned with system_v2.txt and context version stage3g-v2. Fields are information_need_id, label, atomic_claims, evidence_ids, missing_evidence and reason. Atomic entries contain component_id, claim, label, evidence_ids, exact quotes and concise reason. No private reasoning traces. No raw-output repair.

SUPPORT labels follow Stage 3G semantics. Absent evidence is UNKNOWN; explicit contradiction is UNSUPPORTED. Any supported/partial material component with incomplete components aggregates to PARTIALLY_SUPPORTED. All must be supported for SUPPORTED. No supported components plus an explicit contradiction yields UNSUPPORTED; otherwise UNKNOWN.

Atomic component slots are supplied as a structured task decomposition without labels or evidence answers. Qwen classifies each and aggregates them. This measures atomic evidence judgment and completeness against trusted slots, not autonomous free-form decomposition quality. The six-component service example is explicit. Production decomposition and authentication are outside this experiment.

## Controlled comparisons

37 authored synthetic cases, reusing compatible Stage 3E/F evidence wording. No private data. Three primary arms use the same unchanged local model, NF4/double-quantization/BF16, seed 42, greedy decoding, 1536-token cap, thinking disabled and one A30:

* stage2: original grounded_v3 system/task and original analysis_v1 schema, all current candidate evidence, no semantic selection; proposes whole claim plus component claims.
* full: Stage 3G prompt/schema with all current candidate evidence, independent of ranking, no semantic selection.
* rag5: same Stage 3G prompt/schema with real top-five identity-reranked groups.

Stage 2's original definition maps absence to UNSUPPORTED. It remains byte-identical and is evaluated against the requested Stage 3G definitions; this known semantic mismatch can explain apparent gains. The full-versus-rag5 comparison isolates evidence selection with the prompt held fixed. Do not attribute stage2-versus-rag5 differences solely to retrieval.

Stage 2 receives the same provenance-bearing content, serialized into its existing evidence {id,text} shape. Its output schema remains unchanged. Strict schema rates across differing schemas are informative but are not identical tasks. A full-context control is materially stronger than an empty-evidence strawman.

The corpus is deliberately small, often only one or two groups. Most primary five-group contexts contain all available evidence. This can produce no RAG quality gain and limits generalization to long candidate histories. No improvement is assumed.

The rank-five case was designed before Qwen: four QLoRA interest/read/planned/talk items and an actual low-rank-over-frozen-four-bit adaptation description. The unchanged retriever puts actual adaptation fifth. It is a stress case designed around retrieval confusability, not a random held-out sample. No result is manually reordered. Smaller budget ablations (1,3) run on the predeclared compound/distractor/rank5/injection/corroboration categories. Primary and ablation denominators are reported separately.

## Evaluation and attribution

Strict parsing rejects extra prose, fences, duplicate keys and nonfinite values. A dependency-free checker implements exactly the schema subset used here. Structural validation never repairs model output. Deterministic citation existence/ownership derives from checked supplied provenance. Quotes must be exact substrings; positive, partial and contradicted atomic claims need citations. Top-level citation IDs must equal the atomic union.

Closed-fixture document-to-component relations were authored before Qwen. They score atomic positive/partial/contradiction citation entailment; UNKNOWN explanatory citations count for existence but are excluded from entailment precision. This is not a general semantic entailment engine. Citation validity, precision, hallucination and raw JSON/schema metrics are separate. Hallucination rate is the fraction of positive/partial atomic judgments that exceed available support; prose is audited separately and is not silently covered by that metric.

Report both full-available-evidence label accuracy and context-conditional accuracy. A missing relevant item in rag5 is retrieval failure; in a smaller prefix it is selection/ranking loss. Correctly abstaining after a retrieval miss is not an LLM reasoning failure. Correct evidence with wrong labels is reasoning failure. Wrong citations, structured output and security have separate, potentially overlapping attribution. Legacy absence-label differences are semantic-policy mismatch, not proof of RAG benefit.

The original 273 tests are unchanged. New context/contract/metric tests, previous demos, Stage 2 output verification, all 112 Stage 3E retrieval responses and all 297 Stage 3F rankings are replayed. New independent verification regenerates actual embeddings, retrieval, reranking and context/provenance, reconstructs every prompt, decodes saved token IDs and independently recomputes metrics without loading Qwen weights. This is artifact replay, not a second stochastic inference run.

## Execution

Use existing .venv and offline caches. prepare.slurm creates contexts on Slurm CPU resources. gpu.slurm requests one A30, 8 CPUs, 64 GiB and an eight-hour maximum. It runs a smoke process, waits for the reviewed freeze_v2.json, runs the benchmark with one load for all cases, then exits. Each run refuses an existing output directory. Failed runs are preserved. Earlier-stage outputs are read-only; regression writers are redirected into Stage 3G.

Live SQLite files are node-local /tmp; the canonical deterministic records and retrieval responses are saved for reconstruction. No live database is put on shared storage. The preservation manifest hashes all preexisting project/model files except environment bytecode; no dependency install or existing-model download is permitted. Dependency versions and environment freeze are recorded.

## Identifier-blinding correction

A partially completed v1 diagnostic run exposed descriptive fixture IDs in model inputs. It was cancelled, preserved, and excluded from primary metrics. Version 2 changes only public identifier/pointer presentation (plus the version stamp); evidence, gold labels, retrieval responses/vectors, reasoning rules, weights and generation settings are unchanged. The 37-case equality audit is results/stage3g/identifier_blinding_audit.json. Native provenance remains in sidecars. No benchmark answers are included in the prompt. Both the original freeze.json and corrected freeze_v2.json are retained.

For final independent verification use results/stage3g/verify_artifacts_v2.py: it normalizes reconstructed Python tuples to their persisted JSON array representation before equality comparison; it does not repair Qwen text. The dependent CPU final_check.slurm runs this verifier, all regressions and preservation hashes, report generation and environment-freeze comparison after the GPU batch terminates.
