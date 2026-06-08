# Catalog Curation Phase 2 Closeout

Date: 2026-06-07

Packet: `ops/agents/inbox/pending/2026-06-07-codex-catalog-curation-phase2.md`

## Result

Curated the normalized breaker/trip-unit catalog review tree and regenerated the committed manifest.

Review tree:

`C:\Users\jjswe\Resa Power, LLC\RESA Power Ops - Phoenix Files\Technical Data\_NORMALIZED_REVIEW`

Committed metadata:

- `reference/tcc/catalogs/CATALOG-INDEX.csv`
- `reference/tcc/catalogs/README.md`
- `reference/tcc/00-MASTER-INDEX.md`

No PDFs or binaries were committed.

## Final Counts

- Manifest rows: 206
- Normalized review-tree files: 206
- Reclassified non-quarantine `Unknown` PDFs: 12
- Long-tail staged PDFs added: 14
- Dedup/superseded staged PDFs dropped: 5
- Non-quarantine `Unknown` rows remaining: 0
- Quarantine rows remaining: 12

Device classes:

- `Breakers`: 100
- `Trip Units`: 94
- `_quarantine`: 12

Top manufacturer counts:

- Eaton: 41
- Siemens: 23
- ABB: 21
- General Electric: 20
- Schneider Electric: 19
- Westinghouse: 10
- LSIS: 7
- Utility Relay: 7
- Allen-Bradley: 6
- Merlin Gerin: 5

## Bucket A Reclassifications

| Old relpath | New relpath |
|---|---|
| `Breakers/Unknown/Unclassified/1SDC007600G0201_WP MDGF_12.2024.pdf.pdf` | `Breakers/ABB/Ground-fault white paper (MDGF)/1SDC007600G0201_WP MDGF_12.2024.pdf.pdf` |
| `Breakers/Unknown/Unclassified/9AKK108467A9440_en_B_BuyLog Section 8_ LV insulated case circuit breakers.pdf` | `Breakers/ABB/BuyLog Sec. 8 _ ICCB/9AKK108467A9440_en_B_BuyLog Section 8_ LV insulated case circuit breakers.pdf` |
| `Breakers/Unknown/Unclassified/1010466024-la-3000.pdf` | `Breakers/Allis-Chalmers/LA-3000_4000 ACB/1010466024-la-3000.pdf` |
| `Breakers/Unknown/Unclassified/3aaaef.pdf` | `Trip Units/ITE/Power Shield SS trip/3aaaef.pdf` |
| `Trip Units/Unknown/Selectivity/484019416-Catalogue-Record-Plus-English-7-pdf.pdf` | `Breakers/General Electric/Record Plus FD_FE MCCB/484019416-Catalogue-Record-Plus-English-7-pdf.pdf` |
| `Breakers/Unknown/M-Pact/870643927-ACB-OMEGA.pdf` | `Breakers/L&T/Omega ACB/870643927-ACB-OMEGA.pdf` |
| `Trip Units/Unknown/ComPacT NS/kupdf.net_compact-merlin-gerin-str.pdf` | `Trip Units/Merlin Gerin/Compact STR trip/kupdf.net_compact-merlin-gerin-str.pdf` |
| `Breakers/Unknown/Unclassified/W1000710.pdf` | `Trip Units/Federal Pioneer/USR solid-state trip/W1000710.pdf` |
| `Trip Units/Unknown/Unclassified/W1001130.pdf` | `Breakers/Westinghouse/Pow-R _ DS draw-out/W1001130.pdf` |
| `Breakers/Unknown/Unclassified/DEA-013C.pdf` | `Breakers/General Electric/Power Break II ICCB/DEA-013C.pdf` |
| `Breakers/Unknown/WHG/ACB WHG Series WH.08ACB0824.pdf` | `Breakers/Westinghouse/WHG ACB/ACB WHG Series WH.08ACB0824.pdf` |
| `Breakers/Unknown/Unclassified/MCCB-WH-01-MCCB0924.pdf` | `Breakers/Westinghouse/G_F_J MCCB/MCCB-WH-01-MCCB0924.pdf` |

