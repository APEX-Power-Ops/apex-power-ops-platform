# APEX PM Lane 352 - Project Miner Temp Power Remaining Finance And Source Rule Question Card No-Live Packet

Date: 2026-05-18

Status: Documentation-only no-live question card for the remaining finance, customer-billing-delivery, and source-writeback boundary after PM Lane 351

Decision label:

`PROJECT_MINER_TEMP_POWER_REMAINING_FINANCE_SOURCE_RULE_QUESTION_CARD_NO_LIVE`

## Purpose

PM Lane 352 converts the PM Lane 351 narrowed blocker into a compact answer card for the only unresolved Temp Power downstream authority categories still open after the hosted customer-facing delivery execution branch closed.

This lane does not reopen the earlier actuals/customer branch, because that branch was already consumed by PM Lanes 291 through 349. It only packages the remaining unanswered rule groups:

1. finance output
2. customer billing delivery
3. source workbook/PDF writeback and workbook macros

This lane is documentation-only. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation output, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`REMAINING_FINANCE_SOURCE_RULE_QUESTION_CARD_READY_NO_LIVE`

Meaning:

1. PM Lane 351 remains the current no-return blocker classifier.
2. The remaining unresolved rule groups are now packaged into one compact answer card.
3. No new admission phrase is issued by this lane.
4. A later response can now be classified directly as finance rules, output-write request, or source-writeback request.

## Current Remaining Boundary

Current truth before any later return:

1. billing, payroll, invoice, accounting, labor reconciliation, and external finance output remain blocked
2. customer billing delivery remains blocked
3. source workbook/PDF writeback and workbook macros remain blocked
4. no new exact admission phrase is applicable yet

## Answer Labels

Use one or more of these exact labels for the remaining boundary only:

1. `HOLD_NO_RULES_NO_LIVE`
2. `FINANCE_RULES_ONLY_NO_LIVE`
3. `OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED`
4. `SOURCE_WRITEBACK_REQUEST_SEPARATE_AUTHORITY_REQUIRED`

## Finance And Customer Billing Questions

Answer these only if finance or customer billing delivery should be designed later:

1. authoritative billing rate source:
2. billable, non-billable, included, excluded, taxable, or withheld rows:
3. grouping: workpackage, task, apparatus, customer PO line, date, invoice summary, or other:
4. billing export required before invoice creation: yes/no:
5. approval required before invoice creation or customer billing delivery:
6. payroll authoritative source:
7. payroll classifications, pay codes, overtime rules, and cutoff dates:
8. payroll export allowed, preview only, or blocked:
9. accounting system, entity, customer account, item codes, GL codes, cost codes, and tax treatment:
10. action type: preview, journal entry, invoice posting, external sync, or no external posting:
11. external finance sync allowed: yes/no; if yes, name system and boundary:
12. rollback or reversal rule for incorrect finance output:
13. customer billing delivery recipient and authoritative channel:
14. evidence required to prove customer billing delivery occurred:

## Source Writeback And Macro Questions

Answer these only if source files or macros should be considered later:

1. source writeback requested: yes/no:
2. target source file:
3. requested writeback or macro action:
4. workbook macro requested: yes/no:
5. separate source authority packet required before any action: yes/no:
6. rollback or recovery rule if source writeback is wrong:

## Return Intake Rules

Classify any later response to this question card as follows:

| Future return | Classification | Next move |
| --- | --- | --- |
| No answer, generic continuation authority, or no finance/source rules. | `REMAINING_FINANCE_SOURCE_BOUNDARY_STILL_BLOCKED_NO_NEW_RULE_RETURN_NO_LIVE` | Keep PM Lane 351 active and keep all remaining authority blocked. |
| `HOLD_NO_RULES_NO_LIVE` | `HOLD_NO_RULES_NO_LIVE` | Keep all remaining authority blocked; author a no-live hold refresh only. |
| `FINANCE_RULES_ONLY_NO_LIVE` or equivalent finance/customer-billing rules. | `FINANCE_RULES_ONLY_NO_LIVE` | Author a no-live finance-output design packet; no exports, records, syncs, or deliveries. |
| `OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED` or a direct output-write request. | `OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED` | Stop for a separate admitted write packet with exact proof gates. |
| `SOURCE_WRITEBACK_REQUEST_SEPARATE_AUTHORITY_REQUIRED` or source workbook/PDF writeback or macro request. | `SOURCE_WRITEBACK_REQUEST_SEPARATE_AUTHORITY_REQUIRED` | Stop for a separate source authority packet. |

## Blocked Authority

The following remain blocked after Lane 352:

1. billing export writes
2. payroll export writes
3. invoice records
4. payroll records
5. accounting records
6. labor reconciliation outputs
7. external finance-system syncs
8. customer billing delivery
9. source workbook/PDF writeback
10. workbook macros
11. autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 352 files.
3. Selected outcome is present.
4. The finance/source/customer-billing-only boundary is explicit.
5. The reduced label set is present.
6. Remaining finance and source question groups are present.
7. `git diff --check` passes.
8. Staged diff includes only Lane 352 scoped docs, handoff, and PM status surfaces.

## Next Safe Packet

Next safe packet:

`PM Lane 353 - Project Miner Temp Power Remaining Finance And Source Rule Relay Prompt No-Live Packet`
