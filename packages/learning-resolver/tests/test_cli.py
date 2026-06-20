import json

from learning_resolver.cli import main


def test_cli_json_output(capsys, section_with_curated):
    rc = main(["resolve", "--section", section_with_curated, "--limit", "5", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list) and len(payload) <= 5
    assert {"resource_type", "title", "source", "score"} <= set(payload[0].keys())


def test_cli_unknown_section_empty(capsys):
    rc = main(["resolve", "--section", "9.9.9.9-nope", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out) == []
