"""Raw paired text; no identities, trust flags, titles or evaluation labels."""
from dataclasses import dataclass
from ..domain import canonical, digest, required
from ..retrieval.models import InformationNeed

VERSION = 'need-evidence-v1'

@dataclass(frozen=True)
class RerankerInput:
    query: str
    evidence: str
    strategy: str = VERSION
    @property
    def input_hash(self):
        return digest(canonical([self.strategy, self.query, self.evidence]).encode())

def build_input(need, evidence_text, strategy=VERSION):
    if not isinstance(need, InformationNeed) or strategy != VERSION:
        raise ValueError('typed need and known input strategy required')
    required(evidence_text, 'evidence text')
    # Preserve punctuation, quantities, negations, versions and malicious text verbatim.
    return RerankerInput(need.text, evidence_text)
