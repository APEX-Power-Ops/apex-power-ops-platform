# G4 — Calc Guide (Pickup · Tolerance · Delay/Curve Solvers · the Field-Trust Matrix)

> **Owns:** the math and the trust. For any element of an ETU/SST trip — LTPU/STPU/INST/GFPU — this
> guide says *which formula computes its pickup, where its tolerance comes from, which solver draws
> its delay/curve, and whether the resulting number is trustworthy enough to hand a NETA technician.*
> The centerpiece is **§4 — the Field-Trust Matrix** (`PROVEN | BOUNDED | DEFERRED | STUB`). Every
> packet that computes or ships a pickup/delay/tolerance value cites this guide.
>
> Status: DRAFT — agent-authored 2026-05-31; **pickup formulas validated against `SSTSensorRecord` primary source 2026-05-31 (Desktop)**
> Last validated · 2026-06-01 (pickup formulas vs `SSTSensorRecord.cs`; enum vs `SSTCalcMethod.cs`; INVEQ loader reconciled vs pass-2..5; INVEQ managed-evaluator characterized live + corpus distribution measured — §3e; GF-InvEq ANSI cohort re-measured (100 rows / 23 sensors / 3 styles) + hard-excluded; Therm `CalcThermEq` recovered from `TccBase.dll` + patched; **STD-INVEQ Therm parity CLOSED by native-kernel EXECUTION — `TccBase.dll` `CalcThermEq`/`CalcThermEq3` invoked in-process, STD reproduced BIT-EXACT over the complete 4-dial corpus → PROMOTED to "db"; secondary `*ICalc=0` residual CLOSED (zero rows) — §3f**) · **L1 CLOSED 2026-06-09 (STATE §206): `field[13]` = the PLUG rating (In) — slot map banked via ComputeAmps cross-ref; GF-INVEQ Therm plug-basis (`rIRef' = rIRef × plug/pickup`) BIT-EXACT vs native over the complete GF corpus (416 scenarios, maxabs 0.0) → PROMOTED "db" (~1,690 sensors); `/plot-tcc` renders the inverse (`id_*`) sub-blocks band-matched + basis-corrected** · **Native PLOT COMPOSITION recovered 2026-06-09 (STATE §209): `CPointsMergeSST/GF` boundary assembly — pickup asymptote + per-block `TrimCurveX` windows + log-log-intersection handoffs + closed open/clear band + SC-amps right clip + separate GF band — §3g; **serving lane SHIPPED 2026-06-10** (#122 `b2dfa7fd`: `/plot-tcc` `composite_bands` phase+GF open/clear staircase, ratified deviations documented in §3g)** · Open gaps: GF Ansi (100 rows / 23 sensors) formula recovered, anchors PICKUP (corrected 2026-06-09 — independent implement+validate lane), HARD-EXCLUDED meanwhile · GE-TU-STD/Gnd · I2X-255 · WEG OCR-A pickup `[STUB]` · INST `Sec4Inst*` `[DEFERRED]` · LTD `DS2_DLY_PTY` `[DEFERRED]`

---

## 0. How to read this guide (trust model in one paragraph)

A field-tolerance sheet is only as honest as its weakest computed number. This guide separates the
three things a sheet needs — a **pickup current**, a **tolerance band**, and (when applicable) a
**delay/curve point** — because they have *different trust levels*. Pickup currents are simple
arithmetic and are trustworthy. Per-element tolerances are authoritative *data* and are trustworthy.
Delay/curve numbers split sharply: the **direct-band** solvers are proven, but the **inverse-equation
(InvEq)** curve numbers are *dispatch-proven only, never numerically validated*, and several solver
families are **stubbed/deferred** and must be hard-excluded. The Field-Trust Matrix (§4) is the
single table that encodes this so no sheet ever ships an uncertified number as if it were certified.

**Conflict rule (from `00-MASTER-INDEX §2`):** engine source (`[DLL]`) outranks DB description
(`[DVL-DB]`) outranks inference (`[INFERENCE]`). Every "proven" below traces to `[DLL]` recovery
plus row-level evidence; everything weaker is tagged honestly.

---

## 1. Pickup formulas per element (`SSTCalcMethod` / `DVL_SST_SETTING_*`)

Each element's **pickup current** is computed by an arithmetic method selected by a per-sensor
`SSTCalcMethod` byte. The byte→formula table is recovered from decompiled engine source; the
DB descriptions are only a pointer ("See definitions of `DVL_SST_SETTING_*` constants…") and are
resolved here. `[DLL SSTCalcMethod.cs:3-17]` `[DLL DeviceLibrary.cs:37-59]` `[09 §1]`

### 1a. The pickup-method enum (`SSTCalcMethod`, -1..10)

| Value | Constant | Pickup formula (amps) | Dispatched in managed switch? |
|---:|---|---|---|
| **-1** | `DVL_SST_SETTING_NONE` | element absent / N/A | — |
| **0** | `DVL_SST_SETTING_SENSORFRAME` | `setting × SensorValue` | yes |
| **1** | `DVL_SST_SETTING_PLUGTAP` | `setting × plug` | yes |
| **2** | `DVL_SST_SETTING_SENSORFRAME_MULT` | `setting × SensorValue × mult` | yes |
| **3** | `DVL_SST_SETTING_PLUGTAP_MULT` | `setting × plug × mult` | yes |
| **4** | `DVL_SST_SETTING_LTPU` | `setting × ltpuAmps` (tracks computed LTPU) | yes |
| **5** | `DVL_SST_SETTING_SENSORFRAME_C` | `setting × ltpuSetting × SensorValue` (cascaded) | yes |
| **6** | `DVL_SST_SETTING_PLUGTAP_C` | `setting × ltpuSetting × plug` (cascaded plug-tap) | yes |
| **7** | `DVL_SST_SETTING_AMPS` | `setting` (already in primary amps — identity) | yes |
| **8** | `DVL_SST_SETTING_GFPU` | ground-fault variant — **not** in any managed switch (native-side / reserved) | no |
| **9** | `DVL_SST_SETTING_MULTWTH` | "multiple-with"; `CalculateInstAmps`/`…SettingFromAmps` returns **0.0** (no managed formula) | maps to 0.0 |
| **10** | `DVL_SST_SETTING_STPU` | short-time-pickup variant — **not** dispatched in managed switch | no |

`[DLL SSTCalcMethod.cs:5-16]` (names+order) `[DLL DeviceLibrary.cs:37-59]` (literal values) `[09 §1]`
Formula bodies: `[DLL SSTSensorRecord.cs CalculateLtpuAmps 44-50 / CalculateStpuAmps 95-104 / CalculateInstAmps 150-160 / CalculateGroundAmps 208-216]` `[09 §1]`

> **Caveat — values 8/9/10 are not managed-resolvable.** GFPU(8) and STPU(10) are *declared* but never
> appear in a managed amps switch (native-side), and MULTWTH(9) explicitly yields `0.0` in
> `CalculateInstAmps`. A sheet that encounters a pickup method of 8/9/10 on an element it intends to
> ship must treat the pickup as **unresolved**, not zero. `[DLL]` `[09 §1 note]`

> **Per-element dispatch subsets** — each element's `Calculate*Amps` switch handles only a *subset* of the
> enum (validated against primary source); reading the table above as "any method on any element" is wrong:
> - **LTPU** (`CalculateLtpuAmps`): `{0,1,2,3,7}` — *no* cascaded `_C` (5/6), *no* LTPU-relative (4).
> - **STPU** (`CalculateStpuAmps`): `{0,1,4,5,6,7}` — adds LTPU(4) + cascaded(5/6); *no* `_MULT` (2/3).
> - **INST** (`CalculateInstAmps`): `{0,1,4,5,6,7,9}` — the STPU set + `MULTWTH(9) → 0.0`.
> - **GF** (`CalculateGroundAmps`): `{0,1,5,6,7}` — cascaded(5/6); *no* LTPU(4), *no* `_MULT`.
>
> Each also has an inverse `Calculate*SettingFromAmps` (amps → setting) over the same per-element subset.
> `[DLL SSTSensorRecord.cs:35-252]`

### 1b. Which `DatSensor` column drives which element's pickup

From `DeviceLibrary.ReadSSTSensorRecordBySensorId` (the 13-column SELECT, array→property projection):
`[DLL DeviceLibrary.cs:1140-1159]` `[09 §1a]` `[DLL_END_TO_END_MAPPING §1]`

| Element | `DatSensor` column | `SSTSensorRecord` property | Persisted (`tcc.etu_sensors`) |
|---|---|---|---|
| **LTPU** (long-time pickup) | `DS1_PICKUP_CALC` | `LtpuCalcMethod` | `ltpu_calc` |
| **STPU** (short-time pickup) | `DS3_PICKUP_CALC` | `StpuCalcMethod` | `stpu_calc` |
| **INST** (instantaneous pickup) | `DS4_PICKUP_CALC` | `InstCalcMethod` | `inst_calc` |
| **GFPU** (ground-fault pickup) | `DS1GF_PICKUP_CALC` | `GroundCalcMethod` | `gfpu_calc` |

> `SETTING_TYPE` and `DS4_OVR_CALC` carry the *same* `DVL_SST_SETTING_*` description and are
> `SSTCalcMethod`-typed, but **neither is read by the managed library** — they are applied
> native-side (INST override). Their legend is `SSTCalcMethod` by inheritance. `[DLL]` `[09 §1a / §4f]`
>
> **`[EZPDOC]` confirms the INST override is real + user-facing (2026-05-31):** the Phase Trip help's
> **Inst "Enable Override"** = *"disables tripping based on the pickup setting; the device trips at an
> override value that depends on the device style"* — i.e. our `DS4_OVR_*` path (field-trust matrix row 12).
> And **Maint-Inst / Maint-GF** (ARMS / RELT / Quick-Trip, manufacturer-specific names) = the
> `DatSensorMaint` maintenance-mode overrides. `[EZPDOC LV_Breaker/Phase_Trip_Tab]` `[EZPDOC LV_Breaker/Ground_Trip_Tab]`
> **ETAP cross-confirms both:** the Inst Override and normal Inst pickup are **mutually exclusive** ("if
> Override is enabled, Inst pickup is grayed out and vice versa"), and Maintenance Mode applies a temporary
> low setting "to reduce arc-flash incident energy" (handled as separate curves). `[ETAPDOC LVCB_Setting]`

### 1c. Trust statement for pickup currents

**Pickup CURRENTS are simple per-sensor arithmetic (multiply a dial setting by a sensor/plug/LTPU
basis) and are PROVEN-class.** The pickup *dispatch byte* is `[DLL]`-recovered; the arithmetic is a
single multiply with no curve-solver involved. The Series B validation closed the **STPU dispatch**
(`DS3_PICKUP_CALC = 1` for all 7 sensors) and the **GFPU dispatch split** (SE=7 / MX,PX-6B=0) PASS on
real rows. `[HANDOFF task-c-safe-parity-matrix 04-27]` `[06 §matrix]` The single exception is **WEG
OCR Type A** (`DS1GF_PICKUP_CALC = 6`, §N.4) whose pickup formula is **unknown/withheld** — see §4 STUB row.

---

## 2. Tolerance derivation — authoritative per-sensor DATA (the ship-now layer)

**The per-element pickup/delay tolerances are not computed — they are authoritative per-sensor DATA
read straight off `DatSensor` (the `*_tol_hi` / `*_tol_lo` columns), loaded 1:1 into
`tcc.etu_sensors`.** Because they are data, not a solver output, **they carry no kernel-parity risk
and are the safe, ship-now layer of any field sheet.** `[DLL_END_TO_END_MAPPING §16 row 2 — DatSensor
93 cols, source-faithful 1:1 load]` `[HANDOFF TASK-008 per-sensor tolerance closed PASS 04-26]`
`[DLL_SEMANTIC_FINDINGS §5 "Sensor-level tol_hi/lo"]`

| Property | Status |
|---|---|
| **Source** | `DatSensor.*_tol_hi` / `*_tol_lo` per element (and override-specific pairs where present) `[DVL-DB]` |
| **Nature** | Stored data, source-faithful (Phase 3 rebuilt corpus loaded 1:1 from `D:\TCC_NEW.accdb`) `[DLL_END_TO_END_MAPPING §16]` |
| **Per-sensor?** | Yes — each sensor carries its own bands; **not** a global default `[DVL-DB]` |
| **Computation risk** | None — no solver, no curve arithmetic involved |

**Authority note (carries from the project record):** the field Excel that earlier used **NETA-default
tolerance bands was a SIMPLIFICATION** adopted under selection difficulty. **The DB per-sensor
tolerances are authoritative** and supersede the default bands. A field sheet must emit the
per-sensor `*_tol_hi`/`*_tol_lo`, not a canned NETA default, wherever the per-sensor values exist.
`[HANDOFF — Series B Excel was DB-derived under selection difficulty; DB per-sensor tolerances
AUTHORITATIVE (project_tcc_field_tolerances_mvp B0.1)]` `[INFERENCE — reconciles the field-Excel
simplification against the source-faithful per-sensor load]`

> **Override tolerances:** for the 3 STPU-override sensors, the override carries its **own**
> tolerance pair (`tolerance_high` positive / `tolerance_low` negative) in the EAV
> `tcc.etu_stpu_overrides`; when an override applies, use the override tolerances, not the
> sensor-level pair. `[DLL_SEMANTIC_FINDINGS §4]` `[DLL_END_TO_END_MAPPING §10]`

---

## 3. Delay/curve solvers (per `SSTDelayCalc` route)

A sensor's **delay/curve** is generated by a solver selected by the `SSTDelayCalc` routing byte. The
routing byte lives in two `DatSensor` columns — one for the short-time (STD) path, one for the
ground-fault (GFD) path — and **despite the misleading `_I2T` suffix, each casts to the full 0..4
`SSTDelayCalc` enum, NOT the DB-described "0 or 1".** This is the flagship engine-over-DB win.
`[DLL EasyPower.Types SSTDelayCalc / DeviceLibrary.cs:67-75]` `[09 §2]` `[DLL_SEMANTIC_FINDINGS §1-§2]`

> **Vendor-doc corroboration `[EZPDOC]` (2026-05-31):** EasyPower's Phase Trip help describes the ST Pickup
> **(I^x)t In/Out** control directly: *"When you select In, the (I^x)t function is enabled; the delay band
> has a slope of minus 'x'. When you select Out, the (I^x)t function is disabled and the delay is
> independent of the current."* That is the plain-English form of the `SSTDelayCalc` 0 (NONE / flat,
> current-independent) vs 1 (I2X / Iˣ·t slope) routing — the vendor confirms the "0/1" the DB *partially*
> describes, while the engine extends it to the full 0..4. `[EZPDOC LV_Breaker/Phase_Trip_Tab]` **ETAP (a
> different vendor) independently confirms the identical control** — "the short-time I^xT band has IN and
> OUT settings, **default OUT**; IN shifts the curve inward (sloped), OUT outward (L-shaped)" (same for
> Ground) — a second-vendor confirmation of the same routing. `[ETAPDOC LVSST]`

