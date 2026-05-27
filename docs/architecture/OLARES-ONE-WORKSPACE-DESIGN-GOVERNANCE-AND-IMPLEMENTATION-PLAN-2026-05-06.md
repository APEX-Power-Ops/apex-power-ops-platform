# Olares One Workspace Design, Governance, And Operating Model

Date: 2026-05-06 (originally authored)
v2 refresh: 2026-05-26 PM cycle 3 (matrix #69 substrate-currency refresh; absorbs 2026-05-06 → 2026-05-26 evolution)
Status: Active authority surface
Scope: current Olares One workspace constraints, governance rules, target environment, operator process, and bounded closeout routing

## Purpose

This document is the current stakeholder-facing authority for the Olares One workspace operating model.

It consolidates the current truth that is otherwise split across the Olares workspace framework, the post-closure Olares roadmap, the developer-host cutover plans, and the active packet chain.

Use this document when the question is:

1. what the Olares One workspace is supposed to be now,
2. what is constrained or forbidden,
3. which tools and processes are approved,
4. what remains to be aligned or improved,
5. how execution should continue without reopening already-closed lanes,
6. where the compact current lane register lives.

Repo-structure authority companion:

`docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`

Use that document when the decision is about the permanent repo shell, git boundary, authority relocation, or parent-root cutover.

Companion surface:

`docs/architecture/APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md` (v2 refresh applied 2026-05-26 PM cycle 3 per matrix #68; per-lane subsections + 8th lane for PM Schema substrate evolution)

Use that cockpit for rapid lane selection and validation routing. It does not override the authority order below.

Front-door workspace companions:

1. `docs/authority/WORKSPACE-REGISTRY-2026-05-23.md`
2. `docs/authority/REPO-PASSPORT-STANDARD-2026-05-23.md`
3. `REPO_PASSPORT.md`

AI orchestration + delegated-authority companion:

`docs/authority/APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md`

Use that protocol when the decision is about delegating execution to an AI agent (Desktop Claude / VS Code Copilot / Codex / CC), capability-gap surfacing duty (§7A — PATTERN-005 ancestor), PM-lane admitted-write authority (§7C), or AI-orchestration guardrails (§8).

**v2 refresh orientation note (2026-05-26 PM cycle 3):** lane-engagement orientation reports (PATTERN-007 discovery-first methodology; worked example at `C:/APEX Platform/.claude/PLATFORM/OLARES-WORKSPACE-ORIENTATION-2026-05-26.md`) are the recommended substrate for any session newly engaging the Olares Workspace authority chain or any drift-prone authority cluster. Read first, dispatch second.

## Current Program Decision

The Olares One is the durable development anchor for APEX.

That anchor is now also the governing migration direction for the whole program.

Repo structure now has explicit first priority inside that migration direction.

The remaining parent-root publication residue is now signed-off closeout provenance to preserve, demote further when needed, or later archive by explicit packet; it is not an acceptable steady-state repository model.

**Substrate-currency update (matrix #31 closure 2026-05-26):** parent-root `apps/+packages/` under `C:/APEX Platform/` archived to `_archive/Apr2026_PreTranche/`. Canonical operating boundary is now `apex-power-ops-platform/` nested inner repo + `source-domains/*`. Outer `C:/APEX Platform/` umbrella container is the workstation's `RESA-Power-Project-Management.git` clone but is **divergent indefinitely from origin per matrix #32 closure** — outer-repo umbrella IS itself a git repo (intentional dual-role per Dec 2025 cutover) but pushes to its `jasonlswenson-sys/RESA-Power-Project-Management.git` origin are NOT authorized at any horizon. Two-repo nested architecture is intentional operator design. Same pattern on Olares: `/home/olares/code/apex/` IS the RESA-Power-Project-Management.git clone (clean-main) and the active workspace container; canonical `apex-power-ops-platform/` nested within.

**Substrate-currency update (matrix #65 closure 2026-05-26 PM cycle 3):** PM Schema Foundation Plan v2 hybrid synthesis LANDED via Codex Cloud (`C:/APEX Platform/.claude/PLATFORM/PM_SCHEMA_FOUNDATION_PLAN_v2_2026-05-26.md`; 423 lines). v2 hybrid = public.* spine concepts (live production 125 base tables) + seam.* PM mutation/audit/revenue patterns (28 base tables; Lane 411 Rev A-C revrec architecture with "recognition firewall" load-bearing) + net-new `pm_core` namespace for NEW tables only per matrix #33 Q1 Option (c). Era 2.4 SQL packet sequence A-G (RLS first per v2 §15). Packets A + B AUTHORED + REVIEWED 2026-05-26 PM cycle 3 with operator decision walkthrough surfacing 6-role taxonomy correction (matrix #79 record) + Field Tech column-level read restriction (NEW design beyond Packet A scope; revision addendum at `.claude/PLATFORM/ERA_2_4_PACKET_A_REVISION_ADDENDUM_2026-05-26.md`). **Critical security advisory surfaced via v2 §2.2 SQL inspection** (matrix #66 + #78): 66 public + 11 seam.* tables have RLS DISABLED including core PM tables; per Supabase MCP advisory, anyone with the anon key can read or modify every row. Packet A RLS-policy authoring is now first-class prerequisite for live PM admission expansion.

At the current repo-owned evidence floor, that residue no longer blocks the laptop-to-Olares migration signoff.

All Apex Ops work top to bottom should converge on Olares-resident governance, execution, validation, toolchains, and operator context so the field laptop no longer carries durable project risk or accumulates divergent workspace practice.

That does not mean Olares is the canonical source of truth.

The current transitional authoritative split is:

1. GitHub remains the canonical origin.
2. `C:/APEX Platform/apex-power-ops-platform` is the canonical publication boundary for active Apex Ops repo work.
3. `/home/olares/code/apex/apex-power-ops-platform` is the authoritative host implementation surface.
4. `C:/APEX Platform` and `/home/olares/code/apex` are umbrella containers around that repo boundary rather than the default git roots (both are themselves clones of `jasonlswenson-sys/RESA-Power-Project-Management.git`; outer-workstation clone is divergent indefinitely per matrix #32; outer-Olares clone is the active workspace container per matrix #18 reframe).
5. `/home/olares/src/apex-power-ops-platform` is historical only and must remain observe-only. Pre-cutover `/src/` was archived to `/home/olares/archive/src-pre-cutover-2026-04-25/` per Path A 2026-05-23.
6. The laptop is a client surface, not the durable runtime anchor.

## Design Constraints

### Workspace boundary constraints

1. Treat `apex-power-ops-platform` as the independent git root for active repo operations.
2. Scope staging and publication to bounded repo-relative paths unless a deliberate broad repo publication is intended.
3. Do not mutate the historical host clone at `/home/olares/src/apex-power-ops-platform` (archived to `/home/olares/archive/src-pre-cutover-2026-04-25/`).
4. Keep secrets, mutable runtime data, and recovery artifacts outside the git workspace.
5. **(v2 addition)** Source-domain repos (`tcc_v5_backend`, `neta-ett-study-material`, `neta-forms`) live at `source-domains/<repo>/` subpath under the platform root; each has its own `.git/`. Treat as independent git roots for source-domain-specific commits + pushes.
6. **(v2 addition)** Per matrix #31 closure, parent-root `apps/+packages/` paths are archived; use `apex-power-ops-platform/apps/` + `apex-power-ops-platform/packages/` prefixes in all dispatches and operational references.

### Runtime and trust constraints

1. The admitted Olares-first AI/operator boundary remains `apex-fs`, `apex-db`, and `apex-jobs`.
2. `apex-jobs` is the run ledger and promotion gate. **(v2 inline definition)** `apex-jobs` records every bounded operator session run (start time + finish time + executor identity + scope + truthful outcome); promotion gates require successful prior runs of dependency lanes to be present in the ledger before a downstream lane proceeds.
3. Do not widen into `ai_tasks`, broader executor admission, or speculative AI-services rollout without a separate packet.
4. Preserve the distinction between local sandbox proof, workstation proof, and host proof.
5. Prefer truthful `HOLD`, `UNAVAILABLE`, or dormancy outcomes over fabricated readiness.
6. **(v2 addition)** Per matrix #2 closure (2026-05-25): Olares image-service GHCR authentication uses an operator-managed long-lived `read:packages` PAT stored in the `image-service-ghcr-auth` Kubernetes Secret (`os-framework` namespace; `containers/auth.json` format mounted at `/root/.config/containers/auth.json`; NOT `imagePullSecrets`). Replaces prior ephemeral PAT pattern. PAT rotation is out-of-band — never paste PAT into AI conversation context per MASTER.md § CREDENTIAL_HANDLING_PROTOCOL.

### Exposure and governance constraints

1. Keep Olares-hosted development and private-lane services behind the approved private or authenticated access model.
2. Do not use this workspace plan to authorize public ingress widening, canonical-hosting changes, or identity-model changes.
3. Keep GitHub canonical; Gitea remains mirror-only unless a separate transition packet approves otherwise.
4. Do not reopen dormant Olares branches without their published triggers.
5. **(v2 addition; matrix #66 security advisory)** Until matrix #66 Packet A RLS-policy cutover lands, the Supabase `public.*` + `seam.*` row gravity is exposed to anyone with the anon key. Do not introduce browser-side direct admission to either schema; do not author dispatches that assume RLS is enforced. Governed browser consumers must route through `apps/control-plane-api` (per cockpit Lane 4).

### Substrate-authoring constraints (v2 NEW)

These constraints govern PM-schema substrate work (Era 2.4 packet wave / RLS policy authoring / `pm_core` table design / revenue-recognition vocabulary).

1. **Recognition firewall principle (matrix #65 v2 §8; load-bearing):** operational actuals are NOT in the recognition data path. Frozen quote data is recognition source. `recognized_amount` is event-truth. "Actual revenue" is invalid recognition vocabulary. Lane 411 architecture (`seam.apparatus_financials` + `seam.project_contract_snapshots` + `seam.scope_labor_details` + `seam.apparatus_revenue_events`) preserves this firewall via insert-only event/snapshot discipline.
2. **`pm_core` namespace scope (matrix #33 Q1 Option (c)):** `pm_core` holds NEW tables only. Existing `public.*` + `seam.*` tables stay in their namespaces. No destructive renames. No replacement `pm_core.projects/scopes/apparatus/tasks` until a separately authorized later migration packet.
3. **Revenue-recognition scope (matrix #33 Q6):** PM substrate tracks revenue-recognition-tied-to-completion only. NOT full financial authority (AP / AR / GL / billing / payroll / invoicing / vendor management). Forward-extensibility note: if scope ever expands, `finance_core` sibling could be introduced later — but matrix #79 ratified `apex_finance` role REMOVED; revenue write authority folds into `apex_pm`.
4. **Identity/auth substrate (matrix #72 Option (c) hybrid):** Supabase Auth (`auth.users` + `auth.jwt() -> 'app_metadata' ->> 'apex_role'` claim path) is canonical identity source-of-truth for RLS claim evaluation. `seam.users` + `seam.user_roles` + `seam.user_role_audit` preserved as role-audit / read-model only — NOT destructively migrated. New `pm_core` tables reference `auth.users.id` (UUID) for `approved_by` / `submitted_by` / `reviewed_by` columns.
5. **6-role taxonomy (matrix #79 ratification):** `apex_pm` / `apex_operations` / `apex_field_lead` / `apex_field_tech` / `apex_admin` / `apex_estimator` + Supabase built-in `service_role` + restricted `anon`. Finance functions FOLD INTO `apex_pm`. Single-role-per-user start (array roles deferred). Field Tech read scope NARROWED: read all operational data EXCEPT hours/revenue/$ columns (column-level restriction via column GRANTs + VIEW hybrid).
6. **PATTERN-006 schema-closure verification:** before authorizing any RLS `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` cutover, dry-run + Supabase MCP `get_advisors` review + operator authorization. Schema closures based on prior synthesis are insufficient evidence for cutover — live substrate inspection required.

## Governance Rules

### Authority order

Use this order when documents conflict:

1. `docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`
2. `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`
3. `docs/architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md` (this doc; v2 refresh applied)
4. `docs/authority/APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md`
5. `docs/authority/WORKSPACE-REGISTRY-2026-05-23.md`
6. `docs/authority/REPO-PASSPORT-STANDARD-2026-05-23.md`
7. `plan/infrastructure-olares-full-implementation-roadmap-1.md`
8. `docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-TECHNICAL-PLAN-2026-05-05.md`
9. `docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-MILESTONE-PLAN-2026-05-05.md`
10. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md`
11. packet and handoff artifacts under `ops/agents/`

**v2 refresh note:** the protocol (2026-05-15) + registry (2026-05-23) + passport-standard (2026-05-23) are inserted into the authority order at positions 4-6 (previously listed only as front-door companions). The protocol governs AI delegation + capability-gap surfacing + PM-lane admitted writes; the registry + passport-standard govern source-domain enrollment + repo front-door contracts. Per orientation report §3F: these are governance-adjacent docs that resolve real conflicts and belong in the authority order, not merely as companions.

### Execution rules

1. All new Olares scope must be packetized when it changes tooling, runtime, install surfaces, hosting posture, or trust boundaries.
2. Each packet must define what changed, what was validated, what stayed deferred, and what boundaries were preserved.
3. Publication is not complete until `origin/clean-main` is updated from the standalone repo root and `/home/olares/code/apex/apex-power-ops-platform` is restored to clean parity.
4. Host proof is preferred for Olares-first claims whenever a bounded host validation exists.
5. Old evidence remains reference only after newer packet authority supersedes it.
6. **(v2 addition; PATTERN-005)** Every dispatched executor across all repos must surface what was working well, what wasn't, and how things could be enhanced. No prior artifact is sacred — matrix closures, plan drafts, methodology patterns themselves, dispatches, and references are all subject to continuous-improvement critique. Every dispatch wrapper authored from 2026-05-26 forward must include a §"What worked / What didn't / What could be enhanced" subsection requirement. Ancestor: protocol §7A Capability Gap And Best-Tool Duty (2026-05-15) + cockpit Operating Note #4 (2026-05-06).
7. **(v2 addition; PATTERN-007)** Discovery-first orientation before dispatch authoring: when engaging a new lane or drift-prone authority cluster, read across all candidate authority docs (or author/consult a lane-engagement orientation report) before authoring edit specifications. Worked example: `OLARES-WORKSPACE-ORIENTATION-2026-05-26.md` prevented authoring against a wrong premise (initial E3 finding claimed EXECUTOR governance was missing; discovery surfaced it already exists in protocol §4-§6).
8. **(v2 addition; PATTERN-008)** Session-state verification before state-changing operations: before any commit / push / state-changing dispatch, verify session state (uncommitted work / dirty inventory / parallel-execution authorization). Worked example: mystery Packet A+B execution discovery during commit prep was resolved via operator confirmation that parallel-execution was authorized — verification surfaced what could otherwise have been an unauthorized-looking deliverable.
9. **(v2 addition; PATTERN-006)** Schema-closure verification before SQL unblocking: a closure on prior synthesis is insufficient evidence to unblock SQL packet authoring or RLS cutover. Live substrate inspection (Supabase MCP `list_tables` / `pg_policies` query / `get_advisors`) is required before unblocking. Worked example: matrix #65 v2 synthesis (live SQL inspection during dispatch execution revealed structural gaps in v1 closures that prior synthesis missed).

### Operational truth rules

1. If the minimal MCP trio is not running, status surfaces must report that truth instead of implying readiness.
2. If deferred Operations Visibility views remain empty, the correct result is hold or dormancy, not synthetic consumer work.
3. If a host capability is absent and not required by current business truth, keep the lane closed instead of solving speculative gaps.
4. Do not normalize laptop-only or split-residency exceptions into the default Apex Ops operating model; every active lane should converge toward Olares-resident execution.
5. Treat any remaining parent-root publication language as historical residue, not as the desired permanent home for durable project practice.
6. **(v2 addition)** Chat is not state (per protocol §2). Tracked files, task packets, handoffs, validation artifacts, commits, and host-parity checks are state. In-conversation findings are transient until captured to repo. Operator-articulated decisions become governance only when written to the matrix or authority surface.

### Substrate-currency mechanism (v2 NEW)

Per orientation report §3B item 1 (no doc-currency mechanism in v1 plan):

1. **Substrate-currency check trigger:** any newly-engaged lane older than 14 days warrants a lane-engagement orientation read (PATTERN-007).
2. **Cross-doc cross-reference audit:** any matrix closure that affects multiple authority docs (e.g., matrix #65 v2 affects this plan + cockpit + protocol + registry) requires a Tier 1 minimum-edit freshness pass across affected docs before subsequent dispatches.
3. **Substrate-currency anchors:** each authority doc revision should explicitly anchor matrix item numbers it absorbs (this v2 refresh anchors matrix #2, #4, #28, #31, #65, #66, #72, #76, #77, #78, #79 + PATTERN-005/006/007/008).
4. **Freshness-date discipline:** "Current Implemented State" entries (see below) carry explicit dates so the operator can assess freshness at session-start.
5. **Discoverability-drift rule (cockpit Operating Note #4 ancestor):** if a current frontier cannot be summarized in the cockpit without rereading multiple packet chains, that is new discoverability drift and should be corrected as a bounded governance slice.

### PM cockpit companion

1. Use `docs/architecture/APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md` (v2 refresh applied 2026-05-26 PM cycle 3 per matrix #68) as the compact whole-project lane register and session-start routing surface.
2. If the cockpit conflicts with a governing document, the authority order above wins.
3. **(v2 addition)** Cockpit Lane 8 (PM Schema substrate evolution — Era 2.4 packet wave) routes substrate-authoring work (RLS policies / `pm_core` tables / revenue-recognition vocabulary) separately from Lane 5 (Governed PM route promotion). Cross-coordinate when promotion + substrate intersect.

## Optimal Workspace Environment

### Host environment

The optimal current workspace environment is an Olares-hosted, GitHub-canonical, standalone-repo-rooted development model.

The governing target is a whole-project Olares-first operating model with GitHub still canonical while the remaining umbrella-residue and documentation debt are retired one by one.

Authoritative host paths:

1. `/home/olares/code/apex/apex-power-ops-platform` (canonical platform repo; nested in active workspace container at `/home/olares/code/apex/`)
2. `/home/olares/apex-data`
3. `/home/olares/apex-secrets`
4. `/home/olares/apex-backups`
5. `/home/olares/archive/src-pre-cutover-2026-04-25/` (archived pre-cutover `/src/` clone per Path A; observe-only)

Required host characteristics:

1. durable repo mirror,
2. durable toolchain placement outside git,
3. stable private-mesh access,
4. host-resident validation capability for bounded slices,
5. recovery artifacts and operator surfaces that survive laptop disconnects.

### Client environment

The laptop should provide:

1. private-mesh SSH access,
2. VS Code Remote-SSH,
3. browser-delivered Olares desktop or browser-terminal fallback,
4. client access, review, approval, and emergency intervention only,
5. **(v2 addition)** Desktop Claude as primary technical authority for the Project domain (strategy / architecture / orchestration / packet authoring / decision-log discipline / state management per operating model). Operator-delegated execution authority on bounded scopes per protocol §5 + §7.

The laptop should not be the sole holder of:

1. active repo state,
2. long-running toolchains,
3. secrets,
4. mutable development state,
5. completion-critical validation context.

## Approved Tooling Stack

### Core development and validation tools

1. GitHub on `clean-main` as canonical origin.
2. VS Code plus Remote-SSH as the normal editing surface.
3. PowerShell on the workstation and Bash on the Olares host as operator shells.
4. Host-materialized `pnpm` under `/home/olares/apex-data/toolchains/pnpm-10.0.0/node_modules/.bin/pnpm`.
5. Host-materialized calc-engine Python under `/home/olares/apex-data/toolchains/calc-engine-venv/bin/python`.

### Approved Olares-first operator surfaces

1. `tools/ai/run-minimal-mcp-trio.ps1`
2. `tools/ai/run-minimal-mcp-trio.sh`
3. `tools/ai/run-olares-hold-boundary-check.ps1`
4. `tools/ai/run-olares-hold-boundary-check.sh`
5. `tools/ai/run-olares-host-bootstrap-status.sh`

### Approved AI boundary

1. `apex-fs`
2. `apex-db`
3. `apex-jobs`

### Default admitted AI runtime posture

1. The admitted minimal MCP trio remains operator-on-demand by default.
2. Normal Olares durable-host readiness does not require `apex-fs`, `apex-db`, and `apex-jobs` to remain running at rest between bounded operator sessions.
3. `tools/ai/run-olares-host-bootstrap-status.sh` is the controlling readiness surface for this posture: a clean authoritative mirror plus truthful `minimal_mcp.status = not-running` is a valid ready state, not a defect.
4. Open a separate durable-runtime admission packet only if a concrete operator insufficiency, unattended workflow requirement, or new validation obligation proves that operator-on-demand is no longer sufficient.

### Approved substrate-authoring tools (v2 NEW)

For PM-schema substrate work (Era 2.4 packet wave / RLS policy authoring / `pm_core` table design):

1. **Supabase MCP** — read-only schema/policy/advisory inspection (`list_tables` / `execute_sql` for `pg_policies` queries / `get_advisors`). Write access (`apply_migration` / `execute_sql` mutation) reserved for explicit cutover packets with operator authorization.
2. **Codex Cloud** — substantive substrate authoring (PM Schema Foundation Plan v2; Era 2.4 Packets A-G design); preferred for substantial deliverables matching its strengths (conventions / extraction / registry-shaped authoring / verification audits).
3. **PATTERN-006 schema-closure verification discipline** — required before authorizing any RLS cutover or destructive schema migration.
4. **`pg_policies` query** — read-only RLS policy audit (live substrate inspection rather than synthesis-from-prior-state).

Not approved by this plan:

1. broader AI-services expansion,
2. `ai_tasks` bridge widening,
3. speculative orchestration-service rollout,
4. canonical code-hosting transition,
5. **(v2 addition)** live RLS cutover (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`) without dry-run + Supabase MCP `get_advisors` review + operator authorization (PATTERN-006).

## Approved Operating Process

### Standard Olares-first change flow

1. Start from the current authority docs and latest packet frontier.
2. Select the smallest bounded slice that changes one real operator, workflow, or business constraint.
3. Implement only what that slice needs.
4. Validate the slice with the narrowest truthful executable check.
5. Publish bounded commits to `origin/clean-main`.
6. Restore `/home/olares/code/apex/apex-power-ops-platform` to clean parity.
7. Record the outcome in packet, handoff, roadmap, and status surfaces.

### Standard host-readiness flow

1. Run `Olares host bootstrap status` or `bash apex-power-ops-platform/tools/ai/run-olares-host-bootstrap-status.sh` from `/home/olares/code/apex`.
2. Or run `Olares host bootstrap status` or `bash tools/ai/run-olares-host-bootstrap-status.sh` from `/home/olares/code/apex/apex-power-ops-platform`.
3. Confirm canonical mirror head and clean status.
4. Confirm the old clone remains preserved and non-canonical.
5. Confirm materialized toolchains are present.
6. Confirm minimal MCP and hold-boundary posture before deciding whether a new packet is necessary.

### Standard AI-runtime decision rule

1. Treat `not-running` as the default steady-state posture for the admitted trio unless a later packet explicitly widens runtime expectations.
2. Use `run-minimal-mcp-trio` only for bounded operator sessions, verification, or cadence checks that actually need the trio online.
3. Do not promote the trio to always-on host baseline merely because the wrappers and host proof exist.
4. Reopen runtime admission only from concrete evidence, not convenience or drift anxiety.

### Standard substrate-authoring flow (v2 NEW)

For PM-schema substrate work (Era 2.4 packet wave / RLS-policy authoring / `pm_core` table design):

1. Start from the current PM Schema Foundation Plan v2 (`C:/APEX Platform/.claude/PLATFORM/PM_SCHEMA_FOUNDATION_PLAN_v2_2026-05-26.md`) + matrix #65 closure + the relevant Era 2.4 packet wrapper.
2. Verify live substrate state via Supabase MCP read-only inspection (PATTERN-006) — `list_tables` + `pg_policies` query + `get_advisors` — before authoring SQL or RLS policies.
3. Author SQL design files DESIGN-FIRST (no live mutations); apply to staging branch (Supabase branching) for dry-run; surface advisor findings + Codex `EXPLAIN PLAN` output as needed.
4. Surface 6-role taxonomy + Field Tech column-level restriction discipline in any new RLS policy authoring (matrix #79 record + revision addendum specifics).
5. Submit packet handoff + design + SQL files to operator for review-and-authorize cycle BEFORE any cutover (no auto-apply).
6. Cutover only after operator authorization + cutover-specific packet authoring; record in matrix as separate cutover-execution item.

### Standard dispatch-authoring flow (v2 NEW; PATTERN-007 codification)

For any session newly engaging a drift-prone authority cluster:

1. Read current authority docs across the cluster (or author a lane-engagement orientation report) BEFORE authoring dispatch edit specifications.
2. Cross-cut to adjacent authority docs to verify finding doesn't already exist somewhere (avoid duplicate work; avoid authoring against wrong premise per orientation report §9 item 1).
3. Author dispatch wrapper with pre-flight verification section (matrix #76 enhancement; verify all find-strings match target content before edit execution).
4. Include PATTERN-005 §"What worked / What didn't / What could be enhanced" subsection.
5. Use return-for-review pattern for CC dispatches (executor stops at handoff; Desktop reviews before any commits land).

## Current Implemented State

The following are already implemented and validated (freshness dates applied per orientation report §3B item 2):

1. **Olares host mirror and client-only laptop posture** — operational since 2026-04-25 cutover; verified 2026-05-22 via 4-way Blue Sky synthesis.
2. **Bounded host toolchain materialization** — pnpm + calc-engine venv per cutover plan; verified 2026-05-22.
3. **Resumed host-side validation slices** — operational; matrix #28 Phase 3 1A→1D arc verified 2026-05-26.
4. **Minimal MCP trio operator surface and host proof** — operational since plan v1 authoring (2026-05-06); verified 2026-05-22.
5. **Hold-boundary cadence surface with truthful workstation live-DSN proof and host graceful-degrade behavior** — operational; verified 2026-05-22.
6. **Host bootstrap/status operator surface with published host proof** — operational; verified 2026-05-22.
7. **Packetized publication and host parity discipline** — proven across 21+ matrix closures spanning 2026-05-21 → 2026-05-26.
8. **Default runtime governance that keeps the admitted minimal MCP trio operator-on-demand until a separate durable-runtime packet is justified** — operational since plan v1.
9. **(v2 NEW)** **Long-lived GHCR PAT model for image-service** — operator-managed `read:packages` PAT in `image-service-ghcr-auth` secret (operational since 2026-05-25 per matrix #2 closure).
10. **(v2 NEW)** **Parent-root archive operationalized** — `apps/+packages/` archived to `_archive/Apr2026_PreTranche/` 2026-05-25 per matrix #31 closure; canonical operating boundary anchored to `apex-power-ops-platform/`.
11. **(v2 NEW)** **5-repo workspace registry + 1-of-4 active passports** — `WORKSPACE-REGISTRY-2026-05-23.md` enrolled 2026-05-23; `apex-power-ops-platform` REPO_PASSPORT.md authored 2026-05-23; 3 source-domain passports pending matrix #67 enrollment campaign.
12. **(v2 NEW)** **PM Schema Foundation Plan v2 (matrix #65)** — landed 2026-05-26 PM cycle 3; hybrid synthesis (public.* + seam.* + pm_core for NEW tables only); Era 2.4 SQL packet sequence A-G defined; Packets A + B authored + reviewed.
13. **(v2 NEW)** **6-role taxonomy + identity hybrid (matrix #72/#79)** — `apex_pm/apex_operations/apex_field_lead/apex_field_tech/apex_admin/apex_estimator + service_role + anon` ratified; Supabase Auth canonical for RLS via `auth.jwt() -> 'app_metadata' ->> 'apex_role'`; seam.users preserved as read-model.
14. **(v2 NEW)** **8 methodology patterns active** — PATTERN-001 through PATTERN-008 in `METHODOLOGY_PATTERNS.md`; substrate-authoring discipline now formalized across multiple decision contexts.

## Post-Signoff Routing

### Phase 1: Keep the durable host baseline explicit

1. keep the host bootstrap/status surface as the first operator entry point,
2. keep packet, roadmap, and status authority aligned after each bounded slice,
3. prevent historical conceptual docs from being mistaken for current Olares governance,
4. **(v2 addition)** keep substrate-currency anchors current — each authority doc revision absorbs matrix item numbers it affects.

### Phase 2: Open follow-on hardening only where real friction remains

Candidate follow-ons must be chosen by evidence, not by aspiration.

Allowed next-slice classes:

1. docs-and-task discoverability improvements,
2. bounded host validation ergonomics,
3. truthful status or readiness surfaces,
4. publication/parity hygiene improvements,
5. compact lane-frontier surfaces that reduce repeated session-start reconstruction without widening scope,
6. **(v2 addition)** substrate-authoring (Era 2.4 packet wave; RLS-policy authoring; `pm_core` table design) per Cockpit Lane 8 routing,
7. **(v2 addition)** source-domain repo-passport enrollment per matrix #67 (3 source-domain repos: tcc_v5_backend / neta-ett-study-material / neta-forms).

Disallowed by default:

1. installs without a separate authority packet,
2. runtime/service mutation for convenience alone,
3. AI boundary widening,
4. generic infrastructure expansion,
5. **(v2 addition)** live RLS cutover without PATTERN-006 schema-closure verification + operator authorization.

### Phase 3: Reopen other lanes only on trigger

1. reopen deferred Operations Visibility only on live-data change or separately justified need,
2. reopen simultaneous-worker planning only on new evidence satisfying its trigger framework,
3. reopen hosting, Gitea, or broader AI-services only by separate packet,
4. **(v2 addition)** reopen TCC public-reference custody work (matrix #28 4th tier; 82 tables in `public.*`) only by dedicated matrix item with concrete operator-driven motivation.

## PM Routing Rule

The current PM rule is:

1. treat Olares as an active but bounded developer-residency and operator-hardening lane,
2. do not treat it as an always-open infrastructure epic,
3. execute adjacent workflow-hardening slices only when they reduce real operator burden or improve durable host correctness,
4. keep business delivery lanes separate from host-governance hardening unless a packet intentionally bridges them,
5. **(v2 addition)** route PM-schema substrate work (Era 2.4 / RLS / `pm_core` / revenue-recognition vocabulary) through Cockpit Lane 8 (PM Schema substrate evolution), not Lane 5 (Governed PM route promotion). Lane 5 promotes runtime through governed routes; Lane 8 authors the substrate those routes depend on.

## Success Standard

This plan is implemented successfully when:

1. the Olares host remains the durable development anchor,
2. the laptop remains client-only,
3. the approved operator surfaces expose current truth without hidden dependencies,
4. every new Olares-first change is packetized, validated, published, and host-resynced cleanly,
5. no stale document can reasonably be mistaken for the current Olares operating model,
6. **(v2 addition)** PM Schema substrate work proceeds via PATTERN-006 schema-closure verification + Supabase MCP read-only inspection + operator-authorized cutover packets — never via silent live mutations,
7. **(v2 addition)** every dispatch wrapper authored 2026-05-26 forward includes PATTERN-005 §"What worked / What didn't / What could be enhanced" subsection — continuous-improvement is mandate, not aspiration.

---

## v2 Refresh Substrate-Currency Anchors (NEW section)

This v2 refresh absorbs the following 2026-05-06 → 2026-05-26 substrate evolution (matrix items + patterns).

### Matrix items absorbed

| Matrix # | Title | Date closed | This v2 absorbs |
|---|---|---|---|
| #2 | Long-lived GHCR PAT replacement | 2026-05-25 | Design Constraint §Runtime and trust §6 + Current Implemented State #9 |
| #4 | seam.* vs public.* schema namespace | 2026-05-25; reframed 2026-05-26 via #65 | Substrate-authoring constraint §1-2 (hybrid synthesis posture) |
| #28 | tcc_v5_backend deprecation posture (+ 4th tier addendum) | 2026-05-26 PM cycle 2 (Phase 3 1A→1D); 4th tier addendum 2026-05-26 PM cycle 3 | Cockpit Lane 6 reference + Phase 3 §4 reopen-trigger constraint |
| #31 | Duplicate platform-copy routing (parent-root archive) | 2026-05-25 | Current Program Decision §substrate-currency update + Current Implemented State #10 + workspace boundary constraint §6 |
| #32 | Outer-repo push reconciliation strategy | 2026-05-26 | Current Program Decision §transitional split clarification (outer-repo divergent indefinitely) + Cockpit Lane 7 |
| #65 | PM Schema Foundation Plan v2 hybrid synthesis | 2026-05-26 PM cycle 3 | Current Program Decision §substrate-currency update + Cockpit Lane 8 + Current Implemented State #12 + entire substrate-authoring constraint section + standard substrate-authoring flow |
| #66 | Public + seam RLS policy authoring lane | 2026-05-26 PM cycle 3 (executed; revision pending) | Exposure and governance constraint §5 + Substrate-authoring constraint §6 + Phase 2 disallowed §5 |
| #67 | Repo-passport enrollment campaign | open as of 2026-05-26 PM cycle 3 | Current Implemented State #11 (partial; 3 passports pending) + Phase 2 allowed §7 |
| #68 | APEX-PM-LANE-OPERATING-COCKPIT v2 refresh | 2026-05-26 PM cycle 3 (this session) | PM cockpit companion §3 + cross-references throughout |
| #69 | OLARES-ONE plan v2 substrate-currency refresh | 2026-05-26 PM cycle 3 (this v2 refresh) | This entire v2 |
| #70 | Revenue vocabulary + `actual_revenue` disposition | partial closure 2026-05-26 PM cycle 3 | Substrate-authoring constraint §3 (write authority = `apex_pm`; legacy column disposition pending) |
| #71 | Lane 411 table custody decision | open | Substrate-authoring constraint §2 + Cockpit Lane 8 reopen-trigger |
| #72 | Identity/auth substrate (Supabase Auth + seam.users hybrid) | 2026-05-26 PM cycle 3 | Substrate-authoring constraint §4 + Current Implemented State #13 |
| #76 | Pre-flight verification template enhancement | open as of 2026-05-26 PM cycle 3 | Standard dispatch-authoring flow §3 |
| #77 | apex-power-ops-platform uncommitted backlog audit | open as of 2026-05-26 PM cycle 3 | (acknowledged; not absorbed into plan governance — separate audit/disposition matter) |
| #78 | Public broader-policy follow-on | open as of 2026-05-26 PM cycle 3 | Exposure and governance constraint §5 + Cockpit Lane 8 next-truthful-move |
| #79 | Packets A+B operator decision batch tracking (6-role taxonomy ratification) | 2026-05-26 PM cycle 3 | Substrate-authoring constraint §5 + Current Implemented State #13 |

### Methodology patterns referenced

| Pattern | Established | This v2 absorbs |
|---|---|---|
| PATTERN-005 | 2026-05-26 PM cycle 3 (formalized) | Execution rule §6 + ancestor cross-reference to protocol §7A + cockpit Operating Note #4 |
| PATTERN-006 | 2026-05-26 PM cycle 3 (from matrix #65 v2 synthesis) | Substrate-authoring constraint §6 + execution rule §9 + standard substrate-authoring flow §2 |
| PATTERN-007 | 2026-05-26 PM cycle 3 (from Olares orientation report worked example) | Execution rule §7 + standard dispatch-authoring flow §1-2 + purpose §"v2 refresh orientation note" |
| PATTERN-008 | 2026-05-26 PM cycle 3 (from mystery Packet A+B discovery worked example) | Execution rule §8 |

### Adjacent authority docs referenced

| Doc | Date | This v2 relationship |
|---|---|---|
| `APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md` | 2026-05-15 | Authority order position 4; AI orchestration + delegated-authority companion; ancestor to PATTERN-005 via §7A |
| `WORKSPACE-REGISTRY-2026-05-23.md` | 2026-05-23 | Authority order position 5; front-door companion |
| `REPO-PASSPORT-STANDARD-2026-05-23.md` | 2026-05-23 | Authority order position 6; front-door companion |
| `APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md` (v2 refresh 2026-05-26) | 2026-05-26 PM cycle 3 (v2 refresh) | Execution surface companion; Lane 8 routing reference |
| `OLARES-WORKSPACE-ORIENTATION-2026-05-26.md` | 2026-05-26 PM cycle 3 | Lane-engagement orientation PATTERN-007 worked example |
| `PM_SCHEMA_FOUNDATION_PLAN_v2_2026-05-26.md` | 2026-05-26 PM cycle 3 | Substrate-authoring reference (matrix #65) |
| `ERA_2_4_PACKET_A_RLS_POLICY_DESIGN_2026-05-26.md` | 2026-05-26 PM cycle 3 | RLS-policy design substrate |
| `ERA_2_4_PACKET_A_REVISION_ADDENDUM_2026-05-26.md` | 2026-05-26 PM cycle 3 | 6-role taxonomy + Field Tech column-level restriction (matrix #79) |
| `ERA_2_4_PACKET_B_PM_CORE_INTAKE_ENVELOPE_DESIGN_2026-05-26.md` | 2026-05-26 PM cycle 3 | pm_core namespace substrate (matrix #33 Q1 Option c) |
| `METHODOLOGY_PATTERNS.md` (outer-repo) | continuously updated | PATTERN-001 through PATTERN-008 |

---

*v2 refresh authored 2026-05-26 PM cycle 3 (matrix #69 closure). Original 2026-05-06 plan preserved in git history; v2 introduces substrate-currency updates throughout (matrix #2/#4/#28/#31/#32/#65/#66/#70/#71/#72/#79 absorbed + #67/#76/#77/#78 acknowledged), structural additions (substrate-authoring constraints + standard substrate-authoring flow + standard dispatch-authoring flow + substrate-currency mechanism + freshness dates on Current Implemented State + apex-jobs inline definition + v2 Refresh Substrate-Currency Anchors section), methodology pattern cross-references (PATTERN-005/006/007/008 + ancestors), and authority order expansion (8 → 11 docs to include protocol + registry + passport-standard). Per orientation report §4A E7 scope guidance: scope reduced from initial estimate by leveraging adjacent doc cross-references rather than duplicating content (e.g., EXECUTOR governance referenced in protocol §4-§6 rather than duplicated here).*
