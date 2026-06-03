# Tolerance Coverage Punch List — the road to true per-manufacturer tolerances across the board

> **The forward tracker for the north-star product.** This is the single source of truth for *what
> remains* to reach **true per-manufacturer protection tolerances for every device**, and the status of
> each layer. We chip away systematically, smallest durable bites first. **Every closed item lands in the
> owning guide (G0–G4 / GR) first** (SSoT Law) so coverage is permanent — we never fall back to
> re-deriving from the DLLs. Cite this list like any guide.

- **Status:** LIVING TRACKER — created 2026-06-02. Re-confirm counts live (`[VERIFIED-LIVE]`) when a lane is scheduled.
- **Home:** `apex-power-ops-platform/reference/tcc/` · linked from `00-MASTER-INDEX.md` (guide map + §5).

---

## The north star (the asset)

A product with **true per-manufacturer protection tolerances across the board** — every breaker, trip
unit, and relay carrying authoritative, OEM-grounded pickup *and* timing tolerances. That completeness is
the value asset a PE firm capitalizes on. Incremental progress toward it is the goal; **progress is
perfect** — provided each bite is banked durably and the prior work stands.

## What "covered" means (the bar for an element)

Every protective element has **two tolerance facets**:

| Facet | What it is | Trust scale |
|---|---|---|
| **VALUE** | the computed pickup current / delay time | `db` · `verify` · `withheld` (G4 field-trust matrix §4/§6) |
| **BAND** | the **±** tolerance around the value | **per-manufacturer DB** · derived/standard |

**COVERED** = VALUE `db` **AND** BAND per-manufacturer. Anything less is a punch-list item. Where a value
is not yet `db`, the page **withholds the time** (honest, never fabricated) — so the tool is field-safe at
every stage; the punch list is about *coverage*, not *safety*.

## Operating discipline (so progress compounds, never resets)

1. **Close = update the guide first.** A lane is "done" when its finding is banked in G0–G4/GR with
   provenance — not when code merges. The guide is what survives.
2. **Reuse the proven promotion method.** The §107 template promotes a `withheld`/`verify` delay lane to
   `db`: **execute the EasyPower native kernel in-process (`TccBase.dll` via reflection) as the parity
   oracle, prove the managed solver bit-exact over the complete corpus, then promote in `delay_trust.py`.**
   This is the repeatable recipe for L1/L2/L3/L4 — not new research each time.
3. **Counts are cited, then re-confirmed at scheduling.** Sizes below are from G4 §3a / the §106 live
   measurement; re-query before committing a lane.

---

## The board — status snapshot

| # | Lane | Scope (count) | VALUE now | BAND now | Size | Status |
|---|---|---|---|---|---|---|
| — | **Pickups (LTPU/STPU/INST/GFPU)** | ~17,831 sensors | **db** ✓ | per-sensor DB ✓ | — | **BANKED** (validate L7) |
| — | **Direct-band delay (STD/GFD route 0)** | STD 4,364 / GFD 9,933 | **db** ✓ | open/clear (mfr) ✓ | — | **BANKED** |
| — | **LTD delay** | all ETU | **db** ✓ (I²t window §111) | engine window | — | **BANKED** (band → L5) |
| — | **STD-INVEQ Therm** | ~4,524 | **db** ✓ (native §107) | — | — | **BANKED** |
| L1 | **GF-INVEQ Therm + Ansi** (one field[13] lane) | ~1,690 GFD + 23 Ansi | verify / withheld | — | S | **PAUSED** — `field[13]` evidence (you); both promote together |
| ~~L2~~ | ~~GF-INVEQ Ansi (standalone)~~ | — | — | — | — | **MERGED INTO L1** (2026-06-02) — shares `field[13]`, not independent |
| L3 | GE-TU delay solver | STD 235 / GFD 209 | withheld | — | M | OPEN — separate trip-unit math |
| L4 | **I2X / Iˣt delay solver** | STD 8,708 / GFD 5,976 (~15k) | withheld | — | **M (resized 06-03; ~98% = banked I²t)** | OPEN — biggest single lever; gating verify DONE §113 |
| L5 | Delay tolerance BANDS (per-mfr ± on time) | LTD + derived rows | **LTD: db (per-mfr DS2_TOL)** | per-mfr DB band | M | **LTD DONE §114**; STD/GFD + ET 1.0 remain |
| L6 | Envelope-only setting+tolerance catalog | ~4,106 families (PXR2 seeded) | — | `[VENDOR-DOC]` | L (incremental) | IN PROGRESS — validated-library loop |
| L7 | Pickup BAND validation vs OEM | per family | db | per-sensor DB | M | OPEN — confirm DB = true OEM per-mfr |
| L8 | TMT thermal time/band | TMT population | thermal verify | mag DB ✓ | M | OPEN |
| L9 | EMT pickup→current calc | EMT population | withheld | DB ✓ | M | OPEN |
| L10 | Relays (GR) — analytical curves | Models 1–6 | BOUNDED | stored data | L (separate) | OPEN — native kernel UNRECOVERED |

