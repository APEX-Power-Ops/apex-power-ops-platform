# Olares Phase 5 Packet 004 Interactive LarePass Profile Rehydration And Mesh Validation Handoff

Date: 2026-05-03
Status: Complete - interactive profile rehydration succeeded and private-mesh SSH is restored
Packet: `ops/agents/packets/draft/2026-05-03-olares-phase-5-004-interactive-larepass-profile-rehydration-and-mesh-validation.json`
Scope: operator-mediated local LarePass profile rehydration and private-mesh validation only

## Authority

This handoff executes the preferred next packet named in:

1. `ops/agents/handoffs/2026-05-03-olares-phase-5-next-task-and-prompt-routing-handoff.md`
2. `ops/agents/packets/draft/2026-05-03-olares-phase-5-004-interactive-larepass-profile-rehydration-and-mesh-validation.json`
3. `ops/agents/handoffs/2026-05-03-olares-phase-5-003-termpass-needslogin-blocker-audit-and-recovery-path-research-handoff.md`

No installs, service restarts, service reconfiguration, ingress changes, hosting changes, AI-toolchain rollout, or host-runtime mutation were performed.

## Executive Result

Packet 004 succeeded.

The workstation-local LarePass or TermiPass profile state rehydrated after the LarePass desktop UI was surfaced for the operator-mediated step. After that action:

1. TermiPass local API moved from `BackendState: NeedsLogin` to `BackendState: Running`.
2. workstation mesh IP changed from link-local only to `100.64.0.2`.
3. current profile became `default` with profile key `profile-63a9`, node ID `2`, and `ControlURL=https://headscale.jlswen2121.olares.com`.
4. Headscale showed workstation device `Jason_Swenson` / `jason-swenson` online as node ID `2`, user `default`, IP `100.64.0.2`.
5. peer `olares` appeared online at `100.64.0.1`.
6. `Test-NetConnection 100.64.0.1 -Port 22` succeeded from source `100.64.0.2` over interface `TermiPass`.
7. non-interactive SSH to `olares@100.64.0.1` succeeded using a temporary `UserKnownHostsFile`.
8. configured SSH alias `olares-mesh` succeeded.
9. configured SSH alias `olares` also succeeded while VPN DNS resolved `jlswen2121.olares.com` to `100.64.0.1`.

Conclusion:

The private-mesh access blocker identified by Packets 001, 002, and 003 is resolved for the current workstation session. This restores the trusted operator path enough to open a narrow follow-on host runtime inventory packet. It does not by itself prove Olares-first daily development readiness, host clone authority, services-zone completeness, or canonical hosting readiness.

## Pre-Rehydration Evidence

Before surfacing LarePass for the interactive step, the workstation remained in the blocked state documented by Packet 003:

1. `LarePass.exe` was already running from `C:\Program Files\LarePass\LarePass.exe`.
2. `LarePassService` was running and automatic.
3. `TermiPass Tunnel` was up but only had IPv4 `169.254.149.107/16`.
4. no `100.64.*` route was present.
5. local API `GET /localapi/v0/status` returned:
   - `BackendState: NeedsLogin`
   - `AuthURL: ""`
   - `TailscaleIPs: null`
   - zero node key
   - health `state=NeedsLogin, wantRunning=false`
6. local API `GET /localapi/v0/prefs` returned:
   - `ControlURL: ""`
   - `WantRunning: false`
   - `RunSSH: false`
7. local API `GET /localapi/v0/profiles/current` returned an empty profile.
8. local API `GET /localapi/v0/profiles/` returned no usable profile.
9. `Test-NetConnection 100.64.0.1 -Port 22` failed and routed over `Ethernet 8` from `192.168.0.177`.
10. non-interactive SSH to `olares@100.64.0.1` timed out.

Interpretation:

The preflight still matched Packet 003's root-cause classification: local profile state was absent or tombstoned, and no host-side registration step was possible because no real pending node key existed.

## Interactive Recovery Action

Action performed:

1. surfaced the already-installed LarePass desktop app with `Start-Process -FilePath 'C:\Program Files\LarePass\LarePass.exe'`
2. waited for the operator-mediated UI step
3. re-ran the same local API, adapter, route, TCP, and SSH validation checks

No LarePass service restart was performed.

No local client reset was performed.

No Headscale registration command was performed.

No host runtime service was started, stopped, restarted, or reconfigured.

## Post-Rehydration Local API Evidence

`GET /localapi/v0/status` returned:

