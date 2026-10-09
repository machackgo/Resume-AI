"""Provider-independent immutable evidence ledger types (schema version 1)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math
from typing import Any

SCHEMA_VERSION = 1


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(kind: str, *parts: Any) -> str:
    return kind + "_" + digest(canonical([SCHEMA_VERSION, *parts]).encode("utf-8"))


def required(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")


def timestamp(value: str) -> None:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include timezone")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Scope:
    tenant_id: str
    candidate_id: str

    def __post_init__(self) -> None:
        required(self.tenant_id, "tenant_id")
        required(self.candidate_id, "candidate_id")

    @property
    def key(self) -> tuple[str, str]:
        return self.tenant_id, self.candidate_id


class Origin(str, Enum):
    CANDIDATE_SUPPLIED = "candidate_supplied"
    EXTERNALLY_OBSERVED = "externally_observed"
    SYNTHETIC_FIXTURE = "synthetic_fixture"


class ClaimKind(str, Enum):
    ASSERTION = "candidate_assertion"
    OBSERVATION = "observation"
    INFERENCE = "inference"


class Relation(str, Enum):
    ASSERTS = "asserts"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXT = "context"


class VerificationState(str, Enum):
    UNREVIEWED = "unreviewed"
    VERIFIED = "verified"
    REJECTED = "rejected"
    DISPUTED = "disputed"


@dataclass(frozen=True)
class Locator:
    """Extensible, namespaced locator. Immutable JSON preserves adapter context.

    All locators also carry a checked normalized Unicode character span in Pointer.
    Native PDF/line coordinates supplement that span; they do not replace it.
    """
    kind: str
    attributes_json: str = "{}"

    def __post_init__(self) -> None:
        required(self.kind, "locator kind")
        attrs = json.loads(self.attributes_json)
        if not isinstance(attrs, dict):
            raise ValueError("locator attributes must be an object")
        object.__setattr__(self, "attributes_json", canonical(attrs))
        required_keys = {
            "text_input.v1": ("input_id",),
            "document.v1": ("document_id", "section"),
            "website.v1": ("url", "section"),
            "github.v1": ("repository", "commit", "file", "line_start", "line_end"),
            "pdf.v1": ("document_id", "page"),
            "veribridge.v1": ("report_id", "section"),
        }
        for key in required_keys.get(self.kind, ()):
            if key not in attrs:
                raise ValueError(f"{self.kind} requires {key}")
            if key not in {"page", "line_start", "line_end"}:
                required(attrs[key], key)
        for key in ("page", "line_start", "line_end"):
            if key in attrs and (type(attrs[key]) is not int or attrs[key] < 1):
                raise ValueError(f"{key} must be a positive integer")
        if "line_end" in attrs and attrs["line_end"] < attrs.get("line_start", 1):
            raise ValueError("reversed line range")


@dataclass(frozen=True)
class Pointer:
    evidence_id: str
    start: int
    end: int
    quote: str
    locator: Locator

    def __post_init__(self) -> None:
        required(self.evidence_id, "evidence_id")
        if type(self.start) is not int or type(self.end) is not int or not 0 <= self.start < self.end:
            raise ValueError("invalid half-open character span")
        required(self.quote, "quote")
        if not isinstance(self.locator, Locator):
            raise ValueError("pointer requires a typed locator")


@dataclass(frozen=True)
class Source:
    scope: Scope
    source_id: str
    source_type: str
    source_key: str
    source_uri: str | None


@dataclass(frozen=True)
class Evidence:
    scope: Scope
    evidence_id: str
    source_id: str
    version: int
    source_title: str
    raw_ref: str
    normalized_ref: str
    raw_hash: str
    normalized_hash: str
    first_ingested_at: str
    source_timestamp: str | None
    origin: Origin
    supplied_by: str
    adapter: str
    normalization: str
    metadata_json: str
    locator: Locator
    trust: str = field(default="untrusted_data", init=False)


@dataclass(frozen=True)
class IngestionEvent:
    scope: Scope
    event_id: str
    source_id: str
    evidence_id: str | None
    occurred_at: str
    action: str
    previous_evidence_id: str | None
    duplicate: bool = False
    support_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Claim:
    scope: Scope
    claim_id: str
    text: str
    # Concepts are open vocabulary; they are annotations, never a verified skill list.
    concepts: tuple[str, ...] = ()
    subject: str | None = None
    action: str | None = None
    object: str | None = None


@dataclass(frozen=True)
class Support:
    scope: Scope
    support_id: str
    claim_id: str
    pointer: Pointer
    relationship: Relation
    claim_kind: ClaimKind
    extraction_confidence: float | None
    extractor: str
    rationale: str
    # No extraction API can set this to verified.
    verification: VerificationState = field(default=VerificationState.UNREVIEWED, init=False)


@dataclass(frozen=True)
class VerificationRecord:
    """Future authenticated verifier output; no Stage 3A writer or ingestion promotion.

    An issuer label alone is NOT an authenticated VeriBridge attestation.
    Records apply to exact support/evidence versions, never all candidate skills.
    """
    scope: Scope
    support_id: str
    state: VerificationState
    issuer: str
    attestation_ref: str
    policy_version: str
    assessed_at: str
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, VerificationState):
            raise ValueError("invalid verification state")
        for key in ("support_id", "issuer", "attestation_ref", "policy_version", "rationale"):
            required(getattr(self, key), key)
        timestamp(self.assessed_at)


@dataclass(frozen=True)
class ClaimDraft:
    """Output of a trusted extractor implementation, still an unverified proposal."""
    text: str
    start: int
    end: int
    quote: str
    kind: ClaimKind = ClaimKind.ASSERTION
    relationship: Relation = Relation.ASSERTS
    confidence: float | None = None
    concepts: tuple[str, ...] = ()
    subject: str | None = None
    action: str | None = None
    object: str | None = None
    rationale: str = "Explicit synthetic annotation; no semantic verification"
    locator: Locator | None = None

    def __post_init__(self) -> None:
        required(self.text, "claim text")
        required(self.rationale, "rationale")
        if not isinstance(self.kind, ClaimKind) or not isinstance(self.relationship, Relation):
            raise ValueError("invalid claim kind or relationship")
        if self.confidence is not None and (type(self.confidence) not in (int, float)
                or not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1):
            raise ValueError("confidence must be finite and in [0,1]")
        if not isinstance(self.concepts, tuple):
            raise ValueError("concepts must be an immutable tuple")
        for concept in self.concepts:
            required(concept, "concept")
        for part in (self.subject, self.action, self.object):
            if part is not None:
                required(part, "normalized claim component")
