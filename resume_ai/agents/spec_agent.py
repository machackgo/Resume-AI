"""LLM tailoring agent: the model proposes, deterministic validators decide.

Adapted from the private Resume AI control center (resume_ai/overnight.py, its background model-task
runner). What is kept:
  * extract_json and spec_issues (the validation gate the model's output must pass) — logic unchanged,
    but evidence/roles/skills come from a Profile instead of module globals;
  * the prompt shape (evidence digest + hard rules + required output shape + optional validator feedback);
  * the tool-restricted Claude Code CLI invocation (read-only tool allowlist, write/exec tools denied, API-key
    variables removed from the child environment, hard timeout).
What changed:
  * candidate-specific writing rules removed; generic BASE_RULES plus Profile.writing_rules are used instead;
  * the retry-with-feedback cycle, which the original spreads across queued task attempts in SQLite
    (model_tasks), is condensed into generate_spec(); the LLM is any callable, so tests and the demo inject
    a deterministic mock instead of calling a model.

The model never writes files or tracker rows: it returns JSON, and only validated output is used.
Resume bullets are referenced by evidence id, never written by the model.
"""
import json
import os
import re
import signal
import subprocess

from ..grounding import validate
from ..grounding.profile import USABLE_IN_DOCUMENTS

ALLOWED_TOOLS = ["Read", "Glob", "Grep", "WebSearch", "WebFetch"]
DENIED_TOOLS = ["Bash", "Write", "Edit", "NotebookEdit", "Agent", "Task"]
LIMIT_RE = re.compile(r"usage limit|rate[ _-]?limit|limit (reached|exceeded)|out of (extra )?usage|hit your limit|429|quota", re.I)
BUSY_RE = re.compile(r"overloaded|529|503|timed? ?out|ECONN|network", re.I)


def extract_json(text):
    """Last ```json fenced block, else the outermost {...} in the text."""
    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text or "", re.S)
    cand = blocks[-1] if blocks else (text[text.find("{"): text.rfind("}") + 1] if text and "{" in text else "")
    return json.loads(cand)


# ---------------------------------------------------------------- validation (pure, unit tested)
def spec_issues(spec, jt, profile):
    issues = []
    for k in ("slug", "summary", "skills", "experience", "letter_heading", "cover_letter", "outreach"):
        if k not in spec:
            issues.append(f"missing key {k}")
    if issues:
        return issues
    if not re.fullmatch(r"[A-Za-z0-9_]{3,90}", spec["slug"]):
        issues.append("slug must be [A-Za-z0-9_]")
    for section in ("experience", "projects"):
        for role, ids in spec.get(section, []):
            if role not in profile.roles:
                issues.append(f"unknown role {role}")
                continue
            for i in ids:
                it = profile.items.get(i)
                if not it:
                    issues.append(f"unknown evidence id {i}")
                elif it["status"] not in USABLE_IN_DOCUMENTS:
                    issues.append(f"evidence {i} is {it['status']} — not usable")
                elif it["role"] != role:
                    issues.append(f"evidence {i} belongs to {it['role']}, not {role}")
    for label, val in spec["skills"]:
        low = val.lower()
        for skill, (st, _) in profile.skills.items():
            if re.search(r"(?<![\w-])" + re.escape(skill) + r"(?![\w-])", low):
                if st == "PLANNED":
                    issues.append(f"planned skill listed: {skill}")
                elif st == "IN_PROGRESS" and "ongoing" not in label.lower() and "in progress" not in label.lower():
                    issues.append(f"in-progress skill '{skill}' must sit under a label marked ongoing (label: {label})")
    if not isinstance(spec["cover_letter"], list) or not 3 <= len(spec["cover_letter"]) <= 5:
        issues.append("cover_letter must be 3-5 paragraphs")
    o = spec["outreach"]
    for k in ("email", "linkedin_connection", "linkedin_followup"):
        if not o.get(k):
            issues.append(f"outreach.{k} missing")
    if len(o.get("linkedin_connection", "")) > 300:
        issues.append("linkedin_connection over 300 characters")
    free = "\n".join([spec["summary"], *[v for _, v in spec["skills"]], *spec["cover_letter"], *[str(v) for v in o.values()]])
    issues += validate.check_document(free, profile, jt, "cover")
    issues += [f"answers: {x}" for x in validate.check_answers(spec.get("answers", []), profile, jt)]
    return issues


def evidence_digest(profile):
    items = {k: {"role": v["role"], "status": v["status"], "text": v["text"]}
             for k, v in profile.items.items() if v["status"] in USABLE_IN_DOCUMENTS}
    skills = {s: st for s, (st, _) in profile.skills.items() if st != "PLANNED"}
    return json.dumps({"header": profile.header, "education": profile.education, "roles": profile.roles,
                       "items": items, "skills_status": skills}, indent=1)