---

## The lanes (detail + the proven path to close each)

### L1 — GF-INVEQ Therm **+ Ansi** → db  ·  ~1,690 GFD + 23 Ansi  ·  PAUSED (operator evidence)
**One lane, two families, one blocker (merged 2026-06-02 — see below).** GF runtime is `byICalc=1`
(`num3/num4 = field[13]` ≠ pickup), so the managed `num3=num6` form isn't native-faithful; `rIRef<rM` GF rows
return None. **Blocker:** `field[13]` provenance (hypothesis: sensor/frame rating — not yet `[DLL]`-confirmed).
**Close:** confirm `field[13]/pickup` from operator evidence (or sweep it in the oracle vs an EasyPower-GUI GF
reference curve) → correct the managed `field[13]` basis → re-validate **both** families bit-exact → promote.
Oracle harness preserved at `output/inveq-parity/oracle/`. `[G4 §3f/§5]`

> **L2 (GF-Ansi) MERGED into L1 — finding 2026-06-02.** Decomp of `CalcAnsiEqGF` proved its pickup-basis
> selection is **byte-identical to `CalcThermEq`** (`byICalc {0→field[16], 1→field[13], 2→field[12]}`), so GF-Ansi
> anchors on the **same `field[13]`** at runtime — it is **not** an independent ship. The recovered Ansi formula
> `T(M)=rA+rB/M′+rD/M′²+rE/M′³` (C37.112 inverse-time) + its flat-degenerate branch are now **banked in G4 §3f**
> and **structure-validated** (monotone inverse curve). When `field[13]` lands, the 1,690 Therm + 23 Ansi rows
> promote **together** in one motion. Net effect: removed a phantom "XS standalone" bite; de-risked the GF lane.

### L3 — GE-TU delay solver → db  ·  STD 235 + GFD 209  ·  M
GE trip-unit STD/Gnd (routes 3/4) use a separate solver not built. **Close:** RE the GE-TU delay math
(check for a `TccBase.dll` kernel to oracle, same as §107) → managed solver → parity → promote. `[G4 §3a]`

### L4 — I2X / Iˣt delay solver → db  ·  STD 8,708 + GFD 5,976 (~15k)  ·  **M (re-sized down 2026-06-03)**  ·  THE BIG LEVER
The Iˣt slope family (route 1) solver isn't wired — this is ~half of all withheld delay cells. **Gating
verification DONE 2026-06-03 (I2X-1/I2X-2, STATE §113) — triangulated decompile + staging DB + managed
routing, and it CORRECTS the 2026-06-02 scout hypothesis:** route-1 is **NOT** the `CalcThermEq` polynomial.
It is the **`CIxt` power-law kernel** (`TccBase.dll` 24248-24297): `t(M) = T_anchor·(I_anchor/M)^X`
(equivalently `K = I_anchor^X·T_anchor`, `t = K/Iˣ`). The `SetSTDB_{Flat,Inverse}Delay*` setters (24440-24531)
store `(byICalc, rTmin, rX, rTref, rIref, rM)` where **`rX` is the exponent, `rIref/rTref` the anchor** — a
power law, not a Therm shape. The native render discriminator is `IsSTDB_Ixt` (`bool[709]`, read by
`GetMin{Open,Clear}STDB` 26398-26442): **true → Inverse block (the Iˣt ramp), false → Flat block (definite-time
floor)**.
- **Per-band shape** = `DatSection3STD.I2X` smallint: **0/NULL = flat-only** (time = `STD_OPEN`/`STD_CLEAR`, definite);
  **1 = Iˣt-ramp-only** (anchor `I_OPEN`/`T_OPEN`, `I_CLEAR`/`T_CLEAR`); **2 = composite** (ramp **+** flat floor).
  Anchor multiple varies per band (12/14.4, 10, 8, 6, 7, 8.3/12 …) and open≠clear — **read it, do not hardcode 6×**.
