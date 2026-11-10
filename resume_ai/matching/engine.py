"""Matching, family selection and de-duplication — engine v2.

Adapted from the private Resume AI control center (resume_ai/engine.py, engine 2.1.0):
  * skill_match takes the candidate's skill map and declared gaps (Profile.skills, Profile.gaps,
    Profile.hard_gaps) instead of hard-coded tables; the original known-gap list is removed;
  * candidate-specific eligibility rules removed; priority() no longer takes an eligibility class.

Every decision returns its reasons so a reviewer can see why a job scored as it did.
"""
import hashlib
import re
from urllib.parse import urlparse, parse_qs

ENGINE_VERSION = "2.1.0-showcase"
WEIGHT = {"VERIFIED": 1.0, "ATTESTED": 1.0, "IN_PROGRESS": 0.5, "PLANNED": 0.0}
USABLE_AS_FACT = {"VERIFIED", "ATTESTED"}

# posting term -> canonical skill name (generic vocabulary). Whether the candidate has it comes from Profile.skills.
ALIASES = {
    "python": "python", "sql": "sql", "typescript": "typescript", "javascript": "javascript", "js": "javascript",
    "fastapi": "fastapi", "asyncio": "asyncio", "async programming": "asyncio", "react": "react", "next.js": "next.js",
    "postgresql": "postgresql", "postgres": "postgresql", "mysql": "sql", "relational databases": "postgresql",
    "ci/cd": "ci/cd", "git": "git", "cloud": "cloud",
    "aws": "cloud", "gcp": "cloud", "llm": "llm", "llms": "llm", "large language models": "llm", "transformers": "transformers",
    "hugging face": "hugging face", "machine learning": "machine learning", "ml": "machine learning", "nlp": "nlp",
    "computer vision": "computer vision", "classifiers": "machine learning", "recsys": "recommendation systems",
    "recommendation": "recommendation systems", "scikit-learn": "scikit-learn", "lightgbm": "lightgbm", "pandas": "pandas",
    "numpy": "pandas", "statistics": "model evaluation", "model evaluation": "model evaluation", "evaluation": "evals",
    "evals": "evals", "llm evals": "evals", "llm-as-judge": "evals", "eval frameworks": "evals", "benchmarks": "evals",
    "agents": "agents", "llm agents": "agents", "ai agents": "agents", "agentic workflows": "agents", "agentic ai": "agents",
    "coding agents": "agents", "agent runtime": "agents", "tool calling": "tool calling", "function calling": "tool calling",
    "rag": "rag", "retrieval": "rag", "embeddings": "embeddings", "vector db": "vector db", "vector databases": "vector db",
    "pgvector": "pgvector", "reranking": "reranking", "semantic search": "rag", "prompt engineering": "prompt design",
    "structured outputs": "structured outputs", "speech": "speech-to-text", "speech-to-text": "speech-to-text",
    "pytorch": "pytorch", "deep learning": "pytorch", "quantization": "quantization", "llm inference": "llm inference",
    "inference": "llm inference", "lora": "lora", "qlora": "qlora", "fine-tuning": "fine-tuning", "fine-tuned model": "fine-tuning",
    "linux": "linux", "slurm": "slurm", "gpu": "gpu", "cuda": "cuda", "hpc": "hpc", "profiling": "profiling",
    "monitoring": "monitoring", "observability": "monitoring", "mlops": "mlops", "testing": "pytest", "e2e": "e2e testing",
    "mlllm": "llm", "mllms": "llm", "sft": "fine-tuning", "instruction tuning": "fine-tuning", "post-training": "fine-tuning",
    "rlhf": "rlhf", "reinforcement learning": "reinforcement learning", "preference alignment": "rlhf", "distillation": "distillation",
}
RESEARCH_REQ = re.compile(r"research track record|publications? (required|in)|phd required|top-tier .*publications? required", re.I)
RESEARCH_PREF = re.compile(r"publication|phd|neurips|icml|conference paper", re.I)


def _term_present(term, text):
    return re.search(r"(?<![\w+])" + re.escape(term) + r"(?![\w+])", text) is not None


