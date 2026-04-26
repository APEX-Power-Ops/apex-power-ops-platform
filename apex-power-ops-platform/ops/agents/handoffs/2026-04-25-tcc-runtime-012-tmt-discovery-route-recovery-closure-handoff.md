# TCC Runtime 012 TMT Discovery Route Recovery Closure Handoff

Date: 2026-04-25
Packet: `2026-04-25-tcc-runtime-012`
Status: **Closed**
Authority: `2026-04-25-tcc-runtime-012-014-claude-code-sequenced-execution-handoff.md`
Project: live Supabase `fxoyniqnrlkxfligbxmg`

## Outcome

`/api/v1/neta/tmt/facets` and `/api/v1/neta/tmt/frames` are responsive. The bounded live probe budget that previously timed out now completes with a single sub-3-second cold call and sub-quarter-second warm calls. The previously-responsive `/api/v1/neta/tmt/context/{frame_id}` and `/api/v1/neta/tmt/settings/{frame_id}` surfaces remain intact. EMT browse routes are unchanged. No SQL writes, schema migrations, or DDL were applied.

## Root Cause

`_fetch_tmt_browse_rows_rest` (services/neta/router.py) builds the unified TMT browse population by calling `_fetch_rest_rows_paginated` for nine separate Supabase Data API endpoints in series. Live row counts:

| Table | Live rows | Paginated REST round trips at 1000/page |
|---|---:|---:|
| `tcc_tmt_amps` | 66,960 | 67 |
| `tcc_tmt_frames` | 42,069 | 43 |
| `tcc_brk_mccb_styles` | 10,335 | 11 |
| `tcc_brk_pcb_styles` | 3,279 | 4 |
| `tcc_brk_iccb_styles` | 608 | 1 |
| `tcc_brk_mccb` | 599 | 1 |
| `tcc_brk_pcb` | 157 | 1 |
| `tcc_brk_iccb` | 29 | 1 |
| `tcc_manufacturers` | 450 | 1 |
| **TMT cold-start total** | — | **~125 sequential REST round trips** |
| `tcc_emt_*` (all four EMT cold tables) | 4,435 | 5–6 |

Each `_supabase_rest_json` call carries a 20-second per-call socket timeout. The TMT cold start runs ~125 of those calls in series; even at 200–500 ms per call, the chain easily exceeds any practical request-level timeout. EMT cold start runs ~6 calls and finishes in seconds.

`/tmt/context` and `/tmt/settings` survive because their route handlers try the SQLAlchemy session-backed `_load_tmt_contract_bundle(db, frame_id)` first (per-frame queries that complete in milliseconds) and only fall back to REST on exception. `/tmt/frames` previously contained an unconditional `raise RuntimeError("TMT frame search is routed through browse helper for consistent live selector performance")` that forced REST, and `/tmt/facets` called `_build_tmt_facets_rest` directly with no SQL path — both depended on the cold-start REST helper, which is what hung.

## Surfaces Changed

`services/neta/router.py`:

- **Added** `import threading`.
- **Added** `_TMT_BROWSE_SQL` (a single `text(...)` query that materializes the unified TMT browse population in one Postgres round trip via three CTEs: `styled` (UNION ALL of the three class-specific style tables), `breakered` (UNION ALL of the three class-specific breaker tables), and `amps_per_frame` (`array_agg(DISTINCT rating)`)). The result LEFT JOINs these CTEs onto `tcc_tmt_frames` and `tcc_manufacturers` and produces the same browse-row shape as `_fetch_tmt_browse_rows_rest`.
- **Added** `_TMT_BROWSE_SQL_CACHE` and `_TMT_BROWSE_SQL_LOCK` for module-level memoization (one execution per process, thread-safe).
- **Added** `_reset_tmt_browse_sql_cache()` helper for test ergonomics.
- **Added** `_fetch_tmt_browse_rows_sql(db: Session)` — the SQL-backed primary path. Returns the same tuple-of-dicts shape as the REST helper. Raises if the result is empty so the route can fall through to REST.
- **Added** `_search_tmt_frames_in_rows(rows, ...)` and `_build_tmt_facets_in_rows(rows, ...)` — pure filter/aggregate helpers parameterized by `rows`.
- **Refactored** `_search_tmt_frames_rest` and `_build_tmt_facets_rest` into thin wrappers that call the new `_in_rows` helpers with `_fetch_tmt_browse_rows_rest()` as the source.
- **Replaced** the unconditional `raise RuntimeError` in `/tmt/frames` and the direct REST call in `/tmt/facets` with `try _fetch_tmt_browse_rows_sql(db) except → _fetch_tmt_browse_rows_rest()` and added `db: Session = Depends(get_db)` to `/tmt/facets`. The `_prefer_supabase_data_api_reads()` env-flag gate is intentionally not honored on these two discovery routes — the data is too large for paginated REST to satisfy the live timeout budget. A code comment records this exception. Other endpoints' flag handling is unchanged.

`tests/test_tmt_browse_sql_recovery.py` (new, 6 tests):

- `test_tmt_facets_uses_sql_browse_rows` — proves `/tmt/facets` consumes SQL rows and never calls REST when SQL succeeds.
- `test_tmt_frames_uses_sql_browse_rows` — same for `/tmt/frames`, with filter pushdown verified.
- `test_tmt_facets_falls_back_to_rest_when_sql_fails` — SQL helper raises → REST helper invoked exactly once.
- `test_tmt_frames_falls_back_to_rest_when_sql_fails` — same for frames.
- `test_tmt_browse_sql_helper_caches_first_call` — confirms second call returns the same tuple object without re-executing the SQL.
- `test_tmt_browse_sql_helper_raises_on_empty_result` — empty cursor result raises so the route falls back rather than returning empty.

