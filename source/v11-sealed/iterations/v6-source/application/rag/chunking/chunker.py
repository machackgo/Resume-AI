"""Lossless structural chunking and scoped citation resolution (CPU only)."""
from dataclasses import asdict, replace
import re
from typing import Protocol
from ..domain import (Claim, Evidence, IngestionEvent, Scope, Source, Support,
                      canonical, digest, stable_id)
from .models import BoundaryHint, ChunkClaimLink, Citation, Containment, RetrievalChunk
from .policy import CharacterSizer, ChunkPolicy, Sizer


class EvidenceRepository(Protocol):
    scope: Scope
    def evidence(self, evidence_id: str) -> Evidence: ...
    def source(self, source_id: str) -> Source: ...
    def content(self, reference: str) -> bytes: ...
    def claims(self) -> tuple[Claim, ...]: ...
    def support(self, support_id: str) -> Support: ...
    def supports(self, claim_id: str) -> tuple[Support, ...]: ...
    def history(self, source_id: str) -> tuple[IngestionEvent, ...]: ...
    def current(self, source_id: str) -> Evidence | None: ...


def boundaries(text, hints=(), supports=()):
    """Priorities: supplied structures/claims, paragraphs, sentences, words.

    Fenced blocks and heading+following line are soft indivisible spans. Oversize
    structures yield to the hard size cap; no text is stripped or reconstructed.
    """
    points = {0: 5, len(text): 5}
    protected = [(h.start, h.end) for h in hints]
    def add(at, rank):
        points[at] = max(points.get(at, 0), rank)
    for h in hints:
        if h.end > len(text):
            raise ValueError('hint outside evidence')
        add(h.start, 5); add(h.end, 5)
    for s in supports:
        p = s.pointer
        protected.append((p.start, p.end))
        add(p.start, 5); add(p.end, 5)
    for m in re.finditer(r'(?m)^([ \t]*)(```|~~~)[^\n]*\n', text):
        close = re.search(r'(?m)^[ \t]*' + re.escape(m[2]) + r'[^\n]*(?:\n|$)', text[m.end():])
        end = m.end() + close.end() if close else len(text)
        # Ignore closing fences already inside a recognized block.
        if not any(a <= m.start() < b for a, b in protected):
            protected.append((m.start(), end)); add(m.start(), 4); add(end, 4)
    for m in re.finditer(r'\n[ \t]*\n+', text):
        add(m.end(), 4)
    for m in re.finditer(r'(?m)^#{1,6}[ \t]+[^\n]*\n(?:[^\n]+(?:\n|$))?', text):
        protected.append((m.start(), m.end())); add(m.start(), 4); add(m.end(), 4)
    for m in re.finditer(r'(?m)^[ \t]*(?:[-*+] |\d+[.)] )[^\n]*(?:\n|$)', text):
        protected.append((m.start(), m.end())); add(m.start(), 3); add(m.end(), 3)
    for m in re.finditer(r'[.!?](?:[ \t]+|\n+)', text):
        add(m.end(), 2)
    for m in re.finditer(r'\s+', text):
        add(m.end(), 1)
    return points, protected


def spans(text: str, policy: ChunkPolicy, hints=(), supports=(), sizer: Sizer | None = None):
    """Exact covering spans; pure whitespace has no retrieval chunks.

    Overlap uses existing structural/word boundaries, is at most the configured
    budget, and may be zero. Forward progress is mandatory even with huge overlap.
    """
    sizer = sizer or CharacterSizer()
    if (sizer.identity, sizer.unit) != (policy.sizer_identity, policy.unit):
        raise ValueError('sizer does not match pinned policy')
    if not isinstance(text, str):
        raise ValueError('text required')
    points, protected = boundaries(text, hints, supports)
    if not text.strip():
        return ()
    def count(value):
        result = sizer.count(value)
        if type(result) is not int or result < 0 or (value and result == 0):
            raise ValueError('invalid sizer count')
        return result
    start, previous_end, result = 0, 0, []
    while start < len(text):
        cap = sizer.prefix_end(text, start, policy.max_size)
        if type(cap) is not int or not start < cap <= len(text) or count(text[start:cap]) > policy.max_size:
            raise ValueError('invalid sizer prefix')
        if cap <= previous_end:
            start = previous_end
            continue
        fitting = [p for p in points if previous_end < p <= cap and p > start
                   and count(text[start:p]) <= policy.max_size]
        safe = [p for p in fitting if not any(a < p < b for a, b in protected)]
        # Preserve an atomic span if it fits in a fresh chunk but not this one.
        ends = [a for a, b in protected if start < a <= cap < b
                and a > previous_end and count(text[a:b]) <= policy.max_size]
        if cap == len(text):
            end = cap
        elif ends:
            end = min(ends)
        else:
            filled = [p for p in safe if count(text[start:p]) * 100 >=
                      policy.max_size * policy.minimum_fill_percent]
            pool = filled or safe or fitting
            end = max(pool, key=lambda p: (points[p], p)) if pool else cap
        result.append((start, end))
        if end == len(text):
            break
        candidates = [p for p in points if start < p < end
                      and count(text[p:end]) <= policy.overlap
                      and not any(a < p < b for a, b in protected)]
        next_start = min(candidates) if candidates else end
        previous_end, start = end, next_start
    return tuple(result)


