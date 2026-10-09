"""Immutable relevance outputs. Scores have no entailment/support meaning."""
from dataclasses import dataclass
import math
from ..domain import canonical, digest, required
from ..retrieval.models import RetrievalResult

@dataclass(frozen=True)
class RerankerConfig:
    provider: str
    model: str
    revision: str
    tokenizer_revision: str
    input_strategy: str = 'need-evidence-v1'
    device: str = 'cpu'
    dtype: str = 'float32'
    batch_size: int = 16
    max_tokens: int = 512
    runtime: str = 'python'
    version: str = 'reranking-v1'

    def __post_init__(self):
        for name in ('provider', 'model', 'revision', 'tokenizer_revision', 'device', 'dtype', 'runtime'):
            required(getattr(self, name), name)
        if self.input_strategy != 'need-evidence-v1' or self.version != 'reranking-v1':
            raise ValueError('unknown input/config version')
        for number in (self.batch_size, self.max_tokens):
            if type(number) is not int or number < 1:
                raise ValueError('invalid batch/token budget')

    @property
    def identity(self):
        from dataclasses import asdict
        return digest(canonical(asdict(self)).encode())

@dataclass(frozen=True)
class RerankedEvidence:
    original: RetrievalResult
    information_need_id: str
    rerank_rank: int
    rerank_score: float
    config: RerankerConfig
    candidate_budget: int
    output_budget: int
    input_hash: str

    def __post_init__(self):
        if not isinstance(self.original, RetrievalResult) or not isinstance(self.config, RerankerConfig):
            raise ValueError('typed result/config required')
        required(self.information_need_id, 'information_need_id')
        required(self.input_hash, 'input_hash')
        if type(self.rerank_score) not in (int, float) or not math.isfinite(self.rerank_score):
            raise ValueError('finite relevance score required')
        if any(type(n) is not int or n < 1 for n in (self.rerank_rank, self.candidate_budget, self.output_budget)):
            raise ValueError('positive rank/budgets required')
        if self.rerank_rank > min(self.candidate_budget, self.output_budget):
            raise ValueError('rank exceeds budget')

    @property
    def tenant_id(self): return self.original.reference.scope.tenant_id
    @property
    def candidate_id(self): return self.original.reference.scope.candidate_id
    @property
    def original_retrieval_rank(self): return self.original.rank
    @property
    def original_semantic_score(self): return self.original.semantic_score
    @property
    def reference(self): return self.original.reference
    @property
    def corroborating_references(self): return self.original.corroborating_references
    @property
    def reranker_identity(self): return self.config.identity