### 3a. The delay-routing enum (`SSTDelayCalc` / `DB_SST_DLCALC_*`, 0..4)

| Value | Constant | Routing / solver | Delay table read |
|---:|---|---|---|
| **0** | `DB_SST_DLCALC_NONE` | fixed-time bands (flat delay; I2T Out=0/In=1 only) | **STD:** `DatSection3STD` · **GFD:** `DatSection1GfGFD` |
| **1** | `DB_SST_DLCALC_I2X` | I²t / Iˣ·t slope family (via STD table `I2X` column) | `DatSection3STD` (filtered on `I2X`) |
| **2** | `DB_SST_DLCALC_INVEQ` | inverse-equation computed curve → **`IEEEInverseTimeSolver`** | **STD:** `DatSection3InvEq` · **GFD:** `DatSection1GfInvEq` |
| **3** | `DB_SST_DLCALC_TUSTD` | GE trip-unit STD thermal (Enteliguard "not supported" log path) | — (no selectable I2T setting; `<None>`) |
| **4** | `DB_SST_DLCALC_TUG` | GE trip-unit ground family | — (ground delay path) |

`[DLL DeviceLibrary.cs:67-75]` (values) `[DLL DeviceLibrary.cs:1220/1230/1279/1299]` (named enum members in use)
`[DLL ReadStpuDelay 1215-1272 / ReadGroundDelay 1274-1302]` (routing-to-table) `[09 §2]`

**Routing columns** `[DLL DeviceLibrary.cs:1140,1156,1159]` `[09 §2b]`:
- **STD path:** `DatSensor.DS3_SEC3_I2T` → `StpuDelayCalc` → persisted `tcc.etu_sensors.stpu_delay_calc_code` (renamed from legacy `stpu_i2t` at Phase 5 Tier A) `[DLL_END_TO_END_MAPPING §1]`
- **GFD path:** `DatSensor.DS1GF_SEC3_I2T` → `GroundDelayCalc` → persisted `tcc.etu_sensors.ground_delay_calc_code` (renamed from legacy `gfpu_i2t`) `[DLL_END_TO_END_MAPPING §1]`

**Live value distributions (all 17,831 sensors, no NULLs)** `[VERIFIED-LIVE — value distributions
recorded against the 17,831-sensor corpus]` `[DLL_SEMANTIC_FINDINGS §1 / §2]`:

| Route | STD (`DS3_SEC3_I2T`) | GFD (`DS1GF_SEC3_I2T`) |
|---|---:|---:|
| 0 NONE | 4,364 | 9,933 |
| 1 I2X | 8,708 | 5,976 |
| 2 INVEQ | **4,524** | **1,713** |
| 3 TUSTD | 235 | — |
| 4 TUG | — | 209 |

> **Do not conflate the two `3`s.** The routing byte value `3` = `TUSTD` (a mode). Separately, the
> row-reader `dvlSSTGetInvEqDelays(…, nSection, …)` takes `nSection = 3` (STD-inv table) vs `5`
> (GF-inv table) — a *table selector*, NOT the mode enum. `[06 caveat]` `[09 §2a]`

### 3b. Per-route: implemented vs proven

| Route | Solver / table | Implemented? | Numerically proven? | Evidence |
|---|---|---|---|---|
| **STD direct-band** `DS3_SEC3_I2T = 0` | `DatSection3STD` flat/Out-In bands | yes | **yes — row-for-row** | Series B SE `(10,10,2)` / MX `(6,6,1)` / PX-6B mixed; TASK-C 8/8 PASS `[06 §matrix]` |
| **GFD direct-band** `DS1GF_SEC3_I2T = 0` | `DatSection1GfGFD` bands | yes | **yes — literal anchor** | Full-SE `I_OPEN = 2000A` literal ×4 ordinals; TASK-C PASS `[06 §matrix]` |
| **I2X** route `= 1` | `DatSection3STD` Iˣt ramp + flat floor → **`CIxt` power law** (§3b·I2X) | **no — withheld** (kernel **characterized** 2026-06-03 §113) | no — pending §107 oracle parity | Kernel = `t=T_anchor·(I_anchor/M)^X`, X=`DS3_I2T_VAL` (≈2 for 98%); NOT `CalcThermEq`. ~98% = banked I²t (§4). `[§3b·I2X · §113]` |
| **INVEQ** route `= 2` (STD) | `DatSection3InvEq` → `IEEEInverseTimeSolver` | **yes — dispatch wired** | **NO — dispatch only, numbers not validated** | `*Eq=0` uniform, `*ICalc=(10,10,4,4)` integrity, `InOut∈{0,2}` switch → IEEE solver; 4,524 sensors `[06 §matrix / §synthesis-4]` |
| **INVEQ** route `= 2` (GFD) | `DatSection1GfInvEq` → `IEEEInverseTimeSolver` | **yes — full chain bound** | **NO — dispatch only, numbers not validated** | populator `FUN_01207bf0` → reader `nSection=5` → 8 setters; slot matrix BOUND ×3; `byICalc=(in==0)?2:(in==1)?1:0`; Therm/Ansi = IdOp `*Eq` byte; 1,713 sensors `[06 §matrix, pass-5]` |
| **TUSTD** route `= 3` | GE trip-unit STD | **no — fall-through diagnostic only** | no | "Enteliguard not supported", 235 sensors `[DLL_END_TO_END_MAPPING §6/§summary]` `[06 §matrix]` |
| **TUG** route `= 4` | GE trip-unit ground | **no — fall-through diagnostic only** | no | GE-TU-Gnd routing not implemented, 209 sensors `[06 §matrix]` |

**Supporting InvEq recoveries that ARE proven** (the *dispatch*, not the curve numbers):
- **`*ICalc → byICalc` translator** `FUN_01208640`: `byICalc = (in==0)?2 : (in==1)?1 : 0` → on `{1,4,8,10}` gives `1→1, 4→0, 8→0, 10→0`. **PROVEN** (native + Python verbatim). `[06 §matrix, pass-5]`
- **Slot identity** (slot1=flat-open … slot4=inverse-clear; row offsets 0x08/0x3C/0x70/0xA4). **PROVEN** (in-function MOVSS+CALL). `[06 §matrix, pass-5]`
- **Therm-vs-Ansi selector** = IdOp `*Eq` byte at row offset 0x70 (whole-row). **PROVEN.** `[06 §pass-5]`

