"""
Host-side persisted-mode validation runner for Packet UI-001e.

Purpose
-------
Drive the packet-001e closeout against the LIVE local Postgres (apex_pm_stage)
so the pytest suite and the cross-surface integration harness execute with
state that lives in the `seam` schema, not in the in-memory MemoryStore.

This script is intended to be run on the Windows host where
`SEAM_DATABASE_URL` in apps/mutation-seam/.env points at a reachable
apex_pm_stage Postgres. The Linux sandbox used by Desktop Claude cannot
reach the host Postgres and therefore cannot drive persisted-mode validation
end-to-end; this runner exists so the closeout is a one-command action.

What it does
------------
1.  Prints the active SEAM_* env vars so the run is self-describing.
2.  Verifies `SELECT 1` against SEAM_DATABASE_URL.
3.  Verifies `from app.db.memory_store import store` resolves to
    SupabaseStore (i.e. persisted mode, not memory fallback).
4.  Runs `pytest -q` without SEAM_STORE_BACKEND=memory override.
5.  Starts uvicorn in persisted mode on 127.0.0.1:8765.
6.  Runs apps/mutation-seam/validate.py against that server.
7.  Writes a timestamped log file under apps/mutation-seam/logs/ so the
    handoff can cite exact persisted-mode evidence.
8.  Stops uvicorn and exits non-zero if any step failed.

Usage
-----
    cd apps/mutation-seam
    python run_persisted_validation.py

Env flags
---------
    SEAM_DATABASE_URL        (required)  local Postgres DSN
    SEAM_STORE_BACKEND       (must NOT be 'memory' for persisted mode)
    PERSISTED_PORT           (optional)  uvicorn port, default 8765
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import datetime
import signal
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent                             # apex-power-ops-platform/
HARNESS = REPO / "apps" / "mutation-seam" / "validate.py"
LOGDIR = HERE / "logs"
LOGDIR.mkdir(exist_ok=True)

STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
LOGFILE = LOGDIR / f"persisted-validation-{STAMP}.log"

PORT = int(os.environ.get("PERSISTED_PORT", "8765"))


def log(msg: str) -> None:
    line = f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with LOGFILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd: list[str], env: dict | None = None, cwd: Path | None = None) -> tuple[int, str]:
    log(f"$ {' '.join(cmd)}")
    p = subprocess.run(
        cmd,
        env=env or os.environ.copy(),
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    out = (p.stdout or "") + (p.stderr or "")
    with LOGFILE.open("a", encoding="utf-8") as f:
        f.write(out + "\n")
    return p.returncode, out


def fail(msg: str) -> None:
    log(f"FAIL: {msg}")
    sys.exit(1)


def step_env_describe() -> None:
    log("STEP 1 — describe environment")
    dsn = os.environ.get("SEAM_DATABASE_URL", "")
    backend = os.environ.get("SEAM_STORE_BACKEND", "<unset>")
    if not dsn:
        fail("SEAM_DATABASE_URL is not set. Aborting persisted-mode run.")
    if backend == "memory":
        fail("SEAM_STORE_BACKEND=memory is active. Unset it before persisted-mode run.")
    # redact password for log
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
    log(f"  SEAM_STORE_BACKEND = {backend}")


def step_select_1() -> None:
    log("STEP 2 — SELECT 1 against SEAM_DATABASE_URL")
    import psycopg2  # type: ignore
    try:
        conn = psycopg2.connect(os.environ["SEAM_DATABASE_URL"], connect_timeout=5)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            log(f"  SELECT 1 -> {cur.fetchone()[0]}")
            cur.execute("SELECT count(*) FROM seam.apparatus")
            log(f"  seam.apparatus rows -> {cur.fetchone()[0]}")
            cur.execute("SELECT count(*) FROM seam.workpackages")
            log(f"  seam.workpackages rows -> {cur.fetchone()[0]}")
            cur.execute("SELECT count(*) FROM seam.tasks")
            log(f"  seam.tasks rows -> {cur.fetchone()[0]}")
        conn.close()
    except Exception as e:
        fail(f"SELECT 1 failed: {type(e).__name__}: {e}")


def step_import_resolves_supabase() -> None:
    log("STEP 3 — import resolves to SupabaseStore")
    cmd = [sys.executable, "-c",
           "from app.db.memory_store import store; "
           "print(type(store).__name__)"]
    rc, out = run(cmd, cwd=HERE)
    if rc != 0:
        fail(f"import failed (rc={rc})")
    if "SupabaseStore" not in out:
        fail(f"expected SupabaseStore, got: {out.strip()}")
    log("  resolved to SupabaseStore")


def step_pytest_persisted() -> None:
    log("STEP 4 — pytest in persisted mode")
    env = os.environ.copy()
    env.pop("SEAM_STORE_BACKEND", None)
    rc, _ = run([sys.executable, "-m", "pytest", "-q"], env=env, cwd=HERE)
    if rc != 0:
        fail(f"pytest failed (rc={rc}) — see {LOGFILE}")
    log("  pytest passed")


def step_harness_persisted() -> None:
    log("STEP 5 — integration harness in persisted mode")
    env = os.environ.copy()
    env.pop("SEAM_STORE_BACKEND", None)
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(PORT)],
        env=env, cwd=str(HERE),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        # wait for readiness
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

        rc, _ = run([sys.executable, str(HARNESS),
                     "--base-url", f"http://127.0.0.1:{PORT}"], env=env)
        if rc != 0:
            fail(f"integration harness failed (rc={rc})")
        log("  harness passed")
    finally:
        try:
            if os.name == "nt":
                server.send_signal(signal.CTRL_BREAK_EVENT)  # best-effort
            server.terminate()
            server.wait(timeout=5)
        except Exception:
            server.kill()


def main() -> None:
    log(f"Packet UI-001e persisted-mode validation — log: {LOGFILE}")
    step_env_describe()
    step_select_1()
    step_import_resolves_supabase()
    step_pytest_persisted()
    step_harness_persisted()
    log("ALL STEPS PASSED — persisted-mode closeout evidence written")


if __name__ == "__main__":
    main()
