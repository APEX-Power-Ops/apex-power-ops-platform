"""Offline tests for the census collector (no DB, no psycopg).

Two layers, both driver-free:
  * pure state-mapping core: synthetic catalog rows -> schema-valid evidence_snapshot, with the
    observation-state semantics asserted per fact.
  * DB orchestration (_collect) driven through a FAKE cursor: read-only/target guard, query-group
    savepoint recovery, absent-role handling, deterministic dependency ordering, atomic output.

The live census (collect_from_db, which lazily imports psycopg and connects read-only to prod) is
GO-gated and NOT exercised here.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collect_disposition as cd  # noqa: E402
import disposition_signing as ds  # noqa: E402

NOW = "2026-07-11T00:00:00Z"
PROJECT = "fxoyniqnrlkxfligbxmg"
SHA = "8a4c37fc"


def _ephemeral_keypair():
    """Throwaway Ed25519 keypair for signing tests. The PRODUCTION key is generated out-of-band and
    held in Infisical (operator custody); the collector never embeds a real key."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.generate()
    priv_pem = priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    pub_pem = priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv, priv_pem, pub_pem


_MINI_SNAP = {"target_identity": {"current_database": "postgres", "current_user": "x"},
              "relation_count": 0, "query_bundle_sha256": "a" * 64}

CENSUS_COLS = ["schema", "name", "relkind", "owner", "rls_enabled", "is_security_definer_view",
               "inbound_fk_count", "outbound_fk_count", "row_estimate"]
VIEW = ("public", "v_scope_financials", "v", "postgres", False, True, 0, 0, None)
TABLE = ("public", "projects", "r", "postgres", True, None, 2, 1, 1500)

TI_DICT = {
    "current_database": "postgres", "current_user": "authenticator", "server_version": "PostgreSQL 16.13",
    "server_version_num": 160013, "transaction_read_only": True, "expected_database": "postgres",
    "platform_role_markers": ["anon", "authenticated", "service_role"], "guard_passed": True,
}
PRIVS = {"public.v_scope_financials": {"anon": ["SELECT"], "authenticated": ["SELECT"]},
         "public.projects": {"anon": [], "authenticated": ["SELECT"]}}
DEPS = {"public.projects": [
    {"object_type": "view", "identity": "public.v_scope_financials", "direction": "inbound",
     "evidence_type": "pg_depend", "evidence_ref": "query:dependents-v2", "_is_consumer": True},
    {"object_type": "constraint", "identity": "fk_a on public.scopes", "direction": "inbound",
     "evidence_type": "pg_depend", "evidence_ref": "query:dependents-v2", "_is_consumer": True},
]}


def _snap(failed=frozenset(), rows=None, now=NOW, ti=None):
    rows = rows if rows is not None else [dict(zip(CENSUS_COLS, VIEW)), dict(zip(CENSUS_COLS, TABLE))]
    return cd.build_snapshot(rows, PRIVS, DEPS, set(failed), project_ref=PROJECT, repo_sha=SHA,
                             now=now, target_identity=ti or TI_DICT)


def _rel(snap, oid):
    return next(r for r in snap["relations"] if r["object_id"] == oid)


def _dep(object_type, identity, direction="inbound", is_consumer=True):
    return {"object_type": object_type, "identity": identity, "direction": direction,
            "evidence_type": "pg_depend", "evidence_ref": "query:dependents-v2", "_is_consumer": is_consumer}


def _snap_with_deps(deps_list):
    rows = [dict(zip(CENSUS_COLS, TABLE))]
    return cd.build_snapshot(rows, {"public.projects": {"anon": [], "authenticated": []}},
                             {"public.projects": deps_list}, set(),
                             project_ref=PROJECT, repo_sha=SHA, now=NOW, target_identity=TI_DICT)


# ==== pure state-mapping core ================================================
def test_snapshot_is_schema_valid():
    s = _snap()  # build_snapshot validates internally; raises on invalid
    assert s["relation_count"] == 2 and cd._validate(s) == []
    assert s["target_identity"]["guard_passed"] is True


