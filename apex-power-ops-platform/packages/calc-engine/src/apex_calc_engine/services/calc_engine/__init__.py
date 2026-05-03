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
from .relay_dispatch import (
    family_from_model_code,
    evaluate_curve_definition,
    definition_from_iec_row,
    definition_from_swz_row,
    definition_from_bsl_row,
    definition_from_meq_row,
    definition_from_pcd_row,
    definition_from_tcp_points,
)
from .relay_types import (
    RelayCurveDefinition,
    RelayCurvePoint,
    RelayEvaluatedCurve,
    RelayEvaluationStatus,
    RelayFormulaCode,
)

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
    'family_from_model_code',
    'evaluate_curve_definition',
    'definition_from_iec_row',
    'definition_from_swz_row',
    'definition_from_bsl_row',
    'definition_from_meq_row',
    'definition_from_pcd_row',
    'definition_from_tcp_points',
    'RelayCurveDefinition',
    'RelayCurvePoint',
    'RelayEvaluatedCurve',
    'RelayEvaluationStatus',
    'RelayFormulaCode',
]
