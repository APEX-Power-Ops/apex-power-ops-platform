# Olares Phase 5 Step 3 Expansion Decision Surface Handoff

Date: 2026-05-03
Status: Complete - packet-ready decision surface for the bounded Phase 5 expansion lane
Scope: synthesize Step 1, Step 2, and Packet 001 evidence into a packet-ready decision surface that keeps workstation migration, AI services-zone expansion, code-hosting mirror, and canonical-hosting transition as separately governed decisions

## Authority

This handoff executes the synthesis lane defined in:

1. `ops/agents/handoffs/2026-05-03-olares-phase-5-next-task-and-prompt-routing-handoff.md` Prompt 2
2. `plan/infrastructure-olares-full-implementation-roadmap-1.md` Phase 5
3. `Infrastructure/Olares_Workspace_Authority_Framework.md`
4. `Infrastructure/Olares_Build_Guide.md`
5. `.claude/DECISION_LOG.md`
6. `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md`
7. `docs/architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md`

This handoff does not reopen generic Olares implementation, does not authorize installs, ingress changes, auth changes, code-hosting cutover, or any claim that workstation Docker proves Olares host truth.

## Tasks Covered

This handoff closes:

1. `TASK-026` - packet-ready decision surface for future Olares expansion

This handoff partially advances and explicitly leaves open:

1. `TASK-021` - repo authority and publication model assessment for Olares-first daily development
2. `TASK-023` - intended services-zone stack classification
3. `TASK-025` - four-way split decision among workstation migration, AI-services expansion, code-hosting mirror, and canonical-hosting transition

This handoff does not close TASK-021, TASK-023, or TASK-025 because the evidence required for closure is not yet present.

## Inputs Synthesized

1. `ops/agents/handoffs/2026-05-03-olares-phase-5-step-1-dev-workspace-state-and-access-assessment-handoff.md` - closed TASK-019 and TASK-020 with verdict not ready for Olares-first daily development
2. `ops/agents/handoffs/2026-05-03-olares-phase-5-step-2-ai-toolchain-and-codex-role-assessment-handoff.md` - closed TASK-022 and TASK-024 with verdict conditionally ready after bounded decisions; Codex out of first slice
3. `ops/agents/handoffs/2026-05-03-olares-phase-5-001-access-and-runtime-revalidation-handoff.md` - Packet 001 closed partial; private mesh still blocked from current workstation; host runtime not directly inspected
4. `ops/agents/packets/draft/2026-05-03-olares-phase-5-001-access-and-runtime-revalidation.json` - read-only revalidation packet definition
5. `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md` - restored bounded local Olares rerun surfaces in workspace snapshot
6. `ops/agents/handoffs/2026-05-01-olares-private-stack-browser-terminal-bring-up-handoff.md` - documents reproducible mesh-recovery recipe via TermiPass named-pipe and Headscale registration
7. `ops/agents/handoffs/2026-04-25-olares-workstation-001-publication-follow-through-scope-handoff.md` - bounded publication scope of 10 surfaces
8. `ops/agents/handoffs/2026-04-25-olares-workstation-002-publication-follow-through-blocker-handoff.md` - packet-002 blocked because most defined paths now absent or clean
9. `Infrastructure/Olares_Workspace_Authority_Framework.md` - three-zone authority and parent-git-root publication boundary
10. `Infrastructure/Olares_Build_Guide.md` - intended services-zone shape
11. `.claude/DECISION_LOG.md` - sections 8.1, 8.2, 8.3 still entirely open
12. `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` - December 2025 protocol predates Olares transition

## Executive Verdict

Current evidence does not support Olares-first daily development today and does not support opening any of the four future expansion paths from `TASK-025` for implementation in this lane.

The Phase 5 assessment lane has produced a coherent, evidence-bearing decision surface that keeps the four candidate moves explicitly split:

1. workstation-only migration is blocked on access regression and on packet-002 publication scope reality
2. AI services-zone expansion is conditionally blocked behind bounded written decisions named in Step 2
3. Gitea or code-hosting mirror enhancement cannot truthfully proceed because its named gating checklist `docs/architecture/GIT-HOSTING-AND-GITEA-TRANSITION-CHECKLIST-2026-04-23.md` is referenced as authority in the roadmap but does not exist on disk in this workspace snapshot
4. broader canonical-hosting transition remains explicitly out of scope under `ATT-004`, `TASK-013`, and `CON-002`

