# 2026-06-02 CC lvbreakertcc — validated setting-catalog override (envelope-only sensors)

## Status

**Shipped for the first family (Eaton PXR2 20D/25 LSI @225A); a repeatable loop for the rest.**
The lvbreakertcc Protection-Settings dropdowns were offering settings the breaker cannot
physically be set to. Root-caused, fixed for the PXR2 instance via a cited vendor-doc catalog,
and locally validated. Part of the marathon toward a fully functional, validated breaker library.

## The anomaly (operator-flagged, browser-examined)

For the Eaton Power Defense PXR2 20D/25 LSI @225A the Screen-2 settings were wrong:
- **LTPU** offered `80 × Ir … 225 × Ir` (146 values, 1-A step) — including **153 A, which is not a real dial position**, and mislabelled "× Ir" when the value is amperes.
- **LTD** offered only **2** values (`0.5`, `24`) — every intermediate long-time-delay tap missing.
- STPU/INST similarly dense (0.1 steps).

## Root cause (triangulated: live UI + source DB + Eaton vendor doc)

EasyPower's `DatSection*` tables store settings two ways (G1 §7):
- **Discrete taps** (one row per dial position) for **~77%** of ETU sensors — the `/settings`
  endpoint serves these correctly (e.g. MicroLogic 5.0A sensor 1806 → 9 real LTD taps).
- **Envelope-only** (min/max endpoints + an internal `DatSensor.DS*_STEP_SIZE`) for **~23%** —
  newer digital trip units (PXR2, M-Pact, OPTIM 750, Seltronic, …; ~4,106 sensors).

For envelope-only sensors the endpoint synthesized a dense uniform list from `(min,max,step)`.
But **`DS*_STEP_SIZE` is EasyPower's curve-drawing granularity, not the dial increment** — real
taps are non-uniform (PXR2 Ir: `80,90,100,110,125,150,160,175,200,225`). The discrete positions
are **not in EasyPower** for these units; they live only in OEM docs. Confirmed against the source
copy of `D:\TCC_NEW.accdb` (`DatSensorParms`/`DatSettings`/`DatSensorSec2` all empty for sensor
28023; all 4 PXR2 ratings 2-row) and the live API. The Eaton doc the operator supplied
**corrected** an earlier "expand LTD by step 0.1" hypothesis (which would have produced 236 fake
values).

## The fix — cited vendor-doc catalog override

- **`apps/control-plane-api/services/neta/setting_catalog.py`** (NEW) — `(trip_style_id, rating)`
  → validated discrete taps, each with a `[VENDOR-DOC]` source. Seeded with **PXR2 20D/25 LSI
  @225A** from **Eaton Power Defense Frame-2 TCC `TD012064EN`**:
  LTPU `80,90,100,110,125,150,160,175,200,225 A`; STPU `1.5,2,3,4,5,6,8,10,12 ×Ir`;
  LTD `0.5,2,4,7,10,12,15,20,24 s @6×Ir`; INST `2,3,4,5,6,7,8,9 ×In`.
  Plus `pickup_unit()` — the `ETUCalcMethod` → display-unit map (7→"A", 4→"× Ir", 0/1/…→"× In").
- **`services/neta/router.py`** — `get_available_settings` consults the catalog for the sensor's
  `(style, rating)`; when present it serves the validated taps instead of the synthesized range,
  and returns a per-element `units` map + a `validated_source` citation. The discrete-data 77% and
  every other sensor are untouched (catalog keyed by style/rating; only PXR2 affected).
- **`services/neta/schemas.py`** — `units` + `validated_source` added to `AvailableSettingsResponse`
  (additive, optional).
- **`operations-web` (`page.tsx` + `lib/breaker-resources.ts`)** — pickup options now label from the
  backend `units` (LTPU "A", STPU "× Ir", INST "× In"), replacing the hardcoded "× Ir". The label is
  sensor-dependent because LTPU representation is (PXR2 `ltpu_calc=7` amperes vs MicroLogic `calc=1`
  ×In).

## Validation (local; deploy gated separately)

- `py_compile` clean (3 files); catalog logic unit-tested (taps + unit map).
- **`tests/test_settings_route.py` 8/8** — 6 originals unchanged (proves the 77% discrete + the
  range-expansion paths are intact) + 2 new (PXR2 catalog taps/units/citation; sibling 60A rating
  without an entry stays on the prior path). Delay-trust suite 42/42.
- Frontend `tsc --noEmit` exit 0.

## Bounded follow-ons (the marathon)

- PXR2 **60/100/150 A** Ir taps (Ir is rating-specific where `ltpu_calc=7`).
- **OFF** (STPU) and **MAX** (INST) special dial positions; **STD FLAT/I²t** reconciliation (STD
  still serves its EasyPower rows).
- The rest of the ~4,106 envelope-only population — one `[VENDOR-DOC]` family at a time.

## SSoT

- `reference/tcc/00-MASTER-INDEX.md` — new `[VENDOR-DOC]` provenance class (§2) + §5 honesty bullet.
- `reference/tcc/G1-SCHEMA-GUIDE.md` — §7 settings-storage model + the validated catalog; header bumped.
