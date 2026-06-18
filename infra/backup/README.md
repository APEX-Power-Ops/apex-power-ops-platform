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
- **Offsite** — replicate `/mnt/apex-backup` to Backblaze B2 (needs B2 credentials → operator).
- Target is the dedicated 3.6 TB `/mnt/apex-backup` disk (separate spindle from the data
  volume = genuine redundancy, not same-disk copies).
