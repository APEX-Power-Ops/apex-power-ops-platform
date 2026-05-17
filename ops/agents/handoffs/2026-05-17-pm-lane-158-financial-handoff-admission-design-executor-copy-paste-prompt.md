# PM Lane 158 - Financial Handoff Admission Design Executor Copy/Paste Prompt

You are Desktop Codex operating as a bounded PM-lane design executor under VS Code Codex technical authority.

## Assignment

Produce a design-only closeout for financial handoff admission.

Use PM Lane 156 and PM Lane 157 as context, then draft the minimum financial handoff admission design needed before any later packet could safely discuss billing export, payroll export, invoice/accounting boundaries, labor reconciliation, audit/readback, or external finance-system sync.

## Authority Band

Band A/B - read-only design and one closeout handoff only.

## Required Reads

Read these files:

- `C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-17-pm-lane-156-local-financial-handoff-admission-draft-export.json`
- `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-pm-lane-156-local-financial-handoff-admission-draft-export-handoff.md`
- `C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-17-pm-lane-157-local-pilot-launch-binder-export.json`
- `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-pm-lane-157-local-pilot-launch-binder-export-handoff.md`
- `C:\APEX Platform\apex-power-ops-platform\docs\operations\PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `C:\APEX Platform\apex-power-ops-platform\docs\operations\APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `C:\APEX Platform\apex-power-ops-platform\docs\operations\APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`

You may inspect `apps/operations-web/app/pm-review/import-intake/page.tsx` and `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts` only to confirm artifact names and blocked boundary wording. Do not edit them.

## Allowed Write

Write exactly one file:

- `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-pm-lane-158-financial-handoff-admission-design-executor-closeout.md`

## Forbidden Writes And Actions

- Do not edit product code.
- Do not edit docs other than the one closeout.
- Do not create packets beyond the closeout.
- Do not stage, commit, push, or fast-forward any host.
- Do not access Supabase, Render, Vercel, Olares, MCP services, hosted services, credentials, secrets, schemas, auth, ingress, runtime, or control-plane surfaces.
- Do not run SQL or migrations.
- Do not run workbook macros.
- Do not write workbook files.
- Do not call any mutation endpoint.
- Do not create approval rows.
- Do not import projects, workpackages, tasks, or apparatus rows.
- Do not create field authorization, assignment, schedule/status, durable field record, production tracking, customer reporting, billing, payroll, invoice, accounting, labor reconciliation, customer billing delivery, or external finance-system records.
- Do not imply that a financial handoff write path is admitted.

## Required Closeout Content

Your closeout must include:

1. status,
2. files read,
3. files written,
4. commands run,
5. upstream proof gates required before financial handoff can be admitted,
6. proposed financial handoff boundary model,
7. billing export design questions,
8. payroll export design questions,
9. invoice/accounting boundary design questions,
10. labor reconciliation and customer evidence reconciliation checks,
11. audit, readback, idempotency, replay, rollback, and exception-handling requirements,
12. explicit blocked boundaries,
13. recommended next packet,
14. explicit confirmation that no live approval, import, field, production, customer, billing, payroll, invoice, accounting, hosted, SQL, credential, macro, staging, commit, or push action occurred.

## Required Design Stance

The design must keep these truths intact:

- every route and status proposed for financial handoff remains `not_admitted`;
- approval first-row execution remains blocked until the exact PM Lane 142 phrase is provided;
- project import remains blocked until approval-row proof exists;
- field execution remains blocked until import and field authorization packets exist;
- production tracking remains blocked until durable field record and production tracking packets exist;
- customer reporting remains blocked until production tracking proof exists;
- financial handoff remains blocked until customer reporting and completion evidence proof exists;
- external finance-system sync, payroll processing, accounting posting, and invoice creation remain blocked until separately admitted.
- VS Code Codex review is required after the design closeout before any implementation, repo integration, live approval, import, financial handoff, hosted action, or write path.

## Validation

Run only read/check commands needed to support the closeout. At minimum:

```powershell
git diff --check -- "C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-pm-lane-158-financial-handoff-admission-design-executor-closeout.md"
```

If `git diff --check` against a new untracked closeout is not meaningful in your environment, state that plainly and validate with a direct file read plus `git status --short`.

## Stop Conditions

Stop with `ABORTED_SCOPE_WIDENING` if the task requires any product code edit, hosted access, credential use, SQL/schema work, macro execution, mutation endpoint call, approval/import/field/production/customer/finance write, staging, commit, push, or host fast-forward.

Stop with `BLOCKED_CAPABILITY_GAP` if you cannot inspect the required files or cannot produce the closeout without violating the guardrails.
