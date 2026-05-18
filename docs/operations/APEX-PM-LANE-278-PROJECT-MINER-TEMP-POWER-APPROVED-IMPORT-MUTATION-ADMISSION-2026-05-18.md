# PM Lane 278 - Project Miner Temp Power Approved Import Mutation Admission

Date: 2026-05-18

Authority: VS Code Codex technical repo authority plus current stakeholder/PM standing blocker authority from Jason on 2026-05-18

Decision label:

`PROJECT_MINER_TEMP_POWER_APPROVED_IMPORT_MUTATION_ADMISSION`

Selected outcome:

`APPROVED_IMPORT_MUTATION_ROUTE_ADMITTED_WITH_DOWNSTREAM_STOPS`

## Purpose

PM Lane 278 clears the next blocker after PM Lane 277's first approval row:

`STOPPED_AWAITING_PROJECT_IMPORT_MUTATION_PACKET_AFTER_APPROVAL_ROW`

This packet admits the narrow Project Miner Temp Power import mutation route and local implementation needed to persist the approved import candidate into governed PM execution rows.

## Source Floor

Source commit:

`153ad3148a9e7649a77f20123a5fede10031e974`

Prior state:

1. hosted Temp Power candidate is current,
2. approval status is `approved_for_import_packet`,
3. approval row count is `1`,
4. approval record is `pm-import-approval-03a1aea39afde71b44516f44`,
5. `import_authority` on the approval status remains `not_admitted`,
6. no project, workpackage, task, apparatus, assignment, field, schedule/status, customer, production, or finance import has been performed.

## Admitted Route

This packet admits:

`POST /api/v1/mutations/project-imports`

Entity type:

`pm_import`

Action type:

`persist_project_import`

The route must require:

1. PM actor,
2. online source,
3. mutation class `C`,
4. exactly one current approval row,
5. `approved_for_import_packet`,
6. current candidate match,
7. matching candidate id, version, source fingerprint, shape fingerprint, approval record id, idempotency key, accepted warning codes, and accepted human-acceptance checks.

## Admitted Writes

Only these existing seam execution stores may be written:

1. `seam.projects`,
2. `seam.workpackages`,
3. `seam.tasks`,
4. `seam.apparatus`,
5. `seam.audit_log`,
6. `seam.idempotency_keys`.

The Temp Power import writes deterministic row ids under:

`pm-import-project-miner-temp-power`

Expected hosted Temp Power import shape:

| Surface | Count |
| --- | ---: |
| projects | 1 |
| workpackages | 7 |
| tasks | 15 |
| apparatus | 184 |
| source trace entries | 199 |
| warning review entries | 1 |

Source trace evidence is embedded on imported task and apparatus rows. Warning-review evidence is embedded on the imported project row. No new source-trace or warning-review table is admitted in this packet.

## Not Admitted

This packet does not admit:

1. schema migration,
2. direct SQL writes,
3. assignments,
4. field authorization,
5. lead or crew selection,
6. schedule/status mutation,
7. durable field records,
8. production tracking,
9. customer reporting,
10. billing, payroll, invoice, accounting, or external finance-system output,
11. source workbook/PDF edit or writeback,
12. workbook macro execution,
13. Render/Vercel/Olares/DNS/auth/ingress/new-service change from this shell,
14. secret exposure,
15. autonomous AI business-state mutation.

## Required Validation

Local validation must prove:

1. import route rejects when no approval row exists,
2. approval-row-backed import writes deterministic project/workpackage/task/apparatus rows,
3. same-payload replay returns `idempotent_hit`,
4. mismatched replay is rejected,
5. non-PM, offline, and wrong-class requests are rejected,
6. import status readback returns `imported` after accepted import,
7. assignment, snapshot, issue, and hour surfaces remain unchanged.

Hosted execution remains a separate post-deploy proof step. The route must not be called on hosted production until the newly committed route is deployed and preflight readbacks still match the PM Lane 277 approval identity.
