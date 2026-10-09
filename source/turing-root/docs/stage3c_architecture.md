# Stage 3C embedding architecture

This stage adds embedding records and an offline exhaustive evaluation harness. All
Stage 3A/3B files remain unchanged. No vector database, persistent vector service,
production retrieval, hybrid search, reranking, Qwen integration or training exists.

## Contracts

`EmbeddingProvider` is a runtime-checkable structural Protocol with a typed immutable
`EmbeddingConfig` and separate `embed_documents` / `embed_queries` methods. Inputs
are ordered text sequences; outputs must preserve order and cardinality. Providers
own instructions/prefixes. Core modules import neither Transformers nor Torch.
`LocalTransformerProvider` is the only optional vendor-specific adapter. A future API
adapter can satisfy the protocol without altering evidence or chunking types.

`EmbeddingRecord` contains schema version, deterministic record ID and cache key,
Scope, chunk ID and exact revision, evidence/source/version, chunk-policy ID, complete
small model config (provider, model, revision, dimension, normalization, query and
document prefixes, canonical settings JSON), input strategy/hash, immutable vector,
created_at, origin, immutable untrusted-data state, support IDs and provenance-event
IDs. It does not copy source text or large provenance structures. Verification is
resolved from the exact chunk revision's original supports, never inferred from text.

`ChunkEmbedder.resolve(record, CandidateChunks)` validates scope and reference fields,
resolves an authoritative Stage 3B citation and returns the unchanged chain:
record -> exact chunk revision -> evidence/version -> source/locator/supports/history.
Evidence deletion and supersession use Stage 3B historical citation semantics. This
is an application-bound reference API; authentication is outside this stage. Only
trusted application code should supply RetrievalChunk objects; uploaded JSON is not
an authorized chunk constructor. Records do not cryptographically attest vector truth.

## Identities and in-memory reuse

Canonical JSON and SHA-256 reuse Stage 3A's stable-ID convention, with stage3c-v1
markers. A cache key binds scope, semantic input hash, input-strategy version, full
provider configuration fingerprint and document encoding role. Configuration includes
model/tokenizer revision, prefixes, pooling, max tokens, overflow behavior, normalization,
dimension, dtype, device, batch size, thread count and library versions. The input hash
covers the builder's exact UTF-8 output before the provider prefix; the cache identity
also binds that prefix. Do not compare/reuse records from different configurations.

Record identity additionally binds chunk ID and annotation revision. Identical text can
reuse computation within one candidate even across sources/policies, while producing
separate source-bound records. Annotation changes need a new record but can reuse its
unchanged vector. Candidate A and B have identical semantic inputs/vectors but distinct
keys and records. The current cache is ephemeral and never shared across scopes.
Timestamp is excluded from identity. Fixture runs use an explicitly fixed logical
creation clock (2026-09-27 UTC); Slurm logs identify actual execution. Ordinary clients
use the real UTC clock by default. Floating point vectors are not promised bit-identical
across hardware/libraries; same-environment repeat drift and batch drift are measured.

Batch cardinality, finite/nonzero values, dimension and declared unit norm are checked
before cache publication. Invalid batches leave the cache unchanged. Models/configs
cannot silently reuse one another's vectors. Query embeddings do not enter the document
cache; their role is explicit and preserved in evaluation manifests.

## Input construction and untrusted text

`raw-v1`: exact chunk text.

`title-section-v1`: existing source title, existing locator section if present, then
exact chunk text, labeled with `Title:`, `Section:` and `Text:`. No generated heading,
new skills, provenance IDs, tenant/candidate IDs, trust labels, verification state or
confidence scores are added. A section is source-wide locator context, not an inferred
heading for an arbitrary span. Titles themselves remain untrusted source content.

The strategy adds framing labels, not claims. It cannot make malicious text executable
or verified. Embedding an injection preserves `untrusted_data`; supports remain
unreviewed. Fixture-only authority labels never become verification records or semantic
prefixes. Even externally-observed origin would not itself imply verified claims.

## Local encoder

Both pinned models use attention-mask mean pooling and L2 normalization on CPU float32.
MiniLM uses symmetric encoding with empty prefixes and a 256-token budget. E5 uses
`query: ` and `passage: ` and a 512-token budget. Token counts include prefixes and
special tokens. Overflow raises an error; no hidden truncation is allowed. Batch size
is 16, threads 4, eager attention, seed 0, deterministic Torch algorithms, eval mode
and inference mode. Remote model code is disabled. Actual model assets and licenses are
hashed in `results/stage3c/models.lock.json`. Downloads are public and unauthenticated.
After acquisition, loading uses local-files-only and the Slurm runner forces offline mode.
No installation or change to the prior .venv was required; exact packages are recorded
per model. `prepare.py` refuses silently replacing a lock; another model experiment
requires an explicitly separate lock/result version.

## Similarity and evaluation

Cosine works for normalized and unnormalized finite real vectors. Scaling before
normalization avoids overflow/underflow for finite extreme values. Empty vectors,
zero vectors, NaN/Inf, nonnumeric values and dimension mismatch raise errors. Dot
products use accurate summation; rounding is clipped to [-1,1]. Cosine is not calibrated
confidence and score ranges cannot be compared between models.

Rank by descending cosine then stable ID. Ties within 1e-8 are not hard-negative wins.
Recall@k is fraction of judged relevant IDs found in the first k; MRR is reciprocal
first relevant rank; means are macro-averaged across queries. Every fixture query has
one designated target. Hard-negative win compares the best designated positive against
the best specified negative and requires a margin above 1e-8. Pairwise scores, margins,
full rankings, dangerous specified negatives in top 3, winning chunk and target-span
containment are saved. No arbitrary success threshold is used.

The benchmark ranks evidence by the best-scoring chunk and saves every underlying
vector/input/chunk mapping. This avoids overlap copies crowding out distinct sources.
The choice has a max-over-chunks selection bias; it is only an offline evaluation rule,
not a production retrieval design. Supported Recall@1 also requires the winning chunk
to contain the exact target sentence. Complete scores/rankings replay from frozen
vectors without model inference. Fixtures are synthetic, deliberately small, English,
and not an independently held-out estimate of real resume quality.

## Reproduction on Turing

From `~/scratch/resume-ai`:

```sh
# First installation only, after capturing the pre-stage manifest:
.venv/bin/python -B -m rag.embeddings.prepare
# Existing installations already have locked, cached model assets; skip prepare.
/cm/shared/apps/slurm/current/bin/sbatch rag/embeddings/evaluate.slurm
# After benchmark completion (no model inference on login node):
.venv/bin/python -B -m rag.embeddings.validate
# Run model smoke checks in a CPU allocation:
/cm/shared/apps/slurm/current/bin/sbatch --account=cs541 --partition=academic \
  --cpus-per-task=4 --mem=8G --time=00:10:00 \
  --output=results/stage3c/smoke-%j.log \
  --wrap='HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 .venv/bin/python -B -m rag.embeddings.integration'
```

Evaluation JSON/record exports are benchmark artifacts only, not a persistent vector
store. Model files reside under `models/stage3c`. Prior benchmark runners are not used
to rewrite old outputs. The Stage 3C validator executes their tests/frozen replay and
compares prior demos in memory. Root Stage 1 GPU scripts are preserved; historical
GPU generations are not rerun or represented as new measurements.
