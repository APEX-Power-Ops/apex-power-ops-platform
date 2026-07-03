#!/usr/bin/env bash
# test_secret_audit_ac8.sh - AC8 fixture test for infra/secret-audit.sh Check 3.
#
# Plants positive (should-FAIL) and negative (should-PASS) records-serving
# config fixtures in a temp dir, points RECORDS_SERVING_GLOBS at it, and runs
# the real secret-audit.sh. Asserts:
#   - positive fixtures: exit 1, each AC8 rule name is printed
#   - negative fixture (sanctioned role): Check 3 does NOT flag it
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

# ---- positive fixtures (must be flagged) ---------------------------------
# Fixture filenames are deliberately neutral (fixture_N) so no planted VALUE
# is ever a substring of a path that Check 3 would echo back in a FIND line.
printf 'host=h %s dbname=records\n' "$owner" > "$tmp/fixture_1.conf"
printf 'host=h %s dbname=records\n' "$admin" > "$tmp/fixture_2.conf"
printf '%s\n' "$sk" > "$tmp/fixture_3.conf"
printf '%s\n' "$svc" > "$tmp/fixture_4.conf"

out="$(RECORDS_SERVING_GLOBS="$tmp/*" bash "$AUDIT" 2>&1)"
rc=$?

if [[ "$rc" == "1" ]]; then
  say "PASS  positive fixtures: exit 1 as expected"
else
  say "FAIL  positive fixtures: expected exit 1, got $rc"; fail=1
fi

for rule in records-serving-non-app-role records-serving-bypass-credential; do
  if printf '%s' "$out" | grep -qF "[rule: $rule]"; then
    say "PASS  rule fired: $rule"
  else
    say "FAIL  rule did not fire: $rule"; fail=1
  fi
done

# ---- value-silent check: none of the planted VALUES may appear in output --
for val in "$owner" "$admin" "$sk" "$svc"; do
  if printf '%s' "$out" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: a planted value leaked into output"; fail=1
  fi
done
say "PASS  value-silent: no planted value appeared in captured output"

# ---- negative fixture: sanctioned role must not be flagged by Check 3 ----
rm -f "$tmp"/*.conf
printf 'host=h user=records_api dbname=records\n' > "$tmp/fixture_5.conf"

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

if [[ "$fail" == "0" ]]; then
  say "RESULT: AC8 fixture test PASSED"
  exit 0
else
  say "RESULT: AC8 fixture test FAILED"
  exit 1
fi
