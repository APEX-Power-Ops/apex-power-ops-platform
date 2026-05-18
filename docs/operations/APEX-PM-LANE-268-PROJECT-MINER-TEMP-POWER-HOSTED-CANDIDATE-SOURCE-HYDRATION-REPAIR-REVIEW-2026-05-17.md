# PM Lane 268 - Project Miner Temp Power Hosted Candidate Source Hydration Repair Review

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_HOSTED_CANDIDATE_SOURCE_HYDRATION_REPAIR_REVIEW`

Selected outcome:

`STOPPED_AWAITING_HOSTED_SOURCE_STRATEGY_DECISION_NO_LIVE`

## Purpose

PM Lane 268 records the source-hydration repair review required after PM Lane 267 stopped live approval execution.

The exact PM Lane 142 live-admission phrase is present as a current instruction, but the approval POST remains blocked because hosted mutation-seam is not serving the current Project Miner Temp Power import candidate.

This lane performs only repo-local code inspection and packet classification. It does not upload source files, change hosted env vars, deploy Render, create a fixture, send an approval POST, create an approval row, or import project rows.

## Current Stop From PM Lane 267

Hosted access is green, but candidate currency is not.

| Item | Expected for live Temp Power approval | Hosted read-only value |
| --- | --- | --- |
| Candidate id | `pm-import-candidate-miner-temp-power` | `pm-import-candidate-project-miner` |
| Task count | `15` | `0` |
| Apparatus candidate count | `184` | `0` |
| Blocker count | `0` | `2` |
| Accepted warning codes | `PROJECT_DATA_ENTRY_FORMULA_ERRORS` | `MISSING_ESTIMATOR_WORKBOOK`, `MISSING_SLD_PDF`, `NO_ESTIMATOR_LINE_ITEMS` |
| Approval status usefulness | Temp Power pre-write proof required | wrong candidate, not valid pre-write proof |

The live approval branch remains stopped at:

`STOPPED_HOSTED_CURRENT_CANDIDATE_NOT_TEMP_POWER`

## Code Inspection Finding

The hosted candidate mismatch is consistent with missing hosted source files, not with approval storage, route access, or PM decision state.

The import candidate reader calls three source readers:

1. estimator workbook and SLD PDF through `load_project_seed_sources`,
2. Project Data Entry workbook and reference tracker through `load_project_tracker_sources`,
3. equipment inventory and capability matrix through `load_seed_data`.

Those readers resolve source locations through these env vars or defaults:

1. `APEX_PROJECT_MINER_PLANNING_ROOT`
2. `APEX_PROJECT_ESTIMATOR_WORKBOOK`
3. `APEX_PROJECT_SLD_PDF`
4. `APEX_PROJECT_DATA_ENTRY_WORKBOOK`
5. `APEX_REFERENCE_TRACKER_WORKBOOK`
6. `APEX_FIELD_SEED_EQUIPMENT_WORKBOOK`
7. `APEX_FIELD_SEED_CAPABILITY_WORKBOOK`

When the estimator workbook is absent, the local loader cannot hydrate the Temp Power project name or line items. The candidate therefore falls back to the generic Project Miner identity and returns missing-source blockers and warnings.

## Source Set Needed For Hosted Parity

The current Temp Power hosted candidate needs a governed hosted equivalent of the already confirmed local source set:

1. `Estimator R3 - Project Miner Temp Power Testing.xlsm`
2. `Miner Temp SLD-AP-BCARRASCO.pdf`
3. `RESA Power - Project Data Entry MASTER.xlsm`
4. `Garney- Central Mesa Reuse Tracker #677562.xlsm`
5. `EQUIPMENT INVENTORY - 2026.xlsx`
6. `Phx Tech Testing Capability Matrix 032726.xlsx`

These files should not be committed to Git by default. The hosted repair must either place them in a governed runtime-accessible location outside the repo or use an explicitly approved derived-source strategy.

## Repair Options

### Option 1 - Hosted Source Files Env Repair

Use a governed hosted file location for the current source files and point the Render service at those paths with the existing env vars.

