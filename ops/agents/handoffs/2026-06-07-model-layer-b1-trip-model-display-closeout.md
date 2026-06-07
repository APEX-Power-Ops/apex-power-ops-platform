# Model Layer b1 Trip-Unit Model Display Closeout

Date: 2026-06-07

## Scope

Completed the lvbreakertcc model-layer slice b1 serving/frontend wire-up for trip-unit model names. No production DDL or data write was performed; `tcc.trip_model_aliases` was already live and is now recorded in repo migration `014`.

## Commits

- `90d2723f feat(neta): show normalized trip unit models`

## Implementation

- Added `trip_model_display` to ETU cascade trip-type, trip-style, and sensor response models.
- Resolved display names in SQL with a lateral preferred-pick from `tcc.trip_style_aliases` where `match_tier in ('exact', 'core')`, excluding `frame`, then `tcc.trip_model_aliases.etap_model`, then raw EP fallback.
- Re-keyed trip-type and trip-style option dedupe on `manufacturer_display, trip_model_display`, preserving representative ids and merged `style_ids` / `trip_type_ids`.
- Updated operations web ETU trip dropdowns and selected sensor labels to render `trip_model_display ?? raw EP label`.
- Added migration record files:
  - `infra/database/migrations/tcc/014_tcc_trip_model_aliases.sql`
  - `infra/database/migrations/tcc/014_tcc_trip_model_aliases_down.sql`

## TDD

Red first:

- `pytest tests/test_neta_trip_model_display_routes.py -q`
- Result: `5 failed`
- Failure shape: `trip_model_display` absent from response models.

Green after implementation:

- `pytest tests/test_neta_trip_model_display_routes.py -q`
- Result: `5 passed, 1 warning`

## Validation

- Focused + adjacent backend routes:
  - `pytest tests/test_neta_trip_model_display_routes.py tests/test_neta_downstream_label_dedup_routes.py tests/test_cascade_route.py tests/test_etu_breaker_cascade_route.py tests/test_etu_bridge_sensors_route.py -q`
  - Result: `31 passed, 1 warning`
- Compile:
  - `python -m compileall services tests -q`
  - Result: pass
- Frontend:
  - `corepack pnpm --dir apps/operations-web typecheck`
  - Result: pass
  - `corepack pnpm --dir apps/operations-web build`
  - Result: pass
- Non-integration backend regression subset:
  - Result: `1095 passed, 1 skipped, 245 deselected, 1 warning`
- `git diff --check`
  - Result: pass

## Hosted Proof

- Pushed `90d2723f` to `main`.
- Vercel production checks:
  - `Vercel - apex-power-ops-platform`: success
  - `Vercel - apex-operations-web`: success
- Hosted API spot checks on `https://control.apexpowerops.com`:
  - `sensor_id=3841` trip-style row: `trip_style_id=238`, raw `MICROLOGIC 6.0A`, `trip_model_display=MICROLOGIC 6.0`
  - `sensor_id=10332` trip-style row: `trip_style_id=871`, raw `STR53UP`, `trip_model_display=STR53UP`
- Hosted UI proof on `https://operations.apexpowerops.com/lvbreakertcc`:
  - Selected ETU trip manufacturer `Square-D (70)`.
  - Trip Style dropdown had `56` options.
  - Normalized options included `MICROLOGIC 6.0 (1573)` and `MICROLOGIC 6.0 X (ANSI) (100)`.
  - Raw `MICROLOGIC 6.0A` option count was `0`.
  - Relevant control-plane browser requests returned `200`; only console error was the pre-existing favicon `404`.

## Counts

- Seed/source coverage recorded in the packet: `tcc.trip_model_aliases` has `826` rows (`473 exact`, `353 core`), with total expected ETAP display coverage around `881 / 2095` raw trip styles after authoritative exact/core overlay.
- Hosted API returns `trip_model_display` for every visible option because EP fallback is part of the serving `COALESCE`.
- Hosted global cascade display-key result:
  - `1123` visible trip-style options from `2092` merged raw `style_ids`
  - `265` options merge more than one raw style id
  - `232` visible option labels differ from the representative raw EP `trip_style_name`
- Hosted Square-D slice:
  - `55` visible trip-style options from `191` merged raw `style_ids`
  - `26` options merge more than one raw style id
  - `20` visible option labels differ from representative raw EP `trip_style_name`
  - `0` duplicate display groups within that selected manufacturer slice

## Surprises

- The cascade route intentionally keeps option lists broad at selected levels, so exact API proof used `sensor_id` filters and read the returned trip-style row rather than assuming a selected `trip_style_ids` request would narrow the style option list itself.
- Browser proof showed normalized model names immediately at both trip-type and trip-style dropdown levels after selecting Square-D.
