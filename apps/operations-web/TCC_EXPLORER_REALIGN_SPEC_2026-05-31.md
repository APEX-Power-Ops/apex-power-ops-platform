# TCC Breaker Explorer — EasyPower Dual-Filter Realign + NETA Tolerance Output (Spec)

**Date:** 2026-05-31 · **Status:** approved, for execution · **Authority:** EasyPower-fidelity (`source-domains/tcc_v5_backend/services/neta/` + `neta_tcc.html` demo) is the spec of record; the hosted `operations-web` explorer is the lagging forward-port being realigned.

**Why:** the hosted breaker resource explorer must reproduce EasyPower's **dual breaker × trip-unit selection**, and its end-purpose is producing **per-element pickup + time-delay settings and their tolerances for NETA field testing** — not generic resource browsing.

---

## A. Target workflow — EasyPower dual-axis (CONFIRMED against active backend)

Two **independent, manufacturer-cross-filtered** selection axes presented together (not one `family` dropdown):

**Axis 1 — Breaker (construction):** `Breaker Manufacturer → Breaker Class {ICCB | MCCB | PCB} → Breaker → Breaker Style` → terminates in `breaker_style_id` (carries `ac_dc_code`, frame/style, manufacturer). Backend: `GET /api/v1/neta/etu/breaker-cascade` (`router.py:3131`), params `manufacturer_id / breaker_class / breaker_id / breaker_style_id`, over `vw_etu_breaker_cascade` (UNION of `tcc.brk_iccb/mccb/pcb` + `_styles`).

**Axis 2 — Trip unit:** `Trip Unit Manufacturer → Trip Unit Type {ETU | TMT | EMT} → Trip Unit Style → Sensor/Rating` → terminates in `sensor_id` (ETU) / `frame_id` (TMT/EMT). Backend: `GET /api/v1/neta/etu/search` over `vw_trip_unit_cascade` (`router.py:3060`).

**Cross-filtering:** the two views share **`manufacturer_id` only** — no deeper sensor→breaker mapping is persisted (mirrors EasyPower DLL `FindMatchingBreakerStyles` staged narrowing). So selecting on one axis narrows the other **at the manufacturer boundary**. The dual filter is therefore a **manufacturer intersection**, NOT a new join/view: feed the breaker-cascade's manufacturer set into `/etu/search` via its existing `manufacturer_id` param (`router.py:3062`), and feed trip-unit selections (`trip_type_id`/`sensor_id`) into `/etu/breaker-cascade` (params exist `router.py:3134+`).

**Termination:** both axes committed → device fully qualified → load `/context` + `/settings` → POST `/plot-tcc` → render the **test plan** (below).

## B. The NETA purpose — per-element pickup/time-delay tolerance test plan (CONFIRMED)

Seven elements, in calc order; for each: a pickup (current) value + asymmetric tolerance band AND/OR a time-delay value + time band the tester injects against:

| Element | Pickup test | Delay test | Source of numbers |
|---|---|---|---|
| **LTPU** Long-Time Pickup | ramp → pickup + lo/hi | — | `tcc.etu_sensors.ltpu_tol_lo/hi`; `etu_pickup.py` |
| **LTD** Long-Time Delay | — | LTPU×mult → time + band | `tcc.etu_ltd_params.tol_lo/hi`; `ETULTDCalculator` |
| **STPU** Short-Time Pickup | ramp → pickup + band | — | `stpu_tol_lo/hi` (cascade-from-LTPU when method 4/9) |
| **STD** Short-Time Delay | — | STPU×mult → time + band | `tcc.etu_std_bands` + **service ±10% default** (no DB col) |
| **INST** Instantaneous | ramp → pickup + band | — | `inst_tol_lo/hi` |
| **GFPU** Ground-Fault Pickup | ramp → pickup + band | — | `gfpu_tol_lo/hi` |
| **GFD** Ground-Fault Delay | — | GFPU×mult → time + band | `tcc.etu_gfd_bands` + **service ±10% default** |

**Tolerance rule (NETA_TEST_PLAN_SPEC.md:145-149):** `min = expected × (1 + tol_lo/100)`, `max = expected × (1 + tol_hi/100)`, `tol_lo` negative → bands are **asymmetric, per-sensor** (e.g. LTPU +20/−5; 20+ distinct pairs). **Always use per-sensor values; never assume ±10%.** The ±10% default applies ONLY to STD/GFD timing where no DB column exists. A `NULL` tolerance / `PICKUP_CALC=-1` ⇒ absent element ⇒ skip the row.

