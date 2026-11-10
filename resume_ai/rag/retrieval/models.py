"""Retrieval candidates are never entailment or verification decisions."""
from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from ..domain import Scope, Locator, required
from ..vectorstore.models import SearchFilter

class NeedType(str, Enum):
    JOB_REQUIREMENT='job_requirement'
    SKILL='skill'
    EXPERIENCE='experience'
    PROJECT='project'
    CREDENTIAL='credential'
    ACCOMPLISHMENT='accomplishment'
    TECHNOLOGY='technology'
    DOMAIN_KNOWLEDGE='domain_knowledge'
    QUESTION='question'

@dataclass(frozen=True)
class InformationNeed:
    kind: NeedType
    text: str
    requirement_id: str
    def __post_init__(self):
        if not isinstance(self.kind,NeedType): raise ValueError('typed need required')
        required(self.text,'text'); required(self.requirement_id,'requirement_id')
        if len(self.text)>2000: raise ValueError('focused need exceeds 2000 characters')

@dataclass(frozen=True)
class QueryPlan:
    query_id: str
    need: InformationNeed
    text: str
    expansions: tuple[str,...]
    policy: str

@dataclass(frozen=True)
class RetrievalConfig:
    strategy: str='semantic'
    semantic_budget: int=20
    lexical_budget: int=20
    rrf_constant: int=60
    expansion: bool=False
    deduplicate: bool=True
    per_source_cap: int | None=None
    version: str='retrieval-v1-bm25-k1.2-b0.75-rrf'
    def __post_init__(self):
        if self.strategy not in ('semantic','lexical','hybrid'): raise ValueError('strategy')
        for n in (self.semantic_budget,self.lexical_budget,self.rrf_constant):
            if type(n) is not int or not 1<=n<=10000: raise ValueError('budget/rrf')
        if self.per_source_cap is not None and (type(self.per_source_cap) is not int or self.per_source_cap<1): raise ValueError('cap')
        if self.version!='retrieval-v1-bm25-k1.2-b0.75-rrf': raise ValueError('unknown config version')

@dataclass(frozen=True)
class EvidenceReference:
    scope: Scope
    embedding_id: str
    chunk_id: str
    chunk_revision_id: str
    evidence_id: str
    source_id: str
    source_version: int
    source_type: str
    source_uri: str | None
    locator: Locator
    start: int
    end: int
    origin: str
    trust: str
    verification: str
    support_ids: tuple[str,...]
    claim_relationships: tuple[tuple[str,str,str,str],...]
    provenance_event_ids: tuple[str,...]
    semantic_space_id: str
    lifecycle: str

@dataclass(frozen=True)
class RetrievalResult:
    rank: int
    score: float
    strategy: str
    query_id: str
    reference: EvidenceReference
    semantic_rank: int | None
    semantic_score: float | None
    lexical_rank: int | None
    lexical_score: float | None
    hybrid_rrf_score: float | None
    exact_terms: tuple[str,...]
    corroborating_references: tuple[EvidenceReference,...]=()

@dataclass(frozen=True)
class RetrievalResponse:
    query: QueryPlan
    config: RetrievalConfig
    filters: SearchFilter
    results: tuple[RetrievalResult,...]
    eligible_count: int
    duplicate_suppressed: int
    diversity_suppressed: int

class EvidenceRetriever(Protocol):
    def retrieve(self, tenant_id: str, candidate_id: str, information_need: InformationNeed,
                 filters: SearchFilter=SearchFilter(), top_k: int=5) -> RetrievalResponse: ...
