# Dev-lanes Postgres backups

Nightly logical backups of the Olares dev-lanes Postgres (`apex-dev-pg`, PG17) — the
host-only dev state (`records_dev` / `ops_dev` / `orchestration_dev`) which, since the
2026-06-18 dev-residency cutover, lives **only** on the host. Closes the L2 durability
gap in `.claude/PLATFORM/APEX-PLATFORM-OPERATING-ARCHITECTURE-2026-06-18.md` §4 (L2).

## Components
- **`apex-dev-pg-backup.sh`** — `pg_dump -Fc` of each dev DB + `pg_dumpall --globals-only`,
  written to `/mnt/apex-backup/dev-pg/<UTC-stamp>/` with a `SHA256SUMS` manifest and
  `RETAIN_DAYS` (default 14) pruning. Dumps run via `docker exec apex-dev-pg`
  (container-local trust — no password handling).
- **`apex-dev-pg-backup.service`** — oneshot, `User=olares` + `SupplementaryGroups=docker`.
- **`apex-dev-pg-backup.timer`** — nightly 03:30 UTC, `Persistent=true` (catch-up if host was down).

## Install (host)
```bash
sudo install -m0755 infra/backup/apex-dev-pg-backup.sh /usr/local/bin/
sudo install -m0644 infra/backup/apex-dev-pg-backup.service /etc/systemd/system/
sudo install -m0644 infra/backup/apex-dev-pg-backup.timer   /etc/systemd/system/
sudo mkdir -p /mnt/apex-backup/dev-pg && sudo chown olares:olares /mnt/apex-backup/dev-pg
sudo systemctl daemon-reload && sudo systemctl enable --now apex-dev-pg-backup.timer
```

## Restore
```bash
docker exec -i apex-dev-pg pg_restore -U postgres -d <db> --clean --if-exists < <stamp>/<db>.dump
```

## Backlog
- Target is the dedicated 3.6 TB `/mnt/apex-backup` disk (separate spindle from the data
  volume = genuine redundancy, not same-disk copies).

## Offsite (Backblaze B2 via restic) — replicates the L2 dumps off-host (added 2026-06-18)

Mirrors the proven `apex-personal-notes` offsite pattern. Ships the L2 dump sets
(`/mnt/apex-backup/dev-pg/`) to an encrypted **restic** repo on Backblaze B2.

- **`apex-dev-pg-offsite-backup.sh`** — `restic backup /mnt/apex-backup/dev-pg`
  (tags `dev-pg host-scheduled apex-platform`) + tag-filtered `restic forget --prune`
  (keep 7d/4w/3m). Secrets sourced from an **olares-owned 0600 env file OUTSIDE the repo**
  (`~/code/apex/.env.dev-pg-offsite-backup`); refuses to run on placeholder values.
- **`apex-dev-pg-offsite-restore-drill.sh`** — restores the latest snapshot + validates a
  recovered `.dump` with the in-container PG17 `pg_restore -l`. An untested backup is no backup.
- **`*-offsite-backup.{service,timer}`** — oneshot `User=olares`, nightly **04:30 UTC** (after the 03:30 dump).
- **`*-offsite-restore-drill.{service,timer}`** — weekly **Sun 05:00 UTC**.
- **`.env.dev-pg-offsite-backup.template`** — copy + fill (B2 repo/key + restic pw from the Olares Vault).

### Activate offsite to B2 (FUTURE - deferred 2026-06-19; local-SSD config is live, see below)
```bash
cp infra/backup/.env.dev-pg-offsite-backup.template ~/code/apex/.env.dev-pg-offsite-backup
chmod 600 ~/code/apex/.env.dev-pg-offsite-backup
# edit: RESTIC_REPOSITORY (B2 s3 path) + AWS_ACCESS_KEY_ID (B2 keyID) +
#       AWS_SECRET_ACCESS_KEY + RESTIC_PASSWORD   (last two from the Vault)
set -a; . ~/code/apex/.env.dev-pg-offsite-backup; set +a
restic init                                          # one-time: create the repo
systemctl --user 2>/dev/null; sudo systemctl enable --now \
  apex-dev-pg-offsite-backup.timer apex-dev-pg-offsite-restore-drill.timer
sudo systemctl start apex-dev-pg-offsite-backup.service   # first run now
```
Secret custody for these values: `.claude/PLATFORM/APEX-SECRET-CUSTODY-MODEL.md` (L6, private substrate).

## Current backup posture (2026-06-19): local restic on the external TB5 SSD (B2 deferred)

B2 is deferred to "future". The interim off-data-disk copy is an **encrypted restic repo on the
external 4TB TB5 SSD** (OWC Express 1M2 enclosure holding the WD Black SN850X = `/mnt/apex-backup`,
confirmed via Thunderbolt topology). The same offsite scripts/units drive it — `RESTIC_REPOSITORY`
just points at a local path instead of B2 (no AWS creds for a local repo).

- **Repo:** `/mnt/apex-backup/restic-dev-pg` (restic, encrypted) — initialized + LIVE.
- **Env:** `~/code/apex/.env.dev-pg-offsite-backup` (0600) — `RESTIC_REPOSITORY` (local path) +
  `RESTIC_PASSWORD` (generated on the host; **must be saved in the Olares Vault** for recoverability).
- **Chain:** 03:30 L2 `pg_dump` → `/mnt/apex-backup/dev-pg`; 04:30 restic backs those up
  (tag-filtered forget, keep 7d/4w/3m); weekly Sun 05:00 restore-drill validates a recovered dump
  with the in-container PG17 `pg_restore`. Redundancy = data on the internal NVMe vs backups on the
  external SSD; restic adds encryption + versioning + dedup on top.
- **Switch to B2 later:** set `RESTIC_REPOSITORY=s3:…` + B2 AWS creds in the env, then `restic init`.
