# PM Idempotency Sweep Schedule Runbook

This runbook covers the deployment-side schedule for the PM idempotency sweep introduced by packet `2026-04-16-pm-schema-019h`.

## Purpose

The scheduled sweep runs the existing CLI at `apps/control-plane-api/scripts/sweep_pm_idempotency.py` so expired rows are removed from `pm.idempotency_keys` on a fixed cadence and on demand.

This is intentionally the smallest available infra-side scheduling surface in the repo:

- the repo already contains `.github/workflows/`
- the repo does not contain a Kubernetes deployment-manifests lane such as `k8s/`, `helm/`, or `infra/deploy/`
- packet `019h` therefore lands on GitHub Actions rather than inventing a new deployment lane

## Artifact

Workflow file:

- `.github/workflows/pm-idempotency-sweep.yml`

Triggers:

- scheduled cadence: every 15 minutes via `cron: '*/15 * * * *'`
- manual invocation: `workflow_dispatch`

Execution path:

- checkout repo
- install Python 3.11
- install `apps/control-plane-api/requirements.txt`
- run `python scripts/sweep_pm_idempotency.py` from `apps/control-plane-api`

## Environment Contract

Required secret:

- `PM_IDEMPOTENCY_SWEEP_DATABASE_URL`

The workflow maps that secret to `DATABASE_URL` for the CLI.

Optional dispatch input:

- `log_level`

The workflow maps that input to `APEX_LOG_LEVEL` and defaults it to `INFO`.

## Behavior When Secret Is Missing

If `PM_IDEMPOTENCY_SWEEP_DATABASE_URL` is unset or empty, the workflow does not fail the run. It logs that the secret is not configured and skips the sweep step.

This keeps repo forks and non-production environments from generating noisy scheduled failures.

## What The Sweep Does

The workflow does not implement its own sweep logic. It invokes the existing packet-019g CLI, which binds the durable idempotency backend and performs the bounded delete against expired rows.

Operationally, the scheduled path is limited to the existing maintenance action:

- delete expired rows from `pm.idempotency_keys`

## What This Schedule Does Not Do

- no new PM write endpoint
- no new HTTP route
- no application-runtime scheduler or background worker
- no DDL or migration edits
- no shape change to `pm.idempotency_keys`
- no changes to `/api/v1/work/*`
- no changes to `/api/v1/ops/*`
- no writes to `work.wbs_nodes`
- no second sweep implementation path

## Manual Run

From GitHub Actions:

1. Open the `PM Idempotency Sweep` workflow.
2. Choose `Run workflow`.
3. Optionally set `log_level`.
4. Start the run.

The workflow will either:

- skip cleanly because the database secret is not configured, or
- run the existing CLI and report success or failure through the job logs

## Rollback

If the scheduled cadence needs to be disabled quickly:

1. Disable the workflow in GitHub Actions, or
2. Remove the `schedule` trigger from `.github/workflows/pm-idempotency-sweep.yml`, or
3. Remove the `PM_IDEMPOTENCY_SWEEP_DATABASE_URL` secret so runs skip without touching the database

No database rollback is required because packet `019h` adds no DDL and no new runtime surface.

## Future Migration Path

If the platform later adopts a real Kubernetes or deployment-manifests lane, the cadence can move from GitHub Actions to a `CronJob` or equivalent deployment-native scheduler.

That future move should remain bounded:

- keep the existing CLI as the single sweep entrypoint
- preserve the current runtime contracts
- avoid introducing an HTTP-triggered sweep endpoint# PM Idempotency Sweep — Schedule Runbook

**Packet:** `2026-04-16-pm-schema-019h`
**Scope:** Deployment-layer schedule wiring for the packet-019g sweep CLI. Zero application-runtime changes.

This runbook documents how the scheduled sweep of `pm.idempotency_keys` is wired, what environment contract it depends on, and how operators run it on demand. It is paired with the GitHub Actions workflow `.github/workflows/pm-idempotency-sweep.yml`.

## What the scheduled sweep does

The workflow runs the existing CLI `apps/control-plane-api/scripts/sweep_pm_idempotency.py` on a fixed cadence and on demand. The CLI binds the idempotency singleton to the durable backend (`config.SessionLocal`) and calls `IdempotencyCache.sweep_expired()`, which issues a single bounded SQL statement against the existing `pm.idempotency_keys` table:

```sql
DELETE FROM pm.idempotency_keys WHERE expires_at <= now()
```

No DDL. No writes outside `pm.idempotency_keys`. No new HTTP surface.

## Why a GitHub Actions scheduled workflow

