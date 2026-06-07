# Codex Packet — Master EP→ETAP cross-reference workbook (.xlsx) + catalog-resolution scaffold

Lane: lvbreakertcc EP→ETAP nomenclature normalization → **reference-hub foundation.**
Operator directive (verbatim intent): *"make the master cross reference table xlsx showing EP → ETAP; we work
through resolving them against actual mfr reference manuals/catalogs … Apex Power's goal is to be the central hub
for NETA related references. Start building that out and use them to validate what we have, top to bottom,
end-to-end."*

This SUPERSEDES the earlier "surface frame-tier as suggested" idea. Frame-tier ETAP picks are low-confidence
guesses (token+amp-number overlap, e.g. GE ICCB `Hi-Brk-2500A`→`EGG-H/2500-3000`, n=24 candidates). Rather than
ship guesses into a field-trust-gated tool, we build a **durable worklist**: every EP device → its v2 ETAP
candidate + confidence + current live display + an empty resolution scaffold to be filled from manufacturer
catalogs ([VENDOR-DOC] discipline). The workbook is the artifact; humans resolve rows against catalogs over time.

**No prod write in this packet** (CC owns governed writes). Prod **READ-only** is fine and required (live-display join).

## Boundary / hygiene (read first)
- PUBLIC repo. NO secrets/client/job/site/person identifiers. Mfr/model names + ids are library taxonomy — fine.
- §146 source discipline: names only, from the **published ETAP Star Library help docs** (already parsed into the
  v2 TSVs) and, later, from manufacturer catalogs cited by humans. Do **not** persist/cite decoded ETAP curve data.
- Output workbook is host-local (see below) — do **NOT** commit the .xlsx binary. Scoped `git add` for the closeout
  + the one migration RECORD only. Git Bash heredoc for commit messages; trailer at end.

## Step 0 — regenerate the crosswalk (picks up CC's generator fix)
CC fixed a family-inference bug in
`.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/build_v2_starlib_crosswalk.py`:
`infer_trip_family` no longer routes **"static trip"** to EMT (static = solid-state → ETU), and the `la/od`
legacy cues are now `\b`-anchored so "VersaTrip **MOD2**" no longer false-hits `od2`→EMT.
- Re-run it: `uv run --with psycopg2-binary python build_v2_starlib_crosswalk.py` (it reads the Supabase DSN from
  the local `.env` itself — never echo it; reads the Star Library help dir on D:). This rewrites
  `mfr_crosswalk.tsv`, `trip_unit_crosswalk.tsv`, `breaker_crosswalk.tsv` + method/closeout md.
- **Validate the fix took:** the trip family-assignment count for EMT should DROP from the prior `{EMT: 52}` and
  the Static-Trip-II/III + VersaTrip MOD2 rows should now show `etap_family_page=LVSST.htm` with exact/core matches
  (e.g. Siemens `Static Trip II` → exact `Static Trip II`; GE `VersaTrip MOD2` → exact `VersaTrip(MOD2)`;
  Multilin `Static Trip Rel FB600` → exact `FB600`). Report the before/after family counts in the closeout.

## Step 1 — build the workbook
New host-local generator `…/v2_starlib/build_master_crossref_xlsx.py`
(`uv run --with openpyxl --with psycopg2-binary python build_master_crossref_xlsx.py`).
Output: `…/v2_starlib/EP_to_ETAP_master_crossref.xlsx`.

Sheets:
1. **README** — purpose; provenance (`[ETAP Star Library List - published help docs] names-only crosswalk`);
   the tier/confidence legend; the column dictionary; the resolution workflow (each row gets resolved against a
   manufacturer catalog → fill the resolution columns → CC promotes confirmed rows into the live alias tables);
   generated-on date (pass via a constant, NOT `datetime.now()` if you want reproducibility — a fixed string is fine).
2. **Summary** — counts by axis × tier (and × breaker class); coverage % ; shipped-vs-unshipped; resolution-status
   rollup (all `unverified` at first). Small, human-readable.
