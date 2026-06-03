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
| L4 | **I2X / Iˣt delay solver** | STD 8,708 / GFD 5,976 (~15k) | withheld | — | **L (the monster)** | OPEN — biggest single lever |
| L5 | Delay tolerance BANDS (per-mfr ± on time) | LTD + derived rows | — | engine window | M | OPEN — per-mfr time tolerance |
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

### L4 — I2X / Iˣt delay solver → db  ·  STD 8,708 + GFD 5,976 (~15k)  ·  L  ·  THE BIG LEVER
The I²t / Iˣ·t slope family (route 1) solver isn't built — this is ~half of all withheld delay cells. **Risk
re-characterized by a 2026-06-02 decomp scout (de-risk):** there is **no separate native breaker I2X kernel** —
`grep` of `TccBase.dll` finds the only `*I2tEquation` functions are **relay** ones (`CTccRelayCurveBase.*LockedRotorConstantI2tEquation`,
GR lane), not breaker. Breaker STD delay curves are parameterized by the `CTccLVBreakerCurveSST.SetSTDB_{Flat,Inverse}Delay{Open,Clear}[ZSI]`
**setters** (24440-24531), which store the **same `(byICalc, rTmin, rX, rTref, rIref, rM)` Therm-shape params**
and are rendered by the **`CalcThermEq`/`CalcThermEq3` family we already recovered + executed bit-exact in §107**.
**Implication:** L4 is likely *"wire the route-1 I2X data → the already-recovered §107 kernel + oracle-validate,"*
not a from-scratch kernel RE — so it may be **M, not the monster**. **One verification gates the resize:**
confirm how the route-1 populator natively maps I2X (the `i2x`/`exp_x` slope) onto `SetSTDB_Flat` vs
`SetSTDB_Inverse` (i.e. flat-I²t vs a genuine Iˣt power law). That single check is L4's first step; everything
after reuses the §107 oracle recipe. `[G4 §3a/§3c · DLL TccBase.dll SetSTDB_* 24440-24531]`

### L5 — Delay tolerance BANDS (per-manufacturer ± on time)  ·  M
Direct-band STD/GFD carry the manufacturer open/clear band; LTD currently uses the engine's
`(0.7·nominal, nominal)` window. **Close:** source per-manufacturer LTD/delay *time* tolerances (OEM curve
bands) so the ± is per-mfr, not a generic window. `[G4 §4 — §111 note]`

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
INVEQ close). Ship-now relay layer = stored data (settings + raw TCP grid). `[GR §7]`

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
> data not yet in hand; L3/L4/L10 are RE campaigns needing the native-kernel oracle build. So the next *new
> coverage* most likely comes from either (a) your `field[13]` evidence unlocking L1 (both GF families), or
> (b) scheduling the L4 I2X campaign (RE + oracle, the §107 recipe — no external inputs needed). The GF formula
> RE is now fully banked, so L1's remaining work is just the `field[13]` anchor + a re-validate.

*Last updated 2026-06-02 — created. Update status + bump counts (`[VERIFIED-LIVE]`) as lanes close.*
