# G1 — Schema Guide (Access → staging → Supabase `tcc.*`, the join graph, the DVL data dictionary, lineage + dropped-column register)

> **Owns:** the TCC data model end-to-end — the 79 Access user tables and their domains, the declared + logical join graph, the decoded DVL-flag / engine-constant dictionary, the `DatX → *_aligned → tcc.*` lineage, and the register of columns that exist in source Access but are absent in the governed Supabase `tcc.*`. Cite this guide when touching any table, column, loader, or migration.
>
> **Status: DRAFT (agent-authored 2026-05-31; deep-validated vs both live DBs 2026-05-31)**
> Last validated · 2026-05-31 · Desktop (Access OLEDB + Supabase `tcc.*`; 64 claims: 56 MATCH / 4 corrected / 4 refined — `_discovery/_validation/v1-g1-schema-validation.md`) · Open gaps — **all four prior gaps CLOSED:**
> - (1) the 4 SST-bridge columns are **confirmed ABSENT** from `tcc.brk_*_styles` (0/4 live) `[VERIFIED-LIVE 2026-05-31]`
> - (2) the **relay** SST-bridge was **CARRIED, not dropped** — D2 reversed (`tcc.relay_devices` has `use_sst`/`sst_manufacturer`/`sst_type`/`sst_style`) `[VERIFIED-LIVE 2026-05-31]`
> - (3) `DatStyle` = **2,094** (OLEDB authoritative + `tcc.trip_styles`=2,094; the 14,248 CSV estimate discarded) `[VERIFIED-LIVE 2026-05-31]`
> - (4) the EMT breaker-selection edge is **RESOLVED** standalone-only (G0 §5) `[VERIFIED-LIVE 2026-05-31]`
> - count corrections applied below: `EMT` 1,177→**174**, `Relays` 8,395→**1,442**, MCCB `Use_SST=1` 1,704→**1,680** (load-relevant figures unchanged). Governed-load delta flagged: `tcc.brk_mccb` 599 vs Access 640.

**Tag legend** (per 00-MASTER-INDEX §2; conflict rule `[DLL]` > `[DVL-DB]` > inference):
`[VERIFIED-LIVE <date>]` re-queried live · `[DLL <file:line>]` decompiled engine · `[DVL-DB <table.col>]` Access field description · `[HANDOFF <id>]` prior closeout · `[INFERENCE]` reasoned · `[DEFERRED]` known-incomplete · `[OPEN-VALIDATION]` not closable from current sources.

Evidence base for this guide: discovery artifacts `01` (table inventory + linkage), `02` (saved-query join map), `04` (live `.accdb` FKs + bridge population), `08` (DVL flag dictionary), `09` (engine constants); plus `source-domains/tcc_v5_backend/DLL_END_TO_END_MAPPING.md` and `DLL_SEMANTIC_FINDINGS.md`. Cross-refs: trip-family model + bridge mechanism → **G0**; deferred ledger + governance → **G2**; routing/calc-dispatch constant tables → **G3/G4**.

---

## 1. Domain map — the 79 Access user tables

**79 user tables total** (excluding `MSys*`/`~*`/linked), 952 fields, 110 described. `[VERIFIED-LIVE 2026-05-31 OLEDB]` `[04]` `[08]`

"In-TCC-scope" = part of the EasyPower LV trip-curve domain the platform migrates/uses (breaker hardware + the 3 trip families + curve sections + the shared Manufacturers dimension). "Adjacent / non-TCC" = present in the same `.accdb` but explicitly out of scope (cable, fuse, HV, switch, arc-flash, design/estimating, system) — these are NOT migrated to `tcc.*`. `[DLL DeviceLibrary.cs §15]`

### 1A. Breaker hardware — frame/rating layer (IN SCOPE)
| Table | #Cols | ~Rows | Role |
|---|---:|---:|---|
| `BreakerICCB` | 5 | 29 | ICCB family (parent): `ID, Mfr_ID, Type, cStandard, Acdc` |
| `BreakerICCBStyles` | 68 | **608** | ICCB styles (child). Carries `TMT_SST_*` bridge. |
| `BreakerMCCB` | 5 | 640 | MCCB family (parent) |
| `BreakerMCCBStyles` | 68 | **10,335** | MCCB styles (child). Carries `TMT_SST_*` bridge. |
| `BreakerPCB` | 5 | 157 | PCB family (parent) |
| `BreakerPCBStyles` | 76 | **3,279** | PCB styles (child). Carries `TMT_SST_*` bridge (cols shift to idx 35–38). |
| `Breaker_OvrCurves` | 4 | **0** | empty; inst-override curve points by `StyleID` |
| `Breaker_SelCoord` | 16 | 412,437 | selective-coord lookup (downstream device refs, not breaker→trip) |
| `Breaker_SeriesRated` | 19 | 6,393 | series-rated combos (downstream device refs) |

Row counts are the authoritative OLEDB counts; CSV line-counts were 6× inflated by multi-line memo fields (`TMT_Notes`). `[VERIFIED-LIVE 2026-05-31]` `[04 Task 3/6]` `[01 §5]`

### 1B. TMT — Thermal-Magnetic Trip family (breaker-integral curve) (IN SCOPE)
| Table | #Cols | ~Rows | Role |
|---|---:|---:|---|
| `Breaker_TMTFrameSizes` | 26 | 42,238 | TMT frame defs. `StyleID → BreakerXXXStyles.ID` (the breaker→TMT bridge) |
| `Breaker_TMTFrameAmps` | 2 | 67,206 | trip-amp options per `FrameSizeID` |
| `Breaker_TMTFrameSettings` | 5 | 58,041 | adjustable setting ranges per `FrameSizeID` |
| `Breaker_TMTFrameCurves` | 4 | 1,143,458 | curve points (Class/Time/Amps) per `FrameSizeID` |
| `Breaker_TMTThermalTripAdj` | 3 | 21,790 | thermal trip adjustment per `FrameSizeID` |

### 1C. SST/ETU trip units / sensors — the solid-state core (IN SCOPE)
| Table | #Cols | ~Rows | Role |
|---|---:|---:|---|
| `DatStyle` | 9 | **2,094** | trip-unit identity hub: `STYLE_ID, MFG_ID, TYPE, STYLE, NOTES, TCC_NO, TCC2_NO, SENSOR_NAME, SENSOR_TYPE`. The `TMT_SST_*` triple resolves here. *(**2,094** confirmed OLEDB live + `tcc.trip_styles`=2,094; the artifact-01 CSV-estimate 14,248 was multi-line-memo inflation, discarded)* `[VERIFIED-LIVE 2026-05-31]` |
| `DatSensor` | 93 | 17,831 | sensor/plug core (the 93-col table). `StyleID → DatStyle.STYLE_ID` |
| `DatSensorMaint` | 59 | 2,572 | maintenance-mode per-sensor overrides. `SensorID → DatSensor` |
| `DatSensorParms` | 5 | 136,384 | generic per-sensor params (`Section, Index, Value, CurveID`) |
| `DatSensorSec2` | 14 | 3,919 | per-curve Section-2 settings; `CurveID` PK |
| `DatSettings` | 6 | 3,514 | setting descriptions per `SensorID` |
| `DatPlugs` | 2 | 49,901 | plug values (`SensorID, PlugVal`) |