1. `BackendState: Running`
2. `AuthURL: ""`
3. `TailscaleIPs: ["100.64.0.2"]`
4. `Self.ID: "2"`
5. `Self.HostName: Jason_Swenson`
6. `Self.DNSName: jason-swenson.default.example.com`
7. `Self.UserID: 1`
8. `Self.Online: true`
9. non-zero node key present; full key intentionally not recorded
10. `CurrentTailnet.Name: example.com`
11. `MagicDNSSuffix: default.example.com`
12. peer `olares` present with:
    - `ID: "1"`
    - `HostName: olares`
    - `DNSName: olares.default.example.com`
    - `OS: linux`
    - `TailscaleIPs: ["100.64.0.1"]`
    - `Online: true`
    - `Active: true`
13. peer `localhost` present with:
    - `ID: "3"`
    - `TailscaleIPs: ["100.64.0.3"]`
    - `Online: false`

`GET /localapi/v0/prefs` returned:

1. `ControlURL: https://headscale.jlswen2121.olares.com`
2. `WantRunning: true`
3. `RunSSH: false`
4. `ShieldsUp: true`
5. `ForceDaemon: true`
6. `Config.UserProfile.LoginName: default`
7. `Config.UserProfile.DisplayName: default@example.com`
8. `Config.NodeID: "2"`

`GET /localapi/v0/profiles/current` returned:

1. `ID: "63a9"`
2. `Name: default`
3. `Key: profile-63a9`
4. `NodeID: "2"`
5. `LocalUserID: S-1-5-21-1217271336-3335801616-693790071-1001`
6. `ControlURL: https://headscale.jlswen2121.olares.com`

`GET /localapi/v0/profiles/` returned the same `default` profile.

`GET /localapi/v0/derpmap` returned a populated DERP map rather than `null`.

## Adapter Route And SSH Evidence

Post-rehydration Windows adapter evidence:

1. `TermiPass` adapter status: `Up`
2. IPv4 address: `100.64.0.2/32`
3. IPv6 link-local still present

Post-rehydration route evidence includes:

1. `100.64.0.1/32` via `TermiPass`
2. `100.64.0.2/32` via `TermiPass`
3. `100.64.0.3/32` via `TermiPass`
4. `100.100.100.100/32` via `TermiPass`
5. `10.233.0.3/32` via `TermiPass`
6. `192.168.0.0/23` via `TermiPass`

`Test-NetConnection 100.64.0.1 -Port 22` returned:

1. `RemoteAddress: 100.64.0.1`
2. `RemotePort: 22`
3. `InterfaceAlias: TermiPass`
4. `SourceAddress: 100.64.0.2`
5. `TcpTestSucceeded: True`

Non-interactive SSH results:

1. `ssh olares@100.64.0.1 'echo olares-ssh-ok'` returned `olares-ssh-ok`
2. configured alias `olares-mesh` returned `olares-mesh-alias-ok`
3. configured alias `olares` returned `olares-public-alias-ok` after VPN DNS resolved `jlswen2121.olares.com` to `100.64.0.1`

The host's ED25519 key fingerprint read over the restored mesh path is:

`SHA256:Bv4YFhnvW3xYcl+PcES/qiG1iCVYKAdxyb7bFv1I9IU`

This matches the trusted host fingerprint previously recorded in `docs/architecture/OLARES-SSH-HOSTKEY-RECONCILIATION-2026-05-01.md`.

## Headscale Device Evidence

Host-side Kubernetes showed the Headscale workload:

1. namespace `user-space-jlswen2121`
2. pod `headscale-7697d59cf8-htdfs`
3. containers `headscale` and `headscale-api-wrapper`
4. pod status `2/2 Running`
5. services:
   - `headscale-authkey-svc`
   - `headscale-server-svc`
   - `headscale-svc`
   - `headscale` in `user-system-jlswen2121`

Read-only `headscale nodes list` inside the `headscale` container showed:

1. node ID `1`, hostname `olares`, user `default`, IP `100.64.0.1`, online `yes`
2. node ID `2`, hostname `Jason_Swenson`, name `jason-swenson`, user `default`, IP `100.64.0.2`, online `yes`
3. node ID `3`, hostname `localhost`, user `default`, IP `100.64.0.3`, online `no`

Interpretation:

The workstation is now visible as an accepted Headscale device. No pending node-key registration was needed during Packet 004 because the profile rehydration recovered an existing accepted node identity.

## SSH-Over-VPN Status

Current functional status:

1. SSH over the mesh is working.
2. TCP/22 to `100.64.0.1` succeeds over `TermiPass`.
3. OpenSSH login to `olares@100.64.0.1` succeeds.

Current UI/API status:

1. the installed host `olares-cli` does not currently include `olares-cli settings vpn ssh`
2. upstream Olares source context says the newer settings command reads `GET /api/acl/ssh/status`
3. unauthenticated in-cluster probes to `/api/acl/ssh/status` returned `401 Unauthorized` or user-header errors, so the Settings UI ACL value was not directly captured in this packet
4. `docs/architecture/OLARES-SSH-HOSTKEY-RECONCILIATION-2026-05-01.md` previously recorded the authenticated Settings surface as `Allow SSH via VPN` enabled and applied

