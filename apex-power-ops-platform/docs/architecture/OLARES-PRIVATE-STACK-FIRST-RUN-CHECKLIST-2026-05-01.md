# Olares Private Stack First-Run Checklist

Date: 2026-05-01
Status: Active bounded first-run surface; host bring-up, workstation UI proof, bounded backup automation, host-side encrypted offsite cadence, and recurring restore-drill cadence verified
Scope: first live bring-up of the private personal stack on an Olares-aligned host without expanding the governed Olares-installed app set

## Purpose

Use this checklist for the first live bring-up of the private personal stack
defined by the current `infra/private/` example.

This checklist exists to keep the first private deployment small, reversible,
and outside the governed `forms-engine` and `p6-ingest` installed-app lane.

It does not authorize:

1. a new Olares-installed app
2. public ingress
3. shared OIDC sign-on
4. canary or installed-proof claims for the private stack

## Current Evidence Floor

Treat these files as the current first-run surface:

1. `docs/architecture/OLARES-PRIVATE-STACK-BLUEPRINT-2026-05-01.md`
2. `infra/private/personal-stack.compose.yml`
3. `infra/private/.env.personal.template`
4. `infra/private/README.md`
5. `infra/private/run-personal-stack.ps1`
6. `infra/private/run-personal-stack.sh`
7. `infra/private/setup-personal-stack.sh`
8. `infra/private/run-personal-stack-remote.ps1`
9. `infra/private/personal-stack-operator-note.template.md`
10. `infra/private/reconcile-olares-ssh-hostkey.ps1`
11. `docs/architecture/OLARES-SSH-HOSTKEY-RECONCILIATION-2026-05-01.md`
12. `infra/private/run-personal-notes-offsite-backup-remote.ps1`
13. `infra/private/.env.personal-offsite-backup.template`
14. `infra/private/run-personal-notes-offsite-backup-host.sh`
15. `infra/private/personal-notes-offsite-backup-schedule.ps1`
16. `infra/private/run-personal-notes-offsite-restore-drill-host.sh`

## Preconditions

1. Docker and Docker Compose are available on the target host
2. the target host has a non-git personal env file path such as
   `~/code/personal/.env.personal`
3. the target host has a dedicated personal data root such as
   `~/apex-data/personal/`
4. the operator intends to start with `personal-notes` only and leave the `db`
   profile off unless a real need exists
5. the operator accepts the default posture that personal data is useful but
   recoverable rather than already covered by the governed APEX backup proof
6. the SSH alias used by `infra/private/run-personal-stack-remote.ps1` is still
   trusted and does not fail host-key verification

## First-Run Steps

1. verify that `infra/private/personal-stack.compose.yml`,
   `infra/private/.env.personal.template`, and the wrapper script for the host
   shell are present and readable
2. run the host setup helper first so the env file, note file, and bind-mount
   paths are created consistently:
   - PowerShell via SSH: `pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action setup`
   - POSIX on host: `bash infra/private/setup-personal-stack.sh`
3. confirm that `PERSONAL_NOTES_PORT` remains a host-only port binding and do
   not widen it beyond `127.0.0.1` for the first run
4. if the `db` profile will remain off, leave the placeholder Postgres password
   untouched and do not start the optional database service
5. run the wrapper config check first:
   - PowerShell via SSH: `pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action config`
   - POSIX on host: `bash infra/private/run-personal-stack.sh config`
6. bring up the notes service only:
   - PowerShell via SSH: `pwsh -NoProfile -File infra/private/run-personal-stack-remote.ps1 -Action up`
   - POSIX on host: `bash infra/private/run-personal-stack.sh up`
7. confirm that the service is reachable only through the host-bound port and
   that no public or Olares-native route has been introduced
8. open the notes service locally and confirm that new content persists across
   a stop and restart of the stack
9. record the live host path used for the env file and the data directory in a
   machine-local operator note outside the git workspace

## Default Success Criteria

The first run is considered successful when all of the following are true:

1. the private stack starts through the wrapper without editing the checked-in
   compose file
2. only the `personal-notes` service is live by default
3. access remains host-only through `127.0.0.1`
4. note data persists under the dedicated personal data path after restart
5. the private stack remains outside the governed Olares installed-app surface

## Observed Result On 2026-05-01

The initial host bring-up was completed through the authenticated Olares browser
terminal after workstation SSH remained trust-blocked.

Verified results:

1. `personal-notes` was started as user `olares` through Docker Compose
2. `docker compose ... ps` showed `private-personal-notes-1` up with
   `127.0.0.1:5230->5230/tcp`