def test_view_is_definer_observed():
    assert _rel(_snap(), "public.v_scope_financials")["is_security_definer_view"] == {"state": "observed", "value": True}


def test_table_is_definer_not_applicable():
    assert _rel(_snap(), "public.projects")["is_security_definer_view"]["state"] == "not_applicable"


def test_row_estimate_states():
    assert _rel(_snap(), "public.v_scope_financials")["row_estimate"]["state"] == "not_applicable"
    assert _rel(_snap(), "public.projects")["row_estimate"] == {"state": "observed", "value": 1500}


def test_privileges_observed_empty_and_failed():
    # role exists, no grant -> observed EMPTY (not not_observed); group failed -> query_failed
    assert _rel(_snap(), "public.projects")["anon_effective_privs"] == {"state": "observed", "value": []}
    fq = _rel(_snap(failed={"privileges"}), "public.projects")["anon_effective_privs"]
    assert fq["state"] == "query_failed"


def test_in_data_api_exposed_is_not_observed():
    # F7: exposure is not derived authoritatively from the runtime GUC
    assert _rel(_snap(), "public.projects")["in_data_api_exposed_schema"]["state"] == "not_observed"


def test_dependents_sorted_and_database_deps():
    r = _rel(_snap(), "public.projects")
    # DEPS given view-first; emitted sorted by (object_type, identity, direction) -> constraint first
    assert [d["object_type"] for d in r["dependent_objects"]["value"]] == ["constraint", "view"]
    assert r["consumer_evidence"]["database_deps"] == {"state": "observed", "found_consumers": 2, "ref": "query:dependents-v2"}
    rf = _rel(_snap(failed={"dependents"}), "public.projects")
    assert rf["dependent_objects"]["state"] == "query_failed"
    assert rf["consumer_evidence"]["database_deps"]["state"] == "query_failed"


def test_dependents_dedup_counts_once():
    # pg_rewrite emits one pg_depend row per column reference; a duplicated edge must count once
    dup = _dep("view", "public.v_x")
    r = _rel(_snap_with_deps([dup, dict(dup)]), "public.projects")
    assert len(r["dependent_objects"]["value"]) == 1
    assert r["consumer_evidence"]["database_deps"]["found_consumers"] == 1


def test_dependents_function_and_outbound_direction():
    deps = [_dep("function", "public.f()", "inbound", is_consumer=True),
            _dep("constraint", "fk_out -> public.scopes", "outbound", is_consumer=False)]
    r = _rel(_snap_with_deps(deps), "public.projects")
    vals = r["dependent_objects"]["value"]
    assert [(v["object_type"], v["direction"]) for v in vals] == [("constraint", "outbound"), ("function", "inbound")]  # FULL inventory
    assert r["consumer_evidence"]["database_deps"]["found_consumers"] == 1  # only the function is an external consumer


def test_consumer_count_excludes_self_owned_and_outbound():
    # finding #2: owned sequences/triggers/policies and outbound FKs are inventory, not consumers
    deps = [_dep("function", "public.f()", "inbound", True),
            _dep("sequence", "public.projects_id_seq", "inbound", False),
            _dep("trigger", "trg on public.projects", "inbound", False),
            _dep("policy", "pol on public.projects", "inbound", False),
            _dep("constraint", "fk_out -> public.scopes", "outbound", False)]
    r = _rel(_snap_with_deps(deps), "public.projects")
    assert len(r["dependent_objects"]["value"]) == 5  # everything is inventoried
    assert r["consumer_evidence"]["database_deps"]["found_consumers"] == 1  # only the function counts as a consumer


