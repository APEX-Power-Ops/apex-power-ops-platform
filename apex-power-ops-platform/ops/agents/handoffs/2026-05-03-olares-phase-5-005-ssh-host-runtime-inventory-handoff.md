# Olares Phase 5 Packet 005 SSH Host Runtime Inventory Handoff

Date: 2026-05-03
Status: Complete - read-only host runtime inventory captured over restored mesh SSH
Packet: `ops/agents/packets/draft/2026-05-03-olares-phase-5-005-ssh-host-runtime-inventory.json`
Scope: read-only Olares host identity, runtime, app, timer, and repo-clone evidence over `olares-mesh`

## Authority

This handoff executes the next live packet named in:

1. `ops/agents/handoffs/2026-05-03-olares-phase-5-next-task-and-prompt-routing-handoff.md`
2. `ops/agents/packets/draft/2026-05-03-olares-phase-5-005-ssh-host-runtime-inventory.json`
3. `ops/agents/handoffs/2026-05-03-olares-phase-5-004-interactive-larepass-profile-rehydration-and-mesh-validation-handoff.md`
4. `docs/architecture/OLARES-SSH-HOSTKEY-RECONCILIATION-2026-05-01.md`
5. `docs/architecture/SERVICE-HOST-INSTALLED-PROOF-CHECKLIST-2026-04-23.md`
6. `docs/architecture/OLARES-FIRST-STORAGE-BRING-UP-RUNBOOK-2026-04-23.md`

No installs, promotions, ingress changes, auth changes, service restarts, Helm or Kubernetes mutations, git mutations on the host, hosting changes, or Olares-first migration actions were performed.

Docker MCP discovery did not expose Docker runtime inspection tools in this Codex session. The `MCP_DOCKER` namespace exposed only a browser network helper. Docker evidence below was therefore captured by read-only SSH commands on the Olares host.

## Executive Result

Packet 005 succeeded as a read-only inventory pass.

The trusted mesh SSH path remained healthy, the host fingerprint matched the already recorded trusted ED25519 fingerprint, and host runtime was directly inspected.

Controlling result:

1. Packet 001's host-runtime inventory gap is now satisfied for this assessment lane.
2. VS Code Remote-SSH is technically viable through the explicit `olares-mesh` alias because non-interactive SSH over `100.64.0.1` succeeds.
3. This does not make Olares-first daily development ready.
4. The host repo clone is materially divergent from the current workstation publication boundary and remains non-canonical for daily development.
5. A Claude Code reconciliation prompt is warranted to fold the new evidence into TASK-021, TASK-023, and TASK-025 without collapsing the four decision surfaces.

Packet disposition: `complete - pass`.

## Mesh SSH And Trust Evidence

Observed from the workstation:

1. `Test-NetConnection 100.64.0.1 -Port 22` returned:
   - `TcpTestSucceeded: True`
   - `InterfaceAlias: TermiPass`
   - `SourceAddress: 100.64.0.2`
   - `RemoteAddress: 100.64.0.1`
2. `ssh olares-mesh 'printf "%s\n" olares-mesh-ssh-ok'` returned `olares-mesh-ssh-ok`.
3. `ssh olares@100.64.0.1 'printf "%s\n" direct-mesh-ssh-ok'` returned `direct-mesh-ssh-ok`.
4. Host-side ED25519 fingerprint read over the restored mesh path:
   - `SHA256:Bv4YFhnvW3xYcl+PcES/qiG1iCVYKAdxyb7bFv1I9IU`
5. This matches the trusted fingerprint recorded in `docs/architecture/OLARES-SSH-HOSTKEY-RECONCILIATION-2026-05-01.md`.

Boundary note:

The controlling trust proof remains the private mesh path to `100.64.0.1`. This packet does not reconcile or promote the public relay hostname path.

## Host Identity And Tool Evidence

Observed over `olares-mesh`:

| Surface | Evidence |
| --- | --- |
| hostname | `olares` |
| user | `olares` |
| host time | `2026-05-04T00:54:49+00:00` |
| kernel | `Linux olares 6.14.0-35-generic #35~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue Oct 14 13:55:17 UTC 2 x86_64` |
| Docker | `/usr/bin/docker`, client/server `29.1.3` |
| kubectl | `/usr/local/bin/kubectl`, client `v1.33.3+k3s1` |
| Helm | `/usr/local/bin/helm`, `v3.9.0+g7ceeda6` |
| Olares CLI | `/usr/local/bin/olares-cli` |
| git | `/usr/bin/git` |
| systemctl | `/usr/bin/systemctl` |
| ss | `/usr/bin/ss` |

