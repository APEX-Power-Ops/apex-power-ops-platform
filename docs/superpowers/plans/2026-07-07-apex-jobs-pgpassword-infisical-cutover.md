# APEX_JOBS_PGPASSWORD Infisical Cutover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut the apex-jobs worker-ledger password (`APEX_JOBS_PGPASSWORD`) from the `infra/.env` cache to Infisical `dev`-env injection, and shrink the audit cache-allowlist accordingly.

**Architecture:** A thin injected launcher (mirroring `dev-psql.sh`) runs apex-jobs under `inject.sh dev`. The consumer (`db.py:resolve_dsn`) is unchanged - it already reads `APEX_JOBS_PGPASSWORD`. Hygiene state moves the NAME from `secret-audit.sh`'s cache-allowlist to `.managed-secrets`, atomically with the operator-OOB `infra/.env` removal, so the audit never goes red on `main`.

**Tech Stack:** POSIX/bash + shellcheck; Python 3.12 + pytest (uv); self-hosted Infisical (`inject.sh`, project 985aac34...).

## Global Constraints

- Host-canonical single-writer over mesh: author locally -> `scp` per file -> run/commit host-side on worktree `apex-secrets-apex-jobs-pw` (branch `secrets/apex-jobs-pgpassword-cutover`, off `main 58d33c34`).
- ASCII-only added lines (audit each edited file: `LC_ALL=C grep -nP "[^\x00-\x7F]"` returns nothing).
- Value-silent: never echo or assert on a real secret value; tests use non-secret SENTINELs and assert on booleans, never an env dump.
- NEVER sed-edit the live `infra/.env` credential file - its `APEX_JOBS_PGPASSWORD` removal is operator-OOB; the AI verifies by NAME only.
- Any edited shell file must pass `shellcheck` rc=0 (whole file).
- dev-only (`orchestration_dev`); no prod schema; no change to `apex_jobs/db.py`.
- Ordering is load-bearing: remove-from-`.env` -> shrink `ENV_ALLOWED_KEYS` -> arm `.managed-secrets`, as one atomic cutover (Tasks 3+4).
- Whole-branch Codex cross-engine review before finishing (IRP).

---

## File Structure

- Create `infra/infisical/apex-jobs.sh` - injected launcher (dev env).
- Create `infra/infisical/test_apex_jobs_launcher.sh` - launcher dispatch test (stubs `inject.sh`).
- Create `packages/apex-jobs/tests/test_dsn_resolution.py` - `resolve_dsn` contract lock (value-silent).
- Modify `infra/secret-audit.sh` line 67 - drop `APEX_JOBS_PGPASSWORD` from `ENV_ALLOWED_KEYS` default.
- Modify `infra/database/migrations/records/test_secret_audit_env_allowlist.sh` - flip `APEX_JOBS_PGPASSWORD` from allowed-cache to managed/rejected.
- Modify `infra/infisical/.managed-secrets` - arm `APEX_JOBS_PGPASSWORD` (LAST).
- Modify `packages/apex-jobs/README.md` - injected-launch runbook.
- (operator-OOB) `infra/.env` - remove the `APEX_JOBS_PGPASSWORD` line.

---

### Task 1: Injected launcher `apex-jobs.sh`

**Files:**
- Create: `infra/infisical/apex-jobs.sh`
- Test: `infra/infisical/test_apex_jobs_launcher.sh`

**Interfaces:**
- Produces: `infra/infisical/apex-jobs.sh` that execs `inject.sh dev -- bash -c 'cd "$1" && shift && exec uv run apex-jobs "$@"' _ <pkgdir> "$@"`.

- [ ] **Step 1: Write the failing dispatch test** (`test_apex_jobs_launcher.sh`), modeled on `test_secret_audit_env_allowlist.sh` style (plain shell, `say`/PASS/FAIL, exit rc):

```bash
#!/usr/bin/env bash
# Proves apex-jobs.sh dispatches through inject.sh dev with passthrough args,
# without invoking real Infisical/uv. Value-silent.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
say() { printf '%s\n' "$*"; }
fail=0
stub="$(mktemp -d)"
# stub inject.sh: record argv, do not exec anything real
cat > "$stub/inject.sh" <<'STUB'
#!/usr/bin/env bash
printf 'INJECT_ARGV:'; printf ' %s' "$@"; printf '\n'
STUB
chmod +x "$stub/inject.sh"
# run launcher with the stub dir shadowing the real inject.sh
out="$(cd "$HERE" && PATH="$stub:$PATH" bash "$HERE/apex-jobs.sh" review-run --review-head X --base-ref Y 2>&1 || true)"
if printf '%s' "$out" | grep -qF 'INJECT_ARGV: dev -- bash -c'; then
  say "PASS  launcher dispatched via inject.sh dev"; else
  say "FAIL  launcher did not dispatch via inject.sh dev: $out"; fail=1; fi
if printf '%s' "$out" | grep -qF 'review-run --review-head X --base-ref Y'; then
  say "PASS  launcher forwarded verb + args"; else
  say "FAIL  launcher dropped args"; fail=1; fi
rm -rf "$stub"
[[ "$fail" == 0 ]] && { say "RESULT: launcher fixture PASSED"; exit 0; } || { say "RESULT: launcher fixture FAILED"; exit 1; }
```

