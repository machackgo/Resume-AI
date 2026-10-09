"""Stage 3B only: deterministic evidence views, no embeddings or retrieval."""
from .chunker import CandidateChunks, EvidenceRepository, spans
from .models import BoundaryHint, Citation, Containment, RetrievalChunk
from .policy import ChunkPolicy, POLICY_A, POLICY_B

__all__ = ['CandidateChunks', 'EvidenceRepository', 'spans', 'BoundaryHint', 'Citation',
           'Containment', 'RetrievalChunk', 'ChunkPolicy', 'POLICY_A', 'POLICY_B']
