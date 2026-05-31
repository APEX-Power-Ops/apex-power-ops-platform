# TCC Explorer Quick Wins Closeout

Dispatch: `2026-05-31-cc-tcc-explorer-quickwins`
Result: PASS
Date: 2026-05-31

## Summary

Implemented the four quick wins from `apps/operations-web/TCC_EXPLORER_REALIGN_SPEC_2026-05-31.md` without schema or DDL changes.

Commits:

- `5f9af38b claim: 2026-05-31-cc-tcc-explorer-quickwins by codex`
- `7b66b35a web: add breaker explorer neta test plan quick wins`
- `21ca65a4 api: select etu search rank for distinct ordering`

The follow-up API commit fixed a hosted `SELECT DISTINCT` ordering issue by selecting the computed `search_rank` before ordering on it. Local-live route proof showed `GET /api/v1/neta/etu/search?q=GE&limit=5` returning status 200 with GE rows first before that hotfix was pushed.

No revert was needed.

## Changes

1. Rendered the NETA test-plan table in `breaker-selection-panels.tsx`.
   - ETU now consumes `selection.plot.table_rows`.
   - Columns: `Element`, `Setting`, `Test current (xmult)`, `Expected pickup`, `Lo`, `Hi`, `Expected time`, `Time-lo`, `Time-hi`, `Method`.
   - Absent rows with null expected values or absent calc methods are skipped.

2. Rendered tolerances as NETA bands.
   - ETU uses server-returned `table_rows.limit_low/high` and `time_limit_low/high`.
   - TMT surfaces the available selected setting tolerance as an equivalent pickup band.
   - EMT surfaces the available section pickup tolerance as an equivalent pickup band.
   - TMT/EMT do not currently return ETU-style per-element `table_rows`; the UI records this asymmetry by using the available tolerance fields rather than inventing delay rows.

3. Improved ETU search precision.
   - Removed the hardcoded ETU default seed `GE`; the explorer now starts empty.
   - `/etu/search` keeps the same route contract but ranks manufacturer matches first:
     exact manufacturer, manufacturer prefix, manufacturer contains, then trip type/style/sensor fallback.
   - `q=GE` now surfaces real GE rows at the top; `q=Challenger` still returns Challenger.

4. Relabeled the selector.
   - `Breaker family` is now `Trip Unit Type`.

## Local Validation

- Control-plane ETU search test:
  - `1 passed, 1 warning`
- Operations-web typecheck:
  - PASS
- Operations-web production build:
  - PASS
- Breaker browser Playwright smoke:
  - PASS, `1 passed`
  - Extended to assert the ETU NETA test-plan table renders and TMT/EMT tolerance bands are visible.
- Local-live route proof with the canonical read-only DSN:
  - `GET /api/v1/neta/etu/search?q=GE&limit=5` returned 200.
  - Top rows were GE manufacturer rows.

## Hosted Gate

Hosted surfaces:

- Control-plane: `https://control.apexpowerops.com`
- Operations-web: `https://operations.apexpowerops.com`

Deploy confirmation:

- Render served the intermediate quick-win build, then the `21ca65a4` hotfix. After the hotfix deployed, `q=GE` returned GE rows first.
- Hosted operations-web Playwright smoke passed against `https://operations.apexpowerops.com`, proving the deployed explorer renders the NETA table flow.

Post-deploy checks:

| Check | Result |
| --- | --- |
| `GET /api/v1/neta/etu/search?q=GE&limit=5` | PASS, top manufacturers: `GE, GE, GE, GE, GE` |
| `GET /api/v1/neta/etu/search?q=Challenger&limit=3` | PASS, top manufacturers: `Challenger, Challenger, Challenger` |
| `scripts/probe_live_etu_sql_parity.py` | PASS, 3 seeded scenarios, evaluate warnings: 0 |
| `scripts/probe_live_relay_sql_parity.py` | PASS, 6 seeded scenarios; warnings: 0; failures: 0 |
| `GET /api/v1/neta/catalog/status` | PASS, manufacturers: 63, sensors: 17831 |
| `GET /api/v1/neta/tmt/facets` | PASS, 200, total matching frames: 40264 |
| `GET /api/v1/neta/emt/facets` | PASS, 200, total matching frames: 805 |
| Hosted operations-web breaker smoke | PASS, `1 passed`; NETA test-plan table rendered for selected ETU sensor |

Next packet remains the structural dual-axis rebuild: `2026-05-31-cc-tcc-explorer-dualaxis-rebuild`.
