# Stage 3D completion report — persistent vector storage and indexing

**Stage 3D is complete. Stop here.** All implementation and validation are in `~/scratch/resume-ai` on WPI Turing. Stage 3E and all later functionality remain unimplemented.

**Validation:** 164/164 tests pass; all 352 frozen Stage 3C queries reproduce identical full rankings and scores; 1,308 stored embeddings resolve back to their exact citations. All 330 preexisting protected files and 22 pinned model assets are unchanged. No production PostgreSQL, pgvector or ANN claims are made.

## 1. Architecture implemented

An additive provider-independent storage/index contract and a persistent SQLite exact-search reference adapter. Domain/evidence/chunking/embedding code from prior stages is unchanged. Vectors are persisted as binary64 values in normalized relations with minimal provenance references, explicit semantic spaces, source-version states and scoped deletion.

The store provides low-level nearest-neighbor candidate generation only. Similarity does not prove support, certification, verification or factual equivalence. API consumption versus API implementation remains a known semantic failure from Stage 3C.

## 2. Vector-store options compared

PostgreSQL + pgvector, Qdrant, Chroma and SQLite reference were compared on tenancy, filtering, relational integration, persistence/indexing, transactions, operations, local/production deployment, backups/migrations, horizontal scaling, Python, licensing, portability, observability, burden/cost and evidence-model fit. The full evidence-backed matrix and primary-source links are in [ADR 3D](adr/vector_store_selection.md).

No technology was selected merely because it was easy to install or had favorable benchmark reputation. No vendor latency or pricing benchmark was run.

## 3. ADR / selected backend

**Production direction: PostgreSQL + pgvector. Implemented and validated Stage 3D backend: SQLite exact reference.** These are explicitly different decisions. A PostgreSQL adapter is not supplied as an untested stub. The executed migration is SQLite migration 001.

Turing has Slurm and Apptainer/Singularity modules, but PostgreSQL/pgvector were not available in the inspected environment. Installing a production service was unnecessary. Scratch is Ceph; live SQLite files were kept on node-local `/tmp` during a CPU allocation, then closed and archived to scratch.

## 4. Why selected

The future product's users/candidates/sources/evidence/claims/jobs/applications/document versions/contacts/agent runs make relational constraints and shared transactions valuable. PostgreSQL is the best architectural fit under that assumption. Qdrant is a credible reconsideration if independent distributed vector scaling becomes necessary. Chroma's local convenience does not remove ledger synchronization and production authorization requirements.

SQLite is an honest local reference that proves persistence, constraints and transaction behavior without a new service. Its physical candidate isolation and exact numerical behavior make it useful for correctness tests. It is not selected for a concurrent multi-user service. Reconsideration and migration triggers are documented in the ADR.

## 5. Files created / modified

**No preexisting project file was modified.** Additions:

- `rag/vectorstore/__init__.py`, `base.py`, `models.py`, `config.py`, `sqlite_reference.py`
- `rag/vectorstore/replay.py`, `benchmark.py`, `validate.py`, `audit.py`, `validate.slurm`
- `migrations/001_vectorstore_sqlite.sql`
- `tests/rag/test_vectorstore.py` (39 new tests)
- `docs/adr/vector_store_selection.md`
- `docs/stage3d_architecture.md`, `docs/stage3d_report.md`
- `results/stage3d/`: initial protection manifest, deployment transfer archive, environment, writer/reader replay reports, performance, test/regression/demo logs, validation, scheduler log/accounting, closed database archive and final integrity audit.

The final audit enumerates deliverable hashes. The initial manifest covers all prior source/tests/docs/fixtures/results (excluding bytecode and the virtual environment); pinned Stage 3C model assets are verified separately against the existing lock. No dependency was installed or upgraded.

## 6. Vector-store abstraction

`VectorStore` is a typed runtime-checkable Protocol with a bound `Scope`. Operations: register chunk references; upsert embeddings; get embedding; search vectors; count; activate source version; delete embeddings/source; health check; close. Domain contracts contain no database-provider types. `StoreConfig` accepts a private local root directly or via `RESUME_AI_VECTOR_ROOT`.

`EmbeddingSpace`, `ChunkReference`, `SearchFilter`, `VectorQuery`, `StoredEmbedding`, `SearchHit` and `StoreHealth` make inputs/results explicit. Search produces IDs and scores, not an assembled retrieval answer. The architecture document explains contract semantics and future provider implementation requirements.

## 7. Persistent schema

Normalized tables: `scope_binding`, `embedding_spaces`, `sources`, `source_versions`, `chunk_references`, `vector_records`, `purged_ids`; a `stored_vectors` view resolves effective lifecycle. Foreign keys bind scope, space/dimension and exact chunk/evidence/source references. A partial unique index enforces one active source version. Vector byte length must equal dimension × 8.

