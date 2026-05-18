# PM Lane 272 - Project Miner Temp Power Signed Source Snapshot Exporter Design

Date: 2026-05-18

Authority: VS Code Codex technical authority for the PM lane with Jason-delegated incremental no-live blocker approval

Decision label:

`PROJECT_MINER_TEMP_POWER_SIGNED_SOURCE_SNAPSHOT_EXPORTER_DESIGN_NO_LIVE`

Selected outcome:

`EXPORTER_DESIGN_READY_LOCAL_SCRIPT_ONLY_IMPLEMENTATION_RECOMMENDED_NO_LIVE`

## Purpose

PM Lane 272 defines the smallest safe local exporter design for a signed Project Miner Temp Power import-candidate source snapshot while PM Lane 270 remains blocked on authenticated Render/source-placement capability.

This is a design packet only. It does not add the exporter script, create a snapshot artifact, add a hosted fallback loader, update Render, upload hosted source files, send an approval POST, create an approval row, import project rows, read source workbook/PDF contents in this lane, or mutate PM business state.

## Current Blocker Context

PM Lane 270 remains stopped at:

`STOPPED_AWAITING_RENDER_AUTHENTICATED_SOURCE_FILES_REPAIR_NO_APPROVAL_POST`

PM Lane 271 confirmed a snapshot fallback is technically plausible, but only if it is treated as derived evidence with explicit redaction, manifest, runtime custody, and later hosted readback proof.

PM Lane 272 turns that conclusion into an implementation-ready design for a later no-live local exporter packet.

## Exporter Scope

The later implementation packet should add a local script only:

`apps/mutation-seam/scripts/export_pm_import_candidate_snapshot.py`

The exporter should reuse the existing read-only candidate path and admission-plan builder:

1. `apps/mutation-seam/scripts/preview_pm_import_candidate.py` argument/env pattern,
2. `apps/mutation-seam/app/project_import_candidate.py`,
3. `apps/mutation-seam/app/project_import_admission_plan.py`.

The exporter must not add hosted runtime fallback behavior. It must not introduce `APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH` or any loader code in this packet family until a later packet separately admits snapshot runtime readback.

## Output Boundary

The exporter should require an explicit output directory. It should refuse to write into tracked repo paths unless a later packet deliberately admits a repo-local ignored output boundary.

Recommended output files:

1. `candidate.json`
2. `admission-plan.json`
3. `manifest.json`
4. `SHA256SUMS.txt`

The full candidate and admission-plan payloads are runtime artifacts. They may contain source-derived task detail and local source path references because the current candidate model includes those fields. They must not be committed by default.

## Manifest Shape

`manifest.json` should be repo-facing safe by construction. It should include:

1. `schema_version`: `pm_import_candidate_snapshot_manifest_v1`
2. `authority`: `derived_source_snapshot_no_live`
3. `generated_at_utc`
4. `generator_repo_head`
5. `generator_dirty_state`
6. `candidate_id`
7. `candidate_version`
8. `admission_plan_version`
9. `source_stat_fingerprint`
10. `candidate_shape_fingerprint`
11. `workpackage_count`
12. `task_count`
13. `apparatus_candidate_count`
14. `warning_codes`
15. `payload_files` with SHA-256 values
16. `source_files_redacted`
17. `not_allowed_now`

`source_files_redacted` should include only:

1. `source_id`
2. `label`
3. `file_name`
4. `extension`
5. `found`
6. `size_bytes`
7. `modified_at`
8. `freshness_status`
9. existing source-file fingerprint value if present

It must not include Jason's Windows absolute path, directory names, source row content, workbook cell values, extracted PDF text, or proprietary task detail.

## Hash-Signed Meaning

For this lane, "signed" means hash-signed by deterministic SHA-256 checksums:

1. each payload file gets a SHA-256 digest,
2. the manifest records payload digests,
3. `SHA256SUMS.txt` lists the same digests,
4. later hosted readback must recompute and compare digests before any live retry.

No private signing key, secret, certificate, Olares Vault item, or credential-backed signature is admitted in this design.

## Required Implementation Tests

A later exporter implementation packet should include focused tests that prove:

1. the manifest parses as JSON,
2. manifest source entries contain file names but no absolute paths,
3. payload file SHA-256 values match file contents,
4. candidate and admission payloads preserve `mutation_authority: not_admitted`,
5. warning-code and count fields match the candidate/admission plan,
6. output directory is explicit,
7. repo-tracked output is rejected unless a later packet admits a repo-local ignored output directory,
8. no hosted loader or approval/import endpoint behavior is changed.

## Future Hosted Readback Gate

If Render source placement remains unavailable and a later snapshot exporter implementation succeeds, a still-later packet may consider a hosted readback path.

That packet must prove:

1. the hosted service can read the snapshot runtime artifact,
2. manifest digests match hosted payload contents,
3. candidate identity is `pm-import-candidate-miner-temp-power`,
4. task/apparatus counts match the current no-live candidate,
5. source and shape fingerprints match the manifest,
6. mutation authority remains `not_admitted`,
7. approval status is read before any approval POST,
8. no project import or downstream business write occurs.

## Next Technical Move

If authenticated Render source-file placement is still unavailable, the next self-approved no-live implementation packet is:

`PM Lane 273 - Project Miner Temp Power Signed Source Snapshot Exporter Local Script No-Live`

That packet may add the exporter script and focused tests only. It must not run the exporter against the source files unless its packet explicitly admits local source read and runtime artifact creation.

## Guardrails

PM Lane 272 adds no product code, UI section, writable control, button, link, route, handler, backend seam, payload version, localStorage schema, sessionStorage schema, live approval POST, approval row, project import, note, task, action item, owner/due-date assignment, field authorization, lead selection, crew assignment, schedule/status write, procurement or rental commitment, customer commitment, field instruction, durable field record, production tracking row, customer report, billing/payroll/invoice/accounting output, external finance-system output, Supabase write, hosted source upload, Render env var update, Render deploy, Vercel deploy, Olares action, SQL/schema migration, signed snapshot artifact, snapshot exporter script, snapshot runtime fallback, source workbook writeback, source PDF content edit, workbook content read/write in this lane, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS

Proof:

1. PM Lane 270/271 blocker context review,
2. existing candidate/admission code-path inspection,
3. PM Lane 272 text search,
4. packet JSON parse,
5. guardrail keyword scan,
6. corrupted-token scan,
7. `git diff --check`.
