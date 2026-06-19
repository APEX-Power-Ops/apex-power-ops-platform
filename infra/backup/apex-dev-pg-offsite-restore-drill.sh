#!/usr/bin/env bash
# Weekly restore drill: pull the latest dev-pg offsite snapshot from B2 and prove a
# recovered dump is intact + pg_restore-readable (validated with the PG17 client
# inside apex-dev-pg). An untested backup is not a backup.
set -euo pipefail

OFFSITE_ENV_FILE="${OFFSITE_ENV_FILE:-$HOME/code/apex/.env.dev-pg-offsite-backup}"
DRILL_ROOT="${DRILL_ROOT:-$HOME/apex-restore-drills/dev-pg}"
LOCK_FILE="${LOCK_FILE:-$DRILL_ROOT/.offsite-restore-drill.lock}"

value_is_placeholder() {
  case "${1:-}" in
    ''|*REPLACE_WITH*|*SET_FROM*|*SET_IF_REQUIRED*|*OPTIONAL_*) return 0 ;;
    *) return 1 ;;
  esac
}
source_env_file() {
  local env_file="$1" env_source
  env_source="$env_file"
  [[ -f "$env_file" ]] || { echo "Missing env file: $env_file" >&2; exit 1; }
  if grep -q $'\r' "$env_file"; then
    env_source="$(mktemp)"; tr -d '\r' < "$env_file" > "$env_source"
  fi
  set -a; . "$env_source"; set +a
  [[ "$env_source" != "$env_file" ]] && rm -f "$env_source" || true
}

mkdir -p "$DRILL_ROOT"
exec 9>"$LOCK_FILE"
if command -v flock >/dev/null 2>&1; then
  flock -n 9 || { echo "Another dev-pg restore drill is active." >&2; exit 1; }
fi

source_env_file "$OFFSITE_ENV_FILE"
if value_is_placeholder "${RESTIC_REPOSITORY:-}" || value_is_placeholder "${RESTIC_PASSWORD:-}"; then
  echo "RESTIC_REPOSITORY and RESTIC_PASSWORD must be set before drills can run." >&2
  exit 1
fi
case "${RESTIC_REPOSITORY:-}" in
  s3:*) if value_is_placeholder "${AWS_ACCESS_KEY_ID:-}" || value_is_placeholder "${AWS_SECRET_ACCESS_KEY:-}"; then
    echo "S3/B2 repository selected but AWS creds are still placeholders." >&2; exit 1; fi ;;
esac

LABEL="${RESTIC_HOST_LABEL:-$(hostname)}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="$DRILL_ROOT/$STAMP"
restic restore latest --host "$LABEL" --tag dev-pg --target "$TARGET"

dump="$(find "$TARGET" -type f -name '*.dump' | sort | tail -n1)"
[[ -n "$dump" ]] || { echo "Restore drill recovered no .dump file." >&2; exit 1; }

# Validate the custom-format dump TOC with the matching PG17 pg_restore (in-container).
docker cp "$dump" apex-dev-pg:/tmp/drill.dump
if docker exec apex-dev-pg pg_restore -l /tmp/drill.dump >/dev/null 2>&1; then
  echo "Restore drill OK: $(basename "$dump") validates (pg_restore -l)"
  docker exec apex-dev-pg rm -f /tmp/drill.dump || true
else
  docker exec apex-dev-pg rm -f /tmp/drill.dump || true
  echo "Restore drill FAILED: recovered dump did not validate." >&2; exit 1
fi

# Keep only the last 4 drill dirs.
find "$DRILL_ROOT" -mindepth 1 -maxdepth 1 -type d | sort | head -n -4 | xargs -r rm -rf
restic snapshots --tag dev-pg | tail -n 5