### 1D. Curve sections — the TCC math per sensor (IN SCOPE)
| Table | #Cols | ~Rows | Section |
|---|---:|---:|---|
| `DatSection1Sett` | 2 | 128,718 | LTPU settings (`LTD_SETTING`) |
| `DatSection1Mult` | 2 | 4,832 | LT multiplier (`LTD_C`) |
| `DatSection1GfGFD` | 15 | 72,464 | ground-fault delay |
| `DatSection1GfGFP` | 4 | 65,871 | ground-fault pickup |
| `DatSection1GfInvEq` | 35 | 8,550 | ground-fault inverse-equation coeffs |
| `DatSection2LTD` | 4 | 158,074 | long-time delay (`+ CurveID`) |
| `DatSection3InvEq` | 35 | 22,620 | short-time inverse-equation coeffs |
| `DatSection3STD` | 10 | 139,643 | short-time delay (Series B reads this **directly**) |
| `DatSection3STOvr` | 6 | **3** | short-time (breaker) override |
| `DatSection3STP` | 3 | 114,754 | short-time pickup |
| `DatSection4InstCurves` | 4 | 94,873 | instantaneous curve points |
| `DatSection4InstPickup` | 4 | 152,449 | instantaneous pickup |

All `DatSection*` key on `SensorID → DatSensor.SensorID`; some also carry `CurveID → DatSensorSec2.CurveID`. Note: there is **no** plain `DatSection1InvEq` — the only Section-1 inverse-equation table is `DatSection1GfInvEq` (ground). `[04 Task 1]` `[01 §1D]`

### 1E. EMT — Electro-Mechanical Trip family (own catalog) (IN SCOPE)
| Table | #Cols | ~Rows | Role |
|---|---:|---:|---|
| `EMT` | 8 | **174** | EMT trip identity (`ID, Mfr_ID, Type, Style, TCCNumber, Note, TripChar, TripPlug`). *(corrected 2026-05-31: was 1,177)* `[VERIFIED-LIVE 2026-05-31]` |
| `EMT_Frames` | 5 | 806 | frames; `StyleID → EMT.ID` |
| `EMT_FrameAmps` | 2 | 1,704 | trip amps per `FrameID` |
| `EMT_Sections` | 16 | 1,768 | section defs; `FrameID → EMT_Frames.ID` (15 described cols — richest EMT routing table) |
| `EMT_BandNames` | 5 | 2,978 | band names per `SecID → EMT_Sections.ID` |
| `EMT_Pickups` | 3 | 6,593 | pickups per `SecID → EMT_Sections.ID` |
| `EMT_Curves` | 4 | 40,808 | curve points per `ParentID → EMT_Sections.ID` |

> **EMT migration status (corrected 2026-05-31):** EMT **IS loaded into `tcc.*`** — all 7 tables exist and are populated under FK enforcement (`emt` 174, `emt_frames` 805, `emt_frame_amps` 1691, `emt_sections` 1765, `emt_band_names` 2971, `emt_pickups` 6587, `emt_curves` 40735; small RI-orphan deltas vs Access). The prior "not yet loaded" reading was stale. What remains open is browsable-UI *exposure* (a frontend question), **not** the data load. The breaker→EMT selection edge is RESOLVED standalone-only (G0 §5). `[VERIFIED-LIVE 2026-05-31]`

### 1F. Manufacturers — shared dimension (IN SCOPE)
| Table | #Cols | ~Rows | Role |
|---|---:|---:|---|
| `Manufacturers` | 2 | **450** | `ID, Mfr_Name`. Target of every `*Mfr_ID`/`MFG_ID`/`MfrID` numeric FK **and** the name-resolution target for the `*_SST_Mfr` text bridges. |

### 1G. Relays — separate protective-device domain (has the same SST bridge) (PARTIAL SCOPE — relay catalog migrated; loaded live per matrix #80 G-3)
| Table | #Cols | ~Rows | Notable links |
|---|---:|---:|---|
| `Relays` | 8 | **1,442** | `Mfr_ID → Manufacturers` *(corrected 2026-05-31: was 8,395; `tcc.relays`=1,442 corroborates)* `[VERIFIED-LIVE 2026-05-31]` |
| `RelayDevices` | 10 | 7,192 | `Relay_ID → Relays`; **`Use_SST, SST_Mfr, SST_Type, SST_Style` bridge** |
| `RelayRanges` | 11 | 34,955 | `ParentID` (polymorphic — points at section or device) |
| `RelayDiscreteValues` | 3 | 40,348 | `Range_ID → RelayRanges.ID` |
| `RelayLineSection` | 8 | 23,991 | `Device_ID → RelayDevices.ID` |
| `RelayTDSection` | 6 | 6,956 | `Device_ID → RelayDevices.ID` |
| `RelaySec2TCP` | 8 | 18,908 | `Section_ID` |
| `RelaySec2TCPCurves` | 29 | 146,912 | `ParentID → RelaySec2TCP.ID` |
| `RelaySec2{BSL,EGC,IEC,LRM,MEQ,PCD,RXD,SWZ}` | 4–5 | various | each `Section_ID`-keyed (`RelaySec2EGC` is **empty**) |
| `RelaySec2{BSL,IEC,MEQ,PCD,SWZ}Curves` | 6–10 | various | each `ParentID → RelaySec2*.ID` |
| `RelayID` | 1 | 1 | single `UniqueID` sequence holder (not migrated to `tcc.*`) |

> **Relay deep-dive → GR.** The relay domain now has its own validated reference:
> **[GR — Relay Reference](GR-RELAY-REFERENCE.md)** (selection model, full schema + join graph, the
> `RelayTDSection.Model` **0–8 curve-family dispatcher**, calc + the relay field-trust matrix, the SST-2
> bridge). Live counts re-confirmed 2026-05-31 (`Relays`=1,442, `RelayDevices`=7,192, `RelayTDSection`=6,956,
> `RelaySec2TCPCurves` 146,912 wide → `relay_curve_points_tcp` 1,570,700 long). The relay calc **kernel is
> native-only + UNRECOVERED** → relay analytical curves are BOUNDED (weaker than breakers); ship-now =
> stored data. Relay SST-2 bridge **carried** (the precedent for the breaker D1 fix). `[VERIFIED-LIVE 2026-05-31]` `[GR]`

### 1H. Generic curves / MOC / stability (adjacent device libraries — NOT in tcc.* TCC scope)
`GenCurveTypes/Styles/Points`, `MOCTypes/Styles/StyleGrid`, `StabilityNames/Types/Data`. `[01 §1H]`

### 1I. NON-TCC domains (present in `.accdb`, NOT migrated to `tcc.*`)
- **Cable/insulation:** `CableDerating, CableParameter, InsulationHV, InsulationLV, InsulationLVAmps, zOldInsulationLV, ResTempFactors, TransmissionLine, TransmissionLineSizes`
- **Fuses:** `FuseHV(+Styles/StyleInfo/TCC/Curves)`, `FuseLV(+Styles/TCC/Curves)`
- **HV breakers / switches:** `BreakerHV, BreakerHVStyles, Switch, SwitchStyles`
- **Arc-flash:** `AFH, AFHTypes, AfhBusTypes, PPELevels, WkPermit, WkPermitTasks`
- **Busway/bus:** `Busway, BuswayAmpacities, DsgnBus`
- **Design/estimating:** `Dsgn*` (Bus, CondCost, Feeder, Motor, Notes, ProtEqp, Sheets, Xfr2), `Demand*`, `CodeFactor*`, `MCC*`, `Panel*`, `StarterSize`, `MCCLoads`, `PanelLoads`
- **Harmonics / ZSI / system-meta:** `HmSpectrum(+Harmonics)`, `ZSISettings`, `zSysDataVersion, zSysEqpGUID, zSysVersion, Table1`

`DeviceLibrary.cs` has SQL for the cable/fuse/HV/switch tables but the DLL mapping marks all of them ❌ "not TCC scope / not needed for NETA ETT." `[DLL DeviceLibrary.cs:765-1306]` `[01 §1I]`

