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

## Import Approval Persistence Status Readback

PM Lane 137 adds the read-only approval persistence status seam after the repo-local approval persistence implementation.

The read seam is:

`GET /api/v1/reads/project-import-approval-status`

The status read returns:

1. current approval classification,
2. current candidate match flag,
3. approval record id, mutation id, and audit event id when a record exists,
4. approval storage availability,
5. approval record count for the current candidate,
6. storage source and read route,
7. `audit_log_used_for_current_status: false`,
8. `import_authority: not_admitted`.

The status read can classify no-record, current approved, stale, returned, rejected, unsupported, or storage-unavailable states. The current-state source is the dedicated approval record store, not audit history alone.

`/pm-review/import-intake` now consumes the status read and shows Approval Status Readback in the admission/approval and approval-readiness areas. It also includes status readback in the Approval Preview JSON, PM Brief, and Executor Handoff exports.

This is not UI approval activation and not project import. It does not add an approval button, call the approval POST route from the browser, apply hosted SQL, deploy Render/Vercel, import project rows, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

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
4. `GET /api/v1/reads/project-import-approval-storage-plan`,
5. `GET /api/v1/reads/project-import-approval-status`.

It shows candidate identity, source freshness, project location, proposed row counts, warning signals, required PM decisions, workflow gates, admission target rows, approval contract authority, the future `seam.pm_import_candidate_approvals` table, the future `/api/v1/mutations/project-import-approvals` route, hosted-parity status, and merged guardrails.

This route is a navigation and review accelerator only. It does not approve, persist, import, create schema, run SQL, write Supabase rows, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

Hosted note: PM Lane 041A/041B closeouts through PM Lane 076 are accepted for the PM intake path, and PM Lane 041C has now cleared the broader hosted mutation-seam DSN blocker. `/pm-review/import-intake` is hosted at `https://operations.apexpowerops.com`, paired hosted smoke proves operations-web plus the four mutation-seam PM intake reads are current, and deployed mutation-seam smoke now returns `200` for the DB-backed approval and schedule reads. This still does not admit approval persistence, import mutation, schedule/status writes, or production state.

PM Lane 044 updates the hosted parity proof and executor handoffs so `/pm-review/import-intake` is included in the same Vercel promotion lane as `/pm-review/import-approval-readiness`. The prior `404` hosted-route gap is now closed by the PM Lane 041A Vercel closeout.

PM Lane 076 adds the hosted parity executor dispatch binder after the local workbench through PM Lane 119. Desktop Codex executed the binder end to end on 2026-05-16: PM Lane 041A Vercel promotion is accepted green and PM Lane 041B Render PM-intake read parity is accepted green. PM Lane 041C then resolved the remaining Supabase pooler DSN blocker for DB-backed approval/schedule reads by rotating the runtime credential and updating only the existing Render `SEAM_DATABASE_URL`. The closeouts do not admit approval persistence, import mutation, schema work, SQL writes, assignment, schedule/status writes, or autonomous AI business-state mutation.

PM Lane 041C is executed and accepted closed. The secret-safe storage pattern is non-git Olares Vault as the canonical credential boundary and Render `SEAM_DATABASE_URL` as the only live app copy; repo files, handoffs, markdown notes, and repo-local `.env` files must not store the password or DSN value.

PM Lane 137 adds approval persistence status readback to the same workbench. The route now shows whether the current candidate has no approval record, a current approved record, a stale record, a return/rejection record, or unavailable approval storage. The status is informational only and keeps approval persistence/import authority separated from browser-local review.

PM Lane 138 is prepared as the next hosted executor handoff. It may apply only `apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql` and redeploy only the existing Render `apex-platform-mutation-seam` service; it may not add UI POST wiring, create approval records by live smoke, import project rows, create services, expose secrets, or mutate production business state.

PM Lane 138 is now accepted closed. Codex applied exactly migration 003 through the native Supabase connector, proved the approval table and both insert-only triggers exist, proved approval record count remains `0`, and reran the hosted mutation-seam plus paired PM-intake smokes green. The existing hosted mutation seam exposed both approval-status GET and approval POST OpenAPI registration after the schema gate, without a live approval POST, UI approval wiring, project import, assignment, schedule/status write, production tracking write, or other business-state mutation.

PM Lane 139 tightens the hosted gate evidence contract before that credentialed execution. The standard mutation-seam and paired PM-intake hosted smokes now verify approval-status GET readback and approval POST OpenAPI registration without sending a live POST, and the hosted executor closeout template now has a PM Lane 138-specific migration-003 guardrail section.

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

PM Lane 121 wraps the existing Local Import Exception Decision Register body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Source and Exception Detail, keeps the `#import-exception-register` anchor and preserves the existing disclosure, heading, browser-local pill, explanatory no-authority wording, covered/open/blocked summary count, six derived register cards, card order, dynamic detail/evidence text, status pills, quick-jump target, read seams, export behavior, and no persisted collapsed state. This is local exception-register scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 122 wraps the existing Workflow Gates body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Source and Exception Detail after the exception register, keeps the `#workflow-gates` anchor, and preserves the existing disclosure, heading, read-only pill, six gate cards, card order, detail text, status pills, quick-jump target, read seams, export references, and no persisted collapsed state. This is local workflow-gate scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 123 wraps the existing Exception Review and PM Decisions body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Source and Exception Detail after Workflow Gates, preserves the existing disclosure, heading, two detail cards, warning severity/code pills, PM decision prompt/recommended-action text, fallback empty states, export behavior, read seams, authority wording, and no persisted collapsed state. This is local exception/decision scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 124 wraps the existing Admission and Approval Contract body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Approval Prep Detail before Local Review Checklist, preserves the existing disclosure, heading, Admission Shape card, Approval Contract card, labels, values, order, fallback text, export behavior, read seams, authority wording, and no persisted collapsed state. This is local approval-prep contract scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 125 wraps the existing Local Review Checklist body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Approval Prep Detail after Admission and Approval Contract, preserves the existing disclosure, heading, checklist count, seven checklist items, checkbox behavior, clear button, existing candidate-scoped browser storage, export behavior, authority wording, and no persisted collapsed state. This is local review-prep scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 126 wraps the existing Local Approval Decision Draft body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Approval Prep Detail after Local Review Checklist, preserves the existing disclosure, heading, local-only pill, decision select, review notes textarea, local-only attestation checkbox, clear button, existing candidate-scoped browser storage, export behavior, authority wording, and no persisted collapsed state. This is local approval-decision draft scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 127 wraps the existing Local Executor Closeout Intake body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Executor Closeout Detail after Approval Prep Detail, preserves the `#executor-closeout` anchor, existing disclosure, heading, closeout count, eight checklist items, checkbox behavior, clear button, existing candidate-scoped browser storage, export behavior, authority wording, and no persisted collapsed state. This is local executor-closeout audit prep and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 128 wraps the existing Local Field Readiness Checklist body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Field Prep Detail before Local Field Questions Draft, preserves the existing disclosure, heading, field readiness count, eight checklist items, checkbox behavior, clear button, existing candidate-scoped browser storage, export behavior, authority wording, and no persisted collapsed state. This is local field-readiness prep evidence and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, work authorization, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 129 wraps the existing Local Field Questions Draft body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Field Prep Detail after Local Field Readiness Checklist, preserves the existing disclosure, heading, local-only pill, six textarea labels, clear button, existing candidate-scoped browser storage, export inclusion, derived field-prep behavior, authority wording, and no persisted collapsed state. This is local field-question draft scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, work authorization, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 130 wraps the existing Local Field Prep Queue body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Field Prep Detail after Local Field Questions Draft, preserves the `#field-prep` anchor, existing disclosure, heading, browser-local pill, derived queue rows, count summary, authority wording, and no persisted collapsed state. This is local field-prep queue scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, work authorization, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 131 wraps the existing Local Field Prep Coverage Snapshot body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Field Prep Detail after Local Field Prep Queue, preserves the existing disclosure, heading, derived pill, coverage summary, seven coverage articles, authority wording, and no persisted collapsed state. This is local field-prep coverage scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, work authorization, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 132 wraps the existing Local Field Prep Conversation Agenda body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Field Prep Detail after Local Field Prep Coverage Snapshot, preserves the existing disclosure, heading, derived pill, agenda summary, seven agenda articles, authority wording, and no persisted collapsed state. This is local field-prep conversation-agenda scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, work authorization, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 133 wraps the existing Local Field Observation Scratchpad body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Field Prep Detail after Local Field Prep Conversation Agenda, preserves the existing disclosure, heading, browser-local pill, six textarea labels, clear button, candidate-scoped browser storage, export inclusion, derived field-prep behavior, authority wording, and no persisted collapsed state. This is local field-observation scratchpad scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, work authorization, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 134 wraps the existing Approval Persistence Readiness body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The panel remains inside Authority Boundary Detail at the `#approval-readiness` anchor, preserves the existing disclosure, heading, readiness count pill, two explanatory paragraphs, six readiness gate articles, blocked authority wording, readiness calculations, and no persisted collapsed state. This is local future-authority boundary scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, work authorization, task, issue, schedule, status, durable field record, production tracking write, or production state.

