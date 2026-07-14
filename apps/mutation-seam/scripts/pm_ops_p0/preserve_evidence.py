"""P0-A read-only evidence preservation (design-only until a per-action GO).

Captures pre-change evidence for the PM/Ops P0 containment lane in a single
guarded ``REPEATABLE READ, READ ONLY`` transaction, then writes the results to
restricted custody with a SHA-256 manifest. No mutation, deploy, secret change,
or connectivity repair is performed.

Value-silence is absolute: the DSN is read from an environment variable named on
the command line (never passed as a value), and every failure surfaces as a
stable code only — never a DSN, host, password, or raw driver message.

Running this against production is gated behind a separate ``P0-A READ-ONLY
EVIDENCE`` operator GO. House style follows ``scripts/smoke_deployed_mutation_seam.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# self-locate the package on sys.path so `pm_ops_p0.binding` resolves whether the
# script is run directly or imported (parent.parent == apps/mutation-seam/scripts)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pm_ops_p0.binding import (  # noqa: E402
    TargetBindingError,
    assert_bound_connection,
    bind_target,
    scrubbed_pg_env,
)

PROJECT_REF = "fxoyniqnrlkxfligbxmg"
CUSTODY_ROOT = Path("/home/olares/custody/pm-ops-p0")
MANIFEST_NAME = "manifest.sha256"
CONNECT_TIMEOUT_SECONDS = 10

log = logging.getLogger("pm_ops_p0.preserve_evidence")


class EvidenceRefusal(Exception):
    """A pre-connect refusal carrying a stable, value-free code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


# ---------------------------------------------------------------------------
# P0-A read-only SQL snapshot (verbatim from the design packet §2). Raw strings
# preserve the SQL `E'\n'` separators and the `\y` regex word-boundaries.
# ---------------------------------------------------------------------------

_BEGIN = "BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY;"

_GUARD = r"""-- (guard) SECONDARY in-band check: assert read-only + a schema/RPC fingerprint. The fingerprint alone does NOT
--   bind the project (a clone/branch with the same 4 tables + RPC passes) -- the AUTHORITATIVE project binding
--   is the script's --expect-project-ref DSN validation (finding 3). Fails closed on a writable session/wrong DB.
DO $$
BEGIN
  IF NOT (SELECT setting::bool FROM pg_settings WHERE name = 'transaction_read_only') THEN
    RAISE EXCEPTION 'P0-A refused: transaction is not READ ONLY';
  END IF;
  IF to_regclass('public.projects') IS NULL OR to_regclass('public.scopes') IS NULL
     OR to_regclass('public.tasks') IS NULL OR to_regclass('public.apparatus') IS NULL
     OR to_regproc('public.approve_apparatus_completion') IS NULL THEN
    RAISE EXCEPTION 'P0-A refused: target fingerprint absent (wrong database/project?) — expected the 4 PM tables + apparatus RPCs';
  END IF;
END $$;"""

_Q_MARKERS = r"""-- (0) in-band evidence markers (corroborating only; cannot bind the project on managed Supabase)
select current_database() as current_database, current_user as current_user,
       coalesce(inet_server_addr()::text, '(unix socket)') as inet_server_addr;"""

_Q_A = r"""-- (a) exact per-grantee table ACL (rollback-input source; literal ACL entries preserved)
select c.relname, c.relrowsecurity as rls_enabled,
       (select count(*) from pg_policy p where p.polrelid=c.oid) as policies,
       coalesce(array_to_string(c.relacl, E'\n'), '(default/no explicit acl)') as relacl
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relname in ('projects','scopes','tasks','apparatus') order by c.relname;"""

_Q_B = r"""-- (b) EFFECTIVE privilege for the FIXED Data-API principal set across ALL table privileges,
--     driven by principals x privileges (NOT by ACL entries) so membership-inherited access is captured.
select c.relname, pr.role as principal, pv.priv as privilege_type,
       has_table_privilege(pr.role, c.oid, pv.priv) as effective
from pg_class c join pg_namespace n on n.oid=c.relnamespace
cross join (values ('anon'),('authenticated'),('public'),('apex_tcc_runtime')) as pr(role)
cross join (values ('SELECT'),('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),('REFERENCES'),('TRIGGER'),('MAINTAIN')) as pv(priv)
where n.nspname='public' and c.relname in ('projects','scopes','tasks','apparatus')
order by c.relname, principal, privilege_type;"""