This is the preferred fidelity path because it preserves the current source-file based loader, source freshness metadata, source fingerprint behavior, and current candidate read semantics.

This option requires a later admitted hosted-source placement and Render env/deploy packet. It must not commit source workbooks or source PDFs to Git.

### Option 2 - Signed Derived Candidate Snapshot

Create a minimal derived candidate snapshot from the locally reviewed source outputs and teach hosted mutation-seam to read that snapshot when source files are unavailable.

This reduces hosting friction but changes the authority model: hosted would serve a derived snapshot rather than reading source files directly. It therefore requires an explicit packet, signature/fingerprint policy, and readback proof before any live approval retry.

### Option 3 - Fixture Fallback

Add a code-level Temp Power fixture fallback for hosted reads.

This is not recommended as the next move. It is the fastest path technically, but it risks making a stale repo fixture look like current PM source truth. It should stay parked unless Jason explicitly accepts lower source-freshness fidelity for a bounded dry-run or demo path.

### Option 4 - Hold

Hold live approval execution until a hosted source placement strategy is approved.

This is safe but does not reduce the current blocker.

## Technical Authority Recommendation

VS Code Codex recommends Option 1 first:

`APPROVE_HOSTED_SOURCE_FILES_ENV_REPAIR_NO_APPROVAL_POST`

This keeps the hosted candidate tied to governed source files and avoids quietly turning derived data or fixtures into the approval authority.

If secure hosted source placement is not practical, the next safest review path is:

`APPROVE_SIGNED_SOURCE_SNAPSHOT_SCOUT_NO_APPROVAL_POST`

The fixture fallback should remain parked unless the business need is explicitly a non-authoritative demo or dry-run.

## Next Blocker Review Point

PM Lane 268 stops at:

`STOPPED_AWAITING_HOSTED_SOURCE_STRATEGY_DECISION_NO_LIVE`

One exact next label is needed before VS Code Codex should proceed:

1. `APPROVE_HOSTED_SOURCE_FILES_ENV_REPAIR_NO_APPROVAL_POST`
2. `APPROVE_SIGNED_SOURCE_SNAPSHOT_SCOUT_NO_APPROVAL_POST`
3. `APPROVE_DERIVED_FIXTURE_FALLBACK_SCOUT_NO_APPROVAL_POST`
4. `HOLD_HOSTED_SOURCE_REPAIR_NO_LIVE`

## Still Required Before Live Approval POST

After hosted source strategy is repaired, a later live executor still needs:

1. hosted readback showing candidate `pm-import-candidate-miner-temp-power`,
2. hosted readback showing 15 tasks, 184 apparatus candidates, zero blockers, and accepted warning `PROJECT_DATA_ENTRY_FORMULA_ERRORS`,
3. hosted approval contract values for the same Temp Power candidate,
4. pre-write approval-row count for the Temp Power candidate,
5. PM decision value,
6. PM review notes,
7. project import stop-boundary acknowledgement,
8. downstream field, schedule, resource, customer, production, and finance write stop-boundary acknowledgement,
9. one browser/API path approval POST,
10. same-payload idempotent replay proof,
11. approval-status readback for the created approval row.

## Guardrails

PM Lane 268 adds no product code, UI section, writable control, button, link, route, handler, backend seam, payload version, localStorage schema, sessionStorage schema, live approval POST, approval row, project import, note, task, action item, owner/due-date assignment, field authorization, lead selection, crew assignment, schedule/status write, procurement or rental commitment, customer commitment, field instruction, durable field record, production tracking row, customer report, billing/payroll/invoice/accounting output, external finance-system output, Supabase write, Render env var update, Render deploy, Vercel deploy, Olares action, SQL/schema migration, hosted source upload, fixture fallback, derived snapshot, source workbook writeback, source PDF content edit, workbook content write, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS

Proof:

1. repo-local code inspection of source path resolution,
2. packet JSON parse,
3. PM Lane 268 text search,
4. guardrail keyword scan,
5. corrupted-token scan,
6. `git diff --check`.
