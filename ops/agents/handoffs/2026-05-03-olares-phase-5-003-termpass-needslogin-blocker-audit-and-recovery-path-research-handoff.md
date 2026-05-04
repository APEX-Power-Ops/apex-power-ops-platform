# Olares Phase 5 Packet 003 TermiPass NeedsLogin Blocker Audit And Recovery Path Research Handoff

Date: 2026-05-03
Status: Complete - read-only blocker audit complete; no recovery execution performed
Packet: `ops/agents/packets/draft/2026-05-03-olares-phase-5-003-termpass-needslogin-blocker-audit-and-recovery-path-research.json`
Scope: read-only audit of the workstation-side TermiPass or LarePass `NeedsLogin` blocker and bounded recovery-path research

## Authority

This handoff executes Prompt 5 from:

1. `ops/agents/handoffs/2026-05-03-olares-phase-5-next-task-and-prompt-routing-handoff.md`
2. `ops/agents/packets/draft/2026-05-03-olares-phase-5-003-termpass-needslogin-blocker-audit-and-recovery-path-research.json`

Prior evidence used:

1. `ops/agents/handoffs/2026-05-03-olares-phase-5-002-access-recovery-and-runtime-inventory-handoff.md`
2. `ops/agents/handoffs/2026-05-01-olares-private-stack-browser-terminal-bring-up-handoff.md`
3. `docs/architecture/OLARES-SSH-HOSTKEY-RECONCILIATION-2026-05-01.md`
4. `docs/architecture/OLARES-PRIVATE-STACK-FIRST-RUN-CHECKLIST-2026-05-01.md`

This handoff does not reopen generic Olares implementation.

No installs, service restarts, auth changes, ingress changes, host-runtime mutation, AI-toolchain rollout, or hosting changes were performed.

## Executive Result

The current `NeedsLogin` blocker is most likely a workstation-local LarePass or TermiPass profile-state problem, not a basic network reachability problem to the Olares Headscale key endpoint.

Confirmed:

1. the local TermiPass named pipe is present and responds at `\\.\pipe\ProtectedPrefix\Administrators\TermiPass\tailscaled`
2. the running service is `LarePassService`, service name `LarePass`, started automatically as `LocalSystem`
3. the service path is `C:\Program Files\LarePass\tailscaled.exe -no-logs-no-support`
4. the local API reports `BackendState: NeedsLogin`
5. local API prefs report empty `ControlURL` and `WantRunning: false`
6. local API current profile is empty
7. local API profiles list is empty
8. `server-state.conf` contains a cookie and machine key but no usable profile object
9. the current profile pointer decodes to a profile key whose stored value is null
10. the stored cookie can reach `https://headscale.jlswen2121.olares.com/key?v=68` with `200 OK`
11. the TermiPass adapter is up but only has link-local IPv4 `169.254.149.107`
12. no `100.64.*` route exists
13. SSH to `100.64.0.1:22` remains blocked by missing mesh route, not by SSH host-key trust alone

Conclusion:

The next execution packet should not repeat Packet 002 unchanged. The next bounded execution packet should test an interactive LarePass profile rehydration path or an elevated service-control path that explicitly verifies whether a real profile, non-zero node key, auth URL, and `100.64.*` mesh IP are created.

## Current Read-Only Local State

### TermiPass Local API

Named pipe:

`\\.\pipe\ProtectedPrefix\Administrators\TermiPass\tailscaled`

`GET /localapi/v0/status` returned:

1. `Version: 1.48.1-dev20240429-t9d0d32659-dirty`
2. `TUN: true`
3. `BackendState: NeedsLogin`
4. `AuthURL: ""`
5. `TailscaleIPs: null`
6. `Self.HostName: Jason_Swenson`
7. `Self.PublicKey: nodekey:0000000000000000000000000000000000000000000000000000000000000000`
8. `Self.Online: false`
9. health: `state=NeedsLogin, wantRunning=false`

`GET /localapi/v0/prefs` returned:

1. `ControlURL: ""`
2. `WantRunning: false`
3. `RouteAll: true`
4. `AllowSingleHosts: true`
5. `CorpDNS: true`
6. `RunSSH: false`

`GET /localapi/v0/profiles/current` returned an empty profile:

