# 031 TMT Contract-View Transition -- Design + Validation Contract

> Status: DESIGN (2026-06-28). Operator-ratified shape (VOCABULARY_MAP Decision 1 +
> the "028 diagnostic-view transition (031)" step, ratified 2026-06-27). PROD-BOUND,
> OPERATOR-GATED apply. F-79-02/04.

## Goal

After the D4/D5 data carry (029 + 030, applied to prod 2026-06-28), the live 028
contract view `tcc.vw_lvbreakertcc_tmt_frame_contract` still emits two now-stale
projection-hazard flags and carries a latent child-count Cartesian. 031 is a single
`CREATE OR REPLACE VIEW` that transitions the hazard surface and fixes the perf
defect, with no serving change and no `served` flag flips.

## The three changes (and nothing else)

1. **Drop** `d4_tmt_helper_columns_absent_from_projection`. 029 carried + populated the
   six `TMT_*` helper columns into `brk_iccb_styles` / `brk_mccb_styles`. The conditional
   flag (ICCB/MCCB only) is removed from `projection_hazards`.
2. **Relabel** `d5_inst_override_columns_absent_from_projection` ->
   `d5_inst_override_carried_reference_only`. 030 carried the inst-override / timing /
   rating block into `tcc.brk_style_native_overrides` as `native_bounded` REFERENCE.
   It is carried, not projected, NOT served -- the relabel says exactly that.
3. **Fix the `frame_counts` Cartesian** (Codex review-2dd99030 P2). 028 LEFT-JOINs
   `tmt_amps x tmt_settings x tmt_thermal_adj x tmt_curves` before `COUNT(DISTINCT ...)`.
   031 aggregates each child per-frame in its own CTE, then LEFT JOINs the per-frame
   counts onto `tmt_frames` with `COALESCE(...,0)`.

### Why change 3 is value-neutral (proof)

For each child table, `id` is a PK, so within a single `GROUP BY frame_id` aggregate
`count(*)` equals `count(DISTINCT id)`. The 028 Cartesian only needed `DISTINCT` to undo
its own row multiplication; removing the multiplication and counting once is identical.
A frame with no child rows yields `0` in both forms (028: `count(DISTINCT NULL)=0`; 031:
absent from the child CTE -> `COALESCE(NULL,0)=0`). `frame_counts` is still driven from
`tmt_frames` (every frame present). Therefore every count / boolean / posture / partition
column is byte-identical to 028; only `projection_hazards` changes.

## Fail-closed guard

Leading in-tx DO block RAISEs unless ALL of:
- `tcc.brk_style_native_overrides` exists (030 DDL), and is non-empty (030 data);
- `tmt_breaker_type` is non-null on at least one row of `brk_iccb_styles` **AND** at
  least one row of `brk_mccb_styles` (029 data, gated PER CLASS).

`tmt_breaker_type` (smallint enum 0/1) is the population sentinel; the text helper cols
can be empty-string non-null, so they are deliberately NOT used. The two classes are
gated independently (NOT summed): all d4-flagged frames are MCCB (ICCB has 0 tmt_frames),
so a summed check would let an ICCB-only carry mask a skipped MCCB recarry while 031
strips the flag from every MCCB frame -- requiring both classes witnessed closes that
fail-open (IRP guard-fail-closed Important, 2026-06-28). Trailing DO block re-asserts
`serving + hazards = total` (a real structural invariant); the d4/d5 survivor counts are
an authoring tripwire (they read the just-replaced view text), not the data gate.

## Grounded premises (verified against prod fxoyniqnrlkxfligbxmg, 2026-06-28)

- Live view def == the 028 migration file (no hand-patching).
- D4 populated: ICCB 608/608, MCCB 10236/10335 `tmt_breaker_type` non-null.
- D5: 14222 rows, 687 real overrides (`InstOvrAmps > 0`).
- 028 aggregates: `total=42069, serving=40125, hazards=1944, curveless=1923, orphans=0`.
- **Value-parity anchor:** `parity_hash_excl_hazards = 58cc15fe36e5dabf131e154e730c1833`
  (md5 over `frame_id|breaker_class|breaker_style_id|amp_count|setting_count|`
  `thermal_adjustment_count|curve_point_count|trip_class_count|is_curve_serving_candidate|`
  `serving_posture`, ordered by `frame_id`).

## Validation contract (dry-run must satisfy ALL)

Substrate: a fresh host clone off `tcc_breaker_baseline_20260625` with the real committed
chain applied (`028 -> 029 DDL -> 029 data -> 030 DDL -> 030 data`). **Gate:** the clone's
028 view MUST reproduce prod hash `58cc15fe...` + the aggregates before any 031 result is
trusted (proves the clone data == prod for view purposes; catches baseline drift).

1. **Guard negative:** with D4 nulled (in a rolled-back tx), 031's guard RAISEs the D4
   precondition. With the D5 side table emptied (rolled-back tx), it RAISES the D5
   precondition. (Proves the guard actually fences.)
2. **Apply clean:** 031 applies on the fully-carried clone; both DO blocks pass; COMMIT.
3. **Value-parity:** post-031 `parity_hash_excl_hazards` == `58cc15fe...` AND aggregates
   unchanged (`42069/40125/1944/1923/0`). (Proves the perf-fix is value-neutral.)
4. **Hazard transition exact:** post-031 `projection_hazards` distribution ==

   | n | projection_hazards |
   |---|---|
   | 20073 | `{missing_setting_options, missing_thermal_adjustment_rows, d5_inst_override_carried_reference_only}` |
   | 14538 | `{missing_thermal_adjustment_rows, d5_inst_override_carried_reference_only}` |
   | 5502 | `{d5_inst_override_carried_reference_only}` |
   | 1923 | `{missing_curve_points, missing_thermal_adjustment_rows, d5_inst_override_carried_reference_only}` |
   | 21 | `{missing_amp_options, missing_setting_options, missing_thermal_adjustment_rows, d5_inst_override_carried_reference_only}` |
   | 12 | `{missing_setting_options, d5_inst_override_carried_reference_only}` |

   (sum 42069; zero rows with either stale flag).
5. **Perf:** `EXPLAIN (ANALYZE, BUFFERS)` of the 031 `frame_counts` shows no Cartesian
   blow-up (no ~1.1M-row intermediate); 031 full-view runtime materially below 028's.
6. **Idempotency:** re-applying 031 is a clean no-op (CREATE OR REPLACE).
7. **Down restores 028:** `031_down` re-creates the 028 def; hash + the original 10-combo
   hazard distribution return; dependent views revert.

## Cross-engine + apply

- Mandatory IRP: Codex via apex-jobs `review-run --review-head tcc/031-... --base-ref main`
  + an adversarial Claude review pass (value-parity logic / guard completeness /
  perf-equivalence / down fidelity).
- Apply gate: 031 is pure DDL (no separate data step); it still gets its OWN explicit
  operator go. DDL via MCP `apply_migration` (omit the file's outer BEGIN/COMMIT; the
  runner wraps the tx; the fail-closed guard still aborts within it).

## Out of scope (fixed)

No serving change; no `served` flips (Decision 1). Dependent views not re-created (column
list unchanged). F-79-03 row-count anti-join stays PARKED. ASCII-only authored SQL.
