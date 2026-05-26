# PROTOCOLS_AND_NOMENCLATURE.md

Status: Accepted by Desktop Claude 2026-05-23; effective immediately
Date: 2026-05-23 (§9 amended with verified ledger schema 2026-05-23; §10 amended 2026-05-25 to register `apex-p6` and admit `apex-forms`; §11 occupied-names table extended 2026-05-23 to add `apex-power-ops-platform | .github/copilot-instructions.md` after Era 3.1 re-dispatch surfaced it as legacy-occupied)
Scope: Framework-level conventions for the APEX workspace constellation

## 1. Purpose, scope, and authority position

This document is the canonical workspace conventions reference for the APEX repo constellation. It governs packet, handoff, ledger, MCP, role, environment, and naming conventions shared across enrolled repos.

This is a framework-level conventions document. Repo-specific governance lives in each repo's `.claude/MASTER.md`, `REPO_PASSPORT.md`, and the repo-specific authority files named by that passport.

Every enrolled repo's `.claude/MASTER.md` cites this document in its authority order. `WORKSPACE-REGISTRY-2026-05-23.md` cites it as the cross-repo conventions reference for packetized workspace execution.

This document supersedes earlier framework-level conventions material where conflicts exist. Supersession is explicit, not by deletion: older docs remain provenance, while current routing points here for shared conventions.

Audience:

| Audience | Use |
|---|---|
| Operator | Confirms the shared workspace grammar and resolves exceptions |
| Desktop Claude | Uses this as synthesis and review authority |
| VS Code Claude | Uses this for repo-local activity conventions |
| Codex | Uses this for packet execution, authoring, validation, and handoff shape |
| Claude Code / Cowork Claude | Use this when operating inside the repo constellation |
| VS Code Copilot | Uses this through `.github/copilot-instructions.md` shims |
| Future local AI | Uses this only after explicit admission and data-class gating |

This document does not define platform business rules, schema design, product personas, or source-domain content policy. It defines how executors coordinate while those things are designed and built.

## 2. Repo identity and source-domain vocabulary

The workspace constellation separates repo identity by responsibility:

| Classification | Repo id | Meaning |
|---|---|---|
| Platform substrate | `apex-power-ops-platform` | Platform substrate, operator workflow surface, shared governance, MCP family, ledger, and cross-repo packet home |
| Source-domain | `tcc_v5_backend` | Calculation engine and associated integration surface |
| Source-domain | `neta-ett-study-material` | Study content, governance, and planning surface |
| Source-domain | `neta-forms` | Form-template and generation-asset surface |
| Future-reserved | `pss` | Reserved domain, not enrolled until a later packet admits it |

Repo identity is declared by each repo's root `REPO_PASSPORT.md`. The passport standard is `docs/authority/REPO-PASSPORT-STANDARD-2026-05-23.md`; it defines the 12-section front-door contract and quality rules.

Workspace enrollment is declared by `docs/authority/WORKSPACE-REGISTRY-2026-05-23.md`. The registry is the controlling list of active, provisional, historical, and not-enrolled repos in the C:\-side workspace constellation.

Canonical data-class vocabulary is referenced from the passport standard and registry:

| Data class | Meaning boundary |
|---|---|
| `public` | Safe to publish or broadly share |
| `internal` | Workspace-internal operating material |
| `customer-sensitive` | Customer or project material requiring controlled handling |
| `ip-core` | Proprietary logic, source-domain content, or platform moat material |

Canonical repo-status vocabulary:

| Status | Meaning |
|---|---|
| `active` | Enrolled and carrying an active passport |
| `provisional` | Registered but not fully passported |
| `historical` | Preserved for provenance, not an active work surface |
| `not-enrolled` | Reserved or mentioned, but outside the active constellation |

Allowed executor classes are declared per repo in the workspace registry. The vocabulary includes human operator, VS Code Copilot, Desktop Claude, Codex, VS Code Claude, Cowork Claude, Claude Code, and local AI.

`D:\apex-power-ops-platform` is a separate workspace constellation. It is not enrolled in the C:\-side workspace registry. Its own `.claude/STATE.md` and handoff conventions remain in place unless a future cross-workspace registry packet changes that boundary.

## 3. Authority hierarchy + supersession protocol

Framework authority order for workspace conventions is:

