# PM Lane Project Miner Intake Workflow

Date: 2026-05-15
Status: Active operator workflow
Scope: Project Miner planning-folder intake into the PM lane

## Purpose

This runbook explains how a real project starts in the PM lane using the current APEX Ops deployment model:

`Vercel UI -> Render mutation seam/API -> Supabase DB`

The Vercel URL is the user-facing PM application. Render is the governed API boundary between the UI and Supabase. Supabase is the data store and must not be treated as the user-facing workflow surface.

Companion operating plan:

`docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`

Companion visual map:

`docs/operations/APEX-OPS-VISUAL-SYSTEM-MAP-2026-05-15.md`

Start with the visual map when the platform split, PM workflow, or AI orchestration lanes are easier to understand as diagrams than as prose.

Companion acceleration lane:

`docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`

Use the acceleration lane when deciding whether a PM workflow step is actually helping. The PM lane should reduce Jason's coordination burden, not add another process he has to manually carry.

Use that plan for the Temp Power delivery target, Olares One orchestration posture, dual-lane execution rules, and capability-gap escalation duty.

## Current Source Packet

Default local planning root:

`C:/Users/jjswe/Desktop/Project Miner PM Planning`

Current files observed in that root:

1. `Estimator R3 - Project Miner Temp Power Testing.xlsm`
2. `Miner Temp SLD-AP-BCARRASCO.pdf`
3. `EQUIPMENT INVENTORY - 2026.xlsx`
4. `Phx Tech Testing Capability Matrix 032726.xlsx`
5. `Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm`
6. `15_ELECTRICAL_COMBINED.pdf`
7. `Building B IFC.pdf`
8. `RESA Power - Project Data Entry MASTER.xlsm`
9. `Garney- Central Mesa Reuse Tracker #677562.xlsm`

The current seeded PM lane starts from the smaller Miner Temp Power estimator and SLD package. The larger Building A/B estimator and IFC drawing sets are treated as next-project source evidence until a dedicated packet promotes them into the runtime seed.

## Day-To-Day Startup Flow

1. Collect source files into one planning folder.
2. Run the read-only preview command.
3. Review project name, location, drawing package, estimator sheet, line-item count, apparatus candidate count, crew count, equipment inventory rows, and capability rows.
4. Open `https://operations.apexpowerops.com/pm-review/workfront` for the user-facing PM workfront.
5. PM reviews readiness, blockers, unassigned rows, submitted snapshots, drillthrough links, and review signals.
6. Lead and field users work through `/lead-ops` and `/field-tech`.
7. Render mutation seam owns any governed API behavior or state transition.
8. Supabase persists project state after an admitted packet opens the relevant live-data write path.

## Preview Command

From `C:/APEX Platform/apex-power-ops-platform`:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning"
```

JSON output for downstream inspection:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --format json
```

To preview a specific estimator/PDF pair from the same planning folder:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --estimator-workbook "C:/Users/jjswe/Desktop/Project Miner PM Planning/Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm" `
  --sld-pdf "C:/Users/jjswe/Desktop/Project Miner PM Planning/Building B IFC.pdf"
```

To include explicit project data-entry or reference tracker workbooks:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --data-entry-workbook "C:/Users/jjswe/Desktop/Project Miner PM Planning/RESA Power - Project Data Entry MASTER.xlsm" `
  --reference-tracker-workbook "C:/Users/jjswe/Desktop/Project Miner PM Planning/Garney- Central Mesa Reuse Tracker #677562.xlsm"
```

The command is read-only. It does not write to Supabase, mutate schedules, assign work, change statuses, or run Excel macros.

## Import Candidate Preview

PM Lane 032 adds a review-ready import candidate preview for Project Miner Temp Power.

Run it from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_import_candidate.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning"
```

JSON output for PM review or downstream UI work:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_import_candidate.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --format json
```

The same read-only candidate is exposed from the mutation seam at:

`GET /api/v1/reads/project-import-candidate`

The PM-facing review route is:

`https://operations.apexpowerops.com/pm-review/import-candidate`

Local or preview environments expose the same route at:

`/pm-review/import-candidate`

Current Temp Power local preview result:

1. 7 proposed workpackages,
2. 15 proposed tasks,
3. 186 apparatus candidates,
4. 15 crew,
5. 343 equipment inventory rows,
6. 50 capability rows,
7. 2 review signals: one missing-designation information item and one project-data-entry formula-warning item.

This import candidate is a review artifact only. It does not write Supabase rows, assign work, change status, mutate schedules, run Excel macros, or approve a project import.

PM Lane 034 hardens the same review route without admitting persistence:

1. source stat fingerprints show the source path, file size, modified time, availability, and aggregate candidate freshness key,
2. warning filters let PM review all, blocker, warning, info, or specific warning-code subsets without fetching or mutating data,
3. JSON export downloads the current read-only candidate plus the local PM draft notes for offline review or sidecar handoff,
4. PM questions draft is retained only in the local browser and is not approval, import, Supabase state, or a server-side note.

## Import Admission Plan

PM Lane 035 adds a read-only import-admission plan before any import mutation exists.

The read seam is:

`GET /api/v1/reads/project-import-admission-plan`

The PM-facing plan route is:

`/pm-review/import-admission-plan`

Hosted PM intake UI route:

`https://operations.apexpowerops.com/pm-review/import-admission-plan`

This route explains the future import gate:

1. approval record contract,
2. deterministic idempotency key strategy,
3. preview-to-import diff checks,
4. no-go checks,
5. target row counts,
6. future import sequence,
7. actions that remain disallowed.

This is not an approval screen and not an import screen. It does not persist approval, write Supabase rows, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

## Import Approval Contract

PM Lane 038 adds a read-only approval-persistence contract before any approval record can be stored.

The read seam is:

`GET /api/v1/reads/project-import-approval-contract`

This contract explains the future approval packet in machine-checkable form:

1. candidate id, version, source fingerprint, shape fingerprint, and idempotency key that must match,
2. permitted PM decisions,
3. required approval fields,
4. warning codes the PM must accept exactly,
5. human-acceptance no-go checks that may be acknowledged,
6. non-overridable no-go checks that still block import,
7. decision payload template,
8. validation matrix,
9. future mutation contract placeholder.

