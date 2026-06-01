# GR — Relay Reference (Family/Selection · Schema · Curve-Family Routing · Calc + Field-Trust)

> **Owns:** the **relay** protective-device domain — the parallel to the breaker guides G0–G4, for relays.
> How a relay is selected, what tables hold its settings/curves, how its time-overcurrent curve is routed
> and computed, and **which relay numbers are field-trustworthy for NETA relay testing.** Cite this guide
> for any relay selection, schema, or calc decision.
>
> **Status: DRAFT — authored 2026-05-31** from the relay discovery/validation campaign
> (`_discovery/_relay/` R1–R3). Validated vs Access master `D:\TCC_NEW.accdb` (OLEDB) + governed `tcc.*`
> (live) + **EasyPower 25.0 official help docs `[EZPDOC]`**.
> Last validated · 2026-05-31 · Desktop · **Open gaps (read §7):** the native relay evaluator
> (`CTccRelayCurveBase` + per-family curve classes) is a **size-only shell — NO `[DLL]` formula recovered**;
> every analytical relay curve is **BOUNDED at best** (platform solvers validated only on synthetic
> fixtures, not EasyPower-captured rows). Relay curve trust is **weaker than breakers.**

**Tag legend** (per 00-MASTER-INDEX §2): `[VERIFIED-LIVE <date>]` · `[DLL <file:line>]` · `[EZPDOC <page>]`
(EasyPower official help) · `[DVL-DB <table.col>]` · `[INFERENCE]` · `[DEFERRED]` · `[OPEN-VALIDATION]`.
**Conflict rule:** engine source `[DLL]` ≥ vendor doc `[EZPDOC]` > DB description `[DVL-DB]` > inference.
**Relay-specific note:** because there is **no recovered relay `[DLL]`**, `[EZPDOC]` + live data are the
*primary* authority for the relay model here (unlike breakers, where the DLL was the spine).

Evidence base: `_discovery/_relay/R1-easypower-relay-docs.md` (EZPDOC harvest), `R2-relay-schema.md`
(schema vs both DBs + decomp), `R3-relay-model-calc.md` (model/calc/field-trust). Cross-refs: shared
manufacturer dimension + the SST/ETU sensor world the bridge borrows → **G1/G4**; the breaker family model
this parallels → **G0**.

---

## 0. The headline (read first)

Relays are a **separate** protective-device domain from breakers, but they share the `Manufacturers`
dimension and — for relays that carry an electronic trip — the **same ETU/SST sensor world** via a
name-based bridge (SST-2). Three things make the relay lane **different and harder** than the breaker lane:

1. **The calc kernel is native-only and UNRECOVERED.** Unlike breakers (where `EasyPower.DeviceLibrary`
   exposes the managed SQL and the InvEq loader was Ghidra-recovered), the decompiled engine has **ZERO
   managed relay code** — the entire relay evaluator (`CTccRelayCurveBase` Size=472, the per-family
   `CdvlRelayTD{IEC,BSL,…}Curve` classes) decompiled to **size-only native shells**. So **no relay curve
   family is `[DLL]`-validated.** `[VERIFIED 2026-05-31 decomp]` `[R2]` `[R3]`
2. **The platform solver suite exists but is BOUNDED.** `packages/calc-engine/.../relay_*.py` implements
   `{TCP, IEC, MEQ, BSL, SWZ, PCD}` (explicitly UNSUPPORTED: `RXD, LRM, EGC`); its `RelayFormulaCode` enum
   independently reproduces the `Model` byte — but its golden fixtures are **synthetic** (hand-computed
   from the same formula), **NOT EasyPower-captured.** Dispatch proven, numbers not parity-checked. `[VERIFIED-LIVE 2026-05-31]` `[R3]`
3. **The ship-now trustworthy layer is stored DATA** — the discrete settings and the raw Time/Current
   **point grid (TCP)**, read verbatim — **not** a computed analytical curve. (Same principle as the
   breaker INV-1: data is safe, solver output is not until proven.)

> **Net:** for a NETA *relay* field sheet today, ship the **stored settings + raw point grid**; flag and
> withhold the computed analytical curves until a Ghidra recovery + EasyPower-captured fixtures close them
> (§7). The 41 relays that carry an ETU resolve into the **breaker** field-trust matrix (G4) instead.

---

