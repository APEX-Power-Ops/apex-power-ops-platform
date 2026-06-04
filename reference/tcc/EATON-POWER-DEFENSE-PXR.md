# Eaton Power Defense (PDG2–6) + PXR 10/20/20D/25 — Validated Curve Reference `[VENDOR-DOC]`

**Status:** authoritative sources mapped (2026-06-04) · **Trust class:** `[VENDOR-DOC]`
**Purpose:** the durable foundation for correcting the Eaton Power Defense SST-bridge mis-mappings
(STATE §138/§139) and building the full PD2–6 PXR curve/setting catalog (the §108 PXR2 validated-library
loop, extended to the rest of the family).

## 1. Authoritative sources (operator-supplied, on host — NOT committed; cite + extract VALUES only)

- **Eaton Power Xpert Protection Manager (PXPM)** — `C:\Program Files (x86)\Eaton Corporation\Power Xpert
  Protection Manager\Resources\Datafiles\PXR2025MCCB.xml` (the PXR25 setpoint model: Frame=PD2–6, the
  setting IDs/ranges) + `ACB_MCCB_Para_Selection.xml`.
- **Eaton Power Defense TCC documents** (`…\RESA Power Ops…\Technical Data\Breaker Manuals & TCC\Eaton\`):
  - `…frame2-pd2-td012064en.pdf` (**TD012064EN** — already the §108 PXR2 20D/25 setting-catalog source)
  - `…frame3-pd3-td012065en.pdf` (**TD012065EN** — PD3)
  - `…frame5-pd5-td012067en.pdf` (**TD012067EN** — PD5)
  - `…frame6-pd6-td012068en.pdf` (**TD012068EN** — PD6)
  - `series-nrx-with-pxr-nf-and-rf-frames-AD013001EN.pdf` · `magnum-pxr-tcc-td013172en-2023_05.pdf` (NRX/Magnum)
- **Eaton Consulting Application Guide Vol. 4 / Tab 2 MCCB catalog — `CA08100005E` (V4-T2)** (operator-supplied
  2026-06-04): the consolidated Power Defense + Series G + MCP reference. Confirms the canonical frame→rating:
  **Frame Size 1 = 15–125 A (PDG1) · 2 = 15–225 A (PDG2) · 3 = 45–600 A (PDG3) · 4 = 300–800 A (PDG4) ·
  5 = 320–1200 A (PDG5) · 6 = 700–2500 A (PDG6)** · MCP 3–600 A; trip units Basic = PXR 10 (B), Standard =
  PXR 20 (E), Energy/programmable = PXR 25 (P). Used to authoritatively resolve the §151 PXR10/PDF3 SST residual.

## 2. Frame → rating structure (authoritative)

| Frame | Sensor ratings (A) | Ir range (A) | Trip units |
|-------|--------------------|--------------|------------|
| PDG2  | 60–250             | per §108      | PXR 20D/25 |
| **PDG3** | 125 / 250 / 400 / 600 | 45–600 (per-sensor Min–Max) | PXR 20 / 20D / 25 |
| PDG4  | 800–1200           | —             | PXR 20/20D/25 |
| PDG5  | 800–1600           | —             | PXR 20/20D/25 |
| **PDG6** | 1600 / 2000 / 2500 | per-frame Min–Max | PXR 20 / 20D / 25 |

Protection configs (PD6, code): **2 = LSI** · 3 = LSIG · 4 = LSI ARMS · 5 = LSIG ARMS — i.e. PD frames
ship in **LSI (no ground)** as well as LSIG.

## 3. The PXR curve model (selectable slopes — TD012065EN Figs 2–6, TD012068EN Figs 2–11)

The PXR 10/20/20D/25 trip is **selectable-slope**, not a single fixed curve:
- **Long delay:** I²t **or** I⁴t. Pickup = **110% of Ir, ±5%**; Ir 1 A steps. LD time **0.5–24 s**, 0.1 s steps, **+0%/−30%**.
- **Short delay:** **flat (definite)** *or* **I²t**. Isd **1.5–12×**, 0.1× steps, **±5%**. tsd **0.050–0.500 s**, 0.010 s steps,
  graded tolerance (+0/−20% @0.5–0.2 s → +0/−50% @0.09–0.05 s).
- **Instantaneous + override** (per frame); **Ground** I²t delay (PXR 20D/25, PXR 20).

## 4. The SST-bridge correction (STATE §138/§139) — status

EasyPower's source mis-maps the newer PD frames (native to its library; rank=id is bit-exact, prod is
bit-faithful — STATE §138). EasyPower **already carries rating-correct PDG-named styles** (PXR20 family:
PDG2/3/4/5-LSI + PDG6-LSIGM; STD/GFD route 1 (I2X), exponent X=2, with both flat and Iˣt-ramp bands —
see §6), so the gross fix is re-pointing the breaker style. Verdicts:

| Frame (rows) | current (wrong) | rating-correct EP target | status |
|---|---|---|---|
| **PDG5** (10) | PXR 10 · PDG2-LSI [60–225] | **PXR20 · PDG5-LSI** [800–1600, `i2x=1`] | **SHIPPED** (migr 009; matches its own PDG5-1600 sibling — clean) |
| **PDG3** (12) | PXR20/25 · NRX-LSI(RF) [800–4000, `i2x=2`] | PXR20 · PDG3-LSI [125–600, `i2x=1`] | **rating-confirmed; SD-slope tradeoff** (`i2x=2`→`i2x=1`) — see below |
| **PDG6** (9) | PXR 10 · PDG2-LSI [60–225] | PXR20 · PDG6-LSIGM [1600–2500, `i2x=1`] | **rating-confirmed; over-offers G** (LSI→LSIG) — see below |

**The residual fix = the rating re-point only (no curve-override).** PDG5 shipped because it matched
EasyPower's own correct sibling (no new judgment); PDG3/PDG6 are migration `010` (rating-confirmed against
TD012065EN/068EN). The PD6 LSI→LSIGM **over-offers a G element** for a PD6-LSI breaker (a selection nuance,
documented in `010`'s header — not a curve error). **`r_cont_current` rating-narrow** of the bridge (so a
correct mapping surfaces the ONE matching sensor, not the whole style set) needs a governed re-load — prod
`brk_*_styles` dropped the column (STATE §138) — tracked under #74. **`r_cont_current` re-load DONE (§145).**

**§151 — PXR10 PDF3/600 A frame-size residual fixed (2026-06-04, #74 Tier 4).** One Eaton PXR bridge style
survived §144: `brk_mccb_styles` id 10126, frame **`PDF3-N PXR 600A`** (rcc 600), was assigned `PXR 10 ·
PDG2-LSI` (60–225 A sensors). Per **CA08100005E** (Frame Size 3 = 45–600 A) the 600 A PDF3 frame is **PDG3**;
re-pointed `tmt_sst_style` `PDG2-LSI`→`PDG3-LSI` (prod PDG3-LSI carries the 600 A sensor; the §145 narrow now
serves it). Migration `fix_eaton_pxr10_pdf3_frame_size_mismatch` (in-migration assert: 1 row + resolves to a
600 A sensor). It was the **only** `PDF<n>`≠`PDG<m>` frame-size mismatch across all Eaton PXR bridge rows.

> **The earlier "SD-slope fidelity gap" was OVERTURNED by source data — see §6.** EasyPower's `i2x` is its
> per-band SHAPE code (`0`=flat · `1`=Iˣt ramp · `2`=composite), **not** the authoritative doc's slope
> exponent. The PD-LSI sensors already carry BOTH the flat (`i2x=0`) and the I²t-ramp (`i2x=1`, X=2)
> selectable SD bands — i.e. the authoritative selectable flat-or-I²t model is **already faithfully encoded**,
> both tiers `db`. There is no PXR curve to import (an `i2x=2` *composite* is not a PXR SD mode at all).

## 5. Field-trust posture

PDG5 re-map = a data correction to EasyPower's own rating-correct style (faithful, internally consistent).
PDG3/PDG6 re-maps are `[VENDOR-DOC]` (cited to TD0120xxEN/PXPM), the same trust class as the §108 PXR2
setting catalog — VALUE-trusted, plotted as the nominal characteristic.

## 6. Curve-fidelity verification (STATE §142) — the PD-LSI styles are already faithful

The #73 "render the authoritative PXR curve because EasyPower's `i2x=1` is an approximation" premise was
**falsified against live prod** (read-only, 2026-06-04) — the third overturned premise in this arc (after
#59 "scramble" and #71 "load gap"). For the SST-correction targets — **PXR20 PDG3-LSI (style 2466), PXR20
PDG5-LSI (2439), PXR20 PDG6-LSIGM (2377), PXR20D/25 PDG6-LSIGM (2376)**:

- **STD + GFD route = 1 (I2X)**, `stpu_i2t_val`/`gfpu_i2t_val` = **X = 2** (I²t).
- Each sensor carries a **full selectable SD band set**, not one fixed slope:
  - **`i2x=0`** bands (STD ordinals 0–6; GFD 343 rows) = the **flat / definite-time** SD options
    (0.05–0.5 s). Shape → `flat` → **`db`** (identical to a route-0 direct band).
  - **`i2x=1`** bands (STD ordinals 7–9; GFD 105 rows) = the **Iˣt ramp** = the **I²t** SD slope
    (`t = t_open·(i_open/M)^X`, X=2; `i_open=8`). Shape → `ramp` → **`db`** — native-bit-exact to the
    EasyPower `CIxt.ComputeT` kernel (I2X-4, 0 ULP).
- **Both SD slope options of the authoritative PXR model (flat OR I²t) are therefore already encoded and
  already `db`-trusted.** EasyPower's `i2x` is a band-SHAPE code (0/1/2), *not* the doc's slope exponent; an
  `i2x=2` *composite* (ramp clamped to a floor) is not a PXR SD mode, so there is nothing to import.
- **Tolerances match the authoritative doc** (§3): SD pickup ±5%, INST ±10%, GF ±10%; LD time −30/+0 on the
  PXR20D/25 style and curve-type −10/+10 on PXR20 (per §114's curve-type grading); LTPU stored as the
  pickup must-trip band (+5/+15%, the standard EP representation), not the setpoint ±5%.

**⇒ No `pxr_curves` curve-override is built** — doing so would diverge from a faithful EasyPower record (the
anti-pattern). `services/neta/pxr_curves.py` stands as the cited `[VENDOR-DOC]` **validation reference**
(confirming EasyPower is faithful) and the **SST-correction driver** (`correct_sst_target`, used for migr
009/010). #73 is resolved by investigation; the only PD residual is the #74 `r_cont_current` rating-narrow.
