# Secret-handling cleanup -- Part B: apex-jobs command-job env sanitizer

**Status:** Rev 3 (operator spec-review exactness edits folded: pinned worker
test file, recipe cwd, DB-mutation wording). Sanitizer-only; OPS_* cutover
deferred to its own lane (B.8). Ready for the implementation plan.

**Goal:** Close the apex-jobs kind='command' worker path's full-parent-environment
inheritance with a default-deny sanitized env, so a command job's subprocess no
longer inherits every secret the worker sourced. This closes the COMMAND-job path
only; the agent path's identical inheritance is closed separately by Part A
(PR #63), which is unmerged -- so this lane alone does NOT make apex-jobs
leak-free (see B.6).

**Architecture:** One shared env-policy helper (`_env.py`) providing a default-deny
allowlist builder; one `worker.py` line change to use it; value-silent tests; a
docs note. A command job that needs a secret re-injects it in-child via
`infra/infisical/inject.sh` -- worker.py never becomes a secret broker. The
Infisical OPS_* cutover that rev 1 bundled here is deferred (B.8) because ground
truth showed it is a live-consumer migration, not a tight ride-along.

**Tech stack:** Python 3 (apex-jobs, `uv`-managed), pytest (value-silent).

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

**Explicit non-goals (do NOT do in this lane)**
- Do NOT modify `agent_runner.py` (that is PR #63 / Part A's file). The
  DRY-reconcile pointing the agent path at `_env.sanitized_env` is a post-#63
  follow-up (see B.6), not this lane.
- Do NOT build a `db-run.sh` (YAGNI -- no DB command jobs exist; a future one
  uses the existing `inject.sh` / `dev-psql.sh`).
- Do NOT add a per-job `env_secrets` broker to worker.py.
- Do NOT cut over ANY secret out of `infra/.env` in this lane. The OPS_* cutover
  is deferred to its own lane (B.8); `DEV_PG_PASSWORD`, `APEX_JOBS_PGPASSWORD`,
  `TCC_*`, and `SUPABASE_PROD_DSN` are all deferred/out.
- Do NOT change `secret-audit.sh` (`ENV_ALLOWED_KEYS`, `CACHES`, or Checks).

## B.2 The env helper -- `packages/apex-jobs/src/apex_jobs/_env.py` (new)

Two allowlist constants (operator-specified shape), a membership predicate, and
one builder. No secret is named under `LC_` or `XDG_`, so those two standard
namespaces are admitted by prefix; everything else is an exact name.

```python
"""apex-jobs subprocess env policy -- a default-deny allowlist (exact names
plus two provably-safe standard namespace prefixes) for the environment handed
to job child processes. A secret sourced into the worker's own environment
(*_PASSWORD / *_DSN / *_TOKEN / *_KEY / service keys) is never inherited by a
child VIA THE PROCESS ENVIRONMENT -- it is dropped by construction. (On-disk
credential stores under HOME -- e.g. ~/.pgpass, ~/.aws/credentials -- remain
reachable and are OUT OF SCOPE for this env-policy helper; filesystem isolation
is a separate concern. See B.6.)
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
        # filter(None, ...) drops an absent PATH so no trailing os.pathsep (an
        # empty PATH element = CWD) is ever emitted.
        env["PATH"] = os.pathsep.join(filter(None, [extra_path, env.get("PATH")]))
    return env
```

`str.startswith` accepts the prefix tuple directly. `_env` imports only `os`,
so a top-level `from . import _env` in worker.py introduces no import cycle. The
marker assignment overwrites any `APEX_JOB_ENV` that survived the allowlist (it
is not allowlisted, so it is already absent) -- the returned marker is always
`job_env`.

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
arbitrary parent env. A DB command job obtains its secret by putting the wrapper
in its own `payload.command`, e.g. `infra/infisical/inject.sh dev -- <db command>`
-- the secret reaches the child only, never argv or logs.

## B.4 Tests (TDD, value-silent throughout)

**Value-silence rule (load-bearing, [[feedback_value_silent_tests_pytest_introspection]]):**
never reference `env`, `set(env)`, `env[...]`, or `env.get(...)` inside an
`assert` -- pytest's assertion rewriting would render the whole env dict with
real values on failure. Compute plain locals (booleans / sorted name-lists /
the marker string) BEFORE the assert; assert only on those. Battery/probe values
are fixed placeholders (`"PLACEHOLDER-TEST-VALUE"`), never real secrets, and are
never asserted on. This applies to EVERY test below, including PATH comparisons.

New `packages/apex-jobs/tests/test_env.py` -- helper unit tests:
1. `test_sanitized_env_strips_secret_names` -- monkeypatch a secret battery into
   `os.environ` covering every shape the docstring names:
   `APEX_JOBS_PGPASSWORD, DEV_PG_PASSWORD, OPS_API_DSN, OPS_INTAKE_WRITER_DSN,
   SUPABASE_PROD_DSN, PGPASSWORD, TCC_BREAKER_RO_PW, TCC_BREAKER_CODEX_PW,
   GITHUB_TOKEN, AWS_SECRET_ACCESS_KEY, INFISICAL_CLIENT_SECRET` (the `*_PW`
   TCC names and a `*_TOKEN` are included -- real co-residents / advertised
   shapes). `leaked = sorted(set(battery) & set(env))`; `assert leaked == []`.
2. `test_sanitized_env_keeps_basics_and_marker` -- `home_present`, `path_present`
   booleans; `marker == job_env`.
3. `test_sanitized_env_keeps_locale_and_xdg_by_prefix` -- monkeypatch `LC_TIME`
   and `XDG_CONFIG_HOME`; assert `lc_present is True`, `xdg_present is True`.
4. `test_sanitized_env_command_path_no_prepend` -- `extra_path=None`; compute
   `path_unchanged = (env.get("PATH") == os.environ.get("PATH"))`; assert the
   boolean (no `env[...]` in the assert).
5. `test_sanitized_env_extra_path_prepends` -- `extra_path` set; compute
   `prepended = env.get("PATH", "").startswith(extra_path + os.pathsep)`; assert
   the boolean.

Command-job guard (worker path) -- in `tests/test_worker.py`: the guard proves
`worker.py` is WIRED to `sanitized_env`, and its red-first must be INTRINSIC
(not borrowed from ambient `infra/.env`, per the audit).
- Setup: `monkeypatch.setenv("PROBE_LEAK_DSN", "PLACEHOLDER-TEST-VALUE")` INTO
  `os.environ` (self-seeded, like test 1 -- never rely on the recipe sourcing
  `infra/.env`); monkeypatch `worker.subprocess.run` to capture the `env=` kwarg
  and return a PINNED fake proc: an object with `returncode = 0` (int),
  `stdout = ""`, `stderr = ""` (str) so the real `proc.stdout[-4000:]` /
  `proc.returncode` reads don't error; stub `worker.engine.start` to return a
  concrete `run_id` sentinel and `worker.engine.report` to return a concrete
  status.
- Call `_run_command_job({...,"payload":{"command":"true"}}, <job_env>, "cc")`.
- Compute `secret_present = "PROBE_LEAK_DSN" in child`, `home_present =
  "HOME" in child`, `marker = child.get("APEX_JOB_ENV")`; assert
  `secret_present is False`, `home_present is True`, `marker == <job_env>`.
- This is genuinely RED against the current `{**os.environ, "APEX_JOB_ENV": env}`
  (the self-seeded probe appears in the captured child env) and GREEN after B.3;
  because the probe is self-seeded it stays a valid strip-proof forever.

**Red-first (precise):** test 1 is red against the ABSENCE of `_env.py` and goes
green when B.2 is written (it never touches worker.py). Only the worker-path
guard is red against the current worker.py spread and green after B.3. The two
are red for different reasons; do not conflate them.

**Test-run recipe (host) + skip-guard.** The session-autouse `_schema` fixture
SKIPS a test file without DB creds, so even these pure unit tests need
`infra/.env` sourced from the MAIN checkout. A `;`-chained source that fails
would leave pytest exiting 0 with everything SKIPPED -- a false green on the
lane's only security proof ([[feedback_false_green_gate_pipe_masks_exit]] covers
a masked FAIL, NOT an all-skipped exit 0). So:
`cd /home/olares/code/apex/apex-secrets-command-env/packages/apex-jobs; \
set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
export PATH=$HOME/.local/bin:$PATH; \
APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest \
tests/test_env.py tests/test_worker.py -rN -q > /tmp/partb-pytest.out 2>&1; \
echo "rc=$?"`. The `cd` into `packages/apex-jobs` is required: apex-jobs has its
own `pyproject.toml` and the repo root is not a uv workspace. Acceptance requires
ALL of: `rc == 0`; the summary shows the
expected PASSED count (>= 8) for these files; and ZERO `skipped` for them.
State explicitly: **exit 0 with any test skipped is a FAIL for this lane.**
Check the exit code UNMASKED (redirect + `$?`, never a `| tail` pipe).

## B.5 Docs note

Add an env-isolation note to the apex-jobs README **command-job** section (do
NOT rewrite the existing accurate `APEX_JOB_ENV` line, per the Part A doc-fix
lesson): a command job runs with a sanitized, default-deny env; when it needs a
secret it must wrap its own command, e.g.
`infra/infisical/inject.sh dev -- <db command>` (or `dev-psql.sh`), so the secret
reaches the child only.

## B.6 Cross-lane consistency (prefix vs exact) + the "leak-free" boundary

Part A (PR #63) uses an EXACT-name allowlist listing each `LC_*`/`XDG_*` name
individually. Part B uses `ENV_ALLOW_PREFIXES = ("LC_", "XDG_")`. **Proven
non-issue in practice:** a value-silent host inventory (2026-07-05) found ZERO
`LC_*`/`XDG_*` names in the worker env (12 env names total, none locale/XDG), so
the prefix admits an EMPTY set today; the divergence from Part A's exact list is
forward-looking only. Lean: at the post-#63 reconcile, unify the platform on the
prefix form (update the agent path to `_env.sanitized_env`) rather than adding a
mode flag; safe because no secret is named under either namespace. Operator
decision at reconcile; recorded here so the divergence is deliberate.

**Leak-free boundary (premise correction).** This lane closes the COMMAND-job
inheritance path. On main, `agent_runner._agent_env` still full-inherits
`os.environ` until PR #63 merges, so shipping Part B alone does NOT make apex-jobs
leak-free -- the agent/review paths remain closed by Part A, separately. The spec
makes no "last inheritance path" claim.

**Filesystem boundary.** `sanitized_env` sterilizes the process ENVIRONMENT only.
Keeping `HOME` means a command job's child can still read on-disk credential
stores (`~/.pgpass`, `~/.aws`, git credential store). That is intentional (the
in-child `inject.sh` and many CLIs resolve config under HOME) and out of scope;
env-borne secret inheritance is the threat this lane closes, filesystem isolation
is a separate concern.

## B.7 Verification / smoke

- Run the B.4 tests value-silent on host; exit code checked UNMASKED; acceptance
  requires the expected PASSED count and ZERO skipped (all-skipped exit 0 = FAIL).
- The worker guard test IS the wiring proof: a self-seeded probe is absent from
  the command-job child env, HOME present, marker correct.
- No prod/dev data mutation; the tests touch only the disposable
  `orchestration_test` DB (the autouse `_schema` fixture applies downs/ups +
  truncates it).

## B.8 Deferred: OPS_* Infisical cutover (its own follow-up lane)

Rev 1 bundled a cutover of `OPS_API_DSN` + `OPS_INTAKE_WRITER_DSN`. Ground truth
(value-silent scan 2026-07-05): these names live in FOUR live caches
(`apex-power-ops-platform/infra/.env`, `apps/control-plane-api/.env`,
`apex-estimator-renderer/infra/.env`, `apex-learning-lane/infra/.env`) and
`control-plane-api` is a live consumer (72 refs across `main.py`,
`intake_router.py`, `recognition_router.py` + tests). That is a consumer
migration, not a tight ride-along, so it is DESCOPED. Its own lane, explicit scope:
1. Migrate `control-plane-api` launch/config to `inject.sh` (or equivalent) so it
   stops reading OPS_* from a cache.
2. Operator-purge OPS_* from all four caches (value-silent; operator applies,
   never a sed-edit of a credential file).
3. Extend Check 1c coverage: register every discovered cache via
   `APEX_EXTRA_CACHES` (or add to the default CACHES) and assert coverage-equality
   (the set of caches discovered == the set Check 1c scans), so drift-verify
   cannot false-green on an uncovered cache.
4. Verify no lingering OPS_* copy in ANY cache (value-silent, names only).
5. ONLY THEN arm the two NAMES in `.managed-secrets` (arming before every copy is
   gone makes Check 1c fail on first run).
Reject in-line expansion into this sanitizer lane.

## Discipline (whole lane)

Host-canonical single-writer: author locally, scp to the
`apex-secrets-command-env` worktree only, commit host-side. ASCII-only added
lines. Value-silent (names/paths/booleans/counts only; never a DSN or password
value, never a pytest env dump). No production mutation. No dev-DB write
boundary, so no `docs/lanes/README.md` charter required. Do NOT touch
`agent_runner.py` while #63 is open. Commit trailer
`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

## Review record (IRP audit, 2026-07-05)

Adversarial audit before the operator spec-review gate: 4 independent Claude
lenses (residual-leak, cutover-safety, test-rigor, scope/consistency), each
finding pushed through a refute stage (16 of 17 survived), plus the mandatory
Codex cross-engine pass reading the real `worker.py` / `agent_runner.py` /
`secret-audit.sh`. Both engines affirmed the sanitizer DESIGN.

- **Converged false-greens (folded, P2):** the worker guard test was red only
  via ambient `infra/.env` sourcing and would decay to a permanent false-green
  (now self-seeds a probe, B.4); the test recipe could exit 0 all-skipped (now
  count/skip-guarded, B.4); (the cutover drift-coverage false-green is moot --
  cutover descoped, B.8).
- **Cross-engine delta:** Codex uniquely caught the "last inheritance path"
  overclaim (corrected, B.6 -- agent path still leaks pre-#63) and asked the
  prefix set be proven (done -- empty set, B.6). Claude uniquely caught the
  guard-test decay chain and the skip false-green.
- **Scope-gate trip:** the audit + a value-silent host scan showed the OPS_*
  cutover is a live-consumer migration -> operator descoped it to its own lane
  (B.8); this sanitizer lane is unchanged in design.
- Folded polish: PATH trailing-separator hardening (B.2), HOME/filesystem
  scope note (B.6), red-first reword (B.4), pinned fake-proc shape (B.4),
  battery extended to real co-residents + a `*_TOKEN` (B.4), boolean-first PATH
  tests (B.4).

## Self-review notes

- Placeholder scan: none (the worker guard lives in `tests/test_worker.py`;
  every path/name is concrete).
- Consistency: B.2 allowlist matches B.4 expectations; the "no agent_runner.py
  edit" non-goal matches the B.6 reconcile-as-follow-up note; no "last leak"
  claim survives anywhere.
- Scope: one implementation plan -- one helper + one worker edit + tests + a
  docs note. The cutover is fully removed to B.8.
- Ambiguity: "sterile env" is pinned by the B.2 allowlist; the guard's red-first
  is intrinsic via a self-seeded probe; "all-skipped exit 0 = FAIL" is explicit.