3. `curl -I -s http://127.0.0.1:5230 | head -n 5` returned `HTTP/1.1 200 OK`
4. a full `docker compose down && docker compose up -d` cycle returned the
   service to `Up` state on the same host-only port
5. a local-only bootstrap admin credential file was written to
   `/home/olares/apex-secrets/personal/memos-admin.env` with `600`
   permissions and `olares` ownership
6. a sentinel private memo was persisted in the SQLite store and still existed
   after a container restart
7. gRPC reflection on the live Memos service exposed the auth and memo
   procedures needed for host-side application verification
8. a live `AuthService/SignIn` call returned the seeded `ADMIN` user and issued
   a `memos.access-token` cookie
9. reusing that access token against `GET /api/v1/users/1/memos?pageSize=10`
   returned the sentinel private memo through the application API surface
10. the service remained outside the governed Olares installed-app lane

Interactive browser proof was also completed after the Windows mesh path was
recovered.

Additional verified results:

1. the Windows `LarePass` client reached `BackendState: Running` with mesh IP
   `100.64.0.2`
2. `Test-NetConnection 100.64.0.1 -Port 22` succeeded from the workstation
3. non-interactive SSH to `olares@100.64.0.1` succeeded using a temporary
   `UserKnownHostsFile`
4. an SSH tunnel from workstation `127.0.0.1:5231` to host `127.0.0.1:5230`
   loaded the live Memos browser UI successfully
5. the first UI load initially still presented site-host signup because the
   direct SQLite bootstrap had inserted the seeded account as role `ADMIN`
   instead of `HOST`, which is what live Memos `v0.24.3` uses for workspace
   owner detection
6. correcting that one user row from `ADMIN` to `HOST` caused the workspace
   profile to report owner `users/1`
7. signing in through the tunneled browser with the machine-local bootstrap
   credential reached the live home view and rendered the sentinel memo
   `Personal Notes Bootstrap`
8. the workstation access path is now codified in
   `infra/private/run-personal-stack-remote.ps1 -Action tunnel`, which defaults
   to the restored mesh SSH target `olares@100.64.0.1` and local port `5231`
9. a bounded backup path is now codified in
   `infra/private/run-personal-stack-remote.ps1 -Action backup`, which created
   `/home/olares/apex-backups/personal/memos/personal-notes-20260501T234336Z.tgz`
10. listing that archive showed `manifest.json`, `memos/`, and
    `memos/memos_prod.db`, which is sufficient for a bounded local restore path
11. a live restore from that archive completed successfully through
   `infra/private/run-personal-stack-remote.ps1 -Action restore -ForceRestore`
   and produced the pre-restore safety archive
   `/home/olares/apex-backups/personal/memos/pre-restore-personal-notes-20260501T234743Z.tgz`
12. after restore, `curl -I http://127.0.0.1:5230` still returned
   `HTTP/1.1 200 OK`, and the restored SQLite store still showed `user_count 1`,
   `memo_count 1`, and the memo header `# Personal Notes Bootstrap`
13. `infra/private/run-personal-stack-remote.ps1 -Action status` now emits a
   one-command proof summary for the live host, including compose state, HTTP
   health, SQLite counts, the first memo headline, and the latest local
   backup archives
14. `infra/private/run-personal-stack-remote.ps1 -Action backup-fetch` now
   creates a fresh host archive and downloads a separate workstation copy under
   `$HOME\OlaresPersonalBackups\memos`
15. `infra/private/run-personal-stack-remote.ps1 -Action backup-fetch-sync`
   now mirrors that workstation backup set into
   `$HOME\OneDrive\OlaresPersonalBackups\memos`
16. `infra/private/personal-notes-backup-schedule.ps1 -Action install` now
   installs the required daily Task Scheduler path for the bounded backup flow
17. on this workstation the optional `AtLogOn` trigger remains unavailable
   because local Task Scheduler policy denies `ONLOGON` task creation, and the
   helper reports that limitation honestly instead of claiming full trigger
   coverage
18. `infra/private/run-personal-notes-offsite-backup-remote.ps1 -Action setup`
   and `-Action status` first validated the separate host-owned encrypted
   offsite lane scaffold: the real Olares host already has `restic`, the
   machine-local env file exists at
   `/home/olares/code/personal/.env.personal-offsite-backup`, and the
   restore-drill root exists at
   `/home/olares/apex-restore-drills/personal/memos`
