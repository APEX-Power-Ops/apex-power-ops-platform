# apex-jobs — Durable Multi-Agent Core (Design)

**Date:** 2026-06-19
**Lane / branch:** `orchestration/durable-multi-agent` (worktree `apex-orch-lane`, host-side)
**Status:** Draft for operator review
**Builds on:** Chip 3 / D-ARCH-3 — `packages/apex-jobs` + `infra/database/migrations/jobs` (merged to `main` `82e0785e`)

---

## Goal

Upgrade the proven `apex-jobs` task bus from a *crash-fragile shell-command queue* into a **durable multi-agent orchestrator**: I author a parallel plan, the bus durably dispatches it, headless `claude -p` agents execute each unit in an isolated git worktree, I audit each diff, and the operator gates promotion — crash-safe throughout.

## Architecture — the loop

```
author plan ─▶ jobs.job (durable queue) ─▶ claim (atomic) ─▶ agent-runner
                                                                  │
                            git worktree off base_ref ◀───────────┘
                                  │
                            claude -p "<prompt>"  ──▶  diff + structured result
                                  │
                            report() ──▶ jobs.run (ledger) + promotion gate
                                  │
              I audit the diff ──▶ operator approves promotion gate ──▶ merge → base_ref
```

Three components, each an independently testable sub-chip:
- **4a — Durability hardening** (pure backend: env-filtered claim, lease/heartbeat, reaper, status-lifecycle closure).
- **4b — Agent-runner** (worktree isolation + headless `claude -p` + diff/result capture + bounded-concurrency pool).
- **4c — Promotion & audit** (post-run promotion gate, review/promote/reject surface).

## Current state (the foundation we extend)

`apex-jobs` already provides, proven e2e on the host:
- `jobs.job` (queue item, subsumes the inbox frontmatter) / `jobs.run` (run+promotion ledger; `env`=sandbox|host trust evidence) / `jobs.gate` (human-approval records) / `jobs.v_eligible`.
- **Atomic claim** — `FOR UPDATE SKIP LOCKED`, priority then dispatch_id; no double-claim.
- **DAG** via `predecessor_id` (a job is eligible only once its predecessor `succeeded`).
- **Pre-execution gates** enforced at the queue boundary: a job with an open `pending` gate is excluded from `v_eligible` (no execution before approval); `start()` refuses a run whose `run_env` ≠ `env_required` (no `host` promotion without `host` evidence).
- Engine (`enqueue/claim/start/report/request_gate/approve/reject/...`), CLI (full lifecycle), worker (`run_once`/`run_forever`).

### Gaps this design closes
1. **Not crash-safe.** `claim()` → `claimed`, `start()` → `running`; if the worker dies, the job is stuck — no lease, heartbeat, or requeue. `run.attempt` is modeled but **nothing retries**.
2. **`claim()` has no env filter.** A `host`-required job can be claimed by a `sandbox` worker; `start()` then parks it `blocked` — and **no path returns a `blocked` (or `awaiting_approval`) job to `pending`**, so it dead-ends.
3. **Executes shell commands, not agents.** `payload.command` via `subprocess`; no agent abstraction, no worktree isolation, no diff/result capture.
4. **No post-execution audit/promotion gate.** Gates are pre-claim only; nothing pauses completed agent work for diff review before it lands.

## Data model — `migrations/jobs/005_durability_and_agents.sql` (+ `_down`)

```sql
-- requires 001, 002, 004. Applied to orchestration_dev (PG17), role orchestration.

-- New job kind: command (today) vs agent (headless claude -p in a worktree).
CREATE TYPE jobs.job_kind_enum AS ENUM ('command', 'agent');

-- New job status for the post-run review pause (distinct from pre-exec awaiting_approval).
-- NOTE: ALTER TYPE ... ADD VALUE autocommits and the value is usable only after
-- this statement commits; keep it as its own statement (psql -f autocommits each).
ALTER TYPE jobs.job_status_enum ADD VALUE IF NOT EXISTS 'awaiting_promotion';

ALTER TABLE jobs.job
  ADD COLUMN kind         jobs.job_kind_enum NOT NULL DEFAULT 'command',
  ADD COLUMN max_attempts int                NOT NULL DEFAULT 1,
  ADD COLUMN base_ref     text;   -- branch agent work merges into on promotion

ALTER TABLE jobs.run
  ADD COLUMN lease_expires_at timestamptz,
  ADD COLUMN heartbeat_at     timestamptz,
  ADD COLUMN worktree_path    text,
  ADD COLUMN branch           text,
  ADD COLUMN diff_stat        text;
```

**Down migration:** drops the five `run` columns + three `job` columns + `job_kind_enum`. Postgres has no `DROP VALUE`, so the unused `awaiting_promotion` enum value is **left in place** (harmless; full removal needs a type rebuild) — documented in the `_down` file, consistent with the "each file reverses cleanly" convention except for the irreversible enum value.

