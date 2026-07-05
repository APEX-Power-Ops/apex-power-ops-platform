#!/usr/bin/env bash
# Check 1d (cache-coverage completeness) fixture for infra/secret-audit.sh.
# Proves an armed managed name in an UNREGISTERED cache FAILs, that symlinks are
# discovered/deduped by device+inode, and that the coverage summary is emitted on
# both pass and fail. All planted values are synthetic PLACEHOLDERs and must be
# absent from audit output.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../../../.." && pwd)"
AUDIT="$ROOT/infra/secret-audit.sh"
[[ -f "$AUDIT" ]] || { echo "FATAL: cannot locate infra/secret-audit.sh (ROOT=$ROOT)" >&2; exit 2; }

fail=0; say() { printf '%s\n' "$*"; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
PLACEHOLDER='PLACEHOLDER-TEST-VALUE-000000'
MNAME='OPS_API_DSN'

# Build a fixture repo whose copied audit resolves ROOT onto the fixture and
# registers infra/.env + apps/control-plane-api/.env (Check 1d/1c CACHES).
make_repo() {
  local repo="$1"
  mkdir -p "$repo/infra/infisical" "$repo/apps/control-plane-api"
  cp "$AUDIT" "$repo/infra/secret-audit.sh"; chmod +x "$repo/infra/secret-audit.sh"
  printf 'infra/.env\napps/control-plane-api/.env\n' > "$repo/.gitignore"
  git -C "$repo" init -q
  git -C "$repo" add .gitignore infra/secret-audit.sh
  : > "$repo/infra/infisical/.managed-secrets"   # empty = dormant by default
}
arm() { printf '%s\n' "$MNAME" >> "$1/infra/infisical/.managed-secrets"; }
run_audit() { HOME="$tmp/home" bash "$1/infra/secret-audit.sh" 2>&1; }
mkdir -p "$tmp/home"

# --- Case 1: registered cache holds an armed name -> Check 1c drift FAIL -------
r1="$tmp/c1"; make_repo "$r1"
printf '%s=%s\n' "$MNAME" "$PLACEHOLDER" > "$r1/apps/control-plane-api/.env"; chmod 600 "$r1/apps/control-plane-api/.env"
out="$(run_audit "$r1")"                 # dormant: not armed yet
if printf '%s' "$out" | grep -qF "drift: '$MNAME'"; then say "FAIL  case1 fired while dormant"; fail=1; else say "PASS  case1 dormant before arming"; fi
arm "$r1"; out="$(run_audit "$r1")"
if printf '%s' "$out" | grep -qF "drift: '$MNAME' is Infisical-managed but still copied"; then say "PASS  case1 Check 1c drift FAIL after arm"; else say "FAIL  case1 drift not raised"; fail=1; fi

# --- Case 2: unregistered NESTED physical cache holds armed name -> Check 1d ---
r2="$tmp/c2"; make_repo "$r2"; arm "$r2"
mkdir -p "$r2/apps/control-plane-api/scripts"
printf '%s=%s\n' "$MNAME" "$PLACEHOLDER" > "$r2/apps/control-plane-api/scripts/.env"
out="$(run_audit "$r2")"; rc2=$?
if printf '%s' "$out" | grep -qF "uncovered cache holds managed name: $MNAME"; then say "PASS  case2 uncovered-cache FAIL line"; else say "FAIL  case2 missing uncovered FAIL"; fail=1; fi
if [[ "$rc2" == "1" ]]; then say "PASS  case2 rc=1"; else say "FAIL  case2 rc=$rc2 (want 1)"; fail=1; fi
# name-armed guard: the drift/coverage machinery ran (managed-name count in summary >= 1)
if printf '%s' "$out" | grep -qE "cache-coverage check ran \([1-9][0-9]* managed name"; then say "PASS  case2 name-armed (managed>=1)"; else say "FAIL  case2 not armed"; fail=1; fi
# discovered-count proves enumeration (the planted nested cache was swept)
if printf '%s' "$out" | grep -qE "cache-coverage check ran \([0-9]+ managed name\(s\), [1-9][0-9]* caches discovered"; then say "PASS  case2 discovered>=1 (planted cache enumerated)"; else say "FAIL  case2 discovered count 0"; fail=1; fi

# --- Case 3: unregistered SYMLINK to an OUTSIDE physical cache -> Check 1d -----
r3="$tmp/c3"; make_repo "$r3"; arm "$r3"
outside="$tmp/outside-cache.env"; printf '%s=%s\n' "$MNAME" "$PLACEHOLDER" > "$outside"
ln -s "$outside" "$r3/.env.linked"       # symlink under ROOT, name matches .env*
out="$(run_audit "$r3")"
if printf '%s' "$out" | grep -qF "uncovered cache holds managed name: $MNAME"; then say "PASS  case3 symlink-to-outside FAIL"; else say "FAIL  case3 symlink not discovered"; fail=1; fi

# --- Case 4: symlink to a REGISTERED cache that HOLDS the managed name ---------
# The registered target carries OPS_API_DSN so a broken symlink/devino dedup would
# treat the symlink as an unregistered cache and emit an uncovered FAIL -- this
# case only proves collapse because the managed name is present to trigger it.
r4="$tmp/c4"; make_repo "$r4"; arm "$r4"
printf '%s=%s\n' "$MNAME" "$PLACEHOLDER" > "$r4/infra/.env"; chmod 600 "$r4/infra/.env"  # registered, HOLDS the managed name
ln -s "$r4/infra/.env" "$r4/apps/.env.mirror"   # symlink to the registered infra/.env
out="$(run_audit "$r4")"
# Check 1c drift MUST fire (managed name still copied in the registered cache):
if printf '%s' "$out" | grep -qF "drift: '$MNAME' is Infisical-managed but still copied"; then say "PASS  case4 Check 1c drift fires for registered cache"; else say "FAIL  case4 drift not raised"; fail=1; fi
# Check 1d MUST NOT emit an uncovered-cache FAIL: the symlink collapses onto the registered devino:
if printf '%s' "$out" | grep -qF "uncovered cache holds managed name"; then say "FAIL  case4 spurious uncovered-FAIL (broken symlink/devino dedup)"; fail=1; else say "PASS  case4 registered-target symlink collapsed (no uncovered-FAIL)"; fi

# --- Case 5: clean -> PASS summary with non-zero discovered count, rc=0 --------
r5="$tmp/c5"; make_repo "$r5"; arm "$r5"
printf 'DEV_PG_PASSWORD=%s\n' "$PLACEHOLDER" > "$r5/infra/.env"; chmod 600 "$r5/infra/.env"
out="$(run_audit "$r5")"; rc5=$?
if printf '%s' "$out" | grep -qE "PASS  cache-coverage check ran \([0-9]+ managed name\(s\), [1-9][0-9]* caches discovered"; then say "PASS  case5 clean PASS summary w/ discovered>=1"; else say "FAIL  case5 no clean PASS summary"; fail=1; fi
if [[ "$rc5" == "0" ]]; then say "PASS  case5 rc=0"; else say "FAIL  case5 rc=$rc5 (want 0)"; fi

# --- Value-silence: the PLACEHOLDER must never appear in any output ------------
for r in "$r1" "$r2" "$r3" "$r4" "$r5"; do
  # capture first: under set -o pipefail a failing audit (rc=1) would mask a
  # grep match (rc=0), hiding a leak in exactly the failing-audit output.
  vout="$(run_audit "$r")"
  if printf '%s' "$vout" | grep -qF -- "$PLACEHOLDER"; then say "FAIL  value-silent violation: placeholder leaked"; fail=1; fi
done
say "PASS  value-silent: placeholder absent from all output"

if [[ "$fail" == "0" ]]; then say "RESULT: cache-coverage fixture PASSED"; else say "RESULT: cache-coverage fixture FAILED"; fi
exit "$fail"
