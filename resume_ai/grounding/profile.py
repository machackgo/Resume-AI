"""Candidate evidence bank (schema v2) loaded from a JSON profile.

Adapted from the private Resume AI control center (resume_ai/evidence.py): the original module
hard-coded one real candidate's evidence; here the same schema is loaded from a file so the code
carries no personal data. See PROVENANCE.md.

Every evidence item carries provenance and exactly one status:
  VERIFIED     completed work supported by an inspected artifact (repository, document, live page)
  ATTESTED     completed work stated by the candidate, not independently re-checked
  IN_PROGRESS  ongoing work; may only be described as ongoing
  PLANNED      future direction; never presented as experience
  DISPUTED     conflicting sources; excluded from every document until resolved

Skills map to (status, [evidence ids]); the status drives match weight in matching.engine.
"""
import json
from dataclasses import dataclass, field

EVIDENCE_SCHEMA_VERSION = 2
STATUSES = ("VERIFIED", "ATTESTED", "IN_PROGRESS", "PLANNED", "DISPUTED")
USABLE_AS_FACT = {"VERIFIED", "ATTESTED"}
USABLE_IN_DOCUMENTS = {"VERIFIED", "ATTESTED", "IN_PROGRESS"}   # IN_PROGRESS only when labelled ongoing


@dataclass
class Profile:
    header: dict
    education: list
    roles: dict
    items: dict
    skills: dict
    banned_patterns: list = field(default_factory=list)
    allowed_numbers: list = field(default_factory=list)
    writing_rules: list = field(default_factory=list)
    gaps: list = field(default_factory=list)          # posting terms the candidate does not have
    hard_gaps: list = field(default_factory=list)     # subset of gaps that carry an extra match penalty

    def __post_init__(self):
        for k, v in self.items.items():
            if v.get("status") not in STATUSES:
                raise ValueError(f"evidence {k}: unknown status {v.get('status')}")
            if v.get("role") not in self.roles:
                raise ValueError(f"evidence {k}: unknown role {v.get('role')}")
            if not v.get("source"):
                raise ValueError(f"evidence {k}: provenance (source) is required")
        self.skills = {s: (st, list(ids)) for s, (st, ids) in self.skills.items()}
        for s, (st, ids) in self.skills.items():
            if st not in STATUSES:
                raise ValueError(f"skill {s}: unknown status {st}")
            missing = [i for i in ids if i not in self.items]
            if missing:
                raise ValueError(f"skill {s}: unknown evidence ids {missing}")

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        if d.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
            raise ValueError("unsupported profile schema version")
        return cls(d["header"], d["education"], d["roles"], d["items"], d["skills"], d.get("banned_patterns", []),
                   d.get("allowed_numbers", []), d.get("writing_rules", []), d.get("gaps", []), d.get("hard_gaps", []))

    # Same derived views as the original module.
    @property
    def evidence(self):
        return {k: (v["text"], v.get("tags", [])) for k, v in self.items.items() if v["status"] in USABLE_AS_FACT}

    @property
    def evidence_source(self):
        return {k: v["source"] for k, v in self.items.items()}

    @property
    def ongoing(self):
        return {k: v["text"] for k, v in self.items.items() if v["status"] == "IN_PROGRESS"}

    @property
    def verified_skills(self):
        return {s for s, (st, _) in self.skills.items() if st in USABLE_AS_FACT}