1. `PLATFORM_VISION_NORTH_STAR.md`
2. `PLATFORM_DESTINATION_2026-05-22.md`
3. `PLATFORM_ROADMAP_2026-05-22.md`
4. This document, `PROTOCOLS_AND_NOMENCLATURE.md`
5. Repo-level `.claude/MASTER.md`
6. Operator instruction

Repo-specific authority order is declared in that repo's `REPO_PASSPORT.md` section 3, "Authority order." The repo passport names legacy-tolerated files, governing-rules files, state surfaces, and local authority references without forcing filename migration during scaffolding.

Supersession is explicit. A newer document should not silently erase the older one; it should add a closeout interpretation note and current routing section that tells future readers which surface is active and why.

The preferred supersession header style is:

```markdown
Closeout interpretation note:

This document remains provenance, but current execution routing now flows through <current surface>.

Current routing:

1. use <current doc> for <current purpose>,
2. use <older doc> only for <historical/provenance purpose>.
```

When a document is superseded for active work, preserve it unless the packet explicitly authorizes removal. Deletion is not a supersession mechanism.

## 4. Packet contract

Every substantial task should have a machine-readable packet plus an optional human brief. Packets make executor work claimable, reviewable, and resumable without relying on chat memory.

The canonical packet field set is:

| Field | Purpose |
|---|---|
| `packet_id` | Stable packet identifier |
| `title` | Human-readable packet name |
| `objective` | Concrete outcome the packet exists to produce |
| `domain` | Platform, source-domain, workspace, Olares, PM, docs, or other declared domain |
| `active_role` | Current role executing or authoring the packet |
| `repo_paths` | Absolute repo paths and relevant host paths |
| `dependencies` | Upstream packet, doc, service, or decision dependencies |
| `required_inputs` | Files, artifacts, prompts, or evidence required before execution |
| `constrained_outputs` | Authorized output files or artifact classes |
| `write_scope` | Explicit write boundary and non-goals |
| `validation_steps` | Required checks before closeout |
| `handoff_target` | Where the closeout or next handoff lands |
| `status` | Lifecycle state |
| `created_at` / `updated_at` | Timestamp pair |

This document treats `created_at` and `updated_at` as a paired timestamp field, counting them as one field in the 14-field framing. If a future convention pass prefers to count them individually as 15 fields, the field set is identical; only the count label differs.

Canonical lifecycle statuses:

| Status | Meaning |
|---|---|
| `draft` | Not yet ready to claim |
| `ready` | Ready for an executor |
| `claimed` | Claimed by an executor but not yet actively changing state |
| `in_progress` | Execution underway |
| `blocked` | Cannot proceed without a named unblock |
| `review` | Ready for review or acceptance |
| `accepted` | Accepted as complete |
| `archived` | Preserved as completed or obsolete history |

Packets must name both what is allowed and what is not allowed. Ambiguous write authority is a stop condition, not an invitation to infer.

## 5. Packet lifecycle + `ops/agents/` layout

The canonical agent operations layer lives under `ops/agents/` in enrolled repos.

Full layout vocabulary:

```text
ops/agents/
|-- packets/
|   |-- draft/
|   |-- active/
|   |-- blocked/
|   |-- review/
|   |-- done/
|   `-- archive/
|-- handoffs/
|-- inbox/
|-- policies/
|-- logs/
`-- indexes/
```

Mandatory-core directories for every enrolled repo:

| Directory | Required? | Purpose |
|---|---:|---|
| `ops/agents/packets/draft/` | Yes | Packet drafts not ready to claim |
| `ops/agents/packets/active/` | Yes | Active and claimable packets |
| `ops/agents/packets/blocked/` | Yes | Packets stopped on named blockers |
| `ops/agents/packets/review/` | Yes | Packets awaiting review or acceptance |
| `ops/agents/packets/done/` | Yes | Completed packet records |
| `ops/agents/packets/archive/` | Yes | Obsolete or historical packet records |
| `ops/agents/handoffs/` | Yes | Repo-local handoffs and closeouts |
| `ops/agents/policies/` | Yes | Repo-local policy or executor policy files |

Optional-rest directories are created when needed:

