"""
Host-side schedule-bridge bootstrap runner for Packet UI-002a.

Purpose
-------
Apply the `schedule` schema DDL against the local apex_pm_stage Postgres
and run the UI-002a P6 schedule-context loader against the default JSON
fixture (or a .xer file if one is present under fixtures/). Produces a
timestamped log so the handoff can cite concrete persisted-mode evidence.

This script is intended to be run on the Windows host where
`SEAM_DATABASE_URL` points at a reachable apex_pm_stage Postgres. The
Desktop Claude sandbox cannot reach that host; bootstrap must run where
Postgres is.

What it does
------------
1.  Prints the redacted `SEAM_DATABASE_URL` and confirms connectivity.
2.  Applies `migrations/001_schedule_schema.sql` in a single transaction.
    The DDL is idempotent (CREATE ... IF NOT EXISTS) so re-running the
    bootstrap is safe.
3.  Runs `app.schedule.loader.run_load()` against the default JSON
    fixture (or the first .xer file under `app/schedule/fixtures/` if
    PyP6Xer is installed).
4.  Prints row counts per schedule.* table and the latest sync_log entry.
5.  Starts uvicorn on 127.0.0.1:8766 with persisted backend, hits
    `/api/v1/schedule/projects`, `/api/v1/schedule/projects/{id}/wbs`,
    `/api/v1/schedule/tasks`, and `/api/v1/schedule/relationships` so
    the full read-bridge path is exercised end-to-end against live data.
6.  Stops uvicorn.
7.  Writes `apps/mutation-seam/logs/schedule-bootstrap-<STAMP>.log`.

This is the packet UI-002a persisted-mode closeout evidence artifact.

Usage
-----
    cd apps/mutation-seam
    python run_schedule_bootstrap.py
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MIGRATIONS_DIR = HERE / "migrations"
# Retained for log messaging when only a single migration is in scope.
MIGRATION_FILE = MIGRATIONS_DIR / "001_schedule_schema.sql"
LOGDIR = HERE / "logs"
LOGDIR.mkdir(exist_ok=True)

# Honor the documented one-command invocation by loading the local app env
# before any bootstrap step inspects SEAM_DATABASE_URL.
load_dotenv(HERE / ".env")

STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
LOGFILE = LOGDIR / f"schedule-bootstrap-{STAMP}.log"

PORT = int(os.environ.get("SCHEDULE_PORT", "8766"))


def log(msg: str) -> None:
    line = f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with LOGFILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def fail(msg: str) -> None:
    log(f"FAIL: {msg}")
    sys.exit(1)


def step_describe() -> None:
    log("STEP 1 — environment describe")
    dsn = os.environ.get("SEAM_DATABASE_URL", "")
    if not dsn:
        fail("SEAM_DATABASE_URL is not set; cannot bootstrap schedule bridge.")
    try:
        scheme, rest = dsn.split("://", 1)
        if "@" in rest:
            creds, host = rest.split("@", 1)
            user = creds.split(":", 1)[0]
            redacted = f"{scheme}://{user}:***@{host}"
        else:
            redacted = dsn
    except Exception:
        redacted = "<unparseable>"
    log(f"  SEAM_DATABASE_URL = {redacted}")


def step_select_1() -> None:
    log("STEP 2 — SELECT 1")
    import psycopg2  # type: ignore
    conn = psycopg2.connect(os.environ["SEAM_DATABASE_URL"], connect_timeout=5)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        log(f"  SELECT 1 -> {cur.fetchone()[0]}")
    conn.close()


def step_apply_ddl() -> None:
    # Auto-discover numbered migrations (`NNN_*.sql`) and apply them in order.
    # This allows later packets to add migrations (e.g., 002_schedule_baseline
    # under packet 020c) without editing this runner.
    migrations = sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"))
    if not migrations:
        fail(f"no numbered migrations found under {MIGRATIONS_DIR}")
    log(f"STEP 3 — apply DDL ({len(migrations)} migrations)")
    import psycopg2  # type: ignore
    for m in migrations:
        log(f"  applying {m.name}")
        sql = m.read_text(encoding="utf-8")
        conn = psycopg2.connect(os.environ["SEAM_DATABASE_URL"])
        conn.autocommit = False
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        except Exception as e:
            conn.rollback()
            fail(f"DDL apply failed on {m.name}: {type(e).__name__}: {e}")
        finally:
            conn.close()
    log("  all migrations applied successfully")


def step_load_fixture() -> None:
    log("STEP 4 — load schedule fixture via app.schedule.loader")
    # Import lazily so path resolution reflects the repo layout
    sys.path.insert(0, str(HERE))
    from app.schedule.loader import run_load  # type: ignore
    result = run_load()
    log(f"  loader result: {json.dumps(result, default=str)}")


def step_report_counts() -> None:
    log("STEP 5 — post-load row counts")
    import psycopg2  # type: ignore
    conn = psycopg2.connect(os.environ["SEAM_DATABASE_URL"])
    conn.autocommit = True
    with conn.cursor() as cur:
        for t in ("projects", "wbs_nodes", "tasks", "relationships", "sync_log"):
            cur.execute(f"SELECT count(*) FROM schedule.{t}")
            log(f"  schedule.{t}: {cur.fetchone()[0]}")
        cur.execute(
            "SELECT id, source_type, status, stats FROM schedule.sync_log "
            "ORDER BY started_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            log(f"  latest sync_log: id={row[0]} source={row[1]} status={row[2]} stats={row[3]}")
    conn.close()


def step_http_bridge() -> None:
    log("STEP 6 — exercise read bridge over HTTP (uvicorn on 127.0.0.1:{})".format(PORT))
    env = os.environ.copy()
    env.pop("SEAM_STORE_BACKEND", None)
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(PORT)],
        env=env, cwd=str(HERE),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        import urllib.request
        ready = False
        for _ in range(30):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1).read()
                ready = True
                break
            except Exception:
                time.sleep(0.3)
        if not ready:
            fail("uvicorn did not become ready on /health")

        # base64 'field_tech' token matching conftest + validate.py shape
        import base64
        tok_payload = json.dumps({
            "actor_id": "tech-001",
            "actor_role": "field_tech",
            "project_scope": ["proj-001"],
        }).encode()
        token = base64.b64encode(tok_payload).decode()

        def _get(path: str) -> dict | list:
            req = urllib.request.Request(
                f"http://127.0.0.1:{PORT}{path}",
                headers={"Authorization": f"Bearer {token}"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())

        projects = _get("/api/v1/schedule/projects")
        log(f"  GET /projects         -> {len(projects)} rows")
        if not projects:
            fail("schedule.projects is empty after load; bridge cannot exercise further")
        proj_id = projects[0]["id"]
        wbs = _get(f"/api/v1/schedule/projects/{proj_id}/wbs")
        log(f"  GET /projects/{{id}}/wbs -> {len(wbs)} rows")
        tasks = _get(f"/api/v1/schedule/tasks?project_id={proj_id}")
        log(f"  GET /tasks            -> {len(tasks)} rows")
        tasks_scope = _get(f"/api/v1/schedule/tasks-with-scope?project_id={proj_id}")
        log(f"  GET /tasks-with-scope -> {len(tasks_scope)} rows")
        rels = _get(f"/api/v1/schedule/relationships?project_id={proj_id}")
        log(f"  GET /relationships    -> {len(rels)} rows")
        sync = _get("/api/v1/schedule/sync-log?limit=5")
        log(f"  GET /sync-log         -> {len(sync)} rows")
    finally:
        try:
            server.terminate()
            server.wait(timeout=5)
        except Exception:
            server.kill()


def main() -> None:
    log(f"Packet UI-002a schedule bootstrap — log: {LOGFILE}")
    step_describe()
    step_select_1()
    step_apply_ddl()
    step_load_fixture()
    step_report_counts()
    step_http_bridge()
    log("ALL STEPS PASSED — schedule bridge bootstrap complete")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - host runner only
        fail(f"unhandled exception: {type(exc).__name__}: {exc}")