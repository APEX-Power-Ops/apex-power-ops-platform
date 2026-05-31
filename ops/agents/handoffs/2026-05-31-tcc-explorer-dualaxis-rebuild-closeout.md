# TCC Explorer Dual-Axis Rebuild Closeout

Dispatch: `2026-05-31-cc-tcc-explorer-dualaxis-rebuild`
Result: PASS
Date: 2026-05-31

## Summary

Completed the operations-web dual-axis rebuild as a code-only UI composition change. No backend endpoint, view, schema, or DDL change was made.

Commits:

- `217f7eee claim: 2026-05-31-cc-tcc-explorer-dualaxis-rebuild by codex`
- `5b210fb8 web: rebuild breaker explorer dual axis flow`

No revert was needed.

## Pre-Build Verification

Live and code verification confirmed the packet assumptions:

- `/api/v1/neta/etu/breaker-cascade` returns the breaker cascade levels:
  - `manufacturer_id`
  - `breaker_class`
  - `breaker_id`
  - `breaker_style_id`
- The same route accepts cross-half trip-unit filters:
  - `trip_type_id`
  - `trip_style_id`
  - `sensor_id`
- Live proof:
  - empty cascade: count `13897`, manufacturers `120`, classes `ICCB/MCCB/PCB`
  - `trip_type_id=390`: count `23`, manufacturers `1`
  - `sensor_id=29442`: count `68`, manufacturers `1`
  - `manufacturer_id=62&breaker_class=ICCB`: returned breaker-level rows
- `/api/v1/neta/etu/search` accepts `manufacturer_id`; live `manufacturer_id=9&q=GE&limit=3` returned GE rows.
- EMT exposes manufacturer/type/style/frame fields only:
  - live frame keys: `emt_id`, `frame_id`, `manufacturer_id`, `manufacturer_name`, `type_name`, `style_name`, `tcc_number`, `trip_char`, `trip_plug`, `frame_size`, `frame_desc`, `amp_rating_count`, `section_count`
  - no EMT construction / breaker-class signal was found.

EMT axis decision: EMT is manufacturer-intersection only for Axis 1. No construction axis is invented for EMT.

## Built Flow

`breaker-resource-explorer.tsx` now renders two primary axes together:

- Axis 1, Breaker:
  - `Breaker Manufacturer -> Breaker Class -> Breaker -> Breaker Style`
  - backed by `fetchEtuBreakerCascade`
- Axis 2, Trip unit:
  - `Trip Unit Type {ETU|TMT|EMT}` plus the existing family search/results flow
  - backed by `/etu/search`, `/tmt/frames`, and `/emt/frames`

Cross-filter wiring:

- Breaker manufacturer constrains ETU/TMT/EMT searches through existing `manufacturer_id` params.
- Breaker class constrains TMT search through the existing `breaker_class` param.
- Selected ETU trip-unit rows pass `trip_type_id`, `trip_style_id`, and `sensor_id` into the breaker cascade.
- A selected breaker style supplies the breaker context label used in the ETU plot request.

The quick-wins NETA test-plan table remains in the loaded selection panel and renders after context/settings/plot load.

## Local Validation

- Operations-web typecheck:
  - PASS
- Operations-web production build:
  - PASS
- Breaker browser Playwright smoke:
  - PASS, `1 passed`
  - Extended coverage:
    - selects breaker manufacturer/class/breaker/style
    - asserts trip-unit search receives `manufacturer_id`
    - asserts breaker cascade receives selected `sensor_id` and `breaker_style_id`
    - asserts loaded selection renders curve plus NETA test-plan table

## Hosted Gate

Hosted surfaces:

- Control-plane: `https://control.apexpowerops.com`
- Operations-web: `https://operations.apexpowerops.com`

Deploy confirmation:

- Vercel served the updated operations-web bundle after push; hosted Playwright smoke passed against `https://operations.apexpowerops.com`.
- No Render deploy was required for this packet because no backend code changed.

Post-deploy checks:

| Check | Result |
| --- | --- |
| Hosted operations-web breaker smoke | PASS, `1 passed`; dual-axis controls + loaded NETA table present |
| `scripts/probe_live_etu_sql_parity.py` | PASS, 3 seeded scenarios, evaluate warnings: 0 |
| `scripts/probe_live_relay_sql_parity.py` | PASS, 6 seeded scenarios; warnings: 0; failures: 0 |
| `GET /api/v1/neta/catalog/status` | PASS, manufacturers: 63, sensors: 17831 |
| `GET /api/v1/neta/tmt/facets` | PASS, 200, total matching frames: 40264 |
| `GET /api/v1/neta/emt/facets` | PASS, 200, total matching frames: 805 |
| `GET /api/v1/neta/etu/breaker-cascade?breaker_class=ICCB` | PASS, count: 608 |
| `GET /api/v1/neta/etu/breaker-cascade?sensor_id=29442` | PASS, count: 68, manufacturers: 1 |

The explorer now matches the EasyPower-style dual breaker x trip-unit selection methodology at the supported manufacturer-intersection boundary and carries the NETA pickup/time-delay tolerance table through the committed selection flow.
