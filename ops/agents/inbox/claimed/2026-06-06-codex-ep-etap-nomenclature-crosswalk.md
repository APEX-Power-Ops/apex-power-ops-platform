---
dispatch_id: 2026-06-06-codex-ep-etap-nomenclature-crosswalk
target: CODEX
priority: 1
from: CC
created_at: 2026-06-06
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-06-06-ep-etap-nomenclature-crosswalk-closeout.md
---

# EP→ETAP nomenclature crosswalk (mfr + breaker + trip-unit) — build artifact

**Lane:** lvbreakertcc · nomenclature normalization (NEW sub-lane).
**Type:** READ-ONLY build. Prod read + host-local file read. **No DB writes. No DDL. No code wiring. No committing bulk ETAP data.** Deliverable = three host-local crosswalk TSVs + a method doc + an aggregate stats closeout. **Persistence (populating alias tables) and serving wire-up are SEPARATE follow-on packets CC authors after reviewing your output.**
**Must run on the WORKSTATION** — the ETAP source files are host-local and gitignored (see Sources).

## Why
The `lvbreakertcc` UI currently shows raw EasyPower (EP) nomenclature (e.g. mfr `West`, `GE`, `Merlin Gerin`; cryptic trip/frame names). We want to surface the recognizable **ETAP-equivalent** names. The ETAP device-library taxonomy (LibChanges 2024-118 + DemoLib) is now extracted to host-local TSVs, giving us ground-truth ETAP manufacturer/model/family strings. Build the EP↔ETAP crosswalk at three levels (manufacturer, trip-unit, breaker) so CC can (separately) populate alias tables and wire the serving layer.

## CRITICAL REFRAMING (use as your baseline — validate against the data, do NOT blindly re-derive)
CC already characterized the ETAP manufacturer vocabulary. **Key finding: ETAP deliberately PRESERVES legacy brands as distinct manufacturers** — it carries *both* `Cutler-Hammer` AND `Eaton`, *both* `Merlin Gerin` AND `Schneider Electric`, plus `Westinghouse`, `ITE`, `Allis-Chalmers`, `Siemens-Allis` as their own entries. So normalization is **string-alignment to ETAP's exact naming**, NOT brand-modernization. Do **not** collapse Cutler-Hammer→Eaton or Merlin Gerin→Schneider.

The complete ETAP manufacturer vocabulary observed across `lv_breaker_all_rows.tsv` + `trip_device_all_rows.tsv` (excluding `A Demo *` placeholders) is exactly:
`ABB`, `AEG`, `Allis-Chalmers`, `Cutler-Hammer`, `Eaton`, `Federal Pioneer`, `General Electric`, `ITE`, `K Moeller`, `L&T`, `Merlin Gerin`, `Mitsubishi`, `Schneider Electric`, `Siemens`, `Siemens-Allis`, `Square D` / `Square-D` (ETAP itself uses both spellings; `Square-D` dominates ~817 vs 77), `Westinghouse`.

CC's manufacturer normalization map to validate + apply (these are the only non-identity mappings; everything else is exact-match or no-match):

| EP `mfr_name` | → ETAP `manufacturer` | tier |
|---|---|---|
| GE | General Electric | expand |
| West | Westinghouse | expand |
| Schneider | Schneider Electric | expand |
| Moeller | K Moeller | prefix |
| Larsen & Toubro | L&T | contract |
| Square D | Square-D | punctuation |
| Allen-Bradley | ABB | rebrand (per §163 AB=ABB rebrand finding) |

All other EP mfrs that exactly match an ETAP name (case-insensitive) → tier `identity` (Siemens, Cutler-Hammer, Eaton, ABB, Merlin Gerin, Federal Pioneer, Mitsubishi, ITE, Allis-Chalmers, Siemens-Allis). EP mfrs with NO ETAP entry (Terasaki, bticino, OEZ, Fuji, Sensitr, Utility Relay, Federal Pacific, SACE, BBC, Changshu, Unelec, Sylvania, LS Industrial, and the rest of the long tail) → tier `none`, **leave EP name as-is** (ETAP simply does not carry them — do not invent a mapping).