The backend also includes a pure local validator for this approval payload. The validator rejects stale fingerprints, changed warning-code sets, unsupported decisions, missing PM actor/timestamp fields, empty review notes, and attempts to override non-overridable checks.

This is still not approval persistence and not import. It does not write Supabase rows, store PM notes, import project rows, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

## Import Approval Storage Plan

PM Lane 039 adds a read-only storage decision plan before any approval persistence can be implemented.

The read seam is:

`GET /api/v1/reads/project-import-approval-storage-plan`

The plan selects the future persistence shape without opening that write path:

1. dedicated insert-only table: `seam.pm_import_candidate_approvals`,
2. future mutation route: `/api/v1/mutations/project-import-approvals`,
3. future entity type: `pm_import_candidate_approval`,
4. typed identity columns plus JSONB approval payload and validation result,
5. append-only or strict idempotent replay lifecycle,
6. audit as evidence after insert, not as the canonical approval store,
7. readback requirements for current, stale, returned, rejected, or approved candidate state.

The plan explicitly rejects unsafe shortcuts:

1. audit-log-only approval storage,
2. reusing issue, task, or workpackage rows for pre-import approval,
3. browser-local storage as canonical approval,
4. generic PgDict upsert without an explicit approval adapter,
5. direct Supabase writes from Excel or the UI.

This is still not approval persistence and not import. It does not create a table, run SQL, write Supabase rows, store PM notes, import project rows, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

## Import Approval Readiness UI

PM Lane 040 adds a read-only PM UI route that combines the approval contract and approval storage plan before any approval can be persisted.

The operations-web route is:

`/pm-review/import-approval-readiness`

The route consumes only:

1. `GET /api/v1/reads/project-import-approval-contract`,
2. `GET /api/v1/reads/project-import-approval-storage-plan`.

It shows:

1. approval contract identity and candidate identity,
2. required fields, permitted decisions, expected values, and decision payload template,
3. human-acceptance policy and non-overridable blocked checks,
4. approval validation matrix,
5. future mutation contract placeholder,
6. selected dedicated storage table and future route,
7. record lifecycle, adapter requirements, recommended columns, constraints, and rejected storage shortcuts,
8. future admission sequence and merged not-allowed-now guardrails.

The route is intentionally separate from `/pm-review/approval`, because that existing PM route owns admitted PM approval mutation flows for current project work. This readiness route is inspection-only for the future Project Miner import approval packet.

This is still not approval persistence and not import. It does not show approval controls, persist notes, create a table, run SQL, write Supabase rows, import project rows, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

## Hosted Intake Parity Status

PM Lane 036 promoted the operations-web PM intake routes to Vercel production:

1. `https://operations.apexpowerops.com/pm-review/import-candidate`
2. `https://operations.apexpowerops.com/pm-review/import-admission-plan`

Hosted route smoke passed with both markers present.

The matching Render mutation-seam routes are not yet hosted-current:

1. `https://mutation-seam.apexpowerops.com/health` returns `200`,
2. hosted OpenAPI does not list `/api/v1/reads/project-import-candidate`,
3. hosted OpenAPI does not list `/api/v1/reads/project-import-admission-plan`,
4. both PM intake read routes currently return `404`.

This means the user-facing pages are visible, but hosted live intake data remains blocked until a Render-authenticated mutation-seam redeploy and log inspection closes the backend parity gap.

PM Lane 037 refreshes the Render-authenticated executor packet for this exact blocker and adds backend-only smoke coverage:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" `
  --base-url "https://mutation-seam.apexpowerops.com" `
  --include-pm-intake
```

That smoke should remain red until Render serves the current mutation-seam code. It checks the existing health, approval, and schedule reads plus the PM intake OpenAPI paths and read-only payload shape.

After PM Lane 038, the same flag also checks:

1. OpenAPI registration of `/api/v1/reads/project-import-approval-contract`,
2. `GET /api/v1/reads/project-import-approval-contract`,
3. approval-contract payload fields including `mutation_authority` and `persistence_authority`.

After PM Lane 039, it also checks:

1. OpenAPI registration of `/api/v1/reads/project-import-approval-storage-plan`,
2. `GET /api/v1/reads/project-import-approval-storage-plan`,
3. storage-plan payload fields including `selected_storage_decision`, `recommended_table`, `mutation_authority`, and `persistence_authority`.

After PM Lane 040, operations-web hosted route smoke and PM-intake hosted smoke also include `/pm-review/import-approval-readiness`; the mutation-seam side of that hosted smoke still depends on Render serving the current PM intake reads.

PM Lane 041 refreshes the hosted parity packet around the current split:

1. hosted operations-web still serves `/pm-review/import-candidate`,
2. hosted operations-web still serves `/pm-review/import-admission-plan`,
3. hosted operations-web does not yet serve `/pm-review/import-approval-readiness`,
4. hosted mutation-seam health is reachable,
5. hosted mutation-seam OpenAPI is missing all four current PM intake read paths,
6. hosted mutation-seam returns `404` for all four current PM intake reads,
7. hosted schedule reads still return `500`.

Lane 041 therefore splits hosted work into two bounded executor lanes:

1. Vercel-authenticated existing operations-web promotion for the Lane 040 UI route,
2. Render-authenticated existing mutation-seam redeploy and blocker classification for the PM intake reads.

No approval persistence, import mutation, schema migration, SQL write, service admission, auth widening, ingress widening, fixture replay, or live business-state mutation is admitted by this parity lane.

The split executor handoffs are:

1. `ops/agents/handoffs/2026-05-15-pm-lane-041a-vercel-operations-web-promotion-handoff.md`,
2. `ops/agents/handoffs/2026-05-15-pm-lane-041b-render-mutation-seam-redeploy-classification-handoff.md`,
3. `ops/agents/handoffs/2026-05-15-pm-lane-041-dual-executor-dispatch-board.md`.

PM Lane 042 adds the required closeout intake template for these hosted executor returns:

`ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md`

The coordinator should not accept a hosted executor result without source commit, hosted action evidence, exact validation results, blocker classification if red, and guardrail confirmation.

## Project Miner Intake Workbench

PM Lane 043 adds a local-current, read-only PM workbench route:

`/pm-review/import-intake`

The workbench is the day-to-day Project Miner intake starting point. It consolidates the four current intake reads without opening a write path:

1. `GET /api/v1/reads/project-import-candidate`,
2. `GET /api/v1/reads/project-import-admission-plan`,
3. `GET /api/v1/reads/project-import-approval-contract`,
4. `GET /api/v1/reads/project-import-approval-storage-plan`.

