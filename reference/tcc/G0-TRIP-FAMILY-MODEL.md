# G0 — Trip-Family Model (SST/ETU · TMT · EMT) + Breaker×Family Interaction

> **Owns:** the three low-voltage trip families and the single most important question in TCC
> selection — *does choosing a breaker determine its trip unit, and if so, how?* The answer is
> **different for each family.** Every selection/compatibility decision cites this guide.
>
> Last validated · 2026-05-31 (EMT edge **RESOLVED** — standalone-only, via decomp RE + live DB triangulation) · Desktop · Open gaps: **none** (the EMT edge is closed; see §5)

---

## 1. The three families at a glance

| Family | Long name | What it physically is | Curve/setting data lives in |
|---|---|---|---|
| **SST / ETU** | Solid-State Trip / Electronic Trip Unit | A separate electronic trip device installed in the breaker | `DatStyle` → `DatSensor` → `DatSection1/2/3/4*` + `DatPlugs` |
| **TMT** | Thermal-Magnetic Trip | A trip mechanism **built into the breaker frame** (incl. Motor Circuit Protector variant) | `Breaker_TMTFrameSizes` → `Breaker_TMTFrameAmps` / `Breaker_TMTFrameSettings` |
| **EMT** | Electro-Mechanical Trip | A self-contained breaker+trip family modeled on its own frames/sections | `EMT` → `EMT_Frames` / `EMT_Sections` / `EMT_Curves` |