_Q_B2 = r"""-- (b2) role-membership closure of anon/authenticated (which roles inherit them) — completes effective-access evidence
with recursive closure(target, member) as (
    select rolname, rolname from pg_roles where rolname in ('anon','authenticated')
  union
    select c.target, r.rolname
    from closure c
    join pg_roles gr on gr.rolname = c.member
    join pg_auth_members m on m.roleid = gr.oid
    join pg_roles r on r.oid = m.member
)
select target as target_role, array_agg(distinct member order by member) as members_inheriting
from closure group by target order by target;"""

_Q_C = r"""-- (c) counts only
select 'projects' rel, count(*) n from public.projects
union all select 'scopes', count(*) from public.scopes
union all select 'tasks', count(*) from public.tasks
union all select 'apparatus', count(*) from public.apparatus;"""

_Q_D = r"""-- (d) default privileges in schema public — BOTH objtypes r (tables) and f (functions), per grantor
select pg_get_userbyid(d.defaclrole) as grantor, d.defaclobjtype as objtype, array_to_string(d.defaclacl, E'\n') as default_acl
from pg_default_acl d join pg_namespace n on n.oid=d.defaclnamespace
where n.nspname='public' and d.defaclobjtype in ('r','f') order by grantor, objtype;"""

_Q_E = r"""-- (e) SECURITY DEFINER discovery. RELIABLE primary signals: name_refs_targets (regex on the function
--     definition) and has_dynamic_sql (EXECUTE present -> unresolvable target -> fail CLOSED).
--     depends_on_targets (pg_depend) is a SUPPLEMENTARY signal that is INERT for PL/pgSQL bodies (Postgres
--     records no dependency edge from a plpgsql body to referenced tables), so it does NOT fire for the 3
--     plpgsql apparatus RPCs -- they are caught by name_refs_targets. in_scope_failclosed = OR of the three.
with tgt as (
  select oid from pg_class
  where relnamespace = 'public'::regnamespace and relname in ('projects','scopes','tasks','apparatus')
),
dep_fns as (
  select distinct d.objid as fnoid
  from pg_depend d join tgt on d.refobjid = tgt.oid
  where d.classid = 'pg_proc'::regclass and d.refclassid = 'pg_class'::regclass  -- guard same-numbered OIDs
)
select p.proname, pg_get_function_identity_arguments(p.oid) as args, pg_get_userbyid(p.proowner) as owner,
       has_function_privilege('public',p.oid,'EXECUTE') as public_exec,
       has_function_privilege('anon',p.oid,'EXECUTE') as anon_exec,
       has_function_privilege('authenticated',p.oid,'EXECUTE') as auth_exec,
       (p.oid in (select fnoid from dep_fns)) as depends_on_targets,
       (pg_get_functiondef(p.oid) ~* '\y(projects|scopes|tasks|apparatus)\y') as name_refs_targets,
       (pg_get_functiondef(p.oid) ~* '\yexecute\y') as has_dynamic_sql,
       ( p.oid in (select fnoid from dep_fns)
         or pg_get_functiondef(p.oid) ~* '\y(projects|scopes|tasks|apparatus)\y'
         or pg_get_functiondef(p.oid) ~* '\yexecute\y' ) as in_scope_failclosed
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.prosecdef
order by in_scope_failclosed desc, p.proname;"""

_COMMIT = "COMMIT;"

# Ordered evidence steps: (artifact filename, SQL). Executed inside the one txn.
_EVIDENCE_STEPS: list[tuple[str, str]] = [
    ("01_markers.txt", _Q_MARKERS),
    ("02_table_acl.txt", _Q_A),
    ("03_effective_privilege.txt", _Q_B),
    ("04_role_membership_closure.txt", _Q_B2),
    ("05_counts.txt", _Q_C),
    ("06_default_acl.txt", _Q_D),
    ("07_secdef_discovery.txt", _Q_E),
]


def p0a_sql_text() -> str:
    """Return the canonical guarded read-only P0-A SQL block (for the record + parity)."""
    return "\n\n".join(
        [_BEGIN, _GUARD, _Q_MARKERS, _Q_A, _Q_B, _Q_B2, _Q_C, _Q_D, _Q_E, _COMMIT]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "P0-A read-only evidence preservation for the PM/Ops containment lane. "
            "Runs a single guarded REPEATABLE READ, READ ONLY transaction and writes "
            "restricted custody artifacts + a SHA-256 manifest. Requires a per-action GO."
        )
    )
    parser.add_argument(
        "--expect-project-ref",
        required=True,
        help=(
            "Supabase project ref the DSN MUST bind to "
            f"(must equal {PROJECT_REF}); the run refuses otherwise."
        ),
    )
    parser.add_argument(
        "--dsn-env",
        required=True,
        help=(
            "NAME of the environment variable holding the DSN (never the DSN value "
            "itself — value-silence). The variable is read at run time."
        ),
    )
    parser.add_argument(
        "--custody-root",
        default=str(CUSTODY_ROOT),
        help=f"Custody root directory (default: {CUSTODY_ROOT}).",
    )
    return parser


