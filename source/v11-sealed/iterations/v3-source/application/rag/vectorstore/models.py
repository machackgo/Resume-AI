"""Storage contracts; no database or embedding-provider dependencies."""
from dataclasses import dataclass, asdict
from typing import Literal
from ..domain import Scope, stable_id, required
from ..embeddings.models import EmbeddingConfig, EmbeddingRecord
from ..embeddings.input_builder import build_input
from ..embeddings.similarity import validate

State = Literal['active', 'superseded', 'staged', 'deleted']

@dataclass(frozen=True)
class EmbeddingSpace:
    config: EmbeddingConfig
    input_strategy: str

    def __post_init__(self):
        required(self.input_strategy, 'input strategy')
        if not isinstance(self.config, EmbeddingConfig):
            raise ValueError('typed embedding config required')

    @property
    def space_id(self) -> str:
        return stable_id('embedding_space', 'stage3d-v1', self.config.identity, self.input_strategy)

@dataclass(frozen=True)
class ChunkReference:
    scope: Scope
    chunk_id: str
    chunk_revision_id: str
    evidence_id: str
    source_id: str
    evidence_version: int
    policy_id: str
    source_type: str
    evidence_type: str
    origin: str
    trust: str
    support_ids: tuple[str, ...]
    provenance_event_ids: tuple[str, ...]
    input_hashes: tuple[tuple[str, str], ...]
    verification_state: str = 'resolve_supports'

    @classmethod
    def from_citation(cls, citation):
        c = citation.chunk
        if citation.source.scope != c.scope or citation.source.source_id != c.evidence.source_id:
            raise ValueError('foreign citation')
        return cls(c.scope, c.chunk_id, c.revision_id, c.evidence.evidence_id,
                   c.evidence.source_id, c.evidence.version, c.policy.policy_id,
                   citation.source.source_type, c.evidence.locator.kind,
                   c.evidence.origin.value, c.evidence.trust,
                   tuple(x.support.support_id for x in c.claim_links),
                   tuple(x.event_id for x in c.provenance_events),
                   tuple((s, build_input(c, s).input_hash) for s in ('raw-v1', 'title-section-v1')))

    def __post_init__(self):
        if not isinstance(self.scope, Scope) or type(self.evidence_version) is not int or self.evidence_version < 1:
            raise ValueError('invalid scope/version')
        for k in ('chunk_id','chunk_revision_id','evidence_id','source_id','policy_id','source_type','evidence_type','origin'):
            required(getattr(self,k),k)
        if self.trust != 'untrusted_data' or self.verification_state != 'resolve_supports':
            raise ValueError('storage cannot verify evidence')
        if len(dict(self.input_hashes)) != len(self.input_hashes) or not self.input_hashes:
            raise ValueError('input hashes required')

@dataclass(frozen=True)
class SearchFilter:
    state: State | None = 'active'
    source_id: str | None = None
    evidence_id: str | None = None
    source_type: str | None = None
    evidence_type: str | None = None
    origin: str | None = None
    trust: str | None = None
    policy_id: str | None = None
    verification_state: str | None = None

    def __post_init__(self):
        if self.state not in (None, 'active','superseded','staged','deleted'):
            raise ValueError('invalid lifecycle state')
        for k,v in asdict(self).items():
            if v is not None: required(v,k)

@dataclass(frozen=True)
class VectorQuery:
    space: EmbeddingSpace
    vector: tuple[float, ...]
    limit: int = 10
    filters: SearchFilter = SearchFilter()

    def __post_init__(self):
        validate(self.vector, self.space.config.dimension)
        if type(self.limit) is not int or not 1 <= self.limit <= 100000:
            raise ValueError('invalid search limit')

@dataclass(frozen=True)
class StoredEmbedding:
    record: EmbeddingRecord
    state: State
    note: str
    stored_at: str
    updated_at: str

@dataclass(frozen=True)
class SearchHit:
    embedding_id: str
    chunk_id: str
    chunk_revision_id: str
    evidence_id: str
    score: float

@dataclass(frozen=True)
class StoreHealth:
    healthy: bool
    backend: str
    schema_version: int
    details: str


def record_from_dict(value):
    d = dict(value)
    d['scope'] = Scope(**d['scope'])
    d['config'] = EmbeddingConfig(**d['config'])
    for k in ('vector','support_ids','provenance_event_ids'): d[k] = tuple(d[k])
    return EmbeddingRecord(**d)
