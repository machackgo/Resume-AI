"""End-to-end CPU demo on SYNTHETIC data (no GPU, no network, no model download, no LLM call).

    python examples/run_demo.py [--out demo_output]

1. Matching    score three fictional postings against a fictional candidate, with reasons; de-duplicate a repost.
2. Retrieval   ingest the candidate's evidence notes into the scoped ledger, chunk them with exact offsets, embed
               them, store them in the SQLite reference vector store, and run hybrid (BM25 + vector, RRF) and
               component-aware retrieval for each requirement of the best-matching posting.
3. Grounding   a mock LLM proposes a tailored resume spec; the validator rejects the first attempt and the
               retry with feedback passes; the DOCX resume and cover letter are rendered and re-validated.
4. Tracking    the package is recorded in the SQLite tracker; the agent cannot mark it submitted, and the
               database refuses a submission record without a candidate approval.

Embeddings: the demo uses HashingEmbeddingProvider below, a deterministic stdlib feature-hashing stand-in written
for this showcase. It is NOT a semantic model. The original project used a pinned MiniLM sentence-transformer
through resume_ai.rag.embeddings.local.LocalTransformerProvider (requires torch + transformers and a local model).
"""
import argparse
import hashlib
import json
import math
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from resume_ai.agents.spec_agent import generate_spec                      # noqa: E402
from resume_ai.grounding.documents import build_package, job_text           # noqa: E402
from resume_ai.grounding.profile import Profile                             # noqa: E402
from resume_ai.matching import engine                                       # noqa: E402
from resume_ai.rag.adapters import LocalTextAdapter                         # noqa: E402
from resume_ai.rag.chunking.chunker import CandidateChunks                  # noqa: E402
from resume_ai.rag.chunking.policy import POLICY_A                          # noqa: E402
from resume_ai.rag.component.retrieve import ComponentRetriever             # noqa: E402
from resume_ai.rag.domain import Scope                                      # noqa: E402
from resume_ai.rag.embeddings.cache import ChunkEmbedder                    # noqa: E402
from resume_ai.rag.embeddings.models import EmbeddingConfig                 # noqa: E402
from resume_ai.rag.ingestion import MemoryLedger                            # noqa: E402
from resume_ai.rag.reranking.base import CitationTextResolver               # noqa: E402
from resume_ai.rag.retrieval import CandidateEvidenceRetriever, InformationNeed, NeedType, RetrievalConfig  # noqa: E402
from resume_ai.rag.retrieval.lexical import tokens                          # noqa: E402
from resume_ai.rag.vectorstore.config import StoreConfig                    # noqa: E402
from resume_ai.rag.vectorstore.models import ChunkReference, EmbeddingSpace  # noqa: E402
from resume_ai.rag.vectorstore.sqlite_reference import SQLiteVectorStore   # noqa: E402
from resume_ai.tracking.tracker import CandidateOnlyStatus, Tracker         # noqa: E402

DIM = 256


class HashingEmbeddingProvider:
    """Demo-only, deterministic: signed feature hashing of BM25 terms (L2-normalised). Not a semantic model."""
    config = EmbeddingConfig("hashing-demo-v1", "feature-hashing", "v1", DIM, True)

    def _vec(self, text):
        v = [0.0] * DIM
        for t in tokens(text):
            h = hashlib.sha256(t.encode()).digest()
            v[int.from_bytes(h[:4], "big") % DIM] += 1.0 if h[4] & 1 else -1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        if not any(v):
            v[0], n = 1.0, 1.0
        return tuple(x / n for x in v)

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_queries(self, texts):
        return [self._vec(t) for t in texts]


class MockLLM:
    """Returns canned replies in order; stands in for agents.spec_agent.ClaudeCLI."""
    def __init__(self, replies):
        self.replies, self.prompts = list(replies), []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        return {"kind": "ok", "json": self.replies.pop(0)}


