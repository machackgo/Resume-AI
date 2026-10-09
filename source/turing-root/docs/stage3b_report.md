# Stage 3B completion report

Stage 3B adds deterministic evidence-preserving chunking to the completed Stage 3A
ledger. Stage 3A required no repair or redesign. All additions are isolated; no
preexisting file is modified. No embeddings, vector storage, retrieval or model work
is introduced. See `stage3b_architecture.md` for the full contract and limitations.

## 1. Architecture implemented

A scoped `EvidenceRepository` protocol connects the existing CandidateLedger to
`CandidateChunks`. The service generates immutable RetrievalChunk views and resolves
citations against authoritative evidence. The core is independent of future storage
and embedding providers. A separate Sizer protocol allows later token-aware policies.

## 2. Files created and modified

Created:

- `rag/chunking/__init__.py`: public package entry points.
- `rag/chunking/policy.py`: policy fingerprints, sizing protocol, character sizer, A/B defaults.
- `rag/chunking/models.py`: typed hints, chunk/link/citation records and containment enum.
- `rag/chunking/chunker.py`: structural chunker, repository protocol, scoped store, citations and envelopes.
- `rag/chunking/metrics.py`: deterministic structural policy comparison.
- `rag/chunking/demo.py`: fixed synthetic corpus and provenance/trust/isolation demonstrations.
- `rag/chunking/validate.py`: reproducible remote CPU acceptance runner.
- `tests/rag/test_chunking.py`: 39 tests, including 100 seeded boundary-coverage cases.
- `docs/stage3b_architecture.md` and this report.
- `results/stage3b/preexisting_manifest.json`: pre-installation SHA-256 baseline.
- `results/stage3b/demo.json`, `policy_comparison.json`, `validation.json` and six execution logs.

Modified preexisting files: **none**. No dependency, model, environment or GPU allocation changes.

## 3. Chunk schema

Each chunk carries immutable evidence (including scope/source/version/trust/native
locator), chunk and annotation-revision IDs, policy, structural hints, input support
IDs, exact half-open normalized Unicode offsets and substring, measured size,
original support links with explicit intersections/containment, and source event history.
Citation objects add source identity, current evidence ID, current/superseded/deleted
status and a history-changed indicator. Composition retains every Stage 3A evidence
and support field instead of copying only a lossy subset.

## 4. Chunk-ID strategy

Canonical JSON + SHA-256 of the Stage 3B domain marker, tenant/candidate, evidence ID,
evidence version, full policy fingerprint, canonical structural hints and exact span.
Different positions of repeated text have different IDs. Different sources/scopes/
versions/policies remain distinct. No random UUID is used. Annotation/event revisions
have separate deterministic IDs and are retained alongside stable text chunk IDs.

## 5. Policy/versioning strategy

Policy records name, version, schema, max size, overlap, unit, sizer identity, boundary
revision and minimum fill. Every field participates in the fingerprint. Current sizing
is Unicode characters (`unicode-codepoints-v1`), with no Qwen or tokenizer dependency.
A future token policy must pin its tokenizer/assets/revision and provide exact count
and prefix selection. Stored support IDs and hints make historical boundaries reproducible.

## 6. Boundary strategy

Prefer claim/hint boundaries, paragraphs, Markdown headings with following content,
list items, fenced code, sentences and words. Avoid splitting fitting protected spans.
Oversize spans fall back to weaker boundaries and ultimately exact character cuts.
All nonempty canonical text is covered, including internal whitespace; empty/whitespace
input has zero chunks and remains rejected by Stage 3A ingestion.

## 7. Overlap strategy

Overlap is an upper bound. Reuse an existing safe boundary within the budget, preserving
an exact contiguous source slice. Do not fabricate repeated headings or context. Some
chunks have zero overlap. Forward progress and hard sizing hold even at extreme overlap.

## 8. Claim preservation

FULLY_CONTAINED means the original support pointer is entirely within the chunk.
PARTIALLY_OVERLAPPING means only a strict intersection is available. Neither indicates
factual verification. Original relation, claim kind, confidence, extractor, rationale,
native pointer and unreviewed state survive unchanged. Distinct sources and repeated
occurrences retain distinct supports even when Stage 3A shares the conceptual claim ID.
Reannotation preserves old views and records a new revision.

## 9. Citation round-trip demonstration

The demo records complete JSON chains for plain text, resume document, PDF, GitHub,
website and VeriBridge locators. For example the synthetic GitHub capture resolves:
chunk `[0,22)` / `Built a Python service.` -> its exact evidence/version -> source ->
`repository=example/synthetic`, `commit=abc123`, `file=app.py`, `line_start=line_end=5`.
PDF resolves the same canonical quote to `document_id=synthetic-pdf`, `page=3`.
Source locator attributes are preserved, not generated from text similarity.

Resolver checks scoped evidence access, normalized hash and exact substring. Updated
source evidence marks the old chunk superseded while retaining its citation. Tombstones
retain historical citations; reversion restores the original version as current.
These are synthetic native captures, not validation against real PDFs/repositories.
Raw offsets and PDF geometry cannot be reconstructed where Stage 3A supplied no map.

## 10. Tenant-isolation demonstration

