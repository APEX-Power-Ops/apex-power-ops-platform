# Personal Files Bridge Quickstart

This bridge exposes the existing host-side personal lane at `~/Personal` inside
the Olares Files app through the supported `External -> Connect to server`
Samba flow.

It does not move or replace the Olares-managed Files storage volume. It adds a
separate bridge to the already-created personal lane.

## What It Connects

1. Host-side personal lane: `~/Personal`
2. Olares Files entry point: `External`
3. Protocol: Samba / SMB

## One-Time Setup

Run from the workstation repo root:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-files-samba-bridge-remote.ps1 -Action setup
```

That does the following on the Olares host:

1. installs Samba if it is missing
2. creates a dedicated SMB user for the bridge
3. publishes only `/home/olares/Personal` as share `personal`
4. stores the generated credentials in `~/apex-secrets/personal/samba-personal-files.env`

## Show The Credentials

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-files-samba-bridge-remote.ps1 -Action credentials
```

Expected output includes:

1. `files_url=//127.0.0.1/personal`
2. username
3. password
4. whether direct Windows SMB mapping is supported on the current Olares node

## Rotate The Bridge Password

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-files-samba-bridge-remote.ps1 -Action rotate
```

That regenerates the SMB password, updates the local Unix password for the
bridge user, refreshes the Samba account password, and rewrites the credential
file under `~/apex-secrets/personal/samba-personal-files.env`.

## Sync The Current Password To Windows Vault

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-files-samba-bridge-remote.ps1 -Action vault
```

That writes the current bridge credential into Windows Credential Manager under
the target `APEX-Olares-Personal-Files-SMB`.

## Rotate And Sync To Windows Vault

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-files-samba-bridge-remote.ps1 -Action rotate-vault
```

That rotates the live SMB password on the Olares host and then updates the
Windows Credential Manager entry in one pass.

Important: after a password rotation, any previously saved Files external
server entry may need to be reconnected using the new password.

## Workstation Helper

Use the local helper when you want the current reconnect details placed on the
clipboard and the Files `External` page opened for you:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-files-access.ps1 -Action open
```

To rotate the password, sync it to Windows Credential Manager, copy the new
reconnect details, and open the Files page in one step:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-files-access.ps1 -Action rotate-open
```

To print the current reconnect details without opening the browser:

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-files-access.ps1 -Action status
```

## Connect It In Olares Files

1. Open `Files`
2. Open `External`
3. Click `Connect to server`
4. Enter `files_url` from the credentials command
6. Enter the username and password from the credentials command

After that, the host-side `Personal` lane should appear inside the Files app as
an external server-backed location.

## Windows Boundary

On this Olares host, LAN TCP `445` is already published by the built-in
`files-samba` service. That means direct Windows mapping to the host bridge at
`//<host-ip>/personal` is not a valid endpoint even when the bridge password is
correct.

Use this bridge for:

1. `Files -> External -> Connect to server` with `files_url`
2. making the personal lane appear inside the Olares Files service

Do not treat `alt_url` as the Windows mapping target on an Olares node that
already exposes `files-samba` on port `445`.

## Windows Access After Olares Re-Share

If you want the mounted `personal` folder reachable from Windows Explorer, do
that from inside Olares Files after the external SMB mount is already working:

1. open `Files -> External -> olares`
2. right-click `personal`
3. choose `SMB share`
4. create or assign the Olares Files SMB-share account you want Windows to use

That is a second-stage share created by Olares `files-samba`, not the original
host bridge credential.

Validated working pattern for this workstation run:

1. Windows path: `\\192.168.0.243\personal`
2. username: `Jason_Swenson`

Important: that Windows login is the Olares Files SMB-share account, not the
bridge account `personalshare` used for `//127.0.0.1/personal` inside Olares.

## Check Current Status

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-files-samba-bridge-remote.ps1 -Action status
```

That reports:

1. whether `smbd` is running
2. whether port `445` is listening
3. the active Samba share definition

## Boundary Reminder

This bridge is for the personal lane only.

Do not point it at:

1. APEX repo roots
2. governed APEX runtime state
3. secret stores outside the bounded personal lane