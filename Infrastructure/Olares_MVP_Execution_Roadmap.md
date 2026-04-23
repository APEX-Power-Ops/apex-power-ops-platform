# APEX on Olares One — MVP Execution Roadmap

_Execution authority companion to `Olares_Workspace_Authority_Framework.md`._
_Authored 2026-04-23 for stakeholder-directed Olares transition and maintained as the active MVP delivery plan._

## 1. Purpose

This document is the active design-and-delivery roadmap for moving APEX Platform onto the Olares One.

It is not a brainstorming note and it is not a session bootstrap prompt. It is the repo-native statement of what the MVP is, what gets built first, what is deferred, and what technical standards define acceptable implementation.

Use this roadmap when deciding what to build next. Use the build prompt only to bootstrap an implementation session against this roadmap.

## 2. Authority Position

The Olares authority stack is:

1. `Olares_Workspace_Authority_Framework.md` — highest authority for workspace interpretation, decision boundaries, and transition rules
2. this file — active MVP design, sequencing, and delivery authority
3. `Olares_Build_Guide.md` — architectural rationale and target operating model
4. `Olares_Checklist.md` — provisioning and operational checklist
5. `VSCode_Build_Prompt.md` — execution bootstrap for fresh implementation sessions

Implication:

1. the prompt does not define governance
2. the prompt does not override design or sequencing decisions
3. if implementation learns something new, update the framework or this roadmap first, then update the prompt

## 3. Product Decision

The Olares One is the new center of gravity for APEX development.

The MVP is not "run the existing repo somewhere else." The MVP is:

1. a working Olares-hosted dev zone for the live `apex-power-ops-platform` workspace
2. a working services zone for local AI and operational dependencies
3. a first host-truth staging path that proves the APEX completion model on Olares
4. a trust model that preserves the distinction between sandbox progress and host-complete progress

## 4. MVP Outcome

The MVP is successful when all of the following are true:

1. Jason can clone the live workspace onto the Olares One and do normal development there through VS Code Remote-SSH
2. `infra/compose.dev.yml` can bring up the minimum dev dependencies without public exposure
3. the minimum viable MCP trio exists and is reachable over the LarePass mesh only
4. every tracked run that matters to promotion writes an `env` tag to `apex-jobs`
5. `forms-engine` has an installable Olares chart shell in the staging zone
6. at least one Stack Data Center canary lane exists and can be executed reproducibly

## 5. What Is In MVP

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

## 6. Workstreams

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

## 7. Sequencing Authority

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

## 8. Workflow Model

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

## 9. Technical Authority Rules

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

## 10. Immediate Next Packet

The next truthful implementation packet after this roadmap is:

1. `infra/compose.dev.yml`
2. `.env.dev.template`
3. `.gitignore` updates needed for the dev stack

That packet should establish the repeatable dev foundation before any MCP service is authored.

## 11. Success Standard

This roadmap is successful when it prevents two failure modes:

1. the Olares transition degenerating into ad hoc tool setup with no product-oriented sequencing
2. the build prompt being mistaken for the authority model rather than a bootstrap aid

If a future document or session treats the prompt as governance, correct the roadmap or framework and then realign the prompt.