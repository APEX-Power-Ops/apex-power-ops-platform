"""TDD — T6 promotion firewall: engine.promote / discard_promotion + worker
kind-dispatch. Hardened per the adversarial design review: covers the protected /
checked-out / null base refusals, the already-merged no-op (branch preserved),
double-promote & promote-after-discard idempotency, the compare-and-swap
lost-update guard, promotion-gate closure, recoverable discard, the shared
worktree lock, and the worker agent/command dispatch routes. All driven by the
offline fake agent — no claude, no tokens, no OAuth."""
import os
import pathlib
import subprocess
import sys
import threading
from unittest import mock

import pytest

from apex_jobs import agent_runner, engine, worker

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = [sys.executable, os.path.join(HERE, "fake_agent.py")]
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))   # the lane repo root


def _git(*args, cwd=REPO, check=True):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=check)


def _sha(ref):
    return _git("rev-parse", "--verify", ref).stdout.strip()


@pytest.fixture
def promo_env(conn_test, tmp_path, monkeypatch):
    """Throwaway non-checked-out base branch + isolated runs dir; cleans up job
    worktrees/branches, discarded refs, and any extra worktrees/branches a test makes."""
    base = f"test-base-{os.path.basename(str(tmp_path))}"
    _git("branch", "-f", base, "HEAD")
    runs = str(tmp_path / "runs")
    monkeypatch.setenv("APEX_JOBS_REPO", REPO)
    monkeypatch.setenv("APEX_JOBS_RUNS_DIR", runs)
    created, extra_wt, extra_br = [], [], []
    yield base, created, runs, extra_wt, extra_br
    for wt in extra_wt:
        _git("worktree", "remove", "--force", wt, check=False)
    for disp in created:
        _git("worktree", "remove", "--force", os.path.join(runs, disp), check=False)
        _git("branch", "-D", f"job/{disp}", check=False)
        _git("update-ref", "-d", f"refs/discarded/{disp}", check=False)
    for br in extra_br:
        _git("branch", "-D", br, check=False)
    _git("worktree", "prune", check=False)
    _git("branch", "-D", base, check=False)


def _set_base_ref(disp, value):
    with engine._conn() as c:
        with c.cursor() as cur:
            if value is None:
                cur.execute("update jobs.job set base_ref=NULL where dispatch_id=%s", (disp,))
            else:
                cur.execute("update jobs.job set base_ref=%s where dispatch_id=%s", (value, disp))
        c.commit()


def _run_to_awaiting(disp, base, created, agent_cmd=None):
    """Enqueue a kind='agent' job off `base`, run the fake agent to completion ->
    job parks at awaiting_promotion with a job/<disp> branch + worktree + a pending
    promotion gate. Returns the agent branch tip sha."""
    created.append(disp)
    jid = engine.enqueue(dispatch_id=disp, title="agent job", env_required="host",
                         payload={"prompt": "write a file"})
    with engine._conn() as c:
        with c.cursor() as cur:
            cur.execute("update jobs.job set kind='agent', base_ref=%s where id=%s", (base, jid))
        c.commit()
    job = engine.claim(as_="cc", env="host")
    agent_runner.run_agent_job(job, env="host", agent_cmd=agent_cmd or FAKE)
    assert engine.get_job(disp)["status"] == "awaiting_promotion"
    return _sha(f"refs/heads/job/{disp}")


def _promotion_states(disp):
    return [g["state"] for g in engine.gates_for(disp) if g["gate_type"] == "promotion"]


def test_promote_merges_to_base(promo_env):
    base, created, runs, _, _ = promo_env
    tip = _run_to_awaiting("p-ok", base, created)
    old_base = _sha(f"refs/heads/{base}")
    new = engine.promote("p-ok", by="tester")
    # base advanced to a real no-ff MERGE commit of the reviewed branch
    assert _sha(f"refs/heads/{base}") == new
    assert _sha(f"{base}^1") == old_base       # first parent = old base (no history rewrite)
    assert _sha(f"{base}^2") == tip            # second parent = the agent branch tip
    # job + gate closed; branch + worktree removed
    assert engine.get_job("p-ok")["status"] == "succeeded"
    assert _promotion_states("p-ok") == ["approved"]
    assert engine._ref_sha(REPO, "refs/heads/job/p-ok") is None
    assert not os.path.exists(os.path.join(runs, "p-ok"))


