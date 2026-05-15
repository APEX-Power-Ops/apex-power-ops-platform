# PM Lane 001 Handoff - Miner Temp Lead Field And Workfront Read Model

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-001`
Scope: PM runtime product lane with delegated read-only sidecar review

## Summary

This tranche closes the current Miner Temp PM lead/field runtime work and adds the next read-only PM workfront slice.

The mutation seam now hydrates the demo PM lane from project-source workbook/PDF inputs when present, preserves fallback demo data when source files are missing, and exposes a PM workfront projection through `/api/v1/reads/pm-workfront`.

Operations Web now has promoted app routes for:

1. `/lead-ops`
2. `/field-tech`
3. `/pm-review/workfront`

The PM workfront route surfaces ready, blocked, unassigned, owner, designation, drawing reference, checklist progress, blocker counts, and next action while explicitly preserving `ai_mutation_authority: not_admitted`.

## Delegation And Orchestration Notes

Two read-only explorer delegates reviewed the dirty PM tranche before implementation closeout:

1. Backend explorer `019e2c1d-a73d-71e2-9f23-f41ae0046601` confirmed the workbook-backed seed/read implementation and recommended a thin PM workfront read-model builder beside the seed/read surface.
2. Frontend explorer `019e2c1d-bb34-7030-af89-55448b06a65e` confirmed the lead/field route implementation and recommended a sibling PM route under `/pm-review/workfront`.

Codex retained coordinator, reviewer, release-gate, and executor authority for integration, validation, publication, and host parity.

## Files Changed

Backend:

1. `apps/mutation-seam/app/pm_lane_seed.py`
2. `apps/mutation-seam/app/project_seed_sources.py`
3. `apps/mutation-seam/app/seed_workbooks.py`
4. `apps/mutation-seam/app/pm_workfront_read_model.py`
5. `apps/mutation-seam/app/db/memory_store_original.py`
6. `apps/mutation-seam/app/db/supabase_store.py`
7. `apps/mutation-seam/app/routers/reads.py`
8. `apps/mutation-seam/pyproject.toml`
9. `apps/mutation-seam/requirements.txt`
10. `apps/mutation-seam/tests/conftest.py`
11. `apps/mutation-seam/tests/test_pm_lane_seed.py`
12. `apps/mutation-seam/tests/test_project_seed_sources.py`
13. `apps/mutation-seam/tests/test_workbook_seed_reads.py`
14. `apps/mutation-seam/tests/test_pm_workfront_read_model.py`

Frontend:

1. `apps/operations-web/app/page.tsx`
2. `apps/operations-web/app/lead-ops/page.tsx`
3. `apps/operations-web/app/field-tech/page.tsx`
4. `apps/operations-web/app/pm-review/page.tsx`
5. `apps/operations-web/app/pm-review/workfront/page.tsx`
6. `apps/operations-web/tests/browser-shell.lead-field-lanes.smoke.spec.ts`
7. `apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`

Packet and status:

1. `PROJECT_STATUS.md`
2. `ops/agents/packets/draft/2026-05-15-pm-lane-001-miner-temp-lead-field-workfront-read-model.json`
3. `ops/agents/handoffs/2026-05-15-pm-lane-001-miner-temp-lead-field-workfront-read-model-handoff.md`

## Validation

Focused backend validation:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_lane_seed.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_seed_sources.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_workbook_seed_reads.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" -q
```

Result: `8 passed in 3.2s` with existing Pydantic v2 deprecation warnings.

Frontend validation:

```powershell
corepack pnpm build
corepack pnpm typecheck
corepack pnpm exec playwright test tests/browser-shell.lead-field-lanes.smoke.spec.ts tests/browser-shell.pm-workfront.smoke.spec.ts
```

Results:

1. `next build` passed and prerendered `/pm-review/workfront`.
2. `tsc --noEmit` passed after build-generated `.next/types` existed. An earlier parallel typecheck attempt raced with build and failed only because generated `.next/types` files were temporarily absent.
3. Playwright focused smoke passed `3 passed`.

Initial backend validation note:

- The first backend pytest attempt timed out because the autouse store reset could read workstation-default Desktop workbook/PDF paths before tests monkeypatched source paths. `apps/mutation-seam/tests/conftest.py` now forces missing seed paths for the default test reset, making the suite deterministic.

## Guardrails Preserved

1. No SQL or schema migration.
2. No new service admission.
3. No auth or ingress widening.
4. No Operations Visibility reopening.
5. No AI task bridge or AI business-state mutation.
6. PM workfront advisory output is read-only and explicitly reports `ai_mutation_authority: not_admitted`.

## Next Bounded Move

The next PM product slice should add one narrow action loop from the workfront, most likely a PM-to-lead follow-up note or filtered assignment handoff, while preserving read-first semantics until a later packet explicitly admits mutation authority.
