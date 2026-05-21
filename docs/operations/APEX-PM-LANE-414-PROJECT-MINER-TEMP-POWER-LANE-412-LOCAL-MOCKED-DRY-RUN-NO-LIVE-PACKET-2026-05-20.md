# APEX PM Lane 414 - Project Miner Temp Power Lane 412 Local Mocked Dry-Run No-Live Packet

Date: 2026-05-20

Status: Local no-live mocked dry-run for the future Lane 412 import-contract-support write route and paired readback route

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_412_LOCAL_MOCKED_DRY_RUN_NO_LIVE`

## Purpose

PM Lane 414 is the first downstream implementation step named by Lane 413.

This lane creates a self-contained local mock for both future Lane 412 routes using only in-memory state and concrete JSON fixtures. It proves that the request envelope, idempotency digest, success envelope, replay envelope, deliberate conflict envelope, rollback envelopes, and readback classifications are representable without touching Supabase, any hosted surface, or any external state.

This lane is additive only. It does not modify any Lane 411, Lane 412 Revision A or B, or Lane 413 surface.

## Selected Outcome

Selected outcome:

`IMPORT_CONTRACT_SUPPORT_LOCAL_MOCKED_DRY_RUN_READY_NO_LIVE`

Meaning:

1. The future write route and paired readback route can now be exercised locally through a self-contained mock.
2. The mock computes the Lane 413 sha256 business-payload digest and uses an in-memory cache only.
3. All 12 concrete JSON payload fixtures exist and can be returned by trigger condition.
4. The no-Supabase, no-network, no-external-state boundary is locally proven.

## Phase 0 Classification Naming Finding

Phase 0 result: a project-wide mutation-envelope convention already exists.

The prior live-admission route families reviewed for naming precedent show the following stable pattern:

1. top-level mutation envelope status uses compact values such as `accepted`, `idempotent_hit`, `conflict`, and `rejected`
2. route-specific write-storage or readback meaning is expressed separately through domain-specific state names such as `accepted_for_review_storage`, `accepted_for_customer_delivery_event_storage`, `actuals_capture_review_recorded_current_match`, `customer_preview_delivery_blocked`, `customer_delivery_event_recorded_stale_source`, and similar route-scoped statuses
3. replay naming is stable across families: same-payload replay returns `idempotent_hit`
4. readback naming is route-specific and state-specific, not one generic global taxonomy

Evidence for that convention came from:

1. PM Lane 277 through PM Lane 284 hosted/live evidence using `status=accepted` and `status=idempotent_hit`
2. PM Lane 304 and PM Lane 305 actuals-capture local proof surfaces using `accepted` plus route-specific readback status names
3. PM Lane 321 customer-delivery/proof design naming `accepted_for_review_storage`
4. PM Lane 339 customer-facing delivery execution design naming `accepted_for_customer_delivery_event_storage`
5. the shared mutation response envelope in `apps/mutation-seam/app/envelope/response.py`, which defines `status` as `accepted | rejected | conflict | idempotent_hit`

Lane 414 inherits that convention this way:

1. top-level mock mutation responses use repo-standard `status`
2. Lane 413's planned naming stays present as route-specific top-level `classification` and `mutation_status` metadata for this Lane 412 family
3. readback fixtures use top-level `status` values matching the Lane 412 route-specific states `missing`, `ready`, `stale_candidate`, `counts_mismatch`, and `unavailable`

This keeps Lane 414 aligned with the codebase envelope convention without silently rewriting Lane 413. If a later packet decides the Lane 413 wording itself should be renamed for full cross-packet symmetry, that belongs in a separate Lane 413 Revision A packet rather than an implicit change here.

## Inherited Lane 413 Baseline

Lane 414 inherits the following design facts unchanged:

1. write route: `POST /api/v1/mutations/project-import-contract-support`
2. readback route: `GET /api/v1/reads/project-import-contract-support-status`
3. write route and readback route deploy together as one feature unit later under Lane 413 Option B
4. success envelope still carries the Lane 413 planned fields `http_status`, `classification`, `mutation_status`, `mutation_id`, `audit_event_id`, `project_contract_snapshot_id`, `scope_labor_detail_row_count`, `apparatus_financial_row_count`, `idempotent_hit`, and `current_candidate_match`
5. four named rollback classes remain `transaction_rolled_back_scope_detail_conflict`, `transaction_rolled_back_apparatus_financial_validation_failed`, `transaction_rolled_back_audit_write_unavailable`, and `transaction_rolled_back_idempotency_write_unavailable`
6. rollback responses still return `mutation_status = rolled_back` and `partial_commit = false`
7. same business payload under a different `mutation_id` remains a deliberate duplicate-business-payload conflict
8. the idempotency cache key remains the sha256 digest of `project_id | candidate_id | source_fingerprint | snapshot_kind | contract_value | total_quoted_hours | ordered scope_labor_details rows | ordered apparatus_financials rows`
9. readback classifications remain `missing`, `ready`, `stale_candidate`, `counts_mismatch`, and `unavailable`

## Mock Implementation

Implementation path:

`apps/mutation-seam/scripts/lane_414_local_mock/run_lane_414_local_mock.py`

Entry point:

```text
python apps/mutation-seam/scripts/lane_414_local_mock/run_lane_414_local_mock.py
```

The local mock does all of the following:

1. builds a future production request envelope with `idempotency_key`, `mutation_class`, `action_type`, `entity_id`, `payload`, `reason`, `source`, and `client_timestamp`
2. computes the Lane 413 sha256 business-payload digest from ordered `scope_labor_details` and ordered `apparatus_financials`
3. stores committed payloads only in one in-process Python dictionary keyed by that digest
4. returns the success fixture on first cache miss
5. returns the idempotent-hit fixture on same-payload replay with the same `mutation_id`
6. returns the conflict fixture on the same business payload under a different `mutation_id`
7. returns one rollback fixture for each `force_failure` mode
8. returns readback fixtures for the five lane-specific readback states
9. writes `local_trace_no_supabase_touch.txt` beside the script during execution

The mock is self-contained and intentionally does not import any mutation-seam app module, Supabase client, HTTP client, or hosted configuration surface.

## Concrete Fixture Payloads And Trigger Conditions

The concrete JSON fixture directory is:

`apps/mutation-seam/scripts/lane_414_local_mock/`

Write-route fixtures:

1. `success_first_write.json`
   trigger: first cache miss for a valid request envelope
2. `success_idempotent_hit.json`
   trigger: same business payload replayed with the same `mutation_id`
3. `conflict_duplicate_business_payload.json`
   trigger: same business payload replayed with a different `mutation_id`
4. `rollback_scope_detail_conflict.json`
   trigger: `force_failure = scope_detail_conflict`
5. `rollback_apparatus_financial_validation_failed.json`
   trigger: `force_failure = apparatus_financial_validation_failed`
6. `rollback_audit_write_unavailable.json`
   trigger: `force_failure = audit_write_unavailable`
7. `rollback_idempotency_write_unavailable.json`
   trigger: `force_failure = idempotency_write_unavailable`

Readback fixtures:

8. `readback_missing.json`
   trigger: no committed payload or explicit readback request for `missing`
9. `readback_ready.json`
   trigger: committed payload present and counts reconcile
10. `readback_stale_candidate.json`
    trigger: explicit readback request for `stale_candidate`
11. `readback_counts_mismatch.json`
    trigger: explicit readback request for `counts_mismatch`
12. `readback_unavailable.json`
    trigger: explicit readback request for `unavailable`

## Request Envelope And Idempotency

The mocked request envelope follows the current mutation-seam request shape:

1. `idempotency_key`
2. `mutation_class = C`
3. `action_type = persist_project_import_contract_support`
4. deterministic `entity_id`
5. `payload`
6. `reason`
7. `source = online`
8. ISO-8601 `client_timestamp`

The payload includes:

1. `mutation_id`
2. `project_id`
3. `candidate_id`
4. `source_fingerprint`
5. `snapshot_kind`
6. `contract_value`
7. `total_quoted_hours`
8. ordered `scope_labor_details`
9. ordered `apparatus_financials`
10. payload-local `idempotency_key`

The mock validates that:

1. `request.idempotency_key` matches the computed business-payload sha256 digest
2. `payload.idempotency_key` matches the same digest
3. identical business payload plus identical `mutation_id` becomes `idempotent_hit`
4. identical business payload plus different `mutation_id` becomes `duplicate_business_payload_conflict`

## Local Trace And No-Supabase Proof

The local trace file path is:

`apps/mutation-seam/scripts/lane_414_local_mock/local_trace_no_supabase_touch.txt`

The trace records:

1. mutation route and readback route identity
2. computed business-payload digest
3. first-write, replay, conflict, rollback, and readback result summary
4. local source-file scan results for forbidden tokens like `supabase`, `@supabase`, `supabase-py`, `http://`, and `https://`
5. explicit statements that network calls observed are false, external state used is false, and storage is one in-memory Python dictionary

