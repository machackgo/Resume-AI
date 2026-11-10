import json
from pathlib import Path

import pytest

from resume_ai.grounding.profile import Profile

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def profile():
    return Profile.load(EXAMPLES / "profile_alex_rivera.json")


@pytest.fixture
def postings():
    return json.loads((EXAMPLES / "jobs" / "postings.json").read_text())


@pytest.fixture
def good_spec():
    return json.loads((EXAMPLES / "specs" / "globex_mock_llm_replies.json").read_text())["attempts"][1]
