"""TDD smoke - the apex-jobs CLI verbs over the engine."""
from apex_jobs import cli


def test_cli_enqueue_status_queue(conn_test, capsys):
    assert cli.main(["enqueue", "--dispatch-id", "cli-1", "--title", "hello",
                     "--payload", '{"command": "true"}']) == 0
    out = capsys.readouterr().out.strip()
    assert len(out) >= 32  # a uuid was printed
    assert cli.main(["status", "cli-1"]) == 0
    assert "pending" in capsys.readouterr().out
    assert cli.main(["queue"]) == 0
    assert "cli-1" in capsys.readouterr().out


def test_cli_gated_flow(conn_test, capsys):
    assert cli.main(["enqueue", "--dispatch-id", "cli-g", "--title", "g",
                     "--requires-approval", "--gate-category", "schema"]) == 0
    capsys.readouterr()
    cli.main(["queue"])
    assert "cli-g" not in capsys.readouterr().out  # gated -> not claimable
    cli.main(["gates", "--job", "cli-g"])
    gate_id = capsys.readouterr().out.strip().splitlines()[0].split("\t")[0]
    assert cli.main(["approve", "--gate", gate_id, "--by", "operator"]) == 0
    capsys.readouterr()
    assert cli.main(["claim", "--as", "cc", "--env", "host"]) == 0
    assert "cli-g" in capsys.readouterr().out