## §146 SOURCE DISCIPLINE (the boundary is about what you SOURCE FROM, not what you may look at)
The crosswalk's **source** is the ETAP taxonomy/naming layer — the manufacturer/model/family/hierarchy columns: manufacturer, model, function, curve, extra_1, standard, acdc, breaker_class, pole, amp_or_size, trip_family, amp_or_setting, selector_key, is_leaf, live_example_seen, dll_validated_path. Names/identifiers are a legitimate source for a nomenclature crosswalk.
- The **decoded curve/payload data** (curve points, equations, pickup/delay bands, numeric previews, payload bytes/sha256 — i.e. `backend_decoded_*`, `*_decoded.tsv`, `*.dec.bin`, `decoded_*`) is **not a source for use** here: it does not feed the crosswalk, is never persisted as product curve data, and is never cited as a curve/setting authority. Authority for curve numbers stays with public catalogs / the governed DLL. It's fine to glance at for corroboration if ever useful — it's just not the source, and a names crosswalk draws nothing from it.
- The crosswalk OUTPUT carries **names / identifiers / hierarchy strings only** — no curve point, equation, band, numeric value, or payload — because that's what a nomenclature crosswalk *is*, not because the files are off-limits.
- Provenance tag for every output row: `[ETAP-TAXONOMY 2024-118] names-only crosswalk`. ETAP taxonomy names are a fine source for the crosswalk; whether to PERSIST ETAP-sourced names into prod alias tables (vs the public-catalog provenance currently on `trip_style_aliases`) is a CC/operator call in the follow-on — tag honestly so the source is auditable.

## Sources
**EP side — prod Supabase, READ-ONLY** (same access the `2026-06-03-codex-i2x6-prod-band-population-check` dispatch used):
- `tcc.manufacturers` (id, mfr_name)
- `tcc.trip_styles` (id, mfg_id, type, style, sensor_name, sensor_type, tcc_no, notes)
- `tcc.brk_mccb_styles`, `tcc.brk_iccb_styles`, `tcc.brk_pcb_styles` (frame, r_cont_current, standard, voltage_id, tmt_sst_mfr/type/style, breaker_id)
- Reference only (for agreement-check, do not mutate): `tcc.trip_style_aliases` (803 rows: trip_style_id, alias_name, alias_mfr, match_tier, match_basis, n_candidates, provenance).

**ETAP side — host-local, GITIGNORED, workstation only** (`.audit_workspace/etap_tcc_sources/family_tables/`):
- `lv_breaker_all_rows.tsv` (13,896 rows) — breaker level
- `trip_device_all_rows.tsv` (6,213 rows) — trip-unit level
- `family_table_manifest.tsv` — per-family counts (context)

Prerequisite (check before claim): prod read reachable + the three TSVs present on this host. If either is missing, leave in `pending/` and report.

## Method — three levels

### LEVEL 1 — Manufacturer crosswalk → `crosswalk/mfr_crosswalk.tsv`
- Pull distinct EP `mfr_name` that are actually used (appear in `trip_styles` OR any `brk_*_styles`).
- Apply CC's map above; exact-match (case-insensitive) the remainder; tier `none` for no-match (etap name null, leave as-is).
- Columns: `ep_mfr_id, ep_mfr_name, etap_mfr_name, tier, match_basis, ep_trip_style_count, ep_breaker_style_count, provenance`.
- One row per EP mfr. Also report any ETAP mfr with NO EP counterpart (e.g. `AEG`) as informational.

### LEVEL 2 — Trip-unit crosswalk → `crosswalk/trip_unit_crosswalk.tsv`
- For each EP `trip_styles` row, restrict ETAP `trip_device` rows to the Level-1-crosswalked manufacturer.
- Match EP `(type, style)` against ETAP `(model, function, curve, trip_family)`. Document a deterministic core-token normalization (strip `[IEC]`/`[UL]` and similar standard suffixes, collapse whitespace, casefold) BEFORE comparing. Tiers, mirroring the existing `trip_style_aliases` vocabulary:
  - `exact` — model + function/std + functional class all match
  - `core` — model-core matches; variant/frame/standard suffix differs
  - `frame` — only frame/family-level match
  - `none` — no ETAP match (leave as-is)
