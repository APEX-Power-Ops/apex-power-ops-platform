"""Shared target-binding discipline for the PM/Ops P0 containment tooling.

`bind_target(dsn, expect_ref)` parses a DSN, rejects every conninfo shape that
could route the connection away from the expected Supabase project, and returns
an explicit libpq parameter set with `sslmode=verify-full` forced on. It is
imported IDENTICALLY by P0-A's evidence script and P0-E's readiness probes so
both bind to project `fxoyniqnrlkxfligbxmg` (rev5.3 finding 2).

Value-silence is absolute: no function here ever raises, prints, or logs a DSN,
password, host, or a raw driver message. Failures surface only as `TargetBindingError`
whose message is one of a small set of STABLE CODES.

Defence-in-depth (the design's §2 discipline), split by responsibility so it
stays offline-testable:

* `bind_target`            -- parse + reject + anchored match + force verify-full
                              (pure; returns params). The `verify-full` in the
                              returned params means the server TLS cert must match
                              the expected host, so a wrong-IP reroute fails the
                              cert check even before the post-connect re-check.
* `scrubbed_pg_env`        -- context manager that removes the PG* environment
                              overrides libpq would otherwise merge at connect time,
                              restoring them on exit.
* `assert_bound_connection`-- post-connect re-check of `Connection.info` host.

`bind_target` is a pure function so the security matrix is fully testable without
a database; the caller opens the connection inside `scrubbed_pg_env()` and then
calls `assert_bound_connection`.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.conninfo import conninfo_to_dict

# ---- stable, value-free error codes -----------------------------------------
CODE_PARSE_FAILED = "dsn_parse_failed"
CODE_REROUTE_PARAM = "dsn_reroute_param"  # hostaddr / service present
CODE_MULTI_HOST = "dsn_multi_host"  # comma failover list in host/port/hostaddr
CODE_MISSING_HOST = "dsn_missing_host"
CODE_MISSING_USER = "dsn_missing_user"
CODE_HOST_NOT_BOUND = "dsn_host_not_bound_to_project"
CODE_USER_NOT_BOUND = "dsn_user_not_bound_to_project"
CODE_CONN_HOST_MISMATCH = "connection_host_mismatch"

# PG* environment variables libpq merges at connect time for params absent from
# the string. An env-supplied hostaddr/service could reroute the actual TCP
# target while the DSN string passes every reject; scrub them before connecting.
PG_ENV_OVERRIDES = ("PGHOSTADDR", "PGSERVICE", "PGHOST", "PGPORT", "PGSSLMODE")

_POOLER_SUFFIX = ".pooler.supabase.com"


class TargetBindingError(Exception):
    """A DSN or connection could not be bound to the expected project.

    The message is exactly `code` — a stable, value-free token — so it is safe to
    log or surface. It never carries the DSN, password, host, or driver text.
    """

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _is_pooler_host(host: str) -> bool:
    """True for a Supavisor pooler host `<single-label>.pooler.supabase.com`.

    Requires a single, non-empty label before the anchored suffix, which rejects
    suffix-injection like `db.<ref>.supabase.co.pooler.supabase.com`.
    """
    if not host.endswith(_POOLER_SUFFIX):
        return False
    label = host[: -len(_POOLER_SUFFIX)]
    return bool(label) and "." not in label


def bind_target(dsn: str, expect_ref: str) -> dict[str, str]:
    """Validate `dsn` binds to project `expect_ref`; return explicit libpq params.

    Raises `TargetBindingError` (value-free) on any reroute vector or mismatch.
    The returned dict always sets `sslmode=verify-full`.
    """
    try:
        parsed = conninfo_to_dict(dsn)
    except psycopg.Error:
        # a libpq parse error can quote a DSN token — never surface it
        raise TargetBindingError(CODE_PARSE_FAILED) from None

    # (1) reroute params that pull routing out-of-band
    if parsed.get("hostaddr") or parsed.get("service"):
        raise TargetBindingError(CODE_REROUTE_PARAM)

    host = (parsed.get("host") or "").strip()
    user = (parsed.get("user") or "").strip()
    port = (parsed.get("port") or "").strip()

    # (2) comma-separated failover lists (multi host/port/hostaddr)
    for value in (host, port, (parsed.get("hostaddr") or "")):
        if "," in value:
            raise TargetBindingError(CODE_MULTI_HOST)

    # (3) ambiguous/empty identity
    if not host:
        raise TargetBindingError(CODE_MISSING_HOST)
    if not user:
        raise TargetBindingError(CODE_MISSING_USER)

    # (4) anchored host/user match against the expected project
    _assert_anchored(host, user, expect_ref)

    params: dict[str, str] = {
        "host": host,
        "user": user,
        "dbname": (parsed.get("dbname") or "postgres").strip() or "postgres",
        "sslmode": "verify-full",  # forced: cert must match host (defeats IP reroute)
    }
    if port:
        params["port"] = port
    password = parsed.get("password")
    if password:
        params["password"] = password
    return params


def _assert_anchored(host: str, user: str, expect_ref: str) -> None:
    """Bind host/user to `expect_ref` in either the direct or pooler form."""
    direct_host = f"db.{expect_ref}.supabase.co"
    if host == direct_host:
        # direct form: the project-specific host is exact and cert-verified
        return
    if _is_pooler_host(host):
        # pooler form: Supavisor routes by tenant username, so the ref binds there
        if user == f"postgres.{expect_ref}":
            return
        raise TargetBindingError(CODE_USER_NOT_BOUND)
    raise TargetBindingError(CODE_HOST_NOT_BOUND)


@contextmanager
def scrubbed_pg_env() -> Iterator[None]:
    """Remove PG* environment overrides for the duration of the context.

    Values present beforehand are restored on exit; anything the inner code sets
    is cleared, so a leaked override cannot survive the context.
    """
    saved = {key: os.environ.pop(key, None) for key in PG_ENV_OVERRIDES}
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def assert_bound_connection(conn: object, expect_ref: str) -> None:
    """Re-check an open connection's `Connection.info` host binds to `expect_ref`.

    Belt-and-suspenders after `bind_target` + `verify-full`; raises a value-free
    `TargetBindingError(connection_host_mismatch)` if the resolved host is not the
    expected direct or pooler host.
    """
    info = getattr(conn, "info", None)
    host = (getattr(info, "host", "") or "").strip()
    if host == f"db.{expect_ref}.supabase.co" or _is_pooler_host(host):
        return
    raise TargetBindingError(CODE_CONN_HOST_MISMATCH)
