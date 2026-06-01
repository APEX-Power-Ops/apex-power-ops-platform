# G4 — Calc Guide (Pickup · Tolerance · Delay/Curve Solvers · the Field-Trust Matrix)

> **Owns:** the math and the trust. For any element of an ETU/SST trip — LTPU/STPU/INST/GFPU — this
> guide says *which formula computes its pickup, where its tolerance comes from, which solver draws
> its delay/curve, and whether the resulting number is trustworthy enough to hand a NETA technician.*
> The centerpiece is **§4 — the Field-Trust Matrix** (`PROVEN | BOUNDED | DEFERRED | STUB`). Every
> packet that computes or ships a pickup/delay/tolerance value cites this guide.
>
> Status: DRAFT — agent-authored 2026-05-31; **pickup formulas validated against `SSTSensorRecord` primary source 2026-05-31 (Desktop)**
> Last validated · 2026-05-31 (pickup formulas vs `SSTSensorRecord.cs`; enum vs `SSTCalcMethod.cs`; INVEQ loader reconciled vs pass-2..5; **INVEQ managed-evaluator characterized live + corpus distribution measured — §3e**) · Desktop · Open gaps: **InvEq *evaluator* parity — now SPLIT (§3e/§5): (a) 100 GF Ansi sensors BROKEN/now-fixable; (b) 31,070-row Therm corpus is one bounded LOCAL Ghidra fn from PROVEN (`EasyPower.exe` on disk → no longer host-blocked)** · GE-TU-STD/Gnd · I2X-255 · WEG OCR-A pickup `[STUB]` · INST `Sec4Inst*` `[DEFERRED]` · LTD `DS2_DLY_PTY` `[DEFERRED]`

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
| **I2X** route `= 1` | `DatSection3STD` `i2x`/`exp_x` slope | **no — not implemented** | no | I²t solver not built `[DLL_END_TO_END_MAPPING §6/§16, "I²t solver value 1 not implemented"]` |
| **INVEQ** route `= 2` (STD) | `DatSection3InvEq` → `IEEEInverseTimeSolver` | **yes — dispatch wired** | **NO — dispatch only, numbers not validated** | `*Eq=0` uniform, `*ICalc=(10,10,4,4)` integrity, `InOut∈{0,2}` switch → IEEE solver; 4,524 sensors `[06 §matrix / §synthesis-4]` |
| **INVEQ** route `= 2` (GFD) | `DatSection1GfInvEq` → `IEEEInverseTimeSolver` | **yes — full chain bound** | **NO — dispatch only, numbers not validated** | populator `FUN_01207bf0` → reader `nSection=5` → 8 setters; slot matrix BOUND ×3; `byICalc=(in==0)?2:(in==1)?1:0`; Therm/Ansi = IdOp `*Eq` byte; 1,713 sensors `[06 §matrix, pass-5]` |
| **TUSTD** route `= 3` | GE trip-unit STD | **no — fall-through diagnostic only** | no | "Enteliguard not supported", 235 sensors `[DLL_END_TO_END_MAPPING §6/§summary]` `[06 §matrix]` |
| **TUG** route `= 4` | GE trip-unit ground | **no — fall-through diagnostic only** | no | GE-TU-Gnd routing not implemented, 209 sensors `[06 §matrix]` |

**Supporting InvEq recoveries that ARE proven** (the *dispatch*, not the curve numbers):
- **`*ICalc → byICalc` translator** `FUN_01208640`: `byICalc = (in==0)?2 : (in==1)?1 : 0` → on `{1,4,8,10}` gives `1→1, 4→0, 8→0, 10→0`. **PROVEN** (native + Python verbatim). `[06 §matrix, pass-5]`
- **Slot identity** (slot1=flat-open … slot4=inverse-clear; row offsets 0x08/0x3C/0x70/0xA4). **PROVEN** (in-function MOVSS+CALL). `[06 §matrix, pass-5]`
- **Therm-vs-Ansi selector** = IdOp `*Eq` byte at row offset 0x70 (whole-row). **PROVEN.** `[06 §pass-5]`

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

- **Corpus distribution (live, exact):** STD (`DatSection3InvEq`, 22,620 rows) is **100% Therm** (zero
  Ansi). GF (`DatSection1GfInvEq`, 8,550 rows) = **8,450 Therm + exactly 100 Ansi** (the Federal Pioneer
  block, `IdOpEq=1`). So **Ansi exists in only 100 rows of the entire corpus**; 31,070 rows are Therm. `[VERIFIED-LIVE 2026-05-31]`
- **The managed formula** (`etu_curves.py:405-446`): `T = (c1 / (I_norm^c2 − 1) + c3 + c6) × time_dial`,
  then `× (1 + tol/100)`. It loads 6 slots into `c1..c6` but **uses only c1, c2, c3, c6 — silently
  ignoring c4 and c5** (the DB `*4`/`*5` slots = native `rIref`/`rM`). `[VERIFIED-LIVE 2026-05-31 — code read]`
