# G3 — Routing Guide (Selection routing + Calc-dispatch routing)

> **Owns:** how a TCC request *routes* — first through **selection** (the breaker/trip-unit cascade,
> the breaker→trip-unit stitch, the cross-filter contract + the deployed API routes) and then through
> **calc-dispatch** (which `DatSensor` column casts to which engine enum, and which formula/table that
> enum selects per element). Cite this guide when building or altering a selection flow or a calc dispatch.
>
> **Status:** DRAFT — agent-authored 2026-05-31; **routing validated against the `EasyPower.DeviceLibrary` primary source 2026-05-31 (Desktop)**
> **Last validated · 2026-05-31 (vs `DevLibBreaker*`/`DevLibTrip*`/`DevLibTMTFrameSize`/`SSTSensorRecord`/`ManufacturerAliases` source) · Desktop · Open gaps:**
> - Pickup/delay routing constant tables are `[DLL]`-sourced (engine mirror) but **not yet re-queried
>   row-for-row against live `tcc.*`** for this guide → `[OPEN-VALIDATION]`.
> - Cross-filter "fix path" (reload 4 dropped bridge columns + new bridge surface) — **✅ SHIPPED 2026-06-01**
>   (D1 migration `006` + `bridge_only`/`bridge_xfilter`/`/etu/bridge-sensors`; see A3c). `[VERIFIED-LIVE 2026-06-01]`
> - EMT calc-dispatch routing (does an EMT trip ever route through `SSTCalcMethod`/`SSTDelayCalc`?) is
>   unmapped → `[OPEN-VALIDATION]` (cross-ref G0 §5 EMT open edge).
> - `SSTCalcMethod` values **8/9/10** (GFPU/MULTWTH/STPU) are declared but not dispatched in the managed
>   amps switches (native-side / reserved) → `[OPEN-VALIDATION]`.

Provenance tags follow the index convention (`[VERIFIED-LIVE <date>]`, `[DLL <file:line>]`, `[DVL-DB]`,
`[HANDOFF]`, `[INFERENCE]`, `[DEFERRED]`, `[OPEN-VALIDATION]`). **Engine source (`[DLL]`) outranks DB
description (`[DVL-DB]`) outranks inference.** Discovery-artifact citations are `[03]`/`[02]`/`[05]`/`[09]`.

---

# Part A — Selection routing

## A1. The cascade hierarchy per family (cross-ref G0)

Selection always begins on **one axis** (the breaker hardware axis *or* the trip-unit axis) and drills
down. The family determines whether the breaker axis hands off to a separate trip cascade (ETU), terminates
in its own frame (TMT), or is browsed as its own catalog (EMT). All SQL below lives in one assembly,
`EasyPower.DeviceLibrary`. `[DLL 03 §1.1]`

### A1a. ETU / SST trip-unit cascade (the trip axis)

`Manufacturer → Type → Style → Sensor`, all keyed on `DatStyle.STYLE_ID = DatSensor.StyleID` (the manufacturer
link is `Manufacturers.ID = DatStyle.MFG_ID`). `[DLL DevLibTripSensor.cs:13/414]` `[DLL 03 §1.3]` `[02 E17–E30]`

| Step | Getter (DeviceLibrary) | SQL spine | Source |
|---|---|---|---|
| Manufacturer | `GetTripManufacturers` | `Manufacturers JOIN DatStyle ON Manufacturers.ID = DatStyle.MFG_ID` (DISTINCT `Mfr_Name`) | `[DLL 03 §1.3]` |
| Type | `GetTripTypes(mfr)` | + `WHERE Mfr_Name=@ ` (DISTINCT `DatStyle.Type`) | `[DLL 03 §1.3]` |
| Style | `GetTripStyles(mfr,type)` | + `AND DatStyle.Type=@` (DISTINCT `DatStyle.Style`) | `[DLL 03 §1.3]` |
| **Sensor** | `GetTripSensors(mfr,type,style)` | `… DatStyle JOIN DatSensor ON DatStyle.STYLE_ID = DatSensor.StyleID WHERE Mfr/Type/Style ORDER BY SensorValue, SensorDesc` | `[DLL DevLibTripSensor.GetTripSensors]` `[03 §3 step 5]` |
| (plugs) | `GetTripPlugs(…,sensorDesc)` | `DatPlugs JOIN DatSensor … WHERE SensorDesc=@ ORDER BY PlugVal` — **downstream output, not an upstream selector** | `[DLL 03 §3 step 6]` `[HANDOFF sst-filter-workflow-implementation]` `[05 #12]` |