## 1. The relay selection model `[EZPDOC]` `[VERIFIED-LIVE 2026-05-31]`

**Cascade (Specifications tab):** `Mfr → Type (model name) → Device Function → Single/Multi-Function → CT
→ Breaker/Trip`. **Shorter than the breaker cascade** (`Class→Mfr→Type→Style`): there is **no Class /
Style / Standard dropdown** — ANSI-vs-IEC is pushed down into the **device-function suffix** and the
**Curve** list. `[EZPDOC Relay/Specifications_Tab]`

**Device-function taxonomy (the modeled subset — NOT full IEEE C37.2):** `[EZPDOC Relay/Relay_Device_Functions]`
- Functions: **46** Phase-Balance · **49** Thermal · **50** Inst-OC · **51** Time-OC · **51/50**
  Time+Inst-OC · **67** AC-Directional-OC · **79** Reclosing · **87** Differential. (27/59/81/25/32 are
  **not** modeled as plottable device functions.)
- Element suffix: **P**hase / **G**round / **N**eutral / **Q** Neg-Seq. Curve-family suffix: **IAC / IEEE
  / IEC / DT** (definite-time).
- **Live distributions** `[VERIFIED-LIVE 2026-05-31]` `[R3]`: `RelayDevices.DeviceFunction` = **931 distinct**
  free-text ANSI strings (51/50 dominant, then 51N/50N, 51G/50G, 49, 67/67N, Recloser);
  `.Standard` = **ANSI 4,563 / IEC 1,550 / Both 1,079** (Σ 7,192); `Relays.MultFunction` = **985 multi /
  457 single** (Σ 1,442); `Relays.RelayClass` = **Other 1,275 / Motor 127 / Generator 40** (Σ 1,442).

**`RelayClass` is a calc input, not a cascade step:** it sets the **pickup-multiplier basis** — FLA for
Generator/Motor, CT-ratio/rating for Other. `[EZPDOC]` `[DVL-DB Relays.RelayClass]`

---

## 2. The relay schema + join graph `[VERIFIED-LIVE 2026-05-31]`

**22 Access relay tables → 21 governed `tcc.*` tables.** Live counts (Access → `tcc.*`): `[R2]`

| Access table | Access rows | `tcc.*` table | `tcc.*` rows | Role |
|---|---:|---|---:|---|
| `Relays` | **1,442** | `relays` | **1,442** ✓ | relay identity; `Mfr_ID → Manufacturers` |
| `RelayDevices` | 7,192 | `relay_devices` | 6,850 | one per ANSI device-function; **carries the SST-2 bridge** |
| `RelayLineSection` | 23,991 | `relay_line_sections` | 23,387 | pickup/tap section; `Device_ID → RelayDevices` |
| `RelayTDSection` | 6,956 | `relay_td_sections` | 6,635 | **the curve section** (carries `Model`, §3); `Device_ID → RelayDevices` |
| `RelayRanges` | 34,955 | `relay_ranges` | 34,213 | polymorphic `ParentID` (9 parent kinds, see below) |
| `RelayDiscreteValues` | 40,348 | `relay_discrete_values` | 38,679 | discrete settings; `Range_ID → RelayRanges` |
| `RelaySec2TCP` | 18,908 | `relay_curves_tcp` | 16,183 | Time/Current-Points pickup-curve hdr; `Section_ID → RelayTDSection` |
| `RelaySec2TCPCurves` | 146,912 (wide `v1..v25`) | `relay_curve_points_tcp` | **1,570,700** | the point grid — **wide→long unpivot** (not a loss) |
| `RelaySec2{BSL,IEC,MEQ,PCD,SWZ}` | 501 / 995 / 344 / 53 / 958 | `relay_curves_{bsl,iec,meq,pcd,swz}` | RI-trimmed | per-family curve hdrs; `Section_ID → RelayTDSection` |
| `RelaySec2{BSL,IEC,MEQ,PCD,SWZ}Curves` | (children) | `relay_curve_rows_{fam}` | RI-trimmed | per-family curve rows; `ParentID → RelaySec2{fam}.ID` |
| `RelaySec2{LRM,RXD}` | 13 / 26 | `relay_curves_{lrm,rxd}` | 13 / 26 ✓ | **section-only — no Curves child tables** |
| `RelaySec2EGC` | **0** | `relay_curves_egc` | **0** | empty both surfaces |
| `RelayID` | 1 | (not migrated) | — | single `UniqueID` sequence holder |

