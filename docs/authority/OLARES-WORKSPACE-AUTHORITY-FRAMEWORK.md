# APEX on Olares One - Workspace Authority Framework

_Repo-owned authority copy established 2026-05-07 so the active Olares workspace framework lives inside the canonical repo boundary._
_Keep the historical parent-root Infrastructure copy aligned until the broader authority relocation lane is complete._

_Companion authority for `../architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`, `../architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md`, and `../../plan/infrastructure-olares-full-implementation-roadmap-1.md`._
_Authored 2026-04-23 after audit of the live `C:/APEX Platform/apex-power-ops-platform` workspace._

Closeout interpretation note:

This framework remains the highest-authority Olares workspace reference inside the repo, but it now governs a post-cutover closeout baseline rather than an open first-run launch lane.

Current routing:

1. use `../architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md` for repo-shell and git-boundary decisions,
2. use `../architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md` for the current Olares operating model,
3. use `../../plan/infrastructure-olares-full-implementation-roadmap-1.md` and `../architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md` for maintained closeout, rerun, and trigger guidance,
4. treat the original MVP roadmap, build guide, checklist, and build-session prompt as retained first-run references unless a deliberate replay or audit requires them.

## 1. Purpose

This document turns the Olares planning work into repo authority.

The roadmap defines the MVP delivery shape. The build guide explains the target operating model. The checklist sequences provisioning. This framework is the repo-owned middle layer for how the current live repository should be interpreted, governed, and continued through the post-cutover Olares convergence baseline.

Use this file as the highest-authority Olares workspace reference inside this repo. If this file conflicts with older bootstrap-era language elsewhere, this file wins until the conflicting text is revised.

The VS Code build prompt is not governance. It is a reusable implementation bootstrap derived from this framework and the roadmap.

## 1A. Authority Hierarchy

The Olares authority order is:

1. this framework
2. `../architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`
3. `../architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md`
4. `../../plan/infrastructure-olares-full-implementation-roadmap-1.md`
5. `../architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md`
6. `../../plan/Olares_MVP_Execution_Roadmap.md`
7. `OLARES-BUILD-GUIDE.md`
8. `../operations/OLARES-CHECKLIST.md`
9. `../operations/OLARES-VSCODE-BUILD-SESSION-PROMPT.md`

This order is mandatory.

## 2. Audit Summary

### Current verified repo state

Audited workspace root: `C:/APEX Platform/apex-power-ops-platform`

Verified active top-level implementation lanes:

1. `apps/`
2. `packages/`
3. `infra/`
4. `docs/`
5. `ops/`
6. `knowledge/`
7. `archive/`
8. `services/`
9. `tests/`
10. `tools/`

Verified active app surfaces already present:

1. `apps/control-plane-api/`
2. `apps/field-surface/`
3. `apps/forms-studio/`
4. `apps/integration-surface/`
5. `apps/lead-surface/`
6. `apps/mutation-seam/`
7. `apps/operations-web/`
8. `apps/pm-surface/`

Verified shared package lanes already present:

1. `packages/api-contracts/`
2. `packages/calc-engine/`
3. `packages/forms-engine/`
4. `packages/p6-ingest/`

Verified operating reality:

1. the live git root for active Apex Ops repo work is now `C:/APEX Platform/apex-power-ops-platform`
2. `C:/APEX Platform` is now workstation umbrella and historical-lineage residue rather than the repo publication boundary
3. `/home/olares/code/apex/apex-power-ops-platform` is the authoritative host mirror for the standalone repo boundary
4. the current Olares documents are strategically sound, but some earlier pre-cutover statements now require explicit historical framing rather than reuse as current repo authority

### Historical Gap Closed By This Framework

At authoring time, the repo had the beginnings of the future monorepo shape, but it did not yet have a single authoritative transition framework that answered all of the following in one place:

1. what the Olares One becomes in relation to the current repo
2. which existing lanes are authoritative inputs versus target outputs
3. how the three-zone Olares model maps onto the current repo layout
4. what must be authored first inside the repo before the workstation can become the real development center of gravity
5. what changes remain explicitly deferred until later cutover phases

This framework now provides those answers inside the canonical repo boundary.

## 3. Authority Decision

Effective immediately, the intended Olares-hosted workspace authority is:

