# Agent-Env Sanitizer (Part A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild apex-jobs `_agent_env` so agent and review subprocesses receive a default-deny allowlisted environment, not the worker's full `os.environ` (which sources DB secrets).

**Architecture:** One function in `packages/apex-jobs/src/apex_jobs/agent_runner.py` is rewritten to construct the child env from a flat, module-level exact-name allowlist plus the `APEX_JOB_ENV` marker, preserving the existing agent-bin PATH prepend. Both call sites (`run_agent_job`, `run_review_job`) already route through this one function, so no call-site edits are needed. Tests, a README note, and a post-build CLI smoke complete the change.

**Tech Stack:** Python 3.12, pytest, `uv` (with the `test` extra), psycopg3 (the suite's DB fixtures), host PG17 `orchestration_test`.

## Global Constraints

- SCOPE: This plan implements PART A ONLY (the agent-env sanitizer). Part B (Infisical adoption, command-job env policy) is DESIGN-ONLY in the spec and MUST NOT be implemented here. Do NOT modify `packages/apex-jobs/src/apex_jobs/worker.py` (command-job path) -- command jobs legitimately need injected DB secrets and are out of scope.
- ALLOWLIST (ratified, exact names, NO prefix matching -- copy verbatim into the code as `_AGENT_ENV_ALLOW`):
  - Base: `HOME` `PATH` `USER` `LOGNAME` `SHELL` `TERM` `TMPDIR` `TMP` `TEMP` `TZ` `LANG`
  - Locale: `LC_ALL` `LC_COLLATE` `LC_CTYPE` `LC_MESSAGES` `LC_MONETARY` `LC_NUMERIC` `LC_TIME` `LC_ADDRESS` `LC_IDENTIFICATION` `LC_MEASUREMENT` `LC_NAME` `LC_PAPER` `LC_TELEPHONE`
  - XDG: `XDG_CONFIG_HOME` `XDG_CACHE_HOME` `XDG_DATA_HOME` `XDG_STATE_HOME` `XDG_RUNTIME_DIR`
  - Always set (not from os.environ): `APEX_JOB_ENV`. Read-only config (never exported): `APEX_JOBS_AGENT_PATH`.
- DOC-FIX RULE: Do NOT rewrite `packages/apex-jobs/README.md` line 41 to claim agent sanitization -- that line documents the COMMAND-worker path and stays accurate for command jobs. Add the sanitized-env statement in the agent section ("Durable multi-agent core"); optionally qualify line 41 to say "command subprocess".
- HOST-CANONICAL DISCIPLINE: The canonical tree is the host worktree `/home/olares/code/apex/apex-secrets-agent-env` (branch `secrets/agent-env-sanitizer`, off main 3f3ebe46). Author locally, `scp` each changed file to that worktree only, run + commit host-side over `ssh olares-mesh`. Single writer -- never touch the main checkout or any other worktree. ASCII-only added lines. Value-silent (never echo a DSN/password; names/paths/booleans/counts only). No production mutation. Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- TEST RUNNER (host-side): the apex-jobs suite's session-autouse `_schema` fixture SKIPS the whole file without DB creds, so every test run -- including red-proofs of the pure unit tests -- must source the DB env first. `infra/.env` is gitignored (absent in the worktree), so source it from the MAIN checkout:
  ```
  set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a
  cd /home/olares/code/apex/apex-secrets-agent-env/packages/apex-jobs
  APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest <target> -v
  ```
  If the DB creds are stale/absent the suite skips with a hint (conftest) -- that is an environment problem to fix, not a code failure.

---

## Task 1: Agent-env sanitizer (allowlist rewrite + unit tests)

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/agent_runner.py` (add `_AGENT_ENV_ALLOW` above `_agent_env` near line 73; rewrite `_agent_env`; correct its docstring)
- Test: `packages/apex-jobs/tests/test_agent_runner.py` (append four unit tests)

**Interfaces:**
- Consumes: nothing new.
- Produces: `agent_runner._AGENT_ENV_ALLOW` (frozenset of allowed exact names); `agent_runner._agent_env(job_env: str) -> dict` (unchanged signature; now allowlist-filtered). Both `run_agent_job` (line 119) and `run_review_job` (line 178) already call `_agent_env(env)` -- do not touch those call sites.

- [ ] **Step 1: Write the four failing unit tests**

Append to `packages/apex-jobs/tests/test_agent_runner.py` (the file already imports `os` and `from apex_jobs import engine, agent_runner`):

```python
# --- agent-env sanitizer: default-deny allowlist (Part A) ---

_SECRET_BATTERY = {
    "APEX_JOBS_PGPASSWORD": "x", "DEV_PG_PASSWORD": "x",
    "OPS_API_DSN": "postgres://u:p@h/db", "OPS_INTAKE_WRITER_DSN": "postgres://u:p@h/db",
    "SUPABASE_PROD_DSN": "postgres://u:p@h/db",
    "TCC_BREAKER_CODEX_PW": "x", "TCC_BREAKER_RO_PW": "x",
    "PGPASSWORD": "x", "X_TOKEN": "x", "Y_KEY": "x", "Z_DSN": "x", "W_SECRET": "x",
}


def test_agent_env_strips_secrets(monkeypatch):
    for k, v in _SECRET_BATTERY.items():
        monkeypatch.setenv(k, v)
    env = agent_runner._agent_env("host")
    for k in _SECRET_BATTERY:
        assert k not in env, f"secret leaked into agent env: {k}"


def test_agent_env_keeps_allowlisted(monkeypatch):
    monkeypatch.setenv("HOME", "/home/olares")
    monkeypatch.setenv("LANG", "C.UTF-8")
    monkeypatch.setenv("LC_ALL", "C.UTF-8")
    monkeypatch.setenv("TERM", "xterm")
    monkeypatch.setenv("TMPDIR", "/tmp")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/home/olares/.config")
    monkeypatch.setenv("SUPABASE_PROD_DSN", "postgres://u:p@h/db")   # secret: must be dropped
    env = agent_runner._agent_env("host")
    assert env["HOME"] == "/home/olares"
    assert env["LANG"] == "C.UTF-8"
    assert env["LC_ALL"] == "C.UTF-8"
    assert env["TERM"] == "xterm"
    assert env["TMPDIR"] == "/tmp"
    assert env["XDG_CONFIG_HOME"] == "/home/olares/.config"
    assert "SUPABASE_PROD_DSN" not in env
    assert env["APEX_JOB_ENV"] == "host"


def test_agent_env_reads_agent_path_as_config_only(monkeypatch):
    monkeypatch.setenv("APEX_JOBS_AGENT_PATH", "/opt/agent/bin")
    env = agent_runner._agent_env("host")
    assert "/opt/agent/bin" in env["PATH"].split(os.pathsep)   # read: on PATH
    assert "APEX_JOBS_AGENT_PATH" not in env                   # but not exported


def test_agent_env_closure_no_unexpected_keys(monkeypatch):
    monkeypatch.setenv("SOME_RANDOM_SECRET_DSN", "postgres://u:p@h/db")
    env = agent_runner._agent_env("host")
    allowed = set(agent_runner._AGENT_ENV_ALLOW) | {"PATH", "APEX_JOB_ENV"}
    assert set(env).issubset(allowed), set(env) - allowed
```

- [ ] **Step 2: Run the tests and verify they FAIL (true red)**

Run (with the Test Runner env sourced as in Global Constraints):
```
... uv run --extra test pytest tests/test_agent_runner.py -k agent_env -v
```
Expected: the four new tests FAIL (not skip, not error):
- `test_agent_env_strips_secrets` -> AssertionError (secrets present in `{**os.environ,...}`)
- `test_agent_env_keeps_allowlisted` -> AssertionError (`SUPABASE_PROD_DSN` present)
- `test_agent_env_reads_agent_path_as_config_only` -> AssertionError (`APEX_JOBS_AGENT_PATH` present)
- `test_agent_env_closure_no_unexpected_keys` -> AttributeError (`_AGENT_ENV_ALLOW` not defined yet) or AssertionError
If they SKIP, the DB env is not sourced -- fix that (Global Constraints Test Runner) before proceeding; a skip is not a red.

- [ ] **Step 3: Add the allowlist constant and rewrite `_agent_env`**

In `packages/apex-jobs/src/apex_jobs/agent_runner.py`, immediately ABOVE the existing `def _agent_env(job_env):` (line 73), insert the constant, then replace the function body. The final state of the region is:

```python
# Exact-name allowlist for the agent/review subprocess env (default-deny). A flat
# set with NO prefix matching, so any new secret-shaped variable is dropped
# automatically -- there is no denylist to keep current.
_AGENT_ENV_ALLOW = frozenset({
    # base runtime
    "HOME", "PATH", "USER", "LOGNAME", "SHELL", "TERM",
    "TMPDIR", "TMP", "TEMP", "TZ", "LANG",
    # locale (exact keys, not an LC_ prefix)
    "LC_ALL", "LC_COLLATE", "LC_CTYPE", "LC_MESSAGES", "LC_MONETARY", "LC_NUMERIC",
    "LC_TIME", "LC_ADDRESS", "LC_IDENTIFICATION", "LC_MEASUREMENT", "LC_NAME",
    "LC_PAPER", "LC_TELEPHONE",
    # XDG base dirs (exact keys, not an XDG_ prefix)
    "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME",
    "XDG_RUNTIME_DIR",
})


def _agent_env(job_env):
    """Subprocess env for the agent/review CLI: a default-deny allowlisted subset of
    os.environ (see _AGENT_ENV_ALLOW) plus the APEX_JOB_ENV marker, with the agent
    bin dir(s) prepended to PATH so `claude` / `codex` (and their node) resolve under
    the non-interactive worker (neither is on the login PATH). The worker's ambient
    secrets (DB passwords, DSNs, tokens) are NOT inherited. APEX_JOBS_AGENT_PATH is
    read only to compute the PATH prepend; it is not exported. Override the bins via
    APEX_JOBS_AGENT_PATH."""
    env = {k: v for k, v in os.environ.items() if k in _AGENT_ENV_ALLOW}
    env["APEX_JOB_ENV"] = job_env
    extra = os.environ.get("APEX_JOBS_AGENT_PATH", _DEFAULT_AGENT_PATH)
    if extra:
        env["PATH"] = extra + os.pathsep + env.get("PATH", "")
    return env
```

- [ ] **Step 4: Run the new tests and verify they PASS**

Run: `... uv run --extra test pytest tests/test_agent_runner.py -k agent_env -v`
Expected: all four new tests PASS, and the two pre-existing `_agent_env` tests (`test_agent_env_prepends_agent_bins_to_path`, `test_agent_env_default_includes_codex_bin`) also PASS -- the `-k agent_env` selector runs all six.

- [ ] **Step 5: Run the full agent_runner test file (regression)**

Run: `... uv run --extra test pytest tests/test_agent_runner.py -v`
Expected: PASS (no regressions in run_agent_job / run_review_job / run_pool / promotion).

- [ ] **Step 6: Commit**

```bash
# host-side, in the worktree
git add packages/apex-jobs/src/apex_jobs/agent_runner.py packages/apex-jobs/tests/test_agent_runner.py
git commit -m "feat(apex-jobs): default-deny allowlist for _agent_env

Agent/review subprocesses no longer inherit the worker's full os.environ
(which sources DB secrets). _agent_env now builds a flat exact-name
allowlisted subset plus the APEX_JOB_ENV marker; PATH prepend unchanged;
APEX_JOBS_AGENT_PATH read-only. Adds strip-battery/keep/closure/read-config
unit tests. worker.py command path intentionally untouched (Part B).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: README agent-section sanitized-env note

**Files:**
- Modify: `packages/apex-jobs/README.md` (add a sentence in the "Durable multi-agent core (`kind='agent'`)" section, lines 65-80; qualify line 41)

**Interfaces:**
- Consumes: the Task 1 behavior (agent/review env is sanitized).
- Produces: nothing code-facing.

- [ ] **Step 1: Qualify the command-worker sentence (line 41)**

Change line 41 from:
```
The subprocess runs with `APEX_JOB_ENV` set to the worker's env.
```
to:
```
The command subprocess runs with `APEX_JOB_ENV` set to the worker's env.
```
(Only add the word "command" -- this line documents `worker.py` command jobs and stays accurate.)

- [ ] **Step 2: Add the agent-section note**

In the "Durable multi-agent core (`kind='agent'`)" section, immediately AFTER the `durability:` bullet (line 76) and BEFORE the `CLI:` bullet (line 77), insert a new bullet:
```
- **env isolation:** agent and review subprocesses receive a **sanitized** env --
  `_agent_env` builds a default-deny allowlisted subset of the worker env (HOME,
  PATH, locale, XDG dirs) plus `APEX_JOB_ENV`; the worker's DB passwords / DSNs /
  tokens are **not** inherited (command jobs, above, still run with the worker env).
```

- [ ] **Step 3: Verify ASCII-only and read back the two edits**

Run (grep, not line numbers -- the insert shifts subsequent lines):
```
grep -cP '[^\x00-\x7F]' packages/apex-jobs/README.md          # expect 0
grep -n "command subprocess runs with" packages/apex-jobs/README.md   # the qualified line 41
grep -n "env isolation" packages/apex-jobs/README.md          # the new agent-section bullet
```
Expected: 0 non-ASCII; one hit for the qualified command-worker line; one hit for the new `env isolation` bullet.

- [ ] **Step 4: Commit**

```bash
git add packages/apex-jobs/README.md
git commit -m "docs(apex-jobs): note sanitized agent/review env; qualify command-worker line

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Review-path defense-in-depth guard test

**Files:**
- Test: `packages/apex-jobs/tests/test_agent_runner.py` (append one DB-backed test)

**Interfaces:**
- Consumes: `agent_runner.run_review_job(job, env, as_, agent_cmd)`, `agent_runner.subprocess`, the `agent_env` fixture, `engine.enqueue/_conn/claim`.
- Produces: nothing code-facing (a regression guard).

- [ ] **Step 1: Write the guard test**

Append to `packages/apex-jobs/tests/test_agent_runner.py`. It mirrors the existing `test_review_job_never_passes_prompt_with_base` harness (monkeypatched `subprocess.run`), but captures the `env=` kwarg instead of argv:

```python
def test_review_job_env_is_sanitized(agent_env, monkeypatch):
    # Defense in depth: the review path (run_review_job) must also receive the
    # sanitized agent env. Both agent + review call sites route through _agent_env.
    base, created, runs = agent_env
    monkeypatch.setenv("HOME", "/home/olares")
    monkeypatch.setenv("SUPABASE_PROD_DSN", "postgres://u:p@h/db")   # planted secret
    created.append("rev-env")
    jid = engine.enqueue(dispatch_id="rev-env", title="x", env_required="host",
                         payload={"review_head": "HEAD"})
    with engine._conn() as c:
        with c.cursor() as cur:
            cur.execute("update jobs.job set kind='agent', target='codex', base_ref=%s "
                        "where id=%s", (base, jid))
        c.commit()
    job = engine.claim(as_="cc", env="host")

    captured = {}
    real_run = agent_runner.subprocess.run

    def fake_run(argv, **kw):
        if argv and argv[0] == "codex":
            captured["env"] = kw.get("env")
            return real_run(["true"], capture_output=True, text=True)
        return real_run(argv, **kw)

    monkeypatch.setattr(agent_runner.subprocess, "run", fake_run)
    agent_runner.run_review_job(job, env="host")
    env = captured["env"]
    assert env is not None
    assert "SUPABASE_PROD_DSN" not in env       # secret stripped on the review path
    assert env["APEX_JOB_ENV"] == "host"
    assert "HOME" in env                         # allowlisted runtime var preserved
```

- [ ] **Step 2: Run it and verify PASS**

Run: `... uv run --extra test pytest tests/test_agent_runner.py::test_review_job_env_is_sanitized -v`
Expected: PASS against Task 1's sanitizer. (Against pre-Task-1 code this test is red -- `SUPABASE_PROD_DSN` would be present -- so it genuinely guards the review path, it does not merely restate the impl.)

- [ ] **Step 3: Commit**

```bash
git add packages/apex-jobs/tests/test_agent_runner.py
git commit -m "test(apex-jobs): guard that run_review_job env is sanitized too

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Post-build agent-env smoke (host CLIs under the real sanitized env)

**Files:**
- None (a verification step; produces recorded evidence, no code change).

**Interfaces:**
- Consumes: `agent_runner._agent_env("host")`, the real `claude` / `codex` binaries on the host.

- [ ] **Step 1: Run the smoke under the worker env (secrets present, then stripped)**

Host-side, source the worker env FIRST so `os.environ` actually holds the secrets the sanitizer must strip, then confirm both CLIs still launch under the sanitized env:
```
set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a
cd /home/olares/code/apex/apex-secrets-agent-env/packages/apex-jobs
uv run python - <<'PY'
import shutil, subprocess
from apex_jobs import agent_runner
env = agent_runner._agent_env("host")
leaked = [k for k in env if k.endswith(("_PASSWORD", "_DSN", "_TOKEN", "_KEY",
          "_PW", "_SECRET")) or k == "PGPASSWORD"]
assert not leaked, f"secret-shaped keys survived: {leaked}"
for name in ("claude", "codex"):
    # resolve via the SANITIZED env's PATH (not the parent's) so the smoke proves
    # the sanitized env can both locate AND run the CLI.
    exe = shutil.which(name, path=env["PATH"])
    assert exe, f"{name} not found on sanitized PATH"
    r = subprocess.run([exe, "--version"], env=env, capture_output=True, text=True)
    out = (r.stdout or r.stderr).strip().splitlines()[:1]
    print(name, "rc", r.returncode, out)
    assert r.returncode == 0, (name, r.stderr[:200])
print("SMOKE OK")
PY
```
Expected: `leaked` is empty (no secret-shaped key survived even with the worker env sourced); `claude` resolves + prints its version with rc 0; `codex` resolves + prints its version with rc 0; final line `SMOKE OK`.

- [ ] **Step 2: Record the smoke result**

Capture the Step 1 output (value-silent -- it prints only key-shapes, rc, and version strings) into the task/PR notes as the executed proof that turns the A.7 host baseline into an executed verification. No commit required unless the reviewer wants the transcript appended to `ops/orchestration/`.

---

## Self-Review

**1. Spec coverage.**
- A.1 behavior (default-deny, marker, PATH prepend, APEX_JOBS_AGENT_PATH read-only) -> Task 1 Step 3.
- A.2 allowlist verbatim -> Global Constraints + Task 1 Step 3 constant.
- A.4 files: agent_runner.py (Task 1), README (Task 2), tests (Tasks 1 + 3).
- A.5 tests: strip-battery/keep/read-config/closure (Task 1), regression 150/160 (Task 1 Step 4-5), review-path #6 (Task 3), post-build smoke #7 (Task 4).
- A.4 docstring correction -> Task 1 Step 3. README target correction -> Task 2 (agent section, not line 41).
- A.7 executed proof -> Task 4.
- Part B: not present as build tasks (Global Constraints). worker.py untouched. Covered.

**2. Placeholder scan.** No TBD/TODO; every code step shows complete code; every run step shows the command + expected output.

**3. Type consistency.** `_AGENT_ENV_ALLOW` (frozenset) and `_agent_env(job_env) -> dict` are used identically in Task 1 (definition + unit tests), Task 3 (guard test reads the returned env), and Task 4 (smoke reads the returned env). The two existing call sites are unchanged. Test helper names (`agent_env` fixture, `engine.enqueue/_conn/claim`) match the current test file.
