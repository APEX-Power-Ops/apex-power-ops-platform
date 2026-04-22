# NETA ATS-2021 Test Plan Service — Implementation Specification

**Purpose:** Historical VS Code Claude handoff document for the proposed `services/calc_engine/neta_test_plan.py` surface
**Author:** Cowork Claude (data audit + NETA test matrix analysis)
**Date:** 2026-03-20
**Status:** 📋 SPEC COMPLETE — ready for implementation
**Depends on:** B2 (etu_pickup), B3 (etu_curves), B4 (etu_ltd), B7 (router)

**Authority note:** This is a lineage implementation spec for one proposed service surface. It must not be used to classify overall backend maturity or redefine governed TCC architecture outside the current platform authority stack and the paired source-domain schema and DLL authority documents.

---

## 1. Overview

This service generates a complete NETA ATS-2021 test plan for a given circuit breaker trip unit. A technician selects a sensor + 7 dial settings, and the service produces up to 7 test points — each with a test type, test current, expected value, and pass/fail tolerance band.

The service is the bridge between the calc engine (which computes raw values) and the field validation tool (which records and judges measurements).

---

## 2. The 7 NETA Test Elements

| # | Element | Test Type | What the Technician Does | Expected Result |
|---|---------|-----------|--------------------------|-----------------|
| 1 | LTPU    | PICKUP    | Ramp current slowly until trip | Trip at pickup current ± tolerance |
| 2 | LTD     | TIMING    | Inject 300% of LTPU pickup, measure trip time | Trip time matches curve ± tolerance |
| 3 | STPU    | PICKUP    | Ramp current until trip | Trip at pickup current ± tolerance |
| 4 | STD     | TIMING    | Inject fixed multiple of STPU, measure time | Trip time matches delay ± tolerance |
| 5 | INST    | PICKUP    | Ramp current until instantaneous trip | Trip at INST current ± tolerance |
| 6 | GFPU    | PICKUP    | Inject ground fault current until trip | Trip at GFPU current ± tolerance |
| 7 | GFD     | TIMING    | Inject fixed GF current, measure time | Trip time matches delay ± tolerance |

Not all sensors have all 7 elements. The service checks `has_ltpu`, `has_stpu`, `has_inst`, `has_gfpu` flags and only generates test points for present elements. LTD/STD/GFD availability depends on whether the sensor has corresponding band/param rows.

---

## 3. Data Model

### 3.1 Input: `TestPlanRequest`

```python
from pydantic import BaseModel, Field
from typing import Optional

class TestPlanRequest(BaseModel):
    """Everything needed to generate a NETA test plan."""
    sensor_id: int
    plug_id: Optional[int] = None

    # Pickup settings (dial values, not amps)
    ltpu_setting: Optional[float] = None
    stpu_setting: Optional[float] = None
    inst_setting: Optional[float] = None
    gfpu_setting: Optional[float] = None

    # Band/curve selections
    ltd_band_ordinal: int = 1          # Which LTD time band
    std_band_ordinal: int = 1          # Which STD delay band
    gfd_band_ordinal: int = 1          # Which GFD delay band

    # LTD timing test parameters
    ltd_test_multiple: float = 3.0     # Test at 300% of LTPU pickup (NETA default)

    # Project metadata (passed through to tcc_test_plans)
    name: Optional[str] = None
    project: Optional[str] = None
    equipment_tag: Optional[str] = None
    location: Optional[str] = None
```

### 3.2 Output: `NetaTestPoint` and `NetaTestPlan`

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class TestElement(str, Enum):
    LTPU = "LTPU"
    LTD  = "LTD"
    STPU = "STPU"
    STD  = "STD"
    INST = "INST"
    GFPU = "GFPU"
    GFD  = "GFD"

class TestType(str, Enum):
    PICKUP = "PICKUP"
    TIMING = "TIMING"

@dataclass
class NetaTestPoint:
    """One row in the test plan — one thing the technician measures."""
    element: TestElement
    test_type: TestType
    test_current_amps: float          # The current to inject
    expected_value: float             # Pickup amps (PICKUP) or trip time seconds (TIMING)
    min_acceptable: float             # Low end of tolerance band
    max_acceptable: float             # High end of tolerance band
    tolerance_pct_low: float          # e.g. -10.0 (percent)
    tolerance_pct_high: float         # e.g. +10.0 (percent)
    unit: str                         # "A" for amps, "s" for seconds
    notes: str = ""                   # e.g. "300% of LTPU" or "Band 2 delay"

    # For TIMING tests: the curve/band info used
    band_label: Optional[str] = None
    ltd_method: Optional[int] = None  # 1=Thermal, 2=IEEE, 4=TU, 5=TUF