PM Lane 135 wraps the existing Current PM Next Actions and Guardrails body content on `/pm-review/import-intake` in a labeled body-controls container under its already-existing default-open disclosure. The footer remains inside Authority Boundary Detail at the `#guardrails` anchor, preserves the existing disclosure, heading, two guardrail cards, action list, not-allowed list, blocked authority wording, and no persisted collapsed state. This is local final-guardrail scanning and AI/orchestration ergonomics only and does not create a new route, export action, export artifact, write path, hosted proof, approval record, import mutation, work authorization, task, issue, schedule, status, durable field record, production tracking write, or production state.

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

1. Local PM intake workbench usability - active and local-current through PM Lane 212. PM Lanes 043 through 135 built the `/pm-review/import-intake` daily workbench, PM Lane 136 added the repo-local backend approval-persistence implementation, PM Lane 137 surfaces approval persistence status readback without adding frontend POST wiring, PM Lane 140 reconciles hosted approval-readiness truth, PM Lane 141 defines the future browser approval submission packet, PM Lane 142 authors the first-row execution gate prompt without opening the live write, PM Lane 142A adds a mock-only local dry-run envelope builder, PM Lane 143 exports that dry-run envelope as local JSON review context, PM Lane 144 adds a local readiness checkpoint before the envelope is used as future packet context, PM Lane 145 exports that checkpoint as local JSON review context, PM Lane 146 bundles the envelope plus readiness checkpoint as local JSON review context, PM Lane 147 exports a local live-gate preflight as final no-write approval context, PM Lane 148 exports a local field-start preflight as day-one Temp Power readiness context, PM Lane 149 exports a local field execution gate design as the no-write bridge toward lead/field/production tracking, PM Lane 150 exports a local lead field assignment draft as the no-write PM/lead review bridge before real assignment, PM Lane 151 exports a local field authorization and assignment admission draft as the no-write packet-design bridge before authorization or assignment writes, PM Lane 152 exports a local schedule/status controls admission draft as the no-write packet-design bridge before schedule/status writes, PM Lane 153 exports a local durable field record admission draft as the no-write packet-design bridge before durable daily field record writes, PM Lane 154 exports a local production tracking admission draft as the no-write packet-design bridge before quantity, labor, apparatus, and progress tracking writes, PM Lane 155 exports a local customer reporting and completion evidence admission draft as the no-write packet-design bridge before customer-facing reports or completion evidence, PM Lane 156 exports a local financial handoff admission draft as the no-write packet-design bridge before billing, payroll, invoice, accounting, or external finance-system outputs, PM Lane 157 exports a local pilot launch binder as the one-file review bridge across approval preflight, field start, execution gate, assignment, schedule/status, durable field records, production tracking, customer reporting, and financial handoff without opening any write path, PM Lane 158 authors a dispatch-only Desktop Codex financial handoff admission design prompt without changing product code or opening a write path, PM Lane 159 exports a local pilot launch daily brief as a compact PM/lead/customer review sequence without opening any write path, PM Lane 160 exports a local pilot launch standup card as a role-based launch conversation card without opening any write path, PM Lane 161 exports a local pilot launch capture sheet as a blank review-capture artifact for PM decisions, blockers, customer/site questions, executor/AI relay follow-up, and next-packet recommendation without persisting notes, creating action items, assigning owners, creating customer commitments, or opening any write path, PM Lane 162 exports a local pilot launch follow-up packet as a copy/paste review-return artifact for VS Code Codex, Desktop Codex closeout review, and sidecar scout review without persisting review returns, creating action items, assigning owners or due dates, publishing executor output, or opening any write path, PM Lane 163 groups the existing 19 Field Prep Outputs into Field Prep Basics, Admission Drafts, and Pilot Launch Outputs without changing button labels, handlers, filenames, payloads, storage, read seams, or write boundaries, PM Lane 164 mirrors that grouping in the Output Selector, PM Lane 165 groups the Handoff Guide into Review Context, Field And Executor Context, and Approval Boundary Context, PM Lane 166 groups the Workflow Map into Intake Review Path, Field And Executor Path, and Future Authority Boundaries, PM Lane 167 groups the Open Items Lens into Local Attention Items, Executor Evidence Context, and Future Authority Blockers, PM Lane 168 groups the Local PM Intake Snapshot into Review Posture, Field Readiness Posture, and Authority Boundary Posture, PM Lane 169 groups the Local PM Operating Queue into Local Review Moves, Approval Submission Boundary, and Future Import Boundary, PM Lane 170 groups the Local Import Exception Decision Register into Source Review Signals, PM Decision Context, and Admission Boundary, PM Lane 171 groups the Workflow Gates into Source Review Gates, Approval Readiness Gates, and Future Import Boundary, PM Lane 172 groups Exception Review and PM Decisions into Exception Signals and PM Decision Context, PM Lane 173 groups Admission and Approval Contract into Admission Shape Context, Approval Contract Context, and Approval Status Context, PM Lane 174 groups Local Review Checklist into Source Review Evidence, Approval Readiness Evidence, and Write Boundary Confirmation, PM Lane 175 groups Local Approval Decision Draft into Decision Value Context, Review Notes Context, and Local Attestation Context, PM Lane 176 groups Local Approval Submission Dry Run into Dry Run Readiness Context, Future Request Boundary Context, and Local Artifact Actions Context, PM Lane 177 groups Local Executor Closeout Intake into Source and Hosted Evidence, Validation and Verdict Evidence, and Guardrails and Next Action, PM Lane 178 groups Local Field Readiness Checklist into Source and Scope Readiness, Site Access and Safety Readiness, Crew Material and Staging Readiness, and Customer Constraints and Authority Boundary, PM Lane 179 groups Local Field Questions Draft into Source and Site Questions, Crew Material and Staging Questions, and Customer Constraints and PM Follow-up, PM Lane 180 groups Local Field Prep Queue into Field Prep Inputs, Kickoff Artifact, and Authority And Production Boundary, PM Lane 181 groups Local Field Prep Coverage Snapshot into Source And Access Context, Resource And Staging Context, and Authority And Production Boundary, PM Lane 182 groups Local Field Prep Conversation Agenda into Source And Access Conversation, Resource And Staging Conversation, and Authority And Production Boundary, and PM Lane 183 groups Local Field Observation Scratchpad into Source And Area Observation, Access And Resource Observation, and PM Follow-up And Authority Boundary, and PM Lane 184 groups Approval Persistence Readiness gates into Local Review Context, Hosted Persistence Surface, and Blocked Future Write Authority, and PM Lane 185 groups Current PM Next Actions and Guardrails into Current Review Actions and Blocked Write Guardrails, and PM Lane 186 adds repeatable desktop/laptop/tablet/mobile visual QA and fixes mobile horizontal overflow through grid/card/status-row containment, and PM Lane 187 proves the phone-first field-launch path from quick jump through daily script, field prep, field questions, field observations, guardrails, field export readiness, zero mutations, and no new field-launch storage key, and PM Lane 188 exposes a browser-local field-start operator script in Daily Action panels with posture, source/access check, queue/coverage/agenda walk, context-export reminder, stop-line boundary, zero mutations, and no operator-script storage key, and PM Lane 189 adds a browser-local field-start stop-line quick review in Daily Action panels with field authority, assignment/schedule/status, durable record/production, customer/finance, and context-only boundaries, zero mutations, no export, no buttons, and no stop-line quick-review storage key, and PM Lane 190 adds a browser-local field-start customer/site questions quick review in Daily Action panels with site access/safety, customer constraints, material/staging, drawing/source, and PM follow-up/customer commitment boundaries, zero mutations, no export, no buttons, and no customer-site question-review storage key, and PM Lane 191 adds a nested browser-local PM follow-up prompt review under the customer/site panel with next-question prompts for PM, customer/site return, lead conversation, evidence/source, and next-packet boundary context, zero mutations, no export, no buttons, and no follow-up prompt storage key, and PM Lane 192 adds a sibling browser-local field-start conversation closeout prompt review under the same customer/site panel with bring-back prompts for conversation summary, customer/site return, lead/resource return, evidence/source return, and next-packet boundary context, zero mutations, no export, no buttons, no meeting-note capture, and no closeout prompt storage key, and PM Lane 193 adds a sibling browser-local field-start bring-back review queue under the same customer/site panel with source review, customer/site clarification, lead/resource clarification, and later bounded packet candidate buckets, zero mutations, no export, no buttons, no meeting-note capture, and no bring-back review queue storage key, and PM Lane 194 adds a sibling browser-local field-start source review bring-back lens under the same customer/site panel with drawing/workbook source, site note, observer/source, work-area reference, and source-review packet boundary checks, zero mutations, no export, no buttons, no meeting-note capture, and no source review lens storage key, and PM Lane 195 adds a sibling browser-local field-start customer/site clarification bring-back lens under the same customer/site panel with access/shutdown answer, escort/contact path, safety/LOTO clarification, constraint answer boundary, and customer/site promise stop-line checks, zero mutations, no export, no buttons, no meeting-note capture, and no customer/site clarification lens storage key, and PM Lane 196 adds a sibling browser-local field-start lead/resource clarification bring-back lens under the same customer/site panel with lead conversation source, crew readiness, material/equipment clarification, staging/resource limit, and lead/resource authority stop-line checks, zero mutations, no export, no buttons, no meeting-note capture, and no lead/resource clarification lens storage key, and PM Lane 197 adds a sibling browser-local field-start later bounded packet candidate bring-back lens under the same customer/site panel with future packet trigger, authority admission, evidence/context, owner/timing language, and bounded packet stop-line checks, zero mutations, no export, no buttons, no meeting-note capture, and no later bounded packet candidate lens storage key, and PM Lane 198 adds a sibling browser-local field-start bring-back summary triage strip above the detailed queue/lenses with source review, customer/site clarification, lead/resource clarification, and later bounded packet candidate context summaries, zero mutations, no export, no buttons, no meeting-note capture, and no bring-back summary triage strip storage key, and PM Lane 199 adds a sibling browser-local field-start bring-back detail jump rail above the detailed queue/lenses with direct source review, customer/site clarification, lead/resource clarification, and later bounded packet candidate lens jumps, zero mutations, no export, no buttons, no meeting-note capture, and no bring-back detail jump rail storage key, and PM Lane 200 adds a browser-local field-start bring-back lens open-context cue inside the detail jump rail that shows which existing detail lenses currently have populated local context, zero mutations, no export, no links, no buttons, no meeting-note capture, and no bring-back lens open-context cue storage key, and PM Lane 201 adds a browser-local field-start bring-back cue status legend inside the detail jump rail that explains context, review, open, and blocked status meanings, zero mutations, no export, no links, no buttons, no meeting-note capture, and no localStorage or sessionStorage cue status legend key, and PM Lane 202 adds a browser-local field-start bring-back review order hint inside the detail jump rail that explains source review, customer/site clarification, lead/resource clarification, and later bounded packet candidate review order, zero mutations, no export, no links, no buttons, no meeting-note capture, and no localStorage or sessionStorage review order hint key, and PM Lane 203 adds a browser-local field-start later bounded packet future boundary reminder inside the later bounded packet candidate lens that keeps future bounded packet candidate review as classification only, zero mutations, no export, no links, no buttons, no meeting-note capture, and no localStorage or sessionStorage future packet boundary reminder key, and PM Lane 204 adds a browser-local field-start bring-back local review closeout cue at the end of the bring-back panel that keeps the source, customer/site, lead/resource, and future packet review return as local classification only, zero mutations, no export, no links, no buttons, no meeting-note capture, and no localStorage or sessionStorage local review closeout cue key, and PM Lane 205 adds a browser-local field-start bring-back review exit summary at the end of the bring-back panel that summarizes the four local classification lanes and sends anything needing approval, import, assignment, schedule/status, field direction, report, storage, export, route, control, or write authority to a later bounded packet, zero mutations, no export, no links, no buttons, no meeting-note capture, and no localStorage or sessionStorage review exit summary key, and PM Lane 206 records a no-code panel saturation decision that parks additional field-start notelets unless fresh scan-burden evidence appears and selects approval submission/write-prep admission readiness as the next bounded PM move, with no product code, UI control, hosted action, schema change, storage key, route, or write path, and PM Lane 207 records no-code approval first-row write-prep admission readiness by confirming the PM Lane 141 through PM Lane 147 local approval-prep chain is ready for a later executor-prompt refresh only, while the exact PM Lane 142 phrase remains absent and live approval POST, first approval-row creation, project import, hosted action, schema change, route, storage, or write path remain blocked, and PM Lane 208 refreshes the first-row executor prompt and closeout checklist as no-code copy/paste execution guidance, preserving the exact PM Lane 142 phrase as the only live-write opener and admitting no live approval POST, approval row, hosted action, product code, schema change, route, storage, or write path, and PM Lane 209 drill-proves the refreshed prompt stops with STOPPED_NO_LIVE_ADMISSION when the exact PM Lane 142 phrase is absent as current admission, with no hosted smoke, browser live route, approval POST, approval row, product code, schema change, route, storage, project import, or write path.
2. Hosted PM intake parity - accepted green for the PM intake path and the broader deployed mutation-seam read surface. PM Lane 041A Vercel promotion is green, PM Lane 041B Render PM-intake read parity is green, PM Lane 076 closeouts are accepted, PM Lane 041C clears the former Supabase pooler DSN blocker for DB-backed approval/schedule reads, PM Lane 138 applies the approval persistence hosted schema gate, and PM Lane 139 tightens the reusable hosted smoke/closeout contract.
3. Approval/import authority - narrowly advanced for approval-record persistence only. PM Lane 136 adds the dedicated approval table migration, insert-only adapter, PM-only mutation route, idempotent replay, audit linkage, and readback classifier; PM Lane 137 adds a read-only approval status route and UI/export surfacing; PM Lane 138 applies the hosted approval table/schema gate with zero approval rows; PM Lane 139 adds proof that hosted gate smokes check the approval-status GET and approval POST OpenAPI registration; PM Lane 141 defines the future browser approval submission packet; PM Lane 142 defines the exact future live-write admission gate; PM Lane 142A locally rehearses the approval envelope without calling the mutation route; PM Lane 143 exports the dry-run envelope without calling the mutation route; PM Lane 144 classifies the local dry-run readiness without calling the mutation route; PM Lane 145 exports that readiness evidence without calling the mutation route; PM Lane 146 bundles the envelope and readiness evidence without calling the mutation route; PM Lane 147 exports the live-gate preflight without calling the mutation route. Live frontend approval POST and all project import, workpackage, task, apparatus, assignment, schedule, status, durable field record, and production tracking writes remain blocked until separate packets explicitly admit them.

