"""ProposedValue - one proposed datasheet control value from a parsed instrument reading.

Source-agnostic: a mapping function (per format x family) turns a parsed reading model into a list of
these; the DB layer upserts the confirmed ones into records.form_field_values. Carries everything a
form_field_values row needs, including provenance (origin_device + measured_at).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProposedValue:
    field_key: str                 # "<section>.<row>.<column>" (table) | "<section>.<field>" (fields)
    test_group: str                # the section key
    value_numeric: float | None = None
    value_text: str | None = None
    value_kind: str = "numeric"    # records.field_value_kind_enum
    unit: str | None = None
    measured_at: str | None = None
    origin_device: str | None = None   # the instrument string -> "imported" provenance
    notes: str | None = None           # measured/correction/grade context
