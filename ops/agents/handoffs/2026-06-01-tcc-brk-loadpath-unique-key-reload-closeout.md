# 2026-06-01 CC TCC breaker load-path unique-key reload closeout

## Status

Closed. The breaker parent-table load-path gap is remediated live and documented.

## What changed

- Added migration `infra/database/migrations/tcc/005_brk_loadpath_unique_key_reload.sql`.
- Dropped the old `UNIQUE (manufacturer_id, name)` constraints on `tcc.brk_{mccb,iccb,pcb}`.
- Added `UNIQUE NULLS NOT DISTINCT (manufacturer_id, name, standard, ac_dc_code)` on all three breaker parent tables.
- Normalized existing parent tuples from the Access source extracts:
  - `tcc.brk_mccb`: 121 existing rows updated, 41 missing twins inserted.
  - `tcc.brk_pcb`: 10 existing rows updated.
  - `tcc.brk_iccb`: no data changes required.
- Updated the TCC reference SSoT:
  - `reference/tcc/00-MASTER-INDEX.md`
  - `reference/tcc/G1-SCHEMA-GUIDE.md`
  - `reference/tcc/G2-RULES-GUIDE.md`

## Live verification

- Live parent counts:
  - `tcc.brk_mccb`: 640
  - `tcc.brk_iccb`: 29
  - `tcc.brk_pcb`: 157
- New widened constraint count: 3.
- Dry-run and live migration apply both completed cleanly.
- Post-apply source tuple validation found 0 missing Access 4-tuples and 0 duplicate widened keys.

## Route and parity checks

- `packages/calc-engine/tests` + targeted control-plane TCC route tests:
  - `97 passed, 1 skipped, 1 warning`
- `scripts/probe_live_etu_sql_parity.py --base-url https://control.apexpowerops.com --artifact-path ''`
  - PASS across 3 seeded ETU scenarios; evaluate warnings 0.
- `scripts/probe_live_relay_sql_parity.py --base-url https://control.apexpowerops.com --artifact-path ''`
  - PASS across 6 relay scenarios; warnings 0; failures 0.
- `scripts/smoke_local_neta_family_routes.py --base-url https://control.apexpowerops.com --artifact-path '' --candidate-limit 3`
  - Exit 0; catalog/ETU/TMT/EMT surfaces returned governed data.

## Residual noted

The parent rows are complete, but `tcc.brk_mccb_styles` still has 41 distinct `breaker_id` values that do not join to `tcc.brk_mccb`. This was observed before/after the parent-key reload and is not part of the parent unique-key fix. It should ride with the D1 breaker-style reload / bridge-surface lane, where style source IDs and parent surrogate mapping are reworked deliberately.

## Notes

- DSN material was sourced only from the canonical secrets file and was not printed.
- Access artifacts were read from the provided Drive folder; source CSVs were treated read-only.
