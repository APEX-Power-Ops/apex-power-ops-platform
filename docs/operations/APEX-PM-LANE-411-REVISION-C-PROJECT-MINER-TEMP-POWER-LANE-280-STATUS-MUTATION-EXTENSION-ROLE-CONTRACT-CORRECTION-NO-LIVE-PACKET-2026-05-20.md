# APEX PM Lane 411 Revision C - Project Miner Temp Power Lane 280 Status Mutation Extension Role Contract Correction No-Live Packet

Date: 2026-05-20

Status: Documentation-only Revision C layered on top of the historical PM Lane 411 record plus Revision A and Revision B to correct the financial-table role contract from PM+Finance to PM+Operations without changing any other recognition, gate, topology, or downstream packet surface

Decision label:

`PROJECT_MINER_TEMP_POWER_APPARATUS_COMPLETION_REVENUE_RECOGNITION_NO_LIVE_DESIGN_REVISION_C`

## Correction Note (2026-05-20 In-Place Hot-Fix)

Phase 0 of the new Lane 419 implementation packet surfaced an internal contradiction in this document. The Role Contract Correction section (below) and migration 012 correctly grant SELECT and INSERT to both `pm` and `operations` on the four financial tables. The original Deliberate Omissions item 3 contradicted that by asserting no INSERT for Operations, citing preservation of Revision A's read-only Finance contract.

