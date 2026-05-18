# APEX PM Lane 305 - Project Miner Temp Power Actuals Capture Review Local First Write Proof Packet

Date: 2026-05-18

Status: Local executable first-write proof for the admitted actuals-capture review route only

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_LOCAL_FIRST_WRITE_PROOF_PACKET`

## Purpose

PM Lane 305 converts the Lane 304 local runtime implementation into one executable local proof packet for the admitted actuals-capture review route only.

This lane uses a local in-memory mutation-seam proof runner to send one actual request through the admitted route, replay the same payload once, capture paired readback, and prove unchanged downstream counts and blocked downstream boundaries.

This lane does not promote hosted runtime, does not open the customer-preview route, and does not widen customer delivery, finance, or source-writeback authority.

## Selected Outcome

Selected outcome:

`ACTUALS_CAPTURE_REVIEW_LOCAL_FIRST_WRITE_PROOF_RECORDED`

Meaning:

1. the admitted actuals route now has concrete local first-write proof, not only unit-test proof
2. same-payload replay proof is captured with stable `mutation_id` and `audit_event_id`
3. paired readback proof is captured with current project/candidate/source match
4. downstream counts and blocked-boundary posture remain explicit

## Proof Runner

The local proof runner for this lane is:

1. `apps/mutation-seam/scripts/run_temp_power_actuals_capture_review_local_proof.py`

The runner performs all of the following locally:

1. resets the in-memory seam store
2. seeds one Temp Power workpackage, task, and apparatus context
3. sends one request to `POST /api/v1/mutations/temp-power-actuals-capture-reviews`
4. replays the same payload once
5. reads `GET /api/v1/reads/temp-power-actuals-capture-review-status`
6. proves downstream counts are unchanged before and after
7. prints a secret-free JSON proof summary

## Recorded Local First-Write Evidence

The recorded local proof returned:

1. accepted write status: `accepted`
2. accepted entity id: `temp-power-actuals-capture-review-f042997ced32e02f7f81f367`
3. accepted mutation id: `mut-6c51d8f7-c99b-4b8b-b61c-3412ca473fc5`
4. accepted audit event id: `audit-9014e420-8c64-40df-ad27-e796088f3082`
5. replay status: `idempotent_hit`
6. replay mutation id matches first write: `true`
7. replay audit event id matches first write: `true`
8. readback status: `actuals_capture_review_recorded_current_match`
9. readback record count: `1`
10. readback latest review id matches accepted entity id: `true`
11. current candidate match: `true`
12. current source fingerprint match: `true`

## Unchanged Downstream Proof

The local proof showed unchanged downstream counts:

1. `projects: 2 -> 2`
2. `workpackages: 5 -> 5`
3. `tasks: 16 -> 16`
4. `apparatus: 185 -> 185`
5. `assignments: 56 -> 56`
6. `hours: 32 -> 32`
7. `issues: 4 -> 4`

## Blocked-Boundary Proof

The local proof also preserved all of the following:

1. `customer_delivery_authority=not_admitted`
2. `finance_authority=not_admitted`
3. `source_writeback_authority=not_admitted`
4. `durable_delivery_event=false`
5. canonical review record count is `1`
6. audit log count is `1`

## Explicitly Still Blocked

This lane still does not admit:

1. hosted mutation-seam promotion or hosted row proof
2. `POST /api/v1/mutations/temp-power-customer-preview-reviews`
3. any customer preview persistence or delivery event
4. any finance/export/accounting behavior
5. any source workbook writeback or macro behavior

## Validation Checks

Required validation for this lane:

1. run the local proof runner and capture zero-error JSON proof output
2. packet JSON parse
3. decision label and selected outcome search across touched Lane 305 files
4. accepted-write, replay, readback, unchanged-count, and blocked-boundary marker search across touched Lane 305 files
5. diagnostics check on the new proof runner if touched
6. scoped `git diff --check`

## Next Safe Step

Separate later admission only:

1. hosted actuals-route proof packet for this same route, if separately admitted
2. customer-preview first-write packet, if separately admitted