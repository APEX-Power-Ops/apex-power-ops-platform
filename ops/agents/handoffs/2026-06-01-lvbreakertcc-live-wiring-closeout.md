# Closeout: LV Breaker TCC live-wiring lane (Stages A–B + dual-axis backend)

Date: 2026-06-01
Lane: TCC LV Breaker MVP → the field-tolerance product
Status: **Stages A + B (ETU + TMT + EMT) + dual-axis (backend + FRONTEND) + NETA Test @ fix SHIPPED + verified live on prod.** Stage C (live curve + gated engine patch) remains.
Predecessor: `2026-06-01-codex-lvbreakertcc-wiring-scoping` (`WIRING_SCOPING.md`) + the D1 SST-bridge recovery (STATE §104).

This is the authoritative record of the live-wiring build. The reference guides (G0–G4/00) and STATE/memory summarize from here.

## What shipped (all `apex-power-ops-platform` `main`; each smoke-tested on prod)

| Slice | Commit | What |
|---|---|---|
| **A0** | `b9520af6` | `GET /etu/bridge-sensors` — breaker style → compatible ETU sensor set over `tcc.vw_breaker_sst_bridge`; 3 unit tests |
| **A1** | `5f60eb32` | `/lvbreakertcc` Screen 1 **LIVE** — family-dispatched selection (ETU bridge-narrow · TMT · EMT); full 3-family fetch layer already existed in `lib/breaker-resources.ts` |
| **A-fix** | `2af6c077` | `bridge_only` param on `/etu/breaker-cascade` — ETU tab shows only ETU-capable breakers (MCCB 640→130); "Breaker Style" relabeled "Frame Size" (it is `s.frame`) |
| **collision** | `fda37944` | `/etu/bridge-sensors` cross-class id collision fixed (`breaker_class` disambiguation) — **operator-caught** |
| **Stage B** | `f4e6a227` | Screen 2 **LIVE** for ETU — editable settings (`/settings`) → `POST /calculate` → DB-authoritative NETA tolerance bands; measured %Error + PASS/FAIL vs live limits; per-row G4 trust labels |
| **bridge_xfilter** | `05fe82f8` | bridge-aware **bidirectional** cross-filter (opt-in) on `/cascade` + `/etu/breaker-cascade` — replaces manufacturer-only (130→1 / 1562→4) |
| **dual-axis UI** | `99d0dc88` | **co-equal dual-axis ETU selector** — Breaker lane (`/etu/breaker-cascade`) + Trip-Unit lane (`/cascade`), each passing `bridge_xfilter` with the opposite axis as cross-half; shared "Compatible Sensor" terminal from whichever axis reaches a leaf (`/cascade.sensors` intersection, else `/etu/bridge-sensors`); live compatible-count badge. Plumbs `bridgeXfilter` through `fetchCascade` + `fetchEtuBreakerCascade` |
| **NETA Test @** | `ce66a1b7` | **delay Test @ + inject current corrected to NETA points.** The page read the delay "Test @"/"Test Current" from `/calculate`, but it sends the delay BAND as the `p_*_multiplier` param → engine echoed the band as the multiplier (STD showed `0.1× / 1,200 A`, below pickup). Now overrides the DISPLAY with the NETA ATS points (`NETA_TEST_PLAN_SPEC §11`: LTD 3× LTPU · STD 1.5× STPU · GFD 1.5× GFPU) + inject current = multiple × the element's pickup current. Expected *time* stays "verify" (band→curve recompute = Stage C). Pickups + SampleSettings unchanged |
| **TMT/EMT S2** | `7db558e7` | **Screen 2 for the other two families** (were falling through to SampleSettings). **TMT** (bounded): `/tmt/settings` → trip class / amp rating / magnetic setting / thermal adj + a 2-element NETA plan — magnetic INST pickup (= setting × rating) with DB ±tol → measured %err/PASS-FAIL ("DB"); thermal LT @ 3× rating, band curve-governed ("verify"). **EMT** (context-only): `/emt/settings` → the selected section's pickup options + DB ±tol + bands; EMT pickup→current calc not engine-validated → computed amps / PASS-FAIL deliberately withheld (Stage C). |

