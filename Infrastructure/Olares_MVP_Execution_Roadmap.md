# APEX on Olares One — MVP Execution Roadmap

_Execution authority companion to `Olares_Workspace_Authority_Framework.md`._
_Authored 2026-04-23 for stakeholder-directed Olares transition._
_Retained as first-run MVP sequencing context after the 2026-04-25 Olares closure transition; it is no longer the live execution frontier._

## 1. Purpose

This document preserves the original first-run MVP design-and-delivery roadmap for moving APEX Platform onto the Olares One.

It is not a brainstorming note and it is not a session bootstrap prompt. It remains the parent-root statement of what the MVP was, what was built first, what was deferred, and what technical standards defined acceptable first-run implementation.

Do not use this file by itself to decide current Olares execution priority.

Use these repo-local files first for current Olares next steps:

1. `apex-power-ops-platform/plan/infrastructure-olares-full-implementation-roadmap-1.md` — live post-closure Olares roadmap
2. `apex-power-ops-platform/docs/architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md` — bounded follow-through and rerun checklist
3. `apex-power-ops-platform/docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md` — broader platform execution priority

Use this file to understand the original MVP intent, sequencing rationale, and trust-model design that the later repo-local roadmap now inherits.

## 2. Authority Position

The Olares authority stack is:

1. `Olares_Workspace_Authority_Framework.md` — highest authority for workspace interpretation, decision boundaries, and transition rules
2. `apex-power-ops-platform/plan/infrastructure-olares-full-implementation-roadmap-1.md` — live post-closure Olares roadmap
3. `apex-power-ops-platform/docs/architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md` — active bounded follow-through and rerun surface
4. this file — first-run MVP sequencing context and design baseline
5. `Olares_Build_Guide.md` — architectural rationale and target operating model
6. `Olares_Checklist.md` — original provisioning checklist and first-run reference
7. `VSCode_Build_Prompt.md` — execution bootstrap for fresh implementation sessions

Implication:

1. the prompt does not define governance
2. this file no longer overrides the repo-local post-closure roadmap or checklist
3. if implementation learns something new about current Olares scope, update the framework or the repo-local roadmap first, then realign this file only if the original MVP baseline also needs correction

## 3. Current Status Note

As of the 2026-04-25 Olares transition closeout captured in the repo-local roadmap:

1. the first governed workstation lane is closed
2. the first installed-proof lanes for `forms-engine` and `p6-ingest` are closed
3. friendly alias cleanup is closed
4. Olares is not the repo's primary delivery frontier

Current Olares work is now bounded to:

1. publication follow-through for governed workstation-synced surfaces
2. workstation, installed-service, and backup rerun readiness
3. preservation of the known Helm-managed Settings API limitation
4. explicit gating before any future Olares scope expansion

## 4. Product Decision

The Olares One is the new center of gravity for APEX development.

The MVP is not "run the existing repo somewhere else." The MVP is:

1. a working Olares-hosted dev zone for the live `apex-power-ops-platform` workspace
2. a working services zone for local AI and operational dependencies
3. a first host-truth staging path that proves the APEX completion model on Olares
4. a trust model that preserves the distinction between sandbox progress and host-complete progress

## 5. MVP Outcome

The MVP is successful when all of the following are true:

1. Jason can clone the live workspace onto the Olares One and do normal development there through VS Code Remote-SSH
2. `infra/compose.dev.yml` can bring up the minimum dev dependencies without public exposure
3. the minimum viable MCP trio exists and is reachable over the LarePass mesh only
4. every tracked run that matters to promotion writes an `env` tag to `apex-jobs`
5. `forms-engine` has an installable Olares chart shell in the staging zone
6. at least one Stack Data Center canary lane exists and can be executed reproducibly

## 6. What Is In MVP

### Included

1. dev compose stack
2. minimum viable MCP trio: `apex-fs`, `apex-db`, `apex-jobs`
3. `.claude/` authority surfaces for Olares-hosted implementation
4. first Olares-native chart shell for `forms-engine`
5. canary scaffold and run harness
6. shell ergonomics and workspace defaults
7. repo hygiene for the Olares-hosted workflow

### Explicitly deferred

1. public ingress and Cloudflare/Olares tunnel exposure
2. full field-tablet sync workflow
3. real `forms-engine` business implementation
4. write-capable DB mutation surfaces unless explicitly authorized later
5. repo cutover away from parent git root
6. migrating every application surface to Olares-native charts in the first pass

## 7. Workstreams

### Workstream A — Workspace foundation

Deliverables:

1. `infra/compose.dev.yml`
2. `.env.dev.template`
3. `.gitignore` updates for local Olares-hosted dev artifacts
4. baseline `.vscode/settings.json` and shell aliases

