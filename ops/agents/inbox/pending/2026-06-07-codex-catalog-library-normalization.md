# Codex Packet — Normalize the breaker / trip-unit catalog library (staging → canonical reference)

Lane: build the durable, on-going **catalog reference library** that feeds the EP→ETAP
catalog-resolution workbook (`reference/tcc/crosswalk/EP_to_ETAP_master_crossref.xlsx`). Turn the
messy staging pile + the existing (partly-organized) synced library into ONE normalized,
deduped, manufacturer-keyed tree + a committed metadata manifest.

**Non-destructive this pass.** Build the normalized library by COPY; do NOT move/rename/delete any
original. This is the operator's live synced (SharePoint/OneDrive) reference area — treat existing
content as read-only sources.

## Boundary / hygiene (READ FIRST — privacy is load-bearing here)
- **All absolute paths are in the host-local sidecar `.audit_workspace/catalog_lane/paths.local.txt`** (gitignored). Read `TECHDATA`, `SRC_LIB_BREAKERS`, `SRC_LIB_TRIPS`, `SRC_STAGING`, `NORMALIZED_ROOT` from it.
- **NEVER write the absolute synced path, the company name, or the office/site token into any committed file** (packet refs, manifest, closeout, commit messages). The synced area is private. In committed artifacts use only the placeholder `<TECHDATA>` and library-**relative** paths (e.g. `Breakers/Eaton/IZMX/<file>.pdf`).
- **Copyrighted vendor PDFs are NEVER committed** to the repo. Only the **metadata manifest** (vendor names / model / doc-number / title / relative-path — bibliographic, no copyrighted body text, no client/site/person identifiers) is committed.
- §146: page-1 metadata is read for **classification only** (names/identifiers); do not extract/republish curve content.
- Scoped `git add`; Git Bash heredoc for commit messages; trailer at end.

## Sources (all READ-ONLY this pass; counts from CC's scout)
1. `SRC_STAGING` — flat pile, **114 files** (~1.45 GB): 109 PDF + 2 PNG curve-crops + 2 TXT + 1 DXF. Naming chaos: Scribd-IDs (`443882807-Mpactplus-…`), vendor doc-codes (`GET-7002D.pdf`, `1SDC…`), opaque hashes (`1cb6dc.pdf`, `57fd14.pdf`, `3aaaef.pdf`, `764c3d.pdf`, `9d1cf3.pdf`, `f26bd6.pdf`, `4750d9.pdf`, `5912fb.pdf`, `63a682.pdf`, `6abe85.pdf`, `3vf93.pdf` …), and human names. NOTE: a stray non-catalog file `Good question — ETAP is exactly the.txt` (accidental chat save) → quarantine.
2. `SRC_LIB_BREAKERS` — **45 files**, existing mfr subfolders: `ABB · Eaton · Eaton Digitrip 520 · Magnum DS Brkr · Siemens · SQ-D Schneider` (+ 2 loose). Inconsistent: family-folders sit at the mfr level.
3. `SRC_LIB_TRIPS` — **57 files**, existing subfolders: `ABB · AC Pro · Allen Bradley · Eaton · GE · Siemens · Square D` + one mixed-mfr catch-all subfolder (+ loose calculators/screenshots/quick-refs). Naming differs from the breaker tree (`Square D` vs `SQ-D Schneider`).

