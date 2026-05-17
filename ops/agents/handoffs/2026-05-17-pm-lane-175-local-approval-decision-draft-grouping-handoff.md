# PM Lane 175 - Local Approval Decision Draft Grouping Handoff

## Summary

PM Lane 175 groups the existing Local Approval Decision Draft panel on `/pm-review/import-intake`.

The panel already held three browser-local review-prep controls: Decision draft, Review notes draft, and Local-only draft attestation. This lane keeps those same controls, candidate-scoped browser storage, update behavior, clear button behavior, PM brief/export inclusion, approval preview export inclusion, disclosure behavior, no-disclosure-storage posture, and no-write boundary, but groups them into Decision Value Context, Review Notes Context, and Local Attestation Context so Jason can scan the local decision value separately from review notes and the local-only boundary acknowledgement.

## Implementation

- Added `Decision Value Context`, `Review Notes Context`, and `Local Attestation Context` groups inside the existing Local Approval Decision Draft controls.
- Preserved the existing `Decision draft` select, permitted decision source, `Review notes draft` textarea, and `Local-only draft attestation` checkbox.
- Preserved candidate-scoped browser storage, clear decision draft behavior, export inclusion, disclosure behavior, no-disclosure-storage posture, and no-authority wording.
- Added focused smoke assertions for approval decision draft group visibility, three group sections, one label in each group, one select, one textarea, one attestation checkbox, collapse/reopen behavior, no approval-draft disclosure/localStorage state, and the existing zero-mutation guard.

## Guardrails Preserved

- No hosted service access.
- No Supabase, Render, Vercel, or Olares product action.
- No SQL or schema migration.
- No approval POST or approval-row creation.
- No project import mutation.
- No field authorization, assignment, schedule/status write, durable field record, production tracking, customer report, completion evidence, billing, payroll, invoice, accounting, or external finance-system write.
- No workbook macro or writeback.
- No new export action, handler, filename, payload version, localStorage key, backend route, service/auth/ingress change, or autonomous AI business-state mutation.

## Dual-Lane Use

Read-only sidecar Kierkegaard reviewed the Lane 175 shape while VS Code Codex implemented the PM lane and retained PM lane implementation authority plus final integration authority.

The sidecar recommended preserving the existing outer disclosure, state shape, storage key, export builders, clear handler, permitted decision source, no-disclosure-storage behavior, and zero-mutation boundary. It suggested a two-group option; VS Code Codex chose three single-purpose context groups to match the current PM grouping pattern and make each local approval-draft control independently scannable.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
Get-Content -LiteralPath "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-17-pm-lane-175-local-approval-decision-draft-grouping.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 175|Approval decision draft groups|Decision Value Context approval draft group|Review Notes Context approval draft group|Local Attestation Context approval draft group|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- operations-web typecheck passed.
- focused Playwright PM import-intake smoke passed.
- operations-web build passed.
- packet JSON parsed.
- PM Lane 175 guardrail scan returned expected code, docs, packet, handoff, approval draft group, and zero-mutation references.
- `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended PM Move

Continue local PM usability work before opening any write path. The next safe tranche is grouping the next approval-prep surface, likely Local Approval Submission Dry Run, while preserving its dry-run envelope behavior, local-only review posture, export inclusion, no request behavior, no-disclosure-storage posture, and no-write boundary. Browser approval submission, first approval-row creation, project import, field authorization, assignment, schedule/status, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked until separately admitted.