- [ ] **Step 2: Run it - verify RED** (launcher missing)

Run: `ssh olares-mesh 'cd <wt> && bash infra/infisical/test_apex_jobs_launcher.sh'`
Expected: FAIL (apex-jobs.sh not found / no dispatch line).

- [ ] **Step 3: Create the launcher** `infra/infisical/apex-jobs.sh`:

```bash
#!/usr/bin/env bash
# apex-jobs.sh - run apex-jobs with dev secrets injected from Infisical, NOT the
# standalone infra/.env cache. Mirrors infra/infisical/dev-psql.sh.
# Usage: infra/infisical/apex-jobs.sh <verb> [args...]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG="$HERE/../../packages/apex-jobs"
exec "$HERE/inject.sh" dev -- bash -c 'cd "$1" && shift && exec uv run apex-jobs "$@"' _ "$PKG" "$@"
```

- [ ] **Step 4: Run test - verify GREEN**; then `shellcheck infra/infisical/apex-jobs.sh infra/infisical/test_apex_jobs_launcher.sh` rc=0; ASCII audit both.

- [ ] **Step 5: Commit** (`git add` the two files; message `feat(secrets): apex-jobs.sh injected launcher (dev env) + dispatch test`; Co-Authored-By trailer).

---

### Task 2: `resolve_dsn` contract lock (value-silent)

**Files:**
- Test: `packages/apex-jobs/tests/test_dsn_resolution.py`

**Interfaces:**
- Consumes: `apex_jobs.db.resolve_dsn()` (unchanged).

Note: `resolve_dsn` already prefers `APEX_JOBS_PGPASSWORD`; this is a **regression/contract lock** (guards the injected var wins), so it passes on first run - acceptable characterization, not new-feature RED.

- [ ] **Step 1: Write the test** (uses non-secret SENTINELs; asserts on booleans, no connection):

```python
import importlib, os
import apex_jobs.db as db

def _dsn(env):
    old = dict(os.environ)
    try:
        for k in ("APEX_JOBS_DSN", "APEX_JOBS_PGPASSWORD", "DEV_PG_PASSWORD"):
            os.environ.pop(k, None)
        os.environ.update(env)
        return db.resolve_dsn()
    finally:
        os.environ.clear(); os.environ.update(old)

def test_injected_var_used_when_dev_pg_unset():
    dsn = _dsn({"APEX_JOBS_PGPASSWORD": "SENTINEL_A"})
    assert "dbname=orchestration_dev" in dsn
    assert "user=orchestration" in dsn
    assert ("password=SENTINEL_A" in dsn) is True  # boolean, sentinel not a real secret

def test_apex_jobs_pw_wins_over_dev_pg():
    dsn = _dsn({"APEX_JOBS_PGPASSWORD": "SENTINEL_A", "DEV_PG_PASSWORD": "SENTINEL_B"})
    assert ("password=SENTINEL_A" in dsn) is True
    assert ("SENTINEL_B" in dsn) is False
```

- [ ] **Step 2: Run** `ssh olares-mesh 'cd <wt>/packages/apex-jobs && APEX_JOBS_DB=orchestration_test uv run --extra test pytest tests/test_dsn_resolution.py -q'`; Expected: PASS (contract holds). ASCII audit.

- [ ] **Step 3: Commit** (`test(apex-jobs): lock resolve_dsn injected-var-wins contract (value-silent)`).

---

### Task 3: Audit cache-allowlist shrink + test flip (RED -> GREEN)

**Files:**
- Modify: `infra/database/migrations/records/test_secret_audit_env_allowlist.sh`
- Modify: `infra/secret-audit.sh` (line 67)

- [ ] **Step 1: Flip the test first.** In `test_secret_audit_env_allowlist.sh`:
  - Remove `APEX_JOBS_PGPASSWORD` from the "exact allowed keys" fixture and its acknowledge loop: `for key in DEV_PG_PASSWORD APEX_JOBS_PGPASSWORD` -> `for key in DEV_PG_PASSWORD`, and drop the `printf 'APEX_JOBS_PGPASSWORD=%s\n' "$jobs_pw"` fixture line.
  - Add a managed-rejection assertion: a fixture `.env` containing `APEX_JOBS_PGPASSWORD=<sentinel>` now yields exit 1 with `infra/.env non-allowlisted key: APEX_JOBS_PGPASSWORD` (it left the default allowlist).

- [ ] **Step 2: Run it - verify RED** against the current `secret-audit.sh` (which still allowlists `APEX_JOBS_PGPASSWORD`): the managed-rejection assert FAILs.

Run: `ssh olares-mesh 'cd <wt> && bash infra/database/migrations/records/test_secret_audit_env_allowlist.sh'`
Expected: FAIL.

