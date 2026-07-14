"""Offline tests for pm_ops_p0.binding — the shared target-binding gate.

No database is contacted. Every test exercises parsing, the reject/accept
matrix, value-silence, the PG* environment scrub, and the post-connect
re-check (via a stub connection). Runnable under pytest OR directly:

    python tests/test_binding.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# self-locate the package: parents[2] == apps/mutation-seam/scripts
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pm_ops_p0.binding import (  # noqa: E402
    PG_ENV_OVERRIDES,
    SCRUBBED_ENV_VARS,
    TargetBindingError,
    assert_bound_connection,
    bind_target,
    scrubbed_pg_env,
)

REF = "fxoyniqnrlkxfligbxmg"


def _expect_reject(dsn: str, expect_ref: str, code_substr: str) -> None:
    try:
        bind_target(dsn, expect_ref)
    except TargetBindingError as exc:
        assert code_substr in exc.code, (exc.code, code_substr, "wrong reject code")
        # value-silence: the code is stable and carries no DSN token
        assert exc.code == str(exc), "error str must equal the stable code"
    else:  # pragma: no cover - failure path
        raise AssertionError(f"expected TargetBindingError({code_substr}) for this DSN")


def _expect_reject_form(
    dsn: str, expect_ref: str, require_form: str, code_substr: str
) -> None:
    try:
        bind_target(dsn, expect_ref, require_form=require_form)
    except TargetBindingError as exc:
        assert code_substr in exc.code, (exc.code, code_substr, "wrong reject code")
        assert exc.code == str(exc)
    else:  # pragma: no cover
        raise AssertionError(
            f"expected TargetBindingError({code_substr}) for this form"
        )


# ---------------------------------------------------------------- reject matrix


def test_rejects_hostaddr_keyword():
    _expect_reject(
        f"host=aws-0-us-east-1.pooler.supabase.com user=postgres.{REF} "
        f"hostaddr=1.2.3.4 dbname=postgres",
        REF,
        "reroute",
    )


def test_rejects_service_keyword():
    _expect_reject(
        f"host=db.{REF}.supabase.co user=postgres service=myservice dbname=postgres",
        REF,
        "reroute",
    )


def test_uri_query_hostaddr_override_cannot_reroute():
    # libpq surfaces a query hostaddr as a conninfo key; whether it is rejected
    # outright or dropped, the invariant is that no reroute IP survives.
    dsn = (
        f"postgresql://postgres:pw@db.{REF}.supabase.co:5432/postgres?hostaddr=1.2.3.4"
    )
    try:
        params = bind_target(dsn, REF)
    except TargetBindingError as exc:
        assert "reroute" in exc.code or "parse" in exc.code, exc.code
        return
    assert "hostaddr" not in params
    assert params["host"] == f"db.{REF}.supabase.co", params["host"]


def test_rejects_multi_host_failover_list():
    _expect_reject(
        f"host=db.{REF}.supabase.co,evil.attacker.example user=postgres dbname=postgres",
        REF,
        "multi_host",
    )


def test_rejects_multi_port_failover_list():
    _expect_reject(
        f"host=db.{REF}.supabase.co port=5432,5433 user=postgres dbname=postgres",
        REF,
        "multi_host",
    )


def test_rejects_missing_host():
    _expect_reject("user=postgres dbname=postgres", REF, "missing_host")


def test_rejects_empty_or_ambiguous_host():
    # `host=` with no/empty value is malformed; libpq may swallow the next token,
    # so the invariant is simply that it is rejected (value-free), never accepted.
    for dsn in (
        "host= user=postgres dbname=postgres",
        "host='' user=postgres dbname=postgres",
    ):
        try:
            bind_target(dsn, REF)
        except TargetBindingError as exc:
            assert exc.code == str(exc)  # value-silent stable code
        else:  # pragma: no cover
            raise AssertionError("ambiguous empty host must be rejected")


def test_rejects_missing_user():
    _expect_reject(f"host=db.{REF}.supabase.co dbname=postgres", REF, "missing_user")


def test_rejects_wrong_ref_direct_host():
    _expect_reject(
        "host=db.someotherproject.supabase.co user=postgres dbname=postgres",
        REF,
        "host_not_bound",
    )


def test_rejects_wrong_ref_pooler_user():
    _expect_reject(
        "postgresql://postgres.someotherproject:pw@"
        "aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        REF,
        "user_not_bound",
    )


def test_rejects_direct_host_suffix_injection():
    _expect_reject(
        f"host=db.{REF}.supabase.co.evil.tld user=postgres dbname=postgres",
        REF,
        "host_not_bound",
    )


def test_rejects_pooler_host_suffix_injection():
    _expect_reject(
        f"postgresql://postgres.{REF}:pw@"
        "aws-0-us-east-1.pooler.supabase.com.evil.tld:6543/postgres",
        REF,
        "host_not_bound",
    )


def test_rejects_non_supabase_host():
    _expect_reject(
        "host=my-own-postgres.internal user=postgres dbname=postgres",
        REF,
        "host_not_bound",
    )


def test_malformed_dsn_is_value_silent_parse_error():
    try:
        bind_target("=missingkey", REF)
    except TargetBindingError as exc:
        assert exc.code == "dsn_parse_failed", exc.code
    else:  # pragma: no cover
        raise AssertionError("expected a parse-failed reject")


def test_uri_query_host_override_cannot_reroute():
    # a ?host= query param must never steer the bound host to the override value
    dsn = f"postgresql://postgres:pw@db.{REF}.supabase.co:5432/postgres?host=evil.tld"
    try:
        params = bind_target(dsn, REF)
    except TargetBindingError:
        return  # rejected outright — acceptable
    # if accepted, the bound host must be the real project host, never the override
    assert params["host"] == f"db.{REF}.supabase.co", params["host"]
    assert "evil" not in params["host"]


# --------------------------------------------------------------- value silence


def test_error_never_leaks_dsn_tokens():
    secret_pw = "SuperSecretPw123"
    secret_host = "evilhost.attacker.example"
    secret_user = "sneaky_role"
    dsn = f"host={secret_host} user={secret_user} password={secret_pw} dbname=postgres"
    try:
        bind_target(dsn, REF)
    except TargetBindingError as exc:
        blob = f"{exc!r}|{exc}|{exc.code}"
        assert secret_pw not in blob
        assert secret_host not in blob
        assert secret_user not in blob
    else:  # pragma: no cover
        raise AssertionError("expected a reject for a non-supabase host")


# --------------------------------------------------------------- accept matrix


def test_accepts_valid_pooler_and_forces_verify_full():
    params = bind_target(
        f"postgresql://postgres.{REF}:pw@"
        "aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require",
        REF,
    )
    assert params["host"] == "aws-0-us-east-1.pooler.supabase.com"
    assert params["user"] == f"postgres.{REF}"
    assert params["dbname"] == "postgres"
    assert params["port"] == "6543"
    assert params["sslmode"] == "verify-full"  # forced, overriding sslmode=require


def test_accepts_valid_direct_keyword_and_forces_verify_full():
    params = bind_target(
        f"host=db.{REF}.supabase.co port=5432 user=postgres password=pw "
        f"dbname=postgres sslmode=disable",
        REF,
    )
    assert params["host"] == f"db.{REF}.supabase.co"
    assert params["user"] == "postgres"
    assert params["sslmode"] == "verify-full"  # forced, overriding sslmode=disable


def test_accepted_params_carry_no_reroute_keys():
    params = bind_target(
        f"postgresql://postgres:pw@db.{REF}.supabase.co:5432/postgres",
        REF,
    )
    assert "hostaddr" not in params
    assert "service" not in params


# ------------------------------------------------- TLS trust contract (RI2 finding 2)


def test_bind_target_sourcepins_sslrootcert_system():
    # verify-full defaults to ~/.postgresql/root.crt (absent on the host -> fail closed);
    # the OS trust store must be selected explicitly via sslrootcert=system. bind_target
    # source-pins it so the direct-host verify-full cert chain can actually validate.
    params = bind_target(
        f"host=db.{REF}.supabase.co user=postgres dbname=postgres", REF
    )
    assert params["sslmode"] == "verify-full"
    assert params["sslrootcert"] == "system"


def test_bind_target_drops_caller_sslrootcert():
    # a caller-supplied sslrootcert (a rogue CA that would let verify-full validate a
    # man-in-the-middle cert) must never survive: bind_target reconstructs an explicit
    # whitelist and source-pins sslrootcert=system regardless of the DSN value.
    params = bind_target(
        f"host=db.{REF}.supabase.co user=postgres dbname=postgres "
        f"sslrootcert=/tmp/rogue-ca.pem",
        REF,
    )
    assert params["sslrootcert"] == "system"
    assert "/tmp/rogue-ca.pem" not in params.values()


def test_bind_target_sslrootcert_value_is_not_leaked_on_reject():
    # value-silence: a rogue sslrootcert on a wrong-host DSN must not be echoed
    try:
        bind_target(
            "host=evil.attacker.example user=postgres dbname=postgres "
            "sslrootcert=/tmp/rogue-ca.pem",
            REF,
        )
    except TargetBindingError as exc:
        assert "rogue-ca" not in f"{exc!r}|{exc}|{exc.code}"
    else:  # pragma: no cover
        raise AssertionError("expected a host_not_bound reject")


def test_scrubbed_env_includes_openssl_trust_anchors():
    # sslrootcert=system uses the OpenSSL default trust store, which SSL_CERT_FILE /
    # SSL_CERT_DIR redirect, and OPENSSL_CONF/MODULES/ENGINES can subvert (load a provider
    # or lower the TLS floor) -> all must be in the connect-time scrub set (RI2 lens-B F1).
    for var in (
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "OPENSSL_CONF",
        "OPENSSL_MODULES",
        "OPENSSL_ENGINES",
        "PGSSLROOTCERT",
    ):
        assert var in SCRUBBED_ENV_VARS, var
    # env-merged libpq params the DSN allow-list drops must also be scrubbed (lens-B F5)
    for var in ("PGOPTIONS", "PGSSLCRL", "PGGSSENCMODE", "PGCHANNELBINDING"):
        assert var in PG_ENV_OVERRIDES, var
    # the PG* subset stays a subset of the full scrub set
    assert set(PG_ENV_OVERRIDES) <= set(SCRUBBED_ENV_VARS)


def test_bind_target_rejects_non_numeric_port():
    _expect_reject(
        f"host=db.{REF}.supabase.co user=postgres port=54xx dbname=postgres",
        REF,
        "malformed_port",
    )


def test_bind_target_require_form_direct_rejects_pooler():
    # RI2 lens-B F4: the P6 (direct) probe must refuse a pooler DSN mechanically
    _expect_reject_form(
        f"postgresql://postgres.{REF}:pw@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        REF,
        "direct",
        "wrong_connection_form",
    )


def test_bind_target_require_form_pooler_rejects_direct():
    # the P7 (pooler) probe must refuse a direct DSN mechanically
    _expect_reject_form(
        f"host=db.{REF}.supabase.co user=postgres dbname=postgres",
        REF,
        "pooler",
        "wrong_connection_form",
    )


def test_bind_target_require_form_accepts_matching():
    direct = bind_target(
        f"host=db.{REF}.supabase.co user=postgres dbname=postgres",
        REF,
        require_form="direct",
    )
    assert direct["host"] == f"db.{REF}.supabase.co"
    pooler = bind_target(
        f"postgresql://postgres.{REF}:pw@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        REF,
        require_form="pooler",
    )
    assert pooler["host"] == "aws-0-us-east-1.pooler.supabase.com"


def test_bind_target_rejects_unknown_require_form():
    try:
        bind_target(
            f"host=db.{REF}.supabase.co user=postgres dbname=postgres",
            REF,
            require_form="banana",
        )
    except TargetBindingError as exc:
        assert exc.code == "dsn_wrong_connection_form", exc.code
    else:  # pragma: no cover
        raise AssertionError("an unknown require_form must be rejected")


def test_scrubbed_pg_env_scrubs_openssl_trust_anchors_and_restores():
    saved = {k: os.environ.get(k) for k in ("SSL_CERT_FILE", "SSL_CERT_DIR")}
    try:
        os.environ["SSL_CERT_FILE"] = "/tmp/rogue-bundle.pem"
        os.environ["SSL_CERT_DIR"] = "/tmp/rogue-dir"
        with scrubbed_pg_env():
            assert "SSL_CERT_FILE" not in os.environ
            assert "SSL_CERT_DIR" not in os.environ
        assert os.environ.get("SSL_CERT_FILE") == "/tmp/rogue-bundle.pem"
        assert os.environ.get("SSL_CERT_DIR") == "/tmp/rogue-dir"
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# -------------------------------------------------------------- env scrub


def test_scrubbed_pg_env_removes_all_overrides_and_restores():
    # drive the actual scrub list, so adding/removing a var is covered automatically
    names = list(PG_ENV_OVERRIDES)
    assert "PGSERVICE" in names and "PGSSLMODE" in names and "PGSSLROOTCERT" in names
    saved = {k: os.environ.get(k) for k in names}
    try:
        # all present except the last (absent), exercising both restore branches
        for k in names[:-1]:
            os.environ[k] = f"leak-{k}"
        os.environ.pop(names[-1], None)
        with scrubbed_pg_env():
            for k in names:
                assert k not in os.environ, k
            os.environ[names[0]] = "should-not-survive"  # inner leak
        for k in names[:-1]:
            assert os.environ.get(k) == f"leak-{k}", k
        assert names[-1] not in os.environ  # was absent -> stays absent
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# -------------------------------------------------- post-connect re-check


class _StubInfo:
    def __init__(self, host, user="", hostaddr=""):
        self.host = host
        self.user = user
        self.hostaddr = hostaddr


class _StubConn:
    def __init__(self, host, user="", hostaddr=""):
        self.info = _StubInfo(host, user, hostaddr)


def test_assert_bound_connection_accepts_direct_and_valid_pooler():
    # direct form: exact host is sufficient (no user constraint)
    assert_bound_connection(_StubConn(f"db.{REF}.supabase.co"), REF)
    # pooler form REQUIRES the tenant user postgres.<ref> (host alone is shared)
    assert_bound_connection(
        _StubConn("aws-0-us-east-1.pooler.supabase.com", user=f"postgres.{REF}"), REF
    )


def test_assert_bound_connection_rejects_pooler_wrong_user():
    # the pooler host is multi-tenant; a wrong tenant user must be rejected
    try:
        assert_bound_connection(
            _StubConn(
                "aws-0-us-east-1.pooler.supabase.com", user="postgres.someotherproject"
            ),
            REF,
        )
    except TargetBindingError as exc:
        assert exc.code == "connection_user_mismatch", exc.code
        assert "someotherproject" not in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected a connection_user_mismatch reject")


def test_assert_bound_connection_rejects_wrong_host_value_silently():
    try:
        assert_bound_connection(
            _StubConn("evil.attacker.example", user="postgres.x", hostaddr="6.6.6.6"),
            REF,
        )
    except TargetBindingError as exc:
        assert exc.code == "connection_host_mismatch", exc.code
        assert "evil.attacker.example" not in str(exc)
        assert "6.6.6.6" not in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected a connection_host_mismatch reject")


# ------------------------------------------------------------------- runner


def _run() -> int:
    funcs = [
        v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)
    ]
    failures = 0
    for fn in funcs:
        try:
            fn()
            print(f"[PASS] {fn.__name__}")
        except Exception as exc:  # noqa: BLE001 - test runner
            failures += 1
            print(f"[FAIL] {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(funcs) - failures}/{len(funcs)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