def test_dependency_role_classification():
    # durable classification: every stored edge carries dependency_role derived from (direction, is_consumer)
    deps = [_dep("view", "public.v_x", "inbound", True),                 # external_consumer
            _dep("sequence", "public.projects_id_seq", "inbound", False),  # attached_object (owned)
            _dep("constraint", "fk_out -> public.scopes", "outbound", False)]  # outbound_dependency
    r = _rel(_snap_with_deps(deps), "public.projects")
    roles = {(v["object_type"], v["direction"]): v["dependency_role"] for v in r["dependent_objects"]["value"]}
    assert roles == {("view", "inbound"): "external_consumer",
                     ("sequence", "inbound"): "attached_object",
                     ("constraint", "outbound"): "outbound_dependency"}
    # role is durable; the external-consumer COUNT is unchanged (only external_consumer edges count)
    assert r["consumer_evidence"]["database_deps"]["found_consumers"] == 1
    n_ext = sum(1 for v in r["dependent_objects"]["value"] if v["dependency_role"] == "external_consumer")
    assert n_ext == r["consumer_evidence"]["database_deps"]["found_consumers"]


def test_dependency_role_or_across_duplicates():
    # pg_rewrite emits duplicate edges; if ANY twin is a consumer the stored role must be external_consumer
    dup_c = _dep("view", "public.v_dup", "inbound", True)
    dup_n = _dep("view", "public.v_dup", "inbound", False)
    r = _rel(_snap_with_deps([dup_n, dup_c]), "public.projects")  # non-consumer twin first
    vals = r["dependent_objects"]["value"]
    assert len(vals) == 1 and vals[0]["dependency_role"] == "external_consumer"


def test_dsn_project_binding():
    ref = "fxoyniqnrlkxfligbxmg"
    ok = cd._dsn_contains_project_ref
    # ACCEPTED: canonical direct host, pooler user, and a libpq keyword DSN (finding #6)
    assert ok(f"postgresql://postgres:pw@db.{ref}.supabase.co:5432/postgres", ref)
    assert ok(f"postgresql://postgres.{ref}:pw@aws-0-us-west-1.pooler.supabase.com:6543/postgres", ref)
    assert ok(f"host=db.{ref}.supabase.co user=postgres dbname=postgres password=pw", ref)  # keyword DSN
    # REJECTED: the label-collision decoys the OLD `ref in labels` binding wrongly accepted
    assert not ok(f"postgresql://postgres:pw@db.{ref}.attacker.example:5432/postgres", ref)  # ref is a label, wrong domain
    assert not ok(f"postgresql://postgres.{ref}:pw@127.0.0.1:6543/postgres", ref)            # pooler user, non-pooler host
    assert not ok(f"postgresql://postgres.{ref}:pw@evil.example:5432/postgres", ref)         # pooler user, non-pooler host
    assert not ok("postgresql://postgres:pw@db.otherprojectref00000.supabase.co:5432/postgres", ref)  # wrong project
    assert not ok("postgresql://postgres:pw@127.0.0.1:5432/postgres", ref)                   # bare IP
    assert not ok(f"host=db.{ref}.supabase.co hostaddr=1.2.3.4 user=postgres dbname=postgres", ref)  # hostaddr overrides host
    assert not ok("", ref) and not ok("postgresql://x/y", "")


def test_main_write_failure_fails_closed():
    # finding #8: a publish failure must map to fail-closed exit 2, not an uncaught traceback
    orig_collect, orig_write = cd.collect_from_db, cd.write_signed_snapshot
    _priv, priv_pem, _pub = _ephemeral_keypair()
    os.environ["DISPOSITION_DSN"] = f"postgresql://postgres:pw@db.{PROJECT}.supabase.co:5432/postgres"
    os.environ["DISPOSITION_SIGNING_KEY"] = priv_pem.decode("utf-8")
    cd.collect_from_db = lambda *a, **k: dict(_MINI_SNAP)

    def _boom(*a, **k):
        raise OSError("hardlink unsupported on this filesystem")

    cd.write_signed_snapshot = _boom
    try:
        with tempfile.TemporaryDirectory() as d:
            rc = cd.main(["--project-ref", PROJECT, "--expect-database", "postgres",
                          "--repo-sha", SHA, "--out", os.path.join(d, "out.json")])
        assert rc == 2
    finally:
        cd.collect_from_db, cd.write_signed_snapshot = orig_collect, orig_write
        os.environ.pop("DISPOSITION_DSN", None)
        os.environ.pop("DISPOSITION_SIGNING_KEY", None)