def test_promote_refuses_protected_base(promo_env):
    base, created, runs, _, _ = promo_env
    _run_to_awaiting("p-prot", base, created)
    _set_base_ref("p-prot", "main")
    main_before = engine._ref_sha(REPO, "refs/heads/main")
    with pytest.raises(engine.PromoteRefused):
        engine.promote("p-prot")
    # firewall held: job still parked, gate still pending, main untouched, no temp worktree
    assert engine.get_job("p-prot")["status"] == "awaiting_promotion"
    assert _promotion_states("p-prot") == ["pending"]
    assert engine._ref_sha(REPO, "refs/heads/main") == main_before
    assert not any("apex-promote-" in ln for ln in _git("worktree", "list").stdout.splitlines())


def test_promote_refuses_checked_out_base(promo_env, tmp_path):
    base, created, runs, extra_wt, extra_br = promo_env
    _run_to_awaiting("p-co", base, created)
    co = f"co-{os.path.basename(str(tmp_path))}"
    co_wt = str(tmp_path / "co_wt")
    _git("worktree", "add", "-b", co, co_wt, "HEAD")
    extra_wt.append(co_wt)
    extra_br.append(co)
    _set_base_ref("p-co", co)
    before = _sha(f"refs/heads/{co}")
    with pytest.raises(engine.PromoteRefused):
        engine.promote("p-co")
    assert _sha(f"refs/heads/{co}") == before
    assert engine.get_job("p-co")["status"] == "awaiting_promotion"


def test_promote_refuses_null_base(promo_env):
    base, created, runs, _, _ = promo_env
    _run_to_awaiting("p-null", base, created)
    _set_base_ref("p-null", None)
    with pytest.raises(engine.PromoteRefused):
        engine.promote("p-null")
    assert engine.get_job("p-null")["status"] == "awaiting_promotion"


def test_promote_conflict_aborts(promo_env, tmp_path):
    base, created, runs, extra_wt, _ = promo_env
    _run_to_awaiting("p-conf", base, created)             # branch adds AGENT_OUTPUT.md
    # add a CONFLICTING AGENT_OUTPUT.md onto base via a throwaway worktree
    cwt = str(tmp_path / "conf_wt")
    _git("worktree", "add", cwt, base)
    extra_wt.append(cwt)
    pathlib.Path(cwt, "AGENT_OUTPUT.md").write_text("CONFLICTING\n")
    _git("add", "-A", cwd=cwt)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "conflict", cwd=cwt)
    _git("worktree", "remove", "--force", cwt, check=False)   # base no longer checked out
    base_before = _sha(f"refs/heads/{base}")
    with pytest.raises(engine.PromoteConflict):
        engine.promote("p-conf")
    # base untouched, branch retained, job re-promotable, no temp worktree leaked
    assert _sha(f"refs/heads/{base}") == base_before
    assert engine._ref_sha(REPO, "refs/heads/job/p-conf") is not None
    assert engine.get_job("p-conf")["status"] == "awaiting_promotion"
    assert _promotion_states("p-conf") == ["pending"]
    assert not any("apex-promote-" in ln for ln in _git("worktree", "list").stdout.splitlines())


def test_promote_already_merged_preserves_branch(promo_env):
    base, created, runs, _, _ = promo_env
    tip = _run_to_awaiting("p-noop", base, created)
    _git("update-ref", f"refs/heads/{base}", tip)         # fast-forward base over the branch
    base_before = _sha(f"refs/heads/{base}")
    with pytest.raises(engine.PromoteNoChanges):
        engine.promote("p-noop")
    # nothing-to-merge must NOT silently delete the branch
    assert engine._ref_sha(REPO, "refs/heads/job/p-noop") == tip
    assert _sha(f"refs/heads/{base}") == base_before
    assert engine.get_job("p-noop")["status"] == "awaiting_promotion"


def test_promote_double_is_refused(promo_env):
    base, created, runs, _, _ = promo_env
    _run_to_awaiting("p-dbl", base, created)
    engine.promote("p-dbl")
    after = _sha(f"refs/heads/{base}")
    with pytest.raises(engine.PromoteRefused):
        engine.promote("p-dbl")               # already succeeded / branch gone -> refused
    assert _sha(f"refs/heads/{base}") == after
    assert engine.get_job("p-dbl")["status"] == "succeeded"


