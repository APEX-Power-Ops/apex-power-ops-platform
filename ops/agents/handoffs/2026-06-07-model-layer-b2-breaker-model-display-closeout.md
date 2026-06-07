# Model Layer B2 Breaker Model Display Closeout

Date: 2026-06-07
Packet: `ops/agents/inbox/pending/2026-06-07-codex-model-layer-b2-breaker-model-display.md`

## Commits

- `39bf1e1c` `feat(neta): show normalized breaker models`
- `52308976` `fix(neta): guard breaker alias rollout`
- `fc2d4b1d` `ci(control-plane): pin compile workflow actions`
- `71157dcb` `fix(neta): qualify ETU breaker style filters`
- Related CC packet update on `main`: `c052d4f0` `chore(inbox): b2 packet - all 3 breaker classes now seeded (3460 rows)`

## What Changed

- Added additive `breaker_model_display` fields across ETU breaker styles, ETU bridge sensors, TMT frame search/context/plot metadata, and operations-web resource types.
- ETU breaker-style display resolves with `COALESCE(tcc.breaker_style_aliases.etap_model, EP raw frame)` and keeps raw frame fields for compatibility.
- ETU breaker/frame dedup now keys on `(manufacturer_display, breaker_model_display)`.
- TMT frame label grouping uses `breaker_model_display` when present, preserving raw fallback.
- Frontend ETU/TMT breaker-frame dropdown labels render `breaker_model_display ?? breaker_style_name`.
- Migration record `infra/database/migrations/tcc/015_tcc_breaker_style_aliases.sql` now records the fully seeded alias set: PCB 895 + MCCB 2391 + ICCB 174 = 3460 rows.
- Added runtime guard for environments where `tcc.breaker_style_aliases` is not visible yet, falling back to raw EP frames instead of 500.
- Fixed ETU style-level class filters after the alias join by qualifying `etu_breaker_combined.breaker_class`, avoiding ambiguous-column 500s.
- Pinned the triggered control-plane compile workflow actions to full commit SHAs to satisfy the repo Actions policy.

## Validation

- TDD red: initial breaker model-display contract test failed before implementation (`6 failed`).
- Focused green: `pytest tests/test_neta_breaker_model_display_routes.py -q` -> `7 passed, 1 warning`.
- Adjacent backend: `pytest tests/test_neta_breaker_model_display_routes.py tests/test_etu_breaker_cascade_route.py tests/test_neta_downstream_label_dedup_routes.py tests/test_neta_trip_model_display_routes.py tests/test_etu_bridge_sensors_route.py tests/test_cascade_route.py -q` -> `38 passed, 1 warning`.
- Compile: `python -m compileall services tests -q` -> pass.
- Backend non-integration regression: `1102 passed, 1 skipped, 245 deselected, 1 warning`.
- Frontend: `corepack pnpm --dir apps/operations-web typecheck` -> pass.
- Frontend build: `corepack pnpm --dir apps/operations-web build` -> pass.
- GitHub checks for `71157dcb`: `compile` success.
- Deployment statuses for `71157dcb`: Vercel `apex-power-ops-platform` success, Vercel `apex-operations-web` success.

## Hosted Proof

- OpenAPI exposes `breaker_model_display` on `EtuBreakerStyleOption`, `TMTFrameSearchResult`, and `EtuBridgeSensor`.
- Hosted ETU spot check:
  - `GET https://control.apexpowerops.com/api/v1/neta/etu/breaker-cascade?breaker_class=PCB&breaker_style_id=3125`
  - returned matching row `PCB / 3125 / NW12H1` with `breaker_model_display = NW12H1`.
- Hosted ETU class-filter check:
  - `GET https://control.apexpowerops.com/api/v1/neta/etu/breaker-cascade?breaker_class=PCB&breaker_id=42`
  - returned `200`, `level=breaker_styles`, `count=15`, `styles=15`, all with non-null display labels.
- Hosted TMT divergence check:
  - `GET /api/v1/neta/tmt/frames?breaker_class=PCB&manufacturer_ids=17&limit=50`
  - returned `count=50`, `display_non_null=50`, `dedupe_divergence_count=28` versus the slice-a Square-D PCB baseline of 90.
  - Combined `manufacturer_ids=17&35&235` returned `dedupe_divergence_count=26`.
- Browser proof:
  - Opened `https://operations.apexpowerops.com/lvbreakertcc`.
  - Selected ETU -> Square-D -> PCB -> MP NW C37.
  - Frame dropdown enabled and showed normalized labels such as `NW08H1`, `NW16H1`, `NW32H1`, `NW40H2`, rather than raw amp-suffixed EP labels.
  - Only console error observed was missing `favicon.ico` (404).

## Surprises / Notes

- Control-plane hosted runtime is Render-backed (`x-render-origin-server: uvicorn`), while GitHub commit statuses also report Vercel deployments. Render propagation briefly served the pre-fix ETU 500, then the plain hosted URLs returned 200 after deployment settled.
- The class-filtered ETU 500 was not the missing-table case; it was an ambiguous SQL column after joining `tcc.breaker_style_aliases`.
- Direct TMT probes for ETU spot style ids like 3125 returned zero because those style ids do not necessarily exist in `tcc.tmt_frames`; TMT proof used surfaced TMT frame rows instead.
- The repo still has pre-existing local residue outside this packet: `.vscode/tasks.json`, `apps/control-plane-api/uv.lock`, and `packages/calc-engine/uv.lock`.