`olares-cli --help` identified the binary as `Olares Installer` with commands including `backups`, `info`, `logs`, `node`, `start`, `stop`, and `upgrade`. This host binary still does not evidence the newer upstream `settings vpn` commands.

## Docker Runtime Evidence

Observed directly on the Olares host:

| Compose project | Container | Image | Status | Exposed host ports |
| --- | --- | --- | --- | --- |
| `windows-lab` | `personal-windows-lab` | `dockurr/windows` | `Up 24 minutes` | `127.0.0.1:8006->8006/tcp`, `127.0.0.1:3390->3389/tcp`, `127.0.0.1:3390->3389/udp` |
| `private` | `private-personal-notes-1` | `ghcr.io/usememos/memos:0.24.3` | `Up 2 days` | `127.0.0.1:5230->5230/tcp` |
| `apex-dev` | `apex-dev-apex-forms-1` | `apex-dev-apex-forms` | `Up 8 days (healthy)` | `127.0.0.1:8714->8714/tcp` |
| `apex-dev` | `apex-dev-apex-db-1` | `apex-dev-apex-db` | `Up 8 days (healthy)` | `127.0.0.1:8711->8711/tcp` |
| `apex-dev` | `apex-dev-apex-p6-1` | `apex-dev-apex-p6` | `Up 8 days (healthy)` | `127.0.0.1:8713->8713/tcp` |
| `apex-dev` | `apex-dev-postgres-1` | `postgres:16-alpine` | `Up 8 days (healthy)` | `127.0.0.1:55432->5432/tcp` |
| `apex-dev` | `apex-dev-apex-fs-1` | `apex-dev-apex-fs` | `Up 8 days (healthy)` | `127.0.0.1:8710->8710/tcp` |
| `apex-dev` | `apex-dev-apex-jobs-1` | `apex-dev-apex-jobs` | `Up 8 days (healthy)` | `127.0.0.1:8712->8712/tcp` |
| `apex-dev` | `apex-dev-p6-ingest-1` | `apex-dev-p6-ingest` | `Up 8 days (healthy)` | `127.0.0.1:8081->8080/tcp` |
| `apex-dev` | `apex-dev-forms-engine-1` | `apex-dev-forms-engine` | `Up 8 days (healthy)` | `127.0.0.1:8080->8080/tcp` |

Docker networks:

1. `apex-dev` bridge
2. `private_default` bridge
3. `windows-lab_default` bridge
4. default `bridge`
5. `host`
6. `none`

Docker volumes:

1. `apex-dev_apex-dev-data`
2. `apex-dev_apex-dev-forms-templates`
3. `apex-dev_apex-dev-p6-ingest-artifacts`
4. `apex-dev_apex-dev-postgres`
5. `personal_windows_storage`

Selected mounts and roles:

1. `private-personal-notes-1` bind-mounts `/home/olares/apex-data/personal/memos` to `/var/opt/memos`.
2. `apex-dev-p6-ingest-1` mounts `apex-dev_apex-dev-p6-ingest-artifacts` to `/var/lib/p6-ingest/artifacts`.
3. `apex-dev-forms-engine-1` mounts `apex-dev_apex-dev-forms-templates` to `/var/lib/forms-engine/templates`.
4. `personal-windows-lab` mounts `personal_windows_storage` and bind-mounts `/home/olares/Personal/Downloads` to `/shared`.

Classification:

1. `apex-dev` is real on the Olares host and maps to a host-local dev/private-lane surface, not merely workstation-local Docker.
2. `private-personal-notes-1` is real and remains host-only or mesh-tunneled via loopback.
3. `personal-windows-lab` is real but appears operator/personal-lab scoped, not governed as an APEX dev-zone center of gravity.
4. All observed Docker app ports are loopback-bound except host SSH and Olares/K3s ports observed separately.

## K3s, Helm, And Olares App Evidence

K3s node evidence:

1. node `olares`
2. status `Ready`
3. roles `control-plane,master,worker`
4. age `9d`
5. Kubernetes `v1.33.3+k3s1`
6. internal IP `192.168.0.243`
7. OS `Ubuntu 24.04.3 LTS`
8. container runtime `containerd://2.1.3`

Namespaces observed:

