# apex-jobs — APEX platform orchestration task bus

**Chip 3 / D-ARCH-3.** The DB-backed upgrade of the file-based `ops/agents/inbox`
dispatch queue: a durable queue + run/promotion ledger + env & human-approval
gates. Runs on the host PG17 dev-pg (`orchestration_dev`); psycopg3; uv-managed.

## Model (`jobs` schema)
- **`jobs.job`** — the queue item. Subsumes the inbox frontmatter: `dispatch_id`
  (unique), `target` (cc|codex|cowork|any), `priority`, `predecessor_id` (DAG dep),
  `authority` (gated|autonomous_safe), `requires_approval`, `gate_categories`,
  `env_required` (sandbox|host|any), `payload` (jsonb), `status`.
- **`jobs.run`** — the run + promotion **ledger**: one row per attempt, recording
  the `env` (sandbox|host — the trust evidence), `exit_code`, `result`, timings.
- **`jobs.gate`** — human-approval records (`gate_type`, `state`, `decided_by`).

## Gates (the trust model — platform invariants #1 env, #4 human authority)
- **Human-approval gate:** a job with `requires_approval` / `gate_categories` gets
  pending `jobs.gate` rows at enqueue. `jobs.v_eligible` (and `claim()`) exclude
  any job with an open gate, so it is **not claimable until the operator approves**
  — no execution before approval, enforced at the queue boundary.
- **Env gate:** `start()` refuses to open a run unless the worker's `run_env`
  matches the job's `env_required`. Promotion is impossible without `env=host`
  evidence in the ledger.

## Atomicity
`claim()` uses `SELECT … FOR UPDATE SKIP LOCKED` on `jobs.job` (priority asc, then
dispatch_id asc), so concurrent executors never double-claim.

## CLI (`apex-jobs <verb>`)
`enqueue · queue · claim · start · report · request-gate · approve · reject ·
gates · status · ledger · reap · promotions · review · unblock`. Target a database with `APEX_JOBS_DB` (default
`orchestration_dev`) or `APEX_JOBS_DSN`; connects as the `orchestration` role.
Run with the dev password injected from Infisical:
`infra/infisical/apex-jobs.sh <verb>` (mirrors `dev-psql.sh`) injects
`APEX_JOBS_PGPASSWORD` from the `dev` environment. `APEX_JOBS_PGPASSWORD` is
Infisical-managed and no longer in `infra/.env`; `DEV_PG_PASSWORD` (still cached)
remains the fallback when you source `infra/.env` and run `apex-jobs` directly.

## Worker
```python
from apex_jobs.worker import run_once, run_forever
run_once(as_="cc", env="host")          # claim→gates→subprocess(payload.command)→report
run_forever(as_="cc", env="host", poll_s=5.0)
```
The command subprocess runs with `APEX_JOB_ENV` set to the worker's env, and with
a **sanitized, default-deny environment** (`_env.sanitized_env`): only an
allowlist of non-secret names (HOME, PATH, locale/XDG) plus the `APEX_JOB_ENV`
marker passes through, so a command job does not inherit the worker's secrets. A
command job that needs a secret must wrap its own command, e.g.
`infra/infisical/inject.sh dev -- <db command>` (or `dev-psql.sh`), so the secret
reaches the child process only.

## Coexistence
apex-jobs runs **alongside** the `ops/agents/inbox` file queue. No cutover yet —
the inbox remains the live mechanism until apex-jobs is proven in routine use.

## Tests (76)
Credentials come from env only -- no in-code fallback: source the governed
infra/.env first (DEV_PG_PASSWORD) or set APEX_JOBS_PGPASSWORD; the suite
skips with a hint otherwise.
```
set -a; . ../../infra/.env; set +a
APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest
```
The conftest PINS the engine runtime to the fixture target (APEX_JOBS_DB,
default `orchestration_test`, at 127.0.0.1:5432 as `orchestration`) so app
writes can never land in `orchestration_dev`; it refuses `APEX_JOBS_DSN`
and `APEX_JOBS_DB=orchestration_dev` outright. This suite and the
migration tests share `orchestration_test` -- run them sequentially.
enqueue/idempotency · atomic SKIP-LOCKED claim · predecessor + env + human gates ·
run-ledger finalize · CLI smoke · worker end-to-end. Migration tests live in
`infra/database/migrations/jobs/`. See `ops/orchestration/e2e_proof.md` for the
recorded live run.

## Durable multi-agent core (`kind='agent'`)
A **`kind='agent'`** job runs a headless agent in an isolated git worktree off its `base_ref`:
- **agent-runner** (`run_agent_job` / `run_pool`): worktree off `base_ref` → `claude -p`
  (pinned `--permission-mode acceptEdits`; injectable for the offline fake agent) → capture the
  branch diff + result → on success open a **promotion gate** (job parks `awaiting_promotion`,
  worktree retained for review). `run_pool` fans execution across a bounded `ThreadPoolExecutor`.
- **promotion firewall** (`engine.promote` / `discard_promotion`): the operator-gated no-ff merge
  of a reviewed agent branch into `base_ref` in a throwaway detached worktree + compare-and-swap
  base advance. **Never** advances `main`/`master`/protected refs; refuses checked-out/null bases;
  crash-safe. `discard_promotion` snapshots to `refs/discarded/<id>` (recoverable).
- **durability:** each `run` carries `lease_expires_at` + `heartbeat_at`; `reap()` requeues/fails
  lease-expired runs (crash recovery).
- **env isolation:** agent and review subprocesses receive a **sanitized** env --
  `_agent_env` builds a default-deny allowlisted subset of the worker env (HOME,
  PATH, locale, XDG dirs) plus `APEX_JOB_ENV`; the worker's DB passwords / DSNs /
  tokens are **not** inherited (command jobs, above, still run with the worker env).
- **CLI:** `enqueue --kind agent --base-ref <b> --prompt <p>` · `promotions` · `review <job>` ·
  `approve --gate <g> --by operator` (→ promote) · `reject` (→ discard).

Live `claude -p` proof: `ops/orchestration/e2e_proof_agents.md`.
