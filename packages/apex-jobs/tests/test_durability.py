"""TDD — durability engine: env-filtered claim + status-lifecycle closure
(approve -> pending, unblock). No agent/runner here; pure queue logic."""
from apex_jobs import engine


def test_claim_env_filter(conn_test):
    engine.enqueue(dispatch_id="d-host", title="host job", env_required="host", priority=10)
    engine.enqueue(dispatch_id="d-any", title="any job", env_required="any", priority=20)
    # a sandbox worker must skip the host-only job and get the 'any' job
    j = engine.claim(as_="cc", env="sandbox")
    assert j is not None and j["dispatch_id"] == "d-any", j
    # the host job stays unclaimed for a sandbox worker
    assert engine.claim(as_="cc", env="sandbox") is None
    # a host worker can claim it
    j2 = engine.claim(as_="cc", env="host")
    assert j2 is not None and j2["dispatch_id"] == "d-host", j2


def test_claim_env_none_no_filter(conn_test):
    # env=None imposes no restriction (claims regardless of env_required)
    engine.enqueue(dispatch_id="d-h", title="h", env_required="host")
    j = engine.claim(as_="cc", env=None)
    assert j is not None and j["dispatch_id"] == "d-h", j


def test_approve_returns_awaiting_approval_to_pending(conn_test):
    jid = engine.enqueue(dispatch_id="d-aa", title="parked", env_required="any")
    gid = engine.request_gate(jid, "schema")
    # simulate start() having parked it awaiting_approval behind the open gate
    conn_test.execute("update jobs.job set status='awaiting_approval' where id=%s", (jid,))
    assert engine.claim(as_="cc", env="host") is None        # parked + gated -> not claimable
    engine.approve(gid, by="operator")
    j = engine.claim(as_="cc", env="host")                   # closure -> pending -> claimable
    assert j is not None and j["dispatch_id"] == "d-aa", j


def test_approve_keeps_awaiting_promotion(conn_test):
    # the closure must NOT touch awaiting_promotion jobs (they flow to promote(), not pending)
    jid = engine.enqueue(dispatch_id="d-ap", title="promo", env_required="any")
    gid = engine.request_gate(jid, "promotion")
    conn_test.execute("update jobs.job set status='awaiting_promotion' where id=%s", (jid,))
    engine.approve(gid, by="operator")
    assert engine.get_job("d-ap")["status"] == "awaiting_promotion"


def test_unblock(conn_test):
    jid = engine.enqueue(dispatch_id="d-blk", title="blocked", env_required="host")
    conn_test.execute("update jobs.job set status='blocked' where id=%s", (jid,))
    assert engine.claim(as_="cc", env="host") is None        # blocked not eligible
    assert engine.unblock("d-blk") is not None
    j = engine.claim(as_="cc", env="host")
    assert j is not None and j["dispatch_id"] == "d-blk", j


def test_start_stamps_lease(conn_test):
    engine.enqueue(dispatch_id="d-lease", title="x", env_required="host")
    j = engine.claim(as_="cc", env="host")
    run_id = engine.start(j["id"], claimed_by="cc", run_env="host")
    row = conn_test.execute(
        "select lease_expires_at, heartbeat_at, lease_expires_at > now() "
        "from jobs.run where id=%s", (run_id,)).fetchone()
    assert row[0] is not None and row[1] is not None      # lease + heartbeat stamped
    assert row[2] is True                                  # lease is in the future


def test_heartbeat_extends_lease(conn_test):
    engine.enqueue(dispatch_id="d-hb", title="x", env_required="host")
    j = engine.claim(as_="cc", env="host")
    run_id = engine.start(j["id"], claimed_by="cc", run_env="host")
    before = conn_test.execute(
        "select lease_expires_at from jobs.run where id=%s", (run_id,)).fetchone()[0]
    engine.heartbeat(run_id, lease_ttl_s=7200)            # longer than the default 1800
    after = conn_test.execute(
        "select lease_expires_at from jobs.run where id=%s", (run_id,)).fetchone()[0]
    assert after > before


def test_reaper_requeues_then_fails(conn_test):
    jid = engine.enqueue(dispatch_id="d-reap", title="x", env_required="host")
    conn_test.execute("update jobs.job set max_attempts=2 where id=%s", (jid,))
    # attempt 1: claim + start, then force the lease expired -> reap requeues
    j = engine.claim(as_="cc", env="host")
    r1 = engine.start(j["id"], claimed_by="cc", run_env="host")
    conn_test.execute("update jobs.run set lease_expires_at = now() - interval '1 min' "
                      "where id=%s", (r1,))
    assert engine.reap() >= 1
    assert conn_test.execute("select status from jobs.run where id=%s",
                             (r1,)).fetchone()[0] == "failed"
    assert engine.get_job("d-reap")["status"] == "pending"     # budget left -> requeued
    # attempt 2: same again -> budget exhausted -> job terminal failed
    j2 = engine.claim(as_="cc", env="host")
    r2 = engine.start(j2["id"], claimed_by="cc", run_env="host")
    conn_test.execute("update jobs.run set lease_expires_at = now() - interval '1 min' "
                      "where id=%s", (r2,))
    engine.reap()
    assert engine.get_job("d-reap")["status"] == "failed"      # budget exhausted