- **Exponent X** = sensor-level `DatSensor.DS3_I2T_VAL` (STD) / `DS1GF_I2T_VAL` (GFD), gated by `DS{3,1GF}_SEC3_I2T=1`.
  **X = 2.0 for 8,439/8,708 STD (96.9%) and 5,953/5,976 GFD (99.6%) — ~14,392/14,684 (98%).** Variable tail
  ~235 (mostly x=1 linear `I·t`; a few 5.0/2.09/2.17/0.49…); ~48 disabled (`-1.0`/NULL → withhold).
**Implication — L4 is M, not the monster.** ~98% collapse to the **exact I²t closed form already shipped +
live-verified for LTD (§111)**, generalized to read the per-band anchor; the variable-x tail is the SAME one-line
kernel reading `X` from `I2T_VAL`. No `CalcThermEq`, no polynomial root-find.
- **DONE (I2X-3, 2026-06-03):** the validated Iˣt evaluator `packages/calc-engine/.../etu_ixt.py`
  (`t = T_anchor·(I_anchor/M)^X`, mirroring native `CIxt` semantics — `|x|`, sentinel/zero guards — + the
  flat/ramp/composite shape dispatch + field-trust gating: flat & ramp SUPPORTED, composite & unknown WITHHELD)
  + DB-anchored parity fixtures + 19-test parity suite (`test_etu_ixt_parity.py`, all green) whose expected times
  are hand-derived from the decompiled `CIxt` at binary-exact multiples (independent spec, not a restatement).
  Prod band tables carry `i_open/i_clear/t_open/t_clear/i2x` (+ STD `std_open/std_clear` floor). **CORRECTION
  (I2X-6 prod read, 2026-06-03, STATE §117):** there is **no `exp_x`/`std_x` on `tcc.etu_std_bands`** — the exponent
  is a **sensor** field (`DS3_I2T_VAL`), so the wiring sources X from the sensor (default 2). Threading = the proven
  LTD §111 convention (anchor ×pickup, test ×pickup → pickup cancels).
- **DONE (I2X-4 native-CIxt oracle capstone, 2026-06-03, STATE §116):** built `output/inveq-parity/oracle/ixt_oracle.exe`
  (the §107 recipe — `CIxt.{ctor}`+`ComputeT` invoked by reflection over `TccBase.dll`) and confirmed `etu_ixt.ixt_time`
  **BIT-EXACT (max 0 ULP / 20 ramp points)** to the native kernel. Fixture corrected to native-exact (one 1-ULP literal);
  19 parity tests green. **Flat + ramp are now native-grade validated** (§107 "db" bar). Licensed DLL stays in git-ignored `output/`.
- **DONE (I2X-5 composite combine rule RECOVERED, 2026-06-03, STATE §116):** the I2X=2 composite (the *largest* band
  group at 64,840 — the BULK of route-1, not a tail) combine rule is **`t(M) = max(ixt_ramp(M), std_floor)`**,
  decompile-confirmed (not a guess): the Inverse block carries the `CIxt` ramp anchor + an `rTmin` floor
  (`GetMin{Open,Clear}STDB` 26398-26442), and that floor is applied as a min-time clamp on the rendered curve
  identically across every SST renderer (`CalcIeeeEq2` 27005-27017, `CalcGESMREq2` 27251-27281, and the explicit
  `max(rTmin,dMinTime)` lambda in `CalcThermEq2` 27228-27240). DB map: floor ← `STD_OPEN/STD_CLEAR`, ramp anchor ←
  `I_OPEN/T_OPEN`·`I_CLEAR/T_CLEAR`, X ← `DS3_I2T_VAL`. **IMPLEMENTED in `etu_ixt` (commit `apex aa9b89ea`)** —
  `i2x_delay_surface` now SUPPORTS composite (s17 fixture + floor-clamp test, 20 parity green). **Field-trust tier =
  `verify`** (combine rule decompile-confirmed + ramp native-bit-exact, but full render not spot-checked). Capture
  scout: `ComputeIXT` is the *inverse* (amps-from-time) so a native render means driving a full `RecalcCurve_*`
  (heavy) → the **`verify`→`db` gate is a captured EasyPower curve** spot-check (deferred). `[G4 §3b·I2X · STATE §120]`
