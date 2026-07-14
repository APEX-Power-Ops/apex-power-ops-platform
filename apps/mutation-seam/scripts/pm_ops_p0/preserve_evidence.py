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

import os
import sys

# Runtime-integrity preamble (review round 3, finding 1). A planted module on sys.path
# (an untracked pm_ops_p0/subprocess.py, or a PYTHONPATH/cwd/user-site file) would otherwise
# be imported at module load -- before any governance guard -- and run attacker code with the
# injected production DSN in the environment. Two defences, in order:
#   (1) here, BEFORE any shadowable import: restrict sys.path to entries UNDER an interpreter
#       install prefix (sys.*prefix), using only sys+os (already loaded -> unshadowable). That
#       drops EVERY attacker-writable/injected entry -- PYTHONPATH, cwd, "", the script dir,
#       the user site -- regardless of launcher or of whether -I was passed (Codex-c15 P1),
#       so no planted module can shadow the stdlib imports below (nor psycopg later).
#       pm_ops_p0 is already imported (or is re-exposed post-gate by _load_binding), so its
#       submodules resolve via the package __path__, not sys.path.
#   (2) main(): refuse unless the tree is pristine (no untracked files) AND HEAD equals the
#       freshly-fetched origin/main tip -- so a planted shadow is rejected BEFORE
#       pm_ops_p0.binding (hence psycopg) is imported. That import is DEFERRED to
#       _load_binding(), reached only past the gate, and never runs at module load.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_TRUSTED_SYS_PREFIXES = tuple(
    os.path.realpath(getattr(sys, _attr))
    for _attr in ("prefix", "base_prefix", "exec_prefix", "base_exec_prefix")
    if getattr(sys, _attr, "")
)
sys.path[:] = [
    _p
    for _p in sys.path
    if _p
    and any(
        os.path.realpath(_p) == _b or os.path.realpath(_p).startswith(_b + os.sep)
        for _b in _TRUSTED_SYS_PREFIXES
    )
]

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import subprocess  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402

# NOTE: pm_ops_p0.binding (and therefore psycopg) is imported LAZILY via _load_binding(),
# only after main()'s runtime-integrity + provenance gate passes (finding 1).

PROJECT_REF = "fxoyniqnrlkxfligbxmg"
EXPECTED_DB_ROLE = "postgres"  # the administrative role P0-A must resolve to
CUSTODY_ROOT = Path("/home/olares/custody/pm-ops-p0")
MANIFEST_NAME = "manifest.sha256"
PROVENANCE_NAME = "00_provenance.json"
SNAPSHOT_NAME = "00_p0a_snapshot.sql"
CONNECT_TIMEOUT_SECONDS = 10

# parameterised guard: the connection must resolve to the expected admin role
# before any evidence is read (review finding 3). Value-free: %s is bound, and the
# result is a boolean, so neither the expected nor actual role text is interpolated.
_ROLE_CHECK_SQL = "select current_user = %s"

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
--     Residual coverage gap (disclosed): a SECURITY DEFINER function writing a target only INDIRECTLY (via a
--     helper, with no name token and no EXECUTE), or a secdef writer in ANOTHER Data-API-exposed schema
--     (outside this public filter), is not flagged. P0-A output is operator-reviewed EVIDENCE, not an
--     automated gate -- treat any unexpected secdef function as in-scope pending review.
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

_Q_F = r"""-- (f) EXACT function ACL for SECURITY DEFINER functions in public (rollback-input source for P0-C 014):
--     raw proacl + aclexplode grantor/grantee/privilege/grant-option, so the 3 apparatus RPC EXECUTE grants
--     can be restored EXACTLY -- distinguishing DIRECT vs INHERITED vs PUBLIC-derived access (the effective
--     booleans in (e) cannot). A default/NULL proacl shows '(default/no explicit acl)' with null grantor/grantee
--     (the built-in owner-all + PUBLIC EXECUTE, which ALTER DEFAULT PRIVILEGES cannot strip -- design §11.6).
select p.proname, pg_get_function_identity_arguments(p.oid) as args, pg_get_userbyid(p.proowner) as owner,
       coalesce(array_to_string(p.proacl, E'\n'), '(default/no explicit acl)') as proacl,
       pg_get_userbyid(a.grantor) as grantor,
       case when a.grantee = 0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end as grantee,
       a.privilege_type, a.is_grantable
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
left join lateral aclexplode(p.proacl) a on true
where n.nspname='public' and p.prosecdef
order by p.proname, grantee, a.privilege_type;"""

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
    ("08_secdef_function_acl.txt", _Q_F),
]


