from ops_intake.extract import extract_workbook


def test_extract_mini(mini_workbook):
    p = extract_workbook(mini_workbook)
    # Project IDENTITY must be DERIVED from the workbook (Dataverse_Import "Job #"), never hard-coded.
    # This is the false-green the operator caught: counts/structure were asserted but identity never was.
    assert p.project.project_number == "J1-TEST-001"
    assert p.project.project_name  # non-empty (falls back to project_number when no Project Name row)
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
    assert s.lines[1].apparatus_type == "Capcitors - Per Unit" and s.lines[1].hrs_per_unit == 5.0
    assert any(h.apparatus_type == "Circuit Breaker MV - Vacuum Bkr" and h.test_standard == "ATS"
               for h in p.standard_hours)


def test_two_workbooks_yield_distinct_project_numbers(tmp_path):
    # The core multi-project guarantee: an arbitrary workbook yields ITS OWN project_number,
    # so two different uploads do NOT collapse to one identity (the C1 critical the operator caught).
    from fixtures.build_fixture import build
    p1 = extract_workbook(build(tmp_path / "wb1.xlsx", job_number="JOB-AAA"))
    p2 = extract_workbook(build(tmp_path / "wb2.xlsx", job_number="JOB-BBB"))
    assert p1.project.project_number == "JOB-AAA"
    assert p2.project.project_number == "JOB-BBB"
    assert p1.project.project_number != p2.project.project_number


def test_extract_sections_and_metadata(mini_workbook):
    p = extract_workbook(mini_workbook)
    s = p.scopes[0]
    assert any(l.section for l in s.lines)              # section captured
    assert all(l.line_uid for l in s.lines)             # stable per-line identity minted at parse
    assert len({l.line_uid for sc in p.scopes for l in sc.lines}) == sum(len(sc.lines) for sc in p.scopes)  # unique
    assert abs(s.quote.pct_adjust - 1.0) < 1e-9         # N4 read
    assert p.project.client_name is not None            # metadata sheet read
