# PM Lane 407 - Approval Warning Exact-Label Contract Export Alignment No-Live Packet

Date: 2026-05-19
Status: Local executed, no-live
Scope: Carry the full Project Data Entry exact-label warning contract into the browser-local approval JSON artifacts so later review/handoff context no longer has to infer it from Markdown-only surfaces.

## Trigger

After PM Lane 406, the import authority surfaces named the real current blocker state correctly, but the approval JSON artifacts still exposed the Project Data Entry warning gate mostly as compact status metadata:

- `disposition_status`
- `allowed_labels`
- `admission_prerequisites`
- `next_input_needed`
- `source_correction_boundary`

That was enough to prove the warning was unresolved, but it still omitted the rest of the exact decision contract already present in the exception-detail and Markdown exports:

- outcome routes
- valid return checklist
- safe no-live continuation moves

## Outcome

Selected outcome:

`PM_APPROVAL_WARNING_EXACT_LABEL_CONTRACT_EXPORTED_LOCAL_CURRENT`

The shared warning gate object now carries the full no-live exact-label contract, so the local approval preview and relay artifacts can stand alone without losing the exact PM label rules.

## Change Surface

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
   - Extends `projectDataEntryWarningDispositionGate(...)` with:
     - `outcome_routes`
     - `valid_return_checklist`
     - `safe_no_live_continuation_moves`
   - Leaves the existing no-live authority boundary, allowed labels, next-input rule, and source-correction boundary unchanged.
   - Because the following exports already embed the shared gate object, they inherit the added contract automatically:
     - approval packet preview
     - local approval dry-run envelope
     - dry-run readiness export
     - approval review bundle
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
   - Extends focused JSON expectations so the touched exports prove the exact-label contract now includes outcome-route, valid-return, and safe-continuation details.

## Validation

Commands run:

```text
corepack pnpm --dir apps/operations-web typecheck
```

Validation result:

- operations-web typecheck: pass

The long Playwright import-intake smoke remains known to time out later in its existing field-execution-gate-design download step, so this lane records no new hosted or end-to-end runtime claim from that suite.

## Boundary

This lane does not:

1. admit warning acceptance,
2. choose a PM Lane 238 label,
3. add a new UI panel or export button,
4. change backend mutation routes,
5. create or mutate approval rows,
6. change schema or hosted services,
7. admit project import, assignment, schedule/status, field, production, customer, or finance writes,
8. modify source workbooks,
9. run workbook macros,
10. admit autonomous AI business-state mutation.

## Next Safe Move

The next bounded move is still the actual PM warning disposition lane: record exactly one PM Lane 238 Data Entry label in no-live decision context, or keep the warning unresolved while continuing no-live review only. This lane only ensures the exported approval artifacts now carry the full exact-label contract needed for that later decision.