Verification method:

1. inspect the local mock directory for Python source only
2. scan those Python files for Supabase tokens or explicit network URLs
3. note that the mock code path contains no HTTP client import and no hosted SDK import
4. run the self-contained script and confirm it produces the trace from in-process state only

No packet claim is made that tcpdump, strace, or browser network tools were needed. The mock has no network code path to inspect.

## Single-Feature-Unit Deployment Inheritance

This lane keeps the Lane 413 Option B decision explicit.

Even though the work here is local-only, the mock covers both future routes together because:

1. the write route and readback route are one future feature unit
2. the readback is the canonical verification surface for the write route
3. Lane 415 will export one exact envelope lineage from this single mock family instead of splitting the routes into separate dry-run branches

## What Lane 415 Inherits

Lane 415 inherits all of the following from this packet:

1. the Phase 0 naming finding and the repo-standard top-level mutation `status` convention
2. the exact local request envelope shape currently built by the script
3. the ordered `scope_labor_details` and `apparatus_financials` digest inputs
4. the concrete success, replay, conflict, rollback, and readback fixtures
5. the current deterministic entity-id pattern used by the local mock
6. the trace-backed claim that no Supabase touch is required for the dry-run slice

Lane 415's job is export, not redesign.

## Boundaries

This lane does not admit:

1. live route implementation
2. live schema creation or migration
3. live import-support writes
4. live revenue-event writes
5. apparatus status mutation
6. public schema writes
7. billing, invoice, payroll, accounting, customer-billing, or external-finance output
8. source workbook writeback or macros
9. change-order admission
10. live operational hours tracking implementation
11. autonomous AI business-state mutation
12. any Supabase touch from the mock code path
13. hosted deployment of the mock
14. promotion to Lane 415 in this packet

## Validation Checks

Required validation for this lane:

1. Phase 0 naming check is documented with specific repo precedent
2. all 12 canned payload files exist as concrete JSON
3. the local mock accepts the future production request envelope shape
4. the sha256 idempotency digest is implemented exactly once from ordered business-payload fields
5. same-payload replay returns `status = idempotent_hit`
6. same business payload with different `mutation_id` returns `status = conflict` and `classification = duplicate_business_payload_conflict`
7. each of the four force-failure modes returns its matching rollback fixture
8. the readback mock returns all five classification fixtures
9. `local_trace_no_supabase_touch.txt` proves no Supabase import, no network call, and no external state
10. no Lane 411, Lane 412 Revision A or B, or Lane 413 surface is modified
11. the legacy underscore revenue token does not appear anywhere in Lane 414 surfaces
12. `git diff --check` passes for the new Lane 414 files and `PROJECT_STATUS.md`

## Next Safe Packet

Next safe packet:

`PM Lane 415 - Project Miner Temp Power Lane 412 Dry-Run Envelope Export Packet`