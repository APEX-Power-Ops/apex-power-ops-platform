# TCC Tolerance SC1 Guided Cascade Closeout

Dispatch: `2026-05-31-cc-tcc-tol-sc1-guided-cascade`
Executor: Codex
Date: 2026-05-31
Result: PASS

## Summary

Added the guided ETU selection path to operations-web using the existing read-only `GET /api/v1/neta/cascade` route. The ETU browser now lets a tech drill from trip manufacturer to trip type, trip style, and sensor before loading the existing context/settings/plot flow. The free-text `/etu/search` path remains available as a fallback.

Implementation commit: `e388c8eb`

## Cascade Contract Used

Live hosted contract verified against `https://control.apexpowerops.com/api/v1/neta/cascade`:

| Probe | Level | Count | Manufacturers | Trip types | Trip styles | Sensors | Plug values |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| root | `manufacturers` | `17831` | `63` | `558` | `2091` | `0` | `514` |
| `manufacturer_id=35` | `manufacturers` | `5243` | `63` | `70` | `191` | `0` | `101` |
| `manufacturer_id=35&trip_type_id=326` | `trip_types` | `37` | `1` | `70` | `9` | `0` | `56` |
| `manufacturer_id=35&trip_type_id=326&trip_style_id=241` | `trip_styles` | `4` | `1` | `1` | `9` | `4` | `22` |

Client support added in `apps/operations-web/lib/breaker-resources.ts`:

- response types for manufacturers, trip types, trip styles, sensors, and plug values
- `fetchCascade(params)` with `manufacturer_id`, `trip_type_id`, `trip_style_id`, `sensor_id`, `plug_value`, `breaker_class`, `breaker_id`, and `breaker_style_id`

## UI Flow

`breaker-resource-explorer.tsx` now renders ETU as the primary guided cascade:

- Trip Manufacturer
- Trip Type
- Trip Style
- Sensor

Each selection clears narrower selections and refetches the cross-filtered option lists. Final sensor selection is converted into the existing `EtuSearchResult` shape so the existing context, settings, breaker-cascade, and plot load path stays unchanged.

The existing free-text ETU search remains as `ETU search fallback`.

## B1.2 Fix

The Axis-1 breaker count no longer renders `0 matches` when the fetch is null or failed. It now renders:

- `loading` while pending
- `unavailable` on null/error
- real `${count} matches` only after a successful response

The same count-label behavior is used for the new ETU cascade count chip.

## Confirmation Surface

The loaded ETU selection now shows a confirmation summary with:

- manufacturer
- trip type
- trip style
- TCC number when present
- sensor description/rating
- compatible plug values

## Validation

Operations-web:

- `npm run typecheck`: PASS
- `npm run build`: PASS
- `npx playwright test tests/browser-shell.breaker.smoke.spec.ts`: PASS, `1 passed`

The Playwright smoke now asserts:

- guided cascade drives ETU load without `/etu/search`
- cascade requests include manufacturer, trip type, trip style, and breaker style filters
- loaded ETU selection renders the confirmation surface
- plot requests use separated delay fields: `ltd_delay_setting`, `std_delay_setting`, `gfd_delay_setting`, and the matching `*_test_multiple` fields
- TMT and EMT paths still load context/settings/static curves

Backend and hosted no-regression gates:

- `PYTHONPATH=. .venv/bin/python -m pytest tests/test_neta_plot_tcc.py -q`: `37 passed, 1 warning`
- ETU SQL parity: PASS, `3` seeded scenarios, evaluate warnings `0`
- Relay SQL parity: PASS, `6` seeded scenarios, warnings `0`, failures `0`
- `GET /api/v1/neta/catalog/status`: `catalog=live`, manufacturers `63`, sensors `17831`
- `GET /api/v1/neta/tmt/facets`: `200`, total matching frames `40264`, facets `6`
- `GET /api/v1/neta/emt/facets`: `200`, total matching frames `805`, facets `5`

## Hosted Deploy

Vercel deploy confirmation: PASS. Hosted operations-web breaker smoke passed against `https://operations.apexpowerops.com`.

Hosted cascade drill-down check:

```text
OPERATIONS_WEB_BROWSER_SMOKE_BASE_URL=https://operations.apexpowerops.com npx playwright test tests/browser-shell.breaker.smoke.spec.ts
1 passed
```

The hosted smoke exercised the guided ETU cascade selectors, loaded the selected ETU context/settings/plot flow, and verified the confirmation surface. The test intercepts API calls to keep the browser proof deterministic; the live `/cascade` contract was separately verified above.

## Notes

No backend route, DDL, migration, or secret material was introduced for the SC1 UI packet.
