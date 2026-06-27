# 028 F-79-02 - prod apply transcript (evidence)

- **Migration:** `028_lvbreakertcc_tmt_serving_contract_views.sql` (#79 F-79-02)
- **Objects:** three additive diagnostic views in `tcc.*`:
  - `tcc.vw_lvbreakertcc_tmt_frame_contract` (base: class-keyed frame contract + curve-serving posture + projection hazards)
  - `tcc.vw_lvbreakertcc_tmt_serving_frames` (is_curve_serving_candidate)
  - `tcc.vw_lvbreakertcc_tmt_projection_hazards` (NOT is_curve_serving_candidate)
- **Target:** governed Supabase prod `fxoyniqnrlkxfligbxmg` (apex-power-ops, PG 17.6)
- **Method:** MCP `apply_migration`, name `f79_02_lvbreakertcc_tmt_serving_contract_views`
- **Date:** 2026-06-27
- **Authorization:** operator explicit "28 tcc proceed" (028 only)
- **Source ref:** apex-tcc79 @ ee66f8a2 (lane lvbreaker/tcc-79-contract-fixes); functional SQL verbatim, descriptive header reduced to an ASCII pointer, no logic change.

## Preflight (read-only, pre-apply)
- `tcc.tmt_frames` count = **42069**
- existing target views = **0** (clean create, not a re-apply)
- dependency objects present = **11/11** (brk_{mccb,iccb,pcb}_styles, brk_{mccb,iccb,pcb}, manufacturers, tmt_{amps,settings,thermal_adj,curves})

## Apply
- `apply_migration` -> `{"success": true}` (in-transaction partition invariant passed; it would have aborted otherwise)

## Post-checks (read-only, post-apply)
| field | value |
|---|---|
| views_present | 3 |
| total (frame_contract) | 42069 |
| serving (serving_frames) | 40125 |
| hazards (projection_hazards) | 1944 |
| curveless | 1923 |
| orphans (no style parent) | 0 |
| partition_ok (serving + hazards = total) | true |
| total_matches_frame_count (= 42069) | true |

## Assessment
- Structurally valid; additive only (3 views, no data change, no existing object altered).
- LIVE prod counts (42069 / 40125 / 1944 / 1923 / 0) match the sandbox self-check snapshot exactly -> no prod/sandbox divergence for this contract; the orphan-warning branch did not fire (0 orphans, as in sandbox).
- The d4_/d5_ projection-hazard strings now surface in `vw_lvbreakertcc_tmt_projection_hazards` as labels only; their resolution is F-79-04 (Access authority).
- Reversible via `028_lvbreakertcc_tmt_serving_contract_views_down.sql` (drops the three views).

## Scope discipline
- Nothing reads these views yet, so creating them does not change what lvbreakertcc serves; wiring serving to them is a separate calc-engine ruling.
- F-79-03 / F-79-04 remain parked as NEEDS ACCESS EVIDENCE (triangulation / Access authority); untouched by this apply.
- Lane NOT merged to main (operator-gated).