It shows candidate identity, source freshness, project location, proposed row counts, warning signals, required PM decisions, workflow gates, admission target rows, approval contract authority, the future `seam.pm_import_candidate_approvals` table, the future `/api/v1/mutations/project-import-approvals` route, hosted-parity status, and merged guardrails.

This route is a navigation and review accelerator only. It does not approve, persist, import, create schema, run SQL, write Supabase rows, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

Hosted note: PM Lane 043 is local-current only until PM Lane 041A/041B close hosted Vercel and Render parity. Do not claim hosted live-data parity for `/pm-review/import-intake` until those closeouts are accepted.

PM Lane 044 updates the hosted parity proof and executor handoffs so `/pm-review/import-intake` is included in the same Vercel promotion lane as `/pm-review/import-approval-readiness`. The refreshed hosted PM intake smoke currently passes import-candidate and import-admission-plan, but returns `404` for both `/pm-review/import-approval-readiness` and `/pm-review/import-intake` until an authenticated Vercel executor promotes current `origin/clean-main`.

PM Lane 076 adds the current hosted parity executor dispatch binder after the local workbench through PM Lane 119. It points Desktop Codex, or another authenticated external executor if needed, at the existing PM Lane 041A Vercel lane, PM Lane 041B Render lane, and PM Lane 042 closeout template from one copy/paste surface, with current source floor `clean-main e89cabb7a1226ceeb3a431b25147d889402ea1a3`. It does not deploy, change code, write data, or claim hosted parity.

PM Lane 077 groups the existing top output actions on `/pm-review/import-intake` into Review Outputs, Executor Output, Field Prep Outputs, and Refresh. The route links remain separate, and all export labels, handlers, filenames, contents, read seams, and storage keys remain unchanged. This is local UI organization only and does not create a new export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 078 groups the existing export feedback on `/pm-review/import-intake` into Review Output Status, Executor Output Status, and Field Prep Output Status after exports run. The status rail remains absent until an existing export creates a status message, and all export labels, handlers, filenames, contents, read seams, and storage keys remain unchanged. This is local UI organization only and does not create a new export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 079 groups the existing quick-jump links on `/pm-review/import-intake` into Daily Review, Outputs and Handoff, Review Flow, and Source, Field, and Guardrails. Every existing href and target section remains unchanged, and the quick-jump rail stays immediately after the project summary. This is local UI organization only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 080 groups the existing top route links on `/pm-review/import-intake` into Shell, Intake Reads, and PM Workfront. Every existing href and route target remains unchanged, and the quick-jump rail, output actions, output statuses, storage keys, and read seams remain unchanged. This is local UI organization only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 081 groups the existing helper-panel stack below the quick-jump rail on `/pm-review/import-intake` into Intake Triage Panels, Daily Action Panels, and Workflow Review Panels. Every helper panel id, aria label, anchor target, route link, quick-jump link, output action, output status, storage key, and read seam remains unchanged. This is local UI organization only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 082 groups the existing detail workbench below the helper-panel stack on `/pm-review/import-intake` into Review Snapshot Detail, Source and Exception Detail, Approval Prep Detail, Executor Closeout Detail, Field Prep Detail, and Authority Boundary Detail. Every existing panel id, aria label, anchor target, route link, quick-jump link, output action, output status, storage key, and read seam remains unchanged. This is local UI organization only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 083 hardens the focused `/pm-review/import-intake` smoke with a local authority wording guard. The test now rejects implied approval, persistence, import, assignment, schedule, status, task/issue creation, field-release, work-order, hosted-proof, or production-readiness controls; verifies the PM Lane 082 detail-workbench headings remain review/detail/boundary oriented; and keeps route-link, quick-jump, export, output-status, storage, read-count, and zero-mutation coverage intact. This is test-only governance and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 084 wraps the six PM Lane 082 detail-workbench groups on `/pm-review/import-intake` in default-open native disclosure controls. The existing groups, panel ids, aria labels, anchor targets, route links, quick-jump links, output actions, output statuses, storage keys, and read seams remain unchanged, and collapsed state is not persisted. This is local UI ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 085 wraps the three PM Lane 081 helper-panel groups on `/pm-review/import-intake` in default-open native disclosure controls. The existing helper groups, panel ids, aria labels, anchor targets, route links, quick-jump links, output actions, output statuses, storage keys, and read seams remain unchanged, and collapsed state is not persisted. This is local UI ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 086 wraps the top output action rail on `/pm-review/import-intake` in a default-open native disclosure control. The existing Review Outputs, Executor Output, Field Prep Outputs, and Refresh child groups, button labels, button counts, export handlers, refresh handler, output statuses, storage keys, and read seams remain unchanged, and collapsed state is not persisted. This is local UI ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 087 wraps the existing quick-jump rail on `/pm-review/import-intake` in a default-open native disclosure control. The rail id, aria label, group headings, link labels, href targets, link counts, order, target sections, storage keys, and read seams remain unchanged, and collapsed state is not persisted. This is local UI ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 088 wraps the existing conditional output status rail on `/pm-review/import-intake` in a default-open native disclosure control. The rail still remains absent until at least one Review, Executor, or Field Prep output status exists; status labels, message text, ordering, counts, export behavior, storage keys, and read seams remain unchanged, and collapsed state is not persisted. This is local UI ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 089 wraps the existing route-link rail on `/pm-review/import-intake` in a default-open native disclosure control. The existing Shell, Intake Reads, and PM Workfront groups, link labels, href targets, link counts, order, storage keys, and read seams remain unchanged, and collapsed state is not persisted. This is local UI ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 090 wraps the existing Local PM Intake Handoff Guide panel on `/pm-review/import-intake` in a default-open native disclosure control. The guide remains inside Daily Action Panels, and the existing five derived items, labels, hrefs, order, status pills, dynamic text, storage keys, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration handoff ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 091 wraps the existing Local PM Intake Workflow Map panel on `/pm-review/import-intake` in a default-open native disclosure control. The map remains inside Workflow Review Panels, and the existing seven derived items, labels, hrefs, order, status pills, dynamic text, storage keys, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration workflow ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 092 wraps the existing Local PM Intake Open Items Lens panel on `/pm-review/import-intake` in a default-open native disclosure control. The lens remains inside Workflow Review Panels, and the existing six derived items, labels, hrefs, order, status pills, dynamic text, storage keys, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration attention-lens ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 093 wraps the existing Local PM Intake Snapshot panel on `/pm-review/import-intake` in a default-open native disclosure control. The snapshot remains inside Review Snapshot Detail, and the existing six derived snapshot entries, count summary, labels, detail/evidence text, status pills, dynamic behavior, export behavior, storage keys, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration snapshot ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 094 wraps the existing Local PM Operating Queue panel on `/pm-review/import-intake` in a default-open native disclosure control. The queue remains inside Review Snapshot Detail after the snapshot, and the existing six derived queue items, item order, status pills, dynamic count text, storage keys, export references, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration operating-queue ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 095 wraps the existing Local Import Exception Decision Register panel on `/pm-review/import-intake` in a default-open native disclosure control. The register remains inside Source and Exception Detail, and the existing six derived register items, item order, status pills, summary counts, dynamic behavior, export behavior, storage keys, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration exception-register ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 096 wraps the existing Workflow Gates panel on `/pm-review/import-intake` in a default-open native disclosure control. The gates remain inside Source and Exception Detail after the exception register, and the existing six gate items, item order, status pills, detail text, read-only label, quick-jump target, export references, storage keys, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration workflow-gate ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 097 wraps the existing Exception Review and PM Decisions detail panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Source and Exception Detail after Workflow Gates, and the existing warning card, PM decision card, severity/code pills, decision prompt/recommended action text, fallback empty states, export behavior, storage keys, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration exception-and-decision detail ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 098 wraps the existing Admission and Approval Contract panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Approval Prep Detail before Local Review Checklist, and the existing Admission Shape card, Approval Contract card, labels, values, order, fallback text, export behavior, storage keys, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration approval-prep ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 099 wraps the existing Local Review Checklist panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Approval Prep Detail after Admission and Approval Contract and before Local Approval Decision Draft, and the existing seven checklist items, item labels/details, count text, checkbox behavior, clear button, candidate-scoped storage key, export inclusion, dynamic derived-state behavior, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration checklist ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 100 wraps the existing Local Approval Decision Draft panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Approval Prep Detail after Local Review Checklist, and the existing decision selector, review notes textarea, local-only attestation, clear button, candidate-scoped storage key, export inclusion, dynamic derived-state behavior, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration approval-draft ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 101 wraps the existing Local Executor Closeout Intake panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Executor Closeout Detail with the existing `#executor-closeout` anchor target, and the existing eight closeout checklist items, labels/details, count text, checkbox behavior, clear button, candidate-scoped storage key, export inclusion, dynamic derived-state behavior, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration closeout-intake ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, or production state.

