# PM Lane 033 Handoff - Import Candidate PM UI Review

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-033`
Scope: Read-only PM UI review surface for Project Miner Temp Power import candidate

## Summary

PM Lane 033 adds the first PM-facing UI for the read-only Temp Power import candidate.

The route is:

`/pm-review/import-candidate`

It consumes only:

`GET /api/v1/reads/project-import-candidate`

The page is exception-first: required decisions and warnings appear before dense task/workpackage detail. Clean rows remain collapsed by default. The page shows candidate summary, proposed structure, source traceability, resource context, and explicit allowed/not-allowed guardrails from the candidate payload.

No approve, import, edit persistence, assignment, schedule, status, Supabase write, Render deployment, or Vercel promotion authority was added.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/import-candidate/page.tsx`
2. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/page.tsx`
3. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.pm-import-candidate.smoke.spec.ts`
4. `C:/APEX Platform/apex-power-ops-platform/docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
5. `C:/APEX Platform/apex-power-ops-platform/docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
6. `C:/APEX Platform/apex-power-ops-platform/docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
7. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
8. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-033-import-candidate-pm-ui-review.json`
9. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-033-import-candidate-pm-ui-review-handoff.md`

The implementation adds:

1. a governed App Router page at `/pm-review/import-candidate`,
2. candidate fetch using the existing operations-web read-seam pattern,
3. candidate summary cards,
4. required decision cards,
5. warning review cards,
6. collapsed proposed workpackage/task details,
7. resource context cards,
8. source traceability and guardrail panels,
9. a focused Playwright smoke that stubs the read endpoint and asserts zero mutation calls,
10. route links from the operations-web shell and PM workflow docs.

## Sidecar Use

The PM Lane 032 external sidecar scout handoff was accepted as planning input:

`C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-032-sidecar-import-candidate-review-scout-handoff.md`

The implemented scope follows its recommendation:

1. one read-only route,
2. exception-first layout,
3. required decisions before dense tables,
4. clean task rows collapsed,
5. no approval/import mutation,
6. focused smoke proof.

An internal read-only sidecar scout independently matched the same scope and identified the existing page/test patterns to reuse.

## Validation

Passed:

```powershell
corepack pnpm --filter @apex/operations-web build

corepack pnpm --filter @apex/operations-web typecheck

cd "C:/APEX Platform/apex-power-ops-platform/apps/operations-web"
corepack pnpm exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-033-import-candidate-pm-ui-review.json', encoding='utf-8')); print('packet-json-ok')"

git diff --check
```

Results:

```text
operations-web build passed and listed /pm-review/import-candidate
operations-web typecheck passed
focused Playwright smoke passed: 1 passed
packet-json-ok
git diff --check passed
```

Note: The first typecheck attempt ran before Next refreshed route types and failed on stale generated `.next/types`. The subsequent build regenerated route types, and typecheck passed.

## Guardrails Preserved

1. No backend endpoint change.
2. No SQL or schema migration.
3. No live database write.
4. No production import job.
5. No workbook writeback.
6. No workbook macro execution.
7. No Render deployment action.
8. No Vercel promotion.
9. No service admission.
10. No auth or ingress widening.
11. No package dependency addition.
12. No approval persistence.
13. No candidate edit persistence.
14. No import mutation.
15. No assignment mutation.
16. No schedule mutation.
17. No status mutation.
18. No autonomous AI business-state mutation.

## Capability Gaps

1. Hosted Render mutation-seam parity still gates hosted proof of this route against live deployed API.
2. Vercel promotion was not performed in this lane.
3. Candidate approval, edit persistence, stale-source checking, and import mutation remain future lanes.

## Next Bounded Move

Recommended next product move:

`PM Lane 034 - Hosted Import Candidate Route Proof Or Local Review Hardening`

Decision point:

1. If Render/Vercel access is available, prove `/pm-review/import-candidate` against hosted surfaces.
2. If hosted parity remains blocked, keep local PM value moving by adding local review hardening: stale-source fingerprint, exportable candidate JSON, or row-level warning filters, still read-only.