The single recommended next packet is an access-recovery packet, not an expansion packet. Packet `2026-05-03-olares-phase-5-001` remains the correct shape but cannot complete without a precursor that restores private-mesh access from the current workstation. That precursor is itself a candidate for the smallest next packet.

Conclusion: not ready for any expansion path; ready only for a narrow access-recovery packet that unlocks the runtime-inventory portion of Packet 001.

## TASK-021 - Repo Authority And Publication Model For Olares-First Daily Development

### Intended Design

Per `Infrastructure/Olares_Workspace_Authority_Framework.md`:

1. `C:/APEX Platform/apex-power-ops-platform` is the canonical implementation workspace to be hosted on the Olares One
2. parent git root remains `C:/APEX Platform` until a deliberate cutover (Phase E)
3. Olares transition work staged with bounded pathspecs against `apex-power-ops-platform/` or `Infrastructure/` only
4. VS Code Remote-SSH is the primary editing path into the Olares One

### Current-State Findings

Repo-side:

1. parent git root remains `C:/APEX Platform` per `Infrastructure/Olares_Workspace_Authority_Framework.md §6 Git directives`
2. bounded publication scope is defined in the 2026-04-25 publication-scope handoff for these workstation surfaces:
   - `infra/compose.dev.yml`, `infra/olares/`, `packages/forms-engine/`, `packages/p6-ingest/`, `services/mcp/`, `tests/canary/`, `tools/canary/`, `tools/run-canary.sh`, `tools/run-canary.ps1`, `tools/shell/`
3. packet `2026-04-25-olares-workstation-002` is blocked: most defined paths are now absent or already clean on `clean-main`, leaving only `tests/canary/` as residue per the 2026-04-25 blocker handoff
4. the first publication-control tranche landed on `clean-main` as commit `9db2efd`

Host-side:

1. host repo clone exists at `/home/olares/src/apex-power-ops-platform/apex-power-ops-platform` per the 2026-05-01 private-stack handoff - the doubled `apex-power-ops-platform/apex-power-ops-platform` path indicates the clone was placed inside a parent-named directory rather than at root, which doubles the publication-relative path
2. the same handoff acknowledges that the host clone did not contain the workstation-side `infra/private` surfaces and required direct host-side staging to bring up the private stack
3. host runtime was not directly inspected in Packet 001; current host repo state is unknown live

Editing-path:

1. VS Code Remote-SSH is not currently viable from this workstation per Packet 001: `olares-mesh` to `100.64.0.1:22` times out; public hostname returns publickey-denied
2. the configured SSH hosts are `Host olares` -> `jlswen2121.olares.com` and `Host olares-mesh` -> `100.64.0.1`; both currently fail

### Gap Classification

| Gap | Severity | Notes |
|---|---|---|
| no working trusted SSH path from this workstation | blocking for daily editing | recovery recipe is documented in 2026-05-01 private-stack handoff and is reproducible |
| packet-002 publication scope no longer matches branch reality | blocks publication closure | packet must be restated against actual residue or explicitly retired per 2026-04-25 blocker handoff |
| host repo clone path doubling | latent friction | not yet a regression but creates fragile paths for later automation |
| host repo clone staleness vs workstation `infra/private` surfaces | documented in 2026-05-01 handoff | reconciliation depends on restored SSH path |

### Determination

`TASK-021`: open. Current evidence does not support an Olares-first daily development posture without changing the parent git root, primarily because the editing path is currently broken and the packet-002 publication scope is unresolved.

Missing evidence required to close `TASK-021`:

1. working trusted SSH path from this workstation to the Olares host
2. either restated or explicitly retired packet-002 publication scope
3. live host repo state reconciliation showing the host clone matches canonical branch state at a known commit

## TASK-023 - Services-Zone Stack Classification

This task is informed by Step 2 but is the formally responsible task for services-zone classification.

### Classification Matrix

