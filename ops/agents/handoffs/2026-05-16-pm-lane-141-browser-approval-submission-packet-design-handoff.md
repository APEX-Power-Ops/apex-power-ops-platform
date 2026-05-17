# PM Lane 141 - Browser Approval Submission Packet Design Handoff

## Purpose

PM Lane 141 authors the bridge between the current read-only PM intake workbench and a later explicitly admitted browser approval submission lane.

This lane is design and packet-authoring only. It defines the future browser approval submission contract, confirmation copy, response handling, idempotent replay behavior, status-readback proof, and first approval-row execution gate. It does not send a live approval POST, wire a browser approval button, or create the first approval row.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `bbe1bfc83d93fac4edbb6594aeaf7ac674a01086`
- Prior local lane: PM Lane 140, Approval Readiness State Reconciliation
- Prior hosted gate: PM Lane 138, Approval Persistence Hosted Application Gate
- Prior smoke/closeout lane: PM Lane 139, Hosted Gate Smoke And Closeout Contract Tightening

## Implemented Scope

- Authored `PM Lane 141 - Browser Approval Submission Packet Design`.
- Captured the exact future approval persistence route and table:
  - `POST /api/v1/mutations/project-import-approvals`
  - `seam.pm_import_candidate_approvals`
- Defined the future mutation envelope requirements:
  - `mutation_class: C`
  - `action_type: persist_import_approval`
  - `source: online`
  - envelope `idempotency_key` must match `payload.idempotency_key`
  - optional `entity_id` must match the deterministic approval record id if supplied.
- Defined the future payload fields:
  - `candidate_id`
  - `candidate_version`
  - `source_stat_fingerprint`
  - `candidate_shape_fingerprint`
  - `idempotency_key`
  - `decision`
  - `approved_by_actor_id`
  - `approved_at_utc`
  - `accepted_warning_codes`
  - `accepted_no_go_overrides`
  - `review_notes`
- Defined the future UI confirmation requirements, success evidence, readback requirements, failure handling, and first approval-row execution gate.

## Files Changed

- `PROJECT_STATUS.md`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-141-browser-approval-submission-packet-design.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-141-browser-approval-submission-packet-design-handoff.md`

## Not Allowed

- No browser approval button.
- No browser approval POST wiring.
- No live approval POST.
- No approval row creation.
- No project import mutation.
- No project, workpackage, task, apparatus, issue, assignment, schedule, status, durable field record, production tracking, workbook, or import rows.
- No app product code changes in this design lane.
- No live Supabase SQL application or schema migration.
- No Render, Vercel, Olares, or Supabase action.
- No secret access, secret print, secret rotation, or secret storage in repo.
- No workbook macro execution or workbook writeback.
- No service creation, DNS/auth/ingress change, fixture replay into live data, work authorization, field release, live work order creation, or autonomous AI business-state mutation.

## Future Browser Submission Design

The future browser submission must remain a narrow approval-record persistence action, not an import action.

Required confirmation copy:

- The PM is persisting only the import-candidate approval decision.
- The approval record does not import project, workpackage, task, or apparatus rows.
- The approval record does not assign work, change schedules, change status, create field records, create work orders, or write production tracking.
- Project import remains blocked until a separate packet admits that mutation after the approval record exists.

Required future success evidence:

- `POST /api/v1/mutations/project-import-approvals` returns `200`.
- Response status is `accepted` for the first admitted row or `idempotent_hit` for a same-payload replay.
- Response `entity_type` is `pm_import_candidate_approval`.
- Response `action_type` is `persist_import_approval`.
- Response `new_state.import_authority` remains `not_admitted`.
- Approval status readback returns the expected classification for the same candidate.
- Approval record count is `1` after the admitted first-row lane, or stays `1` after idempotent replay.
- Project, workpackage, task, apparatus, assignment, schedule, status, durable field record, and production tracking counts remain unchanged.

Required future failure handling:

- Stale candidate/source/shape/idempotency values return the PM to source review.
- Warning-code mismatches require renewed warning acceptance.
- Missing or mismatched human-acceptance no-go acknowledgements block submission.
- Unsupported decisions and empty review notes block submission.
- Idempotency duplicate with mismatched payload is a blocker.
- Storage-unavailable approval readback blocks project import.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
Get-Content -Path "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-141-browser-approval-submission-packet-design.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 141|No live approval POST|No approval row|not_admitted|Browser Approval Submission Packet Design" PROJECT_STATUS.md docs/operations ops/agents
git diff --check
git diff --cached --check
```

## Validation Results

- Packet JSON parsed with PowerShell `ConvertFrom-Json`.
- Guardrail/status search returned PM Lane 141, no-live-POST, no-approval-row, `not_admitted`, and Browser Approval Submission Packet Design references.
- Scoped `git diff --check` passed.

## Sidecar Result

The read-only sidecar recommended `PM Lane 141 - Browser Approval Submission Packet Design`.

It confirmed that the next safe lane is a design and packet-authoring lane, not the live approval submission. It also recommended the separate future execution gate for first approval-row creation.

## Next Recommended Lane

`PM Lane 142 - Browser Approval Submission First-Row Execution Gate`

That lane must be explicitly admitted before any browser approval control sends `POST /api/v1/mutations/project-import-approvals` or creates the first hosted approval row. It should own the live POST evidence, idempotent replay evidence, approval-status readback, unchanged downstream domain counts, failure handling, and the decision about whether the UI control remains enabled only for PM actors.
