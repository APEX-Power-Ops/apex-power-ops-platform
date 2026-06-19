#!/usr/bin/env bash
# Offsite (Backblaze B2 via restic) replication of the dev-lanes Postgres backups.
# Ships the L2 local dump sets (/mnt/apex-backup/dev-pg/<stamp>/) to an encrypted
# restic repo on B2. Mirrors the proven apex-personal-notes offsite pattern.
# Secrets come from an olares-owned 0600 env file OUTSIDE the repo (never committed);
# the script refuses to run while values are placeholders.
set -euo pipefail

OFFSITE_ENV_FILE="${OFFSITE_ENV_FILE:-$HOME/code/apex/.env.dev-pg-offsite-backup}"
BACKUP_SRC="${BACKUP_SRC:-/mnt/apex-backup/dev-pg}"
LOCK_FILE="${LOCK_FILE:-$HOME/apex-backups/dev-pg/.offsite-backup.lock}"

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

[[ -d "$BACKUP_SRC" ]] || { echo "Missing local backup source: $BACKUP_SRC (run the L2 dump first)" >&2; exit 1; }
mkdir -p "$(dirname "$LOCK_FILE")"
exec 9>"$LOCK_FILE"
if command -v flock >/dev/null 2>&1; then
  flock -n 9 || { echo "Another dev-pg offsite run is active." >&2; exit 1; }
fi

source_env_file "$OFFSITE_ENV_FILE"

if value_is_placeholder "${RESTIC_REPOSITORY:-}" || value_is_placeholder "${RESTIC_PASSWORD:-}"; then
  echo "RESTIC_REPOSITORY and RESTIC_PASSWORD must be set before this runs (see the .template)." >&2
  exit 1
fi
case "${RESTIC_REPOSITORY:-}" in
  s3:*)
    if value_is_placeholder "${AWS_ACCESS_KEY_ID:-}" || value_is_placeholder "${AWS_SECRET_ACCESS_KEY:-}"; then
      echo "S3/B2 repository selected but AWS_ACCESS_KEY_ID/SECRET are still placeholders." >&2
      exit 1
    fi
    ;;
esac

LABEL="${RESTIC_HOST_LABEL:-$(hostname)}"
restic backup "$BACKUP_SRC" --host "$LABEL" --tag dev-pg --tag host-scheduled --tag apex-platform

# Retention filtered to THIS lane (safe even if the repo is shared with other lanes).
restic forget --host "$LABEL" --tag dev-pg \
  --keep-daily "${RESTIC_KEEP_DAILY:-7}" \
  --keep-weekly "${RESTIC_KEEP_WEEKLY:-4}" \
  --keep-monthly "${RESTIC_KEEP_MONTHLY:-3}" \
  --prune

restic snapshots --tag dev-pg | tail -n 10
echo "dev-pg offsite backup OK -> ${RESTIC_REPOSITORY} (tag dev-pg, host $LABEL)"
