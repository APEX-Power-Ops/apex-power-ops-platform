"""Tests for the relay selection-cascade WHERE-builder (Chip 2).

Unit tests for ``_relay_cascade_conditions`` — the faceted-search logic behind the
guided relay dropdowns (Mfr → Type → Device Function → Standard / Family, GR §1).
The SQL execution itself is validated against live data + live-verified post-deploy.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from services.neta.router import _RELAY_STANDARD_LABELS, _relay_cascade_conditions


ALL_FILTERS = {
    "manufacturer_source_id": 55,
    "relay_type": "SEL-751",
    "device_function": "51",
    "standard_code": 0,
    "family_code": 5,
}


def test_no_filters_is_empty():
    clauses, params = _relay_cascade_conditions({})
    assert clauses == []
    assert params == {}


def test_single_filter():
    clauses, params = _relay_cascade_conditions({"manufacturer_source_id": 55})
    assert clauses == ["r.manufacturer_source_id = :manufacturer_source_id"]
    assert params == {"manufacturer_source_id": 55}


def test_all_filters_present():
    clauses, params = _relay_cascade_conditions(ALL_FILTERS)
    assert len(clauses) == 5
    assert params == ALL_FILTERS


def test_none_values_are_excluded():
    clauses, params = _relay_cascade_conditions({**ALL_FILTERS, "relay_type": None, "family_code": None})
    assert "relay_type" not in params
    assert "family_code" not in params
    assert len(clauses) == 3


def test_exclude_drops_only_that_facet():
    clauses, params = _relay_cascade_conditions(ALL_FILTERS, exclude="relay_type")
    assert "relay_type" not in params
    assert "r.relay_type = :relay_type" not in clauses
    assert len(clauses) == 4
    # the other four filters remain (so the relay_type dropdown shows all options
    # compatible with mfr/function/standard/family)
    assert {"manufacturer_source_id", "device_function", "standard_code", "family_code"} <= set(params)


def test_exclude_absent_filter_is_noop():
    base = {"manufacturer_source_id": 55}
    clauses, params = _relay_cascade_conditions(base, exclude="relay_type")
    assert clauses == ["r.manufacturer_source_id = :manufacturer_source_id"]
    assert params == base


def test_standard_label_mapping():
    # 0 ANSI / 1 IEC / 2 Both — confirmed live (GR §1 distribution 0 > 1 > 2)
    assert _RELAY_STANDARD_LABELS == {0: "ANSI", 1: "IEC", 2: "Both"}
