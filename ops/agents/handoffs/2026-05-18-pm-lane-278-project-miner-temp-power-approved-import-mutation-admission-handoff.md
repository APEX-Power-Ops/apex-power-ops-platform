# PM Lane 278 - Approved Import Mutation Admission Handoff

## Purpose

PM Lane 278 clears the next blocker after PM Lane 277:

`STOPPED_AWAITING_PROJECT_IMPORT_MUTATION_PACKET_AFTER_APPROVAL_ROW`

This lane admits and implements the narrow Project Miner Temp Power import mutation route. It writes only the approved candidate into governed project, workpackage, task, and apparatus rows and keeps downstream PM business-state paths closed.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `153ad3148a9e7649a77f20123a5fede10031e974`
- Prior lane: PM Lane 277 first approval row complete

## Admitted Execution

Route:

`POST /api/v1/mutations/project-imports`

Entity/action:

`pm_import` / `persist_project_import`

Required approval state:

- classification: `approved_for_import_packet`
- approval row count: `1`
- current candidate match: `true`
- approval record: `pm-import-approval-03a1aea39afde71b44516f44`

Expected candidate identity:

- candidate: `pm-import-candidate-miner-temp-power`
- candidate version: `pm_import_candidate_read_only_v1`
- source fingerprint: `e111fdbe934bf9de07ed24c1`
- shape fingerprint: `ddc49565eb586af913ad48b2`
- idempotency key: `pm-import:a2acafe8e9928899e8645736`
- accepted warning codes: `PROJECT_DATA_ENTRY_FORMULA_ERRORS`
- accepted no-go overrides: `warnings-reviewed-by-pm`

## Row Boundary

The route may write only:

1. one project row,
2. seven workpackage rows,
3. fifteen task rows,
4. 184 apparatus rows,
5. one audit event,
6. one idempotency cache entry.

Source traces are embedded on task/apparatus rows. Warning review is embedded on the imported project row. No source-trace table, warning-review table, schema migration, direct SQL, or downstream mutation is admitted.

## Required Proof

1. no-approval import rejection,
2. accepted import with deterministic row counts,
3. same-payload replay returns `idempotent_hit`,
4. mismatched replay rejects,
5. non-PM/offline/wrong-class gates reject,
6. import-status readback returns `imported`,
7. assignment, snapshot, issue, and hour counts remain unchanged.

## Hosted Note

Before PM Lane 278 code is deployed, hosted `POST /api/v1/mutations/project-imports` should return `404`. Hosted live import is allowed only after the route is deployed and preflight readbacks still match the PM Lane 277 approval identity.

## Guardrails

No assignment, field authorization, lead/crew selection, schedule/status mutation, durable field record, production tracking, customer report, completion evidence, billing, payroll, invoice, accounting, external finance-system output, source workbook/PDF edit or writeback, workbook macro, direct SQL, schema migration, hosted deploy from this shell, new service, auth/ingress/DNS change, secret exposure, Desktop Codex PM decision authority, or autonomous AI business-state mutation is admitted.
