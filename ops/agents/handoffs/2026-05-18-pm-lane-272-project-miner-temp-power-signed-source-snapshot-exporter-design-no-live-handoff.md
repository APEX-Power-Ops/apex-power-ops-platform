# PM Lane 272 - Signed Source Snapshot Exporter Design Handoff

Date: 2026-05-18

Decision label:

`PROJECT_MINER_TEMP_POWER_SIGNED_SOURCE_SNAPSHOT_EXPORTER_DESIGN_NO_LIVE`

Selected outcome:

`EXPORTER_DESIGN_READY_LOCAL_SCRIPT_ONLY_IMPLEMENTATION_RECOMMENDED_NO_LIVE`

## Scope

Design the smallest safe no-live local exporter path for a Project Miner Temp Power signed source snapshot while PM Lane 270 waits for authenticated Render/source-placement capability.

## Decision

Approved for design only:

1. local exporter script path may be proposed,
2. manifest and checksum shape may be defined,
3. redaction and runtime-custody rules may be defined,
4. later implementation tests may be specified.

Not approved in this lane:

1. adding the exporter script,
2. running the exporter,
3. creating snapshot artifacts,
4. adding hosted loader code,
5. setting `APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH`,
6. uploading hosted source or snapshot files,
7. changing Render env/deploy state,
8. sending approval POST or creating approval rows.

## Implementation Recommendation

The later local exporter implementation should target:

`apps/mutation-seam/scripts/export_pm_import_candidate_snapshot.py`

It should write:

1. `candidate.json`
2. `admission-plan.json`
3. `manifest.json`
4. `SHA256SUMS.txt`

`manifest.json` should be safe to review and contain only redacted source-file metadata. The full candidate and admission-plan payloads should remain runtime artifacts and must not be committed by default.

## Next Packet

If direct Render source placement remains unavailable, next:

`PM Lane 273 - Project Miner Temp Power Signed Source Snapshot Exporter Local Script No-Live`

That packet may add the exporter script and tests only. It still must not run the exporter against source files unless the packet explicitly admits local source read and runtime artifact creation.

## Guardrails

No product code, hosted fallback, approval POST, approval row, project import, Supabase write, hosted source upload, Render env update, Render deploy, signed snapshot artifact, source workbook/PDF content read/write, macro/writeback, Desktop Codex PM decision authority, secret exposure, or PM business-state mutation is admitted by this handoff.
