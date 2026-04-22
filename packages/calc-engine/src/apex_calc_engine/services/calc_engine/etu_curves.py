"""
IEEE Inverse-Time Equation Solver
==================================
Evaluates the 6-coefficient IEEE inverse-time equation used by
STD (Short-Time Delay) and GFD (Ground Fault Delay) curves.

Core equation:
    T = (C1 / (I^C2 - 1) + C3 + C6) × time_dial

Where:
    I = fault_current / pickup_current  (normalized, must be > 1.0)
    C1..C6 = coefficients from tcc_etu_std_equations or tcc_etu_gfd_equations
    time_dial = LTD band multiplier (1.0 = no scaling)

Each equation row stores 4 curve variants:
    FD_OPEN  — frequency-dependent opening time
    FD_CLEAR — frequency-dependent clearing time
    ID_OPEN  — frequency-independent opening time
    ID_CLEAR — frequency-independent clearing time

Usage:
    from config import SessionLocal
    from apex_calc_engine.services.calc_engine.etu_curves import IEEEInverseTimeSolver

    with SessionLocal() as session:
        solver = IEEEInverseTimeSolver(session)

        # Single-point evaluation
        t = solver.trip_time(
            sensor_id=6258, ordinal=5, variant='fd_open',
            fault_current=2400.0, pickup_current=480.0,
        )

        # Generate full curve
        points = solver.generate_curve(
            sensor_id=6258, ordinal=5, variant='fd_open',
            pickup_current=480.0, max_amps=100000.0,
        )
"""

import math
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from apex_calc_engine.models.etu_equations import ETUSTDEquation, ETUGFDEquation


# Valid curve variant prefixes
VARIANTS = ('fd_open', 'fd_clear', 'id_open', 'id_clear')


@dataclass
class Coefficients:
    """Six IEEE inverse-time coefficients for one curve variant."""
    c1: float
    c2: float
    c3: float
    c4: float  # Extended term coefficient (C4*I)
    c5: float  # Extended term coefficient (C5*I²) or tolerance %
    c6: float  # Additive offset

    @property
    def is_zero(self) -> bool:
        """True if all coefficients are zero (no curve)."""
        return self.c1 == 0 and self.c2 == 0 and self.c3 == 0


@dataclass
class CurvePoint:
    """One (current, time) point on a TCC curve."""
    amps: float
    seconds: float


