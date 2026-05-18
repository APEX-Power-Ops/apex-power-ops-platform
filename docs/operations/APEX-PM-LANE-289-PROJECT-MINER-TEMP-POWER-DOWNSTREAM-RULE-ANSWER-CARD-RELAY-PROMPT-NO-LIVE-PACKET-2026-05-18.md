# APEX PM Lane 289 - Project Miner Temp Power Downstream Rule Answer Card Relay Prompt No-Live Packet

Date: 2026-05-18

Status: Local no-live downstream rule answer-card relay prompt

Decision label:

`PROJECT_MINER_TEMP_POWER_DOWNSTREAM_RULE_ANSWER_CARD_RELAY_PROMPT_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 289 converts the still-open PM Lane 287 downstream rule answer card and the PM Lane 288 no-return classifier into one compact relay prompt Jason can answer directly.

This lane does not interpret the current continuation instruction as a downstream rule answer. It creates only a local no-live prompt surface and keeps all downstream production actuals, customer delivery, billing, payroll, invoice, accounting, labor reconciliation, source writeback, and external finance authority blocked.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`DOWNSTREAM_RULE_ANSWER_CARD_RELAY_PROMPT_READY_NO_LIVE`

Meaning:

1. PM Lane 287 remains the active downstream answer card.
2. PM Lane 288 remains the current no-return classification.
3. The relay prompt below is ready for Jason without creating writes.
4. A future response must be classified before design or live admission.

## Relay Prompt

Copy/paste this prompt to Jason when asking for downstream Temp Power rules:

```text
PM Lane 289 downstream rule relay prompt for Project Miner Temp Power.

The Temp Power baseline is complete through import, field assignment, schedule/status readiness, durable field record, production tracking baseline, customer completion baseline, and financial handoff baseline.

Current baseline:
- project: pm-import-project-miner-temp-power
- candidate: pm-import-candidate-miner-temp-power
- workpackages: 7
- ready tasks: 15
- ready apparatus: 184
- assignments: 184
- downstream production/customer/finance output counts: all zero

Please answer using one or more labels:
1. HOLD_NO_RULES_NO_LIVE
2. ACTUALS_CUSTOMER_RULES_ONLY_NO_LIVE
3. FINANCE_RULES_ONLY_NO_LIVE
4. COMBINED_DOWNSTREAM_RULES_NO_LIVE
5. OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED
6. SOURCE_WRITEBACK_REQUEST_SEPARATE_AUTHORITY_REQUIRED

If you want to provide rules, answer the relevant sections:

Actuals and labor:
- allowed recorder role:
- granularity: apparatus, task, workpackage, day, crew shift, or other:
- evidence required before nonzero actuals:
- correction, void, or replacement rule:
- approval required before billable or payroll relevance:

Customer report and delivery:
- customer-facing artifact required: yes/no; describe if yes:
- approver before delivery:
- recipient and authoritative delivery channel:
- durable delivery event allowed: yes/no:
- evidence required to prove customer delivery:

Billing and invoice:
- authoritative billing rate source:
- billable, non-billable, included, excluded, taxable, or withheld rows:
- grouping: workpackage, task, apparatus, customer PO line, date, or summary:
- billing export required before invoice creation: yes/no:
- approval required before invoice creation or customer delivery:

Payroll:
- authoritative labor source:
- separate timekeeping source required: yes/no:
- payroll classifications, pay codes, overtime rules, and cutoff dates:
- payroll export allowed, preview only, or blocked:
- approval required before payroll export or payroll record creation:

Accounting and external finance:
- accounting system, entity, customer account, item codes, GL codes, cost codes, and tax treatment:
- action type: preview, journal entry, invoice posting, or no external posting:
- external finance sync allowed: yes/no; if yes, name system and boundary:
- rollback or reversal rule for incorrect output:
- secret, credential, endpoint, or integration boundary requiring separate admission:

Source writeback and macro:
- source writeback requested: yes/no:
- target source file:
- requested writeback or macro action:
- separate source authority packet required before any action: yes:

Important: this response is no-live rule capture only. It does not authorize production quantities, labor entries, customer reports or delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, source workbook/PDF writeback, macro execution, or any autonomous AI business-state mutation.
```

## Return Intake Rules

Classify any future response to the relay prompt as follows:

| Future return | Classification | Next move |
| --- | --- | --- |
| No answer, unclear continuation, or no downstream rules. | `NO_DOWNSTREAM_RULE_RETURN_PRESENT_KEEP_QUESTION_CARD_OPEN_NO_LIVE` | Keep PM Lane 287 open and keep all output blocked. |
| `HOLD_NO_RULES_NO_LIVE` | `HOLD_NO_RULES_NO_LIVE` | Keep all output blocked; author a no-live hold/refresh packet only. |
| `ACTUALS_CUSTOMER_RULES_ONLY_NO_LIVE` or equivalent actuals/customer rules. | `ACTUALS_CUSTOMER_RULES_ONLY_NO_LIVE` | Author a no-live actuals/customer capture design packet; no writes. |
| `FINANCE_RULES_ONLY_NO_LIVE` or equivalent finance rules. | `FINANCE_RULES_ONLY_NO_LIVE` | Author a no-live finance output design packet; no exports or records. |
| `COMBINED_DOWNSTREAM_RULES_NO_LIVE` or both actuals/customer and finance rules. | `COMBINED_DOWNSTREAM_RULES_NO_LIVE` | Split into bounded no-live design packets before any live admission. |
| `OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED` or a direct output write request. | `OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED` | Stop for a separate admitted write packet with exact proof gates. |
| `SOURCE_WRITEBACK_REQUEST_SEPARATE_AUTHORITY_REQUIRED` or source workbook/PDF writeback or macro request. | `SOURCE_WRITEBACK_REQUEST_SEPARATE_AUTHORITY_REQUIRED` | Stop for a separate source authority packet. |

## Blocked Authority

The following remain blocked after Lane 289:

1. product code, UI controls, routes, backend seams, payload versions, hosted calls, hosted smokes, and browser live route access
2. live mutation POSTs, schema migrations, Supabase/Render/Vercel/Olares actions, service/auth/ingress changes, and secret changes
3. source workbook/PDF writeback and workbook macros
4. production quantity writes, labor entry writes, actual labor hour writes, apparatus progress writes, and progress update writes
5. customer report creation, completion evidence artifact storage, customer delivery, customer commitment, and customer billing delivery
6. billing exports, payroll exports, invoices, payroll records, accounting records, labor reconciliation outputs, and external finance-system syncs
7. autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 289 files.
3. Selected outcome is present.
4. Relay prompt is present.
5. All six Lane 287 return labels remain present.
6. Forbidden output paths remain explicitly blocked.
7. `git diff --check` passes.
8. Staged diff includes only Lane 289 scoped docs, packet, handoff, closeout, and PM status surfaces.

## Next Safe Packet

Next safe packet after a future return:

`PM Lane 290 - Project Miner Temp Power Downstream Rule Return Intake After Relay Prompt No-Live Packet`