@dataclass
class NetaTestPlan:
    """Complete test plan for one breaker trip unit."""
    sensor_id: int
    rating: int
    description: str                  # Sensor description from catalog
    test_points: list[NetaTestPoint]  # Up to 7 test points

    # Settings echo (so the plan is self-documenting)
    ltpu_setting: Optional[float] = None
    stpu_setting: Optional[float] = None
    inst_setting: Optional[float] = None
    gfpu_setting: Optional[float] = None
    ltd_band_ordinal: Optional[int] = None
    std_band_ordinal: Optional[int] = None
    gfd_band_ordinal: Optional[int] = None
```

---

## 4. Tolerance Sources — Complete Map

### 4.1 PICKUP Tests (elements 1, 3, 5, 6)

Tolerance is a **percentage of the expected pickup current**, stored per-sensor.

| Element | Tolerance Source | Columns |
|---------|-----------------|---------|
| LTPU    | `tcc_etu_sensors` | `ltpu_tol_hi`, `ltpu_tol_lo` |
| STPU    | `tcc_etu_sensors` | `stpu_tol_hi`, `stpu_tol_lo` |
| INST    | `tcc_etu_sensors` | `inst_tol_hi`, `inst_tol_lo` |
| GFPU    | `tcc_etu_sensors` | `gfpu_tol_hi`, `gfpu_tol_lo` ← **added 2026-03-20** |

**Tolerance application:**
```python
expected = pickup_current_amps   # from ETUPickupCalculator
min_acceptable = expected * (1 + tol_lo / 100)   # tol_lo is negative, e.g. -10
max_acceptable = expected * (1 + tol_hi / 100)   # tol_hi is positive, e.g. +10
```

**Important:** Some sensors have asymmetric tolerances (e.g. LTPU: +20%/-5%, not ±10%). The data contains 20+ distinct tolerance pairs. Always use the per-sensor values, never assume ±10%.

### 4.2 TIMING Tests (elements 2, 4, 7)

Tolerance is a **percentage of the expected trip/delay time**.

| Element | Expected Value Source | Tolerance Source |
|---------|---------------------|-----------------|
| LTD     | Calc engine `ETULTDCalculator.calculate()` at test current | `tcc_etu_ltd_params.tol_hi`, `tol_lo` |
| STD     | `tcc_etu_std_bands.open_time` / `clear_time` for selected band | **Service-level default: ±10%** (no DB column) |
| GFD     | `tcc_etu_gfd_bands.open_time` / `clear_time` for selected band | **Service-level default: ±10%** (no DB column) |

**LTD tolerance application:**
```python
# LTD has per-param tolerances
expected_time = ltd_calc.calculate(test_current, band_ordinal, is_clear=True)
tol_hi = ltd_param.tol_hi   # from tcc_etu_ltd_params
tol_lo = ltd_param.tol_lo
min_time = expected_time * (1 + tol_lo / 100)
max_time = expected_time * (1 + tol_hi / 100)
```

**STD/GFD tolerance application:**
```python
# STD and GFD use fixed delay bands — tolerance is applied to the delay value
TIMING_TOL_PCT = 10.0  # NETA ATS-2021 default for delay-based elements
expected_time = std_band.clear_time   # or gfd_band.clear_time
min_time = expected_time * (1 - TIMING_TOL_PCT / 100)
max_time = expected_time * (1 + TIMING_TOL_PCT / 100)
```

---

## 5. Algorithm — `generate_test_plan()`

```
Input: TestPlanRequest
Output: NetaTestPlan

1. Load sensor from tcc_etu_sensors (via ETUPickupCalculator)
   → Get rating, description, calc methods, tolerances

2. Calculate all pickup currents (reuse ETUPickupCalculator.calculate())
   → ltpu_amps, stpu_amps, inst_amps, gfpu_amps

