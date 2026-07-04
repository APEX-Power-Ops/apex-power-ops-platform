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
# Sanctioned roles: records_api, records_intake_writer, records_auditor.
# Evidence split: Check 3 detects config-shape + literal bypass tokens; live
# BYPASSRLS on an otherwise-sanctioned role is proven separately by
# assert_serving_identity (Task 3), which Check 3 cannot see from static
# config.
say ""; say "[3] records serving config: only records_api/records_intake_writer/records_auditor, no bypass creds (AC8)"
if [[ -n "${RECORDS_SERVING_GLOBS:-}" ]]; then
  glob_hit=0
  for _g in ${RECORDS_SERVING_GLOBS}; do
    [[ -r "$_g" ]] && glob_hit=1
  done
  # Key is matched case-insensitively via explicit [Xx] classes (NOT a global
  # grep -i, which would also case-fold the VALUE and wrongly sanction
  # PGUSER=RECORDS_API). The key is anchored with a leading \b word boundary
  # so a sanctioned key (user/role/pguser/pgrole) is matched only at a true
  # token boundary and NEVER as a substring inside a larger key name. Keys
  # like DB_USER, SUPER_USER, CLUSTER_ROLE are intentionally OUT of the
  # sanctioned key set: because "_" is a word char, \b does not match between
  # "DB_" and "USER", so such keys are neither scanned nor leaked. \b is
  # zero-width, so the colon-field layout of the grep -o capture is unchanged
  # and the allowlist ":KEYPAT..." filter still lands on the real key.
  #
  # VALUE-SILENCE is guaranteed by the EMIT, not by narrowing the value class:
  # the FIND line carries only bare file:line (cut -d: -f1,2, same as rule (c)
  # and Check 2), so the captured value's content can never reach output no
  # matter what it contains (a colon-joined "role:secret:port", a password
  # field, anything). Because emit is value-silent, the value class can safely
  # capture the WHOLE whitespace-delimited token - either a full quoted string
  # (everything between a pair of quotes) or an unbroken run of non-space
  # chars. Capturing the whole token makes the allowlist's "$" anchor sit at
  # the TRUE end of the value, closing every truncation bypass at once: a
  # sanctioned-role PREFIX ("records_api") followed by "-super", "%owner",
  # "@evil", ";super", ",super", or an embedded quote is captured whole and
  # correctly fails the sanctioned-only allowlist ("-" ";" "," are all legal
  # or role-distinguishing chars, so these are real non-sanctioned roles that
  # must be flagged). The quoted alternative also captures "." so a full
  # Supavisor dotted username (role.projectref) is captured, not truncated.
  #
  # Evidence split: this is best-effort STATIC config-shape detection. The
  # authoritative identity gate is the runtime assert_serving_identity (Task
  # 3), which proves live BYPASSRLS/role at connect time; Check 3 cannot see
  # that from static config and does not try to.
  KEYPAT="([Uu][Ss][Ee][Rr]|[Rr][Oo][Ll][Ee]|[Pp][Gg][Uu][Ss][Ee][Rr]|[Pp][Gg][Rr][Oo][Ll][Ee])"
  VALPAT="(['\"][^'\"]*['\"]|[^[:space:]]+)"
  while IFS= read -r loc; do
    [[ -z "$loc" ]] && continue
    say "  FIND  ${loc}  [rule: records-serving-non-app-role]"; rc=1
  done < <(grep -rHInoE "\b${KEYPAT}[[:space:]]*=[[:space:]]*${VALPAT}" ${RECORDS_SERVING_GLOBS} 2>/dev/null \
             | grep -vE ":${KEYPAT}[[:space:]]*=[[:space:]]*['\"]?(records_api|records_intake_writer|records_auditor)(\.[a-z0-9]+)?['\"]?\$" \
             | cut -d: -f1,2)
  while IFS= read -r loc; do
    [[ -z "$loc" ]] && continue
    say "  FIND  ${loc}  [rule: records-serving-bypass-credential]"; rc=1
  done < <(grep -rHInEi -e 'sb_secret_|service_role|bypassrls' ${RECORDS_SERVING_GLOBS} 2>/dev/null | cut -d: -f1,2)
  # rule (c): URL-form DSN userinfo, e.g. postgresql://<user>:<pw>@host/db and
  # driver-qualified variants postgresql+asyncpg://, postgresql+psycopg://,
  # etc. (SERVING_CONTRACT recognizes the optional "+<driver>" scheme suffix in
  # BOTH the match and the allowlist). Rules (a)/(b) miss this shape: the
  # username in a URL's userinfo is not a "user=" keyword token (misses rule a)
  # and is not itself a bypass literal (misses rule b) even when it names an
  # owner/superuser role. Emit is VALUE-SILENT the same way rule (a) is now:
  # the matched token contains a "://" colon, so instead of a trailing-strip
  # sed we cut to the first two colon-delimited fields (same normalization
  # Check 2 uses) to emit bare file:line - the password half of the userinfo is
  # never printed regardless of the match. The match class already includes
  # "." so a dotted Supavisor username is captured in full; the negative
  # filter below uses the same 3-role + single-dot-ref allowlist as rule (a).
  #
  # SCHEME-CASE: the scheme token is matched case-insensitively via explicit
  # [Xx] character classes (NOT a global grep -i), so a mixed/upper-case
  # scheme such as POSTGRESQL:// or PostgreSQL:// - both valid per RFC 3986
  # and accepted as-is by libpq/SQLAlchemy - can no longer evade rule (c).
  # The sanctioned-role alternation stays CASE-SENSITIVE (lowercase only) in
  # both the match and the allowlist below, the same trap rule (a) already
  # avoids for keys: a naive global -i would also case-fold the ROLE VALUE
  # and wrongly sanction POSTGRESQL://RECORDS_API.
  while IFS= read -r loc; do
    [[ -z "$loc" ]] && continue
    say "  FIND  ${loc}  [rule: records-serving-url-non-app-role]"; rc=1
  done < <(grep -rHInoE '[Pp][Oo][Ss][Tt][Gg][Rr][Ee][Ss]([Qq][Ll])?(\+[a-z0-9]+)?://[A-Za-z0-9._%+-]+[:@]' ${RECORDS_SERVING_GLOBS} 2>/dev/null \
             | grep -vE ':[Pp][Oo][Ss][Tt][Gg][Rr][Ee][Ss]([Qq][Ll])?(\+[a-z0-9]+)?://(records_api|records_intake_writer|records_auditor)(\.[a-z0-9]+)?[:@]$' \
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
