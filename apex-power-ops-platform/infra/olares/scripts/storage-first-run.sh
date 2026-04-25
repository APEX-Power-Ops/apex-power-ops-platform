#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-/tmp/apex-storage-session.env}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "session env file not found: ${ENV_FILE}" >&2
  exit 1
fi

source "${ENV_FILE}"

DATA_DRIVE_MODE="${DATA_DRIVE_MODE:-attached}"

if [[ "${DATA_DRIVE_MODE}" != 'attached' && "${DATA_DRIVE_MODE}" != 'deferred' ]]; then
  echo "DATA_DRIVE_MODE must be either 'attached' or 'deferred'" >&2
  exit 1
fi

required_vars=(
  STORAGE_SESSION_ID
  BACKUP_DEVICE_ID
  OFFSITE_REPO_ID
  BACKUP_DISK_ID
  RESTIC_PASSWORD
  RESTIC_LOCAL_REPOSITORY
  RESTIC_S3_REPOSITORY
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
)

if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  required_vars+=(
    DATA_DEVICE_ID
    DATA_DISK_ID
  )
fi

for name in "${required_vars[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "required variable is missing: ${name}" >&2
    exit 1
  fi
done

placeholder_values=(
  'ACTUAL_EXTERNAL_BY_ID_FROM_LSBLK'
  'SET_FROM_VAULT_OR_PASSWORD_MANAGER'
  'REPLACE_WITH_BUCKET_NAME'
  'REPLACE_WITH_BUCKET_ENDPOINT'
  'SET_FROM_VAULT'
)

if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  placeholder_values+=(
    'ACTUAL_INTERNAL_BY_ID_FROM_LSBLK'
  )
  env_snapshot="$(declare -p DATA_DISK_ID BACKUP_DISK_ID RESTIC_PASSWORD RESTIC_S3_REPOSITORY AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY 2>/dev/null || true)"
else
  env_snapshot="$(declare -p BACKUP_DISK_ID RESTIC_PASSWORD RESTIC_S3_REPOSITORY AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY 2>/dev/null || true)"
fi

for placeholder in "${placeholder_values[@]}"; do
  if grep -Fq "${placeholder}" <<<"${env_snapshot}"; then
    echo "env file still contains placeholder value: ${placeholder}" >&2
    exit 1
  fi
done

for command_name in lsblk wipefs parted udevadm mkfs.ext4 mount blkid restic tee grep; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "required command not found: ${command_name}" >&2
    exit 1
  fi
done

if [[ $EUID -eq 0 ]]; then
  echo "run this script as a normal operator user with sudo access, not as root" >&2
  exit 1
fi

if [[ "${DATA_DRIVE_MODE}" == 'attached' && ! -b "${DATA_DISK_ID}" ]]; then
  echo "data disk block device not found: ${DATA_DISK_ID}" >&2
  exit 1
fi

if [[ ! -b "${BACKUP_DISK_ID}" ]]; then
  echo "backup disk block device not found: ${BACKUP_DISK_ID}" >&2
  exit 1
fi

BACKUP_PARTITION="${BACKUP_DISK_ID}-part1"
APEX_DATA_FSTAB='LABEL=APEX_DATA /srv/apex ext4 defaults,noatime 0 2'
APEX_BACKUP_FSTAB='LABEL=APEX_BACKUP /mnt/apex-backup ext4 defaults,nofail,noatime,x-systemd.automount 0 2'

if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  DATA_PARTITION="${DATA_DISK_ID}-part1"
fi

echo "Session: ${STORAGE_SESSION_ID}"
echo "Data drive mode: ${DATA_DRIVE_MODE}"
if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  echo "Data device id: ${DATA_DEVICE_ID} -> ${DATA_DISK_ID}"
else
  echo 'Data device id: deferred; /srv/apex will remain on the primary workstation filesystem for now'
fi
echo "Backup device id: ${BACKUP_DEVICE_ID} -> ${BACKUP_DISK_ID}"
echo "Offsite repository id: ${OFFSITE_REPO_ID} -> ${RESTIC_S3_REPOSITORY}"

sudo lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN,TYPE,FSTYPE,MOUNTPOINT
ls -l /dev/disk/by-id

if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  read -r -p "About to wipe ${DATA_DISK_ID} and ${BACKUP_DISK_ID}. Type YES to continue: " confirmation
else
  read -r -p "About to wipe ${BACKUP_DISK_ID} and initialize the external backup target. Type YES to continue: " confirmation
fi
if [[ "${confirmation}" != 'YES' ]]; then
  echo 'aborted before destructive operations'
  exit 1
fi

if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  sudo wipefs -a "${DATA_DISK_ID}"
fi
sudo wipefs -a "${BACKUP_DISK_ID}"

if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  sudo parted -s "${DATA_DISK_ID}" mklabel gpt
  sudo parted -s "${DATA_DISK_ID}" mkpart primary ext4 1MiB 100%
fi
sudo parted -s "${BACKUP_DISK_ID}" mklabel gpt
sudo parted -s "${BACKUP_DISK_ID}" mkpart primary ext4 1MiB 100%

sudo udevadm settle

if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  if [[ ! -b "${DATA_PARTITION}" || ! -b "${BACKUP_PARTITION}" ]]; then
    echo 'expected partition devices were not created' >&2
    exit 1
  fi
else
  if [[ ! -b "${BACKUP_PARTITION}" ]]; then
    echo 'expected backup partition device was not created' >&2
    exit 1
  fi
fi

if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  sudo mkfs.ext4 -F -L APEX_DATA "${DATA_PARTITION}"
fi
sudo mkfs.ext4 -F -L APEX_BACKUP "${BACKUP_PARTITION}"

sudo mkdir -p /srv/apex /mnt/apex-backup

if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  sudo grep -q '^LABEL=APEX_DATA /srv/apex ext4 defaults,noatime 0 2$' /etc/fstab || echo "${APEX_DATA_FSTAB}" | sudo tee -a /etc/fstab >/dev/null
fi
sudo grep -q '^LABEL=APEX_BACKUP /mnt/apex-backup ext4 defaults,nofail,noatime,x-systemd.automount 0 2$' /etc/fstab || echo "${APEX_BACKUP_FSTAB}" | sudo tee -a /etc/fstab >/dev/null

if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  sudo mount /srv/apex
fi
sudo mount /mnt/apex-backup

sudo mkdir -p /srv/apex/postgres-dumps
sudo mkdir -p /srv/apex/snapshots
sudo mkdir -p /srv/apex/gitea
sudo mkdir -p /srv/apex/models
sudo mkdir -p /mnt/apex-backup/restic

sudo chown -R "$USER":"$USER" /srv/apex /mnt/apex-backup

RESTIC_REPOSITORY="${RESTIC_LOCAL_REPOSITORY}" restic init
RESTIC_REPOSITORY="${RESTIC_LOCAL_REPOSITORY}" restic snapshots

RESTIC_REPOSITORY="${RESTIC_S3_REPOSITORY}" restic init
RESTIC_REPOSITORY="${RESTIC_S3_REPOSITORY}" restic snapshots

mount | grep -E '/srv/apex|/mnt/apex-backup'
df -h /srv/apex /mnt/apex-backup
if [[ "${DATA_DRIVE_MODE}" == 'attached' ]]; then
  sudo blkid | grep -E 'APEX_DATA|APEX_BACKUP'
else
  sudo blkid | grep -E 'APEX_BACKUP'
fi

echo 'storage first-run completed'