"""Immutable views composed with Stage 3A types; no vector-provider types."""
from dataclasses import dataclass
from enum import Enum
from ..domain import Evidence, IngestionEvent, Source, Support
from .policy import ChunkPolicy


@dataclass(frozen=True, order=True)
class BoundaryHint:
    start: int
    end: int
    kind: str = 'section'

    def __post_init__(self):
        if (type(self.start) is not int or type(self.end) is not int or
            not 0 <= self.start < self.end or self.kind not in
            {'section', 'paragraph', 'list_item', 'code_block', 'function', 'class'}):
            raise ValueError('invalid structural hint')


class Containment(str, Enum):
    FULLY_CONTAINED = 'fully_contained'
    PARTIALLY_OVERLAPPING = 'partially_overlapping'


@dataclass(frozen=True)
class ChunkClaimLink:
    support: Support
    containment: Containment
    overlap_start: int
    overlap_end: int


@dataclass(frozen=True)
class RetrievalChunk:
    chunk_id: str
    revision_id: str
    evidence: Evidence
    policy: ChunkPolicy
    hints: tuple[BoundaryHint, ...]
    input_support_ids: tuple[str, ...]
    start: int
    end: int
    text: str
    measured_size: int
    claim_links: tuple[ChunkClaimLink, ...]
    provenance_events: tuple[IngestionEvent, ...]
    schema_version: int = 1

    @property
    def scope(self):
        return self.evidence.scope


@dataclass(frozen=True)
class Citation:
    chunk: RetrievalChunk
    source: Source
    current_evidence_id: str | None
    source_state: str
    history_changed: bool
    # Native locator remains evidence.locator; more precise support locators are
    # retained on each claim link. start/end refer to normalized Unicode text.
    coordinate_system: str = 'normalized_unicode_codepoints_half_open'
