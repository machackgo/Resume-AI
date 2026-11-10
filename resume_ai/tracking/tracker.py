"""SQLite tracker with versioned migrations and append-only history.

Adapted from the private Resume AI control center (resume_ai/tracker.py, schema v8). Adaptations: the
tracker takes a Profile for scoring; candidate-specific eligibility rules removed (the generic eligibility_*
columns stay NULL unless a caller fills them); a few columns were renamed to neutral eligibility_* /
timing_text names; the dashboard-sync export is renamed export_job(); apply-cap groups removed; migration 9
(new) moves the "agent cannot mark submitted" rule into the database.

Append-only tables (UPDATE/DELETE blocked by triggers): activity, job_snapshots, assessments,
approvals, documents. `jobs` holds the current state per job; every change to it is
also logged in `activity`.
"""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone

from ..matching import engine

STATUSES = ["discovered", "verified", "shortlisted", "preparing", "awaiting approval", "approved", "submitted",
            "interviewing", "offer", "rejected", "withdrawn", "on hold", "skipped"]
AGENT_FORBIDDEN = {"approved", "submitted", "interviewing", "offer", "rejected", "withdrawn"}  # only the candidate sets these


class CandidateOnlyStatus(PermissionError):
    """Raised when agent code tries to record a status that only the candidate may set."""

