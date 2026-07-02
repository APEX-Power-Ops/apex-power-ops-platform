# test_012_ops_app_role_boundary.py -- self-contained migration test (mirrors test_011's shape).
# Applies the FULL ladder 001..012 on ops_test, then proves the 012 posture: role flags,
# non-membership, PUBLIC hygiene, DEFINER/owner conversion, the column-scoped grant matrix,
# the boundary-denial proofs, H2, the FOR-UPDATE regressions, and reversibility.
#
# Denial proofs run via SET ROLE from the admin session: object-privilege checks use
# current_user, and superuser bypass is off after SET ROLE to a non-super role.
# NOTE: the SET ROLE *membership* denial itself cannot be proven from an admin session
# (SET ROLE permission is checked against session_user, which stays postgres); the
# real-login SET ROLE denial lives in packages/ops-intake/tests (writer/api DSNs).
# Here, non-membership is proven via pg_has_role.
import os, pathlib, uuid
import psycopg, pytest
from psycopg import errors
from psycopg.conninfo import conninfo_to_dict

HERE = pathlib.Path(__file__).resolve().parent

DSN = os.environ.get("OPS_DEV_ADMIN_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    "password={} sslmode=disable".format(
        os.environ.get("OPS_DEV_PGPASSWORD") or os.environ.get("PGPASSWORD", "")
    )
)
assert conninfo_to_dict(DSN).get("dbname") == "ops_test", "012 migration tests run on ops_test ONLY"

CHAIN = [
    "001_identity_skeleton.sql",
    "002_quote_model.sql",
    "003_intake_unique_keys.sql",
    "004_person_anchor.sql",
    "005_recognition_ledger.sql",
    "006_progress_billing.sql",
    "007_intake_envelope.sql",
    "008_core_equipment_models.sql",
    "009_recognition_bridge.sql",
    "010_native_envelope_intake.sql",
    "011_scope_quote_line_description.sql",
    "012_ops_app_role_boundary.sql",
]
DOWN012 = HERE / "012_ops_app_role_boundary_down.sql"
UP012 = HERE / "012_ops_app_role_boundary.sql"
DOWN011 = HERE / "011_scope_quote_line_description_down.sql"
DOWN010 = HERE / "010_native_envelope_intake_down.sql"
DOWN009 = HERE / "009_recognition_bridge_down.sql"
DOWN008 = HERE / "008_core_equipment_models_down.sql"
DOWN001 = HERE / "001_identity_skeleton_down.sql"


def _exec(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(pathlib.Path(path).read_text(encoding="utf-8"))


def _admin(autocommit=True):
    return psycopg.connect(DSN, autocommit=autocommit)


def _ops_schema_exists(conn) -> bool:
    return conn.execute(
        "select 1 from pg_catalog.pg_namespace where nspname='ops'"
    ).fetchone() is not None


def _clean_slate():
    """Drop all ops + core schemas so migrations apply cleanly on any ops_test state.
    012_down is guarded (to_regprocedure / pg_roles checks) so it is safe to run even
    when 012 was never applied."""
    with _admin() as c:
        if _ops_schema_exists(c):
            c.execute("delete from ops.intake_runs")  # 010 down data-loss guard
            _exec(DOWN012)
            _exec(DOWN011)
            _exec(DOWN010)
            _exec(DOWN009)
        _exec(DOWN008)
    _exec(DOWN001)


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    with _admin() as c:
        row = c.execute("select current_database()").fetchone()
        assert row[0] == "ops_test", "REFUSING DDL: current_database() != ops_test"
    _clean_slate()
    for f in CHAIN:
        _exec(HERE / f)
    yield
    _clean_slate()


# ---------- Task 1: roles ----------

def test_012_roles_exist_with_hardened_flags():
    with _admin() as c:
        for role, canlogin in (
            ("ops_intake_writer", True),
            ("ops_api", True),
            ("ops_fn_owner", False),
        ):
            row = c.execute(
                "select rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls,"
                " rolreplication from pg_roles where rolname=%s",
                (role,),
            ).fetchone()
            assert row is not None, role + " missing"
            assert row[0] is canlogin, role + " login flag wrong"
            assert row[1:] == (False, False, False, False, False), role + " has a privileged flag"


def test_012_no_login_role_is_member_of_fn_owner():
    with _admin() as c:
        for role in ("ops_intake_writer", "ops_api"):
            assert c.execute(
                "select pg_has_role(%s, 'ops_fn_owner', 'member')", (role,)
            ).fetchone()[0] is False, role + " can reach ops_fn_owner"
        # No non-superuser login role at all may be a member (superusers pass every
        # membership check by definition, so they are excluded from the sweep).
        bad = c.execute(
            "select rolname from pg_roles"
            " where rolcanlogin and not rolsuper"
            "   and pg_has_role(rolname, 'ops_fn_owner', 'member')"
        ).fetchall()
        assert bad == [], "login role(s) are members of ops_fn_owner: " + repr(bad)
