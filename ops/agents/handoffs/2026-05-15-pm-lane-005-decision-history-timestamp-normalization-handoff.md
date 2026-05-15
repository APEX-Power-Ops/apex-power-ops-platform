# PM Lane 005 Handoff - Decision-History Timestamp Normalization

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-005`
Scope: PM runtime backend read hardening for decision-history parity

## Summary

This tranche hardens the existing decision-history read endpoint so PM disposition history has a consistent timestamp field across memory-backed audit events and persisted audit rows.

The route remains:

```text
GET /api/v1/reads/decision-history
```

No new endpoint, mutation endpoint, service, SQL, schema, auth, ingress, frontend UI, or autonomous AI mutation authority was added.

## Backend Changes

`apps/mutation-seam/app/routers/reads.py` now centralizes the PM decision-action set and normalizes each returned history row with:

```text
timestamp = timestamp || server_timestamp || client_timestamp || ""
```

The same fallback is used for newest-first sorting. This preserves Postgres-shaped rows that already expose `timestamp` while making memory-shaped audit rows from `record_audit_event` safe for PM history consumers.

## Test Changes

`apps/mutation-seam/tests/test_pipeline_integration.py` now proves:

1. a PM `return_to_lead` history row exposes the memory audit `server_timestamp` through the normalized `timestamp` field,
2. mixed audit rows with only `server_timestamp` or only `client_timestamp` sort newest-first through `/api/v1/reads/decision-history`.

## Delegation And Orchestration Notes

This was a coordinator-executed hardening packet based on the PM Lane 004 backend scout finding from `019e2c3d-c2a9-75f0-80d4-f09ff919d91d`.

The packet intentionally avoids opening a PM timeline UI or Supabase write test. It prepares the read contract for that later work while keeping validation memory-backed and non-destructive.

## Files Changed

Backend:

1. `apps/mutation-seam/app/routers/reads.py`
2. `apps/mutation-seam/tests/test_pipeline_integration.py`

Packet and status:

1. `PROJECT_STATUS.md`
2. `ops/agents/packets/draft/2026-05-15-pm-lane-005-decision-history-timestamp-normalization.json`
3. `ops/agents/handoffs/2026-05-15-pm-lane-005-decision-history-timestamp-normalization-handoff.md`

## Validation

Focused backend validation:

```powershell
$env:SEAM_STORE_BACKEND='memory'; & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_issue_disposition.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pipeline_integration.py" -q
```

Result: `15 passed` with existing Pydantic v2 deprecation warnings.

## Guardrails Preserved

1. No SQL or schema migration.
2. No new service admission.
3. No auth or ingress widening.
4. No assignment mutation.
5. No schedule mutation.
6. No Operations Visibility reopening.
7. No autonomous AI business-state mutation.
8. No new mutation endpoint.
9. No new read endpoint.
10. No frontend UI change.

## Next Bounded Move

The next PM product slice can now safely choose between:

1. a read-only PM disposition-history drawer in `/pm-review/workfront`, backed by the normalized decision-history shape, or
2. a non-mutating Supabase parity inspection packet for `seam.audit_log` and issue JSON overflow fields before any live-data PM history claim.