def p0a_sql_text() -> str:
    """Return the canonical guarded read-only P0-A SQL block (design §2 + review §F1).

    Archived as ``00_p0a_snapshot.sql``. The design §2 snapshot is queries a-e; the
    function-ACL query (f) is the review-added exact-rollback source (finding 1). The
    in-band ``_Q_MARKERS`` (0) is a supplemental capture recorded separately to
    ``01_markers.txt`` and is not part of this block (review L4).
    """
    return "\n\n".join(
        [_BEGIN, _GUARD, _Q_A, _Q_B, _Q_B2, _Q_C, _Q_D, _Q_E, _Q_F, _COMMIT]
    )


def query_bundle_text() -> str:
    """Return the EXACT ordered SQL bundle the tool executes (for the provenance hash).

    Distinct from ``p0a_sql_text()``: includes the role guard and the markers query
    in run order, so a modified query set changes the recorded ``query_bundle_sha256``.
    """
    steps = [_BEGIN, _GUARD, _ROLE_CHECK_SQL] + [sql for _, sql in _EVIDENCE_STEPS]
    return "\n\n".join([*steps, _COMMIT])


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
        "--expect-repo-sha",
        required=True,
        help=(
            "The git HEAD SHA this run MUST execute from (governance). The run refuses "
            "unless the tracked tree is clean, HEAD matches, and HEAD is merged to main."
        ),
    )
    # NOTE (review round 3, finding 3): the expected admin DB role is SOURCE-PINNED to
    # EXPECTED_DB_ROLE and is deliberately NOT a CLI option -- a fixed P0-A action must
    # not let the caller choose (or weaken) the administrative role it asserts against.
    parser.add_argument(
        "--custody-root",
        default=str(CUSTODY_ROOT),
        help=f"Custody root directory (default: {CUSTODY_ROOT}).",
    )
    return parser


def _utc_clock() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_root() -> Path:
    """Locate the enclosing git repository root (a `.git` dir or worktree pointer file)."""
    start = Path(__file__).resolve()
    for parent in (start, *start.parents):
        if (parent / ".git").exists():
            return parent
    raise EvidenceRefusal("repo_root_not_found")


# git needs only a small, non-secret slice of the environment for the governance preflight
# (rev-parse / status / fetch). Running it with the FULL injected env would hand every
# apex-platform/prod secret -- the DSN, signing keys, other DSNs -- to git's remote
# transports and credential helpers, undermining the child-only secret handling (Codex-c6
# P1). Allow-list only what git legitimately needs; every injected app secret is dropped.
_GIT_ENV_ALLOW = (
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "LANG",
    "TERM",
    "TMPDIR",
    "SSH_AUTH_SOCK",
    "SSH_AGENT_PID",
)


def _git_env() -> dict[str, str]:
    """A scrubbed environment for git subprocesses that carries no injected app secret.

    Passes ONLY the allow-list (+ locale ``LC_*``). It deliberately does NOT forward
    ``GIT_*`` or ``XDG_*``: ``GIT_DIR`` / ``GIT_WORK_TREE`` / ``GIT_INDEX_FILE`` /
    ``GIT_CONFIG*`` and ``XDG_CONFIG_HOME`` are honored OVER ``-C`` and could redirect the
    preflight at a DIFFERENT clean repo/config, defeating the pristine + HEAD-equality gate
    (Codex-c7 P1). git discovers the repo via ``git -C repo_root`` and reads ~/.gitconfig /
    ~/.ssh via ``HOME``; auth that requires a hostile ``GIT_SSH_COMMAND`` simply fails closed
    (``origin_main_unresolvable``), never proceeds against an unverified tip.
    """
    env = {k: os.environ[k] for k in _GIT_ENV_ALLOW if k in os.environ}
    for key, value in os.environ.items():
        if key.startswith("LC_"):  # locale only; no GIT_*/XDG_* redirection surface
            env[key] = value
    return env


