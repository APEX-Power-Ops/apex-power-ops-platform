# Private Stack Example

This directory contains a minimal private-stack example that stays outside the
current governed Olares-installed app scope.

It is intentionally separate from:

1. `infra/compose.dev.yml`
2. `infra/olares/`
3. the installed-proof and canary surfaces for `forms-engine` and `p6-ingest`

## What This Example Is

This example is a small personal-only compose stack with:

1. `personal-notes` as a simple private browser service
2. `personal-postgres` as an optional profile-gated local database for later
   personal services

The database service is off by default. Enable it only if a later personal
service actually needs Postgres.

## Recommended Default

Use this example in the following posture unless a real need appears:

1. keep `personal-notes` as the first live personal service
2. keep access host-only through `127.0.0.1`
3. treat the data as useful but recoverable, not mission-critical
4. leave the `db` profile off until a later service actually requires it

This is the lowest-risk starting point because it avoids premature auth,
ingress, database, and backup complexity.

## Personal Zone For Non-APEX Use

If what you want is a safe general-purpose personal area on the Olares machine,
start here first:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-zone-remote.ps1 -Action setup
```

That prepares a user-owned `~/Personal` area on the host for downloads, notes,
scratch files, and personal compose experiments without mixing them into the
APEX repo lanes.

Plain-English usage guidance lives in:

1. `infra/private/PERSONAL-ZONE-QUICKSTART.md`
2. `infra/private/personal-notes-access.ps1`
3. `infra/private/PERSONAL-FILES-BRIDGE-QUICKSTART.md`
4. `infra/private/personal-files-access.ps1`

Important limit: this Olares host is Ubuntu Linux and Docker is Linux-only, so
native Windows containers are not supported on this machine.

If a personal Windows environment is needed, use the separate Windows Lab lane
documented in `infra/private/WINDOWS-LAB-QUICKSTART.md`. That lab is a Windows
VM running through Docker with KVM acceleration and stays outside the governed
APEX surfaces.

If you want the host-side `~/Personal` lane visible inside the Olares `Files`
app, use the separate SMB bridge helper documented in
`infra/private/PERSONAL-FILES-BRIDGE-QUICKSTART.md`. That bridge keeps the
platform-managed Files storage volume separate and exposes only the bounded
personal folder as an external server-backed location. If Windows Explorer
access is also needed, re-share that mounted folder from inside Olares Files
through its `SMB share` action rather than using the host bridge credential
directly.

## Why This Shape

This is the smallest concrete pattern that satisfies the private-stack
blueprint:

1. localhost-only exposure by default
2. isolated data root
3. no Olares app registration
4. no overlap with the governed APEX app surfaces
5. a realistic personal browser utility rather than an empty placeholder

## Expected Host Layout

Recommended host paths on the Olares machine:

```text
~/code/personal/            -> personal compose files and local notes
~/apex-data/personal/       -> bind-mounted service state
~/apex-secrets/personal/    -> non-git secrets and credentials
```

The checked-in env file is a template only.

## First-Run Guidance

1. copy `.env.personal.template` to a non-git location such as
   `~/code/personal/.env.personal`
2. create the bind-mount paths under `~/apex-data/personal/`
3. replace the placeholder Postgres password before enabling the `db` profile
4. keep ports bound to `127.0.0.1` unless private-mesh access is intentionally
   needed
5. use the included wrapper script so the default path stays consistent
6. on the real Olares host, prefer the setup helper before the first `config`
   or `up` run

## Data Recommendation

For the default `personal-notes` service, treat the mounted data at
`~/apex-data/personal/memos` as useful but recoverable.

That means:

1. keep it on a dedicated personal path
2. do not assume it is part of the governed APEX backup posture
3. use the bounded snapshot path under `~/apex-backups/personal/memos` if you
   want a local restore point for the private notes service
4. avoid storing irreplaceable material in it until you have tested a restore
   path for personal services

## Example Commands

Preferred PowerShell wrapper:

```powershell
pwsh -NoProfile -File infra/private/run-personal-stack.ps1 -Action up
```

Preferred remote PowerShell wrapper for the real Olares host:

```powershell
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action setup
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action config
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action up
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action tunnel
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action backup
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action status
```

The remote wrapper defaults to the verified private-mesh path
`olares@100.64.0.1` for the real Olares host. Override `-HostAlias` only when a
different trusted SSH target is intentionally required.

If SSH reports a host-key mismatch, stop and reconcile `known_hosts` before
attempting setup, bring-up, or tunneling.

When SSH trust is blocked but an authenticated Olares desktop session is
available, the browser terminal is a valid trusted fallback for bounded host
operations. That is the path used for the first verified bring-up of
`personal-notes` on 2026-05-01.

Run only the notes service with raw Docker Compose:

```bash
docker compose \
  --env-file ~/code/personal/.env.personal \
  -f infra/private/personal-stack.compose.yml \
  up -d