### 3b·I2X. The route-1 Iˣt kernel — RECOVERED 2026-06-03 (`CIxt` power law, **NOT** `CalcThermEq`)

The I2X gating verification (punch-list L4 / STATE §113, tasks I2X-1+I2X-2) triangulated the **decompile +
staging DB + managed routing** and **corrects the 2026-06-02 scout hypothesis** that route-1 reused the
`CalcThermEq` polynomial. It does not. Route-1 is a **simple power law**:

> **`t(M) = T_anchor · (I_anchor / M)^X`** — equivalently `K = I_anchor^X · T_anchor`, `t = K / I^X`.

- **Kernel** = `CTccLVBreakerCurveSST`'s `CIxt` class `[DLL TccBase.dll CIxt.{ctor}/ComputeT 24248-24297]`:
  ctor stores `K = pow(I, |x|)·t`; `ComputeT(I) = K / pow(I, x)`. The `SetSTDB_{Flat,Inverse}Delay{Open,Clear}[ZSI]`
  setters `[24440-24531]` carry `(byICalc, rTmin, rX, rTref, rIref, rM)` where **`rX` = exponent X**,
  **`rIref/rTref` = the anchor (I,T)**, `rTmin` = definite-time floor — a power law, not a Therm shape.
- **Flat-vs-Inverse discriminator** = `IsSTDB_Ixt` (`bool[709]`) `[24196]`, read by `GetMin{Open,Clear}STDB`
  `[26398-26442]`: **true → Inverse block (the Iˣt ramp); false → Flat block (definite-time floor).** This is
  the native render of the `[EZPDOC]`/`[ETAPDOC]` **(I^x)t In/Out** control documented above (§3 note): In =
  sloped Iˣt ramp, Out = current-independent flat.
