from ops_intake.classify import classify
from ops_intake.model import IntakePayload, ProjectIn, ScopeIn, QuoteLineIn

def _proj(): return ProjectIn(project_number="J", project_name="N", contract_value=100.0)

def test_decomposed():
    s = ScopeIn(scope_name="A", lines=[QuoteLineIn("X","ATS",1,2.0)])
    assert classify(IntakePayload(_proj(), [s])) == "decomposed_scope_sheet"

def test_decomposed_even_with_zero_contract():
    s = ScopeIn(scope_name="A", lines=[QuoteLineIn("X","ATS",1,2.0)])
    p = IntakePayload(ProjectIn(project_number="J", project_name="N", contract_value=0.0), [s])
    assert classify(p) == "decomposed_scope_sheet"   # 0 total is a finding, not a format rejection

def test_flat_quote():
    assert classify(IntakePayload(_proj(), [ScopeIn(scope_name="A")])) == "flat_quote"

def test_unsupported():
    assert classify(IntakePayload(ProjectIn(project_number="J", project_name="N"), [])) == "unsupported"
