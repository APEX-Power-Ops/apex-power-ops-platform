#!/usr/bin/env bash
# secret-audit.sh - APEX platform secret-hygiene tripwire (L6 custody model).
#
# Check 1: runtime secret-cache files are mode 0600/0400 and gitignored.
# Check 1b: infra/.env holds only allowlisted keys (an orphan secret in the
#           gitignored cache is invisible to Check 2 - flag it by key name).
# Check 1c: Infisical-managed secrets (infra/infisical/.managed-secrets) must not
#           linger in any local cache once migrated (drift; names only).
# Check 2: high-precision scan for leaked CREDENTIALS in tracked files -
#          provider token signatures (GitHub/AWS/Slack/Google/OpenAI), JWTs,
#          private-key blocks, and inline DSN passwords. Example-bearing paths
#          (docs/tests/templates) are allowlisted in infra/.secret-audit-allow.
#          Generic hardcoded constants are OUT OF SCOPE - use gitleaks for depth.
#
# Output is LOCATIONS ONLY - file:line + rule name; values are never printed.
# Exit: 0 = clean, 1 = findings (perms FAIL or possible leak).
set -uo pipefail

# ROOT = the apex repo root, derived from THIS script's own location (not the
# caller's cwd) so the checks can never be silently skipped from another dir.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
if [[ ! -f "$ROOT/infra/secret-audit.sh" ]]; then
  echo "FATAL: cannot locate apex repo root (ROOT=$ROOT)" >&2; exit 2
fi
rc=0
say() { printf '%s\n' "$*"; }

say "APEX secret-audit  (repo: $ROOT)"
say "========================================"

# ---- Check 1: cache-file permissions -------------------------------------
say "[1] runtime secret-cache permissions"
declare -a CACHES=(
  "$ROOT/infra/.env:0"
  "$HOME/code/apex/.env.dev-pg-offsite-backup:0"
)
for extra in ${APEX_EXTRA_CACHES:-}; do CACHES+=("$extra:0"); done

for entry in "${CACHES[@]}"; do
  f="${entry%:*}"; req="${entry##*:}"
  if [[ ! -e "$f" ]]; then
    if [[ "$req" == "1" ]]; then say "  FAIL  missing (required): $f"; rc=1
    else say "  SKIP  not present:        $f"; fi
    continue
  fi
  mode="$(stat -c '%a' "$f" 2>/dev/null || echo '???')"
  if [[ "$mode" == "600" || "$mode" == "400" ]]; then
    say "  PASS  $f  (mode $mode)"
  else
    say "  FAIL  $f  (mode $mode, want 600)  fix: chmod 600 '$f'"; rc=1
  fi
done

if [[ -f "$ROOT/infra/.env" ]]; then
  if git -C "$ROOT" check-ignore -q infra/.env; then
    say "  PASS  infra/.env is gitignored"
  else
    say "  FAIL  infra/.env is NOT gitignored"; rc=1
  fi
fi

# ---- Check 1b: infra/.env carries only allowlisted keys ------------------
# An orphan secret (e.g. a prod DSN) parked in this gitignored 0600 cache is
# invisible to Check 2, which scans TRACKED files only. The cache is meant to
# hold exactly the dev-pg password; flag anything else (key NAMES only).
ENV_ALLOWED_KEYS="${APEX_ENV_ALLOWED_KEYS:-DEV_PG_PASSWORD}"
if [[ -f "$ROOT/infra/.env" ]]; then
  while IFS= read -r k; do
    [[ -z "$k" ]] && continue
    ok=0
    for a in $ENV_ALLOWED_KEYS; do [[ "$k" == "$a" ]] && ok=1; done
    if [[ "$ok" == "1" ]]; then
      say "  PASS  infra/.env key allowed: $k"
    else
      say "  FAIL  infra/.env non-allowlisted key: $k  (move to Vault; allowed: $ENV_ALLOWED_KEYS)"; rc=1
    fi
  done < <(grep -oE '^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=' "$ROOT/infra/.env" 2>/dev/null | sed -E 's/^[[:space:]]*(export[[:space:]]+)?//; s/[[:space:]]*=$//')
