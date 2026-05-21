# APEX PM Lane 501 -> Lane 502 Implementation Requirements

Date: 2026-05-21

## Purpose

This document freezes what Lane 502 must implement after the Lane 501 design-only lane.

Lane 502 is an implementation lane. Lane 501 is not.

## Required Input

Lane 502 must accept exactly one primary input artifact:

1. [intermediate_ingest_contract_v1.schema.json](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_501_onboarding_design/contract/intermediate_ingest_contract_v1.schema.json) validated intermediate JSON

For the current sample, that input shape is exemplified by:

1. [miner_temp_power_testing_intermediate_20260521T103643Z.json](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_501_onboarding_design/sample/miner_temp_power_testing_intermediate_20260521T103643Z.json)

## Required Behavior

Lane 502 must:

1. Read the intermediate JSON.
2. Validate it against the v1 schema before opening any write transaction.
3. Recompute the reconciliation report content hash from the referenced reconciliation report body.
4. Refuse to write unless the supplied admission phrase includes the exact expected SHA-256 hash.
5. Insert `seam.scopes` rows for each scope object in the contract that does not already exist.
6. Update `seam.apparatus.scope_id` only for `matched` apparatus entries.
7. Consider `unmatched_extractor` entries as insert candidates only when explicitly admitted.
8. Leave `unmatched_existing` and `conflicting` rows untouched.

## Idempotency Rules

Lane 502 must be idempotent.

That means:

1. Re-running against the same intermediate JSON and the same reconciliation report is a no-op.
2. Existing scope rows with the same `id` and semantically identical payload must not be duplicated.
3. Existing apparatus rows already carrying the target `scope_id` must not be rewritten unnecessarily.
4. If the same report hash is supplied but the report body on disk differs, Lane 502 must abort.

## Write Boundaries

Lane 502 may write only:

1. `INSERT` into `seam.scopes`
2. `UPDATE seam.apparatus SET scope_id = ...`

Lane 502 must not write:

1. `seam.tasks`
2. `seam.projects`, except an explicit later packet could reopen project `data` changes if separately admitted
3. any `public.*` table
4. any financial table
5. any migration surface
6. any auth module, route module, or persistence module outside the bounded ingester slice

## Scope Identifier Rules

Lane 502 must not invent `scope_id` values at runtime.

It must use the `scope_id` values already present in the intermediate JSON contract, which follow the documented pattern:

1. `pm-import-project-miner-temp-power-scope-001`
2. `pm-import-project-miner-temp-power-scope-002`
3. etc.

## Reconciliation Enforcement

Lane 502 must honor all four categories from the reconciliation report:

1. `matched`: update `scope_id` only
2. `unmatched_existing`: no write
3. `unmatched_extractor`: no write unless explicitly admitted for insert
4. `conflicting`: no write

Lane 502 must abort if the report contains any `conflicting` entry.

## Required Output

Lane 502 must emit a post-write artifact that records:

1. inserted scope ids
2. updated apparatus ids
3. skipped unmatched existing rows
4. skipped unmatched extractor rows
5. the reconciliation report content hash used for admission
6. final row counts for `seam.scopes` and apparatus rows with non-null `scope_id`

## Admission Gate

Lane 502 must require an admission phrase that includes the exact reconciliation report content hash.

For the current sample, the frozen hash is:

`1b87397b17ffecd27679073d9645012d5663533ad344e15110c91258993d6130`

Lane 502 must recompute this from the canonicalized `report_body` object before writing.