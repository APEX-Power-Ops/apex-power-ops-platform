#!/usr/bin/env bash
# test_secret_audit_env_allowlist.sh - Check 1b fixture for infra/secret-audit.sh.
#
# Proves the default infra/.env key allowlist admits only the intended local
# cache keys, including the orchestration credential APEX_JOBS_PGPASSWORD,
# without widening to adjacent APEX_JOBS_* or *_PGPASSWORD shapes. All planted
# values are synthetic and must remain absent from secret-audit output.
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

make_fixture_repo() {
  local repo="$1"
  mkdir -p "$repo/infra"
  cp "$AUDIT" "$repo/infra/secret-audit.sh"
  chmod +x "$repo/infra/secret-audit.sh"
  printf 'infra/.env\n' > "$repo/.gitignore"
  git -C "$repo" init -q
  git -C "$repo" add .gitignore infra/secret-audit.sh
}

run_audit() {
  local repo="$1"
  HOME="$tmp/home" bash "$repo/infra/secret-audit.sh" 2>&1
}

# ---- exact allowed keys pass --------------------------------------------
repo_ok="$tmp/repo-ok"
make_fixture_repo "$repo_ok"
mkdir -p "$tmp/home"
dev_pw="fixture-dev-pw-000000"
jobs_pw="fixture-apex-jobs-pw-000000"
{
  printf 'DEV_PG_PASSWORD=%s\n' "$dev_pw"
  printf 'APEX_JOBS_PGPASSWORD=%s\n' "$jobs_pw"
} > "$repo_ok/infra/.env"
chmod 600 "$repo_ok/infra/.env"

out_ok="$(run_audit "$repo_ok")"
rc_ok=$?

if [[ "$rc_ok" == "0" ]]; then
  say "PASS  exact allowed keys: exit 0"
else
  say "FAIL  exact allowed keys: expected exit 0, got $rc_ok"; fail=1
fi
for key in DEV_PG_PASSWORD APEX_JOBS_PGPASSWORD; do
  if printf '%s' "$out_ok" | grep -qF "infra/.env key allowed: $key"; then
    say "PASS  exact allowed key printed by name: $key"
  else
    say "FAIL  allowed key not acknowledged: $key"; fail=1
  fi
done
for val in "$dev_pw" "$jobs_pw"; do
  if printf '%s' "$out_ok" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: allowed fixture value leaked"; fail=1
  fi
done
say "PASS  value-silent: allowed fixture values absent from output"

# ---- adjacent keys fail --------------------------------------------------
repo_bad="$tmp/repo-bad"
make_fixture_repo "$repo_bad"
bad_pw1="fixture-apex-jobs-password-000000"
bad_pw2="fixture-apex-jobs-pgpassword-extra-000000"
{
  printf 'DEV_PG_PASSWORD=%s\n' "$dev_pw"
  printf 'APEX_JOBS_PASSWORD=%s\n' "$bad_pw1"
  printf 'APEX_JOBS_PGPASSWORD_EXTRA=%s\n' "$bad_pw2"
} > "$repo_bad/infra/.env"
chmod 600 "$repo_bad/infra/.env"

out_bad="$(run_audit "$repo_bad")"
rc_bad=$?

if [[ "$rc_bad" == "1" ]]; then
  say "PASS  adjacent disallowed keys: exit 1"
else
  say "FAIL  adjacent disallowed keys: expected exit 1, got $rc_bad"; fail=1
fi
for key in APEX_JOBS_PASSWORD APEX_JOBS_PGPASSWORD_EXTRA; do
  if printf '%s' "$out_bad" | grep -qF "infra/.env non-allowlisted key: $key"; then
    say "PASS  adjacent disallowed key rejected: $key"
  else
    say "FAIL  adjacent disallowed key was not rejected: $key"; fail=1
  fi
done
for val in "$dev_pw" "$bad_pw1" "$bad_pw2"; do
  if printf '%s' "$out_bad" | grep -qF -- "$val"; then
    say "FAIL  value-silent violation: disallowed fixture value leaked"; fail=1
  fi
done
say "PASS  value-silent: disallowed fixture values absent from output"

if [[ "$fail" == "0" ]]; then
  say "RESULT: env allowlist fixture PASSED"
else
  say "RESULT: env allowlist fixture FAILED"
fi
exit "$fail"