PM Lane 102 wraps the existing Local Field Readiness Checklist panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Field Prep Detail, and the existing eight readiness checklist items, labels/details, count text, checkbox behavior, clear button, candidate-scoped storage key, export inclusion, dynamic derived-state behavior, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration field-prep ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 103 wraps the existing Local Field Questions Draft panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Field Prep Detail, and the existing six textarea labels/values, local-only pill, clear button, candidate-scoped storage key, export inclusion, dynamic field-prep derived-state behavior, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration field-prep ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 104 wraps the existing Local Field Prep Queue panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Field Prep Detail with the existing `#field-prep` anchor target, and the five derived queue items, item order, summary count text, status pills, dynamic derived behavior, no-authority wording, quick-jump target, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration field-prep ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 105 wraps the existing Local Field Prep Coverage Snapshot panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Field Prep Detail, and the existing seven derived coverage items, item order, summary text, status pills, dynamic derived behavior, export inclusion, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration field-prep ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 106 wraps the existing Local Field Prep Conversation Agenda panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Field Prep Detail, and the existing seven derived agenda items, item order, summary text, status pills, dynamic counts, export inclusion, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration field-prep ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 107 wraps the existing Local Field Observation Scratchpad panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Field Prep Detail, and the existing six textarea labels, placeholders, candidate-scoped browser-local storage key, clear button behavior, derived field-observations behavior, export inclusion, browser-local pill, no-authority wording, and read seams remain unchanged, with no persisted collapsed state. This is local AI/orchestration field-prep ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 108 wraps the existing Approval Persistence Readiness panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains inside Authority Boundary Detail, keeps the `#approval-readiness` anchor, and preserves the existing heading, readiness count pill, two explanatory paragraphs, six readiness gates, gate order, gate statuses, route and quick-jump links, no-authority wording, and read seams, with no persisted collapsed state. This is local AI/orchestration authority-boundary ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 109 wraps the existing Current PM Next Actions and Guardrails footer on `/pm-review/import-intake` in a default-open native disclosure control. The footer remains after Approval Persistence Readiness, keeps the `#guardrails` anchor, and preserves both inner cards, list text, list order, not-allowed fallback rendering, route and quick-jump links, no-authority wording, and read seams, with no persisted collapsed state. This is local AI/orchestration footer-scan ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 110 wraps the existing Local PM Intake Command Center panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains under Intake Triage Panels, keeps the `#pm-command-center` anchor, and preserves the existing heading, browser-local pill, explanatory no-authority wording, four derived command-center cards, card order, hrefs, dynamic text, status pills, quick-jump target, and read seams, with no persisted collapsed state. This is local AI/orchestration command-center ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 111 wraps the existing Local PM Intake Meeting Readout panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains under Intake Triage Panels, keeps the `#pm-meeting-readout` anchor and placement after `#pm-command-center` before `#pm-constraint-radar`, and preserves the existing heading, browser-local pill, explanatory no-authority wording, four derived meeting readout cards, card order, hrefs, dynamic text, status pills, quick-jump target, and read seams, with no persisted collapsed state. This is local meeting-prep and AI/orchestration ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 112 wraps the existing Local PM Intake Constraint Radar panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains under Intake Triage Panels, keeps the `#pm-constraint-radar` anchor and placement after `#pm-meeting-readout`, and preserves the existing heading, browser-local pill, explanatory no-authority wording, four derived constraint cards, card order, hrefs, dynamic text, status pills, quick-jump target, export read seams, and no persisted collapsed state. This is local constraint-scanning and AI/orchestration ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 113 wraps the existing Local PM Intake Daily Review Script panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains under Daily Action Panels, keeps the `#pm-daily-review-script` anchor and placement before `#pm-start-here`, and preserves the existing heading, browser-local pill, explanatory no-authority wording, five derived daily review cards, card order, hrefs, dynamic text, status pills, quick-jump target, read seams, and no persisted collapsed state. This is local first-pass review and AI/orchestration ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 114 wraps the existing Local PM Intake Start Here panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains under Daily Action Panels, keeps the `#pm-start-here` anchor and placement after `#pm-daily-review-script`, and preserves the existing heading, browser-local pill, explanatory no-authority wording, five derived start-here cards, card order, hrefs, dynamic text, status pills, quick-jump target, read seams, and no persisted collapsed state. This is local orientation and AI/orchestration ergonomics only and does not create a new route, export, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 115 wraps the existing Local PM Intake Output Selector panel on `/pm-review/import-intake` in a default-open native disclosure control. The panel remains under Daily Action Panels, keeps the `#pm-output-selector` anchor and placement after `#pm-start-here` before `#pm-handoff-guide`, and preserves the existing heading, browser-local pill, explanatory no-authority wording, five derived output-selector cards, card order, hrefs, dynamic text, status pills, quick-jump target, read seams, and no persisted collapsed state. This is local output-selection and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 116 wraps the existing Local PM Intake Handoff Guide body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains under Daily Action Panels, keeps the `#pm-handoff-guide` anchor and placement after `#pm-output-selector`, and preserves the existing disclosure, heading, browser-local pill, explanatory no-authority wording, five derived handoff-guide cards, card order, hrefs, dynamic text, status pills, quick-jump target, read seams, and no persisted collapsed state. This is local handoff-context and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 117 wraps the existing Local PM Intake Workflow Map body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Workflow Review Panels, keeps the `#pm-workflow-map` anchor and placement after `#pm-handoff-guide`, and preserves the existing disclosure, heading, browser-local pill, explanatory no-authority wording, seven derived workflow-map cards, card order, hrefs, dynamic text, status pills, quick-jump target, read seams, and no persisted collapsed state. This is local workflow-orientation and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 118 wraps the existing Local PM Intake Open Items Lens body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Workflow Review Panels, keeps the `#pm-open-items` anchor and placement after `#pm-workflow-map`, and preserves the existing disclosure, heading, browser-local pill, explanatory no-authority wording, six derived open-items cards, card order, hrefs, dynamic text, status pills, quick-jump target, read seams, and no persisted collapsed state. This is local open-items attention scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 119 wraps the existing Local PM Intake Snapshot body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Review Snapshot Detail, keeps the `#pm-intake-snapshot` anchor and placement before `#pm-operating-queue`, and preserves the existing disclosure, heading, browser-local pill, explanatory no-authority wording, snapshot summary count, six derived snapshot cards, card order, dynamic detail/evidence text, status pills, quick-jump target, read seams, export behavior, and no persisted collapsed state. This is local snapshot scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 120 wraps the existing Local PM Operating Queue body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Review Snapshot Detail, keeps the `#pm-operating-queue` anchor and placement after `#pm-intake-snapshot`, and preserves the existing disclosure, heading, browser-local pill, explanatory no-authority wording, complete/next/blocked summary count, six derived queue cards, card order, dynamic detail text, status pills, quick-jump target, read seams, export references, and no persisted collapsed state. This is local operating-queue scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 045 adds a local-only `Export PM Brief` action to `/pm-review/import-intake`. The Markdown brief is generated entirely in the browser from the already-loaded four PM intake reads and includes candidate identity, source freshness, proposed row counts, warning signals, PM decisions, workflow gates, admission and approval authority, future approval table/route, target rows, and not-allowed-now guardrails. It is a portable review and executor-handoff artifact only; it is not approval, persistence, import, assignment, schedule, status, or production state.

