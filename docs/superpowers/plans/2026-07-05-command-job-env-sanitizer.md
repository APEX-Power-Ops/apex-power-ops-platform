# apex-jobs Command-Job Env Sanitizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give apex-jobs kind='command' jobs a default-deny sanitized subprocess env so a command job no longer inherits the worker's secrets, keeping worker.py free of any secret-broker logic.

**Architecture:** A new shared helper `_env.sanitized_env` builds a subprocess env from a default-deny allowlist (exact names + `LC_`/`XDG_` prefixes) plus the `APEX_JOB_ENV` marker. `worker._run_command_job` uses it in place of `{**os.environ, ...}`. A command job that needs a secret re-injects it in-child via `infra/infisical/inject.sh`. The agent path (`agent_runner.py`) is out of scope (Part A / PR #63).

**Tech Stack:** Python 3, apex-jobs (`uv`-managed, own `pyproject.toml`), pytest (value-silent).

**Spec:** `docs/superpowers/specs/2026-07-05-command-job-env-infisical-cutover-design.md` (rev 3, `19a92a39`).

**Lane context (already set up):** branch `secrets/command-job-env-cutover`, host worktree `/home/olares/code/apex/apex-secrets-command-env`, off main `7bf983ec`. Do NOT create a new worktree.

## Global Constraints

- **Allowlist (verbatim, `_env.py`):** `ENV_ALLOW_EXACT = frozenset({"HOME","PATH","USER","LOGNAME","SHELL","TERM","TMPDIR","TMP","TEMP","TZ","LANG"})`; `ENV_ALLOW_PREFIXES = ("LC_","XDG_")`; membership = `name in ENV_ALLOW_EXACT or name.startswith(ENV_ALLOW_PREFIXES)`.
- **Value-silence (load-bearing):** never reference `env`, `set(env)`, `env[...]`, or `env.get(...)` INSIDE an `assert`. Compute plain locals (booleans / sorted NAME-lists / the marker string) BEFORE the assert; assert only on those. Placeholder values (`"PLACEHOLDER-TEST-VALUE"`) are never asserted on.
- **No agent_runner.py edit** (PR #63's file). **No OPS_* cutover** (deferred, spec B.8). **No `secret-audit.sh` change.**
- **Host-canonical single-writer:** author files locally, scp ONLY to the `apex-secrets-command-env` worktree, run + commit host-side over `ssh olares-mesh`. ASCII-only added lines.
- **Test recipe (host, exact):** the session-autouse `_schema` fixture SKIPS the suite without DB creds, so source the MAIN checkout's `infra/.env`; run FROM the apex-jobs package dir (apex-jobs has its own pyproject; the repo root is not a uv workspace):
  ```
  ssh olares-mesh 'cd /home/olares/code/apex/apex-secrets-command-env/packages/apex-jobs; \
    set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
    export PATH=$HOME/.local/bin:$PATH; \
    APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest <TARGETS> -rN -q'
  ```
  Check the exit code UNMASKED (no `| tail` pipe). **exit 0 with any test SKIPPED is a FAIL for this lane** (verify the summary shows PASSED and zero skipped for the target files).
- **No prod/dev data mutation:** tests touch only the disposable `orchestration_test` DB (the autouse `_schema` fixture applies downs/ups + truncates it).
- **Commit trailer (every commit):** `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

---

### Task 1: `_env.sanitized_env` helper + unit tests

**Files:**
- Create: `packages/apex-jobs/src/apex_jobs/_env.py`
- Test: `packages/apex-jobs/tests/test_env.py`

**Interfaces:**
- Consumes: nothing (leaf module; imports only `os`).
- Produces: `apex_jobs._env.sanitized_env(job_env, extra_path=None) -> dict`; `ENV_ALLOW_EXACT: frozenset`; `ENV_ALLOW_PREFIXES: tuple`.

- [ ] **Step 1: Write the failing unit tests**

Create `packages/apex-jobs/tests/test_env.py`:

```python
"""Unit tests for the apex-jobs subprocess env policy (_env.sanitized_env).

Value-silence: assertions are on precomputed booleans / sorted NAME-lists / the
marker string only -- never env, set(env), env[...], or env.get(...) inside an
assert (pytest would render real values on failure). Battery values are fixed
placeholders, never asserted on.
"""
import os

from apex_jobs import _env

_SECRET_BATTERY = [
    "APEX_JOBS_PGPASSWORD", "DEV_PG_PASSWORD", "OPS_API_DSN",
    "OPS_INTAKE_WRITER_DSN", "SUPABASE_PROD_DSN", "PGPASSWORD",
    "TCC_BREAKER_RO_PW", "TCC_BREAKER_CODEX_PW", "GITHUB_TOKEN",
    "AWS_SECRET_ACCESS_KEY", "INFISICAL_CLIENT_SECRET",
]


def test_sanitized_env_strips_secret_names(monkeypatch):
    for k in _SECRET_BATTERY:
        monkeypatch.setenv(k, "PLACEHOLDER-TEST-VALUE")
    env = _env.sanitized_env("host")
    leaked = sorted(set(_SECRET_BATTERY) & set(env))
    assert leaked == []


def test_sanitized_env_keeps_basics_and_marker(monkeypatch):
    monkeypatch.setenv("HOME", "/home/olares")
    env = _env.sanitized_env("staging")
    home_present = "HOME" in env
    path_present = "PATH" in env
    marker = env.get("APEX_JOB_ENV")
    assert home_present is True
    assert path_present is True
    assert marker == "staging"


def test_sanitized_env_keeps_locale_and_xdg_by_prefix(monkeypatch):
    monkeypatch.setenv("LC_TIME", "en_US.UTF-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/home/olares/.config")
    env = _env.sanitized_env("host")
    lc_present = "LC_TIME" in env
    xdg_present = "XDG_CONFIG_HOME" in env
    assert lc_present is True
    assert xdg_present is True


def test_sanitized_env_command_path_no_prepend(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    env = _env.sanitized_env("host")
    path_unchanged = env.get("PATH") == os.environ.get("PATH")
    assert path_unchanged is True


def test_sanitized_env_extra_path_prepends(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    env = _env.sanitized_env("host", extra_path="/opt/agent/bin")
    prepended = env.get("PATH", "").startswith("/opt/agent/bin" + os.pathsep)
    assert prepended is True
```

- [ ] **Step 2: Run the tests to verify they fail**

```
ssh olares-mesh 'cd /home/olares/code/apex/apex-secrets-command-env/packages/apex-jobs; \
  set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
  export PATH=$HOME/.local/bin:$PATH; \
  APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest tests/test_env.py -rN -q'
```
Expected: collection error / FAIL -- `ModuleNotFoundError: No module named 'apex_jobs._env'`.

- [ ] **Step 3: Create the helper**

Create `packages/apex-jobs/src/apex_jobs/_env.py`:

```python
"""apex-jobs subprocess env policy -- a default-deny allowlist (exact names plus
two provably-safe standard namespace prefixes) for the environment handed to job
child processes. A secret sourced into the worker's own environment (*_PASSWORD /
*_DSN / *_TOKEN / *_KEY / service keys) is never inherited by a child via the
process environment -- it is dropped by construction. On-disk credential stores
under HOME (e.g. ~/.pgpass, ~/.aws/credentials) remain reachable and are out of
scope for this env-policy helper; filesystem isolation is a separate concern.
"""
import os

# Exact names kept: home/user/shell basics, temp dirs, timezone, base locale.
ENV_ALLOW_EXACT = frozenset({
    "HOME", "PATH", "USER", "LOGNAME", "SHELL", "TERM",
    "TMPDIR", "TMP", "TEMP", "TZ", "LANG",
})

# Standard non-secret namespaces kept by prefix: POSIX locale (LC_*) and XDG
# base-directory (XDG_*). A prefix admits future members with no code change;
# no platform secret lives under either namespace.
ENV_ALLOW_PREFIXES = ("LC_", "XDG_")


def _allowed(name):
    return name in ENV_ALLOW_EXACT or name.startswith(ENV_ALLOW_PREFIXES)


def sanitized_env(job_env, extra_path=None):
    """Sterile subprocess env: the allowlisted names from os.environ plus the
    APEX_JOB_ENV marker. If extra_path is given, prepend it to PATH (the agent
    path uses this for the claude/codex bin dirs; command jobs pass None)."""
    env = {k: v for k, v in os.environ.items() if _allowed(k)}
    env["APEX_JOB_ENV"] = job_env
    if extra_path:
        # filter(None, ...) drops an absent PATH so no trailing os.pathsep (an
        # empty PATH element = CWD) is ever emitted.
        env["PATH"] = os.pathsep.join(filter(None, [extra_path, env.get("PATH")]))
    return env
```

- [ ] **Step 4: Run the tests to verify they pass**

```
ssh olares-mesh 'cd /home/olares/code/apex/apex-secrets-command-env/packages/apex-jobs; \
  set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
  export PATH=$HOME/.local/bin:$PATH; \
  APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest tests/test_env.py -rN -q'
```
Expected: `5 passed`, 0 skipped. If the summary shows any `skipped`, that is a FAIL (DB creds absent) -- fix the source before trusting green.

- [ ] **Step 5: Commit (host-canonical)**

scp both files to the worktree, then:
```
ssh olares-mesh 'cd /home/olares/code/apex/apex-secrets-command-env; \
  git add packages/apex-jobs/src/apex_jobs/_env.py packages/apex-jobs/tests/test_env.py; \
  git commit -m "feat(apex-jobs): add _env.sanitized_env default-deny env policy + tests

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

### Task 2: Wire worker command jobs to the sanitizer + guard test + README note

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/worker.py` (remove `import os` at line 9; add `from . import _env`; change the `_run_command_job` subprocess `env=` at line 30)
- Test: `packages/apex-jobs/tests/test_worker.py` (append one guard test)
- Modify: `packages/apex-jobs/README.md` (`## Worker` section)

**Interfaces:**
- Consumes: `apex_jobs._env.sanitized_env` (Task 1).
- Produces: `worker._run_command_job` now builds its subprocess env via `_env.sanitized_env(env)`.

- [ ] **Step 1: Write the failing guard test**

Append to `packages/apex-jobs/tests/test_worker.py`:

```python
def test_command_job_child_env_is_sanitized(monkeypatch):
    # Self-seed a secret-shaped probe so red-first is INTRINSIC (never borrowed
    # from ambient infra/.env, and survives any future cutover).
    monkeypatch.setenv("PROBE_LEAK_DSN", "PLACEHOLDER-TEST-VALUE")
    monkeypatch.setenv("HOME", "/home/olares")
    captured = {}

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    def _fake_run(command, **kwargs):
        captured["env"] = kwargs.get("env")
        return _Proc()

    from apex_jobs import worker
    monkeypatch.setattr(worker.subprocess, "run", _fake_run)
    monkeypatch.setattr(worker.engine, "start", lambda *a, **k: "run-sentinel")
    monkeypatch.setattr(worker.engine, "report", lambda *a, **k: "succeeded")

    worker._run_command_job(
        {"id": 1, "dispatch_id": "guard", "payload": {"command": "true"}},
        "host", "cc",
    )
    child = captured["env"]
    secret_present = "PROBE_LEAK_DSN" in child
    home_present = "HOME" in child
    marker = child.get("APEX_JOB_ENV")
    assert secret_present is False
    assert home_present is True
    assert marker == "host"
```

Note: `secret_present`, `home_present`, and `marker` are computed on the captured `child` dict BEFORE the asserts; no `env[...]`/`env.get` appears inside an assert (value-silence).

- [ ] **Step 2: Run the guard test to verify it fails**

```
ssh olares-mesh 'cd /home/olares/code/apex/apex-secrets-command-env/packages/apex-jobs; \
  set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
  export PATH=$HOME/.local/bin:$PATH; \
  APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest \
  tests/test_worker.py::test_command_job_child_env_is_sanitized -rN -q'
```
Expected: `1 failed` -- `AssertionError` on `assert secret_present is False` (the current `{**os.environ, "APEX_JOB_ENV": env}` copies the self-seeded `PROBE_LEAK_DSN` into the child env).

- [ ] **Step 3: Change worker.py to use the sanitizer**

In `packages/apex-jobs/src/apex_jobs/worker.py`:

(a) Remove the now-unused `import os` (line 9 -- its only use was the env spread being replaced).

(b) Add the helper import next to the engine import:
```python
from . import engine
from . import _env
```

(c) Replace the subprocess `env=` kwarg in `_run_command_job`:
```python
    proc = subprocess.run(
        command, shell=True, capture_output=True, text=True,
        env=_env.sanitized_env(env),
    )
```
(was `env={**os.environ, "APEX_JOB_ENV": env}`.)

- [ ] **Step 4: Run the guard test + the existing worker tests to verify green**

```
ssh olares-mesh 'cd /home/olares/code/apex/apex-secrets-command-env/packages/apex-jobs; \
  set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
  export PATH=$HOME/.local/bin:$PATH; \
  APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest \
  tests/test_worker.py tests/test_env.py -rN -q'
```
Expected: all pass (the 4 existing worker tests + the guard + the 5 helper tests), 0 skipped. The existing worker tests still pass because `sanitized_env` keeps HOME/PATH so `echo`/`exit`/`true` resolve normally.

- [ ] **Step 5: Add the README env-isolation note**

In `packages/apex-jobs/README.md`, `## Worker` section, do NOT rewrite the existing line `The subprocess runs with APEX_JOB_ENV set to the worker's env.` -- insert AFTER it:

```markdown
The command subprocess runs with a **sanitized, default-deny environment**
(`_env.sanitized_env`): only an allowlist of non-secret names (HOME, PATH,
locale/XDG) plus the `APEX_JOB_ENV` marker passes through, so a command job does
not inherit the worker's secrets. A command job that needs a secret must wrap its
own command, e.g. `infra/infisical/inject.sh dev -- <db command>` (or
`dev-psql.sh`), so the secret reaches the child process only.
```

Also bump the `## Tests (54)` heading to the new total (run the suite once and use the collected count; adding 6 tests makes it `## Tests (60)` unless the base count has drifted -- use the actual collected number).

- [ ] **Step 6: Commit (host-canonical)**

scp the three files to the worktree, then:
```
ssh olares-mesh 'cd /home/olares/code/apex/apex-secrets-command-env; \
  git add packages/apex-jobs/src/apex_jobs/worker.py packages/apex-jobs/tests/test_worker.py packages/apex-jobs/README.md; \
  git commit -m "feat(apex-jobs): sanitize command-job subprocess env; guard test + README

Command jobs no longer inherit the worker environment; a DB command job wraps
its own command with infra/infisical/inject.sh. Closes the command-job
inheritance path (the agent path is Part A / PR #63).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

## Final verification (before finishing the branch)

- [ ] Run the full apex-jobs suite value-silent, exit code UNMASKED, 0 skipped:
```
ssh olares-mesh 'cd /home/olares/code/apex/apex-secrets-command-env/packages/apex-jobs; \
  set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
  export PATH=$HOME/.local/bin:$PATH; \
  APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest -rN -q; echo "rc=$?"'
```
Expected: all pass, `rc=0`, 0 skipped. (Any `skipped` = DB-creds/source failure = FAIL, not green.)
- [ ] `git -C <worktree> diff --stat main` shows only: `_env.py` (new), `test_env.py` (new), `worker.py` (modified), `test_worker.py` (modified), `README.md` (modified). NO `agent_runner.py`, NO `secret-audit.sh`, NO `infra/.env`.
- [ ] Cross-engine whole-branch Codex review (per Part A precedent) before finishing.

## Self-Review

**Spec coverage:** B.2 helper -> Task 1. B.3 worker change -> Task 2 Step 3. B.4 helper tests -> Task 1 Step 1; B.4 guard (self-seeded probe, pinned fake proc) -> Task 2 Step 1; B.4 skip-guard -> Global Constraints + every run step. B.5 README note -> Task 2 Step 5. B.6 (prefix, boundaries) is design rationale, no code. B.7 verification -> Final verification. B.8 cutover -> explicitly out (Global Constraints). Discipline -> Global Constraints.

**Placeholder scan:** none -- every code block is complete; the only non-literal is the README test count, which is pinned to "the actual collected number" with the expected 60.

**Type consistency:** `sanitized_env(job_env, extra_path=None)` used identically in Task 1 (definition) and Task 2 (`_env.sanitized_env(env)`); `ENV_ALLOW_EXACT` / `ENV_ALLOW_PREFIXES` names match the tests; the guard's `_Proc.returncode/stdout/stderr` match the real `proc.returncode` / `proc.stdout[-4000:]` / `proc.stderr[-4000:]` reads in `_run_command_job`.