BASE_RULES = [
    "Use ONLY facts in the evidence digest. Never invent experience, employers, skills, metrics, numbers, dates or results.",
    'IN_PROGRESS items are ongoing work: any sentence using them must say "ongoing". Never present PLANNED work.',
    "Numbers may only be ones already in the evidence text or the job posting.",
    "Never name a technology the candidate lacks, not even to say it is missing; put such gaps in open_items only.",
    'Write plainly and specifically; no generic filler ("I am passionate", "dynamic", "synergy").',
]


def spec_prompt(job, profile, example=None, feedback=None):
    rules = "\n".join("- " + r for r in BASE_RULES + list(profile.writing_rules))
    return f"""You are preparing a job-application package for the candidate. Do not use any tool except Read, Glob, Grep,
WebSearch and WebFetch. Do not write files. Your final message must contain exactly one ```json block.

JOB (from the tracker; the posting is the authority):
{json.dumps(job, indent=1)[:6000]}

CANDIDATE EVIDENCE DIGEST:
{evidence_digest(profile)}

Hard rules (a validator rejects violations):
{rules}

Produce a spec with this exact shape:
- slug: Company_RoleShort (letters, digits, underscores)
- summary: 2-3 sentences, <= 60 words, tailored to this job
- skills: 4-7 [label, comma list] pairs; skills whose status is IN_PROGRESS go under a label containing "(ongoing)"
- experience: [[ROLE_KEY, [evidence ids]]] ordered by relevance
- projects: [[ROLE_KEY, [evidence ids]]]
- letter_heading: "Company — exact job title, location"
- cover_letter: 3-5 paragraphs
- answers: [[question, answer]] from the digest only; anything uncertain -> "FLAG FOR CANDIDATE"
- outreach: {{"email": "...", "linkedin_connection": "<= 280 characters", "linkedin_followup": "<= 400 characters"}} (drafts; never sent)
- open_items: list of things the candidate must confirm
""" + (f"\nEXAMPLE SPEC (different job):\n{json.dumps(example, indent=1)[:5000]}\n" if example else "") \
        + (f"\nYOUR PREVIOUS ATTEMPT WAS REJECTED BY THE VALIDATOR FOR: {feedback}\nFix every issue." if feedback else "")


def generate_spec(job, jt, profile, llm, max_attempts=2, example=None):
    """Ask the model for a spec; reject anything the validator flags and retry once with the issues as feedback.

    llm(prompt) -> {"kind": "ok", "json": {...}} | {"kind": "error"|"limit"|"busy", "error": str}
    Returns {"ok": bool, "spec": dict|None, "attempts": [{"attempt", "kind", "issues"}]}.
    """
    feedback, log = None, []
    for attempt in range(1, max_attempts + 1):
        res = llm(spec_prompt(job, profile, example, feedback))
        if res["kind"] != "ok":
            log.append({"attempt": attempt, "kind": res["kind"], "issues": [res.get("error", "")]})
            if res["kind"] == "limit":
                break                       # the original sleeps and re-queues; never retries in a loop
            feedback = res.get("error")
            continue
        issues = spec_issues(res["json"], jt, profile)
        log.append({"attempt": attempt, "kind": "ok" if not issues else "invalid", "issues": issues})
        if not issues:
            return {"ok": True, "spec": res["json"], "attempts": log}
        feedback = "; ".join(issues)[:600]
    return {"ok": False, "spec": None, "attempts": log}


class ClaudeCLI:
    """Tool-restricted `claude -p` call (Claude Code CLI). Only its command line is tested; it is never run by the tests or the demo."""

    def __init__(self, cwd, model=None, timeout_s=1500):
        self.cwd, self.model, self.timeout_s = cwd, model, timeout_s

    def command(self):
        cmd = ["claude", "-p", "--output-format", "json", "--setting-sources", "project", "--strict-mcp-config",
               "--no-session-persistence", "--allowedTools", *ALLOWED_TOOLS, "--disallowedTools", *DENIED_TOOLS]
        if self.model:
            cmd += ["--model", self.model]
        return cmd

    def __call__(self, prompt):
        env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
        p = subprocess.Popen(self.command(), cwd=self.cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            out, err = p.communicate(prompt, timeout=self.timeout_s)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGTERM)
            p.communicate()
            return {"kind": "error", "error": f"timed out after {self.timeout_s} s"}
        try:
            d = json.loads(out)
        except ValueError:
            d = {"is_error": True, "result": (out or "")[-800:]}
        text = d.get("result") or ""
        blob = f"{text}\n{err[-800:]}"
        if (d.get("is_error") or p.returncode) and LIMIT_RE.search(blob):
            return {"kind": "limit", "error": blob.strip()[:300]}
        if d.get("is_error") or p.returncode:
            return {"kind": "busy" if BUSY_RE.search(blob) else "error", "error": blob.strip()[:300]}
        try:
            return {"kind": "ok", "json": extract_json(text), "raw": text}
        except ValueError as e:
            return {"kind": "error", "error": f"no parsable JSON in reply ({e})"}
