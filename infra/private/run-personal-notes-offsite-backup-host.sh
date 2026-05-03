#!/usr/bin/env bash
set -euo pipefail

OFFSITE_ENV_FILE="${OFFSITE_ENV_FILE:-$HOME/code/personal/.env.personal-offsite-backup}"
PERSONAL_ENV_FILE="${PERSONAL_ENV_FILE:-$HOME/code/personal/.env.personal}"
BACKUP_ROOT="${BACKUP_ROOT:-$HOME/apex-backups/personal/memos}"
LOCK_FILE="${LOCK_FILE:-$BACKUP_ROOT/.host-offsite-backup.lock}"

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

create_snapshot_archive() {
  source_env_file "$PERSONAL_ENV_FILE"

  local data_root="${PERSONAL_DATA_ROOT:-$HOME/apex-data/personal}"
  local source_dir="$data_root/memos"
  local db_path="$source_dir/memos_prod.db"

  if [[ ! -f "$db_path" ]]; then
    echo "Missing database: $db_path" >&2
    exit 1
  fi

  local timestamp
  timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
  local workdir
  workdir="$(mktemp -d)"

  mkdir -p "$workdir/memos"

  export DB_PATH="$db_path"
  export SNAPSHOT_DB="$workdir/memos/memos_prod.db"

  python3 - <<'PY'
import os
import sqlite3

src = os.environ["DB_PATH"]
dst = os.environ["SNAPSHOT_DB"]

src_conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
dst_conn = sqlite3.connect(dst)
src_conn.backup(dst_conn)
dst_conn.close()
src_conn.close()
PY

  shopt -s dotglob nullglob
  local path
  for path in "$source_dir"/*; do
    local name
    name="$(basename "$path")"
    case "$name" in
      memos_prod.db|memos_prod.db-shm|memos_prod.db-wal)
        continue
        ;;
    esac
    cp -a "$path" "$workdir/memos/"
  done

  cat > "$workdir/manifest.json" <<EOF
{
  "service": "personal-notes",
  "created_at_utc": "$timestamp",
  "env_file": "$PERSONAL_ENV_FILE",
  "backup_root": "$BACKUP_ROOT",
  "source_dir": "$source_dir",
  "db_snapshot": "memos/memos_prod.db"
}
EOF

  local archive="$BACKUP_ROOT/personal-notes-$timestamp.tgz"
  tar -C "$workdir" -czf "$archive" manifest.json memos
  rm -rf "$workdir"

  echo "$archive"
}

mkdir -p "$BACKUP_ROOT"
exec 9>"$LOCK_FILE"
if command -v flock >/dev/null 2>&1; then
  if ! flock -n 9; then
    echo "Another host-owned offsite backup run is already active." >&2
    exit 1
  fi
fi

source_env_file "$OFFSITE_ENV_FILE"

if value_is_placeholder "${RESTIC_REPOSITORY:-}" || value_is_placeholder "${RESTIC_PASSWORD:-}"; then
  echo "RESTIC_REPOSITORY and RESTIC_PASSWORD must be filled before host-side automation can run." >&2
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

archive_path="$(create_snapshot_archive)"
echo "Created archive: $archive_path"

restic backup "$BACKUP_ROOT" \
  --host "${RESTIC_HOST_LABEL:-$(hostname)}" \
  --tag personal-notes \
  --tag host-local-archives \
  --tag private-lane \
  --tag host-scheduled

keep_daily="${RESTIC_KEEP_DAILY:-7}"
keep_weekly="${RESTIC_KEEP_WEEKLY:-4}"
keep_monthly="${RESTIC_KEEP_MONTHLY:-3}"
keep_yearly="${RESTIC_KEEP_YEARLY:-1}"

restic forget \
  --keep-daily "$keep_daily" \
  --keep-weekly "$keep_weekly" \
  --keep-monthly "$keep_monthly" \
  --keep-yearly "$keep_yearly" \
  --prune

restic snapshots | tail -n 10