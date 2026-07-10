#!/bin/sh
# run_updownup_test.sh -- disposable-DB up/down/up proof for schema-placement A1/A2/A3.
# POSIX sh. Self-contained: resolves every input by absolute path from its own location,
# so it runs from any working directory (no manual aliases/symlinks). Talks to a running
# postgres container over `docker exec` (default apex-dev-pg / postgres:17; override with
# SP01_PGC, e.g. a disposable postgres:16 to match prod's major).
# Value-silent: throwaway dev DBs, no secrets. Every psql uses -v ON_ERROR_STOP=1.
# Each case runs in a FRESH disposable DB (createdb/dropdb, name suffix _$$_<case>).
# Scratch outputs go to a mktemp WORK dir (never the repo). ALWAYS drop on exit.
#
# SCOPE OF THE FINGERPRINT PROOF (honest framing):
#   The fingerprint is a TRACKED-OBJECT match, NOT a complete database-state restore.
#   After up->down, A3's rollback intentionally leaves the (now empty) `archive` schema,
#   its comment, and its default-privilege grants in place (it does not DROP SCHEMA).
#   Those schema-level artifacts are out of the tracked-object fingerprint scope by design.
set -u
unset CDPATH  # neutralize CDPATH so `cd` in path resolution never prints/redirects

CID="${SP01_PGC:-apex-dev-pg}"
SU="postgres"
PID="$$"
DB1="sp01_udu_${PID}_c1"
DB2="sp01_uku_${PID}_c2"
DB3="sp01_neg_${PID}_c3"
LEAK="sp01_leak_${PID}"

# --- self-contained path resolution ----------------------------------------
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd -P)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../../../.." && pwd -P)

FIXTURE="$SCRIPT_DIR/fixture.sql"
FIXTURE7="$SCRIPT_DIR/fixture_7th.sql"
FINGERPRINT="$SCRIPT_DIR/fingerprint.sql"

CPM="$REPO_ROOT/apps/control-plane-api/supabase/migrations"
A1="$CPM/20260710_000012_harden_mcp_public_exposure_core.sql"
A1RB="$CPM/20260710_000012_harden_mcp_public_exposure_core.rollback.sql"
A2="$CPM/20260710_000013_retire_mcp_authenticated_contract.sql"
A2RB="$CPM/20260710_000013_retire_mcp_authenticated_contract.rollback.sql"
SPM="$REPO_ROOT/infra/database/migrations/schema-placement"
A3="$SPM/20260710_000001_archive_relocate_scratch.sql"
A3RB="$SPM/20260710_000001_archive_relocate_scratch.rollback.sql"

WORK=$(mktemp -d "${TMPDIR:-/tmp}/sp01_udu.XXXXXX")

FAILS=0
fail() { FAILS=$((FAILS+1)); echo "  FAIL: $*"; }
ok()   { echo "  ok:   $*"; }

# --- primitives -------------------------------------------------------------
createdb_() { docker exec "$CID" createdb -U "$SU" "$1"; }
dropdb_()   { docker exec "$CID" dropdb   -U "$SU" --if-exists "$1" >/dev/null 2>&1; }

# apply a SQL file (host-side, piped over stdin) as superuser, ON_ERROR_STOP.
run_file() { docker exec -i "$CID" psql -U "$SU" -v ON_ERROR_STOP=1 -X -q -d "$1" < "$2"; }

# scalar query -> stdout (trimmed by caller).
scalar() { docker exec -i "$CID" psql -U "$SU" -tA -X -q -d "$1" -c "$2"; }

# deterministic fingerprint of $1 -> file $2 (host-side).
fp() { docker exec -i "$CID" psql -U "$SU" -tA -X -q -d "$1" < "$FINGERPRINT" > "$2"; }

apply_ok() { # db file label  -- expect exit 0
    if run_file "$1" "$2"; then ok "$3 applied (exit 0)"; else fail "$3 did NOT exit 0 (rc=$?)"; fi
}