def section(title):
    print("\n" + "=" * 78 + "\n" + title + "\n" + "=" * 78)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="demo_output")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    profile = Profile.load(HERE / "profile_alex_rivera.json")
    postings = json.loads((HERE / "jobs" / "postings.json").read_text())

    # ------------------------------------------------------------------ 1. matching + tracker ingest
    section("1. Explainable matching and de-duplication (engine %s)" % engine.ENGINE_VERSION)
    t = Tracker(str(out / "tracker.db"), profile=profile, run_id="demo-run")
    t.start_run("demo-run", "showcase-demo", trigger="examples/run_demo.py", model="mock")
    ids = []
    for p in postings:
        jid, created = t.ingest(p, source="synthetic postings")
        if not created:
            print(f"  duplicate skipped -> {jid}: {p['company']} | {p['title']} ({p['posting_url']})")
            continue
        ids.append(jid)
    for r in t.query():
        ex = json.loads(r["explanation_json"])
        print(f"\n  {r['job_id']}  match {r['match_score']:>3}/100  priority {r['priority']:>3}  family {r['family']}"
              f"  {r['company']} | {r['title']}")
        print(f"     verified skills : {', '.join(ex['verified']) or '-'}")
        print(f"     in progress     : {', '.join(ex['in_progress']) or '-'}")
        print(f"     planned only    : {', '.join(ex['planned']) or '-'}")
        print(f"     gaps            : {', '.join(ex['gaps']) or '-'}")
        print(f"     experience      : {ex['experience']['reason']}")
    best = t.query()[0]
    job = t.export_job(best["job_id"])

    # ------------------------------------------------------------------ 2. retrieval
    section("2. Scoped evidence retrieval for %s (%s)" % (best["job_id"], best["company"]))
    scope = Scope("demo-tenant", "alex-rivera")
    # Fixed ingestion clock: chunk revision and embedding ids are content hashes that include provenance-event
    # timestamps, so a fixed clock makes ids (and therefore the store's cosine tie-break) identical on every run.
    ledger = MemoryLedger(clock=lambda: "2026-01-01T00:00:00+00:00").for_candidate(scope)
    chunks_service = CandidateChunks(ledger)
    provider = HashingEmbeddingProvider()
    space = EmbeddingSpace(provider.config, "title-section-v1")
    tmp = tempfile.TemporaryDirectory()
    store = SQLiteVectorStore(StoreConfig(Path(tmp.name)), scope)
    embedder = ChunkEmbedder(scope, provider)
    records = []
    for f in sorted((HERE / "evidence").glob("*.md")):
        item = ledger.ingest(LocalTextAdapter(HERE / "evidence", f.name, f.stem))
        chunks = chunks_service.generate(item.evidence.evidence_id, POLICY_A)
        recs = embedder.embed(chunks, "title-section-v1")
        store.register_chunks([ChunkReference.from_citation(chunks_service.cite(c.chunk_id, c.revision_id)) for c in chunks])
        store.upsert_embeddings(recs)
        store.activate_source_version(item.evidence.source_id, item.evidence.evidence_id, expected_current=None)
        records.extend(recs)
    print(f"  ingested {len(list((HERE / 'evidence').glob('*.md')))} evidence files -> {len(records)} chunks"
          f" (policy '{POLICY_A.name}', max {POLICY_A.max_size} chars, exact Unicode offsets)")
    retriever = CandidateEvidenceRetriever(store, provider, space, chunks_service, [r.record_id for r in records],
                                           RetrievalConfig(strategy="hybrid"))
    for i, req in enumerate(job["required"], 1):
        need = InformationNeed(NeedType.JOB_REQUIREMENT, req, f"{best['job_id']}-r{i}")
        resp = retriever.retrieve(scope.tenant_id, scope.candidate_id, need, top_k=2)
        print(f"\n  requirement: {req}")
        for res in resp.results:
            ref = res.reference
            text = chunks_service.cite(ref.chunk_id, ref.chunk_revision_id).chunk.text
            src = json.loads(ref.locator.attributes_json).get("document_id", ref.source_id[:12])
            print(f"    #{res.rank} rrf={res.score:.4f} sem_rank={res.semantic_rank} bm25_rank={res.lexical_rank}"
                  f"  {src}[{ref.start}:{ref.end}]  trust={ref.trust}")
            print("       " + " ".join(text.split())[:150])
    # Component retrieval runs on semantic scores (its 0.20 floor is a cosine threshold, not an RRF score).
    semantic = CandidateEvidenceRetriever(store, provider, space, chunks_service, [r.record_id for r in records],
                                          RetrievalConfig(strategy="semantic"))
    comp = ComponentRetriever(semantic, CitationTextResolver(store, chunks_service))
    compound = job["required"][-1]
    r = comp.retrieve(scope.tenant_id, scope.candidate_id,
                      InformationNeed(NeedType.JOB_REQUIREMENT, compound, f"{best['job_id']}-compound"))
    print(f"\n  component-aware retrieval for the compound requirement: {compound!r}")
    for c in r["context"]["component_retrieval"]:
        print(f"    component {c['text']!r}: {c['status']} ({len(c['evidence_ids'])} evidence group(s))")
    print("    notice: " + r["context"]["component_notice"])
    store.close(); tmp.cleanup()

    # ------------------------------------------------------------------ 3. grounded generation
    section("3. LLM spec -> validator -> retry with feedback -> rendered documents")
    replies = json.loads((HERE / "specs" / "globex_mock_llm_replies.json").read_text())["attempts"]
    llm = MockLLM(replies)
    jt = job_text(job)
    result = generate_spec(job, jt, profile, llm, max_attempts=2)
    for at in result["attempts"]:
        print(f"  attempt {at['attempt']}: {at['kind'].upper()}")
        for issue in at["issues"]:
            print(f"     - {issue}")
    print(f"  attempt 2 prompt carried the validator feedback: {'REJECTED BY THE VALIDATOR' in llm.prompts[-1]}")
    if not result["ok"]:
        print("  no valid spec; nothing rendered")
        return 1
    res, manifest = build_package(job, result["spec"], profile, str(out / "packages"))
    for kind, v in res.items():
        print(f"  {kind:<13} issues after rendering: {len(v['issues'])}  -> {v.get('docx') or v.get('path')}")
    print(f"  resume bullets come from evidence ids only: {manifest['evidence_ids']}")
    bad = [k for k, v in res.items() if v["issues"]]

    # ------------------------------------------------------------------ 4. approval gates
    section("4. Tracker approval gates (the code never submits)")
    jid = best["job_id"]
    t.add_document(jid, "resume", res["resume"]["docx"], res["resume"]["text"], {"issues": res["resume"]["issues"]}, manifest["generator_version"])
    t.set(jid, application_status="awaiting approval")
    try:
        t.set(jid, application_status="submitted")
    except CandidateOnlyStatus as e:
        print(f"  agent tries to set status 'submitted'      -> refused: {e}")
    try:
        t.db.execute("UPDATE jobs SET application_status='submitted' WHERE job_id=?", (jid,))
    except sqlite3.IntegrityError as e:
        print(f"  raw SQL status update to 'submitted'        -> refused by trigger: {e}")
    try:
        t.mark_submitted(jid, "demo")
    except sqlite3.IntegrityError as e:
        print(f"  submission record without approval          -> refused by trigger: {e}")
    t.record_approval(jid, "submit", "approved", "agent", "demo")
    try:
        t.mark_submitted(jid, "demo")
    except sqlite3.IntegrityError as e:
        print(f"  submission record with an AGENT approval     -> refused by trigger: {e}")
    try:
        t.db.execute("DELETE FROM approvals")
    except sqlite3.IntegrityError as e:
        print(f"  deleting approval history                    -> refused: {e}")
    print(f"  status now: {t.query('job_id=?', (jid,))[0]['application_status']!r}; "
          f"activity events logged: {len(t.activity())}")
    t.finish_run()
    print(f"\nOutputs written under {out}/ (synthetic data only).")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
