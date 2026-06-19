# apex-jobs — Durable Multi-Agent Core — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (inline) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the merged `apex-jobs` task bus into a durable multi-agent orchestrator — crash-safe queue (lease/heartbeat/reaper), a headless `claude -p` agent-runner that executes each job in an isolated git worktree, and an operator-gated promotion step that merges reviewed agent work to its base branch.

**Architecture:** One additive migration (`jobs/005`) adds agent + durability columns to the existing `jobs.job`/`jobs.run`. The engine gains env-filtered claim, lease/heartbeat/reaper, status-lifecycle closure, and promotion (`open_promotion`/`promote`/`discard_promotion`). A new `agent_runner.py` isolates each `kind='agent'` job in a `git worktree`, runs the per-`target` agent CLI (`cc → claude -p`), captures the branch diff + structured result, and opens a promotion gate; `run_pool()` runs N concurrently. A fake-agent harness makes the whole runner TDD-able offline (zero tokens, no OAuth). Built in the existing host lane worktree `apex-orch-lane` (branch `orchestration/durable-multi-agent`).

**Tech Stack:** PostgreSQL 17 (host container `apex-dev-pg`, `127.0.0.1:5432`); Python 3.11 + psycopg3; uv (`uv run --with`); pytest; `psql` for migration apply; git worktrees; headless `@anthropic-ai/claude-code` (`claude -p`, OAuth/Max). SQL `.sql` + `_down.sql` per the `infra/database/migrations/jobs/` convention.

## Global Constraints
- **DEV-ONLY:** `orchestration_dev` / `orchestration_test` (+ a throwaway base branch in tests). NEVER prod, NEVER auto-merge to `main`.
- **Promotion target:** `base_ref` defaults to the job's stated base; `main` only via an explicit, separate operator gate (not in this chip).
- **Untouched:** the parallel `power-test-converters` WIP and `records/chip10-import` stay out of every commit.
- **Credentials:** dev password lives only in gitignored `infra/.env`; **source it, never echo the literal.** OAuth login is operator-performed (out-of-band); no secret in repo, payloads, or logs. No secrets in agent `payload` (public-repo boundary).
- **Where:** all build/test/commit on the Olares host over mesh SSH as the `olares` user, in the `apex-orch-lane` worktree.
- **Additivity:** `jobs/005` is additive (`kind` defaults `command`); existing command jobs + the 15 foundation tests must stay green.

