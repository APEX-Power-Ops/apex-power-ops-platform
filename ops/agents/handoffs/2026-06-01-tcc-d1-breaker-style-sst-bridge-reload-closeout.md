---
dispatch_id: 2026-06-01-cc-tcc-d1-breaker-style-sst-bridge-reload
closeout_of: ops/agents/inbox/done/2026-06-01-cc-tcc-d1-breaker-style-sst-bridge-reload.md
by: CC
date: 2026-06-01
status: CLOSED (Phases A–C) — verified live
result: PASS
---

# D1 — breaker→ETU SST bridge recovered (re-carry + orphan repoint + BG-4 surface)

**Outcome:** the SST-1 breaker→ETU bridge is recovered on governed Supabase. The 4 dropped
columns are re-carried source-faithfully on all 3 `tcc.brk_*_styles` tables, the 325 day-one
orphan MCCB styles are repointed (0 orphans), and the BG-4 bridge surface `tcc.vw_breaker_sst_bridge`
is live. Match-rates reproduce the Access live-join exactly. **Lean A executed (in-place, ids preserved).**

## The key unlock — `rank=id` (PROVEN, not assumed)
The Supabase style surrogate `id` == the position of the Access `Breaker*Styles` row ordered by
`ID` ascending (the original Access→localPG→Supabase load re-sequenced 1..N in source order).
Proven by: 18 head + 6 tail + 22 spread spot-matches (46/46, full range, frame **and** parent key)
+ per-class integrity md5s on every staged dataset. This is why a clean in-place re-carry was possible
without a stable `source_id`. **It is the documented provenance mapping** (id is the immutable PK).

## Why lean A (in-place), not a fresh reload
`apps/control-plane-api/services/neta/router.py` joins `s.id = f.breaker_style_id` and queries
`style_model.id == frame.breaker_style_id` — i.e. the style surrogate `id` is app-depended-upon as
`breaker_style_id`. A reload that renumbered ids would break the deployed router. So D1 **preserves
ids**: ADD columns, populate by `rank=id`, and UPDATE only `breaker_id` for the 325 orphans. No FK
references the style `id` (checked), and no view/matview depends on it (checked).

## What changed on prod (governed Supabase, project fxoy…)
- **Migration `d1_sst_bridge_add_cols_and_staging`** — ADD `source_id`(int) + `tmt_use_sst`(bool, default false)
  + `tmt_sst_{mfr,type,style}`(text) on the 3 style tables; create transient `tcc._stg_d1_*`.
- **Staging** loaded from Access (`_d1_loader/*.sql`, md5-verified): 431 distinct SST triples,
  5,412 `(style_id→triple_id)` assignments, 325 orphan `(style_id→twin 4-tuple)` rows.
- **Migration `d1_sst_bridge_recarry_and_orphan_repoint`** — the SST carry (3 UPDATEs) + the orphan
  repoint (frame-guarded, normalized) → migration-005 twins, with in-transaction assertions.
- **Migration `d1_breaker_sst_bridge_view`** — `CREATE VIEW tcc.vw_breaker_sst_bridge`.
- Staging dropped. Canonical repo artifact: `infra/database/migrations/tcc/006_brk_styles_sst_bridge.sql`
  + `_d1_loader/` (generator `gen_d1_sql.ps1`, the data `.sql`, `RUN_ORDER.md`).

## `tmt_use_sst` semantics (trust-but-verify correction)
Stored boolean = `(Access TMT_Use_SST <> 0)`: **mccb 1704 / iccb 515 / pcb 3193** true.
The packet's "1,680" was the `=1` count; live `TMT_Use_SST` is a dirty Int16 — **1680×1 + 2×2 +
22×255 (=-1 byte-wrapped True) + 725 NULL (→false) + 7906×0**. `<>0` (the engine's gate) = 1704.

## Verification (all live, 2026-06-01)
- Style counts unchanged: 10335 / 608 / 3279. **0 MCCB orphans** (was 325). FK now satisfied.
- `tmt_use_sst` true: 1704 / 515 / 3193 (asserts passed in-transaction).
- Orphan dry-run: 325/325 resolve to exactly 1 parent, 0 unresolved, frame-guard OK on all 325.
- Bridge match-rates (non-null triples) == Access live-join targets: **ICCB 100% (515/515) /
  MCCB 95.6% (1576/1649) / PCB 97.5% (2162/2218)**; residual = genuine catalog gaps.
- Worked example: **`T8V-1600` (ICCB, style 311) → ABB / PR332/P / ICCB-LSIG → trip_style 1230 → 5 sensors.**
  (MCCB sibling `T8-1600` → PR332/P / MCCB-LSIG → trip_style 1226 → 3 sensors.)
- Bridge totals: 4,253 breaker styles → 388 trip_styles → 2,922 sensors (68,155 style-sensor pairs).

## Guides updated (SSoT Law — fix-the-guide deliverable)
- **G1** dropped-column register **D1 → ✅ CLOSED**; new governed-load-delta bullet closing the 325-orphan styles.
- **G0 §3** status note → **RECOVERED** (+ the `vw_breaker_sst_bridge` surface name; UX still mfr-axis = Phase D).
- **G2** BG-4 → **MET**; BG-5 → **UNBLOCKED (Phase D)**; §4.3 governance → **RECOVERED**.

## Decisions / residuals (surfaced)
- **`source_id` bulk population DEFERRED.** Column added; population is the un-applied, ready
  `_d1_loader/d1_90_srcid_*.sql` (array UPDATE keyed by `rank=id`). `rank=id` is the proven provenance,
  so this is a low-value/high-cost-via-MCP-only-channel item — a one-step follow-up. Lean-A "minimal".
  *(No direct Postgres DSN exists locally — `control-plane-api/.env DATABASE_URL` points at a defunct local
  `tcc_v5`; Supabase writes go via the MCP/management API. The 5,412 SST + 325 orphan rows were loaded
  through the MCP with md5 integrity gates; 14k `source_id` ints weren't worth that channel for now.)*
- **`tmt_sst_mfr` kept as source-faithful NAME string** (not coerced to FK) — coercion was the original D1 bug.
- **D4** (`TMT_TCCNumber`/`TMT_Notes`/`TMT_TripPlug`/`TMT_BreakerType`/`TMT_ThermalMagnetic`/`TMT_Thermal`)
  is co-located on the same Access tables but was **NOT** re-carried — still OPEN (G1 D4). `source_id` makes
  any future D4/D5 re-carry a trivial id-join once populated.
- Bridge view is a plain view (small); materialize only if measured need (mirrors AG-3 "no invented targets").

## Next
- **Phase D (BG-5)** — operations-web UX to consume `vw_breaker_sst_bridge` (breaker-style → compatible
  sensors, beyond manufacturer-axis). Author as its own gated packet. Unblocks the field-tolerance MVP narrowing.
- Optional fast-follow: apply `source_id`; re-carry D4.