1. Olares/system namespaces: `os-framework`, `os-platform`, `os-protected`, `os-network`, `os-gpu`, `user-space-jlswen2121`, `user-system-jlswen2121`
2. Kubernetes/platform namespaces: `kube-system`, `kubesphere-system`, `kubesphere-controls-system`, `kubesphere-monitoring-system`
3. user app namespaces: `chromium-jlswen2121`, `firefox-jlswen2121`, `jdownloader2-jlswen2121`, `qbittorrent-jlswen2121`, `windows-jlswen2121`

Installed/running Olares applications from `applications.app.bytetrade.io`:

| Application CR | App | Namespace | State |
| --- | --- | --- | --- |
| `chromium-jlswen2121-chromium` | `chromium` | `chromium-jlswen2121` | `running` |
| `firefox-jlswen2121-firefox` | `firefox` | `firefox-jlswen2121` | `running` |
| `jdownloader2-jlswen2121-jdownloader2` | `jdownloader2` | `jdownloader2-jlswen2121` | `running` |
| `qbittorrent-jlswen2121-qbittorrent` | `qbittorrent` | `qbittorrent-jlswen2121` | `running` |
| `user-space-jlswen2121-forms-engine` | `forms-engine` | `user-space-jlswen2121` | `running` |
| `user-space-jlswen2121-olares-app` | `olares-app` | `user-space-jlswen2121` | `running` |
| `user-space-jlswen2121-p6-ingest` | `p6-ingest` | `user-space-jlswen2121` | `running` |
| `windows-jlswen2121-windows` | `windows` | `windows-jlswen2121` | `running` |

Helm releases captured with `/etc/rancher/k3s/k3s.yaml`:

1. `forms-engine` in `user-space-jlswen2121`, revision `5`, status `deployed`, chart `forms-engine-0.1.0`, app version `0.1.0`
2. `p6-ingest` in `user-space-jlswen2121`, revision `2`, status `deployed`, chart `p6-ingest-0.1.0`, app version `0.1.0`
3. user-facing releases also present for `chromium`, `firefox`, `jdownloader2`, `qbittorrent`, and `windows`
4. Olares/system releases present for `auth`, `headscale`, `infisical`, `launcher-jlswen2121`, `os-framework`, `os-platform`, `settings`, `systemserver`, `tapr`, and related platform components

The first `helm list -A` call without an explicit kubeconfig returned `Error: Kubernetes cluster unreachable: the server could not find the requested resource`. The same read-only Helm inventory succeeded with `--kubeconfig /etc/rancher/k3s/k3s.yaml`.

Storage evidence:

1. PVs are bound for `citus`, `kvrocks`, `nats`, `prometheus`, Olares user app cache, DB data, user template, charts, and userspace.
2. PVCs are bound in `kubesphere-monitoring-system`, `os-framework`, `os-platform`, and `user-space-jlswen2121`.

## Forms Engine And P6 Ingest Evidence

`forms-engine`:

1. Kubernetes deployment `deployment.apps/forms-engine` in `user-space-jlswen2121`
2. `READY 1/1`, `AVAILABLE 1`, age `8d`
3. image `ghcr.io/jasonlswenson-sys/forms-engine:hostproof-20260425`
4. pod `forms-engine-645657d7c4-444kw`, `READY 1/1`, `STATUS Running`, `RESTARTS 0`
5. service `forms-engine`, `ClusterIP 10.233.16.94`, port `8080/TCP`
6. Olares Application CR `user-space-jlswen2121-forms-engine` is `running`
7. AppImage CR `forms-engine` reports `failed`

`p6-ingest`:

1. Kubernetes deployment `deployment.apps/p6-ingest` in `user-space-jlswen2121`
2. `READY 1/1`, `AVAILABLE 1`, age `8d`
3. image `ghcr.io/jasonlswenson-sys/p6-ingest:hostproof-20260425`
4. pod `p6-ingest-554bcf7844-znfvh`, `READY 1/1`, `STATUS Running`, `RESTARTS 0`
5. service `p6-ingest`, `ClusterIP 10.233.48.137`, port `8080/TCP`
6. Olares Application CR `user-space-jlswen2121-p6-ingest` is `running`
7. AppImage CR `p6-ingest` reports `failed`

Interpretation:

The runtime installed-app state for `forms-engine` and `p6-ingest` is real and live in Kubernetes/Helm, but the AppImage CR state is divergent. Treat this as live-but-needing-governance-reconciliation rather than as failed runtime.

## Ports And Network Evidence

Observed host listeners:

1. `0.0.0.0:22` and `[::]:22` for SSH
2. `0.0.0.0:80` and `0.0.0.0:443` for host web entrypoints
3. `*:6443` for Kubernetes API
4. loopback-only Docker/private services:
   - `127.0.0.1:3390`
   - `127.0.0.1:5230`
   - `127.0.0.1:8006`
   - `127.0.0.1:8080`
   - `127.0.0.1:8081`
   - `127.0.0.1:8710`
   - `127.0.0.1:8711`
   - `127.0.0.1:8712`
   - `127.0.0.1:8713`
   - `127.0.0.1:8714`

Observed host interfaces include:

1. `enp129s0` with LAN IP `192.168.0.243/24`
2. `tailscale0` with mesh IP `100.64.0.1/32`
3. Kubernetes/IPVS and Calico interfaces for `10.233.*`
4. Docker bridges `br-0776e1f105db`, `br-555e78222cd0`, and `br-dc62e8250dae`

Boundary classification:

The observed private-lane and dev containers are host-local loopback services. The observed Kubernetes services are cluster-internal unless separately exposed through Olares app routing. This packet does not prove public ingress readiness for any APEX service.

## Private-Lane Backup And Restore-Drill Evidence

Observed systemd timers:

1. `apex-personal-notes-offsite-backup.timer`
   - loaded from `/etc/systemd/system/apex-personal-notes-offsite-backup.timer`
   - `enabled`
   - `active (waiting)`
   - next trigger `2026-05-04 03:47:37 UTC`
   - triggers `apex-personal-notes-offsite-backup.service`
2. `apex-personal-notes-offsite-restore-drill.timer`
   - loaded from `/etc/systemd/system/apex-personal-notes-offsite-restore-drill.timer`
   - `enabled`
   - `active (waiting)`
   - next trigger `2026-05-10 05:01:47 UTC`
   - triggers `apex-personal-notes-offsite-restore-drill.service`
3. platform timers also observed:
   - `backup-etcd.timer`
   - `dpkg-db-backup.timer`

Interpretation:

The host-owned encrypted offsite backup and restore-drill timer surfaces are live and governed as host-native systemd timers. They remain private-lane infrastructure, not evidence of a Market-app Restic installation or public service promotion.

## Host Repo-Clone Evidence

Host clone:

1. repo path: `/home/olares/src/apex-power-ops-platform`
2. git top-level: `/home/olares/src/apex-power-ops-platform`
3. branch: `clean-main`
4. commit: `2836a2622309b4e146ca24f23b5bf87312c0c857`
5. latest commit summary: `2836a26 2026-04-24T18:01:21-07:00 Track Olares storage first-run scripts`
6. remote: `https://github.com/jasonlswenson-sys/apex-power-ops.git`
7. status: dirty, with modified storage scripts, package files, forms-engine files, and untracked `infra/compose.dev.yml`, `infra/olares/charts/`, `infra/private/`, `packages/p6-ingest/`, `services/`, `tests/canary/`, and `tools/`

Current workstation publication boundary:

1. git top-level: `C:/APEX Platform`
2. prefix for this repo view: `apex-power-ops-platform/`
3. branch: `clean-main`
4. commit: `9587c8189ba2fc61a580ba83f0d9895298db243c`
5. latest commit summary: `9587c81 2026-05-03T17:24:52-07:00 docs(olares): author packet 005 ssh inventory`
6. remotes: `origin` and `public` both point to `https://github.com/jasonlswenson-sys/RESA-Power-Project-Management.git`
7. status: workstation has current Phase 5 handoff and packet files untracked, including Packet 001 through Packet 004 handoffs and packet JSON files

Interpretation:

The host clone is not currently canonical for daily APEX development. It is older, dirty, rooted at a different host path, and points at a different GitHub remote than the workstation publication boundary. The restored SSH path makes remote editing technically possible, but repo authority and publication asymmetry remain blockers.

## Three-Zone Classification Update

Dev zone:

1. Real: host-local Docker `apex-dev` project with healthy APEX service containers on loopback.
2. Real but non-canonical: SSH and VS Code Remote-SSH can reach the host through `olares-mesh`.
3. Brittle or unresolved: host clone is dirty, older than workstation, and remote-divergent.
4. Deferred: Olares-first daily development as center of gravity.

Services zone:

1. Real: K3s/Olares system is live; `forms-engine` and `p6-ingest` are deployed through Helm and running as Olares applications.
2. Real: browser/utility apps such as Chromium, Firefox, JDownloader2, qBittorrent, and Windows are running as Olares apps.
3. Present but not current APEX service-zone expansion: Olares AppImage catalog entries exist for many AI and automation apps, including `ollamav2`, `openwebui`, `difyv2`, `n8n`, `gitea`, and related services, but this packet did not observe them as installed/running Applications.
4. Live but needing reconciliation: `forms-engine` and `p6-ingest` Application CRs are `running`, while their AppImage CRs report `failed`.
5. Deferred: AI-services-zone expansion, public ingress promotion, Gitea mirror enhancement, and canonical-hosting transition.

Staging zone:

1. Governed in repo by canary and chart evidence referenced in `docs/architecture/SERVICE-HOST-INSTALLED-PROOF-CHECKLIST-2026-04-23.md`.
2. Not directly proven as a separate live Olares staging zone by this host inventory.
3. Deferred: any promotion from staging evidence to public or canonical hosting.

Private lane:

1. Real: `private-personal-notes-1` on loopback with host data under `/home/olares/apex-data/personal/memos`.
2. Real: offsite backup and restore-drill timers are enabled and waiting.
3. Governed boundary remains host-only or mesh-tunneled.

## TASK Impact

TASK-021:

Packet 005 captures the missing host clone path, branch, commit, cleanliness, and remote evidence. The assessment now has enough evidence to say that Olares-first daily development is not ready because the host clone is dirty, older, path-divergent, and remote-divergent from the workstation publication boundary. Technical SSH reachability is no longer the blocker; repo authority reconciliation is.

TASK-023:

Packet 005 captures live Docker, K3s, Helm, installed-app, ports, volumes, networks, app CRs, and private-lane timer evidence. The inventory gap is satisfied. The services-zone conclusion is mixed: `forms-engine` and `p6-ingest` are live and deployed; broader AI-services-zone apps remain catalog/design intent rather than observed running services; AppImage CR state for the two APEX apps needs reconciliation.

TASK-025:

Packet 005 improves the decision surface but does not make any of the four paths ready:

1. workstation-only migration: technically reachable, not repo-authority ready
2. AI-services-zone expansion: not supported by observed running AI services
3. Gitea/code-hosting mirror enhancement: not supported by current missing/unstated hosting transition authority and host clone divergence
4. canonical-hosting transition: no-go

## Unknowns Requiring Follow-Up

1. Why `forms-engine` and `p6-ingest` AppImage CRs report `failed` while Application CRs, Deployments, Pods, Services, and Helm releases are running.
2. Whether the host clone should be retired, refreshed, preserved as evidence, or reconciled under a future bounded packet.
3. Whether the host `apex-dev` Docker project should be treated as a governed dev-zone surface or only as a legacy/private-lane runtime.
4. Whether any AI services listed in the AppImage catalog are intentionally installable-only, cached catalog entries, or future services-zone candidates.
5. Whether the missing `docs/architecture/GIT-HOSTING-AND-GITEA-TRANSITION-CHECKLIST-2026-04-23.md` should be authored or restated before any Gitea/code-hosting mirror decision.

## Explicit No-Go Items

Do not open generic Olares implementation.

Do not migrate daily APEX development to Olares-first on this evidence.

Do not promote loopback Docker services to public ingress.

Do not change auth, Headscale, LarePass, SSH host trust, Olares Settings, Kubernetes, Helm, or systemd state from this packet.

Do not treat AppImage catalog presence as installed/running AI-service proof.

Do not treat host clone existence as repo authority.

Do not start Gitea, code-hosting mirror, or canonical-hosting transition work from this packet alone.

## Next Packet Recommendation

The smallest truthful next move is not another access-recovery packet.

Recommended next handoff:

`Olares Phase 5 post-005 reconciliation`

Purpose:

1. reconcile Packet 005 evidence into TASK-021, TASK-023, and TASK-025,
2. decide which tasks can close as assessments and which remain open as implementation blockers,
3. classify the AppImage CR mismatch without mutating the host,
4. decide whether a future repo-clone reconciliation packet is warranted,
5. preserve the no-go boundary around Olares-first daily development, services-zone expansion, Gitea, and canonical hosting.

## Final Disposition

Mesh SSH path: healthy.

Host runtime: directly inventoried.

Packet 001 inventory gap: satisfied for host runtime truth.

VS Code Remote-SSH: technically viable through `olares-mesh`.

Packet 005: `complete - pass`.

Claude Code reconciliation prompt: warranted.
