"""Shared target-binding discipline for the PM/Ops P0 containment tooling.

`bind_target(dsn, expect_ref)` parses a DSN, rejects every conninfo shape that
could route the connection away from the expected Supabase project, and returns
an explicit libpq parameter set with `sslmode=verify-full` forced on. It is
imported IDENTICALLY by P0-A's evidence script and P0-E's readiness probes so
both bind to project `fxoyniqnrlkxfligbxmg` (rev5.3 finding 2).

Value-silence is absolute: no function here ever raises, prints, or logs a DSN,
password, host, or a raw driver message. Failures surface only as `TargetBindingError`
whose message is one of a small set of STABLE CODES.

Defence-in-depth (the design's §2 discipline). To avoid a caller getting only
part of the protection (review HIGH-1/M1), the full discipline is bundled into a
single `connect_bound()` context manager that BOTH consumers should use:

* `bind_target`            -- parse + reject + anchored match + force verify-full
                              (pure; returns params). The `verify-full` in the
                              returned params is the AUTHORITATIVE defence against
                              an IP reroute: the server TLS cert must match the
                              expected host, so a wrong-IP target fails the cert
                              check regardless of any env override.
* `scrubbed_pg_env`        -- context manager that removes the PG* environment
                              overrides libpq would otherwise merge at connect time,
                              restoring them on exit.
* `assert_bound_connection`-- post-connect name-level cross-check of the resolved
                              `Connection.info` (host, and pooler tenant user).
* `connect_bound`          -- bind + scrub + connect + re-check, in one call.

`bind_target` is a pure function so the security matrix is fully testable without
a database.
"""

from __future__ import annotations

import os
import threading
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
CODE_CONN_USER_MISMATCH = "connection_user_mismatch"

# PG* environment variables libpq merges at connect time for params absent from
# the string. An env-supplied hostaddr/service could reroute the actual TCP
# target, and an env-supplied SSL trust anchor could point verify-full at a rogue
# CA (verify-full is the load-bearing control, so its trust store is scrubbed too
# — review LOW-1). Scrub all of them before connecting.
PG_ENV_OVERRIDES = (
    "PGHOSTADDR",
    "PGSERVICE",
    "PGHOST",
    "PGPORT",
    "PGSSLMODE",
    "PGSSLROOTCERT",
    "PGSSLCERT",
    "PGSSLKEY",
)

_POOLER_SUFFIX = ".pooler.supabase.com"

# scrubbed_pg_env mutates process-global os.environ, so serialise the brief
# scrub+connect window against concurrent callers (e.g. a threadpooled readiness
# endpoint) — review LOW-2.
_CONNECT_LOCK = threading.Lock()


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
    suffix-injection like `db.<ref>.supabase.co.pooler.supabase.com`. Note the
    pooler host is SHARED/multi-tenant — it does not identify a project; the ref
    binding for the pooler form is the tenant username `postgres.<ref>`.
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

    # reconstruct an explicit whitelist: any exotic/injected libpq keyword in the
    # DSN (service, sslrootcert, options, a second host=, ...) is dropped here and
    # never reaches psycopg.connect.
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
    is cleared, so a leaked override cannot survive the context. Mutates global
    `os.environ` — callers in a concurrent path must serialise (see `connect_bound`).
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
    """Post-connect NAME-level cross-check that the connection binds to `expect_ref`.

    `verify-full` (forced by `bind_target`) is the AUTHORITATIVE defence against an
    IP reroute — the server cert must match the expected host. This function is a
    belt-and-suspenders name-level check: the resolved `Connection.info.host` must
    be the expected direct or pooler host, and for the pooler form (a shared,
    multi-tenant host) the tenant `user` must be `postgres.<ref>`. `hostaddr` is
    not equality-checked because managed Supabase IPs rotate (review MEDIUM-1/L3).

    Raises a value-free `TargetBindingError` on mismatch.
    """
    info = getattr(conn, "info", None)
    host = (getattr(info, "host", "") or "").strip()
    if host == f"db.{expect_ref}.supabase.co":
        return
    if _is_pooler_host(host):
        user = (getattr(info, "user", "") or "").strip()
        if user == f"postgres.{expect_ref}":
            return
        raise TargetBindingError(CODE_CONN_USER_MISMATCH)
    raise TargetBindingError(CODE_CONN_HOST_MISMATCH)


@contextmanager
def connect_bound(
    dsn: str,
    expect_ref: str,
    *,
    connect_timeout: int = 10,
    autocommit: bool = False,
) -> Iterator[object]:
    """The full binding discipline in ONE call — the entry point both P0-A and P0-E use.

    bind_target (rejects before any socket) -> connect inside a scrubbed PG* env
    (serialised against concurrent callers) -> post-connect re-check. Yields an
    open psycopg connection guaranteed bound to `expect_ref`; closes it on exit.
    Value-silent: a bind/reroute mismatch raises `TargetBindingError`; the connect
    itself may raise a psycopg error the caller must catch WITHOUT echoing it.
    """
    import psycopg

    params = bind_target(dsn, expect_ref)  # raises before any socket is opened
    with _CONNECT_LOCK:
        with scrubbed_pg_env():
            conn = psycopg.connect(
                **params, connect_timeout=connect_timeout, autocommit=autocommit
            )
    try:
        assert_bound_connection(conn, expect_ref)
    except BaseException:
        conn.close()
        raise
    try:
        yield conn
    finally:
        conn.close()
