# Secret-Handling Cleanup Lane -- Design

**Date:** 2026-07-04
**Branch:** `secrets/agent-env-sanitizer` (host worktree `apex-secrets-agent-env`, off `main` 3f3ebe46)
**Status:** Rev 3. Spec-review gate passed 2026-07-04 -- Part A approved for implementation planning (not yet built). Part B is design-only and gated. Allowlist ratified 2026-07-04.

## Goal

Stop the apex-jobs worker from passing its entire environment -- which routinely
holds database credentials -- into every `claude` / `codex` agent subprocess, and
record the broader Infisical task-scoped secret model as the next gated lane.

## Problem

`packages/apex-jobs/src/apex_jobs/agent_runner.py` builds the agent subprocess
environment as `{**os.environ, "APEX_JOB_ENV": job_env}` (`_agent_env`, lines
73-82). The worker is launched by sourcing `infra/.env`
(`set -a; . infra/.env; set +a; ... uv run apex-jobs ...`), so at runtime
`os.environ` carries all seven cache secrets:

    APEX_JOBS_PGPASSWORD, DEV_PG_PASSWORD, OPS_API_DSN,
    OPS_INTAKE_WRITER_DSN, SUPABASE_PROD_DSN,
    TCC_BREAKER_CODEX_PW, TCC_BREAKER_RO_PW

Every one of these flows into the `claude` / `codex` child process for every
agent job and every review job. An agent job edits code in an isolated worktree;
it has no legitimate need for any database credential. This is the largest
practical secret-exposure path in the orchestration layer, and it is independent
of Infisical: it can be closed today by filtering the child environment.

### Why the fix is safe (grounded)

- Agent CLIs authenticate from files under `$HOME`, not from environment tokens:
  `~/.claude/.credentials.json` and `~/.claude.json` (claude), `~/.codex/auth.json`
  and `~/.codex/config.toml` (codex), all mode 0600. No `ANTHROPIC_API_KEY`,
  `OPENAI_API_KEY`, or OAuth-token env var is load-bearing in the worker.
- `CODEX_HOME` / `CODEX_PATH` appear only in the unrelated TCC-breaker
  codex-harness scripts, never in `infra/.env` or the apex-jobs worker env, so
  codex resolves its default `~/.codex`. No agent-config env var is required.
- The `APEX_JOB_ENV` marker cannot carry a secret: `engine.start` validates
  `run_env in ("sandbox", "host")` and raises `ValueError` otherwise, so the only
  reachable marker values are the two literals `sandbox` and `host`.
- The existing tests (`tests/test_agent_runner.py:150`, `:160`) only assert the
  PATH prepend and the `APEX_JOB_ENV` marker. Both are preserved under an
  allowlist, so the change is behavior-compatible and cleanly test-drivable.
- Allowlist completeness was checked against a host shell baseline (2026-07-04):
  a value-silent name enumeration (`printenv | cut -d= -f1 | sort`, names only)
  returned 11 names, none in the TLS / proxy / `NODE_*` / `GIT_*` / `npm_*` /
  `FNM_*` / `NVM_*` / `SSH_AUTH_SOCK` / `GPG*` risk families. See A.7.

## Scope and decomposition

Two separable pieces with different risk profiles:

- **Part A -- agent-env sanitizer (BUILD THIS PASS).** One function, its tests,
  and two documentation lines. Infisical-independent. Highest value, smallest
  blast radius.
- **Part B -- Infisical task-scoped adoption (DESIGN ONLY, GATED).** Touches live
  production credential custody and operational runbooks. Recorded here so the
  whole model is explicit; executed later as its own operator-gated plan.

### Non-goals (this pass)

- `worker.py` command-job environment (`_run_command_job`, line 30) is NOT
  changed. It has the same `{**os.environ, ...}` shape, but some command jobs are
  database tasks that legitimately need injected secrets. Command-job env policy
  is a Part B concern (a task-scoped policy that distinguishes DB command jobs
  from the rest), not the agent policy.
- No Infisical migration, no `.managed-secrets` arming, no `secret-audit.sh`
  allowlist changes, no `infra/.env` edits.
- No production Supabase or credential mutation of any kind.

## Part A -- Agent-env sanitizer (build)

### A.1 Behavior

`_agent_env(job_env)` stops copying `os.environ`. It builds the child env
**default-deny from a flat, exact-name allowlist**, then:

1. Copies through only the allowlisted names that are present in `os.environ`.
2. Always sets `APEX_JOB_ENV = job_env` (the env marker; unchanged contract).
3. Prepends the agent bin directories to `PATH` exactly as today:
   `extra = os.environ.get("APEX_JOBS_AGENT_PATH", _DEFAULT_AGENT_PATH)`;
   `env["PATH"] = extra + os.pathsep + env.get("PATH", "")`.

`APEX_JOBS_AGENT_PATH` is read **only** as configuration to compute the PATH
prepend; it is never placed in the returned child environment.

The function signature (`_agent_env(job_env) -> dict`) and both call sites
(`run_agent_job` line 119, `run_review_job` line 178) are unchanged.

### A.2 The allowlist (verbatim, exact names only)

Defined as module-level constants so it is auditable and testable. A flat set of
exact names -- no prefix matching -- so that any new secret-shaped variable is
denied automatically and the "new secret shape denied" guarantee stays airtight.

Base runtime:

    HOME PATH USER LOGNAME SHELL TERM TMPDIR TMP TEMP TZ LANG

Locale (exact keys, not an `LC_` prefix):

    LC_ALL LC_COLLATE LC_CTYPE LC_MESSAGES LC_MONETARY LC_NUMERIC LC_TIME
    LC_ADDRESS LC_IDENTIFICATION LC_MEASUREMENT LC_NAME LC_PAPER LC_TELEPHONE

XDG base directories (exact keys, not an `XDG_` prefix):

    XDG_CONFIG_HOME XDG_CACHE_HOME XDG_DATA_HOME XDG_STATE_HOME XDG_RUNTIME_DIR

Always set (not sourced from `os.environ`): `APEX_JOB_ENV`.
Read-only configuration (never in the child env): `APEX_JOBS_AGENT_PATH`.

### A.3 What is denied, and why there is no denylist

Everything not in A.2 is dropped. That includes, by construction and without any
suffix rules to maintain: `*_PASSWORD`, `*_DSN`, `*_TOKEN`, `*_KEY`, `*_SECRET`,
`*_PW`, `PGPASSWORD` and all other `PG*` libpq vars, `INFISICAL_*`, `SSH_AUTH_SOCK`,
`CODEX_HOME` / `CODEX_PATH`, `CLAUDE_*`, and the seven concrete `infra/.env`
names. Default-deny means a future secret with an unanticipated name is denied on
day one; there is no denylist that could fall behind.

### A.4 Files touched

