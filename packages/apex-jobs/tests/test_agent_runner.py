"""TDD — agent-runner: worktree isolation + diff/result capture + promotion gate.
Driven entirely by the offline fake agent (no claude, no tokens, no OAuth)."""
import os
import subprocess
import sys

import pytest

from apex_jobs import engine, agent_runner

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = [sys.executable, os.path.join(HERE, "fake_agent.py")]
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))   # the lane repo root


@pytest.fixture
def agent_env(conn_test, tmp_path, monkeypatch):
    """Throwaway base branch (not checked out) + an isolated runs dir; cleans up
    any job worktrees/branches it creates."""
    base = f"test-base-{os.path.basename(str(tmp_path))}"
    subprocess.run(["git", "-C", REPO, "branch", "-f", base, "HEAD"],
                   check=True, capture_output=True)
    runs = str(tmp_path / "runs")
    monkeypatch.setenv("APEX_JOBS_REPO", REPO)
    monkeypatch.setenv("APEX_JOBS_RUNS_DIR", runs)
    created = []
    yield base, created, runs
    for disp in created:
        subprocess.run(["git", "-C", REPO, "worktree", "remove", "--force",
                        os.path.join(runs, disp)], capture_output=True)
        subprocess.run(["git", "-C", REPO, "branch", "-D", f"job/{disp}"], capture_output=True)
    subprocess.run(["git", "-C", REPO, "worktree", "prune"], capture_output=True)
    subprocess.run(["git", "-C", REPO, "branch", "-D", base], capture_output=True)


def _enqueue_agent(disp, base, created, prompt="write a file"):
    created.append(disp)
    jid = engine.enqueue(dispatch_id=disp, title="agent job", env_required="host",
                         payload={"prompt": prompt})
    # kind='agent' + base_ref (the enqueue agent params land in Task 7)
    with engine._conn() as c:
        with c.cursor() as cur:
            cur.execute("update jobs.job set kind='agent', base_ref=%s where id=%s", (base, jid))
        c.commit()
    return engine.claim(as_="cc", env="host")


def test_agent_job_success(agent_env):
    base, created, runs = agent_env
    j = _enqueue_agent("a-ok", base, created)
    r = agent_runner.run_agent_job(j, env="host", agent_cmd=FAKE)
    assert r["status"] == "succeeded"
    assert r["no_changes"] is False
    # worktree exists, has the agent output, and is NOT removed (audit the real tree)
    wt = os.path.join(runs, "a-ok")
    assert os.path.exists(os.path.join(wt, "AGENT_OUTPUT.md"))
    run = engine.runs_for("a-ok")[-1]
    assert run["worktree_path"] == wt and run["branch"] == "job/a-ok"
    assert run["diff_stat"]
    # promotion gate opened + job parked awaiting_promotion
    assert engine.get_job("a-ok")["status"] == "awaiting_promotion"
    assert any(g["gate_type"] == "promotion" for g in engine.gates_for("a-ok"))


def test_agent_job_failure(agent_env):
    base, created, runs = agent_env
    j = _enqueue_agent("a-fail", base, created)
    r = agent_runner.run_agent_job(j, env="host", agent_cmd=FAKE + ["--fail"])
    assert r["status"] == "failed"
    assert not any(g["gate_type"] == "promotion" for g in engine.gates_for("a-fail"))
    assert os.path.exists(os.path.join(runs, "a-fail"))   # worktree retained for diagnosis


def test_agent_job_no_changes(agent_env):
    base, created, runs = agent_env
    j = _enqueue_agent("a-noop", base, created)
    r = agent_runner.run_agent_job(j, env="host", agent_cmd=FAKE + ["--no-write"])
    assert r["status"] == "succeeded" and r["no_changes"] is True
    # promotion gate still opened so the reviewer sees "nothing to merge"
    assert any(g["gate_type"] == "promotion" for g in engine.gates_for("a-noop"))