Non-zero `tcc.*` deltas are **RI-orphan trims** at load (not dropped columns); the `+1.42M` on
`relay_curve_points_tcp` is the intended `v1..v25` wide→long unpivot. **Dropped-column register: 0 entries**
(the relay load was clean — unlike the breaker D1). `[VERIFIED-LIVE 2026-05-31]` `[R2]`

**Join-graph spine:** `Relays.ID ←Relay_ID— RelayDevices.ID ←Device_ID— {RelayLineSection, RelayTDSection}`;
`RelayTDSection.ID ←Section_ID— RelaySec2{fam}.ID ←ParentID— RelaySec2{fam}Curves`;
`RelayRanges.ID ←Range_ID— RelayDiscreteValues`. `[VERIFIED-LIVE 2026-05-31]` `[R2]`

**`RelayRanges.ParentID` is polymorphic — 9 parent kinds** (governed `parent_kind`): `line_section`
30,200 / `td_section` 1,078 / + 7 curve kinds. (Access cross-check: 30,897 → LineSection, 1,098 → TDSection.)
`[VERIFIED-LIVE 2026-05-31]` `[R2]`

**Corrections this campaign made to G1 §1G/§2E** (now applied there): `[R2]`
- **`RelaySec2MEQCurves.ParentID → RelaySec2MEQ.ID`** (100%, 1,644/1,644) — the G1 §2E `→ RelaySec2IEC.ID`
  edge was a doc carry-over and is **WRONG** (IEC = 0% of MEQ-curve parents).
- **Only 6 families have curve-child tables** (TCP/BSL/IEC/MEQ/PCD/SWZ). `RelaySec2{LRM,RXD,EGC}Curves`
  **do not exist** — LRM/RXD are section-only; G1 §1G's curve-set shorthand overstated.
- **Access↔`tcc.*` naming divergence pinned:** `RelaySec2{fam}` → `relay_curves_{fam}`; `RelaySec2*Curves`
  → `relay_curve_rows_{fam}`; `RelaySec2TCPCurves` → `relay_curve_points_tcp`. SST bridge col `SST_Mfr` →
  `sst_manufacturer`.

---

## 3. Curve-family routing — the relay flagship (`RelayTDSection.Model`, 0–8)

**`RelayTDSection.Model` is a 9-value (0–8) curve-FAMILY dispatcher — NOT the DB-described binary
"0=Bassler formula / 1=TD Points".** This is the relay analog of the breaker flagship engine-over-DB win
(`SSTDelayCalc` "0 or 1" → full 0..4). The 9 values select which `RelaySec2{family}` table the section's
curve lives in, and the per-value counts **sum exactly to `RelayTDSection` (6,956)**: `[VERIFIED-LIVE 2026-05-31]` `[R3]`

| `Model` | Family | Curve representation | TDSections | Family table |
|---:|---|---|---:|---|
| **0** | Bassler (legacy formula) | analytical | 10 | (inline) |
| **1** | **TCP** | **Time/Current Points** (interpolated grid) | 4,056 | `RelaySec2TCP` |
| **2** | IEC | analytical `K/(M^E−1)` | 995 | `RelaySec2IEC` |
| **3** | MEQ | analytical (polynomial in `M−c`) | 344 | `RelaySec2MEQ` |
| **4** | **BSL** (Basler / ANSI, IEEE C37.112) | analytical | 501 | `RelaySec2BSL` |
| **5** | SWZ (Schweitzer/SEL) | analytical `K/(M^E−1)` | 958 | `RelaySec2SWZ` |
| **6** | PCD (ABB PCD2000) | analytical `K/(M^E−1)` | 53 | `RelaySec2PCD` |
| **7** | RXD (RXIDG) | analytical | 26 | `RelaySec2RXD` (section-only) |
| **8** | LRM (Westinghouse IQ-1000, LR I²t) | analytical | 13 | `RelaySec2LRM` (section-only) |

> **Naming collision to keep straight:** DB `Model 0 = "Bassler"` (the legacy 10-section inline family) ≠
> `Model 4 = BSL` (the real **Basler / ANSI IEEE-C37.112** equation set). Do not conflate. `[R3]`

