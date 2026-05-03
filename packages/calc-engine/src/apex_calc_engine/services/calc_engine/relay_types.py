"""Shared relay types for the calc-engine relay runtime slice."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Mapping


class RelayFormulaCode(IntEnum):
    UNKNOWN = 0
    TCP = 1
    IEC = 2
    MEQ = 3
    BSL = 4
    SWZ = 5
    PCD = 6
    RXD = 7
    LRM = 8
    EGC = 9


class RelayEvaluationStatus(str, Enum):
    SUPPORTED = 'supported'
    UNSUPPORTED = 'unsupported'


SUPPORTED_FAMILIES = frozenset({
    RelayFormulaCode.TCP,
    RelayFormulaCode.IEC,
    RelayFormulaCode.MEQ,
    RelayFormulaCode.BSL,
    RelayFormulaCode.SWZ,
    RelayFormulaCode.PCD,
})

UNSUPPORTED_FAMILIES = frozenset({
    RelayFormulaCode.RXD,
    RelayFormulaCode.LRM,
    RelayFormulaCode.EGC,
})


@dataclass(frozen=True)
class RelayCurvePoint:
    current_multiple: float
    trip_time_seconds: float
    source_ordinal: int | None = None
    time_dial: float | None = None
    label: str | None = None


@dataclass(frozen=True)
class RelayCurveDefinition:
    family: RelayFormulaCode
    curve_name: str
    source_row_id: int
    parent_source_id: int
    ordinal: int | None = None
    coefficients: Mapping[str, float] = field(default_factory=dict)
    points: tuple[RelayCurvePoint, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def require_coefficients(self, *names: str) -> tuple[float, ...]:
        missing = [name for name in names if name not in self.coefficients or self.coefficients[name] is None]
        if missing:
            raise ValueError(f"Relay curve '{self.curve_name}' is missing coefficients: {', '.join(missing)}")
        return tuple(float(self.coefficients[name]) for name in names)


@dataclass(frozen=True)
class RelayEvaluatedCurve:
    family: RelayFormulaCode
    curve_name: str
    time_dial: float
    points: tuple[RelayCurvePoint, ...]
    status: RelayEvaluationStatus = RelayEvaluationStatus.SUPPORTED
    reason: str | None = None
