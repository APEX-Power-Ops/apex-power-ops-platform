# Closeout: 2026-06-06-codex-mfr-display-serving-wireup

## Summary

Implemented the manufacturer-display serving wire-up for lvbreakertcc.

- Added additive `manufacturer_display` response fields for:
  - `/api/v1/neta/cascade`
  - `/api/v1/neta/etu/breaker-cascade`
  - `/api/v1/neta/tmt/manufacturers` and `/api/v1/neta/tmt/facets` shared model surface
  - `/api/v1/neta/emt/manufacturers` and `/api/v1/neta/emt/facets` shared model surface
- Joined `tcc.mfr_aliases` by EP manufacturer name and selected `COALESCE(a.etap_mfr_name, <raw name>) AS manufacturer_display`.
- Preserved EP `manufacturer_id` as the selection key and raw `manufacturer_name` in payloads.
- Updated operations-web lvbreakertcc manufacturer dropdown labels to render `manufacturer_display ?? manufacturer_name`.
- Added repo migration record `infra/database/migrations/tcc/013_tcc_mfr_aliases.sql` plus down file for the already-live 53-row alias seed.
- Did not add prod DDL in this packet.

## Commits

- Claim was already present upstream after rebase: `48236f75 claim: mfr-display-serving-wireup`.
- Implementation pushed: `67ff6913 feat(neta): surface manufacturer display aliases`.

## TDD And Local Validation

Tests were added first and confirmed red before implementation:

- Initial focused run: `tests/test_neta_manufacturer_display_routes.py` failed 4/4 because response models omitted `manufacturer_display`.

Green validation after implementation:

- `apps/control-plane-api`: `.venv/bin/python -m pytest tests/test_neta_manufacturer_display_routes.py -q`
  - Result: `4 passed`.
- `apps/control-plane-api`: `.venv/bin/python -m pytest tests/test_cascade_route.py tests/test_etu_breaker_cascade_route.py tests/test_neta_tmt_facets_route.py tests/test_neta_tmt_routes.py tests/test_neta_emt_facets_route.py tests/test_neta_emt_routes.py tests/test_neta_manufacturer_display_routes.py -q`
  - Result: `38 passed`.
- `apps/control-plane-api`: `.venv/bin/python -m compileall api services scripts tests utils main.py config.py`
  - Result: passed.
- `apps/operations-web`: `corepack pnpm --filter @apex/operations-web typecheck`
  - Result: passed.
- `apps/operations-web`: `corepack pnpm --filter @apex/operations-web build`
  - Result: passed.
- Repo root: `git diff --check`
  - Result: passed.
- API non-env regression pass:
  - `DATABASE_URL=postgresql://postgres:postgres@localhost/test .venv/bin/python -m pytest tests -q -k 'not test_runtime_env_files_prefers_repo_root_env_local_before_backend_env and not TestDemoBrowserWorkflow and not test_local_test_auth_sign_in and not test_local_test_auth_two_user_plan_isolation and not test_emt_live_discovery_context_settings_surface and not test_tmt_live_search_context_settings_plot_surface'`
  - Result: `1080 passed, 219 skipped, 27 deselected`.

Full API suite caveat:

- Attempted `DATABASE_URL=postgresql://postgres:postgres@localhost/test .venv/bin/python -m pytest tests -q`.
- Result: `1093 passed, 219 skipped, 14 failed`.
- Failures were local-environment/unrelated to this patch:
  - one Windows-path expectation in `test_config_database_url_resolution.py`
  - browser/local-test-auth/live-integration tests that require a local Postgres/service-backed runtime; this host had no localhost Postgres listening.

## Live Verification

Prerequisite:

- Prod read-only check confirmed `select count(*) from tcc.mfr_aliases;` = `53`.

Local API against prod read-only DSN:

- `/api/v1/neta/cascade`: `GE -> General Electric`.
- `/api/v1/neta/etu/breaker-cascade`: `Cutler Hammer -> Cutler-Hammer`.
- `/api/v1/neta/tmt/manufacturers?breaker_class=MCCB`: `Cutler Hammer -> Cutler-Hammer`.
- `/api/v1/neta/emt/manufacturers`: display field present; relabel rows include `GE -> General Electric` and `Square D -> Square-D`.

Hosted API after deploy propagation:

- `/api/v1/neta/cascade`: `GE -> General Electric`.
- `/api/v1/neta/etu/breaker-cascade`: `Cutler Hammer -> Cutler-Hammer`.
- `/api/v1/neta/tmt/manufacturers?breaker_class=MCCB`: `Cutler Hammer -> Cutler-Hammer`.
- `/api/v1/neta/emt/manufacturers`: `GE -> General Electric`.

Operations-web deploy:

- Vercel production deployment is READY for commit `67ff6913`: `dpl_H7g75Sb2sJvurDehqRTfq9jVHSAd`.
- Focused hosted browser check on `https://operations.apexpowerops.com/lvbreakertcc`:
  - ETU manufacturer dropdown rendered `General Electric (28)`.
  - TMT manufacturer dropdown rendered `Cutler-Hammer (753)`.

Promoted-host smoke:

- Backend seam passed.
- Hosted route smoke passed: 29/29.
- Browser smoke included lvbreakertcc pass.
- Overall promoted-host wrapper failed later on unrelated PM import-intake download timeout:
  - `tests/browser-shell.pm-import-intake.smoke.spec.ts:703`
  - waiting for `Export Financial Handoff Draft` download.

## Duplicate Display Follow-Up

As expected, display-name normalization creates duplicate-looking labels where multiple EP ids map to one display. Consolidation remains a separate increment because it changes the cascade filter from single id to display/id-set.

Observed duplicate display labels:

- ETU trip manufacturer dropdown:
  - `ABB`: SACE, ABB
  - `ITE (BBC)`: ITE, BBC
  - `LSIS`: LS Industrial, LG Industrial
- ETU breaker manufacturer dropdown:
  - `ABB`: SACE, ABB
  - `Cutler-Hammer`: Cutler Hammer, Cutler-Hammer
  - `Federal Pacific`: Federal Pacific, Fed Pacific
  - `Fuji`: Fuji, Fuji America
  - `ITE (BBC)`: Gould, ITE, Brown Boveri
  - `LSIS`: LS Industrial, LG Industrial
  - `Square-D`: SQD, Square D, SquareD
  - `Westinghouse`: Westinghouse, West
- TMT MCCB manufacturer dropdown:
  - `ABB`: SACE, ABB
  - `Cutler-Hammer`: Cutler Hammer, Cutler-Hammer
  - `Federal Pacific`: Federal Pacific, Fed Pacific
  - `Fuji`: Fuji America, Fuji
  - `ITE (BBC)`: Gould, ITE
  - `LSIS`: LG Industrial, LS Industrial
  - `Square-D`: SquareD, SQD
  - `Westinghouse`: West, Westinghouse
- TMT ICCB manufacturer dropdown:
  - none observed.
- TMT PCB manufacturer dropdown:
  - `ITE (BBC)`: Brown Boveri, ITE
  - `Square-D`: Square D, SQD
- EMT manufacturer dropdown:
  - none observed.

## Notes

- Optional `/etu/bridge-sensors` `manufacturer_display` was not included; this packet focused on the four manufacturer-list paths that drive the selectors.
- Public repo hygiene preserved: no secrets printed, scoped staging only.
