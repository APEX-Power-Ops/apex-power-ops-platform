# Micrologic 6.0 A/E — Validated Trip-Unit Curve Reference `[VENDOR-DOC]`

**Status:** VALIDATED (datasheet + governed-DB cross-checked) · **Trust class:** `[VENDOR-DOC]`
**Sources:** Schneider *Micrologic 2.0A–7.0A* user manual (`micrologic_20_70a_eng`, operator-supplied) ·
governed `tcc` trip-style **246** "MICROLOGIC 6.0A" band records · native `TccBase.dll` `CIxt` kernel (I2X-4).
**Encoded in code:** `apps/control-plane-api/services/neta/micrologic_curves.py` (the rating-independent
S/G I2X band spec) + `etu_ixt.py` (the validated kernel). **Shipped:** STATE §135 (long-time) / §136
(S/G composite) / §137 (band-less serving + I2X-6 `/calculate` flip).

The Square D / Schneider **Micrologic 6.0 A/E** (Masterpact NW/NT, Compact NS) is a full **LSIG**
electronic trip unit. This note is the single source of truth for its time-current model on the
`lvbreakertcc` page.

## 1. Protection elements (per the dial faces + datasheet)

| El | Pickup | Delay | Curve model |
|----|--------|-------|-------------|
| **L** long-time | Ir = 0.4…1·In (9 taps) | tr = 0.5…24 s @ **6·Ir** | I²t: `t(I) = tr·(6·Ir/I)²` |
| **S** short-time | Isd = 1.5…10·Ir (9 taps) | tsd = 0.1/0.2/0.3/0.4 s, **I²t ON/OFF** | I2X **composite** `max(ramp, floor)`, ramp ref **Ir** |
| **I** instantaneous | Ii = 2…15·In, Off | — | definite at breaker clearing time |
| **G** ground-fault | Ig = A…J·In, **1200 A max** | tg = 0.1/0.2/0.3/0.4 s, **I²t ON/OFF** | I2X **composite**, ramp ref **In** |

- "**Both delays built in**": tsd and tg each carry an **I²t-ON ramp** *and* an **I²t-OFF definite floor**.
  The curve is the composite — the Iˣt ramp clamped below by the definite floor: `t = max(ramp, floor)`.
- **7.0** replaces ground-fault with **earth-leakage** (Vigi IΔn / tΔ, a residual-current/RCD function) —
  no phase-overcurrent TCC; EasyPower carries no earth-leakage field (STATE §134). 5.0 = LSI (no ground).

## 2. The I2X composite model (S and G)

The validated route-1 (I2X / Iˣt) kernel (`etu_ixt`, native `CIxt.ComputeT` bit-exact, I2X-4):

```
ramp(M)   = t_open · (i_open / M) ** X          # the Iˣt power law
t(M)      = max(ramp(M), floor)                 # composite (I2X=2), decompile-confirmed (I2X-5)
```

- **M (the current axis):** `M = I / ref`. **STD references Ir** (the datasheet ×Ir axis);
  **GFD references In** (the ×In axis). Datasheet-verified: the ramp meets the floor **exactly at the
  band `i_open` anchor** — **10·Ir** for S, **1·In** for G — where the published curves flatten (STATE §136).
- **X (exponent):** the per-sensor `stpu_i2t_val` / `gfpu_i2t_val` (native `DS3_I2T_VAL` / `DS1GF_I2T_VAL`),
  **= 2** for the 6.0A (true I²t).
- **floor:** the band's definite-time setting (`std_open` / `gfd_open`).

## 3. Canonical rating-independent S/G band spec

Verbatim from `tcc` trip-style 246 (cross-checked vs the datasheet); the delays + multiples are identical
on every 6.0A frame, so one set serves all ratings. Codified in `micrologic_curves.CANONICAL_*_BANDS`.

**Short-time (S)** — all `i2x=2` composite, ramp anchor `i_open = 10` (×Ir):

| dial | t_open | t_clear | floor_open | floor_clear |
|------|--------|---------|------------|-------------|
| 0.1 | 0.08 | 0.10 | 0.08 | 0.14 |
| 0.2 | 0.16 | 0.20 | 0.14 | 0.20 |
| 0.3 | 0.24 | 0.30 | 0.23 | 0.32 |
| 0.4 | 0.32 | 0.40 | 0.35 | 0.50 |

**Ground-fault (G)** — `i2x=2` composite, ramp anchor `i_open = 1` (×In); the **Off** band is an I²t-OFF
definite-time flat:

| dial | i2x | t_open | t_clear | floor_open | floor_clear |
|------|-----|--------|---------|------------|-------------|
| Off | flat | — | — | 0.02 | 0.08 |
| 0.1 | 2 | 0.08 | 0.10 | 0.08 | 0.14 |
| 0.2 | 2 | 0.16 | 0.20 | 0.14 | 0.20 |
| 0.3 | 2 | 0.24 | 0.30 | 0.23 | 0.32 |
| 0.4 | 2 | 0.32 | 0.40 | 0.35 | 0.50 |

## 4. Data-quality note (the band-less style records)

"MICROLOGIC 6.0A" spans **three** `tcc` trip-style records: **246** carries the S/G bands above; **238**
and **1919** (~158 sensors, incl. the former default 25506) are **band-less** (a load gap — the same
device, but the `etu_std_bands` / `etu_gfd_bands` rows weren't loaded). Until those styles are reloaded
from the source library (the durable fix — governed prod write), the serving layer falls back to the
canonical spec above (cited) for both Screen 2 (`/settings`) and the plot, so a band-less 6.0A still
renders the full LSIG (STATE §137; the Eaton-PXR2 "serve the validated characteristic" pattern, G1 §7).

## 5. Field-trust posture (G4)

- **L (long-time):** the I²t window is implementation-complete + window-proven → **db** (G4 row 5).
- **S/G (I2X composite):** `flat`/`ramp` → **db** (native bit-exact, I2X-4); **`composite` → `verify`**
  (combine rule decompile-confirmed + ramp native-validated; full native-render spot-check is the open
  gate). `/calculate` computes the composite field time via `etu_ixt` and badges it **verify** (I2X-6,
  STATE §137); the kernel withholds (→ unsupported) on NULL anchors / unknown shape. The inject current
  (NETA test point) is always field-correct.
- The plot curve is a **nominal illustration** (supplemental); the field-authoritative surface is the
  Screen-2 tolerance table.
