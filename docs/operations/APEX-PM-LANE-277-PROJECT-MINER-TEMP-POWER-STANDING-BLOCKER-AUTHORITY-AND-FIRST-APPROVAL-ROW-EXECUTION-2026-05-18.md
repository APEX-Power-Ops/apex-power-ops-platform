# PM Lane 277 - Project Miner Temp Power Standing Blocker Authority And First Approval Row Execution

Date: 2026-05-18

Authority: VS Code Codex technical repo authority plus current stakeholder/PM authority from Jason on 2026-05-18

Decision label:

`PROJECT_MINER_TEMP_POWER_STANDING_BLOCKER_AUTHORITY_AND_FIRST_APPROVAL_ROW_EXECUTION`

Selected outcome:

`STANDING_PM_BLOCKER_AUTHORITY_ADMITS_FIRST_APPROVAL_ROW_NO_IMPORT`

## Purpose

PM Lane 277 records Jason's current instruction to move forward with authority for PM-lane blocker approvals along the predetermined framework without pausing for a separate approval turn at each step.

This packet admits only the next narrow live write in that framework: the first approval-record persistence row for the current hosted Project Miner Temp Power import candidate.

## Stakeholder Authority

Jason's current instruction grants Codex authority to approve PM-lane blocker items and continue through the predetermined PM framework/path end-to-end as repo technical authority and project stakeholder.

For this packet, that authority is narrowed to:

1. accept `PROJECT_DATA_ENTRY_FORMULA_ERRORS` as the reviewed non-blocking warning for approval-record context,
2. acknowledge the `warnings-reviewed-by-pm` human-acceptance check,
3. submit the PM approval decision `approve_for_import_packet`,
4. create exactly one approval record for the current hosted Temp Power candidate,
5. perform one same-payload idempotent replay,
6. prove approval-status readback,
7. prove downstream PM execution/import surfaces remain unchanged and not admitted.

## Hosted Preflight

The required hosted preflight before execution is:

1. deployed mutation-seam smoke with PM intake returns `RESULT PASS`,
2. operations-web hosted smoke returns `SMOKE_SUMMARY failed=0`,
3. paired hosted PM intake smoke returns `PM_INTAKE_HOSTED_SUMMARY failed=0`,
4. hosted candidate readback returns `pm-import-candidate-miner-temp-power`,
5. candidate shape is 7 workpackages, 15 tasks, 184 apparatus candidates, zero blockers, one warning,
6. source fingerprint is `e111fdbe934bf9de07ed24c1`,
7. shape fingerprint is `ddc49565eb586af913ad48b2`,
8. approval status before write is `no_approval_record` with `approval_record_count_for_candidate=0`.

## Admitted Write

Only this write is admitted:

`POST /api/v1/mutations/project-import-approvals`

Target entity:

`pm_import_candidate_approval`

Target table:

`seam.pm_import_candidate_approvals`

Decision:

`approve_for_import_packet`

The approval record is approval evidence for a later import packet only. It does not import projects, workpackages, tasks, apparatus, source traces, warning-review rows, field records, assignments, schedules, statuses, production tracking, customer reports, finance outputs, or workbook changes.

## Expected Payload

The execution payload must be built from the hosted approval contract:

| Field | Expected value |
| --- | --- |
| `candidate_id` | `pm-import-candidate-miner-temp-power` |
| `candidate_version` | `pm_import_candidate_read_only_v1` |
| `source_stat_fingerprint` | `e111fdbe934bf9de07ed24c1` |
| `candidate_shape_fingerprint` | `ddc49565eb586af913ad48b2` |
| `idempotency_key` | `pm-import:a2acafe8e9928899e8645736` |
| `decision` | `approve_for_import_packet` |
| `accepted_warning_codes` | `["PROJECT_DATA_ENTRY_FORMULA_ERRORS"]` |
| `accepted_no_go_overrides` | `["warnings-reviewed-by-pm"]` |

Review notes:

`Stakeholder/PM authority on 2026-05-18 admits first approval-row persistence for the current Temp Power candidate, accepts PROJECT_DATA_ENTRY_FORMULA_ERRORS as reviewed non-blocking warning context for a later import packet, and keeps project import plus downstream field/schedule/resource/customer/production/finance writes blocked.`

## Required Execution Proof

1. pre-write hosted readback,
2. downstream count snapshot before write,
3. first POST response `status=accepted`,
4. first POST response `entity_type=pm_import_candidate_approval`,
5. first POST response `action_type=persist_import_approval`,
6. first POST response `new_state.import_authority=not_admitted`,
7. same-payload replay response `status=idempotent_hit`,
8. replay does not create a second row,
9. approval-status readback returns `approved_for_import_packet`,
10. approval-status row count is `1`,
11. downstream accessible counts remain unchanged,
12. project import remains blocked.

## Not Admitted

This packet does not admit:

1. project import,
2. workpackage/task/apparatus/source-trace/warning-review import rows,
3. assignment, field authorization, lead/crew selection, schedule/status mutation, durable field record, production tracking, customer report, completion evidence, billing, payroll, invoice, accounting, or external finance-system output,
4. direct SQL insertion for the approval row,
5. schema migration,
6. Render, Vercel, Supabase, Olares, DNS, auth, ingress, or new service change,
7. source workbook/PDF content edit or writeback,
8. workbook macros,
9. secret exposure,
10. autonomous AI business-state mutation.

## Closeout

After execution, create a closeout with exact hosted evidence, response summary, replay proof, approval-status readback, unchanged downstream proof, guardrail confirmation, and the next blocker classification.