def _repo_git_state(repo_root: Path) -> tuple[str, bool, str | None]:
    """Return (HEAD sha, tree-pristine, freshly-fetched origin/main sha or None).

    `pristine` is True only when the tracked tree is clean AND there are no untracked
    files -- `git status --porcelain` with NO `--untracked-files=no`, so a planted
    import-shadow module (which is untracked) makes the tree non-pristine (finding 1).

    The origin/main sha is read AFTER a fresh `git fetch origin main`, so the caller can
    require HEAD == origin/main by equality, not a mere ancestor test (finding 2). It is
    None when the fetch fails or the ref is unresolvable; the caller fails closed on None
    (it cannot prove the current merged-tip guarantee). Every git subprocess runs with a
    scrubbed env so the injected DSN/secrets never reach git's transports (Codex-c6 P1).
    """

    def _git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=False,
            env=_git_env(),
        )

    head = _git("rev-parse", "HEAD")
    if head.returncode != 0:
        raise EvidenceRefusal("git_unavailable")
    head_sha = head.stdout.strip()
    # pristine: no tracked modifications AND no untracked files (a planted shadow is
    # untracked). `--untracked-files=all` is forced AND status.showUntrackedFiles is
    # pinned to `normal` on the command line, so a hostile repo-local .git/config
    # `showUntrackedFiles=no` cannot hide the shadow from this check (review round-3 A1).
    status = _git(
        "-c",
        "status.showUntrackedFiles=normal",
        "status",
        "--porcelain",
        "--untracked-files=all",
    )
    is_pristine = status.returncode == 0 and status.stdout.strip() == ""
    # fresh fetch of the BRANCH ref specifically (refs/heads/main, not the ambiguous "main"
    # which a lightweight tag `main` could satisfy — Codex-c16 P2), then read the just-fetched
    # tip from FETCH_HEAD (NOT the remote-tracking ref, which is updated only opportunistically
    # — review round-3 A6). None (fail closed) on any fetch/parse failure: an unverifiable
    # current-main tip must not proceed.
    origin_main_sha: str | None = None
    if _git("fetch", "--quiet", "origin", "refs/heads/main").returncode == 0:
        fh = _git("rev-parse", "--verify", "--quiet", "FETCH_HEAD")
        if fh.returncode == 0 and fh.stdout.strip():
            origin_main_sha = fh.stdout.strip()
    return head_sha, is_pristine, origin_main_sha


def _trusted_prefixes() -> tuple[str, ...]:
    """Install prefixes a trusted module must live under -- from ``sys`` attributes ONLY.

    Uses ``sys.prefix`` / ``sys.base_prefix`` / ``sys.exec_prefix`` / ``sys.base_exec_prefix``,
    all attributes of the builtin (unshadowable) ``sys`` module, so computing the trusted
    roots imports NOTHING shadowable -- the earlier ``sysconfig``/``site`` approach itself
    ran a PYTHONPATH ``sysconfig.py`` shadow during validation (Codex-c10 P1). A
    venv-installed psycopg lives under ``sys.prefix``; the stdlib under ``sys.base_prefix``;
    a PYTHONPATH / user-site / repo-tree shadow is outside every prefix.
    """
    prefixes: set[str] = set()
    for attr in ("prefix", "base_prefix", "exec_prefix", "base_exec_prefix"):
        value = getattr(sys, attr, "")
        if value:
            prefixes.add(os.path.realpath(value))
    return tuple(prefixes)


def _assert_trusted_location(location: str) -> None:
    """Refuse unless `location` resolves UNDER a real interpreter/venv install prefix.

    Whatever placed a shadow on sys.path -- an untracked file the pristine check missed
    under a hostile .git/config, a TRACKED shadow at origin/main, a PYTHONPATH entry, a
    .pth injection -- the module that resolves must come from the interpreter's own install
    (under ``sys.*prefix``), never a repo-tree ``psycopg.py``, a user-site
    (``~/.local``, PYTHONUSERBASE-redirectable, Codex-c9 P1), NOR a decoy path merely
    CONTAINING ``site-packages`` (``/tmp/site-packages/psycopg.py``, Codex-c8 P1). The
    resolved origin is prefix-matched against ``sys.*prefix``. Value-free code on failure.
    """
    if not location:
        raise EvidenceRefusal("untrusted_binding_source")
    resolved = os.path.realpath(location)
    if not any(
        resolved == base or resolved.startswith(base + os.sep)
        for base in _trusted_prefixes()
    ):
        raise EvidenceRefusal("untrusted_binding_source")


