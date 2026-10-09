# Stage 3F — evidence reranking architecture

Stage 3F orders already retrieved evidence by information-need relevance. A rerank score is an uncalibrated priority signal, never a support label, credential verification, or assertion that a candidate possesses a skill. No Qwen, generation, fine-tuning, or later-stage workflow is invoked.

## Contracts and authorization boundary

`Reranker.rerank(information_need, retrieval_results, top_n)` returns an immutable tuple of `RerankedEvidence`. `ScopedReranker` implements this protocol. Construct it with the authenticated `Scope`, one authentic Stage 3E `RetrievalResponse`, a `ScoreProvider`, and a `CitationTextResolver`. The response is the per-query allowlist; a rerank call may use its subset, but cannot add or alter a result, mix queries/scopes/spaces, or duplicate candidates. The original retrieval order is restored before scoring. Equal scores break ties by original rank, then embedding ID.

`ScoreProvider.score(pairs)` sees immutable query/evidence pairs and returns one finite real score per position. It receives no IDs, labels, retrieval scores, or provenance metadata. The wrapper alone constructs outputs from its original allowlist. IDs or evidence objects returned in place of scores, missing/extra scores, NaN/Inf/bool values, and configuration drift fail closed. Swapping a cross-encoder for an instruction/API/Qwen/deterministic score adapter requires no Stage 3E change; only the identity and local cross-encoder adapters are implemented here. Future adapters still require their own security/evaluation review.

The trusted application must pass a real Stage 3E response; the Python wrapper is not an authenticated network capability or sandbox for malicious Python providers. The OS account and trusted caller remain the authority boundary inherited from Stage 3D/E. Provider model inference uses local safetensors and `trust_remote_code=False`, without an agent, tools, external inference service, or unrestricted search.

## Full provenance preservation

Each `RerankedEvidence.original` is the unchanged complete `RetrievalResult`: original rank, semantic and other component scores/ranks, query ID, scope, embedding ID, chunk/revision, evidence/source/version, native locator and offsets, source type/URI, origin, trust and verification-resolution marker, claim relationships, support IDs, provenance events, semantic space, lifecycle and all corroborating references. Reranking adds need ID, rerank rank/logit, full provider configuration/identity, actual candidate count, requested output budget, and the hash of the exact input pair. Convenience properties expose tenant/candidate and original rank/semantic score without duplicating authoritative metadata.

Before scoring, `CitationTextResolver` retrieves only the supplied embedding IDs from the candidate-bound store; resolves stored record → embedding cache identity → chunk/revision → canonical evidence → source → native provenance; reconstructs and compares every Stage 3E reference field; and checks active state. Every grouped sibling passes the same checks and must have equal whitespace-normalized text. No sibling inherits another source's trust. No corpus search occurs. Superseded/deleted/purged items fail closed, including changes after the initial retrieval. The caller must serialize ingestion/lifecycle updates with retrieval/reranking; there is no cross-ledger transaction or new concurrent snapshot guarantee.

## Input strategy `need-evidence-v1`

The two sequence-classifier inputs are the exact `InformationNeed.text` and the resolved raw chunk text. Structural titles and claim text are omitted for a minimal reproducible first experiment. Tenant/candidate IDs, source metadata, trust flags, grades, expected answers and retrieval scores are absent. Punctuation, exact numbers, framework/model names, versions, negations and malicious text remain verbatim. Hashing covers the strategy version and both texts. Input is paired by the tokenizer, not concatenated into an instruction prompt.

The cross-encoder rejects any combined pair exceeding 512 tokens rather than silently truncating decisive details. No sliding-window aggregation is introduced. Models run in eval/inference mode with float32 CPU, four threads, eager attention, batch size 16, fixed seed and deterministic Torch algorithms. Raw single relevance logits are recorded; they are not probabilities. Tokenizer and model revisions, library versions, configuration identity, budgets, input hashes and maximum observed length are retained. Exact reproducibility is asserted within the recorded environment, not across hardware, library versions or differently padded batch configurations.

## Retrieval and budgets

Stage 3E remains semantic with internal budget 20, exact duplicate grouping on, expansion off and no source caps. Request top 20 to expose the available grouped candidates, then compare the first 5, 10 and up to 20 under identical retrieval inputs. Grouping can leave fewer than 20 unique candidates; actual counts are recorded. Top-five is checked against a separate Stage 3E request. Output budgets two and three are assessed from these full rerank orders without invoking any downstream model.

Exact grouping remains Stage 3E's responsibility. The primary rerank is pure relevance. An evaluation-only source-diversity diagnostic changes order only within exactly tied score tiers; it cannot promote a lower-scored document. Neither source type nor trust is a relevance boost. Retaining all corroborating references is mandatory even when the output budget is small.

## Evaluation and limitations

Two tracks are kept separate. The frozen Stage 3E track reconstructs all 112 saved responses, then compares identity and learned rerankers using the original binary/singleton labels. The extended Stage 3F fixture reuses Stage 3E's synthetic corpus and adds focused hard cases; its full active-document relevance tables were authored before learned scoring. Grades 3/2/1/0 mean direct/strong-but-incomplete/adjacent/irrelevant-or-misleading relevance. They never mean SUPPORTED/PARTIALLY_SUPPORTED/UNSUPPORTED/UNKNOWN.

Metrics use unique exact-text groups and retain all source references. Direct relevance means grade 3 for Recall, MRR, MAP and hit/survival. nDCG uses `2**grade-1`, with the full active corpus as the ideal denominator; candidate-conditional nDCG is separately labeled. Top-1 hard-negative error, explicit stronger/weaker pair inversion rates, strict-score wins, ties, pair coverage and missing stronger evidence are reported. Unretrieved pairs are not silently counted as wins. Query/category regressions and every pair inversion remain visible. The grades are single-author synthetic judgments, not independently validated human labels; no confidence or production accuracy claim follows.

Identity must reproduce exactly. A learned configuration should improve ranking without concealing new action, numeric, entity or verification-related failures; otherwise retain the Stage 3E identity default. Dataset-specific boosts, answer-derived rules, thresholds for support, training and per-example tuning are prohibited.

## Reproduction

One-time acquisition: `module load slurm/current; sbatch rag/reranking/prepare.slurm`. The preparation refuses to repin an existing lock. Models live only in `models/stage3f/`. All previous non-environment project files plus Qwen/embedding/cache assets are hashed before experimentation.

Experiment: `sbatch rag/reranking/evaluate.slurm`. It runs all regression tests and sequential independent-process identity/MiniLM/TinyBERT evaluations on four CPUs, 8 GiB, no GPU. Live SQLite files use node-local temporary storage and are archived after closure. Final independent replay, model overflow checks and preservation audit run through `rag/reranking/final_check.slurm`. New results are confined to `results/stage3f/`; no earlier source, fixture, test, model or result is edited. Archived results must be copied to a fresh Stage 3F run directory before deliberate reruns if those Stage 3F outputs also need immutable retention.
