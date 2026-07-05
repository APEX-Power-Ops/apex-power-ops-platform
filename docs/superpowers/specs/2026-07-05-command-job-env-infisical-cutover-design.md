# Secret-handling cleanup -- Part B: command-job env sanitizer + OPS_* Infisical cutover

**Status:** Rev 1, spec-review gate; pending operator approval after the IRP audit.

**Goal:** Close the last full-parent-environment inheritance path in apex-jobs
(the kind='command' worker path) with a default-deny sanitized env, and prove
the Infisical cutover mechanic end-to-end on the two ready orphan DSNs
(`OPS_API_DSN`, `OPS_INTAKE_WRITER_DSN`) -- remove from cache, arm the NAME in
`.managed-secrets`, verify the drift guard.

**Architecture:** Two independent deliverables under one lane. (1) A small shared
env-policy helper (`_env.py`) that worker.py uses to build a sterile subprocess
env for command jobs; a DB command job re-injects its own secret in-child via
`infra/infisical/inject.sh`, so worker.py never becomes a secret broker. (2) An
operator-gated, value-silent cutover of the two Infisical-reconciled OPS DSNs
from the `infra/.env` cache to Infisical-only, guarded by `secret-audit.sh`
Check 1c. The two deliverables share no code: the sanitizer never reads the OPS
DSNs; the cutover never touches worker.py.

**Tech stack:** Python 3 (apex-jobs, `uv`-managed), pytest (value-silent),
bash (Infisical wrappers + `secret-audit.sh`), self-hosted Infisical
(mesh-only, project `985aac34-9665-423b-b472-78ddbd707ca7`).

**Lane:** branch `secrets/command-job-env-cutover`, host worktree
`/home/olares/code/apex/apex-secrets-command-env`, off main `7bf983ec`.

---

## B.1 Scope and non-goals

**In scope**
- New `packages/apex-jobs/src/apex_jobs/_env.py` (allowlist + `sanitized_env`).
- `packages/apex-jobs/src/apex_jobs/worker.py`: `_run_command_job` uses
  `sanitized_env` instead of `{**os.environ, ...}`.
- Value-silent tests for the helper and the command-job env path.
- README env-isolation note for the command-job section.
- Cutover of `OPS_API_DSN` + `OPS_INTAKE_WRITER_DSN` only: consumer gate ->
  operator cache removal -> arm NAME in `.managed-secrets` -> drift verify.

**Explicit non-goals (do NOT do in this lane)**
- Do NOT modify `agent_runner.py` (that is PR #63 / Part A's file; keep it
  clean and the lanes independent). The DRY-reconcile that points the agent
  path at `_env.sanitized_env` is a noted post-#63 follow-up, not this lane.
- Do NOT build a `db-run.sh` (YAGNI -- there are no DB command jobs today; a
  future one uses the existing `inject.sh` / `dev-psql.sh`).
- Do NOT add a per-job `env_secrets` broker to worker.py.
- Do NOT cut over `DEV_PG_PASSWORD` (sourced by ~30 lane test runbooks),
  `APEX_JOBS_PGPASSWORD` (worker's own ledger password; needs a launch
  wrapper), `TCC_BREAKER_RO_PW` / `TCC_BREAKER_CODEX_PW` (not yet in Infisical),
  or `SUPABASE_PROD_DSN` (prod-only; the active records prod-apply lane still
  reads it host-side). All deferred by operator decision.
- Do NOT change `secret-audit.sh` `ENV_ALLOWED_KEYS` -- the OPS_* names were
  never in it (they are orphans failing Check 1b); their guard is Check 1c.

## B.2 The env helper -- `packages/apex-jobs/src/apex_jobs/_env.py` (new)

Two allowlist constants (operator-specified shape), a membership predicate, and
one builder. No secret is named under `LC_` or `XDG_`, so those two standard
namespaces are admitted by prefix; everything else is an exact name.

```python
"""apex-jobs subprocess env policy -- a default-deny allowlist (exact names
plus two provably-safe standard namespace prefixes) for the environment handed
to job child processes. Secrets sourced into the worker's own environment
(*_PASSWORD / *_DSN / *_TOKEN / *_KEY / service keys) are dropped by
construction: a child that needs a secret injects it itself, in-process, via
infra/infisical/inject.sh -- it never inherits one ambiently.
"""
import os

# Exact names kept: home/user/shell basics, temp dirs, timezone, base locale.
ENV_ALLOW_EXACT = frozenset({
    "HOME", "PATH", "USER", "LOGNAME", "SHELL", "TERM",
    "TMPDIR", "TMP", "TEMP", "TZ", "LANG",
})

# Standard non-secret namespaces kept by prefix: POSIX locale (LC_*) and XDG
# base-directory (XDG_*). A prefix admits future members (LC_FOO / XDG_BAR)
# with no code change; no platform secret lives under either namespace.
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
        env["PATH"] = extra_path + os.pathsep + env.get("PATH", "")
    return env
```