| Surface | Intent (Build Guide §5-6) | Current state (live evidence) | Classification |
|---|---|---|---|
| Ollama | local-model serving, "Internal" auth, LarePass-only | none; not in evidence floor; host inspection failed in Packet 001 | design-intent |
| Open WebUI | human chat surface for Ollama | none | design-intent |
| Dify | agent orchestration, RAG pipelines | none | design-intent |
| n8n | low-code orchestration for scheduled jobs | none; conflicts conceptually with landed `apex-personal-notes-offsite-backup.timer` and weekly restore-drill timer (bare systemd, not n8n) | design-intent with conflict |
| Qdrant | services-zone vector DB | running in workstation `apex-dev` Docker as `apex-dev-qdrant-1` (unhealthy due to `wget: not found` in healthcheck) per Packet 001; no Olares-host install evidence | dev-zone real (workstation), services-zone design-intent only |
| Syncthing | bidirectional file sync to field tablets | none | design-intent |
| Restic | encrypted offsite backups | OPERATIONAL on host as bare-binary runner via `apex-personal-notes-offsite-backup.timer` (daily 03:30 UTC) and `apex-personal-notes-offsite-restore-drill.timer` (weekly Sunday 05:00 UTC); Backblaze B2 backed; snapshot `76b8155c` proven via run-now per `PROJECT_STATUS.md` Phase 2 closure | services-zone operational as bare runner, NOT as Olares-Market app |
| Optional Gitea | local Git mirror | none; gating checklist file does not exist on disk - see Critical Finding below | not yet governed |
| `forms-engine` (NOT services-zone but adjacent) | OlaresManifest installed app | installed proof closed 2026-04-25; current live state unknown (Packet 001 partial) | governed installed app, current state unverified live |
| `p6-ingest` (NOT services-zone but adjacent) | OlaresManifest installed app | installed proof closed 2026-04-25; current live state unknown (Packet 001 partial) | governed installed app, current state unverified live |
| `personal-notes` (private lane, NOT services-zone) | host-only Memos on `127.0.0.1:5230` | operational per 2026-05-01 handoff; not revalidated live in Packet 001 | private lane operational per prior evidence; current live state unverified |

### Critical Finding - Missing Authority File

The roadmap's `FILE-008` and Phase 3 `TASK-013` both name `docs/architecture/GIT-HOSTING-AND-GITEA-TRANSITION-CHECKLIST-2026-04-23.md` as the gating authority for any Gitea or canonical-hosting decision. Prompt 2's reading list also names it. Glob search across `C:/APEX Platform/**` returns no match.

This is not a Step 3 problem to silently fix. It means:

1. `TASK-013` cannot be cited as a gate because its named gating document is absent
2. `TASK-025 (c)` (code-hosting mirror enhancement) has no documented gate to compare against
3. any later packet that proposes Gitea install or mirror posture must either author the missing checklist or restate its gating authority

### Determination

`TASK-023`: open. Classification is captured in this handoff, but cannot be closed because:

1. all "current state" entries for Olares-host services-zone surfaces rest on prior handoff evidence rather than live host inspection (Packet 001 closed partial)
2. the Gitea-checklist authority file does not exist on disk
3. the Restic operational status is honest only as "bare runner via systemd timer" - not the Build Guide's intended Market-app posture - and that distinction must not be smoothed over

Missing evidence required to close `TASK-023`:

1. live Olares-host inventory of installed Market apps (blocked by access regression)
2. an authored or located `GIT-HOSTING-AND-GITEA-TRANSITION-CHECKLIST-2026-04-23.md`
3. an explicit decision on whether the bare-systemd Restic posture supersedes, parallels, or is superseded by an intended Market-app Restic posture

## TASK-025 - Four-Way Split Decision Surface

The four candidate expansion paths must remain split. This section keeps them split and assesses each.

### (a) Workstation-Only Migration

Scope: move daily APEX development center of gravity to the Olares One via VS Code Remote-SSH against `~/code/apex` on the host.

Current readiness: BLOCKED.

Blockers:

1. mesh access regression (Packet 001 partial)
2. publickey auth failure on public FRP path
3. packet-002 publication scope no longer matches branch reality
4. host repo clone path doubling

