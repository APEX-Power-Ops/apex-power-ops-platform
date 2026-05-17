# PM Lane 160 - Local Pilot Launch Standup Card Export Handoff

## Summary

PM Lane 160 adds a local-only pilot launch standup card export to `/pm-review/import-intake`.

The export gives Jason a compact launch-day run card for the first PM, field lead, customer/site contact, and executor/AI relay conversation. It converts the PM Lane 159 daily brief into role-specific talk tracks, questions, no-go checks, capture prompts, next-packet options, and blocked write boundaries without opening any approval, import, field, production, customer, or financial write path.

## What Changed

- Added `Export Pilot Launch Standup Card` to the existing `Field Prep Outputs` rail.
- The export downloads `pm-import-candidate-miner-temp-power-pilot-launch-standup-card.json`.
- The JSON includes PM Lane 159 daily-brief lineage, launch-day summary, role cards, no-go checks, local capture prompts, next packet options, authority boundary flags, and blocked boundaries.
- The focused PM import-intake smoke now proves the downloaded standup card artifact and confirms `mutationRequests` remains `0`.
- The focused smoke timeout is now 60 seconds because the single comprehensive smoke validates all local PM output downloads.

## Guardrails Preserved

- No live POST to `/api/v1/mutations/project-import-approvals`.
- No approval row creation.
- No project import.
- No hosted deployment or promotion.
- No Supabase, Render, Vercel, or Olares action.
- No SQL/schema migration.
- No secret handling.
- No backend route or mutation route change.
- No workpackage, task, apparatus, field work authorization, assignment write, schedule/status write, durable field record write, production tracking write, customer reporting write, customer report write, customer completion evidence write, customer delivery, financial handoff route, billing export write, payroll export write, invoice record write, payroll record write, accounting record write, labor reconciliation write, customer billing delivery, finance system integration, workbook macro, or workbook writeback.
- No role card creates an assignment, field direction, customer commitment, meeting action item, or durable record.
- No service/auth/DNS/ingress/control-plane widening.
- No autonomous AI business-state mutation.

## Pilot Launch Still Blocked

This lane creates a standup card only. It does not create a launch action, approval control, batch submit, hosted control, import mutation, field authorization, production tracker, customer report, billing export, payroll export, invoice, accounting record, or finance-system sync.

The standup card keeps these no-go checks explicit:

1. approval live write is not admitted without the exact PM Lane 142 phrase,
2. project import is not admitted,
3. field direction and schedule/status mutation are not admitted,
4. customer and finance outputs are not admitted.

## Sidecar Result

Read-only sidecar Wegener recommended this as the smallest useful PM Lane 160. The sidecar confirmed that the role-based standup card reduces launch-day relay burden while preserving no-write authority, and listed red flags around implied approval, import, field direction, customer commitment, and finance authority. VS Code Codex kept implementation and final validation local.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
Get-Content -Path "ops/agents/packets/draft/2026-05-17-pm-lane-160-local-pilot-launch-standup-card-export.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 160|Export Pilot Launch Standup Card|pilot-launch-standup-card|pm_lane_160_local_pilot_launch_standup_card_v1|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- PASS.
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"`
- Packet JSON parse returned `2026-05-17-pm-lane-160`.
- PM Lane 160 guardrail scan returned expected code, docs, packet, handoff, and zero-mutation references.
- `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended Lane

Review the Desktop Codex PM Lane 158 closeout when returned. If it is not yet returned and live approval remains unadmitted, the next safe PM lane can continue reducing launch meeting capture burden with local-only artifacts or prepare explicit PM Lane 142 admission review context without opening the live write.
