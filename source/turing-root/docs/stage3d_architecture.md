# Stage 3D architecture and operating contract

Scope: persistent vector storage and exact indexing/search primitives only. `VectorStore` is a runtime-checkable typed protocol, bound at construction to one trusted `Scope`. Stage 3A/3B/3C domain files are unchanged. `sqlite_reference.py` is the only database adapter. No PostgreSQL adapter is represented as implemented.

## Data flow and contract

1. Resolve an exact Stage 3B citation and construct `ChunkReference.from_citation`. This extracts IDs, source/evidence types, support/event IDs and the two Stage 3C input hashes; no source text is stored.
2. `register_chunks` commits immutable reference projections. Source versions begin **staged**. Registration is trusted ingestion infrastructure, not an endpoint for arbitrary evidence-provided metadata.
3. `upsert_embeddings` validates Stage 3C record shape, scope, all reference fields, input hash, deterministic cache/record identity, vector values, normalization, and embedding space. A batch is all-or-nothing, including newly inserted spaces.
4. `activate_source_version(..., expected_current=...)` atomically supersedes the previous version and activates the new one. It checks a compare-and-swap token, monotonic version, nondeleted source and at least one live vector. The caller must verify desired corpus/model coverage before activation; this primitive deliberately does not orchestrate ingestion completeness.
5. `get_embedding` returns an immutable Stage 3C record plus effective lifecycle and operational timestamps. It allows audit access to historical/tombstoned data within the bound scope.
6. `search_vectors(VectorQuery(space, vector, limit, filters))` returns IDs and cosine scores, ordered by descending score then embedding ID. `count` uses the same typed filters. Search defaults to active versions; a caller must explicitly request historical/staged/deleted data. No text-to-query embedding, expansion, support inference or reranking is implemented.
7. `delete_embeddings` or `delete_source` tombstones by default; explicit `purge=True` removes vector rows. `health_check` checks schema version, quick integrity, foreign keys and file scope binding. `close` and context management release the connection.

Source activation and vector ingestion are deliberately separate transactions: partially ingested replacements remain staged; old active vectors remain visible until the activation commit. There is no claim of a single transaction spanning the existing in-memory evidence ledger and this durable projection.

## Schema and invariants

`migrations/001_vectorstore_sqlite.sql` is the executed migration. Unknown versions fail closed; migration 1 is transactional, recorded by `PRAGMA user_version`. Future migration versions require explicit scripts, backup/restore tests and contract replay; there is no silent reset or auto-downgrade.

| Relation | Purpose / constraints |
|---|---|
| scope_binding | Exactly one immutable tenant/candidate pair; singleton CHECK and unique pair |
| embedding_spaces | Provider, model, revision, dimension, normalization, prefixes, canonical provider config and input strategy; deterministic space PK |
| sources | Source ID and scope FK; irreversible deleted flag through adapter |
| source_versions | Exact evidence ID/source/version; unique source+version; lifecycle; one active version per source via partial unique index |
| chunk_references | Exact chunk revision PK; chunk/evidence/source/version/policy IDs, typed filter columns; composite evidence FK; minimal support/provenance/input-hash arrays |
| vector_records | Deterministic embedding ID PK, explicit scope FK, space+dimension FK, chunk FK, binary64 vector length CHECK, cache/input hashes, timestamps, tombstone, note |
| purged_ids | Embedding ID only; prevents delayed replay from restoring purged vectors |
| stored_vectors view | Joins immutable lineage and computes effective state from source/version and per-vector tombstone |

Arrays are canonical JSON only for bounded ID lists and strategy/hash pairs; model configuration is canonical JSON because its fields are provider-specific. Source documents, claims, raw text, citation quotes and large evidence objects are not duplicated. Verification is represented by **resolve_supports**, never copied into a stale verified boolean. Full authority resolves via exact support IDs and the Stage 3A verifier model.

