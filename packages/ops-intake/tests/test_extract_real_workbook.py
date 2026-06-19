"""Integration test against the real Rev10 estimator. Skips unless MINER_WORKBOOK is set."""
from ops_intake.extract import extract_workbook
from ops_intake.validate import validate


def test_real_miner(real_workbook):
    p = extract_workbook(real_workbook)
    assert abs(p.project.contract_value - 4692078.98) < 1.0
    mv = {s.scope_name: s for s in p.scopes if s.lines}
    assert len(mv) == 7  # 7 MV scopes with apparatus lines
    a1 = next(s for s in p.scopes if s.scope_name.startswith("A1"))
    assert abs(a1.quote.total_quoted_hours - 362.5) < 0.01
    assert sum(l.qty for l in a1.lines) >= 100  # QTY-expansion (A1 ~114 units)
    chiller = [s for s in p.scopes if "Chiller" in s.scope_name]
    assert len(chiller) == 2 and all(s.quote.is_estimate for s in chiller)
    bad = [c for c in validate(p) if not c.ok]
    assert not bad, bad