> **`STYLE_ID` wins, `DatTrip.TRIP_ID` is dead.** The shipping runtime joins `DatStyle.STYLE_ID =
> DatSensor.StyleID` everywhere; `DatTrip`/`TRIP_ID` appear **0 times** in the decompiled business code.
> The `DatTrip.TRIP_ID = DatSensor.TRIP_ID` join in the *saved Access queries* (`02 E30`) is legacy/dead
> relative to the runtime — do not model on it. `[DLL 03 §4]` `[02 §0.2]`

### A1b. Breaker cascade (the breaker hardware axis)

`Manufacturer → Class → Breaker(Type) → Style`. Class is the hard-coded enum `ICCB / MCCB / PCB`; each class
has its own `Breaker<Class>` + `Breaker<Class>Styles` pair. `[DLL FindMatchingBreakerStyles DeviceLibrary.cs:403]`
`[02 E1–E10]` `[HANDOFF runtime-013]`

```sql
-- FindMatchingBreakerStyles (one template, retargeted per class)
SELECT DISTINCT Manufacturers.Mfr_Name, {BreakerXXX}.Type, {BreakerXXXStyles}.Style
FROM (({BreakerXXXStyles} INNER JOIN {BreakerXXX} ON {BreakerXXX}.ID = {BreakerXXXStyles}.BreakerID)
      INNER JOIN Manufacturers ON Manufacturers.ID = {BreakerXXX}.Mfr_ID)
WHERE {BreakerXXX}.ACDC = {0|1}
```
`{BreakerXXX} ∈ {BreakerICCB, BreakerMCCB, BreakerPCB}`. `[DLL DeviceLibrary.cs:403]` The style-list builder
additionally SELECTs the bridge columns (`TMT_Use_SST, TMT_SST_Mfr/Type/Style` + class-specific `TMT_Thermal(Magnetic)`)
— see A2. `[DLL DevLibBreakerStyle.GetBreakerStyleListSql]` `[03 §1.3]`

### A1c. TMT frame path (the breaker style *is* the trip)

When the breaker style is thermal-magnetic (`TMT_Use_SST = 0`), there is no separate trip cascade; resolution
continues on the **breaker-style PK** into the frame tables. `[DLL DevLibTMTFrameSize.cs]` `[03 §5]` `[G0 §4]`

`BreakerXXXStyles.ID → Breaker_TMTFrameSizes.StyleID → Breaker_TMTFrameAmps.FrameSizeID / Breaker_TMTFrameSettings.FrameSizeID`

```sql
SELECT ID, FrameSize, FrameDesc, Ordinal, Sec2DiscCont, Sec2PickupCalc, Sec2StepSize
  FROM Breaker_TMTFrameSizes WHERE StyleID = @StyleID ORDER BY Ordinal      -- frames for a style
SELECT * FROM Breaker_TMTFrameAmps     WHERE FrameSizeID = @FrameSizeID ORDER BY TripAmp   -- trip amps
SELECT * FROM Breaker_TMTFrameSettings WHERE FrameSizeID = @FrameSizeID ORDER BY fSetting  -- inst settings
```
`ConvertQueryByClass(brkClass, query)` rewrites the literal `"MCCB"` → `"ICCB"`/`"PCB"` so one template serves
all three classes for frame-by-(frame,trip) lookups (`ReadTmgnFrameIdsMatchingFrameAndTrip`). `[DLL DeviceLibrary.cs:1322/1380]` `[03 §5]`

### A1d. EMT facets (own catalog)

EMT is browsed via its own facet axes — `manufacturers / type_names / style_names / frame_descriptions /
trip_chars / trip_plugs` — over `EMT / EMT_Frames / EMT_Sections / EMT_Curves`, **not** via `BreakerXXXStyles`.
Whether a breaker selection ever resolves to an EMT trip is the one open selection edge. `[HANDOFF runtime-013]`
`[G0 §5]` `[OPEN-VALIDATION]`

---

## A2. The GetDefaultTripInfo stitch (breaker style → trip seed)

**This is the app-code bridge** that makes "pick a breaker, get its compatible trip" work — and the thing
that was lost when the bridge columns were dropped (G0 §3, A3 below). It is **application code, not SQL**:
no join links the breaker tables to `DatStyle/DatSensor`; the connection is four string properties carried in C#.
`[DLL 03 §2]` `[02 §0.2]` `[HANDOFF contract-dll-authority-revision]` `[05 #6]`

