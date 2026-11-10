"""Claim validator — every generated document must pass before it is saved as ready.

Adapted from the private Resume AI control center (resume_ai/validate.py, validator 2.0.0): the
banned-claim list, allowed numbers and evidence now come from a Profile instead of module globals.

Checks:
 1. banned claims (the profile's never-claim list, disputed claims, planned-only research terms)
 2. every number appears in the evidence bank, education block, header, allowed list or the job posting itself
 3. IN_PROGRESS evidence is labelled as ongoing wherever it appears
 4. no PLANNED item text appears at all
"""
import re

VALIDATOR_VERSION = "2.0.0"


def _base_allowed(profile):
    return " ".join(v["text"] for v in profile.items.values() if v["status"] not in ("PLANNED", "DISPUTED")) + " " + \
        " ".join(" ".join(str(x) for x in e.values()) for e in profile.education) + " " + \
        " ".join(str(v) for v in profile.header.values()) + " " + " ".join(profile.allowed_numbers)


def _num_ok(n, allowed):
    core = n.rstrip(".,)").lstrip("(")
    return core in allowed or core.replace(",", "") in allowed


def check_document(text, profile, job_text="", kind="resume"):
    issues = []
    for p in profile.banned_patterns:
        for m in re.finditer(p, text, re.I):
            sent = re.split(r"(?<=[.!?])\s+", text[max(0, m.start() - 200): m.end() + 120])
            ctx = next((x for x in sent if m.group(0) in x), "")
            honest_gap = re.search(r"\b(have not|haven't|not yet|no (prior )?experience|do not have|gap)\b", ctx, re.I)
            if honest_gap and job_text and re.search(p, job_text, re.I):
                continue  # explicit, truthful gap statement about a posting requirement
            issues.append(f"banned claim: '{m.group(0)}'")
            break
    allowed = _base_allowed(profile) + " " + job_text
    for n in sorted(set(re.findall(r"(?<![\w/])\d[\d,.]*\+?", text))):
        if not _num_ok(n, allowed):
            issues.append(f"unverified number: {n}")
    for k, v in profile.items.items():
        frag = v["text"][:60]
        if v["status"] == "PLANNED" and frag.lower() in text.lower():
            issues.append(f"planned item presented: {k}")
        if v["status"] == "IN_PROGRESS" and frag.lower() in text.lower():
            idx = text.lower().find(frag.lower())
            window = text[idx: idx + len(v["text"]) + 40].lower()
            if "ongoing" not in window and "in progress" not in window:
                issues.append(f"in-progress item {k} not labelled ongoing")
    return issues


PLACEHOLDER = re.compile(r"\s*(FLAG FOR CANDIDATE|NEEDS_USER_CONFIRMATION)\b.*", re.S)


def check_answers(qa, profile, job_text=""):
    """Answers to application questions. qa is a list of (question, answer) pairs or the saved "Q: …\nA: …" text.
    Only the candidate's answers are claims: the employer's question text is posting context, and
    FLAG FOR CANDIDATE / NEEDS_USER_CONFIRMATION placeholders say nothing."""
    if isinstance(qa, str):
        qa = re.findall(r"(?ms)^Q: (.*?)\nA: (.*?)(?=\n\s*\nQ: |\n?\Z)", qa)
    answers = "\n".join(str(a) for _, a in qa if not PLACEHOLDER.fullmatch(str(a)))
    return check_document(answers, profile, job_text + "\n" + "\n".join(str(q) for q, _ in qa), "answers")