Execution order remains conservative: repo-local approval-record persistence may advance only inside the dedicated table/adapter/route boundary, while live schema application, hosted deployment, import mutation, work authorization, assignment, schedule, status, durable field records, and production tracking writes remain outside authority until explicitly admitted.

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

PM Lane 136 implements the first repo-local version of Level 2E. The admitted write path is limited to `seam.pm_import_candidate_approvals` plus one linked audit append through `POST /api/v1/mutations/project-import-approvals`; idempotent replays return the original mutation and audit IDs, and readback classification is table-backed rather than audit-log-only. This lane does not apply live SQL, deploy Render or Vercel, wire a frontend approval button, import project/work rows, or mutate assignment, schedule, status, durable field records, or production tracking.

PM Lane 137 makes Level 2E visible to the PM workbench without adding write authority. `GET /api/v1/reads/project-import-approval-status` reports the current table-backed approval classification, storage availability, candidate match, record count, route/source, and import authority. `/pm-review/import-intake` displays that readback and includes it in local exports, while keeping the UI approval POST, project import, assignment, schedule, status, and production tracking paths blocked.

PM Lane 141 defines the browser approval submission bridge for Level 2E without executing it. The design locks the future route to `POST /api/v1/mutations/project-import-approvals`, requires `mutation_class: C`, `action_type: persist_import_approval`, matching envelope/payload idempotency keys, exact current candidate fingerprints, exact warning-code acceptance, exact human-acceptance no-go acknowledgements, nonempty PM review notes, and readback proof after any later admitted submission. It also states that first approval-row creation must be owned by a separate explicit execution gate and still must not import project, workpackage, task, or apparatus rows.