- **Per-band shape** = `DatSection3STD.I2X` smallint `[VERIFIED-LIVE — staging tcc-fidelity-staging, 2026-06-03]`:
  **0 / NULL = flat-only** (time = `STD_OPEN`/`STD_CLEAR`, current-independent); **1 = Iˣt-ramp-only**
  (anchor `I_OPEN`/`T_OPEN` open, `I_CLEAR`/`T_CLEAR` clear); **2 = composite** (Iˣt ramp **+** flat floor).
  Band counts: I2X 0→49,916 / 1→14,181 / 2→64,840 / 255→2 (sentinel) / NULL→10,704 rows over 10,425 sensors.
  **The anchor multiple varies per band** (top groups `I_OPEN/I_CLEAR` = 12/14.4, 10/10, 8/8, 6/6, 7/7, 7/8,
  8.3/12 …) and open≠clear — **read it from the row; do NOT hardcode 6×** (the LTD §4 model's 6× is LTD-specific).
- **Exponent X** = sensor-level `DatSensor.DS3_I2T_VAL` (STD) / `DS1GF_I2T_VAL` (GFD), active when `DS{3,1GF}_SEC3_I2T=1`.
  `[VERIFIED-LIVE]` **X = 2.0 for 8,439/8,708 STD (96.9%) and 5,953/5,976 GFD (99.6%) — ~14,392/14,684 (98%) pure I²t.**
  Variable tail ~235 (mostly x=1 linear `I·t`; a few 5.0 / 2.09 / 2.17 / 0.49 …); ~48 disabled (`-1.0` / NULL).
  This is why the family is **"I2X" = Iˣt** (variable exponent), even though the bands' `STD_DESC` read "I2T = …".

**Status / implication:** route-1 is no longer an unknown-cost RE — its kernel is the **I²t closed form already
shipped + live-verified for LTD (§4 / §111)**, generalized to a per-band anchor + sensor `X`. Punch-list L4 is
resized **L → M**. The residuals: the **I2X=2 composite combination rule** (now RECOVERED — see below) and the
~235-sensor variable-X tail. Until route-1 is promoted in `delay_trust.py`, route-1 stays **withheld** (the §6
field-trust gate holds).

**I2X=2 composite combine rule — RECOVERED 2026-06-03 (I2X-5, decompile-confirmed, NOT a guess):**
`t(M) = max( ixt_ramp(M), floor )` — the Iˣt ramp clamped below at a **definite-time floor**. Evidence chain:
- A composite band stores an **Inverse block** (the ramp: `SetSTDB_InverseDelay{Open,Clear}` 24466-24489 → slots
  185-189/192-196 = `rTmin`,`rX`,`rTref`,`rIref`,`rM`; the `CIxt` anchor is `(rIref,rTref)`, exponent `rX`) **and**
  a `rTmin` **floor**. `GetMin{Open,Clear}STDB` (26398-26442) returns that floor (the active block's `rTmin`).
- The floor is applied as a **minimum-time clamp** on the rendered curve, IDENTICALLY across every SST renderer:
  `*prMin = max(GetMin*STDB, default_slot)` then the curve is clamped at `prMin` — seen in `CalcIeeeEq2`
  (27005-27017), `CalcGESMREq2` (27251-27281), and the explicit combine lambda in `CalcThermEq2`
  (27228-27240: `return (!(rTmin > dMinTime)) ? dMinTime : rTmin` = **`max(rTmin, dMinTime)`**, with sentinel
  handling). So the composite = the `CIxt` Iˣt ramp clamped so `t ≥ floor`.
- **DB mapping:** floor = `rTmin` ← `DatSection3STD.STD_OPEN/STD_CLEAR` (prod `tcc.etu_std_bands.std_open/std_clear`),
  ramp anchor = `I_OPEN/T_OPEN` (open) `I_CLEAR/T_CLEAR` (clear), exponent = `DS3_I2T_VAL`. The evaluator already
  carries all of these (`std_open/std_clear` + `i_open/t_open/…` + `exp_x`).

So the recovered evaluator form is `i2x_composite(M) = max(ixt_time(M, i_anchor, t_anchor, x), std_floor)`.
**IMPLEMENTED 2026-06-03 (commit `apex aa9b89ea`):** `etu_ixt.i2x_delay_surface` now SUPPORTS composite (the s17
fixture carries hand-derived `max(ramp,floor)` checks — ramp dominates at low current, floor clamps at high — + a
dedicated floor-clamp test; 20 parity tests green). **Field-trust tier = `verify`** (not full `db`): the combine rule
is decompile-confirmed (the `max(rTmin,dMinTime)` lambda) and the ramp is native-bit-exact (I2X-4), but the full
native composite **render** has not been spot-checked. **Render-capture feasibility (scouted 2026-06-03):** there is
no clean per-point native evaluator — `CTccLVBreakerCurveSST.ComputeIXT` is the *inverse* (amps-from-time, →
`ComputeAmps`), so a native capture means driving a full `RecalcCurve_SSTT_LT_STDB_INST`/`RecalcCurve_STT_*` with the
complete ~2592-byte object state (heavy). → the **`verify`→`db` promotion gate** is a **captured EasyPower curve**
spot-check (the lighter path), deferred. The evaluator is **ready** but **NOT yet wired into `/calculate`** — the
STD-first wiring + the live un-withhold is the **I2X-6** step (an operator trust-flip boundary: show composite at the
`verify` tier, or hold it until the captured-curve `db` promotion).

**Evaluator built (I2X-3, 2026-06-03):** the validated managed kernel is
`packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_ixt.py` (`ixt_time` =
`t_anchor·(i_anchor/M)^|X|` mirroring native `CIxt`; `i2x_delay_surface` dispatches flat / ramp [SUPPORTED] vs
composite / unknown [WITHHELD]). Parity-proven against DB-anchored fixtures hand-derived from the decompiled
`CIxt` at binary-exact multiples (`tests/test_etu_ixt_parity.py`, 19 tests).

**Prod data state — verified 2026-06-03 (I2X-6 read, STATE §117) — CORRECTS the §113 "bands carry exp_x" claim.**
The prod band tables carry `i_open/i_clear/t_open/t_clear/i2x` (+ STD `std_open/std_clear` floor) but **NOT the
exponent**: there is **no `exp_x`/`std_x` column on `tcc.etu_std_bands`** (GFD has a partial `gfd_x`: 7,745/12,104
ramp, 0/35,522 composite). The exponent is a **SENSOR** field (`DS3_I2T_VAL`/`DS1GF_I2T_VAL`), so the `/calculate`
wiring must source X from the sensor (default `X=2` for ~98%), not the band. STD route-1 is otherwise well-populated
(ramp anchors 14,161/14,181; composite anchors 64,558/64,840 + floor 64,840/64,840 = 100%); **GFD is gappier**
(ramp 7,769/12,104 NULL anchors, no composite `gfd_x`) → wire **STD-first**, defer GFD pending a load fix.

**Native-CIxt oracle capstone DONE (I2X-4, 2026-06-03, STATE §116):** `etu_ixt.ixt_time` was confirmed
**BIT-EXACT (max 0 ULP over all 20 ramp open/clear points)** against the *actual* native `TccBase.dll`
`CIxt.ComputeT`, invoked in-process via `output/inveq-parity/oracle/ixt_oracle.exe` (the §107 oracle pattern,
`CIxt.{ctor}`+`ComputeT` by reflection; licensed DLL stays out of git). The hand-derived fixture matched native
within 1 ULP; the one 1-ULP literal was corrected → the fixture is now native-exact. So the **flat + ramp** subset
is native-grade validated (the §107 "db" bar). **Still NOT wired into `/calculate`** — the two remaining gates are
**I2X-5** (the I2X=2 **composite** combine rule — the *largest* band group at 64,840, so the bulk of route-1
coverage, not a tail — whose rule is now **RECOVERED above** as `max(ixt_ramp, std_floor)`; only its native-render
spot-check validation remains) and **I2X-6** (prod-data confirmation [needs Supabase re-auth] +
wire + trust flip [operator decision boundary]). `[G4 §3a/§3b/§4 · §113/§116 · DLL CIxt 24248-24297 / SetSTDB_*
24440-24531 / IsSTDB_Ixt 24196,26398-26442]`

### 3c. The LTD delay window (separate two-table model)

LTD (long-time delay) is **not** routed by `SSTDelayCalc`; it dispatches on a per-sensor LTD **method
1..5** in a split two-table model: `tcc.etu_ltd_params` ("how to calculate") + `tcc.etu_ltd_bands`
("what values") joined on `curve_id`. `[DLL_SEMANTIC_FINDINGS §3]` `[DLL_END_TO_END_MAPPING §4]`

| Method | Name | Status |
|---:|---|---|
| 1 | Thermal (I²t) | implemented |
| 2 | IEEE inverse-time | implemented |
| 3 | GE-SMR (Spectra Micro Relay) | implemented |
| 4 | ThermTU | implemented |
| 5 | ThermTUF (with fuse coordination) | implemented |

**The LTD calculator (`etu_ltd.py ETULTDCalculator`) implements all 5 methods and is recorded COMPLETE.**
`[DLL_SEMANTIC_FINDINGS §3 "COMPLETE — no work needed"]` However: the LTD **delay-parity** question
(`DS2_DLY_PTY`, §N.3) is a separate, **unresolved** semantic — the LTD *window* arithmetic is
implemented but its delay-priority/parity edge was never characterized. Treat LTD as **implemented,
direct-band-class** for the window; flag `DS2_DLY_PTY` as `[DEFERRED]`. `[06 §matrix §N.3]`

### 3d. The INVEQ mechanism is UNIFORM and the loader is fully recovered (§O CLOSED)

**All inverse equations are loaded + dispatched the same way** — one mechanism, not a per-sensor zoo.
The GF-side INVEQ loader blocker (spec §O) was **CLOSED 2026-04-29** by Ghidra-headless native
disassembly of `EasyPower.exe` — the "producers and consumers" recovery the late-April lane was built
around. `[HANDOFF 2026-04-29-tcc-gf-side-inverse-equation-easypower-exe-ghidra-headless-thunk-xref-recovery — §O CLOSED]` `[HANDOFF …-populator-consumer-recovery]` `[HANDOFF …-hypothesis-validation]` `[06]`

Recovered with direct native evidence (the producer→consumer chain):
- **One chain:** populator `FUN_01207bf0` → wrapper `FUN_011e2710` (pushes `nSection`) → DvlEng
  `dvlSSTGetInvEqDelays(…, nSection, &delays)` fills `TdbPtrArray<dvlDatInveqDelay>` → the populator
  iterates the rows + dispatches to the 8 setters. **STD uses `nSection=3`, GF `nSection=5` — the same
  chain, only the section literal differs.**
- **One row layout, 4 sub-blocks** (FdOp / FdCl / IdOp / IdCl = Flat/Inverse × Open/Clear): byte0 `*Eq`
  (`0=Therm` / `≠0=Ansi`), byte1 `*ICalc`, then **5 Therm floats** (`rTmin, rX, rTref, rIref, rM`) **or
  6 Ansi floats** (`rTmin, rA, rB, rC, rD, rE`). Therm-vs-Ansi for the whole row = the IdOp `*Eq` byte (row offset 0x70).
- **One translation:** `byICalc = (in==0)?2 : (in==1)?1 : 0` (`FUN_01208640`), applied at every setter
  site; on DB `*ICalc ∈ {1,4,8,10}` → `{1→1, 4→0, 8→0, 10→0}`.
- **Binding BOUND × 3** (4 sub-blocks × Therm/Ansi), from in-function `MOVSS [ESI+offset]` reads
  immediately followed by the matching setter `CALL` — direct, not name-correspondence.

**Consequence for trust:** INVEQ is **not** an open-ended unknown. The dispatch, the two coefficient
forms, the discriminators, and the translation are decoded and **uniform** across every INVEQ sensor
(STD + GF, all 4 sub-blocks). The *only* residual (§5) is whether the platform evaluator reproduces
EasyPower's native curve NUMBERS for those two known coefficient forms — a single bounded **two-form**
check, not a 6,200-sensor mystery.

### 3e. Managed evaluator characterization — `IEEEInverseTimeSolver` (NEW 2026-05-31)

§3d proves the *loader* is uniform; this scoping pass (`_discovery/_validation/v4-inveq-parity-scoping.md`)
read the *managed evaluator* that consumes those coefficients, and the parity gap turns out **both more
tractable and more concerning** than the prior framing:

- **Corpus distribution (live, exact — re-measured 2026-06-01).** STD (`DatSection3InvEq`, 22,620 rows)
  is **100% Therm** (zero Ansi). GF (`DatSection1GfInvEq`, 8,550 rows) = **8,450 Therm + exactly 100 Ansi
  ROWS**. **Correction (2026-06-01):** the 100 Ansi rows are **23 distinct sensors** across **3 trip styles**
  — not "100 sensors." `DatStyle` 233 (`USR RMS`/`LSIG`), 1169 (`USR RMS`/`LSIG (2)`), 1074 (`USD-20`/`LVPCB`).
  *(The §98 "Federal Pioneer" attribution is `[OPEN-VALIDATION]` — the trip-style names above are the
  verified identity; the manufacturer was not re-confirmed and is no longer asserted.)* So Ansi = 100 rows /
  23 sensors of the corpus; the other 31,070 rows (STD 22,620 + GF 8,450) are Therm. `[VERIFIED-LIVE 2026-06-01]`
- **The pre-patch managed formula** (`etu_curves.py`, before 2026-06-01): `T = (c1 / (I_norm^c2 − 1) + c3 + c6) × time_dial`,
  then `× (1 + tol/100)`. It loaded 6 slots into `c1..c6` but used only `c1`, `c2`, `c3`, `c6`, silently
  ignoring `c4` and `c5` (native `rIref`/`rM`). `[VERIFIED-LIVE 2026-05-31 — code read]`
- **Native recovery 2026-06-01 (`TccBase.dll`, ILSpy/Mono):**
  - **`CalcThermEq` formula recovered and patched.** Native consumes **both** `rIref` and `rM`:
    `T = rTref × ln(1 / (1 - (rM / I_norm)^rX)) / ln(1 / (1 - (rM / rIref)^rX))`, floored at `rTmin`
    for emitted curve points. Therefore the old managed Therm branch was **wrong**, not merely unvalidated.
    `IEEEInverseTimeSolver` now detects Therm-shaped rows (`c1=rTmin`, `c2=rX`, `c3=rTref`, `c4=rIref`,
    `c5=rM`, `c6=0`) and evaluates this native form. Focused tests: `test_source_faithful_adapters.py`
    + `test_etu_delay_routing.py` = 12/12. `[DLL TccBase.dll CTccLVBreakerCurveGF.CalcThermEq]`
  - **`CalcAnsiEqGF` formula recovered, but still excluded.** Native ANSI uses tolerance-adjusted current
    and `T = A + B/(I-C) + D/(I-C)^2 + E/(I-C)^3`, with a `Tmin` floor/extension. The 100 Ansi rows remain
    hard-excluded by `gf_inveq_is_excluded_ansi(id_open_eq)` until a family-aware ANSI solver path has
    captured EasyPower fixtures; no silent IEEE/Therm fallback is allowed. `[DLL TccBase.dll CTccLVBreakerCurveGF.CalcAnsiEqGF]`
- **Residual parity gate.** The c4/c5 question is closed. What remains is captured EasyPower point parity
  for representative Therm rows (and an ANSI path decision if the excluded cohort must be reintroduced).
  Independent `[DLL]` corroboration of the 5/6 split remains: `GFInverseEqDelayData.cs` declares
  `sTherm`=40B and `sAnsi`=48B (exactly +1 float). `[VERIFIED-LIVE 2026-06-01]` `[06 pass-5]`

### 3f. Native-execution parity CLOSED for STD Therm (NEW 2026-06-01) — `[DLL-EXEC]`

The captured-fixture gate of §3e/§5 is now closed for STD Therm by **executing the native kernel
itself** — the strongest possible oracle (the actual EasyPower engine math, not a paraphrase, not a
GUI screen-scrape). `TccBase.dll` (x86 mixed-mode C++/CLI, `PublicKeyToken=fd790d0312e979ea`) was
loaded in-process under the 32-bit .NET Framework and its module functions
`CTccLVBreakerCurveGF.CalcThermEq` and `CTccLVBreakerCurveSST.CalcThermEq3` invoked via
reflection + `Pointer.Box`, emitting native `(amps, time)` curve points for real DB coefficient rows.
Harness: `output/inveq-parity/oracle/` (local-only; the licensed DLL + decompile are git-ignored). The
captured points are frozen as `packages/calc-engine/tests/fixtures/inveq_therm_native_parity.json` and
asserted by `test_inveq_therm_native_parity.py` (CI runs without the DLL). `[DLL-EXEC TccBase.dll 2026-06-01]`

Decisive results:

- **The native per-point body matches the managed closed form exactly.** Reading the decompiled
  `CalcThermEq` (line ~18350) and `CalcThermEq3` (~27653): `T = ln(1/(1−(num7/amps)^rX)) · rTref / num8`
  with `num7 = num6·rM`, `num8 = ln(1/(1−(num7/(num3·rIRef))^rX))`, floored at `rTmin`. For `byICalc=0`
  (`num3 = field[16] = num6 = pickup`) this reduces to the managed
  `T = rTref·ln(1/(1−(rM/I)^rX)) / ln(1/(1−(rM/rIRef)^rX))`, the absolute pickup cancelling.
- **STD Therm parity is BIT-EXACT and EXHAUSTIVE.** STD `IdOpICalc ≡ 4` (all 22,620 rows) → `byICalc=0`
  → `num3 = pickup`. The STD Therm corpus is **only 4 distinct dial curves** (`rTmin≡rTref ∈
  {0.08,0.14,0.23,0.35}`, `rX=2,rIRef=10,rM=0.9`; 4,524 sensors each). The managed solver reproduces the
  native kernel with **maxabs = 0.0 across all 4 curves** (`GF` fn `byICalc=0` and `SST` fn `byICalc=11`
  give identical output → STD ≡ GF evaluator). **STD INVEQ Therm → PROMOTED PROVEN / "db".**
- **GF Therm is NOT managed-faithful — kept withheld.** GF `IdOpICalc = 1` for 6,760 of 8,450 Therm rows
  → `byICalc=1` → `num3 = field[13] ≠ pickup`, scaling the denominator's effective `rIRef` by
  `num6/field[13]`; and every `rIRef < rM` GF row (e.g. `rIRef=0.48`) makes `rM/rIRef > 1` so the managed
  `num3=num6` form returns **None** outright. Native produces a valid curve there only via the `field[13]`
  basis. So GF route-2 Therm stays **"verify"** (not promoted); the open item is `field[13]` provenance.
- **GF `field[13]` RESOLVED = the PLUG rating (In) — GF-INVEQ Therm PROMOTED "db" (L1 close, 2026-06-09; STATE §206).**
  The provenance fell out of the kernel's own **pickup-basis dispatcher**: `CTccLVBreakerCurveGF.ComputeAmps
  (uCalc, r)` maps each GF pickup calc code to its basis slot, and cross-referencing against the VALIDATED
  managed enum (`etu_pickup.py` `ETUCalcMethod`, mirroring `tcc.etu_sensors.*_calc`) locks **native uCalc =
  DB `*_calc` + 1** via two exact semantic matches (native 8 returns the setting AS AMPS = DB 7 AMPS;
  native 9 anchors `[16]` = DB 8 GFPU-cascade). **Slot map (banked):** `[12]` = sensor/frame rating ·
  **`[13]` = plug value (In)** · `[14]` = GF pickup dial setting · `[15]` = C-factor/multiplier (ctor
  default 1.0) · `[16]` = computed GF pickup amps (`num6`, written by `RecalcCurve`) · `[19]` = pickup max
  cap (`gfpu_pickup_max`) · `[20]` = external ground-sensor rating. Decompile source: Box
  `TCC_Master/DLL/CTccLVBreakerCurveGF.cs` (`{ctor}`, `ComputeAmps` ×2, `RecalcCurve`, `CalcAnsiEqGF`).
  **Numeric validation:** in the normalized managed form, byICalc=1 ≡ the STD-proven Therm equation with
  **`rIRef' = rIRef × (plug/pickup)`**. The preserved §107 oracle re-ran the native `CalcThermEq` with
  `byICalc=1`, `[16]=1.0`, `[13]=R` over the COMPLETE GF Therm corpus (4 open dials rM=0.9 × rIRef ∈
  {1.0,0.75,0.6,0.48,0.2} + 4 clear dials rM=1.1 × rIRef = open×1.1001; rX=2) × R ∈ {1…10} — 416 scenarios:
  **SMOOTH MAXABS = 0.0 (bit-exact)**, 152/152 all-sentinel outputs exactly at the `R·rIRef ≤ rM` validity
  boundary with managed-None agreement, 0 floor-knee mismatches. Fixtures frozen
  (`packages/calc-engine/tests/fixtures/gf_inveq_field13_native_parity.json` + 13 tests; CI runs without
  the DLL). **Production:** `apply_gf_basis()` gates at coefficient load (`*_i_calc` threaded through the
  row loader; basis-less byICalc=1 rows WITHHELD, never silently pickup-computed); `/plot-tcc` STD+GFD
  InvEq curves now render the **inverse sub-blocks** (`id_*` — the native GF-enabled block per pass-5
  gating; `fd_*` is the flat segment) with band-matched ordinal selection, GFD passing
  `gf_basis_ratio = plug/GFPU-pickup`. `delay_trust._classify_gfd` route-2 Therm → **db** (~1,690 sensors;
  certifies the Screen-3 GF-InvEq curve — these sensors carry no direct GFD bands, so no field-table row
  is affected). Apex `da90b3e8`.
- **CORRECTED 2026-06-09 (L1 close): GF-Ansi does NOT ride the field[13] anchor at runtime.** The corpus
  data shows the Ansi rows (`in_out=1`, `id_op_eq=1`) carry `id_op_i_calc = 8` → translator → **byICalc=0 →
  `field[16]` = pickup basis** — the 2026-06-02 "promote together" coupling below over-read the
  byte-identical *selector code* as a shared *runtime anchor*. Consequence: GF-Ansi promotion needs NO
  plug threading — it is an independent, smaller lane: implement the banked C37.112 formula in the managed
  solver + oracle-validate via `CalcAnsiEqGF` (the §107 harness pattern; arg-mapping from the
  `SetAnsi_*` setters) + un-exclude. The 2026-06-02 finding below is retained for the formula bank and
  the selector-recovery provenance:
- ~~GF-Ansi shares the SAME `field[13]` basis → GF-Therm and GF-Ansi are ONE field[13]-gated lane (NEW 2026-06-02).~~
  Decomp of `CalcAnsiEqGF` (line 18392) shows its pickup-basis selection is **byte-identical to `CalcThermEq`**:
  `byICalc {0→field[16], 1→field[13], 2→field[12]}` (Ansi lines 18400-18419 vs Therm 18305-18324), and the
  Ansi current axis is likewise normalized by that basis (`num10 = field[16]·(rTol+1)/num4`, `num4 = field[<sel>]`;
  line 18448). So the GF runtime (`byICalc=1`) anchors **both** families on `field[13]` — the Ansi family carries
  the **same unresolved `field[13]` blocker** as Therm, **not** an independent one. **Consequence:** GF-INVEQ Therm
  (1,690) **and** GF-INVEQ Ansi (23 sensors / 100 rows) promote **together** in one motion once `field[13]` is
  resolved; there is no standalone Ansi ship. The recovered `CalcAnsiEqGF` curve is `T(M) = rA + rB/M' + rD/M'² +
  rE/M'³` with `M' = (I/field[<sel>])/(rTol+1) − rC`, plus a flat/definite degenerate branch (`rB=rD=rE=0` →
  `T = rTmin` from `field[16]·(rTol+1)`); the form is **structure-validated** (monotone inverse-time, C37.112
  shape) `[VERIFIED 2026-06-02]`, leaving `field[13]` as the sole blocker shared with Therm. `[DLL TccBase.dll CTccLVBreakerCurveGF.CalcAnsiEqGF 18392-18490 · CalcThermEq 18298-18324]`
- **Secondary residual `*ICalc=0` CLOSED.** Direct `[VERIFIED-LIVE]` count: **zero rows** in
  `DatSection3InvEq` or `DatSection1GfInvEq` store any `*ICalc = 0`. STD `IdOpICalc ≡ 4`; GF `∈ {1→6760,
  4→1690, 8→100(Ansi)}`. The pass-5 translator branch `*ICalc=0 → byICalc=2 → ref[12]` is correct but
  **never exercised** by real data (`[06 §R4]` answered). `[VERIFIED-LIVE 2026-06-01]`

### 3g. Native TCC PLOT COMPOSITION — RECOVERED 2026-06-09 (`CPointsMergeSST` / `CPointsMergeGF`) `[DLL]`

How the native engine assembles the PLOTTED breaker characteristic from the per-element curve blocks —
previously a G-doc gap (this guide covered calc math only; the composition lived in the unrecovered
`RecalcCurve_SSTT_*` "heavy" render). Recovered from the Box decompile by a 3-reader evidence sweep
(operator feedback session 2026-06-09; raw packet with full quotes:
`.audit_workspace/tcc_composite_boundary/EVIDENCE-wf_a2164913-mergesst-recovery.json`, host-local).

**The composite is ONE ordered polyline per boundary — never independent element traces, never a
pointwise min-envelope.** Rules, each `[DLL TccBase.dll]`-cited:

1. **Assembly orchestrator** = `CPointsMergeSST.MergeSST` (line 1438): builds one current-ordered point
   array per pass; dispatches by element-presence flags (LTPU/STPU/INST/STDB) to
   `MergeSST_LT / _LT_INST / _LT_ST / _LT_ST_INST / _ST_OVR / _LT_OVR`; `bClearing=true` pass is
   point-REVERSED (`ReversePoints`).
2. **Vertical pickup asymptote first**: `AddLongTimePickup` (85-94) writes two points at `x = LTPU`
   (`t = 1,000,000 → 0.001`) — the characteristic's left edge. GF likewise: `{GFPU, 1000} → {GFPU, 0.001}`
   (`CTccLVBreakerCurveGF.RecalcCurve` cases 1/3, 1141-1199; maint mode swaps the maint-GFPU vertical).
3. **Every element block is CLIPPED to an explicit current window** via `CLinearEquation.TrimCurveX`:
   `AddLongTimeDelay` (66-77) trims LT to `[LTPU, dMaxAmps]`; `AddShortTimeDelay` (152) trims ST to
   `[STPU/handoff, dMaxAmps]` (start index advanced past points below the prior block's end);
   `AddShortTimeOverideDelay` (171) trims the override array to `[dMin, dMax]`.
4. **The LT→ST handoff current is a log-log curve INTERSECTION**, not a blind pickup clip:
   `MergeLines` (1173-1431) walks both curves with `CLogLogIntersection.SolveWithinConstraints/Solve`,
   truncates curve-1 at the crossing, records the join; a `bDelayPriority` flag selects equal-time joins.
   In the canonical full-band variant (`MergeSST_LT_ST_OVR_INST_DelayPriorityNone`, 2786-2800) the
   handoff `dMaxAmps` is computed by `ComputeX` at the ST pickup before the Add* sequence:
   `AddLongTimePickup → AddLongTimeDelay → AddShortTimeDelay [+ AddShortTimeOverideDelay] →
   AddInstantaneous(1e10, bOverride)`.
5. **INST floor**: `AddInstantaneous` (18-58) places the horizontal segment in constant-INST mode
   (`P_0[72]==2`) and blends the corner from the prior block with `AutoAdjustFillet(0.09)` +
   `CSplines.Fillet` (cosmetic spline fillets at every block join); with override, the INST time comes
   from the override array.
6. **Open + clear = two MergeSST passes into ONE buffer forming a CLOSED band polygon**:
   `CTccLVBreakerCurveSST.RecalcCurve_STT_LT` (3503-3646) runs `MergeSST(false)` (min-trip/open) then
   `MergeSST(true)` (total-clear, reversed), copies a closing point (3645); `P_0[7]/P_0[8]` are the
   open-count/clear-start section markers.
7. **Final right-edge clip at the study's available short-circuit current**: `RecalcCurve` (3289-3345)
   → `ClipCurve(GetScAmps, …)` after assembly; shape variant chosen by `DetermineShapeSST` (1788-1916,
   element bitmask; the override bit is CLEARED when the override pickup ≤ INST amps).
8. **Ground fault is a fully separate band**: `CPointsMergeGF.MergeGF` (127-200) + `SetGFPU/SetGFDB/SetIXT`
   (217-251) — own vertical GFPU asymptote + GFD band, filleted corner, SC-amps cap, its own open/clear
   passes. Independent of (and conventionally crossing) the phase band.

**Serving lane SHIPPED 2026-06-10 (#122, apex `b2dfa7fd`; STATE §209-§210):**
`services/neta/composite_boundary.py` (pure, 20 TDD tests) assembles `composite_bands`
(`phase_band` + `gf_band`, open/clear boundary polylines each) on `/plot-tcc` from the served
per-element curves; the frontend fills the closed polygon with the per-element traces demoted to a
legend toggle. Implements rules 1-8 with these documented deviations (operator-ratified §209 tiers):
**right edge = 100 kA** (serving sweep default; native clips at study SC amps — SC input later);
**fillets skipped** (rule 5 cosmetic); **route-1 clear-edge synthesis SHIPPED 2026-06-10 (#123, apex
`4f11d4aa`)**: STD/GFD serve the clear boundary from the band's symmetric CLEAR block
(`i_clear`/`t_clear` ramp anchor + `std_clear`/`gfd_clear` floor) through the same validated `CIxt`
kernel — native open/clear are symmetric blocks (`SetSTDB_*Delay{Open,Clear}` 24440-24531; the I2X-4
oracle validated both sides) — and the synthesized LTD serves clear at the matched band's
`clear_time` under the **SAME-BAND law** (the clear basis must come from the band that supplied the
open `tr`; a cross-band pair is a band that does not exist — adversarial-review finding). Remaining
open-only cases are honest withholds surfaced in `open_only_elements` + the UI note: partial composite
clear blocks (floor-without-ramp, 282 STD + 211 GFD rows — native partial-block behavior unratified),
GFD rows missing clear ramp anchors (~8k of 50k), and live LTD (prod `etu_ltd_bands` is the legacy
shape with no `clear_time`; the legacy normalizer DUPLICATES open→clear, which the equality guard
rejects as no independent clear basis). Handoff semantics validated by adversarial review:
next-element pickup when it already governs there (the classic vertical drop at STPU — THE production
case, since DB-route LT curves descend through the ST shelf to their min-time floor), log-log crossing
only when the next block starts ABOVE the current curve (delay priority); region ends = suffix-min of
later region starts, so a low-dialed INST caps every earlier block at its pickup (native
`AddInstantaneous`-at-INST-amps equivalence). Route-1 STD now sweeps to the right edge when no INST
exists (rule 7 — native carries the final element to the clip). Residual per-element serving facts:
INST times are still the 0.05/0.08 s placeholders (`Sec4Inst*` = matrix row 12, unresolved — the band
floor inherits them); route-2 sweeps still default `max_amps=100 kA` (now harmless — the assembly
clips them at the handoffs).

**Tolerance-envelope serving lane SHIPPED 2026-06-10 (#124, apex `8b8120d5` + `9b1e995b`; STATE §212):**
the field-acceptance corridor is a DISTINCT surface from the published band above — `services/neta/
tolerance_envelope.py` (pure) transforms the served per-element curves by the §2 per-sensor tolerances
and reassembles min/max boundaries through the composite assembler; `envelope_bands` on `/plot-tcc`
(per-element basis metadata + `open_only`/`no_envelope` honesty lists, fail-open); FE renders it as a
dotted translucent corridor BEHIND the band, legend toggle default ON, per-element basis lines.
Operator-ratified semantics: **PU tolerance shifts the amps axis for every element** (pcts derived
from the SERVED pickup-marker limits, so whisker↔envelope identity holds by construction — every
served shape is multiplicative in current); **time widening only in acceptance-window mode** (LTD: the
§111 reference-window tolerance chain, generic −30/+0 flagged `est`); **published-band mode for
STD/INST/GFD** (their open/clear pair IS the mfr window — amps shift only). Consistency laws from the
pre-ship adversarial review (51 agents, 7 confirmed findings, all fixed): (1) **maint mode withholds
the envelope** + warning — markers grade the maint configuration while curves are nominal, so a
corridor would mix bases and contradict the whiskers on one plot; (2) **LTD anchor-consistency
guard** — the graded surface is the I²t window THROUGH the marker anchor (`t = expected·(marker_amps/
I)²`), probed at two log-spaced points INSIDE the served sweep (the marker itself may sit beyond the
curve's clip, e.g. a low-dialed STPU; live-caught on 3833): window-law curves keep their envelope at
any clip, non-I²t LTD curve methods (~890 sensors) withhold honestly; (3) **truncation law** — the
corridor never SPANS a served-but-uncertified element's region (a middle/last withhold cuts the
corridor at that element's region start; leading withholds degrade naturally; the assembler's
suffix-min/flat-tail laws would otherwise chord fabricated geometry across the gap); (4) **G4
TIME_WITHHELD elements get NO envelope**, surfaced in `no_envelope_elements`, and a **family-total
withhold surfaces a response warning** (the honesty list has no band to ride on); (5) the LTD basis
accepts ONLY the reference-window timing sources (`band_table`/`curve_interpolation` fallthroughs are
not a multiplicative tolerance and must not masquerade as DS2). Live-verified (3833: boundary law
exact at 1e-6 incl. the real Micrologic **+5/+20 % LTPU** band; identity OK on all four elements;
maint withhold live; 4628 route-2 InvEq serves published-band corridors). ~~**Open characterization
(punch list): sensor-level `etu_sensors.ltd_tol_lo/hi` = `DatSensor.DS2_TOL_*` (universal, all
nonzero) is NOT confirmably the curve-type time tolerance** (545/876 match the `etu_ltd_params` I²T
row; 288 of the 331 mismatches match NO curve row) — not wired anywhere until its native semantics
are pinned.~~ **CLOSED 2026-06-10 (L11, apex `de5cc275`) — semantics PINNED + WIRED.** Triangulation
(PATTERN-010): the EasyPower device-library editor's own Section-2 dialog template labels the pair
**"LT Delay Tolerance Band / Low: / High:"** — exactly parallel to Section1/3/4/1GF's proven pickup
tolerance bands (`[NATIVE-BIN EasyPower.exe dialog resources]`); `DvlEng.dll` places `DS2_TOL_LOW/
HIGH` in the Section-2 LT-delay column cluster whose per-curve reader is `SELECT * FROM DatSensorSec2
WHERE SensorID=%d AND CurveName='%s'`, and the `ALTER TABLE DatSensor ADD DS2_ALLOW_CURVES` migration
strings pin the **two-grain layout**: per-curve `DatSensorSec2` rows (→ `tcc.etu_ltd_params.ds2_tol_*`)
govern in multi-curve mode; the **sensor-level inline pair governs in the native single-curve layout**
(`DS2_ALLOW_CURVES=0` = `etu_sensors.ltd_allow_curves`). Value-shape identity across both grains
(signed percent on time; shared vendor constants −17.89/−26.83/−38.81). The §212 correlation puzzle
resolves: 818/1,100 multi-curve sensors' inline pairs mirror a live curve row, 282 are stale inline
values — which is why the resolver uses the inline pair **only when NO curve rows exist** (additive-
only; disagreeing curve rows still serve the flagged generic rather than the stale-prone inline pair).
Hygiene gates (non-null / not (0,0) / lo ≤ hi / factor > 0): **16,749/16,749 no-params sensors pass —
the generic −30/+0 LTD estimate is RETIRED for the entire population** across whiskers, envelope and
the future field sheet through the unchanged `ltd_reference_window` chain. Live-verified: sensor 849
serves 640/800 s = exactly (1−0.20)/(1.00)×nominal as `ltd_reference_window`/db; flagship 3833 (itself
no-params) upgraded generic→real — envelope LTD basis now `time −20/+0, src=ltd_curve_tol, est=False`.

**Read every sensor's delay-calc route against this table before emitting a delay/curve number.**
Status legend: **PROVEN** = recovered + bound + numerically validated on real rows; **BOUNDED** =
dispatch/routing recovered, wired, and exercised, but the numerical kernel output is *not* yet proven
row-for-row against EasyPower native (consistency-checked on a thin cohort only); **DEFERRED** = out
of scope / fall-through diagnostic only, never numerically characterized; **STUB** = deliberately
withheld with a diagnostic, pickup/curve unknown.

| # | Element / path | Selector | Status | Safe to ship on a field sheet? | Evidence |
|---|---|---|---|---|---|
| 1 | **PU tolerances (all elements)** | `*_tol_hi`/`*_tol_lo` data | **PROVEN (data)** | **YES — always.** Authoritative per-sensor data; no solver. | `[DLL_END_TO_END_MAPPING §16]` `[HANDOFF TASK-008]` |
| 2 | **Pickup CURRENTS** (LTPU/STPU/INST/GFPU) | `DS*_PICKUP_CALC` → `SSTCalcMethod` | **PROVEN (arithmetic)** | **YES** for methods 0-7 (simple multiply); **NO** for 8/9/10 (unresolved). | `[09 §1]` `[HANDOFF task-c STPU=1, GFPU split]` |
| 3 | **STD direct-band** | `DS3_SEC3_I2T = 0` | **PROVEN** | **YES.** Row-for-row Series B parity. | SE `(10,10,2)`/MX `(6,6,1)`/PX-6B mixed; TASK-C 8/8 `[06]` |
| 4 | **GFD direct-band** | `DS1GF_SEC3_I2T = 0` | **PROVEN** | **YES.** Literal-amps anchor validated. | Full-SE `2000A` ×4 ordinals; TASK-C `[06]` |
| 5 | **LTD window** | LTD method 1-5 | **PROVEN (impl. complete)** | **YES** for the window; **flag** `DS2_DLY_PTY` parity. | `etu_ltd.py` 5 methods COMPLETE `[DLL_SEMANTIC_FINDINGS §3]`; §N.3 deferred `[06]` |
| 6 | **STD-side INVEQ curve NUMBERS** | `DS3_SEC3_I2T = 2` (4,524 sensors, **100% Therm**) | **PROVEN (native-execution parity)** | **YES.** Managed solver reproduces the native `CalcThermEq`/`CalcThermEq3` kernel **BIT-EXACT (maxabs 0.0)** over the complete STD Therm corpus (4 dial curves; all `byICalc=0`). Promoted "verify"→"db" in `delay_trust.py`. | `[DLL-EXEC TccBase.dll]` native kernel invoked; `inveq_therm_native_parity.json` + tests `[VERIFIED-LIVE 2026-06-01 §3f]` |
| 7 | **GF-side INVEQ curve NUMBERS** | `DS1GF_SEC3_I2T = 2` (1,713 sensors = **1,690 Therm + 23 Ansi**; 100 Ansi rows) | **Therm = PROVEN (native-execution parity, plug basis); Ansi = FORMULA RECOVERED, anchors pickup, excluded pending implementation** | **Therm: PROMOTED "verify"→"db" (L1 close 2026-06-09). `field[13]` = the PLUG rating (ComputeAmps slot map, §3f); managed `rIRef' = rIRef × plug/pickup` reproduces native `CalcThermEq` byICalc=1 BIT-EXACT (maxabs 0.0, 416-scenario corpus sweep; fixtures `gf_inveq_field13_native_parity.json`). Basis-less rows withheld at the solver. Ansi: anchors PICKUP (`id_op_i_calc=8`→byICalc=0, corrected 2026-06-09) — independent implement+validate lane; HARD-EXCLUDED in `etu_delay_routing.py` meanwhile.** | `[DLL-EXEC TccBase.dll 2026-06-09]` native byICalc=1 sweep; ComputeAmps slot map `[DLL]`; apex `da90b3e8` `[VERIFIED-LIVE 2026-06-09 §3f]` |
| 8 | **WEG OCR Type A pickup** | `DS1GF_PICKUP_CALC = 6` (§N.4, 7 sensors) | **STUB** | **NO — hard-exclude.** Pickup formula UNKNOWN; curve deliberately withheld. Show "unsupported". | diagnostic exclusion `[06 §matrix §N.4]` |
| 9 | **GE-TU-STD** | `DS3_SEC3_I2T = 3` (235 sensors) | **DEFERRED / STUB** | **NO — hard-exclude.** Fall-through diagnostic only; not solved. | "Enteliguard not supported" `[06]` `[DLL_END_TO_END_MAPPING]` |
| 10 | **GE-TU-Gnd** | `DS1GF_SEC3_I2T = 4` (209 sensors) | **DEFERRED / STUB** | **NO — hard-exclude.** Fall-through diagnostic only. | `[06 §matrix]` |
| 11 | **I2X solver** | `DS3_SEC3_I2T = 1` (8,708 sensors) | **DEFERRED / NOT IMPLEMENTED** | **NO — hard-exclude.** I²t/Iˣ·t solver not built; (`I2X=255` §N.2 also open). | `[DLL_END_TO_END_MAPPING §6/§16]` `[06 §N.2]` |
| 12 | **INST override** (`Sec4Inst*` / `DS4_OVR_*`) | INST-override path (§N.5 / §K) | **STUB / DEFERRED** | **NO — hard-exclude / withhold.** INST curve-calc surface unresolved; override math native-only, not read by managed lib. | `[06 §N.5, §K]` `[09 §4f]` |
| 13 | **STPU override (band routing)** | `tcc.etu_stpu_overrides` (3 sensors) | **PARTIAL** | **Constant-mode override pickup + override tolerances OK; decreasing-mode curve = withhold.** Override *routing* covered in TASK-C; broader override math deferred. | `[06 §matrix]` `[DLL_SEMANTIC_FINDINGS §4]` |

**The one-line rule the matrix encodes:** *ship rows 1-5 (and constant-mode override 13) **plus row 6
STD-INVEQ Therm AND row 7 GF-INVEQ Therm** (both native-execution PROVEN — STD §107, GF plug-basis L1
close 2026-06-09 §3f); **hard-exclude the 23 GF Ansi sensors / 100 rows (formula recovered, pickup-anchored,
solver path not yet shipped) and rows 8-12.***

> **Test-POINT vs expected-TIME (NETA sheet column-trust).** For a delay element the test sheet has two
> separable quantities, with *different* trust sources: **(a) the test point** — the NETA test multiple
> (LTD 3× LTPU · STD 1.5× STPU · GFD 1.5× GFPU; `NETA_TEST_PLAN_SPEC §2/§11`) and the **inject current** =
> multiple × the element's pickup current — is **always field-correct** (a fixed NETA procedure applied to
> the *proven* pickup current of row 2), independent of curve-number trust; and **(b) the expected trip
> time** at that point, which inherits this matrix's delay-status (PROVEN for direct-band rows 3-5 **and
> both INVEQ Therm rows 6+7, native-execution PROVEN §3f** — STD §107, GF plug-basis L1 2026-06-09).
> The LV page (`/lvbreakertcc`) renders (a) directly (NETA multiple +
> inject current, field-correct) and **route-gates (b) per the per-sensor delay-calc route** (the §6 gating
> algorithm, encoded once in `apps/control-plane-api/services/neta/delay_trust.py`): **DB** for direct-band
> (STD/GFD route 0) + LTD (methods 1-5) **+ STD- and GFD-INVEQ (route 2) Therm — both validated BIT-EXACT
> vs the native `CalcThermEq` kernel (§3f)**; **"verify"** for the I2X composite shape only (route 1,
> native-render spot-check pending, task #72); and
> **"n/a" (time withheld)** for the
> not-implemented / hard-excluded routes — I2X (route 1), GE-TU STD/Gnd (routes 3/4), and the GF-INVEQ ANSI
> family (`id_op_eq ≠ 0`). `/calculate` now returns a per-delay-element **`trust` + `delay_route` + `trust_reason`**
> and **nulls the expected time for unsupported routes** (the fall-through band value is not a certified curve;
> G4 §6 step 6) — so an I2X sensor like XT2 LSIG (STD/GFD route 1) no longer shows a fall-through `band_table`
> time under a "verify" badge. The inject current (the test point) stays valid in every tier. `/context` also
> now surfaces the route codes as `stpu_delay_calc_code` / `ground_delay_calc_code` (the legacy `*_i2t`
> response aliases had silently dropped to NULL after the Phase 5 Tier A rename). Earlier the page conflated the
> selected delay *band* value with the test multiple (the `/calculate` `p_*_multiplier` param), so it showed
> e.g. STD "0.1× / 1,200 A" (below pickup); now corrected. `[VERIFIED-LIVE 2026-06-01]`

> **Operator-selectable delay test current + the LTD I²t model (the "bigger delay test current" option).**
> The delay **test point (a)** is now operator-selectable per element via `/calculate`'s new
> `ltd_test_multiple` / `std_test_multiple` / `gfd_test_multiple` inputs (default = the NETA points above);
> the inject current scales as `multiple × pickup` and stays field-correct at any multiple. For **LTD the
> expected time (b)** is the long-time **I²t characteristic** `t = setting · (6/N)²`, where the stored LTD
> band setting **is the trip time at 6× Ir** (the industry band reference — confirmed: source `DatSection2LTD.LTD_DESC`
> = whole seconds "2s…24s", and the engine's `_ltd_reference_delay_surface` anchors at 6×). So testing at **6×**
> yields a time equal to the dial setting (the practical, directly-measurable point), while **3× is 4× longer**.
> `/calculate` for LTD now routes through that **reference window** (`use_ltd_reference_window=True`), so the
> Screen-2 bands table **agrees with the Screen-3 curve** at the same multiple. This also fixed a residual
> band↔multiplier conflation specific to `/calculate`'s delay rows: it had echoed the LTD band value as the
> multiplier (e.g. a 12 s band → "12× / 11,520 A" inject) and shown the 6×-anchored time under a 3× label.
> LTD stays **DB** (the band value is DB; I²t scaling between 3× and 6× is the definitional long-time
> characteristic, both points well inside the I²t region).
>
> **LTD time tolerance now per-manufacturer (L5, 2026-06-03).** The reference window's band is no longer the
> hardcoded `(0.7·nominal, nominal)` (−30 % / 0) placeholder. `_authoritative_delay_surface` now loads the
> **per-sensor DB tolerance** `tcc.etu_ltd_params.ds2_tol_low/ds2_tol_high` and applies it as
> `nominal·(1 + tol/100)`. **LTD tolerance is stored PER CURVE TYPE** (I²T vs IEEE V/Mod/Ext vs IEC A/B/C vs
> I⁴T — I²T ≈ −27/+0, IEEE/IEC ±10 %, I⁴T −38.81/+9.7), so `_load_ltd_time_tolerance` pairs the **I²T-curve-type
> row** with the I²t-rendered window; else it accepts only an unambiguous sensor-wide value; else falls back to
> the generic −30/+0 **flagged** `timing_source=ltd_reference_window_generic` (UI shows an `est` marker so a
> placeholder never reads as DB-authoritative). **Open follow-ons:** (a) **ET 1.0 family** (no `ds2_tol` row,
> e.g. PowerPact M-frame MGA36600) — source ±10 % from curve 613-14 via the validated-library, gated on the
> ET 1.0 bridge `[L5-LTD-C, DEFERRED 2026-06-03 — the breaker→trip-unit bridge that makes the whole ETU-library
> family selectable is the real lift; band sourcing is trivial once unblocked]`; (b) **curve-type-aware render**
> `[L5-LTD-B — INVESTIGATED + DEFERRED 2026-06-03, optional feature not a correctness gap]`. DB characterization
> (`DatSensorSec2`): only **1,127** of ~17,831 sensors carry any LTD curve/tol data; of those, **all 110
> single-curve (deterministic-active) sensors are I²t** (62 Thermal-I²T, 48 I2T) → the §111 I²t window is **exact**
> for every sensor whose active LTD curve is determinable; **1,009** multi-curve sensors offer I²t as a selectable
> option (valid default, and I²t is the standard LV long-time characteristic, usually fixed by design not a field
> setting); the **only** non-I²t-only sensors are **8 exotic MTX1/"MODpower" units** (`DELAY AT 6×/7.2× IR` defs,
> almost certainly unserved). So curve-type-aware render is a **product feature** (a Screen-2 LTD curve-type
> selector for multi-curve sensors + per-shape math: power-law exponent from the curve name, IEEE/IEC inverse-time
> equations later), **not** a bug fix — deferred pending operator product call. `/evaluate` still uses the band-table
> LTD path (the LV page computes PASS/FAIL client-side from `/calculate`, so it is unaffected) — reconcile it
> to the reference window if `/evaluate` is ever wired into the page. `[VERIFIED-LIVE 2026-06-02]`

---

## 5. The InvEq numeric-parity gap (CLOSED for Therm — STD §107 2026-06-01, GF plug-basis L1 2026-06-09; residual = the 23-sensor Ansi implement+validate lane)

> **2026-06-09 status:** the "#1 open calc question" below is **answered for the entire Therm corpus**
> (6,214 of 6,237 sensors): STD bit-exact (§3f, §107) and GF bit-exact on the plug basis (§3f, L1 close —
> `field[13]` = plug, 416-scenario sweep, maxabs 0.0, fixtures `gf_inveq_field13_native_parity.json`).
> The historical statement is preserved below for provenance; the only residual is GF-Ansi (23 sensors /
> 100 rows): formula recovered + pickup-anchored, awaiting a managed solver branch + oracle validation.

**Statement of the gap `[OPEN-VALIDATION — historical, see status above]`:** Both InvEq routes (STD `DS3_SEC3_I2T = 2` and GFD
`DS1GF_SEC3_I2T = 2`, ~6,200 sensors combined: 4,524 + 1,713) dispatch into the platform's
pre-existing **`IEEEInverseTimeSolver`** (`source-domains/tcc_v5_backend/services/calc_engine/etu_curves.py`).
That solver was **never validated row-for-row against EasyPower's native inverse-equation kernel —
`CalcThermEq` / `CalcAnsiEqGF` (`CTccLVBreakerCurveGF.cs`).** Every handoff that touched InvEq states
"**no parity claim**" explicitly. The *dispatch* (which sensors route to InvEq, which table, which
slot/setter, the `byICalc` translation) is PROVEN from native disassembly; the *emitted curve/delay
numbers* are validated for **routing consistency only** — TASK-C found no divergence on a **13-InvEq-row
+ 7-WEG** representative cohort, which is *not* point-for-point kernel parity and is a thin sample
against 6,200 sensors. `[06 §synthesis-4, §R1, §R2, §top-question-1]`

> **Scope of the residual — bounded, and now SPLIT into an act-now half + a one-function half
> (sharpened 2026-05-31; `_discovery/_validation/v4-inveq-parity-scoping.md`).** Per §3d/§3e the INVEQ
> *loader/mechanism* is **§O-CLOSED + uniform**; the *managed evaluator* was then read directly and the
> gap resolves to two concrete pieces, NOT a 6,200-sensor mystery:
> 1. **The Ansi half is formula-recovered but still excluded.** Only **100 rows / 23 sensors / 3
>    trip styles** corpus-wide are Ansi (`IdOpEq=1`; §3e). `CalcAnsiEqGF` is now recovered from `TccBase.dll`
>    as `A + B/(I-C) + D/(I-C)^2 + E/(I-C)^3` over tolerance-adjusted current, with a `Tmin` floor.
>    Because the runtime still lacks a family-aware ANSI solver path with captured EasyPower fixtures,
>    the ANSI family is hard-excluded at the dispatch layer (`gf_inveq_is_excluded_ansi` / `id_open_eq`)
>    with an INV-7 diagnostic, exactly like WEG OCR Type A. `[VERIFIED-LIVE 2026-06-01]`
> 2. **The Therm half (31,070 rows) is formula-recovered and patched.** Native `CalcThermEq` uses both
>    `rIref` and `rM`, so the old managed solver was wrong. The patched `IEEEInverseTimeSolver` now uses
>    the native Therm form; captured EasyPower point fixtures remain the field-sheet promotion gate.
>    `[DLL TccBase.dll CTccLVBreakerCurveGF.CalcThermEq]`
>
> So this gap is **no longer a c4/c5 mystery**: the native kernel formula was recovered from `TccBase.dll`,
> and the remaining work is captured-fixture validation plus the Ansi ship/keep-excluded decision.

**Why it matters for the field sheet:** a tolerance sheet derives PU/TD bands *from* curve values. If
the InvEq curve generator diverges from EasyPower native even slightly, **the tolerance window itself
is wrong** — a worse failure than emitting nothing. The dispatch is trustworthy; the kernel arithmetic
on InvEq curves is not yet certified.

**What closes it (STD Therm CLOSED by native execution 2026-06-01; see §3f):**
1. **DONE:** the Ansi hard-exclude diagnostic is implemented (the 100 Ansi rows / 23 sensors), and
   `CalcAnsiEqGF` is formula-recovered but intentionally not shipped without captured parity fixtures.
   Landed as a backward-compatible dispatch-layer guard in `etu_delay_routing.py`
   (`gf_inveq_is_excluded_ansi`, `id_open_eq` threaded through `dispatch_gfd_delay` + `route_delay_curve`).
2. **DONE:** `CalcThermEq` was recovered from `TccBase.dll`, the c4/c5 verdict is **uses both**, and the
   managed solver was patched in `etu_curves.py`.
3. **DONE (the field-trust gate) — STD Therm:** the captured-fixture validation was satisfied by the
   **strongest available oracle: executing the native kernel itself** (`TccBase.dll` `CalcThermEq` /
   `CalcThermEq3` invoked in-process; §3f). STD Therm is reproduced **BIT-EXACT** over its complete
   4-dial corpus → **STD-INVEQ Therm PROMOTED to "db"** in `delay_trust.py`
   (`inveq_therm_native_parity.json` + `test_inveq_therm_native_parity.py`, 12 tests).
4. **REMAINING — GF Therm:** the same oracle showed the **GF runtime uses `byICalc=1`
   (`num3=field13` ≠ pickup)**, which the managed `num3=num6` solver does not reproduce (and `rIRef<rM`
   GF rows return None). GF-INVEQ Therm stays **"verify"**; the bounded next step is to recover
   `field13`'s provenance (the device current basis), thread it into the solver, and re-validate against
   this oracle. Then the 1,690+6,760 GF Therm rows can promote.
5. **DECISION — Ansi:** `CalcAnsiEqGF` is recovered (future-ready) but the 23 Ansi sensors / 100 rows
   remain **hard-excluded** (recommended status quo); wiring it is deferred until a real Federal-Pioneer
   GF inverse-eq job appears. (Operator decision surface — keep-excluded is the safe default.)
`[DLL-EXEC TccBase.dll 2026-06-01 §3f]` `[06 §R1, §provenance-notes]` `[00-MASTER-INDEX §5]`

**Secondary InvEq residual `[CLOSED 2026-06-01]`:** the translator branch `*ICalc=0 → byICalc=2 →
ref[12]` (pass-5) is **never exercised** — a direct `[VERIFIED-LIVE]` count finds **zero rows** with any
`*ICalc=0` in `DatSection3InvEq`/`DatSection1GfInvEq` (STD `IdOpICalc≡4`; GF `∈{1,4,8}`). `[06 §R4]` answered.

---

## 6. Sensor-gating rule for the MVP (how a field sheet must gate each sensor)

A field-tolerance sheet **must classify every sensor by its delay-calc route before deciding what to
emit.** This is the operational form of the Field-Trust Matrix — apply it per sensor, per element.

**Gating algorithm (per sensor):**

1. **Always emit PU tolerances.** Read `*_tol_hi`/`*_tol_lo` per element straight from the persisted
   per-sensor data and emit them. Always safe (row 1). Use the per-sensor values, **not** a NETA
   default band. If an override applies, use the override's own tolerance pair.

2. **Emit pickup currents** for methods 0-7 (simple multiply). If `SSTCalcMethod ∈ {8,9,10}` for an
   element being shipped, mark that element's pickup **unresolved** (do not emit 0).

3. **Read the delay-calc route** for each delay element:
   - **STD:** `stpu_delay_calc_code` (from `DS3_SEC3_I2T`)
   - **GFD:** `ground_delay_calc_code` (from `DS1GF_SEC3_I2T`)

4. **Emit full TD windows for proven routes:** direct-band route **`= 0`** (NONE STD `DatSection3STD` /
   GFD `DatSection1GfGFD`), the **LTD window** (methods 1-5), **constant-mode STPU overrides**, **and
   `STD` INVEQ route `= 2` Therm** — the latter validated BIT-EXACT against the native `CalcThermEq`
   kernel (§3f), so STD InvEq Therm now ships as **"db"**. These are rows 3/4/5/6/13.

5. **FLAG (`"verify"`) the GFD InvEq route (`= 2`) Therm:** the GF runtime uses `byICalc=1`
   (`num3=field13` ≠ pickup) which the managed `num3=num6` solver does not yet reproduce (and `rIRef<rM`
   GF rows return None; §3f). Surface the GFD InvEq Therm curve flagged "verify — engine estimate", not
   as field-authoritative. Promotion to "db" is gated on `field13` provenance + oracle re-validation
   (4,524 STD already promoted; ~1,690+6,760 GF Therm pending).

6. **HARD-EXCLUDE the stubs/deferred routes:** any sensor whose delay element routes to **I2X (`=1`)**,
   **TUSTD (`=3`)**, **TUG (`=4`)**, **WEG OCR Type A pickup (`DS1GF_PICKUP_CALC = 6`)**, the
   **GF-InvEq ANSI family (`id_op_eq != 0` on an INVEQ GFD row — 23 sensors / 100 rows; §3e/§5 row 7)**,
   or the **INST `Sec4Inst*` override** surface must be shown as **"unsupported / withheld"**, never a
   default number. A silent fall-through diagnostic is *not* a curve — do not let it become one on a
   sheet. *(The GF-InvEq ANSI exclusion is wired in `etu_delay_routing.py`; pass `id_op_eq` to
   `route_delay_curve` / `dispatch_gfd_delay` so the gate fires.)*

7. **Consume the current dispatcher, not a stale forward-port.** Behavior authority is the
   source-domain demo (`etu_delay_routing.py` for InvEq dispatch); verify the sheet generator reads
   the *current* dispatcher, not a lagging forward-port. `[06 §R5]`

**One-sentence MVP gate:** *PU tolerances ship for every sensor; TD windows ship for direct-band
(route 0) + LTD + constant-mode overrides **+ STD-INVEQ (route 2) Therm (native-execution PROVEN)**;
GFD-INVEQ (route 2) Therm is flagged "verify"; everything else (I2X, GE-TU, GF-INVEQ Ansi, INST override)
is hard-excluded.*

---

## 7. Cross-references

- The selection routing that *picks the sensor* (cascade, `GetDefaultTripInfo` stitch, cross-filter) and the calc-dispatch routing columns (`DS*_PICKUP_CALC`→SSTCalcMethod, `DS*_SEC3_I2T`→SSTDelayCalc) → **G3**.
- The trip-family model (SST/ETU · TMT · EMT) and how breaker selection reaches a sensor → **G0**.
- The full DVL-flag data dictionary, the persisted `tcc.*` schema, the dropped-column register → **G1**.
- The frozen baselines, the deferred-work ledger + reopen-triggers, reference-of-record vs forward-port governance → **G2**.

---

## 8. Provenance ledger (anchors any future re-validation)

- **Authoritative runtime surfaces:** `source-domains/tcc_v5_backend/services/calc_engine/etu_delay_routing.py` (InvEq dispatch) + `etu_curves.py` (`IEEEInverseTimeSolver` — the kernel UNTOUCHED by the InvEq campaign) + `etu_ltd.py` (`ETULTDCalculator`, 5 methods).
- **Authoritative contract (host-only `[OPEN-VALIDATION]`):** `EASYPOWER-CALC-ENGINE-SPEC.md` (§G STD InvEq / §J GF InvEq / §N open Qs / §O downstream auth) — note spec line-766 wording left stale at pass-5 closure pending spec-rewrite.
- **Constant tables (engine-recovered):** `[09]` `DVL_SST_SETTING_*` / `SSTDelayCalc` from `EasyPower.DeviceLibrary` (`SSTCalcMethod.cs`, `DeviceLibrary.cs:37-85`); no physical `.h` headers exist — the managed C# mirror is authoritative.
- **InvEq binding evidence (pass-5):** `…/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md` (§12 binding matrix, §8 translator) — the canonical anchors for the InvEq parity packet.
- **Tests:** `test_series_b_safe_parity.py` (direct-band, 8) · `test_etu_delay_routing.py` (dispatch, 43) · `test_inveq_representative_validation.py` (InvEq representative, 18).
- **DLL mapping:** `source-domains/tcc_v5_backend/DLL_END_TO_END_MAPPING.md` + `DLL_SEMANTIC_FINDINGS.md` (per-element calc methods, SSTDelayCalc/SSTCalcMethod semantics, 17,831-sensor value distributions).
- **Discovery digests:** `_discovery/06-handoffs-digest-calc-inverse-equation.md` (solver-coverage matrix, InvEq parity gap, R1-R5) · `_discovery/09-dvl-constants-and-enums.md` (pickup/delay enum constant tables).

---

*End of G4 — Calc Guide (DRAFT, pending Desktop validation).*
