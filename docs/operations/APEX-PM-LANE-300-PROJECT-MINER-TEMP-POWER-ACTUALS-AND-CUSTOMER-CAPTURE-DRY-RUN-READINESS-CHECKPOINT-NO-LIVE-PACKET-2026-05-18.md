# APEX PM Lane 300 - Project Miner Temp Power Actuals And Customer Capture Dry Run Readiness Checkpoint No-Live Packet

Date: 2026-05-18

Status: Local no-live dry-run readiness checkpoint for actuals capture review and customer preview review

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_DRY_RUN_READINESS_CHECKPOINT_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 300 converts the Lane 298 local mocked-request preview and Lane 299 dry-run envelope export into a compact readiness checkpoint.

This lane still does not admit any runtime route, browser submit control, or request send. It defines the exact readiness categories, the allowed readiness states, and the minimum conditions needed before the mock envelope is reused as later packet context.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`ACTUALS_CUSTOMER_CAPTURE_DRY_RUN_READINESS_CHECKPOINT_READY_NO_LIVE`

Meaning:

1. The dry-run slice now has a compact readiness checkpoint.
2. Each readiness item must be classified as `ready`, `needs_review`, or `blocked`.
3. Live-write authority remains explicitly blocked unless separately admitted later.
4. The checkpoint may be reviewed locally before the exported envelope is reused as later packet context.

## Readiness Items

The checkpoint must classify all of the following items:

1. `project_source_identity_context`
2. `actuals_evidence_review`
3. `customer_preview_review`
4. `route_and_mock_envelope_continuity`
5. `readback_and_execution_gate_context`
6. `live_write_authority`

## Allowed States

Only the following readiness states are allowed:

1. `ready`
2. `needs_review`
3. `blocked`

## State Rules

The checkpoint must apply these rules:

1. `ready` means the required local evidence is present and consistent with the current mock envelope.
2. `needs_review` means no live write is needed, but PM confirmation or local evidence cleanup is still required.
3. `blocked` means the item cannot be treated as reusable packet context.
4. `live_write_authority` must stay `blocked` unless the exact future admission phrase is current instruction.

## Minimum Classification Criteria

The checkpoint must classify items using at least these criteria:

1. `project_source_identity_context` is `ready` only when `project_id`, `candidate_id`, and `source_fingerprint` match the current mock envelope and export snapshot.
2. `actuals_evidence_review` is `ready` only when actuals/labor preview fields, evidence bundle fields, and correction linkage fields are present or explicitly not needed.
3. `customer_preview_review` is `ready` only when recipient review, delivery-channel review, preview artifact references, and delivery-block posture are present.
4. `route_and_mock_envelope_continuity` is `ready` only when the chosen route, action type, and idempotency key are identical across the mock preview and exported envelope.
5. `readback_and_execution_gate_context` is `ready` only when the designed readback posture and the exact future admission phrase are visible as current packet context.
6. `live_write_authority` remains `blocked` when the exact future admission phrase is absent from current instruction.

## Checkpoint Summary Rules

The readiness checkpoint must also provide:

1. per-item status
2. per-item reason
3. checkpoint timestamp
4. checkpoint actor
5. unchanged no-live boundary summary

## Required Local Checkpoint Proof

Any local readiness proof or closeout must be able to show:

1. all six readiness items
2. allowed states only
3. explicit reason for each non-ready item
4. `live_write_authority=blocked` unless separately admitted later
5. unchanged downstream delivery/finance/writeback posture

## Explicitly Not Admitted By This Lane

This lane does not admit:

1. browser controls that submit a request
2. any runtime route call or network request
3. any record creation or replay proof
4. customer delivery or delivery-proof recording
5. any finance/export/accounting/source-writeback behavior

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 300 files.
3. Selected outcome is present.
4. Readiness items and allowed states are present.
5. State rules and minimum classification criteria are present.
6. `live_write_authority` and `blocked` posture are explicit.
7. Blocked-output boundaries remain explicit.
8. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 301 - Project Miner Temp Power Actuals And Customer Capture Dry Run Readiness Export No-Live Packet`