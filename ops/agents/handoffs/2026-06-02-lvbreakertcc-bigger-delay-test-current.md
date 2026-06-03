# Handoff — lvbreakertcc: operator-selectable delay test current + I²t-consistent LTD time

**Date:** 2026-06-02 · **Commit:** `apex 8b6a9b65` (+ SSoT reconcile commit) · **Status:** SHIPPED + live-verified

## What & why
Operator: *"looking ahead to the bigger delay test current option enable."* The LIVE ETU Screen-2 delay
**Test @** was fixed (LTD hardcoded 3×, display-only); a field tech could not test the long-time delay at
the bigger current where it is practical. Enabled a **selectable delay test current** per delay element and
made the expected trip time correct at the chosen multiple.

## The triangulated finding (why "bigger" matters)
- Source `DatSection2LTD.LTD_DESC` = whole seconds (`"2s".."24s"`); the engine's `_ltd_reference_delay_surface`
  anchors at 6× → **the stored LTD band setting is the trip time at 6× Ir** (industry long-time band reference).
- So the long-time delay is naturally tested at **6× (600%)**, where the expected time **equals the dial
  setting** (e.g. 12 s) and is directly measurable; at 3× it is **4× longer** (48 s).
- The pre-change LIVE page showed the 6×-anchored band time (12 s) under a fixed **"3×"** label, and
  `/calculate` carried a **band↔multiplier conflation** (LTD echoed the band value 12 as the multiplier →
  inject 11,520 A; the frontend masked it). Both now fixed.

## Changes (commit 8b6a9b65 — 5 files)
- **`services/neta/schemas.py`** — `CalculateRequest` gains `ltd_test_multiple` / `std_test_multiple` /
  `gfd_test_multiple` (optional; default = NETA 3× / 1.5× / 1.5×).
- **`services/neta/router.py`** `/calculate` delay loop — inject current = `selected_multiple × pickup_current`;
  LTD routed through `use_ltd_reference_window=True` (`t = setting·(6/N)²`) so the bands table **agrees with the
  Screen-3 `/plot-tcc` curve** at the same multiple. STD/GFD keep the definite-time band table (their inject
  scales). Trust gating + withholding preserved.
- **`app/lvbreakertcc/page.tsx`** — per-delay **Test @** dropdown (1×–6× in 0.5 steps, the `MULT_OPTS` band)
  drives a `/calculate` recompute via a `testMult` state; reads `multiplier`/`test_current`/`delay_seconds`
  straight off the response (removed the `NETA_DELAY_MULT`/`displayTestMult`/`displayTestCurrent` shim that
  only existed to mask the conflation). Methodology note updated.
- **`lib/breaker-resources.ts`** — three test-multiple fields on `EtuCalculateRequest`.
- **`tests/test_neta_plot_tcc.py`** — new `test_calculate_bigger_delay_test_multiple_scales_i2t_and_inject`
  (6× → time=setting, inject=6×pickup; 3× → 4× the time, half the current); updated 2 tests that asserted the
  old band-table LTD time (now the correct I²t value).

## Verification
- **Tests:** 88 green (`test_neta_plot_tcc` 38 + `test_delay_trust` + `test_settings_route` 50); `tsc` + `next build` clean.
- **Live** `[VERIFIED-LIVE 2026-06-02]` — `/calculate` s1806 (LTPU 0.8 → 960 A pickup, LTD band 12 s):
  1× → 432 s / 960 A · 3× → 48 s / 2,880 A · 6× → **12 s / 5,760 A** · trust=db · band scales (0.7·nominal) ·
  ratio time(3×)/time(6×) = 4 (I²t) · conflation gone. STD s30075 inject scales 150→300 A, time correctly
  withheld (I2X route 1). Vercel `/lvbreakertcc` HTTP 200.

## Open decision (operator)
- **LTD default test multiple** = 3× (NETA ATS 300% standard), with **6×** one click away. **Lean: keep 3×
  default** (no surprise vs the established NETA_TEST_PLAN_SPEC) — the tech selects 6× when they want the
  practical, dial-equal time. Flip the default to 6× only on operator direction.

## Follow-ons (noted, not blocking)
- LTD reference-window tolerance band is `(0.7·nominal, nominal)` (−30 %/0) — the engine's window, carried for
  curve↔table consistency. A NETA-specific LTD **time** tolerance is a future refinement (operator's acceptance
  criteria).
- `/evaluate` still uses the band-table LTD path. The LV page computes PASS/FAIL client-side from `/calculate`
  (so it is unaffected); reconcile `/evaluate` to the reference window if it is ever wired into the page.
- §110 plug-truncation bug (separate) still open; §107 GF `field[13]` promotion still paused.

## SSoT
G4-CALC-GUIDE §4 (test-POINT vs expected-TIME note extended: I²t LTD model + conflation fix);
G3-ROUTING-GUIDE §A3d (`/calculate` test-multiple params). STATE §111. Memory `project_tcc_lvbreaker_mvp_page`.
