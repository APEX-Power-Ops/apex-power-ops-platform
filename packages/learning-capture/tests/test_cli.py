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


def test_acquire_subcommand_records_with_envelope(capsys):
    from learning_capture.cli import main
    rc = main(["acquire", "--user", "00000000-0000-0000-0000-000000000001",
               "--type", "resource_completed", "--content", "00000000-0000-0000-0000-000000000010",
               "--section", "7.1", "--run-id", "run-CLI", "--observed-by", "JS",
               "--evidence-ref", "notes#L9", "--fidelity", "rehearsal"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "event_id" in out
