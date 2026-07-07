#!/usr/bin/env bash
# test_apex_jobs_launcher.sh - proves apex-jobs.sh dispatches through inject.sh dev
# with passthrough args, without invoking real Infisical/uv. Value-silent.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
say() { printf '%s\n' "$*"; }
if [[ ! -f "$HERE/apex-jobs.sh" ]]; then say "FAIL  apex-jobs.sh not present"; exit 1; fi
fail=0
tmp="$(mktemp -d)"
cp "$HERE/apex-jobs.sh" "$tmp/apex-jobs.sh"
cat > "$tmp/inject.sh" <<'STUB'
#!/usr/bin/env bash
printf 'INJECT_ARGV:'; printf ' %s' "$@"; printf '\n'
STUB
chmod +x "$tmp/inject.sh" "$tmp/apex-jobs.sh"
out="$(bash "$tmp/apex-jobs.sh" review-run --review-head X --base-ref Y 2>&1 || true)"
rm -rf "$tmp"
if printf '%s' "$out" | grep -qF 'INJECT_ARGV: dev -- bash -c'; then
  say "PASS  launcher dispatched via inject.sh dev"
else
  say "FAIL  launcher did not dispatch via inject.sh dev: $out"; fail=1
fi
if printf '%s' "$out" | grep -qF 'review-run --review-head X --base-ref Y'; then
  say "PASS  launcher forwarded verb + args"
else
  say "FAIL  launcher dropped args"; fail=1
fi
if [[ "$fail" == 0 ]]; then say "RESULT: launcher fixture PASSED"; exit 0; else say "RESULT: launcher fixture FAILED"; exit 1; fi
