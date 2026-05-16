# PM Lane 041C Render Supabase DSN Repair Blocker Handoff

Date: 2026-05-16

## Scope

Bounded hosted remediation on the existing Render service `apex-platform-mutation-seam` for the remaining PM Lane 041C Supabase DSN issue affecting DB-backed approval and schedule reads.

No repo code was changed. No SQL, schema, service creation, auth widening, ingress change, approval persistence, import mutation, assignment mutation, schedule mutation, or AI business-state mutation was performed.

## Source Floor

- Git branch: `clean-main`
- Render deploy commit observed in events: `50b8012`
- Service: `srv-d7tg1657vvec738hstg0`
- Public host under validation: `https://mutation-seam.apexpowerops.com`

## Hosted Actions Performed

1. Confirmed the Render environment page still owns `SEAM_DATABASE_URL` and that env updates trigger a new deploy.
2. Confirmed Supabase exposes both a session-pooler connection shape and a direct connection shape for the same project.
3. Switched Render `SEAM_DATABASE_URL` to the direct Supabase host/user form and triggered a deploy.
4. Waited for the direct-host deploy to become live, then reran hosted validation.
5. Observed the direct-host deploy fail on TCP connectivity, not on application boot.
6. Reverted Render `SEAM_DATABASE_URL` back to the session-pooler form and triggered a second deploy.
7. Waited for the pooler rollback deploy to become live, then reran hosted validation.
8. Confirmed PM intake hosted parity stayed green throughout the entire slice.

Secret values were intentionally not recorded here. Browser tooling exposed plaintext DSN material during interactive field selection, so no DSN must be copied from tool output into repo-visible artifacts.

## Render Deploy Evidence

- Direct-host env update acknowledged by Render with `Updated environment variables for this service. Triggering a deploy.`
- Direct-host deploy reached `live` as deploy `dep-d84e6a37uimc739jhkm0`.
- Pooler rollback env update acknowledged by Render with the same env-update alert.
- Pooler rollback deploy reached `live` as deploy `dep-d84e7pog4nts73f502og`.

## Validation Commands

Mutation seam hosted smoke:

```powershell
& ".venv\Scripts\python.exe" "apps/mutation-seam\scripts\smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

PM intake hosted smoke:

```powershell
corepack pnpm --dir . --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

## Validation Results

Mutation seam hosted smoke after the direct-host deploy was live:

- `health` `200`
- `root` `200`
- `reads_approval_queue` `500`
- `schedule_projects` `500`
- `schedule_drivers` `500`
- `schedule_tracer` `500`
- `schedule_variance` `500`
- `openapi` `200`
- PM intake reads remained `200`
- Overall result: `FAIL`

PM intake hosted smoke after the direct-host deploy was live:

- `PM_INTAKE_HOSTED_SUMMARY failed=0`

Mutation seam hosted smoke after the pooler rollback deploy was live:

- `health` `200`
- `root` `200`
- `reads_approval_queue` `500`
- `schedule_projects` `500`
- `schedule_drivers` `500`
- `schedule_tracer` `500`
- `schedule_variance` `500`
- `openapi` `200`
- PM intake reads remained `200`
- Overall result: `FAIL`

PM intake hosted smoke after the pooler rollback deploy was live:

- `PM_INTAKE_HOSTED_SUMMARY failed=0`

## Log Classification

Direct-host deploy log classification:

- `psycopg2.OperationalError: connection to server at "db.fxoyniqnrlkxfligbxmg.supabase.co" (...), port 5432 failed: Connection refused`
- Interpretation: the direct Supabase host is not reachable from this Render service on the tested path, so direct-host bypass is not a viable recovery path here.

Pooler rollback deploy log classification:

- `psycopg2.OperationalError: connection to server at "aws-0-us-west-2.pooler.supabase.com" (...), port 5432 failed: FATAL:  password authentication failed for user "postgres"`
- Interpretation: the service is back on the pooler path, but authentication is still being rejected for the DB-backed schedule and approval reads.

## Current State

- Render env is left on the session-pooler form, not the direct-host form.
- `https://operations.apexpowerops.com` PM intake remains green.
- `https://mutation-seam.apexpowerops.com` PM intake read paths remain green.
- Approval queue and schedule DB-backed reads remain red with `500`.
- The direct-host bypass path is currently classified as unusable from this Render service because it returns `Connection refused`.
- The remaining blocker is on pooler authentication or credential correctness, not on route registration or PM intake parity.

## Blocker Verdict

PM Lane 041C is not closed.

The hosted blocker is now narrowed to one of these secret-boundary causes:

1. The current session-pooler password material in Render is stale or incorrect.
2. The copied session-pooler connection string from Supabase was not the exact runtime connection string Render needs.
3. Supabase pooler authentication for this role currently requires a password reset or secret rotation before the service can reconnect.

## Recommended Next Bounded Move

1. From an authenticated secret-safe surface, re-open Supabase connection settings and verify the exact session-pooler connection string intended for external clients.
2. If confidence in the current password is low, rotate or reset the database password in Supabase, then repaste the newly issued session-pooler DSN into the existing Render `SEAM_DATABASE_URL` only.
3. Trigger one more Render env-update deploy on the existing service.
4. Rerun the two hosted smoke commands above.
5. If the pooler path still returns password authentication failure after a confirmed fresh credential rotation, classify the blocker as Supabase-side auth/pooler escalation rather than a Render env-shape issue.

## Guardrails Preserved

- No repo code changes
- No SQL or schema writes
- No secret value publication
- No new service creation
- No DNS/auth/ingress changes
- No approval persistence or import mutation admission
- No assignment, schedule, or status mutation
- No AI business-state mutation
