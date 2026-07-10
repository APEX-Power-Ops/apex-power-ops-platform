#!/bin/sh
# run_updownup_test.sh -- disposable-DB up/down/up proof for schema-placement A1/A2/A3.
# POSIX sh. Runs on the Olares host; talks to the running apex-dev-pg (postgres:17) container.
# Value-silent: throwaway dev DBs, no secrets. Every psql uses -v ON_ERROR_STOP=1.
# Each case runs in a FRESH disposable DB (createdb/dropdb, name suffix _$$_<case>).
# ALWAYS dropdb in cleanup even on failure (per-case drop + EXIT trap safety net).
set -u

CID="apex-dev-pg"
SU="postgres"
PID="$$"
DB1="sp01_udu_${PID}_c1"
DB2="sp01_uku_${PID}_c2"
DB3="sp01_neg_${PID}_c3"
LEAK="sp01_leak_${PID}"

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
fp() { docker exec -i "$CID" psql -U "$SU" -tA -X -q -d "$1" < fingerprint.sql > "$2"; }

apply_ok() { # db file label  -- expect exit 0
    if run_file "$1" "$2"; then ok "$3 applied (exit 0)"; else fail "$3 did NOT exit 0 (rc=$?)"; fi
}

expect() { # db label sql expected
    _a=$(scalar "$1" "$3" | tr -d '[:space:]')
    if [ "$_a" = "$4" ]; then ok "$2 (=$_a)"; else fail "$2 expected=$4 got=$_a"; fi
}

cleanup_all() { dropdb_ "$DB1"; dropdb_ "$DB2"; dropdb_ "$DB3";
    docker exec -i "$CID" psql -U "$SU" -X -q -d "$SU" -c "DROP ROLE IF EXISTS $LEAK" >/dev/null 2>&1; }