19. after the host-local env file was completed with the existing Backblaze
   repository path and the matching vault-held secrets, `-Action status`
   confirmed the repository is reachable, `-Action init` confirmed it was
   already initialized, `-Action backup` created fresh archive
   `/home/olares/apex-backups/personal/memos/personal-notes-20260502T180208Z.tgz`
   and Restic snapshot `542e7b9f`, and `-Action restore-drill` recovered and
   validated that archive in
   `/home/olares/apex-restore-drills/personal/memos/20260502T180214Z` without
   touching the live runtime
20. `infra/private/personal-notes-offsite-backup-schedule.ps1 -Action install`
   deployed host runner
   `/home/olares/code/personal/run-personal-notes-offsite-backup-host.sh`
   together with system units
   `apex-personal-notes-offsite-backup.service` and
   `apex-personal-notes-offsite-backup.timer`
21. `infra/private/personal-notes-offsite-backup-schedule.ps1 -Action status`
   confirmed the timer is enabled and active with next run scheduled inside the
   daily `03:30 UTC` window with `20m` jitter
22. `infra/private/personal-notes-offsite-backup-schedule.ps1 -Action run-now`
   completed successfully, produced Restic snapshot `76b8155c`, and pruned the
   earlier host-scheduled snapshot without touching the live Notes runtime
23. the deployed backup timer now has explicit hardening on the live host:
   `RandomizedDelaySec=20m`, `StartLimitIntervalSec=6h`,
   `StartLimitBurst=2`, append-only file logs under
   `/home/olares/apex-logs/personal/apex-personal-notes-offsite-backup.log`,
   and weekly logrotate retention
24. `infra/private/personal-notes-offsite-backup-schedule.ps1 -Action install -ScheduleProfile restore-drill`
   deployed host runner
   `/home/olares/code/personal/run-personal-notes-offsite-restore-drill-host.sh`
   together with system units
   `apex-personal-notes-offsite-restore-drill.service` and
   `apex-personal-notes-offsite-restore-drill.timer`
25. `infra/private/personal-notes-offsite-backup-schedule.ps1 -Action status -ScheduleProfile restore-drill`
   confirmed the weekly Sunday `05:00 UTC` restore-drill window is enabled and
   active with the same jitter behavior
26. `infra/private/personal-notes-offsite-backup-schedule.ps1 -Action run-now -ScheduleProfile restore-drill`
   completed successfully, restored snapshot `76b8155c` into
   `/home/olares/apex-restore-drills/personal/memos/20260502T182526Z`, and
   validated recovered archive
   `/home/olares/apex-restore-drills/personal/memos/20260502T182526Z/home/olares/apex-backups/personal/memos/personal-notes-20260502T181904Z.tgz`

## Do Not Do On First Run

1. do not enable public ingress
2. do not add OlaresManifest files for the private service
3. do not enable the optional database service unless the notes-first shape is
   already insufficient
4. do not place the real env file inside the repo
5. do not classify the service as protected by the governed backup posture
6. do not bypass an SSH host-key mismatch to force the remote wrapper through

## After First Run

After the first run succeeds, the next honest choices are:

1. leave the service host-only and continue using it as a private local tool
2. keep workstation access on demand through the restored private-mesh SSH path
   and local tunneling if a real device-to-device need appears
3. if personal data becomes more than useful-but-recoverable, test the bounded
   `backup`, `backup-fetch-sync`, and `restore` paths before claiming stronger
   recovery posture
4. the separate host-owned encrypted offsite helper is now part of the bounded
   proven recovery posture and should be rerun through `status`, `backup`,
   `snapshots`, `forget-prune`, and `restore-drill` after host, credential, or
   repository drift
5. the host-side recurring timer is now the bounded cadence path for encrypted
   offsite backup and retention and should be checked with `status` or forced
   with `run-now` after systemd, host, or credential drift
6. the weekly restore-drill timer is now part of the bounded recovery proof
   surface and should be checked with `status -ScheduleProfile restore-drill`
   or forced with `run-now -ScheduleProfile restore-drill` after systemd,
   host, credential, or repository drift
7. open a separate explicit packet before any graduation to Olares-native app
   behavior, shared auth, or formal backup and recovery coverage

At the current boundary, the bounded local snapshot and restore path has now
been tested once successfully, but that still does not elevate the private lane
into the governed APEX backup posture.

## Exit Condition

This checklist remains valid when a host operator can bring up the first private
notes service from the existing `infra/private/` surfaces without widening into
new Olares app scope, public exposure, or governed proof claims.