| Directory | Trigger |
|---|---|
| `ops/agents/inbox/` | The repo needs an intake queue |
| `ops/agents/logs/` | The repo emits executor or service logs worth tracking |
| `ops/agents/indexes/` | The repo generates indexes or derived navigation artifacts |

Empty mandatory-core directories should be populated with `.gitkeep` during propagation so the layout exists from line one. Optional-rest directories should not be pre-stamped without a real use.

## 6. Handoff convention

Handoffs let a new executor continue work without reading a long chat transcript.

Canonical filename pattern:

```text
YYYY-MM-DD-<lane-or-topic>-<purpose>-handoff.md
```

Repo-local handoffs land in `ops/agents/handoffs/` unless the repo passport declares a different legacy-tolerated handoff surface.

Framework-level handoffs land in:

```text
C:\APEX Platform\.claude\PLATFORM\HANDOFFS\
```

The framework handoff surface uses the same filename pattern.

Recommended handoff header schema:

```yaml
packet_id: <packet id or source prompt path>
from: <executor/source>
to: <reviewer/next executor>
repo: <repo id or framework>
env_required: sandbox|host|none
mcp_scope: apex-fs|apex-db|apex-jobs|none|other-declared
references:
  - <path or packet id>
```

Minimum handoff content:

| Field | Meaning |
|---|---|
| Source packet | Packet or prompt path that authorized the work |
| Current state | What landed and where |
| Blockers | Exact blockers or `none` |
| Next step | Next executable step |
| Files changed | Paths changed by the packet |
| Validations completed | Checks actually run |
| Validations still required | Review, acceptance, host proof, or unrun checks |

For `D:\apex-power-ops-platform`, handoffs stay at `.claude/HANDOFFS/` per the GATE-A resolved constraint and that workspace's own authority declaration. The function is reconciled without forcing a filename or path migration.

## 7. Standing roles + executor admission

The canonical standing-role model has five roles:

| Role | Responsibility |
|---|---|
| Technical repo authority | Owns repo boundary discipline, architecture fit, validation expectations, and publication readiness |
| Project manager | Chooses sequencing, decomposes bounded slices, synchronizes PM and orchestration lanes, and protects the queue from churn |
| Coordinator | Authors packets and prompts, assigns bounded work, and tracks outputs |
| Reviewer and release gate | Audits diffs, validates claims, decides acceptance, and controls closeout |
| Executor | Implements directly when a slice is small, urgent, cross-cutting, or too context-sensitive to delegate efficiently |

One human or AI may occupy multiple roles for one tranche, but the active role must remain legible in the packet or handoff.

Default executor admission:

| Executor class | Default posture |
|---|---|
| Desktop Claude | Primary technical authority over the Project domain as a whole |
| VS Code Claude | Repo-level activity authority when working inside the IDE/repo context |
| Codex | Bounded executor unless a packet assigns a narrower review, planning, or authoring role |
| Claude Code | Bounded executor unless a packet assigns a narrower role |
| VS Code Copilot | Bounded repo-local executor according to repo passport |
| Cowork Claude | Bounded planning, synthesis, or execution surface according to packet |
| Future local AI | Not admitted until a packet defines data class, role, and validation boundary |

Historical appendix: the older six-role model from `MULTI-AGENT-OPERATING-MODEL-2026-04-12.md` remains reference-only. It named Platform Architect, Product Implementer, Data Steward, Forms and Document Engineer, Automation Operator, and Reviewer and Release Gate. The five-role model above is canonical going forward.

Mapping from the older six-role language:

| Older role | Canonical role usually absorbing it |
|---|---|
| Platform Architect | Technical repo authority |
| Product Implementer | Executor |
| Data Steward | Technical repo authority or executor, depending on packet |
| Forms and Document Engineer | Executor, with domain-specific validation |
| Automation Operator | Coordinator or executor |
| Reviewer and Release Gate | Reviewer and release gate |

## 8. `env=sandbox|host` trust contract + promotion gates

Every `apex-jobs` ledger run carries a mandatory `env` value of `sandbox` or `host`.

`env=sandbox` means the run originated from development, local, compose, or other non-promoted execution. Dev-zone runs cannot claim host proof. The dev compose stack is hardcoded as sandbox for this purpose.

`env=host` means the run closed from a host-promoted runtime. At current foundation state, host evidence requires Olares staging-zone proof, typically through OlaresManifest-packaged staging surfaces or an explicitly admitted host runtime.

