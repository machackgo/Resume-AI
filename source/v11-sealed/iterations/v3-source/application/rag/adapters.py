"""Source adapter contract and offline implementations. No networking or execution."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

from .domain import Locator, Origin, canonical, required, timestamp

MAX_BYTES = 1_000_000
NORMALIZATION = "utf8-newlines-v1"


def normalize(raw: bytes) -> str:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES:
        raise ValueError("content must contain 1..1,000,000 bytes")
    text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip() or "\x00" in text:
        raise ValueError("empty or NUL-containing text")
    return text


@dataclass(frozen=True)
class CanonicalDocument:
    source_type: str
    source_key: str
    source_uri: str | None
    title: str
    raw: bytes
    normalized: str
    origin: Origin
    supplied_by: str
    adapter: str
    locator: Locator
    source_timestamp: str | None = None
    metadata_json: str = "{}"
    normalization: str = NORMALIZATION

    def __post_init__(self) -> None:
        import json
        for name in ("source_type", "source_key", "title", "supplied_by", "adapter", "normalization"):
            required(getattr(self, name), name)
        if self.source_uri is not None:
            required(self.source_uri, "source_uri")
        if not isinstance(self.origin, Origin) or not isinstance(self.locator, Locator):
            raise ValueError("invalid origin or locator")
        if not isinstance(self.raw, bytes) or not 0 < len(self.raw) <= MAX_BYTES:
            raise ValueError("invalid raw content size")
        required(self.normalized, "normalized content")
        if len(self.normalized.encode("utf-8")) > MAX_BYTES or "\x00" in self.normalized:
            raise ValueError("invalid normalized content")
        if self.source_timestamp is not None:
            timestamp(self.source_timestamp)
        metadata = json.loads(self.metadata_json)
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        object.__setattr__(self, "metadata_json", canonical(metadata))


class SourceAdapter(Protocol):
    """Application selects adapter; uploaded content cannot register/select code.

    Implementations must declare truthful collection origin, stable source key,
    versioned normalization, bounded raw/normalized data and native locator.
    EXTERNALLY_OBSERVED is reserved for future trusted collection implementations.
    """
    def read(self) -> CanonicalDocument: ...


@dataclass(frozen=True)
class PlainTextAdapter:
    input_id: str
    text: str
    title: str = "Candidate text"

    def read(self) -> CanonicalDocument:
        raw = self.text.encode("utf-8")
        return CanonicalDocument(
            "plain_text", self.input_id, None, self.title, raw, normalize(raw),
            Origin.CANDIDATE_SUPPLIED, "candidate", "plain-text-v1",
            Locator("text_input.v1", canonical({"input_id": self.input_id})))


@dataclass(frozen=True)
class LocalTextAdapter:
    root: Path
    relative_path: str
    document_id: str

    def read(self) -> CanonicalDocument:
        root = self.root.resolve()
        path = (root / self.relative_path).resolve()
        if not path.is_relative_to(root) or path.suffix.lower() not in {".txt", ".md"}:
            raise ValueError("local file must be .txt/.md within configured root")
        # Bounded read; root must be an application-owned staging directory.
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        return CanonicalDocument(
            "local_document", self.document_id, None, path.name, raw, normalize(raw),
            Origin.CANDIDATE_SUPPLIED, "candidate", "local-text-v1",
            Locator("document.v1", canonical({"document_id": self.document_id,
                                               "section": "whole document"})))


@dataclass(frozen=True)
class NormalizedFixtureAdapter:
    """Represents a normalized capture, NOT proof that a URL was fetched.

    Also covers future document types without adding them to a core enum.
    """
    source_type: str
    source_key: str
    uri: str
    title: str
    text: str
    locator: Locator
    source_timestamp: str | None = None
    metadata_json: str = "{}"

    def read(self) -> CanonicalDocument:
        uri = urlsplit(self.uri)
        if uri.scheme not in {"https", "http"} or not uri.hostname or uri.username or uri.password:
            raise ValueError("fixture URI must be HTTP(S) without credentials")
        raw = self.text.encode("utf-8")
        return CanonicalDocument(
            self.source_type, self.source_key, self.uri, self.title, raw, normalize(raw),
            Origin.SYNTHETIC_FIXTURE, "synthetic_fixture", "normalized-fixture-v1",
            self.locator, self.source_timestamp, self.metadata_json)
