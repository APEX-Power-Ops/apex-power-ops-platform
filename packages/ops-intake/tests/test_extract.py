from ops_intake.extract import extract_workbook


def test_extract_mini(mini_workbook):
    p = extract_workbook(mini_workbook)
    assert p.project.contract_value == 1000.0
    assert len(p.scopes) == 1
    s = p.scopes[0]
    assert s.scope_name == "A1) MV - Test"
    assert s.quote.total_quoted_hours == 25.0
    assert (s.quote.onsite_labor, s.quote.offsite_labor, s.quote.travel, s.quote.outside_services) == (
        800.0, 100.0, 50.0, 50.0,
    )
    assert len(s.lines) == 2  # sub-header row 7 skipped
    assert [l.qty for l in s.lines] == [2, 3]
    assert s.lines[1].apparatus_type == "Transformer - Pad" and s.lines[1].hrs_per_unit == 5.0
    assert any(h.apparatus_type == "Vacuum Interrupter" and h.test_standard == "ATS"
               for h in p.standard_hours)