PM Lane 142 authors that separate explicit execution gate without using it. The dispatch packet and copy/paste prompt tell a future Desktop Codex or coordinator executor to stop unless the exact live-write admission phrase is present. If it is present, the future executor may proceed through local mocked browser validation, hosted operations-web promotion if required, one browser approval persistence POST, same-payload idempotent replay proof, approval-status readback, and unchanged downstream domain-count proof. Project import remains blocked.

PM Lane 142A implements the local mocked browser approval dry run without using the live gate. `/pm-review/import-intake` can now build a review-only approval envelope from the current candidate, source fingerprint, local decision draft, checked review evidence, warning acceptance, no-go acknowledgement, approval-status readback, and future route. The dry run stays on-screen, sends no network request, creates no approval record, and keeps project import blocked.

PM Lane 143 implements the local dry-run envelope export without using the live gate. `/pm-review/import-intake` can now download the mock-only approval envelope as JSON for review or later packet context while refreshing the on-screen preview, sending no network request, creating no approval record, and keeping project import blocked.

PM Lane 144 implements the local dry-run readiness checkpoint without using the live gate. `/pm-review/import-intake` now shows the readiness of source context, warning review, local decision draft, no-go review, approval readback, and live-write authority before the mock envelope is exported or used as later packet context.

PM Lane 145 implements the local dry-run readiness export without using the live gate. `/pm-review/import-intake` can now download the readiness checkpoint as JSON for review or later packet context while sending no network request, creating no approval record, and keeping project import blocked.

PM Lane 146 implements the local approval review bundle export without using the live gate. `/pm-review/import-intake` can now download one JSON review artifact containing the dry-run envelope, readiness checkpoint, artifact names, review sequence, live-write gate phrase, and blocked boundaries while sending no network request, creating no approval record, and keeping project import blocked.

PM Lane 147 implements the local approval live-gate preflight export without using the live gate. `/pm-review/import-intake` can now download one JSON preflight artifact containing the PM Lane 146 review bundle, preflight status counts, approval readback, admission no-go posture, live gate status, required PM Lane 142 phrase, and blocked downstream boundaries while sending no network request, creating no approval record, and keeping project import blocked.

PM Lane 148 implements the local field-start preflight export without opening field execution or production tracking. `/pm-review/import-intake` can now download one JSON preflight artifact containing field questions context, field-readiness evidence, observation context, field-prep queue status, coverage status, agenda status, linked field-prep artifact names, and explicit blocked field/production boundaries while sending no network request, creating no durable field record, and keeping field authorization, assignment, schedule, status, and production tracking blocked.

PM Lane 149 implements the local field execution gate design export without opening field execution or production tracking. `/pm-review/import-intake` can now download one JSON design artifact containing the field-start preflight summary, future route map, minimum admission packet sequence, execution gate statuses, and explicit authority boundary flags for approval first row, project import, lead assignment, schedule/status controls, durable field records, and production tracking while sending no network request and keeping all write paths blocked.

PM Lane 150 implements the local lead field assignment draft export without opening lead assignment, field execution, or production tracking. `/pm-review/import-intake` can now download one JSON draft artifact containing field-start preflight context, field execution gate summary, local prep source files, proposed PM/lead handoff sequence, and explicit no-write assignment boundary flags while sending no network request and keeping lead selection, crew assignment, field authorization, schedule/status, durable field records, and production tracking blocked.

PM Lane 151 implements the local field authorization and assignment admission draft export without opening field authorization, lead assignment, or production tracking. `/pm-review/import-intake` can now download one JSON admission draft artifact containing field execution gate context, lead assignment draft context, proposed field authorization and assignment packet sequence, required proof list, proposed routes marked `not_admitted`, and explicit authority boundary flags while sending no network request and keeping field authorization, lead/crew assignment, schedule/status, durable field records, and production tracking blocked.

PM Lane 152 implements the local schedule/status controls admission draft export without opening schedule or status mutations. `/pm-review/import-intake` can now download one JSON admission draft artifact containing field authorization and assignment context, proposed schedule/status packet sequence, required proof list, proposed routes marked `not_admitted`, and explicit authority boundary flags while sending no network request and keeping schedule plans, status transitions, schedule/status routes, durable field records, and production tracking blocked.

PM Lane 153 implements the local durable field record admission draft export without opening durable field record, field evidence, or production tracking mutations. `/pm-review/import-intake` can now download one JSON admission draft artifact containing schedule/status controls context, proposed durable field record packet sequence, required proof list, proposed routes marked `not_admitted`, and explicit authority boundary flags while sending no network request and keeping durable field records, daily field evidence, production tracking, customer reporting, billing, and payroll outputs blocked.

PM Lane 154 implements the local production tracking admission draft export without opening production quantity, labor, apparatus, progress, customer reporting, billing, or payroll mutations. `/pm-review/import-intake` can now download one JSON admission draft artifact containing durable field record context, proposed production tracking packet sequence, required proof list, proposed routes marked `not_admitted`, and explicit authority boundary flags while sending no network request and keeping production tracking, customer-facing completion evidence, customer reporting, billing, and payroll outputs blocked.

PM Lane 155 implements the local customer reporting and completion evidence admission draft export without opening customer report, completion evidence, billing, payroll, or accounting mutations. `/pm-review/import-intake` can now download one JSON admission draft artifact containing production tracking context, proposed customer reporting packet sequence, required proof list, proposed routes marked `not_admitted`, and explicit authority boundary flags while sending no network request and keeping customer report creation, completion evidence creation, customer delivery, billing, payroll, and accounting outputs blocked.

PM Lane 156 implements the local financial handoff admission draft export without opening billing export, payroll export, invoice, accounting, payroll record, or external finance-system mutations. `/pm-review/import-intake` can now download one JSON admission draft artifact containing customer reporting context, proposed billing/payroll/accounting boundary sequence, required proof list, proposed routes marked `not_admitted`, and explicit authority boundary flags while sending no network request and keeping billing export creation, payroll export creation, invoice creation, accounting posting, payroll processing, and external finance-system sync blocked.

PM Lane 157 implements the local pilot launch binder export without opening approval, import, field, production, customer, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` can now download one JSON binder artifact containing the approval live-gate preflight, field-start context, field execution gate, lead/assignment/schedule/durable/production/customer/financial draft chain, source artifact manifest, next packet options, and blocked write boundaries while sending no network request and keeping every live write path blocked.

PM Lane 158 authors the financial handoff admission design executor dispatch without opening any product, hosted, approval, import, field, production, customer, billing, payroll, invoice, accounting, or external finance-system write path. The dispatch prompt allows Desktop Codex to write exactly one closeout containing a design-only financial handoff boundary recommendation for later VS Code Codex review.

PM Lane 159 implements the local pilot launch daily brief export without opening approval, import, field, production, customer, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` can now download one JSON daily brief artifact containing today's PM/lead/customer review sequence, daily brief items, the source artifact manifest from the pilot launch binder, next packet options, and blocked write boundaries while sending no network request and keeping every live write path blocked.

PM Lane 160 implements the local pilot launch standup card export without opening approval, import, field, production, customer, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` can now download one JSON standup card artifact containing PM, field lead, customer/site contact, and executor/AI relay role cards, no-go checks, local capture prompts, PM Lane 159 daily-brief lineage, next packet options, and blocked write boundaries while sending no network request and creating no assignments, field direction, customer commitments, meeting action items, or live writes.

PM Lane 161 implements the local pilot launch capture sheet export without opening approval, import, field, production, customer, meeting-note, action-item, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` can now download one JSON capture sheet artifact containing PM Lane 160 standup-card lineage, blank local prompts for PM decisions, field-start blockers, customer/site questions, executor/AI relay follow-up, and next-packet recommendation, inherited no-go checks, handoff rules, and blocked write boundaries while sending no network request and creating no notes, action items, assignments, field direction, customer commitments, or live writes.

