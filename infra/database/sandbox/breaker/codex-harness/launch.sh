#!/usr/bin/env bash
set -euo pipefail
# Real sanitized Codex run. Caller must export BREAKER_SANDBOX_DSN (clone DSN) first.
: "${BREAKER_SANDBOX_DSN:?clone DSN required}"
WORKTREE="${1:?codex worktree path}"   # e.g. /home/olares/code/apex/apex-breaker-codex
HERE="$(cd "$(dirname "$0")" && pwd)"
# Self-contained setup (idempotent — same bridge preflight.sh establishes): create the sanitized
# HOME and symlink ONLY codex's own auth (~/.codex / $CODEX_HOME) so codex authenticates under
# env -i. NOT a DB/prod cred — nothing else from the real HOME is exposed.
SANDBOX_HOME=/home/olares/.breaker-codex-home
install -d -m 700 "$SANDBOX_HOME"
REAL_CODEX="${CODEX_HOME:-$HOME/.codex}"
[ -e "$REAL_CODEX" ] && ln -sfn "$REAL_CODEX" "$SANDBOX_HOME/.codex" || true
env -i \
  PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:/usr/bin:/bin \
  HOME="$SANDBOX_HOME" \
  BREAKER_SANDBOX_DSN="$BREAKER_SANDBOX_DSN" \
  codex exec -s workspace-write -C "$WORKTREE" - < "$HERE/direction.md"