> **`DsgnProtEqp` note:** lives in the design/estimating (non-TCC) domain but carries the third SST bridge (`SSTOpt`/`SSTMfrID`/`SSTType`/`SSTStyle`) — see §2/§3. It is out of `tcc.*` scope but documented because the bridge pattern recurs there. `[01 §4]`

### Empty tables (0 data rows) — carry forward
`Breaker_OvrCurves`, `CodeFactorQuantities`, `MCC`, `MCCLoads`, `Panel`, `PanelLoads`, `RelaySec2EGC`, `Table1` (Access scratch artifact). `[01 §5]`

---

## 2. The join graph (edge table)

Edges are `TableA.col = TableB.col`. **Kind:** `B` = declared FK in the live `.accdb` (44 exist) / numeric-ID join confirmed; `T` = logical text-triple bridge (un-declared, name+type+style); `P` = probable by naming convention. **The breaker→trip-unit bridge is `T` (logical), NOT a declared FK** — that is why a loader expecting a numeric `Manufacturers.ID` silently dropped it. `[VERIFIED-LIVE 2026-05-31]` `[04 Task 2]` `[02 §0.2]`

### 2A. SST/ETU trip-unit core chain (the TCC backbone)
| Edge | Kind | Provenance |
|---|---|---|
| `DatStyle.MFG_ID = Manufacturers.ID` | B (declared FK) | `[04 Task 2]` |
| `DatSensor.StyleID = DatStyle.STYLE_ID` | B (declared FK) | `[04 Task 2]` — the live path; `DatTrip`/`TRIP_ID` do **not** exist in this DB |
| `DatPlugs.SensorID = DatSensor.SensorID` | B (declared FK) | `[04]` |
| `DatSensorMaint.SensorID = DatSensor.SensorID` | B | `[01 §2A]` |
| `DatSensorParms.SensorID = DatSensor.SensorID` | B | `[01]` |
| `DatSensorParms.CurveID = DatSensorSec2.CurveID` | P | `[01]` |
| `DatSensorSec2.SensorID = DatSensor.SensorID` | B | `[01]` |
| `DatSettings.SensorID = DatSensor.SensorID` | B | `[01]` |
| `DatSection1Sett.SensorID = DatSensor.SensorID` | B (declared FK) | `[04]` |
| `DatSection1Mult.SensorID = DatSensor.SensorID` | B (declared FK) | `[04]` |
| `DatSection1GfGFD.SensorID = DatSensor.SensorID` | B (declared FK) | `[04]` |
| `DatSection1GfGFP.SensorID = DatSensor.SensorID` | B (declared FK) | `[04]` |
| `DatSection1GfInvEq.SensorID = DatSensor.SensorID` | B | `[01]` |
| `DatSection2LTD.SensorID = DatSensor.SensorID` | B (declared FK) | `[04]` |
| `DatSection2LTD.CurveID = DatSensorSec2.CurveID` | P | `[01]` |
| `DatSection3InvEq.SensorID = DatSensor.SensorID` | B | `[01]` |
| `DatSection3STD.SensorID = DatSensor.SensorID` | B (declared FK) | `[04]` |
| `DatSection3STP.SensorID = DatSensor.SensorID` | B (declared FK) | `[04]` |
| `DatSection3STOvr.SensorID = DatSensor.SensorID` | B | `[01]` |
| `DatSection4InstCurves.SensorID = DatSensor.SensorID` | B | `[01]` |
| `DatSection4InstPickup.SensorID = DatSensor.SensorID` | B (declared FK) | `[04]` |

### 2B. Breaker hardware chain
| Edge | Kind | Provenance |
|---|---|---|
| `BreakerICCB.Mfr_ID = Manufacturers.ID` | B | `[02 E3]` `[01]` |
| `BreakerMCCB.Mfr_ID = Manufacturers.ID` | B | `[02 E5]` |
| `BreakerPCB.Mfr_ID = Manufacturers.ID` | B | `[02 E7]` |
| `BreakerICCBStyles.BreakerID = BreakerICCB.ID` | B | `[02 E4]` |
| `BreakerMCCBStyles.BreakerID = BreakerMCCB.ID` | B | `[02 E6]` |
| `BreakerPCBStyles.BreakerID = BreakerPCB.ID` | B | `[02 E8]` |
| `Breaker_OvrCurves.StyleID = BreakerXXXStyles.ID` | P | (table empty) `[01]` |
| `Breaker_SelCoord.StyleID (+StyleClass) = BreakerXXXStyles.ID` | P | downstream coord; `DnMfrID → Manufacturers.ID`, `DnType/DnStyle` text `[01 §5.6]` |
| `Breaker_SeriesRated.StyleID (+StyleClass) = BreakerXXXStyles.ID` | P | `DnMfrID → Manufacturers.ID`, `DnType/DnStyle` text `[01]` |

