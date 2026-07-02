import psycopg
from ops_intake.envelope import create_run
from ops_intake.approve import approve_run, materialize
from ops_intake.catalog import resolve_models

def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute("insert into ops.persons (display_name) values ('Lead') returning person_id").fetchone()[0]

def test_approve_materializes_tasks_and_freezes(mini_workbook, clean_ops, admin_dsn):
    dsn = clean_ops; who = _person(admin_dsn)
    r = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    approve_run(dsn, r["run_id"], approved_by=who)
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.tasks where legacy_source_id is not null").fetchone()[0] >= 1
        assert c.execute("select count(*) from ops.apparatus where task_id is not null").fetchone()[0] >= 1
        assert c.execute("select bool_and(is_frozen) from ops.scope_quote").fetchone()[0] is True
        assert c.execute("select status from ops.intake_runs where id=%s",(r["run_id"],)).fetchone()[0]=="approved"
    # standard_hours: D4 "no catalog write" - the writer holds NO grant on this table at all
    # (spec S5: dropped over-grant), so this verification read runs as admin, not the writer.
    with psycopg.connect(admin_dsn) as c:
        assert c.execute("select count(*) from ops.standard_hours").fetchone()[0] == 0  # D4: no catalog write

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

def test_recognized_then_reversed_still_blocks(mini_workbook, clean_ops, admin_dsn, api_dsn):
    """recognized -> fully reversed (net 0) -> re-intake still revision_blocked/recognized (EXISTS, not net)."""
    dsn = clean_ops; who = _person(admin_dsn)
    r = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    approve_run(dsn, r["run_id"], approved_by=who)
    with psycopg.connect(dsn, autocommit=True) as c:
        # pick an apparatus that provably satisfies EVERY attest-eligibility gate, so the
        # sanctioned attest fn (T2 guard path) cannot fail on a hidden ineligibility.
        aid = c.execute(
            "select a.id from ops.apparatus a"
            " join ops.scopes s   on s.id = a.scope_id"
            " join ops.projects p on p.id = s.project_id"
            " join ops.scope_quote sq on sq.scope_id = a.scope_id"
            " where a.provenance_status='approved' and a.is_active"
            "   and a.status not in ('Complete','Cancelled')"
            "   and a.quoted_hours > 0 and a.quoted_revenue > 0"
            "   and s.is_active and s.status <> 'Cancelled'"
            "   and p.is_active and p.status <> 'Cancelled'"
            "   and sq.is_frozen and sq.frozen_at is not null"
            " limit 1"
        ).fetchone()[0]
        # assert the eligibility preconditions explicitly (fail loudly here, not inside attest).
        prov, st, qh, qr, frozen = c.execute(
            "select a.provenance_status, a.status, a.quoted_hours, a.quoted_revenue, sq.is_frozen"
            " from ops.apparatus a join ops.scope_quote sq on sq.scope_id=a.scope_id"
            " where a.id=%s", (aid,)).fetchone()
        assert prov == 'approved' and st not in ('Complete','Cancelled') and qh > 0 and qr > 0 and frozen
    # `who` is the approve_run actor; ensure it is a known ops.persons row (attest gate 1).
    # ops.persons SELECT is a dropped over-grant for login roles (spec S5: RI + the DEFINER
    # attest fn read persons AS OWNER; login roles never need it) - verify as admin.
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        assert c.execute("select 1 from ops.persons where person_id=%s", (who,)).fetchone() is not None
    # The 3 recognition fns are EXECUTE-granted to ops_api ONLY (writer is denied) - behavior
    # runs on api_dsn (a fresh connection; aid/who/ev are plain Python values, not tied to `c`).
    with psycopg.connect(api_dsn, autocommit=True) as c:
        c.execute("select ops.attest_apparatus_complete(%s,%s,'tested')", (aid, who))  # sanctioned status=Complete (T2 guard)
        ev = c.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
                       (aid, who)).fetchone()[0]
        c.execute("select ops.reverse_recognition(%s,%s,'correction')", (ev, who))  # confirm arg order vs 005
    out = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    assert out["conflict_kind"] == "recognized" and out["status"] == "revision_blocked"