Model configuration and small ID/hash arrays use canonical JSON; source documents and evidence bodies are not copied. Filter fields include source/evidence types, policy, origin/trust, source/evidence identity and lifecycle. Verification remains a support-resolution reference. Retrieval-critical B-tree indexes are defined; there is no ANN index. Exact search scans filtered rows with the existing cosine function.

## 8. Embedding-space isolation

A deterministic space fingerprint includes the complete Stage 3C configuration identity and embedding-input version. Provider/model/revision/dimension/normalization/prefixes/provider settings all participate. Both evaluated models have 384 dimensions, so equality of dimension is insufficient.

Tests cover changes to every configuration component, unknown input strategy, incompatible IDs, same-dimensional models in separate spaces, invalid query dimensions and vector shape constraints. A model upgrade requires a new space and deliberate re-embedding/cutover; old vectors cannot be relabeled by upsert.

## 9. Tenant/candidate isolation

One private SQLite file per hash of `(tenant_id,candidate_id)`, a checked immutable scope binding, scope foreign keys, bound-scope methods, deterministic scoped IDs and denied ATTACH/DETACH provide independent protection from missing query predicates. Tests deliberately omit tenant/candidate SQL predicates, attempt foreign reads/writes/deletes/search, mutate scope columns, substitute a foreign file and insert identical vectors across tenants/candidates.

All attempts remain scoped or are rejected. Identical vectors are independently stored under distinct embedding IDs. This protection assumes trusted code and the owning OS account; it is not server-side authorization against arbitrary database/file access. Future PostgreSQL RLS and restricted-role requirements are designed but untested.

## 10. Persistence / reopen demonstration

Slurm job **2328526** ran writer PID **344681**, which committed all 16 frozen experiments and exited. Independent reader PID **344682** reopened the files, read/search-tested them and resolved all 1,308 records. Additional unit tests launch separate writer and reader subprocesses, with no parent write.

`results/stage3d/closed-databases-2328526.tar.gz` preserves the closed replay and scale databases. Restore to a private local filesystem before opening; do not run them live on Ceph. Reopen times below exclude process startup, first query and archive extraction. Node-local temporary directories were cleaned after archiving. The final audit checks all 20 archived database hashes and restores a 44-record database into a fresh private local directory for a health/read/search check.

## 11. Idempotent-upsert demonstration

Every replay corpus was upserted twice with unchanged record counts. Unit tests verify duplicate batches and exact no-op timestamps, preserve original embedding creation time on regenerated records, allow only operational note changes, and reject altered vector/configuration/lineage under an existing identity.

A failed batch containing a valid record followed by a missing-reference record leaves neither vector nor newly created embedding space behind. Partial reference-registration failure likewise rolls back all writes.

## 12. Source/version lifecycle

Registered versions start staged. Explicit activation verifies the expected current evidence ID, requires live vectors and atomically supersedes the previous version. Old versions and provenance remain available for scoped audit. Default search/count includes only active data.

Tests cover v1 → v2, history filters, stale compare-and-swap tokens, attempts to reactivate older versions, empty activation and replaying old embeddings without reactivation. Activation only checks that some live vectors exist; verifying complete intended model/chunk coverage belongs to the caller's future ingestion orchestration, not an implicit storage claim.

## 13. Scoped-deletion behavior

Embedding/source deletion defaults to tombstoning. Source deletion covers its versions and semantic spaces and blocks revival. Explicit purge removes vector rows while retaining minimal replay-blocking embedding IDs and lineage references. Tests prove unrelated sources/candidates survive and delayed upserts cannot resurrect deleted data.

Purge does not claim secure erasure of SQLite free pages, historical archives or the authoritative evidence ledger. Account-wide privacy workflows and backup retention remain future work; this schema does not make scoped deletion impossible.

## 14. Provenance / trust preservation

Original record IDs, chunk/revision IDs, evidence/source/version, policy, input hash, model identity, origin, untrusted-data flag, support IDs and provenance-event IDs survive persistence. Every frozen record round-trips through the original Stage 3C citation resolver.

The malicious certification instruction remains untrusted text. Storage, ranking and persistence never promote it. Verification is represented as `resolve_supports`, so a future retrieval layer must consult the authoritative exact support/version state rather than treating a vector metadata flag as verified truth.

## 15. Stage 3C ranking replay comparison

**16/16 experiments, 352/352 queries:** complete embedding rankings agree with the in-memory cosine oracle; complete evidence rankings agree with frozen Stage 3C outputs. Maximum score difference: **0.0**. This includes both models, both input strategies, both policies and short/long fixtures. The existing evidence aggregation is used only inside the offline replay harness; it is not a production retrieval policy.