trap cleanup_all EXIT INT TERM

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
    if run_file "$DB1" fixture.sql; then ok "fixture.sql loaded"; else fail "case1 fixture load"; dropdb_ "$DB1"; return; fi
    # (b) BASELINE fingerprint
    fp "$DB1" c1_baseline.txt; ok "baseline fingerprint captured ($(wc -l < c1_baseline.txt) lines)"
    # (c) apply A1,A2,A3 (asserts pass -> exit 0)
    apply_ok "$DB1" 000012_A1.sql "case1 A1"
    apply_ok "$DB1" 000013_A2.sql "case1 A2"
    apply_ok "$DB1" 000001_A3.sql "case1 A3"
    # (d) POST-UP checks
    post_up_checks "$DB1" "case1:"
    # (e) rollback A3,A2,A1 (as postgres) -> exit 0
    apply_ok "$DB1" 000001_A3.rollback.sql "case1 A3.rollback"
    apply_ok "$DB1" 000013_A2.rollback.sql "case1 A2.rollback"
    apply_ok "$DB1" 000012_A1.rollback.sql "case1 A1.rollback"
    # (f) RESTORED fingerprint + byte-identical diff
    fp "$DB1" c1_restored.txt
    if diff -u c1_baseline.txt c1_restored.txt > c1_fp.diff 2>&1; then
        ok "case1 fingerprint BYTE-IDENTICAL after up->down"
    else
        fail "case1 fingerprint DIFFERS after up->down (see below)"; sed 's/^/    /' c1_fp.diff
    fi
    # (g) re-apply A1,A2,A3 (up-down-UP; asserts pass)
    apply_ok "$DB1" 000012_A1.sql "case1 re-apply A1"
    apply_ok "$DB1" 000013_A2.sql "case1 re-apply A2"
    apply_ok "$DB1" 000001_A3.sql "case1 re-apply A3"
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
    if run_file "$DB2" fixture_7th.sql; then ok "fixture_7th.sql loaded (7 tables)"; else fail "case2 fixture_7th load"; dropdb_ "$DB2"; return; fi
    # guard sanity: the 7th is born-exposed (anon+auth hold ALL = 8/8)
    expect "$DB2" "case2: 7th born-exposed (anon+auth 8/8) pre-up" \
      "SELECT count(*) FROM (VALUES('anon'),('authenticated')) r(role) CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb) WHERE has_table_privilege(r.role,'public.mcp_external_action_audits',v.verb)" "8"
    fp "$DB2" c2_baseline.txt; ok "baseline fingerprint captured ($(wc -l < c2_baseline.txt) lines)"
    apply_ok "$DB2" 000012_A1.sql "case2 A1"
    apply_ok "$DB2" 000013_A2.sql "case2 A2"
    apply_ok "$DB2" 000001_A3.sql "case2 A3"
    post_up_checks "$DB2" "case2:"
    # additional: guarded 7th hardened by A1/A2 (anon+auth 0/8)
    expect "$DB2" "case2: guarded 7th HARDENED (anon+auth 0/8) after up" \
      "SELECT count(*) FROM (VALUES('anon'),('authenticated')) r(role) CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb) WHERE has_table_privilege(r.role,'public.mcp_external_action_audits',v.verb)" "0"
    apply_ok "$DB2" 000001_A3.rollback.sql "case2 A3.rollback"
    apply_ok "$DB2" 000013_A2.rollback.sql "case2 A2.rollback"
    apply_ok "$DB2" 000012_A1.rollback.sql "case2 A1.rollback"
    # additional: guarded 7th restored by rollback (anon+auth 8/8)
    expect "$DB2" "case2: guarded 7th RESTORED (anon+auth 8/8) after down" \
      "SELECT count(*) FROM (VALUES('anon'),('authenticated')) r(role) CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb) WHERE has_table_privilege(r.role,'public.mcp_external_action_audits',v.verb)" "8"
    fp "$DB2" c2_restored.txt
    if diff -u c2_baseline.txt c2_restored.txt > c2_fp.diff 2>&1; then
        ok "case2 fingerprint BYTE-IDENTICAL after up->down (incl. 7th)"
    else
        fail "case2 fingerprint DIFFERS after up->down (see below)"; sed 's/^/    /' c2_fp.diff
    fi
    apply_ok "$DB2" 000012_A1.sql "case2 re-apply A1"
    apply_ok "$DB2" 000013_A2.sql "case2 re-apply A2"
    apply_ok "$DB2" 000001_A3.sql "case2 re-apply A3"
    dropdb_ "$DB2"; ok "case2 disposable DB dropped"
}

# ===========================================================================
# CASE 3 -- NEGATIVE / atomicity: A1 must ABORT when anon retains an inherited
# privilege, and the abort must be atomic (no partial REVOKE commit).
# ===========================================================================
case3() {
    echo "===== CASE 3: NEGATIVE / atomicity  (db=$DB3) ====="
    dropdb_ "$DB3"; createdb_ "$DB3" || { fail "case3 createdb"; return; }
    if run_file "$DB3" fixture.sql; then ok "fixture.sql loaded"; else fail "case3 fixture load"; dropdb_ "$DB3"; return; fi
    # seed a residual reachable path: anon inherits SELECT on mcp_task_packets via role membership.
    if docker exec -i "$CID" psql -U "$SU" -v ON_ERROR_STOP=1 -X -q -d "$DB3" \
         -c "CREATE ROLE $LEAK NOLOGIN" \
         -c "GRANT SELECT ON public.mcp_task_packets TO $LEAK" \
         -c "GRANT $LEAK TO anon"; then ok "case3 leak role seeded ($LEAK -> anon)"; else fail "case3 leak seed"; fi
    expect "$DB3" "case3: leak active (anon inherits SELECT on mcp_task_packets)" \
      "SELECT has_table_privilege('anon','public.mcp_task_packets','SELECT')" "t"
    # apply A1 -- MUST error, message must contain the core-assert failure string.
    _out=$(docker exec -i "$CID" psql -U "$SU" -v ON_ERROR_STOP=1 -X -q -d "$DB3" < 000012_A1.sql 2>&1); _rc=$?
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
echo "### schema-placement A1/A2/A3 up-down-up proof  (pid=$PID, container=$CID)"
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