Smallest move that would advance this path: an access-recovery packet using the documented TermiPass named-pipe and Headscale registration recipe from the 2026-05-01 private-stack handoff §"Verified Workstation Recovery."

### (b) AI Services-Zone Expansion

Scope: open the first AI-toolchain packet on Olares per Step 2's bounded recommendation.

Current readiness: CONDITIONALLY BLOCKED behind written decisions.

Per Step 2 §"Safe First-Slice Boundary," all of the following must close before this path is plausible:

1. decide and document `ai_tasks` versus `apex-jobs` ledger relationship in writing, including `env=sandbox|host` column and `promote_packet` refusal logic
2. close `.claude/DECISION_LOG.md §8.1`, `§8.2`, `§8.3` in writing
3. restate or explicitly supersede `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` against the current Olares boundary
4. declare which Claude Code install is the first-class Olares-side surface
5. select exactly one MCP server for first-slice bring-up

Codex remains out of the first slice per Step 2's re-entry gate.

This path is also indirectly blocked by (a): without working host access, even a bounded MCP-server bring-up cannot be evidenced live.

### (c) Gitea Or Code-Hosting Mirror Enhancement

Scope: stand up local Git mirror; preserve GitHub-canonical posture.

Current readiness: CANNOT TRUTHFULLY PROCEED.

The named gating authority `docs/architecture/GIT-HOSTING-AND-GITEA-TRANSITION-CHECKLIST-2026-04-23.md` does not exist on disk. The framework's Git directive `Infrastructure/Olares_Workspace_Authority_Framework.md §6` says publication still happens from parent git root. `ATT-004` and `TASK-013` say "Keep GitHub canonical during MVP-era hosting; any Gitea use remains mirror-only until a separate transition packet is approved."

Smallest move that would advance this path: author the missing `GIT-HOSTING-AND-GITEA-TRANSITION-CHECKLIST-2026-04-23.md` as a separate documentation packet, OR explicitly restate the gating authority elsewhere. This is documentation work, not infrastructure work.

### (d) Broader Canonical-Hosting Transition

Scope: cut canonical hosting from GitHub to Gitea-on-Olares.

Current readiness: EXPLICITLY OUT OF SCOPE.

Authorities preserving this status:

1. `ATT-004` - Keep GitHub canonical during MVP-era hosting
2. `TASK-013` - GitHub remains canonical; Gitea is mirror-only gate
3. `CON-002` - Do not reopen Olares implementation as the repo's primary frontier unless reopen criteria are met
4. `Olares_Workspace_Authority_Framework.md §5 Phase E` - explicit decision review, not automatic

This path is not opened by this assessment lane and is not the subject of this packet.

### Determination

`TASK-025`: open. The four-way split is preserved in writing. No path is currently READY. Path (a) is unblocked first by an access-recovery packet; path (c) is unblocked first by a documentation packet authoring the missing gating checklist; path (b) requires Step 2's bounded decisions; path (d) is not in scope.

Missing evidence required to close `TASK-025`:

1. for (a): working trusted SSH path plus packet-002 publication-scope resolution
2. for (b): closure of Step 2's five preconditions
3. for (c): authored gating checklist
4. for (d): explicit reopen approval per `CON-002`, not in scope here

## GitHub-Canonical Versus Olares-Hosted-Only Boundary

This section is required by Prompt 2 and is load-bearing for any future packet.

### Currently GitHub-Canonical

Source of truth lives in GitHub for:

1. parent git root `C:/APEX Platform` and all tracked content
2. `apex-power-ops-platform/` workspace including `apps/`, `packages/`, `infra/`, `ops/`, `services/`, `docs/`, `tools/`, `tests/`
3. `Infrastructure/` documents and authority framework
4. `Platform-Authority/` packet stack
5. `Supabase/` schema files and protocols
6. `.claude/` authority surfaces including `DECISION_LOG.md`
7. all dated handoffs under `ops/agents/handoffs/`
8. all packets under `ops/agents/packets/`
9. all OlaresManifest and Helm chart definitions for `forms-engine` and `p6-ingest` that exist in repo

### Olares-Hosted-Only

