"""Compatibility shim for the shared calc-engine IEEE curve module."""

from apex_calc_engine.services.calc_engine.etu_curves import Coefficients
from apex_calc_engine.services.calc_engine.etu_curves import CurvePoint
from apex_calc_engine.services.calc_engine.etu_curves import IEEEInverseTimeSolver
from apex_calc_engine.services.calc_engine.etu_curves import VARIANTS

__all__ = [
    'VARIANTS',
    'Coefficients',
    'CurvePoint',
    'IEEEInverseTimeSolver',
]