PM Lane 046 adds a browser-local `Local Review Checklist` to `/pm-review/import-intake`. The checklist is candidate-scoped in browser storage and covers source freshness, warning review, PM decision capture, admission no-go review, approval storage understanding, hosted-parity awareness, and write-guardrail confirmation. Checked state is included in the local Markdown PM brief so a reviewer or executor can see what was reviewed without turning the checklist into approval, persistence, import, assignment, schedule, status, or production state.

PM Lane 047 adds a browser-local `Local Approval Decision Draft` to `/pm-review/import-intake`. The draft is candidate-scoped in browser storage and lets the PM choose a local decision value from the read-only approval contract, write review notes, and check a local-only attestation. The draft is included in the local Markdown PM brief for future packet context, but it is not approval, persistence, import, assignment, schedule, status, or production state.

PM Lane 048 adds a browser-only `Export Approval Preview JSON` action to `/pm-review/import-intake`. The preview is generated from the four already-loaded read-only intake reads, the local checklist, and the local approval-decision draft. It gives a later admitted approval-persistence packet structured candidate, contract, storage, review-evidence, and boundary context without approving, persisting, importing, assigning, scheduling, changing status, or mutating production state.

PM Lane 049 authors the design-only approval persistence schema and adapter admission packet. It defines the future `seam.pm_import_candidate_approvals` table, explicit insert-only adapter boundary, validation evidence, readback classification, hosted-parity blockers, and guardrails using the PM Lane 048 preview JSON as the input contract. It does not add SQL, run a migration, implement a backend route, persist approval, import rows, assign work, schedule work, change status, or mutate production state.

PM Lane 050 adds a local `Approval Persistence Readiness` panel to `/pm-review/import-intake`. The panel makes the approval-persistence runway visible inside the daily PM workbench: local preview context and review-checklist evidence can turn ready, while hosted parity closeout, schema authority, approval persistence authority, and import mutation authority remain blocked.

This is still local review context only. It does not approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

PM Lane 051 adds a browser-local `Local PM Operating Queue` near the top of `/pm-review/import-intake`. The queue derives complete, next, and blocked status from the checklist, local approval-decision draft, and approval-persistence readiness gates so the day-to-day PM next move is visible without reading packet docs.

This is still local review guidance only. It does not create live tasks, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

PM Lane 052 adds a browser-local `Export Executor Handoff` action to `/pm-review/import-intake`. The Markdown handoff packages candidate identity, local review state, checked and open review evidence, the local PM operating queue, approval-persistence blockers, workflow gates, future-not-admitted surfaces, not-allowed guardrails, and minimum safe next-packet evidence for a later bounded executor.