def _load_binding():
    """Import the shared binding module -- DEFERRED past main()'s governance gate.

    Vets psycopg's ORIGIN via ``importlib.util.find_spec`` and refuses an untrusted
    location BEFORE ``import psycopg`` executes any module body (Codex-c5 P1): a PYTHONPATH
    ``psycopg.py`` shadow must never run its code with the DSN already in the environment.
    Only after psycopg is imported (and re-checked) does it put this repo's
    ``apps/mutation-seam/scripts`` at the FRONT of sys.path (deduped) so
    ``from pm_ops_p0.binding`` binds THIS repo's ``binding.py`` -- the same file
    ``build_provenance`` hashes -- not a foreign/stale ``pm_ops_p0`` on an earlier entry
    (Codex-final P2a). Reached only once the pristine + merged-HEAD gate has proven no
    untracked shadow module exists (finding 1). Returns (TargetBindingError, connect_bound).
    """
    import importlib.util

    spec = importlib.util.find_spec("psycopg")  # locates WITHOUT executing the module
    origin = spec.origin if spec else None
    if not origin:
        raise EvidenceRefusal("untrusted_binding_source")
    _assert_trusted_location(origin)  # vet the resolved origin BEFORE any code runs
    import psycopg

    _assert_trusted_location(
        getattr(psycopg, "__file__", "") or ""
    )  # belt: file matches
    scripts_dir = os.path.dirname(_SCRIPT_DIR)
    while scripts_dir in sys.path:
        sys.path.remove(scripts_dir)
    sys.path.insert(0, scripts_dir)
    from pm_ops_p0.binding import TargetBindingError, connect_bound

    return TargetBindingError, connect_bound


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_provenance(
    *,
    repo_sha: str,
    repo_pristine: bool,
    on_main: bool,
    origin_main_sha: str,
    expect_repo_sha: str,
    expect_project_ref: str,
    expect_db_role: str,
    dsn_env: str,
    started_at: str,
    finished_at: str,
) -> str:
    """Return a deterministic JSON provenance record binding evidence to governed tooling.

    Records the repo SHA, the pristine (clean + no-untracked) flag, the freshly-fetched
    origin/main tip and the HEAD==origin/main equality (finding 2), the tool source
    hashes, the exact query-bundle hash, the source-pinned project/role, the DSN env-var
    NAME (never a value), capture timestamps, and psycopg/libpq versions. A reviewer can
    read HEAD == origin_main_sha == expect_repo_sha straight from the record.
    """
    import psycopg

    here = Path(__file__).resolve().parent
    record = {
        "artifact": "pm_ops_p0.preserve_evidence.provenance",
        "schema_version": 2,
        "expected_project_ref": expect_project_ref,
        "expected_db_role": expect_db_role,
        "dsn_env_var_name": dsn_env,  # NAME only — never the DSN value
        "repo_sha": repo_sha,
        "expect_repo_sha": expect_repo_sha,
        "origin_main_sha": origin_main_sha,
        "repo_tree_pristine": repo_pristine,
        "repo_head_equals_origin_main": on_main,
        "tool_source_sha256": {
            "binding.py": _sha256_file(here / "binding.py"),
            "preserve_evidence.py": _sha256_file(here / "preserve_evidence.py"),
        },
        "query_bundle_sha256": hashlib.sha256(query_bundle_text().encode()).hexdigest(),
        "capture_started_at_utc": started_at,
        "capture_finished_at_utc": finished_at,
        "psycopg_version": psycopg.__version__,
        "libpq_version": psycopg.pq.version(),
    }
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


def _rows_to_text(cur: object) -> str:
    description = getattr(cur, "description", None)
    cols = [d.name for d in description] if description else []
    lines = ["\t".join(cols)]
    for row in cur.fetchall():  # type: ignore[attr-defined]
        lines.append("\t".join("" if v is None else str(v) for v in row))
    return "\n".join(lines) + "\n"