- **Two defects provable TODAY (no native work):**
  1. **Ansi → no curve.** Every Ansi row has `c2 = 0`, so `I^0 − 1 = 0` → singularity guard → `_evaluate`
     returns `None` → the point is skipped → **empty curve**. The 100 Federal Pioneer Ansi GF sensors
     produce **no time-delay curve at all** — worse than withholding (it silently yields nothing). `[VERIFIED-LIVE 2026-05-31]`
  2. **Therm c4/c5 dropped.** STD and GF Therm rows yield **identical** managed output despite `c4`
     differing (STD `rIref`=10 vs GF `rIref`=1) — because c4 is ignored. Whether native `CalcThermEq`
     actually uses `rIref`/`rM` is exactly what the bounded Ghidra fn must settle; if it does, managed
     Therm is *wrong*, not merely unvalidated. `[INFERENCE → Ghidra-confirm]`
- **Native side: GO (bounded).** The evaluator math is **confirmed absent on disk** (the decomp tree
  holds only empty `[NativeCppClass]` stubs; passes 1–5 recovered only the loader/dispatch). A
  Ghidra-headless run on `D:\EasyPower\EasyPower.exe` is needed but **bounded to 2 functions** —
  `CalcThermEq` + `CalcAnsiEqGF` (+ ≤4 setters for slot order) — seeded from pass-5 populator
  `FUN_01207bf0`. Independent `[DLL]` corroboration of the 5/6 split: `GFInverseEqDelayData.cs` declares
  `sTherm`=40B and `sAnsi`=48B (exactly +1 float). `[VERIFIED-LIVE 2026-05-31]` `[06 pass-5]`

---

## 4. THE FIELD-TRUST MATRIX  ← the centerpiece

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
| 6 | **STD-side INVEQ curve NUMBERS** | `DS3_SEC3_I2T = 2` (4,524 sensors, **100% Therm**) | **BOUNDED** (managed ignores coeffs c4/c5; one local Ghidra fn from PROVEN — §3e/§5) | **NO — withhold the TD window; dispatch-only** until the `CalcThermEq` parity check runs. | dispatch PROVEN, numbers NOT `[06 §synthesis-4, R1]` `[VERIFIED-LIVE 2026-05-31]` |
| 7 | **GF-side INVEQ curve NUMBERS** | `DS1GF_SEC3_I2T = 2` (1,713 = **1,613 Therm + 100 Ansi**) | **Therm = BOUNDED** (as row 6); **Ansi = BROKEN → STUB** | **Therm: withhold (as row 6). The 100 Federal Pioneer Ansi sensors: HARD-EXCLUDE — the managed solver emits NO curve (c2=0 singularity), a now-fixable defect (§3e/§5).** | pass-5 BOUND ×3; Ansi defect `[VERIFIED-LIVE 2026-05-31]` `[06 R1]` |
| 8 | **WEG OCR Type A pickup** | `DS1GF_PICKUP_CALC = 6` (§N.4, 7 sensors) | **STUB** | **NO — hard-exclude.** Pickup formula UNKNOWN; curve deliberately withheld. Show "unsupported". | diagnostic exclusion `[06 §matrix §N.4]` |
| 9 | **GE-TU-STD** | `DS3_SEC3_I2T = 3` (235 sensors) | **DEFERRED / STUB** | **NO — hard-exclude.** Fall-through diagnostic only; not solved. | "Enteliguard not supported" `[06]` `[DLL_END_TO_END_MAPPING]` |
| 10 | **GE-TU-Gnd** | `DS1GF_SEC3_I2T = 4` (209 sensors) | **DEFERRED / STUB** | **NO — hard-exclude.** Fall-through diagnostic only. | `[06 §matrix]` |
| 11 | **I2X solver** | `DS3_SEC3_I2T = 1` (8,708 sensors) | **DEFERRED / NOT IMPLEMENTED** | **NO — hard-exclude.** I²t/Iˣ·t solver not built; (`I2X=255` §N.2 also open). | `[DLL_END_TO_END_MAPPING §6/§16]` `[06 §N.2]` |
| 12 | **INST override** (`Sec4Inst*` / `DS4_OVR_*`) | INST-override path (§N.5 / §K) | **STUB / DEFERRED** | **NO — hard-exclude / withhold.** INST curve-calc surface unresolved; override math native-only, not read by managed lib. | `[06 §N.5, §K]` `[09 §4f]` |
| 13 | **STPU override (band routing)** | `tcc.etu_stpu_overrides` (3 sensors) | **PARTIAL** | **Constant-mode override pickup + override tolerances OK; decreasing-mode curve = withhold.** Override *routing* covered in TASK-C; broader override math deferred. | `[06 §matrix]` `[DLL_SEMANTIC_FINDINGS §4]` |

**The one-line rule the matrix encodes:** *ship rows 1-5 (and constant-mode override 13); withhold
rows 6-7 Therm-INVEQ (flag, do not emit numbers); **hard-exclude the 100 GF Ansi sensors (broken — no
curve) and rows 8-12.***

