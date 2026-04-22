# TCC v5 Calculation Engine — Implementation Specification

**Purpose:** VS Code Claude handoff document for building `services/calc_engine/`
**Author:** Cowork Claude (C# source analysis + Supabase data mapping)
**Date:** 2026-03-20
**Status:** Partial implementation handoff. ETU core services are materially implemented, MAINT pickup metadata and request or response parity have advanced, but family coverage and full contract parity are still incomplete.

**Authority note:** This document is a backend-local implementation handoff, not the governing source of TCC architecture truth. Use it only after validating scope and claims against the paired authority stack in the `neta-ett-study-material` repository.

---

## 1. Package Structure

```
services/
  calc_engine/
    __init__.py           # Exports all public classes/functions
    etu_pickup.py         # ETUCalcMethod enum + pickup calculator  ← START HERE
    etu_curves.py         # IEEE inverse-time equation solver (STD/GFD)
    etu_ltd.py            # 5 LTD calculation methods (FULLY DECODED — Section 4)
    etu_merge.py          # Curve segment assembly + fillet (FULLY DECODED — Section 6)
    tmt_curves.py         # Catmull-Rom spline interpolation (FULLY DECODED — Section 5)
    coordination.py       # Multi-breaker coordination study (FUTURE)
```

---

## 2. Service B2: etu_pickup.py — ETU Pickup Calculator

### 2.1 ETUCalcMethod Enum

Maps to `tcc_etu_sensors.ltpu_calc`, `stpu_calc`, `inst_calc`, `gfpu_calc` columns.

```python
from enum import IntEnum

class ETUCalcMethod(IntEnum):
    NONE = -1              # Element not present → return 0.0
    SENSORFRAME = 0        # setting × sensor.rating
    PLUGTAP = 1            # setting × plug.value
    SENSORFRAME_MULT = 2   # setting × sensor.rating × multiplier
    PLUGTAP_MULT = 3       # setting × plug.value × multiplier
    LTPU = 4               # CASCADE: setting × ltpu_current (from LTPU result)
    SENSORFRAME_C = 5      # setting × sensor.rating × c_factor
    PLUGTAP_C = 6          # setting × plug.value × c_factor
    AMPS = 7               # setting is already in amperes
    GFPU = 8               # CASCADE: from GFPU result
    MULTWTH = 9            # Reserved (not seen in data)
    STPU = 10              # CASCADE: from STPU result
```

### 2.2 Calc Method Distribution (actual Supabase data)

| Element | Method -1 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---------|-----------|---|---|---|---|---|---|---|---|
| LTPU    | 33 | 2,006 | **7,292** | 628 | 114 | — | — | — | 1,369 |
| STPU    | 1,769 | 626 | 2,074 | — | — | **5,729** | 563 | 187 | 494 |
| INST    | 483 | 1,639 | **6,087** | — | — | 1,117 | 319 | 44 | 1,753 |
| GFPU    | **3,071** | 2,251 | 3,186 | — | — | — | 1,167 | 7 | 1,760 |

Bold = most common per element. Note: STPU method=4 means CASCADE from LTPU.

### 2.3 Supabase Column Mapping

**Old (SensorCalculator reference) → New (Supabase tcc_etu_sensors):**

| SensorCalculator Key | Supabase Column | Type |
|---------------------|-----------------|------|
| `SensorID` | `id` | int |
| `SensorValue` | `rating` | int |
| `DS1_PICKUP_CALC` | `ltpu_calc` | smallint |
| `DS3_PICKUP_CALC` | `stpu_calc` | smallint |
| `DS4_PICKUP_CALC` | `inst_calc` | smallint |
| `DS1GF_PICKUP_CALC` | `gfpu_calc` | smallint |
| `DS1_TOL_LOW` | `ltpu_tol_lo` | numeric(5,2) |
| `DS1_TOL_HIGH` | `ltpu_tol_hi` | numeric(5,2) |
| `DS3_TOL_LOW` | `stpu_tol_lo` | numeric(5,2) |
| `DS3_TOL_HIGH` | `stpu_tol_hi` | numeric(5,2) |
| `DS4_TOL_LOW` | `inst_tol_lo` | numeric(5,2) |
| `DS4_TOL_HIGH` | `inst_tol_hi` | numeric(5,2) |
| `DS1GF_TOL_LOW` | `gfpu_tol_lo` | numeric(10,2) |
| `DS1GF_TOL_HIGH` | `gfpu_tol_hi` | numeric(10,2) |

**Related tables for lookups:**

| Table | Used When | Key Columns |
|-------|-----------|-------------|
| `tcc_etu_plugs` | method=1,3,6 (PLUGTAP*) | `id`, `trip_style_id`, `value` |
| `tcc_etu_ltpu_pickups` | UI dial settings | `sensor_id`, `value`, `sort_order` |
| `tcc_etu_ltpu_multipliers` | method=2,3 (*_MULT) | `sensor_id`, `value` |
| `tcc_etu_stpu_pickups` | UI dial settings | `sensor_id`, `value` |
| `tcc_etu_inst_pickups` | UI dial settings | `sensor_id`, `value` |
| `tcc_etu_gfpu_pickups` | UI dial settings | `sensor_id`, `value` |

### 2.4 Implementation Notes

- Use SQLAlchemy models from `models/etu_core.py` and `models/etu_pickups.py`
- The calculator should accept a `Session` and `sensor_id`, fetch the sensor + plug data, then compute
- Tolerance calculation: `min = current × (1 + tol_lo/100)`, `max = current × (1 + tol_hi/100)`. Note tol_lo is typically negative (e.g., -10.00 means -10%)
- CASCADE methods (4=LTPU, 8=GFPU, 10=STPU) must be computed in dependency order: LTPU first, then STPU (may depend on LTPU), then INST, then GFPU
- Method 5 (SENSORFRAME_C) and 6 (PLUGTAP_C): the C factor comes from `tcc_etu_sensor_params` table (check `c_factor` or similar column)
- `calculate(..., maint_mode=True)` must derive MAINT capability from `tcc_etu_sensor_maint` data presence, not from a UI toggle field.
- Low-level calc-engine responses should propagate `maint_mode`, `maint_capable`, `maint_support_level`, warnings, and per-element MAINT metadata so they align with the higher-level NETA contract.

### 2.5 Golden Test Fixture — Sensor 6258

```json
{
  "sensor_id": 6258,
  "trip_style_id": 687,
  "rating": 600,
  "ltpu_calc": 1,
  "stpu_calc": 4,
  "inst_calc": 1,
  "gfpu_calc": -1,
  "ltpu_tol_lo": "5.00",
  "ltpu_tol_hi": "20.00",
  "stpu_tol_lo": "-10.00",
  "stpu_tol_hi": "10.00",
  "inst_tol_lo": "-10.00",
  "inst_tol_hi": "10.00",
  "plugs_for_style_687": [200, 250, 400, 600, 800, 1000, 1200, 1600, 2000, 2500]
}
```

**Example calculation with sensor 6258, plug=600, LTPU setting=0.8:**

- LTPU: method=1 (PLUGTAP) → 0.8 × 600 = **480A**
  - min = 480 × (1 + 5/100) = 504A  *(note: tol_lo=5.00 means +5% lower bound — unusual, verify)*
  - max = 480 × (1 + 20/100) = 576A
- STPU: method=4 (LTPU CASCADE) → stpu_setting × LTPU_current. If stpu_setting=4: 4 × 480 = **1920A**
  - min = 1920 × (1 - 10/100) = 1728A
  - max = 1920 × (1 + 10/100) = 2112A
- INST: method=1 (PLUGTAP) → inst_setting × 600. If inst_setting=10: **6000A**
- GFPU: method=-1 (NONE) → **0.0A** (element not present)

**NOTE:** The tolerance sign convention needs verification. Sensor 6258 has `ltpu_tol_lo=5.00` (positive) which is unusual. This may mean the low tolerance is +5% (asymmetric band). Check if the formula should be `current × (1 - abs(tol_lo)/100)` or `current × (1 + tol_lo/100)`. The SensorCalculator reference uses `(1 - tol_low/100)` and `(1 + tol_high/100)`.

### 2.6 Golden Test Fixture — Sensor 160 (simple PLUGTAP all elements)

```json
{
  "sensor_id": 160,
  "trip_style_id": "LVPCB",
  "rating": 1600,
  "ltpu_calc": 1,
  "stpu_calc": 1,
  "inst_calc": 1,
  "gfpu_calc": 0
}
```

All three main elements use PLUGTAP (method=1), GFPU uses SENSORFRAME (method=0). Simplest test case.

---

## 3. Service B3: etu_curves.py — IEEE Inverse-Time Equation Solver

### 3.1 Core Equation

The STD and GFD inverse-time delay equation (from IMPLEMENTATION_STATUS.md and confirmed in C# source):

```
T = (C1 / (I^C2 - 1) + C3 + C6) × LTD_band_multiplier
```

Where:
- `I` = Current / Pickup (normalized current ratio)
- `C1..C5` = IEEE curve coefficients stored in `tcc_etu_std_equations` and `tcc_etu_gfd_equations`
- `C6` = additional offset (often NULL)
- Each equation row has OPEN and CLEAR variants (8 columns each: `fd_open_1..6`, `fd_clear_1..6`)
- `in_out` flag: 0=out-only, 1=in-only, 2=both (determines which curves to generate)

### 3.2 STD Equation Table Structure (`tcc_etu_std_equations`)

| Column | Meaning | Maps to |
|--------|---------|---------|
| `sensor_id` | FK to tcc_etu_sensors | — |
| `ordinal` | Dial position (1-based) | STD band selection |
| `label` | Display label ("0", "0.1", "0.2"...) | UI display |
| `in_out` | 0=out, 1=in, 2=both | Curve generation flag |
| `fd_open_1` | C1 (open) | Numerator constant |
| `fd_open_2` | C2 (open) | Current exponent |
| `fd_open_3` | C3 (open) | Additive constant |
| `fd_open_4` | C4 (open) | *Not used in base IEEE eq — used in extended formula* |
| `fd_open_5` | C5 (open) | *Not used in base IEEE eq — used in extended formula* |
| `fd_open_6` | C6 (open, often NULL) | Additional offset |
| `fd_open_i_calc` | Pickup calc method for this curve | Same enum as ETUCalcMethod |
| `fd_clear_*` | Same structure for CLEAR curve | — |
| `id_open_*` | Inverse-delay OPEN coefficients | Used for ID curves |
| `id_clear_*` | Inverse-delay CLEAR coefficients | Used for ID curves |

### 3.3 C# IEEE Implementation (decoded from CalcIeeeEq2)

From the decompiled `CalcIeeeEq2` at line 158-306 of the C# source:

```python
def calc_ieee_eq2(coefficients, I_normalized, ltd_band_multiplier, tolerance_pct):
    """
    IEEE inverse-time equation.

    Args:
        coefficients: dict with keys c1, c2, c3, c4, c5, c6
        I_normalized: current / pickup (must be > 1.0)
        ltd_band_multiplier: LTD delay band setting
        tolerance_pct: tolerance percentage / 100

    Returns:
        trip time in seconds
    """
    c1, c2, c3, c6 = coefficients['c1'], coefficients['c2'], coefficients['c3'], coefficients.get('c6', 0)

    # Core IEEE equation
    T_base = (c1 / (I_normalized ** c2 - 1.0) + c3 + (c6 or 0)) * ltd_band_multiplier

    # Apply tolerance
    T_with_tol = (tolerance_pct + 1.0) * T_base

    # Apply fixed delay offset (c4 = additional time, from column fd_open_4/5)
    T_with_offset = T_base + coefficients.get('c4_offset', 0)  # c5 column in some variants

    # For CLEAR curve: use max(T_with_tol, T_with_offset)
    # For OPEN curve: use min(T_with_tol, T_with_offset)

    return T_base  # Simplified — see full implementation below
```

### 3.4 The 5 LTD Calculation Methods (dispatch)

The C# `CalcEquationLTDB` dispatches on `ltd_function` field (offset 82 in the struct):

| ltd_function | Method Name | Description |
|-------------|-------------|-------------|
| 1 | CalcThermEq2 | **Thermal** — `T = K × ln(1 / (1 - (I_ref/I)^n)) / ln(1/(1-(I_ref/I_thresh)^n))` |
| 2 | CalcIeeeEq2 | **IEEE** — `T = (C1/(I^C2 - 1) + C3 + C6) × LTD_mult` |
| 3 | CalcGESMREq2 | **GE-SMR** — `T = -102.4 × ln(1 - (1.12×rating)² / (I_effective²))` |
| 4 | CalcThermTU2 | **Thermal-TU** — Like Thermal but with TU offset parameter |
| 5 | CalcThermTUF2 | **Thermal-TUF** — Like Thermal-TU but simplified formula |

**For B3 (etu_curves.py), implement method 2 (IEEE) first** — it's the most common and uses the 6-coefficient equation stored in `tcc_etu_std_equations` / `tcc_etu_gfd_equations`. The other 4 methods go in `etu_ltd.py` (service B4, spec pending).

### 3.5 IEEE Curve Generation Algorithm (from C# CalcIeeeEq2)

```python
def generate_ieee_curve(sensor_id, ordinal, is_clear, max_amps, session):
    """
    Generate (current, time) curve points using IEEE inverse-time equation.

    Returns: list of (amps, seconds) tuples — the TCC curve
    """
    # 1. Load equation coefficients
    eq = session.query(ETUSTDEquation).filter_by(sensor_id=sensor_id, ordinal=ordinal).one()

    # 2. Select open or clear coefficients
    if is_clear:
        c1, c2, c3 = float(eq.fd_clear_1), float(eq.fd_clear_2), float(eq.fd_clear_3)
        c4, c5 = float(eq.fd_clear_4 or 0), float(eq.fd_clear_5 or 0)
        c6 = float(eq.fd_clear_6 or 0)
        tol_pct = c5 / 100.0  # C5 is tolerance percentage for clear
    else:
        c1, c2, c3 = float(eq.fd_open_1), float(eq.fd_open_2), float(eq.fd_open_3)
        c4, c5 = float(eq.fd_open_4 or 0), float(eq.fd_open_5 or 0)
        c6 = float(eq.fd_open_6 or 0)
        tol_pct = c5 / 100.0

    # 3. Get the LTDB pickup value (base current for normalization)
    pickup = get_calc_method_value_ltdb(sensor_id, session)  # Uses ETUCalcMethod

    # 4. Determine minimum time (from STD band minimum or 0.01s floor)
    min_time = get_min_std_time(sensor_id, is_clear, session)

    # 5. Generate curve points by sweeping current
    points = []
    I_start = pickup * c4 / pickup  # Starting normalized current
    I_end = max_amps / pickup
    I_step = 0.001  # Adaptive step — increases with spacing

    I = I_start
    while I < I_end or len(points) <= 2:
        amps = pickup * I

        if amps < pickup * c4:
            # Below minimum pickup — flat at max_amps
            points.append((max_amps, points[-1][1] if points else 0))
            break

        # Core IEEE equation
        T = (c1 / (I ** c2 - 1.0) + c3 + c6) * ltd_band_mult
        T_tol = (tol_pct + 1.0) * T
        T_offset = T + c4  # Fixed delay offset

        # Select appropriate time
        if is_clear:
            time = max(T_tol, T_offset)
        else:
            time = min(T_tol, T_offset)

        # Clamp to minimum time
        if min_time and time < min_time:
            # Interpolate crossover point, then go flat
            points.append((amps_at_crossover, min_time))
            points.append((max_amps, min_time))
            break

        points.append((amps, time))

        # Adaptive step: larger steps where curve is flatter
        I_step = get_eq_increment(points[-2:])  # Log-space adaptive
        I += I_step

    return points
```

### 3.6 Golden Test Data — STD Equations for Sensor 6258

First 5 ordinals (of 60 total):

| ordinal | label | in_out | fd_open_1 | fd_open_2 | fd_open_3 | fd_open_4 | fd_open_5 |
|---------|-------|--------|-----------|-----------|-----------|-----------|-----------|
| 1 | "0" | 0 (out) | 0.020000 | 2.000000 | 0.001000 | 1.000000 | 0.900000 |
| 2 | "0.1" | 2 (both) | 0.080000 | 2.000000 | 0.003200 | 1.000000 | 0.900000 |
| 3 | "0.2" | 2 (both) | 0.140000 | 2.000000 | 0.005600 | 1.000000 | 0.900000 |
| 4 | "0.3" | 2 (both) | 0.230000 | 2.000000 | 0.009200 | 1.000000 | 0.900000 |
| 5 | "0.4" | 2 (both) | 0.350000 | 2.000000 | 0.014000 | 1.000000 | 0.900000 |

Note: `in_out=0` means "out only" (open curve only), `in_out=2` means generate both open and clear.

---

## 4. Service B4: etu_ltd.py — 5 LTD Methods (FULLY DECODED)

The `CalcEquationLTDB` dispatcher (line 16-27 of C# source) switches on `ltd_function`:

```python
def calc_ltd_curve(ltd_function, sensor_data, is_clear, max_amps, ltd_band_mult):
    match ltd_function:
        case 1: return calc_thermal(sensor_data, is_clear, max_amps, ltd_band_mult)
        case 2: return calc_ieee(sensor_data, is_clear, max_amps, ltd_band_mult)  # → etu_curves.py
        case 3: return calc_ge_smr(sensor_data, is_clear, max_amps)
        case 4: return calc_thermal_tu(sensor_data, is_clear, max_amps, ltd_band_mult)
        case 5: return calc_thermal_tuf(sensor_data, is_clear, max_amps, ltd_band_mult)
        case _: return []
```

### 4.1 Method 1: Thermal (CalcThermEq2) — Lines 315-411

**Core equation (per-point):**
```python
# Coefficients from tcc_etu_ltd_params
# Open: Ipu=offset[42], K=offset[43], n=offset[44], Ithresh=offset[45]
# Clear: Ipu=offset[47], K=offset[48], n=offset[49], Ithresh=offset[50]

# Reference ratio
ref_ratio = ln(1 / (1 - (rating * Ipu / (pickup * Ithresh))^n))

# For each current I (normalized = I / pickup):
time = K * ltd_band_mult * ln(1 / (1 - (rating * Ipu / (pickup * I_norm))^n)) / ref_ratio
```

**Min time logic:** If `ltd_function == 1`, use `GetMinClearSTDB()` or `GetMinOpenSTDB()` from the STD band data; otherwise use the fixed minimum from offset [46]/[51].

**Starting current:** `I_start = Ipu × 1.001 × rating / pickup`

**Adaptive stepping:** Same `GetEqIncrement` used across all methods (log-space adaptive).

### 4.2 Method 2: IEEE (CalcIeeeEq2) — See Section 3

### 4.3 Method 3: GE-SMR (CalcGESMREq2) — Lines 35-150

**Core equation:**
```python
I_rated = rating * 1.12  # 112% of rated current

if is_clear:
    I_eff = (1 - ((I - I_rated/0.9) * 0.1 / (max_amps * 15.6 - I_rated/0.9) + 0.1)) * I
else:
    I_eff = I * 1.2

time = -102.4 * ln(1 - (I_rated^2 - 1) / I_eff^2)
```

**Starting current:** `I_start = (num2 + 1) × rating / pickup` where `num2` = clear offset [32] or open offset [31].

**No ltd_band_mult:** GE-SMR does not use the LTD band multiplier.

### 4.4 Method 4: Thermal-TU (CalcThermTU2) — Lines 531-662

**Core equation:**
```python
alpha = offset[38] (clear) or offset[37] (open)  # Pre-load factor
I_nom = rating * Ipu / (1 - alpha)  # Nominal current

# Starting point: I_start = I_nom, T = 1,000,000 (off-chart)
# For each current I_norm (starting at I_nom * 1.001):
time = ln(1 - (rating * Ipu)^n / (I * (1-alpha))^n) * (-K) * ltd_band_mult + TU_offset
```

**TU offset:** Clear uses offset [68] (if not sentinel 3.12345e38, else 0). Open always 0.

**Key difference from Thermal:** Uses `(1 - alpha)` denominator and adds a fixed TU_offset for clearing curves.

**Segment transition:** After the main curve, adds a flat segment at `I = rating × STPU_pickup` and extends to max_amps.

### 4.5 Method 5: Thermal-TUF (CalcThermTUF2) — Lines 670-782

**Core equation (simplified TU):**
```python
time = (rating / (I * (1-alpha)))^n * K * ltd_band_mult + TU_offset
```

**Fixed step:** Uses 0.1 instead of adaptive stepping.

**Starting current:** `(offset[31/32] + 1) × rating / pickup`

**Same TU offset logic** as Method 4.

### 4.6 Shared Utilities Needed

```python
def get_eq_increment(prev_points):
    """Adaptive log-space step size between curve points."""
    # Increase step when points are close together (flat curve)
    # Decrease step when points are far apart (steep curve)
    pass

def get_calc_method_value_ltdb(sensor_id, session):
    """Get the base current for LTD normalization using ETUCalcMethod."""
    # Depends on etu_pickup.py — returns the LTPU pickup current
    pass

def get_min_open_stdb(sensor_id, session):
    """Get minimum open time from STD band data."""
    pass

def get_min_clear_stdb(sensor_id, session):
    """Get minimum clear time from STD band data."""
    pass
```

### 4.7 Supabase Tables for LTD

| Table | Used By | Key Columns |
|-------|---------|-------------|
| `tcc_etu_ltd_params` | Methods 1, 4, 5 | `sensor_id`, coefficients |
| `tcc_etu_ltd_bands` | All methods | `sensor_id`, `ordinal`, band multipliers |
| `tcc_etu_std_equations` | Method 2 | `sensor_id`, `ordinal`, 6 coefficients × open/clear |
| `tcc_etu_sensor_params` | Methods 4, 5 | `sensor_id`, alpha, TU offset |

---

## 5. Service B5: tmt_curves.py (FULLY DECODED)

Source: `CTccLVBreakerCurveTMT.cs` (551KB, 5500+ lines). Analyzed key methods.

### 5.1 Core Algorithm

From the C# source (lines 100-118), the TMT curve generation logic is:

```python
def generate_tmt_curve(frame_id, trip_class, session):
    """
    Generate a TCC curve for a TMT (Thermal-Magnetic Trip) breaker.

    1. Load raw data points from tcc_tmt_curves
    2. If < 4 points: return them directly (no interpolation)
    3. If >= 4 points: apply Catmull-Rom spline interpolation
    """
    # Load raw data points sorted by current
    raw_points = session.query(TMTCurve).filter_by(
        frame_id=frame_id, trip_class=trip_class  # column is 'class'
    ).order_by(TMTCurve.current_amp).all()

    points = [(float(p.current_amp), float(p.time_sec)) for p in raw_points]

    if len(points) < 4:
        return points  # Direct copy, no interpolation

    # Apply Catmull-Rom spline interpolation
    return catmull_rom_spline(points, num_output_points=len(points))
```

### 5.2 Catmull-Rom Spline Implementation

The `CSplines::CatmullRom` function is called throughout the C# code. It's the standard Catmull-Rom centripetal spline. Use scipy or implement directly:

```python
import numpy as np

def catmull_rom_spline(points, num_output_points=None, alpha=0.5):
    """
    Catmull-Rom spline interpolation through control points.

    Args:
        points: list of (x, y) tuples — the control points
        num_output_points: desired output count (default: 10× input for smooth curve)
        alpha: 0=uniform, 0.5=centripetal (default), 1.0=chordal

    Returns:
        list of (x, y) interpolated points
    """
    if num_output_points is None:
        num_output_points = len(points) * 10

    pts = np.array(points, dtype=np.float64)
    n = len(pts)

    # Pad with phantom points at start and end
    p0 = 2 * pts[0] - pts[1]
    pn = 2 * pts[-1] - pts[-2]
    pts = np.vstack([p0, pts, pn])

    result = []
    segments = len(pts) - 3

    for i in range(segments):
        p0, p1, p2, p3 = pts[i], pts[i+1], pts[i+2], pts[i+3]

        # Number of points for this segment (proportional)
        seg_points = max(2, num_output_points // segments)

        for t in np.linspace(0, 1, seg_points, endpoint=(i == segments - 1)):
            # Catmull-Rom basis matrix
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2*p1[0]) + (-p0[0]+p2[0])*t +
                        (2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2 +
                        (-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            y = 0.5 * ((2*p1[1]) + (-p0[1]+p2[1])*t +
                        (2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2 +
                        (-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            result.append((x, y))

    return result
```

### 5.3 Fillet (CSplines::Fillet)

Used at segment transitions (e.g., where LTD meets STD). Creates a smooth rounded corner between two line segments.

```python
def fillet(p_before, p_corner, p_after, radius, num_points=25, reverse=False):
    """
    Create a fillet (rounded corner) between two line segments meeting at p_corner.

    Args:
        p_before: point before the corner
        p_corner: the corner point
        p_after: point after the corner
        radius: fillet radius (0.09 is the standard value in C# source)
        num_points: interpolation points (25 is standard in C# source)
        reverse: if True, generate points in reverse order

    Returns:
        list of (x, y) points forming the fillet arc
    """
    # Standard fillet via Catmull-Rom through 3 control points with radius offset
    pass  # Standard geometry — compute tangent points, then spline
```

The fillet radius is **0.09** for INST transitions and uses the STD band's delay time for LTD-STD transitions.

### 5.4 TMT Table Schema

```
tcc_tmt_curves: id, frame_id, class (trip class), time_sec (NUMERIC), current_amp (NUMERIC)
tcc_tmt_frames: id, breaker_style_id, breaker_class, frame (VARCHAR), size (NUMERIC)
tcc_tmt_amps: id, frame_id, amp_rating
tcc_tmt_settings: id, frame_id, setting (trip class setting)
```

### 5.5 Sample Data (frame_id=1, class=0)

| current_amp | time_sec |
|------------|----------|
| 1.09 | 9,779.63 |
| 1.08 | 963.54 |
| 1.09 | 118.63 |
| 1.13 | 52.02 |
| 1.36 | 21.81 |

These are the raw control points — the Catmull-Rom spline produces a smooth curve through them.

### 5.6 Alternative: Use scipy

```python
from scipy.interpolate import CubicSpline
# Or: from scipy.interpolate import make_interp_spline (k=3 for cubic)
```

scipy's CubicSpline with `bc_type='natural'` gives equivalent results for most curves. Consider this if numpy-only is preferred over manual Catmull-Rom.

---

## 6. Service B6: etu_merge.py (FULLY DECODED)

Source: `CPointsMergeSST.cs` (132KB, 3400 lines). Analyzed MergeSST orchestrator + MergeLines core.

### 6.1 Merge Dispatch Logic (MergeSST, lines 1438-1549)

The orchestrator checks which protection elements are present and dispatches to the appropriate merge variant:

```python
def merge_sst_curves(ltpu, stpu, inst, ovrd, ltd_curve, std_curve, inst_curve, ovrd_curve,
                     fillet_inst=0.09, fillet_ovrd=0.09, is_clearing=False, max_amps=100000):
    """
    Merge protection element curves into a single TCC curve.

    Args:
        ltpu, stpu, inst, ovrd: pickup values (0 or sentinel = element not present)
        ltd_curve, std_curve, inst_curve, ovrd_curve: [(amps, time)] curve data
        fillet_inst: fillet radius for INST transition (default 0.09)
        is_clearing: True for clearing curve, False for opening curve

    Returns:
        list of (amps, time) — the merged TCC curve
    """
    has_stpu = stpu not in (0, SENTINEL, None)
    has_inst = inst not in (0, SENTINEL, None)
    has_ovrd = ovrd not in (0, SENTINEL, None)

    # Dispatch based on which elements are present:
    if not has_stpu:
        if not has_inst:
            if has_ovrd:
                return merge_lt_ovr(...)
            else:
                return merge_lt_only(...)
        else:
            return merge_lt_inst(...)
    elif not has_inst:
        return merge_lt_st(...)
    else:
        return merge_lt_st_inst(...)  # Most common case

    # If is_clearing: reverse the output point order
```

### 6.2 Merge Variants

| Variant | Elements | C# Method |
|---------|----------|-----------|
| LT only | LTD | `MergeSST_LT` |
| LT + INST | LTD + INST | `MergeSST_LT_INST` |
| LT + OVR | LTD + Override | `MergeSST_LT_OVR` |
| LT + ST | LTD + STD | `MergeSST_LT_ST` + delay priority sub-variants |
| LT + ST + INST | LTD + STD + INST | `MergeSST_LT_ST_INST` + delay priority sub-variants |
| ST + OVR | STD + Override | `MergeSST_ST_OVR` |

### 6.3 Delay Priority (for LT+ST and LT+ST+INST merges)

When both LTD and STD curves exist, their overlap region needs a priority rule:

| Priority | Meaning | C# Method Suffix |
|----------|---------|-------------------|
| None | Use whichever is lower (faster trip) | `_DelayPriorityNone` |
| LT | LTD takes priority in overlap | `_DelayPriorityLT` |
| ST | STD takes priority in overlap | `_DelayPriorityST` |
| Min | Use minimum of both | `_DelayPriorityMin` |

Default is `None` (fastest trip wins).

### 6.4 MergeLines Core Algorithm (lines 1173-1431)

The core `MergeLines` function finds the intersection of two curve segments in log-log space:

```python
def merge_lines(curve1, curve2, max_amps, delay_priority=False):
    """
    Find where curve1 and curve2 intersect, then splice them.

    Algorithm:
    1. Walk curve1 segments and curve2 segments
    2. For each pair of segments, compute log-log intersection
    3. If intersection found within both segment bounds:
       - Truncate curve1 at intersection
       - Start curve2 from intersection
    4. If no intersection: curve1 ends before curve2 starts (gap)

    Returns:
        (truncated_curve1, splice_position_in_curve2)
    """
    for i in range(1, len(curve1)):
        seg1 = (curve1[i-1], curve1[i])

        for j in range(1, len(curve2)):
            seg2 = (curve2[j-1], curve2[j])

            # Skip if segments don't overlap in x (current) range
            if seg1[1][0] < seg2[0][0]:
                continue

            # Log-log intersection
            intersection = log_log_intersect(seg1, seg2)

            if intersection and point_in_bounds(intersection, seg1, seg2, tolerance=0.01):
                # Splice: curve1[:i] + [intersection] + curve2[j:]
                return splice_at(curve1, i, curve2, j, intersection)

    return None  # No intersection found
```

### 6.5 Log-Log Intersection

All curve operations happen in **log-log space** (both current and time are log-scaled):

```python
import math

def log_log_intersect(seg1, seg2):
    """
    Find intersection of two line segments in log-log space.

    seg1 = ((x1, y1), (x2, y2))
    seg2 = ((x3, y3), (x4, y4))
    """
    # Convert to log space
    lx1, ly1 = math.log10(seg1[0][0]), math.log10(seg1[0][1])
    lx2, ly2 = math.log10(seg1[1][0]), math.log10(seg1[1][1])
    lx3, ly3 = math.log10(seg2[0][0]), math.log10(seg2[0][1])
    lx4, ly4 = math.log10(seg2[1][0]), math.log10(seg2[1][1])

    # Standard 2D line intersection
    denom = (lx1-lx2)*(ly3-ly4) - (ly1-ly2)*(lx3-lx4)
    if abs(denom) < 1e-12:
        return None  # Parallel

    t = ((lx1-lx3)*(ly3-ly4) - (ly1-ly3)*(lx3-lx4)) / denom

    lx = lx1 + t * (lx2 - lx1)
    ly = ly1 + t * (ly2 - ly1)

    return (10**lx, 10**ly)
```

### 6.6 Fillet at Transitions

After merging, fillets are applied at each transition point (where one curve hands off to the next):

```python
# Standard fillet parameters from C# source:
FILLET_INST = 0.09      # Radius for INST transitions
FILLET_POINTS = 25      # Number of interpolation points per fillet
# FILLET_STD uses the STD band's delay time value
```

### 6.7 Implementation Priority

Build merge in this order:
1. `merge_lt_st_inst()` — covers most real-world breakers
2. `merge_lines()` — the core intersection algorithm
3. `log_log_intersect()` — helper
4. Fillet — can be added as polish (curves work without it, just with sharp corners)

---

## 7. FastAPI Endpoint Contracts (for service B7)

```python
# POST /api/v1/calculate/etu-pickup
{
    "sensor_id": 6258,
    "plug_id": 7389,           # Optional — from tcc_etu_plugs
    "ltpu_setting": 0.8,
    "stpu_setting": 4.0,       # Optional
    "inst_setting": 10.0,      # Optional
    "gfpu_setting": null        # Optional
}
# Response:
{
    "sensor_id": 6258,
    "rating": 600,
    "elements": {
        "LTPU": {"test_current": 480.0, "min_limit": 504.0, "max_limit": 576.0, "method": 1},
        "STPU": {"test_current": 1920.0, "min_limit": 1728.0, "max_limit": 2112.0, "method": 4},
        "INST": {"test_current": 6000.0, "min_limit": 5400.0, "max_limit": 6600.0, "method": 1},
        "GFPU": null
    }
}

# POST /api/v1/calculate/etu-curve
{
    "sensor_id": 6258,
    "plug_id": 7389,
    "ltpu_setting": 0.8,
    "stpu_setting": 4.0,
    "std_ordinal": 5,          # STD band dial position
    "inst_setting": 10.0,
    "max_amps": 100000.0
}
# Response:
{
    "sensor_id": 6258,
    "curves": {
        "ltd_open": [[480, 100.5], [600, 50.2], ...],
        "ltd_clear": [[480, 120.3], [600, 60.1], ...],
        "std_open": [...],
        "std_clear": [...],
        "inst_open": [...],
        "inst_clear": [...]
    }
}

# POST /api/v1/calculate/tmt-curve
{
    "frame_id": 1,
    "trip_class": 0,
    "amp_rating": 100
}
# Response:
{
    "frame_id": 1,
    "trip_class": 0,
    "curve": [[1.09, 9779.63], [1.08, 963.54], ...]
}
```

---

## 8. Dependencies & Setup

```bash
# From C:/APEX Platform/apex-power-ops-platform/
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv numpy
```

- **numpy** needed for spline interpolation (TMT curves) and efficient array math
- All services should import `config.get_db` for database sessions
- All services should use SQLAlchemy models from `models/` — do NOT write raw SQL

---

## 9. Build Order for VS Code Claude

1. **NOW:** `etu_pickup.py` — fully specified above, no blockers
2. **NOW:** `etu_curves.py` — IEEE equation fully decoded, STD equation table mapped
3. **WAIT:** `etu_ltd.py` — Cowork delivering remaining 4 method specs
4. **WAIT:** `tmt_curves.py` — Cowork delivering Catmull-Rom spec
5. **WAIT:** `etu_merge.py` — Cowork delivering merge algorithm spec
6. **AFTER 1-5:** FastAPI endpoint wiring
