"""Adapted from the private control center's tests/test_core.py (claim validation) and profile rules."""
import json

import pytest

from resume_ai.grounding import validate
from resume_ai.grounding.documents import build_package, docx_text
from resume_ai.grounding.profile import Profile


def test_validator(profile):
    assert validate.check_document("Capstone with 5,000 users on Kubernetes", profile)
    assert validate.check_document(profile.items["L1"]["text"], profile) == []
    assert any("unverified number" in i for i in validate.check_document("Improved accuracy by 37%", profile))
    assert validate.check_document(profile.items["D1"]["text"], profile)                 # disputed claim
    assert validate.check_document("I have not yet worked with Spark at scale.", profile, "Spark", "cover") == []
    unlabeled = profile.items["T1"]["text"].replace(" (ongoing)", "")
    assert any("not labelled ongoing" in i for i in validate.check_document(unlabeled, profile))
    assert any("planned item presented" in i for i in validate.check_document(profile.items["P1"]["text"], profile))


def test_numbers_from_posting_are_allowed(profile):
    assert validate.check_document("Your team ships 37 releases a year.", profile) != []
    assert validate.check_document("Your team ships 37 releases a year.", profile, "37 releases per year") == []


def test_check_answers_parses_saved_file_and_ignores_question_text(profile):
    saved = "Q: Proficiency in Kubernetes and C++\nA: FLAG FOR CANDIDATE\n\nQ: PhD advisor(s)\nA: NEEDS_USER_CONFIRMATION\n"
    assert validate.check_answers(saved, profile) == []
    assert validate.check_answers("Q: Platforms?\nA: I am an expert in Kubernetes.\n", profile)


def test_profile_rejects_missing_provenance(tmp_path, profile):
    bad = {"schema_version": 2, "header": profile.header, "education": [], "roles": profile.roles,
           "items": {"X": {"role": "LAB", "status": "VERIFIED", "source": "", "text": "x"}}, "skills": {}}
    p = tmp_path / "p.json"; p.write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="provenance"):
        Profile.load(p)


def test_package_bullets_only_from_evidence_and_validated_after_render(tmp_path, profile, good_spec):
    job = {"job_id": "FT001", "title": "Applied AI Engineer", "required": ["Python"], "key_tech": ["RAG"]}
    res, manifest = build_package(job, good_spec, profile, str(tmp_path))
    assert all(not v["issues"] for v in res.values()), {k: v["issues"] for k, v in res.items()}
    text = docx_text(res["resume"]["docx"])
    for i in manifest["evidence_ids"]:
        assert profile.items[i]["text"] in text
    assert "Kubernetes" not in text and profile.items["P1"]["text"] not in text