def collect_evidence(dsn: str, expect_ref: str) -> dict[str, str]:
    """Open a bound, read-only connection and capture the P0-A evidence set.

    Imports the shared binding discipline LAZILY via ``_load_binding`` (finding 1): the
    import (and therefore psycopg) is reached only after main()'s pristine + merged-HEAD
    gate has proven no untracked shadow module exists. Inside the guarded read-only
    transaction, refuses (value-free ``db_role_mismatch``) unless ``current_user`` is the
    SOURCE-PINNED admin role ``EXPECTED_DB_ROLE`` (finding 3), then captures
    ``{filename: text}``. The live connect/query is not exercised by the offline suite;
    the choreography (execute order, env-scrub-at-connect, the pre-query host re-check,
    and the role guard) is verified offline via a fake conn.
    """
    _TargetBindingError, connect_bound = _load_binding()
    artifacts: dict[str, str] = {SNAPSHOT_NAME: p0a_sql_text()}
    with connect_bound(
        dsn, expect_ref, connect_timeout=CONNECT_TIMEOUT_SECONDS, autocommit=True
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(_BEGIN)
            cur.execute(_GUARD)
            cur.execute(_ROLE_CHECK_SQL, (EXPECTED_DB_ROLE,))
            if not (cur.fetchone() or [False])[0]:
                raise EvidenceRefusal("db_role_mismatch")  # value-free (no role echo)
            for filename, sql in _EVIDENCE_STEPS:
                cur.execute(sql)
                artifacts[filename] = _rows_to_text(cur)
            cur.execute(_COMMIT)
    return artifacts


def _write_restricted_file(path: Path, data: bytes) -> None:
    """Create `path` at mode 0400 (O_EXCL: no-clobber, no perm window), fsync'd.

    Loops until the whole buffer is written: `os.write` may write fewer bytes than
    requested without raising (short write), which would otherwise leave a truncated
    evidence file while the manifest records the full-buffer hash (review Codex-delta-P2).
    fsync makes the bytes durable before the directory is published (review finding 6).
    """
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written == 0:  # pragma: no cover - defensive against a stuck fd
                raise OSError("custody write made no progress")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_dir(path: Path) -> None:
    """fsync a directory so its entries (creates/renames) are durable."""
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_custody(
    base_dir: str | Path, artifacts: dict[str, str], *, clock: str
) -> Path:
    """Atomically publish artifacts to ``<base_dir>/<clock>/`` (dir 0700, files 0400) + manifest.

    Bundle-atomic + durable (review finding 6): every artifact + manifest is written
    (0400, fsync'd) into a ``.partial-<clock>`` staging dir, the staging dir is
    fsync'd, then it is ``os.rename``d onto the final ``<clock>`` name and the parent
    is fsync'd — so a crash mid-run leaves only a ``.partial-*`` dir, never a partial
    final-named bundle. Restrictive modes are set atomically under a tightened umask
    (no perm window, review Codex-P2/L5). No-clobber: a pre-existing final dir, a
    stale ``.partial`` dir, or an artifact name collision (``O_EXCL``) raises
    ``FileExistsError``.
    """
    base = Path(base_dir)
    final_dir = base / clock
    partial_dir = base / f".partial-{clock}"
    old_umask = os.umask(0o077)
    try:
        if final_dir.exists():
            raise FileExistsError(f"custody run already published: {final_dir}")
        # umask 0o077 keeps every created dir (leaf + any parents) at 0o700
        partial_dir.mkdir(
            mode=0o700, parents=True
        )  # no exist_ok -> no stale-partial clobber
        manifest_lines: list[str] = []
        for name in sorted(artifacts):
            data = artifacts[name].encode()
            _write_restricted_file(partial_dir / name, data)
            manifest_lines.append(f"{hashlib.sha256(data).hexdigest()}  {name}")
        _write_restricted_file(
            partial_dir / MANIFEST_NAME, ("\n".join(manifest_lines) + "\n").encode()
        )
        _fsync_dir(partial_dir)
        os.rename(partial_dir, final_dir)  # atomic publish
        _fsync_dir(base)  # make the rename durable
    finally:
        os.umask(old_umask)
    return final_dir


def _fail(code: str) -> int:
    print("RESULT FAIL")
    print(f"FAILURE {code}")
    return 1


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    args = build_parser().parse_args(argv)
    started_at = _utc_now_iso()

    # --- pre-flight refusals (fail closed before reaching the DB layer OR the deferred
    #     binding/psycopg import, so a planted shadow module is never imported) ---
    try:
        if args.expect_project_ref != PROJECT_REF:
            raise EvidenceRefusal("unexpected_project_ref")
        dsn = os.getenv(args.dsn_env)
        if not dsn:
            raise EvidenceRefusal("dsn_unset")
        # governance: run only from a pristine checkout whose HEAD IS the current merged
        # main tip. pristine = clean + no untracked (finding 1); the three-way equality
        # HEAD == origin/main == --expect-repo-sha (finding 2) rejects a stale/ancestor or
        # self-attested checkout that an ancestor test would have passed.
        repo_sha, repo_pristine, origin_main_sha = _repo_git_state(_repo_root())
        if not repo_pristine:
            raise EvidenceRefusal("repo_dirty")  # tracked OR untracked changes present
        if repo_sha != args.expect_repo_sha:
            raise EvidenceRefusal("repo_sha_mismatch")
        # fail closed: an unresolvable/unfetchable origin/main cannot prove the merged,
        # current-tip guarantee, so refuse rather than proceed (review Codex-P2 + finding 2).
        if origin_main_sha is None:
            raise EvidenceRefusal("origin_main_unresolvable")
        if repo_sha != origin_main_sha:
            raise EvidenceRefusal(
                "repo_head_not_origin_main"
            )  # ancestor/stale/self-attested
    except EvidenceRefusal as exc:
        return _fail(exc.code)

    # --- live read-only capture. The binding module (hence psycopg) is imported HERE,
    #     only after the governance gate above (finding 1); connect_bound binds BEFORE
    #     opening any socket, so a wrong-project DSN raises with no connection made. ---
    try:
        TargetBindingError, _connect_bound = _load_binding()
    except Exception as exc:  # noqa: BLE001 - a shadowed/broken binding import fails closed
        log.warning("binding import failed: %s", type(exc).__name__)  # class only
        return _fail("binding_import_failed")
    try:
        artifacts = collect_evidence(dsn, args.expect_project_ref)
    except (TargetBindingError, EvidenceRefusal) as exc:
        return _fail(exc.code)  # bind/host/role mismatch — value-free stable code
    except Exception as exc:  # noqa: BLE001
        log.warning("evidence collection failed: %s", type(exc).__name__)  # class only
        return _fail("connection_or_query_failed")

    # --- provenance (binds the evidence to the governed tooling + this run) ---
    artifacts[PROVENANCE_NAME] = build_provenance(
        repo_sha=repo_sha,
        repo_pristine=repo_pristine,
        on_main=(repo_sha == origin_main_sha),
        origin_main_sha=origin_main_sha,
        expect_repo_sha=args.expect_repo_sha,
        expect_project_ref=args.expect_project_ref,
        expect_db_role=EXPECTED_DB_ROLE,
        dsn_env=args.dsn_env,
        started_at=started_at,
        finished_at=_utc_now_iso(),
    )

    # --- custody (atomic + durable publish) ---
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


def _isolation_gate(isolated: bool) -> int | None:
    """Refuse the CLI unless the interpreter is isolated (``python -I``).

    ``-I`` makes Python ignore ``PYTHONPATH``, the user site, and the unsafe ``sys.path[0]``
    (cwd / script dir), so NO environment-injected path -- including a ``PYTHONPATH`` entry
    pointing at a repo subdir -- can shadow an import before the pristine gate. Enforcing it
    closes the import-shadow class at the interpreter level (Codex-c14 P1); the sys.path
    preamble above is then belt-and-suspenders. Returns a non-None exit code when NOT isolated.
    """
    if not isolated:
        print("RESULT FAIL")
        print("FAILURE interpreter_not_isolated")
        return 1
    return None


if __name__ == "__main__":
    _rc = _isolation_gate(sys.flags.isolated)
    sys.exit(_rc if _rc is not None else main())
