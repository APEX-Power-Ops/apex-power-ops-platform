#!/usr/bin/env bash
# test_secret_audit_ac8.sh - AC8 fixture test for infra/secret-audit.sh Check 3.
#
# Plants positive (should-FAIL) and negative (should-PASS) records-serving
# config fixtures in a temp dir, points RECORDS_SERVING_GLOBS at it, and runs
# the real secret-audit.sh. Covers keyword-form (user=/role=) DSNs, bypass
# literals, and URL-form DSNs (postgresql://user:pw@host/db). Asserts:
#   - positive fixtures: exit 1, each AC8 rule name is printed
#   - negative fixture (sanctioned role, keyword-form and URL-form): Check 3
#     does NOT flag it
#   - value-silent: none of the planted secret VALUES ever appear in the
#     captured stdout+stderr - only file:line + rule name may appear.
#
# Every planted signature is built by RUNTIME STRING CONCATENATION so this
# tracked test file itself never holds a live signature that Check 2's
# git-grep credential scan would flag.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../../../.." && pwd)"
AUDIT="$ROOT/infra/secret-audit.sh"
if [[ ! -f "$AUDIT" ]]; then
  echo "FATAL: cannot locate infra/secret-audit.sh (ROOT=$ROOT)" >&2; exit 2
fi

fail=0
say() { printf '%s\n' "$*"; }

tmp="$(mktemp -d)"
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT

# ---- build planted signatures via runtime concatenation (no live value here) --
owner="user=""postgres"
admin="user=""records_admin"
sk="sb""_secret_""FAKE0000000000000000"
svc="service""_role"
urlowner="postgresql""://""postgres"":""FAKEPW0000000000""@host/db"
urlpw="FAKEPW0000000000"

# ---- positive fixtures (must be flagged) ---------------------------------
# Fixture filenames are deliberately neutral (fixture_N) so no planted VALUE
# is ever a substring of a path that Check 3 would echo back in a FIND line.
printf 'host=h %s dbname=records\n' "$owner" > "$tmp/fixture_1.conf"
printf 'host=h %s dbname=records\n' "$admin" > "$tmp/fixture_2.conf"
printf '%s\n' "$sk" > "$tmp/fixture_3.conf"
printf '%s\n' "$svc" > "$tmp/fixture_4.conf"
printf 'DATABASE_URL=%s\n' "$urlowner" > "$tmp/fixture_6.conf"

out="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc=$?

if [[ "$rc" == "1" ]]; then
  say "PASS  positive fixtures: exit 1 as expected"
else
  say "FAIL  positive fixtures: expected exit 1, got $rc"; fail=1
fi

for rule in records-serving-non-app-role records-serving-bypass-credential records-serving-url-non-app-role; do
  if printf '%s' "$out" | grep -qF "[rule: $rule]"; then
    say "PASS  rule fired: $rule"
  else
    say "FAIL  rule did not fire: $rule"; fail=1
  fi
done

# ---- URL rule FIND line is bare file:line (like rules a/b), not
# file:line:postgresql://postgres - the tighten strips the matched
# scheme://user token instead of leaving it stuck to the location. ----
urlline="$(printf '%s\n' "$out" | grep -F '[rule: records-serving-url-non-app-role]')"
if printf '%s' "$urlline" | grep -qF "fixture_6.conf:1"; then
  say "PASS  URL rule FIND line carries file:line"
else
  say "FAIL  URL rule FIND line missing file:line"; fail=1
fi
if printf '%s' "$urlline" | grep -qE ':(postgresql|postgres)://'; then
  say "FAIL  URL rule FIND line still carries scheme://user token (not bare file:line)"; fail=1
else
  say "PASS  URL rule FIND line is bare file:line (no scheme://user token)"
fi

# ---- value-silent check: none of the planted VALUES may appear in output --
for val in "$owner" "$admin" "$sk" "$svc" "$urlowner" "$urlpw"; do
  if printf '%s' "$out" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: a planted value leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no planted value appeared in captured output"

