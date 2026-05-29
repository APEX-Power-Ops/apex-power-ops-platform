# ETU INST Tolerance Divergence Characterization And Reconciliation - Closeout

Date: 2026-05-29
Status: PASS for characterization and no-live reconciliation design; live cutover deferred pending operator authorization
Purpose: Record the bounded characterization and parity-surface reconciliation design for the remaining ETU evaluate-side INST warning on live-derived sensor `17892`

---

## 1. Branch Decision

This packet closes under branch `3(a)`.

Decision:

- the route-owned `±15%` INST band for sensor `17892` is the correct normal-mode contract
- the remaining divergence is a stale SQL helper issue in `fn_evaluate_test_results`
- no route edit is required or allowed for this packet

Why this branch is correct:

- live ETU context for sensor `17892` exposes `inst_tol_lo = -15.0` and `inst_tol_hi = 15.0`
- the same live context exposes `inst_ovrtol_min/max = NULL`, so the helper's `±10%` result was a fallback, not a sourced family rule
- live `fn_calculate_test_currents` already reads `ctx.inst_tol_lo/hi` and returns `INST.limit_low/high = 127.5 / 172.5`
- `apps/control-plane-api/services/calc_engine/NETA_TEST_PLAN_SPEC.md` says INST pickup tolerance must use the per-sensor `inst_tol_lo/hi` values and must not assume `±10%`
- `apps/control-plane-api/migrations/full_access_import.py` maps `DS4_TOL_LOW/HIGH` to `inst_tol_lo/hi` and maps `DS4_OVRTOL_MIN/MAX` separately, proving those are distinct concepts in the import lineage

The stale helper was therefore using the override-only band as if it were the normal-mode band.

---

## 2. Bounded Changes

Files changed:

- `apps/control-plane-api/supabase/migrations/20260528_000011_reapply_etu_evaluate_function.sql`
- `apps/control-plane-api/migrations/maint/fn_evaluate_test_results.sql`
- `PROJECT_STATUS.md`

Bounded code change:

- normal-mode INST evaluation now reads `ctx.inst_tol_lo/hi` instead of `ctx.inst_ovrtol_min/max`
- MAINT precedence remains unchanged through `maint_inst_tol_lo/hi`
- no route, plot, settings, TMT, EMT, hosted, or product-surface edits were made
- no live database mutation was applied in this packet

Intentionally not widened in this packet:

- no edit to `apps/control-plane-api/services/neta/router.py`
- no live application of the migration
- no cleanup of the separate checked-in drift in `fn_calculate_test_currents.sql` or `vw_sensor_calc_context.sql`

---

## 3. Validation

Focused validation completed immediately after the helper design edit.

1. Rollback-only targeted dry-run
   - method: load the patched `20260528_000011_reapply_etu_evaluate_function.sql` inside a single SQL transaction, call the live route for sensor `17892`, call the helper in the same uncommitted transaction, then roll the transaction back
   - result: PASS
   - route `INST.limit_low/high`: `127.5 / 172.5`
   - dry-run helper `INST.limit_low/high`: `127.5 / 172.5`
   - pickup pass state: matched

2. Rollback-only full-matrix dry-run
   - method: replay all three committed ETU matrix scenarios against the live route while the patched helper was loaded only inside the rollback-only transaction
   - result: PASS
   - `sensor-25-ge-mvt-rms9-800-normal`: matched
   - `sensor-26-ge-mvt-rms9-600-live-derived`: matched
   - `sensor-17892-abb-ekip-dip-lvpcb-lsi-100-live-derived`: matched

3. Supabase advisor sweep
   - method: current project security and performance advisor retrieval
   - result: no new blocker tied to this helper correction
   - observed baseline items remained info-level project debt such as `rls_enabled_no_policy` and `unindexed_foreign_keys`

Because the packet preserved the no-live gate, the previously recorded live parity artifact remains truthful: `2` pass scenarios and `1` evaluate-side warning until an operator authorizes the live helper reapply.

---

## 4. Operational Meaning

This packet establishes that the unresolved ETU warning is not a route-contract defect.

It is a parity-helper drift issue only:

- runtime authority remains with the route
- the route's `±15%` result is backed by live sensor data and import/spec lineage
- the helper design is now corrected in-repo
- the remaining live warning persists only because no live helper cutover was performed here

---

## 5. Next Step

Operator-authorized follow-on only:

1. apply `apps/control-plane-api/supabase/migrations/20260528_000011_reapply_etu_evaluate_function.sql` to the governed Supabase project
2. rerun `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py --base-url http://127.0.0.1:8010`
3. confirm the live artifact resolves from `2 pass / 1 warn` to `3 pass / 0 warn`

Until that explicit cutover happens, no live-parity pass claim should be made for sensor `17892`.