def _utc_clock() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _rows_to_text(cur: object) -> str:
    description = getattr(cur, "description", None)
    cols = [d.name for d in description] if description else []
    lines = ["\t".join(cols)]
    for row in cur.fetchall():  # type: ignore[attr-defined]
        lines.append("\t".join("" if v is None else str(v) for v in row))
    return "\n".join(lines) + "\n"


def collect_evidence(params: dict[str, str], expect_ref: str) -> dict[str, str]:
    """Open a bound, read-only connection and capture the P0-A evidence set.

    Connects inside a scrubbed PG* environment, re-checks the resolved host, runs
    the guarded read-only transaction, and returns ``{filename: text}``. Live only
    (not exercised by the offline suite).
    """
    import psycopg  # local import keeps offline paths driver-light

    artifacts: dict[str, str] = {"00_p0a_snapshot.sql": p0a_sql_text()}
    with scrubbed_pg_env():
        with psycopg.connect(
            **params, connect_timeout=CONNECT_TIMEOUT_SECONDS, autocommit=True
        ) as conn:
            assert_bound_connection(conn, expect_ref)  # post-connect host re-check
            with conn.cursor() as cur:
                cur.execute(_BEGIN)
                cur.execute(_GUARD)
                for filename, sql in _EVIDENCE_STEPS:
                    cur.execute(sql)
                    artifacts[filename] = _rows_to_text(cur)
                cur.execute(_COMMIT)
    return artifacts


def write_custody(
    base_dir: str | Path, artifacts: dict[str, str], *, clock: str
) -> Path:
    """Write artifacts to ``<base_dir>/<clock>/`` (dir 0700, files 0400) + manifest.

    No-clobber: a pre-existing run directory raises ``FileExistsError``.
    """
    run_dir = Path(base_dir) / clock
    run_dir.mkdir(parents=True)  # no exist_ok -> no-clobber
    run_dir.chmod(0o700)
    manifest_lines: list[str] = []
    for name in sorted(artifacts):
        data = artifacts[name].encode()
        path = run_dir / name
        path.write_bytes(data)
        path.chmod(0o400)
        manifest_lines.append(f"{hashlib.sha256(data).hexdigest()}  {name}")
    manifest = run_dir / MANIFEST_NAME
    manifest.write_text("\n".join(manifest_lines) + "\n")
    manifest.chmod(0o400)
    return run_dir


def _fail(code: str) -> int:
    print("RESULT FAIL")
    print(f"FAILURE {code}")
    return 1


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    args = build_parser().parse_args(argv)

    # --- pre-connect binding (fails closed; never connects on refusal) ---
    try:
        if args.expect_project_ref != PROJECT_REF:
            raise EvidenceRefusal("unexpected_project_ref")
        dsn = os.getenv(args.dsn_env)
        if not dsn:
            raise EvidenceRefusal("dsn_unset")
        params = bind_target(dsn, expect_ref=args.expect_project_ref)
    except (EvidenceRefusal, TargetBindingError) as exc:
        return _fail(exc.code)

    # --- live read-only capture ---
    try:
        artifacts = collect_evidence(params, args.expect_project_ref)
    except TargetBindingError as exc:
        return _fail(exc.code)  # post-connect host mismatch
    except Exception as exc:  # noqa: BLE001
        log.warning("evidence collection failed: %s", type(exc).__name__)  # class only
        return _fail("connection_or_query_failed")

    # --- custody ---
    try:
        run_dir = write_custody(args.custody_root, artifacts, clock=_utc_clock())
    except FileExistsError:
        return _fail("custody_path_exists")
    except Exception as exc:  # noqa: BLE001
        log.warning("custody write failed: %s", type(exc).__name__)
        return _fail("custody_write_failed")

    print("RESULT PASS")
    print(f"CUSTODY {run_dir}")
    print(f"ARTIFACTS {len(artifacts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
