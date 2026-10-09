# Stage 3B architecture: evidence-preserving chunking

Stage 3B composes with the unchanged Stage 3A domain and scoped ledger. No prior
source, tests, fixtures, benchmarks or result artifacts are modified. The new
standard-library-only package runs on CPU; no models, GPU jobs or packages are needed.

## Pipeline and API

`CandidateLedger -> EvidenceRepository protocol -> CandidateChunks.generate -> RetrievalChunk`

`CandidateChunks.cite(chunk_id, revision_id) -> Citation -> Evidence -> Source`

The repository protocol is satisfied by Stage 3A's CandidateLedger. Generation reads
only canonical normalized content, supports and history through that scoped API.
No vector provider or embedding interface is imported. A CandidateChunks instance is
bound to one authorized repository. `get`, `cite`, `generate`, and `untrusted_envelope`
reject foreign identifiers. No unscoped index or lookup exists. As in Stage 3A,
authentication must bind the scope outside this in-process reference implementation;
Python process memory is not a hostile-code security boundary.

## Immutable schema

RetrievalChunk contains:

- `chunk_id`, `revision_id`, and chunk schema version 1.
- The original immutable `Evidence`: scope, source and evidence IDs, version, raw and
  normalized hashes/references, origin, supplied-by category, adapter/normalizer,
  source/ingestion timestamps, metadata, native locator and fixed `untrusted_data` trust.
- Full `ChunkPolicy` and canonicalized adapter-supplied `BoundaryHint` tuple.
- `input_support_ids`: the complete support set used to choose boundaries, including
  supports outside the resulting span, allowing historical boundary regeneration.
- `start`, `end`: half-open Unicode code-point offsets into canonical normalized text.
- `text`: exactly `normalized[start:end]`, never stripped, joined, paraphrased or prefixed.
- `measured_size`, the size under the pinned sizing implementation.
- `claim_links`: original Support objects plus FULLY_CONTAINED or PARTIALLY_OVERLAPPING
  and exact evidence-relative intersection offsets. Each original Support retains
  its claim ID, native pointer, relation, kind, confidence, extractor, rationale and
  verification state. Chunk-relative intersection offsets are intersection minus start.
- `provenance_events`: immutable source history snapshot at generation.

A Citation contains the chunk, original Source, current evidence ID (or null),
`current`/`superseded`/`deleted` status, a history-changed flag and coordinate-system label.
The chunk embeds the evidence locator; links retain any more precise support locator.

## Identity and historical views

IDs use Stage 3A canonical JSON/SHA-256 helpers, with a separate `stage3b-v1` domain
marker. Chunk identity includes tenant and candidate, evidence ID and source-version
ordinal, policy fingerprint, supplied hints and exact start/end. Evidence ID already
binds source, raw/normalized content hashes and provenance. Equal text at different
positions, sources, scopes or versions therefore remains distinct. Different policy
fields change identity even if a short input produces the same boundaries.

Revision identity additionally includes the full input support ID set, overlapping
support/link records and provenance event snapshot. The same evidence may be
re-extracted or ingested again without changing the text identity. New views do not
overwrite old revisions: the reference store retains `(chunk_id, revision_id)` keys;
a lookup without revision uses the latest generated view for that chunk ID.
Historical views stay auditable. After reannotation, old boundaries can be regenerated
with the stored policy, hints and `support_ids=chunk.input_support_ids`. New source
history produces a new revision; the original revision remains readable. Caller clocks
can change event/revision IDs but never the deterministic text chunk IDs.

These APIs expose exact historical objects, not a current-vector-index membership
service. Old chunks and old policy generations remain explicitly addressable. A future
index must select a generation and inspect citation status before exposing current results.

## Versioned sizing and boundaries

Policy v1 uses Unicode characters, not bytes, words or estimated tokens. This is an
explicit dependency-free baseline, not a claim that 640 characters fit any particular
embedding model. Policy metadata includes name, version, max size, overlap budget,
unit, sizer identity, boundary algorithm revision, minimum fill percentage and schema.
No size is hard-coded into domain types. `Sizer` allows exact future token counting
and prefix selection with pinned tokenizer assets/revision; no Qwen dependency or
new tokenizer download exists. Prefix selection must return a nonempty fitting span,
and counts must be nonnegative integers and positive for nonempty text. Count
additivity/monotonicity is not assumed. A byte-sizing test exercises the interface.

