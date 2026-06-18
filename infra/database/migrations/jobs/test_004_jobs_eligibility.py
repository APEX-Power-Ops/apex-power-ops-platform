"""TDD - jobs.v_eligible claim-eligibility view (status/predecessor/gate/order)."""
from _dbtest import connect, psql_file

APPLY = ["001_jobs_enums.sql", "002_jobs_tables.sql",
         "003_jobs_indexes.sql", "004_jobs_views.sql"]
DOWN = ["004_jobs_views_down.sql", "003_jobs_indexes_down.sql",
        "002_jobs_tables_down.sql", "001_jobs_enums_down.sql"]


def _reset_up():
    for f in DOWN:
        try:
            psql_file(f)
        except Exception:
            pass
    for f in APPLY:
        psql_file(f)


def _ins(c, dispatch_id, **kw):
    cols = ["dispatch_id", "title"]
    vals = [dispatch_id, dispatch_id]
    for k, v in kw.items():
        cols.append(k)
        vals.append(v)
    ph = ",".join(["%s"] * len(vals))
    q = f"insert into jobs.job ({','.join(cols)}) values ({ph}) returning id"
    return c.execute(q, vals).fetchone()[0]


def _elig(c):
    return [r[0] for r in c.execute("select dispatch_id from jobs.v_eligible").fetchall()]


def test_basic_and_status_exclusions():
    _reset_up()
    with connect() as c:
        _ins(c, "j-a", priority=50)
        _ins(c, "j-claimed", status="claimed")
        _ins(c, "j-done", status="succeeded")
        e = _elig(c)
        assert "j-a" in e
        assert "j-claimed" not in e and "j-done" not in e


def test_predecessor_gate():
    _reset_up()
    with connect() as c:
        pred = _ins(c, "j-pred", status="pending")
        _ins(c, "j-child", predecessor_id=pred)
        assert "j-child" not in _elig(c)
        c.execute("update jobs.job set status='succeeded' where id=%s", (pred,))
        assert "j-child" in _elig(c)


def test_open_gate_blocks():
    _reset_up()
    with connect() as c:
        j = _ins(c, "j-gated", requires_approval=True)
        c.execute("insert into jobs.gate (job_id, gate_type) values (%s, 'schema')", (j,))
        assert "j-gated" not in _elig(c)
        c.execute("update jobs.gate set state='approved' where job_id=%s", (j,))
        assert "j-gated" in _elig(c)


def test_order_priority_then_dispatch():
    _reset_up()
    with connect() as c:
        _ins(c, "b-low", priority=10)
        _ins(c, "a-low", priority=10)
        _ins(c, "z-high", priority=200)
        assert _elig(c) == ["a-low", "b-low", "z-high"]