```

Run the notes service plus the optional database:

```bash
docker compose \
  --env-file ~/code/personal/.env.personal \
  -f infra/private/personal-stack.compose.yml \
  --profile db \
  up -d
```

Stop the private stack:

```bash
docker compose \
  --env-file ~/code/personal/.env.personal \
  -f infra/private/personal-stack.compose.yml \
  down
```

Preview the resolved configuration through the wrapper:

```powershell
pwsh -NoProfile -File infra/private/run-personal-stack.ps1 -Action config
```

Open a local SSH tunnel to the host-only notes service from the workstation:

```powershell
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action tunnel
```

That maps local `http://127.0.0.1:5231` to host `127.0.0.1:5230` by default.
Use `-LocalPort`, `-RemoteHost`, or `-RemotePort` only when a bounded alternate
mapping is actually needed.

Create a bounded local backup archive for the notes service on the Olares host:

```powershell
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action backup
```

That writes a timestamped archive under `~/apex-backups/personal/memos/` and
packages a consistent `memos/memos_prod.db` snapshot plus a small manifest.

Create that same host snapshot and immediately pull a workstation copy outside
the Olares host:

```powershell
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action backup-fetch
```

By default, that downloads the created archive into `$HOME\OlaresPersonalBackups\memos` on the workstation.

Mirror the workstation backup set into the default offsite folder under the
personal OneDrive tree:

```powershell
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action sync-offsite
```

By default, that copies new or changed workstation archives into
`$HOME\OneDrive\OlaresPersonalBackups\memos`.

Create a fresh host archive, fetch it to the workstation, and mirror the full
workstation backup set into the offsite folder in one step:

```powershell
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action backup-fetch-sync
```

Install the bounded workstation-side scheduler for that same end-to-end backup
flow:

```powershell
pwsh -NoProfile -File infra/private/personal-notes-backup-schedule.ps1 -Action install
```

Check the installed task state at any time:

```powershell
pwsh -NoProfile -File infra/private/personal-notes-backup-schedule.ps1 -Action status
```

Run the scheduled flow immediately without waiting for the next trigger:

```powershell
pwsh -NoProfile -File infra/private/personal-notes-backup-schedule.ps1 -Action run-now
```

Scaffold the separate host-owned encrypted offsite backup helper on the Olares
host:

```powershell
pwsh -NoProfile -File infra/private/run-personal-notes-offsite-backup-remote.ps1 -Action setup
```

That creates the machine-local host env file
`~/code/personal/.env.personal-offsite-backup` if it does not already exist and
prepares the isolated restore-drill root under
`~/apex-restore-drills/personal/memos`.

Check the current host-owned offsite readiness state at any time:

```powershell
pwsh -NoProfile -File infra/private/run-personal-notes-offsite-backup-remote.ps1 -Action status
```

Validated on 2026-05-02: the helper reached the real Olares host over the
restored mesh path, confirmed `restic` is installed at `/usr/local/bin/restic`,
confirmed the machine-local env file exists, and after the host-local env was
completed with the existing Backblaze bucket endpoint plus the matching vault-
held key material, `status` confirmed the repository is reachable.

Initialize the encrypted offsite repository if needed:

```powershell
pwsh -NoProfile -File infra/private/run-personal-notes-offsite-backup-remote.ps1 -Action init
```

Create a fresh host-local Notes archive and push the full host archive root into
the encrypted offsite repository:

```powershell
pwsh -NoProfile -File infra/private/run-personal-notes-offsite-backup-remote.ps1 -Action backup
```

List the current encrypted offsite snapshots:

```powershell
pwsh -NoProfile -File infra/private/run-personal-notes-offsite-backup-remote.ps1 -Action snapshots
```

Run retention and prune using either the default template values or explicit
overrides:

```powershell
pwsh -NoProfile -File infra/private/run-personal-notes-offsite-backup-remote.ps1 -Action forget-prune
```

Run the bounded restore drill for the encrypted offsite path without touching
the live Notes runtime:

```powershell
pwsh -NoProfile -File infra/private/run-personal-notes-offsite-backup-remote.ps1 -Action restore-drill
```

That restores the latest encrypted offsite snapshot into
`~/apex-restore-drills/personal/memos/<timestamp>` on the host, finds a
recovered `personal-notes-*.tgz` archive there, and validates that the restored
archive still contains both `manifest.json` and `memos/memos_prod.db`.

Validated on 2026-05-02: `init` confirmed the encrypted offsite repository was
already initialized, `backup` created fresh host archive
`/home/olares/apex-backups/personal/memos/personal-notes-20260502T180208Z.tgz`,
saved Restic snapshot `542e7b9f`, and `restore-drill` restored that snapshot
into `/home/olares/apex-restore-drills/personal/memos/20260502T180214Z` while
validating the recovered archive contents without touching the live Notes
runtime.

Install the separate host-side recurring systemd timer for that same encrypted
offsite path:

```powershell
pwsh -NoProfile -File infra/private/personal-notes-offsite-backup-schedule.ps1 -Action install
```

Check the installed timer and service state:

```powershell
pwsh -NoProfile -File infra/private/personal-notes-offsite-backup-schedule.ps1 -Action status
```

Run the host-side timer payload immediately without waiting for the next daily
window:

```powershell
pwsh -NoProfile -File infra/private/personal-notes-offsite-backup-schedule.ps1 -Action run-now
```

Remove the host-side timer and deployed host runner if the cadence needs to be
withdrawn:

```powershell
pwsh -NoProfile -File infra/private/personal-notes-offsite-backup-schedule.ps1 -Action uninstall
```

Validated on 2026-05-02: the helper deployed
`/home/olares/code/personal/run-personal-notes-offsite-backup-host.sh`,
installed system units `apex-personal-notes-offsite-backup.service` and
`apex-personal-notes-offsite-backup.timer`, registered a daily `03:30 UTC`
timer window with `RandomizedDelaySec=20m`, applied `StartLimitIntervalSec=6h`
plus `StartLimitBurst=2`, and writes append-only service output to
`/home/olares/apex-logs/personal/apex-personal-notes-offsite-backup.log` with
weekly logrotate retention (`rotate 8`, `size 5M`). `run-now` completed
successfully with Restic snapshot `76b8155c` while pruning the earlier
host-scheduled snapshot.

Install the separate host-side recurring restore-drill timer with the same
operator helper:

```powershell
pwsh -NoProfile -File infra/private/personal-notes-offsite-backup-schedule.ps1 -Action install -ScheduleProfile restore-drill
```

Check or manually run that restore-drill cadence:

```powershell
pwsh -NoProfile -File infra/private/personal-notes-offsite-backup-schedule.ps1 -Action status -ScheduleProfile restore-drill
pwsh -NoProfile -File infra/private/personal-notes-offsite-backup-schedule.ps1 -Action run-now -ScheduleProfile restore-drill
```

Validated on 2026-05-02: the restore-drill profile deployed
`/home/olares/code/personal/run-personal-notes-offsite-restore-drill-host.sh`,
installed `apex-personal-notes-offsite-restore-drill.service` and
`apex-personal-notes-offsite-restore-drill.timer`, registered a weekly Sunday
`05:00 UTC` timer window with the same `20m` jitter, and `run-now` completed
successfully by restoring snapshot `76b8155c` into
`/home/olares/apex-restore-drills/personal/memos/20260502T182526Z` while
validating recovered archive
`/home/olares/apex-restore-drills/personal/memos/20260502T182526Z/home/olares/apex-backups/personal/memos/personal-notes-20260502T181904Z.tgz`.

Restore a previously created archive back into the live notes data path:

```powershell
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 `
   -Action restore `
   -ArchiveFile '/home/olares/apex-backups/personal/memos/personal-notes-YYYYMMDDTHHMMSSZ.tgz' `
   -ForceRestore
