# PM Idempotency Metrics Export Runbook

This runbook covers:

- the deployment-side metrics exporter introduced by packet `2026-04-16-pm-schema-019j`
- the bounded threshold-evaluation step layered onto the same workflow by packet `2026-04-16-pm-schema-019k`

## Purpose

The scheduled exporter scrapes the two existing read-only PM idempotency ops endpoints:

- `GET /api/v1/ops/pm-idempotency/stats`
- `GET /api/v1/ops/pm-idempotency/by-route`

It writes the fetched JSON payloads into a GitHub Actions artifact and renders a concise markdown summary in the workflow run.

This is intentionally the smallest available infra-side exporter surface in the repo:

- the repo already contains `.github/workflows/`
- packet `019h` already established GitHub Actions as the legitimate deployment-side schedule lane
- packet `019j` therefore lands as a second bounded workflow in the same lane rather than introducing a background worker, database table, or runtime exporter service

## Artifact

Workflow file:

- `.github/workflows/pm-idempotency-metrics-export.yml`

Triggers:

- scheduled cadence: every 15 minutes via `cron: '*/15 * * * *'`
- manual invocation: `workflow_dispatch`

Execution path:

- checkout repo
- install Python 3.11
- call the two existing ops endpoints over HTTP
- validate the expected payload shape and route inventory
- write the results into `stats.json`, `by-route.json`, and `export.json`
- evaluate pinned thresholds over the exported payload (packet `019k`)
- write `threshold-evaluation.json` into the same artifact directory
- upload those files as a GitHub Actions artifact (runs `if: always()` so breach records are preserved)

## Environment Contract

Required repository variable:

- `PM_IDEMPOTENCY_OPS_BASE_URL`

The workflow uses that value as the base URL for both ops requests. Example:

- `https://control-plane.example.com`

The workflow then scrapes:

- `https://control-plane.example.com/api/v1/ops/pm-idempotency/stats`
- `https://control-plane.example.com/api/v1/ops/pm-idempotency/by-route`

No bearer token or shared secret is currently required by the runtime because both ops endpoints are already live as read-only unauthenticated surfaces. Packet `019j` keeps the call contract at base URL only and does not invent a new auth lane.

## Behavior When Secret Is Missing

If `PM_IDEMPOTENCY_OPS_BASE_URL` is unset or empty, the workflow does not fail the run. It logs that the repo variable is not configured and skips the export step.

This keeps repo forks and non-production environments from generating noisy scheduled failures.

## What The Exporter Records

The workflow uploads one artifact per run:

- `pm-idempotency-metrics-export-<run_id>`

Artifact contents:

- `stats.json` — raw payload from `GET /api/v1/ops/pm-idempotency/stats`
- `by-route.json` — raw payload from `GET /api/v1/ops/pm-idempotency/by-route`
- `export.json` — consolidated export document with fetch timestamp, base URL, endpoint URLs, and both payloads
- `threshold-evaluation.json` — packet `019k` threshold result with `overall`, `limits`, and per-`checks` pass/fail records

The workflow also writes a markdown summary into the Actions run showing:

- fetch timestamp
- backend kind
- total count
- expired count
- oldest expiry
- the seven per-route rows
- the threshold-evaluation table (packet `019k`) with `PASS`/`FAIL` per threshold and a failed-checks block when breached

## Threshold Contract (packet `019k`)

The threshold-evaluation step consumes only the existing packet-019j
export payload. It does NOT re-fetch the ops endpoints, does NOT
introduce a second scrape path, and does NOT invent new runtime
metrics. Thresholds cover the existing exported fields only.

Pinned limits (hard-coded in `.github/workflows/pm-idempotency-metrics-export.yml`):