Lives only on the Olares host and is not GitHub-canonical:

1. `/home/olares/apex-secrets/personal/memos-admin.env` - machine-local bootstrap admin credential file with `-rw-------` permissions
2. `/home/olares/code/personal/.env.personal` - machine-local env path
3. `/home/olares/apex-data/personal/memos/` - mutable runtime data path with SQLite store `memos_prod.db`
4. `/home/olares/apex-backups/personal/memos/` - host-local Memos backup archives
5. `/home/olares/code/personal/personal-stack-operator-note.md` - machine-local operator note
6. `/home/olares/code/personal/run-personal-notes-offsite-backup-host.sh` - deployed host-native runner
7. `/home/olares/code/personal/run-personal-notes-offsite-restore-drill-host.sh` - deployed restore-drill runner
8. `apex-personal-notes-offsite-backup.timer` and `.service` - systemd unit installed on host
9. `apex-personal-notes-offsite-restore-drill.timer` and `.service` - systemd unit installed on host
10. host-side Restic repository on Backblaze B2 - credentialed from host env file
11. K3s and Helm runtime state for installed `forms-engine` and `p6-ingest`
12. `/home/olares/.ssh/authorized_keys` - host SSH authorization state
13. host SSH keypair `/etc/ssh/ssh_host_ed25519_key` - fingerprint `SHA256:Bv4YFhnvW3xYcl+PcES/qiG1iCVYKAdxyb7bFv1I9IU` per 2026-05-01 verification

### Workstation-Only (Neither Olares-Hosted Nor GitHub-Canonical Until Published)

Lives only on the workstation:

1. `$HOME\OlaresPersonalBackups\memos` - workstation-held backup copy
2. `$HOME\OneDrive\OlaresPersonalBackups\memos` - workstation-mediated OneDrive mirror
3. local `apex-dev` Docker compose runtime with 11 containers - this is workstation Docker, not Olares host
4. workstation TermiPass client state and Headscale registration

### Boundary Erosion Risks Currently Open

1. host clone at `/home/olares/src/apex-power-ops-platform/apex-power-ops-platform` is acknowledged stale relative to workstation surfaces; reconciliation is gated on access recovery
2. direct host-side staging of `infra/private` files in 2026-05-01 bring-up created a divergence between host repo state and canonical branch state that has not been reconciled
3. packet-002 publication-scope mismatch means some workstation-evidenced surfaces are not currently published from canonical branch state

The boundary above must be cited verbatim in any future packet that proposes to install, promote, or move surfaces between zones.

## Explicit No-Go Items For Now

This list is binding on any next packet authored under this lane.

1. no Olares-first daily development migration packet
2. no host runtime mutation
3. no Olares-installed services beyond `forms-engine` and `p6-ingest`
4. no AI-services-zone expansion packet until Step 2's five preconditions close in writing
5. no Codex install or admission as local executor or remote batch worker
6. no Ollama, Open WebUI, Dify, n8n, or Open WebUI install
7. no MCP fabric beyond a single server in any first slice
8. no LiteLLM or equivalent Anthropic proxying
9. no public ingress for any surface
10. no auth posture changes
11. no Gitea install or mirror posture without first authoring the missing `GIT-HOSTING-AND-GITEA-TRANSITION-CHECKLIST-2026-04-23.md` or restating its gating authority
12. no canonical-hosting cutover from GitHub
13. no force-push of packet-002 publication against a scope that no longer exists as defined
14. no force-reconciliation of workstation `known_hosts` from the public FRP hostname candidate key
15. no claim that local workstation `apex-dev` Docker proves Olares host runtime truth
16. no promotion of the private personal lane into AI-toolchain scope, governed installed-app set, or public ingress
17. no silent re-use of `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` (December 2025) as if it were Olares-aware
18. no collapsing of paths (a), (b), (c), and (d) of `TASK-025` into a single move-to-Olares lane

## Recommended Smallest Next Packet

The single recommended next packet is an **access-recovery packet** that uses the documented and reproducible TermiPass named-pipe plus Headscale registration recipe from `ops/agents/handoffs/2026-05-01-olares-private-stack-browser-terminal-bring-up-handoff.md §Verified Workstation Recovery`.