PM Lane 162 implements the local pilot launch follow-up packet export without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` can now download one JSON follow-up packet artifact containing PM Lane 161 capture-sheet lineage, copy/paste review-return sections for VS Code Codex, Desktop Codex closeout review, and sidecar scout review, inherited no-go checks, review-return rules, and blocked write boundaries while sending no network request and creating no notes, action items, owners, due dates, assignments, field direction, customer commitments, executor publications, hosted writes, or live writes.

PM Lane 163 implements local field-prep output subgrouping without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups the existing 19 Field Prep Outputs into Field Prep Basics, Admission Drafts, and Pilot Launch Outputs while preserving every existing button label, handler, filename, payload, storage behavior, read seam, export content, and write boundary.

PM Lane 164 implements local output-selector group parity without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups the browser-local Output Selector into Review Outputs, Executor Output, Field Prep Basics, Admission Drafts, and Pilot Launch Outputs so the selector mirrors the existing output action rail while preserving every existing export action, button label, handler, filename, payload, storage behavior, read seam, export content, and write boundary.

PM Lane 165 implements local handoff-guide grouping without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups the browser-local Handoff Guide into Review Context, Field And Executor Context, and Approval Boundary Context while preserving the same five advisory links, labels, hrefs, dynamic text, disclosure behavior, storage behavior, read seams, export content, and write boundaries.

PM Lane 166 implements local workflow-map grouping without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups the browser-local Workflow Map into Intake Review Path, Field And Executor Path, and Future Authority Boundaries while preserving the same seven advisory links, labels, hrefs, dynamic text, disclosure behavior, storage behavior, read seams, export content, and write boundaries.

PM Lane 167 implements local open-items lens grouping without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups the browser-local Open Items Lens into Local Attention Items, Executor Evidence Context, and Future Authority Blockers while preserving the same six advisory links, labels, hrefs, dynamic text, disclosure behavior, storage behavior, read seams, export content, and write boundaries.

PM Lane 168 implements local PM intake snapshot grouping without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups the browser-local Snapshot into Review Posture, Field Readiness Posture, and Authority Boundary Posture while preserving the same six snapshot cards, labels, detail/evidence text, status pills, summary count, disclosure behavior, storage behavior, read seams, export content, and write boundaries.

PM Lane 169 implements local PM operating queue grouping without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups the browser-local Operating Queue into Local Review Moves, Approval Submission Boundary, and Future Import Boundary while preserving the same seven queue cards, labels, dynamic detail text, status pills, complete/next/blocked summary count, disclosure behavior, storage behavior, read seams, export references, and write boundaries.

PM Lane 170 implements local import exception register grouping without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups the browser-local Import Exception Decision Register into Source Review Signals, PM Decision Context, and Admission Boundary while preserving the same six register cards, labels, dynamic detail/evidence text, status pills, covered/open/blocked summary count, disclosure behavior, storage behavior, read seams, export content, and write boundaries.

PM Lane 171 implements local workflow gates grouping without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups the read-only Workflow Gates into Source Review Gates, Approval Readiness Gates, and Future Import Boundary while preserving the same six gate cards, labels, dynamic detail text, status pills, disclosure behavior, storage behavior, read seams, export content, and write boundaries.

PM Lane 172 implements local exception and decision detail grouping without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups Exception Review and PM Decisions into Exception Signals and PM Decision Context while preserving the same two top-level detail cards, warning rendering, decision rendering, warning severity/code pills, prompt and recommended-action text, fallback empty states, disclosure behavior, storage behavior, read seams, export content, and write boundaries.

PM Lane 173 implements local admission and approval contract grouping without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups Admission Shape, Approval Contract, and Approval Status Readback into Admission Shape Context, Approval Contract Context, and Approval Status Context while preserving the same three top-level contract cards, admission plan values, target-row/no-go readback, approval contract values, approval status readback, no-write sentence, disclosure behavior, storage behavior, read seams, export content, and write boundaries.

PM Lane 174 implements local review checklist grouping without opening approval, import, field, production, customer, meeting-note, action-item, review-return, billing, payroll, invoice, accounting, or external finance-system mutations. `/pm-review/import-intake` now groups the seven Local Review Checklist items into Source Review Evidence, Approval Readiness Evidence, and Write Boundary Confirmation while preserving the same checklist labels/details, checkbox behavior, candidate-scoped browser storage, clear button behavior, export inclusion, disclosure behavior, read seams, and write boundaries.

PM Lane 175 executes the local Approval Decision Draft Grouping tranche. The Local Approval Decision Draft now groups the existing Decision draft select, Review notes draft textarea, and Local-only draft attestation checkbox into Decision Value Context, Review Notes Context, and Local Attestation Context while preserving the same decision behavior, notes behavior, attestation behavior, candidate-scoped browser storage, clear button behavior, export inclusion, disclosure behavior, read seams, and write boundaries.

PM Lane 176 executes the local Approval Submission Dry Run Grouping tranche. The Local Approval Submission Dry Run now groups the existing readiness checkpoint, future route/local draft gate/write boundary cards, and local artifact buttons/status/preview into Dry Run Readiness Context, Future Request Boundary Context, and Local Artifact Actions Context while preserving the same dry-run builders, export handlers, filenames, payloads, clear behavior, no-request behavior, disclosure behavior, read seams, and write boundaries.

PM Lane 177 executes the local Executor Closeout Intake Grouping tranche. The Local Executor Closeout Intake now groups the same eight browser-local closeout evidence checklist items into Source and Hosted Evidence, Validation and Verdict Evidence, and Guardrails and Next Action while preserving the same checkbox behavior, candidate-scoped browser storage, clear button behavior, export inclusion, disclosure behavior, read seams, and write boundaries.

PM Lane 178 executes the local Field Readiness Checklist Grouping tranche. The Local Field Readiness Checklist now groups the same eight browser-local field-prep evidence checklist items into Source and Scope Readiness, Site Access and Safety Readiness, Crew Material and Staging Readiness, and Customer Constraints and Authority Boundary while preserving the same checkbox behavior, candidate-scoped browser storage, clear button behavior, export inclusion, disclosure behavior, read seams, and write boundaries.

PM Lane 179 executes the local Field Questions Draft Grouping tranche. The Local Field Questions Draft now groups the same six browser-local field-question inputs into Source and Site Questions, Crew Material and Staging Questions, and Customer Constraints and PM Follow-up while preserving the same textarea behavior, candidate-scoped browser storage, clear button behavior, export inclusion, disclosure behavior, read seams, and write boundaries.

PM Lane 180 executes the local Field Prep Queue Grouping tranche. The Local Field Prep Queue now groups the same five derived browser-local queue cards into Field Prep Inputs, Kickoff Artifact, and Authority And Production Boundary while preserving the same derived status logic, summary count, `#field-prep` anchor, disclosure behavior, no-storage posture, export references, read seams, and write boundaries.

PM Lane 181 executes the local Field Prep Coverage Snapshot Grouping tranche. The Local Field Prep Coverage Snapshot now groups the same seven derived browser-local coverage cards into Source And Access Context, Resource And Staging Context, and Authority And Production Boundary while preserving the same derived status logic, summary count, disclosure behavior, no-storage posture, export references, read seams, and write boundaries.

PM Lane 182 executes the local Field Prep Conversation Agenda Grouping tranche. The Local Field Prep Conversation Agenda now groups the same seven derived browser-local agenda cards into Source And Access Conversation, Resource And Staging Conversation, and Authority And Production Boundary while preserving the same derived status logic, summary count, disclosure behavior, no-storage posture, export references, read seams, and write boundaries.

PM Lane 183 executes the local Field Observation Scratchpad Grouping tranche. The Local Field Observation Scratchpad now groups the same six browser-local observation fields into Source And Area Observation, Access And Resource Observation, and PM Follow-up And Authority Boundary while preserving the same textarea behavior, candidate-scoped browser storage, clear button behavior, export inclusion, downstream field-prep behavior, disclosure behavior, read seams, and write boundaries.