expect() { # db label sql expected
    _a=$(scalar "$1" "$3" | tr -d '[:space:]')
    if [ "$_a" = "$4" ]; then ok "$2 (=$_a)"; else fail "$2 expected=$4 got=$_a"; fi
}

# shellcheck disable=SC2317  # body runs from the EXIT/INT/TERM trap, not inline
cleanup_all() { dropdb_ "$DB1"; dropdb_ "$DB2"; dropdb_ "$DB3";
    docker exec -i "$CID" psql -U "$SU" -X -q -d "$SU" -c "DROP ROLE IF EXISTS $LEAK" >/dev/null 2>&1;
    [ -n "${WORK:-}" ] && rm -rf "$WORK"; }
trap cleanup_all EXIT INT TERM

# --- preflight: every input exists, container reachable ---------------------
preflight() {
    _missing=0
    for f in "$FIXTURE" "$FIXTURE7" "$FINGERPRINT" "$A1" "$A1RB" "$A2" "$A2RB" "$A3" "$A3RB"; do
        if [ ! -f "$f" ]; then echo "  MISSING INPUT: $f"; _missing=$((_missing+1)); fi
    done
    if [ "$_missing" -ne 0 ]; then echo "=== PREFLIGHT FAILED: $_missing missing input file(s) ==="; exit 2; fi
    if ! docker exec "$CID" true 2>/dev/null; then
        echo "=== PREFLIGHT FAILED: container '$CID' not reachable (set SP01_PGC) ==="; exit 2; fi
}

# 8 mcp objects (always in public) as a reusable VALUES source.
OBJ8="(VALUES('public.mcp_job_runs'),('public.mcp_lane_priorities'),('public.mcp_local_action_queue'),('public.mcp_review_decisions'),('public.mcp_task_packets'),('public.mcp_validation_artifacts'),('public.mcp_job_run_summary_v'),('public.mcp_task_packet_summary_v'))"
AUTHPOL="'mcp_task_packets_auth_read','mcp_review_decisions_auth_read','mcp_review_decisions_auth_insert_self','mcp_local_action_queue_auth_read_own','mcp_local_action_queue_auth_insert_own','mcp_job_runs_auth_read_requested','mcp_validation_artifacts_auth_read','mcp_lane_priorities_auth_read'"
SVCPOL="'mcp_task_packets_service_all','mcp_review_decisions_service_all','mcp_local_action_queue_service_all','mcp_job_runs_service_all','mcp_validation_artifacts_service_all','mcp_lane_priorities_service_all'"
CMT6="'mcp_job_runs','mcp_lane_priorities','mcp_local_action_queue','mcp_review_decisions','mcp_task_packets','mcp_validation_artifacts'"

# --- shared POST-UP assertions (hardened state) -----------------------------
post_up_checks() { # db prefix
    _db="$1"; _p="$2"
    expect "$_db" "$_p anon+auth NO privilege (0/64) on 8 mcp objects" \
      "SELECT count(*) FROM (VALUES('anon'),('authenticated')) r(role) CROSS JOIN $OBJ8 o(obj) CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb) WHERE has_table_privilege(r.role,o.obj,v.verb)" "0"
    expect "$_db" "$_p 8 authenticated policies DROPPED" \
      "SELECT count(*) FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND p.polname IN ($AUTHPOL)" "0"
    expect "$_db" "$_p 6 *_service_all policies REMAIN" \
      "SELECT count(*) FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND p.polname IN ($SVCPOL)" "6"
    expect "$_db" "$_p 6 comments read 'RETIRED ... 01b-auth'" \
      "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r' AND c.relname IN ($CMT6) AND obj_description(c.oid,'pg_class') LIKE '%RETIRED%' AND obj_description(c.oid,'pg_class') LIKE '%01b-auth%'" "6"
    expect "$_db" "$_p 2 scratch tables now in schema archive" \
      "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind='r' AND n.nspname='archive' AND c.relname IN ('_009_rollback_snapshot','_phase3_load_manifest')" "2"
    expect "$_db" "$_p 0 scratch tables left in public" \
      "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind='r' AND n.nspname='public' AND c.relname IN ('_009_rollback_snapshot','_phase3_load_manifest')" "0"
    expect "$_db" "$_p anon+auth NO privilege on archived scratch tables" \
      "SELECT count(*) FROM pg_class c CROSS JOIN (VALUES('anon'),('authenticated')) r(role) CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb) WHERE c.relkind='r' AND c.relname IN ('_009_rollback_snapshot','_phase3_load_manifest') AND has_table_privilege(r.role,c.oid,v.verb)" "0"
    expect "$_db" "$_p archive schema postgres-owned + anon/auth NO USAGE (A3 schema posture)" \
      "SELECT (SELECT r.rolname FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner WHERE n.nspname='archive')='postgres' AND NOT has_schema_privilege('anon','archive','USAGE') AND NOT has_schema_privilege('authenticated','archive','USAGE')" "t"
    expect "$_db" "$_p apex_tcc_runtime grants UNCHANGED (32/32) on 8 mcp objects" \
      "SELECT count(*) FROM $OBJ8 o(obj) CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb) WHERE has_table_privilege('apex_tcc_runtime',o.obj,v.verb)" "32"
}