This handoff is context only and grants no authority. It does not create live tasks, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

PM Lane 053 adds a browser-local `Local Executor Closeout Intake` checklist to `/pm-review/import-intake`. It helps review returned executor evidence for source commit, changed files, hosted action evidence, exact validation results, final verdict, remaining blocker classification, guardrail confirmation, and bounded coordinator recommendation.

This closeout intake is audit prep only and grants no acceptance authority. It does not create live tasks, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

PM Lane 054 adds a browser-local `Export Field Kickoff Brief` action to `/pm-review/import-intake`. The Markdown brief packages the current candidate identity, project location, source freshness, proposed workpackage/task/apparatus shape, workpackage preview, field-prep questions, exceptions, PM decisions, local review evidence, local executor closeout evidence, operating queue, workflow gates, future-not-admitted surfaces, and not-allowed guardrails.

This field kickoff brief is field-prep context only and grants no work authorization. It does not create live tasks, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 055 adds a browser-local `Local Field Readiness Checklist` to `/pm-review/import-intake`. It captures field-prep evidence for drawing/source questions, scope assumptions, site access and contacts, safety planning, crew/equipment questions, material/staging questions, customer constraint questions, and field-authority boundary acknowledgement.

This checklist is candidate-scoped browser prep evidence only and grants no field release. It does not create live tasks, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 056 adds a browser-local `Local Field Questions Draft` to `/pm-review/import-intake`. It captures draft text for drawing/source questions, site access and safety questions, crew/equipment questions, material/staging questions, customer constraint questions, and PM follow-up notes.

This draft is candidate-scoped browser prep context only and is not a system of record. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 057 adds a browser-local `Local Field Prep Queue` to `/pm-review/import-intake`. It derives complete, next, and blocked prep moves from the field questions draft and field readiness checklist so the next field-prep action is visible without turning local notes into production tasks.

This queue is browser-local prep guidance only and stores no additional state. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 058 adds a browser-local `Local Field Observation Scratchpad` and `Export Field Observation Notes` action to `/pm-review/import-intake`. It captures date or shift note, observer/source, workpackage or area reference, access/safety observations, material/staging/equipment observations, and open PM follow-up questions as local field-prep context.

This scratchpad is candidate-scoped browser context only and is not the durable field record. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 059 adds a browser-local `Local Field Prep Coverage Snapshot` and `Export Field Prep Coverage Snapshot` action to `/pm-review/import-intake`. It derives covered, partial, open, and blocked coverage from the existing local review checklist, field readiness checklist, field questions draft, and field observation scratchpad. The snapshot covers source/drawing, access/safety, crew/equipment, material/staging, customer constraints, field authority boundary, and the production tracking boundary.

This snapshot is derived conversation prep only and adds no local storage key. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 060 adds a browser-local `Local Field Prep Conversation Agenda` and `Export Field Prep Conversation Agenda` action to `/pm-review/import-intake`. It derives context, ask, confirm, and blocked agenda items from the local field-prep coverage snapshot so PM, lead, customer, and field conversations can start from the next useful question instead of another manual summary.

This agenda is derived conversation prep only and adds no local storage key. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 061 adds a browser-local `Export Field Prep Packet` action to `/pm-review/import-intake`. It bundles the local field prep queue, coverage snapshot, conversation agenda, readiness evidence, questions draft, observation scratchpad, review and closeout context, workflow gates, future-not-admitted surfaces, and not-allowed guardrails into one Markdown prep packet.

This packet is derived conversation prep only and adds no local storage key or new form. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 062 adds a browser-local `Local Import Exception Decision Register` and `Export Import Exception Register` action to `/pm-review/import-intake`. It derives covered, open, and blocked exception-review synthesis from source freshness evidence, candidate warnings, human decision prompts, admission no-go checks, local review evidence, local decision draft evidence, and the future write boundary.

This register is browser-local review synthesis only and adds no local storage key. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 063 adds a browser-local `Local PM Intake Snapshot` and `Export PM Intake Snapshot` action to `/pm-review/import-intake`. It compresses exception posture, decision draft posture, field-prep context, next local action, approval-persistence boundary, and hosted-parity boundary into one covered, open, and blocked scan view near the top of the workbench.

This snapshot is browser-local review synthesis only and adds no local storage key. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 064 adds a browser-local `PM Intake Quick Jump Rail` to `/pm-review/import-intake`. It links directly to the existing snapshot, operating queue, exception register, project/source packet, workflow gates, approval readiness, field-prep, executor closeout, and guardrails sections so the daily workbench can be used without reconstructing the vertical page map.

This rail is browser-local navigation only and adds no local storage key or export contract. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 065 adds a browser-local `Local PM Intake Start Here` panel to `/pm-review/import-intake`. It derives one top-level focus list from existing workbench state: first local move, exception attention, field-prep focus, useful local export, and blocked future authority.

This panel is browser-local synthesis only and adds no local storage key or export contract. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 066 adds a browser-local `Local PM Intake Workflow Map` panel to `/pm-review/import-intake`. It derives the visible intake path from existing workbench state: source intake, exception review, decision draft, field prep, executor closeout, approval-persistence boundary, and project-import boundary.

This map is browser-local synthesis only and adds no local storage key or export contract. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 067 adds a browser-local `Local PM Intake Open Items Lens` panel to `/pm-review/import-intake`. It derives the visible open-item posture from existing workbench state: exception review, decision draft, field-prep queue, executor closeout evidence, approval-persistence boundary, and project-import boundary.

This lens is browser-local synthesis only and adds no local storage key or export contract. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 068 adds a browser-local `Local PM Intake Daily Review Script` panel to `/pm-review/import-intake`. It derives the first five minutes of PM intake review from existing workbench state: source context, exception posture, local draft notes, field-prep questions, executor closeout evidence, approval-persistence boundary, and project-import boundary.

This script is browser-local synthesis only and adds no local storage key or export contract. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 069 adds a browser-local `Local PM Intake Output Selector` panel to `/pm-review/import-intake`. It derives existing-output guidance from current workbench state for the PM Brief, Approval Preview JSON, Executor Handoff, Field Kickoff Brief, and Field Prep Packet.

