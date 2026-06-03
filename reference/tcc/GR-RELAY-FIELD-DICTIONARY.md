# GR Relay Field Dictionary — Access source columns + DVL type-flag descriptions

> **The relay parallel to the breaker "08 DVL-flag dictionary."** Every column of every relay table in the
> source Access master, with the **`Description` (DVL type-flag) text** captured verbatim from the Access
> table definitions. Cite this for the meaning of any relay column. The decisive use this campaign:
> **settling, multi-source, where relay tolerances live (they don't — see the headline).**

- **Source:** `D:\TCC_NEW.accdb` (the filtered EasyPower `Stdlib.mdb`), read **read-only via DAO**
  (`DAO.DBEngine.120`, the `Description` field property) on **2026-06-03**. `[VERIFIED-LIVE 2026-06-03]`
- **Scope:** 22 `Relay*` source tables · **154 fields · 30 carry a `Description`**.
- **Type legend** (DAO `Field.Type`): `2`=Byte · `4`=Long · `6`=Single(float) · `10`=Text · `12`=Memo.
- **Home:** `apex-power-ops-platform/reference/tcc/` · cited by `GR-RELAY-REFERENCE.md` (§2/§6/§7).

---

## Headline — relay tolerances are NOT in EasyPower (triangulated)

A keyword scan of governed column *names* alone is not enough to conclude this, so it was checked across
**all three sources** + the breaker contrast:

1. **Governed `tcc.relay_*`** (21 tables, full column inventory) — **no** tolerance/accuracy column.
2. **Source Access `D:\TCC_NEW.accdb`** (22 tables, 154 fields **+ the DVL descriptions below**) — **no**
   tolerance column and **no description mentions tolerance/accuracy/percent/band**. The relay model is
   purely **settings** (`RelayRanges` adjustable range + `RelayDiscreteValues`) **+ curves** (per-family
   coefficients or the TCP point grid).
3. **DLL (`TccBase`/`dbBase` decompile)** — no `*Relay*`/`*REL*` file references tolerance; `CdbRELRow` is a
   **size-only `[NativeCppClass]` shell** (empty struct, `Size=516`). No native relay tolerance logic.
4. **The decisive contrast (same Access file + same DLL):** the **breaker/ETU/EMT** side DOES carry
   tolerance — `DatSensor.DS1/DS2/DS3/DS4_TOL_HIGH/LOW` + `DS4_OVRTOL_MIN/MAX`, `DatSensorSec2.DS2_TOL_*`,
   `DatSensorMaint.DS*_TOL_*`, `Breaker{ICCB,MCCB,PCB}Styles.{,N}InstOvr{Min,Max}Tolerance`,
   `EMT_Sections.PickupToler{High,Low}`, `DatSection3STOvr.OvrToler{High,Low}Pct`.

**Conclusion:** EasyPower **deliberately** models breaker tolerance bands but renders **relays as nominal
curves** (no tolerance). → Relay NETA tolerances must be sourced **externally** — the NETA standard
acceptance band (the always-available floor) + the relay manufacturer's published accuracy spec
(`[VENDOR-DOC]`, the validated-library loop). There is **no EasyPower-DB tolerance path for relays**
(unlike breakers). This confirms the roadmap **Chip 3** two-tier source model is the only viable one.

---

## Field dictionary (by table) — described fields highlighted

> Fields with no `Description` in Access are listed compactly; the **bold** ones carry a DVL flag.

### `Relays` (relay identity)
- `ID` (4) · **`Mfr_ID` (4): Link to Manufacturers.ID** · `Type` (10) · `Note` (12) ·
  **`MultFunction` (4): 0 = single function, 1 = mult function** ·
  **`DCOffsetFilter` (4): 0 = Off, 1 = On** · **`RelayClass` (4): 0 = Other, 1 = Motor, 2 = Generator** ·
  `RelayConstr` (2)

### `RelayDevices` (one per ANSI device-function; carries the SST-2 bridge)
- `ID` (4) · **`Relay_ID` (4): Link to Relays.ID** ·
  **`DeviceFunction` (10): 51/50,51/50N,67, 67N etc.. (similar to other equipment's style)** · `Ordinal` (4) ·
  **`Standard` (2): 0=ANSI, 1=IEC, 2 = Both** · `DFType` (2) · `Use_SST` (2) ·
  `SST_Mfr` (10) · `SST_Type` (10) · `SST_Style` (10)

### `RelayLineSection` (pickup/tap section — note the unfinished "decide" fields)
- `ID` (4) · **`Device_ID` (4): Link to RelayDevices.ID** · **`SectionNumber` (2): Available values: 1, 3, 4** ·
  **`Name` (10): Section name** · **`Pickup` (2): Option field (Chet to decide)** ·
  **`SecondaryI` (4): To decide** · **`Amps` (4): Option field. 0 or 1** · `UseTOCMult` (4)
  > `Pickup`/`SecondaryI` are **DESIGN-OPEN source fields** ("Chet to decide" / "To decide") — do not rely on
  > them (GR §7).

### `RelayTDSection` (the curve section)
- `ID` (4) · **`Device_ID` (4): Link to RelayDevices.ID** · `Name` (10) ·
  **`Model` (2): Option field: 0 = Bassler formula, 1 = TD Points** ·
  **`Type` (2): Applies to TD Points Model: 0 = Discrete, 1 = Continuous** · `AllowTripLtStDelay` (4)
  > NB the **`Description` says `Model` is binary "0 Bassler / 1 TD Points"** — but the DATA uses the full
  > **0–8 family dispatcher** (GR §3, the engine-over-DB win). The description is the misleading-DB case;
  > trust the data + DLL.

### `RelayRanges` (polymorphic setting range; the adjustable bounds — NOT a tolerance)
- `ID` (4) · **`ParentID` (4): Link to RelayLineSection.ID** · **`AuxKey` (4): Used by TD section tables** ·
  `Ordinal` (4) · `Min` (6) · `Max` (6) ·
  **`Step` (6): If Null, then the range takes discrete values from table DiscreteValues** ·
  `RelUnit` (4) · `UseRange` (4) · `RangeKey` (4) · `ScaleWithTimeMultiplier` (4)

### `RelayDiscreteValues` (discrete setting values)
- **`Range_ID` (4): Link to RelayRanges.ID** · `Value` (6) · `Description` (10)

### `RelaySec2{IEC,SWZ,MEQ,PCD,BSL,LRM,RXD,EGC}` (per-family curve headers)
- `ID` (4) · **`Section_ID` (4): Link to RelayTDSection.ID** · `MinPickup` (6) · `MaxPickup` (6)
  *(LRM also `LRUnit` (4))* — `MinPickup`/`MaxPickup` = the pickup **range the curve covers**, not a tolerance.

### `RelaySec2{IEC,SWZ,MEQ,PCD,BSL}Curves` (per-family curve coefficients)
- `ParentID` (4) · `CurveName` (10) · `Ordinal` (4) · coefficients `vA,vB,vC,…` (6).
  - IEC: `vK,vE,DTAfter,DTMinTime` · SWZ: `vA,vB,vE` · MEQ: `vA..vE` · PCD: `vA,vB,vC` · BSL: `vA,vB,vC,vD,vN,vK,vR`.
  - **`RelaySec2MEQCurves.ParentID` Description says "Link to RelaySec2IEC.ID" — this is WRONG** (the data
    links to `RelaySec2MEQ.ID`, GR §2 correction). Another misleading-description case.

### `RelaySec2TCP` / `RelaySec2TCPCurves` (the Time/Current point grid, Model 1)
- `RelaySec2TCP`: `ID` (4) · **`Section_ID` (4): Link to RelayTDSection.ID** · `CurveName` (10) ·
  `TCCNumber` (10) · `Ordinal` (4) · **`Discrete` (4): 1 - discrete, 0 - continuous** ·
  **`StepSize` (6): Used only if continuous** · `HorzAmps` (2)
- `RelaySec2TCPCurves`: **`ParentID` (4): Link to RelaySec2TCP.ID** ·
  **`TimeDial` (6): If TimeDial=-100.0 then the row identifies pickups** · `TDDesc` (10) · `Ordinal` (4) ·
  `v1..v25` (6) — the point grid (wide→long unpivot to `tcc.relay_curve_points_tcp`).

### `RelayID`
- `UniqueID` (4) — single sequence holder (not migrated).

---

## What the descriptions corrected / confirmed
- **Confirmed** the discrete/continuous sentinel (`RelaySec2TCP.Discrete` 1/0), the `RelayRanges.Step=Null →
  discrete` sentinel, the `TimeDial=-100.0 → pickup-identifier` sentinel, the `Standard` 0/1/2 = ANSI/IEC/Both
  map, and the SST-2 bridge columns.
- **Confirmed two misleading-description cases** (the "trust engine/data over DB-description" rule, 00 §2):
  `RelayTDSection.Model` description says binary but data is the 0–8 dispatcher; `RelaySec2MEQCurves.ParentID`
  description mis-points to IEC.
- **Confirmed `RelayLineSection.Pickup`/`SecondaryI` are unfinished source fields** ("Chet to decide").

## Cross-references
- The relay schema + join graph this details → **`GR-RELAY-REFERENCE.md` §2**.
- The relay field-trust matrix (curves bounded; the external-tolerance consequence) → **GR §6**.
- The roadmap Chip 3 (NETA serving + the external tolerance source) → **`GR-RELAY-ROADMAP.md`**.
- The breaker DVL flags this parallels → the breaker `_discovery/08` DVL-flag dictionary + **G1**.
