import json

from learning_projections.cli import main

U_TARGET = "11111111-0000-0000-0000-000000000001"


def test_cli_competency_json(capsys):
    rc = main(["competency", "--user", U_TARGET])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["resolved_level"] == "II"
    assert out["coverage"][0]["covered_ksas"] == 2


def test_cli_cohort_json(capsys):
    rc = main(["cohort"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["user_count"] == 4