`tests/test_neta_tmt_routes.py`:

- Updated `test_tmt_frame_search_returns_matching_frames` to mock `_fetch_tmt_browse_rows_sql` (the new primary source) rather than the removed legacy `db.query(TMTFrame)...` chain. The test was already broken against current code; this aligns it with the new SQL-first architecture and matches the route under test.

## Validation

### Focused tests

```
tests/test_tmt_browse_sql_recovery.py — 6 passed
tests/test_neta_tmt_routes.py         — 7 passed
                              total — 13 passed, 1 warning, 2.14s
```
(SQLAlchemy `MovedIn20Warning` from `models/base.py` is pre-existing and unrelated.)

### Live probes (project `fxoyniqnrlkxfligbxmg`, server bound to 127.0.0.1:8765 with `DATABASE_URL` from `.secrets/tcc-v5-backend.env`)

| Probe | Status | Time |
|---|---|---:|
| `GET /api/v1/neta/tmt/facets` (cold) | 200 | **2.354 s** |
| `GET /api/v1/neta/tmt/facets` (warm) | 200 | 0.214 s |
| `GET /api/v1/neta/tmt/facets?breaker_class=MCCB` | 200 | 0.195 s |
| `GET /api/v1/neta/tmt/frames?limit=2` | 200 | 0.004 s |
| `GET /api/v1/neta/tmt/frames?limit=5` | 200 | 0.003 s |
| `GET /api/v1/neta/tmt/frames?manufacturer_name=SquareD&breaker_class=MCCB&limit=2` | 200 | 0.025 s |
| `GET /api/v1/neta/tmt/context/28244` | 200 | (REST cold path; pre-existing) |
| `GET /api/v1/neta/tmt/settings/28244` | 200 | 0.671 s |
| `GET /api/v1/neta/emt/facets` | 200 | 0.989 s |
| `GET /api/v1/neta/emt/frames?limit=2` | 200 | 0.004 s |

The cold `/tmt/facets` query plan was confirmed via `EXPLAIN ANALYZE` against the live project before the code change: `Execution Time: 692.748 ms` for the full 42,069-row population, dominated by `Index Only Scan using tcc_tmt_amps_frame_id_rating_key` and `Index Scan using idx_tcc_tmt_frames_breaker_style_id`.

`/tmt/facets` returned full live distributions:

- `breaker_classes`: `MCCB: 30,809; PCB: 11,260` (sums to 42,069 = full `tcc_tmt_frames` row count; `ICCB` frames in the live data have no rows in `tcc_tmt_frames` so they correctly do not appear).
- `manufacturers`: 100+ entries including `ABB`, `Allen-Bradley`, `bticino`, `Changshu`, `SquareD`, etc.

Filtered `/tmt/frames?manufacturer_name=SquareD&breaker_class=MCCB&limit=2` returned two SquareD MCCB frames (`frame_id=28244`, `frame_id=28245`, both `breaker_style_id=7799`, breaker `E Frame`, style `ML`, frame size `100.0`). 500 SquareD MCCB frames exist in live data; the `limit=2` shaping is honored.

### Live data observations (informational, not regressions)

- Some `tcc_tmt_frames` rows reference a `breaker_style_id` whose style row points to a `breaker_id` that has no matching row in the corresponding class-specific breakers table (e.g. frame 11736 → style 4211 → breaker_id 273, no MCCB breaker row at 273). The new SQL `LEFT JOIN` returns these frames with `manufacturer_name=null` and `breaker_name=null`, matching the existing REST helper's behavior. This is a live data integrity quirk, not a packet-012 bug, and is not in scope.
- The live manufacturer name is `SquareD` (no space), not `Square D`. Filter callers must match exactly; this is the existing `_string_equals_ci` contract and is not changed.

## Hard Limits Respected

- ETU packets `010` and `011` were not reopened. No `services/calc_engine`, `services/neta/schemas.py` (control-path block), `demo/neta_tcc.html` user-facing surface, or ETU test changes.
- No SQL writes. No schema migrations. No DDL. The new path uses the existing `tcc_brk_*`, `tcc_brk_*_styles`, `tcc_tmt_amps`, `tcc_tmt_frames`, `tcc_manufacturers` tables exactly as they ship today.
- `public._009_rollback_snapshot` was not touched.
- No widening into `/tmt/plot-tcc`, EMT, curve-drawing completion, demo redesign, or selector parity (those remain packet-013 / packet-014 scope).
- The current local REST browse checkpoint was retained as the documented fallback path on every TMT discovery route. It was not replaced wholesale.

## Merge Gate

| Gate | Result |
|---|---|
| Syntax check | PASS — `ast.parse` clean |
| Focused tests | PASS — 6 new + 7 existing TMT route tests |
| Live cold probe `/tmt/facets` | PASS — 200 in 2.354 s |
| Live warm probe `/tmt/facets` | PASS — 200 in 0.214 s |
| Live probe `/tmt/frames?limit=2` | PASS — 200 in 0.004 s |
| Filtered live probe `/tmt/frames?manufacturer_name=SquareD&breaker_class=MCCB` | PASS — 200 in 0.025 s, 2 frames returned |
| Regression: `/tmt/context`, `/tmt/settings`, `/emt/facets`, `/emt/frames` | PASS — all 200 |
| Closure handoff authored | PASS — this file |

## Next Lane

Packet `013` (`Family Selector Parity And Dual-Filter Demo Alignment`) is unblocked. Per the sequenced execution handoff, packet 013 must use the now-responsive TMT discovery surface to land named selector parity across TMT and EMT, while keeping EMT bounded to its current frame/context/section-settings/plot contract. Selector work must materially improve the flow rather than cosmetically relabel raw ids. Packet `014` remains gated on packet 013.
