"""Only the trusted wrapper constructs outputs; providers return positional scores.

Bind to one authentic Stage 3E response per need. There is no search capability in
this layer. The caller authenticates the scope and supplies Stage 3E's response;
Python in-process objects are not a cryptographic boundary against the OS owner.
"""
import math
from typing import Protocol, Sequence
from ..domain import Scope
from ..retrieval.models import InformationNeed, RetrievalResponse, RetrievalResult, EvidenceReference
from ..retrieval.query import construct
from ..embeddings.cache import ChunkEmbedder
from ..vectorstore.models import ChunkReference, EmbeddingSpace
from .models import RerankerConfig, RerankedEvidence
from .input_builder import build_input, RerankerInput

class ScoreProvider(Protocol):
    config: RerankerConfig
    def score(self, pairs: Sequence[RerankerInput]) -> Sequence[float]: ...

class Reranker(Protocol):
    def rerank(self, information_need: InformationNeed,
               retrieval_results: Sequence[RetrievalResult], top_n: int) -> tuple[RerankedEvidence, ...]: ...

class IdentityProvider:
    config = RerankerConfig('identity', 'stage3e-order', 'identity-v1', 'none', dtype='none', max_tokens=1)
    def score(self, pairs):
        # These synthetic scores deliberately denote order only.
        return tuple(-float(index) for index in range(len(pairs)))

class CitationTextResolver:
    """Resolve only supplied IDs through stored vectors and the canonical ledger.

    Revalidates lifecycle and every provenance field at use time. The application
    must serialize ingestion/lifecycle mutations with retrieval and reranking,
    as required by Stage 3E's cross-ledger consistency model.
    """
    def __init__(self, store, service):
        if store.scope != service.scope:
            raise ValueError('scope mismatch')
        self.scope, self.store, self.service = store.scope, store, service

    def __call__(self, ref):
        if not isinstance(ref, EvidenceReference) or ref.scope != self.scope:
            raise ValueError('foreign reference')
        stored = self.store.get_embedding(ref.embedding_id)
        if stored is None or stored.state != 'active':
            raise ValueError('missing/stale evidence')
        citation = ChunkEmbedder(self.scope, None).resolve(stored.record, self.service)
        c = citation.chunk
        r = ChunkReference.from_citation(citation)
        expected = EvidenceReference(r.scope, stored.record.record_id, r.chunk_id, r.chunk_revision_id,
            r.evidence_id, r.source_id, r.evidence_version, r.source_type, citation.source.source_uri,
            c.evidence.locator, c.start, c.end, r.origin, r.trust, r.verification_state,
            r.support_ids, tuple((x.support.claim_id, x.support.support_id, x.support.relationship.value,
                                  x.containment.value) for x in c.claim_links),
            r.provenance_event_ids, EmbeddingSpace(stored.record.config, stored.record.input_strategy).space_id,
            stored.state)
        if ref != expected:
            raise ValueError('reference/provenance/semantic-space mismatch')
        return c.text

class ScopedReranker:
    def __init__(self, scope, response, provider, resolver):
        if not isinstance(scope, Scope) or not isinstance(response, RetrievalResponse):
            raise ValueError('typed scope and authentic retrieval response required')
        if resolver.scope != scope or not isinstance(provider.config, RerankerConfig):
            raise ValueError('scope/config mismatch')
        if response.query != construct(response.query.need, response.config.expansion):
            raise ValueError('query identity mismatch')
        if response.filters.state != 'active':
            raise ValueError('reranking requires active evidence')
        self.scope, self.response, self.provider, self.resolver = scope, response, provider, resolver
        self.config = provider.config
        self.allowed = {}
        spaces = set()
        for result in response.results:
            if not isinstance(result, RetrievalResult) or result.query_id != response.query.query_id:
                raise ValueError('query/result mismatch')
            if result.rank != len(self.allowed) + 1:
                raise ValueError('noncontiguous original ranking')
            for ref in (result.reference,) + result.corroborating_references:
                if ref.scope != scope or ref.lifecycle != 'active':
                    raise ValueError('foreign or inactive reference')
                spaces.add(ref.semantic_space_id)
            if result.reference.embedding_id in self.allowed:
                raise ValueError('duplicate candidate ID')
            if not math.isfinite(result.score) or (result.semantic_score is not None and not math.isfinite(result.semantic_score)):
                raise ValueError('invalid retrieval score')
            self.allowed[result.reference.embedding_id] = result
        if len(spaces) > 1:
            raise ValueError('mixed semantic spaces')

    def rerank(self, information_need, retrieval_results, top_n):
        if information_need != self.response.query.need:
            raise ValueError('need differs from retrieved need')
        if type(top_n) is not int or not 0 <= top_n <= 100:
            raise ValueError('top_n must be 0..100')
        rows = tuple(retrieval_results)
        if len(rows) > 100:
            raise ValueError('candidate budget exceeds Stage 3E maximum')
        seen = set()
        for row in rows:
            if not isinstance(row, RetrievalResult) or self.allowed.get(row.reference.embedding_id) != row:
                raise ValueError('unseen or modified retrieval result')
            if row.reference.embedding_id in seen:
                raise ValueError('repeated candidate')
            seen.add(row.reference.embedding_id)
        # Callers choose a subset, but cannot change the identity baseline tie order.
        rows = tuple(sorted(rows, key=lambda row: row.rank))
        if not rows or not top_n:
            return ()
        if self.provider.config != self.config:
            raise ValueError('provider configuration drift')
        pairs = []
        for row in rows:
            text = self.resolver(row.reference)
            for ref in row.corroborating_references:
                sibling = self.resolver(ref)
                if ' '.join(sibling.split()) != ' '.join(text.split()):
                    raise ValueError('corroboration is not an exact text group')
            pairs.append(build_input(information_need, text, self.config.input_strategy))
        scores = tuple(self.provider.score(tuple(pairs)))
        if self.provider.config != self.config or len(scores) != len(rows):
            raise ValueError('provider config/cardinality changed')
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in scores):
            raise ValueError('provider must return only finite positional scores')
        order = sorted(range(len(rows)), key=lambda i: (-scores[i], rows[i].rank, rows[i].reference.embedding_id))
        return tuple(RerankedEvidence(rows[i], information_need.requirement_id, rank, float(scores[i]),
                     self.config, len(rows), top_n, pairs[i].input_hash)
                     for rank, i in enumerate(order[:top_n], 1))