1. empty `ID`
2. empty `Name`
3. empty `Key`
4. empty `NodeID`
5. empty `ControlURL`

`GET /localapi/v0/profiles/` returned an empty list.

`GET /localapi/v0/derpmap` returned `null`.

### Windows Service And Process State

Observed service:

1. `Name: LarePass`
2. `DisplayName: LarePassService`
3. `State: Running`
4. `StartMode: Auto`
5. `StartName: LocalSystem`
6. `PathName: C:\Program Files\LarePass\tailscaled.exe -no-logs-no-support`

Observed processes:

1. two `tailscaled.exe` processes were visible
2. creation times were 2026-05-02 19:28:05 and 2026-05-02 19:28:07 local
3. process executable path and command line were not readable from the current shell

Interpretation:

The service is alive, but the local API reports no logged-in profile or active node identity.

### Adapter And Route State

Observed adapters:

1. `TermiPass Tunnel` is `Up`
2. ExpressVPN adapters are present but disconnected

Observed TermiPass IP state:

1. IPv4 address: `169.254.149.107`
2. IPv6 link-local: present
3. no IPv4 default gateway
4. no `100.64.*` route

Interpretation:

The tunnel adapter exists, but it is not populated with the expected Olares mesh address. Windows therefore routes `100.64.0.1` attempts over ordinary LAN interfaces instead of the TermiPass mesh.

### Local Client Artifacts

Readable `C:\ProgramData\TermiPass\server-state.conf` contains:

1. a `Cookie` value
2. a `_machinekey` value
3. `_profiles`
4. a current-user profile pointer
5. `profile-ed6e` and `profile-edfe` entries with null values
6. no `server-mode-start-key`

Non-secret structural decoding:

1. current profile pointer decodes to `profile-ed6e`
2. `_profiles` decodes to an empty object
3. the profile entry selected by the current profile pointer is null

Cookie reachability check:

1. the stored cookie is base64 encoded and contains an auth token
2. decoded token metadata shows MFA present
3. a read-only GET to `https://headscale.jlswen2121.olares.com/key?v=68` with the stored cookie returned `200 OK`
4. no token value is recorded in this handoff

Interpretation:

The client has enough server-side web authentication material to reach the Headscale key endpoint, but the local Tailscale profile state consumed by the named-pipe API is empty or tombstoned. That explains why the local API remains in `NeedsLogin` even though the Headscale key endpoint itself is reachable.

### Logs

Readable log inventory exists under:

1. `C:\ProgramData\TermiPass\Logs`
2. `C:\Users\jjswe\AppData\Roaming\LarePass\logs`

Relevant observations:

1. the latest TermiPass service log for 2026-05-03 is zero bytes
2. the previous active TermiPass logs show repeated `open-conn-track` timeouts from `169.254.149.107` to `169.254.169.254:80` with `no associated peer node`
3. the 2026-05-01 logs show repeated authentication attempts and earlier `fetch control key: 400` failures before shutdown/restart cycles
4. the 2026-05-01 and 2026-05-02 logs contain raw auth material, so they should not be quoted into future handoffs or tickets
5. LarePass application log is mostly UI lifecycle and update-check material; it shows prior network errors such as `ERR_NAME_NOT_RESOLVED` and `ERR_NETWORK_CHANGED`, but it does not explain the current profile-null state

Interpretation:

The logs support the same local-state theory: the daemon is alive but has no associated peer node and no usable local profile.

## Comparison To 2026-05-01 Recovered State

### 2026-05-01 Recovered State

Prior documented success in `docs/architecture/OLARES-SSH-HOSTKEY-RECONCILIATION-2026-05-01.md` and `ops/agents/handoffs/2026-05-01-olares-private-stack-browser-terminal-bring-up-handoff.md`:

1. local TermiPass named-pipe API was used
2. `ControlURL` was reseeded as `https://headscale.jlswen2121.olares.com`
3. `WantRunning=true` was set
4. current pending node key was registered in the Olares Headscale pod for user `default`
5. local status moved to `BackendState: Running`
6. workstation mesh IP became `100.64.0.2`
7. peer `olares` appeared online at `100.64.0.1`
8. `Test-NetConnection 100.64.0.1 -Port 22` succeeded
9. non-interactive SSH to `olares@100.64.0.1` succeeded