PM Lane 184 executes the local Approval Persistence Readiness Grouping tranche. The Approval Persistence Readiness panel now groups the same six gate cards into Local Review Context, Hosted Persistence Surface, and Blocked Future Write Authority while preserving the Approval Status Readback card, readiness count, gate titles/details/status logic, disclosure behavior, no-storage posture, route/quick-jump anchors, read seams, export references, and write boundaries.

PM Lane 185 executes the local Current PM Next Actions and Guardrails Grouping tranche. The Current PM Next Actions and Guardrails footer now groups the same two cards into Current Review Actions and Blocked Write Guardrails while preserving the `#guardrails` anchor, footer heading, action list text/order, not-allowed list fallback rendering, disclosure behavior, no-storage posture, route/quick-jump behavior, read seams, export references, and write boundaries.

PM Lane 186 executes the local PM Intake Workbench Visual QA And Mobile Scan tranche. The existing read-only PM import-intake smoke now checks 1440x900, 1366x768, 1024x768, 390x844, and 360x800 viewports for horizontal overflow, visible key workbench surfaces, and desktop/mobile group column behavior. The scan caught mobile overflow from long grouped workbench content, and the fix keeps existing grid/card/status primitives inside the viewport with min-width containment, long-token wrapping, and mobile wrapping for status/link rows while preserving all PM write guardrails.

PM Lane 187 executes the local PM Intake Field Launch Mobile Use Path tranche. The Project Miner intake workflow now has a phone-first proof from quick jump to Daily Script, Daily Script Minute 3 to Field Prep, field questions, field observations, field-prep export readiness, and guardrails at `390x844`, without approving, importing, authorizing field work, assigning crews, scheduling/statusing work, creating durable field records, production tracking, customer reports, or finance outputs.

PM Lane 188 executes the local PM Intake Field Start Operator Script tranche. The Project Miner intake workflow now has a Daily Action operator script for morning-of field-start review, deriving posture, source/access checks, field-prep queue/coverage/agenda, context-export reminders, and stop-line guardrails from existing local state without approving, importing, authorizing field work, assigning crews, scheduling/statusing work, creating durable field records, production tracking, customer reports, or finance outputs.

PM Lane 189 executes the local PM Intake Field Start Stop-Line Quick Review tranche. The Project Miner intake workflow now has a Daily Action stop-line panel for phone-first confirmation that field authority, assignment/schedule/status, durable record/production, customer/finance, and context-only boundaries remain blocked before the Temp Power field-start discussion.

PM Lane 190 executes the local PM Intake Field Start Customer/Site Questions Quick Review tranche. The Project Miner intake workflow now has a Daily Action customer/site questions panel for phone-first confirmation that site access/safety, customer constraints, material/staging, drawing/source, and PM follow-up/customer commitment boundaries remain local conversation context before the Temp Power field-start discussion.

PM Lane 191 executes the local PM Intake Field Start PM Follow-up Prompt Review tranche. The Project Miner intake workflow now has a nested prompt review inside the customer/site questions panel for phone-first confirmation of the next PM follow-up, customer/site return, lead conversation, evidence/source, and next-packet boundary questions before the Temp Power field-start discussion.

PM Lane 192 executes the local PM Intake Field Start Conversation Closeout Prompt Review tranche. The Project Miner intake workflow now has a sibling prompt review inside the customer/site questions panel for phone-first confirmation of what to bring back after the Temp Power field-start discussion: conversation summary, customer/site return, lead/resource return, evidence/source return, and next-packet boundary questions.

PM Lane 193 executes the local PM Intake Field Start Bring-Back Review Queue tranche. The Project Miner intake workflow now has a sibling queue inside the customer/site questions panel for phone-first classification of returned field-start conversation items: source review, customer/site clarification, lead/resource clarification, and later bounded packet candidate buckets remain local review context only.

PM Lane 194 executes the local PM Intake Field Start Source Review Bring-Back Lens tranche. The Project Miner intake workflow now has a sibling source review lens inside the customer/site questions panel for phone-first review of returned drawing/workbook source, site-note source, observer/source context, work-area reference, and source-review packet boundary items before any later bounded packet.

PM Lane 195 executes the local PM Intake Field Start Customer/Site Clarification Bring-Back Lens tranche. The Project Miner intake workflow now has a sibling customer/site clarification lens inside the customer/site questions panel for phone-first review of returned access/shutdown answers, escort/contact path, safety/LOTO clarification, constraint answer boundary, and customer/site promise stop-line items before any later bounded packet.

PM Lane 196 executes the local PM Intake Field Start Lead/Resource Clarification Bring-Back Lens tranche. The Project Miner intake workflow now has a sibling lead/resource clarification lens inside the customer/site questions panel for phone-first review of returned lead conversation source, crew readiness, material/equipment clarification, staging/resource limit, and lead/resource authority stop-line items before any later bounded packet.

PM Lane 197 executes the local PM Intake Field Start Later Bounded Packet Candidate Bring-Back Lens tranche. The Project Miner intake workflow now has a sibling later bounded packet candidate lens inside the customer/site questions panel for phone-first review of returned future packet trigger, authority admission, evidence/context, owner/timing language, and bounded packet stop-line items before any later bounded packet.

PM Lane 199 executes the local PM Intake Field Start Bring-Back Detail Jump Rail tranche. The Project Miner intake workflow now has a sibling detail jump rail inside the customer/site questions panel for phone-first movement from the summary triage strip into the exact source review, customer/site clarification, lead/resource clarification, or later bounded packet candidate detail lens without creating notes, tasks, owners, due dates, assignments, reports, routes, storage keys, or write paths.

PM Lane 200 executes the local PM Intake Field Start Bring-Back Lens Open-Context Cue tranche. The Project Miner intake workflow now has a colocated cue inside the detail jump rail for phone-first visibility into which bring-back detail lenses currently have populated local context before Jason opens a lens, without creating another panel, notes, links, buttons, tasks, owners, due dates, assignments, reports, routes, storage keys, or write paths.

PM Lane 201 executes the local PM Intake Field Start Bring-Back Cue Status Legend tranche. The Project Miner intake workflow now has a colocated legend inside the detail jump rail for phone-first explanation of context, review, open, and blocked status words before Jason opens a bring-back lens, without creating another workflow action, notes, links, buttons, tasks, owners, due dates, assignments, reports, routes, storage keys, or write paths.

PM Lane 202 executes the local PM Intake Field Start Bring-Back Review Order Hint tranche. The Project Miner intake workflow now has a colocated hint inside the detail jump rail for phone-first review order: source review first, customer/site clarification second, lead/resource clarification third, and later bounded packet candidate only for future packet classification, without creating another workflow action, notes, links, buttons, tasks, owners, due dates, assignments, reports, routes, storage keys, or write paths.

PM Lane 203 executes the local PM Intake Field Start Bring-Back Future Packet Boundary Reminder tranche. The Project Miner intake workflow now has a colocated reminder inside the later bounded packet candidate lens that keeps future bounded packet candidate review as classification only, without creating another workflow action, notes, links, buttons, tasks, owners, due dates, assignments, reports, routes, storage keys, controls, or write paths.

PM Lane 204 executes the local PM Intake Field Start Bring-Back Local Review Closeout Cue tranche. The Project Miner intake workflow now has a final colocated cue at the end of the bring-back panel that keeps source review, customer/site clarification, lead/resource clarification, and future packet classification returns as local review only, without creating another workflow action, notes, links, buttons, tasks, owners, due dates, assignments, reports, routes, storage keys, controls, or write paths.

PM Lane 205 executes the local PM Intake Field Start Bring-Back Review Exit Summary tranche. The Project Miner intake workflow now has a final summary at the end of the bring-back panel that compresses the return into source review, customer/site clarification, lead/resource clarification, and future packet question as local classifications only, while anything needing approval submission, import, assignment, schedule/status, field direction, customer report, storage, export, route, control, or write authority remains a later bounded packet, without creating another workflow action, notes, links, buttons, tasks, owners, due dates, assignments, reports, routes, storage keys, controls, or write paths.

PM Lane 206 executes the no-code PM Intake Panel Saturation And Next Write-Prep Selection tranche. The Project Miner intake workflow now treats the field-start bring-back panel as saturated enough for the current local review run and parks further display-only note additions unless new scan-burden evidence appears. The next selected bounded move is approval submission/write-prep admission readiness, with no live approval POST or project import write admitted by this lane.

