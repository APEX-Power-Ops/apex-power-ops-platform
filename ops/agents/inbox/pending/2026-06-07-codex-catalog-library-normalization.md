# Codex Packet — Build the breaker / trip-unit catalog reference library (web-sourced + local seed)

Lane: build the durable, on-going **catalog reference library** that feeds the EP→ETAP
catalog-resolution workbook (`reference/tcc/crosswalk/EP_to_ETAP_master_crossref.xlsx`) and is the
foundation of Apex Power's "central hub for NETA references."

**Primary source = the web (authoritative vendor catalogs).** The vendors' own current published
catalogs / curve-books are the [VENDOR-DOC]-grade material we want. Web-source them per manufacturer
× family, and **fold in the local pile as a supplement** (it has real value for legacy/obscure docs
the web won't surface — e.g. Westinghouse static-trip, GE Power-Break `GET-7002D`, the M-Pact Plus
catalog). One canonical, deduped tree + a committed metadata manifest is the deliverable.

Operator has **explicitly authorized web-sourcing + downloading** for this lane. Build is
**non-destructive** — copy/download into a fresh canonical tree; leave the existing folders' originals
in place (they're just renameable staging titles).

## Boundary / hygiene
- **Downloads — official vendor domains PREFERRED, reputable secondary sources PERMITTED** (operator
  widened scope). Tier-1 = official (`eaton.com`, `se.com`/`schneider-electric.com`,
  `new.abb.com`/`library.abb.com`, `siemens.com`, `gevernova.com`/legacy GE, `lsis.com`/`ls-electric.com`,
  `terasaki.*`, `weg.net`, `rockwellautomation.com`, …). Tier-2 = reputable secondary (authorized
  distributors, IEEE/standards bodies, established engineering-document repositories) when no official copy
  is available. **Hard safety floor (non-negotiable):** every download MUST be a **verified PDF** (HTTP
  content-type + `%PDF` magic bytes); **never download or execute an executable/archive/script**
  (`.exe/.msi/.zip/.scr/.js/.html`-as-doc/etc.); skip any site flagged unsafe. Record the provenance tier
  per doc (Tier-1 official vs Tier-2 secondary) so authority is traceable.
- **Copyrighted PDFs are NEVER committed** to the repo — they live in the synced library only. Only the
  **metadata manifest** (vendor / model / doc-number / title / relative-path / source-URL — bibliographic,
  no copyrighted body text) is committed.
- Scoped `git add`; Git Bash heredoc for commit messages; trailer at end.

## Paths (real; operator confirmed these titles are non-sensitive + renameable)
- Existing synced library root: `C:\Users\jjswe\Resa Power, LLC\RESA Power Ops - Phoenix Files\Technical Data`
  - `…\Breaker Manuals & TCC\` (45 files, mfr-keyed-but-inconsistent — READ-ONLY source)
  - `…\Trip Units\` (57 files, mfr-keyed-but-inconsistent — READ-ONLY source)
- Messy staging pile (READ-ONLY source): `D:\Circuit Breaker Technical Data\` (114 files, ~1.45 GB)
- **CREATE** the canonical tree under: `…\Technical Data\_NORMALIZED_REVIEW\` (operator reviews, then we promote it to replace the loose folders in Phase 2).

## Canonical taxonomy
```
_NORMALIZED_REVIEW/
  Breakers/   <CanonicalManufacturer>/ <Family>/ <doc>.pdf
  Trip Units/ <CanonicalManufacturer>/ <Family>/ <doc>.pdf
  _quarantine/   (non-catalog: stray .txt, screenshots, pdftotext extracts, .dxf, the loose calculators — copied, NOT deleted)
```
- **`<CanonicalManufacturer>` MUST use the cross-ref workbook's `Manufacturers` sheet vocabulary**
  (`reference/tcc/crosswalk/EP_to_ETAP_master_crossref.xlsx`) — `General Electric`, `Eaton`,
  `Cutler-Hammer`, `ABB`, `Siemens`, `Schneider`, `Square-D`, `Westinghouse`, `LSIS`, `Terasaki`,
  `WEG`, `Allen-Bradley`, … Map the existing inconsistent folders → canonical (`Magnum DS Brkr`→`Eaton/Magnum`;
  `SQ-D Schneider`/`Square D` → split by the actual brand on each doc; `Eaton Digitrip 520` → trip-unit
  `Eaton/Digitrip 520`; the mixed-mfr catch-all → identify each file's real mfr and re-file). If a real
  vendor/family is **not** in the workbook vocab (e.g. `AC-PRO` = Utility Relay Co. retrofit trip), use the
  correct vendor name + flag `not_in_workbook=Y` (candidate to add to `tcc.mfr_aliases`).
- A doc covering BOTH a breaker frame AND its trip unit → place once under its PRIMARY subject and
  **cross-tag both model sets in the manifest** (never duplicate big PDFs across Breakers/ and Trip Units/).

## Steps
1. **Local inventory + identify** all 216 local files. For opaque/hash/ID-named PDFs, read page-1 text
   (`pdftotext -f 1 -l 2`, mingw64) for manufacturer / family / doc-number / title — classification only.
2. **Web-source (primary) — COMPREHENSIVE across EVERY manufacturer in the workbook.** Pull the workbook
   `Breakers`/`Trips` sheets and enumerate **all** canonical manufacturers (rank by unmapped `none`/`frame`
   row count only to ORDER the work — do **not** limit to the top). For each manufacturer × principal LV
   breaker + trip-unit family, web-search for the CURRENT authoritative catalog + its curve/TCC/selectivity
   book and download it (Tier-1 official first, Tier-2 secondary fallback per the policy above). Per target,
   ONE authoritative catalog + ONE curve/selectivity book suffices — don't chase every revision / language /
   minor variant, but DO attempt every manufacturer and every principal family. Record what was sourced
   (with provenance tier) + every gap not filled.
3. **Dedupe** across local + web by SHA-256 (exact) and recovered doc-identity (same doc-number/title).
   Prefer the **official-vendor / newest-edition** copy as canonical; keep legacy-only docs from the local
   pile. Record dropped duplicates + which source won.
4. **Classify + place** every kept doc into `Breakers|Trip Units / <Mfr>/<Family>/`; non-catalog → `_quarantine/`.
5. **Manifest (committed)** at `reference/tcc/catalogs/`:
   - `CATALOG-INDEX.csv` — one row/doc: `device_class, canonical_mfr, family, models_covered, doc_type
     (catalog|instruction-manual|curve-book|selectivity-table|brochure|order-code|tool), doc_number, title,
     normalized_relpath, provenance_type (web-official|web-secondary|local), source_url, retrieved
     (YYYY-MM-DD or blank), source_origin (web|staging|lib-breakers|lib-trips), original_name,
     not_in_workbook, dup_of, notes`.
   - `README.md` — the library's purpose, the canonical taxonomy + workbook-vocab rule, the official-domain
     sourcing policy, the dedupe policy, and how it ties to the resolution workbook (workbook row → manifest
     lookup → open catalog → resolve confirmed/corrected → CC promotes to live alias tables).
   - Add a guide-map row in `reference/tcc/00-MASTER-INDEX.md`.
6. **Coverage + review report** (closeout): per-canonical-manufacturer doc counts (web vs local); the
   workbook-gap coverage delta (how many `none`/`frame` rows now have a catalog available); the web-sourced
   list (mfr/family/edition/URL); remaining gaps; low-confidence classifications; duplicates; quarantined
   items; `not_in_workbook` vendors (candidates to extend `tcc.mfr_aliases`).

## Self-checks (fail-closed)
- every LOCAL source file is accounted for (placed | deduped-dropped | quarantined) — assert
  `placed_local + dropped + quarantined == 216`; list any unaccounted.
- every web download is a **valid PDF** (`%PDF` magic bytes — reject + log anything that isn't; never an
  executable/archive); each `source_url` recorded with its provenance tier (Tier-1 official vs Tier-2 secondary).
- `CATALOG-INDEX.csv` row count == kept docs; every `normalized_relpath` exists under `_NORMALIZED_REVIEW`.
- no committed artifact contains copyrighted body text or any PDF/binary.

## Out of scope (this pass)
- Moving/renaming/deleting ANY original (Phase 2, after operator reviews `_NORMALIZED_REVIEW`).
- Filling the resolution workbook itself (separate lane — this builds the source material for it).
- Curve extraction/parsing. Relay catalogs (breaker + trip-unit only). Every minor revision / language
  variant (one authoritative catalog + curve book per manufacturer × family suffices).

## Deliverables + closeout
1. `_NORMALIZED_REVIEW/{Breakers,Trip Units,_quarantine}/…` built by copy/download (synced; not committed).
2. Committed: `reference/tcc/catalogs/CATALOG-INDEX.csv` + `README.md` + the `00-MASTER-INDEX.md` row.
3. Closeout `ops/agents/handoffs/2026-06-07-catalog-library-normalization-closeout.md` (the coverage + review
   report above; note Phase 2 awaits operator sign-off on `_NORMALIZED_REVIEW`). Then `git mv` this packet
   pending→done and push (`git status -sb` in-sync; admin bypass on main expected).

## Commit hygiene
Scoped `git add` (manifest + README + index + closeout + `git mv`); Git Bash heredoc; end every commit with:
```
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```
