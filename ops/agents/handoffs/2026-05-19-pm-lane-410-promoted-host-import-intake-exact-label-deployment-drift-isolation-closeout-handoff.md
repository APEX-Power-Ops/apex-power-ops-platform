# PM Lane 410 - Promoted-Host Import-Intake Exact-Label Deployment Drift Isolation Closeout Handoff

## Outcome

Executed PM Lane 410 as the promoted-host import-intake exact-label deployment-drift isolation tranche.

Selected outcome: `PM_IMPORT_INTAKE_EXACT_LABEL_DEPLOYMENT_DRIFT_ISOLATED`

The next promoted-host PM failure is no longer a route publication issue, no longer a live-data seam issue, and no longer a control-plane payload-shape issue. The promoted host is serving an older `/pm-review/import-intake` browser contract than the current workspace code: under the same mocked intake reads, the local browser build still renders the Project Data Entry exact-label branch, while the promoted host does not.

## Change Surface

Product files changed:

- `apps/operations-web/scripts/smoke-promoted-host.mjs`

Repo governance files changed:

- `PROJECT_STATUS.md`
- `ops/agents/handoffs/2026-05-19-pm-lane-410-promoted-host-import-intake-exact-label-deployment-drift-isolation-closeout-handoff.md`

## Validation

Focused validation passed:

```text
corepack pnpm --dir . --filter @apex/operations-web smoke:hosted -- --base-url https://operations.apexpowerops.com
SMOKE_SUMMARY failed=0 passed=29

corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts -g "captures the exact Project Data Entry label in local approval artifacts"
1 passed
```

Promoted-host validation isolated the hosted-only drift:

```text
corepack pnpm --dir . --filter @apex/operations-web smoke:promoted-host -- --operations-web-base-url https://operations.apexpowerops.com --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks
PROMOTED_HOST_STEP backend-seam ... RESULT PASS
PROMOTED_HOST_STEP hosted-routes ... SMOKE_SUMMARY failed=0 passed=29
PROMOTED_HOST_STEP browser-smoke ... 5 failed
```

The hosted-only single-test repro failed against the promoted host:

```text
$env:OPERATIONS_WEB_BROWSER_SMOKE_BASE_URL='https://operations.apexpowerops.com'
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts -g "captures the exact Project Data Entry label in local approval artifacts" --trace on
1 failed
```

Hosted failure evidence showed the stale UI branch clearly:

- the current repo test helper still mocks `PROJECT_DATA_ENTRY_FORMULA_ERRORS`
- local current code renders and passes the exact-label workflow
- hosted failure snapshot showed `Local decision draft has partial browser-local context; confirm the missing decision, notes, or local-only attestation.` instead of the current exact-label wording, proving the promoted host is serving an older import-intake browser contract

## Boundary

- No mutation-seam or control-plane schema/read-shape fix was required.
- No import-intake route publication fix was required.
- No PM live-data regression reopened.
- No hosted redeploy was performed in this packet.
- No live approval, import, assignment, schedule/status, field, production, customer, or finance write admission.
- No autonomous AI business-state mutation.

## Next Branch Set

The next bounded PM move should target hosted operations-web deployment parity for `/pm-review/import-intake`.

- Verify which deployment commit is currently serving `https://operations.apexpowerops.com` for the import-intake route.
- Promote or redeploy the current operations-web build that includes the exact-label branch already present in the workspace.
- Rerun the single hosted import-intake exact-label Playwright test first.
- Then rerun `smoke:promoted-host` end to end to confirm the hosted browser slice clears.