Sandbox completion is useful implementation evidence. It is not end-to-end promotion evidence.

Canonical promotion gates:

| Gate | Evidence requirement |
|---|---|
| Source | Canonical repo path, commit or working-tree identity, packet authority, and bounded write scope |
| Build | Artifact, image, package, or deterministic build evidence tied to the source state |
| Host | Closed `env=host` run from an admitted host-promoted runtime |
| Backup | Required ledger and state artifacts are inside the admitted backup posture or explicitly deferred by packet |
| Rollback | Prior state, rollback route, or safe recovery plan is named |
| Closeout | Handoff, validations, ledger event, and state-update expectations are complete |

`promote_packet` refuses without at least one closed `env=host` run for the `packet_id`. That refusal belongs at the MCP-server level, not merely in human convention.

The three-zone realization is:

| Zone | Trust role |
|---|---|
| Dev zone | Produces `env=sandbox` implementation evidence |
| Services zone | Hosts control-plane services and support state; not a junk drawer |
| Staging zone | Produces host-origin product or service promotion evidence |

Current Olares synthesis locks Docker `apex-dev` compose as the canonical dev-zone MCP serving runtime. OlaresManifest packaging is the graduation path to staging-zone host truth. Direct host Node MCP processes are decommission targets after audit, canonical-capability verification, switchover with paused writes, and cleanup.

## 9. `apex-jobs` ledger interface

The `apex-jobs` ledger is the workspace execution-truth interface. It records runs, packet linkage, environment claims, closeout state, validation references, and promotion evidence. It is not merely a storage file.

GATE-B Option A is resolved as Olares-side local-tier SSD only, for now. The ledger interface remains GATE-B-agnostic: it admits Option A and a future Option B without changing the logical contract.

### 9.1 Logical contract

Every ledger event must be able to answer:

| Question | Required answer |
|---|---|
| What work? | Run id and packet linkage |
| Who/what executed? | Executor and active role |
| Under what trust class? | `env=sandbox` or `env=host` |
| What happened? | Status and closeout result |
| When? | Created/updated or event timestamps |
| With what proof? | Validation references and handoff references |
| Can it promote? | Promotion gate evidence or refusal reason |

### 9.2 Verified field schema

Field schema verified against `services/mcp/apex-jobs/` source code on 2026-05-23 (see `.claude/PLATFORM/PHASE_0/APEX_JOBS_LEDGER_SCHEMA_INVENTORY_2026-05-23.md`). Ledger top-level shape: `runs: LedgerRun[]` and `promotions: LedgerPromotion[]`; both initialize to `[]` when the ledger file is absent.

Run record fields (snake_case):

| Field | Type | Required | Origin |
|---|---|---|---|
| `run_id` | string | yes | service-generated at `start_run` |
| `env` | `"sandbox" \| "host"` | yes | caller-supplied at `start_run` |
| `service` | string | yes | caller-supplied at `start_run` |
| `packet_id` | string | no | caller-supplied at `start_run` |
| `status` | `"running" \| "success" \| "failure" \| "canceled"` | yes | `running` at start; closed status on end |
| `created_at` | ISO timestamp string | yes | service-generated at `start_run` |
| `notes` | string | no | caller-supplied at `end_run` |
| `completed_at` | ISO timestamp string | yes on closed runs | service-generated at `end_run` |

Promotion record fields (snake_case):

| Field | Type | Required | Origin |
|---|---|---|---|
| `packet_id` | string | yes | caller-supplied at `promote_packet` |
| `promoted_at` | ISO timestamp string | yes | service-generated |
| `supporting_run_ids` | string[] | yes | service-derived from successful `env=host` runs for the packet |

Notes on the verified contract:

- `env` is caller-supplied at request time; the service does not currently read `APEX_ENV`. The Olares foundation synthesis describes dev compose hardcoding `APEX_ENV=sandbox` as the caller environment; binding the service runtime to also read `APEX_ENV` directly is a future implementation packet.
- Run-status enum (`running` / `success` / `failure` / `canceled`) is distinct from the broader packet-lifecycle status set in section 4. Run status tracks a single ledger event; packet lifecycle status tracks a packet across its life.
- `service` is the current implemented service/executor-surface field. First-class executor identity and role fields are future schema extensions; until admitted, executor and role identity flow through `service` plus packet linkage.
- `supporting_run_ids` is the current promotion-evidence pointer. The six-gate promotion-evidence framework in section 8 is the conventions-layer trust contract; binding each gate to first-class structured fields in the ledger is a future schema extension.
- The service parses and casts the ledger JSON without read-time schema validation. Adding read-time validation is a future implementation packet.