1. `C:/APEX Platform/apex-power-ops-platform` is the canonical local repo root and publication boundary for active Apex Ops repo work
2. when mirrored on the Olares One, the authoritative host path is `~/code/apex/apex-power-ops-platform/`
3. this authority defines the governing repo and host path shape; it does not by itself approve every future expansion of the daily development center of gravity onto Olares
4. `Platform-Authority/` is historical strategic lineage unless a surviving decision has not yet been absorbed into repo-native authority surfaces under this workspace
5. `C:/APEX Platform` is workstation umbrella and provenance residue, not the publication boundary for this repo
6. no future documentation should describe `apex-power-ops-platform` as merely speculative bootstrap scaffolding unless it is explicitly discussing pre-2026-04-23 history

## 4. Workspace Model On Olares

### Source-of-truth directories on the Olares One

Recommended filesystem layout on the Olares host:

```text
~/code/apex/ -> workstation-umbrella and lineage parent on the Olares host
~/code/apex/apex-power-ops-platform/ -> canonical host mirror for active Apex Ops repo work
~/apex-data/ -> mutable project/job/state data
~/apex-secrets/ -> local bootstrap secrets not committed to git
~/apex-backups/ -> optional local landing zone before offsite backup
```

Design rules:

1. source code for active Apex Ops repo work lives under `~/code/apex/apex-power-ops-platform/`, while `~/code/apex/` remains the surrounding Olares host umbrella path
2. mutable runtime and canary data live in `~/apex-data/`
3. secrets never live inside the git workspace
4. staging and service mounts should reference these stable host paths rather than ad hoc directories under home

### Olares three-zone mapping

#### Dev zone

Purpose: fast local iteration and scaffolding.

Repo lanes that feed it first:

1. `apps/control-plane-api/`
2. `apps/forms-studio/`
3. `apps/operations-web/`
4. `packages/*`
5. `services/mcp/`
6. `infra/compose.dev.yml`

Rules:

1. dev zone is always tagged `env=sandbox`
2. docker compose is the default runtime for local service iteration
3. dev zone can use localhost or LarePass-only exposure, never public ingress

#### Services zone

Purpose: long-running shared ops dependencies and optional AI services on the Olares One.

Repo lanes that govern it:

1. `infra/olares/`
2. `docs/authority/` operating notes
3. future MCP deployment notes

Rules:

1. Syncthing and Restic are the current baseline services-zone concerns; Ollama, Open WebUI, Dify, Qdrant, and n8n remain optional deferred candidates until a later packet admits them
2. services-zone components support the dev and staging zones but are not themselves proof that APEX is complete
3. any repo automation for them must preserve the LarePass-only access model

#### Staging zone

Purpose: host-bootstrap truth for end-to-end completion.

Repo lanes that must be authored for it:

1. `infra/olares/`
2. `infra/olares/scripts/`
3. run-ledger enforcement in `apex-jobs`
4. canary harness and promotion tooling

Rules:

1. staging zone is always tagged `env=host`
2. only staging-origin runs can satisfy packet promotion gates
3. every OlaresManifest must declare an OIDC client and the required backing middleware

## 5. Repo Transition Framework

The transition is phased. Do not skip phases.

### Phase A - Repo authority alignment

Goal: make the repo describe the Olares transition truthfully.

Required outputs:

1. this framework
2. the MVP roadmap
3. aligned Olares build prompt as a non-authoritative session bootstrap
4. aligned root README guidance for Olares hosting

Exit condition:

1. future implementation sessions can start from repo-native authority without relying on informal chat context

### Phase B - Dev workspace foundation

Goal: make the Olares One a working dev host.

Required outputs:

1. `infra/compose.dev.yml`
2. `.env.dev.template`
3. repo-owned AI backbone authority, scaffold, and execution surfaces under `docs/authority/OLARES-AI-BACKBONE-FRAMEWORK-2026-05-08.md`, `docs/architecture/OLARES-AI-BACKBONE-SCAFFOLD-SPEC-2026-05-08.md`, and `docs/operations/CODEX-AI-BACKBONE-FIRST-PASS-EXECUTION-BRIEF-2026-05-08.md`
4. minimum viable MCP trio under `services/mcp/`
5. shell aliases and VS Code ergonomics surfaces

Exit condition:

1. the Olares One can clone the workspace, bring up the dev stack, and expose the MCP trio over the LarePass mesh only

