"""Scoped in-memory reuse only. No persistent vector storage or retrieval API."""
from dataclasses import replace
from ..domain import stable_id, now
from .input_builder import build_input
from .models import EmbeddingRecord


def cache_key(chunk, built, config):
    # Same semantic content can reuse computation within a scope; source-bound
    # record IDs remain separate. Never reuse across tenants or candidates.
    return stable_id('embedding_cache', 'stage3c-v1', chunk.scope.key,
                     built.strategy, built.input_hash, config.identity, 'document')


class ChunkEmbedder:
    def __init__(self, scope, provider, clock=now):
        self.scope, self.provider, self.clock = scope, provider, clock
        self._cache = {}

    def embed(self, chunks, strategy='raw-v1'):
        chunks = tuple(chunks)
        if any(c.scope != self.scope for c in chunks):
            raise ValueError('foreign candidate chunk')
        config = self.provider.config
        built = [build_input(c, strategy) for c in chunks]
        keys = [cache_key(c,b,config) for c,b in zip(chunks,built)]
        pending = dict((k,b.text) for k,b in zip(keys,built) if k not in self._cache)
        vectors = tuple(self.provider.embed_documents(tuple(pending.values()))) if pending else ()
        if len(vectors) != len(pending):
            raise ValueError('provider batch cardinality mismatch')
        fresh = dict(zip(pending, (tuple(v) for v in vectors)))
        records = []
        for c,b,k in zip(chunks,built,keys):
            vector = fresh[k] if k in fresh else self._cache[k]
            record_id = stable_id('embedding_record', c.scope.key, c.chunk_id, c.revision_id, k)
            records.append(EmbeddingRecord(record_id, k, c.scope, c.chunk_id, c.revision_id,
                c.evidence.evidence_id, c.evidence.source_id, c.evidence.version,
                c.policy.policy_id, config, b.strategy, b.input_hash, vector, self.clock(),
                c.evidence.origin.value, c.evidence.trust,
                tuple(link.support.support_id for link in c.claim_links),
                tuple(event.event_id for event in c.provenance_events)))
        if config != self.provider.config:
            raise ValueError('provider changed configuration during encoding')
        self._cache.update(fresh)  # publish only after every output validates
        return tuple(records)

    def resolve(self, record, chunk_service):
        if record.scope != self.scope or chunk_service.scope != self.scope:
            raise ValueError('foreign record/service')
        citation = chunk_service.cite(record.chunk_id, record.chunk_revision_id)
        c = citation.chunk
        b = build_input(c, record.input_strategy)
        expected = cache_key(c, b, record.config)
        if (record.cache_key != expected or record.input_hash != b.input_hash or
            record.record_id != stable_id('embedding_record', c.scope.key, c.chunk_id, c.revision_id, expected) or
            (record.evidence_id,record.source_id,record.evidence_version,record.policy_id,
             record.origin,record.trust,record.support_ids,record.provenance_event_ids) !=
            (c.evidence.evidence_id,c.evidence.source_id,c.evidence.version,c.policy.policy_id,
             c.evidence.origin.value,c.evidence.trust,tuple(x.support.support_id for x in c.claim_links),
             tuple(x.event_id for x in c.provenance_events))):
            raise ValueError('record reference mismatch')
        return citation
