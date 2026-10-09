# Stage 3A: evidence model and ingestion architecture

Status: implementation restricted to evidence ingestion. Standard library Python 3.11+;
no new dependencies, model calls, chunking, networking, embeddings, vector database,
retrieval, reranking, training or browser/application automation.

## Starting point and architectural decision

Inspection found a script-based Qwen experiment, not an application backend. Stage 2
freezes `grounded_v3` and retains a standalone evaluation harness. Its eight-case
closed vocabulary and citation labels are experimental controls, not a general
candidate evidence schema. Stage 3A adds a separate `rag` package and does not map
new objects into that benchmark or change its prompts, vocabulary, labels or scorer.
The new package uses open source-type strings and open concept annotations.

Proposed and implemented flow:

    application-selected SourceAdapter
      -> bounded CanonicalDocument (raw + normalized content + acquisition provenance)
      -> ClaimExtractor protocol (no claims by default; explicit fixture annotations in demo)
      -> span and identity validation
      -> atomic commit in tenant/candidate-scoped reference ledger
      -> immutable Evidence + Claims + Support links + append-only ingestion history

`rag/domain.py` owns immutable, provider-independent types. `rag/adapters.py` owns
normalization and offline adapters. `rag/ingestion.py` owns the reference in-memory
ledger and extraction contract. `rag/demo.py` is the runnable synthetic example.
A flat package is intentional: these concerns need four modules, not a framework.

## Normalized entities

| Entity | Responsibility |
|---|---|
| Scope | Required tenant ID and candidate ID; both participate in all identities and partitions |
| Source | Logical source identity: scoped type + caller's stable source key, with immutable optional URI |
| Evidence | Immutable source snapshot: version, title, raw/normalized blob references and SHA-256 hashes, first ingestion time, source time, acquisition origin, supplied-by actor category, adapter/normalizer revisions, metadata, native locator, fixed untrusted-data marker |
| IngestionEvent | Each ingestion attempt that commits, including duplicates; time, previous/current evidence IDs and support IDs. Also explicit source tombstone events |
| Claim | Atomic proposed statement, optional subject/action/object, open concepts; no verification or confidence shortcut |
| Support | Claim occurrence/relationship linked to an exact evidence span, claim kind, extraction confidence, extractor revision and rationale; always unreviewed at ingestion |
| VerificationRecord | Future assessment of an exact support ID with issuer, attestation reference, policy revision, time and rationale. Model only: no accepted/persisted assessments in Stage 3A |

Candidate assertion, observable collection origin, inference, support relationship,
and verification are separate axes. A collected repository file can be observable
while its author's text remains an assertion. A future trusted adapter declares
collection origin; the extractor classifies each proposed claim. `supplied_by` can
record candidate involvement independently of observation origin. The three built-in
adapters never claim external observation. The synthetic collector test demonstrates
the contract but is not a production collector.

`asserts`, `supports`, `contradicts`, and `context` describe the extractor's proposed
relationship, not an adjudicated entailment label. Even `supports` stays unreviewed.
Extraction confidence measures extractor uncertainty only. Confidence 0.97 cannot
create verification. Uploaded metadata such as `verified: true` remains untrusted
metadata; it is never read as authority. A VeriBridge report title/URL is not proof
of an authenticated VeriBridge assessment. Future authenticated verification requires
an explicit trust policy, issuer authentication, revocation/expiry and auditable
assessment records; none is silently simulated here.

The extractor interface accepts atomic claims but does not prove atomicity or
entailment. An incorrect claim paired with an exact quote can pass structural
validation. This is a stated boundary, tested explicitly, not factual verification.
No fixed list of skills, proof types or profession-specific rules exists.

## Adapter and extractor contracts

Adapters are application code selected outside evidence. Content cannot register
adapters, name executable plugins or execute instructions. Each adapter returns:

- Stable logical source key and source type; URI/title for traceability.
- Raw bytes and normalized Unicode text, bounded to 1 MB each in this prototype.
- Truthful acquisition origin, supplied-by category, adapter and normalization revisions.
- Source timestamp when supplied, immutable metadata JSON and native locator.

Built-ins: candidate plain text keyed by input ID; staged local UTF-8 `.txt`/`.md`
keyed by document ID; normalized offline URL/document fixtures keyed by capture's
logical source. The local adapter requires an application-owned root, resolves paths
and symlinks, rejects escapes, and performs bounded reads. This is not a hostile
multi-process upload sandbox; production needs secure upload storage and race-safe
file handling. The fixture adapter permits credential-free HTTP(S) labels and does
not fetch URLs. PDF, GitHub and VeriBridge examples are normalized captures, not
parsers, real repositories, or authenticated reports. No website was accessed.

Raw bytes are preserved exactly. Built-in text normalization only converts CRLF/CR
to LF with strict UTF-8 decoding. Normalizer identity is versioned. A new parser can
produce different normalized text without modifying the domain. Rejected/empty,
oversized, invalid-UTF-8 or NUL text is not committed.

`ClaimExtractor.extract(document)` returns `ClaimDraft` values. Defaults produce no
claims rather than treating arbitrary documents as facts. The fixture extractor uses
explicit annotations from application test code, not instructions or annotations
embedded in uploads. All drafts validate before any state mutation. Failures leave
no partial sources, blobs, claims, supports, or ingestion events. A persistent
implementation must replace this single-process commit with a real transaction.