**The payload already exists and is already fetched.** `POST /plot-tcc` returns `EtuPlotResponse.table_rows: EtuPlotTableRow[]` (`lib/breaker-resources.ts:186-223`): `element, kind, setting, test_multiple, expected_current, limit_low, limit_high, expected_time, time_limit_low, time_limit_high, calc_method, notes` — **this IS the NETA test plan.** The explorer already builds the request (`buildEtuPlotRequest` w/ `plug_rating`+settings, `breaker-resource-explorer.tsx:75`) and calls `fetchEtuPlot` (`:25`). TMT/EMT carry tolerances on `TMTSettingOption.tol_lo/hi` and `EMTSectionSummary.pickup_tol_lo/hi`.

## C. Gaps (current vs target)

- **[UI] The `table_rows` NETA test plan is fetched but NEVER rendered.** `breaker-selection-panels.tsx` references only `marker.expected_current` (`:456`, a curve marker) — zero rendering of `table_rows`. **Primary gap; the operator's stated deliverable is dropped.** CONFIRMED.
- **[UI] No dual-axis form.** Single `family` dropdown (`breaker-resource-explorer.tsx:150,424-434`); breaker-construction axis absent for ETU/EMT; present only inside TMT (`:452-466`) as a search branch, and as a *passive* post-selection "breaker matches" card for ETU (`:303,596`). CONFIRMED.
- **[UI] Tolerances shown as raw `tol -10 to +10`, not a NETA band** (`breaker-selection-panels.tsx:706`). CONFIRMED.
- **[UI] Hardcoded search seed `etu: 'GE'`** (`breaker-resource-explorer.tsx:50`) → auto-floods on load. CONFIRMED.
- **[backend] ETU `q` = `ILIKE '%q%'` over 4 text cols** (manufacturer/trip_type/trip_style/sensor_desc, `router.py:1676-1686`) → "GE" substring-matches Generic / Challen**ge**r / **GE**N3 / Merlin **Ge**rin. GE manufacturer exists ("GE", "GEIS" among 120) but is buried. CONFIRMED.
- **[backend/data] `/etu/search` exposes NO construction column** — construction lives only in `vw_etu_breaker_cascade`, joinable to the trip-unit axis at `manufacturer_id` only. So dual-axis ETU filtering = manufacturer intersection (no schema change). CONFIRMED.
- **[data — INFERENCE] EMT likely has no construction/`breaker_class` notion** — cross-filter EMT by manufacturer only (verify before building axis-1 for EMT).

## D. Fix plan

### Quick wins (no schema; deliver the NETA purpose)
1. **[UI] Render the `table_rows` test-plan table** — new section in `breaker-selection-panels.tsx` consuming `selection.plot.table_rows`: columns Element / Test current / Expected / Lo / Hi / Expected time / Time-lo / Time-hi / Method. (Also surface TMT/EMT tolerance equivalents where present.) **Highest value.**
2. **[UI] Tolerances as NETA bands** (`expected → [lo, hi]`), replacing raw `±tol` at `breaker-selection-panels.tsx:706`.
3. **[backend+UI] Search precision** — remove the hardcoded `'GE'` seed (`breaker-resource-explorer.tsx:50`); make `/etu/search` `q` manufacturer-prioritized (rank/anchor exact+prefix manufacturer matches; keep style/desc as secondary), `router.py:1676-1686`. Acceptance: `q=GE` surfaces real "GE" rows at the top, not Generic/Challenger noise.
4. **[UI] Relabel** "Breaker family" → "Trip Unit Type" (`breaker-resource-explorer.tsx:423`).

### Structural — EasyPower dual-axis rebuild (second dispatch)
5. **[UI] Add Axis 1 (breaker construction) front-of-form** for all families, fed by `/etu/breaker-cascade` (`fetchEtuBreakerCascade`, `lib/breaker-resources.ts:594`): `Breaker Mfr → Class → Breaker → Style`. Move it from the passive post-selection card to a primary cascade.
6. **[UI/backend] Manufacturer-level cross-filtering both directions** — breaker-half → constrains `/etu/search` via `manufacturer_id`; trip-unit-half → passes `trip_type_id`/`sensor_id` into `/etu/breaker-cascade`. No new endpoints (composition only).
7. **[data] EMT construction axis** — conditional on confirming EMT carries a construction signal; else document EMT as manufacturer-only and stop.

**Files:** `apps/operations-web/app/breaker-selection-panels.tsx`, `apps/operations-web/app/breaker-resource-explorer.tsx`, `apps/operations-web/lib/breaker-resources.ts`, `apps/control-plane-api/services/neta/router.py:1668-1687`.

**CONFIRMED vs INFERENCE:** all CONFIRMED items verified 2026-05-31 against active files + live endpoints. INFERENCE: EMT-has-no-construction; effort estimates. Source-domain `tcc_v5_backend` line numbers describe the demo (behavior matches active; active line numbers differ).
