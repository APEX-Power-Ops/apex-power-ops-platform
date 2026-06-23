import psycopg
from ops_intake.envelope import create_run
from ops_intake.approve import approve_run, materialize
from ops_intake.catalog import resolve_models

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
    dsn = clean_ops
    _MODEL_KEY = "Capcitors - Per Unit"
    line  = {"apparatus_type":_MODEL_KEY,"test_standard":"ATS","qty":2,"hrs_per_unit":2.0,
             "section":"S1","line_number":1,"line_uid":"A:row1"}
    scope = {"scope_name":"A","legacy_source_id":"A",
             "quote":{"onsite_labor":1000,"unit_multiplier":1,"pct_adjust":1,"total_quoted_hours":4},
             "lines":[line]}
    payload = {"project":{"project_number":"FR-1","project_name":"N","contract_value":1000.0}, "scopes":[scope]}
    with psycopg.connect(dsn) as c:
        pid = c.execute("insert into ops.projects (project_number,project_name,source) "
                        "values ('OTHER','o','manual') returning id").fetchone()[0]
        c.execute("insert into ops.scopes (project_id,scope_name,source) values (%s,'keep','manual')", (pid,))  # FOREIGN
        resolved = resolve_models(c.cursor(), [_MODEL_KEY])
        materialize(c, "FR-1", payload, resolved); c.commit()
        counts = lambda: {t: c.execute(f"select count(*) from ops.{t}").fetchone()[0]
                          for t in ("scope_quote","scope_quote_line","tasks","apparatus")}
        before = counts()
        materialize(c, "FR-1", {**payload, "scopes": []}, {}); c.commit()                       # drop the WHOLE scope
        after = counts()
        intake_scopes = c.execute("select count(*) from ops.scopes where source='ops-intake'").fetchone()[0]
        foreign       = c.execute("select count(*) from ops.scopes where source='manual'").fetchone()[0]
    assert before["apparatus"] == 2 and before["tasks"] >= 1
    assert intake_scopes == 0 and all(v == 0 for v in after.values())   # every intake child gone, zero orphans
    assert foreign == 1                                                  # the foreign scope was never touched

def test_null_section_lines_are_idempotent(clean_ops):
    """Lines with section=None get a deterministic __ungrouped__ task; re-materialize does not grow tasks."""
    dsn = clean_ops
    _MODEL_KEY = "Capcitors - Per Unit"
    scope = {"scope_name":"A","legacy_source_id":"A",
             "quote":{"onsite_labor":1000,"unit_multiplier":1,"pct_adjust":1,"total_quoted_hours":2},
             "lines":[{"apparatus_type":_MODEL_KEY,"test_standard":"ATS","qty":1,"hrs_per_unit":2.0,
                       "section":None,"line_number":1,"line_uid":"A:row1"}]}
    payload = {"project":{"project_number":"NS-1","project_name":"N","contract_value":1000.0}, "scopes":[scope]}
    with psycopg.connect(dsn) as c:
        resolved = resolve_models(c.cursor(), [_MODEL_KEY])
        materialize(c, "NS-1", payload, resolved); c.commit()
        t1 = c.execute("select count(*) from ops.tasks").fetchone()[0]
        materialize(c, "NS-1", payload, resolved); c.commit()
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


def test_approve_refuses_foreign_source_project(clean_ops):
    """A project bearing a non-ops-intake scope (legacy Miner rows) must be REFUSED by approve
    (outcome 'foreign_source') with NO scopes deleted -- so delete-by-marker can never orphan
    foreign rows. (operator missing-coverage: foreign-source refusal)"""
    import pathlib
    import tempfile

    from fixtures.build_fixture import build

    dsn = clean_ops
    who = _person(dsn)
    # Seed a project "FS-1" carrying a FOREIGN (non-ops-intake) scope.
    with psycopg.connect(dsn, autocommit=True) as c:
        pid = c.execute(
            "insert into ops.projects (project_number, project_name, source) "
            "values ('FS-1','Foreign','manual') returning id"
        ).fetchone()[0]
        c.execute(
            "insert into ops.scopes (project_id, scope_name, source) values (%s,'legacy',%s)",
            (pid, "miner_rev10.xlsm"),
        )
    # An intake workbook whose Job# == FS-1 (so the run targets the foreign-bearing project).
    wb = build(pathlib.Path(tempfile.mkdtemp()) / "fs.xlsx", job_number="FS-1")
    r = create_run(dsn, uploaded_by=who, filename="fs.xlsm",
                   raw_bytes=wb.read_bytes(), content_type="xlsm")
    out = approve_run(dsn, r["run_id"], approved_by=who)
    assert out["outcome"] == "foreign_source"
    with psycopg.connect(dsn) as c:
        assert c.execute(
            "select count(*) from ops.scopes where source='miner_rev10.xlsm'"
        ).fetchone()[0] == 1  # the foreign scope survived
        assert c.execute(
            "select count(*) from ops.scopes where source='ops-intake'"
        ).fetchone()[0] == 0  # nothing materialized


def test_two_projects_share_line_uid_no_apparatus_key_collision(clean_ops):
    """Two DIFFERENT projects whose lines share a line_uid must BOTH materialize -- apparatus
    legacy_source_id is project-qualified (f'{project_number}:{line_uid}:u{i}'), so the GLOBALLY
    unique uq_ops_apparatus_intake does not collide. (operator missing-coverage: two-project key)"""
    import pathlib
    import tempfile

    from fixtures.build_fixture import build

    dsn = clean_ops
    who = _person(dsn)
    d = pathlib.Path(tempfile.mkdtemp())
    # Same default scope_name -> identical line_uids (e.g. "A1) MV - Test:row8") across both projects.
    a = build(d / "a.xlsx", job_number="P-AAA")
    b = build(d / "b.xlsx", job_number="P-BBB")
    ra = create_run(dsn, uploaded_by=who, filename="a.xlsm", raw_bytes=a.read_bytes(), content_type="xlsm")
    approve_run(dsn, ra["run_id"], approved_by=who)
    rb = create_run(dsn, uploaded_by=who, filename="b.xlsm", raw_bytes=b.read_bytes(), content_type="xlsm")
    approve_run(dsn, rb["run_id"], approved_by=who)
    with psycopg.connect(dsn) as c:
        for pn in ("P-AAA", "P-BBB"):
            n = c.execute(
                "select count(*) from ops.apparatus a "
                "join ops.scopes s on s.id = a.scope_id "
                "join ops.projects p on p.id = s.project_id "
                "where p.project_number = %s",
                (pn,),
            ).fetchone()[0]
            assert n >= 1, pn  # both projects materialized apparatus despite shared line_uids