### Current Blocked State

Current evidence:

1. local API is reachable
2. local API remains `BackendState: NeedsLogin`
3. no non-zero node key exists
4. no auth URL exists
5. no mesh IP exists
6. no peer map exists
7. profile list is empty
8. current profile pointer points to a null profile entry
9. Headscale key endpoint is reachable with the stored cookie
10. no `100.64.*` route exists
11. `100.64.0.1:22` remains unreachable

### Delta

The missing pieces versus 2026-05-01 are:

1. a valid local profile object
2. persistent `ControlURL`
3. persistent `WantRunning=true`
4. generated non-zero node key
5. host-side node registration candidate
6. mesh IP assignment
7. peer map containing `olares`

The critical change is not that the local API disappeared. The critical change is that the local API has no usable profile or node identity to start from.

## Confirmed Blockers

1. Local API state is `NeedsLogin`.
2. Local API reports zero node key.
3. Local API reports no `AuthURL`.
4. Local API reports no mesh IP.
5. Local API profiles list is empty.
6. Current profile pointer resolves to a null profile entry.
7. No `100.64.*` route exists.
8. `100.64.0.1:22` times out.
9. Host-side Headscale registration cannot proceed because no pending node key exists.
10. Host runtime inventory remains blocked because SSH remains unavailable.

## Likely Root-Cause Candidates

### Candidate 1 - Local Profile Store Tombstoned Or Corrupt

Evidence:

1. `_profiles` decodes to an empty object
2. current profile pointer resolves to `profile-ed6e`
3. `profile-ed6e` is null
4. local API profiles list returns `[]`

Likelihood: high.

### Candidate 2 - GUI Session Not Currently Authenticated Into A TermiPass Network Profile

Evidence:

1. no local API current profile
2. no local API auth URL
3. LarePass app last logged close event on 2026-05-03 14:38:39
4. local server-state has a cookie but no profile object

Likelihood: high.

### Candidate 3 - Daemon In-Memory State Is Stale Relative To Server-State File

Evidence:

1. two `tailscaled.exe` processes have been running since 2026-05-02 19:28
2. Packet 002 preference writes were echoed once but did not persist into status
3. current service log for 2026-05-03 is zero bytes

Likelihood: medium.

### Candidate 4 - Headscale Endpoint Or Auth Cookie Is Not The Primary Failure

Evidence:

1. stored cookie can reach `https://headscale.jlswen2121.olares.com/key?v=68` with `200 OK`
2. there is still no profile, node key, or mesh IP

Likelihood: medium-high as a negative finding.

This means endpoint reachability alone is not enough. The client still needs profile rehydration and node identity generation.

### Candidate 5 - Host-Side Registration Is A Secondary Blocker, Not The First Blocker

Evidence:

1. no pending node key exists locally
2. prior successful flow required node-key registration after the node key existed

Likelihood: high.

Host registration remains required later, but it cannot be the immediate next step until a non-zero node key exists.

## Viable Bounded Recovery Methods

### Method A - Interactive LarePass Or TermiPass Profile Rehydration

Purpose:

Use the GUI/web-authenticated LarePass path to recreate a local profile and start the mesh client, then re-run read-only local API status checks.

Prerequisites:

1. operator has local desktop access
2. operator can open LarePass or the Olares desktop profile app
3. operator can complete any MFA or browser-mediated login

Required privilege:

User-interactive local session. No Windows elevation should be required unless the app fails to communicate with the service.

Expected evidence:

1. `GET /localapi/v0/profiles/` no longer returns `[]`
2. `GET /localapi/v0/profiles/current` has non-empty `ID`, `Key`, `NodeID`, or `ControlURL`
3. `GET /localapi/v0/status` moves from zero node key to a real node key or to `Running`
4. `TailscaleIPs` includes `100.64.*`
5. peer `olares` appears at `100.64.0.1`

Risk:

Low to medium. It changes local client auth/session state but does not mutate host runtime, ingress, or service configuration.

Packet suitability:

Yes. This is the recommended next execution packet if the operator can be present for interactive login.

### Method B - Elevated Local Service Restart Followed By Read-Only Status Checks

Purpose:

Clear stale daemon in-memory state and force the service to reload local state.

Prerequisites:

1. local Windows elevation
2. explicit packet authorization to restart `LarePassService`
3. a post-restart read-only local API check

Required privilege:

Administrator.

Expected evidence:

1. service restart succeeds
2. local API remains reachable
3. profile state either rehydrates or remains empty
4. if still empty, this method proves restart alone is insufficient

Risk:

Medium. It mutates local service state but not host runtime. Earlier authority explicitly avoided service restart without privilege and packet authorization.

Packet suitability:

Yes, but only as a separate local-client-recovery packet that explicitly authorizes the restart.

### Method C - Browser-Terminal-Assisted Host Inventory Without Mesh Recovery

Purpose:

Bypass workstation mesh recovery for the inventory task by using authenticated Olares browser terminal access, if available.

Prerequisites:

1. authenticated browser terminal is available
2. operator can run read-only commands on the host
3. command list is pre-bounded to Docker, K3s or Helm, ports, volumes, networks, and private-lane timers

Required privilege:

Authenticated Olares browser session. Host command permissions depend on the terminal user.

Expected evidence:

1. direct host runtime inventory without workstation SSH
2. no change to local mesh state
3. Packet 001 inventory portion can be satisfied even while Remote-SSH remains blocked

Risk:

Low if commands remain read-only. It does not solve daily development access, but it unblocks evidence collection.

Packet suitability:

Yes. This is the recommended next packet if the operator wants runtime truth before fixing Remote-SSH.

### Method D - Headscale Registration After Node Key Appears

Purpose:

Register the workstation pending node key in the Olares Headscale pod for user `default`.

Prerequisites:

1. local API produces a real non-zero node key
2. host-side registration path is available through browser terminal or SSH
3. explicit packet authorizes the registration step

Required privilege:

Host-side access to Headscale pod controls.

Expected evidence:

1. local node key moves from pending to accepted
2. local status moves to `BackendState: Running`
3. `TailscaleIPs` includes `100.64.*`

Risk:

Medium. This changes mesh control-plane state, so it must stay packetized.

Packet suitability:

Not as the immediate next standalone packet because no node key currently exists. It is a second-stage action inside Method A or Method B if those produce a pending node key.

### Method E - Local Profile Store Reset Or Repair

Purpose:

Remove or repair tombstoned profile entries so the client can recreate a profile.

Prerequisites:

1. exact vendor-supported or operator-approved reset path
2. local backup of current client state
3. explicit packet authorization

Required privilege:

Likely local elevation or at least user-level file access, depending on target.

Expected evidence:

1. profile store rebuilt
2. current profile no longer points at null
3. GUI or local API can start login flow

Risk:

Medium-high. It mutates local client state and may destroy useful forensic context or require re-auth.

Packet suitability:

Not recommended as the next packet. Use only after Method A and Method B are blocked or explicitly rejected.

## Methods Not Currently Viable

### Repeating Packet 002 Unchanged

Not viable because:

1. it already showed that local API preference writes do not persist into active status
2. no auth URL or node key was produced
3. the local profile store remains empty

### Host-Side Registration First

Not viable because:

1. no local node key exists
2. there is nothing to register

### Public FRP SSH Trust Reconciliation

Not viable because:

1. the public hostname is already documented as an FRP relay with a distinct key
2. public-host SSH has separate publickey auth behavior
3. the trusted path remains private mesh or browser-terminal fallback

### Olares Expansion Or Migration

Not viable because:

1. no host runtime inventory was captured
2. VS Code Remote-SSH remains blocked
3. daily-development migration evidence is still missing

## Official Olares Source Cross-Check

After the local read-only audit, the upstream `beclab/Olares` repository and
official Olares documentation were checked as source context for the recovery
recommendation.

Relevant source findings:

1. the upstream `beclab/Olares` README identifies `apps` as the system-app code
   area, primarily for `larepass`
2. the same README describes Olares networking as using Tailscale, Headscale,
   Cloudflare Tunnel, and FRP
3. the official LarePass documentation describes LarePass as the cross-platform
   client for Olares, including device and network management
4. the official LarePass VPN documentation says LarePass VPN uses Tailscale for
   private access, and that if VPN is disabled traffic routes through public
   internet tunnels such as Cloudflare or FRP