def skill_match(job, skills, gaps=(), hard_gaps=()):
    """Return (score 0-100, explanation dict). Score weights evidence status; gaps are explicit.

    A term is a gap when it maps to a canonical skill the profile does not list, or when the profile declares it
    in `gaps`. `hard_gaps` (a subset the profile declares) carry the extra penalty. Other terms are unassessed."""
    gaps = {g.lower() for g in gaps}
    hard_gaps = {g.lower() for g in hard_gaps}
    vocabulary = list(ALIASES) + sorted(gaps - set(ALIASES))
    terms = [t.strip().lower() for t in job.get("key_tech", [])]
    req_text = " ".join(job.get("required_qualifications", [])).lower()
    pref_text = " ".join(job.get("preferred_qualifications", [])).lower()
    for t in vocabulary:
        if _term_present(t, req_text) and t not in terms:
            terms.append(t)
    required_terms = {t for t in terms if _term_present(t, req_text)}
    satisfied_alts = set()
    for req in job.get("required_qualifications", []) + job.get("preferred_qualifications", []):
        rl = req.lower()
        if not re.search(r"\bor\b|/|,", rl):
            continue
        group = [t for t in vocabulary if _term_present(t, rl)]
        if any(ALIASES.get(t) and WEIGHT[skills.get(ALIASES[t], ("PLANNED",))[0]] == 1.0 for t in group):
            satisfied_alts.update(t for t in group if ALIASES.get(t) is None or skills.get(ALIASES[t], ("",))[0] not in USABLE_AS_FACT)
    ex = {"verified": [], "in_progress": [], "planned": [], "gaps": [], "unassessed": [], "evidence_ids": set()}
    got = total = 0.0
    for t in dict.fromkeys(terms):
        if t in satisfied_alts:
            continue
        canon = None if t in gaps else ALIASES.get(t, t if t in skills else "?")
        if canon not in (None, "?") and canon not in skills:
            canon = None                       # a known skill the profile does not list is a gap
        w_req = 1.5 if t in required_terms else 1.0
        if canon == "?":
            ex["unassessed"].append(t); total += 0.5 * w_req; continue
        total += w_req
        if canon is None:
            ex["gaps"].append(t + (" (required)" if t in required_terms else ""))
            continue
        status, ids = skills[canon]
        got += WEIGHT[status] * w_req
        ex["evidence_ids"].update(ids)
        key = {"VERIFIED": "verified", "ATTESTED": "verified", "IN_PROGRESS": "in_progress", "PLANNED": "planned"}[status]
        ex[key].append(t)
    score = 100 * got / total if total else 50
    hard = [g for g in ex["gaps"] if g.split(" (")[0] in hard_gaps]
    score -= sum(10 if g.endswith("(required)") else 4 for g in hard)
    if RESEARCH_REQ.search(req_text):
        score -= 30; ex["gaps"].append("research/publication track record (required)")
    elif RESEARCH_PREF.search(pref_text):
        score -= 6; ex["gaps"].append("publications/PhD (preferred only)")
    if total < 5:
        score = min(score, 78); ex["thin_posting"] = True
    ex["experience"] = experience_check(job)
    if ex["experience"]["ok"] is False:
        score -= 20
    ex["evidence_ids"] = sorted(ex["evidence_ids"])
    return max(0, min(100, round(score))), ex


def experience_check(job):
    t = " ".join(job.get("required_qualifications", []) + [job.get("seniority", ""), job.get("title", "")]).lower()
    m = re.search(r"(\d+)\+?\s*(?:-\s*\d+\s*)?years?", t)
    if re.search(r"new grad|graduate|university grad|0-1 years|0-2|emerging talent|entry", t):
        return {"ok": True, "reason": "Early-career / new-grad level."}
    if m and int(m.group(1)) >= 2:
        return {"ok": False, "reason": f"Asks for {m.group(1)}+ years."}
    if m and int(m.group(1)) == 1:
        return {"ok": None, "reason": "Asks for 1+ year; internship and project work may count — confirm."}
    return {"ok": None, "reason": "Experience level not stated."}


FAMILIES = {1: "Software Engineer (Backend)", 3: "Generative AI and LLM Engineer", 4: "Applied AI Engineer",
            5: "AI and Machine Learning Engineer", 6: "MLOps and ML Platform Engineer", 8: "LLM Systems and Research Engineer"}


def pick_family(job):
    t = (job["title"] + " " + job.get("category", "") + " " + " ".join(job.get("key_tech", []))).lower()
    if re.search(r"research|infra|post-training|foundation model|evaluation", t):
        return 8
    if re.search(r"mlops|ml platform|sre", t):
        return 6
    if re.search(r"llm|generative|genai|rag|forward deployed|agent|conversational", t):
        return 3
    if re.search(r"applied ai|ai engineer|ai software", t):
        return 4
    if re.search(r"machine learning|ml engineer|data scientist", t):
        return 5
    return 1


def canonical_url(url):
    u = urlparse(url.strip())
    q = parse_qs(u.query)
    gh = f"?gh_jid={q['gh_jid'][0]}" if "gh_jid" in q else ""
    return f"{u.netloc.lower().removeprefix('www.')}{u.path.rstrip('/')}{gh}"


def fingerprint(job):
    title = re.sub(r"[^a-z0-9]+", " ", job["title"].lower()).strip()
    return hashlib.sha1(f"{job['company'].lower()}|{title}|{job.get('country','').lower()}".encode()).hexdigest()[:12]


def priority(job, score, deadline_days=None):
    """Match score plus a bonus for a deadline within three weeks."""
    p = score
    if deadline_days is not None and 0 <= deadline_days <= 21:
        p += 10
    return round(p)