Bounded scope:

1. use the local TermiPass named-pipe API to recover `LarePass` with `ControlURL=https://headscale.jlswen2121.olares.com` and `WantRunning=true`
2. confirm node key registration in the Olares Headscale pod for user `default`
3. validate `BackendState: Running` and workstation mesh IP allocation in the `100.64.*` range
4. validate peer `olares` online at `100.64.0.1`
5. validate `Test-NetConnection 100.64.0.1 -Port 22` succeeds
6. validate non-interactive SSH to `olares@100.64.0.1` succeeds
7. on success, immediately re-trigger the inventory portion of Packet 001 (Docker, K3s or Helm, installed apps, ports, volumes, networks, private-lane timers)
8. write a dated handoff at `ops/agents/handoffs/2026-05-03-olares-phase-5-002-access-recovery-and-runtime-inventory-handoff.md`

Out of scope for this packet:

1. no installs
2. no promotions
3. no ingress changes
4. no auth changes
5. no migration
6. no AI-toolchain scaffolding
7. no Gitea or hosting changes
8. no public-host SSH trust changes

This packet does not open expansion. It restores the access path that Packet 001 needed but could not establish, and it captures the inventory that Packet 001 was authorized but unable to capture.

## Status Of Packet 2026-05-03-olares-phase-5-001

Packet `2026-05-03-olares-phase-5-001` is **not superseded**.

It remains the correct shape for the inventory portion of the work it was authored to do. Its access-revalidation portion completed and produced a definitive negative finding. Its runtime-inventory portion did not complete because access was not restored.

Recommended disposition:

1. mark Packet 001 closure status as `partial - access-blocked` rather than re-running it as authored
2. open the recommended access-recovery packet above as a precursor
3. on access-recovery success, re-run Packet 001's runtime-inventory steps within the new packet rather than re-issuing Packet 001

## Decision Standard Statement

Per Prompt 2's decision standard:

1. **Current evidence does not support Olares-first daily development.** Stated directly. The reasons are access regression, packet-002 publication-scope mismatch, and absence of live host runtime evidence.
2. **No roadmap task is being marked complete by this handoff except `TASK-026`**, which closes because this handoff IS the packet-ready decision surface.
3. **`TASK-021`, `TASK-023`, `TASK-025` remain open** with named missing evidence as listed above.

## Phase 5 Roadmap Task Disposition

After this handoff lands and the roadmap is updated:

| Task | Status | Closing handoff |
|---|---|---|
| `TASK-019` | Closed 2026-05-03 | Step 1 |
| `TASK-020` | Closed 2026-05-03 | Step 1 |
| `TASK-021` | Open - access regression and packet-002 unresolved | this handoff names missing evidence |
| `TASK-022` | Closed 2026-05-03 | Step 2 |
| `TASK-023` | Open - live host inventory missing; Gitea checklist file missing | this handoff names missing evidence |
| `TASK-024` | Closed 2026-05-03 | Step 2 |
| `TASK-025` | Open - all four paths classified; none currently READY | this handoff names per-path missing evidence |
| `TASK-026` | Closed 2026-05-03 | this handoff |

## Validation Performed

This handoff is read-only synthesis. No host runtime mutation, no installs, no ingress or auth changes, no code-hosting cutover. Validation steps performed:

1. cross-referenced `TASK-019` through `TASK-026` against Step 1, Step 2, and Packet 001 closure handoffs to confirm closure-versus-open status
2. confirmed by glob search that `docs/architecture/GIT-HOSTING-AND-GITEA-TRANSITION-CHECKLIST-2026-04-23.md` does not exist on disk
3. confirmed the bounded publication-scope path list from the 2026-04-25 publication-scope handoff and the residue list from the 2026-04-25 blocker handoff
4. confirmed Packet 001 disposition `partial` by direct read of the Packet 001 handoff
5. confirmed the documented access-recovery recipe by direct read of the 2026-05-01 private-stack handoff §Verified Workstation Recovery
6. preserved the four-way `TASK-025` split without collapsing
7. preserved the GitHub-canonical versus Olares-hosted-only boundary verbatim from prior handoffs
