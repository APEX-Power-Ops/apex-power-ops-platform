"""TDD smoke - T7 CLI agent verbs: enqueue --kind agent (+ base-ref/prompt),
reap, promotions, review, unblock, and approve/reject routing a promotion gate to
engine.promote / discard_promotion. Reuses the offline fake-agent harness to park
a job at awaiting_promotion - no claude, no tokens."""
import os
import subprocess
import sys

import pytest

from apex_jobs import agent_runner, cli, engine

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = [sys.executable, os.path.join(HERE, "fake_agent.py")]
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def _git(*args, cwd=REPO, check=True):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=check)


@pytest.fixture
def promo_env(conn_test, tmp_path, monkeypatch):
    base = f"test-base-{os.path.basename(str(tmp_path))}"
    _git("branch", "-f", base, "HEAD")
    runs = str(tmp_path / "runs")
    monkeypatch.setenv("APEX_JOBS_REPO", REPO)
    monkeypatch.setenv("APEX_JOBS_RUNS_DIR", runs)
    created = []
    yield base, created
    for disp in created:
        _git("worktree", "remove", "--force", os.path.join(runs, disp), check=False)
        _git("branch", "-D", f"job/{disp}", check=False)
        _git("update-ref", "-d", f"refs/discarded/{disp}", check=False)
    _git("worktree", "prune", check=False)
    _git("branch", "-D", base, check=False)


def _enqueue_agent(disp, base):
    return cli.main(["enqueue", "--kind", "agent", "--dispatch-id", disp, "--title", "x",
                     "--base-ref", base, "--env-required", "host", "--prompt", "write a file"])


def _run_to_awaiting(disp, base, created):
    created.append(disp)
    assert _enqueue_agent(disp, base) == 0
    job = engine.claim(as_="cc", env="host")
    agent_runner.run_agent_job(job, env="host", agent_cmd=FAKE)
    assert engine.get_job(disp)["status"] == "awaiting_promotion"


def test_enqueue_agent_sets_kind_base_prompt(conn_test):
    assert cli.main(["enqueue", "--kind", "agent", "--dispatch-id", "a-1", "--title", "x",
                     "--base-ref", "tb", "--env-required", "host", "--prompt", "do x"]) == 0
    job = engine.get_job("a-1")
    assert job["kind"] == "agent"
    assert job["base_ref"] == "tb"
    assert job["payload"]["prompt"] == "do x"


def test_enqueue_command_default_kind(conn_test):
    assert cli.main(["enqueue", "--dispatch-id", "c-1", "--title", "x"]) == 0
    assert engine.get_job("c-1")["kind"] == "command"


def test_reap_prints_count(conn_test, capsys):
    assert cli.main(["reap"]) == 0
    assert capsys.readouterr().out.strip().isdigit()


def test_unblock_returns_to_pending(conn_test):
    engine.enqueue(dispatch_id="u-1", title="x", env_required="host")
    with engine._conn() as c:
        with c.cursor() as cur:
            cur.execute("update jobs.job set status='blocked' where dispatch_id='u-1'")
        c.commit()
    assert cli.main(["unblock", "u-1"]) == 0
    assert engine.get_job("u-1")["status"] == "pending"


def test_promotions_lists_awaiting(promo_env, capsys):
    base, created = promo_env
    _run_to_awaiting("a-2", base, created)
    capsys.readouterr()
    assert cli.main(["promotions"]) == 0
    assert "a-2" in capsys.readouterr().out


def test_review_prints_branch_and_diff(promo_env, capsys):
    base, created = promo_env
    _run_to_awaiting("a-5", base, created)
    capsys.readouterr()
    assert cli.main(["review", "a-5"]) == 0
    out = capsys.readouterr().out
    assert "job/a-5" in out and "AGENT_OUTPUT.md" in out


def test_approve_promotion_gate_promotes(promo_env):
    base, created = promo_env
    _run_to_awaiting("a-3", base, created)
    gate = next(g for g in engine.gates_for("a-3")
                if g["gate_type"] == "promotion" and g["state"] == "pending")
    assert cli.main(["approve", "--gate", str(gate["id"]), "--by", "operator"]) == 0
    assert engine.get_job("a-3")["status"] == "succeeded"
    assert _git("rev-parse", f"{base}^2", check=False).returncode == 0


def test_reject_promotion_gate_discards(promo_env):
    base, created = promo_env
    _run_to_awaiting("a-4", base, created)
    gate = next(g for g in engine.gates_for("a-4")
                if g["gate_type"] == "promotion" and g["state"] == "pending")
    assert cli.main(["reject", "--gate", str(gate["id"]), "--by", "operator"]) == 0
    assert engine.get_job("a-4")["status"] == "cancelled"