# ===========================================================================
# CASE 1 -- 6-table up / down / up
# ===========================================================================
case1() {
    echo "===== CASE 1: 6-table up/down/up  (db=$DB1) ====="
    dropdb_ "$DB1"; createdb_ "$DB1" || { fail "case1 createdb"; return; }
    # (a) load fixture
    if run_file "$DB1" "$FIXTURE"; then ok "fixture.sql loaded"; else fail "case1 fixture load"; dropdb_ "$DB1"; return; fi
    # (b) BASELINE fingerprint
    fp "$DB1" "$WORK/c1_baseline.txt"; ok "baseline fingerprint captured ($(wc -l < "$WORK/c1_baseline.txt") lines)"
    # (c) apply A1,A2,A3 (asserts pass -> exit 0)
    apply_ok "$DB1" "$A1" "case1 A1"
    apply_ok "$DB1" "$A2" "case1 A2"
    apply_ok "$DB1" "$A3" "case1 A3"
    # (d) POST-UP checks
    post_up_checks "$DB1" "case1:"
    # (e) rollback A3,A2,A1 (as postgres) -> exit 0
    apply_ok "$DB1" "$A3RB" "case1 A3.rollback"
    apply_ok "$DB1" "$A2RB" "case1 A2.rollback"
    apply_ok "$DB1" "$A1RB" "case1 A1.rollback"
    # (f) RESTORED fingerprint + tracked-object match diff
    fp "$DB1" "$WORK/c1_restored.txt"
    if diff -u "$WORK/c1_baseline.txt" "$WORK/c1_restored.txt" > "$WORK/c1_fp.diff" 2>&1; then
        ok "case1 tracked-object fingerprint MATCH after up->down (schema-level archive residue -- empty schema + comment + default privs -- intentionally retained by A3 rollback; out of tracked scope)"
    else
        fail "case1 tracked-object fingerprint DIFFERS after up->down (see below)"; sed 's/^/    /' "$WORK/c1_fp.diff"
    fi
    # (g) re-apply A1,A2,A3 (up-down-UP; asserts pass)
    apply_ok "$DB1" "$A1" "case1 re-apply A1"
    apply_ok "$DB1" "$A2" "case1 re-apply A2"
    apply_ok "$DB1" "$A3" "case1 re-apply A3"
    dropdb_ "$DB1"; ok "case1 disposable DB dropped"
}

