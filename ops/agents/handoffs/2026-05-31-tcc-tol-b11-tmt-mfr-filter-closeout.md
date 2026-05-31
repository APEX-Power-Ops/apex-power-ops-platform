# B1.1 TMT Manufacturer Filter Closeout

Dispatch: `2026-05-31-codex-tcc-tol-b11-tmt-mfr-filter`
Executor: Codex
Date: 2026-05-31

## Summary

Implemented the backend-only TMT `/api/v1/neta/tmt/frames` filter fix.

Commit: `2a49965a api: filter tmt frames by hardware ids`

## Route Diff

- Added optional query params to `/tmt/frames`:
  - `manufacturer_id`
  - `breaker_id`
  - `breaker_style_id`
- Joined the class-specific breaker table and `tcc.manufacturers` before applying filters.
- Applied `manufacturer_id`, `breaker_id`, `breaker_style_id`, `manufacturer_name`, `breaker_name`, and `breaker_style_name` before the candidate `LIMIT`.
- Preserved backward-compatible partial `manufacturer_name` matching, with exact manufacturer-name matches ranked ahead of prefix and substring matches.

Changed files:
- `apps/control-plane-api/services/neta/router.py`
- `apps/control-plane-api/tests/test_neta_tmt_routes.py`

## Manufacturer Name Finding

`manufacturer_name=GE` was not a catalog data gap. Live read-only characterization found GE TMT frames in the catalog:

- GE manufacturer id: `9`
- GE MCCB TMT frames: `670`
- GE PCB TMT frames: `2119`

The zero-result behavior came from the old handler applying `manufacturer_name` after a pre-filter candidate sample. The sampled rows could exclude GE before the bundle-level name check ran. The patch moves name filtering into SQL before the limit and ranks exact manufacturer-name matches first.

## Validation

Local focused tests:

```text
DATABASE_URL=postgresql://postgres:postgres@localhost/test PYTHONPATH=. .venv/bin/pytest tests/test_neta_tmt_routes.py tests/test_neta_tmt_facets_route.py
10 passed, 1 warning
```

Local patched route against live read-only DSN:

- `manufacturer_id=9&breaker_class=MCCB&limit=8` returned 8 GE rows.
- `manufacturer_id=1&breaker_class=MCCB&limit=8` returned 8 ABB rows.
- `manufacturer_name=GE&breaker_class=MCCB&limit=8` returned 8 GE rows.
- `manufacturer_name=Square&breaker_class=MCCB&limit=8` returned 8 SquareD rows.
- No params remained unfiltered; `breaker_class=MCCB&limit=8` returned the same early mixed catalog rows.

Hosted deploy confirmation:

- Polling `https://control.apexpowerops.com/api/v1/neta/tmt/frames` showed old behavior for attempts 1-3.
- Attempt 4 showed deployed behavior:
  - `manufacturer_id=9` returned only GE rows.
  - `manufacturer_id=1` returned only ABB rows.
  - `manufacturer_name=GE` returned GE rows.

Post-deploy no-regression gates:

- ETU SQL parity: PASS across 3 seeded scenarios; evaluate warnings `0`.
- Relay SQL parity: PASS across 6 seeded scenarios; warnings `0`; failures `0`.
- `GET /api/v1/neta/catalog/status`: `catalog=live`, `manufacturer_count=63`, `sensor_count=17831`.
- `GET /api/v1/neta/tmt/facets`: `200`, `total_matching_frames=40264`, `facet_count=6`.
- `GET /api/v1/neta/emt/facets`: `200`, `total_matching_frames=805`, `facet_count=5`.

## Notes

No DDL, migrations, frontend changes, or secret material were introduced.
