# ADR 3D: relational production vector storage; isolated SQLite reference

Status: accepted for Stage 3D; production adapter/deployment deferred. Decision date: 2026-09-27.

## Decision and context

Select **PostgreSQL + pgvector as the intended production architecture** and **SQLite with exact binary64 cosine as the implemented Stage 3D reference backend**. This is one tested backend, not a claim that two implementations exist. No PostgreSQL service, RLS policy, pgvector extension, HNSW index or distributed deployment has been exercised here.

Resume AI's durable object graph is fundamentally relational: candidates own source versions, evidence owns claims/supports, chunks reference exact evidence revisions, and vectors reference chunks. VeriBridge will also need users, jobs, applications, resume/letter versions, contacts and agent runs. Our architectural inference is that keeping these references and version transitions in one transaction is more valuable initially than independently scaling a vector service. This conclusion depends on modest per-candidate corpora and a future relational system of record; it is not a benchmark claim.

MiniLM + title-section-v1 is only the provisional integration configuration. MiniLM and E5 in Stage 3C both have 384 dimensions, so dimension alone emphatically does not identify a semantic space. Search is candidate generation, never evidence of support.

## Evidence behind the comparison

pgvector provides exact search by default and optional HNSW/IVFFlat; filtering and index tuning change recall/performance tradeoffs. It supports keeping vectors in PostgreSQL alongside other data. We have not measured those indexes. [pgvector documentation](https://github.com/pgvector/pgvector)

PostgreSQL RLS can constrain reads and writes independently of a query's predicates. Owners normally bypass RLS; FORCE RLS affects owners, but superusers/BYPASSRLS remain exceptions. The future application must use a restricted role and trusted transaction scope. [PostgreSQL row security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

Qdrant offers payload filtering/indexes and tenant-oriented partitioning. Its distributed model supports shards/replicas, but does not promise atomic distributed point updates. This would add reconciliation responsibilities between the evidence ledger and vector service. [Payload indexes](https://qdrant.tech/documentation/concepts/payload/), [multitenancy](https://qdrant.tech/documentation/tutorials/multiple-partitions/), [horizontal scaling](https://qdrant.tech/documentation/scaling/horizontal-scaling/)

Chroma offers local persistent clients and tenant/database/collection concepts. Its distributed architecture is a distinct deployment with services, object storage and caches; moving from a local client is an operational change, not merely changing a filesystem path. [Python client](https://docs.trychroma.com/reference/python), [architecture](https://docs.trychroma.com/reference/architecture/overview), [distributed architecture](https://docs.trychroma.com/references/architecture/distributed)

SQLite is appropriate for local application storage, with limited concurrent writes; direct shared-network-filesystem access brings locking risks. It is a useful reference, not our multi-user server choice. [SQLite deployment guidance](https://www.sqlite.org/whentouse.html), [locking](https://www.sqlite.org/lockingv3.html)

## Product-specific comparison

The suitability/cost judgments below are architectural assessments, not measured vendor benchmarks or pricing quotations.

| Requirement | PostgreSQL + pgvector | Qdrant | Chroma | SQLite exact reference |
|---|---|---|---|---|
| Tenant/candidate isolation | Composite scope keys plus restricted roles and RLS; strongest fit for shared relational ledger | Separate collections/shards or payload partitions plus trusted authorization; tenant filter alone is insufficient | Tenant/database namespaces require authenticated access enforcement; local client is not a user-auth boundary | Physically distinct candidate files; immutable scope binding/FKs; trusted process and private files |
| Metadata filtering | Typed columns, joins and selective indexes | Indexed payload fields; mirror required ledger references | Collection metadata filters; mirror ledger references | Typed SQL filters and B-tree indexes before exhaustive cosine |
| Relational integration | Same database, foreign keys, transactions | Separate evidence DB and synchronization/outbox likely needed | Separate evidence DB and synchronization likely needed | Normalized local reference catalog; not a full durable evidence ledger |
| Persistence | Durable server storage | Persistent service storage | Persistent client/server/cloud choices | Actual on-disk SQLite, binary64 vectors |
| Vector indexing | Exact initially; HNSW/IVFFlat only after measured need | Purpose-built vector indexing and payload-aware search | Managed collection vector indexes | No ANN; exact scan of filtered candidates |
| Transaction behavior | Can commit source state and vectors atomically | Point update/consistency controls do not replace relational cross-system transactions | Collection API does not give this application a shared relational transaction | Atomic registration/upsert/lifecycle/delete transactions; writes serialized |
| Operational complexity | One DB if relational store also PostgreSQL; extension/version management | Additional service, health, replicas and ledger reconciliation | Simple local API; distributed deployment brings additional components | Low service burden; explicit file backup/ownership and single-host restrictions |
| Local development | Local server or managed dev instance | Local service/client | Very convenient persistent Python client | Python standard library; no downloads |
| Production deployment | Private managed/self-hosted DB, restricted application role | Private managed/self-hosted service alongside ledger DB | Server/cloud with explicit tenancy/auth design | Not selected for concurrent multi-user server deployment |
| Backups/migrations | SQL migrations, dumps/base backup/WAL/PITR | Snapshot + relational backup coordination; schema/payload evolution | Pin storage/client versions; test backup and collection migration | Versioned SQL migration; closed snapshots; reject unknown version |
| Horizontal scaling path | Partitioning/read replicas first; distributed writes require further architecture | Explicit distributed sharding/replication path | Distributed service architecture available | Candidate files can be placed independently; no distributed query/write layer here |
| Python | Standard PostgreSQL drivers and pgvector bindings | Python client | Python client | sqlite3, dataclasses, Protocol |
| License | PostgreSQL permissive license; pgvector PostgreSQL license | Apache-2.0 core | Apache-2.0 core | SQLite public domain; Python runtime terms |
| Cloud portability | Many managed PostgreSQL choices; verify extension availability/version | Self-host or cloud service; client/API portability | Local/self-host/cloud; deployment-specific features need review | Portable closed files on supported SQLite platforms |
| Observability | DB statistics, query plans, locks and index monitoring | Service/vector/cluster metrics need operations ownership | Client/service telemetry and storage diagnostics need evaluation | health_check, timing logs, query plans, integrity/FK checks |
| Expected burden/cost | Likely lowest incremental burden if PostgreSQL already hosts product data | Justified if vector workload deserves separate scaling; extra service cost initially | Lowest prototyping effort; production integration cost still present | No new service cost for experiment; maintenance of limited reference code |
| Evidence/provenance fit | Native relational references and coordinated lifecycle | Stable IDs in payload, authoritative data resolved elsewhere | IDs/metadata references, authoritative data resolved elsewhere | Minimal immutable chunk/support/event references, no duplicated source content |

PostgreSQL backup options and statistics are documented independently: [backup/restore](https://www.postgresql.org/docs/current/backup.html), [statistics](https://www.postgresql.org/docs/current/monitoring-stats.html). License sources: [PostgreSQL](https://www.postgresql.org/about/licence/), [pgvector](https://github.com/pgvector/pgvector/blob/master/LICENSE), [Qdrant](https://github.com/qdrant/qdrant/blob/master/LICENSE), [Chroma](https://github.com/chroma-core/chroma/blob/main/LICENSE), [SQLite](https://www.sqlite.org/copyright.html). Hosted service terms are separate and were not assessed.

## Why these choices

PostgreSQL wins on expected total-system integrity and operational simplicity, conditional on the relational product roadmap. Qdrant is a credible alternative if distributed vector capacity becomes a primary requirement; we have no evidence of that requirement yet. Chroma is convenient, but adopting its collection model now does not resolve the harder shared-ledger transaction/isolation requirements. Neither loses because of headline benchmark speed.

For Stage 3D, SQLite is preferable to installing a server or vector library merely to store 44-record fixtures. It directly exercises typed references, SQL constraints, failures, migrations and persistence with an exact numerical oracle. Its limitations are explicit and tested within a trusted local-process boundary. It does **not** stand in as evidence that PostgreSQL RLS, pgvector float32 ranking, or ANN recall works.

## Turing inspection and deployment mechanics

The project is not a Git checkout. Initial non-login PATH had no psql/postgres/Docker/Apptainer/Slurm. Module inspection found Slurm and Apptainer/Singularity; no PostgreSQL module appeared in the inspected inventory. This is not proof PostgreSQL could never be installed in user space. Compiling/deploying PostgreSQL + extension or a container service is unnecessary for this bounded reference experiment.

Project scratch is Ceph. Live databases are created with mode 0600 under a 0700 node-local `/tmp` directory inside a CPU Slurm allocation. SQLite uses rollback journals and FULL synchronous mode. Writer exits before reader opens. Closed, committed files are archived to scratch; restore onto local storage before opening. A short shared scratch transfer archive was used to deploy additive source files because login sessions may land on different nodes. No listener, root access or database credentials are needed.

## Future production implementation gate

Implement the same VectorStore protocol with PostgreSQL only when an actual private PostgreSQL/pgvector environment is available. Reuse the contract tests and replay fixtures, and add real non-owner RLS tests. Required design is in `../stage3d_architecture.md`. Do not call a sketch or an unexecuted migration validated infrastructure.

Use exact pgvector search first, compare binary32 storage to the binary64 oracle with explicit tolerances and tie analysis. Add per-space partial/expression HNSW indexes only after representative candidate sizes/concurrency fail a measured latency budget. Record exact-vs-ANN recall and filtered-search behavior. IVFFlat additionally requires representative training/data sizing. No ANN performance advantage is claimed by Stage 3D.

Model migration creates a new space; populate from authoritative chunk revisions, validate counts/lineage/replay, then deliberately select the new space at the caller. Keep old spaces during rollback and expire/purge via explicit lifecycle operations. Never relabel old vectors with a new model ID.

## Reconsideration triggers

Reopen this ADR if representative workloads show PostgreSQL cannot meet latency/concurrency/cost objectives after measured indexing/partitioning, if per-tenant vector volume becomes much larger, if independent regional vector distribution becomes necessary, or if the product's system of record is no longer relational PostgreSQL. Qdrant then warrants a measured comparison including synchronization, deletion convergence and tenant authorization. Chroma warrants reconsideration for a predominantly local/client product or demonstrated operational advantages in a supported deployment.

Migration must preserve deterministic IDs, space fingerprints, scope, source-version state, tombstones and provenance. Dual-write only with a reconciliation plan, compare exact rankings before cutover, and test deletions during the transition. No cross-system transaction guarantees should be assumed.