Original embedding `created_at` is retained even if an identical record is regenerated later. `stored_at` records initial persistence. Only the bounded operational `note` may be changed through upsert, updating `updated_at`. Identical retries are true no-ops; any change to identity-bearing metadata or vector values is rejected. Lifecycle is a separate operation and never changed by upsert. Return counts report accepted input records, not distinct insertions.

## Embedding-space compatibility

`space_id = stable_id('embedding_space', 'stage3d-v1', config.identity, input_strategy)`.

The existing configuration fingerprint includes provider, model, revision, dimension, normalized flag, query/document prefixes, tokenizer/pooling/runtime options and canonical provider configuration. This is intentionally conservative: even a configuration change with the same vector dimension gets a distinct space. A normalized boolean means the existing Stage 3C unit-normalization contract; a future different normalization policy must change the provider/config identity. Explicit query space is mandatory. Query dimension is checked; an unknown space is rejected. The caller is responsible for truthful query/model provenance; numeric vectors cannot prove which model generated them.

The store rechecks Stage 3C cache and record IDs. Input strategies and hashes must agree with the registered chunk reference. A space mismatch cannot overwrite or silently join another model's vectors. Model upgrades require re-embedding into a new space, replay validation and deliberate caller cutover. There is no alias silently switching a model underneath existing data.

## Isolation and threat boundary

Reference defense in depth:

- Each candidate scope maps through a hash of the full tenant/candidate pair to a separate local database file. There is no query method accepting arbitrary scope overrides.
- A singleton binding rejects a database copied/renamed into another scope's path. Root is private 0700; files are 0600; final-component symlinks are rejected.
- Scope columns and foreign keys reject foreign vector/source writes; immutable binding triggers reject reassignment. Stage 3C deterministic identities are scope-bound.
- Reads missing all scope predicates can only see that file's rows. SQLite ATTACH/DETACH is denied on the adapter connection.
- Deliberate cross-tenant and same-tenant/different-candidate reads, writes, search, source deletion and vector purge are tested with identical vectors.

This is a trusted local application/reference boundary, **not SQLite RLS**. The OS account/root owner can open other files, change code or disable constraints; private attributes are not a security boundary against arbitrary Python execution. Caller scope must come from authenticated authorization in a future service, never from a CV, query string or model output. The root directory/parents must be controlled by the trusted operator; do not accept arbitrary paths from users. Public multi-tenant clients must not access this backend directly.

## Filtering and indexing

Filterable typed fields: lifecycle, source ID, evidence ID, source type, evidence locator type, origin, trust, chunk policy and the verification resolution marker. The space is a required query argument. Tenant/candidate is enforced by the bound file and checked scope, not an optional filter.

Indexed: embedding ID, space+tombstone+chunk revision, chunk revision, evidence ID, source+version/state, and source-type/evidence-type/policy. Source-type/evidence-type are useful coarse candidate partitions; policy prevents accidental mixture of chunking experiments. Origin/trust are retained but low cardinality, so there is no separate trust index. Verification-state filtering can select the resolution marker only; real verified/unverified support filtering is deferred until an authoritative verification projection with invalidation exists. Do not interpret unknown/resolution-needed as verified. Arbitrary user metadata and notes are not indexed.

Reference search streams persisted candidate vectors through the **same Stage 3C cosine** implementation and lets SQL select top-k. It is exhaustive O(N·D) over matching rows, not an ANN vector index. Binary64 storage avoids precision drift from frozen Python floats; deterministic ties are preserved. B-tree query plans and measured scale costs are retained in `performance.json`. A future adapter may optimize exact search but must preserve the contract and replay behavior. No ANN performance is claimed.

## Lifecycle, deletions and failure recovery

`staged -> active -> superseded`; deletion makes records effectively deleted. Source versions retain exact provenance. Activation never moves backwards, rejects a stale expected-current token, and never revives a deleted source. Re-upserting old records does not make their version current. Chunk annotation revisions can coexist within the same source version; the caller can tombstone obsolete embedding IDs explicitly. There is no automatic annotation-revision selection policy here.

