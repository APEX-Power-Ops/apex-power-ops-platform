from ops_intake.model import (
    IntakePayload, ProjectIn, ScopeIn, ScopeQuoteIn, QuoteLineIn, StandardHourIn,
)


def test_payload_constructs_and_totals():
    line = QuoteLineIn(apparatus_type="Transformer - Pad", test_standard="ATS", qty=9,
                       hrs_per_unit=8.0, neta_section="7.2", drawing="E01-01", line_number=20)
    assert line.line_hours == 72.0
    quote = ScopeQuoteIn(onsite_labor=67787.5, offsite_labor=3081.25, travel=16946.875,
                         outside_services=3375.0, unit_multiplier=1.0, pct_adjust=1.0,
                         total_quoted_hours=362.5)
    assert round(quote.unadjusted_total, 3) == 91190.625
    assert round(quote.adjusted_total, 3) == 91190.625
    scope = ScopeIn(scope_name="A1) Medium-Voltage - Core", scope_type="OTHER",
                    sort_order=1, quote=quote, lines=[line])
    payload = IntakePayload(
        project=ProjectIn(project_number="MINER-PHX-AB-MV",
                          project_name="Project Miner — PHX Bldg A & B MV",
                          status="Won", quote_revision="Rev10", contract_value=4692078.98,
                          description="Public/product name: Project Jupiter."),
        scopes=[scope],
        standard_hours=[StandardHourIn(apparatus_type="Transformer - Pad", test_standard="ATS",
                                       default_hours=8.0, neta_section="7.2")])
    assert payload.scopes[0].lines[0].qty == 9
    assert payload.project.contract_value == 4692078.98


from ops_intake.model import ProjectIn, QuoteLineIn, PAYLOAD_SCHEMA_VERSION

def test_project_carries_client_site():
    p = ProjectIn(project_number="J1", project_name="N", client_name="Garney", site_city="Mesa")
    assert p.client_name == "Garney" and p.site_city == "Mesa"

def test_line_carries_section():
    assert QuoteLineIn(apparatus_type="X", test_standard="ATS", qty=1, hrs_per_unit=2.0,
                       section="SES-00-001").section == "SES-00-001"

def test_line_carries_stable_uid():
    l = QuoteLineIn(apparatus_type="X", test_standard="ATS", qty=1, hrs_per_unit=2.0,
                    section="SES-00-001", line_uid="ScopeA:row7")
    assert l.line_uid == "ScopeA:row7"

def test_schema_version_constant():
    assert PAYLOAD_SCHEMA_VERSION == "1"
