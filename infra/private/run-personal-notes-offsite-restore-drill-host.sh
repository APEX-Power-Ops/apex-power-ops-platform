#!/usr/bin/env bash
set -euo pipefail

OFFSITE_ENV_FILE="${OFFSITE_ENV_FILE:-$HOME/code/personal/.env.personal-offsite-backup}"
RESTORE_DRILL_ROOT="${RESTORE_DRILL_ROOT:-$HOME/apex-restore-drills/personal/memos}"
LOCK_FILE="${LOCK_FILE:-$RESTORE_DRILL_ROOT/.host-offsite-restore-drill.lock}"

value_is_placeholder() {
  case "${1:-}" in
    ''|*REPLACE_WITH*|*SET_FROM*|*SET_IF_REQUIRED*|*OPTIONAL_*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

source_env_file() {
  local env_file="$1"
  local env_source="$env_file"

  if [[ ! -f "$env_file" ]]; then
    echo "Missing env file: $env_file" >&2
    exit 1
  fi

  if grep -q $'\r' "$env_file"; then
    env_source="$(mktemp)"
    tr -d '\r' < "$env_file" > "$env_source"
  fi

  set -a
  # shellcheck disable=SC1090
  . "$env_source"
  set +a

  if [[ "$env_source" != "$env_file" ]]; then
    rm -f "$env_source"
  fi
}

mkdir -p "$RESTORE_DRILL_ROOT"
exec 9>"$LOCK_FILE"
if command -v flock >/dev/null 2>&1; then
  if ! flock -n 9; then
    echo "Another host-owned offsite restore drill is already active." >&2
    exit 1
  fi
fi

source_env_file "$OFFSITE_ENV_FILE"

if value_is_placeholder "${RESTIC_REPOSITORY:-}" || value_is_placeholder "${RESTIC_PASSWORD:-}"; then
  echo "RESTIC_REPOSITORY and RESTIC_PASSWORD must be filled before host-side restore drills can run." >&2
  exit 1
fi

case "${RESTIC_REPOSITORY:-}" in
  s3:*)
    if value_is_placeholder "${AWS_ACCESS_KEY_ID:-}" || value_is_placeholder "${AWS_SECRET_ACCESS_KEY:-}"; then
      echo "S3 repository selected but AWS credentials are still placeholders." >&2
      exit 1
    fi
    ;;
esac

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target_dir="$RESTORE_DRILL_ROOT/$timestamp"
extract_dir="$(mktemp -d)"

cleanup() {
  rm -rf "$extract_dir"
}

trap cleanup EXIT

restic restore latest --target "$target_dir"

restored_archive="$(find "$target_dir" -type f -name 'personal-notes-*.tgz' | sort | tail -n 1)"
if [[ -z "$restored_archive" ]]; then
  echo "Restore drill did not recover a personal-notes archive." >&2
  exit 1
fi

tar -C "$extract_dir" -xzf "$restored_archive"

if [[ ! -f "$extract_dir/manifest.json" ]] || [[ ! -f "$extract_dir/memos/memos_prod.db" ]]; then
  echo "Restore drill recovered an archive but failed integrity validation." >&2
  exit 1
fi

echo "Restore drill target: $target_dir"
echo "Validated archive: $restored_archive"

restic snapshots | tail -n 10