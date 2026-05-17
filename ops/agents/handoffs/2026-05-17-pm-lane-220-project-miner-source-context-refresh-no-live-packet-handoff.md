# PM Lane 220 Handoff - Project Miner Source Context Refresh No-Live Packet

Date: 2026-05-17

Decision label:

`PROJECT_MINER_SOURCE_CONTEXT_REFRESH_NO_LIVE_METADATA_ONLY_NO_WRITE`

## Objective

Refresh the local Project Miner source context from metadata-only evidence so the next PM lane can ask Jason to confirm which files are current source candidates, reference-only files, resource context, unknown/stale context, or authority-required stops.

## Inputs

1. `docs/operations/APEX-PM-LANE-219-PROJECT-MINER-FIELD-START-CLARIFICATION-RETURN-CLOSEOUT-AND-NEXT-PACKET-SELECTION-2026-05-17.md`
2. `ops/agents/handoffs/2026-05-17-pm-lane-219-project-miner-field-start-clarification-return-closeout-and-next-packet-selection-closeout.md`
3. `C:\Users\jjswe\Desktop\Project Miner PM Planning`
4. `C:\APEX Platform\Reference_Files\Excel\Estimator VBA Modules\DataverseExport.bas`
5. `C:\APEX Platform\Reference_Files\Excel\Estimator VBA Modules\DataverseMappingVerification.bas`

## Allowed Work

1. Inspect repo-local PM lane docs and handoffs.
2. Inspect local source paths by existence, filename, size, and modified time only.
3. Record human confirmation questions.
4. Classify the source-refresh posture without creating business state.
5. Recommend the next no-live packet.

## Forbidden Work

Do not:

1. open workbook contents,
2. run macros,
3. read source PDF contents,
4. compute or publish durable source fingerprints,
5. write back to any workbook,
6. access hosted services,
7. access Supabase, Render, Vercel, Olares, credentials, or secrets,
8. run browser live routes or hosted smokes,
9. create live approval POSTs or approval rows,
10. import project rows,
11. create notes, tasks, action items, owners, due dates, assignments, schedules, statuses, field instructions, customer commitments, reports, production records, or finance outputs,
12. stage, commit, push, or publish from a sidecar unless separately admitted.

## Source Context Buckets

Use these buckets:

1. `CURRENT_SOURCE_CANDIDATE`
2. `REFERENCE_ONLY`
3. `RESOURCE_CONTEXT`
4. `UNKNOWN_OR_STALE`
5. `STOP_AUTHORITY_REQUIRED`

## Expected Output

1. Source metadata inventory.
2. Human confirmation question list.
3. No-live/no-content-read guardrails.
4. Next safe packet recommendation.

## Current Recommendation

Proceed next with:

`PM Lane 221 - Project Miner Source Artifact Role Confirmation No-Live Packet`

This should be a no-live, no-content-read confirmation packet unless Jason explicitly authorizes a later bounded source-content review.
