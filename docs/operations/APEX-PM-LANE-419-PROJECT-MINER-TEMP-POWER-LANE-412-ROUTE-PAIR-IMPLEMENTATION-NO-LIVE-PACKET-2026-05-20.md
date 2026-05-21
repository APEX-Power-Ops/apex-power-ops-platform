# APEX PM Lane 419 - Project Miner Temp Power Lane 412 Route Pair Implementation No-Live Packet

Date: 2026-05-20

Status: Implemented locally in the mutation-seam app with no live Supabase write path admitted

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_412_ROUTE_PAIR_IMPLEMENTATION_NO_LIVE`

## Purpose

PM Lane 419 implements the missing Lane 412 route pair directly in `apps/mutation-seam/app/**` so the downstream hosted-smoke and live-admission roadmap can proceed truthfully.

This lane closes the gap identified by PM Lane 413 Revision A: the future `project-import-contract-support` write route and readback route now exist in the deployable seam app surface, inherit the corrected PM+Operations role contract from Lane 411 Revision C, and remain bounded to no-live behavior.

## Selected Outcome

Selected outcome:

`LANE_412_ROUTE_PAIR_IMPLEMENTATION_READY_NO_LIVE`

Meaning:

1. `POST /api/v1/mutations/project-import-contract-support` now exists in the seam app and returns the Lane 415 frozen write-envelope responses for success, replay, conflict, and the four rollback classes.
2. `GET /api/v1/reads/project-import-contract-support-status` now exists in the seam app and returns the Lane 415 readback envelope baseline for the route family.
3. Both routes use a route-local strict auth wrapper around the established bearer-token dependency pattern so missing auth returns `401` instead of the mutation-seam dev fallback actor.
4. Both routes admit only `pm` and `operations`; the runtime field-role identifier `task_lead` and other non-admitted roles are rejected with `403`.
5. The implementation stays fully no-live: no new production code imports the mutation-seam DB shim or any Supabase-backed store path.

## Implemented Surface

The route pair is implemented through these repo surfaces:

1. `apps/mutation-seam/app/routers/project_import_contract_support.py`
2. `apps/mutation-seam/app/project_import_contract_support_persistence.py`
3. `apps/mutation-seam/app/project_import_contract_support_models.py`
4. `apps/mutation-seam/app/main.py`
5. `apps/mutation-seam/tests/test_project_import_contract_support.py`

## Route Contract

### Write route

Implemented route:

`POST /api/v1/mutations/project-import-contract-support`

Implemented behavior:

1. accepts the Lane 415 frozen request-envelope shape plus optional `dry_run` and `force_failure` inputs
2. validates `action_type`, `mutation_class`, `source`, envelope idempotency key, payload idempotency key, and deterministic entity id before any persistence behavior runs
3. computes the business-payload digest using the same canonical ordering contract introduced by Lane 414 and Lane 415
4. returns the exact frozen success, replay, conflict, and rollback envelopes from `apps/mutation-seam/scripts/lane_415_envelope_export/`
5. uses module-local in-memory state only for same-process replay and duplicate-business-payload conflict behavior
6. gates `dry_run` and `force_failure` behind `LANE_412_DRY_RUN_ENABLED`; when the flag is absent those inputs are ignored

### Readback route

Implemented route:

`GET /api/v1/reads/project-import-contract-support-status`

Implemented behavior:

1. accepts the query shape required by the Lane 412 route family: `project_id`, `candidate_id`, and `source_fingerprint`
2. returns the frozen Lane 415 `missing` readback envelope when no local no-live write state exists
3. supports same-process no-live readback progression for the route family without opening any database path

## Auth And Role Boundary

This lane preserves the established auth dependency but corrects the one mismatch uncovered in Phase 0 discovery.

1. The new routes use a route-local strict wrapper around `app.auth.jwt.get_current_actor(...)`.
2. Missing auth is rejected with `401` instead of inheriting the mutation-seam dev fallback actor.
3. Invalid bearer format still rejects with `401` through the underlying dependency.
4. Only `pm` and `operations` are admitted.
5. The runtime field-role identifier `task_lead` is rejected with `403`.

## No-Live Boundary

This implementation remains no-live by construction.

1. New production code does not import `app.db.memory_store` or the Supabase-backed store shim.
2. All write-path behavior is fixture-backed and module-local only.
3. No schema migration, no live route deployment, and no live row insertion is admitted here.
4. Lane 420 remains the next hosted-smoke lane.

## Validation

Focused executable validation passed:

```powershell
.\.venv\Scripts\python.exe -m pytest apps/mutation-seam/tests/test_project_import_contract_support.py -q
```

Result:

`15 passed`

Covered proof:

1. success envelope parity
2. replay envelope parity
3. duplicate-business-payload conflict envelope parity
4. all four rollback envelope parities under the env gate
5. ignored `dry_run` and `force_failure` when the env gate is absent
6. PM and Operations admission
7. `task_lead` and `field_tech` rejection with `403`
8. missing auth rejection with `401`
9. strict-auth wrapper behavior for missing auth, invalid auth, dev-fallback rejection, and valid actor pass-through
10. baseline readback parity with the frozen `missing` export

## Boundary

Still blocked:

1. hosted deployment proof
2. live route exercise against hosted surfaces
3. live Supabase writes
4. schema migration execution
5. apparatus status mutation
6. revenue-event writes
7. billing, payroll, invoice, accounting, customer-billing, and external-finance output
8. source workbook writeback and workbook macros
9. autonomous AI business-state mutation

## Next Truth

The next truthful follow-on is PM Lane 420 Hosted Dual-Route Smoke Readiness, because the route family now exists locally in the deployable seam surface and the remaining unanswered question is hosted no-write parity rather than missing implementation.
