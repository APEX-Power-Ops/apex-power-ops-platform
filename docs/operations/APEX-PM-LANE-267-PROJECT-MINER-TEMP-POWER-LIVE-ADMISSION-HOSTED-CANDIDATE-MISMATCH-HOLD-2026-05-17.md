# PM Lane 267 - Project Miner Temp Power Live Admission Hosted Candidate Mismatch Hold

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_LIVE_ADMISSION_HOSTED_CANDIDATE_MISMATCH_HOLD`

Selected outcome:

`LIVE_ADMISSION_PRESENT_STOPPED_HOSTED_CANDIDATE_MISMATCH`

## Purpose

PM Lane 267 records the first live-admission preflight after Jason supplied the exact PM Lane 142 admission phrase as a current instruction:

`I explicitly admit PM Lane 142 live approval POST and first approval-row creation for the current Project Miner Temp Power import candidate.`

The exact phrase is present, but the live approval POST is not safe to send because hosted mutation-seam is not currently serving the Project Miner Temp Power candidate.

This lane performs only read-only hosted readiness checks and no live write.

## Hosted Route Proof

Read-only hosted readiness is green at the route level:

| Check | Result |
| --- | --- |
| operations-web hosted smoke | `SMOKE_SUMMARY failed=0 passed=12 base_url=https://operations.apexpowerops.com/` |
| paired PM intake hosted smoke | `PM_INTAKE_HOSTED_SUMMARY failed=0` |
| deployed mutation-seam smoke with PM intake | `RESULT PASS` |

The read endpoints are reachable, approval status readback is available, and hosted approval storage is not the current blocker.

## Candidate Mismatch Evidence

The hosted read-only candidate does not match the current Temp Power candidate required for live approval-row creation.

| Item | Expected for live Temp Power approval | Hosted read-only value |
| --- | --- | --- |
| Candidate id | `pm-import-candidate-miner-temp-power` | `pm-import-candidate-project-miner` |
| Candidate version | `pm_import_candidate_read_only_v1` | `pm_import_candidate_read_only_v1` |
| Mutation authority | `not_admitted` | `not_admitted` |
| Task count | `15` | `0` |
| Apparatus candidate count | `184` | `0` |
| Blocker count | `0` | `2` |
| Warning count | `1` accepted no-live warning | `3` hosted warnings |
| Accepted warning codes | `PROJECT_DATA_ENTRY_FORMULA_ERRORS` | `MISSING_ESTIMATOR_WORKBOOK`, `MISSING_SLD_PDF`, `NO_ESTIMATOR_LINE_ITEMS` |
| Approval status classification | current Temp Power candidate required | `no_approval_record` for hosted Project Miner candidate |
| Approval record count | current Temp Power candidate count required | `0` for hosted Project Miner candidate |
| Current candidate match | `true` required | `false` |

The approval count of zero cannot be used as the Temp Power pre-write proof because it belongs to the hosted `pm-import-candidate-project-miner` candidate, not `pm-import-candidate-miner-temp-power`.

## Classification

This is a hosted candidate freshness/source-hydration blocker, not a PM approval decision blocker and not a Render route-access blocker.

The likely source of the mismatch is that hosted mutation-seam is resolving the Project Miner planning sources from the default desktop-oriented source paths or env overrides, and those Temp Power source files are not present in the hosted runtime. Code inspection shows the seed source defaults and overrides are:

1. `APEX_PROJECT_MINER_PLANNING_ROOT`
2. `APEX_PROJECT_ESTIMATOR_WORKBOOK`
3. `APEX_PROJECT_SLD_PDF`
4. default root `Desktop/Project Miner PM Planning`

This lane does not change Render env vars, upload source files, create a fixture, deploy services, or alter hosted source strategy.

## Stop Condition

The live approval branch is stopped at:

`STOPPED_HOSTED_CURRENT_CANDIDATE_NOT_TEMP_POWER`

No approval POST was sent.

No approval row was created.

No project import was performed.

## Still Required Before Live Approval POST

After hosted candidate parity is repaired, a later live executor still needs:

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

## Next Safe Packet

The next safe packet is:

`PM Lane 268 - Project Miner Temp Power Hosted Candidate Source Hydration And Freshness Repair Packet`

That packet should repair or classify the hosted source strategy so Render serves the same Temp Power candidate as local review, then rerun hosted smokes and candidate/contract/status readbacks. It must not send an approval POST, create an approval row, import project rows, read workbook/PDF contents beyond the already approved source-preview boundary, run macros, commit source workbooks or source PDFs into the repo, expose secrets, or mutate PM business state.

## Guardrails

PM Lane 267 adds no product code, UI section, writable control, button, link, route, handler, backend seam, payload version, localStorage schema, sessionStorage schema, live approval POST, approval row, project import, note, task, action item, owner/due-date assignment, field authorization, lead selection, crew assignment, schedule/status write, procurement or rental commitment, customer commitment, field instruction, durable field record, production tracking row, customer report, billing/payroll/invoice/accounting output, external finance-system output, Supabase write, Render env var update, Render deploy, Vercel deploy, Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook content write, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
