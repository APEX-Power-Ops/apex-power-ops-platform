# EP → ETAP Master Cross-Reference

Durable home for the EasyPower → ETAP nomenclature crosswalk — the working
artifact behind Apex Power's "central hub for NETA references." Every EasyPower
(EP) device in the governed TCC library is mapped to its ETAP-equivalent name,
with a confidence tier and an open scaffold for catalog-grade resolution.

## Asset

- **`EP_to_ETAP_master_crossref.xlsx`** — the master workbook (regenerate, don't hand-edit structure).

### Sheets
| sheet | rows | content |
| --- | ---: | --- |
| README | — | in-workbook method + column dictionary + tier legend |
| Summary | — | counts by axis × tier (× breaker class); shipped-vs-raw rollup |
| Manufacturers | 137 | EP mfr → ETAP mfr |
| Trips | 2,095 | ETU/TMT/MCP/EMT trip styles → ETAP trip model |
| Breakers | 14,222 | MCCB/ICCB/PCB styles → ETAP breaker model |

Each data row = the v2 crosswalk columns + **live shipped-display state**
(`current_display`, `display_source`, `is_shipped_alias` — what the
`lvbreakertcc` selectors render *today*) + the **resolution scaffold**
(`resolution_status` ∈ `unverified|confirmed|corrected|no_etap_equiv|superseded|needs_catalog`,
`catalog_source`, `resolved_etap_mfr`, `resolved_etap_model`, `resolved_tier`,
`reviewer`, `review_date`, `notes`).

## Provenance (§146-clean)

`[ETAP Star Library List - published help docs] names-only crosswalk`. The ETAP
side is sourced from ETAP's **published Star Library List help pages**
(`LVSST.htm`, `Thermal_Magnetic_Trip.htm`, `Motor_Circuit_Protector.htm`,
`Electro_Magnetic_Trip.htm`, the `*_Molded/Insulated/Power_*_breakers.htm` set).
**Names and identifiers only** — no decoded ETAP curve data is used, persisted,
or cited as curve authority. The EP side + `is_shipped_alias` are read from the
governed prod library (`tcc.*`) read-only.

## Confidence tiers (read before trusting a row)

| tier | meaning | trust |
| --- | --- | --- |
| `exact` | compact model equality, or model-core + matching protection code | high |
| `core` | model-core containment | good |
| `frame` | token + amp-number overlap only | **low — a hint to check, not an answer** |
| `none` | no Star Library candidate after mfr/family restriction | shows raw EP |

Only `exact`/`core` are shipped into the live alias tables today; `frame`/`none`
are intentionally **withheld** from the field tool (raw EP identity beats a
guessed ETAP name in a NETA tool). This workbook is exactly the worklist for
turning `frame`/`none` rows into catalog-confirmed `exact`/`core`.

## Resolution workflow

1. AutoFilter a manufacturer + tier (start with `frame`/`none` on the Breakers
   sheet — SQD + GE are ~65% of the unmapped mass).
2. Resolve each row against that manufacturer's **published catalog / reference
   manual** ([VENDOR-DOC] grade). Cite it in `catalog_source`.
3. Set `resolution_status` (`confirmed` if the v2 pick is right; `corrected` +
   `resolved_etap_model` if not; `no_etap_equiv` if EP has no ETAP analogue).
4. Hand the sheet back — CC promotes every `confirmed`/`corrected` row into the
   live alias tables (`tcc.mfr_aliases` / `tcc.trip_model_aliases` /
   `tcc.breaker_style_aliases`) as a governed, hash-checked write, then
   live-verifies on `operations.apexpowerops.com/lvbreakertcc`.

## Regeneration

Generators are workstation-bound (need the ETAP help install on `D:` + a prod
DSN) and live host-local under
`.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/` (gitignored):

```
uv run --with psycopg2-binary python build_v2_starlib_crosswalk.py      # refresh TSVs
uv run --with openpyxl --with psycopg2-binary python build_master_crossref_xlsx.py
```

Re-running rebuilds the v2 crosswalk TSVs and this workbook. The crosswalk
build encodes the §184 family-inference fix (static-trip / `MOD2` → ETU). Note:
regeneration **resets the resolution columns** — promote or export filled work
before regenerating, or merge by `trip_style_id` / `(breaker_class, style_id)`.

## Lineage

- Live serving + alias tables: STATE §181–§184; topic `project_tcc_lvbreaker_mvp_page_2026-06-01.md`.
- Migrations: `infra/database/migrations/tcc/013` (mfr) · `014` (trip-model) · `015` (breaker-model) · `016` (trip solid-state-fix).
- This workbook is a **living document** (binary; opaque to git diff). Periodic
  snapshots are fine; if churn becomes heavy, consider Git LFS.