class CandidateChunks:
    """Scoped in-memory reference API; scope must be bound by authenticated caller.

    Stable chunk identity is separate from append-only annotation/event revisions.
    Regeneration can incorporate new support links without losing old views.
    """
    def __init__(self, repository: EvidenceRepository):
        if not isinstance(repository.scope, Scope):
            raise ValueError('scoped repository required')
        self._repo = repository
        self._views = {}
        self._latest = {}

    @property
    def scope(self):
        return self._repo.scope

    def _evidence_text(self, evidence_id):
        evidence = self._repo.evidence(evidence_id)
        if evidence.scope != self.scope:
            raise KeyError(evidence_id)
        blob = self._repo.content(evidence.normalized_ref)
        if digest(blob) != evidence.normalized_hash:
            raise ValueError('evidence content hash mismatch')
        return evidence, blob.decode('utf-8')

    def generate(self, evidence_id: str, policy: ChunkPolicy = ChunkPolicy(),
                 hints: tuple[BoundaryHint, ...] = (), sizer: Sizer | None = None,
                 support_ids: tuple[str, ...] | None = None):
        e, text = self._evidence_text(evidence_id)
        hints = tuple(sorted(set(hints)))
        supports = tuple(sorted((s for c in self._repo.claims() for s in self._repo.supports(c.claim_id)
                                if s.pointer.evidence_id == evidence_id), key=lambda s: s.support_id))
        if support_ids is not None:
            supports = tuple(self._repo.support(key) for key in sorted(set(support_ids)))
        input_support_ids = tuple(s.support_id for s in supports)
        for s in supports:
            p = s.pointer
            if s.scope != self.scope or p.evidence_id != evidence_id or not 0 <= p.start < p.end <= len(text) or text[p.start:p.end] != p.quote:
                raise ValueError('invalid scoped support pointer')
        events = self._repo.history(e.source_id)
        if any(event.scope != self.scope for event in events):
            raise ValueError('foreign provenance event')
        sizer = sizer or CharacterSizer()
        output = []
        for start, end in spans(text, policy, hints, supports, sizer):
            links = tuple(ChunkClaimLink(s,
                          Containment.FULLY_CONTAINED if start <= s.pointer.start and s.pointer.end <= end
                          else Containment.PARTIALLY_OVERLAPPING,
                          max(start, s.pointer.start), min(end, s.pointer.end))
                          for s in supports if s.pointer.start < end and s.pointer.end > start)
            chunk_id = stable_id('chunk', 'stage3b-v1', self.scope.key, e.evidence_id,
                                 e.version, policy.policy_id, [asdict(h) for h in hints], start, end)
            revision_id = stable_id('chunk_revision', chunk_id, input_support_ids,
                                    [asdict(link) for link in links], [asdict(event) for event in events])
            output.append(RetrievalChunk(chunk_id, revision_id, e, policy, hints, input_support_ids, start, end,
                                         text[start:end], sizer.count(text[start:end]), links, events))
        # Publish only after complete validation/generation.
        for chunk in output:
            self._views[(chunk.chunk_id, chunk.revision_id)] = chunk
            self._latest[chunk.chunk_id] = chunk.revision_id
        return tuple(output)

    def fit_for_embedding(self, chunks, provider, strategy='title-section-v1'):
        """Split only overflowing chunks; exact Unicode spans and old fitting IDs survive.

        Budget includes provider prefix, title, section, and special tokens. No
        embedding truncation or whole-source rollback for a repairable overflow.
        """
        from ..embeddings.input_builder import build_input
        output = []
        def size(c):
            text = provider.config.document_prefix + build_input(c, strategy).text
            return len(provider.tokenizer(text, add_special_tokens=True)['input_ids'])
        for parent in chunks:
            if parent.scope != self.scope:
                raise ValueError('foreign candidate chunk')
            if size(parent) <= provider.max_tokens:
                output.append(parent)
                continue
            policy = replace(parent.policy, name='embedding-aware', version='2:' + provider.config.identity)
            offset = 0
            while offset < len(parent.text):
                lo, hi, best = offset + 1, len(parent.text), None
                while lo <= hi:
                    mid = (lo + hi) // 2
                    probe = replace(parent, text=parent.text[offset:mid])
                    if size(probe) <= provider.max_tokens:
                        best = mid; lo = mid + 1
                    else:
                        hi = mid - 1
                if best is None:
                    raise ValueError('embedding metadata leaves no room for one character')
                # Prefer a word boundary while retaining at least half the span.
                if best < len(parent.text):
                    split = max(parent.text.rfind(' ', offset, best), parent.text.rfind('\n', offset, best))
                    if split > (offset + best) // 2:
                        best = split + 1
                start, end = parent.start + offset, parent.start + best
                links = tuple(replace(link,
                    containment=Containment.FULLY_CONTAINED if start <= link.support.pointer.start and link.support.pointer.end <= end else Containment.PARTIALLY_OVERLAPPING,
                    overlap_start=max(start, link.support.pointer.start), overlap_end=min(end, link.support.pointer.end))
                    for link in parent.claim_links if link.support.pointer.start < end and link.support.pointer.end > start)
                cid = stable_id('chunk', 'embedding-fit-v1', self.scope.key, parent.evidence.evidence_id,
                                policy.policy_id, strategy, start, end)
                revision = stable_id('chunk_revision', cid, parent.input_support_ids,
                                    [asdict(link) for link in links], [asdict(e) for e in parent.provenance_events])
                child = replace(parent, chunk_id=cid, revision_id=revision, policy=policy,
                    start=start, end=end, text=parent.text[offset:best], measured_size=best-offset, claim_links=links)
                if size(child) > provider.max_tokens:
                    raise ValueError('embedding fit invariant')
                output.append(child)
                offset = best
        # Publish only after the complete source has been fitted and validated.
        for c in output:
            self._views[(c.chunk_id,c.revision_id)] = c
            self._latest[c.chunk_id] = c.revision_id
        return tuple(output)

    def get(self, chunk_id: str, revision_id: str | None = None) -> RetrievalChunk:
        revision_id = revision_id or self._latest[chunk_id]
        chunk = self._views[(chunk_id, revision_id)]
        if chunk.scope != self.scope:
            raise KeyError(chunk_id)
        self._repo.evidence(chunk.evidence.evidence_id)  # Scoped authoritative read.
        return chunk

    def cite(self, chunk_id: str, revision_id: str | None = None) -> Citation:
        chunk = self.get(chunk_id, revision_id)
        e, text = self._evidence_text(chunk.evidence.evidence_id)
        if e != chunk.evidence or text[chunk.start:chunk.end] != chunk.text:
            raise ValueError('citation no longer matches immutable evidence')
        source = self._repo.source(e.source_id)
        if source.scope != self.scope:
            raise KeyError(source.source_id)
        current = self._repo.current(e.source_id)
        state = 'deleted' if current is None else 'current' if current.evidence_id == e.evidence_id else 'superseded'
        return Citation(chunk, source, current.evidence_id if current else None, state,
                        self._repo.history(e.source_id) != chunk.provenance_events)

    def untrusted_envelope(self, chunk_id: str, revision_id: str | None = None) -> str:
        chunk = self.get(chunk_id, revision_id)
        return canonical({'schema_version': 1, 'trust': chunk.evidence.trust,
                          'tenant_id': self.scope.tenant_id, 'candidate_id': self.scope.candidate_id,
                          'chunk': asdict(chunk)})