5. upstream source paths include Settings VPN and Headscale device surfaces:
   - `apps/packages/app/src/stores/settings/headscale.ts`
   - `apps/packages/app/src/pages/settings/Vpn/VPNPage.vue`
   - `apps/packages/app/src/pages/settings/Vpn/HeadScaleDeviceCard.vue`
   - `cli/cmd/ctl/settings/vpn/devices.go`
   - `cli/cmd/ctl/settings/vpn/ssh.go`

Interpretation:

1. the packet's local finding remains valid: the immediate blocker is local
   LarePass or TermiPass profile state, because the daemon has no current
   profile, node key, mesh IP, or DERP map
2. the upstream source reinforces that the correct private path is LarePass VPN
   over Tailscale/Headscale, not the public FRP hostname
3. host-side Headscale device visibility and SSH-over-VPN state are separate
   configuration evidence surfaces; they become useful only after the local
   client produces a real device identity or after browser-terminal host access
   is available
4. the next packet should explicitly capture three configuration surfaces:
   local LarePass profile state, Headscale device list/status, and
   SSH-over-VPN allowance

## Recommended Next Packet

Open one of two bounded execution packets, depending on operator availability.

### Preferred Next Packet: Interactive Local LarePass Profile Rehydration

Use this when the operator can interact with the Windows desktop and complete LarePass or Olares MFA.

Exact method to test:

1. open LarePass or the relevant Olares desktop profile app interactively
2. confirm account/session state through the UI
3. use the LarePass VPN or network-management UI to start or enable the private
   mesh
4. confirm whether this workstation appears as a Headscale device, if the UI
   exposes that status
5. confirm whether Olares Settings still reports SSH-over-VPN as allowed or
   applied, if the UI exposes that status
6. then run read-only checks:
   - local API `status`
   - local API `prefs`
   - local API `profiles/current`
   - local API `profiles/`
   - adapter IP state
   - `100.64.*` route table
   - `Test-NetConnection 100.64.0.1 -Port 22`
   - non-interactive SSH using a temporary `UserKnownHostsFile`
7. if a pending real node key appears but the node is not accepted, perform the
   already-documented Headscale registration step only if explicitly authorized
   in that same packet

Why this is preferred:

The confirmed blocker is empty or null local profile state. The GUI-auth path is the least invasive way to recreate profile state.

### Alternate Next Packet: Browser-Terminal-Assisted Host Runtime Inventory

Use this when the priority is host runtime truth rather than Remote-SSH recovery.

Exact method to test:

1. open authenticated Olares browser terminal
2. run only pre-approved read-only inventory commands
3. capture Docker, K3s or Helm, installed apps, ports, volumes, networks, and private-lane timer evidence
4. record that Remote-SSH remains blocked separately

Why this is useful:

It can satisfy the missing inventory portion of Packet 001 without depending on the broken workstation mesh.

## Roadmap Update Decision

No roadmap update was made.

Reason:

1. this packet is research-only
2. it does not restore access
3. it does not capture host runtime inventory
4. it does not materially change the live Olares boundary
5. no Phase 5 task can close from this result

## Packet Disposition

Packet `2026-05-03-olares-phase-5-003` closes as `complete - research only`.

It produces a bounded recommendation for the next execution packet but does not authorize execution by itself.

## Final Recommendation

A new execution packet is justified, but it should be narrower than Packet 002.

Recommended title:

`Olares Phase 5 004 - Interactive LarePass Profile Rehydration And Mesh Validation`

Recommended objective:

Use an operator-mediated LarePass or Olares UI login/start path to recreate the
missing local profile state, then validate whether the workstation receives a
real node key, `100.64.*` mesh IP, peer `olares`, and working SSH to
`100.64.0.1`.

Recommended config evidence to capture in that packet:

1. local LarePass profile and VPN status
2. local TermiPass named-pipe `status`, `prefs`, and `profiles`
3. Headscale device list/status showing this workstation or its pending node
4. SSH-over-VPN setting status
5. private route and SSH reachability to `100.64.0.1`

Fallback packet if operator interaction is not available:

`Olares Phase 5 004B - Browser Terminal Host Runtime Inventory`

Recommended objective:

Use authenticated Olares browser terminal only for read-only host runtime inventory so the platform can recover host truth while workstation Remote-SSH remains blocked.
