# Catalog Library Normalization Closeout

Date: 2026-06-07

Packet: `ops/agents/inbox/pending/2026-06-07-codex-catalog-library-normalization.md`

## Result

Built the first normalized breaker/trip-unit catalog reference library under the synced review tree:

`C:\Users\jjswe\Resa Power, LLC\RESA Power Ops - Phoenix Files\Technical Data\_NORMALIZED_REVIEW`

Committed metadata only:

- `reference/tcc/catalogs/CATALOG-INDEX.csv`
- `reference/tcc/catalogs/README.md`
- `reference/tcc/00-MASTER-INDEX.md`

PDFs and local binary/tool files were not committed.

## Build Summary

- Local source files accounted: 216 / 216
- Local placed catalog docs: 150
- Local duplicate drops: 48
  - SHA-256 exact duplicates: 17
  - recovered doc identity duplicates: 31
- Local quarantined files: 18
- Verified web PDF downloads: 30
- Rejected web candidates: 12
- Total kept manifest rows: 198

Device-class distribution:

- `Breakers`: 88
- `Trip Units`: 92
- `_quarantine`: 18

Source-origin distribution:

- `lib-breakers`: 42
- `lib-trips`: 40
- `staging`: 86
- `web`: 30

Manufacturer distribution:

- Eaton: 41
- Unknown: 30, including 18 quarantined non-catalog/non-PDF files and 12 low-confidence kept PDFs
- Siemens: 23
- Schneider Electric: 19
- ABB: 18
- General Electric: 17
- Utility Relay: 7
- LSIS: 7
- Westinghouse: 7
- Allen-Bradley: 6
- Mitsubishi: 4
- Terasaki: 4
- Changshu: 4
- WEG: 4
- Moeller: 2
- Square-D: 2
- Cutler-Hammer: 1
- Legrand: 1
- OEZ: 1

## Workbook Gap Coverage

The EP to ETAP workbook currently has 12,009 trip/breaker rows at `none` or `frame` confidence.
After manufacturer-name normalization, 9,002 of those rows now have at least one catalog source
available by canonical manufacturer in the manifest. This is catalog availability only; it is not a
confirmed alias-resolution count.

Top remaining pressure points:

| Canonical manufacturer | Gap rows | Catalog in manifest |
|---|---:|---|
| Siemens | 1,558 | yes |
| ABB | 1,244 | yes |
| Eaton | 997 | yes |
| General Electric | 967 | yes |
| Square-D | 789 | yes |
| Cutler-Hammer | 759 | yes |
| Merlin Gerin | 479 | no |
| LSIS | 409 | yes |
| Fuji | 390 | no |
| Allen-Bradley | 328 | yes |
| Westinghouse | 316 | yes |
| Moeller | 288 | yes |
| Mitsubishi | 262 | yes |
| ITE (BBC) | 253 | no |
| Legrand | 245 | yes |
| Terasaki | 218 | yes |
| Schneider Electric | 199 | yes |
| L&T | 181 | no |
| OEZ | 180 | yes |
| Changshu | 160 | yes |

## Web-Downloaded Official PDFs

Verified web PDFs were downloaded only after `%PDF` magic-byte validation.

Covered vendors/families include:

- ABB: Tmax XT, SACE Emax 2, low-voltage selectivity
- Allen-Bradley: 140G/140MG catalog, selectivity, 140G-N curves
- Cutler-Hammer: Series C L-frame curves
- Eaton: MCCB catalog, Magnum DS/SB/IEC catalog, PXR trip-unit manual, selectivity tables
- General Electric: ABB-hosted instantaneous selectivity guide covering legacy GE/ABB families
- LSIS: Susol/Metasol ACB and Susol UL MCCB catalogs
- Mitsubishi: World Super V, AE-SW ACB catalog, AE-SW instruction manual
- Moeller: NZM selectivity guides
- Siemens: 3VA manual, 3VA selectivity guide, 3VL manual
- Terasaki: TemBreak PRO and TemPower PRO catalogs
- WEG: DWB UL, DWB IEC, UBW technical manual
- Legrand: DPX3 catalog

## Rejected Web Candidates

Rejected candidates were not placed in the library:

- ABB/GE BuyLog direct URLs returned 404.
- Schneider/Square-D `se.com/download/document/...` endpoints returned HTML landing pages instead of PDF bytes.
- Siemens LV10 catalog attachment returned 410.
- L&T D Sine MCCB and C-Power ACB direct URLs returned 404.

These should be revisited in a follow-up web-source pass using vendor landing-page extraction or manual download links.

## Low-Confidence Review Items

Twelve kept PDFs remain `canonical_mfr=Unknown` with `not_in_workbook=Y`. They are intentionally visible in the
manifest rather than force-classified:

- `1SDC007600G0201_WP MDGF_12.2024.pdf.pdf`
- `1010466024-la-3000.pdf`
- `3aaaef.pdf`
- `484019416-Catalogue-Record-Plus-English-7-pdf.pdf`
- `870643927-ACB-OMEGA.pdf`
- `9AKK108467A9440_en_B_BuyLog Section 8_ LV insulated case circuit breakers.pdf`
- `ACB WHG Series WH.08ACB0824.pdf`
- `DEA-013C.pdf`
- `kupdf.net_compact-merlin-gerin-str.pdf`
- `MCCB-WH-01-MCCB0924.pdf`
- `W1000710.pdf`
- `W1001130.pdf`

## Quarantine

Eighteen non-PDF/non-catalog local files were copied to `_NORMALIZED_REVIEW\_quarantine` and indexed:

- Excel curve calculators and quick-reference workbooks
- JPG screenshots
- loose `.txt` notes/extracts
- one `.dxf`
- one `.docx`

No originals were moved, renamed, or deleted.

## Validation

Commands run:

```powershell
uv run --with openpyxl --with pypdf python -m py_compile ".audit_workspace\etap_tcc_sources\catalogs\build_catalog_library.py"
uv run --with openpyxl --with pypdf python ".audit_workspace\etap_tcc_sources\catalogs\build_catalog_library.py"
```

Self-checks passed:

- Local accounting: `150 placed + 48 dropped + 18 quarantined == 216`
- Manifest rows: 198
- Normalized files: 198
- Every `normalized_relpath` in `CATALOG-INDEX.csv` exists under `_NORMALIZED_REVIEW`
- Every web download kept in the manifest had `%PDF` magic bytes
- No PDFs/binaries are staged for commit

Tooling note: `pdftotext` was not available on PATH, so page-one/two classification used `pypdf`.
Some source PDFs emitted recoverable `pypdf` "Ignoring wrong pointing object" warnings; extraction continued.

## Phase 2 Carry-Forward

Operator review is still required before replacing or retiring the loose source folders. The next useful lane is:

1. Manually resolve the 12 `Unknown` kept PDFs.
2. Revisit rejected Schneider/Square-D/ABB-GE/L&T vendor URLs through landing-page extraction.
3. Add Fuji, Merlin Gerin, ITE/BBC, L&T, Federal Pacific, Hyundai, Chint, Federal Pioneer, and other long-tail official catalogs.
4. Use the manifest to fill workbook `catalog_source`, `resolved_*`, and `resolution_status` fields.
