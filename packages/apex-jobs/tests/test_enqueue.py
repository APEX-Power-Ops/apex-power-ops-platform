"""TDD - engine.enqueue + idempotency. RED until engine.py exists."""


def test_enqueue_creates_pending(conn_test):
    from apex_jobs.engine import enqueue, get_job
    jid = enqueue(dispatch_id="t-001", title="canary", payload={"command": "true"})
    j = get_job(jid)
    assert j["status"] == "pending"
    assert j["dispatch_id"] == "t-001"
    assert j["payload"] == {"command": "true"}


def test_enqueue_idempotent(conn_test):
    from apex_jobs.engine import enqueue
    a = enqueue(dispatch_id="t-002", title="x")
    b = enqueue(dispatch_id="t-002", title="x")
    assert a == b