### 2C. TMT (thermal-magnetic) chain — breaker → integral curve
| Edge | Kind | Provenance |
|---|---|---|
| `Breaker_TMTFrameSizes.StyleID = BreakerICCBStyles.ID` | B (declared FK) | `[04 Task 2]` — described as "Reference to Styles.ID" `[DVL-DB Breaker_TMTFrameSizes.StyleID]` |
| `Breaker_TMTFrameSizes.StyleID = BreakerMCCBStyles.ID` | B (declared FK) | `[04 Task 2]` (same column, also FK'd to MCCB; PCB by analogy) |
| `Breaker_TMTFrameAmps.FrameSizeID = Breaker_TMTFrameSizes.ID` | B (declared FK) | `[04]` `[DVL-DB Breaker_TMTFrameAmps.FrameSizeID]` |
| `Breaker_TMTFrameSettings.FrameSizeID = Breaker_TMTFrameSizes.ID` | B (declared FK) | `[04]` `[DVL-DB]` |
| `Breaker_TMTFrameCurves.FrameSizeID = Breaker_TMTFrameSizes.ID` | B | `[DVL-DB Breaker_TMTFrameCurves.FrameSizeID]` `[01]` |
| `Breaker_TMTThermalTripAdj.FrameSizeID = Breaker_TMTFrameSizes.ID` | B | `[01]` |

### 2D. EMT chain
| Edge | Kind | Provenance |
|---|---|---|
| `EMT.Mfr_ID = Manufacturers.ID` | B (declared FK) | `[DVL-DB EMT.Mfr_ID]` `[04]` |
| `EMT_Frames.StyleID = EMT.ID` | B (declared FK) | `[DVL-DB EMT_Frames.StyleID]` `[04]` |
| `EMT_FrameAmps.FrameID = EMT_Frames.ID` | B | `[DVL-DB EMT_FrameAmps.FrameID]` |
| `EMT_Sections.FrameID = EMT_Frames.ID` | B | `[DVL-DB EMT_Sections.FrameID]` |
| `EMT_BandNames.SecID = EMT_Sections.ID` | B | `[DVL-DB EMT_BandNames.SecID]` |
| `EMT_Pickups.SecID = EMT_Sections.ID` | B | `[DVL-DB EMT_Pickups.SecID]` |
| `EMT_Curves.ParentID = EMT_BandNames.ID` | B (100%) | **RESOLVED 2026-05-31:** the DB description ("`EMT_Bands.ID`" = the physically-named `EMT_BandNames`) was RIGHT; artifact 01's "`EMT_Sections.ID`" was WRONG — 100% of 40,808 rows join to `EMT_BandNames.ID` (only 2.7% coincidental overlap with `EMT_Sections.ID`). `[VERIFIED-LIVE 2026-05-31]` `[DVL-DB EMT_Curves.ParentID]` |
| `EMT_BandNames.SecID = EMT_Sections.ID` | B (100%) | the intermediate edge — full chain `EMT_Curves → EMT_BandNames → EMT_Sections → EMT_Frames → EMT` `[VERIFIED-LIVE 2026-05-31]` |

### 2E. Relay chain (parallel SST bridge)
| Edge | Kind | Provenance |
|---|---|---|
| `Relays.Mfr_ID = Manufacturers.ID` | B | `[DVL-DB Relays.Mfr_ID]` `[02 E15]` |
| `RelayDevices.Relay_ID = Relays.ID` | B | `[DVL-DB RelayDevices.Relay_ID]` `[01]` |
| `RelayLineSection.Device_ID = RelayDevices.ID` | B | `[DVL-DB RelayLineSection.Device_ID]` |
| `RelayTDSection.Device_ID = RelayDevices.ID` | B | `[DVL-DB RelayTDSection.Device_ID]` |
| `RelayRanges.ParentID = RelayLineSection.ID` | B | `[DVL-DB RelayRanges.ParentID]` — *polymorphic*: DB description says `RelayLineSection.ID` but artifact 01 flags it as pointing at section **or** device by context `[01 §5.5]` |
| `RelayDiscreteValues.Range_ID = RelayRanges.ID` | B | `[DVL-DB RelayDiscreteValues.Range_ID]` |
| `RelaySec2{BSL,IEC,MEQ,SWZ,TCP}.Section_ID = RelayTDSection.ID` | B | `[DVL-DB RelaySec2*.Section_ID]` |
| `RelaySec2TCPCurves.ParentID = RelaySec2TCP.ID` | B | `[DVL-DB]` `[02]` |
| `RelaySec2MEQCurves.ParentID = RelaySec2MEQ.ID` | B (100%) | **RESOLVED 2026-05-31:** live 1,644/1,644 join to `RelaySec2MEQ.ID` (IEC = 0%); the DB-description `→ RelaySec2IEC.ID` was a doc carry-over and is WRONG. `[VERIFIED-LIVE 2026-05-31]` `[GR §2]` |

### 2F. The logical composite bridges (the cross-domain edges — NOT declared FKs)
These are the high-value, un-declared joins the engine resolves in **application code** (zero saved Access queries walk them — full-text grep for `TMT`/`SST_Mfr`/etc. across all 33 queries returned 0 hits). `[02 §3 verdict]`

| # | Bridge (composite) | Gate | Resolves to | Kind | Provenance |
|---|---|---|---|---|---|
| **SST-1** | `BreakerXXXStyles.(TMT_SST_Mfr, TMT_SST_Type, TMT_SST_Style)` → `(Manufacturers.Mfr_Name, DatStyle.TYPE, DatStyle.STYLE)` then `DatStyle.STYLE_ID → DatSensor.StyleID` | `TMT_Use_SST = 1` | trip unit's sensors/sections/plugs | T (name-based; needs name→ID hop through `Manufacturers`) | `[VERIFIED-LIVE 2026-05-31]` `[04 Task 4]` `[01 §3]` `[DLL DevLibBreakerStyle.cs:135-139]` `[DLL DeviceLibrary.cs:478]` — see G0 §3 |
| **SST-2** | `RelayDevices.(SST_Mfr, SST_Type, SST_Style)` → `(Manufacturers.Mfr_Name, DatStyle.TYPE, DatStyle.STYLE)` | `Use_SST = 1` | same `DatStyle` trip-unit world | T (name-based) | `[01 §4]` — e.g. `West / Amptector I-A / LVPCB` |
| **SST-3** | `DsgnProtEqp.(SSTMfrID, SSTType, SSTStyle)` → `DatStyle` via `MFG_ID` | `SSTOpt` | `DatStyle` | B (uses **numeric** `MFG_ID`, not name) | `[01 §4]` — design/estimating layer; also has `Prot*`/`Moc*` parallel sets |
| **TMT-bridge** | `BreakerXXXStyles.ID → Breaker_TMTFrameSizes.StyleID` | `TMT_Use_SST = 0` | the breaker's own thermal-mag frame curve | B (declared FK) | `[04 Task 2]` `[DLL DeviceLibrary.cs:1322 ReadTmgnFrameIdsMatchingFrameAndTrip]` — see G0 §4 |

**Bridge population & join health (live, the SST-1 case):** `[VERIFIED-LIVE 2026-05-31]` `[04 Task 3/4]`

| Class | Total styles | `Use_SST=1` | non-blank style | matched to `DatStyle` (non-blank denom) | match rate |
|---|---:|---:|---:|---:|---:|
| ICCB | 608 | 515 | 515 | 515 | **100.0%** |
| MCCB | 10,335 | 1,680 | 1,648 | 1,576 | **95.6%** |
| PCB | 3,279 | 3,193 | 2,218 | 2,162 | **97.5%** |

Unmatched non-blank rows are **genuine `DatStyle` catalog gaps** (missing TYPE/STYLE combos — e.g. Cutler-Hammer "DT 310+" LG-Frame, Siemens "ETU25B [IEC]" 3WL11), **not** name-hygiene: manufacturer name resolves for 100% of misses and `UCASE+TRIM` rescues 0. PCB also has 975 `Use_SST=1` rows with a **blank** `TMT_SST_Style` that can never bridge (drags the all-rows PCB rate to 67.7%). `[04 Task 4c]`

### 2G. Other dimension FKs (in-scope subset)
`MOCTypes.MFG_ID → Manufacturers.ID`, `MOCStyles.TYPE_ID → MOCTypes.TYPE_ID`, `MOCStyleGrid.STYLE_ID → MOCStyles.STYLE_ID` are declared FKs (MOC is non-TCC but the FKs are in the live 44). `[04 Task 2]`

> **Saved-query world note (provenance caveat):** the 33 saved Access queries reference a `DatTrip`/`DatType`/`DAT`/`SST_MFG` schema keyed on `TRIP_ID`/`TYPE_ID` (World B). **`DatTrip` does NOT exist in the live `.accdb`** — `DatSensor` has `StyleID` (→`DatStyle.STYLE_ID`), not `TRIP_ID`. The shipping-DLL `StyleID` path is physically backed; the saved-query `TRIP_ID` path references objects that aren't in this DB. **DLL path wins.** Do not load the saved-query join graph as the live model. `[VERIFIED-LIVE 2026-05-31]` `[04 verdict]` `[02 §0]`

---

## 3. DVL-flag data dictionary

Two layers: **(3.1)** Access field DESCRIPTIONS (`[DVL-DB]`, the design-time "Description (Optional)" metadata — 110 described fields across 34 tables, NOT present in CSV exports), and **(3.2)** the authoritative engine-constant tables (`[DLL]`, the `DVL_SST_SETTING_*` / `SSTDelayCalc` / etc. that the DB descriptions defer to). **(3.3)** reconciles the two where they disagree — engine wins.

### 3.1 Described columns by table (the `[DVL-DB]` legends)

**Breaker style tables — family/standard discriminators**
| Column | Tables | Type | Decoded legend | Tag |
|---|---|---|---|---|
| `TMT_BreakerType` | ICCB, MCCB styles | Long | `0 = Thermal Magnetic`, `1 = Motor Circuit Protector` | `[DVL-DB]` |
| `TMT_ThermalMagnetic` | ICCB, MCCB styles | Long | `0 = With Adjustable Instantaneous`, `1 = Without adj instantaneous` | `[DVL-DB]` |
| `TMT_TripPlug` | ICCB, MCCB styles | Long | `0 = Trip`, `1 = Plug` | `[DVL-DB]` |
| `c_testing_std` | HV, ICCB, MCCB, PCB, Switch styles | Byte | `0 = ANSI-SYM`, `1 = IEC`, `2 = ANSI-TOTAL` | `[DVL-DB]` |
| (HV only) `r_int_ka` | HVStyles | Single | "INT kA @ Max-kV" | `[DVL-DB]` |
| (HV only) `r_max_int_ka` | HVStyles | Single | "Max INT kA" | `[DVL-DB]` |

> PCB style table: `c_testing_std` is its **only** described column (of 76); the described `TMT_TripPlug/BreakerType/ThermalMagnetic` exist only on ICCB & MCCB. `[DVL-DB BreakerPCBStyles]` `[08 §2]`

**`DatSensor` — ETU/SST trip-unit definition (18 described of 93)**
| Column | Type | Legend / pointer | Tag |
|---|---|---|---|
| `SEC1_LTF` | Long | `0 = Discrete, 1 = Continuous` (LTPU setting form) | `[DVL-DB]` |
| `SEC2_LTF` | Long | `0 = Discrete, 1 = Continuous` (LTD) | `[DVL-DB]` |
| `SEC3_STF` | Long | `0 = Discrete, 1 = Continuous` (STPU) | `[DVL-DB]` |
| `INST_FUNC` | Long | `0 = Discrete, 1 = Continuous` (INST) | `[DVL-DB]` |
| `SEC1GF_GFF` | Long | `0 = Discrete, 1 = Continuous` (GF) | `[DVL-DB]` |
| `SETTING_METHOD` | Long | `0 = Long Time Delay Band (Seconds)` | `[DVL-DB]` |
| `DS1_PICKUP_CALC` | Long | "See `DVL_SST_SETTING_*` constants in source header files" → resolved to `SSTCalcMethod` (3.2) | `[DVL-DB]`→`[DLL]` |
| `DS3_PICKUP_CALC` | Long | same → `SSTCalcMethod` | `[DVL-DB]`→`[DLL]` |
| `DS4_PICKUP_CALC` | Long | same → `SSTCalcMethod` | `[DVL-DB]`→`[DLL]` |
| `DS1GF_PICKUP_CALC` | Long | same → `SSTCalcMethod` | `[DVL-DB]`→`[DLL]` |
| `DS4_OVR_CALC` | Long | same → `SSTCalcMethod` (native-only, see 3.2) | `[DVL-DB]`→`[DLL]` |
| `SETTING_TYPE` | Long | same → `SSTCalcMethod`-typed (native-only) | `[DVL-DB]`→`[DLL]` |
| `DS1Gf_I2T_TYPE` | Long | DB cites `DVL_SST_SETTING_*` but real legend is the I2T-TYPE pair (see flagship reconcile) | `[DVL-DB]` (mislabeled) |
| **`DS3_SEC3_I2T`** | Long | **DB says "0 or 1"** → engine reality `SSTDelayCalc` **0..4** (FLAGSHIP) | `[DVL-DB]` vs `[DLL]` |
| **`DS1GF_SEC3_I2T`** | Long | **DB says "0 or 1"** → engine reality `SSTDelayCalc` **0..4** | `[DVL-DB]` vs `[DLL]` |
| `DS3_I2T_TYPE` | Long | `0 = Setting*Sensor, 1 = Setting*Tap` (Access typo "Seetting") | `[DVL-DB]` |
| `DS4_OVR_VALUE` | Single | "Must be set if `DS4_OVR_CALC >= 0`" (Access typo `DS4_OVR_VALC`) | `[DVL-DB]` |
| `DS1_C_NAME` | Text | "Setting C Name" | `[DVL-DB]` |

**`DatStyle` — rating basis/term**
| Column | Legend | Tag |
|---|---|---|
| `SENSOR_NAME` | `0 = Plug, 1 = Tap` (rating-term label; **a flag, NOT a FK** despite the name) | `[DVL-DB]` |
| `SENSOR_TYPE` | `0 = Sensor, 1 = Frame` (rating basis) | `[DVL-DB]` |

**EMT family discriminators**
| Column | Legend | Tag |
|---|---|---|
| `EMT.TripChar` | **Bitmap** `1=LT, 2=ST, 4=Inst` (OR-combined: `3`=LT+ST, `5`=LT+Inst, `7`=all) — decode bitwise, not as an ordinal | `[DVL-DB]` |
| `EMT.TripPlug` | `0 = Trip, 1 = Plug` | `[DVL-DB]` |
| `EMT_Sections.SecChar` | `1, 2 or 4` (mirrors the LT/ST/Inst weights — selects per-section meaning) | `[DVL-DB]` |
| `EMT_Sections.CurveType` | section-dependent: `Sec 1,2: 0 = Variable pu/Open-clear`; `Sec 3: 0 = Horz delay band` | `[DVL-DB]` |
| `EMT_Sections.PickupCalc` | `0 = Ipu * Trip amps` | `[DVL-DB]` |
| `EMT_Sections.PickupSetting` | `0 = discrete, 1 = continuous` | `[DVL-DB]` |
| `EMT_Sections.CurrentCalc` | `0 = Normalized track pickup, 1 = Current in (A)` | `[DVL-DB]` |
| `EMT_Sections.{DelayClrCurve, DelayOpenTime, DelayClearTime, OpenCurveRadius, ClearCurveRadius}` | **"Used if `SecChar=4`"** (inst section only); `DelayClrCurve 0 = Constant, 1 = Decreasing` | `[DVL-DB]` `[RULE]` |
| `EMT_Sections.StepSize` | "Used if continuous" | `[DVL-DB]` `[RULE]` |
| `EMT_Curves.Class` | `0 = Opening, 1 = clearing` | `[DVL-DB]` |

**TMT frame routing (`Breaker_TMTFrameSizes` — 13 described)**
| Column | Legend | Tag |
|---|---|---|
| `Sec1PickupCalc` | `0 = Current*Trip` | `[DVL-DB]` |
| `Sec2PickupCalc` | `0 = Frame Size * Setting` | `[DVL-DB]` |
| `Sec2CurrentCalc` | `0 = Normalize & Track Pickup` | `[DVL-DB]` |
| `Sec2DiscCont` | `1 = Continuous`; `0`/blank = Discrete | `[DVL-DB]` |
| `Sec2CurveType` | `0 = Open/Clear (adj. tolerance)` | `[DVL-DB]` |
| `Sec2InstClrCurve` | `0 = Constant, 1 = Decreasing` | `[DVL-DB]` |
| `Sec2InstClrChar` | `0 = Norm Track, 1 = Fixed` | `[DVL-DB]` |
| `Breaker_TMTFrameCurves.Class` | `0 = Sec1 Opening, 1 = Sec1 Clearing, 2 = Sec2 Clearing` | `[DVL-DB]` |

**Relay discriminators (selected)**
| Column | Legend | Tag |
|---|---|---|
| `RelayDevices.Standard` | `0 = ANSI, 1 = IEC, 2 = Both` | `[DVL-DB]` |
| `RelayDevices.DeviceFunction` | ANSI device-function code (`51/50`, `67N`, …) | `[DVL-DB]` |
| `Relays.MultFunction` | `0 = single function, 1 = mult function` | `[DVL-DB]` |
| `Relays.RelayClass` | `0 = Other, 1 = Motor, 2 = Generator` | `[DVL-DB]` |
| `Relays.DCOffsetFilter` | `0 = Off, 1 = On` | `[DVL-DB]` |
| `RelayTDSection.Model` | `0 = Bassler formula, 1 = TD Points` | `[DVL-DB]` |
| `RelayTDSection.Type` | (TD-Points) `0 = Discrete, 1 = Continuous` | `[DVL-DB]` |
| `RelaySec2TCP.Discrete` | **`1 = discrete, 0 = continuous`** — opposite polarity to DatSensor/EMT | `[DVL-DB]` |
| `RelaySec2TCPCurves.TimeDial` | `-100.0` = sentinel "this row identifies pickups" | `[DVL-DB]` |
| `RelayRanges.Step` | Null → take discrete values from `DiscreteValues` (routing sentinel) | `[DVL-DB]` |
| `RelayLineSection.{Pickup, SecondaryI}` | **DESIGN-OPEN** ("Chet to decide" / "To decide") — unfinished in the DB itself | `[DVL-DB]` `[DEFERRED]` |

**Other:** `MOCStyles.MOC_PICKUPCALC = 0 → Current * Full Load Amps`; `StarterSize.HpKw` = HP if `Unit=0` (US) else kW (`Unit=1`); `zOldInsulationLV.Unit` same `0=US/1=Metric`. `[DVL-DB]`

### 3.2 Authoritative engine-constant tables (`[DLL]` — what the DB defers to)

The DB descriptions point at "`DVL_SST_SETTING_*` constants in source header files." **No physical `.h`/`.hpp` exist** anywhere in `D:\Access DB\DLL Decomp\`; the native `DvlEng` decompiled only to nameless raw-IL struct shells. The authoritative recovered form is the **managed C# mirror** in `EasyPower.DeviceLibrary` (enums + `const` blocks, 1:1 faithful to the native constants). `[DLL §0/§6]` `[09]`

**`SSTCalcMethod` / `DVL_SST_SETTING_*` — pickup-calc method (-1..10).** Casts from `DS1/DS3/DS4/DS1GF_PICKUP_CALC` (+ native-only `SETTING_TYPE`, `DS4_OVR_CALC`). `[DLL SSTCalcMethod.cs:3-17]` `[DLL DeviceLibrary.cs:37-59]`
| Val | Constant | Engine formula (amps) |
|---:|---|---|
| -1 | `DVL_SST_SETTING_NONE` | element absent / N/A |
| 0 | `DVL_SST_SETTING_SENSORFRAME` | `setting × SensorValue` |
| 1 | `DVL_SST_SETTING_PLUGTAP` | `setting × plug` |
| 2 | `DVL_SST_SETTING_SENSORFRAME_MULT` | `setting × SensorValue × mult` |
| 3 | `DVL_SST_SETTING_PLUGTAP_MULT` | `setting × plug × mult` |
| 4 | `DVL_SST_SETTING_LTPU` | `setting × ltpuAmps` |
| 5 | `DVL_SST_SETTING_SENSORFRAME_C` | `setting × ltpuSetting × SensorValue` (cascaded) |
| 6 | `DVL_SST_SETTING_PLUGTAP_C` | `setting × ltpuSetting × plug` (cascaded) |
| 7 | `DVL_SST_SETTING_AMPS` | `setting` is already primary amps (identity) |
| 8 | `DVL_SST_SETTING_GFPU` | GF-pickup variant (declared; native-side, not in managed switch) |
| 9 | `DVL_SST_SETTING_MULTWTH` | "mult-with"; maps to `0.0` in managed amps switch |
| 10 | `DVL_SST_SETTING_STPU` | STPU-relative variant (declared; native-side) |

**`SSTDelayCalc` / `DB_SST_DLCALC_*` — short-time/ground delay-curve routing (0..4).** The enum the `*_SEC3_I2T` columns actually cast to. `[DLL DeviceLibrary.cs:67-75]` `[DLL DeviceLibrary.cs:1220,1230,1279,1299]`
| Val | Constant | Routing | Delay table the engine reads |
|---:|---|---|---|
| 0 | `DB_SST_DLCALC_NONE` | no delay-calc; fixed-time bands, I2T Out=0/In=1 | `DatSection3STD` |
| 1 | `DB_SST_DLCALC_I2X` | I²·x (I^x·t) slope family via STD `I2X` column | `DatSection3STD` filtered on `I2X` |
| 2 | `DB_SST_DLCALC_INVEQ` | inverse-equation (computed curve) | `DatSection3InvEq` / GF: `DatSection1GfInvEq` |
| 3 | `DB_SST_DLCALC_TUSTD` | trip-unit STD / Enteliguard (no I2T setting; "not supported" log path) | — |
| 4 | `DB_SST_DLCALC_TUG` | trip-unit ground family | (ground delay path) |

**`ContinuousSettings`** (`0 = DVL_DISCRETE, 1 = DVL_CONTINUOUS`) — casts from `SEC1_LTF, SEC3_STF, INST_FUNC, SEC2_LTF, SEC1GF_GFF`. `[DLL ContinuousSettings.cs:3-7]`

**`DVL_SST_STP_TRACKS_*`** (`0=NONE, 1=INST, 2=LTPU`) — casts from `DS3_STP_TRACKS` (undescribed in DB). `[DLL DeviceLibrary.cs:61-65]`

**`DB_SST_I2T_*`** (`0=OUT, 1=IN, 2=BOTH`) — the byte in the I2T pick-list (in/out *within* a delay family; distinct from the `*_SEC3_I2T` routing enum). `[DLL DeviceLibrary.cs:77-81]`

**`DVL_CCBRK_WITH[OUT]_ADJ_INST`** (`0=WITH, 1=WITHOUT` adjustable inst) and **`CCBkreakerCalcMethod`** (`0=DVL_CCBRK_CALC_IPU_TRIP_AMPS, 1=DVL_CCBRK_CALC_CURRENT_IN_AMPS`) — the molded-case/thermal-mag (CC breaker) analogue of `SSTCalcMethod`. No separate "TMT"/"EMT" `DVL_*` enum exists in the managed tree beyond these two. `[DLL DeviceLibrary.cs:83-85]` `[DLL CCBkreakerCalcMethod.cs:3-7]`

### 3.3 DB-description ⇄ engine-constant reconciliation (conflict rule: `[DLL]` > `[DVL-DB]`)

| Column | DB description (verbatim) | Engine reality | Verdict |
|---|---|---|---|
| **`DS3_SEC3_I2T`** | **"0 or 1"** | **`SSTDelayCalc` 0..4** (NONE/I2X/INVEQ/TUSTD/TUG) | **Misleading/Incomplete — FLAGSHIP** |
| **`DS1GF_SEC3_I2T`** | **"0 or 1"** | **`SSTDelayCalc` 0..4** (GroundDelayCalc) | **Misleading/Incomplete** (same flagship pattern, ground twin) |
| `DS1/DS3/DS4/DS1GF_PICKUP_CALC` | "See `DVL_SST_SETTING_*`…" | `SSTCalcMethod` -1..10 | Incomplete (pointer only; resolved in 3.2) |
| `SETTING_TYPE`, `DS4_OVR_CALC` | same pointer | `SSTCalcMethod`-typed but **native-only** (not read by managed lib; grep = 0 hits) | Incomplete |
| `DS1Gf_I2T_TYPE` | "See `DVL_SST_SETTING_*`…" | really the I2T-TYPE pair (`0=Setting*Sensor,1=Setting*Tap`), **not** the SST_SETTING enum | Misleading (wrong legend cited) |
| `DS3_I2T_TYPE` | "0 = Seetting*Sensor, 1 = Setting*Tap" | I2T multiply basis (Sensor vs Tap) | Complete (typo "Seetting") |
| `DS4_OVR_VALUE` | "Must be set if `DS4_OVR_VALC >= 0`" | gated by `DS4_OVR_CALC` | Misleading (typo `DS4_OVR_VALC`→`DS4_OVR_CALC`) |
| `SEC1_LTF`/`SEC2_LTF`/`SEC3_STF`/`INST_FUNC`/`SEC1GF_GFF` | "0=Discrete,1=Continuous" | `ContinuousSettings` (0/1) | Complete |
| `DS3_STP_TRACKS` | (no description) | `DVL_SST_STP_TRACKS_*` 0/1/2 | Incomplete (undocumented; resolved in 3.2) |

**Value distributions (live, all 17,831 sensors, no NULLs) for the flagship columns** `[DLL_SEMANTIC_FINDINGS §1/§2]` `[VERIFIED-LIVE pre-migration]`:
- `DS3_SEC3_I2T`: 0=4,364 · 1=8,708 · 2=4,524 · 3=235 (no value 4)
- `DS1GF_SEC3_I2T`: 0=9,933 · 1=5,976 · 2=1,713 · 4=209 (no value 3)

### 3.4 Undescribed coded regions (semantics live in engine source — recover before relying)
- **Family crossover (highest priority):** `TMT_Use_SST`, `TMT_SST_Mfr/Type/Style`, `TMT_TCCNumber` on ICCB/MCCB/PCB — **NO DB description**; polarity/join from engine (`TMT_Use_SST=1 ⇒ borrow SST/ETU`, `=0 ⇒ TMT frame`). `[DLL DevLibBreakerStyle.cs:135-139]` `[08 §3.2]`
- **Inst-override blocks** `InstOvr*` + `NInstOvr*` (≈16 cols each × 3 tables) — undescribed; map to the native breaker-override mechanism. `[DEFERRED]` `[08 §3.3]`
- **Mechanism/rating columns** `BrkTimes*50/60` (Hz suffix), `r_int_inst_{240,480,600}` / `r_iec_inst_{220..1000}` / `r_*_series_*` (voltage-class suffix) — suffix decodable, convention undocumented for LV. `[08 §3.4/3.5]`
- **All `DatSection*` engine tables** carry **zero** field descriptions (incl. `DatSection3STD.I2X` byte flag, `STD_OPEN/CLEAR`, `I/T_OPEN/CLEAR`); the I²t/open-vs-clear/tolerance routing for the SST short-time band lives entirely in engine source. `[08 §3.6]`

---

## 4. Source → staging → Supabase lineage

**Three-hop pipeline:** Access `DatX` / `Breaker_*` → Phase-2 staging `*_aligned` (in `tcc_fidelity_staging`, loaded 1:1 from `D:\TCC_NEW.accdb`) → governed Supabase persisted catalog. All SQL the engine issues is centralized in `DeviceLibrary.cs` (no other `.cs` carries SQL). `[DLL_END_TO_END_MAPPING]`

> **Decision-012 `tcc.*` unification (2026-05-30 — supersedes the table names below).** The DLL mapping was authored against the **pre-unification** `tcc_etu_*` / `tcc_brk_*` / `tcc_tmt_*` names in the **public** schema. **Decision-012 (CLOSED end-to-end 2026-05-30)** moved all 60 breaker `public.tcc_*` + relay `work.tcc_relay_*` tables into the **single `tcc.*` schema** (per Decision-010 apparatus-role), dropped all back-compat views + 10 `_pre_rebuild` + 1 `_v2`, and repointed every consumer (raw SQL + ORM, API + calc-engine). **Read every `tcc_<x>` name in the table below as `tcc.<x>`** (e.g. `tcc_etu_sensors` → `tcc.etu_sensors`, `tcc_brk_iccb_styles` → `tcc.brk_iccb_styles`). `[HANDOFF Decision-012]` `[MEMORY project_decision_012]` `[OPEN-VALIDATION]` exact final `tcc.*` table names pending a live `tcc` schema `list_tables` (Supabase MCP unauthorized this session).

### 4.1 ETU/SST sensor-rooted lineage (19 tables — the calc core)
| Access table | Staging `*_aligned` | Supabase (read as `tcc.*`) | DLL reader |
|---|---|---|---|
| `DatStyle` | `trip_styles_aligned` | `tcc_trip_styles` | join queries |
| `DatSensor` (93) | `etu_sensors_aligned` | `tcc_etu_sensors` | `ReadSSTSensorRecordBySensorId` (1138) |
| `DatPlugs` | `etu_plugs_aligned` | `tcc_etu_plugs` | `ReadSSTSensorPlugsBySensorId` (1126) |
| `DatSensorMaint` | `etu_sensor_maint_aligned` | `tcc_etu_sensor_maint` | app-layer JSON |
| `DatSensorParms` | `etu_sensor_params_aligned` | `tcc_etu_sensor_params` | in-memory |
| `DatSensorSec2` | `etu_ltd_delay_profiles_aligned` | `tcc_etu_ltd_params` | in-memory |
| `DatSettings` | `etu_settings_aligned` | `tcc_etu_settings` | none proven (live legacy was 0 rows) |
| `DatSection1Sett` | `etu_ltpu_pickups_aligned` | `tcc_etu_ltpu_pickups` | `ReadLtpuSettings` (1178) |
| `DatSection1Mult` | `etu_ltpu_multipliers_aligned` | `tcc_etu_ltpu_multipliers` | `ReadLtpuMult` (1191) |
| `DatSection2LTD` | `etu_ltd_bands_aligned` | `tcc_etu_ltd_bands` | `ReadLtDelays` (1166) |
| `DatSection3STP` | `etu_stpu_pickups_aligned` | `tcc_etu_stpu_pickups` | `ReadStpuSettings` (1204) |
| `DatSection3STD` | `etu_std_bands_aligned` | `tcc_etu_std_bands` | `ReadStpuDelay` default (1216) |
| `DatSection3InvEq` | `etu_std_equations_aligned` | `tcc_etu_std_equations` | `ReadStpuDelay` INVEQ |
| `DatSection3STOvr` | `etu_stpu_overrides_aligned` | `tcc_etu_stpu_overrides` | `CBreakerOverride.cs` (EAV, 5 attrs) |
| `DatSection4InstPickup` | `etu_inst_pickups_aligned` | `tcc_etu_inst_pickups` | `ReadInstSettings` (1251) |
| `DatSection4InstCurves` | `etu_inst_curves_aligned` | `tcc_etu_inst_curves` | in-memory |
| `DatSection1GfGFP` | `etu_gfpu_pickups_aligned` | `tcc_etu_gfpu_pickups` | `ReadGroundSettings` (1263) |
| `DatSection1GfGFD` | `etu_gfd_bands_aligned` | `tcc_etu_gfd_bands` | `ReadGroundDelay` default (1275) |
| `DatSection1GfInvEq` | `etu_gfd_equations_aligned` | `tcc_etu_gfd_equations` | `ReadGroundDelay` INVEQ |

The two flagship routing columns: `DatSensor.DS3_SEC3_I2T` → `tcc_etu_sensors.stpu_delay_calc_code` (renamed from legacy `stpu_i2t` at Phase-5 Tier-A 2026-04-26); `DatSensor.DS1GF_SEC3_I2T` → `tcc_etu_sensors.ground_delay_calc_code` (from legacy `gfpu_i2t`). `[HANDOFF Phase-5-Tier-A]` `[DLL_END_TO_END_MAPPING §1]`

### 4.2 TMT, breaker-hardware, reference lineage
| Access table | Supabase (read as `tcc.*`) | DLL reader |
|---|---|---|
| `Breaker_TMTFrameSizes` | `tcc_tmt_frames` | `ReadTmgnFrameRecordByFrameId` (1392) |
| `Breaker_TMTFrameSettings` | `tcc_tmt_settings` | `ReadTmgnFrameInstSettingsByFrameId` (1411) |
| `Breaker_TMTFrameAmps` | `tcc_tmt_amps` | `ReadTmgnTripAmpsByFrameId` (1354) |
| (TMT curves — computed, not in Access) | `tcc_tmt_curves` | N/A |
| `BreakerMCCB` / `BreakerMCCBStyles` | `tcc_brk_mccb` / `tcc_brk_mccb_styles` | `FindMatchingBreakerStyles` (403) |
| `BreakerICCB` / `BreakerICCBStyles` | `tcc_brk_iccb` / `tcc_brk_iccb_styles` | same |
| `BreakerPCB` / `BreakerPCBStyles` | `tcc_brk_pcb` / `tcc_brk_pcb_styles` | same |
| `Manufacturers` | `tcc_manufacturers` | join queries |
| (trip types — derived) | `tcc_trip_types` | — |
| (thermal adj — derived) | `tcc_tmt_thermal_adj` | — |

**Supabase-only (no Access source):** `tcc_test_plans`, `tcc_test_results` (NETA storage, new for v5) — **note: these live in `public.*`, NOT `tcc.*`** `[VERIFIED-LIVE 2026-05-31]`. **Relay catalog** loaded live in governed Supabase per matrix #80 G-3; relay parent `tcc.relays`=1,442. The relay SST-bridge (`use_sst`/`sst_manufacturer`/`sst_type`/`sst_style`) **was carried** (see §5 D2). `[HANDOFF matrix-80-G-3]` `[VERIFIED-LIVE 2026-05-31]`

---

## 5. Dropped-column register (source Access columns ABSENT in governed `tcc.*`)

Columns that exist in source Access but are **not** present in the deployed `tcc.*` catalog. Each is a fidelity gap with a downstream consequence.

| # | Column(s) | Source table(s) | Target `tcc.*` | Why it matters | Root cause | Status |
|---|---|---|---|---|---|---|
| **D1** | `tmt_use_sst`, `tmt_sst_mfr`, `tmt_sst_type`, `tmt_sst_style` | `BreakerICCBStyles` / `BreakerMCCBStyles` / `BreakerPCBStyles` | `tcc.brk_iccb_styles` / `brk_mccb_styles` / `brk_pcb_styles` | This is the **SST-1 breaker→ETU bridge** — the columns that make "T8V-1600 → ABB PR332/P → exactly 5 sensors" possible. Without them the deployed cross-filter is **manufacturer-axis only** (offered 117 ABB trips instead of the 1 correct trip). | **Name-vs-id loader assumption:** `tmt_sst_mfr` is a manufacturer **NAME** string, but the loader expected a numeric `Manufacturers.ID` FK, so the bridge join silently dropped and the 4 columns were not carried. | **ANCHOR / OPEN.** Confirmed missing live (G0 §3) `[VERIFIED-LIVE 2026-05-31]`; recovery is a tracked schema gap (G2 governance). Needs `information_schema` re-confirm `[OPEN-VALIDATION]` |
| **D2** | `Use_SST`, `SST_Mfr`, `SST_Type`, `SST_Style` | `RelayDevices` | `tcc.relay_devices` (matrix #80 G-3 load) | The **SST-2 relay→ETU bridge** (same "borrow-an-SST" shape, name-based). | n/a — bridge was preserved. | **CARRIED, NOT DROPPED — D2 REVERSED 2026-05-31.** Live `tcc.relay_devices` HAS the bridge: `use_sst`, `sst_manufacturer` (renamed from `sst_mfr`), `sst_type`, `sst_style`. The relay G-3 loader preserved the name-key; only the **breaker** loader (D1) dropped it. This narrows the "name-vs-id drop" to the breaker-style load specifically. `[VERIFIED-LIVE 2026-05-31]` |
| **D3** | `SSTOpt`, `SSTMfrID`, `SSTType`, `SSTStyle` (+ `Prot*`, `Moc*` parallels) | `DsgnProtEqp` | (none — `Dsgn*` is non-TCC, not migrated) | The **SST-3 design-layer bridge** (uses numeric `MFG_ID`, so it would NOT hit the D1 name-vs-id trap). Matters only if/when the design/estimating layer is brought into scope. | `DsgnProtEqp` is in the non-TCC design domain and was never migrated to `tcc.*`. | **OUT OF SCOPE / not dropped-by-bug.** Documented for completeness `[INFERENCE]` |
| **D4** | TMT helper cols `TMT_TCCNumber`, `TMT_Notes`, `TMT_TripPlug`, `TMT_BreakerType`, `TMT_ThermalMagnetic`, `TMT_Thermal` (ICCB/MCCB only) | `BreakerICCBStyles` / `BreakerMCCBStyles` | `tcc.brk_iccb_styles` / `brk_mccb_styles` | These describe the **thermal-magnetic alternative** used when `TMT_Use_SST=0` and decode the TMT breaker sub-type (`0=Thermal Magnetic / 1=Motor Circuit Protector`, etc.). Their absence weakens TMT-breaker characterization. | Carried along with the D1 drop (same `TMT_*` column block) / not part of the migrated `brk_*_styles` projection. | **LIKELY DROPPED.** Co-located with D1; not individually live-confirmed `[OPEN-VALIDATION]` `[INFERENCE]` |
| **D5** | `InstOvr*` + `NInstOvr*` inst-override blocks (≈16 cols each); `BrkTimes*50/60`; LV `r_int_*` / `r_iec_*` rating columns | `BreakerICCB/MCCB/PCBStyles` | `tcc.brk_*_styles` | Frame-limited instantaneous override (amps/tolerances/open-clear delay+radius) + mechanism timing + interrupt ratings. Needed for full breaker-override fidelity + ANSI/IEC rating display. | Undescribed columns outside the minimal migrated projection (`FindMatchingBreakerStyles` selects only `Mfr_Name, Type, Style`). | **DEFERRED.** Inst-override is a known deferred item (G0 §4) `[DEFERRED]` `[INFERENCE]` |
| **D6** | `DatSettings` (3,514 rows / 235 sensors) | `DatSettings` | `tcc.etu_settings` | Per-sensor setting descriptions. | Phase-2/3 governance gated the live load pending an identified runtime dependency. | **NOW LOADED (updated 2026-05-31):** `tcc.etu_settings` = **3,514 rows** (no longer the legacy 0-row empty load). The rebuilt corpus carried it; no runtime consumer was ever proven, so it is loaded-but-unconsumed, not a dropped gap. `[VERIFIED-LIVE 2026-05-31]` |

> **Pattern note (D1/D4) — refined 2026-05-31:** D1 and D4 are the *same* `TMT_*`/`SST_*` text-bridge column block on the **breaker-style** tables, dropped by the *same* name-vs-id loader assumption. **D2 is NO LONGER part of this pattern** — the relay loader (a separate matrix-#80 G-3 load) preserved its bridge (with the `sst_mfr`→`sst_manufacturer` rename). So the drop is specific to the **breaker-style** load path, not a universal loader trait. Recovering D1 is the gating fix; D4 rides along on the same projection widen. The fix is a **name→ID resolution hop** through `Manufacturers` at load time (or carrying the raw name columns and resolving at query time), per the bridge mechanism in G0 §3 — and the relay loader (D2) is the working precedent for how to carry it. `[VERIFIED-LIVE 2026-05-31]`

> **Governed-load deltas (NOT dropped columns — row-count shortfalls vs Access source):** a handful of `tcc.*` tables carry fewer rows than their Access source, from referential-integrity orphan drops at load. Flagged 2026-05-31: `tcc.brk_mccb` = **599** vs Access `BreakerMCCB` = **640** (41-row MCCB-parent shortfall — worth an operator look: investigate vs accept); `tcc.tmt_thermal_adj` 14,620 vs 21,790; EMT child tables a few rows under Access (RI orphans). These are *load-completeness* notes distinct from the *dropped-column* (schema-projection) gaps D1–D6. `[VERIFIED-LIVE 2026-05-31]`

---

## 6. Cross-references
- Trip-family model + the bridge mechanism narrative (SST/ETU vs TMT vs EMT) → **G0**
- Frozen-baseline status of the D1 bridge gap + the deferred-work ledger (D5/D6) + reopen triggers → **G2**
- Selection-routing + calc-dispatch constant tables (`*_PICKUP_CALC`→SSTCalcMethod, `*_SEC3_I2T`→SSTDelayCalc) in dispatch context → **G3**
- Per-family pickup/delay formulas + the field-trust matrix → **G4**