---

## 5. The InvEq numeric-parity gap (the #1 open calc question)

**Statement of the gap `[OPEN-VALIDATION]`:** Both InvEq routes (STD `DS3_SEC3_I2T = 2` and GFD
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
> 1. **The Ansi half is BROKEN and fixable NOW (no native work).** Only **100 sensors** corpus-wide are
>    Ansi (Federal Pioneer GF, `IdOpEq=1`); the managed solver hits a `c2=0` singularity and emits **no
>    curve** for them. Action: hard-exclude with an INV-7 diagnostic (like WEG OCR Type A) so they never
>    ship a blank curve. Closes the *dangerous* half immediately. `[VERIFIED-LIVE 2026-05-31]`
> 2. **The Therm half (31,070 rows) is one bounded Ghidra function from PROVEN.** The managed solver
>    drops coeffs c4/c5; whether native `CalcThermEq` uses `rIref`/`rM` decides whether managed Therm is
>    merely unvalidated or actually wrong. The native evaluator is **absent from the decomp** (only
>    stubs), so a Ghidra-headless run on `D:\EasyPower\EasyPower.exe` — **local and tractable**, bounded
>    to `CalcThermEq` (+`CalcAnsiEqGF` only if a Federal Pioneer GF job appears) — is the close.
>    `[INFERENCE → Ghidra-confirm]`
>
> So this gap is **no longer host-blocked**: the earlier "needs host-only spec" framing is superseded —
> `EasyPower.exe` is on disk. It is a bounded, locally-runnable check.

**Why it matters for the field sheet:** a tolerance sheet derives PU/TD bands *from* curve values. If
the InvEq curve generator diverges from EasyPower native even slightly, **the tolerance window itself
is wrong** — a worse failure than emitting nothing. The dispatch is trustworthy; the kernel arithmetic
on InvEq curves is not yet certified.

**What closes it (smallest next step, sharpened 2026-05-31):** split the work —
1. **Now (no native, no host spec):** add the Ansi hard-exclude diagnostic (the 100 Federal Pioneer GF
   sensors) so the broken half never ships a blank curve, and unblock the Therm half for the field sheet
   as BOUNDED-pending-Ghidra. This is a small calc-engine change against `etu_delay_routing.py` —
   *surfaced for operator authorization, not yet actioned.*
2. **Then (one bounded local Ghidra run):** decompile native `CalcThermEq` from
   `D:\EasyPower\EasyPower.exe`, resolve whether it uses c4 (`rIref`) / c5 (`rM`), and confirm-or-patch
   the managed solver — moving the 31,070-row Therm corpus BOUNDED→PROVEN. Seed from pass-5 §12 binding
   matrix + §8 translator + populator `FUN_01207bf0`. The host-only `EASYPOWER-CALC-ENGINE-SPEC.md`
   (§G/§J/§N/§O) would *corroborate* but is **no longer required** — the binary is local.
`[VERIFIED-LIVE 2026-05-31]` `[06 §R1, §provenance-notes]` `[00-MASTER-INDEX §5]`

**Secondary InvEq residual `[OPEN-VALIDATION]`:** pass-5 proved the translator branch `*ICalc=0 →
byICalc=2 → ref[12]`, but whether **any DB row actually stores `*ICalc=0`** is an unresolved DB-fact
check (`[06 §R4]`). It does not block the parity packet but should be answered alongside it.

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

4. **Emit full TD windows ONLY for proven direct-band routes:** route **`= 0`** (NONE/direct-band STD
   `DatSection3STD` / GFD `DatSection1GfGFD`). Plus the **LTD window** (methods 1-5, implemented) and
   **constant-mode STPU overrides**. These are the rows-3/4/5/13 surfaces.

5. **FLAG and WITHHOLD the InvEq routes (`= 2`):** do **not** emit a TD window number for an InvEq
   sensor (STD or GFD). Surface it as "inverse-equation curve — pending numeric validation" rather
   than a number. The dispatch is correct but the numbers are uncertified (§5). ~6,200 sensors.

6. **HARD-EXCLUDE the stubs/deferred routes:** any sensor whose delay element routes to **I2X (`=1`)**,
   **TUSTD (`=3`)**, **TUG (`=4`)**, **WEG OCR Type A pickup (`DS1GF_PICKUP_CALC = 6`)**, or the
   **INST `Sec4Inst*` override** surface must be shown as **"unsupported / withheld"**, never a default
   number. A silent fall-through diagnostic is *not* a curve — do not let it become one on a sheet.

7. **Consume the current dispatcher, not a stale forward-port.** Behavior authority is the
   source-domain demo (`etu_delay_routing.py` for InvEq dispatch); verify the sheet generator reads
   the *current* dispatcher, not a lagging forward-port. `[06 §R5]`

**One-sentence MVP gate:** *PU tolerances ship for every sensor; TD windows ship only for direct-band
(route 0) + LTD + constant-mode overrides; InvEq (route 2) is flagged-and-withheld; everything else is
hard-excluded.*

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