### Phase C - Trust and promotion guardrails

Goal: encode the difference between sandbox-complete and host-complete.

Required outputs:

1. `apex-jobs` run ledger
2. enforced `env=sandbox|host` tagging
3. canary harness
4. promotion refusal without `env=host`

Exit condition:

1. the repo can prove which runs are dev-only and which are eligible for completion or promotion

### Phase D - First service graduation

Goal: author the first real Olares-native app shell.

Required outputs:

1. `infra/olares/forms-engine/`
2. OlaresManifest with OIDC + middleware declaration
3. installable chart skeleton

Exit condition:

1. `forms-engine` can be installed into the staging zone as a private Olares app

### Phase E - Workspace cutover review

Goal: decide whether to keep the parent git boundary or cut the workspace into its own repository.

Do not treat this as automatic.

Decision inputs:

1. whether `apex-power-ops-platform` now contains the full active implementation surface
2. whether historical parent-root lanes still matter operationally
3. whether Olares-hosted development is now dominant enough to justify independent repo history and automation

## 6. Repo Design Directives

### Directory directives

The following repo additions are explicitly authorized and expected:

1. `services/mcp/`
2. `infra/compose.dev.yml`
3. `infra/olares/`
4. `tools/shell/`
5. `tests/canary/`
6. `tools/ai/`

The following current directories remain authoritative and should be integrated rather than replaced:

1. `apps/`
2. `packages/`
3. `infra/`
4. `docs/`
5. `ops/`
6. `knowledge/`
7. `archive/`

### Tooling directives

1. VS Code Remote-SSH should be treated as the primary editing path into the Olares One
2. Parsec is a fallback GUI path, not the main engineering workflow
3. LarePass is the primary mesh boundary for anything remotely reachable
4. no repo-authored service should assume public ingress unless a later explicit public-access phase authorizes it
5. LiteLLM or any equivalent proxy may front local models only; it must not front Anthropic access

### Git directives

1. until a later cutover, publication still happens from parent git root `C:/APEX Platform`
2. Olares transition work should be staged with bounded pathspecs against `apex-power-ops-platform/` or `Infrastructure/` only
3. do not mix Olares workspace work with unrelated parent-root changes

## 7. Workflow Authority

The default engineering loop for Olares-hosted APEX work is:

1. author or update repo authority docs if a load-bearing decision changes
2. scaffold in the dev zone first
3. validate locally with the smallest truthful smoke tests
4. add run-ledger and canary hooks before calling the slice complete
5. graduate stabilized slices to Olares-native charts for staging
6. treat staging as the only end-to-end completion surface

This means:

1. code that only runs in compose is not complete
2. code that bypasses `apex-jobs` provenance and env tagging is not complete
3. code that reaches the public internet without later explicit authorization is non-compliant

## 8. Recorded First-Pass Authoring Backlog

This backlog records the first-pass authoring tranche from the framework stage.

It is no longer the default next-session queue.

Current bounded execution should instead start from the repo-owned AI backbone authority, scaffold, execution-brief, and Olares session-prompt surfaces.

Original first-pass backlog at authoring time:

1. author `infra/compose.dev.yml`
2. author `.env.dev.template` and update `.gitignore`
3. scaffold `services/mcp/apex-fs/`
4. scaffold `services/mcp/apex-db/`
5. scaffold `services/mcp/apex-jobs/`
6. author the admitted backbone session-wiring guidance surfaces, later superseded by the repo-owned prompt, scaffold, and execution-brief docs
7. author `infra/olares/charts/forms-engine/`
8. author `tools/run-canary.sh` and the `tests/canary/stack-data-center/` scaffold
9. update root `README.md` and `CODEOWNERS` as needed for the Olares-hosted workflow

## 9. Explicit Non-Goals For This Framework

This framework does not itself:

1. install anything onto the Olares One
2. author the real business logic of `forms-engine`
3. expose any public route
4. perform repo cutover away from the parent git root

Those are later implementation or decision steps.

## 10. Success Condition

This framework is successful when:

1. the repo describes the Olares transition truthfully
2. future build sessions can work from repo-native authority rather than missing context
3. implementation can proceed in bounded phases without re-arguing workspace shape on every session
4. the Olares One becomes the real development center of gravity without weakening the trust, audit, or promotion rules that define APEX completion