Verification notes:

- Page 1-3 text confirmed 8 directly.
- `870643927-ACB-OMEGA.pdf`, `W1001130.pdf`, and `ACB WHG Series WH.08ACB0824.pdf` were supported by family/device text plus packet identification.
- `DEA-013C.pdf` was image-only in page text; kept as General Electric / Power Break II based on packet identification and metadata.
- Modern licensed Westinghouse WHG/G-F-J docs are flagged in manifest notes as modern licensed brand, not legacy Westinghouse lineage.

## Bucket B Long-Tail Additions

Added:

- Fuji / BT3 Series ACB
- Fuji / DW Series ACB
- Fuji / MCCB/ELCB Americas
- ITE / Solid State Trip / 504 Test Set
- ITE / K-Line K225-K2000
- General Electric / MicroVersaTrip RMS-9
- L&T / C-Power ACB
- L&T / D Sine MCCB
- Merlin Gerin / Compact NS
- Merlin Gerin / Complementary Technical Information
- Merlin Gerin / Masterpact NT/NW
- Merlin Gerin / Application Guide
- ABB / BuyLog Sec. 6 / MCCB
- Square-D / PowerPacT H/J/L

`retrieved=2026-06-06` was used for staged web PDFs because no staging note/source-URL metadata was present.

## Dedup Decisions

| Dropped source | Kept relpath | Reason |
|---|---|---|
| `larsen-toubro/lt-omega-acb.pdf` | `Breakers/L&T/Omega ACB/870643927-ACB-OMEGA.pdf` | exact SHA duplicate |
| `rejected-revisit/abb_buylog_08_lv_power_insulated_case_breakers.pdf` | `Breakers/ABB/BuyLog Sec. 8 _ ICCB/9AKK108467A9440_en_B_BuyLog Section 8_ LV insulated case circuit breakers.pdf` | exact SHA duplicate |
| `rejected-revisit/lt_cpower_acb_catalogue.pdf` | `Breakers/L&T/C-Power ACB/lt-cpower-acb-catalogue-2024.pdf` | partial/superseded by full 2024 copy |
| `rejected-revisit/lt_dsine_mccb_catalogue.pdf` | `Breakers/L&T/D Sine MCCB/lt-dsine-mccb-catalogue.pdf` | exact SHA duplicate |
| `rejected-revisit/siemens_3va_mccb_ul_catalog.pdf` | `Breakers/Siemens/SENTRON 3VA/sie-pc-3va-catalog.pdf` | exact SHA duplicate already present |

SHA evidence is recorded in:

- `.audit_workspace/etap_tcc_sources/catalogs/phase2_dedup_decisions.csv`

## Manufacturer Alias Candidates

No `not_in_workbook=Y` non-quarantine vendors remain after checking the workbook `Manufacturers` sheet.

CC review notes:

- Allis-Chalmers is present via `Allis Chalmer` / `Allis-Chalmers`.
- ITE is present, though the workbook canonical display is `ITE (BBC)`.
- L&T is present via `Larsen & Toubro` -> `L&T`.
- Federal Pioneer and Westinghouse are present.
- Modern licensed Westinghouse line should be reviewed semantically, but it is not a missing manufacturer-vocabulary candidate.

## Validation

Commands run:

```powershell
uv run --with openpyxl --with pypdf python -m py_compile ".audit_workspace\etap_tcc_sources\catalogs\curate_catalog_phase2.py"
uv run --with openpyxl --with pypdf python ".audit_workspace\etap_tcc_sources\catalogs\curate_catalog_phase2.py"
```

Checks passed:

- 206 manifest rows
- 206 normalized files
- zero missing `normalized_relpath` targets
- zero non-quarantine `Unknown` rows
- no `Unknown` directories remain under `Breakers/` or `Trip Units/`
- no staged PDFs/binaries

Commit hash: recorded in final operator response after commit/push.
