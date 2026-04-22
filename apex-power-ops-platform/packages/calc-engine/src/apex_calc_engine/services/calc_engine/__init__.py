"""
Apex Platform Calc Engine
=========================
Shared platform calc-domain package for breaker curve and pickup calculations.

Services:
- etu_pickup: ETU pickup current calculator (11 calc methods)
- etu_curves: IEEE inverse-time equation solver (STD/GFD curves)
- etu_ltd: 5 LTD calculation methods (Thermal, IEEE, GE-SMR, TU, TUF)
- tmt_curves: TMT Catmull-Rom spline interpolation
- etu_merge: Curve segment assembly with fillet transitions
"""

from .etu_pickup import ETUCalcMethod, ETUPickupCalculator, PickupResult, AllPickupResults
from .etu_curves import IEEEInverseTimeSolver, Coefficients, CurvePoint
from .etu_ltd import ETULTDCalculator, LTDCurvePoint
from .tmt_curves import TMTCurveGenerator, TMTCurvePoint, fillet
from .etu_merge import merge_sst_curves, log_log_intersect

__all__ = [
    'ETUCalcMethod',
    'ETUPickupCalculator',
    'PickupResult',
    'AllPickupResults',
    'IEEEInverseTimeSolver',
    'Coefficients',
    'CurvePoint',
    'ETULTDCalculator',
    'LTDCurvePoint',
    'TMTCurveGenerator',
    'TMTCurvePoint',
    'fillet',
    'merge_sst_curves',
    'log_log_intersect',
]
