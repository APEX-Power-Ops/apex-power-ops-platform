# PM Lane 185 - Current PM Next Actions And Guardrails Grouping Handoff

## Summary

PM Lane 185 groups the existing Current PM Next Actions and Guardrails footer on `/pm-review/import-intake`.

The footer already held two read-only authority cards: Current PM Next Actions and Not Allowed Now. This lane keeps the `#guardrails` anchor, footer heading, default-open disclosure behavior, body/control wrappers, two existing cards, action list text/order, not-allowed fallback rendering, route/quick-jump behavior, no-disclosure-storage posture, and no-write authority boundary, but groups the two cards into Current Review Actions and Blocked Write Guardrails.

## Implementation

- Added `Current Review Actions` and `Blocked Write Guardrails` groups inside the existing Current PM guardrails controls.
- Preserved the existing details/summary behavior, `#guardrails` anchor, footer heading, body/control wrappers, two guardrail cards, action list, not-allowed list, fallback rendering, route/quick-jump behavior, and no-storage disclosure posture.
- Preserved read-only authority wording and the no approval/import/field/production/finance write boundary.
- Added focused smoke assertions for guardrail group visibility, two group sections, 1/1 article distribution, preserved two total article count, collapse/reopen behavior, no guardrails disclosure/localStorage state, preserved next-action and not-allowed text, and existing zero-mutation guard.

## Guardrails Preserved

- No hosted service access.
- No Supabase, Render, Vercel, or Olares product action.
- No SQL or schema migration.
- No browser approval button, approval POST wiring, approval submission, or approval-row creation.
- No project import mutation.
- No field authorization, assignment, schedule/status write, durable field record, production tracking, customer report, completion evidence, billing, payroll, invoice, accounting, or external finance-system write.
- No workbook macro or writeback.
- No new export action, handler, filename, payload version, localStorage key, backend route, service/auth/ingress change, or autonomous AI business-state mutation.

## Dual-Lane Use

Read-only sidecar Locke reviewed the Lane 185 shape while VS Code Codex implemented the PM lane and retained PM lane implementation authority plus final integration authority.

The sidecar recommended grouping the existing two footer cards into Current Review Actions and Blocked Write Guardrails while preserving `details#guardrails`, the summary heading, body/control wrappers, card wording/order, not-allowed fallback rendering, quick-jump target, no-storage posture, and mutation boundary. That grouping recommendation was accepted.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
Get-Content -LiteralPath "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-17-pm-lane-185-current-pm-next-actions-guardrails-grouping.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 185|Current PM guardrail groups|Current Review Actions guardrail group|Blocked Write Guardrails guardrail group|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- PASS - operations-web typecheck passed.
- PASS - focused Playwright pm import-intake smoke passed.
- PASS - operations-web build passed.
- PASS - packet JSON parsed as `2026-05-17-pm-lane-185`.
- PASS - PM Lane 185 guardrail `rg` found the expected status, docs, packet, handoff, UI grouping, smoke grouping, and zero-mutation evidence.
- PASS - `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended PM Move

Run a focused PM intake workbench visual QA and mobile scan before opening any write path. The grouped local workbench now has many folded and grouped surfaces; the next safe tranche is a viewport/readability proof and any small layout-only correction required by that proof. Browser approval submission, first approval-row creation, project import, field authorization, assignment, schedule/status, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked until separately admitted.