# ===========================================================================
# CASE 2 -- 7-table (guarded mcp_external_action_audits) up / down / up
# ===========================================================================
case2() {
    echo "===== CASE 2: 7-table up/down/up  (db=$DB2) ====="
    dropdb_ "$DB2"; createdb_ "$DB2" || { fail "case2 createdb"; return; }
    # fixture_7th.sql is a SELF-CONTAINED superset (all of fixture.sql PLUS the 7th
    # table); loading it alone yields the 7-table mini-prod (no duplicate DDL).
    if run_file "$DB2" "$FIXTURE7"; then ok "fixture_7th.sql loaded (7 tables)"; else fail "case2 fixture_7th load"; dropdb_ "$DB2"; return; fi
    # guard sanity: the 7th is born-exposed (anon+auth hold ALL = 8/8)
    expect "$DB2" "case2: 7th born-exposed (anon+auth 8/8) pre-up" \
      "SELECT count(*) FROM (VALUES('anon'),('authenticated')) r(role) CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb) WHERE has_table_privilege(r.role,'public.mcp_external_action_audits',v.verb)" "8"
    fp "$DB2" "$WORK/c2_baseline.txt"; ok "baseline fingerprint captured ($(wc -l < "$WORK/c2_baseline.txt") lines)"
    apply_ok "$DB2" "$A1" "case2 A1"
    apply_ok "$DB2" "$A2" "case2 A2"
    apply_ok "$DB2" "$A3" "case2 A3"
    post_up_checks "$DB2" "case2:"
    # additional: guarded 7th hardened by A1/A2 (anon+auth 0/8)
    expect "$DB2" "case2: guarded 7th HARDENED (anon+auth 0/8) after up" \
      "SELECT count(*) FROM (VALUES('anon'),('authenticated')) r(role) CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb) WHERE has_table_privilege(r.role,'public.mcp_external_action_audits',v.verb)" "0"
    apply_ok "$DB2" "$A3RB" "case2 A3.rollback"
    apply_ok "$DB2" "$A2RB" "case2 A2.rollback"
    apply_ok "$DB2" "$A1RB" "case2 A1.rollback"
    # F3 fail-closed: the A1/A2 rollbacks intentionally do NOT re-grant the born-exposed
    # 7th bootstrap table (a speculative re-grant could re-open exposure on a substrate
    # where 000009 landed after apply). It stays HARDENED (anon+auth 0/8).
    expect "$DB2" "case2: guarded 7th STAYS hardened (anon+auth 0/8) after down [fail-closed]" \
      "SELECT count(*) FROM (VALUES('anon'),('authenticated')) r(role) CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb) WHERE has_table_privilege(r.role,'public.mcp_external_action_audits',v.verb)" "0"
    fp "$DB2" "$WORK/c2_restored.txt"
    # Governed surface (6+2 objects + scratch) must round-trip exactly -- exclude the
    # intentionally-different 7th table from the comparison.
    grep -v 'mcp_external_action_audits' "$WORK/c2_baseline.txt" > "$WORK/c2_baseline_gov.txt"
    grep -v 'mcp_external_action_audits' "$WORK/c2_restored.txt" > "$WORK/c2_restored_gov.txt"
    if diff -u "$WORK/c2_baseline_gov.txt" "$WORK/c2_restored_gov.txt" > "$WORK/c2_fp.diff" 2>&1; then
        ok "case2 governed-surface tracked-object MATCH after up->down (7th intentionally stays hardened; archive residue retained by design)"
    else
        fail "case2 governed-surface fingerprint DIFFERS after up->down (see below)"; sed 's/^/    /' "$WORK/c2_fp.diff"
    fi
    # The ONLY baseline-vs-restored delta must be the 7th table's ACL flipping exposed->hardened.
    _total=$(diff "$WORK/c2_baseline.txt" "$WORK/c2_restored.txt" | grep -Ec '^[<>]')
    _delta=$(diff "$WORK/c2_baseline.txt" "$WORK/c2_restored.txt" | grep -E '^[<>]' | grep -c 'mcp_external_action_audits')
    if [ "$_total" -gt 0 ] && [ "$_delta" -eq "$_total" ]; then
        ok "case2 full-fingerprint delta is EXACTLY the 7th-table posture ($_total lines, all mcp_external_action_audits)"
    else
        fail "case2 unexpected fingerprint delta beyond the 7th table (total=$_total, 7th=$_delta)"
    fi
    apply_ok "$DB2" "$A1" "case2 re-apply A1"
    apply_ok "$DB2" "$A2" "case2 re-apply A2"
    apply_ok "$DB2" "$A3" "case2 re-apply A3"
    dropdb_ "$DB2"; ok "case2 disposable DB dropped"
}