## Live verification (prod: `control.apexpowerops.com` + `operations.apexpowerops.com`)
- `/etu/bridge-sensors?breaker_style_id=311&breaker_class=ICCB` → 5 ABB PR332/P sensors (`T8V-1600`).
- `bridge_only`: MCCB **640 → 130** ETU-capable breakers; all-class `{ICCB:27, MCCB:130, PCB:97}`.
- collision: style `1510` → **3 DT 510 R-Frame (MCCB) only**, not the 13 with the foreign PCB MPS-C-2000 bleed-in.
- Stage B: LTPU 0.9×1000 → 900 A test, band **945–1080** (DB-authoritative); STPU/INST likewise.
- `bridge_xfilter`: breaker→trip **130 trip styles → 1**; trip→breaker **1562 breakers → 4**.
- **dual-axis UI (live browser, prod):** trip-first — Trip Style 155 (R-Frame) narrowed Breaker Manufacturer **44 → 2** (Cutler Hammer / West) and surfaced **3** DT 510 sensors; picking sensor 1195 finalized (Trip *Cutler-Hammer DT 510 R-Frame*, Ir 2000 A, plugs 1000–2000A) and Screen 2 computed live DB bands. Breaker-first — Breaker Class ICCB narrowed the compatible-sensor pool **~17,831 → 444**. No console errors. The asymmetry (dense breaker→sensor, sparse sensor→breaker) is correct bridge data; both flows still finalize on a sensor.
- **NETA Test @ (live browser, prod):** ABB Ekip Dip XT2 LSIG (sensor 30075) → pickups **1×** (DB); **LTD 3× / 216 A** (= 3×LTPU 72), **STD 1.5× / 825 A** (= 1.5×STPU 550, now *above* pickup), **GFD 1.5× / 83 A** (= 1.5×GFPU 55). Inject currents cross-check exactly; element cards match the table; 0 console errors.
- **TMT S2 (live browser, prod):** ABB Tmax T5V-630 (frame 8038, amp 320, mag 4.0×) → magnetic INST pickup **1,280 A** (= 4×320), DB band **1,152–1,408 A** (±10%); thermal LT 320 A @ **3×** = **960 A**, band curve-governed ("—"). **EMT S2:** GE EC-1 AK-1-25 (frame 3575), section "LT Pickup" → pickup 0.8, DB **±10%** tol, 3 bands; context-only (no computed amps). 0 console errors.

## Key findings (propagated to the guides)
1. **Per-class serial-id OVERLAP hazard.** `brk_{iccb,mccb,pcb}` and their `*_styles` use independent per-class serial ids that **collide** (style `1510` is both an MCCB *DT 510* and a PCB *MPS-C-2000*). The real key is the **`(class, id)` pair**. Now applied in `bridge_only`, `/etu/bridge-sensors`, and `bridge_xfilter`. → **G1 hazard note.**
2. **The cross-filter fix is SHIPPED** (was `[DEFERRED]` / "proposed"): bridge-aware **bidirectional** cross-filter (`bridge_xfilter`), opt-in so the explorer's manufacturer-only behavior is untouched. → **G2 BG-5, G3 A3, 00.**
3. **Field-trust on the LV page (G4).** Pickup bands (LTPU/STPU/INST/GFPU) = DB-authoritative per-sensor tolerances (field-safe, "DB" badge). For delays the **test point is separable from the time**: the NETA test multiple (LTD 3× / STD·GFD 1.5×) + inject current (= multiple × pickup) are **field-correct** (now rendered directly, `ce66a1b7`); only the expected **time** stays **"verify"** (the band→curve recompute at the point = Stage C). → **new G4 §4 "test-POINT vs expected-TIME" note.**

## Residuals / next
- ✅ **Dual-axis FRONTEND** — SHIPPED `99d0dc88`, live-verified (co-equal, both axes narrow each other; sensor reachable from either end). The §97 manufacturer-only ceiling is now closed end-to-end in the UX.
- ✅ **TMT/EMT Screen 2** — SHIPPED `7db558e7`, live-verified (TMT bounded w/ magnetic ±tol DB; EMT context-only). G4 bounded-surface posture honored.
- **Stage C** — live per-family curve (`/plot-tcc` · `/tmt/plot-tcc` · `/emt/plot-tcc`; the curve *render* is shippable bounded) + the **gated** `route_delay_curve` engine patch (promotes delay rows from "verify" → "DB"; engine change = checkpoint). Also unlocks: selectable delay test points (live time recompute), EMT computed test currents, TMT thermal LT band.
- **D4** (`TMT_*` helper cols) still open — now a trivial `source_id`-join.
- **Pre-existing test failure** — `test_etu_search_count_query_reuses_plug_join_and_scope_filters` (stale exact-param-dict assertion, doesn't account for `q_exact`/`q_prefix`); reproduces on clean `f4e6a227`, **NOT from this lane**. Needs a 1-line test fix.

## Boundaries honored
Read-only against governed Supabase (the D1 write was a prior-session authorized write). No secrets / client / job identifiers in this PUBLIC repo. Scoped `git add`. `tsc --noEmit` + `next build` green each deploy; pytest green except the noted pre-existing failure.
