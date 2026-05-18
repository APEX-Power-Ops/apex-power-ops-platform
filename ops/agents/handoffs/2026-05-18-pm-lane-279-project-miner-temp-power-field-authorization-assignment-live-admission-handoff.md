# PM Lane 279 - Project Miner Temp Power Field Authorization Assignment Live Admission Handoff

## Summary

PM Lane 279 admits the first post-import field authorization and assignment write for the Project Miner Temp Power pilot.

Jason's 2026-05-18 standing PM blocker authority is the stakeholder authority for this bounded packet. The lane uses the existing hosted assignment mutation seam and does not open schedule/status, durable field record, production tracking, customer, or finance writes.

## Preconditions

- PM Lane 277 approval row exists and reads back as `approved_for_import_packet`.
- PM Lane 278 import reads back as `classification=imported`, `current_candidate_match=true`, and `counts_match=true`.
- Hosted imported counts are 1 project, 7 workpackages, 15 tasks, 184 apparatus, 199 source trace rows, and 1 warning review row.
- Hosted assignment readback was 0 before PM Lane 279 writes.
- Hosted crew seed has `tech-001` Alex Rivera, `tech-002` Sam Chen, and `tech-003` Jordan Bell.

## Assignment Contract

The admitted write creates one assignment per imported Temp Power apparatus through:

`POST https://operations.apexpowerops.com/api/v1/mutations/assignments`

The write uses:

- lead actor role,
- online source,
- mutation class `B`,
- action type `assign`,
- null `entity_id` for route-owned assignment creation,
- deterministic idempotency key `pm-lane-279-field-assignment-v2:<apparatus_id>`,
- payload field `assignment_external_id` for deterministic external traceability,
- field authorization record `pm-lane-279-field-auth-temp-power-2026-05-18`,
- source fingerprint `e111fdbe934bf9de07ed24c1`.

The assignment policy is `deterministic_lowest_planned_hours_then_assignment_count_then_tech_id`.

Expected distribution:

| Tech | Assignment count | Planned hours |
| --- | ---: | ---: |
| `tech-001` | 66 | 194.5 |
| `tech-002` | 59 | 217.5 |
| `tech-003` | 59 | 194.75 |

## Readback Fix

Hosted assignment reads returned the correct assignment rows, but the PM workfront projection still counted rows as unassigned because readiness only inspected `apparatus.assigned_to`. This lane patches `apps/mutation-seam/app/pm_workfront_read_model.py` so readiness uses the resolved owner from either the apparatus row or the assignment row.

Focused regression coverage was added in `apps/mutation-seam/tests/test_pm_workfront_read_model.py`.

## Boundaries

This lane admits only assignment rows and assignment-readback support.

Still blocked:

- task, workpackage, or apparatus status mutation,
- schedule/date mutation,
- durable field record write,
- production tracking write,
- customer report or customer commitment,
- billing, payroll, invoice, accounting, or external finance output,
- direct SQL,
- schema migration,
- source workbook/PDF writeback,
- workbook macros,
- new service, DNS, auth, ingress, or secret change.

## Validation

Run before closeout:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_pm_workfront_read_model.py -q
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_project_import_persistence.py -q
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com
git diff --check
```

## Next Blocker

After PM Lane 279 closeout, the next blocker is schedule/status mutation admission. Durable field records, production tracking, customer reporting, and finance remain separately packeted.
