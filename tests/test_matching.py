"""Adapted from the private control center's tests/test_core.py (matching section), on the synthetic profile."""
from resume_ai.matching import engine


def test_matching_weights_and_gaps(profile):
    s_k8s, ex = engine.skill_match({"title": "ML Platform Engineer", "key_tech": ["Kubernetes", "C++", "Distributed training", "Python"],
                                    "required_qualifications": ["Production Kubernetes", "Multi-node distributed training", "C++"]}, profile.skills, profile.gaps, profile.hard_gaps)
    assert s_k8s < 40 and "kubernetes (required)" in ex["gaps"]
    s_llm, ex2 = engine.skill_match({"title": "LLM Engineer", "key_tech": ["LLM", "LoRA", "Python", "FastAPI"],
                                     "required_qualifications": ["Python", "LLM"]}, profile.skills, profile.gaps, profile.hard_gaps)
    assert "llm" in ex2["in_progress"] and "python" in ex2["verified"] and 60 < s_llm < 100
    s_rl, ex3 = engine.skill_match({"title": "RL Engineer", "key_tech": ["Reinforcement learning", "RLHF"],
                                    "required_qualifications": []}, profile.skills, profile.gaps, profile.hard_gaps)
    assert ex3["planned"] and s_rl == 0


def test_known_skill_missing_from_profile_is_a_gap(profile):
    _, ex = engine.skill_match({"title": "x", "key_tech": ["Vector databases", "Python"]}, profile.skills, profile.gaps, profile.hard_gaps)
    assert "vector databases" in ex["gaps"]


def test_research_requirement_penalised(profile):
    base, _ = engine.skill_match({"title": "x", "key_tech": ["Python", "RAG"], "required_qualifications": ["Python"]}, profile.skills, profile.gaps, profile.hard_gaps)
    req, ex = engine.skill_match({"title": "x", "key_tech": ["Python", "RAG"],
                                  "required_qualifications": ["Python", "PhD required"]}, profile.skills, profile.gaps, profile.hard_gaps)
    assert req < base and "research/publication track record (required)" in ex["gaps"]


def test_experience_level():
    assert engine.experience_check({"required_qualifications": ["3+ years experience"], "title": "Engineer"})["ok"] is False
    assert engine.experience_check({"required_qualifications": [], "title": "Software Engineer, New Grad"})["ok"] is True


def test_canonical_url_and_fingerprint(postings):
    a, dup = postings[0], postings[3]
    assert engine.canonical_url(a["posting_url"]) == engine.canonical_url(dup["posting_url"])
    assert engine.fingerprint(a) == engine.fingerprint(dict(a, title=a["title"].upper()))


def test_family_and_priority():
    assert engine.pick_family({"title": "LLM Agents Engineer"}) == 3
    assert engine.pick_family({"title": "MLOps Engineer"}) == 6
    assert engine.priority({}, 80) == 80
    assert engine.priority({}, 80, deadline_days=5) == 90


def test_gaps_come_from_the_profile(profile):
    job = {"title": "x", "key_tech": ["Kubernetes", "Python"], "required_qualifications": ["Kubernetes"]}
    _, declared = engine.skill_match(job, profile.skills, profile.gaps, profile.hard_gaps)
    _, undeclared = engine.skill_match(job, profile.skills)
    assert "kubernetes (required)" in declared["gaps"]
    assert "kubernetes" in undeclared["unassessed"] and not undeclared["gaps"]   # no hard-coded gap list
