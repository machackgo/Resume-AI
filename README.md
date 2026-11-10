# Resume AI

Resume AI is a personal project that prepares job applications from a candidate's own evidence and refuses to
write anything it cannot trace back to that evidence. It combines:

- **scoped, citation-preserving retrieval** over the candidate's documents (hybrid BM25 + embedding search with
  reciprocal rank fusion, exact character offsets, component-aware retrieval for compound requirements);
- **explainable job matching** weighted by how well each skill is evidenced (verified vs. ongoing vs. planned);
- **grounded generation**: a language model proposes a tailored resume spec that may only reference evidence ids,
  and deterministic validators reject invented numbers, banned claims and mislabelled ongoing work;
- **an application tracker** with append-only history. SQLite triggers refuse to mark an application
  `submitted` (in the `applications` table or as a job's status) unless a candidate approval row exists, and
  `Tracker.set()` raises `CandidateOnlyStatus` for any of the statuses only the candidate may record (`approved`,
  `submitted`, `interviewing`, `offer`, `rejected`, `withdrawn`); the `submitted` rule also holds under
  `python -O` (tested). The code never submits an
  application; it only records what the candidate did.

Everything in this repository runs on a CPU in seconds on synthetic data. No GPU, model download or API key is
needed for the tests or the demo.

> This branch adds a curated package (`resume_ai/`) on top of a preservation snapshot of the original research
> code. The snapshot is kept unchanged under [`source/`](source/) and described in [ARCHIVE.md](ARCHIVE.md).
> Where each file came from is listed in [PROVENANCE.md](PROVENANCE.md).

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the diagram and component details.

| Package | What it does | Main files |
|---|---|---|
| `resume_ai/rag/` | Scoped ingestion ledger, structural chunking with exact offsets, embedding records with configuration identity, SQLite exact-cosine reference vector store, semantic / BM25 / hybrid retrieval, requirement decomposition and component retrieval, model-facing citation contract | `ingestion.py`, `chunking/chunker.py`, `vectorstore/sqlite_reference.py`, `retrieval/service.py`, `component/retrieve.py`, `reasoning/contract.py` |
| `resume_ai/matching/` | Alias normalisation, status-weighted skill score with explanation, profile-declared gaps, experience check, role family, priority, URL/fingerprint de-duplication | `engine.py` |
| `resume_ai/grounding/` | Evidence bank with a status per item, claim validator, DOCX resume / cover-letter builder, semantic relationship contracts | `profile.py`, `validate.py`, `documents.py` |
| `resume_ai/agents/` | LLM spec generation with validator feedback and retry; tool-restricted Claude Code CLI adapter | `spec_agent.py` |
| `resume_ai/tracking/` | SQLite tracker (9 migrations, append-only triggers, submission guards, crash recovery) and worker control state | `tracker.py`, `control.py` |

## Tech stack

Python 3.10+ (standard library for all retrieval, matching, validation and tracking code), SQLite,
`python-docx` for documents, `pytest`. Optional: PyTorch + Hugging Face Transformers for the pinned
`sentence-transformers/all-MiniLM-L6-v2` embedding provider (`rag/embeddings/local.py`); that provider is
not exercised by CI or the demo. In the original
work, generation used an open-weight Qwen model on a university GPU cluster (v11 pipeline, archive) and later
the Claude Code CLI in the private application tracker.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt           # or: pip install .   (installs the resume_ai package)
python -m pytest -q                       # 301 tests (+38 subtests), about 1-2 s on a laptop CPU
python examples/run_demo.py               # writes demo_output/ (git-ignored)
```

## Example workflow (excerpt of the real output of `python examples/run_demo.py`)

All inputs are synthetic: a fictional candidate (Alex Rivera), fictional employers and fictional postings in
[`examples/`](examples/). The demo uses `HashingEmbeddingProvider`, a deterministic feature-hashing stand-in
defined in `examples/run_demo.py`; it is **not** a semantic model and was written only so the demo needs no
download. The language model is a mock that replays two canned replies. The output is deterministic (identical
across runs and `PYTHONHASHSEED` values).

**1. Matching and de-duplication**

```text
  duplicate skipped -> FT001: Globex Data Systems | Applied AI Engineer, New Grad (https://www.jobs.example.com/globex/applied-ai-engineer/?gh_jid=1001&utm_source=board)

  FT001  match  95/100  priority  95  family 3  Globex Data Systems | Applied AI Engineer, New Grad
     verified skills : python, rag, embeddings, evals, fastapi, postgresql, retrieval
     in progress     : llm
     planned only    : -
     gaps            : -
     experience      : Early-career / new-grad level.

  FT003  match  57/100  priority  57  family 3  Acme Applied AI | LLM Agents Engineer (Early Career)
     verified skills : python, evals
     in progress     : llm agents, tool calling, pytorch, llm, agents
     planned only    : reinforcement learning
     gaps            : -
     experience      : Early-career / new-grad level.

  FT002  match   0/100  priority   0  family 5  Initech Health | Machine Learning Platform Engineer
     verified skills : python
     gaps            : kubernetes (required), c++ (required), distributed training (required), spark, publications/PhD (preferred only)
     experience      : Asks for 3+ years.
```

**2. Retrieval with citations** (excerpt)

```text
  ingested 5 evidence files -> 9 chunks (policy 'small', max 320 chars, exact Unicode offsets)

  requirement: Built and deployed REST APIs with FastAPI and PostgreSQL
    #1 rrf=0.0328 sem_rank=1 bm25_rank=1  internship_summary[0:294]  trust=untrusted_data
       # Fictional Freight Co. — internship summary (synthetic) ## Ticket classification service I built a FastAPI service that routes inbound support ticket
    #2 rrf=0.0318 sem_rank=4 bm25_rank=2  lab_retrieval_notes[0:191]  trust=untrusted_data

  component-aware retrieval for the compound requirement: 'Built and deployed REST APIs with FastAPI and PostgreSQL'
    component 'Built REST APIs with FastAPI and PostgreSQL.': selected_candidates (1 evidence group(s))
    component 'deployed REST APIs with FastAPI and PostgreSQL.': no_plausible_candidate_retrieved (0 evidence group(s))
    notice: Retrieval membership does not prove support. No plausible candidate means retrieval absence, not contradiction or proof of corpus absence.
```

**3. Model proposes, validator decides**

```text
  attempt 1: INVALID
     - evidence P1 is PLANNED — not usable
     - in-progress skill 'fine-tuning' must sit under a label marked ongoing (label: Machine learning)
     - in-progress skill 'lora' must sit under a label marked ongoing (label: Machine learning)
     - banned claim: 'Kubernetes'
     - banned claim: '5,000 users'
     - unverified number: 37
     - unverified number: 5,000
  attempt 2: OK
  attempt 2 prompt carried the validator feedback: True
  resume        issues after rendering: 0  -> demo_output/packages/FT001/Alex_Rivera_Globex_AppliedAIEngineer_Resume.docx
  cover_letter  issues after rendering: 0  -> demo_output/packages/FT001/Alex_Rivera_Globex_AppliedAIEngineer_CoverLetter.docx
  resume bullets come from evidence ids only: ['L1', 'L2', 'L3', 'I1', 'I2', 'O1', 'T1']
```

**4. Approval gates**

```text
  agent tries to set status 'submitted'      -> refused: 'submitted' can only be recorded from a candidate action
  raw SQL status update to 'submitted'        -> refused by trigger: status submitted requires a candidate approval record
  submission record without approval          -> refused by trigger: submission requires a candidate approval record
  submission record with an AGENT approval     -> refused by trigger: submission requires a candidate approval record
  deleting approval history                    -> refused: approvals is append-only
```

## Measured results from the original work

All numbers below come from the archived reports; none were produced by this showcase except where noted.
They are small, synthetic, internal benchmarks, not production metrics.

| Result | Value | Source |
|---|---|---|
| Component-aware retrieval (Stage 3I): material requirement components surviving into the final context, at the MEDIUM, LARGE and XL corpus scales | 10/12 (83.33%) with the previous global retrieval → 11/12 (91.67%) | `source/turing-root/docs/stage3i_report.md` §6. Retrieval coverage only; downstream label accuracy unchanged (68.75% in all arms at MEDIUM, §8), and at LARGE/XL the component arm scored 62.50% vs 68.75% for the 3-group baseline (§8). Decision "B — do not freeze RAG yet"; one requirement (h06) is still lost. |
| Requirement decomposer on its frozen 34-case synthetic benchmark | precision 93.02%, recall 86.96%, invented components 0% | `source/turing-root/docs/stage3i_report.md` §4; reproduced by `tests/rag/test_component.py::DecompositionTests::test_frozen_benchmark` and `resume_ai.rag.component.benchmark.evaluate` in this repo |
| v11 end-to-end acceptance (20 original + 10 stress cases, base model, no fine-tuning) | 23/30 passed; decision **NOT READY / NO-GO** | `source/v11-sealed/FINAL_REPORT.txt` |

## Known limitations

- **The end-to-end pipeline did not pass its own acceptance gate.** The v11 pipeline (archive) passed 23 of 30
  cases; the remaining failures are in claim licensing, project-identity reconciliation and positive-evidence
  recovery (one case produced an empty resume). See `source/v11-sealed/FINAL_REPORT.txt`.
- Component retrieval improved coverage on a 12-component synthetic benchmark but did not fix every loss;
  the benchmark is small and authored by the developer.
- The vector store is an exact-scan SQLite **reference implementation**. PostgreSQL + pgvector was the intended
  production direction and was not built.
- Matching is lexical (alias table + regular expressions). Gaps are only reported for terms that map to a
  skill the profile does not list or that the profile declares as gaps; other unknown terms are counted as
  "unassessed", not as gaps.
- The claim validator checks numbers by substring and claims by pattern; it is a guard rail, not an entailment
  check.
- The demo's embeddings are feature hashing, not semantic embeddings, so its rankings illustrate the mechanics only.
- Private browser-assist and discovery components, the dashboard and the process supervisor are not included.
  See PROVENANCE.md.

## Development status

- **Completed:** scoped ingestion, chunking, embedding, vector-store, retrieval and component-retrieval stages
  with tests; v11 pipeline evaluation (NO-GO); a private application tracker with approval gates used by the
  author; this curated showcase.
- **Ongoing:** the private application tracker. Repairing the v11 failure classes (claim licensing and
  identity reconciliation) is the documented next step in `FINAL_REPORT.txt`; it is not part of this repository.
- **Future:** a production vector store (pgvector), semantic entailment checks in the validator, and a
  larger independently labelled evaluation set.

## License

No license has been chosen yet. Third-party models referenced by the code are not included in this
repository: `sentence-transformers/all-MiniLM-L6-v2` (Apache-2.0), `intfloat/e5-small-v2` (MIT),
`cross-encoder/ms-marco-MiniLM-L6-v2` and `cross-encoder/ms-marco-TinyBERT-L2-v2` (Apache-2.0) were evaluated
in the archived RAG stages, and the archived v11 pipeline used `Qwen/Qwen3.8-27B` (Apache-2.0; licence text in
`provenance/upstream-licenses/`). Licences as recorded in `provenance/rag-models.stage3*.lock.json` and
`provenance/base-model.lock.json`.