fi

# ---- Check 1c: Infisical drift -- a migrated secret must not linger in caches --
# Once a secret is SOURCED from Infisical (named in infra/infisical/.managed-secrets),
# any leftover copy in a local cache is DRIFT to remove (rotation runbook step 6:
# "no value outside Infisical"). Dormant until the manifest names a secret. NAMES only.
MANAGED="$ROOT/infra/infisical/.managed-secrets"
if [[ -f "$MANAGED" ]]; then
  declare -a MNAMES=()
  while IFS= read -r line; do
    line="${line%%#*}"; line="${line//[[:space:]]/}"
    [[ -n "$line" ]] && MNAMES+=("$line")
  done < "$MANAGED"
  if [[ "${#MNAMES[@]}" -gt 0 ]]; then
    for entry in "${CACHES[@]}"; do
      cache="${entry%:*}"
      [[ -f "$cache" ]] || continue
      for nm in "${MNAMES[@]}"; do
        if grep -qE "^[[:space:]]*(export[[:space:]]+)?${nm}[[:space:]]*=" "$cache" 2>/dev/null; then
          hint=""
          for a in $ENV_ALLOWED_KEYS; do [[ "$nm" == "$a" ]] && hint="  (also in ENV_ALLOWED_KEYS - drop it there once removed)"; done
          say "  FAIL  drift: '$nm' is Infisical-managed but still copied in $cache$hint"; rc=1
        fi
      done
    done
    say "  PASS  Infisical drift check ran (${#MNAMES[@]} managed name(s))"
  fi
fi

# ---- Check 2: leaked credentials in tracked files ------------------------
say ""
say "[2] leaked credentials in tracked files"

