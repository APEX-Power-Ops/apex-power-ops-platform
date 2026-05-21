# PM Lane 406 - Import Mutation Authority Readiness-Detail Alignment No-Live Packet

Date: 2026-05-19
Status: Local executed, no-live
Scope: Align the PM import-intake import-authority detail with the real admission-plan readiness state so the next required review step is named truthfully without widening write authority.

## Trigger

After confirming that `MISSING_SLD_PDF` is not a real current warning under the default planning-root discovery path, the next remaining warning/blocker surface was the project import authority boundary.

Focused readback showed a mismatch in how that boundary was explained:

- the real admission plan for the live candidate returns `readiness_status: needs_human_acceptance_before_import_packet`
- the same plan returns one active review item, `warnings-reviewed-by-pm`
- the same plan still returns `mutation_authority: not_admitted`
- several import-intake UI surfaces were still rendering generic later-packet blocker copy instead of naming that current readiness state

## Outcome

Selected outcome:

`PM_IMPORT_MUTATION_AUTHORITY_READINESS_DETAIL_ALIGNED_LOCAL_CURRENT`

The workbench keeps project import blocked, but it now explains the real current posture: warning acceptance is the live review item, while import mutation authority remains not admitted.

## Change Surface

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
   - Adds a shared helper that derives import-authority detail from `admissionPlan.readiness_status` plus the relevant `no_go_checks`.
   - Updates the import mutation authority card in Approval Persistence Readiness to use that derived detail.
   - Updates the project import gate detail in the field-start preflight/export path to use that same derived detail.
   - Updates the project import authority detail in the Pilot Launch Binder export path to use that same derived detail.
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
   - Updates focused expectations so the readiness and handoff/export assertions expect the admission-plan-specific wording instead of the old generic blocker sentence.

## Validation

Commands run:

```text
corepack pnpm --dir apps/operations-web typecheck
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Validation result:

- operations-web typecheck: pass
- focused import-intake Playwright smoke: advanced past the touched import-detail assertions, then hit the existing later timeout at the `Export Field Execution Gate Design` download step in the same long test; no assertion failure occurred on the touched import-detail strings

## Boundary

This lane does not:

1. admit project import,
2. change backend mutation routes,
3. create or mutate approval rows,
4. change schema, payload, or hosted services,
5. widen assignment, schedule/status, field, production, customer, or finance authority,
6. modify source workbooks,
7. run workbook macros,
8. claim hosted validation beyond the local read-only UI/typecheck boundary,
9. admit autonomous AI business-state mutation.

## Next Safe Move

The next bounded move remains one of two paths:

1. resolve or explicitly accept `PROJECT_DATA_ENTRY_FORMULA_ERRORS` in the later approval record lane, or
2. admit a separate later import packet after approval-record proof exists.

This lane only makes the current blocker explanation truthful; it does not open the blocked import path.