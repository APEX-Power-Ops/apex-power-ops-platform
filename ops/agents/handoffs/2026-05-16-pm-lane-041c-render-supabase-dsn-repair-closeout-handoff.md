# PM Lane 041C Render Supabase DSN Repair Closeout Handoff

Date: 2026-05-16

## Scope

Bounded hosted remediation on the existing Render service `apex-platform-mutation-seam` for the remaining Supabase session-pooler credential failure affecting DB-backed approval and schedule reads.

No repo code, SQL, schema, auth, ingress, service-topology, approval-persistence, import-mutation, assignment, schedule, or AI business-state changes were made.

## Source Floor

- Git branch: `clean-main`
- Render service: `apex-platform-mutation-seam`
- Render service id: `srv-d7tg1657vvec738hstg0`
- Hosted endpoint under proof: `https://mutation-seam.apexpowerops.com`

## Hosted Actions Completed

1. Reset the Supabase database password from the authenticated dashboard using the built-in generator.
2. Stored the rotated credential in the non-git secret boundary as Olares Vault item `8276c6c0-aa9c-4adc-9624-074b0469521b`.
3. Updated the existing Render `SEAM_DATABASE_URL` value to the matching session-pooler DSN built from the rotated password.
4. Saved the Render env update and allowed the existing service to redeploy.
5. Waited for the new deploy to reach `live` at approximately `2:52 PM` local time.
6. Reran the repo-owned hosted validation commands against the live deployment.

## Secret Storage Instructions

Canonical storage:

1. Keep the current mutation-seam Supabase runtime credential in Olares Vault item `8276c6c0-aa9c-4adc-9624-074b0469521b`.
2. Treat Vault as the durable non-git source of truth for future rotations.

Runtime storage:

1. Keep the live application copy only in the existing Render environment variable `SEAM_DATABASE_URL`.
2. Do not duplicate the password or DSN into repo files, handoffs, transcripts, or repo-local `.env` files.

Future rotation procedure:

1. Reset the password in Supabase.
2. Update the same Olares Vault item with the fresh value.
3. Update the existing Render `SEAM_DATABASE_URL` value.
4. Wait for the deploy to become live.
5. Rerun the hosted mutation-seam and PM-intake smokes.

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

Mutation seam hosted smoke:

- `health` `200`
- `root` `200`
- `reads_approval_queue` `200`
- `schedule_projects` `200`
- `schedule_drivers` `200`
- `schedule_tracer` `200`
- `schedule_variance` `200`
- `openapi` `200`
- `project_import_candidate` `200`
- `project_import_admission_plan` `200`
- `project_import_approval_contract` `200`
- `project_import_approval_storage_plan` `200`
- Overall result: `RESULT PASS`

PM intake hosted smoke:

- `PM_INTAKE_HOSTED_SUMMARY failed=0`

## Final Verdict

PM Lane 041C is closed.

The remaining hosted Render/Supabase DSN blocker was caused by stale or invalid session-pooler password material. After password rotation and Render env update, the deployed mutation-seam service now serves both PM intake reads and the broader DB-backed approval and schedule reads successfully.

## Guardrails Preserved

- No repo code changes
- No SQL or schema writes
- No secret value publication
- No new service creation
- No DNS/auth/ingress changes
- No approval persistence or import mutation admission
- No assignment, schedule, or status mutation
- No AI business-state mutation