### 9.3 Future schema extensions (carry-forwards)

The following extensions are admitted into the contract conceptually but require packetized admission before becoming first-class fields:

1. **Executor identity field.** A dedicated executor field separate from `service`. Triggered when multi-instance role accountability requires it.
2. **Active-role field.** A dedicated role field aligned with the five standing roles in section 7. Triggered when role-aware ledger filtering becomes operationally necessary.
3. **Structured validation-reference field.** Replaces or supplements free-form `notes` for closeout evidence linkage. Triggered when validation audit traceability becomes operationally necessary.
4. **Six-gate promotion-evidence structure.** First-class fields for each of source, build, host, backup, rollback, closeout gates per section 8. Triggered when promotion audit requires structured evidence beyond `supporting_run_ids`.
5. **`APEX_ENV` runtime binding.** Service-side env-tag derivation from `APEX_ENV` in addition to caller-supplied values. Triggered when sandbox-host enforcement should be structural rather than honor-based.
6. **Read-time JSON schema validation.** Service-side validation of existing ledger records on read. Triggered when ledger drift detection becomes operationally necessary.

### 9.4 Write and correction contract

The ledger is append-only by default. Corrections are new events, not in-place mutation of prior truth. A bad closeout remains visible and is corrected by an explicit follow-up event.

Promotion operations refuse without at least one closed `env=host` run for the packet id. Refusal is recorded as operational truth, not hidden in chat.

Physical storage is runtime-resolved. Current discovered storage is:

```text
/home/olares/code/apex/apex-power-ops-platform/.apex-data/apex-jobs-ledger.json
```

Under Gate-B Option A, the first mandatory backup scope is:

```text
/mnt/apex-backup/restic/apex-jobs-ledger/
```

The ledger contract must survive physical relocation, Docker-to-host switchover, and future OlaresManifest graduation.

## 10. MCP family bounds + three-surface topology

The bounded MCP family is:

| Server | Boundary |
|---|---|
| `apex-fs` | Bounded filesystem access across declared roots |
| `apex-db` | Bounded database access under no-live and substrate authority |
| `apex-jobs` | Ledger, runs, packets, handoffs, and promotion evidence |
| `apex-p6` | Bounded bridge over the admitted `packages/p6-ingest` runtime status and Stack fixture surfaces |
| `apex-forms` | Bounded forms-engine template inventory, inspection, validation, and sandbox render-preview |

New MCP servers are packetized decisions, not accumulation. Each proposed addition must declare:

1. why the existing trio cannot cover the need,
2. the new server's authority boundary,
3. the trust contract it enforces,
4. its backup and restore story.

Current MCP-config topology has three surfaces:

| Surface | Location | Scope | Notes |
|---|---|---|---|
| Per-user stdio MCPs | `~/.claude.json` `mcpServers` | Operator/user scoped | Not repo-propagated |
| Repo-root HTTP MCPs | `<repo-root>/.mcp.json` | Repo scoped when present | Optional per repo, declared in repo MASTER |
| Claude.ai OAuth-brokered integrations | `~/.claude/mcp-needs-auth-cache.json` and related user cache | User scoped by OAuth construction | Not repo-propagated |

Examples of per-user stdio MCPs may include server names like `MCP_DOCKER`, `tcc-fidelity-staging`, or `playwright`, but values and credentials are not surfaced.

The observed repo-root HTTP MCP example is the NETA ETT `supabase` server advertisement. Repo-root config names server ids only in documentation unless a packet explicitly authorizes config inspection.

Server names should remain disjoint across surfaces. If a same-name collision occurs later, repo-root config wins for that repo because it is the repo's declared working context.

### 10.1 `apex-p6` registration note

