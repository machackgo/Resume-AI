from typing import Protocol, Sequence, runtime_checkable
from .models import EmbeddingConfig


@runtime_checkable
class EmbeddingProvider(Protocol):
    @property
    def config(self) -> EmbeddingConfig: ...
    def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...
    def embed_queries(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...
