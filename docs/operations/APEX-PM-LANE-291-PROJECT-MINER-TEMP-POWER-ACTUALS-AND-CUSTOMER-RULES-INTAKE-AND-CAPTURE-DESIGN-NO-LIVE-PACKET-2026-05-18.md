# APEX PM Lane 291 - Project Miner Temp Power Actuals And Customer Rules Intake And Capture Design No-Live Packet

Date: 2026-05-18

Status: Local no-live actuals and customer rule intake and capture design

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_RULES_INTAKE_CAPTURE_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 291 intakes Jason's downstream rule return after the PM Lane 289 relay prompt and classifies it as actuals/customer only.

The reply explicitly allows the recommended actuals/labor and customer report/delivery rule defaults to proceed as no-live design inputs, while items 3 through 5 remain future and potential feature placeholders only. This lane records the accepted no-live defaults for actuals capture and customer report preview, keeps all finance and source-writeback boundaries blocked, and sets the next safe lane as actuals/customer capture contract design only.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`ACTUALS_CUSTOMER_RULES_ONLY_NO_LIVE_CAPTURE_DESIGN_READY`

Meaning:

1. The latest downstream reply is interpreted as a valid actuals/customer rules return.
2. Actuals/labor and customer report/delivery rules are accepted as no-live design inputs only.
3. Billing/invoice, payroll, and accounting/external finance remain future placeholders only and are not admitted for design or output behavior in this lane.
4. Source workbook/PDF writeback and workbook macros remain not requested and separately blocked.

## Current Return Classification

| Field | Value |
| --- | --- |
| Current project | `pm-import-project-miner-temp-power` |
| Current candidate | `pm-import-candidate-miner-temp-power` |
| Prior answer card | PM Lane 287 |
| Prior relay prompt | PM Lane 289 |
| Continuation authority present | Yes |
| Equivalent actuals/customer return present | Yes |
| Actuals/customer rules present | Yes |
| Finance rules present | No |
| Finance rules intentionally deferred as placeholders | Yes |
| Output-write request present | No |
| Source-writeback request present | No |
| Interpreted as downstream rule answer | Yes |
| Downstream output authority | `not_admitted` |

## Accepted Actuals And Labor Rules

The following actuals/labor defaults are accepted for no-live design only:

1. Allowed recorder role: PM and field lead only.
2. Granularity: task plus apparatus when available; otherwise task and day.
3. Required evidence before nonzero actuals: signed field ticket or daily field record, plus supporting test sheet, PM-approved field note, or photo evidence when applicable.
4. Correction, void, or replacement rule: append-only void and replacement only; no destructive edits.
5. Approval required before billable or payroll relevance: yes, PM approval required.

## Accepted Customer Report And Delivery Rules

The following customer-report and delivery defaults are accepted for no-live design only:

1. Customer-facing artifact required: yes, but preview only in the next no-live design lane.
2. Approver before delivery: PM.
3. Recipient and authoritative delivery channel: named customer PM or owner representative through controlled email or a later approved portal.
4. Durable delivery event allowed: no; keep preview-only until separately admitted.
5. Evidence required to prove customer delivery later: email receipt, signed transmittal, or portal timestamp once delivery is separately admitted.

## Explicit Deferred Placeholder Groups

The following groups are not answered for current design execution and remain future placeholders only:

1. billing and invoice rules
2. payroll rules
3. accounting and external finance rules

These groups remain blocked, unadmitted, and out of scope for PM Lane 291.

## Source Writeback And Macro Posture

Source workbook/PDF writeback and workbook macros remain outside this lane:

1. source writeback requested: no
2. workbook macro requested: no
3. separate source authority packet required before any future action: yes

## Design Consequences

Use the following consequences for later no-live design lanes:

1. actuals capture may be designed only as a no-live contract and review surface; no writes
2. customer report may be designed only as a preview artifact; no durable delivery event
3. no billing, payroll, invoice, accounting, labor reconciliation, or external finance behavior may be designed from this lane's accepted rules
4. no customer billing delivery, source writeback, or macro behavior may be designed from this lane's accepted rules
5. any future live or durable output path still requires separate explicit admission

## Blocked Authority

The following remain blocked after Lane 291:

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
2. Decision label is present in all touched Lane 291 files.
3. Selected outcome is present.
4. `ACTUALS_CUSTOMER_RULES_ONLY_NO_LIVE` classification is present.
5. Accepted actuals/labor defaults are present.
6. Accepted customer report/delivery defaults are present.
7. Deferred finance placeholder posture is present.
8. Forbidden output paths remain explicitly blocked.
9. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 292 - Project Miner Temp Power Actuals And Customer Capture Contract Design No-Live Packet`