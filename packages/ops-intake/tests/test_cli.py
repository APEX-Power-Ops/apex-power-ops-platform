import json

from ops_intake.cli import main


def test_cli_extract(mini_workbook, tmp_path):
    out = tmp_path / "p.json"
    rc = main(["extract", str(mini_workbook), "--out", str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["project"]["contract_value"] == 1000.0
    assert len(data["scopes"]) == 1
    assert data["scopes"][0]["scope_name"] == "A1) MV - Test"
