# PM Lane 163 - Local Field Prep Output Subgrouping Handoff

## Summary

PM Lane 163 groups the existing Field Prep Outputs on `/pm-review/import-intake`.

The Field Prep Outputs rail had grown to 19 buttons. This lane keeps the same rail and the same 19 actions, but makes the screen easier to scan by grouping them into Field Prep Basics, Admission Drafts, and Pilot Launch Outputs. It does not create a new export, change a filename, change a payload, persist UI state, or open any live write path.

## What Changed

- Added `Field Prep Basics`, `Admission Drafts`, and `Pilot Launch Outputs` subgroups inside the existing `Field Prep Outputs` rail.
- Kept all 19 existing field-prep output buttons under the same top-level Field Prep Outputs section.
- Preserved all button labels, handlers, disabled states, filenames, payload versions, storage behavior, read seams, and export contents.
- Extended the focused PM import-intake smoke to prove subgroup visibility, subgroup counts, exact subgroup button labels, unchanged total button count, and existing zero-mutation behavior.

## Guardrails Preserved

- No new export action.
- No export handler change.
- No filename or payload version change.
- No new subgroup collapse, selection, favorite, or persisted UI localStorage key.
- No live POST to `/api/v1/mutations/project-import-approvals`.
- No approval row creation.
- No project import.
- No hosted deployment or promotion.
- No Supabase, Render, Vercel, or Olares action.
- No SQL/schema migration.
- No secret handling.
- No backend route or mutation route change.
- No workpackage, task, apparatus, field work authorization, lead assignment, crew assignment, owner assignment, due-date assignment, schedule/status write, durable field record write, production tracking write, customer reporting write, customer report write, customer completion evidence write, customer commitment, meeting note persistence, action item persistence, review-return persistence, financial handoff route, billing export write, payroll export write, invoice record write, payroll record write, accounting record write, labor reconciliation write, customer billing delivery, finance system integration, workbook macro, or workbook writeback.
- No Desktop Codex output is staged, merged, published, or deployed by this lane.
- No service/auth/DNS/ingress/control-plane widening.
- No autonomous AI business-state mutation.

## Sidecar Result

Read-only sidecar Hypatia reviewed the proposed PM Lane 163 shape while VS Code Codex retained technical authority and implementation responsibility. The sidecar recommended keeping all 19 actions in the existing Field Prep Outputs rail, with 6 Field Prep Basics actions, 8 Admission Draft actions, and 5 Pilot Launch Outputs actions, and warned against new handlers, filenames, payloads, storage keys, routes, persistence, or authority-implying labels.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
Get-Content -Path "ops/agents/packets/draft/2026-05-17-pm-lane-163-local-field-prep-output-subgrouping.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 163|Field prep output subgroups|Field Prep Basics|Admission Drafts|Pilot Launch Outputs|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- PASS.
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"`
- Packet JSON parse returned `2026-05-17-pm-lane-163`.
- PM Lane 163 guardrail scan returned expected code, docs, packet, handoff, subgroup, and zero-mutation references.
- `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended Lane

Keep PM live writes blocked. The next safe PM lane can continue local-only ergonomics around review-return use, consume Desktop Codex closeouts for VS Code Codex technical-authority review, or prepare explicit PM Lane 142 admission review context without creating approval rows, imports, assignments, schedule/status changes, review-return records, customer commitments, meeting records, or hosted writes.
