#!/usr/bin/env bash
# Nightly logical backup of the Olares dev-lanes Postgres (apex-dev-pg, PG17).
# Backs up the host-only dev state (records_dev / ops_dev / orchestration_dev)
# to the dedicated backup disk. Dev DBs live ONLY on the host now (dev-residency,
# 2026-06-18), so this closes the L2 durability gap: a host-data-volume fault no
# longer strands in-flight dev state. Offsite (Backblaze B2) is a later add.
set -euo pipefail

CONTAINER="apex-dev-pg"
BACKUP_ROOT="/mnt/apex-backup/dev-pg"
DBS="records_dev ops_dev orchestration_dev"
RETAIN_DAYS="${RETAIN_DAYS:-14}"
STAMP="$(date -u +%Y-%m-%dT%H%M%SZ)"
DEST="${BACKUP_ROOT}/${STAMP}"

mkdir -p "$DEST"

# Per-DB custom-format dumps (compressed, restorable with pg_restore). pg_dump
# runs inside the container as the postgres superuser over the local socket
# (trust) -- no password handling needed.
for db in $DBS; do
  docker exec "$CONTAINER" pg_dump -U postgres -Fc "$db" > "${DEST}/${db}.dump"
done

# Cluster globals (roles/grants) so a restore can recreate the role landscape.
docker exec "$CONTAINER" pg_dumpall -U postgres --globals-only > "${DEST}/globals.sql"

# Integrity manifest.
( cd "$DEST" && sha256sum ./* > SHA256SUMS )

# Retention: prune backup sets older than RETAIN_DAYS.
find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime "+${RETAIN_DAYS}" -exec rm -rf {} +

# Size summary for the journal.
echo "apex-dev-pg backup OK -> ${DEST}"
du -sh "$DEST" | awk '{print "  set size: " $1}'
ls -1 "$DEST"