`apex-p6` was present at canonical `services/mcp/apex-p6/` before this amendment and is registered here as an admitted family member. This amendment does not rebase, rewrite, or widen the service source. Its boundary is the bounded schedule-ingest bridge already represented by the canonical service: runtime status, admitted Stack fixture summary, and live-lane task-code inspection.

### 10.2 `apex-forms` admission declarations

`apex-forms` is admitted by packet `APEX_FORMS_MCP_ADMISSION_2026-05-25` as a fresh canonical-lineage service, not as mechanical extraction from `/src/`.

#### Declaration 1 - Why the existing trio cannot cover the need

`apex-fs` provides bounded filesystem access: file reads and writes within declared roots. It cannot interpret form templates, validate template structure, or render template output. A consumer wanting "list available MOP templates with their applicable apparatus types and render a preview for transformer testing" via `apex-fs` would need to list filesystem paths, manually parse each template file, and manually invoke the forms-engine runtime to render. That is a non-trivial composition that every consumer would re-implement.

`apex-db` provides bounded database access under no-live and substrate authority. Form templates are repo-curated assets, not database-backed; `apex-db` has no surface for template inventory, validation, or rendering.

`apex-jobs` is the ledger: runs, packets, promotions, evidence. It records that work happened; it does not perform work. Template-related work may be invoked through forms-engine and recorded in `apex-jobs`, but `apex-jobs` is not the template surface.

Conclusion: the existing trio cannot cover programmatic forms-engine template access. `apex-forms` fills a genuine bounded-domain gap.

#### Declaration 2 - The new server's authority boundary

`apex-forms` may:

- read the forms-engine template inventory: list templates, get template metadata, and get template content for inspection;
- validate template structure against the `neta-forms` authority surfaces, including `C:\APEX Platform\source-domains\neta-forms\REPO_PASSPORT.md` and `C:\APEX Platform\source-domains\neta-forms\.claude\MASTER.md` sections 10-15;
- render previews through forms-engine runtime bindings when the service is operating under `env=sandbox`.

`apex-forms` may not:

- write template source files;
- perform production rendering for customer delivery;
- write to platform databases;
- call `apex-jobs` or `apex-db` as an internal chain;
- activate itself through Docker compose, K3s, Olares Application, AppImage, GHCR publication, or registry mutation.

Service activation remains a separate operator-authorized packet.

#### Declaration 3 - The trust contract it enforces

`env=sandbox` is the default and only state admitted by the admission packet. In sandbox, `apex-forms` renders against local or canonical working-tree templates and local forms-engine runtime bindings. It cannot claim host proof.

`env=host` is future-only for `apex-forms`. A later activation packet must prove source commit, build artifact, host runtime health, backup coverage, rollback path, and closeout evidence before `apex-forms` may emit or advertise `env=host`.

Host promotion must not reuse ad hoc registry or auth assumptions. The 2026-05-25 AppImage Option 2 repair proved that Olares `image-service` uses containers-style auth material mounted at `/root/.config/containers/auth.json`, that private GHCR artifacts can drift or be absent, and that steady-state registry access should use a dedicated operator-managed `read:packages` credential rather than transient CLI credentials.

Promotion gates per section 8 apply when a future activation packet is authorized:

| Gate | `apex-forms` evidence requirement |
|---|---|
| Source | Canonical repo at named commit |
| Build | `apex-forms` image or runtime artifact at named tag |
| Host | `env=host` runtime closed and observed healthy |
| Backup | Source and required mutable state in Gate-B local-tier SSD Restic scope |
| Rollback | Prior known-good image/tag or deactivation path |
| Closeout | Ledger event written through `apex-jobs`, or handoff-bound evidence if ledger write is not yet admitted |

The bounded-family rule remains: `apex-forms` is admitted as a new family member; further MCP additions remain packetized decisions.

#### Declaration 4 - Backup and restore story

`apex-forms` is stateless. It reads templates from the source-domain repo and invokes forms-engine for preview work. It does not own durable data, queues, databases, or customer-deliverable storage.