> **Naming note:** "SST" (EasyPower's internal term, from the device-library code) and "ETU"
> (electronic trip unit, the field/NETA term) are the **same family**. The DB/engine use *SST*; the
> platform UI uses *ETU*. `[DLL EasyPower.DeviceLibrary]` `[DVL-DB]`

---

## 2. The Breaker × Family interaction matrix  ← the core of this guide

| Family | Does breaker selection determine the trip? | Discriminator (on the breaker style row) | Mechanism (how the trip is reached from a breaker) |
|---|---|---|---|
| **SST / ETU** | **Yes — the breaker style *points* to its compatible trip** | `TMT_Use_SST = 1` | `BreakerXXXStyles.(TMT_SST_Mfr, TMT_SST_Type, TMT_SST_Style)` → name-join → `DatStyle (Mfr_Name, TYPE, STYLE)` → `DatStyle.STYLE_ID` → `DatSensor.StyleID` → sections/plugs |
| **TMT** | **Yes — the breaker style *is* the trip** | `TMT_Use_SST = 0` | `BreakerXXXStyles.ID` → `Breaker_TMTFrameSizes.StyleID` → frame amps/settings (the thermal-mag curve is intrinsic to the frame) |
| **EMT** | **No — standalone-only.** A breaker selection **never** resolves to EMT `[VERIFIED-LIVE 2026-05-31]` | (no breaker-style→EMT pointer column exists; `EMT` carries no breaker back-reference) | EMT is reached ONLY via its **own** `EMT → EMT_Frames → EMT_Sections` manufacturer/frame/section browse. The managed `DeviceLibrary` (100% of engine device-SQL) has **zero** EMT references; no `EMT_*` column on any `BreakerXXXStyles`. `[DLL DevLibBreakerStyle.cs:135-159]` `[04]` |

**Plain-language summary for the field/UI:**
- **ETU breaker** → the breaker tells you exactly which electronic trip belongs to it (one trip family, a handful of sensors). *This is what makes "T8V-1600 → ABB PR332/P → 5 sensors" possible — and what was lost when the bridge columns were dropped (see §3).*
- **TMT breaker** → there is no separate trip to pick; the breaker frame **is** the trip.
- **EMT breaker** → **there is no "EMT breaker" in the breaker→trip sense.** EMT is its own self-contained family, selected directly from the `EMT*` catalog; no `Breaker*` row ever points to an EMT trip. `[VERIFIED-LIVE 2026-05-31]`

---

## 3. SST / ETU — the bridge (detailed)

**Gate:** `BreakerXXXStyles.TMT_Use_SST = 1` means "this breaker shell borrows an electronic (SST/ETU)
trip"; `= 0` means thermal-magnetic (→ TMT). The flag itself carries **no DB description**; its
polarity is established from the engine. `[DVL-DB BreakerMCCBStyles.TMT_Use_SST → no description]`
`[DLL DevLibBreakerStyle.cs GetBreakerStyles → DefaultUseSST]`

**The composite-key join** (name-based, *not* a numeric FK — this is why a loader expecting
`Manufacturers.ID` silently dropped it): `[VERIFIED-LIVE 2026-05-31]` `[01]` `[04]`

```
BreakerXXXStyles.TMT_SST_Mfr   = Manufacturers.Mfr_Name        (→ Manufacturers.ID)
BreakerXXXStyles.TMT_SST_Type  = DatStyle.TYPE
BreakerXXXStyles.TMT_SST_Style = DatStyle.STYLE      (with DatStyle.MFG_ID = Manufacturers.ID)
        → DatStyle.STYLE_ID = DatSensor.StyleID  (declared FK)
        → DatSection1/2/3/4* . SensorID  and  DatPlugs.SensorID
```

**Where the stitch lives:** application code, not SQL. `DevLibBreakerStyle.GetBreakerStyles(...)`
binds `TMT_Use_SST`/`TMT_SST_*` → `DefaultUseSST`/`DefaultTrip{Manufacturer,Type,Style}`; surfaced by
`DeviceLibrary.GetDefaultTripInfo(...)`; those strings are re-fed as the trip-cascade seed.
`[DLL DevLibBreakerStyle.cs:135-139]` `[DLL DeviceLibrary.cs:478]` `[03]` `[HANDOFF 2026-04-29-tcc-breaker-trip-unit-filter-workflow-audit]`

**Population & join health (live, authoritative):** `[VERIFIED-LIVE 2026-05-31]` `[04]`

| Class | Styles | `Use_SST=1` | matched to `DatStyle` | match rate |
|---|---:|---:|---:|---:|
| ICCB | 608 | 515 | 515 | **100%** |
| MCCB | 10,335 | 1,680 | 1,576 | **95.6%** |
| PCB | 3,279 | 3,193 | 2,162 | **97.5%** |

Unmatched rows are **genuine source catalog gaps** (missing `DatStyle` TYPE/STYLE combos), *not*
name-hygiene — `UCASE+TRIM` rescues 0. Fall back to manufacturer-scope + flag when no exact match.

**Worked example (the UI case):** breaker `T8V-1600` = `BreakerICCBStyles` id 44551, `TMT_Use_SST=1`,
SST = **ABB / PR332/P / ICCB-LSIG** → exactly **1 `DatStyle`** (STYLE_ID 1230) → **5 `DatSensor`** + 18
plugs. (Contrast the manufacturer-only UI, which offered 117 ABB trips.) `[VERIFIED-LIVE 2026-05-31]` `[04]`

> **Status of the persisted catalog:** the 4 bridge columns (`tmt_use_sst`, `tmt_sst_mfr/type/style`)
> are **NOT** in `tcc.brk_*_styles` today — dropped at load. Recovering them is a tracked schema gap
> (see G1 dropped-column register + G2 governance). Until then, the deployed cross-filter is
> manufacturer-axis only. `[VERIFIED-LIVE 2026-05-31]` `[HANDOFF 2026-04-29-tcc-etu-stage1-slice-gamma]`

**Same pattern, other domains** (for awareness; mapped in G1): `RelayDevices.SST_*` and
`DsgnProtEqp.SST*` use the identical "borrow-an-SST" shape (the latter via numeric `MFG_ID`). `[01]`

---

## 4. TMT — the trip *is* the frame (detailed)

**Gate:** `TMT_Use_SST = 0`. The thermal-magnetic curve is intrinsic to the breaker style's frame;
there is no separate trip-unit selection. `[DLL DevLibTMTFrameSize.cs]` `[03]`

**Path:** `BreakerXXXStyles.ID → Breaker_TMTFrameSizes.StyleID` → `Breaker_TMTFrameAmps` /
`Breaker_TMTFrameSettings`. `[DLL DeviceLibrary.cs:1322 ReadTmgnFrameIdsMatchingFrameAndTrip]`
`[VERIFIED-LIVE 2026-05-31 declared FK]` `[04]`

**TMT sub-discriminators on the breaker style** (decode before interpreting a TMT breaker): `[DVL-DB]` `[08]`

| Flag | Meaning |
|---|---|
| `TMT_BreakerType` | `0 = Thermal Magnetic`, `1 = Motor Circuit Protector` |
| `TMT_ThermalMagnetic` | `0 = With Adjustable Instantaneous`, `1 = Without adj instantaneous` |
| `TMT_TripPlug` | `0 = Trip`, `1 = Plug` |
| `c_testing_std` | `0 = ANSI-SYM`, `1 = IEC`, `2 = ANSI-TOTAL` (drives the test plan) |

**Instantaneous override on the frame:** the `InstOvr*` / `NInstOvr*` column blocks on the breaker
style carry a frame-limited instantaneous override (amps, tolerances, open/clear delay + radius).
These are **undescribed** in the DB and map to the engine's breaker-override mechanism. `[DEFERRED]`
`[DVL-DB BreakerMCCBStyles.InstOvr* → no description]` `[06]`

---

## 5. EMT — own catalog (detailed, with the open edge)

EMT is modeled by its own tables (`EMT`, `EMT_Frames`, `EMT_Sections`, `EMT_BandNames`, `EMT_Curves`)
and browsed via EMT facets — **never via `BreakerXXXStyles`.** `[01]` `[VERIFIED-LIVE 2026-05-31]`

**EMT discriminators** `[DVL-DB]` `[08]`:
- `EMT.TripChar` — **bitmap** `1=LT, 2=ST, 4=Inst` (OR-combined: `3`=LT+ST, `7`=all). **Decode bitwise, not as an ordinal.**
- `EMT.TripPlug` — `0 = Trip`, `1 = Plug`.
- `EMT PickupCalc = 0 → Ipu × TripAmps`; `EMT_Sections` carry conditional gates ("Delay/Radius used if `SecChar=4`").

**The open edge — RESOLVED 2026-05-31: standalone-only.** A `Breaker*` selection **never** resolves to
an EMT trip. Triangulated across all three surfaces (`[VERIFIED-LIVE 2026-05-31]` `[DLL]` `[04]` — see
`_discovery/_validation/v3-emt-edge.md`):
- **Engine (authoritative):** the managed `EasyPower.DeviceLibrary` — which centralizes 100% of the
  engine's device SQL — has **zero** EMT references (no token, no `GetEMT*` method, no EMT SQL). The
  breaker-style reader (`DevLibBreakerStyle.cs:135-159`) projects only `TMT_Use_SST`/`TMT_SST_*`/
  `TMT_Thermal*`; `GetDefaultTripInfo` returns only `useSST` + the SST triple. A breaker resolves to
  exactly **two** outcomes — borrow-an-SST (`TMT_Use_SST=1`) or TMT-frame (`=0`) — never a third. EMT has
  no managed class at all (only native `DvlEng\CdbDvlEMT*` nameless raw-IL shells). `[DLL DevLibBreakerStyle.cs:135-159]`
- **Access (both directions):** no `EMT_*` pointer column on `BreakerICCB/MCCB/PCBStyles` (68/68/76 cols);
  `EMT` carries no breaker back-reference (only `Mfr_ID`). `[04]`
- **Supabase:** no EMT-pointer column on any `tcc.brk_*_styles`. `[VERIFIED-LIVE 2026-05-31]`

**Residual caveat (does not weaken the verdict):** the native EMT C++ reader internals are unreadable
(decompiled to size-only struct shells) — but the breaker→trip dispatch lives entirely in the readable
managed layer, and that layer offers EMT no entry point.

**EMT load + curve chain (corrected 2026-05-31):** EMT **IS** loaded into `tcc.*` (7 populated tables:
`emt` 174, `emt_frames` 805, `emt_frame_amps` 1691, `emt_sections` 1765, `emt_band_names` 2971,
`emt_pickups` 6587, `emt_curves` 40735 — small RI-orphan deltas vs Access). The earlier "not yet
loaded" reading was stale; only browsable-UI *exposure* is a separate open question. The curve chain is
`EMT_Curves → EMT_BandNames(SecID) → EMT_Sections → EMT_Frames → EMT` (G1 §2D — `EMT_Curves.ParentID →
EMT_BandNames.ID`, 100%). `[VERIFIED-LIVE 2026-05-31]`

---

## 6. How families route into pickup/delay calc (pointer to G3/G4)

Once a family + sensor is selected, the **per-element routing** is governed by the engine constants
(authoritative table in G3/G4; named here so the family→calc handoff is explicit):
- Pickup method per element: `DS1/DS3/DS4/DS1GF_PICKUP_CALC` → `SSTCalcMethod` (`DVL_SST_SETTING_*`, -1..10). `[DLL SSTCalcMethod.cs:3-17]` `[09]`
- Delay routing per element: `DS3_SEC3_I2T`/`DS1GF_SEC3_I2T` → `SSTDelayCalc` (`DB_SST_DLCALC_*`, **0..4** — *not* the DB-described "0 or 1"). `[DLL DeviceLibrary.cs:67-75]` `[09]`

---

## 7. Cross-references
- Schema of every table named here + the dropped-column register → **G1**.
- The frozen-baseline status of the bridge gap + the deferred ledger → **G2**.
- The full selection-routing + calc-dispatch constant tables → **G3**.
- Per-family pickup/delay formulas + the field-trust matrix → **G4**.
