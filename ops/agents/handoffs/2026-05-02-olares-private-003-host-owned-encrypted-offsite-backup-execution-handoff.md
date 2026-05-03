# Olares Private 003 Host-Owned Encrypted Offsite Backup Execution Handoff

Date: 2026-05-02
Status: Complete
Related packet: `ops/agents/packets/draft/2026-05-02-olares-private-003-host-owned-encrypted-offsite-backup-execution.json`
Related planning packet: `ops/agents/packets/draft/2026-05-02-olares-private-002-backup-governance-hardening-planning.json`
Related planning handoff: `ops/agents/handoffs/2026-05-02-olares-private-002-backup-governance-hardening-planning-handoff.md`

## Purpose

Implement the bounded repo surfaces for host-owned encrypted offsite backup and
restore-drill hardening over the existing `personal-notes` host-local archive
set.

This packet does not widen runtime, ingress, auth, or installed-app scope.

## What Landed

1. `infra/private/run-personal-notes-offsite-backup-remote.ps1`
   - dedicated mesh-SSH helper for host-owned encrypted offsite backup
   - scoped actions: `setup`, `status`, `init`, `backup`, `snapshots`,
     `forget-prune`, `restore-drill`
   - uses the existing host-local notes archive root as the governed backup
     source instead of introducing a second live-database path
2. `infra/private/.env.personal-offsite-backup.template`
   - machine-local template for encrypted offsite repository and credential
     values
   - intended to be copied to the host outside repo publication scope and then
     filled with real values there

## Current Boundary After This Packet

1. the live `personal-notes` service remains host-only or mesh-tunneled
2. the existing workstation-held export and workstation-mediated OneDrive mirror
   remain the current off-host floor until the host-owned encrypted repository
   is initialized live
3. the new helper governs the host-owned encrypted path over the existing
   `~/apex-backups/personal/memos` archive root
4. restore-drill hardening restores into an isolated host path under
   `~/apex-restore-drills/personal/memos` and validates recovered archive
   integrity without touching the live runtime by default

## Validation Disposition

Repo implementation is complete.

Live encrypted offsite proof is now complete on the real Olares host.

Validation completed on 2026-05-02:

1. `run-personal-notes-offsite-backup-remote.ps1 -Action setup` reached the real
   Olares host and created or preserved the host-local env file path
   `/home/olares/code/personal/.env.personal-offsite-backup`
2. that same run prepared the isolated restore-drill root at
   `/home/olares/apex-restore-drills/personal/memos`
3. `run-personal-notes-offsite-backup-remote.ps1 -Action status` confirmed
   `restic` is installed at `/usr/local/bin/restic`
4. the helper also confirmed the existing local Notes archive root is present
   and already contains the validated `personal-notes-*.tgz` archive series
5. the host-local env file was then completed with the existing Backblaze bucket
   endpoint, the existing Olares storage access key id, the matching Backblaze
   secret access key, and the existing Restic repository password held in the
   authorized vault surfaces
6. `run-personal-notes-offsite-backup-remote.ps1 -Action status` then confirmed
   the repository is configured, credentials are ready, and the repository is
   reachable
7. `run-personal-notes-offsite-backup-remote.ps1 -Action init` confirmed the
   encrypted offsite repository was already initialized rather than creating a
   parallel repository
8. `run-personal-notes-offsite-backup-remote.ps1 -Action backup` created fresh
   host archive `/home/olares/apex-backups/personal/memos/personal-notes-20260502T180208Z.tgz`
   and saved Restic snapshot `542e7b9f` tagged for `personal-notes`
9. `run-personal-notes-offsite-backup-remote.ps1 -Action restore-drill`
   restored that snapshot into
   `/home/olares/apex-restore-drills/personal/memos/20260502T180214Z` and
   validated the recovered archive contents without touching the live Notes
   runtime

## Next Action

1. keep the workstation-mediated OneDrive mirror as a secondary off-host copy
   path unless a later packet intentionally retires it
2. rerun `backup`, `snapshots`, `forget-prune`, and `restore-drill` after host,
   credential, repository, or restore-path drift
3. open a later bounded packet only if host-owned offsite backup now needs
   recurring automation beyond the current operator-invoked helper path