declare -a ALLOW=()
ALLOWFILE="$ROOT/infra/.secret-audit-allow"
if [[ -f "$ALLOWFILE" ]]; then
  while IFS= read -r g; do
    [[ -z "$g" || "$g" == \#* ]] && continue
    ALLOW+=("$g")
  done < "$ALLOWFILE"
fi
allowed_file() {
  local f="$1" p
  for p in "${ALLOW[@]:-}"; do [[ -n "$p" && "$f" == $p ]] && return 0; done
  return 1
}

# dummy/placeholder filter (mainly for inline-url-password)
IGNORE='(\$\{|\$\(|<[A-Za-z0-9_]+>|\[[A-Za-z0-9_]+\]|changeme|CHANGEME|example|EXAMPLE|placeholder|YOUR_|REPLACE|:postgres@|:password@|:secret@|:root@|:admin@)'

# high-precision credential signatures (case-sensitive on purpose)
declare -A RULES=(
  ["private-key-block"]='-----BEGIN [A-Z ]*PRIVATE KEY-----'
  ["aws-access-key-id"]='AKIA[0-9A-Z]{16}'
  ["github-token"]='gh[pousr]_[A-Za-z0-9]{36}'
  ["github-fine-pat"]='github_pat_[A-Za-z0-9_]{40,}'
  ["slack-token"]='xox[baprs]-[A-Za-z0-9-]{12,}'
  ["google-api-key"]='AIza[0-9A-Za-z_-]{35}'
  ["openai-key"]='sk-[A-Za-z0-9]{20,}'
  ["jwt"]='eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}'
  ["inline-url-password"]='://[A-Za-z0-9._-]+:[^@/[:space:]"]{6,}@'
  ["supabase-secret-key"]='sb_secret_[A-Za-z0-9_-]{16,}'
)
hits=0; suppressed=0
for name in "${!RULES[@]}"; do
  pat="${RULES[$name]}"
  while IFS= read -r m; do
    [[ -z "$m" ]] && continue
    file="${m%%:*}"
    if allowed_file "$file"; then suppressed=$((suppressed+1)); continue; fi
    say "  FIND  ${m}  [rule: $name]"
    hits=$((hits+1)); rc=1
  done < <(git -C "$ROOT" grep -nIE -e "$pat" -- . 2>/dev/null | grep -vEi "$IGNORE" | cut -d: -f1,2)
done
if [[ "$hits" == "0" ]]; then say "  PASS  no leaked credentials in tracked files"; fi
[[ "$suppressed" -gt 0 ]] && say "  note  $suppressed match(es) suppressed by infra/.secret-audit-allow"

# ---- Check 3: records serving config -- only sanctioned app roles (AC8) --
say ""; say "[3] records serving config: only records_api/records_intake_writer, no bypass creds (AC8)"
if [[ -n "${RECORDS_SERVING_GLOBS:-}" ]]; then
  glob_hit=0
  for _g in ${RECORDS_SERVING_GLOBS}; do
    [[ -r "$_g" ]] && glob_hit=1
  done
  while IFS= read -r loc; do
    [[ -z "$loc" ]] && continue
    say "  FIND  ${loc}  [rule: records-serving-non-app-role]"; rc=1
  done < <(grep -rHInoE "(user|role)[[:space:]]*=[[:space:]]*['\"]?[A-Za-z0-9_]+['\"]?" ${RECORDS_SERVING_GLOBS} 2>/dev/null \
             | grep -vE ":(user|role)[[:space:]]*=[[:space:]]*['\"]?(records_api|records_intake_writer)['\"]?\$" \
             | sed -E 's/:[^:]*$//')
  while IFS= read -r loc; do
    [[ -z "$loc" ]] && continue
    say "  FIND  ${loc}  [rule: records-serving-bypass-credential]"; rc=1
  done < <(grep -rHInEi -e 'sb_secret_|service_role|bypassrls' ${RECORDS_SERVING_GLOBS} 2>/dev/null | cut -d: -f1,2)
  # rule (c): URL-form DSN userinfo, e.g. postgresql://<user>:<pw>@host/db.
  # Rules (a)/(b) miss this shape: the username in a URL's userinfo is not a
  # "user=" keyword token (misses rule a) and is not itself a bypass literal
  # (misses rule b) even when it names an owner/superuser role. -o with -H/-n
  # keeps this VALUE-SILENT: the match stops at the ":" or "@" delimiter, so
  # the password half of the userinfo is never captured or printed. The
  # matched token itself contains a "://" colon, so the trailing-strip sed
  # rules (a)/(b) use would leave it stuck to the FIND line; cut to the first
  # two colon-delimited fields instead (same normalization Check 2 uses) so
  # this rule also emits bare file:line.
  while IFS= read -r loc; do
    [[ -z "$loc" ]] && continue
    say "  FIND  ${loc}  [rule: records-serving-url-non-app-role]"; rc=1
  done < <(grep -rHInoE '(postgresql|postgres)://[A-Za-z0-9._%+-]+[:@]' ${RECORDS_SERVING_GLOBS} 2>/dev/null \
             | grep -vE ':(postgresql|postgres)://(records_api|records_intake_writer)[:@]$' \
             | cut -d: -f1,2)
  if [[ "$glob_hit" == "1" ]]; then
    say "  PASS  records serving scan ran (globs: ${RECORDS_SERVING_GLOBS})"
  else
    say "  FAIL  RECORDS_SERVING_GLOBS matched no readable files  [rule: records-serving-empty-glob]"; rc=1
  fi
else
  say "  SKIP  no RECORDS_SERVING_GLOBS set (serving config not built yet)"
fi

say ""
say "========================================"
if [[ "$rc" == "0" ]]; then say "RESULT: clean"; else say "RESULT: findings above - review (redact & rotate if a value is real)"; fi
exit "$rc"
