# Master EP to ETAP cross-reference workbook closeout

Dispatch: `2026-06-07-codex-master-ep-etap-crossref-xlsx`

Mode: prod Supabase read-only plus host-local ETAP Star Library help-doc crosswalk. No prod writes, no DDL, no serving/frontend changes, and no workbook binary committed.

## Generated artifacts

- Workbook: `C:\APEX Platform\apex-power-ops-platform\.audit_workspace\etap_tcc_sources\crosswalk\v2_starlib\EP_to_ETAP_master_crossref.xlsx`
- Host-local generator: `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/build_master_crossref_xlsx.py`
- Regenerated host-local TSVs:
  - `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/mfr_crosswalk.tsv`
  - `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/trip_unit_crosswalk.tsv`
  - `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/breaker_crosswalk.tsv`
  - `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/crosswalk_method.md`

Workbook provenance: `[ETAP Star Library List - published help docs] names-only crosswalk`.

## Workbook contents

| sheet | rows |
| --- | ---: |
| README | 10 |
| Summary | 54 |
| Manufacturers | 137 |
| Trips | 2,095 |
| Breakers | 14,222 |

Data sheets include source TSV columns, live shipped display state, and the catalog-resolution scaffold:

- `current_display`
- `display_source`
- `is_shipped_alias`
- `resolution_status`
- `catalog_source`
- `resolved_etap_mfr`
- `resolved_etap_model`
- `resolved_tier`
- `reviewer`
- `review_date`
- `notes`

All resolution rows are initialized as `unverified` with a dropdown for:
`unverified | confirmed | corrected | no_etap_equiv | superseded | needs_catalog`.

## Tier distribution

Manufacturers:

| tier | rows |
| --- | ---: |
| case | 3 |
| conditional | 2 |
| contract | 1 |
| expand | 3 |
| identity | 28 |
| label | 3 |
| none | 88 |
| punctuation | 4 |
| rebrand | 2 |
| shorthand | 1 |
| spelling | 1 |
| typo | 1 |

Trips:

| tier | rows |
| --- | ---: |
| exact | 486 |
| core | 362 |
| frame | 657 |
| none | 590 |

Breakers overall:

| tier | rows |
| --- | ---: |
| exact | 2,139 |
| core | 1,321 |
| frame | 2,071 |
| none | 8,691 |

Breakers by class:

| class | exact | core | frame | none | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| ICCB | 143 | 31 | 85 | 349 | 608 |
| MCCB | 1,374 | 1,017 | 1,546 | 6,398 | 10,335 |
| PCB | 622 | 273 | 440 | 1,944 | 3,279 |

## Live shipped state

| axis | shipped alias rows | EP raw fallback rows | total |
| --- | ---: | ---: | ---: |
| Manufacturers | 53 | 84 | 137 |
| Trips | 891 | 1,204 | 2,095 |
| Breakers | 3,460 | 10,762 | 14,222 |

Display-source meaning:

- Trips: `overlay`, `v2_model_alias`, or `ep_raw`
- Breakers: `alias` or `ep_raw`
- Manufacturers: `alias` or `ep_raw`

## Family-inference fix evidence

Before regeneration, the v2 Star Library closeout had:

`{'ETU': 2009, 'EMT': 52, 'MCP': 10, 'TMT': 24}`

After regeneration:

`{'ETU': 2046, 'EMT': 15, 'MCP': 10, 'TMT': 24}`

Delta: ETU +37, EMT -37, MCP unchanged, TMT unchanged.

Spot-checks from `trip_unit_crosswalk.tsv`:

- GE `VersaTrip MOD2` style IDs `39,40,41,42,43,44,45,2444` now resolve to `LVSST.htm`, `VersaTrip(MOD2)`, tier `exact`.
- Siemens `Static Trip II` style IDs `132-137` now resolve to `LVSST.htm`, `Static Trip II`, tier `exact`.
- Siemens `Static Trip III` style ID `138` now resolves to `LVSST.htm`, `Static Trip III`, tier `exact`.
- Multilin `Static Trip Rel` style ID `140` now resolves to `LVSST.htm`, `FB600`, tier `exact`; style ID `141` resolves to `FB600`, tier `core`.

Trip tier improvement after the fix: `none` dropped from 597 to 590; exact/core matched rows rose from 841 to 848; alias conflicts dropped from 40 to 33.

## Migration record

Added repo record only:

- `infra/database/migrations/tcc/016_tcc_trip_model_aliases_solidstate_fix.sql`
- `infra/database/migrations/tcc/016_tcc_trip_model_aliases_solidstate_fix_down.sql`

This records the 10 already-applied prod rows from CC migration `tcc_trip_model_aliases_solidstate_fix_seed`; it is marked do-not-rerun.

## Validation

- `uv run --with psycopg2-binary python build_v2_starlib_crosswalk.py`
- `uv run --with openpyxl --with psycopg2-binary python build_master_crossref_xlsx.py`
- Workbook self-checks:
  - source TSV row count assertions passed: Manufacturers 137, Trips 2,095, Breakers 14,222
  - no blank `current_display` values found
  - workbook reopened with expected sheets: `README`, `Summary`, `Manufacturers`, `Trips`, `Breakers`
  - reopened data row counts matched source TSV row counts
- Openpyxl structural inspection:
  - `Manufacturers`: `A1:S138`, freeze `A2`, autofilter `A1:S138`
  - `Trips`: `A1:Z2096`, freeze `A2`, autofilter `A1:Z2096`
  - `Breakers`: `A1:Y14223`, freeze `A2`, autofilter `A1:Y14223`

## Carry-forward

The operator should pick the workbook's durable home after the first manufacturer catalog-validation pass: either Box reference storage or a repo path such as `reference/tcc/crosswalk/`. The current workbook remains host-local by design, because this packet did not commit `.xlsx` binaries.
