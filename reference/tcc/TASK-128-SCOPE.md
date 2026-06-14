# Task #128 — Generalize route-1 STD/GFD curve synthesis (SCOPE + RATIFIED DECISIONS)

*Created 2026-06-14. RATIFIED by operator ("proceed as outlined"). Tier-1 build in progress.*
*Cross-refs: STATE §214 (the #72 composite verify→db close), §207/§119 (InvEq un-gate), G4-CALC-GUIDE §3g, `RESUME_HERE.md` §128 queue item, `TOLERANCE-COVERAGE-PUNCHLIST.md` L4.*

## Problem

Route-1 trip sensors carry native time-current BAND data (`tcc.etu_std_bands` / `etu_gfd_bands`). Today the STD/GFD "staircase" curve is synthesized in `/plot-tcc` **only when the trip-style NAME contains "Micrologic"** (the `synthesize_i2t_longtime` gate). So ~**10,219 STD + 8,381 GFD** non-Micrologic route-1 sensors serve DLL-certified delay **times** + an INST vertical, but render **no short-time / GF curve**. The time axis is already ungated (fires on `route==1`); only the rendered curve is missing.

## Population (prod, 2026-06-14)

| | STD | GFD |
|---|---|---|
| non-Micrologic route-1 gap | 10,219 | 8,381 |
| └ composite i2x=2 (**§214 DLL-certified times**) | 5,549 | 4,659 |
| └ ramp i2x=1 | 1,624 | 792 |
| └ flat i2x=0/NULL | (overlapping) | (overlapping) |
| └ unknown i2x=255 → withhold | 2 | 2 |

The composite sets (5,549 / 4,659) match the §214 certified-times population (5,609 / 4,669) — these are the same sensors. Vendor spread = the entire electronic-trip universe minus Micrologic (Westinghouse/C-H Seltronic, SqD Masterpact + Compact NS, AB 140U, Eaton Digitrip DT 310 + PXR20/25, GE Spectra/MVT/M-Pact/ME, ABB Ekip Dip, Siemens ETU/Static Trip II, Terasaki Tembreak-2).

**RISK-1 evidence:** STD ramp anchor `i_open` is NOT clustered at the Micrologic ×Ir=10 convention — it spans 2, 2.5, 3, 3.05, 3.38, 4, 5, 6, 7, 7.2, 8, 8.3, 10, 12 … 23. The reference-axis basis is vendor-specific. **But** the time path uses the same `ref=Ir`, and §214 certified those times bit-exact, so the composite-certified set's curves are **transitively basis-validated**. The basis is unproven only for the non-certified tail.

## Ratified decisions

- **D1 — Gate = per-element `route==1`** (not the style name, not "has a band"). Mirrors `classify_delay_trust` and the already-shipped time path; preserves the InvEq fall-through for route-2.
- **D2 — Decouple the LTD-I²t flag.** Scope #128 to **STD/GFD only**. The LTD `t = tr·(6·Ir/I)²` law is Micrologic/IEC-specific; keep LTD synthesis on its own narrow flag (do NOT lift it for all styles).
- **D3 — STD reference-axis basis.** Tier-1 (composite-certified) needs no new basis work (transitively validated). Tier-2+ gets a bounded per-vendor basis-confirmation pass.
- **D4 — GFD plug-basis withhold.** Align the curve path with the time path — withhold the GF curve when the plug (In) basis is absent; do not guess `ref_in`.
- **Keep:** the partial-clear-block withhold, the InvEq no-double-draw guard, and the kernel's self-withhold on NULL/sentinel anchors. No fabrication.

## Code anchors (scoping map — confirm at edit time)

- Gate: `apps/control-plane-api/services/neta/router.py:7117-7119` (def), `:7137` (call), `:2965` (param), consumers `:3081` (LTD), `:3124` (STD), `:3203` (GFD).
- Time-path route==1 (mirror this): `router.py:~7146-7164, 7200`. GFD time-path withhold (mirror for D4): `router.py:~3246-3250` + `delay_trust.py:152-161`.
- Unchanged (vendor-agnostic, DLL-validated): `_synthesize_i2x_delay_curve`, `_load_i2x_curve_band`, `etu_ixt.i2x_delay_surface`, `composite_boundary.py`, `delay_trust.py`.

## Rollout (tiered by risk)

1. **Tier 1 — composite-certified (~5,549 STD + 4,659 GFD).** Basis proven via §214 times. Ship behind D1 + D2 + D4 + partial-clear withhold. Highest confidence, biggest immediate win. **← this build.**
2. **Tier 2 — ramp/flat sensors with complete anchor data** + the D3 per-vendor basis pass.
3. **Tier 3 — incomplete data** (NULL ramp anchors = L4 7,769/12,104 GFD; partial clear; no plug basis) → honest withhold.

## Validation plan

- **No-regression:** golden-snapshot byte-equality on Cohort A (corpus sensors 17/809/1160/3833/4628 + Micrologic — must be unchanged) + kernel-identity assertions on Cohort B (new sensors serve exactly the proven kernel output).
- **Oracle fixtures** all exist + CI-safe; new capture only if a vendor band tuple falls outside the captured corpus (D3 surfaces this).
- **Gate-pinning test to rewrite:** `test_neta_plot_tcc.py:1580` ("non-Micrologic ⇒ no synthesis") — flips for STD/GFD, stays for LTD.
- **Live-verify:** probe `/plot-tcc` on non-Micrologic corpus sensors 17/809/1160; deploy marker = a `std_*`/`gfd_*` curve appearing where there was none. Control sensor 3833 byte-unchanged. Playwright screenshot.
