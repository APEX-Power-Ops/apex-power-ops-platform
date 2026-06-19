import pytest

from ops_intake.extract import extract_workbook
from ops_intake.model import ScopeQuoteIn
from ops_intake.validate import IntakeValidationError, assert_valid, validate


def test_validate_mini_passes(mini_workbook):
    checks = validate(extract_workbook(mini_workbook))
    assert all(c.ok for c in checks), [c for c in checks if not c.ok]


def test_validate_catches_total_mismatch(mini_workbook):
    p = extract_workbook(mini_workbook)
    # break the scope quote so Σ adjusted_total no longer equals contract_value (1000)
    p.scopes[0].quote = ScopeQuoteIn(onsite_labor=1.0, total_quoted_hours=25.0)
    with pytest.raises(IntakeValidationError):
        assert_valid(p)