def test_promote_after_discard_is_refused(promo_env):
    base, created, runs, _, _ = promo_env
    _run_to_awaiting("p-pad", base, created)
    base_before = _sha(f"refs/heads/{base}")
    engine.discard_promotion("p-pad")
    with pytest.raises(engine.PromoteRefused):
        engine.promote("p-pad")               # must NOT merge rejected work into base
    assert _sha(f"refs/heads/{base}") == base_before
    assert engine.get_job("p-pad")["status"] == "cancelled"


def test_promote_compare_and_swap_guards_base(promo_env, monkeypatch):
    base, created, runs, _, _ = promo_env
    _run_to_awaiting("p-cas", base, created)
    orig = engine._advance_base_ref

    def racing(repo, b, newsha, oldsha):
        # simulate a concurrent advance of base AFTER promote captured oldsha
        concurrent = _git("commit-tree", f"{b}^{{tree}}", "-p", b, "-m", "concurrent",
                          cwd=repo).stdout.strip()
        _git("update-ref", f"refs/heads/{b}", concurrent, cwd=repo)
        return orig(repo, b, newsha, oldsha)   # CAS with the now-stale oldsha -> fails

    monkeypatch.setattr(engine, "_advance_base_ref", racing)
    with pytest.raises(engine.PromoteConflict):
        engine.promote("p-cas")
    # the concurrent commit survived (not clobbered); job stays re-promotable
    assert _git("log", "-1", "--format=%s", base).stdout.strip() == "concurrent"
    assert engine.get_job("p-cas")["status"] == "awaiting_promotion"
    assert engine._ref_sha(REPO, "refs/heads/job/p-cas") is not None


def test_discard_promotion(promo_env):
    base, created, runs, _, _ = promo_env
    tip = _run_to_awaiting("p-disc", base, created)
    base_before = _sha(f"refs/heads/{base}")
    saved = engine.discard_promotion("p-disc", by="tester")
    assert engine.get_job("p-disc")["status"] == "cancelled"
    assert _promotion_states("p-disc") == ["rejected"]
    assert _sha(f"refs/heads/{base}") == base_before               # base untouched
    assert engine._ref_sha(REPO, "refs/heads/job/p-disc") is None  # branch removed
    assert not os.path.exists(os.path.join(runs, "p-disc"))        # worktree removed
    # the agent work is recoverable from the snapshot ref
    assert saved == tip
    assert engine._ref_sha(REPO, "refs/discarded/p-disc") == tip


def test_run_once_dispatches_agent_jobs(promo_env):
    base, created, runs, _, _ = promo_env
    created.append("w-agent")
    jid = engine.enqueue(dispatch_id="w-agent", title="agent", env_required="host",
                         payload={"prompt": "x"})
    with engine._conn() as c:
        with c.cursor() as cur:
            cur.execute("update jobs.job set kind='agent', base_ref=%s where id=%s", (base, jid))
        c.commit()
    sentinel = {"job": "w-agent", "status": "succeeded"}
    with mock.patch.object(agent_runner, "run_agent_job", return_value=sentinel) as m_agent, \
         mock.patch.object(worker, "_run_command_job") as m_cmd:
        out = worker.run_once(as_="cc", env="host")
    assert out is sentinel
    assert m_agent.called and not m_cmd.called


def test_run_once_dispatches_command_jobs(promo_env):
    base, created, runs, _, _ = promo_env
    engine.enqueue(dispatch_id="w-cmd", title="cmd", env_required="host",
                   payload={"command": "true"})
    with mock.patch.object(agent_runner, "run_agent_job") as m_agent:
        out = worker.run_once(as_="cc", env="host")
    assert out["job"] == "w-cmd" and out["status"] == "succeeded"
    assert not m_agent.called


def test_promote_uses_shared_worktree_lock(promo_env, monkeypatch):
    base, created, runs, _, _ = promo_env
    _run_to_awaiting("p-lock", base, created)
    real = threading.Lock()
    calls = []

    class TrackLock:
        def __enter__(self):
            calls.append(1)
            real.acquire()
            return self

        def __exit__(self, *a):
            real.release()
            return False

    monkeypatch.setattr(agent_runner, "_WORKTREE_LOCK", TrackLock())
    engine.promote("p-lock")
    assert calls   # promote acquired agent_runner._WORKTREE_LOCK (the shared object), not a private lock