Interpretation:

The SSH-over-VPN setting is functionally effective now, but the current authenticated Settings UI status remains an evidence gap. This should not block the next host-runtime inventory packet, but it should be captured later through the authenticated Settings UI or a supported CLI/API path.

## DNS And Public Host Boundary

After the private mesh was restored, `Resolve-DnsName jlswen2121.olares.com` returned:

1. `Type: A`
2. `IPAddress: 100.64.0.1`

This differs from earlier Packet 001 evidence where the same name resolved through the public FRP relay path.

Interpretation:

The configured `Host olares` alias now succeeds because private VPN DNS maps the hostname to the mesh address while the VPN is active. Do not treat this as proof that the public FRP SSH boundary has been reconciled. The controlling trusted path remains `olares-mesh` or direct mesh SSH to `olares@100.64.0.1`.

## Host Reachability Evidence

Read-only SSH host identity probes returned:

1. `hostname`: `olares`
2. `whoami`: `olares`
3. host date: `2026-05-03T23:41:34+00:00`
4. kernel: `Linux olares 6.14.0-35-generic #35~24.04.1-Ubuntu`
5. host tools present:
   - `/usr/local/bin/olares-cli`
   - `/usr/local/bin/kubectl`
   - `/usr/local/bin/helm`

Limited Kubernetes observations during Packet 004 also showed `forms-engine` and `p6-ingest` pods present and running in `user-space-jlswen2121`, but Packet 004 did not perform a full host runtime inventory. Those observations are incidental and should not be treated as satisfying Packet 001 inventory.

## VS Code Remote-SSH Assessment

Current SSH config contains:

1. `Host olares` -> `HostName jlswen2121.olares.com`
2. `Host olares-mesh` -> `HostName 100.64.0.1`
3. both use user `olares` and the workstation private key

Current viability:

1. `olares-mesh` is viable now because direct non-interactive SSH succeeds.
2. `olares` also succeeds while VPN DNS resolves the hostname to `100.64.0.1`.
3. prefer `olares-mesh` for VS Code Remote-SSH validation because it makes the trusted mesh dependency explicit and avoids ambiguity with public relay behavior.

This restores enough access to test VS Code Remote-SSH in a narrow follow-on validation. It does not prove that Olares is stable enough to become the daily APEX development center of gravity.

## Packet 001 Inventory Status

Packet 004 restores the access prerequisite that Packet 001 lacked.

Packet 004 does not satisfy the Packet 001 runtime-inventory portion because it did not perform the full read-only Docker, K3s or Helm, installed-app, ports, volumes, networks, and private-lane timer inventory.

The correct next move is a narrow SSH-based host runtime inventory packet. Packet 004B is no longer the preferred immediate fallback while mesh SSH remains healthy; keep 004B reserved for browser-terminal inventory if mesh access regresses again or if authenticated browser terminal becomes the chosen proof path.

## Roadmap Update Decision

A roadmap update is justified because the live Olares boundary materially changed:

1. private-mesh access changed from blocked to restored
2. VS Code Remote-SSH changed from blocked to technically viable for `olares-mesh`
3. the host runtime inventory can now be reopened through SSH rather than browser terminal

No Phase 5 task should close solely from Packet 004:

1. `TASK-021` still needs repo-publication and host-clone reconciliation evidence
2. `TASK-023` still needs full host runtime inventory and written Restic posture reconciliation
3. `TASK-025` still needs per-path readiness synthesis after host inventory and repo-authority checks

## Packet Disposition

Packet `2026-05-03-olares-phase-5-004` closes as `complete - pass`.

The private-mesh access path is restored.

Headscale registration was not performed because no pending node was required.

Host runtime inventory remains unsatisfied and should be opened as a separate bounded packet.

## Final Recommendation

Open a narrow next packet for SSH-based read-only host runtime inventory while the restored mesh path is live.

Recommended packet:

`Olares Phase 5 005 - SSH-Based Host Runtime Inventory`

Recommended objective:

Use the restored `olares-mesh` SSH path to capture the host runtime inventory that Packet 001 could not obtain, covering Docker, K3s or Helm, installed apps, ports, volumes, networks, private-lane timers, and enough repo-host clone evidence to support later TASK-021 and TASK-023 reconciliation.

No-go items remain:

1. no generic Olares reopening
2. no installs
3. no ingress changes
4. no auth changes
5. no service restarts
6. no AI-toolchain rollout
7. no Gitea or canonical-hosting cutover
8. no claim that restored SSH alone makes Olares-first daily development ready
