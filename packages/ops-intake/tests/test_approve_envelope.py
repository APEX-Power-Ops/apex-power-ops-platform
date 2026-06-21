import psycopg
from ops_intake.envelope import create_run
from ops_intake.approve import approve_run

def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute("insert into ops.persons (display_name) values ('Lead') returning person_id").fetchone()[0]

def test_approve_materializes_tasks_and_freezes(mini_workbook, clean_ops):
    dsn = clean_ops; who = _person(dsn)
    r = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    approve_run(dsn, r["run_id"], approved_by=who)
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.tasks where legacy_source_id is not null").fetchone()[0] >= 1
        assert c.execute("select count(*) from ops.apparatus where task_id is not null").fetchone()[0] >= 1
        assert c.execute("select bool_and(is_frozen) from ops.scope_quote").fetchone()[0] is True
        assert c.execute("select count(*) from ops.standard_hours").fetchone()[0] == 0  # D4: no catalog write
        assert c.execute("select status from ops.intake_runs where id=%s",(r["run_id"],)).fetchone()[0]=="approved"

def test_materialize_full_replacement_removes_all_children_and_spares_foreign(clean_ops):
    """Full replacement removes ALL intake-owned children via the source='ops-intake' scope cascade; foreign rows survive."""
    from ops_intake.approve import materialize
    dsn = clean_ops
    line  = {"apparatus_type":"X","test_standard":"ATS","qty":2,"hrs_per_unit":2.0,
             "section":"S1","line_number":1,"line_uid":"A:row1"}
    scope = {"scope_name":"A","legacy_source_id":"A",
             "quote":{"onsite_labor":1000,"unit_multiplier":1,"pct_adjust":1,"total_quoted_hours":4},
             "lines":[line]}
    payload = {"project":{"project_number":"FR-1","project_name":"N","contract_value":1000.0}, "scopes":[scope]}
    with psycopg.connect(dsn) as c:
        pid = c.execute("insert into ops.projects (project_number,project_name,source) "
                        "values ('OTHER','o','manual') returning id").fetchone()[0]
        c.execute("insert into ops.scopes (project_id,scope_name,source) values (%s,'keep','manual')", (pid,))  # FOREIGN
        materialize(c, "FR-1", payload); c.commit()
        counts = lambda: {t: c.execute(f"select count(*) from ops.{t}").fetchone()[0]
                          for t in ("scope_quote","scope_quote_line","tasks","apparatus")}
        before = counts()
        materialize(c, "FR-1", {**payload, "scopes": []}); c.commit()                       # drop the WHOLE scope
        after = counts()
        intake_scopes = c.execute("select count(*) from ops.scopes where source='ops-intake'").fetchone()[0]
        foreign       = c.execute("select count(*) from ops.scopes where source='manual'").fetchone()[0]
    assert before["apparatus"] == 2 and before["tasks"] >= 1
    assert intake_scopes == 0 and all(v == 0 for v in after.values())   # every intake child gone, zero orphans
    assert foreign == 1                                                  # the foreign scope was never touched

def test_null_section_lines_are_idempotent(clean_ops):
    """Lines with section=None get a deterministic __ungrouped__ task; re-materialize does not grow tasks."""
    from ops_intake.approve import materialize
    dsn = clean_ops
    scope = {"scope_name":"A","legacy_source_id":"A",
             "quote":{"onsite_labor":1000,"unit_multiplier":1,"pct_adjust":1,"total_quoted_hours":2},
             "lines":[{"apparatus_type":"X","test_standard":"ATS","qty":1,"hrs_per_unit":2.0,
                       "section":None,"line_number":1,"line_uid":"A:row1"}]}
    payload = {"project":{"project_number":"NS-1","project_name":"N","contract_value":1000.0}, "scopes":[scope]}
    with psycopg.connect(dsn) as c:
        materialize(c, "NS-1", payload); c.commit()
        t1 = c.execute("select count(*) from ops.tasks").fetchone()[0]
        materialize(c, "NS-1", payload); c.commit()
        t2 = c.execute("select count(*) from ops.tasks").fetchone()[0]
    assert t1 == 1 and t2 == 1   # exactly one __ungrouped__ task, not duplicated on re-approve

def test_recognized_then_reversed_still_blocks(mini_workbook, clean_ops):
    """recognized -> fully reversed (net 0) -> re-intake still revision_blocked/recognized (EXISTS, not net)."""
    dsn = clean_ops; who = _person(dsn)
    r = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    approve_run(dsn, r["run_id"], approved_by=who)
    with psycopg.connect(dsn, autocommit=True) as c:
        aid = c.execute("select id from ops.apparatus limit 1").fetchone()[0]
        c.execute("update ops.apparatus set status='Complete' where id=%s", (aid,))
        ev = c.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
                       (aid, who)).fetchone()[0]
        c.execute("select ops.reverse_recognition(%s,%s,'correction')", (ev, who))  # confirm arg order vs 005
    out = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    assert out["conflict_kind"] == "recognized" and out["status"] == "revision_blocked"