def test_write_signed_snapshot_roundtrip():
    # the collector signs the exact snapshot bytes; the checker's file-verifier must accept them, and
    # any tamper to the published snapshot must fail verification against the public key.
    priv, _priv_pem, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "snap.json")
        sig = out + ".sig"
        cd.write_signed_snapshot(out, _snap(), sig_path=sig, private_key=priv)
        pub_path = os.path.join(d, "verify.pub")
        with open(pub_path, "wb") as fh:
            fh.write(pub_pem)
        ok, _reason = ds.verify_snapshot_files(out, sig, pub_path)
        assert ok
        with open(out, "ab") as fh:
            fh.write(b" ")  # tamper the signed bytes
        bad, _reason2 = ds.verify_snapshot_files(out, sig, pub_path)
        assert not bad


def test_signed_snapshot_overwrite_failure_preserves_prior():
    # Codex P2: if the snapshot write fails during an --overwrite refresh, the PRIOR valid snapshot
    # must survive (no destructive removal). Sidecar is published first, so we never leave a snapshot
    # without a signature either.
    priv, _pp, _pub = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "snap.json")
        sig = out + ".sig"
        cd.write_signed_snapshot(out, {"kind": "evidence_snapshot", "v": 1}, sig_path=sig, private_key=priv)
        with open(out, encoding="utf-8") as fh:
            first = fh.read()
        orig = cd._write_bytes_atomic

        def _selective(path, data, *, overwrite=False):
            if os.path.abspath(path) == os.path.abspath(out):
                raise OSError("disk full writing snapshot")
            return orig(path, data, overwrite=overwrite)

        cd._write_bytes_atomic = _selective
        try:
            cd.write_signed_snapshot(out, {"kind": "evidence_snapshot", "v": 2}, sig_path=sig, private_key=priv, overwrite=True)
            raise AssertionError("snapshot write failure did not raise")
        except OSError:
            pass
        finally:
            cd._write_bytes_atomic = orig
        with open(out, encoding="utf-8") as fh:
            assert fh.read() == first  # prior snapshot intact — never deleted


def test_main_signs_and_publishes():
    # end-to-end: main publishes BOTH the snapshot and a sidecar that verifies against the pubkey
    orig_collect = cd.collect_from_db
    priv, _priv_pem, pub_pem = _ephemeral_keypair()
    os.environ["DISPOSITION_DSN"] = f"postgresql://postgres:pw@db.{PROJECT}.supabase.co:5432/postgres"
    os.environ["DISPOSITION_SIGNING_KEY"] = _priv_pem.decode("utf-8")
    cd.collect_from_db = lambda *a, **k: dict(_MINI_SNAP)
    try:
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "prod.json")
            rc = cd.main(["--project-ref", PROJECT, "--expect-database", "postgres", "--repo-sha", SHA, "--out", out])
            assert rc == 0 and os.path.exists(out) and os.path.exists(out + ".sig")
            pub_path = os.path.join(d, "verify.pub")
            with open(pub_path, "wb") as fh:
                fh.write(pub_pem)
            ok, reason = ds.verify_snapshot_files(out, out + ".sig", pub_path)
            assert ok, reason
    finally:
        cd.collect_from_db = orig_collect
        os.environ.pop("DISPOSITION_DSN", None)
        os.environ.pop("DISPOSITION_SIGNING_KEY", None)