**Mechanism (the exact chain):** `[DLL DevLibBreakerStyle.cs:135-139]` `[DLL DeviceLibrary.cs:478]` `[03 §2.1–2.3]`

1. `DevLibBreakerStyle.GetBreakerStyles(...)` reads each breaker-style row, binding the 4 bridge columns onto
   model properties:

   | Breaker-style column | Model property | Type |
   |---|---|---|
   | `TMT_Use_SST` | `DefaultUseSST` | bool (the gate) |
   | `TMT_SST_Mfr` | `DefaultTripManufacturer` | string |
   | `TMT_SST_Type` | `DefaultTripType` | string |
   | `TMT_SST_Style` | `DefaultTripStyle` | string |
   | `TMT_Thermal` (ICCB) / `TMT_ThermalMagnetic` (MCCB) | `TMTThermalMagnetic` | int → `TMTUseInstantaneous = (==0)` |

2. `DeviceLibrary.GetDefaultTripInfo(acdc, class, brkMfr, brkType, brkStyle, out defaultUseSST,
   out defaultTripManufacturer, out defaultTripType, out defaultTripStyle)` surfaces those four values. `[DLL DeviceLibrary.cs:478]`

3. **Gate on `defaultUseSST`:**
   - `true (TMT_Use_SST=1)` → the three `Default Trip*` strings **re-seed the ETU trip cascade** (A1a) as
     `@Mfr_Name/@Type/@Style`; the matching `DatStyle(TYPE,STYLE)` rows are pre-selected → `STYLE_ID` →
     `DatSensor.StyleID`. The name-composite join is `TMT_SST_Mfr = Manufacturers.Mfr_Name`,
     `TMT_SST_Type = DatStyle.TYPE`, `TMT_SST_Style = DatStyle.STYLE` (with `DatStyle.MFG_ID = Manufacturers.ID`). `[G0 §3]`
   - `false (TMT_Use_SST=0)` → route to the TMT frame path (A1c) on `BreakerXXXStyles.ID`; the `TMT_SST_*`
     strings are not used to drive a `DatSensor` lookup. `[03 §2.3]`

> **Why this isn't a saved query:** a full-text grep of all 33 saved Access queries for `TMT`/`Use_SST`/
> `SST_Mfr/Type/Style` returns **0 matches**; the queries only populate the two *endpoints* (breaker styles
> via `devices*Breakers.sql`; trip styles via `devicesSST.sql` → `DatStyle.TYPE/STYLE`). EasyPower stitches
> them at runtime in C#. `[02 §0.2 / §3]`

**Worked example (the UI case):** breaker `T8V-1600` (`BreakerICCBStyles` id 44551, `TMT_Use_SST=1`,
SST = ABB / PR332/P / ICCB-LSIG) → exactly **1 `DatStyle`** (STYLE_ID 1230) → **5 `DatSensor`** + 18 plugs —
versus the 117 ABB trips a manufacturer-only filter offers. `[VERIFIED-LIVE 2026-05-31]` `[G0 §3]`

---

## A2a. Manufacturer alias reconciliation (a name means different things per catalog)

A manufacturer's name is **not constant across catalogs** — the breaker-hardware name, the per-class
LV-breaker names (LVPCB / ICCB / AC-MCCB / DC-MCCB), the SST (trip) name, and the HV name can each differ.
EasyPower carries an explicit in-code alias table to reconcile them; a naive exact-string match misses
legitimate equivalences. `[DLL ManufacturerAliases.cs:67-119]` `[DLL ManufacturerAliasNames.cs]`

| Preferred | LVPCB | ICCB | MCCB (AC) | **SST (trip)** | HV |
|---|---|---|---|---|---|
| Allis-Chalmers | Allis Chalmer | — | — | Allis-Chalmers | Allis Chalmer |
| BBC | Brown Boveri | — | — | BBC | Brown Boveri |
| Cutler-Hammer | Cutler-Hammer | Cutler-Hammer | Cutler Hammer | Cutler-Hammer | C-H |
| English Electric | English Elect | — | — | — | — |
| Federal Pacific | Fed Pacific | — | Fed Pacific | Federal Pacific | Fed Pacific |
| Siemens-Allis | Siemens Allis | — | — | — | Siemens Allis |
| Square D | SQD | SQD | SQD | Square D | SQD |
| Westinghouse | West | West | West | **West** | West |

