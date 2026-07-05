#!/usr/bin/env bash
# Argv-contract test for run_platform_api_local.sh. Proves the launcher invokes
# inject.sh with the exact `dev -- uvicorn ...` argv. This is NOT a cutover proof:
# it does not run uvicorn, import main.py, or touch Infisical. Value-silent (no
# secret values are involved).
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
LAUNCHER="$HERE/run_platform_api_local.sh"
fail=0; say() { printf '%s\n' "$*"; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

if [[ ! -f "$LAUNCHER" ]]; then
  say "FAIL  launcher missing: $LAUNCHER"; exit 1
fi

# Temp repo fixture: launcher three levels under root; stub inject.sh at the real
# relative path apps/control-plane-api/scripts -> ../../.. = fixture root.
mkdir -p "$tmp/apps/control-plane-api/scripts" "$tmp/infra/infisical"
cp "$LAUNCHER" "$tmp/apps/control-plane-api/scripts/run_platform_api_local.sh"
chmod +x "$tmp/apps/control-plane-api/scripts/run_platform_api_local.sh"
cat > "$tmp/infra/infisical/inject.sh" <<'STUB'
#!/usr/bin/env bash
# Stub: capture argv, do NOT exec uvicorn.
printf '%s\n' "$*" > "$CAPTURE"
STUB
chmod +x "$tmp/infra/infisical/inject.sh"

CAPTURE="$tmp/argv.txt" bash "$tmp/apps/control-plane-api/scripts/run_platform_api_local.sh"
got="$(cat "$tmp/argv.txt" 2>/dev/null || echo '<none>')"
expected='dev -- uvicorn main:app --app-dir apps/control-plane-api --host 127.0.0.1 --port 8010'
if [[ "$got" == "$expected" ]]; then
  say "PASS  launcher argv contract"
else
  say "FAIL  launcher argv contract"; say "  expected: $expected"; say "  got:      $got"; fail=1
fi

if [[ "$fail" == "0" ]]; then say "RESULT: launcher argv fixture PASSED"; else say "RESULT: launcher argv fixture FAILED"; fi
exit "$fail"