def test_main_missing_signing_key_fails_closed():
    # signing is mandatory (F1); a missing key fails closed BEFORE any DB work
    called = {"v": False}
    orig_collect = cd.collect_from_db
    os.environ["DISPOSITION_DSN"] = f"postgresql://postgres:pw@db.{PROJECT}.supabase.co:5432/postgres"
    os.environ.pop("DISPOSITION_SIGNING_KEY", None)

    def _spy(*a, **k):
        called["v"] = True
        return dict(_MINI_SNAP)

    cd.collect_from_db = _spy
    try:
        with tempfile.TemporaryDirectory() as d:
            rc = cd.main(["--project-ref", PROJECT, "--expect-database", "postgres", "--repo-sha", SHA, "--out", os.path.join(d, "o.json")])
        assert rc == 2 and called["v"] is False  # short-circuited before the census
    finally:
        cd.collect_from_db = orig_collect
        os.environ.pop("DISPOSITION_DSN", None)


def test_main_invalid_signing_key_fails_closed():
    # a malformed key PEM fails closed (value-silent: the message never echoes key material)
    called = {"v": False}
    orig_collect = cd.collect_from_db
    os.environ["DISPOSITION_DSN"] = f"postgresql://postgres:pw@db.{PROJECT}.supabase.co:5432/postgres"
    os.environ["DISPOSITION_SIGNING_KEY"] = "-----BEGIN PRIVATE KEY-----\nnot-a-real-key\n-----END PRIVATE KEY-----\n"

    def _spy(*a, **k):
        called["v"] = True
        return dict(_MINI_SNAP)

    cd.collect_from_db = _spy
    try:
        with tempfile.TemporaryDirectory() as d:
            rc = cd.main(["--project-ref", PROJECT, "--expect-database", "postgres", "--repo-sha", SHA, "--out", os.path.join(d, "o.json")])
        assert rc == 2 and called["v"] is False
    finally:
        cd.collect_from_db = orig_collect
        os.environ.pop("DISPOSITION_DSN", None)
        os.environ.pop("DISPOSITION_SIGNING_KEY", None)


def test_main_empty_schemas_fails_closed():
    # Claude R2: a blank/comma-only --schemas must fail closed BEFORE any DB work, not emit empty census
    called = {"v": False}
    orig_collect = cd.collect_from_db
    os.environ["DISPOSITION_DSN"] = f"postgresql://postgres:pw@db.{PROJECT}.supabase.co:5432/postgres"

    def _spy(*a, **k):
        called["v"] = True
        return {"target_identity": {"current_database": "postgres", "current_user": "x"}, "relation_count": 0, "query_bundle_sha256": "a" * 64}

    cd.collect_from_db = _spy
    try:
        with tempfile.TemporaryDirectory() as d:
            rc = cd.main(["--project-ref", PROJECT, "--expect-database", "postgres", "--repo-sha", SHA,
                          "--schemas", " , ,", "--out", os.path.join(d, "o.json")])
        assert rc == 2 and called["v"] is False  # short-circuited before any DB connection
    finally:
        cd.collect_from_db = orig_collect
        os.environ.pop("DISPOSITION_DSN", None)


def test_workflow_dims_not_observed():
    r = _rel(_snap(), "public.projects")
    assert r["advisor_findings"]["state"] == "not_observed"
    for dim in ("static_repo", "runtime_logs", "external_clients", "operator_declaration"):
        cell = r["consumer_evidence"][dim]
        assert cell["state"] == "not_observed" and cell["found_consumers"] is None and cell["ref"] is None


def test_sha256_deterministic_and_hex():
    h = cd.query_bundle_sha256()
    assert len(h) == 64 and all(ch in "0123456789abcdef" for ch in h) and h == cd.query_bundle_sha256()


def test_self_validation_rejects_bad_now():
    try:
        _snap(now="not-a-date")
        raise AssertionError("bad observed_at was not rejected")
    except ValueError:
        pass


# ==== target guard (pure) ====================================================
def _ti_row(**over):
    base = {"current_database": "postgres", "current_user": "authenticator", "server_version": "PostgreSQL 16.13",
            "server_version_num": 160013, "transaction_read_only": True, "db_now": NOW,
            "platform_role_markers": ["anon", "authenticated", "service_role"]}
    base.update(over)
    return base


def test_guard_passes_clean():
    ti, ok, reasons = cd.evaluate_target_guard(_ti_row(), expect_database="postgres",
                                               required_role_markers=("anon", "authenticated", "service_role"))
    assert ok and reasons == [] and ti["guard_passed"] is True and ti["transaction_read_only"] is True


