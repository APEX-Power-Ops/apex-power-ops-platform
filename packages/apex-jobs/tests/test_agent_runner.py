"""TDD — agent-runner: worktree isolation + diff/result capture + promotion gate,
plus the bounded-concurrency pool. Driven entirely by the offline fake agent
(no claude, no tokens, no OAuth)."""
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


def _enqueue_agent_unclaimed(disp, base, created, prompt="write a file"):
    """Enqueue a kind='agent' job and leave it pending (NOT claimed) so run_pool
    can claim it itself. Returns the job id."""
    created.append(disp)
    jid = engine.enqueue(dispatch_id=disp, title="agent job", env_required="host",
                         payload={"prompt": prompt})
    # kind='agent' + base_ref (the enqueue agent params land in Task 7)
    with engine._conn() as c:
        with c.cursor() as cur:
            cur.execute("update jobs.job set kind='agent', base_ref=%s where id=%s", (base, jid))
        c.commit()
    return jid


def _enqueue_agent(disp, base, created, prompt="write a file"):
    """Enqueue + claim — the single-job tests drive run_agent_job on the claimed job."""
    _enqueue_agent_unclaimed(disp, base, created, prompt)
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


def test_run_pool_concurrency(agent_env, tmp_path):
    base, created, runs = agent_env
    probe = str(tmp_path / "probe.log")
    disps = ["p-0", "p-1", "p-2", "p-3"]
    for d in disps:
        _enqueue_agent_unclaimed(d, base, created)

    summaries = agent_runner.run_pool(
        as_="cc", env="host", concurrency=3,
        agent_cmd=FAKE + ["--probe", probe, "--sleep", "0.3"],
    )

    # every job ran to completion, each isolated in its own worktree
    assert len(summaries) == 4
    assert all(s["status"] == "succeeded" for s in summaries)
    for d in disps:
        assert engine.get_job(d)["status"] == "awaiting_promotion"
    worktrees = {engine.runs_for(d)[-1]["worktree_path"] for d in disps}
    assert len(worktrees) == 4, worktrees

    # the pool never ran more than `concurrency` agents simultaneously, but did run
    # them in parallel (a serial pool peaks at 1; an unbounded one at 4).
    events = []
    with open(probe) as f:
        for line in f:
            if not line.strip():
                continue
            kind, _pid, ts = line.split()
            events.append((float(ts), 1 if kind == "START" else -1))
    events.sort(key=lambda e: (e[0], e[1]))   # END (-1) before START (+1) at equal ts
    peak = cur = 0
    for _ts, delta in events:
        cur += delta
        peak = max(peak, cur)
    assert peak <= 3, f"pool exceeded concurrency cap: peak={peak}"
    assert peak >= 2, f"pool did not run agents in parallel: peak={peak}"


def test_run_pool_isolates_failing_job(agent_env, monkeypatch):
    base, created, runs = agent_env
    for d in ("q-0", "q-1"):
        _enqueue_agent_unclaimed(d, base, created)
    real = agent_runner.run_agent_job

    def maybe_fail(job, env, as_="cc", agent_cmd=None):
        if job["dispatch_id"] == "q-0":
            raise RuntimeError("agent blew up")
        return real(job, env, as_=as_, agent_cmd=agent_cmd)

    monkeypatch.setattr(agent_runner, "run_agent_job", maybe_fail)
    res = agent_runner.run_pool(as_="cc", env="host", concurrency=2, agent_cmd=FAKE)
    # one job blew up but the pool drained both and the other still completed
    assert len(res) == 2
    assert any("error" in r for r in res)
    assert any(r.get("status") == "succeeded" for r in res)
    assert engine.get_job("q-1")["status"] == "awaiting_promotion"


def test_agent_env_prepends_agent_bins_to_path(monkeypatch):
    monkeypatch.setenv("APEX_JOBS_AGENT_PATH", "/opt/agent/bin")
    monkeypatch.setenv("PATH", "/usr/bin")
    env = agent_runner._agent_env("host")
    assert env["APEX_JOB_ENV"] == "host"
    parts = env["PATH"].split(os.pathsep)
    assert parts[0] == "/opt/agent/bin", parts
    assert "/usr/bin" in parts


def test_agent_env_default_includes_codex_bin(monkeypatch):
    monkeypatch.delenv("APEX_JOBS_AGENT_PATH", raising=False)
    env = agent_runner._agent_env("host")
    assert "/home/olares/.nvm/versions/node/v20.20.2/bin" in env["PATH"].split(os.pathsep)