MIGRATIONS = {
    1: """
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE, canonical_url TEXT UNIQUE,
  company TEXT, title TEXT, country TEXT, city TEXT, work_arrangement TEXT, salary TEXT,
  posting_url TEXT, ats TEXT, date_posted TEXT, deadline TEXT, date_discovered TEXT,
  jd_summary TEXT, required_json TEXT, preferred_json TEXT, key_tech_json TEXT,
  start_text TEXT, timing_text TEXT, eligibility_text TEXT, verification_note TEXT,
  match_score INTEGER, matched_json TEXT, gaps_json TEXT, eligibility TEXT, eligibility_notes_json TEXT,
  eligibility_status TEXT, family INTEGER, priority INTEGER, shortlisted INTEGER DEFAULT 0,
  resume_path TEXT, cover_letter_path TEXT, recruiter_json TEXT, outreach_status TEXT DEFAULT 'not started',
  application_status TEXT DEFAULT 'discovered', current_activity TEXT, follow_up_date TEXT,
  updated_at TEXT, raw_json TEXT);
CREATE TABLE IF NOT EXISTS activity (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, job_id TEXT, kind TEXT, message TEXT, evidence TEXT);
""",
    2: """
CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT, description TEXT);
ALTER TABLE jobs ADD COLUMN category TEXT;
ALTER TABLE jobs ADD COLUMN eligibility_assessment TEXT;
ALTER TABLE jobs ADD COLUMN apply_cap_group TEXT;
ALTER TABLE jobs ADD COLUMN explanation_json TEXT;
ALTER TABLE jobs ADD COLUMN still_live INTEGER;
ALTER TABLE jobs ADD COLUMN verified_at TEXT;
ALTER TABLE jobs ADD COLUMN decision_note TEXT;
ALTER TABLE activity ADD COLUMN run_id TEXT;
CREATE TABLE runs (run_id TEXT PRIMARY KEY, started_at TEXT, finished_at TEXT, workflow_version TEXT,
  engine_version TEXT, model TEXT, trigger TEXT, notes TEXT);
CREATE TABLE tasks (task_id TEXT PRIMARY KEY, run_id TEXT, job_id TEXT, kind TEXT, state TEXT CHECK(state IN
  ('QUEUED','ACTIVE','COMPLETED','BLOCKED','FAILED','CANCELLED')), created_at TEXT, started_at TEXT, finished_at TEXT,
  detail TEXT, error TEXT, attempts INTEGER DEFAULT 0);
CREATE TABLE job_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT, captured_at TEXT, source TEXT,
  payload_json TEXT, sha256 TEXT);
CREATE TABLE assessments (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT, created_at TEXT, engine_version TEXT,
  match_score INTEGER, eligibility TEXT, eligibility_assessment TEXT, priority INTEGER, explanation_json TEXT);
CREATE TABLE documents (doc_id TEXT PRIMARY KEY, job_id TEXT, kind TEXT, version INTEGER, path TEXT, sha256 TEXT,
  created_at TEXT, validation_json TEXT, generator_version TEXT, UNIQUE(job_id, kind, version));
CREATE TABLE approvals (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT, action TEXT, decision TEXT, actor TEXT,
  ts TEXT, source TEXT, note TEXT);
CREATE TABLE applications (job_id TEXT PRIMARY KEY, status TEXT, package_version INTEGER, submitted_at TEXT,
  submission_ref TEXT, updated_at TEXT);
CREATE TRIGGER no_submit_without_approval BEFORE UPDATE OF status ON applications
  WHEN NEW.status = 'submitted' AND NOT EXISTS (SELECT 1 FROM approvals a WHERE a.job_id = NEW.job_id
       AND a.action = 'submit' AND a.decision = 'approved' AND a.actor = 'candidate')
  BEGIN SELECT RAISE(ABORT, 'submission requires a candidate approval record'); END;
CREATE TRIGGER no_insert_submitted BEFORE INSERT ON applications WHEN NEW.status = 'submitted'
  BEGIN SELECT RAISE(ABORT, 'submission requires a candidate approval record'); END;
CREATE TRIGGER no_resubmit BEFORE UPDATE OF status ON applications WHEN OLD.status = 'submitted' AND NEW.status = 'submitted'
  BEGIN SELECT RAISE(ABORT, 'already submitted'); END;
""" + "".join(f"""
CREATE TRIGGER {t}_append_only_u BEFORE UPDATE ON {t} BEGIN SELECT RAISE(ABORT, '{t} is append-only'); END;
CREATE TRIGGER {t}_append_only_d BEFORE DELETE ON {t} BEGIN SELECT RAISE(ABORT, '{t} is append-only'); END;"""
           for t in ("activity", "job_snapshots", "assessments", "approvals", "documents")),
    3: """
CREATE TABLE job_links (job_id TEXT PRIMARY KEY REFERENCES jobs(job_id), posting_url TEXT, application_url TEXT,
  application_url_source TEXT, application_url_verified INTEGER DEFAULT 0, ats TEXT, last_verified_url TEXT,
  last_verified_at TEXT, last_nav_ok_at TEXT, last_nav_url TEXT, draft_id TEXT, session_status TEXT DEFAULT 'NO_SESSION',
  session_note TEXT, needs_human_json TEXT, resume_doc_id TEXT, cover_doc_id TEXT, last_checkpoint_id INTEGER,
  last_validation_json TEXT, updated_at TEXT);
CREATE TABLE work_items (job_id TEXT PRIMARY KEY REFERENCES jobs(job_id), stage TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN
  ('QUEUED','ACTIVE','BLOCKED','FAILED','PARKED','AWAITING_APPROVAL','DONE')), attempts INTEGER DEFAULT 0,
  next_attempt_at TEXT, blocker TEXT, last_error TEXT, created_at TEXT, updated_at TEXT);
CREATE TABLE worker_control (id INTEGER PRIMARY KEY CHECK(id = 1), desired TEXT NOT NULL CHECK(desired IN
  ('RUNNING','PAUSED','STOPPED')), updated_at TEXT, actor TEXT, note TEXT);
CREATE TABLE control_history (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, desired TEXT, actor TEXT, note TEXT);
CREATE TABLE worker_status (id INTEGER PRIMARY KEY CHECK(id = 1), pid INTEGER, state TEXT, stage TEXT, job_id TEXT,
  step TEXT, started_at TEXT, heartbeat_at TEXT, browser TEXT, last_error TEXT, cycle INTEGER DEFAULT 0, detail_json TEXT);
CREATE TABLE commands (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT, job_id TEXT, payload_json TEXT,
  state TEXT DEFAULT 'QUEUED' CHECK(state IN ('QUEUED','ACTIVE','DONE','FAILED')), result TEXT, finished_at TEXT);
CREATE TABLE browser_events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, job_id TEXT, action TEXT, url TEXT,
  target TEXT, value_note TEXT, ok INTEGER, detail TEXT, screenshot TEXT);
CREATE TABLE form_checkpoints (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, job_id TEXT, url TEXT, package_version INTEGER,
  fields_json TEXT, filled INTEGER, verified INTEGER, skipped_json TEXT, screenshot TEXT);
INSERT INTO worker_control VALUES (1, 'STOPPED', CURRENT_TIMESTAMP, 'migration-v3', 'initial state; only you start the worker');
INSERT INTO worker_status (id, state) VALUES (1, 'STOPPED');
""" + "".join(f"""
CREATE TRIGGER {t}_append_only_u BEFORE UPDATE ON {t} BEGIN SELECT RAISE(ABORT, '{t} is append-only'); END;
CREATE TRIGGER {t}_append_only_d BEFORE DELETE ON {t} BEGIN SELECT RAISE(ABORT, '{t} is append-only'); END;"""
           for t in ("control_history", "browser_events", "form_checkpoints")),
}
MIGRATIONS[4] = """
CREATE TABLE work_items_v4 (job_id TEXT PRIMARY KEY REFERENCES jobs(job_id), stage TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN
  ('QUEUED','ACTIVE','BLOCKED','WAITING_FOR_USER','FAILED','PARKED','AWAITING_APPROVAL','DONE')), attempts INTEGER DEFAULT 0,
  next_attempt_at TEXT, blocker TEXT, last_error TEXT, created_at TEXT, updated_at TEXT);
INSERT INTO work_items_v4 SELECT job_id, stage, state, attempts, next_attempt_at, blocker, last_error, created_at, updated_at FROM work_items;
DROP TABLE work_items;
ALTER TABLE work_items_v4 RENAME TO work_items;
UPDATE work_items SET state='WAITING_FOR_USER' WHERE state='BLOCKED' AND job_id IN
  (SELECT job_id FROM job_links WHERE session_status IN ('NEEDS_LOGIN','NEEDS_HUMAN'));
"""
MIGRATIONS[5] = """
CREATE TABLE contacts (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT REFERENCES jobs(job_id), found_at TEXT, name TEXT,
  title TEXT, company TEXT, relation TEXT, email TEXT, email_source_url TEXT, email_check TEXT, linkedin_url TEXT,
  source_urls_json TEXT, verification TEXT, notes TEXT, run_id TEXT);
CREATE TABLE model_tasks (job_id TEXT, kind TEXT, state TEXT NOT NULL, attempts INTEGER DEFAULT 0, next_attempt_at TEXT,
  last_error TEXT, output_path TEXT, cost_usd_equiv REAL, started_at TEXT, updated_at TEXT, PRIMARY KEY (job_id, kind));
ALTER TABLE jobs ADD COLUMN contact_status TEXT;
"""
MIGRATIONS[6] = """
ALTER TABLE job_links ADD COLUMN form_status_json TEXT;
"""
MIGRATIONS[7] = """
CREATE TABLE outreach_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, job_id TEXT REFERENCES jobs(job_id), contact_id INTEGER,
  channel TEXT CHECK(channel IN ('email','linkedin_connection','linkedin_followup')), action TEXT, actor TEXT, note TEXT);
CREATE TRIGGER outreach_log_append_only_u BEFORE UPDATE ON outreach_log BEGIN SELECT RAISE(ABORT, 'outreach_log is append-only'); END;
CREATE TRIGGER outreach_log_append_only_d BEFORE DELETE ON outreach_log BEGIN SELECT RAISE(ABORT, 'outreach_log is append-only'); END;
"""
MIGRATIONS[8] = """
CREATE TABLE answers (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, job_id TEXT NOT NULL, qkey TEXT NOT NULL, question TEXT, value TEXT,
  status TEXT CHECK(status IN ('USER_CONFIRMED','USER_APPROVED','INFERRED_DRAFT','REJECTED')), source TEXT, actor TEXT);
CREATE INDEX answers_job ON answers(job_id, qkey);
CREATE TRIGGER answers_append_only_u BEFORE UPDATE ON answers BEGIN SELECT RAISE(ABORT, 'answers is append-only'); END;
CREATE TRIGGER answers_append_only_d BEFORE DELETE ON answers BEGIN SELECT RAISE(ABORT, 'answers is append-only'); END;
"""
MIGRATIONS[9] = """
CREATE TRIGGER jobs_no_submitted_without_approval BEFORE UPDATE OF application_status ON jobs
  WHEN NEW.application_status = 'submitted' AND NOT EXISTS (SELECT 1 FROM approvals a WHERE a.job_id = NEW.job_id
       AND a.action = 'submit' AND a.decision = 'approved' AND a.actor = 'candidate')
  BEGIN SELECT RAISE(ABORT, 'status submitted requires a candidate approval record'); END;
CREATE TRIGGER jobs_no_insert_submitted BEFORE INSERT ON jobs WHEN NEW.application_status = 'submitted'
  BEGIN SELECT RAISE(ABORT, 'status submitted requires a candidate approval record'); END;
"""
MIGRATION_NOTES = {1: "initial jobs + activity", 2: "provenance, append-only history, tasks/runs, approvals, submission guard",
                   3: "local control center: job links, durable work queue, worker control/status, commands, browser audit, form checkpoints",
                   4: "work_items: WAITING_FOR_USER state (sign-in / CAPTCHA / manual step); table rebuilt with all rows copied",
                   5: "contacts table, model_tasks queue, jobs.contact_status",
                   6: "job_links.form_status_json: latest scan of the employer form (required fields done / missing, attachments), no values",
                   7: "outreach_log: per-contact, per-channel outreach states you record (e.g. marked sent by you); append-only",
                   8: "answers: your answers, generated drafts and their review states per question (job or '*' = all); append-only",
                   9: "jobs.application_status cannot become 'submitted' without a candidate approval record (showcase)"}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(s):
    return hashlib.sha256(s.encode() if isinstance(s, str) else s).hexdigest()