def test_guard_fails_not_read_only():
    ti, ok, reasons = cd.evaluate_target_guard(_ti_row(transaction_read_only=False))
    assert not ok and any("read-only" in r for r in reasons) and ti["guard_passed"] is False


def test_guard_fails_wrong_database():
    _ti, ok, reasons = cd.evaluate_target_guard(_ti_row(current_database="dev_db"), expect_database="postgres")
    assert not ok and any("current_database" in r for r in reasons)


def test_guard_fails_missing_marker():
    _ti, ok, reasons = cd.evaluate_target_guard(_ti_row(platform_role_markers=["anon"]),
                                                required_role_markers=("anon", "authenticated", "service_role"))
    assert not ok and any("marker" in r for r in reasons)


# ==== fake-cursor DB orchestration ===========================================
class FakeDBError(Exception):
    pass


class _Col:
    def __init__(self, name):
        self.name = name


class FakeCursor:
    """Scripts cd.QUERY_BUNDLE by exact SQL string. A script value that is an Exception subclass is
    raised (to drive savepoint recovery); SAVEPOINT/RELEASE/ROLLBACK statements are recorded no-ops."""

    def __init__(self, script):
        self.script = script
        self._reverse = {v: k for k, v in cd.QUERY_BUNDLE.items()}
        self._rows = None
        self._cols = None
        self.executed = []

    def execute(self, sql, params=None):
        head = sql.split()[0] if sql else ""
        if head in ("SAVEPOINT", "RELEASE", "ROLLBACK"):
            self.executed.append(sql.strip())
            return
        key = self._reverse.get(sql)
        self.executed.append(key or "UNKNOWN")
        if key not in self.script:
            raise AssertionError(f"unscripted query: {key!r}")
        spec = self.script[key]
        if isinstance(spec, type) and issubclass(spec, Exception):
            raise spec("scripted failure")
        self._rows = spec["rows"]
        self._cols = [_Col(c) for c in spec["cols"]]

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    @property
    def description(self):
        return self._cols


TI_ROWS = [("postgres", "authenticator", "PostgreSQL 16.13", 160013, True, NOW,
            ["anon", "authenticated", "service_role"])]
TI_SCRIPT_COLS = ["current_database", "current_user", "server_version", "server_version_num",
                  "transaction_read_only", "db_now", "platform_role_markers"]


def _script(**over):
    base = {
        "target_identity": {"rows": TI_ROWS, "cols": TI_SCRIPT_COLS},
        "roles": {"rows": [("anon",), ("authenticated",)], "cols": ["rolname"]},
        "census": {"rows": [VIEW, TABLE], "cols": CENSUS_COLS},
        "privileges": {"rows": [
            ("public.projects", "anon", "SELECT", False),
            ("public.projects", "authenticated", "SELECT", True),
            ("public.v_scope_financials", "anon", "SELECT", True),
            ("public.v_scope_financials", "authenticated", "SELECT", True),
        ], "cols": ["object_id", "grantee", "verb", "has_priv"]},
        "dependents": {"rows": [
            ("public.projects", "trigger", "trg_z on public.projects", "inbound", False),
            ("public.projects", "constraint", "fk_a on public.scopes", "inbound", True),
            ("public.projects", "view", "public.v_scope_financials", "inbound", True),
        ], "cols": ["object_id", "dep_type", "dep_identity", "direction", "is_consumer"]},
    }
    base.update(over)
    return base


def _run_fake(script, expect_database=None, required_role_markers=()):
    return cd._collect(FakeCursor(script), ["public"], db_error=FakeDBError, project_ref=PROJECT,
                       repo_sha=SHA, expect_database=expect_database, required_role_markers=required_role_markers)


