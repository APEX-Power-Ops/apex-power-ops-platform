# APEX on Olares One — Workspace Authority Framework

_Companion authority for `Olares_MVP_Execution_Roadmap.md`, `Olares_Build_Guide.md`, and `Olares_Checklist.md`._
_Authored 2026-04-23 after audit of the live `C:/APEX Platform/apex-power-ops-platform` workspace._

## 1. Purpose

This document turns the Olares planning work into repo authority.

The roadmap defines the MVP delivery shape. The build guide explains the target operating model. The checklist sequences provisioning. This framework closes the missing middle layer: how the current live repository should be interpreted, reshaped, and governed while the APEX Platform transitions onto the Olares One as its primary development and staging host.

Use this file as the highest-authority Olares workspace reference inside this repo. If this file conflicts with the older bootstrap-era language elsewhere, this file wins until the conflicting text is revised.

The VS Code build prompt is not governance. It is a reusable implementation bootstrap derived from this framework and the roadmap.

## 1A. Authority Hierarchy

The Olares authority order is:

1. this framework
2. `Olares_MVP_Execution_Roadmap.md`
3. `Olares_Build_Guide.md`
4. `Olares_Checklist.md`
5. `VSCode_Build_Prompt.md`

This order is mandatory.

## 2. Audit Summary

### Current verified repo state

Audited workspace root: `C:/APEX Platform/apex-power-ops-platform`

Verified active top-level implementation lanes:

1. `apps/`
2. `packages/`
3. `infra/database/`
4. `docs/`
5. `ops/`
6. `knowledge/`
7. `archive/`

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

Verified operating reality:

1. the live git root is still `C:/APEX Platform`
2. `C:/APEX Platform/apex-power-ops-platform` is already the practical implementation surface
3. the parent repo is currently at a zero-frontier publication checkpoint, so the next Olares work is newly-authored infrastructure and workflow work rather than residue cleanup
4. the current Olares documents are strategically sound, but they assume an implementation push that has not yet been codified as repo authority and staged migration phases

### Gap that must be closed

The repo has the beginnings of the future monorepo shape, but it does not yet have a single authoritative transition framework that answers all of the following in one place:

1. what the Olares One becomes in relation to the current repo
2. which existing lanes are authoritative inputs versus target outputs
3. how the three-zone Olares model maps onto the current repo layout
4. what must be authored first inside the repo before the workstation can become the real development center of gravity
5. what changes remain explicitly deferred until later cutover phases

This framework provides those answers.

## 3. Authority Decision

Effective immediately, the intended Olares-hosted workspace authority is:

1. `C:/APEX Platform` remains the canonical publication boundary, and `C:/APEX Platform/apex-power-ops-platform` is the active implementation surface inside that parent git root
2. when mirrored on the Olares One, the intended host parent-root path is `~/code/apex/`, with the active implementation surface at `~/code/apex/apex-power-ops-platform/`
3. this authority defines the intended host path shape and governance boundary; it does not by itself approve migration of the daily development center of gravity onto Olares
3. `Platform-Authority/` remains strategic authority until its surviving decisions are absorbed into repo-native authority surfaces under this workspace
4. the parent git root at `C:/APEX Platform` remains the publication boundary until a deliberate repo cutover is executed later
5. no future documentation should describe `apex-power-ops-platform` as merely speculative bootstrap scaffolding unless it is explicitly discussing pre-2026-04-23 history

## 4. Workspace Model On Olares

### Source-of-truth directories on the Olares One

Recommended filesystem layout on the Olares host:

```text
~/code/apex/              -> parent-root mirror of C:/APEX Platform
~/code/apex/apex-power-ops-platform/ -> active implementation surface inside that mirror
~/apex-data/              -> mutable project/job/state data
~/apex-secrets/           -> local bootstrap secrets not committed to git
~/apex-backups/           -> optional local landing zone before offsite backup
```

Design rules:

1. source code lives under the parent-root mirror `~/code/apex/`, and active implementation work stays under `~/code/apex/apex-power-ops-platform/`
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
5. future `services/mcp/`
6. future `infra/compose.dev.yml`

Rules:

1. dev zone is always tagged `env=sandbox`
2. docker compose is the default runtime for local service iteration
3. dev zone can use localhost or LarePass-only exposure, never public ingress

#### Services zone

Purpose: long-running shared AI and ops dependencies on the Olares One.

Repo lanes that govern it:

1. future `infra/olares/`
2. future `docs/authority/` or `docs/olares/` operating notes
3. future MCP deployment notes

Rules:

1. Ollama, Open WebUI, Dify, Qdrant, n8n, Syncthing, and Restic are services-zone concerns
2. these support the dev and staging zones but are not themselves proof that APEX is complete
3. any repo automation for them must preserve the LarePass-only access model

#### Staging zone

Purpose: host-bootstrap truth for end-to-end completion.

Repo lanes that must be authored for it:

1. `infra/olares/charts/`
2. `infra/olares/scripts/`
3. run-ledger enforcement in `apex-jobs`
4. canary harness and promotion tooling

Rules:

1. staging zone is always tagged `env=host`
2. only staging-origin runs can satisfy packet promotion gates
3. every OlaresManifest must declare an OIDC client and the required backing middleware

## 5. Repo Transition Framework

The transition is phased. Do not skip phases.

### Phase A — Repo authority alignment

Goal: make the repo describe the Olares transition truthfully.

Required outputs:

1. this framework
2. the MVP roadmap
3. aligned Olares build prompt as a non-authoritative session bootstrap
4. aligned root README guidance for Olares hosting

Exit condition:

1. future implementation sessions can start from repo-native authority without relying on informal chat context

### Phase B — Dev workspace foundation

Goal: make the Olares One a working dev host.

Required outputs:

1. `infra/compose.dev.yml`
2. `.env.dev.template`
3. `.claude/CLAUDE.md`
4. `.claude/mcp.json`
5. minimum viable MCP trio under `services/mcp/`
6. shell aliases and VS Code ergonomics surfaces

Exit condition:

1. the Olares One can clone the workspace, bring up the dev stack, and expose the MCP trio over the LarePass mesh only

### Phase C — Trust and promotion guardrails

Goal: encode the difference between sandbox-complete and host-complete.

Required outputs:

1. `apex-jobs` run ledger
2. enforced `env=sandbox|host` tagging
3. canary harness
4. promotion refusal without `env=host`

Exit condition:

1. the repo can prove which runs are dev-only and which are eligible for completion or promotion

### Phase D — First service graduation

Goal: author the first real Olares-native app shell.

Required outputs:

1. `infra/olares/charts/forms-engine/`
2. OlaresManifest with OIDC + middleware declaration
3. installable chart skeleton

Exit condition:

1. `forms-engine` can be installed into the staging zone as a private Olares app

### Phase E — Workspace cutover review

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
6. `.claude/`

The following current directories remain authoritative and should be integrated rather than replaced:

1. `apps/`
2. `packages/`
3. `infra/database/`
4. `docs/`
5. `ops/`

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

## 8. Immediate Authoring Backlog

The next implementation session should start here:

1. author `infra/compose.dev.yml`
2. author `.env.dev.template` and update `.gitignore`
3. scaffold `services/mcp/apex-fs/`
4. scaffold `services/mcp/apex-db/`
5. scaffold `services/mcp/apex-jobs/`
6. author `.claude/CLAUDE.md`, `.claude/mcp.json`, and subagent briefs
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