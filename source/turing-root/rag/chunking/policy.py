"""Versioned, provider-independent sizing and boundary behavior."""
from dataclasses import asdict, dataclass
from typing import Protocol
from ..domain import stable_id


class Sizer(Protocol):
    """Trusted application code. prefix_end returns a fitting Unicode boundary.

    Token implementations must pin tokenizer assets/revision and implement exact
    counting and prefix selection; counts need not be additive or monotonic.
    """
    identity: str
    unit: str
    def count(self, text: str) -> int: ...
    def prefix_end(self, text: str, start: int, limit: int) -> int: ...


@dataclass(frozen=True)
class CharacterSizer:
    identity: str = 'unicode-codepoints-v1'
    unit: str = 'characters'
    def count(self, text: str) -> int:
        return len(text)
    def prefix_end(self, text: str, start: int, limit: int) -> int:
        return min(len(text), start + limit)


@dataclass(frozen=True)
class ChunkPolicy:
    name: str = 'moderate'
    version: str = '1'
    max_size: int = 640
    overlap: int = 96
    unit: str = 'characters'
    sizer_identity: str = 'unicode-codepoints-v1'
    boundary_version: str = 'structural-v1'
    minimum_fill_percent: int = 50
    schema_version: int = 1

    def __post_init__(self):
        if not all(isinstance(x, str) and x.strip() for x in
                   (self.name, self.version, self.unit, self.sizer_identity)):
            raise ValueError('policy identity fields must be nonempty')
        if self.boundary_version != 'structural-v1' or self.schema_version != 1:
            raise ValueError('unsupported policy behavior/schema')
        if (type(self.max_size) is not int or self.max_size < 1 or
            type(self.overlap) is not int or not 0 <= self.overlap < self.max_size or
            type(self.minimum_fill_percent) is not int or not 1 <= self.minimum_fill_percent <= 100):
            raise ValueError('invalid size/overlap/fill')

    @property
    def policy_id(self):
        return stable_id('chunk_policy', asdict(self))


POLICY_A = ChunkPolicy(name='small', max_size=320, overlap=48)
POLICY_B = ChunkPolicy()