# ---- negative fixture: sanctioned role must not be flagged by Check 3 ----
rm -f "$tmp"/*.conf
printf 'host=h user=records_api dbname=records\n' > "$tmp/fixture_5.conf"
urlapi="postgresql""://""records_api"":""FAKEPW0000000000""@host/db"
printf 'DATABASE_URL=%s\n' "$urlapi" > "$tmp/fixture_7.conf"

out2="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"

if printf '%s' "$out2" | grep -qF '[rule: records-serving-non-app-role]'; then
  say "FAIL  sanctioned role (records_api) was incorrectly flagged"; fail=1
else
  say "PASS  sanctioned role (records_api) not flagged"
fi
if printf '%s' "$out2" | grep -qF '[rule: records-serving-bypass-credential]'; then
  say "FAIL  sanctioned fixture unexpectedly tripped bypass-credential rule"; fail=1
else
  say "PASS  sanctioned fixture did not trip bypass-credential rule"
fi
if printf '%s' "$out2" | grep -qF '[rule: records-serving-url-non-app-role]'; then
  say "FAIL  sanctioned URL-form DSN (records_api) was incorrectly flagged"; fail=1
else
  say "PASS  sanctioned URL-form DSN (records_api) not flagged"
fi
if printf '%s' "$out2" | grep -qF -- "$urlapi"; then
  say "FAIL  value-silent violation: sanctioned URL fixture value leaked into output"; fail=1
else
  say "PASS  value-silent: sanctioned URL fixture value absent from output"
fi

# ---- single-file regression: grep must stay value-silent with ONE match ---
# GNU grep omits the filename prefix when exactly one file matches, which
# previously (a) dropped the path from rule (a)'s FIND line and (b) shifted
# cut's fields in rule (b) so the matched line - including the secret VALUE -
# was printed instead of file:line. -H on both grep calls fixes this; this
# case proves it stays fixed.
rm -f "$tmp"/*.conf
svc2="service""_role"
printf 'key=%s\n' "$svc2" > "$tmp/single.conf"

out3="$(RECORDS_SERVING_GLOBS="$tmp/single.conf" bash "$AUDIT" 2>&1)"
rc3=$?

if [[ "$rc3" == "1" ]]; then
  say "PASS  single-file fixture: exit 1 as expected"
else
  say "FAIL  single-file fixture: expected exit 1, got $rc3"; fail=1
fi

if printf '%s' "$out3" | grep -qF '[rule: records-serving-bypass-credential]'; then
  say "PASS  single-file fixture: rule fired"
else
  say "FAIL  single-file fixture: rule did not fire"; fail=1
fi

if printf '%s' "$out3" | grep -qF "$tmp/single.conf"; then
  say "PASS  single-file fixture: file path present in FIND line"
else
  say "FAIL  single-file fixture: file path missing from FIND line"; fail=1
fi

if printf '%s' "$out3" | grep -qF -- "$svc2"; then
  say "FAIL  single-file fixture: value-silent violation - planted value leaked"; fail=1
else
  say "PASS  single-file fixture: planted value absent from captured output"
fi

# ---- whitespace/quote-tolerant fixtures (Codex gap #1) -------------------
# Owner/admin keyword DSNs with normal whitespace around "=" and/or quoted
# values must still be flagged; a sanctioned role in the same forms must not.
rm -f "$tmp"/*.conf
ownersp="user"" = ""postgres"
adminq="user='""records_admin""'"
roleq='role = "'"postgres"'"'
printf 'host=h %s dbname=records\n' "$ownersp" > "$tmp/fixture_8.conf"
printf 'host=h %s dbname=records\n' "$adminq" > "$tmp/fixture_9.conf"
printf 'host=h %s dbname=records\n' "$roleq" > "$tmp/fixture_10.conf"

out4="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc4=$?

if [[ "$rc4" == "1" ]]; then
  say "PASS  whitespace/quoted owner fixtures: exit 1 as expected"
else
  say "FAIL  whitespace/quoted owner fixtures: expected exit 1, got $rc4"; fail=1
fi

for f in fixture_8.conf fixture_9.conf fixture_10.conf; do
  if printf '%s' "$out4" | grep -qF "$f" && printf '%s' "$out4" | grep -qF '[rule: records-serving-non-app-role]'; then
    say "PASS  whitespace/quoted owner form flagged: $f"
  else
    say "FAIL  whitespace/quoted owner form NOT flagged: $f"; fail=1
  fi
done

for val in "$ownersp" "$adminq" "$roleq"; do
  if printf '%s' "$out4" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: whitespace/quoted planted value leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no whitespace/quoted planted value appeared in captured output"

# ---- whitespace-tolerant SANCTIONED fixture must NOT be flagged ----------
rm -f "$tmp"/*.conf
apisp="user"" = ""records_api"
printf 'host=h %s dbname=records\n' "$apisp" > "$tmp/fixture_11.conf"

out5="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc5=$?

if [[ "$rc5" == "0" ]]; then
  say "PASS  whitespace sanctioned fixture: exit 0 as expected"
else
  say "FAIL  whitespace sanctioned fixture: expected exit 0, got $rc5"; fail=1
fi

if printf '%s' "$out5" | grep -qF '[rule: records-serving-non-app-role]'; then
  say "FAIL  whitespace sanctioned role (records_api) was incorrectly flagged"; fail=1
else
  say "PASS  whitespace sanctioned role (records_api) not flagged"
fi

# ---- empty-glob must fail closed (Codex gap #2) --------------------------
rm -f "$tmp"/*.conf
out6="$(RECORDS_SERVING_GLOBS="$tmp/nonexistent-*.conf" bash "$AUDIT" 2>&1)"
rc6=$?

if [[ "$rc6" != "0" ]]; then
  say "PASS  empty-glob: exit nonzero as expected"
else
  say "FAIL  empty-glob: expected nonzero exit, got $rc6"; fail=1
fi

if printf '%s' "$out6" | grep -qF '[rule: records-serving-empty-glob]'; then
  say "PASS  empty-glob: records-serving-empty-glob rule name present"
else
  say "FAIL  empty-glob: records-serving-empty-glob rule name missing"; fail=1
fi

# ---- 3-role allowlist + Supavisor dotted-user + uppercase PGUSER (AC8+) --
# Every signature below is built by runtime concatenation (never a live
# literal in this tracked file). Three NEGATIVE (must not flag) and five
# POSITIVE (must flag records-serving-non-app-role) fixtures.
rm -f "$tmp"/*.conf
auditor="user=""records_auditor"
supavisor_ok="user=""records_api"".""abcdefghijklmnop"
supavisor_multidot="user=""records_api"".""evil"".""postgres"
supavisor_badbase="user=""postgres"".""abcdefghijklmnop"
pguser_ok="PGUSER=""records_api"
pguser_bad="PGUSER=""records_owner"
pguser_upper="PGUSER=""RECORDS_API"
supavisor_mixed="user=""records_API"".""abcdefgh"

printf 'host=h %s dbname=records\n' "$auditor" > "$tmp/fixture_neg_auditor.conf"
printf 'host=h %s dbname=records\n' "$supavisor_ok" > "$tmp/fixture_neg_supavisor_ok.conf"
printf '%s\n' "$pguser_ok" > "$tmp/fixture_neg_pguser_ok.conf"

out7="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc7=$?

if [[ "$rc7" == "0" ]]; then
  say "PASS  3-role/dotted-user negative fixtures: exit 0 as expected"
else
  say "FAIL  3-role/dotted-user negative fixtures: expected exit 0, got $rc7"; fail=1
fi

if printf '%s' "$out7" | grep -qF '[rule: records-serving-non-app-role]'; then
  say "FAIL  negative fixture incorrectly flagged records-serving-non-app-role"; fail=1
else
  say "PASS  negative fixtures (auditor, supavisor_ok, pguser_ok) not flagged"
fi

for val in "$auditor" "$supavisor_ok" "$pguser_ok"; do
  if printf '%s' "$out7" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: negative fixture value leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no negative-fixture value appeared in captured output"

rm -f "$tmp"/*.conf
printf 'host=h %s dbname=records\n' "$supavisor_multidot" > "$tmp/fixture_pos_multidot.conf"
printf 'host=h %s dbname=records\n' "$supavisor_badbase" > "$tmp/fixture_pos_badbase.conf"
printf '%s\n' "$pguser_bad" > "$tmp/fixture_pos_pguser_bad.conf"
printf '%s\n' "$pguser_upper" > "$tmp/fixture_pos_pguser_upper.conf"
printf 'host=h %s dbname=records\n' "$supavisor_mixed" > "$tmp/fixture_pos_mixed.conf"

out8="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc8=$?

if [[ "$rc8" == "1" ]]; then
  say "PASS  3-role/dotted-user positive fixtures: exit 1 as expected"
else
  say "FAIL  3-role/dotted-user positive fixtures: expected exit 1, got $rc8"; fail=1
fi

for f in fixture_pos_multidot.conf fixture_pos_badbase.conf fixture_pos_pguser_bad.conf fixture_pos_pguser_upper.conf fixture_pos_mixed.conf; do
  if printf '%s' "$out8" | grep -qF "$f" && printf '%s' "$out8" | grep -qF '[rule: records-serving-non-app-role]'; then
    say "PASS  positive fixture flagged: $f"
  else
    say "FAIL  positive fixture NOT flagged: $f"; fail=1
  fi
done

for val in "$supavisor_multidot" "$supavisor_badbase" "$pguser_bad" "$pguser_upper" "$supavisor_mixed"; do
  if printf '%s' "$out8" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: positive fixture value leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no positive-fixture value appeared in captured output"

# ---- Finding 1 fix: rule (a) value-capture truncation bypass -------------
# grep -o with a value class of [A-Za-z0-9_.]+ truncates at the first
# out-of-class char, so a sanctioned-role PREFIX followed by an out-of-class
# suffix (-, %, @, a space inside quotes) was silently truncated to the
# sanctioned prefix and then wrongly sanctioned by the allowlist's "$"
# anchor. "-" is a legal Postgres role-name char, so these are distinct,
# non-sanctioned roles that must be flagged. Five POSITIVE + a value-silence
# guard fixture + two quoted NEGATIVE fixtures.
rm -f "$tmp"/*.conf
dq='"'
bypass_dash="user=""records_api""-""super"
bypass_dash2="user=""records_api""-""owner"
bypass_pct="user=""records_api""%""owner"
bypass_at="user=""records_api""@""evil"
bypass_quoted="user=""${dq}""records_api evil""${dq}"

printf 'host=h %s dbname=records\n' "$bypass_dash" > "$tmp/fixture_bypass_dash.conf"
printf 'host=h %s dbname=records\n' "$bypass_dash2" > "$tmp/fixture_bypass_dash2.conf"
printf 'host=h %s dbname=records\n' "$bypass_pct" > "$tmp/fixture_bypass_pct.conf"
printf 'host=h %s dbname=records\n' "$bypass_at" > "$tmp/fixture_bypass_at.conf"
printf 'host=h %s dbname=records\n' "$bypass_quoted" > "$tmp/fixture_bypass_quoted.conf"

out9="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc9=$?

if [[ "$rc9" == "1" ]]; then
  say "PASS  value-truncation bypass fixtures: exit 1 as expected"
else
  say "FAIL  value-truncation bypass fixtures: expected exit 1, got $rc9"; fail=1
fi

for f in fixture_bypass_dash.conf fixture_bypass_dash2.conf fixture_bypass_pct.conf fixture_bypass_at.conf fixture_bypass_quoted.conf; do
  if printf '%s' "$out9" | grep -qF "$f" && printf '%s' "$out9" | grep -qF '[rule: records-serving-non-app-role]'; then
    say "PASS  value-truncation bypass flagged: $f"
  else
    say "FAIL  value-truncation bypass NOT flagged (bug present or regression): $f"; fail=1
  fi
done

for val in "$bypass_dash" "$bypass_dash2" "$bypass_pct" "$bypass_at" "$bypass_quoted"; do
  if printf '%s' "$out9" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: bypass fixture value leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no value-truncation bypass fixture value appeared in captured output"

# ---- Finding 1 value-silence guard: flagged bypass row + trailing password --
# The fixed value-capture must consume the WHOLE value token and then STOP
# before a following password field, so the planted password is still never
# printed even though the row is (correctly) flagged.
rm -f "$tmp"/*.conf
guard_pw="GUARDPW0000000000"
guard_line="user=""records_api""-""super"" password=""$guard_pw"
printf 'host=h %s dbname=records\n' "$guard_line" > "$tmp/fixture_guard.conf"

out10="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc10=$?

if [[ "$rc10" == "1" ]]; then
  say "PASS  value-silence guard fixture: exit 1 as expected"
else
  say "FAIL  value-silence guard fixture: expected exit 1, got $rc10"; fail=1
fi

if printf '%s' "$out10" | grep -qF "fixture_guard.conf" && printf '%s' "$out10" | grep -qF '[rule: records-serving-non-app-role]'; then
  say "PASS  value-silence guard fixture flagged"
else
  say "FAIL  value-silence guard fixture NOT flagged"; fail=1
fi

if printf '%s' "$out10" | grep -qF -- "$guard_pw"; then
  say "FAIL  value-silent violation: planted password leaked into Check 3 output"; fail=1
else
  say "PASS  value-silent: planted password absent from Check 3 output"
fi

# ---- Finding 1 NEGATIVE: legit quoted sanctioned forms still pass ---------
rm -f "$tmp"/*.conf
quoted_api="user=""${dq}""records_api""${dq}"
quoted_ref="user=""${dq}""records_api"".""abcdefghijklmnop""${dq}"
printf 'host=h %s dbname=records\n' "$quoted_api" > "$tmp/fixture_quoted_api.conf"
printf 'host=h %s dbname=records\n' "$quoted_ref" > "$tmp/fixture_quoted_ref.conf"

out11="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc11=$?

if [[ "$rc11" == "0" ]]; then
  say "PASS  quoted sanctioned negative fixtures: exit 0 as expected"
else
  say "FAIL  quoted sanctioned negative fixtures: expected exit 0, got $rc11"; fail=1
fi

if printf '%s' "$out11" | grep -qF '[rule: records-serving-non-app-role]'; then
  say "FAIL  quoted sanctioned form incorrectly flagged"; fail=1
else
  say "PASS  quoted sanctioned forms (records_api, records_api.ref) not flagged"
fi

for val in "$quoted_api" "$quoted_ref"; do
  if printf '%s' "$out11" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: quoted negative fixture value leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no quoted negative fixture value appeared in captured output"

# ---- Finding 2: rule (c) URL-form has no fixtures -------------------------
# The rule (c) allowlist was widened to the 3-role form but had zero
# URL-form fixtures, so a regression there would go uncaught. Three
# POSITIVE + two NEGATIVE URL-form fixtures, all value-silent.
rm -f "$tmp"/*.conf
url_dotted_evil="postgresql""://""records_api"".""evil"".""postgres"":""URLPW0000000000""@host:5432/db"
url_owner="postgresql""://""postgres"":""URLPW0000000000""@host:5432/db"
url_upper="postgresql""://""RECORDS_API"":""URLPW0000000000""@host:5432/db"
url_pw="URLPW0000000000"

printf 'DATABASE_URL=%s\n' "$url_dotted_evil" > "$tmp/fixture_url_dotted_evil.conf"
printf 'DATABASE_URL=%s\n' "$url_owner" > "$tmp/fixture_url_owner.conf"
printf 'DATABASE_URL=%s\n' "$url_upper" > "$tmp/fixture_url_upper.conf"

out12="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc12=$?

if [[ "$rc12" == "1" ]]; then
  say "PASS  URL-form positive fixtures: exit 1 as expected"
else
  say "FAIL  URL-form positive fixtures: expected exit 1, got $rc12"; fail=1
fi

for f in fixture_url_dotted_evil.conf fixture_url_owner.conf fixture_url_upper.conf; do
  if printf '%s' "$out12" | grep -qF "$f" && printf '%s' "$out12" | grep -qF '[rule: records-serving-url-non-app-role]'; then
    say "PASS  URL-form positive fixture flagged: $f"
  else
    say "FAIL  URL-form positive fixture NOT flagged: $f"; fail=1
  fi
done

for val in "$url_dotted_evil" "$url_owner" "$url_upper" "$url_pw"; do
  if printf '%s' "$out12" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: URL-form positive fixture value leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no URL-form positive fixture value (incl. password) appeared in captured output"

rm -f "$tmp"/*.conf
url_auditor="postgresql""://""records_auditor"":""URLPW0000000000""@host:5432/db"
url_ref_ok="postgresql""://""records_api"".""abcdefghijklmnop"":""URLPW0000000000""@host:5432/db"

printf 'DATABASE_URL=%s\n' "$url_auditor" > "$tmp/fixture_url_auditor.conf"
printf 'DATABASE_URL=%s\n' "$url_ref_ok" > "$tmp/fixture_url_ref_ok.conf"

out13="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc13=$?

if [[ "$rc13" == "0" ]]; then
  say "PASS  URL-form negative fixtures: exit 0 as expected"
else
  say "FAIL  URL-form negative fixtures: expected exit 0, got $rc13"; fail=1
fi

if printf '%s' "$out13" | grep -qF '[rule: records-serving-url-non-app-role]'; then
  say "FAIL  URL-form negative fixture incorrectly flagged"; fail=1
else
  say "PASS  URL-form negative fixtures (records_auditor, records_api.ref) not flagged"
fi

for val in "$url_auditor" "$url_ref_ok" "$url_pw"; do
  if printf '%s' "$out13" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: URL-form negative fixture value leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no URL-form negative fixture value (incl. password) appeared in captured output"

# ---- TERMINAL FIX: residual truncation + colon-leak + substring-key + driver URLs --
# The prior widening left three holes and one CRITICAL leak, all closed here.
# Every planted signature is built by runtime concatenation (no live literal).

# (T1) Rule (a) residual truncation POSITIVES: ";" and "," in the value were
# excluded by the old class and silently dropped the non-sanctioned suffix, so
# these bypassed the allowlist. The whole-token value class now captures them.
rm -f "$tmp"/*.conf
tf_semi="user=""records_api"";""super"
tf_comma="user=""records_api"",""super"
tf_quotejunk="user=""${dq}""records_api""${dq}""evil""${dq}"
printf 'host=h %s dbname=records\n' "$tf_semi" > "$tmp/fixture_tf_semi.conf"
printf 'host=h %s dbname=records\n' "$tf_comma" > "$tmp/fixture_tf_comma.conf"
printf 'host=h %s dbname=records\n' "$tf_quotejunk" > "$tmp/fixture_tf_quotejunk.conf"

out_tf1="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc_tf1=$?

if [[ "$rc_tf1" == "1" ]]; then
  say "PASS  terminal residual-truncation positives: exit 1 as expected"
else
  say "FAIL  terminal residual-truncation positives: expected exit 1, got $rc_tf1"; fail=1
fi

for f in fixture_tf_semi.conf fixture_tf_comma.conf fixture_tf_quotejunk.conf; do
  if printf '%s' "$out_tf1" | grep -qF "$f" && printf '%s' "$out_tf1" | grep -qF '[rule: records-serving-non-app-role]'; then
    say "PASS  terminal residual-truncation flagged: $f"
  else
    say "FAIL  terminal residual-truncation NOT flagged (bug present or regression): $f"; fail=1
  fi
done

for val in "$tf_semi" "$tf_comma" "$tf_quotejunk"; do
  if printf '%s' "$out_tf1" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: residual-truncation fixture value leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no residual-truncation fixture value appeared in captured output"

# (T2) CRITICAL colon-leak guard: a colon-joined "role:secret:port" value must
# FLAG and the planted SENTINEL must be ABSENT (the old sed left the sentinel
# stuck to the FIND line; the bare file:line emit closes this content-blind).
rm -f "$tmp"/*.conf
tf_sentinel="SENTINELCOLON000"
tf_colon="user=""records_api""-""super"":""$tf_sentinel"":""5432"
printf '%s\n' "$tf_colon" > "$tmp/fixture_tf_colon.conf"

out_tf2="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc_tf2=$?

if [[ "$rc_tf2" == "1" ]]; then
  say "PASS  terminal colon-leak guard: exit 1 as expected"
else
  say "FAIL  terminal colon-leak guard: expected exit 1, got $rc_tf2"; fail=1
fi

if printf '%s' "$out_tf2" | grep -qF "fixture_tf_colon.conf" && printf '%s' "$out_tf2" | grep -qF '[rule: records-serving-non-app-role]'; then
  say "PASS  terminal colon-leak guard flagged"
else
  say "FAIL  terminal colon-leak guard NOT flagged"; fail=1
fi

if printf '%s' "$out_tf2" | grep -qF -- "$tf_sentinel"; then
  say "FAIL  value-silent violation (CRITICAL): colon-joined SENTINEL leaked into Check 3 output"; fail=1
else
  say "PASS  value-silent: colon-joined SENTINEL absent from Check 3 output"
fi

# (T3) SUBSTRING-KEY negatives: DB_USER / SUPER_USER must NOT be scanned (the
# \b anchor does not match inside a larger key) AND must NOT leak, even though
# their value is a non-sanctioned role joined with a sentinel.
rm -f "$tmp"/*.conf
tf_sentdb="SENTINELDB00000"
tf_dbuser="DB_USER=""records_owner"":""$tf_sentdb"":""5432"
tf_superuser="SUPER_USER=""records_api""-""super"":""$tf_sentdb"":""5432"
printf '%s\n' "$tf_dbuser" > "$tmp/fixture_tf_dbuser.conf"
printf '%s\n' "$tf_superuser" > "$tmp/fixture_tf_superuser.conf"

out_tf3="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc_tf3=$?

if [[ "$rc_tf3" == "0" ]]; then
  say "PASS  terminal substring-key negatives: exit 0 as expected"
else
  say "FAIL  terminal substring-key negatives: expected exit 0, got $rc_tf3"; fail=1
fi

if printf '%s' "$out_tf3" | grep -qF '[rule: records-serving-non-app-role]'; then
  say "FAIL  substring-key (DB_USER/SUPER_USER) was incorrectly scanned/flagged"; fail=1
else
  say "PASS  substring-key (DB_USER/SUPER_USER) not scanned/flagged"
fi

if printf '%s' "$out_tf3" | grep -qF -- "$tf_sentdb"; then
  say "FAIL  value-silent violation: substring-key SENTINEL leaked into output"; fail=1
else
  say "PASS  value-silent: substring-key SENTINEL absent from output"
fi

# (T4) PGUSER positive (owner) - keyword-form uppercase key, non-sanctioned role.
rm -f "$tmp"/*.conf
tf_pguser_owner="PGUSER=""records_owner"
printf '%s\n' "$tf_pguser_owner" > "$tmp/fixture_tf_pguser_owner.conf"

out_tf4="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc_tf4=$?

if [[ "$rc_tf4" == "1" ]] && printf '%s' "$out_tf4" | grep -qF "fixture_tf_pguser_owner.conf" && printf '%s' "$out_tf4" | grep -qF '[rule: records-serving-non-app-role]'; then
  say "PASS  terminal PGUSER=records_owner flagged"
else
  say "FAIL  terminal PGUSER=records_owner NOT flagged (rc=$rc_tf4)"; fail=1
fi

# (T5) Keyword-form NEGATIVES that must still PASS after the widening: bare
# sanctioned role, quoted sanctioned role, and a dotted sanctioned ref.
rm -f "$tmp"/*.conf
tf_neg_bare="user=""records_api"
tf_neg_quoted="user=""${dq}""records_api""${dq}"
tf_neg_dot="user=""records_api"".""abcdefghijklmnop"
printf 'host=h %s dbname=records\n' "$tf_neg_bare" > "$tmp/fixture_tf_neg_bare.conf"
printf 'host=h %s dbname=records\n' "$tf_neg_quoted" > "$tmp/fixture_tf_neg_quoted.conf"
printf 'host=h %s dbname=records\n' "$tf_neg_dot" > "$tmp/fixture_tf_neg_dot.conf"

out_tf5="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc_tf5=$?

if [[ "$rc_tf5" == "0" ]]; then
  say "PASS  terminal keyword-form negatives: exit 0 as expected"
else
  say "FAIL  terminal keyword-form negatives: expected exit 0, got $rc_tf5"; fail=1
fi

if printf '%s' "$out_tf5" | grep -qF '[rule: records-serving-non-app-role]'; then
  say "FAIL  terminal keyword-form sanctioned role incorrectly flagged"; fail=1
else
  say "PASS  terminal keyword-form sanctioned roles not flagged"
fi

# (T6) Rule (c) driver-qualified POSITIVES: postgresql+asyncpg:// and
# postgresql+psycopg:// with non-sanctioned userinfo roles must FLAG (P2), and
# an unqualified evil-dotted role too. Planted PW must be ABSENT.
rm -f "$tmp"/*.conf
tf_urlpw="URLPWTERM000000"
tf_url_asyncpg="postgresql""+asyncpg""://""records_owner"":""$tf_urlpw""@host/db"
tf_url_psycopg="postgresql""+psycopg""://""service_role"":""$tf_urlpw""@host/db"
tf_url_plain="postgresql""://""postgres"":""$tf_urlpw""@host/db"
tf_url_dotevil="postgresql""://""records_api"".""evil"".""postgres"":""$tf_urlpw""@host/db"
printf 'DATABASE_URL=%s\n' "$tf_url_asyncpg" > "$tmp/fixture_tf_url_asyncpg.conf"
printf 'DATABASE_URL=%s\n' "$tf_url_psycopg" > "$tmp/fixture_tf_url_psycopg.conf"
printf 'DATABASE_URL=%s\n' "$tf_url_plain" > "$tmp/fixture_tf_url_plain.conf"
printf 'DATABASE_URL=%s\n' "$tf_url_dotevil" > "$tmp/fixture_tf_url_dotevil.conf"

out_tf6="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc_tf6=$?

if [[ "$rc_tf6" == "1" ]]; then
  say "PASS  terminal driver-URL positives: exit 1 as expected"
else
  say "FAIL  terminal driver-URL positives: expected exit 1, got $rc_tf6"; fail=1
fi

for f in fixture_tf_url_asyncpg.conf fixture_tf_url_psycopg.conf fixture_tf_url_plain.conf fixture_tf_url_dotevil.conf; do
  if printf '%s' "$out_tf6" | grep -qF "$f" && printf '%s' "$out_tf6" | grep -qF '[rule: records-serving-url-non-app-role]'; then
    say "PASS  terminal driver-URL positive flagged: $f"
  else
    say "FAIL  terminal driver-URL positive NOT flagged (bug present or regression): $f"; fail=1
  fi
done

# bypass-credential rule also fires on service_role fixture; that is expected
# and does not affect the url-non-app-role assertions above.
for val in "$tf_url_asyncpg" "$tf_url_psycopg" "$tf_url_plain" "$tf_url_dotevil" "$tf_urlpw"; do
  if printf '%s' "$out_tf6" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: driver-URL positive fixture value (incl. PW) leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no driver-URL positive fixture value (incl. PW) appeared in captured output"

# (T7) Rule (c) driver-qualified NEGATIVE: postgresql+asyncpg:// with a
# sanctioned role must NOT flag. Planted PW must be ABSENT.
rm -f "$tmp"/*.conf
tf_url_ok="postgresql""+asyncpg""://""records_api"":""$tf_urlpw""@host/db"
printf 'DATABASE_URL=%s\n' "$tf_url_ok" > "$tmp/fixture_tf_url_ok.conf"

out_tf7="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc_tf7=$?

if [[ "$rc_tf7" == "0" ]]; then
  say "PASS  terminal driver-URL sanctioned negative: exit 0 as expected"
else
  say "FAIL  terminal driver-URL sanctioned negative: expected exit 0, got $rc_tf7"; fail=1
fi

if printf '%s' "$out_tf7" | grep -qF '[rule: records-serving-url-non-app-role]'; then
  say "FAIL  driver-qualified sanctioned URL (records_api) incorrectly flagged"; fail=1
else
  say "PASS  driver-qualified sanctioned URL (records_api) not flagged"
fi

if printf '%s' "$out_tf7" | grep -qF -- "$tf_url_ok" || printf '%s' "$out_tf7" | grep -qF -- "$tf_urlpw"; then
  say "FAIL  value-silent violation: driver-URL sanctioned negative value leaked into output"; fail=1
else
  say "PASS  value-silent: driver-URL sanctioned negative value absent from output"
fi

# (T8) SCHEME-CASE fix: rule (c)'s URL scheme match was case-SENSITIVE, so a
# mixed/upper-case scheme (POSTGRESQL://, PostgreSQL://) evaded detection even
# though RFC 3986 schemes are case-insensitive and libpq/SQLAlchemy accept
# them. Three POSITIVES (upper scheme + owner role, mixed scheme + owner role,
# upper scheme + upper role value - must still flag) and one NEGATIVE (mixed
# scheme + sanctioned role, lowercase - must still pass, proving the fix does
# NOT case-fold the role alternation). Planted PW must be ABSENT throughout.
rm -f "$tmp"/*.conf
tf_urlpw_case="URLPWCASE0000000"
tf_url_upper_owner="POSTGRESQL""://""records_owner"":""$tf_urlpw_case""@host/db"
tf_url_mixed_owner="PostgreSQL""://""records_owner"":""$tf_urlpw_case""@host/db"
tf_url_upper_role="POSTGRESQL""://""RECORDS_API"":""$tf_urlpw_case""@host/db"
printf 'DATABASE_URL=%s\n' "$tf_url_upper_owner" > "$tmp/fixture_tf_url_upper_owner.conf"
printf 'DATABASE_URL=%s\n' "$tf_url_mixed_owner" > "$tmp/fixture_tf_url_mixed_owner.conf"
printf 'DATABASE_URL=%s\n' "$tf_url_upper_role" > "$tmp/fixture_tf_url_upper_role.conf"

out_tf8="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc_tf8=$?

if [[ "$rc_tf8" == "1" ]]; then
  say "PASS  scheme-case positives: exit 1 as expected"
else
  say "FAIL  scheme-case positives: expected exit 1, got $rc_tf8"; fail=1
fi

for f in fixture_tf_url_upper_owner.conf fixture_tf_url_mixed_owner.conf fixture_tf_url_upper_role.conf; do
  if printf '%s' "$out_tf8" | grep -qF "$f" && printf '%s' "$out_tf8" | grep -qF '[rule: records-serving-url-non-app-role]'; then
    say "PASS  scheme-case positive flagged: $f"
  else
    say "FAIL  scheme-case positive NOT flagged (miss present or regression): $f"; fail=1
  fi
done

for val in "$tf_url_upper_owner" "$tf_url_mixed_owner" "$tf_url_upper_role" "$tf_urlpw_case"; do
  if printf '%s' "$out_tf8" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: scheme-case positive fixture value leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no scheme-case positive fixture value appeared in captured output"

# (T9) SCHEME-CASE NEGATIVE: mixed-case scheme with a sanctioned (lowercase)
# role must still PASS - proves the scheme case-fold does not also case-fold
# the role alternation (a naive global -i would wrongly sanction
# POSTGRESQL://RECORDS_API too; that must stay flagged, per T8 above).
rm -f "$tmp"/*.conf
tf_url_mixed_ok="PostgreSQL""://""records_api"":""$tf_urlpw_case""@host/db"
printf 'DATABASE_URL=%s\n' "$tf_url_mixed_ok" > "$tmp/fixture_tf_url_mixed_ok.conf"

out_tf9="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc_tf9=$?

if [[ "$rc_tf9" == "0" ]]; then
  say "PASS  scheme-case sanctioned negative: exit 0 as expected"
else
  say "FAIL  scheme-case sanctioned negative: expected exit 0, got $rc_tf9"; fail=1
fi

if printf '%s' "$out_tf9" | grep -qF '[rule: records-serving-url-non-app-role]'; then
  say "FAIL  mixed-scheme sanctioned URL (records_api) incorrectly flagged"; fail=1
else
  say "PASS  mixed-scheme sanctioned URL (records_api) not flagged"
fi

if printf '%s' "$out_tf9" | grep -qF -- "$tf_url_mixed_ok" || printf '%s' "$out_tf9" | grep -qF -- "$tf_urlpw_case"; then
  say "FAIL  value-silent violation: scheme-case sanctioned negative value leaked into output"; fail=1
else
  say "PASS  value-silent: scheme-case sanctioned negative value absent from output"
fi

if [[ "$fail" == "0" ]]; then
  say "RESULT: AC8 fixture test PASSED"
  exit 0
else
  say "RESULT: AC8 fixture test FAILED"
  exit 1
fi
