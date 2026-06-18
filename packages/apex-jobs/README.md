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
gates · status · ledger`. Target a database with `APEX_JOBS_DB` (default
`orchestration_dev`) or `APEX_JOBS_DSN`; connects as the `orchestration` role.
The dev password lives in the gitignored `infra/.env` — never committed.

## Worker
```python
from apex_jobs.worker import run_once, run_forever
run_once(as_="cc", env="host")          # claim→gates→subprocess(payload.command)→report
run_forever(as_="cc", env="host", poll_s=5.0)
```
The subprocess runs with `APEX_JOB_ENV` set to the worker's env.

## Coexistence
apex-jobs runs **alongside** the `ops/agents/inbox` file queue. No cutover yet —
the inbox remains the live mechanism until apex-jobs is proven in routine use.

## Tests (15)
```
APEX_JOBS_DB=orchestration_test uv run --with pytest pytest
```
enqueue/idempotency · atomic SKIP-LOCKED claim · predecessor + env + human gates ·
run-ledger finalize · CLI smoke · worker end-to-end. Migration tests live in
`infra/database/migrations/jobs/`. See `ops/orchestration/e2e_proof.md` for the
recorded live run.