## Pointers and provenance

Every Support has one typed Pointer; a Claim may have many Support links, including
multiple sources, contradictory sources, and multiple spans within a source.
Pointers always contain an immutable evidence ID, exact quote, and half-open
`[start, end)` Unicode code-point offsets in normalized text. Validation checks the
quote equals the indicated substring. Offsets are neither bytes nor token offsets.
Raw-to-normalized offsets can differ; raw hashes preserve the original, and the
normalizer revision explains transformation. No arbitrary native coordinate is
claimed to have been checked against a real PDF or Git repository in this stage.

Locators use a namespaced kind and immutable JSON attributes. Known kinds validate
required fields: input ID; document ID/section; website URL/section; repository,
commit, file and line range; PDF document/page; VeriBridge report/section. Namespaced
future kinds can pass through without core changes, retaining the checked canonical
span. New adapters validate their own native locator schema; unknown schemas are
not silently represented as authenticated provenance. Evidence-level locators give
capture context; claim-level locators can add more precise sections/coordinates.

To audit a claim: load scoped Claim -> Support(s) -> Pointer -> Evidence -> Source;
read scoped normalized blob and verify substring; inspect raw/normalized hashes,
adapter revision, origin, source time and ingestion events (including support IDs).
Event time records later extractions even when an existing snapshot is reused.

## Identity, deduplication and lifecycle

SHA-256 IDs derive from canonical JSON with schema version 1 and entity kind.
Source IDs include scope, type and stable source key. URI changes under an existing
key are rejected; use a new source key for a moved/reidentified source. For URLs the
caller should consistently choose an exact canonical URL as key or maintain an
explicit source mapping; this layer does not guess equivalence of URL spellings.

Evidence IDs include source ID, raw/normalized hashes, adapter/normalization revisions
and provenance envelope (origin, supplied-by, title, timestamp, metadata, locator).
Exact repeated ingestion reuses Evidence and blob IDs but appends an event. Changed
bytes at the same source create a new version and retain old content. Provenance
changes also create a version even if bytes are unchanged. Reversion to previously
seen content/provenance reuses the original version and records a new current-head
event; the largest version number is not necessarily the current head.

Blob IDs include scope and content hash, permitting reuse within a candidate but
never exposing a global blob API. Identical files with different logical upload IDs
share scoped blobs but retain separate Source/Evidence provenance. Caller-provided
stable document IDs allow exact retry detection of an upload.

Claim identity includes scope, whitespace-normalized text, sorted unique concepts,
and optional subject/action/object. Identical structured claims across CV, portfolio,
and synthetic report share an ID but retain three distinct supports. Similar wording
or changed structured annotations remain distinct; semantic/entity resolution is
future work, not heuristic merging. Support identity includes exact pointer,
relationship, claim kind, extractor revision, confidence and rationale, so re-extraction
retains earlier interpretations. Original quote whitespace remains unchanged.

Deletion is an explicit tombstone: current() returns None while historical snapshots,
claims and citations remain accessible through scoped audit methods. Reingestion
restores the current head. Source deletion on the internet is not detected automatically.
Source changes can only be known after another ingestion; hashes do not monitor URLs.
Privacy erasure/retention is a separate future policy and cannot be confused with this
provenance-preserving tombstone. No destructive historical update API exists.

## Isolation and trust boundary

All public ledger reads/writes occur through `for_candidate(Scope(tenant,candidate))`.
There is no global evidence list or cross-scope lookup API. Foreign source, evidence,
claim, support and blob IDs fail with KeyError even when underlying content matches.
Future indexes must carry BOTH IDs, filter before candidate material is exposed,
and recheck every returned reference through the authorized ledger scope. IDs are
not authentication tokens, and hashes are not access controls. The caller must bind
scope from authenticated server context, never trust a request's candidate ID alone.
This is an in-process reference API, not a deployed authentication boundary; malicious
code in the same Python process can access internals. Production storage needs
transactionality, durable persistence, concurrency controls and row/object authorization.

Everything uploaded, normalized, extracted or later retrieved is untrusted DATA.
`untrusted_envelope()` returns JSON with fixed structural fields and escaped content;
it does not assemble prompts or grant actions. A malicious role/closing-tag string
cannot become a structural system field through serialization. A later RAG consumer
must retain system instructions separately, identify citations and untrusted data,
never interpolate evidence into system instructions, and never let evidence control
tools, verification or authorization. JSON alone does not make an LLM injection-proof.
Stage 3A executes no model, tools from content, shell commands from content, or URLs.

## Proposed Stage 3B boundary — requires a new instruction

Evidence-preserving chunking only: define immutable chunk records referencing an
Evidence version, candidate/tenant scope, normalization revision and exact span;
implement deterministic chunking plus pointer round-trip tests, synthetic boundary
cases, deduplication and isolation checks. Do not extract new verified claims or alter
source snapshots. Keep embeddings, vector storage, retrieval, reranking, prompt/model
integration, QLoRA/training and browser/application automation outside that boundary.
No Stage 3B implementation has been started.