def test_reapprove_after_recognition_hits_approve_time_toctou(mini_workbook, clean_ops, admin_dsn, api_dsn):
    """F-012-4: the approve-time conflict re-check at approve.py:241 is a LIVE re-check
    (ops._conflict_kind under the held project/apparatus locks), independent of the
    conflict_kind stored on the run row at create_run time. test_recognized_then_reversed_
    still_blocks (above) only proves envelope-time (create_run) blocking -- create_run's own
    _classify_conflict pre-marks a NEW run status='revision_blocked' the moment a conflict
    already exists, so approve_run never reaches its OWN re-check in that flow.

    To genuinely exercise approve.py:241 this seeds round 2's intake_run directly (admin
    INSERT, status='parsed', conflict_kind='none') -- bypassing create_run's own
    classification -- so approve_run's line-209/212 gates pass and its LIVE re-check at
    line 241 is what fires. Reuses round 1's own stored payload JSON (valid by construction:
    it already materialized once) since the TOCTOU return happens before the payload is
    read for materialization.
    """
    dsn = clean_ops
    who = _person(admin_dsn)
    r1 = create_run(dsn, uploaded_by=who, filename="m.xlsm",
                     raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    out1 = approve_run(dsn, r1["run_id"], approved_by=who)
    assert out1["outcome"] == "approved"

    with psycopg.connect(admin_dsn, autocommit=True) as c:
        project_number, canonical_json, review_json, review_version = c.execute(
            "select project_number, canonical_payload_json, review_payload_json,"
            " review_payload_version from ops.intake_runs where id=%s",
            (r1["run_id"],),
        ).fetchone()
        # eligible apparatus for attest (same gates as test_recognized_then_reversed_still_blocks)
        aid = c.execute(
            "select a.id from ops.apparatus a"
            " join ops.scopes s   on s.id = a.scope_id"
            " join ops.projects p on p.id = s.project_id"
            " join ops.scope_quote sq on sq.scope_id = a.scope_id"
            " where a.provenance_status='approved' and a.is_active"
            "   and a.status not in ('Complete','Cancelled')"
            "   and a.quoted_hours > 0 and a.quoted_revenue > 0"
            "   and s.is_active and s.status <> 'Cancelled'"
            "   and p.is_active and p.status <> 'Cancelled'"
            "   and sq.is_frozen and sq.frozen_at is not null"
            " limit 1"
        ).fetchone()[0]

    # attest + recognize as api_dsn (the 3 recognition fns are EXECUTE-granted to ops_api
    # only) -- this creates the live ops.revenue_recognition_event row that _conflict_kind
    # will see. Do NOT reverse it this time (must still conflict when approve_run re-checks).
    with psycopg.connect(api_dsn, autocommit=True) as c:
        c.execute("select ops.attest_apparatus_complete(%s,%s,'tested')", (aid, who))
        c.execute(
            "select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
            (aid, who),
        )

    # Seed round 2's intake_run directly (admin), status='parsed'/conflict_kind='none' --
    # bypassing create_run's own _classify_conflict so approve_run's line-209/212 gates let
    # it through to the live re-check at line 241.
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        run2_id = c.execute(
            "insert into ops.intake_runs (project_number, project_id, source_format, status,"
            " conflict_kind, payload_schema_version, parser_version, canonical_payload_json,"
            " review_payload_json, review_payload_version, uploaded_by)"
            " select project_number, project_id, source_format, 'parsed'::ops.intake_run_status,"
            " 'none'::ops.intake_conflict_kind, payload_schema_version, parser_version,"
            " canonical_payload_json, review_payload_json, review_payload_version, uploaded_by"
            " from ops.intake_runs where id=%s returning id",
            (r1["run_id"],),
        ).fetchone()[0]

    out2 = approve_run(dsn, run2_id, approved_by=who)
    assert out2["outcome"] == "revision_blocked", out2
    assert out2["conflict_kind"] == "recognized", out2
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        status = c.execute(
            "select status from ops.intake_runs where id=%s", (run2_id,)
        ).fetchone()[0]
        assert status == "revision_blocked"  # the TOCTOU re-check persisted the block


def test_approve_refuses_foreign_source_project(clean_ops, admin_dsn):
    """A project bearing a non-ops-intake scope (legacy Miner rows) must be REFUSED by approve
    (outcome 'foreign_source') with NO scopes deleted -- so delete-by-marker can never orphan
    foreign rows. (operator missing-coverage: foreign-source refusal)"""
    import pathlib
    import tempfile

    from fixtures.build_fixture import build

    dsn = clean_ops
    who = _person(admin_dsn)
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


def test_two_projects_share_line_uid_no_apparatus_key_collision(clean_ops, admin_dsn):
    """Two DIFFERENT projects whose lines share a line_uid must BOTH materialize -- apparatus
    legacy_source_id is project-qualified (f'{project_number}:{line_uid}:u{i}'), so the GLOBALLY
    unique uq_ops_apparatus_intake does not collide. (operator missing-coverage: two-project key)"""
    import pathlib
    import tempfile

    from fixtures.build_fixture import build

    dsn = clean_ops
    who = _person(admin_dsn)
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