- `packages/apex-jobs/src/apex_jobs/agent_runner.py`
  - Add module-level allowlist constants (frozenset).
  - Rewrite `_agent_env` to build default-deny from the allowlist.
  - Correct the `_agent_env` docstring (currently "os.environ + the job-env
    marker") to describe the allowlisted subset.
- `packages/apex-jobs/README.md`
  - The existing worker/command sentence (near line 41: "The subprocess runs with
    `APEX_JOB_ENV` set to the worker's env.") documents the COMMAND-job path
    (`run_once`/`run_forever`, `worker.py`), and it stays accurate -- command
    subprocesses still inherit the worker env. Do NOT rewrite it to claim agent
    sanitization; that would falsify the command-job docs. Optionally qualify it
    to read "command subprocess" for clarity.
  - Add a distinct statement where agent/review jobs are documented: agent and
    review subprocesses receive only the `_agent_env` allowlisted env plus
    `APEX_JOB_ENV`. (Cross-engine review, Codex 2026-07-04: line 41 is the wrong
    target; the agent-section note is the correct fix.)
- `packages/apex-jobs/tests/test_agent_runner.py`
  - Add the tests in A.5. The two existing `_agent_env` tests stay unchanged.

### A.5 Tests (TDD)

1. **Strip battery (red first).** With a representative secret battery set in the
   environment -- the seven real names plus synthetic `X_TOKEN`, `Y_KEY`,
   `Z_DSN`, `W_SECRET`, `PGPASSWORD` -- `_agent_env("host")` returns an env
   containing **none** of them.
2. **Keep allowlisted.** With `HOME`, `LANG`, `LC_ALL`, `TERM`, `TMPDIR`,
   `XDG_CONFIG_HOME` set (plus a secret), the returned env contains each
   allowlisted name with its value, the secret is absent, and
   `env["APEX_JOB_ENV"] == "host"`.
3. **Read-as-config-only.** With `APEX_JOBS_AGENT_PATH` set, its bin dir appears
   in the returned `PATH`, but `APEX_JOBS_AGENT_PATH` itself is **absent** from
   the returned env. This makes the read-only rule executable.
4. **Closure.** The set of returned keys is a subset of
   (allowlist) union {`PATH`, `APEX_JOB_ENV`}. No unexpected key survives.
5. **Regression.** The existing `test_agent_env_prepends_agent_bins_to_path`
   (`:150`) and `test_agent_env_default_includes_codex_bin` (`:160`) still pass:
   PATH prepend and the `APEX_JOB_ENV` marker are preserved.
6. **Review-path defense in depth.** `run_review_job` (`:178`) routes through the
   same `_agent_env`, so the sanitized env reaches review subprocesses too. Prove
   it end-to-end by capturing the `env=` passed to `subprocess.run` for a review
   job (the harness already exists at
   `test_review_job_never_passes_prompt_with_base`, `:257`, which monkeypatches
   `subprocess.run`) and asserting a planted secret is absent while `HOME` and
   `APEX_JOB_ENV` are present.
7. **Post-build agent-env smoke (plan verification step, not a unit test).** After
   the change lands, run `claude --version` and `codex --version` in a subprocess
   whose env is the ACTUAL `_agent_env("host")` output (not a hand-shaped env),
   confirming both CLIs still launch under the real sanitized env. This converts
   the A.7 host baseline into an executed proof and belongs in the implementation
   plan's final verification, not in the pytest suite.

### A.6 Error handling and edge cases

- If an allowlisted name is not in `os.environ`, it is simply omitted (no
  `KeyError`); the child inherits the platform default for it.
- If `PATH` is unset in `os.environ`, the prepend still yields a valid `PATH`
  consisting of just the agent bins (`env.get("PATH", "")` today; unchanged).
- `job_env` is always written to `APEX_JOB_ENV`, matching current behavior; no
  gate, promotion, heartbeat, or worktree-plumbing behavior changes.

### A.7 Allowlist completeness -- host shell baseline + agent-env smoke (2026-07-04)

The strict default-deny allowlist is only safe if no non-secret runtime variable
the agents rely on is silently dropped. Checked value-silent (names only) as a
host shell baseline -- a proxy for the manually-launched worker env, which
inherits from the launching shell:

- A login-shell `printenv | cut -d= -f1 | sort` returned 11 names. None belong to
  the risk families the audit flagged: no `NODE_OPTIONS` / `NODE_EXTRA_CA_CERTS` /
  `NODE_PATH`, no `SSL_CERT_FILE` / `SSL_CERT_DIR` / CA-bundle var, no
  `HTTP(S)_PROXY` / `NO_PROXY` (either case), no `GIT_*`, no `npm_*` / `FNM_*` /
  `NVM_*`, no `SSH_AUTH_SOCK` / `GNUPGHOME` / `GPG_TTY`.
- The only names present that are neither allowlisted nor a known secret are
  shell-internal / session variables the agent does not need: `MAIL`, `PWD`,
  `SHLVL`, `SSH_CLIENT`, `SSH_CONNECTION`, `_`.
- Independent cross-engine confirmation (Codex 2026-07-04): `claude --version`,
  `codex --version`, and `git status` all launched cleanly under a minimal env
  shaped like this allowlist; the codex wrapper reads only
  `npm_config_user_agent` / `npm_execpath` (package-manager detection) before
  spawning the native binary.

Decision: the allowlist requires no additions; TLS / proxy / `NODE_OPTIONS` /
`GIT_*` are consciously omitted because they are not set in the host shell
baseline. This baseline is turned into an executed proof by a post-build smoke
(A.5 item 7): run `claude --version` and `codex --version` under the ACTUAL
`_agent_env("host")` output (not a hand-shaped env). Re-check trigger: if the
worker launch context is ever changed to set a custom CA bundle, an egress proxy,
or `NODE_OPTIONS`, re-run the name diff and allowlist the specific name (these are
paths / routing config, not secrets) before shipping that change.

## Part B -- Infisical task-scoped adoption (design only, gated)

End state, one line: **Infisical stores; wrappers inject; agents inherit almost
nothing; DB tasks receive secrets only inside their child process.**

Invariants (operator model, 2026-07-04):

1. Infisical is canonical for DB passwords / DSNs / service keys / orchestration
   creds.
2. The only bootstrap secret on disk is the Infisical machine-identity credential
   (0600 gitignored `infra/infisical/.env.agent`, host + project scoped).
3. Broad shell sourcing stops: `infra/.env` becomes transitional, then
   empty/non-secret.
4. DB-only injection via wrappers (`dev-psql.sh` is the pattern: `PGPASSWORD`
   reaches psql inside the injected child only, never argv or logs).
5. Agent env isolation -- delivered by Part A.

Command-job env policy (distinct from the agent policy, deferred): DB command
jobs keep their injected secrets through a wrapper (`inject.sh`, or a narrower
`db-run.sh`); non-DB command jobs get a sanitized env. This requires classifying
command jobs (DB-task vs not) and is why `worker.py` is out of scope for Part A.

Cleanup sequence (ordered, each step operator-gated):

1. Sanitized agent env for apex-jobs (Part A -- done first, Infisical-independent).
2. Separate DB-task runner path: only DB / migration / test command jobs may call
   `inject.sh` or `db-run.sh`.
3. Move one secret at a time from `infra/.env` to Infisical-only, then arm its
   NAME in `infra/infisical/.managed-secrets` (only after the value is removed
   from every cache, else Check 1c correctly fails on first run).
4. Shrink `secret-audit.sh` `ENV_ALLOWED_KEYS` as each name migrates.
5. Update runbooks that still say `source infra/.env` to the wrapper pattern.

Migration targets (the orphans `secret-audit.sh` flags in `infra/.env` today):
`SUPABASE_PROD_DSN`, `OPS_API_DSN`, `OPS_INTAKE_WRITER_DSN`, `TCC_BREAKER_RO_PW`,
`TCC_BREAKER_CODEX_PW`. (`DEV_PG_PASSWORD` is already injectable via `dev-psql.sh`;
`APEX_JOBS_PGPASSWORD` stays allowlisted in Check 1b until a runner path exists.)

Substrate already built and verified: `infra/infisical/README.md`, `inject.sh`,
`dev-psql.sh`, `.managed-secrets` (empty), `secret-audit.sh` Checks 1b/1c
(project id `985aac34-9665-423b-b472-78ddbd707ca7`, mesh-only
`http://100.64.0.1:8222`).

## Review record (IRP audit, 2026-07-04)

Adversarial audit run before the operator review gate: 4 independent Claude lenses
(over-strictness, residual-leak, test-rigor, scope/doc) plus the mandatory Codex
cross-engine pass reading the actual `agent_runner.py` / `worker.py` / tests.

- Convergence: the sanitizer design is sound; the strip-battery and
  read-as-config tests are genuinely red against the current `{**os.environ,...}`;
  no residual env leak in the agent/review paths; the `worker.py` command-job
  scope-out is honest; no gate/promotion/heartbeat interaction.
- Cross-engine delta -- Codex caught (P2, folded into A.4): the original doc-fix
  target (`README.md` line 41) is the command-worker section; rewriting it would
  falsify command-job docs. Fix is an agent-section note instead.
- Claude caught (P1, folded into A.7): allowlist completeness was unverified
  against the live host env; the value-silent name diff now records it and turns
  the TLS/proxy/NODE/GIT omissions into documented decisions.
- Conditional P1/P2/P3 breakage risks (TLS, proxy, `NODE_OPTIONS`, `GIT_*`,
  SSH/GPG): all resolved as not-present in the worker env (A.7); no allowlist
  change. Verdict: approve-with-changes -> changes folded (this revision).

## Discipline (both parts)

Host-canonical single-writer: author locally, scp to the
`apex-secrets-agent-env` worktree only, commit host-side. ASCII-only added lines.
Value-silent (never echo a DSN or password; names, paths, booleans, counts only).
No production mutation. Any Part B database step uses disposable targets and stays
operator-gated. Commit trailer `Co-Authored-By: Claude Opus 4.8
<noreply@anthropic.com>`.

## Self-review notes

- Placeholder scan: none.
- Consistency: the allowlist in A.2 matches the deny discussion in A.3 and the
  tests in A.5; `worker.py` non-goal is stated once and referenced consistently.
- Scope: Part A is a single implementation plan (one function + tests + docs);
  Part B is explicitly design-only and gets its own later plan.
- Ambiguity: "read-as-config-only" for `APEX_JOBS_AGENT_PATH` is pinned by test 3;
  "sanitized env" is pinned by the exact allowlist in A.2.
