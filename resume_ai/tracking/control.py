"""Worker control, worker status, dashboard commands and browser audit records (schema v3).

Copied unchanged from the private Resume AI control center (resume_ai/control.py).

desired state (worker_control)   written by the dashboard / CLI: RUNNING, PAUSED, STOPPED
reported state (worker_status)   written only by the worker: STARTING, RUNNING, PAUSED, IDLE, BLOCKED, STOPPING, STOPPED
The dashboard never trusts the reported state alone: a stale heartbeat or a dead pid is shown as DISCONNECTED.
"""
import json
import os
from datetime import datetime, timezone

from .tracker import now

DESIRED = ("RUNNING", "PAUSED", "STOPPED")
HEARTBEAT_STALE_S = 20
COMMAND_KINDS = ("open_posting", "open_application", "resume_session", "verify_now", "retry", "background", "review_submit", "review_check")


def _ts(s):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def set_desired(db, desired, actor, note=None):
    assert desired in DESIRED, desired
    ts = now()
    db.execute("UPDATE worker_control SET desired=?, updated_at=?, actor=?, note=? WHERE id=1", (desired, ts, actor, note))
    db.execute("INSERT INTO control_history(ts, desired, actor, note) VALUES(?,?,?,?)", (ts, desired, actor, note))
    db.execute("INSERT INTO activity(ts, kind, message, evidence) VALUES(?,?,?,?)",
               (ts, "control", f"Control set to {desired} by {actor}" + (f" — {note}" if note else ""), None))
    db.commit()


def desired(db):
    return db.execute("SELECT desired FROM worker_control WHERE id=1").fetchone()[0]


def report(db, **fields):
    """Worker-side status write; always refreshes the heartbeat."""
    if "detail" in fields:
        fields["detail_json"] = json.dumps(fields.pop("detail"))
    fields["heartbeat_at"] = now()
    cols = ",".join(f"{k}=?" for k in fields)
    db.execute(f"UPDATE worker_status SET {cols} WHERE id=1", tuple(fields.values()))
    db.commit()


def pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def effective_status(db):
    """What the dashboard shows. Combines desired state, reported state, heartbeat age and pid liveness."""
    st = dict(db.execute("SELECT * FROM worker_status WHERE id=1").fetchone())
    want = desired(db)
    hb = _ts(st.get("heartbeat_at"))
    age = (datetime.now(timezone.utc) - hb).total_seconds() if hb else None
    alive = pid_alive(st.get("pid"))
    shown = st.get("state") or "STOPPED"
    reason = None
    if shown not in ("STOPPED",) and (not alive or age is None or age > HEARTBEAT_STALE_S):
        shown, reason = "DISCONNECTED", ("worker process is not running" if not alive else f"no heartbeat for {int(age or 0)}s")
    elif shown == "STOPPED" and want != "STOPPED":
        reason = f"desired {want} but no worker is running — press Start"
    st.update(shown_state=shown, desired=want, heartbeat_age_s=None if age is None else round(age, 1), pid_alive=alive,
              reason=reason, detail=json.loads(st.get("detail_json") or "null"))
    return st


# ---------- commands (dashboard -> worker)
def enqueue(db, kind, job_id=None, payload=None):
    assert kind in COMMAND_KINDS, kind
    cur = db.execute("INSERT INTO commands(ts, kind, job_id, payload_json) VALUES(?,?,?,?)",
                     (now(), kind, job_id, json.dumps(payload or {})))
    db.commit()
    return cur.lastrowid


def next_command(db):
    r = db.execute("SELECT * FROM commands WHERE state='QUEUED' ORDER BY id LIMIT 1").fetchone()
    if r:
        db.execute("UPDATE commands SET state='ACTIVE' WHERE id=?", (r["id"],)); db.commit()
    return dict(r) if r else None


def finish_command(db, cid, ok, result):
    db.execute("UPDATE commands SET state=?, result=?, finished_at=? WHERE id=?", ("DONE" if ok else "FAILED", result, now(), cid))
    db.commit()


def fail_orphan_commands(db, reason):
    db.execute("UPDATE commands SET state='FAILED', result=?, finished_at=? WHERE state='ACTIVE'", (reason, now()))
    db.commit()


# ---------- audit
def browser_event(db, job_id, action, url, target=None, value_note=None, ok=True, detail=None, screenshot=None):
    db.execute("""INSERT INTO browser_events(ts, job_id, action, url, target, value_note, ok, detail, screenshot)
                  VALUES(?,?,?,?,?,?,?,?,?)""", (now(), job_id, action, url, target, value_note, int(bool(ok)), detail, screenshot))
    db.commit()


def checkpoint(db, job_id, url, package_version, fields, skipped, screenshot):
    filled = sum(1 for f in fields if f.get("filled"))
    verified = sum(1 for f in fields if f.get("readback_ok") and not f.get("draft"))     # inserted drafts are never "verified"
    cur = db.execute("""INSERT INTO form_checkpoints(ts, job_id, url, package_version, fields_json, filled, verified, skipped_json, screenshot)
                        VALUES(?,?,?,?,?,?,?,?,?)""", (now(), job_id, url, package_version, json.dumps(fields), filled, verified,
                                                       json.dumps(skipped), screenshot))
    db.commit()
    return cur.lastrowid


def last_checkpoint(db, job_id):
    r = db.execute("SELECT * FROM form_checkpoints WHERE job_id=? ORDER BY id DESC LIMIT 1", (job_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["fields"] = json.loads(d.pop("fields_json") or "[]")
    d["skipped"] = json.loads(d.pop("skipped_json") or "[]")
    return d
