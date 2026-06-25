#!/usr/bin/env bash
set -euo pipefail
# Real sanitized Codex run. Caller must export BREAKER_SANDBOX_DSN (clone DSN) first.
: "${BREAKER_SANDBOX_DSN:?clone DSN required}"
WORKTREE="${1:?codex worktree path}"   # e.g. /home/olares/code/apex/apex-breaker-codex
HERE="$(cd "$(dirname "$0")" && pwd)"
env -i \
  PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:/usr/bin:/bin \
  HOME=/home/olares/.breaker-codex-home \
  BREAKER_SANDBOX_DSN="$BREAKER_SANDBOX_DSN" \
  codex exec -s workspace-write -C "$WORKTREE" - < "$HERE/direction.md"
