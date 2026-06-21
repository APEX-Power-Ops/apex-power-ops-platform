from ops_intake.validate import validate_payload, Finding
from ops_intake.model import IntakePayload, ProjectIn, ScopeIn, ScopeQuoteIn, QuoteLineIn


def _mismatch_payload():
    q = ScopeQuoteIn(onsite_labor=1000, total_quoted_hours=5)  # P4=1000
    s = ScopeIn(scope_name="A", quote=q, lines=[QuoteLineIn("X","ATS",1,2.0)])  # line hrs=2 != J3=5
    return IntakePayload(ProjectIn(project_number="J", project_name="N", contract_value=1000.0), [s])


def test_blocking_has_no_dollars_in_message():
    fs = validate_payload(_mismatch_payload(), source_format="decomposed_scope_sheet")
    bad = [f for f in fs if not f.ok and f.severity == "blocking"]
    assert bad
    for f in bad:
        assert "$" not in f.message              # no currency symbol in PM-safe text
        assert "1000" not in f.message           # the P4 figure lives only in diagnostic_detail
        assert f.message                         # PM-safe message non-empty
        assert f.diagnostic_detail               # the numbers are captured for finance


def test_n4_default_is_info_when_reconciles():
    q = ScopeQuoteIn(onsite_labor=1000, unit_multiplier=1, pct_adjust=1, total_quoted_hours=2)
    s = ScopeIn(scope_name="A", quote=q, lines=[QuoteLineIn("X","ATS",1,2.0)])
    p = IntakePayload(ProjectIn(project_number="J", project_name="N", contract_value=1000.0), [s])
    fs = validate_payload(p, source_format="decomposed_scope_sheet", n4_defaulted=True)
    n4 = [f for f in fs if f.code == "n4_default"][0]
    assert n4.severity in ("info","fidelity") and n4.ok is True
    assert all(f.ok for f in fs if f.severity == "blocking")