PM Lane 207 executes the no-code Approval First-Row Write-Prep Admission Readiness tranche. The Project Miner intake workflow now treats PM Lane 141 through PM Lane 147 as enough local proof to refresh a later first-row executor prompt, while the exact PM Lane 142 phrase remains absent and no live approval POST, approval row, project import write, or downstream PM business-state write is admitted by this lane.

PM Lane 208 executes the no-code Approval First-Row Executor Prompt Refresh tranche. The Project Miner intake workflow now has refreshed future-executor copy/paste guidance for the first approval-row gate, while the exact PM Lane 142 phrase remains absent and no live approval POST, approval row, project import write, or downstream PM business-state write is admitted by this lane.

PM Lane 209 executes the no-code Approval First-Row No-Admission Stop Drill tranche. The Project Miner intake workflow now has proof that the refreshed first-row executor prompt stops with `STOPPED_NO_LIVE_ADMISSION` when the exact PM Lane 142 phrase is absent as current admission, with no hosted smoke, browser live route, live approval POST, approval row, project import write, or downstream PM business-state write admitted by this lane.

PM Lane 210 executes the no-code Approval First-Row Live-Admission Evidence Checklist tranche. The Project Miner intake workflow now has a concise checklist for the future live approval-row decision: exact phrase admission, source floor, candidate identity, PM decision and notes, local zero-mutation proof, hosted readiness after admission, pre-write row count, one browser-path approval POST, one same-payload idempotent replay, approval-status readback, unchanged downstream counts, and secret-free closeout. The exact PM Lane 142 phrase remains absent as current admission in this lane, so no hosted smoke, browser live route, live approval POST, approval row, project import write, or downstream PM business-state write is admitted by this lane.

PM Lane 211 executes the no-code Approval First-Row Live-Admission Readiness Review Packet tranche. The Project Miner intake workflow now has a Jason-reviewable packet for the future live approval-row decision with the safe label `READY_FOR_JASON_REVIEW_NOT_AUTHORIZED`, no-authorization wording, review questions, no-live decision labels, future executor boundaries, downstream mutation boundaries, and stop conditions. The exact PM Lane 142 phrase remains absent as current admission in this lane, so no hosted smoke, browser live route, live approval POST, approval row, project import write, or downstream PM business-state write is admitted by this lane.

PM Lane 212 executes the no-code Approval First-Row Admission Hold And Evidence Gap Closeout tranche. The Project Miner intake workflow now records the current approval first-row state as `STOPPED_NO_LIVE_ADMISSION_WITH_EVIDENCE_GAP_CLOSEOUT`: Lane 211 is reviewable but not authorization, and the exact PM Lane 142 phrase remains absent as current admission. The closeout names the evidence gaps that block live execution and keeps hosted smoke, browser live route, live approval POST, approval row, project import write, and downstream PM business-state writes blocked until a later explicit admission packet.

PM Lane 213 executes the no-code Approval First-Row No-Live Decision Return And Evidence Refresh Packet tranche. The Project Miner intake workflow now returns the first approval-row decision to Jason as `READY_FOR_JASON_DECISION_NOT_AUTHORIZED_NO_LIVE_REFRESH` with the bounded options to hold no-live, return with questions, or provide the exact PM Lane 142 phrase later as current admission for a separate admitted packet. This lane allows only repo-local evidence refresh and keeps hosted smoke, browser live route, live approval POST, approval row, project import write, and downstream PM business-state writes blocked.

PM Lane 214 executes the no-code Approval First-Row No-Live Decision Return Closeout And Question Packet tranche. The Project Miner intake workflow now has a concise Jason question packet under `READY_FOR_JASON_QUESTIONS_NOT_AUTHORIZED_NO_LIVE_CLOSEOUT` covering hold/no-live posture, missing or stale candidate/fingerprint/PM decision/review-note/warning/no-go fields, evidence-gap closeout, and whether any later live execution will require exact admission in a separate turn. This lane keeps hosted smoke, browser live route, live approval POST, approval row, project import write, and downstream PM business-state writes blocked.

PM Lane 215 executes the no-code Approval First-Row No-Live Evidence Gap Triage And Jason Question Closeout Packet tranche. The Project Miner intake workflow now classifies the approval first-row gaps under `READY_FOR_JASON_QUESTION_CLOSEOUT_NOT_AUTHORIZED_NO_LIVE_GAP_TRIAGE`: repo-local lane evidence is confirmed, live-use candidate/fingerprint/warning context is stale, PM decision and notes are absent, and hosted readiness plus approval-write proof remains deferred. This lane keeps hosted smoke, browser live route, live approval POST, approval row, project import write, and downstream PM business-state writes blocked.

PM Lane 216 executes the no-code Approval First-Row No-Live Evidence Gap Closeout And Hold Continuation Packet tranche. The Project Miner intake workflow now parks the approval first-row branch at `APPROVAL_BRANCH_PARKED_NO_LIVE_HOLD_CONTINUES` and returns PM focus to non-live readiness work: field-start context packaging, source/customer/lead clarification capture, local evidence review ergonomics, Temp Power day-one readiness surfaces, and no-live import/field readiness prompts. This lane keeps hosted smoke, browser live route, live approval POST, approval row, project import write, and downstream PM business-state writes blocked.

PM Lane 217 executes the no-code Project Miner No-Live Readiness Return Packet tranche. The Project Miner intake workflow now routes the next safe PM move into a field-start clarification review return under `PROJECT_MINER_READINESS_RETURN_NO_LIVE_NO_WRITE`, covering project identity, source/scope floor, customer/site questions, lead/resource questions, import-candidate context, blocked authority, and next packet options from existing local surfaces. This lane keeps hosted smoke, browser live route, live approval POST, approval row, project import write, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes blocked.

PM Lane 218 executes the no-code Project Miner Field-Start Clarification Review Return Packet tranche. The Project Miner intake workflow now has a compact local return package under `PROJECT_MINER_FIELD_START_CLARIFICATION_REVIEW_RETURN_NO_LIVE_NO_WRITE`: project identity, source evidence reviewed, customer/site clarification, lead/resource clarification, import-candidate context, known no-go or blocked authority, and requested next packet. This lane keeps hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes blocked.

PM Lane 219 executes the no-code Project Miner Field-Start Clarification Return Closeout And Next-Packet Selection tranche. The Project Miner intake workflow now has a local next-packet classifier under `PROJECT_MINER_FIELD_START_CLARIFICATION_RETURN_CLOSEOUT_NEXT_PACKET_SELECTION_NO_LIVE_NO_WRITE`: hold, source refresh, later approval prep, or later import prep, with customer/site, lead/resource, UI scan-burden, and authority-required stop conditions tracked as context flags. This lane keeps hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes blocked.

PM Lane 220 executes the no-code Project Miner Source Context Refresh No-Live Packet tranche. The Project Miner intake workflow now has a metadata-only source context refresh under `PROJECT_MINER_SOURCE_CONTEXT_REFRESH_NO_LIVE_METADATA_ONLY_NO_WRITE`: local source filenames, sizes, modified times, expected estimator export module paths, tracker workbook path, and Project Data Entry workbook path are recorded as review anchors only. The next safe packet should classify each source artifact as current source candidate, reference only, resource context, unknown/stale, or authority-required stop, while workbook content reads, source PDF content reads, macro execution, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked.

PM Lane 221 executes the no-code Project Miner Source Artifact Role Confirmation No-Live Packet tranche. The Project Miner intake workflow now has a source-role confirmation matrix under `PROJECT_MINER_SOURCE_ARTIFACT_ROLE_CONFIRMATION_NO_LIVE_METADATA_ONLY_NO_CONTENT_READ_NO_WRITE`: current source candidate, reference only, resource context, unknown/stale, and stop authority required are the only role buckets, and every artifact remains `NEEDS_JASON_CONFIRMATION`. This lane keeps Desktop Codex source classification deferred until a later explicit packet and keeps workbook content reads, source PDF content reads, macro execution, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes blocked.

