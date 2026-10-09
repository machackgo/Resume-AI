# Stage 3E — candidate-scoped evidence retrieval

Retrieval selects evidence worth examining. Neither cosine, BM25, RRF, exact terms nor source origin establishes entailment. There is no support label, verifier, model-generated explanation, reranker or generator in this package.

## Minimal additive implementation

`rag/retrieval/models.py` defines an `EvidenceRetriever` protocol and immutable `InformationNeed`, `QueryPlan`, `RetrievalConfig`, `EvidenceReference`, `RetrievalResult`, and `RetrievalResponse` contracts. `CandidateEvidenceRetriever` composes the Stage 3C provider, Stage 3D VectorStore, and Stage 3B citation service. No old source, migration, test, fixture or report is edited.

The trusted ingestion caller supplies a complete embedding-ID catalogue for exactly one scope and semantic space. Preparation resolves each stored record through `ChunkEmbedder.resolve`, checking all immutable lineage and input hashes. It retains citation references in memory, not copied source payloads in output. Each retrieval checks all catalogue IDs through bound `get_embedding`, applies typed filters, and compares eligible count against the store. An incomplete catalogue fails closed and must be rebuilt after ingestion. Deletions/purges and version activation are rechecked each request.

This is a deliberately simple provider-independent reference adapter, not a scalable persistent lexical index. It uses only public storage methods; no SQLite private SQL or backend row types enter the public RAG interface. A future paginated scoped-record API could replace the supplied ID catalogue without changing the retrieval contracts. Lexical retrieval deliberately requires registered embeddings in the selected space so it cannot introduce unindexed or foreign evidence through a side channel.

## Information needs and queries

Need kinds: job requirement, skill, experience, project, credential, accomplishment, technology, domain knowledge and question. Text and a caller-provided requirement ID are mandatory; text is bounded at 2,000 characters. The application supplies one meaningful need at a time. This stage does not parse or decompose a whole job description. Kinds participate in query identity but have no experimentally unsupported weighting yet.

`focused-v1` normalizes whitespace and uses the focused need verbatim. Identity includes kind, requirement ID, normalized text, policy, and expansions. Query identity describes a need; scope remains a separate mandatory field. All retrieval uses `embed_queries`, checks batch cardinality and provider configuration drift, and supplies the complete pinned semantic-space identity to search.

Optional `focused-v1-conservative-expansion` adds the AWS full name, Postgres canonical name, and containerization/Docker/model-serving concepts for an explicit containerized need. It does not expand Kubernetes to Docker, cloud platforms to one another, LoRA to QLoRA, or action verbs. Expanded text and exact additions are returned. This small fixed rule set was specified before the experiment; it is not fitted to individual answers. Defaults keep expansion off.

## Ranking and budgets

Semantic: exact Stage 3D cosine over active scoped records, using MiniLM + `title-section-v1`. Lexical: deterministic BM25 with k1=1.2 and b=0.75, computed over eligible chunk bodies. Tokenizer casefolds, retains C++, C#, dotted/hyphenated names and distinguishes LoRA/QLoRA; a fixed small stopword list removes common function words. No stemming or fuzzy adjacent-technology substitution. Terms must occur as tokens, not arbitrary substrings. Zero-score lexical documents are omitted.

Hybrid: equally weighted RRF, sum 1/(60+branch rank). Raw BM25 and cosine are never added. The measured default strategy is semantic with exact grouping enabled. Branches each default to 20 candidates; requested output is 0..100, normally 5. Output may contain fewer results than requested, including zero for lexical queries without matching terms. Equal scores break by embedding ID. Config/version, branch ranks/scores, RRF score, token intersections and query policy are all machine-readable. `exact_terms` reports all matching lexical tokens, not an inferred skill list.

## Scope, filters and trust

Store and citation service must bind to the same authorized tenant/candidate. Every request supplies both IDs and must match. Every registered embedding must exist in that bound store and selected space. A foreign perfect answer cannot enter lexical, semantic or fused results. Scope comes from authenticated trusted application context; this local reference does not itself authenticate users.

`SearchFilter` supports lifecycle (active default), source/evidence identity, source/evidence type, origin, trust, chunk policy and the verification-resolution marker. Exact historical versions can be selected by evidence ID plus `state='superseded'`; `state=None` is an explicit audit request. Wall-clock date ranges are deferred: ingestion time and source timestamp have different meanings and this reference does not guess which one implies current experience.

Candidate assertions remain eligible by default. Returned origins, `untrusted_data`, support IDs, relationship/containment tuples and provenance events are retained. `resolve_supports` is a pointer to authoritative verification resolution, never a verified boolean. Synthetic observed origins in the new fixture simulate trusted adapter outputs; no synthetic issuer sentence creates an actual authenticated credential. Malicious evidence strings are never executed or interpolated as instructions.

A result resolves via embedding ID → stored EmbeddingRecord → exact chunk revision → evidence/version → native locator/source URI. Outputs retain offsets and IDs, not full source text. Callers resolve text through the scope-bound citation service. All grouped references preserve this same complete lineage.

## Duplicate and source controls

Configurable (default enabled) whitespace-normalized exact-text grouping keeps the highest-ranked representative and separately records other discovered references. It never manufactures combined provenance or infers corroboration strength from duplication. Grouped references are bounded by branch budgets. It does not claim every duplicate in the entire corpus was found. Wording differences, negation, action verbs, punctuation and numeric changes remain distinct; automatic semantic near-duplicate suppression is intentionally deferred because it risks merging contradictory evidence.

Optional per-source caps apply after ranking and exact grouping. They may reduce the number of returned candidates. They do not add relevance or trust boosts. Experiments compare raw hybrid, deduplication, and deduplication plus cap=1, reporting representative-only and grouped recall separately. Many distinct sources repeating a claim can still crowd raw results; provenance count is not evidence independence.

## Consistency and operational limits

The caller must serialize ingestion/lifecycle mutation with retrieval. The Stage 3D protocol has no shared read transaction spanning vector state and the in-memory canonical ledger; no concurrent snapshot guarantee is claimed. The catalogue is immutable within a retriever instance. Reference exact search is O(ND); lexical statistics/tokenization and lifecycle checking are O(N) per request. Performance reports include those costs. SQLite databases are opened only on node-local `/tmp` inside Slurm and archived after close. No service, GPU, dependency upgrade or external API is introduced.

## Reproduce

From `~/scratch/resume-ai`: `source /etc/profile`, `module load slurm/current`, then `sbatch rag/retrieval/evaluate.slurm`. This writes only Stage 3E artifacts. It runs unchanged prior-stage tests/demos and frozen Stage 2 replay, hashes protected files and pinned models, compares frozen semantic scores, generates new CPU embeddings, measures quality and performance, and archives closed databases. The quality fixture, all new document/query vectors, branch diagnostics, configs and metrics are retained. Repeated query embeddings are checked for equality during the run.

Stage 3F is a future consumer of bounded, traceable candidate sets. Stage 3E performs no cross-encoder/model reranking, entailment classification, answer drafting, Qwen execution, fine-tuning or application workflow.