**Discrete vs continuous = `RelaySec2TCP.Discrete`** (`1 = discrete, 0 = continuous` — **OPPOSITE polarity
to `DatSensor`/EMT**, where 1 = continuous): live 10,357 discrete / 8,551 continuous. **`RelayTDSection.Type`
is a red herring** (100% value 0 — do not use it as the discrete/continuous selector). `[VERIFIED-LIVE 2026-05-31]` `[R3]`

**Routing sentinels** (read before interpreting curve rows): `[DVL-DB]` `[R2]` `[R3]`
- `RelaySec2TCPCurves.TimeDial = -100.0` → this row **identifies the ×pickup multiples** (not a curve point);
  18,906 such header rows. The data rows hold trip-times per time-dial.
- `RelayRanges.Step = NULL` → take the discrete values from `RelayDiscreteValues` (continuous otherwise).

---

## 4. The curve math `[EZPDOC]`

EasyPower ships **7 formula families** + the Time/Current-Points (interpolation) representation. `[EZPDOC 09_EasyPower_Device_Library/TCC/TCC_Based_on_Formulas]`

**Basler/Siemens (recovered verbatim from the vendor doc image):**
```
T = A·D / (M^N − C)  +  B·D  +  K
```
where `D` = Time Dial (continuous 0.001–9.9), `M` = multiples of pickup (1.03–40), and `{A,B,C,N,K}` come
from a 10-row constant table (Short / Long / Definite / Moderately / Inverse / Very / Extremely /
Fixed-Time …). The other families: **IEC / SWZ / PCD** = `K/(M^E − 1)` form (live BSL ANSI-EI constants
`v_a=28.2, v_n=2, v_c=1` corroborate); **BSL** = IEEE C37.112; **MEQ** = polynomial-in-`(M−c)`.

**Modifiers** (all `[EZPDOC Relay/Settings_Tab]`): **Minimum-Time clamp** — "the time-overcurrent function
never trips faster than the specified time; the curve becomes flat at this time even if the inverse-time
curve is programmed to trip faster" (recloser relays); plus **Time-Adder** and **Shift-Mult**.

> **Constant-table gap `[OPEN-VALIDATION]`:** the non-Basler family constant tables (IEC, Multilin ANSI,
> Schweitzer, ABB PCD2000, RXIDG, Westinghouse IQ-1000) are **not in the public help** — they live in
> `EasyPower.DeviceLibrary` (same place the breaker enums were recovered). To certify any analytical relay
> family, those constants must come from the DeviceLibrary source + a native-kernel recovery (§7).

---

## 5. The SST-2 bridge — a relay borrows an ETU `[VERIFIED-LIVE 2026-05-31]`

A relay device whose curve is delegated to an electronic trip unit carries the **same name-composite
bridge** as the breaker (SST-1), here called **SST-2**: `[R2]` `[R3]`
```
RelayDevices.(SST_Mfr, SST_Type, SST_Style)  → (Manufacturers.Mfr_Name, DatStyle.TYPE, DatStyle.STYLE)
        gate Use_SST = 1   → DatStyle.STYLE_ID → DatSensor.StyleID → the breaker ETU sensor world
```
- **Population:** **41 of 7,192** `RelayDevices` have `Use_SST = 1` (39 non-blank style). **Carried** into
  `tcc.relay_devices` as `use_sst` / `sst_manufacturer` / `sst_type` / `sst_style` (38 fully populated).
- **Worked example:** `West / Amptector I-A / LVPCB` (`RelayDevices` 4206/2905, `Use_SST=1`) → DatStyle
  `STYLE_ID 56` → **19 `DatSensor`**. The relay borrows the breaker ETU/SST world wholesale.
- **D2 reversal confirmed (3rd time):** the relay bridge was **CARRIED, not dropped** — it is the **working
  precedent** for recovering the dropped breaker D1 bridge (G1 §5). `[VERIFIED-LIVE 2026-05-31]`
- **Provenance caveat:** there is **no managed relay reader** to cite for the resolution order (DeviceLibrary
  has zero relay code), so the SST-2 mechanism is `[INFERENCE]` from the column semantics + the breaker
  SST-1 precedent (which IS `[DLL]`-recovered). `[R2]`

**Field-trust consequence:** for these 41 devices, do **not** use the relay solvers — route them into the
**breaker ETU field-trust matrix (G4)** and gate by the sensor's delay-calc code there.

