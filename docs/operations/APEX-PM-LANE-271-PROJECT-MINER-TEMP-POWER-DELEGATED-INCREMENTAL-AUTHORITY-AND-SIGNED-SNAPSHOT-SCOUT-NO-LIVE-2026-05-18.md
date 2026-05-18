# PM Lane 271 - Project Miner Temp Power Delegated Incremental Authority And Signed Snapshot Scout

Date: 2026-05-18

Authority: VS Code Codex technical authority for the PM lane with Jason-delegated incremental no-live blocker approval

Decision label:

`PROJECT_MINER_TEMP_POWER_DELEGATED_INCREMENTAL_AUTHORITY_AND_SIGNED_SNAPSHOT_SCOUT_NO_LIVE`

Selected outcome:

`SIGNED_SOURCE_SNAPSHOT_SCOUT_APPROVED_RENDER_AUTH_CAPABILITY_GAP_REMAINS_NO_LIVE`

## Purpose

PM Lane 271 records Jason's delegated approval posture for incremental PM-lane technical blockers and uses that authority to evaluate the next no-live fallback while PM Lane 270 waits for an authenticated Render/source-placement executor.

This lane does not change the existing live approval boundary. It does not admit approval POST, approval-row creation, project import, Supabase writes, hosted source upload, Render env changes, Render deploys, source workbook/PDF commits, macros, or PM business-state mutation.

## Delegated Incremental Authority

Jason's current instruction delegates incremental blocker approval to VS Code Codex as repo technical authority and project stakeholder for PM-lane advancement.

VS Code Codex accepts that delegation for:

1. no-live technical blocker classification,
2. packet sequencing,
3. no-live scout selection,
4. executor prompt authoring,
5. queue and ledger maintenance,
6. validation and closeout publication.

VS Code Codex does not treat that delegation as blanket authority for:

1. secret access or secret rotation,
2. hosted source upload without an authenticated surface,
3. Render/Vercel/Olares/Supabase mutation without the needed capability and packet boundary,
4. live approval POST,
5. approval-row creation,
6. project import,
7. field/resource/schedule/customer/production/finance writes,
8. autonomous AI business-state mutation.

## Current PM Lane 270 Blocker

PM Lane 270 remains stopped at:

`STOPPED_AWAITING_RENDER_AUTHENTICATED_SOURCE_FILES_REPAIR_NO_APPROVAL_POST`

That is a capability blocker, not a decision-label blocker. The local shell still has no Render CLI/API credential exposure and no authenticated hosted source-placement surface.

## Self-Approved No-Live Fallback Scout

Under the delegated incremental authority, VS Code Codex approves a no-live scout of the signed source snapshot fallback that PM Lane 268 had parked behind explicit approval:

`APPROVE_SIGNED_SOURCE_SNAPSHOT_SCOUT_NO_APPROVAL_POST`

This is only a scout. It does not create a snapshot artifact, add snapshot fallback code, upload files, commit derived data, or change hosted service behavior.

## Scout Findings

Existing code already provides the raw ingredients for a signed or manifest-backed snapshot path:

1. `apps/mutation-seam/scripts/preview_pm_import_candidate.py` can serialize the current read-only import candidate as JSON.
2. `apps/mutation-seam/app/project_import_candidate.py` builds candidate identity, workpackages, tasks, apparatus candidates, source freshness, warnings, human decisions, and mutation authority.
3. `apps/mutation-seam/app/project_import_admission_plan.py` computes candidate shape fingerprint, source stat fingerprint, warning-code set, idempotency plan, no-go checks, and approval record contract.
4. Existing tests already cover the Temp Power candidate identity, ground-resistance lot handling, candidate shape, warning behavior, and read-only mutation authority.

The same code also shows why a snapshot fallback needs an explicit authority model:

1. candidate JSON includes source-derived business data and local source path references,
2. source freshness currently uses path, size, and modified-time fingerprints,
3. a hosted snapshot would be derived evidence, not direct source-file read parity,
4. path redaction or path normalization is needed before any snapshot metadata is treated as repo-facing,
5. a snapshot runtime path would need a later loader/fallback packet and readback proof before any live approval retry.

## Recommended Snapshot Shape

A later implementation packet, if selected, should produce a runtime-only snapshot bundle with two layers:

1. Candidate payload:
   - read-only candidate JSON,
   - admission plan JSON,
   - no mutation authority,
   - explicit derived-source authority label.
2. Manifest:
   - snapshot schema version,
   - generator repo commit,
   - generated timestamp,
   - candidate id,
   - candidate version,
   - source stat fingerprint,
   - candidate shape fingerprint,
   - workpackage/task/apparatus counts,
   - warning-code set,
   - snapshot payload SHA-256,
   - source file names, sizes, and modified times without Jason's Windows absolute path in repo-facing records.

The manifest may be committed only if it contains no source-derived proprietary task detail and no personal absolute paths. The full candidate snapshot should remain runtime-only unless a later packet explicitly admits a redacted, non-sensitive publication boundary.

## Recommended Future Loader Boundary

If direct Render source-file placement remains blocked, a later code packet may add a read-only fallback such as:

`APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH`

That fallback must:

1. be disabled unless the env var is explicitly set,
2. label the candidate as derived snapshot authority,
3. preserve `mutation_authority: not_admitted`,
4. expose the snapshot manifest in readback,
5. reject malformed or stale snapshot schema,
6. keep source-file direct read as the preferred path,
7. require hosted readback before any approval POST retry.

## Next Technical Move

The next self-approved no-live packet, if Render source placement remains unavailable, should be:

`PM Lane 272 - Project Miner Temp Power Signed Source Snapshot Exporter Design No-Live`

That packet should decide whether to add a local exporter script only, without adding hosted fallback code yet.

## Guardrails

PM Lane 271 adds no product code, UI section, writable control, button, link, route, handler, backend seam, payload version, localStorage schema, sessionStorage schema, live approval POST, approval row, project import, note, task, action item, owner/due-date assignment, field authorization, lead selection, crew assignment, schedule/status write, procurement or rental commitment, customer commitment, field instruction, durable field record, production tracking row, customer report, billing/payroll/invoice/accounting output, external finance-system output, Supabase write, hosted source upload, Render env var update, Render deploy, Vercel deploy, Olares action, SQL/schema migration, signed snapshot artifact, fixture fallback, derived snapshot runtime fallback, source workbook writeback, source PDF content edit, workbook content read/write, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS

Proof:

1. PM Lane 270 blocker review,
2. source snapshot code-path inspection,
3. PM-256 closeout absence check,
4. PM Lane 271 text search,
5. packet JSON parse,
6. guardrail keyword scan,
7. corrupted-token scan,
8. `git diff --check`.
