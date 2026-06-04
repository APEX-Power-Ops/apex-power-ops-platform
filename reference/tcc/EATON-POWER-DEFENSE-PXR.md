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
PDG2/3/4/5-LSI + PDG6-LSIGM, `i2x=1`), so the gross fix is re-pointing the breaker style. Verdicts:

| Frame (rows) | current (wrong) | rating-correct EP target | status |
|---|---|---|---|
| **PDG5** (10) | PXR 10 · PDG2-LSI [60–225] | **PXR20 · PDG5-LSI** [800–1600, `i2x=1`] | **SHIPPED** (migr 009; matches its own PDG5-1600 sibling — clean) |
| **PDG3** (12) | PXR20/25 · NRX-LSI(RF) [800–4000, `i2x=2`] | PXR20 · PDG3-LSI [125–600, `i2x=1`] | **rating-confirmed; SD-slope tradeoff** (`i2x=2`→`i2x=1`) — see below |
| **PDG6** (9) | PXR 10 · PDG2-LSI [60–225] | PXR20 · PDG6-LSIGM [1600–2500, `i2x=1`] | **rating-confirmed; over-offers G** (LSI→LSIG) — see below |

**The fidelity gap (the proper fix):** EasyPower's PXR20 PDG-LSI styles encode SD as `i2x=1`, but the
authoritative PXR SD is **flat or I²t** (`i2x=0`/`i2x=2`), and EasyPower lacks (a) a PXR20/25 `i2x=2` PD3
curve at 125–600 A and (b) a PD6 **LSI** (no-ground) style. So a fully-faithful PD3/PD6 fix = **import the
authoritative Eaton PXR curves** from TD012065EN/TD012068EN as cited `[VENDOR-DOC]` styles (the §108 loop,
extended), rather than re-binning to imperfect existing styles. PDG5 shipped because it matched EasyPower's
own correct sibling (no new judgment). **Next:** the PD2–6 PXR curve-catalog build (operator-directed scope).

## 5. Field-trust posture

PDG5 re-map = a data correction to EasyPower's own rating-correct style (faithful, internally consistent).
PDG3/PDG6 re-maps and any imported PXR curves are `[VENDOR-DOC]` (cited to TD0120xxEN/PXPM), the same trust
class as the §108 PXR2 setting catalog — VALUE-trusted, plotted as the nominal characteristic.
