import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone

DB_PATH = os.environ.get("ONBOARDING_DB", os.path.join("data", "onboarding.db"))


def now():
    return datetime.now(timezone.utc).isoformat()


def connect():
    directory = os.path.dirname(DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db():
    con = connect()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_ref TEXT UNIQUE NOT NULL,
            country TEXT NOT NULL,
            customer_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'in_progress',
            decision TEXT,
            decision_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            step_index INTEGER NOT NULL,
            answers_json TEXT NOT NULL,
            integration TEXT,
            completed_at TEXT NOT NULL,
            UNIQUE(application_id, step_index),
            FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS integration_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            integration TEXT NOT NULL,
            result_json TEXT NOT NULL,
            request_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
        );
        """
    )
    # Lightweight migration for databases created by the first version.
    columns = {row[1] for row in con.execute("PRAGMA table_info(applications)").fetchall()}
    if "decision_reason" not in columns:
        con.execute("ALTER TABLE applications ADD COLUMN decision_reason TEXT")
    con.commit()
    con.close()


def audit(con, app_id, event_type, details):
    con.execute(
        "INSERT INTO audit_events(application_id,event_type,details,created_at) VALUES (?,?,?,?)",
        (app_id, event_type, json.dumps(details), now()),
    )


def create_application(country, customer_type):
    stamp = now()
    ref = "APP-" + uuid.uuid4().hex[:10].upper()
    con = connect()
    cur = con.execute(
        "INSERT INTO applications(application_ref,country,customer_type,created_at,updated_at) VALUES (?,?,?,?,?)",
        (ref, country, customer_type, stamp, stamp),
    )
    app_id = cur.lastrowid
    audit(con, app_id, "application_created", {"country": country, "customer_type": customer_type})
    con.commit()
    con.close()
    return app_id


def get_application(app_id):
    con = connect()
    app = con.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
    if not app:
        con.close()
        return None

    steps = con.execute(
        "SELECT * FROM steps WHERE application_id=? ORDER BY step_index", (app_id,)
    ).fetchall()
    results = con.execute(
        "SELECT * FROM integration_results WHERE application_id=? ORDER BY id", (app_id,)
    ).fetchall()
    audit_rows = con.execute(
        "SELECT * FROM audit_events WHERE application_id=? ORDER BY id", (app_id,)
    ).fetchall()
    con.close()

    return {
        "app": dict(app),
        "steps": [dict(x) for x in steps],
        "results": [dict(x) for x in results],
        "audit": [dict(x) for x in audit_rows],
    }


def save_step(app_id, step_index, answers, integration):
    con = connect()
    stamp = now()
    con.execute(
        """
        INSERT INTO steps(application_id,step_index,answers_json,integration,completed_at)
        VALUES(?,?,?,?,?)
        ON CONFLICT(application_id,step_index) DO UPDATE SET
            answers_json=excluded.answers_json,
            integration=excluded.integration,
            completed_at=excluded.completed_at
        """,
        (app_id, step_index, json.dumps(answers), integration, stamp),
    )
    # Remove stale result(s) when a user edits and re-runs an integration.
    if integration:
        con.execute(
            "DELETE FROM integration_results WHERE application_id=? AND integration=?",
            (app_id, integration),
        )
    con.execute("UPDATE applications SET updated_at=? WHERE id=?", (stamp, app_id))
    audit(con, app_id, "step_completed", {"step_index": step_index, "integration": integration})
    con.commit()
    con.close()


def save_integration(app_id, result):
    con = connect()
    con.execute(
        "INSERT INTO integration_results(application_id,integration,result_json,request_id,created_at) VALUES(?,?,?,?,?)",
        (
            app_id,
            result["integration"],
            json.dumps(result),
            result["request_id"],
            now(),
        ),
    )
    audit(
        con,
        app_id,
        "integration_checked",
        {
            "integration": result["integration"],
            "status": result["status"],
            "code": result["code"],
            "request_id": result["request_id"],
        },
    )
    con.commit()
    con.close()


def finalize(app_id, decision, reason):
    con = connect()
    stamp = now()
    con.execute(
        "UPDATE applications SET status='completed',decision=?,decision_reason=?,updated_at=? WHERE id=?",
        (decision, reason, stamp, app_id),
    )
    audit(con, app_id, "decision_made", {"decision": decision, "reason": reason})
    con.commit()
    con.close()