`str.startswith` accepts the prefix tuple directly. `_env` imports only `os`,
so a top-level `from . import _env` in worker.py introduces no import cycle.

## B.3 worker.py change

In `_run_command_job`, replace the full-environment spread with the sanitized
builder (one substantive line + one import):

```python
from . import _env      # add alongside `from . import engine`
...
    proc = subprocess.run(
        command, shell=True, capture_output=True, text=True,
        env=_env.sanitized_env(env),          # was: {**os.environ, "APEX_JOB_ENV": env}
    )
```

Behavior change (documented, not an error): a command job no longer inherits
arbitrary parent env. A DB command job obtains its secret by putting the
wrapper in its own `payload.command`, e.g.
`infra/infisical/inject.sh dev -- <db command>` -- the secret reaches the child
only, never argv or logs.

## B.4 Tests (TDD, value-silent throughout)

**Value-silence rule (load-bearing, [[feedback_value_silent_tests_pytest_introspection]]):**
never reference `env`, `set(env)`, `env[...]`, or `env.get(...)` inside an
`assert` -- pytest's assertion rewriting would render the whole env dict with
real values on failure. Compute plain locals (booleans / sorted name-lists /
the marker string) BEFORE the assert; assert only on those. Battery values are
fixed placeholders (`"PLACEHOLDER-TEST-VALUE"`), never real secrets, and are
never asserted on.

New `packages/apex-jobs/tests/test_env.py` -- helper unit tests:
1. `test_sanitized_env_strips_secret_names` -- monkeypatch a secret battery
   (`APEX_JOBS_PGPASSWORD, DEV_PG_PASSWORD, OPS_API_DSN, OPS_INTAKE_WRITER_DSN,
   SUPABASE_PROD_DSN, PGPASSWORD, AWS_SECRET_ACCESS_KEY, INFISICAL_CLIENT_SECRET`)
   into `os.environ`; `leaked = sorted(set(battery) & set(env))`; `assert leaked == []`.
2. `test_sanitized_env_keeps_basics_and_marker` -- HOME/PATH present booleans;
   `marker == job_env`.
3. `test_sanitized_env_keeps_locale_and_xdg_by_prefix` -- `LC_TIME`,
   `XDG_CONFIG_HOME` present booleans (proves the prefix admits them).
4. `test_sanitized_env_command_path_no_prepend` -- with `extra_path=None`, the
   returned PATH equals the allowlisted `os.environ` PATH (no agent-bin prefix).
5. `test_sanitized_env_extra_path_prepends` -- with `extra_path` set, PATH
   startswith `extra_path + os.pathsep` (boolean).

Command-job guard (worker path) -- in the worker test module: monkeypatch
`worker.subprocess.run` to capture the `env=` kwarg, and stub
`worker.engine.start` / `worker.engine.report`; call `_run_command_job` with a
trivial `payload.command`; compute `secret_present = "OPS_API_DSN" in child`,
`home_present = "HOME" in child`, `marker = child.get("APEX_JOB_ENV")`;
`assert secret_present is False`, `assert home_present is True`,
`assert marker == <job_env>`. This is the worker-path analog of Part A's
review-path guard: defense in depth proving the wiring, not just the helper.

Red-first: tests 1 and the guard are genuinely red against the current
`{**os.environ, "APEX_JOB_ENV": env}` (a monkeypatched secret name appears in
the child env); they go green only after B.3.

Test-run recipe (host): the session-autouse `_schema` fixture skips a test file
without DB creds, so even these pure unit tests need `infra/.env` sourced from
the MAIN checkout. From the worktree package dir:
`set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
export PATH=$HOME/.local/bin:$PATH; \
APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest \
tests/test_env.py tests/<worker-test-file> -q`. Check the pytest exit code
UNMASKED (redirect to a file then read `$?`; never through a `| tail` pipe --
[[feedback_false_green_gate_pipe_masks_exit]]).

## B.5 OPS_* cutover (operator-gated, value-silent, ordered)

Targets: `OPS_API_DSN`, `OPS_INTAKE_WRITER_DSN` -- both Infisical-reconciled
this session (Development env). Ordered steps; each gate must pass before the next.

**Step 0 -- consumer discovery (HARD GATE).** Value-silent enumeration (names /
paths only) of every consumer and cache location of the two names:
`git -C <repo> grep -nI -E 'OPS_API_DSN|OPS_INTAKE_WRITER_DSN' -- .` over tracked
files, plus a NAME scan of the known caches (`infra/.env`, any `gate*/.env.dev`,
the offsite-backup cache). **If any current consumer reads `infra/.env`
directly for these names, then in THIS lane either (a) migrate that consumer to
`infra/infisical/inject.sh dev -- ...` , or (b) STOP and rescope.** Do NOT remove
the OPS lines from `infra/.env` until this is resolved
([[feedback_cc_fill_stop_on_resource_gaps]]).