Primary short-corpus Policy B examples (Stage 3C = Stage 3D):

| Configuration | Recall@1 | Recall@3 | MRR | Hard-negative wins |
|---|---:|---:|---:|---:|
| MiniLM + title-section-v1 | 68.18% | 90.91% | 0.8030 | 86.36% |
| MiniLM raw-v1 | 59.09% | 90.91% | 0.7652 | 81.82% |
| E5 raw-v1 | 63.64% | 81.82% | 0.7554 | 77.27% |
| E5 + title-section-v1 | 50.00% | 81.82% | 0.6703 | 72.73% |

The MiniLM context corpus's 44-vector query mean was 14.99 ms. Frozen model outputs were reused; no model inference or semantic tuning took place. MiniLM remains provisional, not permanently optimal. Neither retrieval accuracy nor trust safety improved merely because vectors were persisted.

## 16. Performance measurements

One CPU, 384-dimensional synthetic independent vectors, deterministic seed 73, node-local storage. Each row has five warm exact-query samples; full timings and query plans are in `performance.json`.

| Records | Insert batch | Insert vectors/s | Exact query median | Reopen | Database MiB |
|---:|---:|---:|---:|---:|---:|
| 100 | 1 | 3,259 | 32.34 ms | 0.354 ms | 0.734 |
| 100 | 100 | 4,535 | 32.58 ms | 0.346 ms | 0.734 |
| 1,000 | 100 | 4,442 | 342.29 ms | 0.372 ms | 6.262 |
| 10,000 | 100 | 4,127 | 3,545.89 ms | 0.426 ms | 61.719 |

Ten-thousand-record insertion took 2.423 s; reference registration separately took 0.434 s. A fully validated duplicate upsert batch took 10.015 s, reflecting reconstruction/identity checks; idempotency is correct but this reference path is not throughput-optimized. At 100 records, batching improved insertion throughput in this run; no statistical or production claim is justified.

The exact Python cosine scan scales linearly and is unsuitable for a low-latency 10,000-vector service without further backend work. These results motivate measuring a native backend when needed; they do not measure pgvector/Qdrant/Chroma or prove ANN advantages. Database footprint includes normalized metadata/indexes; archive size and peak memory are separate quantities.

Slurm job: 68 seconds elapsed, one allocated CPU, 2 GiB memory request, no GPU requested, batch MaxRSS 290,860 KiB, COMPLETED exit 0. The scheduler placed the CPU-only job on a GPU-capable host; no GPU was used.

## 17. Tests / regression results

| Suite | Passed |
|---|---:|
| Stage 1/2 evaluation and artifact regression tests | 19 |
| Stage 3A ingestion/evidence | 27 |
| Stage 3B chunking | 39 |
| Stage 3C embeddings/evaluation | 40 |
| Stage 3D storage | 39 |
| **Total** | **164** |

All old tests are unchanged. Frozen Stage 2 replay passes; Stage 3A and 3B demos equal their saved JSON. All 330 protected files are byte-identical, including prior reports/benchmarks; 22 pinned model assets match existing hashes. Stage 1 historical GPU benchmark scripts and Stage 2 generative outputs were preserved, not regenerated. No new generative benchmark result is claimed.

Stage 3D covers the protocol, exact/idempotent persistence, independent processes, configuration/dimension safety, missing references, source lifecycle, scoped tombstone/purge, malicious text/trust, provenance, metadata filtering, health, SQL constraints, file substitution/symlinks/permissions, unknown schema rejection and abrupt process exit during an uncommitted write. The separate replay harness covers all frozen ranking comparisons.

## 18. Security assumptions and remaining limits

No public database service/listener, credentials, root installation or paid API was introduced. Connections are local files; configuration comes from trusted code/environment. Evidence content is never executed. Parameterized SQL handles values and typed allowlisted filters supply column names.

The trusted ingestion process authenticates scope and reference provenance; arbitrary Python/SQL access as the same OS account can bypass a local reference boundary. Private file modes are not a replacement for future service authorization. PostgreSQL RLS, actual pgvector precision, concurrent production writers, ANN, disaster recovery, secure erasure and distributed behavior remain unvalidated. Live SQLite on network filesystems is explicitly unsupported by this workflow.

Production deployment is gated on real backend integration tests, restricted-role RLS tests, representative latency/concurrency/recall measurements and backup/restore validation. The ADR includes migration/reconsideration triggers; this choice is not permanent dogma.

**Stopped after Stage 3D.** No production retrieval orchestration, hybrid/BM25 search, query expansion, requirement decomposition, reranking, support classification, Qwen-RAG, QLoRA, fine-tuning, browser automation, job searching/applications or recruiter outreach was implemented.
