# APEX PM Lane 287 - Project Miner Temp Power Downstream Rule Question Card No-Live Packet

Date: 2026-05-18

Status: Local no-live downstream rule question card

Decision label:

`PROJECT_MINER_TEMP_POWER_DOWNSTREAM_RULE_QUESTION_CARD_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 287 converts the PM Lane 286 missing-rule binder into a compact Jason-facing answer card for downstream production actuals, customer delivery, billing, payroll, invoice, accounting, labor reconciliation, source writeback, and external finance rules.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`DOWNSTREAM_RULE_QUESTION_CARD_READY_NO_LIVE`

Meaning:

1. The Lane 286 proof binder stays the current post-pilot baseline.
2. Downstream output authority is still missing and remains blocked.
3. The next PM action is to collect Jason's downstream rules through the answer card below.
4. Any returned answer must be classified before another packet can design or admit output behavior.

## Source Baseline

Lane 287 inherits the PM Lane 286 no-live binder result:

- positive baseline: 1 imported project, 7 workpackages, 15 ready tasks, 184 ready apparatus, 184 assignments, 1 durable field record, 1 production tracking record, 1 customer completion record, 1 financial handoff record, 199 source trace rows, and 1 warning review row
- zero-output state: 0 production quantities, 0 labor entries, `0.00` actual labor hours, 0 apparatus progress entries, 0 progress updates, 0 customer reports, 0 completion evidence artifacts, 0 customer delivery events, 0 billing exports, 0 payroll exports, 0 invoice records, 0 payroll records, 0 accounting records, 0 labor reconciliation entries, 0 external finance syncs, 0 customer billing deliveries, `0.00` billable amount total, and `0.00` payroll amount total

## Jason Answer Card

Use this card as the exact return surface for downstream rule capture. Jason can answer one section, several sections, or select a hold/request label. All answers are no-live rule inputs only.

### Return Labels

Choose one or more labels:

1. `HOLD_NO_RULES_NO_LIVE`
2. `ACTUALS_CUSTOMER_RULES_ONLY_NO_LIVE`
3. `FINANCE_RULES_ONLY_NO_LIVE`
4. `COMBINED_DOWNSTREAM_RULES_NO_LIVE`
5. `OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED`
6. `SOURCE_WRITEBACK_REQUEST_SEPARATE_AUTHORITY_REQUIRED`

### Actuals And Labor Rules

Answer when actuals, labor, apparatus progress, or progress updates should be designed later:

1. Allowed recorder role:
2. Granularity: apparatus, task, workpackage, day, crew shift, or other:
3. Required evidence before nonzero actuals:
4. Correction, void, or replacement rule:
5. Approval required before billable or payroll relevance:

### Customer Report And Delivery Rules

Answer when customer-facing reports, completion evidence, or delivery events should be designed later:

1. Customer-facing artifact required: yes/no; describe if yes:
2. Approver before delivery:
3. Recipient and authoritative delivery channel:
4. Durable delivery event allowed: yes/no; if no, keep local artifact only:
5. Evidence required to prove customer delivery:

### Billing And Invoice Rules

Answer when billing exports or invoice design should be considered later:

1. Authoritative billing rate source:
2. Billable, non-billable, included, excluded, taxable, or withheld rows:
3. Grouping: workpackage, task, apparatus, customer PO line, date, or summary:
4. Billing export required before invoice creation: yes/no:
5. Approval required before invoice creation or customer delivery:

### Payroll Rules

Answer when payroll exports, payroll records, or labor reconciliation should be considered later:

1. Authoritative labor source:
2. Separate timekeeping source required: yes/no; describe if yes:
3. Payroll classifications, pay codes, overtime rules, and cutoff dates:
4. Payroll export allowed, preview only, or blocked:
5. Approval required before payroll export or payroll record creation:

### Accounting And External Finance Rules

Answer when accounting records, finance outputs, or external finance syncs should be considered later:

1. Accounting system, entity, customer account, item codes, GL codes, cost codes, and tax treatment:
2. Action type: preview, journal entry, invoice posting, or no external posting:
3. External finance sync allowed: yes/no; if yes, name system and boundary:
4. Rollback or reversal rule for incorrect output:
5. Secret, credential, endpoint, or integration boundary requiring separate admission:

### Source Writeback And Macro Rules

Answer only if source workbook/PDF writeback or macro execution is being requested:

1. Source writeback requested: yes/no:
2. Target source file:
3. Requested writeback or macro action:
4. Separate source authority packet required before any action: yes:

## Classification Logic

Use this classifier on any answer returned to this card:

| Return condition | Classification | Next move |
| --- | --- | --- |
| Jason gives no downstream rules or selects hold. | `HOLD_NO_RULES_NO_LIVE` | Keep all output blocked; route to a later hold, refresh, or answer-card return intake. |
| Jason gives actuals, labor, progress, customer report, completion evidence, or customer delivery rules only. | `ACTUALS_CUSTOMER_RULES_ONLY_NO_LIVE` | Prepare a no-live actuals/customer capture design packet; no writes. |
| Jason gives billing, payroll, invoice, accounting, labor reconciliation, customer billing delivery, or external finance rules only. | `FINANCE_RULES_ONLY_NO_LIVE` | Prepare a no-live finance output design packet; no exports or records. |
| Jason gives both actuals/customer and finance rules. | `COMBINED_DOWNSTREAM_RULES_NO_LIVE` | Split into bounded no-live design packets before any live admission. |
| Jason requests production, customer, billing, payroll, invoice, accounting, sync, or other output writes. | `OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED` | Stop for a separate admitted write packet with exact proof gates. |
| Jason requests source workbook/PDF writeback or macro execution. | `SOURCE_WRITEBACK_REQUEST_SEPARATE_AUTHORITY_REQUIRED` | Stop for a separate source authority packet. |

## Blocked Authority

The following remain blocked after Lane 287:

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
2. Decision label is present in all touched Lane 287 files.
3. Selected outcome is present.
4. Return labels are present.
5. Actuals/customer, finance, output-write, and source-writeback classifiers are present.
6. Forbidden output paths remain explicitly blocked.
7. `git diff --check` passes or reports only known line-ending warnings.
8. Staged diff includes only Lane 287 scoped docs, packet, handoff, closeout, and PM status surfaces.

## Next Safe Packet

Next safe packet:

`PM Lane 288 - Project Miner Temp Power Downstream Rule Return Intake And Classification No-Live Packet`