class Tracker:
    def __init__(self, path, profile=None, run_id=None):
        self.profile = profile          # needed for assess(); pure bookkeeping works without it
        self.db = sqlite3.connect(path, timeout=30)  # worker and dashboard share the file
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=30000")
        self.run_id = run_id
        self.migrate()

    # ---------- schema
    def schema_version(self):
        has = self.db.execute("SELECT 1 FROM sqlite_master WHERE name='schema_migrations'").fetchone()
        if has:
            return self.db.execute("SELECT COALESCE(MAX(version),0) FROM schema_migrations").fetchone()[0]
        return 1 if self.db.execute("SELECT 1 FROM sqlite_master WHERE name='jobs'").fetchone() else 0

    def migrate(self):
        v = self.schema_version()
        for n in sorted(MIGRATIONS):
            if n > v:
                self.db.executescript(MIGRATIONS[n])
                if n >= 2:
                    if n == 2:  # record history for both
                        self.db.execute("INSERT OR IGNORE INTO schema_migrations VALUES(1,?,?)", (now(), MIGRATION_NOTES[1]))
                    self.db.execute("INSERT INTO schema_migrations VALUES(?,?,?)", (n, now(), MIGRATION_NOTES[n]))
                self.db.commit()
        if v and v < 2:
            self._backfill_v2()

    def _backfill_v2(self):
        for r in self.db.execute("SELECT * FROM jobs").fetchall():
            raw = r["raw_json"] or "{}"
            self.db.execute("INSERT INTO job_snapshots(job_id,captured_at,source,payload_json,sha256) VALUES(?,?,?,?,?)",
                            (r["job_id"], r["date_discovered"], "migration-v2 backfill", raw, sha(raw)))
            self.db.execute("INSERT INTO assessments(job_id,created_at,engine_version,match_score,eligibility,eligibility_assessment,priority,explanation_json) VALUES(?,?,?,?,?,?,?,?)",
                            (r["job_id"], r["updated_at"], "1.0.0", r["match_score"], r["eligibility"], r["eligibility_status"], r["priority"],
                             json.dumps({"matched": json.loads(r["matched_json"] or "[]"), "gaps": json.loads(r["gaps_json"] or "[]")})))
        self.db.commit()
        self.log("migration", "Schema migrated v1 → v2; v1 scores preserved as engine 1.0.0 assessments")

    # ---------- events / runs / tasks
    def log(self, kind, message, job_id=None, evidence=None):
        self.db.execute("INSERT INTO activity(ts,job_id,kind,message,evidence,run_id) VALUES(?,?,?,?,?,?)",
                        (now(), job_id, kind, message, evidence, self.run_id))
        self.db.commit()

    def start_run(self, run_id, workflow_version, trigger, model="claude (session)", notes=None):
        self.run_id = run_id
        self.db.execute("INSERT OR IGNORE INTO runs VALUES(?,?,?,?,?,?,?,?)",
                        (run_id, now(), None, workflow_version, engine.ENGINE_VERSION, model, trigger, notes))
        self.db.commit()
        self.log("run", f"Run {run_id} started ({trigger})")

    def finish_run(self):
        self.db.execute("UPDATE runs SET finished_at=? WHERE run_id=?", (now(), self.run_id)); self.db.commit()
        self.log("run", f"Run {self.run_id} finished")

    def task(self, task_id, kind, job_id=None, state="QUEUED", detail=None, error=None):
        ts = now()
        row = self.db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            self.db.execute("INSERT INTO tasks(task_id,run_id,job_id,kind,state,created_at,detail) VALUES(?,?,?,?,?,?,?)",
                            (task_id, self.run_id, job_id, kind, state, ts, detail))
        else:
            self.db.execute("""UPDATE tasks SET state=?, detail=COALESCE(?,detail), error=?,
               started_at=CASE WHEN ?='ACTIVE' THEN ? ELSE started_at END,
               finished_at=CASE WHEN ? IN ('COMPLETED','BLOCKED','FAILED','CANCELLED') THEN ? ELSE finished_at END,
               attempts=attempts + CASE WHEN ?='ACTIVE' THEN 1 ELSE 0 END WHERE task_id=?""",
                            (state, detail, error, state, ts, state, ts, state, task_id))
        self.db.commit()
        self.log(f"task:{state.lower()}", f"{kind}: {detail or ''}".strip(": "), job_id, task_id)

    def recover_interrupted(self):
        """Tasks left ACTIVE by a crashed run go back to QUEUED (logged), so they are retried, not lost."""
        stale = self.db.execute("SELECT task_id, kind, job_id FROM tasks WHERE state='ACTIVE'").fetchall()
        for t in stale:
            self.db.execute("UPDATE tasks SET state='QUEUED', error='recovered after interruption' WHERE task_id=?", (t["task_id"],))
            self.log("recovery", f"Re-queued interrupted task {t['kind']}", t["job_id"], t["task_id"])
        self.db.commit()
        return [t["task_id"] for t in stale]

    # ---------- jobs
    def next_id(self):
        n = self.db.execute("SELECT COALESCE(MAX(CAST(SUBSTR(job_id,3) AS INTEGER)),0) FROM jobs").fetchone()[0]
        return f"FT{n + 1:03d}"

    def find_duplicate(self, job):
        fp, cu = engine.fingerprint(job), engine.canonical_url(job["posting_url"])
        r = self.db.execute("SELECT job_id FROM jobs WHERE fingerprint=? OR canonical_url=?", (fp, cu)).fetchone()
        return r["job_id"] if r else None

    def ingest(self, job, discovered=None, source="discovery"):
        dup = self.find_duplicate(job)
        if dup:
            self.log("dedupe", f"Duplicate of {dup} not re-added: {job['company']} — {job['title']}", dup, job["posting_url"])
            return dup, False
        jid, ts = self.next_id(), now()
        self.db.execute("""INSERT INTO jobs(job_id,fingerprint,canonical_url,company,title,country,city,work_arrangement,salary,
            posting_url,ats,date_posted,deadline,date_discovered,jd_summary,required_json,preferred_json,key_tech_json,start_text,
            timing_text,eligibility_text,verification_note,category,application_status,current_activity,updated_at,raw_json,still_live,verified_at,
            apply_cap_group) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (jid, engine.fingerprint(job), engine.canonical_url(job["posting_url"]), job["company"], job["title"], job["country"],
             job.get("city"), job.get("work_arrangement"), job.get("salary"), job["posting_url"], job.get("ats"), job.get("date_posted"),
             job.get("deadline"), discovered or ts[:10], job.get("jd_summary"), json.dumps(job.get("required_qualifications", [])),
             json.dumps(job.get("preferred_qualifications", [])), json.dumps(job.get("key_tech", [])), job.get("start_date_text"),
             job.get("timing_text"), job.get("eligibility_text"), job.get("verification_note"), job.get("category"),
             "verified", "Verified live; scored", ts, json.dumps(job), 1, discovered or ts[:10],
             None))
        raw = json.dumps(job, sort_keys=True)
        self.db.execute("INSERT INTO job_snapshots(job_id,captured_at,source,payload_json,sha256) VALUES(?,?,?,?,?)",
                        (jid, ts, source, raw, sha(raw)))
        self.db.commit()
        self.log("discovered", f"{job['company']} — {job['title']} ({job['country']})", jid, job["posting_url"])
        if self.profile is not None:
            self.assess(jid)
        return jid, True

    def raw(self, job_id):
        return json.loads(self.db.execute("SELECT raw_json FROM jobs WHERE job_id=?", (job_id,)).fetchone()[0])

    def add_snapshot(self, job_id, source, payload):
        raw = json.dumps(payload, sort_keys=True)
        self.db.execute("INSERT INTO job_snapshots(job_id,captured_at,source,payload_json,sha256) VALUES(?,?,?,?,?)",
                        (job_id, now(), source, raw, sha(raw)))
        self.db.commit()

    def assess(self, job_id, deadline_days=None):
        job = self.raw(job_id)
        score, ex = engine.skill_match(job, self.profile.skills, self.profile.gaps, self.profile.hard_gaps)
        elig, notes, sp_text, sp = None, [], None, None      # candidate-specific eligibility rules removed
        fam = engine.pick_family(job)
        pr = engine.priority(job, score, deadline_days)
        ex_json = json.dumps(ex)
        self.db.execute("INSERT INTO assessments(job_id,created_at,engine_version,match_score,eligibility,eligibility_assessment,priority,explanation_json) VALUES(?,?,?,?,?,?,?,?)",
                        (job_id, now(), engine.ENGINE_VERSION, score, elig, sp, pr, ex_json))
        self.db.execute("""UPDATE jobs SET match_score=?, matched_json=?, gaps_json=?, eligibility=?, eligibility_notes_json=?,
            eligibility_status=?, eligibility_assessment=?, family=?, priority=?, explanation_json=?, updated_at=? WHERE job_id=?""",
                        (score, json.dumps(ex["verified"] + ex["in_progress"]), json.dumps(ex["gaps"]), elig, json.dumps(notes),
                         sp_text, sp, fam, pr, ex_json, now(), job_id))
        self.db.commit()
        self.log("scored", f"Match {score}/100 · family {fam} · priority {pr} (engine {engine.ENGINE_VERSION})", job_id)
        return score, elig

    def set(self, job_id, **fields):
        st = fields.get("application_status")
        if st is not None:
            if st not in STATUSES:
                raise ValueError(f"unknown status {st!r}")
            if st in AGENT_FORBIDDEN:
                raise CandidateOnlyStatus(f"'{st}' can only be recorded from a candidate action")
        fields["updated_at"] = now()
        cols = ",".join(f"{k}=?" for k in fields)
        self.db.execute(f"UPDATE jobs SET {cols} WHERE job_id=?", (*fields.values(), job_id))
        self.db.commit()

    # ---------- approvals / applications / documents
    def record_approval(self, job_id, action, decision, actor, source, note=None):
        if actor not in ("candidate", "agent"):
            raise ValueError(f"unknown actor {actor!r}")
        self.db.execute("INSERT INTO approvals(job_id,action,decision,actor,ts,source,note) VALUES(?,?,?,?,?,?,?)",
                        (job_id, action, decision, actor, now(), source, note))
        self.db.commit()
        self.log("approval", f"{actor} {decision} {action}", job_id, source)

    def mark_submitted(self, job_id, ref):
        """Only succeeds with a candidate 'submit' approval on record (enforced by trigger); never twice."""
        self.db.execute("INSERT OR IGNORE INTO applications(job_id,status,updated_at) VALUES(?,?,?)", (job_id, "ready", now()))
        self.db.execute("UPDATE applications SET status='submitted', submitted_at=?, submission_ref=?, updated_at=? WHERE job_id=?",
                        (now(), ref, now(), job_id))
        self.db.commit()

    def add_document(self, job_id, kind, path, content, validation, generator_version):
        v = (self.db.execute("SELECT COALESCE(MAX(version),0) FROM documents WHERE job_id=? AND kind=?", (job_id, kind)).fetchone()[0]) + 1
        doc_id = f"{job_id}-{kind}-v{v}"
        self.db.execute("INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?)",
                        (doc_id, job_id, kind, v, path, sha(content), now(), json.dumps(validation), generator_version))
        self.db.commit()
        self.log("document", f"Saved {kind} v{v} ({'passed' if not validation.get('issues') else 'FAILED'} validation)", job_id, path)
        return doc_id, v

    # ---------- reads
    def query(self, where="1=1", params=(), order="priority DESC"):
        return [dict(r) for r in self.db.execute(f"SELECT * FROM jobs WHERE {where} ORDER BY {order}", params)]

    def activity(self, job_id=None):
        q = "SELECT * FROM activity" + (" WHERE job_id=?" if job_id else "") + " ORDER BY id"
        return [dict(r) for r in self.db.execute(q, (job_id,) if job_id else ())]

    def documents(self, job_id):
        return [dict(r) for r in self.db.execute("SELECT * FROM documents WHERE job_id=? ORDER BY kind, version", (job_id,))]

    def export_job(self, job_id):
        j = self.query("job_id=?", (job_id,))[0]
        keys = ("job_id", "company", "title", "country", "city", "work_arrangement", "salary", "posting_url", "ats", "date_posted",
                "deadline", "date_discovered", "jd_summary", "start_text", "timing_text", "eligibility_text", "verification_note",
                "match_score", "eligibility", "eligibility_status", "eligibility_assessment", "family", "priority", "category",
                "apply_cap_group", "resume_path", "cover_letter_path", "outreach_status", "application_status", "current_activity",
                "follow_up_date", "updated_at", "verified_at", "decision_note")
        out = {k: j.get(k) for k in keys}
        out["verified_live"] = bool(j.get("still_live"))
        for k in ("required", "preferred", "key_tech", "gaps", "eligibility_notes"):
            out[k] = json.loads(j[f"{k}_json"] or "[]")
        ex = json.loads(j["explanation_json"] or "{}")
        out["explanation"] = ex
        out["matched"] = ex.get("verified", []) + ex.get("in_progress", [])
        out["shortlisted"] = bool(j["shortlisted"])
        out["recruiter"] = json.loads(j["recruiter_json"]) if j["recruiter_json"] else None
        out["documents"] = [{"kind": d["kind"], "version": d["version"], "path": d["path"], "sha256": d["sha256"][:12],
                             "created_at": d["created_at"], "validation": json.loads(d["validation_json"])} for d in self.documents(job_id)]
        out["assessments"] = [dict(r) for r in self.db.execute(
            "SELECT created_at, engine_version, match_score, eligibility, eligibility_assessment FROM assessments WHERE job_id=? ORDER BY id", (job_id,))]
        out["history"] = [{"ts": a["ts"], "kind": a["kind"], "message": a["message"], "evidence": a["evidence"]}
                          for a in self.activity(job_id) if a["kind"] != "dedupe"][-60:]
        return out