Template authority lives in `C:\APEX Platform\source-domains\neta-forms\`, and the forms-engine runtime lives in `apex-power-ops-platform/packages/forms-engine/`. Under current Olares foundation synthesis Gate-B Option A, the first mandatory backup tier is Restic to the Olares local-tier SSD, with future offsite extension handled separately. This admission does not widen backup scope; it requires future activation work to confirm source paths are inside the admitted backup posture or surface the gap.

Render-preview outputs are disposable unless a caller explicitly promotes them into a packet artifact. Temporary preview files are not system-of-record material and should be garbage-collectable.

Restore path: restore canonical source from Git or Gate-B backup, restore `neta-forms` template source from Restic/local-tier snapshot, rebuild or reinstall `apex-forms` from canonical source, and re-run validation. No data migration, schema migration, or state reconciliation is expected.

## 11. Naming + equivalence rules

The canonical filename inside `.claude/` is:

```text
MASTER.md
```

Scope disambiguates identical names:

| Scope | Path |
|---|---|
| Framework MASTER | `C:\APEX Platform\.claude\PLATFORM\MASTER.md` |
| Repo MASTER | `<repo>/.claude/MASTER.md` |

Root shims are pointer files only:

| Shim | Native audience |
|---|---|
| `AGENTS.md` | Codex, newer Claude Code, VS Code Claude, and broad agent tooling |
| `.github/copilot-instructions.md` | VS Code Copilot |

Each shim should be 5-10 lines of pointer content to `.claude/MASTER.md`. Substantive governance belongs in `.claude/MASTER.md`, not in a shim.

Where shim names are already occupied by legacy content, Era 3.1 does not touch the legacy file. Known occupied names include:

| Repo | Legacy-tolerated content |
|---|---|
| `apex-power-ops-platform` | Root `AGENTS.md`; `.github/copilot-instructions.md` (2,673 B, 2026-05-07; substantive RESA-era governance file — not a shim; shim conversion deferred to apex-power-ops-platform audit packet) |
| `neta-forms` | Root `CLAUDE.md` |
| `neta-ett-study-material` | Root `MASTER-STANDARDS.md` and `GOVERNANCE-FRAMEWORK.md` |

Passport section 3 names each legacy file as legacy-tolerated. Future per-repo audit packets decide what content migrates into `.claude/MASTER.md`, what retires, and what remains as legacy.

Function-not-filename principle: the skeleton declares what function each file performs. A repo may preserve a legacy governing-rules filename while the passport names that function explicitly.

Scaffold-then-audit principle: Era 3.1 lands universal scaffolding additively. Later per-repo audit packets migrate or retire existing content deliberately.

## 12. Credential handling, Capability-Gap Duty, and discipline patterns

Credential handling is governed by `C:\APEX Platform\.claude\PLATFORM\MASTER.md` section `CREDENTIAL_HANDLING_PROTOCOL`. Do not duplicate that protocol into repo-local files in a way that can drift.

In brief: production credentials never enter AI conversation context; AI assistants reference credentials by environment variable name only; AI assistants do not read env files containing production credentials; `.env.example` is the safe env-shape surface; if a credential is pasted into chat, stop and surface the compromise without echoing the value.

Platform credentials do not migrate to Vault until a Vault restore plan exists. Vault may remain deployed as workspace infrastructure, but it is not admitted as the platform secret store by implication.

Capability-Gap Duty: an executor must not silently continue with a materially suboptimal path when a missing tool, unavailable connector, absent credential, stale deployment, platform limitation, or MCP gap blocks the best execution path.

When Capability-Gap Duty triggers, the executor must:

1. disclose the gap in the tranche or handoff,
2. name the missing or degraded capability directly,
3. state whether the fallback is acceptable or the slice should stop,
4. recommend the best available tool or admission path when known,
5. avoid normalizing temporary fallbacks into the permanent model without a packet.

Cross-repo execution must remain packetized whenever it changes more than one repo or changes a shared contract. This is Workspace Registry Rule 4 and is repeated here because it is load-bearing for executor safety.

Discipline patterns are cited by reference from `C:\APEX Platform\.claude\PLATFORM\METHODOLOGY_PATTERNS.md`:

| Pattern | Convention impact |
|---|---|
| PATTERN-001 | Use parallel-run packets for high-stakes design decisions |
| PATTERN-002 | Treat deployed state as context, not constraint |
| PATTERN-003 | Scaffold first, then audit and backfill deliberately |

Closed-clean discipline applies to all packeted work: bounded scope, smallest truthful validation, explicit handoff, no hidden failed checks, no unrelated edits, and no silent state drift.