Identical content is ingested for two candidates in one tenant and the same candidate
label in another tenant. Scoped chunk IDs differ; foreign `generate`, `get`, `cite`
and `untrusted_envelope` calls fail (eight explicit demo rejections). Tests also reject
foreign/wrong-evidence support recipes and foreign revision lookups. Scope comes from
trusted application authentication, as in Stage 3A; this is not a deployed auth service.

## 11. Prompt-injection/trust demonstration

The synthetic instruction to ignore previous instructions and claim AWS certification,
plus a forged JSON system role, remains plain untrusted text. No role escapes the data
envelope, no claim is automatically created, and no verification changes. Separate
tests with an explicitly annotated malicious assertion prove its support stays unreviewed.
Inferences, contradictions and external observations preserve their separate metadata.

## 12. Policy A versus Policy B

Same fixed corpus: 13 evidence objects, 4,896 source characters, six unique annotated
claims and twelve source-specific support occurrences. Both policies use structural-v1
and a 50% minimum fill preference. The corpus is fixed independently of measured results.

| Structural metric | A: 320 chars / 48 overlap | B: 640 chars / 96 overlap |
|---|---:|---:|
| Chunks | 28 | 20 |
| Average chunk size, characters | 190.43 | 262.65 |
| Characters represented including overlap | 5,332 | 5,253 |
| Overlap duplication / source characters | 8.91% | 7.29% |
| Unique claim containment | 83.33% | 100% |
| Support-occurrence containment | 91.67% | 100% |
| Claims with partial links | 1 | 0 |
| Claims without a fully containing chunk | 1 | 0 |
| Supports without a fully containing chunk | 1 | 0 |
| Successful citation round trips | 28/28 | 20/20 |
| Deterministic regeneration | Yes | Yes |

Containment rate means at least one chunk fully contains the annotated span. The
support-level rate prevents one fully contained corroborating source from concealing
a split span in another source. No embeddings or retrieval-quality measurements exist.

## 13. Tests executed and results

Remote acceptance command, from `~/scratch/resume-ai`:

```sh
.venv/bin/python -B -m rag.chunking.validate
```

Remote result: **85/85 tests passed** on Python 3.11.12: 39 Stage 3B, 27 Stage 3A,
and 19 existing tests. All six acceptance commands exited successfully.

The runner executes Stage 3B tests (39), Stage 3A tests (27), existing eval tests (19), frozen
Stage 2 replay, and both stage demos. It also compares full Stage 3B demo output across
two fresh Python processes with different hash seeds. See `results/stage3b/validation.json`
and the corresponding logs for authoritative execution results and artifact hashes.

The new tests cover all fourteen requested semantic-integrity cases plus policy and
hint validation, custom sizing, exact overlap intersections, clock-independent IDs,
reannotation recipes, deletion/reversion, corrupted content rejection, immutable views,
all native locator forms and 100 seeded boundary-covering inputs.

## 14. Regression verification

The acceptance runner checks all 256 files in the pre-Stage-3B baseline and separately
the original 238 Stage 1/2 protected files. It compares the Stage 3A demo structurally
against its frozen JSON and reruns the eight-case frozen Stage 2 output/metric replay.
Root-level GPU benchmark scripts are preserved, not executed as CPU unit tests.
No previous tests are weakened or benchmark outputs rewritten.

Verified results: **256/256 pre-Stage-3B files byte-identical**, including all **238/238
Stage 1/2 protected files**; Stage 3A demo equal; all eight Stage 2 replay cases and
strict metrics reproduced. Both independent Stage 3B demo processes produced SHA-256
`fbc4bfacb7bd13e548d50388fc625b17fff40a74fc359205b77fa783da1b02a2`.

## 15. Limitations

Character sizing is not a token limit. Regex structures are heuristic, not full Markdown
or AST parsing. Oversize/overlapping structures may split; code-point fallback may split
a grapheme cluster. Internal whitespace may form a whitespace-only chunk under a hard
limit. Claim-span containment is not entailment or verification. Corpus breadth and
annotations are deliberately limited and synthetic. Native citation precision cannot
exceed Stage 3A's captured locator; no raw/PDF geometry map is invented. Source freshness
requires ingestion. The store is ephemeral, single-process, and not optimized for scale;
no durable/authenticated service, vector index or LLM injection evaluation is claimed.

## 16. Recommended default for Stage 3C experiments

Use Policy B provisionally: maximum 640 Unicode characters, overlap budget 96,
structural-v1, 50% fill preference. It yields fewer chunks, less measured duplication
and full containment of all annotated support occurrences on this corpus. This is a
structural baseline, not evidence of optimal retrieval quality. Retain A as a comparison
and measure actual tokenizer lengths before any future model-bound ingestion.

## 17. Exact proposed Stage 3C boundary — not begun

A separately authorized Stage 3C could evaluate embedding-model/tokenizer compatibility
and generate reproducible embedding artifacts for frozen Stage 3B chunk generations.
Pin model/tokenizer revisions, measure token budgets, preserve scoped chunk/revision
references, and test deterministic input manifests and embedding provenance. Select the
model and compute resources only within that later authorization. Proposed exclusions:
vector database integration, semantic/hybrid retrieval, reranking, Qwen RAG prompts,
training/QLoRA, and job/browser automation. Stage 3B stops before any of this work.
