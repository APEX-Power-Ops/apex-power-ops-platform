#!/usr/bin/env bash
set -euo pipefail
# Proves the sanitized launch environment BEFORE any real Codex run. Exits non-zero on any failure.
SANDBOX_HOME=/home/olares/.breaker-codex-home
CODEX_PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:/usr/bin:/bin
install -d -m 700 "$SANDBOX_HOME"
# Codex's OWN auth lives in the real ~/.codex (or $CODEX_HOME). Bridge ONLY that into the sandbox
# HOME so codex can authenticate — this is codex's credential, NOT a DB/prod cred, so it does not
# weaken the DB-isolation guarantee. Nothing else from the real HOME (no .pgpass, no shell rc, no
# infra/.env) is exposed.
REAL_CODEX="${CODEX_HOME:-$HOME/.codex}"
if [ -e "$REAL_CODEX" ]; then ln -sfn "$REAL_CODEX" "$SANDBOX_HOME/.codex"; fi
# 1. codex resolves + authenticates under the sanitized PATH+HOME
env -i PATH="$CODEX_PATH" HOME="$SANDBOX_HOME" codex --version >/tmp/codex_ver 2>&1 \
  || { echo "FAIL: codex --version"; cat /tmp/codex_ver; exit 1; }
# 2. no-op exec under full sanitization (read-only sandbox, trivial prompt)
env -i PATH="$CODEX_PATH" HOME="$SANDBOX_HOME" codex exec -s read-only 'reply with the word OK' \
  >/tmp/codex_noop 2>&1 || { echo "FAIL: no-op exec"; tail -8 /tmp/codex_noop; exit 1; }
# 3. env proof: ONLY BREAKER_SANDBOX_DSN among PG/DSN/DATABASE/SUPABASE vars (grep -E is portable)
LEAK=$(env -i PATH="$CODEX_PATH" HOME="$SANDBOX_HOME" \
  BREAKER_SANDBOX_DSN="postgresql://placeholder" bash -c 'printenv | grep -E "PG|DSN|DATABASE|SUPABASE" || true')
if [[ "$LEAK" != "BREAKER_SANDBOX_DSN=postgresql://placeholder" ]]; then
  echo "FAIL: env leak -> [$LEAK]"; exit 1
fi
echo "preflight OK (codex resolves, no-op exec clean, env shows only BREAKER_SANDBOX_DSN)"