The Role Contract Correction section is canonical — it matches migration 012 and the PROJECT_STATUS supplement, and reflects the clarified business intent: Operations and PM are equivalent peer roles on this APEX Power Operations LLC platform. Operations is a peer write authority, not a Finance-style read-only observer (which was Revision A's design vocabulary). Revision C therefore deliberately widens Operations' privileges beyond what Finance had in Revision A; this is intentional, not a preservation.

This in-place hot-fix amends the Precision note below and replaces the contradictory Deliberate Omissions item 3 with a non-conflicting statement. The hot-fix is restorative — it brings Revision C's text into alignment with its own actual, originally-prescribed contract — and therefore does not require a separate Revision D under the layered-revision discipline.

## Purpose

PM Lane 411 Revision C corrects the role contract used by the Lane 411 Revision A financial-table separation design.

Lane 411 Revision A and Revision B remain canonical for the recognition firewall, the vocabulary firewall, the schema topology, the insert-only reversal discipline, and the bidirectional Lane 280 to Lane 412 admission gate. Revision C changes only the role contract on the four financial tables and records the platform-ownership context that explains why Operations, not Finance, is the canonical platform role.

## Selected Outcome

Selected outcome:

`APPARATUS_COMPLETION_REVENUE_RECOGNITION_DESIGN_READY_NO_LIVE_REVISION_C`

Meaning:

1. The historical Lane 411 packet remains intact as the original no-live recognition design.
2. Lane 411 Revision A remains intact as the recognition-firewall and `seam.apparatus_financials` separation refactor.
3. Lane 411 Revision B remains intact as the bidirectional Lane 280 to Lane 412 admission-gate tightening.
4. Revision C corrects only the financial-table role contract and records the APEX platform-ownership context plus the future RESA Corporate accounting integration stub.

## Phase 0 Discovery

### 1. Existing `operations` role references

Discovery result:

1. `apps/mutation-seam/app/auth/jwt.py` and `apps/mutation-seam/app/auth/role_guard.py` do not contain an admitted auth-layer role literal `operations` or `ops`.
2. Repo-wide hits for `operations` are hostnames, route names, documentation text, or natural-language labels such as operations staff references, not a current runtime role identifier enforced by the mutation-seam auth layer.
3. No existing Phase 0 evidence surfaced a conflicting prior meaning for `operations` inside the current auth or role-guard system.

Conclusion:

No auth-role overload conflict surfaced in this repository. Revision C may safely name `operations` as the future non-field financial-table role for this design surface.

### 2. Existing `Finance` or `finance` usage in role contexts

Discovery result:

1. Lane 411 Revision A records the four financial tables as PM-and-Finance-role-only at the grant boundary.
2. Lane 411 Revision B inherits that same PM-and-Finance wording in its unchanged Revision A baseline.
3. Lane 412 Revision A repeats Finance-role wording in its role-separation design discussion.
4. No live mutation-seam auth code currently uses `finance` as an admitted runtime actor role identifier.

Conclusion:

Finance is currently a documentation-only role concept in the Lane 411 and Lane 412 design family, not a live auth-layer identifier. Revision C amends the Lane 411 role contract only and leaves the Lane 412 family unchanged by packet boundary.

### 3. Current financial-table GRANT statements

Discovery result:

1. Repo-local migrations `001` through `011` do not create `seam.apparatus_financials`, `seam.project_contract_snapshots`, `seam.scope_labor_details`, or `seam.apparatus_revenue_events`.
2. Those migrations also do not create a `finance` role, an `operations` role, or the PM-and-Finance GRANT surface described by Lane 411 Revision A.
3. The current repo therefore carries the Lane 411 Revision A and B grant model as a design contract, not as an applied database migration.

Conclusion:

Revision C cannot truthfully amend already-applied financial-table GRANT SQL because no such migration exists in this repo. The Revision C migration artifact is therefore a forward migration contract for the first future application of this surface.

### 4. `finance_authority` finding

Discovery result:

1. No repo-local migration currently defines `seam.apparatus_financials.finance_authority`.
2. The implemented `finance_authority` columns found in current migrations live on later downstream record tables such as `seam.durable_field_records`, `seam.production_tracking_records`, `seam.customer_completion_records`, `seam.financial_handoff_records`, `seam.actuals_capture_reviews`, and `seam.customer_preview_reviews`.
3. In those implemented tables, `finance_authority` tracks downstream finance-output admission state and remains constrained to blocked or lane-scoped admitted values while billing, payroll, invoice, accounting, and external-finance outputs remain separately governed.

Conclusion:

The `seam.apparatus_financials.finance_authority` question is a carry-forward design concern rather than an implemented repo-local schema concern. Revision C records it as a separate future decision and does not rename anything.

## Inherited Lane 411 Revision A And B Baseline

Revision C inherits the following unchanged:

1. The recognition firewall: apparatus revenue recognition reads frozen-at-import quote data only and never operational actuals.
2. The vocabulary firewall: revenue is `quoted_revenue` when frozen and `recognized_amount` when earned.
3. The bidirectional Lane 280 to Lane 412 admission gate from Revision B.
4. The schema topology: `seam.apparatus` remains identity, status, location, and equipment only, with financial data on the separate planned financial tables.
5. The constrained-text `snapshot_kind` pattern.
6. The insert-only `seam.apparatus_revenue_events` reversal discipline.
7. The planned trigger behavior on PM disposition to `Complete`.
8. Every CHECK constraint and trigger described by Revision A.
9. Field Tech and Field Lead exclusion from financial-table SELECT.

This packet does not modify any of those.

## Role Contract Correction

Lane 411 Revision A's role contract used Finance as the non-field financial-table role. Revision C amends that role contract to Operations.

Corrected table-level contract:

1. `seam.apparatus_financials`: GRANT SELECT, INSERT to `pm` and `operations`.
2. `seam.project_contract_snapshots`: GRANT SELECT, INSERT to `pm` and `operations`.
3. `seam.scope_labor_details`: GRANT SELECT, INSERT to `pm` and `operations`.
4. `seam.apparatus_revenue_events`: GRANT SELECT, INSERT to `pm` and `operations`.
5. `field_tech` and `field_lead` remain excluded from SELECT and INSERT on all four financial tables.

Precision note:

Revision C amends the financial-table role contract by replacing Finance with Operations AND by deliberately widening the non-PM role's privileges to peer-write status. Operations receives the same SELECT and INSERT privileges as `pm` on all four financial tables, reflecting Operations' position as a peer write authority under APEX Power Operations LLC governance — not as a read-only Finance-style observer (which was Revision A's design vocabulary). Revision C does not widen the table list, alter the recognition firewall, or change any non-role behavior in Revision A or Revision B.

## Platform Ownership

Platform ownership.

This platform is APEX Power Operations LLC infrastructure, a separate legal entity from any RESA or related operating company. Current admitted roles for this design surface are `pm` and `operations`.

Operations performs the role functions that Revision A described with Finance vocabulary: contract-support admission, revenue-recognition oversight, and financial-table access under APEX Power Operations LLC governance rather than under a RESA-org Finance department.

## Future RESA Corporate Accounting Integration Stub

Future RESA Corporate accounting integration, documented stub only.

A future read or write integration between this platform and a RESA Corporate accounting system has been discussed but not designed. If that integration is ever admitted, it is a separate service-to-service boundary, not a role on this platform. No GRANT, schema, or route in the current Lane 411 family pre-admits that integration. It is recorded here only so later packets do not re-derive the question.

## Carry-Forward Note On `finance_authority`

`finance_authority` column name - flagged for separate decision.

The `finance_authority` naming concern tied to planned financial surfaces remains unresolved in this repo. Current implemented uses of `finance_authority` mean downstream finance-output admission state, while the planned `seam.apparatus_financials` surface has not yet been migrated into the database at all.

With Operations now established as the canonical platform-local role, the name may later prove semantically misleading or may prove reserved for the future RESA Corporate accounting integration stub. That question is OUT OF SCOPE for Lane 411 Revision C and requires its own focused decision packet. Revision C does not propose a rename, and Lane 412 surfaces remain unchanged.

## Forward Migration Contract

Because no repo-local migration currently creates the Lane 411 financial tables or applies the Revision A PM-and-Finance grant model, Revision C records the first truthful forward application contract at:

`apps/mutation-seam/migrations/012_pm_lane_411_revision_c_role_contract_grants.md`

That migration-equivalent contract:

1. records that `operations` is the intended replacement for the prior Finance role vocabulary,
2. records the future SQL needed once the underlying financial tables exist,
3. creates `operations` if absent in the future live migration,
4. carries the corrected four-table PM-and-Operations SELECT and INSERT contract,
5. preserves Field Tech and Field Lead exclusion,
6. does not pretend that prior Finance grants were ever applied from this repo.

## Boundaries

This revision does not admit:

1. live route implementation
2. hosted deployment
3. live business writes
4. apparatus status mutation
5. public schema writes
6. billing, invoice, payroll, accounting, customer-billing, or external-finance output
7. RESA Corporate accounting integration
8. source workbook writeback or macros
9. change-order admission
10. live operational-hours tracking
11. autonomous AI business-state mutation
12. modification to Lane 412, Lane 413, Lane 414, Lane 415, Lane 416, Lane 417, or Lane 418 surfaces
13. rename of any `finance_authority` column
14. promotion to Lane 413 Revision A or the later live implementation packet

## Validation Before Closeout

Required validation for this revision packet:

1. all four Phase 0 discovery questions are documented
2. the role contract amendment is limited to the four named financial tables
3. the amendment is precise: PM+Finance becomes PM+Operations on those four tables only
4. Field Tech and Field Lead exclusions remain unchanged
5. the forward migration artifact is documented as first application because no prior applied grant SQL exists in repo migrations
6. `operations` is documented as pre-existing nowhere in repo auth and as created by the future migration contract if absent
7. the platform-ownership context is explicit
8. the future RESA Corporate accounting stub is recorded as non-admitted
9. the `finance_authority` naming issue is recorded as a separate decision item and not renamed here
10. the recognition firewall remains unchanged
11. the vocabulary firewall remains unchanged and the legacy underscore revenue token stays absent
12. the Lane 280 to Lane 412 bidirectional gate remains unchanged
13. no Lane 412, Lane 413, or Lane 414 through Lane 418 artifact is modified

## Validation Commands

```powershell
Get-Content ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-c-project-miner-temp-power-lane-280-status-mutation-extension-role-contract-correction-no-live-packet.json | ConvertFrom-Json | Out-Null
Select-String -Path PROJECT_STATUS.md,docs/operations/APEX-PM-LANE-411-REVISION-C-PROJECT-MINER-TEMP-POWER-LANE-280-STATUS-MUTATION-EXTENSION-ROLE-CONTRACT-CORRECTION-NO-LIVE-PACKET-2026-05-20.md,apps/mutation-seam/migrations/012_pm_lane_411_revision_c_role_contract_grants.md,ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-c-project-miner-temp-power-lane-280-status-mutation-extension-role-contract-correction-no-live-packet.json,ops/agents/handoffs/2026-05-20-pm-lane-411-revision-c-project-miner-temp-power-lane-280-status-mutation-extension-role-contract-correction-no-live-packet-handoff.md,ops/agents/handoffs/2026-05-20-pm-lane-411-revision-c-project-miner-temp-power-lane-280-status-mutation-extension-role-contract-correction-no-live-packet-closeout.md -Pattern "PM-and-Operations|APEX Power Operations LLC|finance_authority|first truthful forward application|GRANT SELECT, INSERT"
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-411-REVISION-C-PROJECT-MINER-TEMP-POWER-LANE-280-STATUS-MUTATION-EXTENSION-ROLE-CONTRACT-CORRECTION-NO-LIVE-PACKET-2026-05-20.md apps/mutation-seam/migrations/012_pm_lane_411_revision_c_role_contract_grants.md ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-c-project-miner-temp-power-lane-280-status-mutation-extension-role-contract-correction-no-live-packet.json ops/agents/handoffs/2026-05-20-pm-lane-411-revision-c-project-miner-temp-power-lane-280-status-mutation-extension-role-contract-correction-no-live-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-411-revision-c-project-miner-temp-power-lane-280-status-mutation-extension-role-contract-correction-no-live-packet-closeout.md
```

Canonical GRANT SQL for the corrected contract lives in `apps/mutation-seam/migrations/012_pm_lane_411_revision_c_role_contract_grants.md` (Future Application Contract section). That file is the single source of truth for the eventual forward migration; this Validation Commands block intentionally does not duplicate the SQL.

## Deliberate Omissions

1. No live SQL is applied by this packet.
2. No Finance-role REVOKE block is recorded because no prior applied Finance grant migration was found in repo history.
3. No new tables, columns, constraints, triggers, or check rules are introduced by this packet; the schema topology established by Revision A remains structurally unchanged.
4. No `finance_authority` rename is proposed because that is a separate design decision.

## Boundary Note

If a future live packet finds that the target database already contains a conflicting `operations` role definition or pre-existing Finance grants created outside this repo, that packet must classify and resolve the live-environment drift explicitly rather than silently overloading this contract.
