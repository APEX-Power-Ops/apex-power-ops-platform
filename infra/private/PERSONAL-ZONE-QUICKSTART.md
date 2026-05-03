# Personal Zone Quickstart

This is the safe non-APEX area on the Olares workstation.

It is designed for:

1. personal downloads
2. trying personal Linux apps and Docker Compose stacks
3. personal notes and scratch work
4. app experiments that should stay outside the APEX repo and runtime lanes

It is not for:

1. APEX source code
2. APEX runtime data
3. APEX secrets
4. Windows containers on the Olares host

## One-Time Setup

From this repo on your Windows workstation:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-zone-remote.ps1 -Action setup
```

That creates these host paths for user `olares`:

1. `~/Personal/Downloads`
2. `~/Personal/Notes`
3. `~/Personal/Scratch`
4. `~/Personal/Compose` -> `~/code/personal/compose`
5. `~/Personal/Data` -> `~/apex-data/personal`
6. `~/Personal/Backups` -> `~/apex-backups/personal`

## What To Use It For

Use `~/Personal/Downloads` for files you bring onto the machine.

Use `~/Personal/Compose` for small personal Docker Compose experiments.

Use `~/Personal/Notes` and `~/Personal/Scratch` for plain non-APEX work.

Use this existing helper to open the already-running Personal Notes app from the workstation:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-access.ps1 -Action open
```

To create a host backup for Personal Notes and pull a workstation copy outside
the Olares machine:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-stack-remote.ps1 -Action backup-fetch
```

That writes the local workstation copy under `$HOME\OlaresPersonalBackups\memos`
by default.

To mirror the workstation backup set into the default offsite folder under the
personal OneDrive tree:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-stack-remote.ps1 -Action sync-offsite
```

To create a fresh host backup, pull it to the workstation, and mirror it into
that offsite folder in one step:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-stack-remote.ps1 -Action backup-fetch-sync
```

To install the workstation-side daily scheduler for that same backup flow:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-backup-schedule.ps1 -Action install
```

To check or manually run it later:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-backup-schedule.ps1 -Action status
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-backup-schedule.ps1 -Action run-now
```

To scaffold the separate host-owned encrypted offsite helper on the Olares host
and check whether it is ready for live use:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-notes-offsite-backup-remote.ps1 -Action setup
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-notes-offsite-backup-remote.ps1 -Action status
```

Validated on 2026-05-02: that helper confirmed the real host already has
`restic`, confirmed the host-local env file exists, and after that env file was
completed with the existing Backblaze bucket and matching vault-held secrets,
the helper passed `status`, `init`, `backup`, and `restore-drill` against the
real host.

On this workstation the daily task is installed successfully, while the logon
trigger remains optional and is skipped because local Task Scheduler policy
denies `ONLOGON` task creation.

To install a host-side recurring systemd timer for the encrypted offsite path:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-offsite-backup-schedule.ps1 -Action install
```

To check or manually run that host-side cadence later:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-offsite-backup-schedule.ps1 -Action status
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-offsite-backup-schedule.ps1 -Action run-now
```

Validated on 2026-05-02: that helper deployed the host-native runner at
`/home/olares/code/personal/run-personal-notes-offsite-backup-host.sh`,
installed `apex-personal-notes-offsite-backup.timer` for a daily `03:30 UTC`
window with `20m` jitter, added append-only file logging under
`/home/olares/apex-logs/personal/apex-personal-notes-offsite-backup.log` plus
weekly logrotate retention, and a manual `run-now` completed successfully with
Restic snapshot `76b8155c`.

To install the matching weekly restore-drill cadence:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-offsite-backup-schedule.ps1 -Action install -ScheduleProfile restore-drill
```

To check or manually run the restore drill later:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-offsite-backup-schedule.ps1 -Action status -ScheduleProfile restore-drill
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-offsite-backup-schedule.ps1 -Action run-now -ScheduleProfile restore-drill
```

Validated on 2026-05-02: that profile deployed
`/home/olares/code/personal/run-personal-notes-offsite-restore-drill-host.sh`,
installed `apex-personal-notes-offsite-restore-drill.timer` for weekly Sunday
`05:00 UTC` execution with the same jitter, and a manual `run-now` restored
snapshot `76b8155c` into isolated drill root
`/home/olares/apex-restore-drills/personal/memos/20260502T182526Z`.

To restore from one of those workstation-held archives:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-stack-remote.ps1 `
	-Action restore-local `
	-LocalArchiveFile "$HOME\OlaresPersonalBackups\memos\personal-notes-YYYYMMDDTHHMMSSZ.tgz" `
	-ForceRestore
```

If you want a separate personal Windows lab on this Linux Olares host, use:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-windows-lab-remote.ps1 -Action setup
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-windows-lab-remote.ps1 -Action up
```

Then open it with:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-windows-lab-access.ps1 -Action open-web
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-windows-lab-access.ps1 -Action open-rdp
```

Use `-Action status` to see whether the web and RDP local tunnels are currently active.

## Important Limits

Olares Market apps are managed by Olares itself. Installing them does not place
their files into `~/Personal`, but they are still outside the APEX repo unless
you intentionally bring them into governed APEX work.

This Olares host runs Ubuntu Linux and Docker reports `OSType=linux`.

That means native Windows containers are not supported on this host.

If you need Windows on this machine, the supported personal-lab pattern is a
Windows virtual machine running through Docker with KVM acceleration, not a
native Windows container.

## Check Current State

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-zone-remote.ps1 -Action status
```