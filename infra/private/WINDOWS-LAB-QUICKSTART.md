# Windows Lab Quickstart

This is a personal Windows lab for the Olares workstation.

Important: this is not a native Windows container.

It is a Windows virtual machine running through Docker on the Linux host using
KVM acceleration.

## Why This Is Safe

1. it stays outside the APEX repo and governed APEX app surfaces
2. it uses a separate personal compose lane
3. it stores the Windows disk inside a dedicated Docker volume on the host
4. it exposes the viewer and RDP only on host-local ports by default

## One-Time Setup

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-windows-lab-remote.ps1 -Action setup
```

## Start The Windows Lab

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-windows-lab-remote.ps1 -Action up
```

First boot takes a while because it downloads and installs Windows.

## Check Progress

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-windows-lab-remote.ps1 -Action status
```

## Open The Web Viewer

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-windows-lab-access.ps1 -Action open-web
```

That opens a local browser view at `http://127.0.0.1:8007` through a safe SSH tunnel.

## Open RDP

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-windows-lab-access.ps1 -Action open-rdp
```

That opens Microsoft Remote Desktop against the safe local tunnel target `127.0.0.1:3391`.

## Check Local Access Tunnels

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-windows-lab-access.ps1 -Action status
```

The helper reports web and RDP tunnel state separately.

## Close Local Access Tunnels

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-windows-lab-access.ps1 -Action close-web
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-windows-lab-access.ps1 -Action close-rdp
```

## Show The Windows Login

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-windows-lab-remote.ps1 -Action credentials
```

## Stop The Lab

```powershell
pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\run-personal-windows-lab-remote.ps1 -Action down
```

## What It Uses

1. Windows version: `10l` by default, which is Windows 10 LTSC
2. Storage: Docker volume `personal_windows_storage`
3. Shared host folder inside Windows: `~/Personal/Downloads`
4. Host-local web viewer port: `8006`
5. Host-local RDP port: `3390`
6. Workstation local web tunnel port: `8007`
7. Workstation local RDP tunnel port: `3391`

## Important Limits

1. this does not repartition the host disk
2. this does not create a public route
3. this does not change any APEX runtime surface
4. if you later want a bigger Windows disk, that can be changed safely in the env file before you rely on it heavily
