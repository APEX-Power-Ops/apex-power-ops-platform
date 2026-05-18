# PM Lane 278 - Render Project Import Route Deploy And Live Import Executor Prompt

Status: Superseded by VS Code Codex live execution on 2026-05-18.

Do not execute this prompt unless a later coordinator explicitly asks for replay-only evidence or recovery. The hosted route deployed after publication, the live import POST returned `accepted`, same-payload replay returned `idempotent_hit`, and import-status readback returned `imported`.

You are the authenticated Render executor for PM Lane 278.

## Role

Use authenticated Render/browser access to deploy the existing mutation-seam service to the published clean-main commit and execute the newly admitted Project Miner Temp Power import route only if all hosted preflight checks still match.

You are an executor only. VS Code Codex remains repo technical authority.

## Source Floor

Repo: `C:/APEX Platform/apex-power-ops-platform`

Branch: `clean-main`

Required commit already pushed:

`4d5af24f`

Commit title:

`Admit PM Lane 278 import route`

## Objective

Deploy the existing hosted mutation-seam service so these routes exist:

1. `POST /api/v1/mutations/project-imports`
2. `GET /api/v1/reads/project-import-status`

Then, if preflight still matches, execute one live Project Miner Temp Power import mutation and one same-payload idempotent replay.

## Hard Guardrails

Do not create a new Render service.

Do not create or change DNS, auth, ingress, Supabase schema, Supabase credentials, Vercel config, Olares config, source workbooks, source PDFs, workbook macros, or public storage.

Do not run direct SQL.

Do not import anything except the currently approved Temp Power candidate through:

`POST /api/v1/mutations/project-imports`

Do not create assignments, field authorizations, lead/crew selections, schedule/status writes, durable field records, production tracking, customer reports, billing/payroll/invoice/accounting outputs, workbook writeback, or autonomous AI business-state mutations.

## Hosted Preflight

Use the PM actor token style already used by the mutation-seam prototype:

Base64 JSON payload:

```json
{"actor_id":"pm-001","actor_role":"pm","project_scope":["proj-001"]}
```

Before the import POST, prove:

1. deployed mutation-seam smoke passes,
2. hosted candidate readback returns:
   - `candidate_id`: `pm-import-candidate-miner-temp-power`
   - `candidate_version`: `pm_import_candidate_read_only_v1`
   - workpackages: `7`
   - tasks: `15`
   - apparatus candidates: `184`
   - source fingerprint: `e111fdbe934bf9de07ed24c1`
   - shape fingerprint: `ddc49565eb586af913ad48b2`
   - blocker count: `0`
   - warning code: `PROJECT_DATA_ENTRY_FORMULA_ERRORS`
3. approval status readback returns:
   - `classification`: `approved_for_import_packet`
   - `approval_record_count_for_candidate`: `1`
   - `current_candidate_match`: `true`
   - `approval_record_id`: `pm-import-approval-03a1aea39afde71b44516f44`
   - `decision`: `approve_for_import_packet`
4. project import status is either:
   - `no_import_record`, or
   - already `imported` with matching candidate and counts, in which case do not create a second live import and only record replay/status evidence if safe.
5. downstream accessible counts before import are captured for:
   - workpackages,
   - tasks,
   - apparatus,
   - assignments,
   - snapshots,
   - issues,
   - hours,
   - approval queue total,
   - schedule projects,
   - schedule tasks with scope,
   - schedule relationships.

## Import Payload

POST:

`https://operations.apexpowerops.com/api/v1/mutations/project-imports`

Body:

```json
{
  "idempotency_key": "pm-import:a2acafe8e9928899e8645736",
  "mutation_class": "C",
  "action_type": "persist_project_import",
  "entity_id": "pm-import-project-miner-temp-power",
  "payload": {
    "candidate_id": "pm-import-candidate-miner-temp-power",
    "candidate_version": "pm_import_candidate_read_only_v1",
    "source_stat_fingerprint": "e111fdbe934bf9de07ed24c1",
    "candidate_shape_fingerprint": "ddc49565eb586af913ad48b2",
    "idempotency_key": "pm-import:a2acafe8e9928899e8645736",
    "approval_record_id": "pm-import-approval-03a1aea39afde71b44516f44",
    "accepted_warning_codes": [
      "PROJECT_DATA_ENTRY_FORMULA_ERRORS"
    ],
    "accepted_no_go_overrides": [
      "warnings-reviewed-by-pm"
    ],
    "import_notes": "Stakeholder/PM standing authority on 2026-05-18 admits the PM Lane 278 project import mutation for the current approved Temp Power candidate. Persist only project, workpackage, task, and apparatus rows; keep assignment, field, schedule/status, customer, production, finance, workbook, schema, and autonomous AI business-state writes blocked."
  },
  "reason": "Persist approved Project Miner Temp Power import rows only; keep downstream workflow blocked.",
  "source": "online",
  "client_timestamp": "<current UTC ISO timestamp>"
}
```

Then POST the exact same payload again.

## Required Success Evidence

The first POST must return:

1. HTTP `200`,
2. `status`: `accepted`,
3. `entity_type`: `pm_import`,
4. `action_type`: `persist_project_import`,
5. `entity_id`: `pm-import-project-miner-temp-power`,
6. `new_state.import_authority`: `admitted_by_pm_lane_278`,
7. row counts:
   - projects `1`,
   - workpackages `7`,
   - tasks `15`,
   - apparatus `184`,
   - source trace rows `199`,
   - warning review rows `1`.

The second POST must return:

1. HTTP `200`,
2. `status`: `idempotent_hit`,
3. same `entity_id`,
4. same mutation id,
5. same audit event id.

Import-status readback after replay must return:

1. `classification`: `imported`,
2. `current_candidate_match`: `true`,
3. `counts_match`: `true`,
4. imported counts equal expected counts.

Downstream proof after import:

1. assignments unchanged,
2. snapshots unchanged,
3. issues unchanged,
4. hours unchanged,
5. approval queue does not grow from import,
6. schedule context counts unchanged except read-only schedule state already present.

## Handoff Required

Create a concise closeout message with:

1. Render deployment proof and deployed commit,
2. preflight readback summary,
3. first POST response summary,
4. replay response summary,
5. import-status readback,
6. downstream count before/after table,
7. guardrail confirmation,
8. any blocker if the route does not deploy or validation fails.