This selector is browser-local synthesis only and adds no local storage key, export action, or export contract. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 070 adds a browser-local `Local PM Intake Handoff Guide` panel to `/pm-review/import-intake`. It derives next-context guidance from current workbench state for Jason local review, field conversation prep, bounded executor context, hosted parity executor boundary, and future approval-persistence packet boundary.

This guide is browser-local synthesis only and adds no local storage key, export action, export contract, or handoff artifact. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 071 adds a browser-local `Local PM Intake Command Center` panel to `/pm-review/import-intake`. It derives one compact top-of-page scan from current workbench state: current local PM move, next field-question posture, handoff context, and blocked future authority.

This command center is browser-local synthesis only and adds no local storage key, export action, export contract, or handoff artifact. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 072 adds a browser-local `Local PM Intake Meeting Readout` panel to `/pm-review/import-intake`. It derives a conversation-ready local summary from current workbench state: project readout, review posture, field ask, and boundary statement.

This meeting readout is browser-local synthesis only and adds no local storage key, export action, export contract, or handoff artifact. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 073 adds a browser-local `Local PM Intake Constraint Radar` panel to `/pm-review/import-intake`. It derives a constraint-first scan from current workbench state: source/review constraints, field-prep constraints, executor/hosted constraints, and future write-authority constraints.

This radar is browser-local synthesis only and adds no local storage key, export action, export contract, or handoff artifact. It does not create issues, create tasks, create live work orders, approve, persist, import, create schema, run SQL, write Supabase rows, call live services, run workbook macros, write workbook cells, assign work, change status, mutate schedules, create durable field records, write production tracking rows, claim hosted parity, or admit autonomous AI business-state action.

PM Lane 074 carries the `Local PM Intake Constraint Radar` into the existing `Export PM Brief` and `Export Executor Handoff` downloads from `/pm-review/import-intake`. It keeps the same source/review, field-prep, executor/hosted, and future write-authority constraints visible when a local PM artifact is used for review or a bounded executor handoff.

This is an existing-export context extension only and adds no new storage key, export action, new export artifact, backend route, approval record, schema, SQL, live service call, hosted claim, task, issue, assignment, schedule, status, durable field record, production tracking row, or production write.

PM Lane 075 promotes the existing browser-local `PM Intake Quick Jump Rail` to the top of `/pm-review/import-intake`, immediately after the project summary and before the helper-panel stack. It keeps the same links but makes navigation available before Jason scrolls through command center, meeting readout, constraint radar, daily script, start-here, output selector, handoff guide, workflow map, and open-items panels.

This is existing navigation placement only and adds no new storage key, export action, new export artifact, backend route, approval record, schema, SQL, live service call, hosted claim, task, issue, assignment, schedule, status, durable field record, production tracking row, or production write.

## Environment Overrides

Set this when using a different planning folder:

```powershell
$env:APEX_PROJECT_MINER_PLANNING_ROOT = "C:/Users/jjswe/Desktop/Project Miner PM Planning"
```

Specific file overrides still take precedence:

```powershell
$env:APEX_PROJECT_ESTIMATOR_WORKBOOK = "C:/path/to/Estimator.xlsm"
$env:APEX_PROJECT_SLD_PDF = "C:/path/to/SLD.pdf"
$env:APEX_FIELD_SEED_EQUIPMENT_WORKBOOK = "C:/path/to/EQUIPMENT INVENTORY - 2026.xlsx"
$env:APEX_FIELD_SEED_CAPABILITY_WORKBOOK = "C:/path/to/Phx Tech Testing Capability Matrix 032726.xlsx"
$env:APEX_PROJECT_DATA_ENTRY_WORKBOOK = "C:/path/to/RESA Power - Project Data Entry MASTER.xlsm"
$env:APEX_REFERENCE_TRACKER_WORKBOOK = "C:/path/to/Garney- Central Mesa Reuse Tracker #677562.xlsm"
```

## Excel MCP Tooling Posture

`sbroenne/mcp-server-excel` is useful as a workstation-side operator accelerator because it controls real Microsoft Excel through COM. It is a good fit for:

1. visually inspecting `.xlsm` estimator tabs,
2. verifying formulas and calculated quantities,
3. exporting screenshots for human review,
4. reviewing PivotTables, charts, Power Query, VBA, and formatting,
5. helping an agent map workbook rows into clean PM intake records.

It is not part of the production runtime:

1. no Render dependency,
2. no Vercel dependency,
3. no Supabase direct-write authority,
4. no server-side batch processing requirement,
5. no macro execution unless explicitly approved by a packet and a human operator.

The repo-owned baseline remains `openpyxl` and `pypdf` inside `apps/mutation-seam` for deterministic read-only intake preview. Excel MCP may be installed separately in VS Code or another MCP client when live Excel interaction is useful.

The built-in Codex spreadsheet tooling is appropriate for producing human-review workbooks, dashboards, or import QA summaries after a packet requests that artifact. It is not required for the live PM lane runtime and should not replace the deterministic seed readers without a bounded packet.

## Estimator VBA Lineage

Earlier estimator-intake work produced two VBA modules under:

1. `C:/APEX Platform/Reference_Files/Excel/Estimator VBA Modules/DataverseExport.bas`
2. `C:/APEX Platform/Reference_Files/Excel/Estimator VBA Modules/DataverseMappingVerification.bas`

Those modules are Dataverse-era artifacts and should not be treated as the current production import path. Their value is the workbook mapping they preserve:

1. metadata originally came from a `Dataverse_Import` sheet,
2. scope totals came from `Equipment Reference`,
3. active scope sheets were listed in `Equipment Reference!L:M`,
4. scope-level fields used `C4`, `J3`, `M4`, `P3`, and `P4`,
5. apparatus line rows used `C` for quantity, `E` for equipment type, `I` for hours per unit, and `J` for total hours,
6. each quantity greater than one expanded into one apparatus candidate per unit.

Current Project Miner workbooks no longer include `Dataverse_Import`, but they do still include `Equipment Reference`. The PM lane reader therefore supports two read-only estimator shapes:

1. flat quote shape: `Updated` or `Quote Tab`,
2. scope-sheet shape: active sheets listed in `Equipment Reference!L:M`.

The VBA files remain static reference evidence only. Do not run their macros as part of PM lane intake.

## Project Data-Entry Workbook Lineage