The repo has no Kubernetes deployment-manifests lane — `infra/` contains only `infra/database/` for SQL migrations. The smallest legitimate scheduled infra surface that already exists is GitHub Actions (`.github/workflows/control-plane-api-ci.yml` is the precedent). Per packet 019h hard requirement §7, when no Kubernetes manifest lane exists, the scheduled workflow is the correct landing lane, and this is documented explicitly.

When the platform later adopts a Kubernetes deployment-manifests lane (for example under `infra/deploy/` or an equivalent directory), a follow-on packet should migrate the cadence from GitHub Actions to a Kubernetes `CronJob`. Until then, the GitHub Actions workflow owns the cadence.

## Schedule

Default cadence is every 15 minutes:

```yaml
on:
  schedule:
    - cron: '*/15 * * * *'
```

This cadence is a safety net, not the primary prune path. The packet-019f durable backend already issues an opportunistic `DELETE ... WHERE expires_at <= now()` at insert time inside `_DurableBackend.register_request`, which keeps the table bounded under normal load. The scheduled sweep ensures that even if no PM POST requests arrive for a long stretch, expired rows are eventually reaped.

Operators may tighten the cadence (for example to every 5 minutes in production) by editing the `cron` expression in the workflow; no other file needs to change.

## On-demand invocation

The workflow exposes a `workflow_dispatch` trigger so operators can run the sweep from the Actions UI without waiting for the next scheduled tick:

1. Go to the repo's **Actions** tab.
2. Select **PM Idempotency Sweep** from the workflow list.
3. Click **Run workflow**, optionally overriding `log_level` (default `INFO`).

The same `DATABASE_URL` contract applies for on-demand runs.

## Environment contract

The CLI reads from the standard `config.py` environment, which means the job needs:

| Variable | Purpose | Source |
|---|---|---|
| `DATABASE_URL` | PostgreSQL URL for the Supabase instance hosting the `pm` schema. | GitHub Actions secret `PM_IDEMPOTENCY_SWEEP_DATABASE_URL`. |
| `APEX_LOG_LEVEL` | Optional log level (`DEBUG` / `INFO` / `WARNING` / `ERROR`). | Workflow input or defaults to `INFO`. |

The secret is intentionally separate from the request-path `DATABASE_URL` used by the control-plane API process. This lets the operator target a different role, search path, or read-write split for the sweep cadence if desired, without coupling to the application-runtime connection config.

If `PM_IDEMPOTENCY_SWEEP_DATABASE_URL` is unset the workflow logs a skip message and exits cleanly — it never fails an empty-config run, so repo forks without the secret don't raise CI noise.

## Setting up the secret

One-time setup for a repo administrator:

1. In the repo settings, navigate to **Secrets and variables → Actions → New repository secret**.
2. Name: `PM_IDEMPOTENCY_SWEEP_DATABASE_URL`.
3. Value: a PostgreSQL connection URL for the target Supabase instance, for example `postgresql://USER:PASSWORD@HOST:PORT/DB`. The role must have `DELETE` on `pm.idempotency_keys`.
4. Save.

The next scheduled tick (or the next `workflow_dispatch` run) picks up the secret automatically.

## What the workflow does NOT do

* It does not call any `/api/v1/*` HTTP surface. The sweep is a Python callable driven via a CLI — no new PM write endpoint, no new ops endpoint, no change to the packet-019g `GET /api/v1/ops/pm-idempotency/stats` surface.
* It does not run migrations. `infra/database/` is untouched.
* It does not touch `work.wbs_nodes` or any other PM entity table.
* It does not change the work schema registry (still 22) or the `/api/v1/work/*` path count (still 15).

## Observing sweep outcomes

The CLI emits a single INFO line on success:

```
PM idempotency sweep complete: N expired row(s) deleted from pm.idempotency_keys.
```

The packet-019g `GET /api/v1/ops/pm-idempotency/stats` endpoint continues to return `{count, expired_count, oldest_expires_at, backend_kind}` live against the production backend. After a successful sweep, `expired_count` should drop toward zero and `oldest_expires_at` should advance forward.

## Rollback

To stop the scheduled cadence temporarily without deleting the workflow, comment out the `schedule` block in `.github/workflows/pm-idempotency-sweep.yml`. `workflow_dispatch` continues to work for on-demand runs. To disable fully, either delete the workflow file or remove the secret `PM_IDEMPOTENCY_SWEEP_DATABASE_URL` (the guard step will begin skipping every run gracefully).

No database rollback is required — the sweep's only effect is deleting rows whose `expires_at` has already passed, and those rows have no semantic value for replay anyway.
