"""Stage 3A evidence ingestion. No embeddings, retrieval, prompts or model calls."""
from .domain import Scope
from .ingestion import MemoryLedger

__all__ = ["Scope", "MemoryLedger"]