- **DONE (I2X-6 prod data check, 2026-06-03, STATE §117 — via dispatch):** Codex ran the prod read.
  **STD route-1 is well-populated** (ramp anchors 14,161/14,181; composite anchors 64,558/64,840 + floor 100%);
  **GFD is gappier** (ramp 7,769/12,104 NULL anchors; no composite `gfd_x`). The exponent is **on the sensor**
  (`DS3_I2T_VAL`), not the band → source X from the sensor (default 2 for ~98%); withhold the NULL-anchor gaps;
  wire **STD-first**, defer GFD pending a load fix.
- **Remaining (gated):** (b) **validate the composite render** — native composite-band render spot-check confirming
  `max(ramp, floor)`, then promote composite from WITHHELD; (c) confirm the **sensor exponent** column is in prod
  `tcc.etu_sensors` + populated (one more read; default 2 covers ~98%); (d) wire `etu_ixt` into `/calculate`
  (STD-first; source X from sensor; withhold NULL-anchor + GFD), promote route-1 flat+ramp `withheld`→`db` in
  `delay_trust.py`, frontend un-withhold, SSoT-reconcile, deploy, live-verify (**operator decision boundary** —
  flips field-tech-facing trust).
`[G4 §3a/§3c/§4 · DLL TccBase.dll CIxt 24248-24297 / SetSTDB_* 24440-24531 / IsSTDB_Ixt 24196,26398-26442 ·
DatSection3STD + DatSensor.DS3_I2T_VAL/DS1GF_I2T_VAL · §113]`

### L5 — Delay tolerance BANDS (per-manufacturer ± on time)  ·  **LTD DONE 2026-06-03; B/C re-scoped+deferred; STD/GFD direct-band remains**
- **DONE — LTD time band now per-manufacturer.** Replaced the hardcoded `(0.7·nominal, nominal)` placeholder
  with the per-sensor DB tolerance `tcc.etu_ltd_params.ds2_tol_low/high`, applied as `nominal·(1 + tol/100)`.
  Tolerance is stored **per LTD curve TYPE** (I²T ≈ −27/+0, IEEE/IEC ±10 %, I⁴T −38.81/+9.7), so the loader pairs
  the **I²T row** with the §111 I²t-rendered window (`_load_ltd_time_tolerance`: prefer I²T → else unambiguous
  sensor value → else generic). Generic fallback is **flagged** (`timing_source=…_generic`, UI `est` marker).
  Tests green, deployed + live-verified. `[G4 §4 · router `_load_ltd_time_tolerance` · §114]`
- **Remaining:** (a) **ET 1.0 family** (no `ds2_tol` row — e.g. MGA36600) → source ±10 % from curve 613-14
  `[L5-LTD-C — DEFERRED 2026-06-03: gated on the ET 1.0 → trip-unit bridge; that bridge (whole ETU-library family
  becomes selectable) is the real lift, band sourcing trivial once unblocked]`; (b) **curve-type-aware render**
  `[L5-LTD-B — INVESTIGATED + DEFERRED 2026-06-03]`: `DatSensorSec2` shows the §111 I²t render is **exact** for all
  **110 single-curve** sensors (100 % I²t — 62 Thermal-I²T, 48 I2T) and a valid default for the **1,009** multi-curve
  sensors that offer I²t (I²t = the standard LV long-time characteristic, usually fixed by design); the **only**
  non-I²t-only sensors are **8 exotic MTX1 "delay-at-6×/7.2×" units** (likely unserved) → **not a correctness gap**,
  it's an optional Screen-2 LTD curve-selector feature (operator product call); (c) **STD/GFD direct-band** time
  tolerances — confirm the open/clear band is per-mfr **(the real remaining L5 engineering)**.

### L6 — Envelope-only setting + tolerance catalog  ·  ~4,106 families  ·  L (incremental)
~23% of ETU sensors store only min/max envelopes; their real dial taps **and** tolerances live in OEM docs
(`[VENDOR-DOC]`). The **validated-library loop** is shipped and seeded (Eaton PXR2 20D/25 LSI @225A). **Close:**
one cited family/rating at a time — the ideal "small bite." Each adds real settable taps + per-mfr tolerances.
`[G1 §7]`

