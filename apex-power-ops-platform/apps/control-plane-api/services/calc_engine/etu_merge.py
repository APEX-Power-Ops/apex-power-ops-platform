"""Compatibility shim for the shared calc-engine merge module."""

from apex_calc_engine.services.calc_engine.etu_merge import Curve
from apex_calc_engine.services.calc_engine.etu_merge import FILLET_INST
from apex_calc_engine.services.calc_engine.etu_merge import FILLET_POINTS
from apex_calc_engine.services.calc_engine.etu_merge import SENTINEL
from apex_calc_engine.services.calc_engine.etu_merge import log_log_intersect
from apex_calc_engine.services.calc_engine.etu_merge import merge_sst_curves

__all__ = [
    'Curve',
    'SENTINEL',
    'FILLET_INST',
    'FILLET_POINTS',
    'merge_sst_curves',
    'log_log_intersect',
]
