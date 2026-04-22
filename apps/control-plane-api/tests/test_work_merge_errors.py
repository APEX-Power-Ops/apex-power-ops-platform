"""
PM/Work Domain — Merge-Errors Helper Unit Tests
================================================
Packet: 2026-04-16-pm-schema-019

Exercises the shared ``_merge_errors`` and ``_raise_if_errors`` helpers
extracted from the seven PM mutation services.  These helpers consolidate
two patterns that were previously repeated by hand across every write
handler:

  * ``errors = {**org_errors, **wp_errors}`` (two sites in the
    work-package mutations).  Now one call: ``_merge_errors(...)``.
  * ``if errors: raise OrgValidationError(errors)`` (fourteen sites).
    Now one call: ``_raise_if_errors(errors)``.

Because the helpers are pure functions that live adjacent to the
OrgValidationError class and are exercised end-to-end by every PM write
test that asserts 422 behaviour (400+ pre-existing tests), this module
pins down the direct per-function contract: empty inputs no-op, single
inputs round-trip, multiple inputs merge with right-most-wins on key
overlap, and ``None`` inputs are tolerated as a convenience so callers
can hand in optional error dicts without pre-guarding.
"""

import sys
import os

import pytest

# Ensure the app root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.work.mutations import (  # noqa: E402
    OrgValidationError,
    _merge_errors,
    _raise_if_errors,
)


# ---------------------------------------------------------------------------
# _merge_errors
# ---------------------------------------------------------------------------

class TestMergeErrors:
    """Tests for ``_merge_errors``."""

    def test_merge_no_args_returns_empty_dict(self):
        assert _merge_errors() == {}

    def test_merge_single_empty_dict_returns_empty_dict(self):
        assert _merge_errors({}) == {}

    def test_merge_single_non_empty_returns_equal_dict(self):
        errors = {"client_id": "Invalid client_id"}
        merged = _merge_errors(errors)
        assert merged == errors

    def test_merge_returns_new_dict_not_input(self):
        errors = {"client_id": "Invalid client_id"}
        merged = _merge_errors(errors)
        # Mutating the merged dict must not affect the caller's dict.
        merged["other"] = "touched"
        assert "other" not in errors

    def test_merge_two_disjoint_dicts(self):
        a = {"client_id": "Invalid client_id"}
        b = {"site_id": "Invalid site_id"}
        merged = _merge_errors(a, b)
        assert merged == {
            "client_id": "Invalid client_id",
            "site_id": "Invalid site_id",
        }

    def test_merge_three_disjoint_dicts(self):
        a = {"client_id": "Invalid client_id"}
        b = {"site_id": "Invalid site_id"}
        c = {"contract_id": "Invalid contract_id"}
        merged = _merge_errors(a, b, c)
        assert set(merged.keys()) == {"client_id", "site_id", "contract_id"}

    def test_merge_right_most_wins_on_overlap(self):
        """Later inputs overwrite earlier inputs on the same key.

        This mirrors the ``{**a, **b}`` behaviour the helper replaced —
        important for sites that layer org/identity/intra-work error
        dicts where the last validator's message is the authoritative
        one for that key.
        """
        a = {"client_id": "first message"}
        b = {"client_id": "second message"}
        merged = _merge_errors(a, b)
        assert merged == {"client_id": "second message"}

    def test_merge_none_inputs_are_skipped(self):
        """``None`` is accepted as a convenience for optional error dicts."""
        a = {"client_id": "Invalid client_id"}
        merged = _merge_errors(a, None, {"site_id": "Invalid site_id"})
        assert merged == {
            "client_id": "Invalid client_id",
            "site_id": "Invalid site_id",
        }

    def test_merge_all_none_returns_empty_dict(self):
        assert _merge_errors(None, None) == {}

    def test_merge_all_empty_returns_empty_dict(self):
        assert _merge_errors({}, {}, {}) == {}

    def test_merge_preserves_string_values_verbatim(self):
        a = {"field_a": "message a with : colons and ; semicolons"}
        merged = _merge_errors(a)
        assert merged["field_a"] == "message a with : colons and ; semicolons"


# ---------------------------------------------------------------------------
# _raise_if_errors
# ---------------------------------------------------------------------------

class TestRaiseIfErrors:
    """Tests for ``_raise_if_errors``."""

    def test_noop_on_empty_dict(self):
        # Must not raise.
        _raise_if_errors({})

    def test_noop_on_none(self):
        _raise_if_errors(None)

    def test_raises_on_single_error(self):
        with pytest.raises(OrgValidationError) as exc_info:
            _raise_if_errors({"client_id": "Invalid client_id"})
        assert exc_info.value.errors == {"client_id": "Invalid client_id"}

    def test_raises_on_multiple_errors(self):
        payload = {
            "client_id": "Invalid client_id",
            "site_id": "Invalid site_id",
        }
        with pytest.raises(OrgValidationError) as exc_info:
            _raise_if_errors(payload)
        assert exc_info.value.errors == payload

    def test_raises_with_copied_dict_not_reference(self):
        """The raised exception carries a separate dict from the caller's.

        Callers commonly continue to populate the error dict after a
        non-raising check; the helper should defensively copy so a later
        mutation doesn't retroactively change the captured exception.
        """
        errors = {"client_id": "Invalid client_id"}
        try:
            _raise_if_errors(errors)
        except OrgValidationError as e:
            errors["site_id"] = "late addition"
            assert "site_id" not in e.errors

    def test_merge_then_raise_roundtrip(self):
        """Integration across the two helpers — the ``{**a, **b}`` pattern."""
        org_errors = {"client_id": "Invalid client_id"}
        wp_errors = {"site_id": "Invalid site_id"}
        merged = _merge_errors(org_errors, wp_errors)
        with pytest.raises(OrgValidationError) as exc_info:
            _raise_if_errors(merged)
        assert exc_info.value.errors == {
            "client_id": "Invalid client_id",
            "site_id": "Invalid site_id",
        }