---

## 6. The relay field-trust matrix

Status legend as in G4. The relay ceiling is lower than the breaker ceiling because the native kernel is
unrecovered and the platform solvers are validated only on synthetic fixtures. `[VERIFIED-LIVE 2026-05-31]` `[R3]`

| # | Relay path | Selector | Status | Safe to ship on a NETA relay sheet? |
|---|---|---|---|---|
| 1 | **Discrete settings (tap/pickup/time-dial values)** | stored `RelayDiscreteValues` / settings | **PROVEN (data)** | **YES — always.** Stored data, no solver. |
| 2 | **Raw Time/Current point grid (TCP)** | `Model=1` `relay_curve_points_tcp` | **PROVEN (data, as stored)** | **YES** to display the stored points verbatim; **interpolation between them is BOUNDED.** |
| 3 | **TCP interpolation curve** | `Model=1` | **BOUNDED** | **Flag.** Interpolation logic not parity-checked vs native. |
| 4 | **IEC / BSL / SWZ / MEQ / PCD analytical curves** | `Model ∈ {2,3,4,5,6}` | **BOUNDED** | **Flag — withhold numbers.** Solver implemented; fixtures synthetic, not EasyPower-captured. |
| 5 | **Bassler-0 / RXD / LRM** | `Model ∈ {0,7,8}` | **DEFERRED / STUB** | **NO — hard-exclude.** Platform explicitly UNSUPPORTED (RXD/LRM) or legacy (Bassler-0). |
| 6 | **EGC** | (empty) | **N/A** | no data either surface. |
| 7 | **SST-2 bridge relays (41 devices)** | `Use_SST=1` | **defer to G4** | route into the **breaker ETU** matrix; gate by sensor delay-calc code (G4). |

**One-line rule:** *ship the stored discrete settings + the raw TCP point grid; flag-and-withhold every
computed analytical curve (Models 1–6); hard-exclude Bassler-0/RXD/LRM; route the 41 SST-2 relays into G4.*

---

## 7. Open validation + the close path

- **The native relay evaluator is UNRECOVERED `[OPEN-VALIDATION]`.** `CTccRelayCurveBase` (Size=472) and the
  per-family `CdvlRelayTD{IEC,BSL,…}Curve` classes decompiled to **size-only `[NativeCppClass]` shells** —
  the relay curve math has **no `[DLL]` recovery** (strictly more open than the breaker InvEq, which at
  least has its loader recovered). `[R2]` `[R3]`
- **The non-Basler family constants `[OPEN-VALIDATION]`** live only in `EasyPower.DeviceLibrary` (not public
  help) — needed to certify Models 2/3/5/6/8.
- **`RelayLineSection.{Pickup, SecondaryI}` are DESIGN-OPEN in the DB itself** ("Chet to decide" / "To
  decide") — unfinished source fields; do not rely on them. `[DVL-DB]` `[DEFERRED]`
- **BSL `v_a`/`v_b` column-order vs DB row-order** caveat — verify before shipping any BSL curve. `[R3]`

**Close path (the relay equivalent of the breaker INVEQ §5 plan):** one **Ghidra-headless run on
`D:\EasyPower\EasyPower.exe`** for `CTccRelayCurveBase` + the per-family curve evaluators, **plus
EasyPower-captured fixtures** (real plotted curves exported from EasyPower, not synthetic) to move the
analytical families BOUNDED→PROVEN. This is a larger effort than the breaker `CalcThermEq` close (more
families, no loader pre-recovered) — scope it as its own lane after the breaker INVEQ close.

---

## 8. Cross-references
- The shared `Manufacturers` dimension + the ETU/SST sensor world the SST-2 bridge borrows → **G1 / G4**.
- The breaker trip-family model this parallels (and the SST-1 bridge that SST-2 mirrors) → **G0 / G1 §2F**.
- The breaker field-trust matrix the 41 SST-2 relays route into → **G4**.
- The SSoT Law, provenance tags (incl. `[EZPDOC]`), evidence base → **00-MASTER-INDEX**.

---

*GR authored 2026-05-31 from the relay discovery/validation campaign (`_discovery/_relay/` R1–R3),
read-only on all sources. Pending: the native-kernel Ghidra recovery + EasyPower-captured fixtures (§7).*
