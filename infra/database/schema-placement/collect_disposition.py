"""Read-only census collector for the schema-placement disposition ledger.

Emits an IMMUTABLE evidence_snapshot (validated against disposition.schema.json) of the
machine-derivable facts for a set of relations. The state-mapping CORE is pure and
offline-testable (synthetic catalog rows -> snapshot); psycopg is imported LAZILY inside the
DB opener, so importing this module, exercising the core, and running its offline test need no
driver and never touch a database. The DB orchestration (`_collect`) is driven through a plain
cursor object, so a fake cursor exercises it offline (read-only assertion, target-guard failure,
query-group recovery, absent roles, deterministic ordering) with no driver and no database.

Discipline / hardening (review findings):
  * Value-silent: the DSN is read from an env var (--dsn-env), never an argv; it is never
    printed and never embedded in the snapshot (generator carries only tool + version). Driver
    errors surface as the exception TYPE only (they can embed connection info); guard failures
    surface their message (DSN-free by construction).
  * Target-bound (F2): the DSN is first bound to --project-ref via parsed host/user identity
    (db.<ref>.supabase.co OR pooler user postgres.<ref>) — a DSN that does not carry the ref is
    REFUSED before connecting. Then every run reads current_database/current_user/server version/
    transaction_read_only + platform role markers and passes them through evaluate_target_guard;
    a mismatch (wrong DB, not read-only, missing markers) RAISES before any snapshot is built.
    --expect-database is required. observed_at comes from the database clock (now()), never a
    caller value; repo_sha derives from git HEAD by default.
  * Read-only (F2/F3): the session is opened read_only and the guard asserts it; only SELECTs run.
  * Transaction isolation (F3): each OPTIONAL query group runs under its own SAVEPOINT, so a
    failure rolls back just that group (never poisoning later groups in the aborted transaction)
    and is recorded as query_failed.
  * Role existence (F4): missing anon/authenticated roles yield `not_observed` privileges — an
    absent role is NOT manufactured into an observed-empty grant set.
  * Enumerated one-hop catalog inventory (F1/F3, findings #2/#7): dependent_objects enumerates the
    DIRECT (one-hop) pg_depend-representable relationships — view/matview rewrites, pg_proc function
    deps, INBOUND and OUTBOUND FK constraints (direction per edge), triggers, RLS policies,
    publications (explicit membership AND FOR ALL TABLES / FOR TABLES IN SCHEMA), owned sequences,
    and inheritance/partition children — de-duplicated (SQL `union` + a Python edge-key dedup).
    database_deps.found_consumers counts ONLY EXTERNAL CONSUMERS (edges the SQL flags is_consumer:
    views/matviews, function deps, inbound FKs from OTHER tables, publications, inheritance
    children); it EXCLUDES the relation's OWN sequences/triggers/policies and its OUTBOUND FKs,
    which are inventory but not consumers. It is ONE-HOP (not transitive) and does NOT see
    function/procedure BODY references, dynamic SQL, or application code (pg_depend does not track
    those); those consumer classes are supplied later (source/dynamic_sql/manual evidence) by the
    consumer-evidence workflow. No consumer CONCLUSION is drawn here.
  * Atomic output (F6): the snapshot is written to a sibling temp file, fsync'd, then os.replace'd;
    an existing output is refused unless --overwrite.
  * Observation states: a fact whose query group FAILED is `query_failed` (never a dropped field);
    a semantically-inapplicable fact is `not_applicable`; an unavailable value is `not_observed`.
  * Provenance: query_bundle_sha256 pins the exact SQL that produced the snapshot.

in_data_api_exposed_schema is emitted as `not_observed` (F7): Data API exposure is authoritative
only from platform config, not from the pgrst.db_schemas runtime GUC; it is supplied later by a
config-backed overlay. The four workflow consumer dimensions + advisor_findings are likewise
`not_observed` overlays.

    collect_disposition.py --dsn-env DISPOSITION_DSN --project-ref fxoyniqnrlkxfligbxmg \
        --expect-database postgres --require-role-markers anon,authenticated,service_role \
        --schemas public --out evidence/prod-<ts>.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disposition.schema.json")
COLLECTOR_VERSION = "0.1.0"

# Named SQL query bundle. query_bundle_sha256 hashes a canonical serialization of THIS dict, so
# the snapshot records exactly which SQL produced it. Read-only SELECTs only.
QUERY_BUNDLE = {
    "target_identity": """
        select current_database() as current_database,
               current_user as current_user,
               version() as server_version,
               current_setting('server_version_num')::int as server_version_num,
               (current_setting('transaction_read_only') = 'on') as transaction_read_only,
               now() as db_now,
               array(select rolname from pg_roles
                     where rolname in ('anon', 'authenticated', 'service_role', 'authenticator', 'postgres')
                     order by rolname) as platform_role_markers
    """,
    "roles": "select rolname from pg_roles where rolname in ('anon', 'authenticated')",
    "census": """
        select n.nspname as schema, c.relname as name, c.relkind::text as relkind,
               pg_get_userbyid(c.relowner) as owner,
               c.relrowsecurity as rls_enabled,
               case when c.relkind = 'v'
                    then coalesce((select option_value from pg_options_to_table(c.reloptions)
                                   where option_name = 'security_invoker'), 'false') = 'false'
                    else null end as is_security_definer_view,
               (select count(*) from pg_constraint k where k.confrelid = c.oid and k.contype = 'f') as inbound_fk_count,
               (select count(*) from pg_constraint k where k.conrelid = c.oid and k.contype = 'f') as outbound_fk_count,
               case when c.relkind in ('r', 'm') and c.reltuples >= 0 then c.reltuples::bigint else null end as row_estimate
        from pg_class c join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = any(%(schemas)s) and c.relkind in ('r', 'v', 'm', 'p', 'f')
        order by n.nspname, c.relname
    """,
    "privileges": """
        select n.nspname || '.' || c.relname as object_id, r.rolname as grantee, v.verb,
               has_table_privilege(r.rolname, c.oid, v.verb) as has_priv
        from pg_class c join pg_namespace n on n.oid = c.relnamespace
        cross join (values ('anon'), ('authenticated')) r(rolname)
        cross join (values ('SELECT'), ('INSERT'), ('UPDATE'), ('DELETE'), ('TRUNCATE'), ('REFERENCES'), ('TRIGGER')) v(verb)
        where n.nspname = any(%(schemas)s) and c.relkind in ('r', 'v', 'm', 'p', 'f')
          and exists (select 1 from pg_roles pr where pr.rolname = r.rolname)
    """,
    "dependents": """
        with targets as (
            select c.oid, c.relnamespace as nsoid, c.relkind::text as relkind, n.nspname || '.' || c.relname as object_id
            from pg_class c join pg_namespace n on n.oid = c.relnamespace
            where n.nspname = any(%(schemas)s) and c.relkind in ('r', 'v', 'm', 'p', 'f')
        ),
        rules as (
            select t.object_id,
                   case dc.relkind when 'm' then 'materialized_view' else 'view' end as dep_type,
                   dn.nspname || '.' || dc.relname as dep_identity, 'inbound' as direction, true as is_consumer
            from pg_depend d
            join targets t on t.oid = d.refobjid and d.refclassid = 'pg_class'::regclass
            join pg_rewrite rw on rw.oid = d.objid and d.classid = 'pg_rewrite'::regclass
            join pg_class dc on dc.oid = rw.ev_class
            join pg_namespace dn on dn.oid = dc.relnamespace
            where dc.oid <> t.oid
        ),
        funcs as (
            select t.object_id, 'function' as dep_type,
                   pn.nspname || '.' || p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')' as dep_identity,
                   'inbound' as direction, true as is_consumer
            from pg_depend d
            join targets t on t.oid = d.refobjid and d.refclassid = 'pg_class'::regclass
            join pg_proc p on p.oid = d.objid and d.classid = 'pg_proc'::regclass
            join pg_namespace pn on pn.oid = p.pronamespace
        ),
        in_fks as (
            select t.object_id, 'constraint' as dep_type,
                   con.conname || ' on ' || rn.nspname || '.' || rc.relname as dep_identity, 'inbound' as direction,
                   (con.conrelid <> con.confrelid) as is_consumer
            from pg_constraint con
            join targets t on t.oid = con.confrelid
            join pg_class rc on rc.oid = con.conrelid
            join pg_namespace rn on rn.oid = rc.relnamespace
            where con.contype = 'f'
        ),
        out_fks as (
            select t.object_id, 'constraint' as dep_type,
                   con.conname || ' -> ' || fn.nspname || '.' || fc.relname as dep_identity, 'outbound' as direction, false as is_consumer
            from pg_constraint con
            join targets t on t.oid = con.conrelid
            join pg_class fc on fc.oid = con.confrelid
            join pg_namespace fn on fn.oid = fc.relnamespace
            where con.contype = 'f'
        ),
        trigs as (
            select t.object_id, 'trigger' as dep_type, tg.tgname || ' on ' || t.object_id as dep_identity, 'inbound' as direction, false as is_consumer
            from pg_trigger tg join targets t on t.oid = tg.tgrelid
            where not tg.tgisinternal
        ),
        pols as (
            select t.object_id, 'policy' as dep_type, pol.polname || ' on ' || t.object_id as dep_identity, 'inbound' as direction, false as is_consumer
            from pg_policy pol join targets t on t.oid = pol.polrelid
        ),
        pubs as (
            select t.object_id, 'publication' as dep_type, p.pubname as dep_identity, 'inbound' as direction, true as is_consumer
            from pg_publication_rel pr
            join targets t on t.oid = pr.prrelid
            join pg_publication p on p.oid = pr.prpubid
        ),
        pubs_all as (
            select t.object_id, 'publication' as dep_type, p.pubname as dep_identity, 'inbound' as direction, true as is_consumer
            from pg_publication p cross join targets t
            where p.puballtables and t.relkind in ('r', 'p')
        ),
        pubs_schema as (
            select t.object_id, 'publication' as dep_type, p.pubname as dep_identity, 'inbound' as direction, true as is_consumer
            from pg_publication_namespace pns
            join pg_publication p on p.oid = pns.pnpubid
            join targets t on t.nsoid = pns.pnnspid
            where t.relkind in ('r', 'p')
        ),
        seqs as (
            select t.object_id, 'sequence' as dep_type, dn.nspname || '.' || dc.relname as dep_identity, 'inbound' as direction, false as is_consumer
            from pg_depend d
            join targets t on t.oid = d.refobjid and d.refclassid = 'pg_class'::regclass
            join pg_class dc on dc.oid = d.objid and d.classid = 'pg_class'::regclass and dc.relkind = 'S'
            join pg_namespace dn on dn.oid = dc.relnamespace
        ),
        inherits_children as (
            select t.object_id, 'table' as dep_type, cn.nspname || '.' || cc.relname as dep_identity, 'inbound' as direction, true as is_consumer
            from pg_inherits inh
            join targets t on t.oid = inh.inhparent
            join pg_class cc on cc.oid = inh.inhrelid
            join pg_namespace cn on cn.oid = cc.relnamespace
        )
        select object_id, dep_type, dep_identity, direction, is_consumer from rules
        union select object_id, dep_type, dep_identity, direction, is_consumer from funcs
        union select object_id, dep_type, dep_identity, direction, is_consumer from in_fks
        union select object_id, dep_type, dep_identity, direction, is_consumer from out_fks
        union select object_id, dep_type, dep_identity, direction, is_consumer from trigs
        union select object_id, dep_type, dep_identity, direction, is_consumer from pols
        union select object_id, dep_type, dep_identity, direction, is_consumer from pubs
        union select object_id, dep_type, dep_identity, direction, is_consumer from pubs_all
        union select object_id, dep_type, dep_identity, direction, is_consumer from pubs_schema
        union select object_id, dep_type, dep_identity, direction, is_consumer from seqs
        union select object_id, dep_type, dep_identity, direction, is_consumer from inherits_children
        order by object_id, dep_type, dep_identity, direction
    """,
}
_DEP_TYPES = {"table", "view", "materialized_view", "function", "procedure", "trigger", "policy",
              "constraint", "sequence", "index", "publication", "subscription", "foreign_table",
              "type", "source_reference"}
_TARGET_ROLES = ("anon", "authenticated")


def query_bundle_sha256() -> str:
    canonical = json.dumps(QUERY_BUNDLE, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ---- observation-state helpers ---------------------------------------------
def _obs(value):
    return {"state": "observed", "value": value}


def _na(detail):
    return {"state": "not_applicable", "detail": detail}


def _no(detail):
    return {"state": "not_observed", "detail": detail}


def _qf(detail):
    return {"state": "query_failed", "detail": detail}


def _cdim_observed(n, ref):
    return {"state": "observed", "found_consumers": int(n), "ref": ref}


def _cdim(state, detail):
    return {"state": state, "found_consumers": None, "ref": None, "detail": detail}


# ---- pure core: one relation_observation from raw facts --------------------
def build_relation_observation(census_row, privs, deps, failed_groups, now):
    """census_row: dict (schema/name/relkind/owner/rls_enabled/is_security_definer_view/
    inbound_fk_count/outbound_fk_count/row_estimate). privs: dict of role -> [verbs] for roles
    KNOWN TO EXIST (a missing key => role absent => not_observed); None if no privilege data.
    deps: list[dependency_record] or None. failed_groups: set of query-group names that raised."""
    schema, name, relkind = census_row["schema"], census_row["name"], census_row["relkind"]
    oid = f"{schema}.{name}"

    def priv_fact(role):
        if "privileges" in failed_groups:
            return _qf("privileges query failed")
        if privs is None:
            return _no("no privilege rows returned for this relation")
        if role not in privs:
            return _no(f"role '{role}' not present in target (or no privilege data returned)")
        return _obs(sorted(privs[role]))

    is_def = census_row.get("is_security_definer_view")
    row_est = census_row.get("row_estimate")

    if "dependents" in failed_groups:
        deps_fact = _qf("dependents query failed")
        ddeps_dim = _cdim("query_failed", "dependents query failed")
    else:
        # dependent_objects = the FULL enumerated catalog inventory (every edge, deduped by
        # (object_type, identity, direction)). database_deps.found_consumers counts ONLY external
        # CONSUMERS — edges flagged _is_consumer by the SQL: views/matviews, pg_proc deps, inbound
        # FKs from OTHER tables (self-referential FKs excluded), publications (incl. FOR ALL TABLES
        # / schema-level), inheritance children. It EXCLUDES the relation's OWN owned sequences,
        # triggers, policies and its OUTBOUND FKs — inventory, not consumers (finding #2). pg_rewrite
        # emits one row per column reference, so dedup precedes counting; consumer status is OR-ed
        # across duplicate keys so a consumer edge is never masked by a non-consumer twin.
        records_by_key, consumer_keys, order = {}, set(), []
        for dep in sorted(deps or [], key=lambda x: (x["object_type"], x["identity"], x["direction"])):
            edge_key = (dep["object_type"], dep["identity"], dep["direction"])
            if edge_key not in records_by_key:
                records_by_key[edge_key] = {k: v for k, v in dep.items() if not k.startswith("_")}
                order.append(edge_key)
            if dep.get("_is_consumer"):
                consumer_keys.add(edge_key)
        deps_fact = _obs([records_by_key[k] for k in order])
        ddeps_dim = _cdim_observed(len(consumer_keys), "query:dependents-v2")

    return {
        "object_id": oid, "schema": schema, "name": name, "relkind": relkind,
        "owner": _obs(census_row["owner"]) if census_row.get("owner") else _no("owner unavailable"),
        "rls_enabled": _obs(bool(census_row["rls_enabled"])) if census_row.get("rls_enabled") is not None else _no("rls unavailable"),
        "is_security_definer_view": _obs(bool(is_def)) if is_def is not None else _na("not a view"),
        "in_data_api_exposed_schema": _no("Data API exposure is authoritative only from platform config, not the pgrst.db_schemas GUC; supplied later by a config-backed overlay"),
        "anon_effective_privs": priv_fact("anon"),
        "authenticated_effective_privs": priv_fact("authenticated"),
        "inbound_fk_count": _obs(int(census_row["inbound_fk_count"])),
        "outbound_fk_count": _obs(int(census_row["outbound_fk_count"])),
        "dependent_objects": deps_fact,
        "row_estimate": _obs(int(row_est)) if row_est is not None else _na("no row estimate for this relkind"),
        "advisor_findings": _no("advisor findings are sourced from the Supabase advisor API, not the SQL census"),
        "consumer_evidence": {
            "observation_window": {"started_at": now, "ended_at": now},
            "database_deps": ddeps_dim,
            "static_repo": _cdim("not_observed", "supplied by the consumer-evidence workflow"),
            "runtime_logs": _cdim("not_observed", "supplied by the consumer-evidence workflow"),
            "external_clients": _cdim("not_observed", "supplied by the consumer-evidence workflow"),
            "operator_declaration": _cdim("not_observed", "supplied by the consumer-evidence workflow"),
        },
    }


def build_snapshot(census_rows, privs_by_oid, deps_by_oid, failed_groups, *,
                   project_ref, repo_sha, now, target_identity, validate=True):
    relations = []
    for row in census_rows:
        oid = f"{row['schema']}.{row['name']}"
        relations.append(build_relation_observation(row, privs_by_oid.get(oid), deps_by_oid.get(oid), failed_groups, now))
    snapshot = {
        "kind": "evidence_snapshot", "project_ref": project_ref, "observed_at": now, "repo_sha": repo_sha,
        "collector_version": COLLECTOR_VERSION, "query_bundle_sha256": query_bundle_sha256(),
        "relation_count": len(relations), "generator": f"collect_disposition/{COLLECTOR_VERSION}",
        "target_identity": target_identity, "relations": relations,
    }
    if validate:
        errs = _validate(snapshot)
        if errs:
            raise ValueError(f"collector produced a schema-invalid snapshot: {errs[0]}")
    return snapshot


def _validate(snapshot):
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)
    v = Draft202012Validator(schema, format_checker=FormatChecker())
    return [f"{'/'.join(str(p) for p in e.path)}: {e.message}" for e in sorted(v.iter_errors(snapshot), key=lambda e: str(e.path))]


# ---- target guard (pure; offline-testable) ---------------------------------
def evaluate_target_guard(ti_row, *, expect_database=None, required_role_markers=(), require_read_only=True):
    """From a raw target_identity row, produce (target_identity_dict, ok, reasons). ok is False when
    the session is not read-only, the database is not the expected one, or a required platform role
    marker is absent. Fail-closed: the collector RAISES on ok=False and emits no snapshot."""
    ro_raw = ti_row.get("transaction_read_only")
    read_only = ro_raw is True or (isinstance(ro_raw, str) and ro_raw.strip().lower() == "on")
    markers = sorted({m for m in (ti_row.get("platform_role_markers") or [])})
    reasons = []
    if require_read_only and not read_only:
        reasons.append("session is not read-only")
    if expect_database is not None and ti_row.get("current_database") != expect_database:
        reasons.append("current_database does not match --expect-database")
    missing = [m for m in required_role_markers if m not in markers]
    if missing:
        reasons.append("missing required platform role markers: " + ",".join(sorted(missing)))
    ok = not reasons
    target_identity = {
        "current_database": ti_row.get("current_database") or "",
        "current_user": ti_row.get("current_user") or "",
        "server_version": ti_row.get("server_version") or "",
        "server_version_num": ti_row.get("server_version_num"),
        "transaction_read_only": bool(read_only),
        "expected_database": expect_database,
        "platform_role_markers": markers,
        "guard_passed": ok,
    }
    return target_identity, ok, reasons


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


# ---- DB orchestration (driven through a plain cursor; offline-testable) -----
def _execute_group(cur, key, sql, params, db_error, failed):
    """Run one OPTIONAL query group under its own SAVEPOINT. On a driver error, roll back JUST this
    group (so the aborted transaction does not poison later groups) and record it as failed."""
    cur.execute("SAVEPOINT sp_" + key)
    try:
        if params is None:
            cur.execute(sql)
        else:
            cur.execute(sql, params)
        rows = cur.fetchall()
        cur.execute("RELEASE SAVEPOINT sp_" + key)
        return rows
    except db_error:
        cur.execute("ROLLBACK TO SAVEPOINT sp_" + key)
        failed.add(key)
        return None


def _collect(cur, schemas, *, db_error, project_ref, repo_sha, expect_database, required_role_markers):
    failed = set()

    # 1. Target identity + guard (MANDATORY). A mismatch raises before anything is built.
    cur.execute(QUERY_BUNDLE["target_identity"])
    ti_cols = [c.name for c in cur.description]
    ti_row = dict(zip(ti_cols, cur.fetchone()))
    observed_at = _iso(ti_row["db_now"])
    target_identity, ok, reasons = evaluate_target_guard(
        ti_row, expect_database=expect_database, required_role_markers=required_role_markers)
    if not ok:
        raise RuntimeError("target guard failed: " + "; ".join(reasons))

    # 2. Role existence (optional). Unknown existence => treat as none initialized (F4).
    role_rows = _execute_group(cur, "roles", QUERY_BUNDLE["roles"], None, db_error, failed)
    existing_roles = None if role_rows is None else {r[0] for r in role_rows}

    # 3. Census (MANDATORY): if this fails there is nothing to census, so let it propagate.
    cur.execute(QUERY_BUNDLE["census"], {"schemas": schemas})
    c_cols = [c.name for c in cur.description]
    census_rows = [dict(zip(c_cols, r)) for r in cur.fetchall()]
    censused_oids = [f"{r['schema']}.{r['name']}" for r in census_rows]

    # 4. Privileges (optional). Manufacture observed-empty ONLY for roles proven to exist (F4).
    priv_rows = _execute_group(cur, "privileges", QUERY_BUNDLE["privileges"], {"schemas": schemas}, db_error, failed)
    privs_by_oid = {}
    if "privileges" not in failed:
        for oid, grantee, verb, has in priv_rows:
            if has:
                privs_by_oid.setdefault(oid, {}).setdefault(grantee, []).append(verb)
        init_roles = existing_roles if existing_roles is not None else set()
        for oid in censused_oids:
            entry = privs_by_oid.setdefault(oid, {})
            for role in _TARGET_ROLES:
                if role in init_roles:
                    entry.setdefault(role, [])

    # 5. Dependents (optional): enumerated pg_depend catalog inventory (F1); direction + external-
    #    consumer flag per edge (finding #2 — the flag drives found_consumers, not raw edge count).
    dep_rows = _execute_group(cur, "dependents", QUERY_BUNDLE["dependents"], {"schemas": schemas}, db_error, failed)
    deps_by_oid = {}
    if "dependents" not in failed:
        for oid, dep_type, dep_identity, direction, is_consumer in dep_rows:
            deps_by_oid.setdefault(oid, []).append({
                "object_type": dep_type if dep_type in _DEP_TYPES else "source_reference",
                "identity": dep_identity,
                "direction": direction if direction in ("inbound", "outbound") else "inbound",
                "evidence_type": "pg_depend", "evidence_ref": "query:dependents-v2",
                "_is_consumer": bool(is_consumer),
            })

    return build_snapshot(census_rows, privs_by_oid, deps_by_oid, failed,
                          project_ref=project_ref, repo_sha=repo_sha, now=observed_at,
                          target_identity=target_identity)


def _dsn_contains_project_ref(dsn, project_ref):
    """Bind the DSN to the Supabase project ref with a STRICTLY ANCHORED host/user check
    (finding #6): a DIRECT connection host must be exactly db.<ref>.supabase.co, or a POOLED
    connection must use an approved *.pooler.supabase.com host with user postgres.<ref>. Both URL
    and libpq keyword DSNs are parsed via psycopg's conninfo parser. Value-silent: only host and
    user are inspected; the password is never read or logged. The project ref is a public
    identifier, not a secret. Returns False (=> fail closed) on any parse failure or non-match."""
    ref = (project_ref or "").strip().lower()
    if not ref:
        return False
    host, user, hostaddr = "", "", ""
    try:
        from psycopg.conninfo import conninfo_to_dict  # noqa: PLC0415 -- live-only, PURE parse (no connection)
        info = conninfo_to_dict(dsn)
        host = str(info.get("host") or "").strip().lower()
        user = str(info.get("user") or "").strip().lower()
        hostaddr = str(info.get("hostaddr") or "").strip()
    except Exception:  # noqa: BLE001 -- fall back to URL parsing; never surface the DSN
        pass
    # hostaddr overrides host at connect time, so a DSN naming the right host but connecting to a
    # different IP would pass a host-only bind. Refuse any hostaddr — the host must resolve normally.
    if hostaddr:
        return False
    if not host:
        try:
            from urllib.parse import urlsplit  # noqa: PLC0415
            parts = urlsplit(dsn)
            host = (parts.hostname or "").strip().lower()
            user = (parts.username or "").strip().lower()
        except Exception:  # noqa: BLE001
            return False
    direct = host == f"db.{ref}.supabase.co"
    pooled = host.endswith(".pooler.supabase.com") and user == f"postgres.{ref}"
    return direct or pooled


def collect_from_db(dsn, schemas, *, project_ref, repo_sha, expect_database, required_role_markers=()):
    if not _dsn_contains_project_ref(dsn, project_ref):
        raise RuntimeError(f"DSN host/user identity is not bound to project_ref {project_ref} (refusing to census an unidentified target)")
    if not (expect_database or "").strip():
        raise RuntimeError("expect_database is required (the target guard must assert current_database)")

    import psycopg  # lazy: only needed for the live census run

    with psycopg.connect(dsn) as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            return _collect(cur, schemas, db_error=psycopg.Error, project_ref=project_ref, repo_sha=repo_sha,
                            expect_database=expect_database, required_role_markers=required_role_markers)


# ---- atomic output (F6 + no-overwrite race) ---------------------------------
def write_snapshot(path, snapshot, *, overwrite=False):
    """Publish atomically. No-overwrite uses os.link (atomic create-if-absent — raises
    FileExistsError if the destination exists, with NO check-then-act race). Overwrite uses
    os.replace. Either way the content is fully written + fsync'd to a sibling temp first, so a
    crash mid-write can never leave a partial destination."""
    directory = os.path.dirname(os.path.abspath(path))
    tmp = os.path.join(directory, f".{os.path.basename(path)}.tmp-{os.getpid()}")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, indent=2, sort_keys=True)
            fh.flush()
            os.fsync(fh.fileno())
        if overwrite:
            os.replace(tmp, path)          # atomic overwrite
        else:
            os.link(tmp, path)             # atomic no-clobber publish; raises FileExistsError if present
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _git_head_sha(repo_dir):
    import subprocess  # noqa: PLC0415 -- live-only; keeps the import off the offline path
    try:
        out = subprocess.run(["git", "-C", repo_dir, "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only, target-bound census collector for the disposition ledger.")
    ap.add_argument("--dsn-env", default="DISPOSITION_DSN", help="env var holding the DSN (value-silent; never argv).")
    ap.add_argument("--project-ref", required=True)
    ap.add_argument("--repo-sha", default=None, help="override; default derives from git HEAD of the collector's repo.")
    ap.add_argument("--schemas", default="public", help="comma-separated schema list.")
    ap.add_argument("--expect-database", required=True, help="fail closed unless current_database() matches (e.g. postgres).")
    ap.add_argument("--require-role-markers", default="anon,authenticated,service_role",
                    help="comma-separated platform roles that MUST exist (target guard); empty to disable.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--overwrite", action="store_true", help="permit replacing an existing --out.")
    args = ap.parse_args(argv)

    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        print(f"SP000 collector: env var {args.dsn_env} is not set (DSN is never passed on the command line)", file=sys.stderr)
        return 2
    if os.path.exists(args.out) and not args.overwrite:
        print(f"SP000 collector: refusing to overwrite existing {args.out} (pass --overwrite)", file=sys.stderr)
        return 2
    repo_sha = args.repo_sha or _git_head_sha(os.path.dirname(os.path.abspath(__file__)))
    if not repo_sha:
        print("SP000 collector: could not derive repo SHA from git HEAD (pass --repo-sha)", file=sys.stderr)
        return 2
    schemas = [s.strip() for s in args.schemas.split(",") if s.strip()]
    if not schemas:
        print("SP000 collector: --schemas is empty (refusing to produce an empty census)", file=sys.stderr)
        return 2
    markers = tuple(s.strip() for s in args.require_role_markers.split(",") if s.strip())
    try:
        snapshot = collect_from_db(dsn, schemas, project_ref=args.project_ref, repo_sha=repo_sha,
                                   expect_database=args.expect_database, required_role_markers=markers)
    except RuntimeError as exc:  # guard/logic failures — DSN-free by construction
        print(f"SP000 collector: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 -- driver/connection errors may embed connection info; print TYPE only
        print(f"SP000 collector failed: {type(exc).__name__}", file=sys.stderr)
        return 2
    try:
        write_snapshot(args.out, snapshot, overwrite=args.overwrite)
    except Exception as exc:  # noqa: BLE001 -- fail closed on any publish error (finding #8); DSN-free by construction
        print(f"SP000 collector: failed to publish snapshot ({type(exc).__name__})", file=sys.stderr)
        return 2
    ti = snapshot["target_identity"]
    print(f"=== CENSUS: {snapshot['relation_count']} relations -> {args.out} "
          f"(db={ti['current_database']} user={ti['current_user']} bundle {snapshot['query_bundle_sha256'][:12]}) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
