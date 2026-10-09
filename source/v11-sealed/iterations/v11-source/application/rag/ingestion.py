"""Atomic, scoped reference ingestion ledger; deliberately no storage provider."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

from .adapters import CanonicalDocument, SourceAdapter
from .domain import (Claim, ClaimDraft, ClaimKind, Evidence, IngestionEvent, Origin,
                     Pointer, Scope, Source, Support, canonical, digest, now,
                     required, stable_id, timestamp)


class ClaimExtractor(Protocol):
    version: str

    def extract(self, document: CanonicalDocument) -> tuple[ClaimDraft, ...]: ...


@dataclass(frozen=True)
class NoClaims:
    """Lossless ingestion is useful before a semantic extractor exists."""
    version: str = "no-claims-v1"

    def extract(self, document: CanonicalDocument) -> tuple[ClaimDraft, ...]:
        return ()


@dataclass(frozen=True)
class AnnotatedFixtureExtractor:
    """Explicit test annotations, supplied by application code, not document metadata.

    No sentence splitting, chunking, skill rules, LLM, or verification.
    """
    drafts: tuple[ClaimDraft, ...]
    version: str = "annotated-fixture-v1"

    def extract(self, document: CanonicalDocument) -> tuple[ClaimDraft, ...]:
        return self.drafts


@dataclass(frozen=True)
class IngestionResult:
    evidence: Evidence
    event: IngestionEvent
    claims: tuple[Claim, ...]
    supports: tuple[Support, ...]


@dataclass
class _Partition:
    sources: dict[str, Source] = field(default_factory=dict)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    blobs: dict[str, bytes] = field(default_factory=dict)
    claims: dict[str, Claim] = field(default_factory=dict)
    supports: dict[str, Support] = field(default_factory=dict)
    events: list[IngestionEvent] = field(default_factory=list)
    current: dict[str, str] = field(default_factory=dict)
    deleted: set[str] = field(default_factory=set)


class MemoryLedger:
    """Single-process reference store. Scope must come from authenticated context.

    Scoping prevents accidental cross-candidate reads, not malicious Python code
    with access to process memory. No public unscoped read/list API is provided.
    Production storage must implement authorization and transactional constraints.
    """
    def __init__(self, clock: Callable[[], str] = now) -> None:
        self._partitions: dict[Scope, _Partition] = {}
        self._clock = clock

    def for_candidate(self, scope: Scope) -> CandidateLedger:
        if not isinstance(scope, Scope):
            raise ValueError("explicit tenant/candidate scope required")
        return CandidateLedger(scope, self._partitions.setdefault(scope, _Partition()), self._clock)


class CandidateLedger:
    def __init__(self, scope: Scope, partition: _Partition, clock: Callable[[], str]) -> None:
        self._scope, self._data, self._clock = scope, partition, clock

    @property
    def scope(self) -> Scope:
        return self._scope

    def source(self, source_id: str) -> Source:
        return self._data.sources[source_id]

    def evidence(self, evidence_id: str) -> Evidence:
        return self._data.evidence[evidence_id]

    def claim(self, claim_id: str) -> Claim:
        return self._data.claims[claim_id]

    def support(self, support_id: str) -> Support:
        return self._data.supports[support_id]

    def content(self, reference: str) -> bytes:
        return self._data.blobs[reference]

    def claims(self) -> tuple[Claim, ...]:
        return tuple(self._data.claims.values())

    def supports(self, claim_id: str) -> tuple[Support, ...]:
        self.claim(claim_id)  # Reject foreign/nonexistent identifiers, not silent empty results.
        return tuple(s for s in self._data.supports.values() if s.claim_id == claim_id)

    def history(self, source_id: str) -> tuple[IngestionEvent, ...]:
        self.source(source_id)
        return tuple(e for e in self._data.events if e.source_id == source_id)

    def versions(self, source_id: str) -> tuple[Evidence, ...]:
        self.source(source_id)
        return tuple(e for e in self._data.evidence.values() if e.source_id == source_id)

    def current(self, source_id: str) -> Evidence | None:
        self.source(source_id)
        if source_id in self._data.deleted:
            return None
        return self.evidence(self._data.current[source_id])

    def delete_source(self, source_id: str) -> IngestionEvent:
        """Tombstone only. Retain historical snapshots/citations; no physical erasure."""
        self.source(source_id)
        at = self._clock()
        timestamp(at)
        previous = self._data.current[source_id]
        event = IngestionEvent(self.scope, stable_id("event", self.scope.key,
                               len(self._data.events), source_id, "delete", at),
                               source_id, None, at, "delete", previous)
        self._data.deleted.add(source_id)
        self._data.events.append(event)
        return event

    def ingest(self, adapter: SourceAdapter,
               extractor: ClaimExtractor = NoClaims()) -> IngestionResult:
        document = adapter.read()
        if not isinstance(document, CanonicalDocument):
            raise ValueError("adapter must return CanonicalDocument")
        required(extractor.version, "extractor version")
        at = self._clock()
        timestamp(at)
        source_id = stable_id("source", self.scope.key, document.source_type, document.source_key)
        source = Source(self.scope, source_id, document.source_type,
                        document.source_key, document.source_uri)
        old_source = self._data.sources.get(source_id)
        if old_source is not None and old_source != source:
            raise ValueError("source key already identifies another URI; use a new source key")
        raw_hash = digest(document.raw)
        normalized_bytes = document.normalized.encode("utf-8")
        normalized_hash = digest(normalized_bytes)
        raw_ref = stable_id("blob", self.scope.key, raw_hash)
        normalized_ref = stable_id("blob", self.scope.key, normalized_hash)
        evidence_id = stable_id(
            "evidence", self.scope.key, source_id, raw_hash, normalized_hash,
            document.normalization, document.adapter, document.origin.value,
            document.supplied_by, document.title, document.source_timestamp,
            document.metadata_json, document.locator.kind, document.locator.attributes_json)
        existing = self._data.evidence.get(evidence_id)
        version = 1 + sum(e.source_id == source_id for e in self._data.evidence.values())
        evidence = existing or Evidence(
            self.scope, evidence_id, source_id, version, document.title, raw_ref,
            normalized_ref, raw_hash, normalized_hash, at, document.source_timestamp,
            document.origin, document.supplied_by, document.adapter,
            document.normalization, document.metadata_json, document.locator)
        claims: dict[str, Claim] = {}
        supports: dict[str, Support] = {}
        for draft in extractor.extract(document):
            if not isinstance(draft, ClaimDraft):
                raise ValueError("extractor must return ClaimDraft objects")
            pointer = Pointer(evidence_id, draft.start, draft.end, draft.quote,
                              draft.locator or document.locator)
            if pointer.end > len(document.normalized) or document.normalized[pointer.start:pointer.end] != pointer.quote:
                raise ValueError("claim pointer does not match exact normalized content")
            if draft.kind == ClaimKind.OBSERVATION and document.origin != Origin.EXTERNALLY_OBSERVED:
                raise ValueError("candidate/fixture text cannot be promoted to an external observation")
            # Exact identity only: no unsafe semantic merging of similar claims.
            text = " ".join(draft.text.split())
            concepts = tuple(sorted(set(draft.concepts)))
            claim_id = stable_id("claim", self.scope.key, text, concepts,
                                 draft.subject, draft.action, draft.object)
            claim = Claim(self.scope, claim_id, text, concepts,
                          draft.subject, draft.action, draft.object)
            support_id = stable_id("support", self.scope.key, claim_id, evidence_id,
                                   pointer.start, pointer.end, pointer.quote,
                                   pointer.locator.kind, pointer.locator.attributes_json,
                                   draft.relationship.value, draft.kind.value,
                                   draft.confidence, extractor.version, draft.rationale)
            support = Support(self.scope, support_id, claim_id, pointer,
                              draft.relationship, draft.kind, draft.confidence,
                              extractor.version, draft.rationale)
            claims[claim_id], supports[support_id] = claim, support
        previous = self._data.current.get(source_id)
        event = IngestionEvent(
            self.scope, stable_id("event", self.scope.key, len(self._data.events), evidence_id, at),
            source_id, evidence_id, at, "ingest", previous, existing is not None, tuple(supports))
        # Commit only after ALL adapter/extractor/span validation succeeds.
        self._data.sources[source_id] = source
        self._data.evidence[evidence_id] = evidence
        self._data.blobs[raw_ref] = document.raw
        self._data.blobs[normalized_ref] = normalized_bytes
        self._data.claims.update(claims)
        self._data.supports.update(supports)
        self._data.current[source_id] = evidence_id
        self._data.deleted.discard(source_id)
        self._data.events.append(event)
        return IngestionResult(evidence, event, tuple(claims.values()), tuple(supports.values()))

    def untrusted_envelope(self, evidence_id: str) -> str:
        """Data-only transport contract, NOT a prompt builder or injection defense.

        Future callers must keep system instructions separate and disable tool or
        verification authority for evidence. JSON escaping prevents structural
        field injection; it cannot prevent a language model obeying malicious text.
        """
        e = self.evidence(evidence_id)
        return canonical({"schema_version": 1, "trust": "untrusted_data",
                          "tenant_id": self.scope.tenant_id,
                          "candidate_id": self.scope.candidate_id,
                          "evidence_id": e.evidence_id, "source_id": e.source_id,
                          "origin": e.origin.value,
                          "content": self.content(e.normalized_ref).decode("utf-8")})
