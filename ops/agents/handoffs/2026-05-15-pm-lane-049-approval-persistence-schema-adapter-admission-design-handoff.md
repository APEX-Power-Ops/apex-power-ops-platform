# PM Lane 049 Handoff - Approval Persistence Schema And Adapter Admission Design

Date: 2026-05-15
Status: Authored, design-only
Scope: Future Project Miner import-candidate approval persistence schema and adapter admission

## Executive Summary

PM Lane 049 does not implement approval persistence. It admits the design contract for a later execution packet.

The future persistence target remains:

```text
seam.pm_import_candidate_approvals
```

The future route remains:

```text
/api/v1/mutations/project-import-approvals
```

This lane turns the PM Lane 048 approval preview JSON into a precise future executor contract: table columns, adapter boundary, validation evidence, readback classification, blockers, and guardrails. It creates no SQL file, runs no migration, implements no backend route, persists no approval, imports no rows, calls no live service, and changes no production state.

## Input Contract

The input evidence is the PM Lane 048 browser-only preview artifact:

```text
preview_kind: pm_import_candidate_approval_packet_preview
preview_version: pm_import_candidate_approval_packet_preview_v1
```

That preview is review context only. It is not a canonical approval record.

## Target Table

Future table:

```text
seam.pm_import_candidate_approvals
```

Future entity type:

```text
pm_import_candidate_approval
```

Future write model:

```text
insert_once_with_strict_idempotent_replay
```

## Target Columns

The later execution packet should create this column contract:

1. `approval_record_id text primary key`
2. `candidate_id text not null`
3. `candidate_version text not null`
4. `source_stat_fingerprint text not null`
5. `candidate_shape_fingerprint text not null`
6. `idempotency_key text not null`
7. `decision text not null`
8. `approved_by_actor_id text not null`
9. `approved_at_utc timestamptz not null`
10. `accepted_warning_codes jsonb not null`
11. `accepted_no_go_overrides jsonb not null`
12. `review_notes text not null`
13. `approval_payload jsonb not null`
14. `validation_result jsonb not null`
15. `created_at timestamptz not null default now()`

Allowed decision values:

1. `approve_for_import_packet`
2. `return_for_revision`
3. `reject_candidate`

## Constraints

The later execution packet should preserve these rules:

1. `approval_record_id` is deterministic from candidate identity plus idempotency key.
2. Candidate identity fields must be non-null and match the current approval contract.
3. `decision` must be permitted by the approval contract.
4. `accepted_warning_codes` must be a JSON array matching the current warning-code set.
5. `accepted_no_go_overrides` must be a JSON array containing only human-acceptance check ids.
6. `review_notes` must be non-empty.
7. Canonical approval rows are append-only.
8. Replay is idempotent only when the deterministic id and normalized payload match the stored row.

## Adapter Boundary

The later execution packet should add a dedicated approval adapter or repository.

The adapter must:

1. validate with `validate_project_import_approval_payload()` before insert,
2. use authenticated PM actor context for `approved_by_actor_id`,
3. use server time for `approved_at_utc`,
4. write only one canonical approval row,
5. record a separate audit event after the insert succeeds,
6. reject direct writes from UI, Excel, browser-local storage, or generic `PgDict` upsert,
7. reject stale candidate identity, stale fingerprints, unsupported decisions, warning-code drift, non-overridable no-go acknowledgements, missing actor, missing timestamp, and empty review notes.

The adapter must not:

1. route through generic `mutation_pipeline.py` apply/upsert behavior,
2. create or update project rows,
3. create or update workpackage rows,
4. create or update task rows,
5. create or update apparatus rows,
6. create or update issue rows,
7. create or update assignment rows,
8. mutate schedule state,
9. mutate status state,
10. import project rows.

## Required Future Evidence

The later execution packet should include:

1. local JSON-shape validation using a saved or generated Lane 048 preview payload,
2. validator tests for stale candidate id, candidate version, source fingerprint, shape fingerprint, idempotency key, warning-code mismatch, non-overridable no-go acknowledgement, missing actor, missing timestamp, empty review notes, and unsupported decision,
3. adapter contract tests using memory or fake store only for insert-once behavior, strict replay, replay mismatch rejection, and no generic mutation-pipeline call,
4. schema DDL review as text before execution,
5. readback design tests for current, stale, returned, rejected, and approved status classification without audit-log-only inference,
6. hosted parity evidence or a precise accepted blocker classification before live persistence is claimed.

## Blockers Before Execution

Actual schema and adapter implementation remain blocked until:

1. hosted PM intake parity is green or the remaining hosted blocker is precisely accepted and classified,
2. live schema authority is explicitly granted,
3. approval persistence authority is explicitly granted,
4. import mutation authority remains separately blocked,
5. the PM Lane 048 preview is treated as context only, not as approval.

## Sidecar Result

A read-only sidecar confirmed this boundary.

Recommended target columns, constraints, adapter rules, validation evidence, blockers, and guardrails were accepted in the design-only packet. The sidecar made no edits, staged no files, committed nothing, pushed nothing, deployed nothing, and did not call live services.

## Validation

Commands run from:

```text
C:/APEX Platform/apex-power-ops-platform
```

Packet JSON parse:

```powershell
C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-049-approval-persistence-schema-adapter-admission-design.json', encoding='utf-8')); print('packet-json-ok')"
```

Expected result:

```text
packet-json-ok
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Expected result:

```text
pass, with line-ending normalization warnings only if unstaged unrelated residue remains
```

## Guardrails Preserved

This tranche does not authorize:

1. SQL file creation,
2. SQL execution,
3. schema migration,
4. Supabase write,
5. backend endpoint change,
6. adapter implementation,
7. mutation-pipeline admission,
8. approval persistence,
9. import mutation,
10. live service call,
11. Render redeploy,
12. Vercel promotion,
13. service creation,
14. DNS, auth, ingress, or secret change,
15. fixture replay,
16. workbook macro execution,
17. workbook writeback,
18. assignment mutation,
19. schedule mutation,
20. status mutation,
21. autonomous AI business-state mutation.

## Next Recommended Move

Keep PM Lane 041A/041B as the hosted parity lanes. If hosted parity is closed or the blocker is explicitly accepted, the next execution packet can implement the dedicated schema and adapter from this contract, still without importing project rows.