Resolver methods: `GetPreferredName(name)`, `GetLVBreakerName(acdc, class, name)`, and the bridge-relevant
**`GetLVBreakerSSTName(name)`** (breaker → SST name). `[DLL ManufacturerAliases.cs:10-65]`

> **Bridge relevance:** the SST-side join `TMT_SST_Mfr = Manufacturers.Mfr_Name` (A2 / G0 §3) works because
> `TMT_SST_Mfr` is already stored in the **SST namespace** (e.g. Westinghouse's SST name is `West`). A reload
> of the bridge columns (A3c) must preserve `TMT_SST_Mfr` **verbatim**, and for robustness against the ~3–5%
> catalog-gap residual should resolve names through this alias table rather than exact-match only.
> `[INFERENCE from ManufacturerAliases + 04 join match-rates]`

---

## A3. The cross-filter contract (current state, ceiling, fix path)

### A3a. Legacy default — manufacturer-axis IN-subquery, both directions *(superseded by the opt-in bridge-aware filter — see A3c, shipped 2026-06-01; this manufacturer-only path is retained as the default so the explorer is untouched)*

When both the breaker half and the trip-unit half carry a selection, each cascade narrows the other by a
single shared axis — **manufacturer only**: `[HANDOFF stage1-slice-gamma]` `[05 #28]`

```
-- trip-unit cascade narrowed by an active breaker-half selection
… WHERE manufacturer_id IN (SELECT manufacturer_id FROM etu_breaker_combined WHERE <breaker filters>)
-- breaker cascade narrowed by an active trip-unit selection
… WHERE manufacturer_id IN (SELECT manufacturer_id FROM vw_trip_unit_cascade WHERE <trip filters>)
```

- `etu_breaker_combined` = UNION-ALL of `tcc_brk_iccb/mccb/pcb` (mirrors `FindMatchingBreakerStyles`, A1b). `[HANDOFF stage1-slice-alpha]` `[05 #23]`
- `vw_trip_unit_cascade` = the trip-unit/sensor cascade view backing `/cascade`. `[HANDOFF sst-filter-workflow-implementation]` `[05 #12]`
- Both halves are **family-distinct (Gap 5)**: ETU SQL never references TMT/EMT tables. `[05 #28]`

### A3b. The structural ceiling — why it stops at manufacturer

`vw_trip_unit_cascade` has **19 columns, all trip-unit/sensor-side, ZERO breaker-style columns** (no
`breaker_id` / `breaker_name` / `breaker_class` / `breaker_style_id`). There is **no live column to join
breaker-style → sensor on**, so the only shared axis is `manufacturer_id`. This is the "no deeper structural
cross-filter, within the persisted schema's structural ceiling" ruling. `[VERIFIED-LIVE 2026-04-29, HANDOFF
sst-remaining-gap-scoping Inspection 1]` `[05 #20/#28]`

**Root cause = dropped columns.** The 4 bridge columns (`tmt_use_sst`, `tmt_sst_mfr/type/style`) are **NOT**
in `tcc.brk_*_styles` today — dropped at load (a loader expecting a numeric `Manufacturers.ID` FK silently
dropped a name-composite key). The ceiling is therefore *recoverable*, not inherent. `[VERIFIED-LIVE 2026-05-31]`
`[HANDOFF schema-augmentation-lane1 / sst-breaker-trip-unit stage1-slice-gamma]` `[G0 §3]` `[05 §4]`

### A3c. The fix path — ✅ SHIPPED 2026-06-01

**All three steps below are DONE** (D1 + the LV-wiring lane; handoff `2026-06-01-lvbreakertcc-live-wiring-closeout`). The ceiling is lifted from manufacturer-axis to true breaker-style→sensor narrowing, **bidirectional and opt-in**: `[VERIFIED-LIVE 2026-06-01]`
- `tcc.vw_breaker_sst_bridge` (BG-4) is the new bridge surface; **`GET /etu/bridge-sensors`** narrows a breaker style → its compatible ETU sensors directly (`?breaker_style_id&breaker_class`).
- **`bridge_only`** on `/etu/breaker-cascade` restricts the ETU breaker list to ETU-capable breakers (MCCB 640→130).
- **`bridge_xfilter`** on `/cascade` + `/etu/breaker-cascade` makes the cross-filter **bridge-compatibility-aware both directions** (130 trip styles→1, 1562 breakers→4), replacing the manufacturer-axis IN-subquery. The legacy manufacturer-only path is the default (explorer untouched).
- **Per-class id hazard:** breaker / style ids are per-class serials that OVERLAP across ICCB/MCCB/PCB — every bridge filter keys on the **`(class, id)` PAIR** (see G1). A bare id-only filter cross-matches classes (e.g. style `1510` = MCCB *DT 510* + PCB *MPS-C-2000*).

The original plan, now executed: `[INFERENCE→VERIFIED-LIVE]` from `[05 §4]` + `[G0 §3]`
1. **Re-load the 4 dropped columns** (`TMT_Use_SST`, `TMT_SST_Mfr/Type/Style`) onto `tcc.brk_*_styles`,
   carrying the **`TMT_SST_*` name-composite verbatim** (do not coerce to a numeric FK — that drop is what lost it).
2. **Add a new bridge surface** (e.g. `vw_etu_breaker_contract_bridge`) — the bridge **cannot** be bolted onto
   `vw_trip_unit_cascade` because that view has no breaker-style column (A3b). This is gate 4 of the program's
   pre-registered 5-gate acceptance list; gate 3 ("prove a real breaker-style → `STYLE_ID`/sensor mapping")
   is **answered** by the `TMT_SST_*` stitch (A2); staging-table gates 1–2 are likely **moot**. `[05 §3/§4]`
3. Gate it on a product-direction decision (the named reopen-trigger for "breaker-side hierarchy ownership").
   A field-tolerance MVP needing breaker→compatible-sensor narrowing is a concrete trigger. `[HANDOFF sst-remaining-support-surfaces-audit]` `[05 #22]`

> Family-distinct (Gap 5) is **not** violated by the fix: the stitch is *within* the breaker/`DatStyle`/`DatSensor`
> family, not a TMT/EMT cross-reference. `[05 §4]`

### A3d. Deployed API routes

| Route | Half / family | Backing surface | Cross-filter behavior |
|---|---|---|---|
| `/cascade` | trip-unit (ETU) | `vw_trip_unit_cascade` | accepts breaker-half filters; manufacturer-axis IN-subquery by default, **`?bridge_xfilter=true` → bridge-compatibility narrowing** (sensors in `vw_breaker_sst_bridge` for the breaker scope) `[VERIFIED-LIVE 2026-06-01]` |
| `/etu/breaker-cascade` | breaker (ETU) | `etu_breaker_combined` (`tcc_brk_*`) | accepts trip-unit filters; manufacturer-axis by default, **`?bridge_xfilter=true` → bridge narrowing** ((class,style) pairs in the bridge for the trip scope); **`?bridge_only=true` → only ETU-capable breakers**; `?acdc=0\|1` truthful filter `[VERIFIED-LIVE 2026-06-01]` `[05 #10/#24/#28]` |
| `/etu/bridge-sensors` | breaker→ETU (D1) | `tcc.vw_breaker_sst_bridge` | **NEW 2026-06-01.** `?breaker_style_id&breaker_class` → the compatible ETU sensor set for a breaker style (the one-way crosswalk Screen 1 consumes); `bridge_match_status=unmatched` ⇒ fall back to manufacturer axis / search `[VERIFIED-LIVE 2026-06-01]` |
| `/tmt/facets` · `/tmt/frames` | TMT | `_TMT_BROWSE_SQL` (3-CTE) + `tcc_tmt_*` | facet co-population; plot is nominal-class curve (setting validated, not applied) `[05 #1/#3]` |
| `/emt/facets` | EMT | `tcc_emt_*` | own-catalog facets; bounded to frame/context/section-settings/plot `[05 #2/#3]` |
| `/plot-tcc` | all | calc engine | consumes the resolved sensor/frame record; curves generated at calc-time, never user-selected `[05 #12]` |

---

# Part B — Calc-dispatch routing

Once a sensor (ETU) is resolved, `DeviceLibrary.ReadSSTSensorRecordBySensorId(sensorId)` reads 13 columns off
`DatSensor` and **casts** them to engine enums on the `SSTSensorRecord`. The cast targets are the routing
authority. `[DLL DeviceLibrary.cs:1138-1159]` `[03 §1.3 read-back]` `[09 §1a/§2a]`

```sql
SELECT SensorValue, SensorDesc, SEC1_LTF, DS1_PICKUP_CALC, SEC3_STF, DS3_PICKUP_CALC,
       INST_FUNC, DS4_PICKUP_CALC, SEC2_LTF, DS3_SEC3_I2T, SEC1GF_GFF,
       DS1GF_PICKUP_CALC, DS1GF_SEC3_I2T
FROM DatSensor WHERE SensorId = {sensorId}
```

## B1. Pickup routing — `DS*_PICKUP_CALC` → `SSTCalcMethod` (`DVL_SST_SETTING_*`, −1..10)

Each pickup element reads its own `DatSensor` column, cast to the `SSTCalcMethod` enum; the enum value selects
the amps formula in `SSTSensorRecord.Calculate*Amps`. Provenance: enum names `[DLL SSTCalcMethod.cs:3-17]`;
literal values `[DLL DeviceLibrary.cs:37-59]`; formulas `[DLL SSTSensorRecord.cs:44-216]`; column→property
`[DLL DeviceLibrary.cs:1140-1159]` `[09 §1/§1a]`.

**Which column feeds which element:**

| DatSensor column | `SSTSensorRecord` property | Element |
|---|---|---|
| `DS1_PICKUP_CALC` | `LtpuCalcMethod` | **LTPU** (long-time pickup) |
| `DS3_PICKUP_CALC` | `StpuCalcMethod` | **STPU** (short-time pickup) |
| `DS4_PICKUP_CALC` | `InstCalcMethod` | **INST** (instantaneous pickup) |
| `DS1GF_PICKUP_CALC` | `GroundCalcMethod` | **GF** (ground-fault pickup) |

> Also `SSTCalcMethod`-typed in the native engine but **not read by the managed library**: `SETTING_TYPE`
> and `DS4_OVR_CALC` (INST override). Their authoritative legend is, by inheritance, this same table. `[09 §1a/§4f]`

**The value → formula table** (`setting` = the picklist/continuous value; `SensorValue` = sensor/frame rating;
`plug` = plug/tap; `mult` / `ltpuSetting` / `ltpuAmps` as named): `[09 §1]`

| Value | Constant | Amps formula (managed) |
|---:|---|---|
| **−1** | `DVL_SST_SETTING_NONE` | element absent / N/A (no calc) |
| **0** | `DVL_SST_SETTING_SENSORFRAME` | `setting × SensorValue` |
| **1** | `DVL_SST_SETTING_PLUGTAP` | `setting × plug` |
| **2** | `DVL_SST_SETTING_SENSORFRAME_MULT` | `setting × SensorValue × mult` |
| **3** | `DVL_SST_SETTING_PLUGTAP_MULT` | `setting × plug × mult` |
| **4** | `DVL_SST_SETTING_LTPU` | `setting × ltpuAmps` (tracks computed LTPU amps) |
| **5** | `DVL_SST_SETTING_SENSORFRAME_C` | `setting × ltpuSetting × SensorValue` (cascaded) |
| **6** | `DVL_SST_SETTING_PLUGTAP_C` | `setting × ltpuSetting × plug` (cascaded) |
| **7** | `DVL_SST_SETTING_AMPS` | `setting` (already primary amps; identity) |
| **8** | `DVL_SST_SETTING_GFPU` | GF-pickup variant — **declared, not dispatched** in managed switch (native/reserved) `[OPEN-VALIDATION]` |
| **9** | `DVL_SST_SETTING_MULTWTH` | "mult-with" — maps to **0.0** in `CalculateInstAmps` (no managed formula) `[OPEN-VALIDATION]` |
| **10** | `DVL_SST_SETTING_STPU` | STPU-relative variant — **declared, not dispatched** in managed switch `[OPEN-VALIDATION]` |

> Only `NONE, SENSORFRAME, PLUGTAP, [SENSORFRAME|PLUGTAP]_MULT, [SENSORFRAME|PLUGTAP]_C, LTPU, AMPS` appear in
> the managed amps switches. `GFPU(8)/STPU(10)` route native-side; `MULTWTH(9)` is explicit 0.0. `[09 §1 note]`

## B2. Delay routing — `DS*_SEC3_I2T` → `SSTDelayCalc` (`DB_SST_DLCALC_*`, 0..4)

Short-time and ground delays route on the (misleadingly named) `*_SEC3_I2T` columns, cast to the `SSTDelayCalc`
enum; the value selects the delay table the engine reads. Provenance: values `[DLL DeviceLibrary.cs:67-75]`;
named enum members in use `[DLL DeviceLibrary.cs:1220/1230/1279/1299]`; table routing `[DLL DeviceLibrary.cs
ReadStpuDelay 1215-1272 / ReadGroundDelay 1274-1302]` `[09 §2/§2a/§2b]`.

**Which column feeds which element:**

| DatSensor column | `SSTSensorRecord` property | Element |
|---|---|---|
| `DS3_SEC3_I2T` | `StpuDelayCalc` (= `I2TCalcMethod`) | **STD** (short-time delay) |
| `DS1GF_SEC3_I2T` | `GroundDelayCalc` | **GFD** (ground-fault delay) |

**The value → routing → table:** `[09 §2]` `[DLL DeviceLibrary.cs ReadStpuDelay/ReadGroundDelay]`

| Value | Constant | Routing | Table the engine reads (STD path · GFD path) |
|---:|---|---|---|
| **0** | `DB_SST_DLCALC_NONE` | no delay-calc / I2T Out=0/In=1 fixed bands | `DatSection3STD` · `DatSection1GfGFD` |
| **1** | `DB_SST_DLCALC_I2X` | I^x·t thermal slope (via STD `i2x`/`exp_x`) | `DatSection3STD` · `DatSection1GfGFD` |
| **2** | `DB_SST_DLCALC_INVEQ` | inverse-equation (computed curve) | `DatSection3InvEq` · `DatSection1GfInvEq` |
| **3** | `DB_SST_DLCALC_TUSTD` | GE TU STD / Enteliguard — **no selectable I2T; skip** | (none — "Enteliguard not supported" log path) |
| **4** | `DB_SST_DLCALC_TUG` | GE TU ground family | (ground delay path) |

**Dispatch summary (`ReadStpuDelay` / `ReadGroundDelay`):** `2 → InvEq` table; `3 → skip` (no table access);
`0/1/4 → default` band table (`DatSection3STD` / `DatSection1GfGFD`, `ORDER BY Ordinal`). `[DLL 03 §1.3 / DLL_END_TO_END_MAPPING §6/§9]`

**Live value distributions** (all 17,831 sensors, no NULLs) — note neither column actually spans the full 0..4:
`DS3_SEC3_I2T ∈ {0:4364, 1:8708, 2:4524, 3:235}` (no 4); `DS1GF_SEC3_I2T ∈ {0:9933, 1:5976, 2:1713, 4:209}`
(no 3). `[VERIFIED-LIVE — DLL_SEMANTIC_FINDINGS §1/§2]` `[OPEN-VALIDATION: not re-queried against tcc.* for this guide]`

> **Persisted columns:** `DS3_SEC3_I2T` → `tcc.etu_sensors.stpu_delay_calc_code`; `DS1GF_SEC3_I2T` →
> `tcc.etu_sensors.ground_delay_calc_code` (Phase 5 Tier A renames; values/lineage unchanged). `[HANDOFF Phase 5 Tier A]`

### B2a. The "two 3s" caveat (do not conflate)

There are **two different "3"s** in the delay path; reading one as the other mis-routes:
- **Routing-mode value `3` = `DB_SST_DLCALC_TUSTD`** — a *value* of the `SSTDelayCalc` enum stored in
  `DS3_SEC3_I2T`; it means "GE TU STD, skip, no selectable I2T." `[09 §2]`
- **`nSection` / "Section 3" = the short-time section table-selector** — the *positional argument* identifying
  which `DatSection<n>` family is being read (Section 3 = short-time = `DatSection3STD/STP/InvEq`). This "3" is
  table addressing, **not** a routing value. `[INFERENCE from 03 §1.3 section-table layout + 09 §2]`

A `DS3_SEC3_I2T = 3` is **routing TUSTD**, not "use Section 3." The column name's embedded `SEC3` + the value
`3` colliding is the trap. `[09 §2]`

### B2b. The DB-says-"0 or 1", engine-is-0..4 trap (flagship)

`DS3_SEC3_I2T` and `DS1GF_SEC3_I2T` are **described "0 or 1"** in the Access field metadata, but the engine
**casts them to the full 0..4 `SSTDelayCalc` routing enum.** The "I2T" suffix is also misleading — these are
not I²t booleans; they are delay-curve routing codes. Per the conflict rule, **engine source wins**: treat
them as 0..4 routing enums and record the DB description as incomplete/misleading. Two independent managed
consumers prove the 0..4 cast (`ReadSSTSensorRecordBySensorId` projection + `DevLibTripSensor.GetI2TSettings`
switching on cases 0/1/2/3/4). `[DVL-DB DatSensor.DS3_SEC3_I2T → "0 or 1"]` `[DLL DeviceLibrary.cs:1140/1156/1159;
DevLibTripSensor.cs:265-286]` `[09 §2a/§5]`

> Distinct from the routing enum: the per-row **I2T in/out** state (`DB_SST_I2T_*`: 0=OUT, 1=IN, 2=BOTH) is the
> *byte emitted in the I2T pick-list* once a family is chosen — it is **not** the `*_SEC3_I2T` routing value.
> The `*_SEC3_I2T` column chooses the family; the 0/1/2 in/out chooses within it. `[09 §4b]`

### B2c. When short-time pickup / I2T settings apply (the `STP_TRACKS` gate)

Whether a sensor even *exposes* a short-time pickup and an I2T in/out choice is gated by more than the route
value — two extra `DatSensor` columns decide it: `[DLL DevLibTripSensor.cs:61-97, 258-294]`
- `DS3_STP_TRACKS` → `ShortTimePickupTracks`.
- **`UseShortTimePickup`** = `DS3_PICKUP_CALC ≠ -1` **and** `DS3_STP_TRACKS ≠ 1`.
- **`ShortTimePickupBasedOnInst`** = `DS3_STP_TRACKS == 1` — STPU **tracks INST** (derived from the instantaneous, not set independently).
- **`UseI2TSetting`** = `UseShortTimePickup` **and** `DS3_SEC3_I2T ≠ 3` (TUSTD exposes no I2T choice).
- I2T pick-list (`GetI2TSettings`): route `0` → {Out=0, In=1}; route `3` → {`<None>`}; routes `1/2/4` → Out/In present only where `HasShortTimeDelays`. `[DLL DevLibTripSensor.cs:265-294]`

**The actual STD-band filter** (how delay-band rows are chosen once In/Out is set):
- non-INVEQ: `DatSection3STD WHERE I2X = @InOut OR I2X = 2 OR (0 = @InOut AND I2X IS NULL)`
- INVEQ (route 2): `DatSection3InvEq WHERE InOut = @InOut OR InOut = 2`

(`I2X` / `InOut = 2` is the **BOTH** wildcard.) `[DLL DevLibTripSensor.cs:23, 25, 311]`

## B3. Polarity-not-uniform warning (discrete/continuous flips between tables)

The discrete/continuous flag does **not** share a polarity across the schema — engine code must branch per table: `[DVL-DB]` `[08 §16, §211-213]` `[09 §3a]`

| Column(s) | Table family | Polarity |
|---|---|---|
| `SEC1_LTF`, `SEC2_LTF`, `SEC3_STF`, `INST_FUNC`, `SEC1GF_GFF` | `DatSensor` (ETU) → `ContinuousSettings` | **`0 = Discrete`, `1 = Continuous`** |
| `EMT_Sections` disc/cont, `EMT.PickupSetting` | EMT | **`0 = Discrete`, `1 = Continuous`** (same as DatSensor) |
| `RelaySec2TCP.Discrete` | Relay | **`1 = discrete`, `0 = continuous`** — **INVERTED** |

> **The trap:** `DatSensor`/`EMT` use `0=Discrete/1=Continuous`, but `RelaySec2TCP.Discrete` is the opposite
> (`1=discrete/0=continuous`). Any code reading a disc/cont flag must branch on which table it came from; a
> single shared decoder will mis-classify relay rows. `[08 §16]` `[09 §3a]`

The ETU disc/cont columns also route through `ReadSSTSensorRecordBySensorId` onto
`LtpuDiscCont/StpuDiscCont/InstDiscCont/LtdDiscCont/GroundDiscCont` (cast to `ContinuousSettings`,
`DVL_DISCRETE=0/DVL_CONTINUOUS=1`). `[DLL DeviceLibrary.cs:1149-1157]` `[09 §3]`

---

## Cross-references
- The three families + the breaker×family interaction matrix (and the EMT open edge) → **G0**.
- Schema of every table/column named here + the **dropped-column register** (the 4 bridge columns) → **G1**.
- Governance of the cross-filter fix path (reopen-trigger, frozen baselines, deferred ledger) → **G2**.
- The pickup/delay **formulas** themselves + tolerance derivation + the field-trust matrix → **G4**.
