# TCC Catalog Reference Library

This directory contains the committed metadata index for the Apex TCC breaker and trip-unit catalog library.
The PDFs themselves are intentionally not committed; they live in the synced review tree:

`C:\Users\jjswe\Resa Power, LLC\RESA Power Ops - Phoenix Files\Technical Data\_NORMALIZED_REVIEW`

## Purpose

The catalog library is the `[VENDOR-DOC]` evidence lane for resolving the EP to ETAP master
cross-reference workbook at `reference/tcc/crosswalk/EP_to_ETAP_master_crossref.xlsx`.

Resolution flow:

1. Find a workbook row that is `frame`, `none`, or otherwise unverified.
2. Look up the relevant manufacturer/family in `CATALOG-INDEX.csv`.
3. Open the normalized catalog PDF from the synced review tree.
4. Confirm or correct the ETAP manufacturer/model/tier in the workbook.
5. Promote confirmed aliases to the live `tcc.*` alias tables in a separate governed lane.

## Taxonomy

Normalized review material is organized as:

```text
_NORMALIZED_REVIEW/
  Breakers/<CanonicalManufacturer>/<Family>/<doc>.pdf
  Trip Units/<CanonicalManufacturer>/<Family>/<doc>.pdf
  _quarantine/<source-origin>/<non-catalog-or-non-pdf-source-file>
```

The canonical manufacturer vocabulary follows the `Manufacturers` sheet in the EP to ETAP workbook.
When a real vendor is not represented by the workbook vocabulary, the manifest sets `not_in_workbook=Y`
so the vendor can be reviewed as a candidate for `tcc.mfr_aliases`.

## Sourcing Policy

Authoritative vendor catalogs and curve/selectivity books are preferred. The builder accepts web downloads
only when the response is a verified PDF: HTTP download plus `%PDF` magic bytes. Landing pages, HTML
responses, executables, archives, and scripts are rejected and recorded as gaps.

Local source material is copied from the existing synced library and staging pile, then deduped into the
normalized review tree. Originals remain untouched pending Phase 2 operator review.

## Dedupe Policy

Exact SHA-256 duplicates are dropped first. Remaining same-document candidates are grouped by recovered
document number/title identity. The canonical copy prefers official web sources when available, then the
existing synced library over staging-only copies.

`CATALOG-INDEX.csv` records `dup_of` only for kept rows when relevant. Full duplicate-drop details live in
the host-local audit workspace:

`C:\APEX Platform\apex-power-ops-platform\.audit_workspace\etap_tcc_sources\catalogs\duplicate_drops.csv`

## Manifest

`CATALOG-INDEX.csv` is bibliographic metadata only. It contains no copyrighted PDF body text and no binary
payloads. Each row points to a relative path under `_NORMALIZED_REVIEW`.

## Current State

Phase 2 curation on 2026-06-07 reclassified the remaining non-quarantine `Unknown` PDFs, filed the Fuji,
ITE, L&T, and Merlin Gerin long-tail staging sets, and deduped exact/superseded recoveries.

Current manifest:

- 206 rows
- 100 breaker rows
- 94 trip-unit rows
- 12 quarantine rows
- 0 non-quarantine `Unknown` rows
