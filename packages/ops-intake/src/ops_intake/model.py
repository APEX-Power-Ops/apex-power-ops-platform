from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QuoteLineIn:
    apparatus_type: str
    test_standard: str
    qty: int
    hrs_per_unit: float
    neta_section: str | None = None
    drawing: str | None = None
    designation: str | None = None
    notes: str | None = None
    line_number: int | None = None
    catalog_default_hours: float | None = None

    @property
    def line_hours(self) -> float:
        return round(self.qty * self.hrs_per_unit, 4)


@dataclass
class ScopeQuoteIn:
    onsite_labor: float = 0.0
    offsite_labor: float = 0.0
    travel: float = 0.0
    outside_services: float = 0.0
    unit_multiplier: float = 1.0
    pct_adjust: float = 1.0
    total_quoted_hours: float = 0.0
    is_estimate: bool = False  # chiller lump-sum flag

    @property
    def unadjusted_total(self) -> float:
        return self.onsite_labor + self.offsite_labor + self.travel + self.outside_services

    @property
    def adjusted_total(self) -> float:
        return self.unadjusted_total * self.unit_multiplier * self.pct_adjust


@dataclass
class ScopeIn:
    scope_name: str
    scope_type: str = "OTHER"
    sort_order: int = 0
    quote: ScopeQuoteIn = field(default_factory=ScopeQuoteIn)
    lines: list[QuoteLineIn] = field(default_factory=list)


@dataclass
class StandardHourIn:
    apparatus_type: str
    test_standard: str
    default_hours: float
    neta_section: str | None = None
    category: str | None = None


@dataclass
class ProjectIn:
    project_number: str
    project_name: str
    status: str = "Won"
    quote_revision: str | None = None
    quote_date: str | None = None
    estimator: str | None = None
    contract_value: float = 0.0
    business_unit: str | None = None
    description: str | None = None


@dataclass
class IntakePayload:
    project: ProjectIn
    scopes: list[ScopeIn] = field(default_factory=list)
    standard_hours: list[StandardHourIn] = field(default_factory=list)
