"""Phase 1 RED-PROOF (Supabase-compat).

Proves the LOCAL non-superuser applier mode (--apply-as-non-superuser) reproduces
the 2026-07-04 Supabase prod failure class as a CI tripwire: the UNADAPTED records
security stack applies 001-044 fine as a non-super applier, then FAILS at exactly
045's `alter role records_api ... nosuperuser` with SQLSTATE 42501
(insufficient_privilege) - not earlier at CREATE ROLE (the wrong reason).

This is a LOCAL APPROXIMATION on a true-superuser local Postgres; it is NOT a
Supabase-compat proof. A real Supabase branch (Phase 0) is the fidelity authority,
and Phase 0 is currently blocked on Supabase lifecycle capacity.

Skips when RECORDS_PG_ADMIN_DSN is absent (no local Postgres), and self-skips once
045 is adapted (Phase 2 Task 2.1 supersedes this red-proof).
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_validation as rv  # noqa: E402
import _dbtest  # noqa: E402

ADMIN = os.environ.get("RECORDS_PG_ADMIN_DSN")
if not ADMIN:
    pytest.skip(
        "RECORDS_PG_ADMIN_DSN not set - local non-super red-proof skipped",
        allow_module_level=True,
    )

_SQL045 = os.path.join(rv.HERE, "045_records_security_rls.sql")


def _045_is_unadapted():
    """True while 045 still self-sets `nosuperuser` on records_api (the failure this
    proof targets). Once Phase 2 drops that clause, this proof is superseded."""
    with open(_SQL045, encoding="utf-8") as fh:
        txt = fh.read().lower()
    return bool(re.search(r"alter role\s+records_api\b[^;]*\bnosuperuser\b", txt))


if not _045_is_unadapted():
    pytest.skip(
        "045 already adapted (Phase 2) - red-proof superseded by Task 2.1",
        allow_module_level=True,
    )


@pytest.fixture(scope="module")
def applier_on_base_stack():
    """A disposable DB with 001-044 applied AS the non-super applier; yields the
    applier apply-DSN. The fixture succeeding IS the base-stack viability proof (a
    non-super createrole applier can apply the whole pre-security stack). Value-silent."""
    import psycopg

    rv.check_admin_dsn(ADMIN)
    val = rv.make_val_name()
    rv.assert_val_name(val)
    applier = rv.make_local_applier(ADMIN, rv.LOCAL_APPLIER_ENVELOPE)
    rv.assert_applier_name(applier.role)
    with psycopg.connect(ADMIN, autocommit=True) as c:
        c.execute(f'create database "{val}"')
    try:
        with psycopg.connect(ADMIN, autocommit=True) as c:
            c.execute(applier.create_sql)
            c.execute(f'grant create on database "{val}" to "{applier.role}"')
        apply_dsn = rv.derive_child_dsn(applier.dsn, val)
        migs, _ = rv.enumerate_stack(rv.HERE)
        for num, fname in migs:
            if num >= 45:
                break
            rv._apply_as_applier(fname, apply_dsn)  # each must succeed (viability)
        yield apply_dsn
    finally:
        with psycopg.connect(ADMIN, autocommit=True) as c:
            c.execute(f'drop database if exists "{val}" with (force)')
            c.execute(applier.drop_sql)


def test_unadapted_045_fails_at_alter_role_42501(applier_on_base_stack):
    with pytest.raises(rv.ApplierApplyError) as ei:
        rv._apply_as_applier("045_records_security_rls.sql", applier_on_base_stack)
    err = ei.value
    assert err.migration.endswith("045_records_security_rls.sql")
    assert err.sqlstate == "42501"            # insufficient_privilege (superuser-only)
    assert err.line == 21                     # the `alter role` line, NOT 17 (create role)
    assert "alter role" in err.message.lower()  # reached the ALTER for the RIGHT reason


def test_base_stack_001_044_apply_under_non_super(applier_on_base_stack):
    # Reaching here means the module-scoped fixture applied 001-044 as the applier
    # without raising - the mode is viable, not vacuously green.
    assert applier_on_base_stack