Done means:

1. dev dependencies start cleanly
2. no service is published beyond localhost or the LarePass mesh
3. the workspace has a repeatable startup path on the Olares One

### Workstream B — MCP and run ledger

Deliverables:

1. `services/mcp/apex-fs/`
2. `services/mcp/apex-db/`
3. `services/mcp/apex-jobs/`
4. run-ledger rules enforcing `env=sandbox|host`

Done means:

1. all three servers respond to `tools/list`
2. `apex-db` rejects non-SELECT access
3. `promote_packet` refuses when host evidence is missing

### Workstream C — Claude and operator surfaces

Deliverables:

1. `.claude/CLAUDE.md`
2. `.claude/mcp.json`
3. `.claude/agents/forms-engine.md`
4. `.claude/agents/p6-ingest.md`
5. `.claude/agents/ui.md`

Done means:

1. a fresh implementation session can operate without reconstructing core context from memory
2. the Olares workflow, trust rules, and MVP priorities are explicit and testable

### Workstream D — First staging graduation

Deliverables:

1. `infra/olares/charts/forms-engine/Chart.yaml`
2. `infra/olares/charts/forms-engine/OlaresManifest.yaml`
3. minimum `templates/` scaffolds
4. `infra/olares/scripts/promote.sh`

Done means:

1. the chart is structurally installable
2. OIDC is declared
3. required middleware is declared
4. host-origin run labeling is wired into the service shell

### Workstream E — Trust and audit guardrails

Deliverables:

1. `tests/canary/stack-data-center/`
2. `tools/run-canary.sh`
3. documented rule that staging is the only end-to-end completion surface

Done means:

1. the canary harness has a stable interface
2. the path from dev proof to host proof is explicit

## 8. Original Sequencing Baseline

The sequence below is the original first-run MVP order. It remains useful as design rationale, but it is no longer the current live Olares frontier.

The default sequence is:

1. Workspace foundation
2. MCP and run ledger
3. Claude and operator surfaces
4. First staging graduation
5. Trust and audit guardrails

Reasoning:

1. the Olares One is not a real development center until the dev workspace is repeatable
2. trust rules are meaningless if there is no run ledger to enforce them
3. the first chart shell should be written after the dev and operator model exist
4. canary execution is most useful once the chart shell and run-ledger model are present

## 9. Workflow Model

The authoritative workflow is:

1. design in the framework and roadmap
2. scaffold in bounded packets
3. validate the smallest truthful runnable slice
4. publish bounded commits with proof
5. keep the repo clean between packets

Required proof per implementation packet:

1. what changed
2. what was validated
3. what was deferred
4. which trust constraints were preserved

## 10. Technical Authority Rules

The repo technical authority may decide without pausing for approval on:

1. internal workspace structure under the already-authorized Olares transition model
2. tooling and scaffold layout for dev, services, and staging zones
3. MCP interface shape inside the boundaries already laid out in this roadmap
4. bounded documentation and operator-surface changes needed to preserve clarity

Escalate only for:

1. public exposure decisions
2. identity model changes that conflict with Olares-native auth
3. destructive data operations against real project data
4. repo-cutover decisions away from the parent git root

## 11. Current Next-Step Routing

The original immediate next packet below has been overtaken by later execution and closure.

The current truthful Olares next steps are:

1. finish or explicitly retire the remaining governed workstation publication follow-through from the repo-local Olares roadmap
2. keep workstation rerun readiness current rather than reopening first-run bring-up work
3. keep installed-service rerun readiness current for `forms-engine` and `p6-ingest`
4. keep backup and restore readiness evidence-backed after meaningful drift
5. require a new explicit packet before any future Olares scope expansion

Use these files to execute those steps:

1. `apex-power-ops-platform/plan/infrastructure-olares-full-implementation-roadmap-1.md`
2. `apex-power-ops-platform/docs/architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md`
3. `apex-power-ops-platform/ops/agents/handoffs/2026-04-25-olares-workstation-001-publication-follow-through-scope-handoff.md`
4. `apex-power-ops-platform/ops/agents/handoffs/2026-04-25-olares-workstation-002-publication-follow-through-blocker-handoff.md`

## 12. Success Standard

This roadmap is successful when it prevents two failure modes:

1. the Olares transition degenerating into ad hoc tool setup with no product-oriented sequencing
2. this first-run MVP baseline being mistaken for the current live Olares execution frontier

If a future document or session treats this file as the live frontier again, correct the repo-local roadmap or framework first, then realign this context file so it continues to describe the historical MVP baseline truthfully.