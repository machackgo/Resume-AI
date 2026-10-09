from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import tempfile
import unittest

from rag.adapters import (CanonicalDocument, LocalTextAdapter, NormalizedFixtureAdapter,
                          PlainTextAdapter, normalize)
from rag.demo import MALICIOUS, demonstrate
from rag.domain import (ClaimDraft, ClaimKind, Locator, Origin, Relation, Scope,
                        VerificationRecord, VerificationState, canonical)
from rag.ingestion import AnnotatedFixtureExtractor, MemoryLedger


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryLedger(clock=lambda: "2026-09-26T12:00:00+00:00")
        self.a = self.store.for_candidate(Scope("t1", "a"))
        self.adapter = PlainTextAdapter("message", "Built a Python service.")
        self.draft = ClaimDraft(self.adapter.text, 0, len(self.adapter.text), self.adapter.text,
                                concepts=("Python",), confidence=0.97)
        self.extractor = AnnotatedFixtureExtractor((self.draft,))

    def ingest(self):
        return self.a.ingest(self.adapter, self.extractor)

    def test_demonstration(self):
        result = demonstrate()
        self.assertEqual(len(result["ingestions"]), 6)
        self.assertEqual(result["shared_claim_support_count"], 3)
        self.assertTrue(result["cross_candidate_read_rejected"])
        self.assertEqual(result["verification_promotions"], 0)

    def test_duplicate_and_ingestion_event(self):
        one, two = self.ingest(), self.ingest()
        self.assertEqual(one.evidence, two.evidence)
        self.assertFalse(one.event.duplicate)
        self.assertTrue(two.event.duplicate)
        self.assertNotEqual(one.event.event_id, two.event.event_id)
        self.assertEqual(len(self.a.versions(one.evidence.source_id)), 1)
        self.assertEqual(len(self.a.history(one.evidence.source_id)), 2)
        self.assertEqual(len(self.a.supports(one.claims[0].claim_id)), 1)

    def test_ids_independent_of_clock(self):
        other = MemoryLedger(clock=lambda: "2027-01-01T00:00:00+00:00").for_candidate(self.a.scope)
        one, two = self.ingest(), other.ingest(self.adapter, self.extractor)
        self.assertEqual(one.evidence.evidence_id, two.evidence.evidence_id)
        self.assertEqual(one.claims, two.claims)
        self.assertNotEqual(one.evidence.first_ingested_at, two.evidence.first_ingested_at)

    def test_change_and_reversion_preserve_history(self):
        one = self.ingest()
        two = self.a.ingest(replace(self.adapter, text="Changed."))
        three = self.ingest()
        self.assertEqual(two.evidence.version, 2)
        self.assertNotEqual(one.evidence.evidence_id, two.evidence.evidence_id)
        self.assertEqual(three.evidence.version, 1)
        self.assertEqual(three.event.previous_evidence_id, two.evidence.evidence_id)
        self.assertTrue(three.event.duplicate)
        self.assertEqual(self.a.current(one.evidence.source_id), one.evidence)
        self.assertEqual(self.a.content(one.evidence.normalized_ref).decode(), self.adapter.text)

    def test_isolation_all_reference_accessors(self):
        one = self.ingest()
        for scope in (Scope("t1", "b"), Scope("t2", "a")):
            other = self.store.for_candidate(scope)
            two = other.ingest(self.adapter, self.extractor)
            self.assertEqual(one.evidence.raw_hash, two.evidence.raw_hash)
            for x, y in ((one.evidence.evidence_id, two.evidence.evidence_id),
                         (one.evidence.raw_ref, two.evidence.raw_ref),
                         (one.evidence.source_id, two.evidence.source_id),
                         (one.claims[0].claim_id, two.claims[0].claim_id),
                         (one.supports[0].support_id, two.supports[0].support_id)):
                self.assertNotEqual(x, y)
            for method, key in ((other.evidence, one.evidence.evidence_id),
                                (other.content, one.evidence.raw_ref),
                                (other.source, one.evidence.source_id),
                                (other.history, one.evidence.source_id),
                                (other.current, one.evidence.source_id),
                                (other.versions, one.evidence.source_id),
                                (other.delete_source, one.evidence.source_id),
                                (other.claim, one.claims[0].claim_id),
                                (other.supports, one.claims[0].claim_id),
                                (other.support, one.supports[0].support_id),
                                (other.untrusted_envelope, one.evidence.evidence_id)):
                with self.assertRaises(KeyError):
                    method(key)

    def test_scope_required(self):
        for args in (("", "a"), ("t", " "), (None, "a")):
            with self.assertRaises(ValueError):
                Scope(*args)
        with self.assertRaises(ValueError):
            self.store.for_candidate(None)
        with self.assertRaises(AttributeError):
            self.a.scope = Scope("other", "candidate")

    def test_exact_claim_dedup_across_sources(self):
        one = self.ingest()
        two = self.a.ingest(replace(self.adapter, input_id="different-source"), self.extractor)
        self.assertEqual(one.claims, two.claims)
        self.assertNotEqual(one.evidence.evidence_id, two.evidence.evidence_id)
        self.assertEqual(len(self.a.supports(one.claims[0].claim_id)), 2)
        self.assertEqual(one.evidence.raw_ref, two.evidence.raw_ref)

    def test_distinct_claims_not_semantically_merged(self):
        self.ingest()
        draft = replace(self.draft, text="Expert in Python.")
        self.a.ingest(self.adapter, AnnotatedFixtureExtractor((draft,)))
        self.assertEqual(len(self.a.claims()), 2)
        # Validation proves citation integrity, NOT semantic entailment.

    def test_confidence_is_never_verification(self):
        result = self.ingest()
        self.assertEqual(result.supports[0].extraction_confidence, 0.97)
        self.assertEqual(result.supports[0].verification, VerificationState.UNREVIEWED)
        self.assertIn(result.supports[0].support_id, result.event.support_ids)
        with self.assertRaises((TypeError, ValueError)):
            replace(result.supports[0], verification=VerificationState.VERIFIED)

    def test_invalid_drafts_fail(self):
        for confidence in (float("nan"), float("inf"), -0.1, 1.1, True):
            with self.assertRaises(ValueError):
                replace(self.draft, confidence=confidence)
        for changes in ({"text": " "}, {"concepts": ["Python"]},
                        {"kind": "observation"}, {"relationship": "verified"}):
            with self.assertRaises(ValueError):
                replace(self.draft, **changes)

    def test_bad_spans_rollback_entire_ingestion(self):
        for changes in ({"quote": "wrong"}, {"end": 999}, {"start": -1},
                        {"start": 1.2}, {"start": 3, "end": 2}):
            bad = replace(self.draft, **changes)
            with self.assertRaises(ValueError):
                self.a.ingest(self.adapter, AnnotatedFixtureExtractor((self.draft, bad)))
            self.assertEqual(self.a.claims(), ())
        result = self.ingest()
        self.assertEqual(result.evidence.version, 1)
        self.assertEqual(len(self.a.history(result.evidence.source_id)), 1)

    def test_no_candidate_promotion_to_observation(self):
        draft = replace(self.draft, kind=ClaimKind.OBSERVATION, relationship=Relation.SUPPORTS)
        with self.assertRaises(ValueError):
            self.a.ingest(self.adapter, AnnotatedFixtureExtractor((draft,)))
        self.assertEqual(self.a.claims(), ())

    def test_trusted_collection_contract_separates_observation_and_verification(self):
        document = replace(self.adapter.read(), origin=Origin.EXTERNALLY_OBSERVED,
                           supplied_by="test-collector", adapter="test-collector-v1")
        class Collector:
            def read(self):
                return document
        draft = replace(self.draft, kind=ClaimKind.OBSERVATION, relationship=Relation.SUPPORTS)
        result = self.a.ingest(Collector(), AnnotatedFixtureExtractor((draft,)))
        self.assertEqual(result.supports[0].verification, VerificationState.UNREVIEWED)
        self.assertEqual(result.evidence.origin, Origin.EXTERNALLY_OBSERVED)

    def test_inferences_and_contradictions_preserve_provenance(self):
        draft = replace(self.draft, kind=ClaimKind.INFERENCE, relationship=Relation.CONTRADICTS,
                        rationale="Synthetic contradictory interpretation")
        result = self.a.ingest(self.adapter, AnnotatedFixtureExtractor((draft,)))
        support = result.supports[0]
        self.assertEqual(support.claim_kind, ClaimKind.INFERENCE)
        self.assertEqual(support.relationship, Relation.CONTRADICTS)
        self.assertEqual(support.pointer.quote, self.adapter.text)
        self.assertEqual(support.extractor, self.extractor.version)

    def test_delete_restore_retains_citations(self):
        one = self.ingest()
        self.a.delete_source(one.evidence.source_id)
        self.assertIsNone(self.a.current(one.evidence.source_id))
        self.assertEqual(self.a.evidence(one.evidence.evidence_id), one.evidence)
        self.assertEqual(self.a.content(one.evidence.raw_ref).decode(), self.adapter.text)
        two = self.ingest()
        self.assertTrue(two.event.duplicate)
        self.assertEqual(self.a.current(one.evidence.source_id), one.evidence)
        self.assertEqual([e.action for e in self.a.history(one.evidence.source_id)],
                         ["ingest", "delete", "ingest"])

    def test_content_and_records_are_immutable(self):
        result = self.ingest()
        with self.assertRaises(FrozenInstanceError):
            result.evidence.source_title = "tampered"
        with self.assertRaises(FrozenInstanceError):
            result.supports[0].pointer.quote = "tampered"
        self.assertIsInstance(self.a.content(result.evidence.raw_ref), bytes)

    def test_injection_is_ordinary_data(self):
        result = self.a.ingest(PlainTextAdapter("attack", MALICIOUS))
        payload = json.loads(self.a.untrusted_envelope(result.evidence.evidence_id))
        self.assertEqual(payload["content"], MALICIOUS)
        self.assertEqual(payload["trust"], "untrusted_data")
        self.assertNotIn("role", payload)
        self.assertEqual(result.claims, ())
        self.assertEqual(result.supports, ())

    def test_normalization_and_unicode_offsets(self):
        raw = "Résumé\r\nBuilt a Python service.\r".encode()
        self.assertEqual(normalize(raw), "Résumé\nBuilt a Python service.\n")
        adapter = PlainTextAdapter("unicode", raw.decode())
        text = adapter.read().normalized
        start = text.index(self.draft.text)
        draft = replace(self.draft, start=start, end=start + len(self.draft.text))
        result = self.a.ingest(adapter, AnnotatedFixtureExtractor((draft,)))
        self.assertEqual(self.a.content(result.evidence.raw_ref), raw)
        self.assertEqual(self.a.content(result.evidence.normalized_ref).decode(), text)
        self.assertNotEqual(result.evidence.raw_hash, result.evidence.normalized_hash)

    def test_invalid_content(self):
        for raw in (b"", b"   ", b"\xff", b"a\x00", b"x" * 1_000_001):
            with self.assertRaises((ValueError, UnicodeDecodeError)):
                normalize(raw)

    def test_local_root_and_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "cv.md").write_text(self.adapter.text)
            self.assertEqual(LocalTextAdapter(root, "cv.md", "cv").read().normalized, self.adapter.text)
            for path in ("../outside.md", "/etc/passwd", "script.py"):
                with self.assertRaises(ValueError):
                    LocalTextAdapter(root, path, "cv").read()
            (root / "link.md").symlink_to("/etc/passwd")
            with self.assertRaises(ValueError):
                LocalTextAdapter(root, "link.md", "cv").read()

    def fixture(self):
        return NormalizedFixtureAdapter("future-source", "future-id", "https://example.invalid/x",
                                        "Synthetic", self.adapter.text,
                                        Locator("vendor.future.v7", '{"entry":"1"}'))

    def test_extension_and_metadata_are_untrusted(self):
        adapter = replace(self.fixture(), metadata_json='{"verified":true,"issuer":"VeriBridge"}')
        result = self.a.ingest(adapter, self.extractor)
        self.assertEqual(self.a.source(result.evidence.source_id).source_type, "future-source")
        self.assertEqual(result.evidence.origin, Origin.SYNTHETIC_FIXTURE)
        self.assertEqual(result.supports[0].verification, VerificationState.UNREVIEWED)

    def test_locator_validation(self):
        for kind, attrs in (("github.v1", {}), ("pdf.v1", {"document_id": "x", "page": 0}),
                            ("text_input.v1", {"input_id": ""})):
            with self.assertRaises(ValueError):
                Locator(kind, canonical(attrs))
        with self.assertRaises(ValueError):
            Locator("custom", '[]')

    def test_fixture_uri_and_timestamp_validation(self):
        for uri in ("file:///etc/passwd", "javascript:alert(1)", "https://u:p@example.invalid"):
            with self.assertRaises(ValueError):
                replace(self.fixture(), uri=uri).read()
        with self.assertRaises(ValueError):
            replace(self.fixture(), source_timestamp="2026-09-26").read()
        with self.assertRaises(ValueError):
            replace(self.fixture(), metadata_json='[]').read()

    def test_source_key_cannot_silently_retarget_uri(self):
        self.a.ingest(self.fixture())
        with self.assertRaises(ValueError):
            self.a.ingest(replace(self.fixture(), uri="https://example.invalid/other"))

    def test_metadata_or_adapter_change_versions(self):
        one = self.a.ingest(self.fixture())
        two = self.a.ingest(replace(self.fixture(), source_timestamp="2026-09-25T00:00:00Z"))
        self.assertNotEqual(one.evidence.evidence_id, two.evidence.evidence_id)
        self.assertEqual(one.evidence.raw_hash, two.evidence.raw_hash)
        self.assertEqual(two.evidence.version, 2)

    def test_extractor_revision_preserves_old_support(self):
        one = self.ingest()
        two = self.a.ingest(self.adapter, replace(self.extractor, version="annotated-fixture-v2"))
        self.assertEqual(one.evidence, two.evidence)
        self.assertNotEqual(one.supports[0].support_id, two.supports[0].support_id)
        self.assertEqual(len(self.a.supports(one.claims[0].claim_id)), 2)

    def test_verification_record_requires_attestation_provenance(self):
        with self.assertRaises(ValueError):
            VerificationRecord(self.a.scope, "support", VerificationState.VERIFIED,
                               "VeriBridge", "", "v1", "2026-09-26T00:00:00Z", "review")


if __name__ == "__main__":
    unittest.main()
