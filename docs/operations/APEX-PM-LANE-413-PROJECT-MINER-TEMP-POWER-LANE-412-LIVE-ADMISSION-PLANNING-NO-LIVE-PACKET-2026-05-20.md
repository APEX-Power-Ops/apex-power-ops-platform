# APEX PM Lane 413 - Project Miner Temp Power Lane 412 Live Admission Planning No-Live Packet

Date: 2026-05-20

Status: Documentation-only planning packet layered on top of the historical Lane 412 packet and Lane 412 Revision A + B to define the full admission roadmap from design-only state to first verified live row written to `seam.apparatus_financials`

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_412_LIVE_ADMISSION_PLANNING_NO_LIVE`

## Purpose

PM Lane 413 is the planning bridge from the stable Lane 412 design state to the first later packet that will actually write a live row.

This packet does not admit any write. It does not deploy any route. It does not migrate any schema. Its job is to name the downstream packets in order, articulate the failure-mode contract the route must satisfy, identify the earliest step where the synthetic multi-scope fixture must be exercised, and define the gate criteria each step must clear before the next one is admittable.

## Selected Outcome

Selected outcome:

`LANE_412_LIVE_ADMISSION_PLAN_READY_NO_LIVE`

Meaning:

1. The Lane 412 route family now has an explicit ordered roadmap from planning to first verified live write.
2. The failure-mode contract is named before any write packet is discussable.
3. The multi-scope fixture is required before any live-gate packet, not left to a later proof cleanup.
4. Every downstream step named by this packet still requires its own later admission packet.

## Inherited Lane 412 Revision A + B Baseline

This planning packet inherits the following design facts unchanged:

1. pure insert-only into `seam.apparatus_financials` with the per-row internal-consistency CHECK on `quoted_revenue` and `recognition_rate_per_hour_snapshot`
2. project-level CHECK on `seam.project_contract_snapshots` rate consistency
3. financial tables are PM-and-Finance-role-only at the RLS grant level; Field Tech and Field Lead are excluded
4. the readback classifications remain `missing`, `ready`, `stale_candidate`, `counts_mismatch`, and `unavailable`
5. the explicit downstream-gate clause from Lane 412 Revision B remains canonical: later Lane 280 live admission requires Lane 412 readback `classification = ready`
6. the multi-scope allocation rule remains `scope_pool_amount = project_pool_amount * (scope_hours / project_hours)` with `named_design_assumption: true`

This planning packet does not modify any of those inherited facts.

## Full Admission Roadmap

The downstream packet sequence is:

1. PM Lane 414 - Local Mocked Dry-Run Packet
2. PM Lane 415 - Dry-Run Envelope Export Packet
3. PM Lane 416 - Dry-Run Readiness Checkpoint Packet
4. PM Lane 417 - Dry-Run Readiness Export Packet
5. PM Lane 418 - Review Bundle Export Packet
6. PM Lane 419 - Hosted Dual-Route Smoke Readiness Packet
7. PM Lane 420 - Live-Gate Preflight Packet
8. PM Lane 421 - First-Write Mutation Seam Packet
9. PM Lane 422 - Production Proof Packet

Why this shape was selected:

1. local mocked steps are needed because the write path spans five write targets inside one atomic transaction
2. the earliest multi-scope gate must happen locally before hosted promotion becomes discussable
3. the hosted smoke step must prove both routes are deployed and safe before the first live write packet is discussable
4. production proof must remain separate from the first-write packet so rollback, idempotent replay, and readback verification are independently captured

## Single-Route Vs Dual-Route Sequencing Decision

Selected option: `Option B - write route and readback route deploy together as a single feature unit`

Reason:

1. both routes share the same schema, idempotency semantics, and lane meaning
2. the readback route exists specifically to surface the write route's state, so separating deployments would create an intermediate hosted state where the write surface exists without its canonical status surface
3. the first live row is not truthfully verifiable for Lane 412 without the readback contract that later Lane 280 admission depends on
4. deploying both routes together minimizes drift between stored state and the readback surface that classifies that state

## Failure-Mode Contract

The future write route is:

`POST /api/v1/mutations/project-import-contract-support`

The route writes:

1. one `seam.project_contract_snapshots` row
2. several `seam.scope_labor_details` rows
3. several insert-only `seam.apparatus_financials` rows
4. one audit event
5. one idempotency cache entry

### Transaction Boundary

All five write groups must run inside one Postgres transaction. The transaction commits only after every write target succeeds. Any failure before commit rolls back the entire unit of work.

### Success Response

On first successful write the route returns a committed success payload shaped like:

```text
http_status = 201
classification = import_contract_support_persisted
mutation_status = committed
mutation_id = caller mutation id
audit_event_id = committed audit id
project_contract_snapshot_id = committed snapshot row id
scope_labor_detail_row_count = committed count
apparatus_financial_row_count = committed count
idempotent_hit = false
current_candidate_match = true
```

### Same-Payload Retry

On retry of the exact same payload with the same idempotency key the route returns:

```text
http_status = 200
classification = idempotent_hit
mutation_status = previously_committed
mutation_id = original committed mutation id
audit_event_id = original committed audit id
project_contract_snapshot_id = original committed snapshot row id
scope_labor_detail_row_count = original committed count
apparatus_financial_row_count = original committed count
idempotent_hit = true
```

### Idempotency Key Construction

The idempotency key must be a stable digest of the business payload, not just the caller-supplied mutation id.

Recommended construction:

```text
sha256(
  project_id |
  candidate_id |
  source_fingerprint |
  snapshot_kind |
  contract_value |
  total_quoted_hours |
  ordered scope_labor_details rows |
  ordered apparatus_financials rows
)
```

### Partial Failure Responses And Database State

1. Snapshot insert succeeds but a `seam.scope_labor_details` row fails on constraint:
   response = `409 transaction_rolled_back_scope_detail_conflict`
   database state after response = completely rolled back; no snapshot row, no scope rows, no apparatus financial rows, no audit event, no idempotency cache entry remain committed.
2. Snapshot insert succeeds but one `seam.apparatus_financials` row fails the internal-consistency CHECK:
   response = `422 transaction_rolled_back_apparatus_financial_validation_failed`
   database state after response = completely rolled back; no partial inserts remain committed.
3. Audit event insert fails:
   response = `503 transaction_rolled_back_audit_write_unavailable`
   database state after response = completely rolled back; no business rows remain committed.
4. Idempotency cache write fails:
   response = `503 transaction_rolled_back_idempotency_write_unavailable`
   database state after response = completely rolled back; no snapshot, scope, apparatus financial, or audit rows remain committed.

In every failure case the route must return `mutation_status = rolled_back` and `partial_commit = false`.

### Same Payload With Different Mutation Id

If the same business payload arrives a second time with a different `mutation_id`, the route must treat that as a deliberate conflict, not a server error.

Required response:

```text
http_status = 409
classification = duplicate_business_payload_conflict
mutation_status = rejected
conflict_reason = same business payload supplied under a different mutation id
```

If the route does not catch this before persistence and the underlying unique write guard rejects it, the rejection must still be mapped to the same deliberate conflict response, never a 500.

## Multi-Scope Fixture Requirement

The multi-scope fixture is mandatory because single-scope Miner Temp Power data can hide normalization defects.

### Synthetic Fixture Shape

Use a synthetic two-scope project fixture with:

1. project `contract_value = 10000.00`
2. scope A quoted hours = `60.00`
3. scope B quoted hours = `40.00`
4. project total quoted hours = `100.00`
5. project recognition rate per hour = `100.00`
6. scope A expected pool amount = `6000.00`
7. scope B expected pool amount = `4000.00`
8. apparatus distribution chosen so each scope has multiple apparatus rows and no single apparatus equals its scope total alone

### Earliest Required Packet

The fixture must be present and exercised by PM Lane 416 - Dry-Run Readiness Checkpoint Packet at the latest. It may be introduced earlier in Lane 414, but promotion beyond Lane 416 is blocked if it has not been exercised there.

### Required Verification

The fixture must prove:

1. summed `apparatus_financials.quoted_revenue` by scope equals `scope_pool_amount` for each scope
2. the project-level sum of all `apparatus_financials.quoted_revenue` equals `contract_value`
3. the stored `recognition_rate_per_hour_snapshot` produces the same per-row `quoted_revenue` used by the fixture expectations

## Per-Step Gate Criteria

### PM Lane 414 - Local Mocked Dry-Run Packet

Evidence required:

1. canned write-route success payload
2. canned rollback payloads for each named failure class
3. local trace showing no Supabase touch

Gate to next step:

The packet proves the envelope, response families, and rollback classifications are representable without live writes.

Blocks promotion:

1. missing failure payload family
2. ambiguous success/readback shape
3. any local path that touches Supabase

### PM Lane 415 - Dry-Run Envelope Export Packet

Evidence required:

1. exported wire-format envelope
2. stable ordering proof for scope rows and apparatus rows
3. exported idempotency-key input summary

Gate to next step:

The exact future request envelope is frozen for review and replay simulation.

Blocks promotion:

1. unstable field ordering
2. missing envelope fields required by failure-mode contract
3. idempotency-key inputs not traceable from the export

### PM Lane 416 - Dry-Run Readiness Checkpoint Packet

Evidence required:

1. readiness checklist
2. exercised synthetic two-scope fixture
3. fixture verification output for scope totals and project total
4. rollback expectation matrix

Gate to next step:

The multi-scope fixture passes and the route contract is reviewable as ready for export.

Blocks promotion:

1. fixture absent
2. fixture present but scope totals do not reconcile
3. checkpoint leaves any failure-mode path unspecified

### PM Lane 417 - Dry-Run Readiness Export Packet

Evidence required:

1. exported readiness checkpoint artifact
2. embedded fixture results
3. embedded promotion blockers, if any

Gate to next step:

The readiness posture is exportable and stable for external review.

Blocks promotion:

1. export omits fixture proof
2. export omits blockers or gate state
3. export diverges from checkpoint facts

### PM Lane 418 - Review Bundle Export Packet

Evidence required:

1. bundle containing envelope export, readiness export, fixture evidence, failure-mode contract summary, and sequencing decision
2. explicit no-live boundary statement

Gate to next step:

The full review package exists for hosted promotion discussion.

Blocks promotion:

1. missing bundle member
2. missing failure-mode summary
3. boundary wording implies admission instead of planning

### PM Lane 419 - Hosted Dual-Route Smoke Readiness Packet

Evidence required:

1. hosted deployment proof that write and readback routes are present in the same feature unit
2. safe no-write smoke proof on the hosted surface
3. authentication and role-boundary proof
4. no-write failure proof showing no live row was inserted

Gate to next step:

Hosted deployment is reachable and safe, but still no live write has occurred.

Blocks promotion:

1. only one of the two routes is deployed
2. hosted smoke implies write side effects
3. auth or role boundaries drift from Revision A + B

### PM Lane 420 - Live-Gate Preflight Packet

Evidence required:

1. final pre-write checklist
2. hosted route readiness proof
3. multi-scope fixture evidence carried forward
4. transaction rollback expectations restated
5. exact admission phrase for the first write

Gate to next step:

The route is ready for the first controlled live write packet.

Blocks promotion:

1. fixture not already proven
2. hosted smoke incomplete
3. rollback contract unresolved
4. admission phrase not explicit

### PM Lane 421 - First-Write Mutation Seam Packet

Evidence required:

1. first committed live response payload
2. direct database verification of one committed snapshot row, expected scope rows, expected apparatus financial rows, one audit event, and one idempotency cache entry
3. exact same-payload replay proof returning `idempotent_hit`
4. deliberate conflict proof for same business payload under a different mutation id

Gate to next step:

The first live row family is written and proven with replay and conflict behavior.

Blocks promotion:

1. any partial-write residue
2. replay creates duplicate rows
3. conflict path returns 500 or other ambiguous failure
4. readback does not reflect the committed write state

### PM Lane 422 - Production Proof Packet

Evidence required:

1. production readback proof showing the expected classification after the first write
2. proof that downstream gate semantics remain intact for later Lane 280 admission
3. production artifact set tying hosted mutation result to readback state

Gate to next step:

The first verified live row is fully closed out and the next active item becomes whatever subsequent live-admission step the proof identifies.

Blocks promotion:

1. production readback inconsistent with committed data
2. downstream gate wording drift
3. proof artifact missing mutation-to-readback traceability

## Cross-Lane Gate Inheritance

This planning packet itself does not gate on Lane 412 readback `classification = ready` because Lane 412 is the readback surface being implemented.

That changes only after the readback exists live. Any later Lane 280 status-mutation extension live-admission packet inherits the downstream gate from Lane 412 Revision B: Lane 280 live admission is not admittable until Lane 412 readback returns `classification = ready` for the project in current production state.

Lane 412 Revision B is the canonical source of that downstream gate. Lane 411 Revision B is the matching reverse-side admission-time prerequisite.

## Boundaries

This planning packet does not admit:

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
12. admission of any named downstream packet; naming is design, not admission

## Validation Before Closeout

Required validation for this planning packet:

1. the full admission roadmap is named with every packet enumerated in order
2. the failure-mode contract states what the route returns and what the database state is for each named partial failure
3. the multi-scope fixture requirement names PM Lane 416 as the earliest mandatory exercised gate at the latest
4. each named packet has explicit gate criteria and blockers
5. the cross-lane gate inheritance section is explicit that this planning packet does not gate on readback, but later Lane 280 admission does
6. the single-route versus dual-route sequencing decision is named and justified
7. the inherited Lane 412 Revision A + B baseline section lists the unchanged design facts carried forward
8. the legacy underscore revenue token does not appear anywhere in this packet