**Host shell conventions (every task):**
- `R=/home/olares/code/apex/apex-orch-lane` ; run from there (or `packages/apex-jobs`).
- `UV="$HOME/.local/bin/uv"` (uv is not on the non-interactive SSH PATH).
- Recreate the gitignored `infra/.env` in the lane once (new worktrees don't carry gitignored files): `cp /home/olares/code/apex/apex-power-ops-platform/infra/.env "$R/infra/.env"`
- Load the password by **sourcing** it (robust whether or not the value is quoted — `grep|cut` is NOT, it keeps any quotes; never echo it): `set -a; . "$R/infra/.env"; set +a`
- Test DSN: `host=127.0.0.1 port=5432 dbname=orchestration_test user=orchestration password=$DEV_PG_PASSWORD sslmode=disable` ; runtime DSN: same with `dbname=orchestration_dev`.
- Engine/CLI target the DB via `APEX_JOBS_DB` (default `orchestration_dev`); tests pin `APEX_JOBS_DB=orchestration_test`.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `infra/database/migrations/jobs/005_durability_and_agents.sql` (+ `_down`) | `job_kind_enum`; `job.kind/max_attempts/base_ref`; `run.lease_expires_at/heartbeat_at/worktree_path/branch/diff_stat`; `job_status_enum += awaiting_promotion` |
| `infra/database/migrations/jobs/test_005_durability_schema.py` | new columns/enum present; additive (job/run still hold their 002 columns); down drops the columns + `job_kind_enum` |
| `infra/database/migrations/jobs/MANIFEST.md` | add the `005` row + an Agents/Durability note (modify) |
| `packages/apex-jobs/src/apex_jobs/engine.py` | env-filtered `claim`; `heartbeat`; `reap`; `unblock`; `approve` lifecycle-closure; `set_run_artifacts`; `open_promotion`; `promote`; `discard_promotion` (modify) |
| `packages/apex-jobs/src/apex_jobs/agent_runner.py` | `run_agent_job` (worktree isolate → agent CLI → capture diff/result → promotion gate); `run_pool` (bounded concurrency); per-`target` `AGENT_CMD` (create) |
| `packages/apex-jobs/src/apex_jobs/worker.py` | dispatch by `kind` (command vs agent); opportunistic `reap()`; keep `run_once`/`run_forever` (modify) |
| `packages/apex-jobs/src/apex_jobs/cli.py` | new verbs `reap`/`promotions`/`review`/`promote`/`unblock`; agent fields on `enqueue` (`--kind --base-ref --max-attempts --prompt`) (modify) |
| `packages/apex-jobs/tests/fake_agent.py` | deterministic fake agent: writes a file + prints JSON, exit 0; `--fail` variant exits 1 (create) |
| `packages/apex-jobs/tests/test_durability.py` | env-filtered claim; lease stamp; reaper requeue ≤ max_attempts then fail; `approve`→pending; `unblock` (create) |
| `packages/apex-jobs/tests/test_agent_runner.py` | worktree isolate + diff/result capture + promotion gate on success + worktree retained; `run_pool` runs N concurrently, no collision (create) |
| `packages/apex-jobs/tests/test_promotion.py` | `promote` merges → base advances + worktree/branch removed; conflict → abort + retained; `discard_promotion` → cancelled + cleaned (create) |
| `packages/apex-jobs/tests/test_cli_agents.py` | CLI smoke for the new verbs + agent enqueue (create) |
| `packages/apex-jobs/README.md` | agent jobs, promotion, reaper, `run_pool` (modify) |
| `ops/orchestration/e2e_proof_agents.md` | recorded live `claude -p` agent proof (create; after Task 0 provisioning) |

---

## Task 0: Provisioning + baseline (infra; one operator-gated step)

**Files:** none committed here except possibly nothing; this is host setup + verification.

- [ ] **Step 1: Verify the lane worktree + uv + psql + a clean green baseline**

```bash
ssh olares-mesh 'set -e; R=/home/olares/code/apex/apex-orch-lane; cd "$R"; \
  git worktree list | grep apex-orch-lane; git branch --show-current; \
  "$HOME/.local/bin/uv" --version; which psql; \
  set -a; . "$R/infra/.env"; set +a; \
  cd packages/apex-jobs && APEX_JOBS_DB=orchestration_test "$HOME/.local/bin/uv" run --with "psycopg[binary]" --with pytest --with-editable . pytest -q'
```
Expected: branch `orchestration/durable-multi-agent`; uv version; `/usr/bin/psql`; **15 passed** (the foundation baseline). If `orchestration_test` is missing, create it (idempotent), then re-run:
```bash
ssh olares-mesh 'set -a; . /home/olares/code/apex/apex-orch-lane/infra/.env; set +a; \
  for db in orchestration_dev orchestration_test; do \
    PGPASSWORD=$DEV_PG_PASSWORD psql -h 127.0.0.1 -p 5432 -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='"'"'$db'"'"'" | grep -q 1 || \
    PGPASSWORD=$DEV_PG_PASSWORD psql -h 127.0.0.1 -p 5432 -U postgres -c "CREATE DATABASE $db OWNER orchestration"; done'
```

- [ ] **Step 2: Install the headless agent CLI on the host (no sudo — nvm-user npm)**

```bash
ssh olares-mesh '. "$HOME/.nvm/nvm.sh"; npm i -g @anthropic-ai/claude-code && command -v claude && claude --version'
```
Expected: `claude` resolves + prints a version. If npm global needs a user prefix, set `npm config set prefix "$HOME/.npm-global"` and add `$HOME/.npm-global/bin` to PATH first.

- [ ] **Step 3: 🛑 OPERATOR-GATED — authenticate `claude` (OAuth/Max), out-of-band**

I do not run this; the operator does, as the `olares` user (the user the worker runs as). STOP and hand off:
> Operator: on the host as `olares`, run `claude` and complete the OAuth/Max login once. Tell me when done.

- [ ] **Step 4: Verify headless `claude -p` works (I run this after the operator confirms)**

```bash
ssh olares-mesh '. "$HOME/.nvm/nvm.sh"; cd /tmp && claude -p "reply with exactly: apex-ok" --output-format json 2>&1 | head -20'
```
Expected: a JSON envelope whose result text contains `apex-ok`. Pin the exact flags we will template (`--output-format`, permission mode, `--model`, timeout) from `claude --help` here and record them in Task 4's `AGENT_CMD`.

> **Note:** Tasks 1–3, 6–7 (durability, promotion, CLI) and the *fake-agent* paths of Tasks 4–5 do NOT need Steps 2–4. Only the live-agent path (Task 4 live opt-in, Task 8 e2e) does. If provisioning is blocked, build everything else; the runner tests run against the fake agent regardless.

---

## Task 1: migration 005 — durability + agent columns [TDD]

**Files:** Create `infra/database/migrations/jobs/005_durability_and_agents.sql` (+ `_down`), `test_005_durability_schema.py`; Modify `MANIFEST.md`.

- [ ] **Step 1: Write the failing test** `test_005_durability_schema.py`

```python
"""TDD — jobs 005 durability + agent columns. RED until 005 exists."""
from _dbtest import psql_file, connect

APPLY = ["001_jobs_enums.sql","002_jobs_tables.sql","003_jobs_indexes.sql",
         "004_jobs_views.sql","005_durability_and_agents.sql"]
DOWN  = ["005_durability_and_agents_down.sql","004_jobs_views_down.sql",
         "003_jobs_indexes_down.sql","002_jobs_tables_down.sql","001_jobs_enums_down.sql"]

def _reset_up():
    for f in DOWN:
        try: psql_file(f)
        except Exception: pass
    for f in APPLY: psql_file(f)

def _cols(c, table):
    return {r[0] for r in c.execute(
        "select column_name from information_schema.columns "
        "where table_schema='jobs' and table_name=%s",(table,)).fetchall()}

def test_new_columns_present_and_additive():
    _reset_up()
    with connect() as c:
        job = _cols(c,"job")
        assert {"kind","max_attempts","base_ref"} <= job, job
        # additive: the 002 columns survive
        assert {"dispatch_id","payload","status","predecessor_id"} <= job
        run = _cols(c,"run")
        assert {"lease_expires_at","heartbeat_at","worktree_path","branch","diff_stat"} <= run
        assert {"attempt","claimed_by","env","exit_code"} <= run

def test_job_kind_enum_and_awaiting_promotion():
    _reset_up()
    with connect() as c:
        kinds = {r[0] for r in c.execute(
            "select e.enumlabel from pg_enum e join pg_type t on t.oid=e.enumtypid "
            "join pg_namespace n on n.oid=t.typnamespace where n.nspname='jobs' and t.typname='job_kind_enum'").fetchall()}
        assert kinds == {"command","agent"}, kinds
        statuses = {r[0] for r in c.execute(
            "select e.enumlabel from pg_enum e join pg_type t on t.oid=e.enumtypid "
            "join pg_namespace n on n.oid=t.typnamespace where n.nspname='jobs' and t.typname='job_status_enum'").fetchall()}
        assert "awaiting_promotion" in statuses, statuses

def test_down_drops_new_columns():
    _reset_up()
    for f in DOWN: psql_file(f)
    # schema is gone after full down (001_down drops schema CASCADE)
    with connect() as c:
        ns = c.execute("select 1 from information_schema.schemata where schema_name='jobs'").fetchone()
        assert ns is None
```

- [ ] **Step 2: Run — verify it FAILS**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-orch-lane/infra/database/migrations/jobs && \
  set -a; . /home/olares/code/apex/apex-orch-lane/infra/.env; set +a; \
  "$HOME/.local/bin/uv" run --with "psycopg[binary]" --with pytest pytest test_005_durability_schema.py -q'
```
Expected: FAIL — `psql 005_durability_and_agents.sql failed` (file absent).

- [ ] **Step 3: Write `005_durability_and_agents.sql`**

```sql
-- jobs 005 — durability + agent columns (requires 001-004). Additive.
-- NOTE: ALTER TYPE ADD VALUE must NOT run inside an explicit txn block; psql -f
-- (no --single-transaction) autocommits each statement, so this is safe as-is.
CREATE TYPE jobs.job_kind_enum AS ENUM ('command', 'agent');
ALTER TYPE jobs.job_status_enum ADD VALUE IF NOT EXISTS 'awaiting_promotion';

ALTER TABLE jobs.job
  ADD COLUMN kind         jobs.job_kind_enum NOT NULL DEFAULT 'command',
  ADD COLUMN max_attempts int                NOT NULL DEFAULT 1,
  ADD COLUMN base_ref     text;

ALTER TABLE jobs.run
  ADD COLUMN lease_expires_at timestamptz,
  ADD COLUMN heartbeat_at     timestamptz,
  ADD COLUMN worktree_path    text,
  ADD COLUMN branch           text,
  ADD COLUMN diff_stat        text;
```

- [ ] **Step 4: Write `005_durability_and_agents_down.sql`**

```sql
-- reverse of 005. The awaiting_promotion enum value is left in place
-- (Postgres has no DROP VALUE; removal needs a full type rebuild — documented).
ALTER TABLE jobs.run
  DROP COLUMN IF EXISTS diff_stat, DROP COLUMN IF EXISTS branch,
  DROP COLUMN IF EXISTS worktree_path, DROP COLUMN IF EXISTS heartbeat_at,
  DROP COLUMN IF EXISTS lease_expires_at;
ALTER TABLE jobs.job
  DROP COLUMN IF EXISTS base_ref, DROP COLUMN IF EXISTS max_attempts,
  DROP COLUMN IF EXISTS kind;
DROP TYPE IF EXISTS jobs.job_kind_enum;
```

- [ ] **Step 5: Run — verify it PASSES** (same command as Step 2). Expected: 3 passed.

- [ ] **Step 6: Update `MANIFEST.md`** — add the `005` row to the execution-order table + a one-line "Durability + agents (Chip: durable multi-agent core)" note.

- [ ] **Step 7: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-orch-lane && git add infra/database/migrations/jobs/ && \
  git commit -q -m "feat(jobs): migration 005 durability + agent columns (TDD)" \
  -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"'
```

---

## Task 2: durability — env-filtered claim + lifecycle closure [TDD]

**Files:** Modify `engine.py` (`claim`, `approve`, add `unblock`); Create `tests/test_durability.py` (claim + lifecycle cases).

- [ ] **Step 1: Failing tests** (in `test_durability.py`):
  - `test_claim_env_filter` — enqueue job A `env_required='host'`, job B `env_required='any'`; `claim(as_="cc", env="sandbox")` returns **B only** (never A); `claim(env="host")` can return A.
  - `test_approve_returns_job_to_pending` — enqueue with `requires_approval=true`; `claim` then `start(run_env=...)` parks it `awaiting_approval` (open gate); `approve(gate)` → job back to `pending` and re-claimable.
  - `test_unblock` — a job forced to `blocked` → `unblock(job)` → `pending`.

- [ ] **Step 2: Run — FAIL** (env-mismatched job still returned / job stuck `awaiting_approval` / no `unblock`). Command:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-orch-lane/packages/apex-jobs && \
  set -a; . /home/olares/code/apex/apex-orch-lane/infra/.env; set +a; \
  APEX_JOBS_DB=orchestration_test "$HOME/.local/bin/uv" run --with "psycopg[binary]" --with pytest --with-editable . pytest test_durability.py -q'
```

- [ ] **Step 3: Implement** in `engine.py`:

`claim(as_=None, env=None)` — add an env predicate to the inline eligible query:
```python
# in the WHERE, after the status/predecessor/gate clauses:
and (j.env_required = 'any' or %(env)s is null or j.env_required = %(env)s)
```
(pass `env` as a named param; `None` ⇒ no env restriction.)

`approve(gate_id, by, note=None)` — after `_decide_gate(...,'approved',...)`, add lifecycle closure:
```python
with _conn() as conn, conn.cursor() as cur:
    cur.execute("""
        update jobs.job j set status='pending', updated_at=now()
        from jobs.gate g
        where g.id=%s and j.id=g.job_id and j.status='awaiting_approval'
          and not exists (select 1 from jobs.gate g2
                          where g2.job_id=j.id and g2.state='pending')
    """, (gate_id,))
    conn.commit()
return gid
```
(Only `awaiting_approval` jobs are reset — `awaiting_promotion` is untouched, so promotion approval flows to `promote()` in Task 6, not back to `pending`.)

`unblock(ident)` — new:
```python
def unblock(ident):
    """Return a blocked job to pending (re-claimable)."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("update jobs.job set status='pending', updated_at=now() "
                    "where (id::text=%s or dispatch_id=%s) and status='blocked' returning id",
                    (str(ident), str(ident)))
        r = cur.fetchone(); conn.commit()
    return r["id"] if r else None
```

- [ ] **Step 4: Run — PASS.** Re-run the **full** suite to confirm additivity (15 baseline + new). 
- [ ] **Step 5: Commit** (`feat(jobs): env-filtered claim + status lifecycle closure (TDD)`).

---

## Task 3: durability — lease + heartbeat + reaper [TDD]

**Files:** Modify `engine.py` (`start` stamps lease; add `heartbeat`, `reap`); Add cases to `test_durability.py`.

- [ ] **Step 1: Failing tests**:
  - `test_start_stamps_lease` — after `claim`+`start`, the run row has `lease_expires_at > now()` and `heartbeat_at` set.
  - `test_reaper_requeues_then_fails` — make a `running` run with `lease_expires_at = now()-1min`, `job.max_attempts=2`: first `reap()` → that run `failed` + job back to `pending` (attempt budget left); after a 2nd run+expiry, `reap()` → job terminal `failed` (budget exhausted). Returns count reaped.
  - `test_heartbeat_extends_lease` — `heartbeat(run_id)` pushes `lease_expires_at` later.

- [ ] **Step 2: Run — FAIL.**

- [ ] **Step 3: Implement** in `engine.py`:

Add `LEASE_TTL_S = int(os.environ.get("APEX_JOBS_LEASE_TTL_S", "1800"))` (import `os`).

In `start(...)`, change the run INSERT to stamp the lease:
```python
"insert into jobs.run (job_id, attempt, claimed_by, env, status, started_at, "
"lease_expires_at, heartbeat_at) values (%s,%s,%s,%s,'running',now(), "
"now() + (%s||' seconds')::interval, now()) returning id",
(job_id, attempt, claimed_by, run_env, str(LEASE_TTL_S)),
```

```python
def heartbeat(run_id, lease_ttl_s=LEASE_TTL_S):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("update jobs.run set heartbeat_at=now(), "
                    "lease_expires_at=now()+(%s||' seconds')::interval "
                    "where id=%s and status='running'", (str(lease_ttl_s), run_id))
        conn.commit()

def reap():
    """Fail lease-expired running runs; requeue the job if attempts remain, else fail it.
    Returns the number of runs reaped."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("""
            select r.id as run_id, r.job_id, j.max_attempts,
                   (select count(*) from jobs.run r2 where r2.job_id=j.id) as attempts
            from jobs.run r join jobs.job j on j.id=r.job_id
            where r.status='running' and r.lease_expires_at is not null
              and r.lease_expires_at < now()
            for update skip locked
        """)
        rows = cur.fetchall()
        for row in rows:
            cur.execute("update jobs.run set status='failed', finished_at=now(), "
                        "result=coalesce(result,'{}'::jsonb)||'{\"reaped\":\"lease_expired\"}'::jsonb "
                        "where id=%s", (row["run_id"],))
            new = 'pending' if row["attempts"] < row["max_attempts"] else 'failed'
            cur.execute("update jobs.job set status=%s, updated_at=now() where id=%s",
                        (new, row["job_id"]))
        conn.commit()
    return len(rows)
```

- [ ] **Step 4: Run — PASS** (full suite). **Step 5: Commit** (`feat(jobs): lease/heartbeat + reaper for crash recovery (TDD)`).

---

## Task 4: agent-runner — fake-agent harness + single-job execution [TDD]

**Files:** Create `agent_runner.py`, `tests/fake_agent.py`; Modify `engine.py` (`set_run_artifacts`, `open_promotion`); Create `tests/test_agent_runner.py`.

- [ ] **Step 1: Write `tests/fake_agent.py`** (the deterministic offline agent)

```python
"""Deterministic fake agent for TDD. Writes a file in cwd + prints a JSON
envelope; `--fail` exits 1 without writing. Stands in for `claude -p`."""
import json, sys, pathlib
def main(argv):
    fail = "--fail" in argv
    prompt = next((a for a in argv if not a.startswith("-")), "")
    if fail:
        print(json.dumps({"result": "refused", "is_error": True})); return 1
    pathlib.Path("AGENT_OUTPUT.md").write_text(f"# done\n\nprompt: {prompt}\n")
    print(json.dumps({"result": "wrote AGENT_OUTPUT.md", "is_error": False})); return 0
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: Write failing `test_agent_runner.py`** (single-job, fake agent):
  - Fixture: create a throwaway **base branch** in a temp clone/repo (or the lane repo) that is *not checked out* — e.g. `git branch test-base-<rand> main`; set `APEX_JOBS_REPO` to that repo, `APEX_JOBS_RUNS_DIR` to a tmp dir.
  - `test_agent_job_success` — enqueue `kind='agent'`, `target='cc'`, `base_ref=test-base-*`, `env_required='host'`, payload `{"prompt":"write a file"}`. Run `run_agent_job(job, env="host", agent_cmd=[sys.executable, fake_agent_path])`. Assert: a `job/<dispatch_id>` worktree exists with `AGENT_OUTPUT.md`; the run row has `worktree_path`, `branch`, non-empty `diff_stat`, `status='succeeded'`; a `gate` row `gate_type='promotion'` exists; job `status='awaiting_promotion'`; **worktree NOT removed**.
  - `test_agent_job_failure` — `agent_cmd=[..., "--fail"]` → run `failed`, **no** promotion gate, worktree retained.
  - `test_agent_job_no_changes` — a fake agent that writes nothing → run `succeeded`, `result.no_changes is True`, promotion gate still opened.

- [ ] **Step 3: Run — FAIL** (`ModuleNotFoundError: apex_jobs.agent_runner`).

- [ ] **Step 4: Implement `engine.py` helpers**

```python
def set_run_artifacts(run_id, worktree_path=None, branch=None, diff_stat=None):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("update jobs.run set worktree_path=coalesce(%s,worktree_path), "
                    "branch=coalesce(%s,branch), diff_stat=coalesce(%s,diff_stat) where id=%s",
                    (worktree_path, branch, diff_stat, run_id))
        conn.commit()

def set_base_ref(job_id, base_ref):
    """Persist the resolved base_ref when the job was enqueued without one (promote() needs it)."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("update jobs.job set base_ref=%s, updated_at=now() "
                    "where id=%s and base_ref is null", (base_ref, job_id))
        conn.commit()

