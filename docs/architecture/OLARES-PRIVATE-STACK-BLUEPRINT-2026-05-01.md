---
goal: Bounded Private Personal Stack Blueprint For Olares-Aligned Local Services
version: 1.0
date_created: 2026-05-01
last_updated: 2026-05-02
owner: Platform Architecture / Olares Execution Lane
status: Proposed bounded design note
tags: [olares, architecture, private, personal, services, compose]
---

# Olares Private Stack Blueprint

## Executive Summary

This document sketches the first safe shape for a personal private setup on the
Olares host without reopening the governed Olares app lane.

The intended first version is not a new Olares-installed app.

It is a private stack that lives in the existing dev or services zone and stays
outside the current host-installed proof boundary for `forms-engine` and
`p6-ingest`.

The design goal is to allow personal services, experiments, utilities, and
private browser tools to run in isolation while preserving the current repo rule
that any new Olares-installed service requires a new explicit packet.

## Authority And Boundary

Use these files first:

1. `C:/APEX Platform/apex-power-ops-platform/docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`
2. `plan/infrastructure-olares-full-implementation-roadmap-1.md`
3. `docs/architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md`

Current boundary:

1. the repo's governed Olares-installed app set is currently bounded to
   `forms-engine` and `p6-ingest`
2. a personal private stack is allowed only as a private dev or services-zone
   concern unless a later explicit packet promotes it
3. this blueprint does not authorize a new OlaresManifest, new public ingress,
   new canonical hosting posture, or new production proof claim

## Scope Lock

In scope:

1. a private compose-managed stack for personal-only use
2. LarePass-only or localhost-only access
3. isolated data, secrets, and optional backup posture
4. a future graduation rule if the stack later needs Olares-native behavior

Out of scope:

1. new installed Olares apps
2. new public URLs or internet exposure
3. promotion into the governed canary or installed-proof chain
4. changes to the existing `forms-engine` or `p6-ingest` app surfaces

## Design Rules

1. keep the private stack separate from the current governed APEX app set
2. use plain Docker Compose first, not OlaresManifest packaging
3. expose services only through localhost or the private mesh
4. keep secrets outside git and outside shared runtime env files
5. give the private stack its own data root so cleanup, migration, and backup
   decisions stay explicit
6. do not let the private stack silently inherit production-like claims by
   sharing the installed-proof or promotion surfaces

## Recommended Host Layout

Recommended host paths:

```text
~/code/personal/            -> personal compose files, private helper code, local notes
~/apex-data/personal/       -> mutable state for personal services
~/apex-secrets/personal/    -> non-git secrets and credentials
~/apex-backups/personal/    -> optional local backup landing zone for personal data
```

Rules:

1. source and configuration live under `~/code/personal/`
2. mutable volumes mount from `~/apex-data/personal/`
3. secrets live under `~/apex-secrets/personal/` and are loaded explicitly
4. backup targeting is opt-in per service rather than assumed

Current bounded implementation on 2026-05-01:

1. `personal-notes` runtime data lives under `~/apex-data/personal/memos`
2. the operator wrapper now writes bounded local snapshots under
   `~/apex-backups/personal/memos`
3. those snapshots are intentionally local restore points, not proof that the
   private stack has joined the governed APEX backup posture

Current bounded implementation on 2026-05-02:

1. workstation-held backup copies are now codified under
   `$HOME\OlaresPersonalBackups\memos`
2. workstation-mediated offsite mirroring is now codified under
   `$HOME\OneDrive\OlaresPersonalBackups\memos`
3. the bounded workstation helper now installs the required daily Task
   Scheduler path for the same backup-fetch-sync flow while reporting the
   optional logon trigger honestly when local machine policy blocks it
4. the separate host-owned encrypted offsite helper now exists at
   `infra/private/run-personal-notes-offsite-backup-remote.ps1`
5. that helper has now been live-validated against the real host and the
   existing Backblaze-backed Restic repository: `status` confirmed repository
   reachability, `init` confirmed the repository already existed, `backup`
   saved a fresh tagged Notes snapshot, and `restore-drill` recovered and
   validated that snapshot in the isolated drill root
6. the host-side recurring cadence helper now exists at
   `infra/private/personal-notes-offsite-backup-schedule.ps1`
7. that helper now deploys a host-native runner plus system-level timer on the
   real Olares host, with the timer validated for daily `03:30 UTC` execution
   and a manual `run-now` producing live Restic snapshot `76b8155c`
8. that same helper now also deploys a weekly host-native restore-drill timer,
   and the backup timer has explicit jitter, start-limit controls, append-only
   file logs under `~/apex-logs/personal/`, and weekly logrotate retention

## Network And Access Model

The first version should use one of these access patterns only:

1. `127.0.0.1`-bound ports for services used only on the host
2. LarePass-reachable private hostnames or ports for services used from a
   laptop or another approved device on the private mesh

