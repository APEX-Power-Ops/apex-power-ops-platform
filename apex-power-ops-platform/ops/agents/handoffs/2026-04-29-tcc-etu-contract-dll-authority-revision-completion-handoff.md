# TCC ETU Contract DLL Authority Revision — Completion Handoff

Date: 2026-04-29
Status: Closed PASS
Purpose: Record the governance correction that promotes the DLL-visible ETU selection workflow, breaker hierarchy surfaces, and SQL-bearing cross-filter behavior to ETU contract authority

---

## Summary

The ETU contract posture has been revised away from the older
"trip-unit-rooted runtime plus bounded breaker-context metadata" framing.

The new governing note is:

`source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-DLL-AUTHORITY-REVISION-2026-04-29.md`

That note establishes that:

1. the ETU contract source of truth is the DLL-authored selection stack itself
   inside governance: `DvlEng.dll` for workflow shape and
   `EasyPower.DeviceLibrary.DeviceLibrary.cs` for SQL ownership,
2. the contract includes upstream breaker-half hierarchy surfaces and staged
   narrowing behavior where the DLL preserves them,
3. the current runtime ETU cascade is a partial implementation surface rather
   than the contract authority itself,
4. further breaker / ETU refinement should sequence through contract
   reconciliation, not continue under the older bounded-posture assumption.

No new ETU backend or frontend implementation was landed in this packet.

---

## Files Written Or Updated

1. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-DLL-AUTHORITY-REVISION-2026-04-29.md` — new governing contract-revision note.
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SELECTION-MODEL-STATUS-2026-03-24.md` — superseded-in-part authority update added near the header.
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-REMAINING-SUPPORT-SURFACES-AUDIT-2026-04-29.md` — superseded-in-part authority update added near the header.
4. `source-domains/tcc_v5_backend/IMPLEMENTATION_STATUS.md` — current runtime-position wording corrected so the repo no longer presents the older bounded ETU posture as contract truth.
5. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-contract-dll-authority-revision-completion-handoff.md` — this handoff.

---

## Additional Cleanup Performed

An unvalidated ETU backend/test slice begun before the contract decision changed
was removed. The runtime was returned to the prior route behavior before the
governance edits were authored.

Focused route validation after that revert:

```text
tests/test_cascade_route.py
tests/test_etu_search_route.py
7 passed, 1 warning in 2.48s
```

The warning is the existing SQLAlchemy `MovedIn20Warning` from
`models/base.py`.

---

## Net Decision

The ETU contract should now be interpreted as DLL-authoritative for selection
workflow shape, breaker/trip-unit linkage, and cross-filter semantics.

The previous statement that full breaker hierarchy was merely future
architecture work is no longer the honest authority posture.

The next ETU packet should therefore be a contract-reconciliation / runtime-gap
packet, not another refinement packet layered on the old contract framing.

That scoping lane is now closed PASS as:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-2026-04-29.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-contract-reconciliation-runtime-gap-scoping-handoff.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-RULING-2026-04-29.md`
4. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-contract-reconciliation-runtime-gap-scoping-completion-handoff.md`

That ruling records that the ETU / SST runtime represents 9 of 10
DLL-authored contract stages and that Stage 1 (upstream breaker-half identity)
is the single material runtime gap.

The first later execution packet authorizable after this scoping closeout is
Slice alpha only: a read-only ETU breaker-cascade backend over the existing
`tcc_brk_*` tables. Any later Slice beta or Slice gamma work remains
conditional follow-on work after Slice alpha and must be separately authored.

That Slice-alpha lane is now closed PASS as:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-2026-04-29.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-alpha-breaker-cascade-backend-execution-handoff.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
4. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-alpha-breaker-cascade-backend-completion-handoff.md`

That closeout records that Contract Stage 1 is now restored as a read-only
ETU-distinct backend cascade endpoint at `GET /api/v1/neta/etu/breaker-cascade`
with no frontend work and no cross-half SQL wiring.

The Slice-beta lane is now closed PASS as:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-BETA-BREAKER-HALF-UI-AND-INVALIDATION-2026-04-29.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-beta-breaker-half-ui-and-invalidation-execution-handoff.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-BETA-BREAKER-HALF-UI-AND-INVALIDATION-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
4. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-beta-breaker-half-ui-and-invalidation-completion-handoff.md`

That closeout records that Stage 1 is now visible in the ETU demo as a
frontend-only consumer of the alpha backend, while cross-half SQL remains
explicitly held for Slice gamma.

The Slice-gamma lane is now closed PASS as:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-GAMMA-CROSS-HALF-SQL-AND-UI-SCOPING-2026-04-29.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-gamma-cross-half-sql-and-ui-scoping-execution-handoff.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-GAMMA-CROSS-HALF-SQL-AND-UI-SCOPING-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
4. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-gamma-cross-half-sql-and-ui-scoping-completion-handoff.md`

That closeout records that the ETU lane now honors a truthful cross-half
cross-filter contract at the manufacturer axis between the breaker-half and the
trip-unit-half cascades, with minimal UI scoping updates and no DDL, TMT/EMT
widening, or parity claim.

Trigger #3 of the TCC program closeout artifact (breaker-side hierarchy
ownership) is now satisfied. No further conditional follow-on is required to
honor the DLL-authority revision contract within the persisted schema's
structural ceiling.

Residual bounded follow-ons remain separate and unauthored: the REST fallback
path in `/api/v1/neta/cascade` does not yet apply Slice-gamma cross-half
filtering, and the `acdc` parameter on `/api/v1/neta/etu/breaker-cascade`
remains a forward-compatibility no-op pending a separately authored schema-
augmentation packet.