# ===========================================================================
# CASE 3 -- NEGATIVE / atomicity: A1 must ABORT when anon retains an inherited
# privilege, and the abort must be atomic (no partial REVOKE commit).
# ===========================================================================
case3() {
    echo "===== CASE 3: NEGATIVE / atomicity  (db=$DB3) ====="
    dropdb_ "$DB3"; createdb_ "$DB3" || { fail "case3 createdb"; return; }
    if run_file "$DB3" "$FIXTURE"; then ok "fixture.sql loaded"; else fail "case3 fixture load"; dropdb_ "$DB3"; return; fi
    # seed a residual reachable path: anon inherits SELECT on mcp_task_packets via role membership.
    if docker exec -i "$CID" psql -U "$SU" -v ON_ERROR_STOP=1 -X -q -d "$DB3" \
         -c "CREATE ROLE $LEAK NOLOGIN" \
         -c "GRANT SELECT ON public.mcp_task_packets TO $LEAK" \
         -c "GRANT $LEAK TO anon"; then ok "case3 leak role seeded ($LEAK -> anon)"; else fail "case3 leak seed"; fi
    expect "$DB3" "case3: leak active (anon inherits SELECT on mcp_task_packets)" \
      "SELECT has_table_privilege('anon','public.mcp_task_packets','SELECT')" "t"
    # apply A1 -- MUST error, message must contain the core-assert failure string.
    _out=$(docker exec -i "$CID" psql -U "$SU" -v ON_ERROR_STOP=1 -X -q -d "$DB3" < "$A1" 2>&1); _rc=$?
    if [ "$_rc" -ne 0 ] && printf '%s' "$_out" | grep -q '01b-core FAILED: anon retains privilege'; then
        ok "case3 A1 correctly ABORTED (rc=$_rc; assert message present)"
    else
        fail "case3 A1 did not abort as expected (rc=$_rc); output: $_out"
    fi
    # atomicity: A1's REVOKE did not partially commit -- anon STILL holds its
    # original DIRECT grant (all 4 verbs) on mcp_job_runs.
    expect "$DB3" "case3: anon retains 4/4 verbs on mcp_job_runs (rolled back)" \
      "SELECT count(*) FROM (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb) WHERE has_table_privilege('anon','public.mcp_job_runs',v.verb)" "4"
    expect "$DB3" "case3: anon DIRECT grant on mcp_job_runs intact (acl entry present)" \
      "SELECT count(*)>0 FROM pg_class c, aclexplode(c.relacl) a JOIN pg_roles g ON g.oid=a.grantee WHERE c.oid='public.mcp_job_runs'::regclass AND g.rolname='anon'" "t"
    # cleanup leak role (cluster-global) then drop db.
    docker exec -i "$CID" psql -U "$SU" -X -q -d "$DB3" \
      -c "REVOKE SELECT ON public.mcp_task_packets FROM $LEAK" \
      -c "REVOKE $LEAK FROM anon" >/dev/null 2>&1
    docker exec -i "$CID" psql -U "$SU" -X -q -d "$DB3" -c "DROP ROLE IF EXISTS $LEAK" >/dev/null 2>&1 && ok "case3 leak role dropped"
    dropdb_ "$DB3"; ok "case3 disposable DB dropped"
}

# ===========================================================================
preflight
echo "### schema-placement A1/A2/A3 up-down-up proof  (pid=$PID, container=$CID)"
echo "### server_version: $(scalar "$SU" 'SHOW server_version' | tr -d '[:space:]')"
echo "### repo_root: $REPO_ROOT"
case1
case2
case3

echo ""
if [ "$FAILS" -eq 0 ]; then
    echo "=== UPDOWNUP: ALL PASS ==="
    exit 0
else
    echo "=== UPDOWNUP: $FAILS FAILURE(S) ==="
    exit 1
fi
