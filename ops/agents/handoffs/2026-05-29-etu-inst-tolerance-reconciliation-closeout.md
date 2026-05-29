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

---

## 6. Addendum (2026-05-29, operator-directed) — fallback eliminated, derive-from-tables enforced

Operator review challenged the residual `±10` *fallback* left in the helper (`COALESCE(ctx.inst_tol_lo, -10)`), on the principle that **NETA general tolerances apply only in the absence of manufacturer data; we have that data, so the band must be derived from the tables.** `NETA_TEST_PLAN_SPEC.md:149` states it directly: "Always use the per-sensor values, never assume ±10%." (Contrast STD/GFD *timing* at `:158-159`, which have **no** manufacturer column and legitimately use a ±10% service default.)

### 6.1 Hypothesis + evidence
Operator hypothesis: a NULL pickup tolerance means **the element isn't present on that trip unit**. Substantiated against the raw manufacturer source (`DatSensor`, 17,831 rows, in the fidelity-staging Postgres mirror of the same Access source; the governed Supabase MCP is read-blocked for SQL, so staging — identical reference data — was used; 17892 cross-checked = same `±15` as live):

INST (`DS4_PICKUP_CALC` × `DS4_TOL_LOW/HIGH`):
| inst_calc | sensors | tol NULL | tol present |
|---|---|---|---|
| −1 (no calc / absent) | 653 | 65 | 588 |
| 0,1,4,5,6,7 (valid) | 17,178 | **0** | 17,178 |

GFPU (`DS1GF_PICKUP_CALC` × `DS1GF_TOL_LOW/HIGH`):
| gfpu_calc | sensors | tol NULL | tol present |
|---|---|---|---|
| −1 (no calc / absent) | 6,424 | 397 | 6,027 |
| 0,1,5,6,7 (valid) | 11,407 | **0** | 11,407 |

- A NULL pickup tolerance occurs **only** where `PICKUP_CALC = −1` (65/65 INST, 397/397 GFPU). The element-present-but-tolerance-NULL case is **exactly 0**.
- Observed present-element tolerances are genuinely per-device, several asymmetric: −12.7/+11, −8/8, −20/20, −15/15 — never a uniform ±10.
- 17892 = StyleID 1541: `Inst Pickup` calc=1 tol=−15/+15 (present); `GF Pickup` calc=−1 (absent, stale −10/10 ignored). An LSI-class unit: instantaneous present, ground fault absent.

### 6.2 Mechanism (why the fallback was already dead)
`fn_calc_etu_pickup_current` returns NULL when `p_calc_method = −1` (or NULL). The evaluate helper computes bands only inside `IF *_test_i IS NOT NULL`. So an absent element (calc=−1) yields a NULL test current and is **skipped entirely** (no band, no JSON block, excluded from `overall_pass`). The `±10` fallback could therefore only ever be reached for an absent element that was already being skipped → **dead code** that produced no wrong evaluation, but violated the spec in principle and was a latent trap.

### 6.3 Corrected change (behavior-neutral, spec-clean)
- Dropped the `±10` magic fallback for the manufacturer-data elements: `COALESCE(ctx.inst_tol_lo, -10)` → `ctx.inst_tol_lo` (and hi / GFPU). **Provably behavior-neutral** across the full catalog (NULL tol only co-occurs with the skipped calc=−1 path), while removing the spec-violating default and codifying derive-from-tables.
- Added a defensive guard: if a *present* element ever lacks a tolerance (data says never; catches a future import regression), append a warning and leave the band indeterminate rather than fabricate a default.
- STD/GFD timing `±10` retained (spec-sanctioned; no manufacturer column).
- Files: `fn_evaluate_test_results.sql` (maint) + `20260528_000011_reapply_etu_evaluate_function.sql`. Route untouched.

### 6.4 Status
Design corrected in-repo. Live apply still pending operator-authorized cutover (now routed to CC on the proven governed DSN): apply the migration → rerun the probe → confirm `2 pass / 1 warn` → `3 pass / 0 warn`. No live mutation performed in this addendum.