`v_eligible` is **unchanged in shape** but `claim()` gains an env predicate (below) — implemented in the query, not the view, so existing eligibility semantics are preserved.

## 4a — Durability hardening

**Config:** `lease_ttl` (default 30 min, env-overridable) — generous enough for long agent runs, bounded by heartbeats.

- **Env-filtered claim.** `claim(as_, env)` adds `AND (env_required = 'any' OR env_required = :env)` to the eligible query, so a worker only claims jobs it can actually run. This removes the primary source of `blocked` jobs.
- **Lease.** `start()` stamps `run.lease_expires_at = now() + lease_ttl`, `heartbeat_at = now()`. New `heartbeat(run_id)` extends both — the agent-runner calls it periodically during long runs.
- **Reaper.** New `reap()` (engine) + `apex-jobs reap` (CLI) + an opportunistic call inside the worker loop:
  - Find `jobs.run` with `status='running'` AND `lease_expires_at < now()`.
  - Mark the run `failed` (`exit_code=NULL`, result note `lease_expired`).
  - If the owning job's completed `attempt` count `< max_attempts`: requeue job → `pending` (re-claimable). Else: job → `failed`.
  - Stale worktrees from reaped runs are recorded for cleanup (cleaned by the agent-runner's pre-flight or `apex-jobs reap --prune`).
- **Status-lifecycle closure.** `approve(gate)` — if the owning job is `awaiting_approval` and it now has **no** remaining open gate, flip it back to `pending` (re-claimable). `unblock(job)` (CLI) — return a `blocked` job to `pending`. Net: every non-terminal status has a path back to `pending`; no dead-ends.

## 4b — Agent-runner

**Provisioning prerequisite (plan Task 0):** install `@anthropic-ai/claude-code` on the host (node v20.20.2 present); operator runs `claude` OAuth login once (flat-cost Max). I set preconditions + verify `claude -p` works; I never handle the credential. Until this is done, 4b tests run against a **fake agent** (below) and the live path is skipped.

**Per-target command template** (CLI-agnostic; `cc` provisioned first):
```python
AGENT_CMD = {
    "cc":    ["claude", "-p", "{prompt}", "--output-format", "json"],  # exact flags pinned at impl via `claude --help`
    "codex": ["codex", "exec", "{prompt}"],                            # future second seat
}
```
Resolved by `job.target` (default `cc`). Overridable via env/config; tests inject a fake.

**`run_agent_job(job, env)`** (the `kind='agent'` execution path):
1. **Pre-flight:** resolve `base_ref` (from `job.base_ref`, else the lane branch); ensure the agent CLI is resolvable for `job.target` (else GateError → `blocked`).
2. **Isolate:** `git worktree add <runs_dir>/<dispatch_id> -b job/<dispatch_id> <base_ref>`. Record `run.worktree_path` + `run.branch`.
3. **Execute:** run `AGENT_CMD[target]` with `cwd=<worktree>`, `env={**os.environ, "APEX_JOB_ENV": env}` (OAuth session inherited from host `~/.claude`), a **timeout**, and periodic `heartbeat(run_id)`. Capture stdout (JSON → structured result), stderr (→ log file at `log_ref`), exit code.
4. **Capture work:** commit any uncommitted changes on `job/<dispatch_id>` (`git -C <worktree> add -A && git commit`), then compute the branch's **total diff vs base** — `git diff <base_ref>...job/<dispatch_id>` — into `run.diff_stat` (`--stat`) and `run.result.diff` (full; tail in DB, full in `log_ref`). This captures work whether the agent committed it itself or left it uncommitted, and makes promotion a clean branch merge.
5. **Report:** `report(run_id, exit_code, result={...})`. **On success:** create a `promotion` gate (`gate_type='promotion'`), set job → `awaiting_promotion`, and **leave the worktree intact** for real-tree audit. **On failure:** worktree retained for diagnosis; reaper/retry policy applies.

**Parallelism — `run_pool(as_, env, concurrency=N)`:** a `ThreadPoolExecutor(max_workers=N)` that repeatedly claims an eligible job and runs it end-to-end (claim→worktree→agent→report→gate) until the queue is empty, ≤ N concurrent. Each agent run is a subprocess (no GIL contention). This is the parallel execution for this chip; **supervised always-on service (systemd self-wake) is a follow-on chip.**

## 4c — Promotion & audit

- **`apex-jobs promotions`** — jobs in `awaiting_promotion` (the review queue).
- **`apex-jobs review <job>`** — the run's structured result + `diff_stat` + full diff + `worktree_path`/`branch`, so I (or the operator) can inspect the real tree.
- **Promotion = approving the `promotion` gate.** `apex-jobs approve --gate <promotion-gate> --by operator` triggers `promote(job)`:
  - No-ff merge of `job/<dispatch_id>` → `base_ref` (exact git orchestration — dedicated merge checkout vs. lane worktree — pinned at impl).
  - **On conflict:** abort the merge, leave job `awaiting_promotion`, retain the worktree, surface the conflict (promotion fails loudly; never a partial merge).
  - **On success:** job → `succeeded`; remove the job worktree + delete the `job/<dispatch_id>` branch.
- **Reject** (`reject --gate <promotion-gate>`) → `promote` skipped; worktree + branch discarded; job → `cancelled`.

## Trust model / invariants preserved
- **No execution before approval** (pre-exec gates) and **no work lands before review** (promotion gate) — both enforced at the queue boundary, uniform `jobs.gate` mechanism (`gate_type` in `{approval, schema, …, promotion}`).
- **Promotion never auto-merges to `main`.** `base_ref` defaults to the lane/feature branch; `main` only via an explicit, separate operator gate.
- **`env` stays the trust evidence** in the ledger; agent jobs default `env_required='host'` (they touch the real repo), so a `host` worker + the env gate still govern them.

## Error handling
- **Worker/host crash mid-run** → lease expires → reaper requeues (≤ `max_attempts`) or fails. Idempotent: a requeued agent job prunes its stale worktree on pre-flight before re-isolating.
- **Agent non-zero exit / timeout** → run `failed`; retry policy applies; worktree retained for diagnosis.
- **Empty diff** (agent made no changes) → run still `succeeded` but flagged `no_changes` in result; promotion gate still created so I can see "nothing to merge" and reject/close it.
- **Promote merge conflict** → abort + surface (above); never partial.
- **Concurrency** → atomic `SKIP LOCKED` claim already prevents double-claim; per-job worktrees prevent file collisions across parallel agents.

## Testing strategy (TDD, `orchestration_test`)
- **Durability (4a)** — deterministic, no agent: lease stamping; reaper requeues a lease-expired run and respects `max_attempts`; env-filtered claim skips mismatched jobs; `approve` returns an `awaiting_approval` job to `pending`; `unblock`.
- **Agent-runner (4b)** — a **fake agent** (`tests/fake_agent.py`): writes a known file + prints known JSON, exit 0; a failing variant exits 1. Tests assert worktree creation, diff/result capture, promotion-gate creation on success, worktree retention, `run_pool` runs N concurrently without collision — **all offline, zero tokens, no OAuth.**
- **Promotion (4c)** — fake-agent diff → `promote` merges to `base_ref` + cleans up; conflict → aborts + retains; reject → discards.
- **Live e2e proof** (separate, manual, opt-in like `ops/orchestration/e2e_proof.md`) — one real `claude -p` agent job end-to-end after provisioning, recorded.
- Run: `APEX_JOBS_DB=orchestration_test uv run --with "psycopg[binary]" --with pytest pytest`.

## Security / credentials
- OAuth login is **out-of-band** (operator-performed; I verify only). No API key or token in the repo, payloads, or logs.
- **No secrets in `payload`** (public-repo boundary inherited from the inbox model); agent prompts must not embed credentials.
- `log_ref` files live under a host-local, gitignored runs dir — never committed.

## Out of scope → explicit follow-on chips
- **systemd self-wake** — a supervised always-on `run_pool` service (the deferred Phase-3 autonomy).
- **dispatch-inbox cutover** — bridge/migrate `ops/agents/inbox` → `jobs.job`, then retire the git-mutex queue.
- **Plan/DAG batch-authoring ergonomics** — a manifest → many-jobs+edges enqueue helper (a thin Python authoring API may land opportunistically in 4b, but the rich version is later).

## Decisions (technical-authority calls; operator may veto any)
1. Promotion never auto-merges to `main`; `base_ref` default = lane branch; `main` via explicit gate only.
2. Reuse `jobs.gate` for promotion (`gate_type='promotion'`) — one uniform trust model.
3. Agent worktrees persist until promote/reject — audit the real tree, not just a diff string.
4. Runner is CLI-agnostic (per-`target` template); `cc`/`claude` provisioned first.
5. `claim()` gains an env filter (prevents the `blocked` dead-end at the source); reaper + `approve→pending` + `unblock` close every other status dead-end.
6. Lease/visibility-timeout for crash recovery (not advisory locks) — survives full host restart; reaper is idempotent and CLI-invokable.

## Open questions (pinned at implementation, not blockers)
- Exact `claude -p` flags (`--output-format`, permission mode, `--model`, `--max-turns`, timeout) — resolved against `claude --help` in Task 0.
- Promote merge mechanics — dedicated detached merge checkout vs. operating in the lane worktree — chosen for robustness in 4c.
- `lease_ttl` default + heartbeat interval — tuned once a real agent run's duration is observed.