3. **Manufacturers** — from `mfr_crosswalk.tsv`.
4. **Trips** — from `trip_unit_crosswalk.tsv` (all ETU/TMT/MCP/EMT trip styles, ~2095).
5. **Breakers** — from `breaker_crosswalk.tsv` (all MCCB/ICCB/PCB styles, ~14k).

Per data-sheet columns = source columns + these enrichments:
- **Live shipped state** (query prod READ-only, replicate the serving COALESCE exactly):
  - Trips: `current_display = COALESCE(trip_style_aliases(exact/core, 1), trip_model_aliases.etap_model, ts.type)`;
    `display_source ∈ {overlay, v2_model_alias, ep_raw}`; `is_shipped_alias` bool.
  - Breakers: `current_display = COALESCE(breaker_style_aliases(exact/core join on (class,style_id)).etap_model,
    brk_<class>_styles.frame)`; `display_source ∈ {alias, ep_raw}`; `is_shipped_alias` bool.
  - Mfr: `current_display = COALESCE(mfr_aliases.etap_mfr_name, m.mfr_name)`.
- **Resolution scaffold** (empty, for humans):
  `resolution_status` (data-validation dropdown:
  `unverified | confirmed | corrected | no_etap_equiv | superseded | needs_catalog`),
  `catalog_source`, `resolved_etap_mfr`, `resolved_etap_model`, `resolved_tier`, `reviewer`, `review_date`, `notes`.

Formatting: freeze header row; autofilter on every data sheet; conditional fill by `tier`
(exact=green, core=blue, frame=amber, none=grey); column widths; wrap long text (`alt_candidates`, `match_basis`,
`notes`). **Sort each data sheet by `breaker_class`(breakers) / family, then `etap_mfr`(or ep_mfr), then tier-rank
(exact<core<frame<none), then model** — so a reviewer can work one manufacturer's catalog top-to-bottom.

Self-checks (fail-closed, raise on mismatch — this is the rigor in place of full TDD for a report generator):
- assert each data sheet's data-row count == its source TSV row count (minus header);
- assert no `current_display` is null/empty;
- after writing, re-open the workbook with openpyxl and assert sheet names + the Trips/Breakers row counts.

## Step 2 — record the (c) migration in the repo ledger (parity with b1/b2)
CC already applied to prod (migration `tcc_trip_model_aliases_solidstate_fix_seed`): +10 additive
`tcc.trip_model_aliases` rows (GE VersaTrip MOD2 style_ids 39,40,41,42,43,44,45,2444 → `VersaTrip(MOD2)` exact;
Multilin 140 → `FB600` exact, 141 → `FB600` core). Add a repo RECORD
`infra/database/migrations/tcc/016_tcc_trip_model_aliases_solidstate_fix.sql` (+ a `_down` that deletes those 10
ids) capturing the applied INSERT verbatim, **marked already-applied to prod (do NOT re-run).**

## Out of scope
- Any prod DDL/data change (CC owns alias tables + seeds). Serving code / frontend changes (none this packet).
- Filling the resolution columns (that's the human catalog-validation lane this workbook enables).
- Relay axis (separate lane) — trips/breakers/mfr only.

## Deliverables + closeout
1. Regenerated TSVs (host-local) with the before/after trip family-count delta reported.
2. `EP_to_ETAP_master_crossref.xlsx` (host-local) + `build_master_crossref_xlsx.py` (host-local).
3. The `016_…` migration record committed.
4. Closeout `ops/agents/handoffs/2026-06-07-master-ep-etap-crossref-xlsx-closeout.md`: the workbook path; per-sheet
   row counts; tier distribution per axis; shipped-vs-unshipped counts; the EMT→ETU family-count delta from the
   fix; and a note flagging that the operator should pick the workbook's durable home (Box reference / repo
   `reference/tcc/crosswalk/`) once a first manufacturer pass is validated. Then `git mv` this packet pending→done
   and push (`git status -sb` in-sync; admin bypass on main is expected).

## Commit hygiene
Scoped `git add` (the `016_*.sql`, the closeout, the `git mv`); Git Bash heredoc; end every commit message with:
```
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```