class IEEEInverseTimeSolver:
    """
    Evaluates IEEE inverse-time equations from the STD/GFD equation tables.

    Supports both single-point trip time calculation and full curve generation
    for TCC plotting.
    """

    # Minimum time floor (seconds) — prevents degenerate near-zero times
    MIN_TIME = 0.001
    # Points per log decade for curve generation
    POINTS_PER_DECADE = 50

    def __init__(self, session: Session):
        self.session = session

    def trip_time(
        self,
        sensor_id: int,
        ordinal: int,
        variant: str,
        fault_current: float,
        pickup_current: float,
        time_dial: float = 1.0,
        tolerance_pct: float = 0.0,
        equation_type: str = 'std',
    ) -> Optional[float]:
        """
        Calculate trip time for a single fault current.

        Args:
            sensor_id: Sensor ID
            ordinal: Dial/band position (1-based)
            variant: One of 'fd_open', 'fd_clear', 'id_open', 'id_clear'
            fault_current: Fault current in amps
            pickup_current: Pickup current in amps (from ETUPickupCalculator)
            time_dial: LTD band multiplier (default 1.0)
            tolerance_pct: Tolerance percentage (e.g. 10.0 for +10%)
            equation_type: 'std' or 'gfd'

        Returns:
            Trip time in seconds, or None if current is below pickup.
        """
        if pickup_current <= 0:
            return None

        I_norm = fault_current / pickup_current
        if I_norm <= 1.0:
            return None  # Below pickup — no trip

        coeff = self._load_coefficients(sensor_id, ordinal, variant, equation_type)
        if coeff is None or coeff.is_zero:
            return None

        return self._evaluate(coeff, I_norm, time_dial, tolerance_pct)

    def generate_curve(
        self,
        sensor_id: int,
        ordinal: int,
        variant: str,
        pickup_current: float,
        max_amps: float = 100000.0,
        time_dial: float = 1.0,
        tolerance_pct: float = 0.0,
        min_time: Optional[float] = None,
        equation_type: str = 'std',
    ) -> list[CurvePoint]:
        """
        Generate a full TCC curve as a list of (amps, seconds) points.

        Points are spaced logarithmically for smooth TCC plotting.

        Args:
            sensor_id: Sensor ID
            ordinal: Dial/band position (1-based)
            variant: One of 'fd_open', 'fd_clear', 'id_open', 'id_clear'
            pickup_current: Pickup current in amps
            max_amps: Maximum current in amps
            time_dial: LTD band multiplier
            tolerance_pct: Tolerance percentage
            min_time: Optional minimum time floor (seconds)
            equation_type: 'std' or 'gfd'

        Returns:
            List of CurvePoint sorted by descending time (ascending current).
        """
        if pickup_current <= 0:
            return []

        coeff = self._load_coefficients(sensor_id, ordinal, variant, equation_type)
        if coeff is None or coeff.is_zero:
            return []

        floor = min_time if min_time is not None else self.MIN_TIME

        # Log-spaced current sweep from just above pickup to max_amps
        I_start = 1.01  # Just above pickup
        I_end = max_amps / pickup_current
        if I_end <= I_start:
            return []

        points: list[CurvePoint] = []
        num_points = max(
            10,
            int(self.POINTS_PER_DECADE * math.log10(I_end / I_start))
        )

        log_start = math.log10(I_start)
        log_end = math.log10(I_end)
        step = (log_end - log_start) / num_points

        for i in range(num_points + 1):
            I_norm = 10 ** (log_start + i * step)
            amps = pickup_current * I_norm

            t = self._evaluate(coeff, I_norm, time_dial, tolerance_pct)
            if t is None or t < 0:
                continue

            if t < floor:
                # Hit the time floor — add crossover point then flat line
                points.append(CurvePoint(amps=round(amps, 2), seconds=round(floor, 6)))
                # Extend flat line to max amps
                if amps < max_amps:
                    points.append(CurvePoint(amps=round(max_amps, 2), seconds=round(floor, 6)))
                break

            points.append(CurvePoint(amps=round(amps, 2), seconds=round(t, 6)))

        return points

    def get_equation_info(
        self,
        sensor_id: int,
        equation_type: str = 'std',
    ) -> list[dict]:
        """
        Get all available equations (dial positions) for a sensor.

        Returns:
            List of dicts with 'ordinal', 'label', 'in_out' for each equation.
        """
        model = ETUSTDEquation if equation_type == 'std' else ETUGFDEquation
        rows = (
            self.session.query(model.ordinal, model.label, model.in_out)
            .filter(model.sensor_id == sensor_id)
            .order_by(model.ordinal)
            .all()
        )
        return [
            {'ordinal': r.ordinal, 'label': r.label, 'in_out': r.in_out}
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_coefficients(
        self,
        sensor_id: int,
        ordinal: int,
        variant: str,
        equation_type: str,
    ) -> Optional[Coefficients]:
        """Load 6 coefficients for one curve variant from the database."""
        if variant not in VARIANTS:
            raise ValueError(f"Invalid variant '{variant}'. Must be one of {VARIANTS}")

        model = ETUSTDEquation if equation_type == 'std' else ETUGFDEquation
        eq = (
            self.session.query(model)
            .filter(model.sensor_id == sensor_id, model.ordinal == ordinal)
            .one_or_none()
        )
        if eq is None:
            return None

        # Column names follow pattern: {variant}_1 .. {variant}_6
        def _col(n: int) -> float:
            val = getattr(eq, f'{variant}_{n}', None)
            return float(val) if val is not None else 0.0

        return Coefficients(
            c1=_col(1), c2=_col(2), c3=_col(3),
            c4=_col(4), c5=_col(5), c6=_col(6),
        )

    @staticmethod
    def _evaluate(
        coeff: Coefficients,
        I_norm: float,
        time_dial: float,
        tolerance_pct: float,
    ) -> Optional[float]:
        """
        Evaluate the IEEE inverse-time equation.

        Full equation (from C# CalcIeeeEq2):
            T_base = (C1 / (I^C2 - 1) + C3 + C6) × time_dial
            T_tol  = T_base × (1 + tolerance_pct / 100)

        The extended polynomial terms (C4*I + C5*I²) are available
        but rarely used in the standard IEEE formulation. When present,
        they add fixed-time offsets.

        Returns None if the denominator is invalid (I^C2 ≈ 1).
        """
        # Compute I^C2
        try:
            I_pow = I_norm ** coeff.c2
        except (OverflowError, ValueError):
            return None

        denom = I_pow - 1.0
        if abs(denom) < 1e-12:
            return None  # Singularity at I = 1.0

        # Core IEEE equation
        T_base = (coeff.c1 / denom + coeff.c3 + coeff.c6) * time_dial

        # Apply tolerance
        if tolerance_pct != 0.0:
            T_base *= (1.0 + tolerance_pct / 100.0)

        # Return None for negative times (non-physical)
        if T_base < 0:
            return None

        return T_base