3. For each of the 7 elements, IF the element is present:

   LTPU (PICKUP):
     test_current = ltpu_amps (this IS the expected value)
     expected = ltpu_amps
     tolerance = sensor.ltpu_tol_hi / ltpu_tol_lo
     → append NetaTestPoint

   LTD (TIMING):
     test_current = ltpu_amps × ltd_test_multiple (default 3.0)
     Load LTD param for this sensor (tcc_etu_ltd_params)
     expected = ETULTDCalculator.calculate(test_current, band_ordinal, is_clear=True)
     tolerance = ltd_param.tol_hi / tol_lo
     → append NetaTestPoint

   STPU (PICKUP):
     test_current = stpu_amps
     expected = stpu_amps
     tolerance = sensor.stpu_tol_hi / stpu_tol_lo
     → append NetaTestPoint

   STD (TIMING):
     Load STD band for this sensor (tcc_etu_std_bands, ordinal = std_band_ordinal)
     test_current = stpu_amps × 1.5 (or use band's associated current if available)
     expected = std_band.clear_time
     tolerance = ±10% (service default)
     → append NetaTestPoint

   INST (PICKUP):
     test_current = inst_amps
     expected = inst_amps
     tolerance = sensor.inst_tol_hi / inst_tol_lo
     → append NetaTestPoint

   GFPU (PICKUP):
     test_current = gfpu_amps
     expected = gfpu_amps
     tolerance = sensor.gfpu_tol_hi / gfpu_tol_lo
     → append NetaTestPoint

   GFD (TIMING):
     Load GFD band (tcc_etu_gfd_bands, ordinal = gfd_band_ordinal)
     test_current = gfpu_amps × 1.5
     expected = gfd_band.clear_time
     tolerance = ±10% (service default)
     → append NetaTestPoint

4. Return NetaTestPlan with all test points
```

---

## 6. Validation — `validate_results()`

After the technician records measurements, this function judges each test point.

```python
def validate_results(
    plan: NetaTestPlan,
    measurements: dict[str, float]   # element name → measured value
) -> list[TestResult]:
    """
    Compare measured values against the test plan tolerance bands.

    Returns one TestResult per element with pass/fail status.
    """
    results = []
    for tp in plan.test_points:
        measured = measurements.get(tp.element.value)
        if measured is None:
            continue
        passed = tp.min_acceptable <= measured <= tp.max_acceptable
        results.append(TestResult(
            element=tp.element,
            test_type=tp.test_type,
            expected=tp.expected_value,
            actual=measured,
            min_accept=tp.min_acceptable,
            max_accept=tp.max_acceptable,
            passed=passed,
        ))
    return results
```

---

## 7. DB Queries Required

The service needs these queries (all can go through SQLAlchemy or Supabase PostgREST):

| Query | Table | Purpose |
|-------|-------|---------|
| Sensor lookup | `tcc_etu_sensors` | Get calc methods + tolerances for all 4 pickup elements |
| Pickup calculation | Reuse `ETUPickupCalculator` | Get ltpu/stpu/inst/gfpu amps |
| LTD params | `tcc_etu_ltd_params` | Get method, coefficients, tol_hi, tol_lo |
| LTD calculation | Reuse `ETULTDCalculator` | Compute trip time at test current |
| STD bands | `tcc_etu_std_bands` | Get delay time for selected band |
| GFD bands | `tcc_etu_gfd_bands` | Get delay time for selected band |
| LTPU pickups | `tcc_etu_ltpu_pickups` | Available settings (for dropdown) |
| STPU pickups | `tcc_etu_stpu_pickups` | Available settings (for dropdown) |
| INST pickups | `tcc_etu_inst_pickups` | Available settings (for dropdown) |
| GFPU pickups | `tcc_etu_gfpu_pickups` | Available settings (for dropdown) |
| LTD bands | `tcc_etu_ltd_bands` | Available band choices (for dropdown) |
| STD band list | `tcc_etu_std_bands` | Available band choices (for dropdown) |
| GFD band list | `tcc_etu_gfd_bands` | Available band choices (for dropdown) |

---

## 8. FastAPI Endpoints

Add to `router.py` (or a new `neta_router.py`):

### 8.1 Generate Test Plan

```
POST /api/v1/test-plan/generate
```

**Request:** `TestPlanRequest` (Section 3.1)

**Response:**
```json
{
  "sensor_id": 5817,
  "rating": 1600,
  "description": "LS SUSOL TS800 800AF 800AT S-ZONE LTD",
  "test_points": [
    {
      "element": "LTPU",
      "test_type": "PICKUP",
      "test_current_amps": 640.0,
      "expected_value": 640.0,
      "min_acceptable": 576.0,
      "max_acceptable": 704.0,
      "tolerance_pct_low": -10.0,
      "tolerance_pct_high": 10.0,
      "unit": "A",
      "notes": "LTPU pickup at setting 0.8"
    },
    {
      "element": "LTD",
      "test_type": "TIMING",
      "test_current_amps": 1920.0,
      "expected_value": 12.47,
      "min_acceptable": 11.22,
      "max_acceptable": 13.72,
      "tolerance_pct_low": -10.0,
      "tolerance_pct_high": 10.0,
      "unit": "s",
      "notes": "300% of LTPU, IEEE Ext Inv, Band 2",
      "band_label": "Band 2",
      "ltd_method": 2
    }
  ],
  "ltpu_setting": 0.8,
  "stpu_setting": null,
  "inst_setting": null,
  "gfpu_setting": null,
  "ltd_band_ordinal": 1,
  "std_band_ordinal": null,
  "gfd_band_ordinal": null
}
```

### 8.2 Validate Results

```
POST /api/v1/test-plan/validate
```

**Request:**
```json
{
  "sensor_id": 5817,
  "plan": { /* ... TestPlanRequest to regenerate, OR plan_id to load saved */ },
  "measurements": {
    "LTPU": 635.2,
    "LTD": 12.88,
    "STPU": null,
    "STD": null,
    "INST": 12850.0,
    "GFPU": null,
    "GFD": null
  }
}
```

**Response:**
```json
{
  "sensor_id": 5817,
  "results": [
    {
      "element": "LTPU",
      "test_type": "PICKUP",
      "expected": 640.0,
      "actual": 635.2,
      "min_accept": 576.0,
      "max_accept": 704.0,
      "passed": true
    },
    {
      "element": "LTD",
      "test_type": "TIMING",
      "expected": 12.47,
      "actual": 12.88,
      "min_accept": 11.22,
      "max_accept": 13.72,
      "passed": true
    }
  ],
  "overall_pass": true,
  "tested_count": 2,
  "passed_count": 2
}
```

### 8.3 Save Test Plan (writes to existing Supabase tables)

```
POST /api/v1/test-plan/save
```

Maps to existing tables:
- `tcc_test_plans` — header row with sensor_id, setting IDs, computed test amps / min / max seconds
- `tcc_test_results` — one row per element with expected/actual/min_accept/max_accept/passed

### 8.4 Sensor Options (for cascading dropdowns)

```
GET /api/v1/test-plan/sensor/{sensor_id}/options
```

Returns all available settings for the dropdowns:
```json
{
  "sensor_id": 5817,
  "rating": 1600,
  "description": "...",
  "ltpu_pickups": [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0],
  "ltd_bands": [{"ordinal": 1, "label": "Band 1"}, ...],
  "stpu_pickups": [2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0],
  "std_bands": [{"ordinal": 1, "label": "0.1s"}, ...],
  "inst_pickups": [2.0, 3.0, 4.0, 5.0, ...],
  "gfpu_pickups": [0.2, 0.3, 0.4, 0.5, ...],
  "gfd_bands": [{"ordinal": 1, "label": "0.1s"}, ...]
}
```

---

## 9. Supabase Table Mapping

The existing `tcc_test_plans` and `tcc_test_results` tables map to the service output as follows:

### `tcc_test_plans` columns → Service fields

| Column | Source |
|--------|--------|
| `id` | Auto-generated UUID |
| `user_id` | From Supabase auth (JWT) |
| `name` | `request.name` |
| `project` | `request.project` |
| `equipment_tag` | `request.equipment_tag` |
| `location` | `request.location` |
| `sensor_id` | `request.sensor_id` |
| `ltpu_pickup_id` | ID from `tcc_etu_ltpu_pickups` matching selected setting |
| `ltd_band_id` | ID from `tcc_etu_ltd_bands` matching selected ordinal |
| `stpu_pickup_id` | ID from `tcc_etu_stpu_pickups` matching selected setting |
| `std_band_id` | ID from `tcc_etu_std_bands` matching selected ordinal |
| `inst_pickup_id` | ID from `tcc_etu_inst_pickups` matching selected setting |
| `gfpu_pickup_id` | ID from `tcc_etu_gfpu_pickups` matching selected setting |
| `gfd_band_id` | ID from `tcc_etu_gfd_bands` matching selected ordinal |
| `ltpu_test_amps` | LTPU test point `test_current_amps` |
| `ltpu_min_sec` | LTPU test point `min_acceptable` |
| `ltpu_max_sec` | LTPU test point `max_acceptable` |
| `std_test_amps` | STD test point `test_current_amps` |
| `std_min_sec` | STD test point `min_acceptable` |
| `std_max_sec` | STD test point `max_acceptable` |
| `inst_test_amps` | INST test point `test_current_amps` |
| `inst_min_sec` | INST test point `min_acceptable` |
| `inst_max_sec` | INST test point `max_acceptable` |
| `gfpu_test_amps` | GFPU test point `test_current_amps` |
| `gfpu_min_sec` | GFPU test point `min_acceptable` |
| `gfpu_max_sec` | GFPU test point `max_acceptable` |

### `tcc_test_results` columns → Service fields

| Column | Source |
|--------|--------|
| `id` | Auto-generated UUID |
| `plan_id` | FK to `tcc_test_plans.id` |
| `test_type` | `test_point.test_type.value` ("PICKUP" or "TIMING") |
| `element` | `test_point.element.value` ("LTPU", "LTD", etc.) |
| `expected` | `test_point.expected_value` |
| `actual` | Technician's measured value |
| `min_accept` | `test_point.min_acceptable` |
| `max_accept` | `test_point.max_acceptable` |
| `passed` | `min_accept <= actual <= max_accept` |
| `tested_at` | Timestamp of measurement |
| `technician` | Technician name/ID |
| `notes` | Free text |

---

## 10. Implementation Checklist

- [ ] Create `services/calc_engine/neta_test_plan.py`
  - [ ] `TestElement` and `TestType` enums
  - [ ] `NetaTestPoint` and `NetaTestPlan` dataclasses
  - [ ] `NetaTestPlanGenerator` class
    - [ ] `__init__(db, sensor_id)` — loads sensor + tolerances
    - [ ] `generate(request) → NetaTestPlan`
    - [ ] `_make_pickup_point(element, pickup_result, tol_hi, tol_lo) → NetaTestPoint`
    - [ ] `_make_ltd_timing_point(ltpu_amps, band_ordinal, test_multiple) → NetaTestPoint`
    - [ ] `_make_delay_timing_point(element, delay_time, test_current) → NetaTestPoint`
  - [ ] `validate_results(plan, measurements) → list[TestResult]`
- [ ] Create `services/calc_engine/neta_router.py` (or extend router.py)
  - [ ] `POST /api/v1/test-plan/generate`
  - [ ] `POST /api/v1/test-plan/validate`
  - [ ] `POST /api/v1/test-plan/save`
  - [ ] `GET /api/v1/test-plan/sensor/{sensor_id}/options`
- [ ] Update `__init__.py` to export new classes
- [ ] Tests
  - [ ] Unit test: pickup tolerance bands for known sensor (asymmetric case)
  - [ ] Unit test: LTD timing tolerance with IEEE method
  - [ ] Unit test: STD/GFD default ±10% timing tolerance
  - [ ] Unit test: sensor with missing elements generates partial plan
  - [ ] Integration test: full 7-element test plan for a sensor with all elements
  - [ ] Integration test: validate_results with mix of pass/fail
  - [ ] Integration test: save round-trip (generate → save → load → compare)

---

## 11. Constants

```python
# NETA ATS-2021 defaults for timing tests without per-sensor tolerances
DEFAULT_TIMING_TOL_HI = 10.0    # +10%
DEFAULT_TIMING_TOL_LO = -10.0   # -10%

# Default test multiples
DEFAULT_LTD_TEST_MULTIPLE = 3.0  # Test LTD at 300% of LTPU pickup
DEFAULT_STD_TEST_MULTIPLE = 1.5  # Test STD at 150% of STPU pickup
DEFAULT_GFD_TEST_MULTIPLE = 1.5  # Test GFD at 150% of GFPU pickup
```