def test_fake_happy_path_valid_and_bound():
    snap = _run_fake(_script(), expect_database="postgres", required_role_markers=("anon", "authenticated"))
    assert cd._validate(snap) == [] and snap["relation_count"] == 2
    assert snap["observed_at"] == NOW  # observed_at comes from the DB clock, not a caller value
    assert snap["target_identity"]["current_database"] == "postgres"
    assert snap["target_identity"]["guard_passed"] is True


def test_fake_read_only_assertion_blocks():
    ro_off = list(TI_ROWS[0]); ro_off[4] = False
    try:
        _run_fake(_script(target_identity={"rows": [tuple(ro_off)], "cols": TI_SCRIPT_COLS}))
        raise AssertionError("non-read-only session was not blocked")
    except RuntimeError as exc:
        assert "read-only" in str(exc)


def test_fake_target_guard_failure_blocks():
    dev = list(TI_ROWS[0]); dev[0] = "dev_db"
    try:
        _run_fake(_script(target_identity={"rows": [tuple(dev)], "cols": TI_SCRIPT_COLS}), expect_database="postgres")
        raise AssertionError("wrong-database target was not blocked")
    except RuntimeError as exc:
        assert "target guard failed" in str(exc)


def test_fake_query_group_recovery():
    # privileges group raises -> dependents STILL runs; privileges recorded query_failed
    snap = _run_fake(_script(privileges=FakeDBError))
    proj = _rel(snap, "public.projects")
    assert proj["anon_effective_privs"]["state"] == "query_failed"
    assert proj["authenticated_effective_privs"]["state"] == "query_failed"
    assert proj["dependent_objects"]["state"] == "observed"  # later group unaffected
    assert snap["relation_count"] == 2


def test_fake_absent_role_not_observed():
    # anon role absent from pg_roles AND no anon grant -> not_observed (not observed-empty)
    script = _script(
        roles={"rows": [("authenticated",)], "cols": ["rolname"]},
        census={"rows": [TABLE], "cols": CENSUS_COLS},
        privileges={"rows": [("public.projects", "authenticated", "SELECT", True)], "cols": ["object_id", "grantee", "verb", "has_priv"]},
    )
    proj = _rel(_run_fake(script), "public.projects")
    assert proj["anon_effective_privs"]["state"] == "not_observed"
    assert proj["authenticated_effective_privs"] == {"state": "observed", "value": ["SELECT"]}


def test_fake_deterministic_dependency_ordering():
    proj = _rel(_run_fake(_script()), "public.projects")
    got = [(d["object_type"], d["identity"]) for d in proj["dependent_objects"]["value"]]
    assert got == sorted(got)  # stable order regardless of fetch order
    assert [d["object_type"] for d in proj["dependent_objects"]["value"]] == ["constraint", "trigger", "view"]


def test_fake_preserves_edge_direction():
    script = _script(dependents={"rows": [
        ("public.projects", "constraint", "fk_out -> public.scopes", "outbound", False),
        ("public.projects", "view", "public.v_x", "inbound", True),
    ], "cols": ["object_id", "dep_type", "dep_identity", "direction", "is_consumer"]})
    vals = _rel(_run_fake(script), "public.projects")["dependent_objects"]["value"]
    dirs = {(v["object_type"], v["direction"]) for v in vals}
    assert dirs == {("constraint", "outbound"), ("view", "inbound")}


# ==== atomic output (F6) =====================================================
def test_atomic_write_and_refuse_and_overwrite():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "snap.json")
        cd.write_snapshot(path, {"kind": "x", "n": 1})
        assert json.load(open(path, encoding="utf-8"))["n"] == 1
        try:
            cd.write_snapshot(path, {"kind": "x", "n": 2})
            raise AssertionError("existing output was overwritten without overwrite=True")
        except FileExistsError:
            pass
        assert json.load(open(path, encoding="utf-8"))["n"] == 1  # untouched
        cd.write_snapshot(path, {"kind": "x", "n": 3}, overwrite=True)
        assert json.load(open(path, encoding="utf-8"))["n"] == 3
        assert [f for f in os.listdir(d) if ".tmp-" in f] == []  # no temp leftovers


