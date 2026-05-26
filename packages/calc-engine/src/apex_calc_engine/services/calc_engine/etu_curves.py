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

from sqlalchemy import text
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
        return [
            {
                'ordinal': row['ordinal'],
                'label': row['label'],
                'in_out': row['in_out'],
            }
            for row in self._load_equation_rows(sensor_id, equation_type)
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

        row = next(
            (
                equation_row
                for equation_row in self._load_equation_rows(sensor_id, equation_type)
                if int(equation_row['ordinal']) == int(ordinal)
            ),
            None,
        )
        if row is None:
            return None

        # Column names follow pattern: {variant}_1 .. {variant}_6
        def _col(n: int) -> float:
            val = row.get(f'{variant}_{n}')
            return float(val) if val is not None else 0.0

        return Coefficients(
            c1=_col(1), c2=_col(2), c3=_col(3),
            c4=_col(4), c5=_col(5), c6=_col(6),
        )

    def _load_equation_rows(
        self,
        sensor_id: int,
        equation_type: str,
    ) -> list[dict[str, object]]:
        """Load source-faithful equation rows, falling back to package ORM rows.

        Promoted from the tcc source-domain compatibility path per matrix
        #30(b). The SQL path accepts rebuilt/source-faithful column names
        (`eq_desc`, `fd_op_*`, `fd_cl_*`, `id_op_*`, `id_cl_*`), while the
        fallback preserves the package's existing ORM-backed row contract.
        """
        table_name = 'tcc_etu_std_equations' if equation_type == 'std' else 'tcc_etu_gfd_equations'
        params = {'sensor_id': sensor_id}

        try:
            rows = self.session.execute(
                text(
                    f"""
                    SELECT eq_desc AS label,
                           in_out,
                           fd_op_1 AS fd_open_1,
                           fd_op_2 AS fd_open_2,
                           fd_op_3 AS fd_open_3,
                           fd_op_4 AS fd_open_4,
                           fd_op_5 AS fd_open_5,
                           fd_op_6 AS fd_open_6,
                           fd_cl_1 AS fd_clear_1,
                           fd_cl_2 AS fd_clear_2,
                           fd_cl_3 AS fd_clear_3,
                           fd_cl_4 AS fd_clear_4,
                           fd_cl_5 AS fd_clear_5,
                           fd_cl_6 AS fd_clear_6,
                           id_op_1 AS id_open_1,
                           id_op_2 AS id_open_2,
                           id_op_3 AS id_open_3,
                           id_op_4 AS id_open_4,
                           id_op_5 AS id_open_5,
                           id_op_6 AS id_open_6,
                           id_cl_1 AS id_clear_1,
                           id_cl_2 AS id_clear_2,
                           id_cl_3 AS id_clear_3,
                           id_cl_4 AS id_clear_4,
                           id_cl_5 AS id_clear_5,
                           id_cl_6 AS id_clear_6
                    FROM {table_name}
                    WHERE sensor_id = :sensor_id
                    ORDER BY CASE
                               WHEN eq_desc ~ '^-?[0-9]+(\\.[0-9]+)?$' THEN eq_desc::numeric
                               ELSE NULL
                             END NULLS LAST,
                             eq_desc
                    """
                ),
                params,
            ).fetchall()
            return self._normalize_equation_rows(rows)
        except Exception:
            if hasattr(self.session, 'rollback'):
                self.session.rollback()

        model = ETUSTDEquation if equation_type == 'std' else ETUGFDEquation
        rows = (
            self.session.query(model)
            .filter(model.sensor_id == sensor_id)
            .order_by(model.ordinal)
            .all()
        )
        return self._normalize_equation_rows(rows)

    @staticmethod
    def _normalize_equation_rows(rows) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []

        def _read(row, key: str, default=None):
            if hasattr(row, '_mapping'):
                return row._mapping.get(key, default)
            if isinstance(row, dict):
                return row.get(key, default)
            return getattr(row, key, default)

        for index, row in enumerate(rows, start=1):
            ordinal = _read(row, 'ordinal', index)
            normalized.append({
                'ordinal': int(ordinal) if ordinal is not None else index,
                'label': _read(row, 'label'),
                'in_out': _read(row, 'in_out'),
                'fd_open_1': _read(row, 'fd_open_1'),
                'fd_open_2': _read(row, 'fd_open_2'),
                'fd_open_3': _read(row, 'fd_open_3'),
                'fd_open_4': _read(row, 'fd_open_4'),
                'fd_open_5': _read(row, 'fd_open_5'),
                'fd_open_6': _read(row, 'fd_open_6'),
                'fd_clear_1': _read(row, 'fd_clear_1'),
                'fd_clear_2': _read(row, 'fd_clear_2'),
                'fd_clear_3': _read(row, 'fd_clear_3'),
                'fd_clear_4': _read(row, 'fd_clear_4'),
                'fd_clear_5': _read(row, 'fd_clear_5'),
                'fd_clear_6': _read(row, 'fd_clear_6'),
                'id_open_1': _read(row, 'id_open_1'),
                'id_open_2': _read(row, 'id_open_2'),
                'id_open_3': _read(row, 'id_open_3'),
                'id_open_4': _read(row, 'id_open_4'),
                'id_open_5': _read(row, 'id_open_5'),
                'id_open_6': _read(row, 'id_open_6'),
                'id_clear_1': _read(row, 'id_clear_1'),
                'id_clear_2': _read(row, 'id_clear_2'),
                'id_clear_3': _read(row, 'id_clear_3'),
                'id_clear_4': _read(row, 'id_clear_4'),
                'id_clear_5': _read(row, 'id_clear_5'),
                'id_clear_6': _read(row, 'id_clear_6'),
            })
        return normalized

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
