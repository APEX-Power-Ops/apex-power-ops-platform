import json

from learning_capture.cli import main
from tests.conftest import USER


def test_cli_record_prints_event_id(capsys):
    rc = main(["record", "--user", USER, "--type", "resource_viewed", "--section", "7.2.1.1"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "event_id" in out


def test_cli_list_json(capsys):
    main(["record", "--user", USER, "--type", "resource_completed"])
    capsys.readouterr()  # drain the record output
    rc = main(["list", "--user", USER, "--limit", "5", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert isinstance(data, list)
    assert all("event_type" in r for r in data)
