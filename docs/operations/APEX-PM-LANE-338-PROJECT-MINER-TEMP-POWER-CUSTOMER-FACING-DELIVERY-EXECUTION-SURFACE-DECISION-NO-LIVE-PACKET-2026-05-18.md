# APEX PM Lane 338 - Project Miner Temp Power Customer-Facing Delivery Execution Surface Decision No-Live Packet

Date: 2026-05-18

Status: Local no-live architecture decision for customer-facing delivery execution

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_FACING_DELIVERY_EXECUTION_SURFACE_DECISION_NO_LIVE`

## Purpose

PM Lane 338 resolves the architecture choice left open by PM Lane 337.

The repo now has canonical hosted preview-review and delivery/proof review rows, but it still needs one bounded decision about where actual customer-facing delivery execution belongs before any live-admission phrase can be truthful.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, customer-facing report delivery, email send, portal upload, customer delivery event persistence, finance output, source writeback, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`CUSTOMER_FACING_DELIVERY_EXECUTION_SURFACE_SELECTED_OPS_WEB_ORCHESTRATION_PLUS_SEAM_EVENT_RECORDING`

Meaning:

1. `apps/operations-web` is the correct owner for the authenticated PM-facing orchestration surface.
2. `apps/mutation-seam` is the correct owner for the canonical insert-only customer-delivery event mutation and readback surface.
3. Actual customer-facing delivery execution must be operator-driven and visibly orchestrated, not hidden inside a review-row route.
4. No exact live-execution phrase is applicable yet because the chosen architecture still needs its route, payload, and stop conditions designed.

## Decision Inputs

The repo already proves the following:

1. `apps/operations-web` is the governed browser operator shell and the public ingress layer for PM-facing route traffic.
2. Browser-side writes are still required to go through the governed mutation seam rather than bypassing it.
3. `apps/mutation-seam` already owns the adjacent canonical customer slices: customer completion baseline, customer preview review, and customer delivery/proof review.
4. The existing delivery/proof review slice already requires `customer_delivery_event_id`, which means a later execution surface should materialize that identity canonically instead of inventing a second parallel identifier.
5. The customer completion baseline still enforces `customer_delivery_authority=not_admitted_external_delivery`, so no existing surface truthfully performs external customer delivery today.

## Architecture Decision

The future customer-facing delivery execution path is split into two bounded surfaces:

1. `apps/operations-web` owns the authenticated operator review-and-launch surface.
2. `apps/mutation-seam` owns the canonical insert-only customer-delivery event recording and readback surface.

The intended future boundaries are:

1. operations-web route placeholder: `/pm-review/customer-delivery-execution`
2. seam mutation route placeholder: `/api/v1/mutations/temp-power-customer-delivery-events`
3. seam status route placeholder: `/api/v1/reads/temp-power-customer-delivery-event-status`

## Why This Split Is Required

1. External customer delivery execution is an operator-facing workflow decision, so it belongs in the browser orchestration lane rather than inside a hidden backend-only branch.
2. Canonical durable state still belongs in the governed mutation seam, consistent with the adjacent preview-review and delivery/proof review slices.
3. The browser surface must not hold direct database authority or bypass the seam.
4. The mutation seam must not silently own external email send or portal upload side effects without a separately designed operator-visible execution contract.

## Required Future Contract Constraints

Any later contract-design lane for this architecture must preserve all of the following:

1. existing hosted delivery/proof review row is a prerequisite
2. canonical `customer_delivery_event_id` must match the reviewed delivery/proof lineage rather than being regenerated from unrelated fields
3. named recipient, delivery channel, delivered artifact refs, `delivered_at_utc`, proof type, and proof ref remain explicit and reviewable
4. operations-web may orchestrate operator intent, but final durable recording still flows through the seam mutation contract
5. customer completion remains a downstream summary consumer, not the primary canonical execution store
6. finance, source writeback, customer billing delivery, and unrelated widening remain separately blocked

## Rejected Architecture Options

Lane 338 explicitly rejects:

1. browser-direct customer delivery execution with no governed seam recording contract
2. direct browser-side database access or secret-held send logic inside operations-web
3. extending the existing delivery/proof review route so it claims customer-facing delivery execution occurred
4. a seam-owned hidden external send path with no operator-facing orchestration surface

## Exact Phrase Result

No next exact live-execution phrase is applicable yet.

Why:

1. the chosen architecture now exists only as a repo-owned decision, not a designed execution contract
2. the next truthful step is contract design for the selected operations-web plus mutation-seam split
3. a live phrase before that design would skip the exact route, payload, and stop-condition definition the PM lane requires

## Current Stop Boundary

The PM lane is truthfully stopped at:

`STOPPED_AWAITING_CUSTOMER_FACING_DELIVERY_EXECUTION_ORCHESTRATION_AND_EVENT_CONTRACT_DESIGN_NO_LIVE`

## Next Safe Packet

The next safe packet is:

`PM Lane 339 - Project Miner Temp Power Customer-Facing Delivery Execution Orchestration And Event Contract Design No-Live Packet`

That packet should define:

1. the operations-web orchestration contract
2. the seam delivery-event mutation and status contract
3. the exact lineage and proof rules tying the future event to the existing hosted delivery/proof review row
4. the exact stop conditions that must hold before any later live-admission phrase can exist

## Explicitly Still Blocked

1. customer-facing report delivery, email send, portal upload, or any other external delivery execution
2. customer delivery event persistence in production or hosted environments
3. finance, billing, payroll, invoice, accounting, labor reconciliation, external finance sync, or customer billing delivery
4. source workbook or PDF writeback and workbook macros
5. any unrelated mutation or autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 338 files.
3. Selected outcome is present.
4. The chosen operations-web plus mutation-seam split is explicit.
5. The absence of an applicable exact live-execution phrase is explicit.
6. The stop boundary is present.
7. The next safe packet is present.
8. `git diff --check` passes.