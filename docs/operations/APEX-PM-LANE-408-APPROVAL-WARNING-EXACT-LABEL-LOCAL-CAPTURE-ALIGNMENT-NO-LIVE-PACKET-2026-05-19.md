# PM Lane 408 - Approval Warning Exact-Label Local Capture Alignment No-Live Packet

Date: 2026-05-19
Status: Local executed, no-live
Scope: Record the exact PM Lane 238 Project Data Entry label inside browser-local approval-review state and carry that selected label through the no-live approval artifacts without implying warning acceptance or any live mutation admission.

## Trigger

After PM Lane 407, the import-intake workbench exported the full Project Data Entry exact-label decision contract, but it still did not capture which label PM had actually selected during local review.

That left a narrow but real truthfulness gap:

- the warning gate could describe the allowed labels,
- the exports could relay the full contract,
- but the local approval draft had no field for the selected exact label,
- and the completion checks still treated the draft as complete without that selection.

## Outcome

Selected outcome:

`PM_APPROVAL_WARNING_EXACT_LABEL_LOCAL_CAPTURE_ALIGNED_LOCAL_CURRENT`

The exact PM Lane 238 Project Data Entry label is now part of the existing browser-local approval decision draft and no-live export bundle chain.

## Change Surface

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
   - Extends `ApprovalDecisionDraft` with `project_data_entry_label`.
   - Requires that label only when `PROJECT_DATA_ENTRY_FORMULA_ERRORS` is present.
   - Adds the browser-local `Project Data Entry exact label` select to the approval draft UI.
   - Threads the selected label through:
     - approval packet preview
     - local approval submission dry run
     - dry-run readiness export
     - approval review bundle export
     - live-gate preflight export
     - downstream Markdown review packet sections
   - Keeps the warning gate no-live by distinguishing:
     - `requires_exact_pm_label`
     - `local_exact_pm_label_recorded_no_live`
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
   - Updates the local approval draft expectations for the added exact-label select.
   - Selects `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE`.
   - Proves the selected label is persisted in the touched JSON, Markdown, and local storage expectations.

## Validation

Commands and checks run:

```text
corepack pnpm --dir apps/operations-web typecheck
get_errors apps/operations-web/app/pm-review/import-intake/page.tsx
get_errors apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Validation result:

- operations-web typecheck: pass
- intake page diagnostics: no errors
- smoke spec diagnostics: no errors

The long Playwright import-intake smoke was not rerun for this closeout because the known later timeout at the field-execution-gate-design download step remains outside the touched exact-label-local-capture slice.

## Boundary

This lane does not:

1. accept the Project Data Entry warning,
2. write the selected label to any live backend surface,
3. create or mutate approval rows,
4. change backend mutation routes,
5. change schema or hosted services,
6. admit project import, assignment, schedule/status, field, production, customer, or finance writes,
7. modify source workbooks,
8. run workbook macros,
9. admit autonomous AI business-state mutation.

## Next Safe Move

The next bounded move is to decide whether the remaining blocker is another local truthfulness gap in the PM intake workbench or a separate no-live warning-handling tranche. This lane only makes the selected exact Project Data Entry label part of the truthful local review record and exported review context.