After the Dataverse JSON export, the old process used workbook tooling to turn streamlined estimator apparatus rows into a task-by-task and apparatus-by-apparatus project plan. The two reference files in the current planning folder are:

1. `C:/Users/jjswe/Desktop/Project Miner PM Planning/RESA Power - Project Data Entry MASTER.xlsm`
2. `C:/Users/jjswe/Desktop/Project Miner PM Planning/Garney- Central Mesa Reuse Tracker #677562.xlsm`

The master workbook is the blank or reusable shaping surface. The Garney tracker is a populated example of the downstream project plan.

Important sheet roles:

1. `Project_Form` stores client, project, job number, start date, site, contact, project lead, and workscope names.
2. `Task_Entry` is the transitional import/input table with `Scope`, `NETA_Standard`, `Task_ID`, `Task`, `Apparatus`, `Designation`, `Drawing`, and `Apparatus_Hourrs`.
3. `All_Tasks` is the expanded task/apparatus plan with due date, notes, assessment, datasheet, completion, delays, hours, status, availability, priority, and apparatus category.
4. `All_Tasks_Billing` and `PowerBI_Data` are downstream reporting/export surfaces.

The PM lane preview now reads those workbooks as historical workflow evidence and reports project form metadata, workscope names, `Task_Entry` counts, `All_Tasks` counts, status counts, availability counts, apparatus-category counts, and formula-error counts. It does not write back to the workbooks.

The new PM lane should recreate this workflow as a governed review/import candidate:

1. estimator source rows become normalized apparatus candidates,
2. PM/Ops groups or accepts them into task rows,
3. the system preserves source workbook, sheet, and row traceability,
4. a human approves the import candidate,
5. only then may a later admitted packet write project, workpackage, task, and apparatus rows into Supabase.

## Current Delivery Target

Project Miner Temp Power is the first live PM lane pilot.

The near-term target is not a generic PM system demo. The target is a field-usable workflow before the late-May or early-June 2026 Temp Power start window.

Current prioritized task-lane status:

1. Local PM intake workbench usability - active and local-current. PM Lanes 043 through 120 have built the `/pm-review/import-intake` daily workbench, local review outputs, field-prep artifacts, grouped/disclosed panels, authority-wording guard, and predictable body-control wrappers through the Local PM Operating Queue. The next bounded local move is PM Lane 121, Local Import Exception Decision Register Body Controls.
2. Hosted PM intake parity - ready for Desktop Codex authenticated executor action, not yet accepted as green. PM Lane 041A covers existing Vercel operations-web promotion, PM Lane 041B covers existing Render mutation-seam redeploy or blocker classification, and PM Lane 076 is the current copy/paste dispatch binder. Hosted parity remains unclaimed until closeouts prove the hosted routes and four PM intake reads are current or precisely classify the remaining blocker.
3. Approval/import authority - designed but not admitted. The approval contract, approval storage plan, approval-readiness UI, and schema/adapter admission packet context exist, but approval persistence and import mutation remain blocked until hosted reads are current or precisely classified and a later packet explicitly admits the narrow write path.

Execution order remains conservative: local PM ergonomics may continue while hosted parity is pursued, but approval persistence, import mutation, work authorization, assignment, schedule, status, durable field records, and production tracking writes remain outside authority until explicitly admitted.

Olares One should support this by reducing relay friction, preserving host validation, and keeping packet/handoff evidence durable. It is not currently assumed to provide autonomous AI-to-AI queue ownership.

## Workflow Levels

Level 0 - Source Intake:
Validate the planning folder exists and the preview command resolves the expected estimator, PDF, equipment inventory, capability matrix, project data-entry workbook, and reference tracker.

Level 1 - Scope Extraction:
Read estimator line items into project, workpackage, task, and apparatus candidates. Preserve drawing references, designations, source sheet names, scope sheet names, and source row references where available.

Level 2 - Task Plan Shaping:
Transform estimator apparatus candidates into task-by-task and apparatus-by-apparatus import candidates, mirroring the old `Task_Entry` to `All_Tasks` workflow without writing production state.

Level 2A - Import Candidate Review Hardening:
Review source freshness, warning filters, exported candidate JSON, and local PM questions before any import mutation is admitted.

Level 2B - Import Admission Planning:
Review the approval contract, idempotency key, diff checks, target rows, and no-go checks that a later import packet must satisfy.

Level 2C - Approval Contract Design:
Define and validate the PM approval packet shape, candidate fingerprints, warning acceptance, human-acceptance no-go acknowledgements, actor/timestamp fields, and reviewer notes before any approval persistence exists.

Level 2D - Approval Storage Design:
Define the dedicated approval record table, future mutation route, adapter rules, idempotent replay behavior, audit/readback expectations, and rejected storage shortcuts before any schema or approval persistence exists.

Level 2D.5 - Import Intake Workbench:
Review the candidate, admission plan, approval contract, and approval storage plan from `/pm-review/import-intake` as the daily PM starting point. This is a read-only consolidation layer and does not replace the dedicated detail routes.

Level 2E - Approval Persistence:
Persist only the PM approval decision, candidate fingerprints, warning acceptance, no-go acknowledgement notes, and reviewer notes for the import candidate after a later packet admits a narrow storage path. This is not an import mutation and must not write project, workpackage, task, or apparatus rows.

Level 3 - Resource Context:
Read equipment inventory and technician capability rows so PM can understand whether the project can be staffed with available people and equipment.

Level 4 - PM Workfront:
Surface readiness, blockers, unassigned rows, PM review rows, submitted snapshots, review signals, and drillthrough links in the Vercel UI.

Level 5 - Lead/Field Execution:
Lead assigns work and field updates apparatus/checklist/issue progress through governed mutation-seam endpoints only after the relevant write path is admitted.

Level 6 - PM Review And Closeout:
PM reviews escalations, submitted snapshots, task/workpackage review, disposition history, schedule drillthroughs, and variance context before approving or returning work.

## Guardrails

1. Do not write directly from Excel to Supabase.
2. Do not treat spreadsheet rows as production state until an admitted packet opens a live-data import or write path.
3. Do not run workbook macros during read-only intake preview.
4. Do not write back to estimator, data-entry, or tracker workbooks during read-only preview.
5. Do not let Vercel become a second backend authority.
6. Do not let AI auto-assign apparatus, change statuses, mutate schedules, or write PM business state until a later packet explicitly admits that authority.