Deletion is bound to one candidate file. Source deletion covers all that source's spaces and versions and blocks further ingestion under that source ID. Tombstones retain audit data but are excluded from default search. Purge removes the vector bytes from live rows and leaves a noncontent embedding-ID marker to prevent delayed resurrection; source/chunk/support references remain. A new source identity is needed for an intentional reconnect after deletion.

Purge is **not** secure erasure: SQLite free pages, journal remnants, snapshots, replicas of earlier files and the evidence ledger require a separate future privacy workflow. Account deletion can remove the entire closed candidate file and associated backups through a trusted operator; no full compliance workflow is claimed. Never delete another candidate's file. Existing historical evidence remains outside this vector projection.

Mutating operations use BEGIN IMMEDIATE/commit/rollback; foreign keys are enabled; journal mode DELETE and synchronous FULL are explicit. Partial invalid batches roll back all earlier rows and space creation. A subprocess killed via abrupt exit after an uncommitted delete leaves prior committed data readable. Connection timeout bounds lock contention; callers may retry an entire idempotent batch after transient database errors. One connection is single-threaded; use separate connections for separate workers. This implementation is not intended for sustained concurrent writers or network filesystems.

## Production PostgreSQL design (not executed)

Use normalized embedding_spaces and vector_records plus authoritative tenant/candidate/source/evidence/chunk tables. Every owned key and FK must carry `(tenant_id,candidate_id,...)`, including references from chunks through evidence and vectors. A candidate FK must bind candidate to tenant, not independent FKs that allow mismatched pairs. Model config identity and dimension belong in embedding_spaces, with a composite `(space_id,dimension)` FK and `vector_dims(embedding)=dimension` CHECK. Use `(tenant_id,candidate_id,embedding_id)` as the vector PK. Keep support/provenance in normalized join/reference tables where available.

Enable and FORCE RLS on **all** owned tables with matching USING and WITH CHECK predicates for both scope components. Application role: nonowner, NOSUPERUSER, NOBYPASSRLS; no DDL, TRUNCATE or permission to change security-definer routines. Trusted middleware validates membership and sets scope using transaction-local settings on every transaction, with a fail-closed missing-scope policy. It must reset/rollback pooled connections; user SQL is prohibited. A scope-setting GUC is not authentication against a client allowed arbitrary SQL. For direct database users, map roles to membership instead of letting them select their own scope settings. Migration/backup roles are separate and carefully audited.

Source activation locks the source row, verifies expected current version, and updates current state atomically with required vector publication. SQL migrations enforce one active version per scoped source. Exact queries bind space, tenant, candidate and active-state filters, while RLS remains the independent isolation layer. Start with B-tree filter indexes and exact cosine. Index each semantic space separately if ANN is later justified; do not put unrelated models in one HNSW graph merely because dimensions match.

Before claiming production readiness: run the complete contract suite on actual PostgreSQL; intentionally omit scope predicates as the real application role; test missing scope, forged scope, FK/unique error leakage, pooled connections and transaction rollback; validate backups/restores and binary32/ANN ranking differences. None of these PostgreSQL-specific checks were performed in Stage 3D.

## Reproduction

From `~/scratch/resume-ai` on Turing:

```sh
source /etc/profile
module load slurm/current
sbatch rag/vectorstore/validate.slurm
```

This creates only Stage 3D reports and a closed database archive. It does not load embedding models or run generative inference. Tests run with `-B` to preserve old artifacts. `replay write` exits; `replay read` reopens independently and compares all 16 frozen experiments. Benchmark generation is synthetic and deterministic (seed 73), on one CPU.

For local use, set `RESUME_AI_VECTOR_ROOT` to a private local directory and construct `StoreConfig.from_env()`. Use one bound store per authorized scope. To inspect archived persistence, extract the tarball into a new private node-local directory and invoke `python -B -m rag.vectorstore.replay read <extracted>/replay` from the project. Do not open the archived files directly on Ceph. Stage 3D report paths are overwritten by intentional validation reruns; historical stages are never rewritten.