Structural-v1 detects paragraphs, Markdown headings with the next short content line,
list items, fenced code blocks, sentence punctuation followed by whitespace, and word
boundaries. Typed application-supplied hints can mark sections, paragraphs, list items,
code blocks, functions and classes. Hints are range-checked, deduplicated, sorted and
recorded. There is no language-specific AST parser or semantic segmentation.

Claims, hints, fitting code blocks, headings and list items are soft protected spans.
The algorithm prefers safe structural cuts above a 50% fill threshold, then safe
shorter cuts, then weaker boundaries. It moves a fitting protected span to a fresh
chunk when necessary. Oversized or mutually overlapping spans can require splitting;
the hard size ceiling wins and partial support links remain explicit. Long words or
unbroken text finally fall back to exact character cuts. No text is lost: spans cover
the input, including internal whitespace. Pure empty/whitespace inputs yield no spans;
Stage 3A ingestion already rejects such evidence.

Overlap is a maximum budget, not a required duplicated window. The next chunk can
start at an existing safe structural/word boundary within the budget. It never starts
inside a protected span. Actual overlap can be less than requested or zero; the next
chunk must extend beyond the previous end. All overlap is represented by real offsets,
not copied headings or synthetic context. Character boundaries can split grapheme
clusters under a hard fallback; byte-perfect canonical substring fidelity still holds.

## Claims, citations and trust

Containment describes the **support pointer span**, not truth or semantic entailment.
A fully contained pointer does not verify its claim, and a partial pointer never
pretends to contain all supporting text. Multiple supports, even for an identical claim
from distinct sources, remain separate. Contradictions, inferences and external
observation origin retain their original classifications. No support is promoted.

Citation resolution checks scoped evidence access, normalized blob hash and the exact
chunk substring before returning existing source provenance. It does not search for a
matching passage or infer a locator from semantic similarity. The six demonstrated
native locator forms are input/message, resume document/section/page, PDF/page,
GitHub/repository/commit/file/line, website URL snapshot/section and VeriBridge report/
section. Source changes are known only after ingestion; deletion is the existing
Stage 3A tombstone. Reversion can restore a historical evidence version as current;
the history-changed flag still exposes additional ledger events, including retries.

Exact offsets are in normalized text. Native locator context is inherited unchanged;
Stage 3A does not provide a byte-to-character or PDF geometry map. Thus a GitHub line
range or PDF page is the original capture's locator, not newly calculated subchunk
coordinates. Real adapters must supply trustworthy captures and richer span maps if
those are needed. Fixture round trips prove preservation, not authenticity of files,
websites, binaries, report issuers or Git commits.

JSON envelopes preserve malicious instruction-like strings as ordinary escaped data.
They contain fixed trust and scope fields plus the full chunk view. Chunking executes
no text, creates no claims, changes no verification and builds no prompts. JSON alone
is not an LLM prompt-injection defense; no LLM is invoked here.

## Instrumentation and limitations

The fixed synthetic corpus includes short and oversized claim spans, adjacent topics,
headings, bullets, code, repeated content, Unicode and malicious-looking strings, plus
all six locator forms. Both policies see the identical corpus. Metrics distinguish
unique-claim containment from support-occurrence containment, so one fully contained
source cannot conceal a split corroborating support. Split metrics report partial
links and claims/supports lacking any fully containing chunk. Duplication ratio is
`(sum(chunk characters) - source characters) / source characters`.

This is not a retrieval-quality evaluation. Only six unique explicitly annotated
claims across twelve support occurrences appear in the comparison; broader corpora
and token-aware budgets remain future experiments. The in-memory store has no durable
persistence, transactions, eviction, concurrency guarantees or deployed authentication.
The reference algorithm scans candidate boundaries and scoped claims; large-scale
indexing/performance optimization is outside this stage. Application code selects and
versions trusted sizers and hints; content cannot load executable plugins. Regex
boundaries are heuristics, not a full Markdown or source-code parser. Long whitespace
inside otherwise valid text can create whitespace-only chunks to preserve coverage.
