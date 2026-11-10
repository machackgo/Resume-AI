"""Vendor-independent immutable contracts and identity fingerprints."""
from dataclasses import dataclass, asdict
import json
import math
from ..domain import Scope, canonical, stable_id, required, timestamp
from .similarity import validate


@dataclass(frozen=True)
class EmbeddingConfig:
    provider: str
    model: str
    revision: str
    dimension: int
    normalized: bool
    document_prefix: str = ''
    query_prefix: str = ''
    configuration_json: str = '{}'

    def __post_init__(self):
        for name in ('provider', 'model', 'revision'):
            required(getattr(self, name), name)
        if type(self.dimension) is not int or self.dimension < 1 or type(self.normalized) is not bool:
            raise ValueError('invalid dimension/normalization')
        if not isinstance(self.document_prefix, str) or not isinstance(self.query_prefix, str):
            raise ValueError('prefixes must be strings')
        value = json.loads(self.configuration_json)
        if not isinstance(value, dict):
            raise ValueError('configuration must be an object')
        object.__setattr__(self, 'configuration_json', canonical(value))

    @property
    def identity(self):
        return stable_id('embedding_config', asdict(self))


@dataclass(frozen=True)
class EmbeddingInput:
    strategy: str
    text: str
    input_hash: str


@dataclass(frozen=True)
class EmbeddingRecord:
    record_id: str
    cache_key: str
    scope: Scope
    chunk_id: str
    chunk_revision_id: str
    evidence_id: str
    source_id: str
    evidence_version: int
    policy_id: str
    config: EmbeddingConfig
    input_strategy: str
    input_hash: str
    vector: tuple[float, ...]
    created_at: str
    origin: str
    trust: str
    support_ids: tuple[str, ...]
    provenance_event_ids: tuple[str, ...]
    schema_version: int = 1

    def __post_init__(self):
        if not isinstance(self.scope, Scope) or not isinstance(self.vector, tuple):
            raise ValueError('typed scope and immutable vector required')
        validate(self.vector, self.config.dimension)
        if self.config.normalized and not math.isclose(math.hypot(*self.vector), 1, abs_tol=1e-5):
            raise ValueError('provider returned non-unit vector')
        if self.trust != 'untrusted_data':
            raise ValueError('embeddings cannot promote trust')
        timestamp(self.created_at)
