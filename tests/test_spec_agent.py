"""Adapted from the private control center's tests/test_overnight.py: the model's output is never trusted without these checks."""
import copy

from resume_ai.agents import spec_agent as A


def test_valid_spec_passes(profile, good_spec):
    assert A.spec_issues(good_spec, "Applied AI Engineer", profile) == []


def test_rejects_unknown_or_planned_evidence_and_wrong_role(profile, good_spec):
    s = copy.deepcopy(good_spec)
    s["experience"] = [["LAB", ["L1", "ZZ9", "P1", "I1"]]]
    iss = " ".join(A.spec_issues(s, "", profile))
    assert "unknown evidence id ZZ9" in iss and "P1 is PLANNED" in iss and "I1 belongs to INTERN" in iss


def test_in_progress_skill_needs_ongoing_label_and_banned_claims_fail(profile, good_spec):
    s = copy.deepcopy(good_spec)
    s["skills"] = [["Machine learning", "LoRA, PyTorch, Python"]]
    s["cover_letter"] = s["cover_letter"][:3] + ["I hold a cloud certification and led a team."]
    iss = " ".join(A.spec_issues(s, "", profile))
    assert "lora" in iss and "pytorch" in iss and "banned claim" in iss


def test_linkedin_limit_and_missing_outreach(profile, good_spec):
    s = copy.deepcopy(good_spec)
    s["outreach"] = {"email": "x", "linkedin_connection": "y" * 301}
    iss = " ".join(A.spec_issues(s, "", profile))
    assert "over 300" in iss and "linkedin_followup missing" in iss


def test_extract_json():
    assert A.extract_json('text ```json\n{"a": 1}\n``` more ```json\n{"b": 2}\n```') == {"b": 2}
    assert A.extract_json('prefix {"c": 3} suffix') == {"c": 3}


def test_generate_spec_retries_with_validator_feedback(profile, good_spec):
    bad = dict(copy.deepcopy(good_spec), summary="Improved recall by 37% for 5,000 users.")
    prompts = []

    def llm(prompt):
        prompts.append(prompt)
        return {"kind": "ok", "json": [bad, good_spec][len(prompts) - 1]}
    r = A.generate_spec({"title": "x"}, "", profile, llm, max_attempts=2)
    assert r["ok"] and [a["kind"] for a in r["attempts"]] == ["invalid", "ok"]
    assert "REJECTED BY THE VALIDATOR" not in prompts[0] and "unverified number: 37" in prompts[1]


def test_generate_spec_gives_up_and_stops_on_usage_limit(profile):
    r = A.generate_spec({}, "", profile, lambda p: {"kind": "limit", "error": "usage limit"}, max_attempts=3)
    assert not r["ok"] and len(r["attempts"]) == 1


def test_cli_is_tool_restricted():
    cmd = A.ClaudeCLI(cwd=".").command()
    allowed = cmd[cmd.index("--allowedTools") + 1: cmd.index("--disallowedTools")]
    assert set(allowed) == {"Read", "Glob", "Grep", "WebSearch", "WebFetch"}
    assert {"Bash", "Write", "Edit"} <= set(cmd[cmd.index("--disallowedTools") + 1:])