- For trip_styles already in `tcc.trip_style_aliases`, set `agrees_with_existing_alias` = yes/no/na (does your ETAP-taxonomy match agree with the prior public-catalog alias name?). **Flag conflicts explicitly** — those are the highest-value review rows.
- Columns: `trip_style_id, ep_mfr, ep_type, ep_style, etap_mfr, etap_model, etap_function, etap_curve, tier, match_basis, n_candidates, alt_candidates, agrees_with_existing_alias, provenance`.

### LEVEL 3 — Breaker crosswalk → `crosswalk/breaker_crosswalk.tsv`
- For each EP `brk_*_styles` row, restrict ETAP `lv_breaker` rows to: Level-1-crosswalked manufacturer **AND** matching `standard` (ANSI/IEC) **AND** `breaker_class` (Molded Case / Insulated Case / Power CB — map EP class MCCB/ICCB/PCB accordingly) **AND** `acdc` where determinable.
- Match EP `frame` against ETAP `model` + `amp_or_size`; EP `r_cont_current` against ETAP `amp_or_size` as a corroborator. Tiers: `exact` (model + amp), `core` (model match), `frame`, `none`.
- Columns: `breaker_class, breaker_style_id, ep_mfr, ep_frame, ep_r_cont_current, etap_mfr, etap_model, etap_amp_or_size, tier, match_basis, n_candidates, alt_candidates, provenance`.

### Determinism / no-fabrication rules
- **Never invent an ETAP name.** `none` tier when no match; leave EP as-is.
- One row per EP entity; if multiple ETAP candidates, keep the single best, set `n_candidates`, list the others in `alt_candidates`.
- Write `crosswalk/crosswalk_method.md` documenting the EXACT normalization/tokenization + tier rules you used (so CC can reproduce + the follow-on persistence is auditable).

## Output (host-local, gitignored)
Write all four files under `.audit_workspace/etap_tcc_sources/crosswalk/`:
`mfr_crosswalk.tsv`, `trip_unit_crosswalk.tsv`, `breaker_crosswalk.tsv`, `crosswalk_method.md`.

## Closeout (committed) — AGGREGATE ONLY
At `ops/agents/handoffs/2026-06-06-ep-etap-nomenclature-crosswalk-closeout.md`, report:
- **Level 1:** count by tier; the full ~62-row mfr map (names only — OK to include, public facts); any ETAP-only mfrs (e.g. AEG).
- **Level 2:** trip_style coverage by tier (counts + %); count of agreements vs conflicts against existing `trip_style_aliases`; 5–10 illustrative sample rows; the conflict list.
- **Level 3:** breaker-style coverage by tier, per class (MCCB/ICCB/PCB); 5–10 samples.
- **Anomalies:** ETAP `Square D`/`Square-D` split; EP mfrs absent from ETAP; ETAP mfrs absent from EP; any EP entity matching multiple ETAP candidates suspiciously.
- One-line **verdict** on overall coverage per level.
- **NO bulk row dump, NO curve/payload data, NO secrets** (no DSN/token/project-ref/client/job/site identifiers).

## Boundaries
- READ-ONLY on prod. No writes/DDL/code. Host-local file READ only; outputs to gitignored `.audit_workspace/.../crosswalk/`.
- §146 source discipline (above) — crosswalk is sourced from the taxonomy/naming layer; decoded curve/payload data is not a source for use (not persisted as product data, not cited as curve authority).
- PUBLIC repo + no secrets in the closeout/chat (aggregate + names only).
- Inbox lifecycle: `git mv pending→claimed` + push before running; closeout to the `closeout:` path; then `git mv claimed→done` + push.

## Acceptance
The three crosswalk TSVs + `crosswalk_method.md` exist host-local; the closeout carries per-level tier coverage + samples + the alias-conflict list + anomalies + verdict. CC reviews, then authors the follow-on prod-write packet (populate a mfr-alias table, extend `trip_style_aliases`, add a breaker-style alias table) and the serving-layer wire-up.