PM Lane 222 executes the no-code Project Miner Source Role Return Classifier No-Live Packet tranche. The Project Miner intake workflow now has a return classifier under `PROJECT_MINER_SOURCE_ROLE_RETURN_CLASSIFIER_NO_LIVE_NO_CONTENT_READ_NO_WRITE` that reuses Lane 221's five role buckets and defaults to `NO_JASON_SOURCE_ROLE_RETURN_PRESENT_HOLD_NO_LIVE` because no current source-role return is present. No artifact becomes source truth, Desktop Codex source classification remains deferred, and workbook content reads, source PDF content reads, macro execution, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked.

PM Lane 223 executes the no-code Project Miner Source Role Return Closeout And Next-Packet Selection No-Live Packet tranche. The Project Miner intake workflow now closes the no-return condition under `PROJECT_MINER_SOURCE_ROLE_RETURN_CLOSEOUT_NEXT_PACKET_SELECTION_NO_LIVE_NO_CONTENT_READ_NO_WRITE`: no current Jason source-role return is present, `NO_JASON_SOURCE_ROLE_RETURN_PRESENT_HOLD_NO_LIVE` remains a source-authority hold only, and the selected next move is `NO_RETURN_HOLD_AND_ASK_JASON_SOURCE_CONFIRMATION`. PM Lane 224 should produce a compact Jason-facing source confirmation question packet. Desktop Codex source classification remains deferred, and workbook content reads, source PDF content reads, macro execution, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked.

PM Lane 224 executes the no-code Project Miner Source Confirmation Question Packet No-Live tranche. The Project Miner intake workflow now has a compact Jason-facing source answer form under `PROJECT_MINER_SOURCE_CONFIRMATION_QUESTION_PACKET_NO_LIVE_NO_CONTENT_READ_NO_WRITE`: current source candidates, reference only, resource context, unknown/stale, stop-authority-required, allowed later bounded content review, metadata-only, separate source package expected, recommended next packet, and notes. The next safe packet is PM Lane 225 source confirmation return intake and classification. Desktop Codex source classification remains deferred, and workbook content reads, source PDF content reads, macro execution, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked.

PM Lane 225 executes the no-code Project Miner Source Confirmation Return Intake And Classification No-Live Packet tranche. The Project Miner intake workflow now has a return classifier under `PROJECT_MINER_SOURCE_CONFIRMATION_RETURN_INTAKE_AND_CLASSIFICATION_NO_LIVE_NO_CONTENT_READ_NO_WRITE`; because no current Jason source confirmation return is present, Lane 224 remains open under `NO_JASON_SOURCE_CONFIRMATION_RETURN_PRESENT_CONTINUE_NO_LIVE_PM_WORK` and the selected outcome is `NO_RETURN_PRESENT_KEEP_SOURCE_QUESTION_OPEN_CONTINUE_NO_LIVE_PM_WORK`. The next safe packet is PM Lane 226 no-live PM work continuation while source confirmation is pending. Desktop Codex source classification remains deferred, and workbook content reads, source PDF content reads, macro execution, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked.

PM Lane 226 executes the no-code Project Miner No-Live PM Work Continuation While Source Confirmation Pending Packet tranche. The Project Miner intake workflow now has a source-pending continuation selector under `PROJECT_MINER_NO_LIVE_PM_WORK_CONTINUATION_WHILE_SOURCE_CONFIRMATION_PENDING_NO_SOURCE_TRUTH_NO_WRITE`: Lane 224 remains open, Lane 225 remains the future return classifier, and the selected focus is `SOURCE_PENDING_PM_DAILY_OPERATING_BRIEF_NO_LIVE`. The next safe packet is PM Lane 227 source-pending PM daily operating brief, including field-start customer/site and lead/resource prompts as local review context only. Desktop Codex source classification remains deferred, and workbook content reads, source PDF content reads, macro execution, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked.

PM Lane 227 executes the no-code Project Miner Source-Pending PM Daily Operating Brief No-Live Packet tranche. The Project Miner intake workflow now has a compact daily source-pending brief under `PROJECT_MINER_SOURCE_PENDING_PM_DAILY_OPERATING_BRIEF_NO_LIVE_NO_SOURCE_TRUTH_NO_CONTENT_READ_NO_WRITE`: today in one screen, waiting on Jason, safe local review, field-start questions, blocked authority, sidecar help, and next packet menu. The next safe packet is PM Lane 228 daily brief closeout and next-packet selector. Desktop Codex source classification remains deferred, and workbook content reads, source PDF content reads, macro execution, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked.

PM Lane 228 executes the no-code Project Miner Source-Pending Daily Brief Closeout And Next-Packet Selector No-Live Packet tranche. The Project Miner intake workflow now closes the Lane 227 brief branch under `PROJECT_MINER_SOURCE_PENDING_DAILY_BRIEF_CLOSEOUT_NEXT_PACKET_SELECTOR_NO_LIVE_NO_SOURCE_TRUTH_NO_CONTENT_READ_NO_WRITE`: no current Lane 224 source confirmation return is present, no current Lane 227 daily brief return is present, Lane 224 remains open, Lane 225 remains ready, the default classification is `NO_JASON_SOURCE_OR_BRIEF_RETURN_PRESENT_HOLD_SOURCE_PENDING_NO_LIVE`, and the selected outcome is `KEEP_LANE_224_OPEN_NO_SOURCE_TRUTH_CONTINUE_ONLY_NO_LIVE_REVIEW_BURDEN_WORK`. The next optional packet is PM Lane 229 source-pending brief refresh and operator-card compression. Desktop Codex source classification remains deferred, and workbook content reads, source PDF content reads, macro execution, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked.

PM Lane 229 executes the no-code Project Miner Source Confirmation Return Received No-Live Packet tranche. The Project Miner intake workflow now has Jason's source confirmation return under `PROJECT_MINER_SOURCE_CONFIRMATION_RETURN_RECEIVED_NO_LIVE_METADATA_ONLY_NO_CONTENT_READ_NO_WRITE`: `Estimator R3 - Project Miner Temp Power Testing.xlsm` and `Miner Temp SLD-AP-BCARRASCO.pdf` are current Temp Power source candidates, while `EQUIPMENT INVENTORY - 2026.xlsx` and `Phx Tech Testing Capability Matrix 032726.xlsx` are resource context candidates. Buildings A and B main-project testing remains separate pending-contract context until exact scope/source package is confirmed. The next blocker is bounded local content-review admission for the two Temp Power source candidates only. Desktop Codex source classification remains deferred, and workbook content reads, source PDF content reads, macro execution, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked.

PM Lane 230 executes the no-code Project Miner Intake Source Folder Scope Clarification No-Live Packet tranche. The Project Miner intake workflow now treats the current Project Miner PM Planning folder contents as expected intake sources except `RESA Power - Project Data Entry MASTER.xlsm` and `Garney- Central Mesa Reuse Tracker #677562.xlsm`, which remain excluded planning/reference workbooks. The expected source set is metadata-only: `15_ELECTRICAL_COMBINED.pdf`, `Building B IFC.pdf`, `Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm`, `EQUIPMENT INVENTORY - 2026.xlsx`, `Estimator R3 - Project Miner Temp Power Testing.xlsm`, `Miner Temp SLD-AP-BCARRASCO.pdf`, and `Phx Tech Testing Capability Matrix 032726.xlsx`. Possible Building A low-voltage remains parked until award/scope confirmation. The next blocker is bounded local content-review admission for the expected source set. Desktop Codex source classification remains deferred, and workbook content reads, source PDF content reads, macro execution, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked.

PM Lane 231 executes the Project Miner Expected Intake Source Content Review No-Live Packet tranche. The Project Miner intake workflow now has bounded local content-orientation evidence for all seven expected intake sources, with excluded MASTER and Garney tracker workbooks still unread. Temp Power resolves as candidate `pm-import-candidate-miner-temp-power` with 7 workpackages, 15 tasks, 186 apparatus candidates, 138 topology labels, one informational missing-designation warning, and zero blockers. A/B MV Rev 9 resolves as candidate `pm-import-candidate-cupertino-miner-estimator-phx-bldg-a-b-mv-rev9` with 9 workpackages, 122 tasks, 5400 apparatus candidates, two warnings, and zero blockers, but remains pending separate A/B testing scope confirmation and warning review. The next safe workflow packet is a no-live Temp Power current-candidate approval readiness refresh. Desktop Codex source classification remains deferred, and macro execution, workbook writeback, durable fingerprints, hosted smoke, browser live route, live approval POST, approval row, project import write, notes, tasks, owners, due dates, assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked.

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
