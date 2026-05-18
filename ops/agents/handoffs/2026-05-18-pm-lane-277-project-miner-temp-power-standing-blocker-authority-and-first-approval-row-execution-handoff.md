# PM Lane 277 - Standing Blocker Authority And First Approval Row Execution Handoff

## Purpose

PM Lane 277 records Jason's current stakeholder authority to move through PM-lane blocker approvals along the predetermined framework without separate approval turns for every blocker, then narrows that authority to the next live PM action: first approval-record persistence for the hosted Temp Power import candidate.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `646a56824773a2908b435874b0da8147fb5ce5e9`
- Prior lane: PM Lane 276 Render executor return accepted

## Admitted Execution

Only this live write is admitted:

`POST /api/v1/mutations/project-import-approvals`

Decision:

`approve_for_import_packet`

Payload identity:

- candidate: `pm-import-candidate-miner-temp-power`
- candidate version: `pm_import_candidate_read_only_v1`
- source fingerprint: `e111fdbe934bf9de07ed24c1`
- shape fingerprint: `ddc49565eb586af913ad48b2`
- idempotency key: `pm-import:a2acafe8e9928899e8645736`
- accepted warning codes: `PROJECT_DATA_ENTRY_FORMULA_ERRORS`
- accepted no-go overrides: `warnings-reviewed-by-pm`

## Required Proof

1. hosted mutation-seam and operations-web smokes are green,
2. candidate/status preflight matches the expected Temp Power candidate and zero approval rows,
3. exactly one first approval POST returns `accepted`,
4. exactly one same-payload replay returns `idempotent_hit`,
5. approval-status readback returns `approved_for_import_packet` with one row,
6. downstream accessible counts remain unchanged,
7. project import remains blocked.

## Guardrails

No project import, source trace import, warning-review import, workpackage/task/apparatus import, assignment, field authorization, lead/crew selection, schedule/status mutation, durable field record, production tracking, customer report, completion evidence, billing, payroll, invoice, accounting, external finance-system output, source workbook/PDF edit or writeback, workbook macro, direct SQL approval-row insert, schema migration, hosted deploy, new service, auth/ingress/DNS change, secret exposure, Desktop Codex PM decision authority, or autonomous AI business-state mutation is admitted.

## Next

After closeout, the next PM blocker should be classified from live evidence. If the approval row is accepted and replay-safe, the expected next blocker is project import packet admission, not another approval-row prompt.