def open_promotion(job_id):
    """Create a pending promotion gate + move the job to awaiting_promotion."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("insert into jobs.gate (job_id, gate_type) values (%s,'promotion') returning id",(job_id,))
        gid = cur.fetchone()["id"]
        cur.execute("update jobs.job set status='awaiting_promotion', updated_at=now() where id=%s",(job_id,))
        conn.commit()
    return gid
```

- [ ] **Step 5: Implement `agent_runner.py`**

```python
"""apex-jobs agent-runner — execute a kind='agent' job in an isolated git
worktree via a headless agent CLI; capture the branch diff + structured result;
open a promotion gate on success. Offline-testable by injecting agent_cmd."""
import os, subprocess, json, threading
from . import engine

LEASE_TTL_S = engine.LEASE_TTL_S
REPO     = os.environ.get("APEX_JOBS_REPO", os.path.expanduser("~/code/apex/apex-orch-lane"))
RUNS_DIR = os.environ.get("APEX_JOBS_RUNS_DIR", os.path.expanduser("~/.apex-jobs/runs"))
TIMEOUT  = int(os.environ.get("APEX_JOBS_AGENT_TIMEOUT_S", "3600"))

AGENT_CMD = {  # exact flags pinned in Task 0 Step 4
    "cc":    ["claude", "-p", "{prompt}", "--output-format", "json"],
    "codex": ["codex", "exec", "{prompt}"],
}

def _git(*args, cwd=REPO, check=True):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=check)

def _agent_argv(target, prompt):
    tmpl = AGENT_CMD.get(target if target in AGENT_CMD else "cc")
    return [a.replace("{prompt}", prompt) for a in tmpl]

def run_agent_job(job, env, as_="cc", agent_cmd=None):
    run_id = engine.start(job["id"], claimed_by=as_, run_env=env)   # raises GateError if gated
    base_ref = job.get("base_ref") or _git("rev-parse","--abbrev-ref","HEAD").stdout.strip()
    if not job.get("base_ref"):
        engine.set_base_ref(job["id"], base_ref)   # persist resolved base for promote()
    branch = f"job/{job['dispatch_id']}"
    wt = os.path.join(RUNS_DIR, job["dispatch_id"])
    os.makedirs(RUNS_DIR, exist_ok=True)
    _git("worktree","remove","--force",wt, check=False)            # idempotent (requeue-safe)
    _git("branch","-D",branch, check=False)
    _git("worktree","add","-b",branch,wt,base_ref)
    prompt = (job.get("payload") or {}).get("prompt","")
    argv = agent_cmd or _agent_argv(job.get("target","cc"), prompt)
    stop = threading.Event()
    def _hb():
        while not stop.wait(LEASE_TTL_S/3): 
            try: engine.heartbeat(run_id)
            except Exception: pass
    threading.Thread(target=_hb, daemon=True).start()
    try:
        proc = subprocess.run(argv, cwd=wt, env={**os.environ,"APEX_JOB_ENV":env},
                              capture_output=True, text=True, timeout=TIMEOUT)
        rc = proc.returncode; out, err = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        rc, out, err = 124, (e.stdout or ""), f"timeout after {TIMEOUT}s"
    finally:
        stop.set()
    _git("add","-A",cwd=wt,check=False)
    _git("-c","user.email=apex-jobs@local","-c","user.name=apex-jobs",
         "commit","-m",f"agent:{job['dispatch_id']}","--allow-empty",cwd=wt,check=False)
    diff_stat = _git("diff","--stat",f"{base_ref}...{branch}",check=False).stdout
    diff      = _git("diff",f"{base_ref}...{branch}",check=False).stdout
    result = {"stdout":out[-4000:], "stderr":err[-4000:], "diff":diff[-8000:],
              "no_changes": diff.strip()==""}
    status = engine.report(run_id, exit_code=rc, result=result)
    engine.set_run_artifacts(run_id, worktree_path=wt, branch=branch, diff_stat=diff_stat)
    if status=="succeeded":
        engine.open_promotion(job["id"])
    return {"job":job["dispatch_id"],"run":str(run_id),"status":status,"no_changes":result["no_changes"]}
```

- [ ] **Step 6: Run — PASS** (`test_agent_runner.py`, all fake-agent). **Step 7: Commit** (`feat(jobs): agent-runner with worktree isolation + promotion gate (TDD)`).

- [ ] **Step 8 (optional, live, after Task 0 provisioning):** one real `run_agent_job` with no injected `agent_cmd` against a throwaway base branch in `orchestration_dev`; confirm `claude -p` produced a diff. Defer to Task 8 if provisioning is pending.

---

## Task 5: agent-runner — bounded-concurrency pool [TDD]

**Files:** Modify `agent_runner.py` (`run_pool`); Add a case to `test_agent_runner.py`.

- [ ] **Step 1: Failing test** `test_run_pool_concurrency` — enqueue 4 `kind='agent'` jobs (each base off its own throwaway base branch); `run_pool(as_="cc", env="host", concurrency=3, agent_cmd=[sys.executable, fake_agent_path])` returns 4 summaries; each job ends `awaiting_promotion`; each has a **distinct** worktree (no path collision); assert the pool honored ≤3 in flight (a fake agent that writes a sentinel + sleeps briefly; max concurrent sentinels ≤ 3).

- [ ] **Step 2: Run — FAIL** (no `run_pool`).

- [ ] **Step 3: Implement** in `agent_runner.py`:
```python
from concurrent.futures import ThreadPoolExecutor

def run_pool(as_, env, concurrency=4, agent_cmd=None, max_jobs=None):
    """Drain eligible agent/command jobs, up to `concurrency` in flight, until the
    queue is empty (or max_jobs reached). Returns the list of summaries."""
    results, in_flight = [], set()
    done = 0
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        while True:
            engine.reap()                                  # opportunistic crash recovery
            job = engine.claim(as_=as_, env=env)
            if job is None:
                if not in_flight: break
            else:
                fut = ex.submit(_run_one, job, env, as_, agent_cmd)
                in_flight.add(fut)
            # harvest finished
            for fut in [f for f in in_flight if f.done()]:
                results.append(fut.result()); in_flight.discard(fut); done += 1
            if max_jobs and done >= max_jobs: break
            if job is None:
                # wait for at least one in-flight to finish before re-polling
                next(iter(in_flight)).result()
    return results

def _run_one(job, env, as_, agent_cmd):
    if job.get("kind") == "agent":
        return run_agent_job(job, env, as_=as_, agent_cmd=agent_cmd)
    # command job — preserve the existing worker path
    from .worker import _run_command_job
    return _run_command_job(job, env, as_)
```
(**Extract now** — pull the command-run body from `worker.run_once` into `worker._run_command_job(job, env, as_)` so both the pool and `run_once` share it; `run_once` keeps working by delegating to it. Task 6 then adds `kind`-dispatch on top.)

- [ ] **Step 4: Run — PASS. Step 5: Commit** (`feat(jobs): bounded-concurrency agent pool (TDD)`).

---

## Task 6: promotion + audit (engine.promote/discard + worker dispatch) [TDD]

**Files:** Modify `engine.py` (`promote`, `discard_promotion`, `PromoteConflict`); Modify `worker.py` (`kind` dispatch + `_run_command_job` + reap step); Create `tests/test_promotion.py`.

- [ ] **Step 1: Failing `test_promotion.py`** (fake-agent fixtures):
  - `test_promote_merges_to_base` — run a fake-agent job off `test-base-*`; `promote(job)` → `test-base-*` now contains `AGENT_OUTPUT.md` (ref advanced), the `job/<id>` worktree removed + branch deleted, job `status='succeeded'`.
  - `test_promote_conflict_aborts` — pre-commit a conflicting change to `test-base-*` after the worktree branched; `promote` raises `PromoteConflict`, base unchanged, worktree retained, job stays `awaiting_promotion`.
  - `test_discard_promotion` — `discard_promotion(job)` → worktree + branch gone, base unchanged, job `status='cancelled'`.

- [ ] **Step 2: Run — FAIL.**

- [ ] **Step 3: Implement** in `engine.py`:
```python
class PromoteConflict(Exception): ...

def _git(*a, cwd, check=True):
    import subprocess
    return subprocess.run(["git","-C",cwd,*a], capture_output=True, text=True, check=check)

def promote(ident, repo=None):
    """No-ff merge job/<dispatch_id> into its base_ref via a throwaway detached
    worktree, then advance the base ref. Conflict → abort + raise PromoteConflict.
    Success → remove the job worktree/branch + set job succeeded. base_ref MUST NOT
    be a currently-checked-out branch."""
    import os, tempfile
    repo = repo or os.environ.get("APEX_JOBS_REPO", os.path.expanduser("~/code/apex/apex-orch-lane"))
    job = get_job(ident); base = job["base_ref"]; branch = f"job/{job['dispatch_id']}"
    tmp = tempfile.mkdtemp(prefix="apex-promote-")
    try:
        _git("worktree","add","--detach",tmp,base,cwd=repo)
        m = _git("merge","--no-ff","-m",f"promote {job['dispatch_id']}",branch,cwd=tmp,check=False)
        if m.returncode != 0:
            _git("merge","--abort",cwd=tmp,check=False)
            raise PromoteConflict(m.stdout+m.stderr)
        newsha = _git("rev-parse","HEAD",cwd=tmp).stdout.strip()
        _git("update-ref",f"refs/heads/{base}",newsha,cwd=repo)
    finally:
        _git("worktree","remove","--force",tmp,cwd=repo,check=False)
    # cleanup the job worktree + branch
    _runs = runs_for(job["id"]); wt = _runs[-1].get("worktree_path") if _runs else None
    if wt: _git("worktree","remove","--force",wt,cwd=repo,check=False)
    _git("branch","-D",branch,cwd=repo,check=False)
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("update jobs.job set status='succeeded', updated_at=now() where id=%s",(job["id"],))
        conn.commit()
    return base

def discard_promotion(ident, repo=None):
    import os
    repo = repo or os.environ.get("APEX_JOBS_REPO", os.path.expanduser("~/code/apex/apex-orch-lane"))
    job = get_job(ident); branch = f"job/{job['dispatch_id']}"
    _runs = runs_for(job["id"]); wt = _runs[-1].get("worktree_path") if _runs else None
    if wt: _git("worktree","remove","--force",wt,cwd=repo,check=False)
    _git("branch","-D",branch,cwd=repo,check=False)
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("update jobs.job set status='cancelled', updated_at=now() where id=%s",(job["id"],))
        conn.commit()
```

- [ ] **Step 4: `worker.py` kind-dispatch** — make `run_once` dispatch by `kind` (`agent` → `agent_runner.run_agent_job`, else the `worker._run_command_job` extracted in Task 5), and call `engine.reap()` once per idle poll in `run_forever`. Existing `test_worker.py` must stay green.

- [ ] **Step 5: Run — PASS** (`test_promotion.py` + full suite). **Step 6: Commit** (`feat(jobs): promotion merge + discard + worker kind-dispatch (TDD)`).

---

## Task 7: CLI — new verbs + agent enqueue fields [TDD smoke]

**Files:** Modify `cli.py`; Create `tests/test_cli_agents.py`.

- [ ] **Step 1: Failing `test_cli_agents.py`** (invoke `cli.main(argv)`, capture stdout):
  - `enqueue --kind agent --dispatch-id a-1 --title x --base-ref test-base --prompt "do x" --env-required host` → prints job id; `get_job` shows `kind='agent'`, `base_ref`, payload `{"prompt":"do x"}`.
  - `promotions` → lists `a-1` after a fake-agent run leaves it `awaiting_promotion`.
  - `review a-1` → prints the diff_stat + worktree path.
  - `reap` → prints a count. `unblock <job>` → prints ok.
  - `promote --gate <promotion-gate> --by operator` path: `approve` of a `promotion` gate triggers `engine.promote` (CLI orchestrates: approve gate → if `gate_type='promotion'` then promote; `reject` → discard_promotion).

- [ ] **Step 2: Run — FAIL.**

- [ ] **Step 3: Implement `cli.py`** — add subparsers:
  - `enqueue`: add `--kind {command,agent}` (default command), `--base-ref`, `--max-attempts` (int), `--prompt` (folded into `payload={"prompt":...}` when `--kind agent`).
  - `reap` → `engine.reap()`; `promotions` → jobs in `awaiting_promotion` (new `engine.list_promotions()`); `review <job>` → latest run's `diff_stat`/`worktree_path`/`branch` + result; `unblock <job>` → `engine.unblock`.
  - `approve --gate --by`: after `engine.approve`, fetch the gate; if `gate_type='promotion'` → `engine.promote(job_id)` (catch `PromoteConflict` → non-zero exit + message). `reject --gate --by`: if promotion gate → `engine.discard_promotion(job_id)`.

- [ ] **Step 4: Run — PASS. Step 5: Commit** (`feat(jobs): CLI agent enqueue + reap/promotions/review/promote (TDD)`).

---

## Task 8: live e2e proof (real `claude -p`) on `orchestration_dev`

**Files:** Create `ops/orchestration/e2e_proof_agents.md`. **Prereq:** Task 0 Steps 2–4 complete (operator OAuth done).

- [ ] **Step 1:** create a throwaway base branch `e2e-base-2026-06-19` off `main` (not checked out).
- [ ] **Step 2:** `apex-jobs enqueue --kind agent --dispatch-id 2026-06-19-agent-canary --title "agent canary" --base-ref e2e-base-2026-06-19 --env-required host --prompt "Create a file HELLO.md containing the single line: apex agent works."`
- [ ] **Step 3:** `python -c "from apex_jobs.agent_runner import run_pool; print(run_pool(as_='cc', env='host', concurrency=1, max_jobs=1))"` → job `awaiting_promotion`; `apex-jobs review 2026-06-19-agent-canary` shows a diff adding `HELLO.md`.
- [ ] **Step 4:** `apex-jobs approve --gate <promotion-gate> --by operator` → `e2e-base-2026-06-19` now contains `HELLO.md`; worktree/branch cleaned; job `succeeded`.
- [ ] **Step 5:** record the transcript in `ops/orchestration/e2e_proof_agents.md`; clean the throwaway base branch; **commit**.

---

## Task 9: docs + push + SSoT reconcile

- [ ] **Step 1:** `packages/apex-jobs/README.md` — add the agent-job model (`kind`, `base_ref`, `prompt`), the promotion gate + `review`/`promote` flow, the reaper, and `run_pool`.
- [ ] **Step 2:** Push: `git push -u origin orchestration/durable-multi-agent`.
- [ ] **Step 3:** SSoT — append STATE `## section N` + bump `RESUME_HERE.md` (durable multi-agent core built+tested; live-agent proof status); update memory `apex-operating-architecture-2026-06-18` (orchestration: durable multi-agent core). PR to `main` is the operator's call (the orchestration lane merge precedent).

---

## Self-Review notes
- **Spec coverage:** migration 005 (T1) ✓; durability — env-filtered claim + lifecycle closure (T2) + lease/heartbeat/reaper (T3) ✓; agent-runner worktree isolation + capture + promotion gate (T4) + bounded concurrency (T5) ✓; promotion merge/discard + worker kind-dispatch (T6) ✓; CLI (T7) ✓; live `claude -p` e2e (T8) ✓; docs/push/SSoT (T9) ✓. The fake-agent harness covers the whole runner offline; one recorded live proof.
- **Additivity:** 005 is additive; the 15 foundation tests + `test_worker` re-run green after T2/T3/T6.
- **Promote safety:** never `main`; `base_ref` must be a non-checked-out branch; merge via throwaway detached worktree + `update-ref`; conflict → abort + retain (loud, never partial).
- **Credentials:** `DEV_PG_PASSWORD` sourced from `infra/.env`, never echoed; OAuth out-of-band (operator); no secrets in payloads/logs; `RUNS_DIR` host-local + gitignored.
- **Open risk:** exact `claude -p` flags pinned in T0S4 before T4's `AGENT_CMD` is trusted live; `lease_ttl`/heartbeat tuned after observing a real run (T8).
