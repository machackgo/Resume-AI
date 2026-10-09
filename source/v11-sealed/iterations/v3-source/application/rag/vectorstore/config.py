"""No credentials or hard-coded user paths. Local filesystem only for live SQLite."""
from dataclasses import dataclass
import os
from pathlib import Path

@dataclass(frozen=True)
class StoreConfig:
    root: Path
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls):
        value = os.environ.get('RESUME_AI_VECTOR_ROOT')
        if not value: raise ValueError('RESUME_AI_VECTOR_ROOT must name a private local directory')
        return cls(Path(value))

    def __post_init__(self):
        if self.timeout_seconds <= 0: raise ValueError('positive timeout required')
        object.__setattr__(self, 'root', Path(self.root).expanduser().absolute())