| Threshold                       | Limit       | Source field                            | Rationale                                                        |
| ------------------------------- | ----------: | --------------------------------------- | ---------------------------------------------------------------- |
| `total_count`                   | `100,000`   | `stats.count`                           | Loose ceiling; breach indicates unbounded growth or sweep stall. |
| `expired_count`                 | `1,000`     | `stats.expired_count`                   | Sweep backlog; with a 15-min sweep cadence this should stay low. |
| `oldest_expiry_age_hours`       | `2`         | `stats.oldest_expires_at`               | Only breaches when oldest row is *in the past* by more than 2h.  |
| `per_route_count[<route>]`      | `20,000`    | `by_route[*].count`                     | Hotspot detector for any one PM POST route.                      |
| `per_route_expired_count[<r>]`  | `500`       | `by_route[*].expired_count`             | Per-route sweep-pressure detector.                               |

The per-route checks run once per row of the `by_route` payload, so
the total check count is `3 + 2 × 7 = 17` checks per run (total,
expired, oldest-expiry + per-route count × 7 + per-route expired × 7).

### Breach behavior

- The threshold step writes `threshold-evaluation.json` into the
  artifact directory BEFORE deciding pass/fail, so the breach record
  is preserved regardless of outcome.
- The step appends a markdown table to the Actions run summary
  showing each threshold, its limit, the observed value, and a
  `PASS`/`FAIL` verdict.
- When any threshold fails, the step calls `sys.exit(1)` after
  emitting `::error::` annotations, which turns the workflow run red
  in the Actions UI.
- The upload-artifact step runs on `if: always()`, so breach runs
  still upload `stats.json`, `by-route.json`, `export.json`, and
  `threshold-evaluation.json` for operators to triage.

### Tuning thresholds

Thresholds are pinned constants inside the workflow step, not repo
variables and not a YAML config file. To change a threshold:

1. Edit the corresponding `MAX_*` constant inside the
   `Evaluate PM idempotency thresholds` step in
   `.github/workflows/pm-idempotency-metrics-export.yml`.
2. Mirror the change in the Threshold Contract table above.
3. Open a PR with both edits in the same diff so review captures
   both the workflow and the runbook.

This keeps every tuning change version-controlled, PR-reviewed, and
visible in `git log`. It also prevents the threshold contract from
drifting silently between the workflow and the runbook.

### What the threshold evaluation deliberately does NOT do

- no external alert integration (no Slack/PagerDuty/webhook sink)
- no second scrape path (reads only the files the export step wrote)
- no new application-runtime endpoint or metric
- no DDL or `pm.idempotency_keys` schema change
- no mutation of the seven PM POST handler contracts
- no broadening of `/api/v1/work/*` (still 15) or `/api/v1/ops/*` (still 2)

If operators later want external alerting or long-retention threshold
history, that must land as a separately authored bounded follow-on.

## What This Export Does Not Do

- no new PM write endpoint
- no new HTTP route
- no application-runtime scheduler or background worker
- no DDL or migration edits
- no shape change to `pm.idempotency_keys`
- no changes to `/api/v1/work/*`
- no changes to `/api/v1/ops/*`
- no writes to `work.wbs_nodes`
- no second PM metrics implementation path

## Manual Run

From GitHub Actions:

1. Open the `PM Idempotency Metrics Export` workflow.
2. Choose `Run workflow`.
3. Start the run.

The workflow will either:

- skip cleanly because the base URL secret is not configured, or
- fetch both existing ops payloads, validate them, and upload the artifact

## Rollback

If the scheduled cadence needs to be disabled quickly:

1. Disable the workflow in GitHub Actions, or
2. Remove the `schedule` trigger from `.github/workflows/pm-idempotency-metrics-export.yml`, or
3. Remove the `PM_IDEMPOTENCY_OPS_BASE_URL` repo variable so runs skip without scraping the runtime

No database rollback is required because packet `019j` adds no DDL and no write path.

## Future Follow-On

If operators later want exported PM idempotency metrics pushed into an external monitoring sink, alert channel, or long-retention storage target, that should land as a separately authored bounded follow-on.

Packet `019j` stops at scheduled scrape plus artifact export and does not assume any broader monitoring platform.
