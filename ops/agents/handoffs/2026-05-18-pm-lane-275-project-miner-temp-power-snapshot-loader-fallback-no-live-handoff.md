# PM Lane 275 - Snapshot Loader Fallback No-Live Handoff

Date: 2026-05-18

Decision label:

`PROJECT_MINER_TEMP_POWER_SNAPSHOT_LOADER_FALLBACK_NO_LIVE`

Selected outcome:

`SNAPSHOT_LOADER_IMPLEMENTED_AND_REAL_RUNTIME_SNAPSHOT_VERIFIED_NO_LIVE`

## Scope

Implement the no-live mutation-seam read fallback that lets hosted reads use a PM Lane 274 runtime snapshot through:

`APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH`

Allowed writes:

1. snapshot loader module,
2. candidate/admission read wiring,
3. focused tests,
4. PM lane docs and closeout.

Forbidden:

1. approval POST,
2. approval-row creation,
3. project import,
4. Supabase write,
5. Render env/deploy action,
6. hosted source upload,
7. committed runtime payload,
8. workbook macro or writeback.

## Closeout Requirements

Report:

1. loader env var,
2. checksum and authority validation behavior,
3. focused test result,
4. real runtime snapshot probe result,
5. exact hosted unblock steps,
6. next blocker.