### L7 — Pickup BAND validation vs OEM  ·  M
Pickup VALUES are `db`; the per-sensor DB tolerance *bands* are served as authoritative, but the field-tol MVP
B0.1 finding showed some diverge from NETA-standard (e.g. GFPU −20%/0 vs ±10%) — decided **per-sensor DB is
authoritative** (OEM per-sensor). **Close:** validate the DB bands against OEM published tolerances per
manufacturer/family, upgrading any DB-derived approximations to confirmed per-mfr values. `[field-tol MVP B0.1; G4]`

### L8 — TMT thermal time/band → db  ·  M
TMT magnetic INST pickup is DB ±tol (field-usable); the thermal long-time time/band is curve-governed
("verify"). **Close:** validate the thermal LT curve/band per manufacturer. `[G4; lvbreakertcc §105]`

### L9 — EMT pickup→current calc → db  ·  M
EMT pickup setting + ±tol are DB; the pickup→test-current conversion is not engine-validated (withheld).
**Close:** validate the EMT current calc per family. `[G4; lvbreakertcc §105]`

### L10 — Relays (GR) analytical curves → db  ·  L (separate large lane)
The native relay evaluator (`CTccRelayCurveBase` + per-family classes) decompiled to size-only shells — **no
`[DLL]` relay formula.** Platform solvers (TCP/IEC/MEQ/BSL/SWZ/PCD) validated on synthetic fixtures only →
BOUNDED. **Close:** Ghidra-headless on `EasyPower.exe` + EasyPower-captured fixtures (larger than the breaker
INVEQ close). Ship-now relay layer = stored data (settings + raw TCP grid). `[GR §7]` **L10 is the
*fidelity* climb of the relay lane; the *product* climb (cascade → NETA serving → field-sheet UI) is
tracked in [`GR-RELAY-ROADMAP.md`](GR-RELAY-ROADMAP.md) (they meet at roadmap Chip 5 = this lane). The
roadmap's Chip 1 (`relay_trust.py` field-trust classifier) is DONE (2026-06-03).**

---

## Banked — do not re-derive (the floor that must never regress)

These are closed and locked in the guides; reopening only on a cited reason:
- **All four pickup VALUES** `db` across ~17,831 sensors; **absent-element handling** (NULL tol ⇔ element
  absent — the §107 drop-the-±10) `[G4]`.
- **Direct-band STD/GFD (route 0)** VALUE+band `db` (open/clear manufacturer band) `[G4 §3a]`.
- **LTD** VALUE `db` — the I²t reference window, band setting = trip time at 6× Ir `[G4 §4 · §111]`.
- **STD-INVEQ Therm** VALUE `db` — native-kernel bit-exact `[G4 §3f · §107]`.
- **Envelope-only catalog framework** shipped; PXR2 seeded `[G1 §7 · §108]`.
- **The breaker→ETU SST bridge** recovered end-to-end `[G0 §3 / G1 D1 / §104]`.
- **Per-sensor delay-route field-trust gating** live (withhold-not-fabricate) `[G4 §6 · §106]`.

## Suggested sequence (smallest durable bites first)
**L1** (GF Therm **+** Ansi, one motion — gated on your `field[13]` evidence; formula side already banked +
structure-validated 2026-06-02) → **L7/L5** (band validation / per-mfr time tol, bounded) → **L6** (catalog,
one cited family per bite — open-ended but always-additive) → **L3** (GE-TU) → **L4** (I2X — the deliberate big
campaign, the ~15k lever) → **L8/L9** (TMT/EMT) → **L10** (relays — its own large lane).

> **What an autonomous bite can/can't do right now (2026-06-02):** L1 is gated on operator `field[13]` evidence
> (field-trust law forbids promoting on the unconfirmed hypothesis); L5/L7/L6/L8/L9 need OEM/vendor tolerance
> data not yet in hand; L3/L10 are RE campaigns needing the native-kernel oracle build. **L4's gating RE is now
> DONE (§113)** — its kernel is the banked I²t closed form (~98% x=2) generalized to per-band anchors + sensor `X`,
> so L4 no longer needs a from-scratch kernel; remaining L4 work is implementation + the §107 oracle parity pass
> (no external inputs needed). So the next *new coverage* most likely comes from either (a) your `field[13]`
> evidence unlocking L1 (both GF families), or (b) building the L4 I2X solver (now an M-sized implementation, not
> a monster RE). The GF formula RE is fully banked, so L1's remaining work is just the `field[13]` anchor + a
> re-validate.

*Last updated 2026-06-02 — created. Update status + bump counts (`[VERIFIED-LIVE]`) as lanes close.*