Do not start with:

1. public ingress
2. Cloudflare Tunnel or equivalent public exposure
3. Olares app registration or desktop entrance publication

This preserves the existing repo rule that personal utilities are not the same
thing as governed Olares-native apps.

## Minimum Topology

The first private stack should stay small.

Recommended first topology:

1. one primary personal app or gateway container
2. zero or one personal database only if the app truly requires it
3. zero or one helper service such as a file browser, small API, notes service,
   model UI, or proxy

Example shape:

```text
personal-stack
  personal-ui-or-api
  optional-db
  optional-helper
```

The stack should not depend on the governed APEX MCP, canary, or installed-app
surfaces unless a later packet intentionally opens that integration.

## Storage And Data Posture

Use three data classes:

1. disposable
2. useful but recoverable
3. important and recovery-sensitive

Recommended handling:

1. disposable data can stay in ephemeral containers or easily deleted bind
   mounts
2. useful but recoverable data should mount from
   `~/apex-data/personal/<service>`
3. important data should not be admitted until its backup and restore path is
   explicitly chosen and tested

The private stack should not assume that the governed APEX storage and restore
evidence automatically covers personal services.

At the current boundary, the private lane now has three distinct backup layers:

1. host-local timestamped archives under `~/apex-backups/personal/memos`
2. workstation-held export and workstation-mediated OneDrive mirror as the
   active off-host copy floor
3. a host-owned encrypted offsite path governed by the separate Restic helper
   and machine-local env file, now live-proven against the existing Backblaze
   repository without widening the private-lane runtime boundary
4. a host-native recurring automation layer that now executes the encrypted
   offsite backup and retention cadence on the Olares host through a systemd
   timer rather than depending only on workstation-triggered runs
5. a second host-native recurring automation layer that now executes isolated
   restore drills on a weekly cadence so recovery proof no longer depends only
   on ad hoc operator-triggered tests

## Secrets Posture

Use per-service env files or explicit secret files under
`~/apex-secrets/personal/`.

Do not:

1. place personal secrets in the git workspace
2. reuse governed APEX env files for unrelated personal services
3. publish secret-bearing examples into repo-owned docs without placeholders

## Operational Model

Expected lifecycle:

1. build or pull the service images manually or through a local compose wrapper
2. start and stop the private stack independently from the governed APEX stack
3. keep logs, ports, and bind mounts isolated so diagnosis stays local
4. document the service purpose, ports, volumes, and backup expectation in a
   small local note next to the compose file

The private stack is intentionally not part of the current platform promotion
story.

## Example Decision Matrix

Use the following rule set when deciding whether a service stays private or
graduates:

### Keep It Private

Keep the service in the private stack when all of the following are true:

1. it is for one user or a very small trusted set of devices
2. it does not need Olares desktop registration
3. it does not need shared OIDC sign-on
4. failure of the service does not change APEX host-proof status

### Consider Graduation

Open a new explicit packet when one or more of the following becomes true:

1. the service needs a stable Olares entrance URL
2. the service needs shared auth or role mapping
3. the service becomes operationally important enough to require governed
   health checks, canaries, or hosted proof
4. the service begins to hold important shared data that needs formal backup
   and restore coverage
5. the service becomes part of the APEX product or operator workflow rather
   than a personal helper

## Graduation Rule

If the private stack later needs Olares-native behavior, do not convert it ad
hoc.

Instead:

1. author a new explicit packet
2. define the auth, storage, ingress, and middleware posture
3. decide whether the service belongs in the governed app set, shared services
   zone, or somewhere else entirely
4. only then add `infra/olares/<service>/OlaresManifest.yaml` or related chart
   surfaces

## Recommended First Move

The first practical move is a minimal private compose stack with:

1. one personal service
2. one isolated data path
3. one isolated secrets path
4. localhost or LarePass-only exposure
5. no public ingress and no governed promotion claim

For a concrete starting point in this workspace, use:

1. `infra/private/personal-stack.compose.yml`
2. `infra/private/.env.personal.template`
3. `infra/private/README.md`

That gives the user a safe private sandbox without widening the current Olares
boundary.

## Related Files

1. `C:/APEX Platform/apex-power-ops-platform/docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`
2. `plan/infrastructure-olares-full-implementation-roadmap-1.md`
3. `docs/architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md`
4. `docs/architecture/OLARES-WORKSTATION-BRING-UP-CHECKLIST-2026-04-23.md`
5. `docs/architecture/OLARES-FIRST-STORAGE-BRING-UP-RUNBOOK-2026-04-23.md`
6. `infra/private/personal-stack.compose.yml`
7. `infra/private/.env.personal.template`
8. `infra/private/README.md`
9. `docs/architecture/OLARES-PRIVATE-STACK-FIRST-RUN-CHECKLIST-2026-05-01.md`