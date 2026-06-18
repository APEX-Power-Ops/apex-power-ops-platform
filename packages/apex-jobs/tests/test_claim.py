"""TDD - atomic claim (FOR UPDATE SKIP LOCKED) + predecessor gating."""
import threading

from apex_jobs.engine import claim, enqueue, get_job


def test_claim_marks_claimed(conn_test):
    enqueue(dispatch_id="c-1", title="x")
    job = claim(as_="cc")
    assert job is not None and job["dispatch_id"] == "c-1"
    assert get_job("c-1")["status"] == "claimed"
    assert claim(as_="cc") is None  # nothing eligible left


def test_atomic_claim_no_double(conn_test):
    enqueue(dispatch_id="c-only", title="x")
    results = {}
    barrier = threading.Barrier(2)

    def worker(i):
        barrier.wait()
        results[i] = claim(as_=f"w{i}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in (0, 1)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    got = [r for r in results.values() if r is not None]
    assert len(got) == 1, results


def test_predecessor_blocks(conn_test):
    a = enqueue(dispatch_id="p-a", title="a")
    enqueue(dispatch_id="p-b", title="b", predecessor_id=a)
    first = claim(as_="cc")
    assert first["dispatch_id"] == "p-a"
    assert claim(as_="cc") is None  # p-b blocked: p-a only 'claimed', not 'succeeded'
    conn_test.execute("update jobs.job set status='succeeded' where dispatch_id='p-a'")
    nxt = claim(as_="cc")
    assert nxt is not None and nxt["dispatch_id"] == "p-b"
