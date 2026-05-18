# PM Lane 268 - Hosted Candidate Source Hydration Repair Review Handoff

Date: 2026-05-17

Decision label:

`PROJECT_MINER_TEMP_POWER_HOSTED_CANDIDATE_SOURCE_HYDRATION_REPAIR_REVIEW`

Selected outcome:

`STOPPED_AWAITING_HOSTED_SOURCE_STRATEGY_DECISION_NO_LIVE`

## Objective

Classify the hosted source-hydration repair needed before retrying the PM Lane 142 live approval POST for the current Project Miner Temp Power import candidate.

## Current Blocker

PM Lane 267 proved hosted routes are reachable, but hosted mutation-seam serves the wrong candidate:

`pm-import-candidate-project-miner`

The expected current Temp Power candidate remains:

`pm-import-candidate-miner-temp-power`

No approval POST may be retried until hosted readback returns the Temp Power candidate with the expected task/apparatus counts, zero blockers, and accepted warning `PROJECT_DATA_ENTRY_FORMULA_ERRORS`.

## Technical Finding

The source readers already support hosted repair through existing env vars:

1. `APEX_PROJECT_MINER_PLANNING_ROOT`
2. `APEX_PROJECT_ESTIMATOR_WORKBOOK`
3. `APEX_PROJECT_SLD_PDF`
4. `APEX_PROJECT_DATA_ENTRY_WORKBOOK`
5. `APEX_REFERENCE_TRACKER_WORKBOOK`
6. `APEX_FIELD_SEED_EQUIPMENT_WORKBOOK`
7. `APEX_FIELD_SEED_CAPABILITY_WORKBOOK`

The safest next repair is governed source-file placement plus Render env/deploy admission. Derived snapshots and fixture fallbacks remain parked unless explicitly selected.

## Next Review Needed

Return exactly one next label:

1. `APPROVE_HOSTED_SOURCE_FILES_ENV_REPAIR_NO_APPROVAL_POST`
2. `APPROVE_SIGNED_SOURCE_SNAPSHOT_SCOUT_NO_APPROVAL_POST`
3. `APPROVE_DERIVED_FIXTURE_FALLBACK_SCOUT_NO_APPROVAL_POST`
4. `HOLD_HOSTED_SOURCE_REPAIR_NO_LIVE`

## Guardrails

Do not send an approval POST. Do not create an approval row. Do not import project rows. Do not upload hosted source files, change Render env vars, deploy Render, create fixtures, create derived snapshots, run macros, write source workbooks, edit source PDFs, commit source workbooks/PDFs, write Supabase, or mutate PM business state without a later explicit packet.
