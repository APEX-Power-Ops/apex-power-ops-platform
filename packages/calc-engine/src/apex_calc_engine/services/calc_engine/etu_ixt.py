"""Route-1 (I2X / Iˣt) short-time + ground delay kernel.

The native EasyPower renderer evaluates a route-1 STD/GFD delay band as a
**power law** — recovered 2026-06-03 (G4 §3b·I2X, STATE §113) and triangulated
across the decompile (`TccBase.dll` `CIxt.{ctor}`/`ComputeT` 24248-24297), the
staging source DB (`DatSection3STD` + `DatSensor.DS3_I2T_VAL`), and the managed
routing module (`etu_delay_routing.SSTDelayCalc.I2X`). It is **NOT** the
`CalcThermEq` polynomial (route 2); it is::

    t(M) = T_anchor * (I_anchor / M) ** X          (== K / M**X, K = I_anchor**X * T_anchor)

where ``(I_anchor, T_anchor)`` is the band's open/clear anchor point and ``X`` is
the per-sensor exponent (``DS3_I2T_VAL`` / ``DS1GF_I2T_VAL``, ``X = 2`` for ~98% of
the route-1 corpus, hence "I²t"; the family is "I2X" = Iˣt because X varies). This
is the SAME closed form already shipped + live-verified for the LTD reference
window (§111, ``_ltd_reference_delay_surface``: ``setting * (6/M)**2``), generalized
to read the band anchor + exponent instead of hardcoding ``(6, x=2)``.

The native ``CIxt`` semantics this module mirrors exactly (decomp 24248-24297):
  * ``CIxt.{ctor}(dI, dt, dx)`` stores ``x = Math.Abs(dx)`` and the constant
    ``K = pow(dI, x) * dt``.
  * ``CIxt.ComputeT(dI)`` returns ``K / pow(dI, x)``, EXCEPT it returns ``0.0`` when
    ``dI`` or ``pow(dI, x)`` or ``x`` is zero or the EasyPower "no-value" sentinel
    ``3.123456801690127e+38``. This module returns ``None`` for those unusable
    inputs (so callers WITHHOLD rather than emit a fall-through 0.0).

Per-band SHAPE (``DatSection3STD.I2X`` smallint):
  * ``0`` / ``NULL`` -> **flat** / definite-time band: time = the definite setting
    (``std_open`` / ``std_clear``), current-independent. Identical to the
    db-proven route-0 direct band (G4 §3b); the power law does not apply.
  * ``1`` -> **ramp**: a pure Iˣt ramp through ``(I_anchor, T_anchor)`` — the power
    law above. SUPPORTED here.
  * ``2`` -> **composite**: an Iˣt ramp clamped to a definite-time floor
    (``std_open``/``std_clear``). The ramp-vs-floor COMBINE RULE (provisional
    ``t = max(ramp, floor)`` definite-time minimum) is NOT yet confirmed against
    the native render; this module returns it UNSUPPORTED pending captured-fixture
    parity (G4 §3b·I2X residual).

THREADING NOTE (the units convention): ``I_anchor`` and the NETA ``test_multiple``
are both multiples of the element pickup, so the pickup cancels and ``M`` here is
the test multiple directly — the same convention the shipped LTD reference window
uses (anchor 6× pickup, test N× pickup). This module evaluates the math only; it
does not itself decide that convention.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# EasyPower's "no value" / uninitialised double marker (appears throughout the
# TccBase.dll decompile; CIxt.ComputeT treats it as a degenerate input).
EP_SENTINEL = 3.123456801690127e+38

# Per-band I2X shape codes (DatSection3STD.I2X).
SHAPE_FLAT = "flat"
SHAPE_RAMP = "ramp"
SHAPE_COMPOSITE = "composite"
SHAPE_UNKNOWN = "unknown"


def _usable(v: Optional[float]) -> bool:
    """A double is usable iff present, finite-ish, and not the EP sentinel."""
    return v is not None and v != EP_SENTINEL


def i2x_shape(i2x_flag: Optional[float]) -> str:
    """Map a ``DatSection3STD.I2X`` smallint to a band shape.

    ``0`` / ``NULL`` -> flat · ``1`` -> ramp · ``2`` -> composite · else unknown.
    Accepts float (prod column is ``Numeric``) or int; compares on the rounded int.
    """
    if i2x_flag is None:
        return SHAPE_FLAT
    try:
        code = int(round(float(i2x_flag)))
    except (TypeError, ValueError):
        return SHAPE_UNKNOWN
    if code == 0:
        return SHAPE_FLAT
    if code == 1:
        return SHAPE_RAMP
    if code == 2:
        return SHAPE_COMPOSITE
    return SHAPE_UNKNOWN


def ixt_time(
    test_multiple: Optional[float],
    i_anchor: Optional[float],
    t_anchor: Optional[float],
    x: Optional[float],
) -> Optional[float]:
    """Native ``CIxt.ComputeT`` power law: ``t = t_anchor * (i_anchor / M) ** |x|``.

    Returns ``None`` for any unusable input (None / EP sentinel / a zero that would
    make the power law degenerate), mirroring the native ``0.0`` guard so callers
    withhold rather than emit a meaningless value.
    """
    if not (_usable(test_multiple) and _usable(i_anchor) and _usable(t_anchor) and _usable(x)):
        return None
    x_eff = abs(float(x))  # CIxt ctor uses Math.Abs(dx)
    m = float(test_multiple)
    if x_eff == 0.0 or m == 0.0 or i_anchor == 0.0:
        return None
    k = (float(i_anchor) ** x_eff) * float(t_anchor)  # CIxt ctor [1]
    denom = m ** x_eff  # CIxt ComputeT num2
    if denom == 0.0:
        return None
    return k / denom


@dataclass(frozen=True)
class IxtDelaySurface:
    """One element's route-1 delay surface at a NETA test multiple.

    ``supported`` is False for composite / unknown / degenerate bands — callers
    must WITHHOLD the time (G4 §6 field-trust gate) when not supported.
    """

    expected_time: Optional[float]
    time_low: Optional[float]
    time_high: Optional[float]
    shape: str
    supported: bool
    reason: str


def i2x_delay_surface(
    *,
    test_multiple: Optional[float],
    i2x_flag: Optional[float],
    i_open: Optional[float] = None,
    t_open: Optional[float] = None,
    i_clear: Optional[float] = None,
    t_clear: Optional[float] = None,
    std_open: Optional[float] = None,
    std_clear: Optional[float] = None,
    exp_x: Optional[float] = None,
) -> IxtDelaySurface:
    """Resolve the route-1 (I2X) delay surface for one element + test multiple.

    Shippable subset (G4 §3b·I2X): ``flat`` (definite-time, current-independent)
    and ``ramp`` (the Iˣt power law). ``composite`` and ``unknown`` are returned
    UNSUPPORTED for the caller to withhold.
    """
    shape = i2x_shape(i2x_flag)

    if shape == SHAPE_FLAT:
        # Current-independent definite time — identical to the db-proven route-0
        # direct band. The power law / exponent do not apply.
        open_t = float(std_open) if _usable(std_open) else None
        clear_t = float(std_clear) if _usable(std_clear) else None
        if open_t is None and clear_t is None:
            return IxtDelaySurface(None, None, None, shape, False,
                                   "I2X=flat band carries no definite-time setting.")
        lo, hi = _lo_hi(open_t, clear_t)
        return IxtDelaySurface(open_t, lo, hi, shape, True,
                               "I2X flat (definite-time) band — current-independent (G4 §3b·I2X).")

    if shape == SHAPE_RAMP:
        open_t = ixt_time(test_multiple, i_open, t_open, exp_x)
        clear_t = ixt_time(test_multiple, i_clear, t_clear, exp_x)
        if open_t is None and clear_t is None:
            return IxtDelaySurface(None, None, None, shape, False,
                                   "I2X ramp band has no usable anchor/exponent.")
        lo, hi = _lo_hi(open_t, clear_t)
        return IxtDelaySurface(open_t, lo, hi, shape, True,
                               "I2X Iˣt ramp — t = T_anchor·(I_anchor/M)^X (G4 §3b·I2X).")

    if shape == SHAPE_COMPOSITE:
        # Composite (I2X=2): the Iˣt ramp clamped below at the band's definite-time
        # floor. Combine rule t(M) = max(ramp(M), floor) — RECOVERED + decompile-
        # confirmed (G4 §3b·I2X / STATE §116): the native renderers apply the floor as
        # a minimum-time clamp on the curve (the explicit max(rTmin, dMinTime) lambda in
        # CalcThermEq2, the universal *prMin clamp across CalcIeeeEq2/CalcGESMREq2). The
        # ramp is native-bit-exact (I2X-4); the floor is the stored std_open/std_clear.
        ramp_open = ixt_time(test_multiple, i_open, t_open, exp_x)
        ramp_clear = ixt_time(test_multiple, i_clear, t_clear, exp_x)
        floor_open = float(std_open) if _usable(std_open) else None
        floor_clear = float(std_clear) if _usable(std_clear) else None
        open_t = _max_opt(ramp_open, floor_open)
        clear_t = _max_opt(ramp_clear, floor_clear)
        if open_t is None and clear_t is None:
            return IxtDelaySurface(None, None, None, shape, False,
                                   "I2X composite band has no usable ramp anchor or floor.")
        lo, hi = _lo_hi(open_t, clear_t)
        return IxtDelaySurface(open_t, lo, hi, shape, True,
                               "I2X composite — max(Iˣt ramp, definite-time floor) (G4 §3b·I2X).")

    return IxtDelaySurface(None, None, None, shape, False,
                           f"I2X shape {i2x_flag!r} unrecognised — withheld.")


def _lo_hi(a: Optional[float], b: Optional[float]) -> tuple[Optional[float], Optional[float]]:
    if a is not None and b is not None:
        return (min(a, b), max(a, b))
    return (a, b)


def _max_opt(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """max() that ignores None (the composite ramp-vs-floor clamp)."""
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)