**Step 1 -- precondition verify (value-silent).** Confirm both names resolve
from Infisical dev without printing values:
`infra/infisical/inject.sh dev -- bash -c 'for n in OPS_API_DSN OPS_INTAKE_WRITER_DSN; do if [ -n "${!n:+x}" ]; then echo "$n present"; else echo "$n MISSING"; fi; done'`
(`${!n:+x}` expands to a literal `x`, never the value). Both must print `present`.

**Step 2 -- operator removes the two lines from `infra/.env`.** I never sed-edit
a credential file ([[feedback_value_silence_credential_file_discipline]]); I
provide the exact NAMES to remove and the operator applies. I verify post-state
by NAME absence: `cut -d= -f1 infra/.env | grep -E 'OPS_API_DSN|OPS_INTAKE_WRITER_DSN'`
returns nothing.

**Step 3 -- I arm the two NAMES in `infra/infisical/.managed-secrets`** (create
the file; one name per line; NAMES only -- safe to write; commit it). Arming
comes AFTER Step 2, else Check 1c fails on first run.

**Step 4 -- drift verify.** Run `infra/secret-audit.sh`. Assert: the two OPS_*
names appear under the Check 1c "managed" run with NO `drift:` FAIL line, and
Check 1b no longer lists them. The overall script still exits 1 (because
`SUPABASE_PROD_DSN` + `TCC_*` remain intentionally parked) -- so assert on the
OPS_* lines specifically, NOT on exit 0.

**Success criteria (this lane):** `OPS_API_DSN` and `OPS_INTAKE_WRITER_DSN` are
gone from `infra/.env`, armed in `.managed-secrets`, and non-drifting under
Check 1c. NOT "secret-audit exits 0."

**Runbook:** if Step 0 found and migrated a real consumer, update that consumer's
runbook line to the `inject.sh dev -- ...` pattern. If no consumer existed, no
runbook change.

## B.6 Cross-lane consistency note (prefix vs exact)

Part A (PR #63) ratified an EXACT-name allowlist that lists each `LC_*` and
`XDG_*` name individually and explicitly avoids prefixes. Part B uses
`ENV_ALLOW_PREFIXES = ("LC_", "XDG_")`. Consequence: the post-#63 DRY-reconcile
(pointing `agent_runner._agent_env` at `_env.sanitized_env`) would change the
agent path from exact-name to prefix matching for those two namespaces.

Assessment: safe. No platform secret is named under `LC_` or `XDG_`; the change
is strictly more permissive only within two standard non-secret namespaces, and
is robust to new members. Lean: at reconcile time, unify the platform on the
prefix policy (update the agent path to match), rather than adding a mode flag
to the shared helper to preserve two behaviors for no security gain. This is an
operator decision at reconcile, recorded here so the divergence is deliberate,
not accidental.

## B.7 Verification / smoke

- Run the B.4 tests value-silent on host, exit code checked unmasked.
- Post-build guard confirms a command-job child env is sterile (no battery name
  present, HOME present, marker correct) -- the guard test IS this proof.
- No live DB mutation anywhere in the lane.
- After the cutover steps: Check 1c reports the two OPS_* names managed +
  non-drifting (value-silent).

## Discipline (whole lane)

Host-canonical single-writer: author locally, scp to the
`apex-secrets-command-env` worktree only, commit host-side. ASCII-only added
lines. Value-silent (names / paths / booleans / counts only; never a DSN or
password value, never a pytest env dump). No production mutation --
`SUPABASE_PROD_DSN` is untouched. Credential-file discipline: the operator
applies `infra/.env` edits; I set preconditions and verify post-state. This
lane introduces no dev-DB write boundary, so no `docs/lanes/README.md` charter
is required. Do NOT touch `agent_runner.py` while #63 is open. Commit trailer
`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

## Self-review notes

- Placeholder scan: none (all file paths, names, and code are concrete).
- Consistency: the B.2 allowlist matches the B.4 test expectations; the "no
  agent_runner.py edit" non-goal matches the B.6 reconcile-as-follow-up note;
  the "audit not green" success framing is stated once in B.5 and reused in B.7.
- Scope: one implementation plan -- one helper + one worker edit + tests + docs
  + a bounded 4-step cutover. No decomposition needed.
- Ambiguity: "sterile env" is pinned by the exact B.2 allowlist; "cutover
  success" is pinned by the B.5 success criteria (names transitioned, not exit
  0); the consumer gate in B.5 Step 0 has an explicit stop-or-migrate branch.