## Canonical taxonomy to BUILD (under `NORMALIZED_ROOT`)
```
_NORMALIZED_REVIEW/
  Breakers/   <CanonicalManufacturer>/ <Family>/ <doc>.pdf
  Trip Units/ <CanonicalManufacturer>/ <Family>/ <doc>.pdf
  _quarantine/   (non-catalog: stray .txt, screenshots, pdftotext extracts, .dxf, calculators — copied here, NOT deleted)
```
- **`<CanonicalManufacturer>` MUST use the cross-ref workbook's `Manufacturers` sheet vocabulary** (`reference/tcc/crosswalk/EP_to_ETAP_master_crossref.xlsx`) — e.g. `General Electric`, `Eaton`, `Cutler-Hammer`, `ABB`, `Siemens`, `Schneider`, `Square-D`, `Westinghouse`, `LSIS`, `Terasaki`, `WEG`, `Allen-Bradley`. Map the existing inconsistent folder names → canonical: `SQ-D Schneider`/`Square D` → split by the actual brand on each doc (`Square-D` vs `Schneider`; ETAP keeps both); `Magnum DS Brkr` → `Eaton/Magnum`; `Eaton Digitrip 520` → trip-unit `Eaton/Digitrip 520`; the mixed-mfr catch-all subfolder → identify each file's real mfr and re-file. If a real manufacturer/family is **not** in the workbook vocab (e.g. `AC-PRO` = Utility Relay Co. retrofit trip), use the correct vendor name and flag `not_in_workbook=Y` in the manifest (candidate to add to `tcc.mfr_aliases`).
- **Device-class placement:** a doc that covers BOTH a breaker frame AND its trip unit (e.g. IZMX + PXR) → place the physical file under its PRIMARY subject (the breaker if it's a breaker catalog) and **cross-tag both model sets in the manifest** (do NOT duplicate big PDFs across Breakers/ and Trip Units/).
- **Canonical filename:** keep it human-readable + traceable — `<doc-number-or-slug>__<short-title>.pdf`; preserve the original name in the manifest. Resolve opaque hash-named files to a real name via page-1 metadata.

## Steps
1. **Inventory + identify** every file across the 3 sources (216 total). For opaque/hash/ID-named files, read page-1 text (`pdftotext -f 1 -l 2`, mingw64) to recover manufacturer / family / doc-number / title — **classification metadata only**.
2. **Dedupe** across all sources: exact dups by SHA-256; near-dups by recovered doc-identity (same doc-number/title, different filename). The staging pile very likely overlaps the existing synced library folders (e.g. Eaton Digitrip 520, NRX, M-Pact). Keep ONE canonical copy; record the dropped duplicates + which source won in the manifest.
3. **Classify** each kept doc: device_class (`Breaker` | `TripUnit` | `Both`), canonical_mfr, family, models_covered (breaker models + trip-unit models, using workbook vocab where possible), doc_type (`catalog` | `instruction-manual` | `curve-book` | `selectivity-table` | `brochure` | `order-code` | `tool`), doc_number, title.
4. **COPY** the deduped, classified catalog docs into `NORMALIZED_ROOT/{Breakers,Trip Units}/<Mfr>/<Family>/`. Non-catalog items → `_quarantine/`. **Originals untouched.**
5. **Manifest (committed)** at `reference/tcc/catalogs/`:
   - `CATALOG-INDEX.csv` — one row per kept doc: `device_class, canonical_mfr, family, models_covered, doc_type, doc_number, title, normalized_relpath, source (staging|lib-breakers|lib-trips), original_name, not_in_workbook, dup_of, notes`. **Relative paths only; no absolute/private paths.**
   - `README.md` — what the library is, the canonical taxonomy + mfr-vocab rule, the dedupe policy, how it ties to the resolution workbook (workbook row → manifest lookup → open catalog → resolve), and the regeneration/update note. Reference the synced root only as `<TECHDATA>` (point to the host-local sidecar for the concrete path).
   - Add a guide-map row in `reference/tcc/00-MASTER-INDEX.md`.
6. **Review lists** (in the closeout, names-only): files whose mfr/family was **low-confidence** (need a human glance), the **duplicate** decisions, the **quarantined** non-catalog items, and any **`not_in_workbook` manufacturers/families** (candidates to extend `tcc.mfr_aliases`).

## Self-checks (fail-closed)
- every source file is accounted for (placed | deduped-dropped | quarantined) — assert `placed + dropped + quarantined == 216`; list any unaccounted.
- no committed artifact contains the absolute `<TECHDATA>` path, the company name, or the site/office token (grep the manifest/README/closeout before commit).
- `CATALOG-INDEX.csv` row count == count of kept docs; every `normalized_relpath` exists under `NORMALIZED_ROOT`.

## Out of scope (this pass)
- Moving/renaming/deleting ANY original (Phase 2, after operator reviews `_NORMALIZED_REVIEW`).
- Filling the resolution workbook (separate lane). Curve extraction / parsing. Relay catalogs (breaker+trip only).
- Committing any PDF/binary.

## Deliverables + closeout
1. `NORMALIZED_ROOT/{Breakers,Trip Units,_quarantine}/…` built by copy (host/synced; not committed).
2. Committed: `reference/tcc/catalogs/CATALOG-INDEX.csv` + `README.md` + the `00-MASTER-INDEX.md` row.
3. Closeout `ops/agents/handoffs/2026-06-07-catalog-library-normalization-closeout.md`: per-source counts, total kept / deduped / quarantined, the canonical mfr list + doc counts per mfr, the review lists (low-confidence / dups / not-in-workbook), and a note that Phase 2 (retire originals + apply review fixes) awaits operator sign-off on `_NORMALIZED_REVIEW`. Then `git mv` this packet pending→done and push (`git status -sb` in-sync; admin bypass on main expected).

## Commit hygiene
Scoped `git add` (manifest + README + index + closeout + `git mv`); Git Bash heredoc; end every commit message with:
```
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```
