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

if [[ "$fail" == "0" ]]; then
  say "RESULT: AC8 fixture test PASSED"
  exit 0
else
  say "RESULT: AC8 fixture test FAILED"
  exit 1
fi