```

By default, restore stops `personal-notes`, creates a pre-restore snapshot,
replaces `~/apex-data/personal/memos`, and restarts the service. Use
`-SkipRestart` only when an operator explicitly wants the service left stopped
after restore.

Restore from a workstation-held archive copy by uploading it back to the Olares
host and then running the same validated restore flow:

```powershell
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 `
   -Action restore-local `
   -LocalArchiveFile "$HOME\OlaresPersonalBackups\memos\personal-notes-YYYYMMDDTHHMMSSZ.tgz" `
   -ForceRestore
```

Validated on 2026-05-01: restoring
`/home/olares/apex-backups/personal/memos/personal-notes-20260501T234336Z.tgz`
completed successfully, restarted `personal-notes`, and preserved the seeded
`Personal Notes Bootstrap` memo. The restore run also emitted a pre-restore
snapshot at `/home/olares/apex-backups/personal/memos/pre-restore-personal-notes-20260501T234743Z.tgz`.

Validated on 2026-05-02: `backup-fetch` created a new host archive at
`/home/olares/apex-backups/personal/memos/personal-notes-20260502T012105Z.tgz`,
downloaded it to the workstation at
`C:\Users\jjswe\OlaresPersonalBackups\memos\personal-notes-20260502T012105Z.tgz`,
and `restore-local` successfully re-uploaded that workstation copy, completed a
forced restore, emitted pre-restore snapshot
`/home/olares/apex-backups/personal/memos/pre-restore-personal-notes-20260502T012221Z.tgz`,
and returned `HTTP 200` with the seeded `Personal Notes Bootstrap` memo intact.

Validated on 2026-05-02: `backup-fetch-sync` created host archive
`/home/olares/apex-backups/personal/memos/personal-notes-20260502T012419Z.tgz`,
downloaded it to the workstation at
`C:\Users\jjswe\OlaresPersonalBackups\memos\personal-notes-20260502T012419Z.tgz`,
and mirrored the workstation backup set into the offsite folder
`C:\Users\jjswe\OneDrive\OlaresPersonalBackups\memos`, where both fetched
archives are now present.

Validated on 2026-05-02: `personal-notes-backup-schedule.ps1 -Action install`
now succeeds on this workstation by installing the required daily task
`APEX-Olares-Personal-Notes-Backup-Daily` for `02:15`. The helper reports the
`AtLogOn` trigger honestly as optional and not installed because local Task
Scheduler policy returns `Access is denied` for `ONLOGON` task creation here.
`-Action run-now` was then revalidated end to end: it created host archive
`/home/olares/apex-backups/personal/memos/personal-notes-20260502T172606Z.tgz`,
downloaded it to the workstation, mirrored it into
`C:\Users\jjswe\OneDrive\OlaresPersonalBackups\memos`, and wrote a local log
file under `C:\Users\jjswe\OlaresPersonalBackups\logs`.

Print a one-command proof summary for the current host state:

```powershell
pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action status
```

That reports the live `docker compose ps` state, host-local HTTP health,
SQLite user and memo counts, the first memo headline, the latest host-local
backup archives, the workstation backup copy folder contents, and the offsite
backup mirror folder contents.

## Operating Rules

1. do not treat this stack as part of the current Olares installed-app set
2. do not place secrets in the repo copy of the env template
3. do not publish this service through public ingress by default
4. do not add canary or installed-proof claims for this stack without a new
   explicit packet
5. if the service later needs shared auth, a stable Olares entrance, or formal
   backup coverage, open a new packet before promoting it
6. do not bypass SSH host-key verification just to make the remote wrapper run
7. keep host-owned encrypted offsite repository and credential values machine-local and out of repo publication scope

## Related Files

1. `docs/architecture/OLARES-PRIVATE-STACK-BLUEPRINT-2026-05-01.md`
2. `infra/compose.dev.yml`
3. `infra/olares/`
4. `infra/private/run-personal-stack.ps1`
5. `infra/private/run-personal-stack.sh`
6. `docs/architecture/OLARES-PRIVATE-STACK-FIRST-RUN-CHECKLIST-2026-05-01.md`
7. `infra/private/setup-personal-stack.sh`
8. `infra/private/run-personal-stack-remote.ps1`
9. `infra/private/personal-stack-operator-note.template.md`
10. `infra/private/reconcile-olares-ssh-hostkey.ps1`
11. `docs/architecture/OLARES-SSH-HOSTKEY-RECONCILIATION-2026-05-01.md`
12. `infra/private/run-personal-notes-offsite-backup-remote.ps1`
13. `infra/private/.env.personal-offsite-backup.template`