def test_atomic_write_failure_preserves_original():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "snap.json")
        cd.write_snapshot(path, {"kind": "x", "n": 1})
        try:
            cd.write_snapshot(path, {"bad": {1, 2, 3}}, overwrite=True)  # set is not JSON-serializable
            raise AssertionError("serialization failure did not raise")
        except TypeError:
            pass
        assert json.load(open(path, encoding="utf-8"))["n"] == 1  # original intact
        assert [f for f in os.listdir(d) if ".tmp-" in f] == []  # temp cleaned up


ALL = [
    ("snapshot_is_schema_valid", test_snapshot_is_schema_valid),
    ("view_is_definer_observed", test_view_is_definer_observed),
    ("table_is_definer_not_applicable", test_table_is_definer_not_applicable),
    ("row_estimate_states", test_row_estimate_states),
    ("privileges_observed_empty_and_failed", test_privileges_observed_empty_and_failed),
    ("in_data_api_exposed_is_not_observed", test_in_data_api_exposed_is_not_observed),
    ("dependents_sorted_and_database_deps", test_dependents_sorted_and_database_deps),
    ("dependents_dedup_counts_once", test_dependents_dedup_counts_once),
    ("dependents_function_and_outbound_direction", test_dependents_function_and_outbound_direction),
    ("consumer_count_excludes_self_owned_and_outbound", test_consumer_count_excludes_self_owned_and_outbound),
    ("dependency_role_classification", test_dependency_role_classification),
    ("dependency_role_or_across_duplicates", test_dependency_role_or_across_duplicates),
    ("dsn_project_binding", test_dsn_project_binding),
    ("main_write_failure_fails_closed", test_main_write_failure_fails_closed),
    ("write_signed_snapshot_roundtrip", test_write_signed_snapshot_roundtrip),
    ("signed_snapshot_overwrite_failure_preserves_prior", test_signed_snapshot_overwrite_failure_preserves_prior),
    ("main_signs_and_publishes", test_main_signs_and_publishes),
    ("main_missing_signing_key_fails_closed", test_main_missing_signing_key_fails_closed),
    ("main_invalid_signing_key_fails_closed", test_main_invalid_signing_key_fails_closed),
    ("main_empty_schemas_fails_closed", test_main_empty_schemas_fails_closed),
    ("workflow_dims_not_observed", test_workflow_dims_not_observed),
    ("sha256_deterministic_and_hex", test_sha256_deterministic_and_hex),
    ("self_validation_rejects_bad_now", test_self_validation_rejects_bad_now),
    ("guard_passes_clean", test_guard_passes_clean),
    ("guard_fails_not_read_only", test_guard_fails_not_read_only),
    ("guard_fails_wrong_database", test_guard_fails_wrong_database),
    ("guard_fails_missing_marker", test_guard_fails_missing_marker),
    ("fake_happy_path_valid_and_bound", test_fake_happy_path_valid_and_bound),
    ("fake_read_only_assertion_blocks", test_fake_read_only_assertion_blocks),
    ("fake_target_guard_failure_blocks", test_fake_target_guard_failure_blocks),
    ("fake_query_group_recovery", test_fake_query_group_recovery),
    ("fake_absent_role_not_observed", test_fake_absent_role_not_observed),
    ("fake_deterministic_dependency_ordering", test_fake_deterministic_dependency_ordering),
    ("fake_preserves_edge_direction", test_fake_preserves_edge_direction),
    ("atomic_write_and_refuse_and_overwrite", test_atomic_write_and_refuse_and_overwrite),
    ("atomic_write_failure_preserves_original", test_atomic_write_failure_preserves_original),
]


if __name__ == "__main__":
    ok = True
    for name, fn in ALL:
        try:
            fn()
            r = True
        except Exception as exc:  # noqa: BLE001
            r = False
            name = f"{name} ({type(exc).__name__}: {exc})"
        ok = ok and r
        print(f"  {'ok  ' if r else 'FAIL'}: {name}")
    print("\n=== COLLECTOR OFFLINE SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