- [ ] **Step 3: Shrink the allowlist.** In `infra/secret-audit.sh:67`:

```bash
# old
ENV_ALLOWED_KEYS="${APEX_ENV_ALLOWED_KEYS:-DEV_PG_PASSWORD APEX_JOBS_PGPASSWORD}"
# new
ENV_ALLOWED_KEYS="${APEX_ENV_ALLOWED_KEYS:-DEV_PG_PASSWORD}"
```

- [ ] **Step 4: Run test - verify GREEN**; `shellcheck infra/secret-audit.sh infra/database/migrations/records/test_secret_audit_env_allowlist.sh` rc=0; ASCII audit both.

- [ ] **Step 5: Commit** (`refactor(secrets): drop APEX_JOBS_PGPASSWORD from cache allowlist + flip audit test`). Do NOT arm `.managed-secrets` yet (Task 4).

---

### PREREQ GATE (operator-OOB, before Task 4)

- [ ] Operator stores `APEX_JOBS_PGPASSWORD` in Infisical project 985aac34... env `dev`.
- [ ] Operator removes the `APEX_JOBS_PGPASSWORD=...` line from `infra/.env`.
- [ ] AI verifies value-silently: `grep -c '^APEX_JOBS_PGPASSWORD=' infra/.env` == 0, and `DEV_PG_PASSWORD` / `SUPABASE_PROD_DSN` / `TCC_BREAKER_*` still present BY NAME (`grep -c '^<NAME>='` == 1 each). No values printed.

---

### Task 4: Wet cutover - arm `.managed-secrets` + verify audit green (operator-gated)

**Files:**
- Modify: `infra/infisical/.managed-secrets`

- [ ] **Step 1: Injected round-trip proof (value-silent).** With `DEV_PG_PASSWORD` unset in the calling shell, confirm the injected launch resolves + connects:

Run: `ssh olares-mesh 'cd <wt> && env -u DEV_PG_PASSWORD infra/infisical/apex-jobs.sh status'` (or a read-only verb)
Expected: connects to `orchestration_dev` (no error, no value printed).

- [ ] **Step 2: Arm the name.** Append `APEX_JOBS_PGPASSWORD` to `infra/infisical/.managed-secrets` (name only, one per line).

- [ ] **Step 3: Verify NO audit regression against the REAL `infra/.env`** (run from the MAIN worktree - the lane worktree has no `infra/.env`; it is a per-worktree gitignored cache).

Baseline is `rc=1`: Check 1b FAILs 3 pre-existing PARKED keys (`TCC_BREAKER_RO_PW`, `TCC_BREAKER_CODEX_PW`, `SUPABASE_PROD_DSN`) - OUT OF SCOPE. Success = that FAIL set is UNCHANGED and `APEX_JOBS_PGPASSWORD` adds zero findings. Verify the shrunk allowlist against the real `.env` WITHOUT editing main, via the `:67` override:

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && APEX_ENV_ALLOWED_KEYS="DEV_PG_PASSWORD" bash infra/secret-audit.sh'`
Expected: Check 1b PASSes `DEV_PG_PASSWORD`, FAILs ONLY the 3 parked keys; no `APEX_JOBS_PGPASSWORD` finding. And `grep -c '^APEX_JOBS_PGPASSWORD=' <each of the 3 caches>` == 0 (drift-clean). Do NOT expect `rc=0` (parked keys keep it 1). Full colocated confirmation (real `.env` + armed `.managed-secrets` + shrunk script together) is a post-merge run on `main`.

- [ ] **Step 4: Commit** (`chore(secrets): arm APEX_JOBS_PGPASSWORD in .managed-secrets (post-cutover)`).

---

### Task 5: README launch runbook

**Files:**
- Modify: `packages/apex-jobs/README.md`

- [ ] **Step 1:** Replace the "no cutover yet" launch note with the injected launcher: run apex-jobs via `infra/infisical/apex-jobs.sh <verb>` (or `inject.sh dev -- uv run apex-jobs`), and state that `APEX_JOBS_PGPASSWORD` is now Infisical-managed (dev env), no longer in `infra/.env`.
- [ ] **Step 2:** ASCII audit; commit (`docs(apex-jobs): injected-launch runbook post-cutover`).

---

### Task 6: Whole-branch Codex cross-engine review (IRP)

- [ ] **Step 1:** Run the wired front door against the branch:

```
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform/packages/apex-jobs && \
  set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
  export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH; \
  export APEX_JOBS_REPO=/home/olares/code/apex/apex-power-ops-platform; \
  APEX_JOBS_DB=orchestration_dev uv run apex-jobs review-run \
    --review-head secrets/apex-jobs-pgpassword-cutover --base-ref main --json'
```

- [ ] **Step 2:** Fold findings; fix Critical/Important; re-review if needed.
- [ ] **Step 3:** Finish via superpowers:finishing-a-development-branch (operator lean: push + PR, independent merge timing).
