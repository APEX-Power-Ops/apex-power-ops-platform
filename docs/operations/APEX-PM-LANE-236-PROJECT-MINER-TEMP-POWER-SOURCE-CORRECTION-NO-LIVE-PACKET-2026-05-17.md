# APEX PM Lane 236 - Project Miner Temp Power Source Correction No-Live Packet

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_SOURCE_CORRECTION_NO_LIVE`

## Purpose

PM Lane 236 intakes Jason's selected PM Lane 234 response:

`REQUEST_SOURCE_CORRECTION_NO_LIVE`

Jason clarified that source row 28 / `miner-line-015` is normally performed as a single test consisting of multiple individual measurements. The repo-local candidate correction should therefore represent that row as `Ground Resistance Test Lot` instead of treating the blank source designation as an unresolved apparatus designation.

This lane applies that correction to the read-only candidate normalization path only. It does not write back to the source workbook, run macros, open approval POST, create an approval row, import the project, or mutate PM business state.

## Selected Outcome

`SOURCE_CORRECTION_APPLIED_GROUND_RESISTANCE_TEST_LOT_NO_LIVE`

## Correction Applied

| Field | Value |
| --- | --- |
| Candidate ID | `pm-import-candidate-miner-temp-power` |
| Source line ID | `miner-line-015` |
| Estimator source row | 28 |
| Source quantity | 3 |
| Section | `7.13` |
| Apparatus type | `Ground Resistance Test - Two-Point (Lot)` |
| Corrected candidate designation | `Ground Resistance Test Lot` |
| Corrected candidate shape | one lot-level task candidate with three measurements |
| Planned hours preserved | 24 |
| Source workbook writeback | not performed |
| Live approval/import authority | not admitted |

## Implementation

Updated:

1. `apps/mutation-seam/app/project_seed_sources.py`
2. `apps/mutation-seam/tests/test_project_import_candidate.py`

The correction is intentionally narrow:

1. A missing designation on a `Ground Resistance Test` lot row resolves to `Ground Resistance Test Lot`.
2. The task quantity remains `3`, preserving the source measurement count.
3. Expanded apparatus candidates for that row collapse to one lot-level candidate, preventing the three measurements from being treated as three separate apparatus rows.
4. The lot-level candidate receives the full line planned hours when the line total is available.
5. Other blank designations continue to produce `MISSING_DESIGNATIONS`.

## Corrected Preview Evidence

Focused local read-only preview after the correction:

| Field | Value |
| --- | --- |
| Candidate ID | `pm-import-candidate-miner-temp-power` |
| Task count | 15 |
| Apparatus candidate count | 184 |
| Warning count | 1 |
| Blocker count | 0 |
| Remaining warning code | `PROJECT_DATA_ENTRY_FORMULA_ERRORS` |
| `miner-line-015` designation | `Ground Resistance Test Lot` |
| `miner-line-015` quantity | 3 |
| `miner-line-015` apparatus candidates | 1 |
| `miner-line-015` planned hours | 24 |

The prior `MISSING_DESIGNATIONS` warning is cleared by the repo-local candidate correction. The remaining warning is separate tracker/formula context and still needs PM classification before a later approval/import packet.

## Next Safe Branch

PM Lane 237 should refresh approval readiness against the corrected candidate and classify the remaining `PROJECT_DATA_ENTRY_FORMULA_ERRORS` warning without opening live approval/import authority.

## Guardrails

PM Lane 236 adds no hosted smoke, browser live route access, live approval POST, approval row, project import, note, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, service/auth/ingress change, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, confirmed source-truth promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
