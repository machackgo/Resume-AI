"""Adapted from the private control center's tests/test_core.py (dedupe, approval boundaries, history, recovery, migration)."""
import sqlite3

import pytest

import subprocess
import sys
from pathlib import Path

from resume_ai.tracking.tracker import MIGRATIONS, CandidateOnlyStatus, Tracker


def fresh(tmp_path, profile):
    return Tracker(str(tmp_path / "t.db"), profile=profile)


def test_ingest_and_dedupe(tmp_path, profile, postings):
    t = fresh(tmp_path, profile)
    created = [t.ingest(j)[1] for j in postings]
    assert created == [True, True, True, False]            # the fourth posting is a tracking-parameter repost
    v = dict(postings[0], posting_url="https://example.com/other", title=postings[0]["title"].upper())
    assert t.ingest(v)[1] is False                          # same company+title+country, different URL
    assert len(t.query()) == 3


def test_no_unauthorized_submission_and_no_duplicates(tmp_path, profile, postings):
    t = fresh(tmp_path, profile); jid, _ = t.ingest(postings[0])
    for s in ("submitted", "approved"):
        with pytest.raises(CandidateOnlyStatus):
            t.set(jid, application_status=s)
    with pytest.raises(sqlite3.IntegrityError):              # database-level guard (migration 9)
        t.db.execute("UPDATE jobs SET application_status='submitted' WHERE job_id=?", (jid,))
    with pytest.raises(sqlite3.IntegrityError):
        t.mark_submitted(jid, "ref-1")                      # no candidate approval
    t.record_approval(jid, "submit", "approved", "agent", "test")
    with pytest.raises(sqlite3.IntegrityError):
        t.mark_submitted(jid, "ref-1")                      # agent approval is not enough
    t.record_approval(jid, "submit", "approved", "candidate", "dashboard")
    t.mark_submitted(jid, "ref-1")
    with pytest.raises(sqlite3.IntegrityError):
        t.mark_submitted(jid, "ref-2")                      # duplicate submission


def test_history_is_append_only(tmp_path, profile, postings):
    t = fresh(tmp_path, profile); t.ingest(postings[0])
    for sql in ("UPDATE activity SET message='x'", "DELETE FROM assessments", "UPDATE job_snapshots SET payload_json='{}'"):
        with pytest.raises(sqlite3.IntegrityError):
            t.db.execute(sql)


def test_interrupted_task_recovery(tmp_path, profile, postings):
    p = str(tmp_path / "r.db"); t = Tracker(p, profile=profile, run_id="r1")
    jid, _ = t.ingest(postings[0]); t.task("r1:x", "prepare package", jid, "ACTIVE")
    t.db.close()                                            # simulated crash
    t2 = Tracker(p, profile=profile, run_id="r2")
    assert t2.recover_interrupted() == ["r1:x"]
    assert t2.db.execute("SELECT state FROM tasks WHERE task_id='r1:x'").fetchone()[0] == "QUEUED"
    assert t2.ingest(postings[0])[1] is False


def test_migration_v1_to_latest_preserves_data(tmp_path):
    p = str(tmp_path / "m.db"); c = sqlite3.connect(p); c.executescript(MIGRATIONS[1])
    c.execute("INSERT INTO jobs(job_id,fingerprint,canonical_url,company,title,country,match_score,eligibility,raw_json,updated_at,date_discovered) "
              "VALUES('FT001','f','u','Acme','ML Eng','United States',50,'X','{}','2026-10-12T00:00:00Z','2026-10-12')")
    c.commit(); c.close()
    t = Tracker(p)
    assert t.schema_version() == max(MIGRATIONS)
    assert t.db.execute("SELECT engine_version, match_score FROM assessments").fetchone()[:] == ("1.0.0", 50)
    assert t.db.execute("SELECT COUNT(*) FROM job_snapshots").fetchone()[0] == 1


def test_worker_starts_stopped_and_control_is_audited(tmp_path, profile):
    from resume_ai.tracking import control
    t = fresh(tmp_path, profile)
    assert control.desired(t.db) == "STOPPED"               # only the user starts the worker
    control.set_desired(t.db, "RUNNING", "candidate", "test")
    assert control.desired(t.db) == "RUNNING"
    with pytest.raises(sqlite3.IntegrityError):
        t.db.execute("DELETE FROM control_history")


def test_submission_guard_holds_under_python_O(tmp_path):
    """Assertions are stripped by `python -O`; the guards must still refuse."""
    code = """
import json, sqlite3, sys
from resume_ai.grounding.profile import Profile
from resume_ai.tracking.tracker import Tracker, CandidateOnlyStatus
assert False, 'asserts are active'          # must be stripped under -O
root = sys.argv[1]
p = Profile.load(root + '/examples/profile_alex_rivera.json')
t = Tracker(sys.argv[2], profile=p)
jid, _ = t.ingest(json.load(open(root + '/examples/jobs/postings.json'))[0])
out = []
try:
    t.set(jid, application_status='submitted'); out.append('python-guard-bypassed')
except CandidateOnlyStatus:
    out.append('python-guard-ok')
try:
    t.db.execute("UPDATE jobs SET application_status='submitted' WHERE job_id=?", (jid,)); out.append('db-guard-bypassed')
except sqlite3.IntegrityError:
    out.append('db-guard-ok')
t.record_approval(jid, 'submit', 'approved', 'candidate', 'test')
t.db.execute("UPDATE jobs SET application_status='submitted' WHERE job_id=?", (jid,)); out.append('candidate-approved-ok')
print(','.join(out))
"""
    root = Path(__file__).resolve().parents[1]
    r = subprocess.run([sys.executable, "-O", "-c", code, str(root), str(tmp_path / "o.db")], cwd=root,
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "python-guard-ok,db-guard-ok,candidate-approved-ok"
