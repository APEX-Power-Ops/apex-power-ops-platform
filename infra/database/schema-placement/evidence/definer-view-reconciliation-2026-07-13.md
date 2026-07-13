# Definer-view reconciliation — Phase 8 (PROVISIONAL, offline)

2026-07-13 · disposition-ledger lane · operator GO "Phase 8 only" (corrected under GO "Phase 8C only") · **stops for Phase 8R operator ratification**

## Scope and standing disclaimers

- OFFLINE reconciliation only: no database, production, external-API, overlay-collection, signing, or SQL action was taken.
- Every disposition below is a PROVISIONAL PROPOSAL. This artifact creates **no accepted decisions and no accepted cluster manifest**.
- All six evidence dimensions — `in_data_api_exposed_schema`, `advisor_findings`, `static_repo`, `runtime_logs`, `external_clients`, `operator_declaration` — are UNRESOLVED for every view until their signed overlays exist (Phase 9). Repository callsite data herein is preliminary repo-grep evidence at the pinned HEAD; it does not discharge the `static_repo` dimension.

## Provenance pins and grounding

- Branch `schema-placement/definer-view-recon-2026-07-13` off clean `main@fdb5fc384c5f9c4c442f45cff530f7599f14a406`.
- Source census `infra/database/schema-placement/evidence/census-prod-20260713T154550Z.json`, sha256 `52962abea7c8b81f62e6331c169f9b6963bf546763a76898cf707d076cf94130` (re-hashed before derivation), repo_sha `7a70cb6322a29a59f36db67e8665a95e3c20cc01`, observed_at `2026-07-13T15:45:51.086245+00:00`.
- Grounding tiers used in this artifact, distinguished throughout: **(a) census-observed facts** from the pinned snapshot; **(b) repository facts** at the pinned HEAD (word-boundary grep, file contents); **(c) policy anchors** (schema-placement policy 2026-07-09, Packet-01 governance of the `mcp_*` views, this lane's evidence rules); **(d) PostgreSQL-semantic inferences**, labeled as such where they appear.
- Acceptance of this artifact should rest on the independently reproducible checks (census sha256, 31-object uniqueness, three-way set-equality, 29/2 disposition histogram, 31 per-view records, cohort-subset) — the multi-agent drafting process behind the prose is process narrative, and its intermediate work products are not committed.

## Reconciliation proof (exactly 31 = prior 29 + 2 mcp_*)

- Fresh census yields **31 unique** `is_security_definer_view=true` object_ids (29 program views + 2 `mcp_*`).
- Set-equal to the prior committed census (`census-prod-20260711T215509Z.json`): additions = ∅, removals = ∅.
- Set-equal to the documented inventory in `docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md` Appendix A (29 program views + the two Packet-01b/6b `mcp_*` exceptions): symmetric difference = ∅.
- The two `mcp_*` views: `public.mcp_job_run_summary_v`, `public.mcp_task_packet_summary_v` — **separately identified**; governed by schema-placement Packet 01 (anon hardening + explicitly deferred invoker conversion), NOT re-dispositioned by this 29-view program.

## Summary

| # | view | disposition (provisional) | conf | callsites (apps/total) | repo defs |
|---|------|---------------------------|------|------------------------|-----------|
| 1 | `public.v_active_tasks` | harden | medium | 0/5 | 1 |
| 2 | `public.v_agent_dashboard` | harden | medium | 0/5 | 1 |
| 3 | `public.v_apparatus_approval_queue` | harden | medium | 0/3 | 1 |
| 4 | `public.v_apparatus_resources` | harden | medium | 0/2 | 0 |
| 5 | `public.v_apparatus_testing_status` | harden | medium | 0/9 | 2 |
| 6 | `public.v_apparatus_type_resources` | harden | medium | 0/2 | 0 |
| 7 | `public.v_approval_queue_summary` | harden | medium | 0/3 | 1 |
| 8 | `public.v_equipment_current_status` | harden | medium | 0/3 | 1 |
| 9 | `public.v_equipment_movement_history` | harden | medium | 0/3 | 1 |
| 10 | `public.v_guide_image_completeness` | harden | medium | 0/1 | 0 |
| 11 | `public.v_image_production_queue` | harden | medium | 0/1 | 0 |
| 12 | `public.v_image_sourcing_summary` | harden | medium | 0/1 | 0 |
| 13 | `public.v_neta_test_details` | harden | medium | 0/2 | 0 |
| 14 | `public.v_pending_handoffs` | harden | medium | 0/4 | 1 |
| 15 | `public.v_project_equipment` | harden | medium | 0/3 | 1 |
| 16 | `public.v_projects_active` | harden | medium | 0/9 | 2 |
| 17 | `public.v_projects_full` | harden | medium | 0/15 | 2 |
| 18 | `public.v_pss_dashboard` | harden | medium | 0/10 | 2 |
| 19 | `public.v_scope_financials` | harden | medium | 0/43 | 2 |
| 20 | `public.v_scope_summary` | harden | medium | 0/2 | 0 |
| 21 | `public.v_tcc_calc_input` | harden | medium | 0/1 | 0 |
| 22 | `public.v_tcc_etu_catalog` | harden | medium | 0/1 | 0 |
| 23 | `public.v_tcc_etu_coefficients` | harden | medium | 0/1 | 0 |
| 24 | `public.v_tcc_tmt_catalog` | harden | medium | 0/1 | 0 |
| 25 | `public.v_tcc_tmt_curve_data` | harden | medium | 0/1 | 0 |
| 26 | `public.vw_etu_browse` | harden | high | 0/43 | 1 |
| 27 | `public.vw_etu_calc_context` | harden | medium | 0/35 | 1 |
| 28 | `public.vw_sensor_calc_context` | harden | medium | 29/66 | 1 |
| 29 | `public.vw_trip_unit_cascade` | harden | medium | 23/105 | 4 |
| 30 | `public.mcp_job_run_summary_v` | defer | high | 18/34 | 3 |
| 31 | `public.mcp_task_packet_summary_v` | defer | high | 16/31 | 3 |

Disposition histogram: {"defer": 2, "harden": 29}.

## Cross-cutting findings

1. **Broad effective privileges on definer views (census-observed):** anon holds privileges beyond SELECT on 31/31 views; authenticated on 31/31. Grant provenance was not observed in this packet. On a definer-semantics view, SELECT reads bypass caller-context RLS on any underlying table that enforces it, and simple single-table views can be auto-updatable (both PostgreSQL-semantic inferences). Whether any of these grants are externally reachable depends on the unresolved `in_data_api_exposed_schema` dimension — surfaced here, resolved only by its Phase-9 overlay.
2. **Views with no defining SQL in the repo (12):** `public.v_apparatus_resources`, `public.v_apparatus_type_resources`, `public.v_guide_image_completeness`, `public.v_image_production_queue`, `public.v_image_sourcing_summary`, `public.v_neta_test_details`, `public.v_scope_summary`, `public.v_tcc_calc_input`, `public.v_tcc_etu_catalog`, `public.v_tcc_etu_coefficients`, `public.v_tcc_tmt_catalog`, `public.v_tcc_tmt_curve_data`. Their upstream dependencies cannot be derived offline; each carries a per-view blocker.
3. **`mcp_*` census-vs-Packet-01 apply-state question:** the census observes anon/authenticated holding all seven privileges on both `mcp_*` views while Packet-01 drift tests model a SELECT-only hardened target — consistent with the Packet-01 A1/A2 APPLY still being HELD (per that lane), and routed to Packet-01 reconciliation, not this program.

## Provisional 3–5-view cohort proposal

**Proposed cohort (operator lean, conflict-checked): `public.v_active_tasks`, `public.v_agent_dashboard`, `public.v_pending_handoffs`**

- Conflict check: **confirm as-is** — no static-repo conflicts found. All three have zero `apps/` callsites (repo hits are the defining `CREATE VIEW` statements in `infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql` plus docs), zero census dependents, and zero FK coupling; none is governed by another packet.
- Coherence: all three are defined in that one source file over a closed three-table domain (`ai_tasks`, `ai_agent_state`, `ai_handoffs`), carry the same census-observed posture (postgres-owned definer view; anon and authenticated each holding all seven privileges), and share the same provisional disposition (harden).
- They share one decisive lineage-status question — is the apex-resa AI-orchestration lineage live or retired? — which a single `operator_declaration` overlay can answer for all three views. **That declaration resolves the lineage-status question only: evidence readiness for the cluster still requires all six signed dimensions per view** (`in_data_api_exposed_schema`, `advisor_findings`, `static_repo`, `runtime_logs`, `external_clients`, `operator_declaration`).
- Kept lean at 3: other low-footprint candidates belong to different domains (apparatus/NETA/TCC) and would break the one-lineage property without reducing total evidence work.

This cohort is NOT accepted by this artifact; acceptance is Phase 8R (operator ratification), and any cluster manifest is Phase 11.

## Per-view records — 29-view program

### `public.v_active_tasks`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

v_active_tasks is a postgres-owned view over the AI-orchestration task queue (ai_tasks LEFT JOIN ai_agent_state) carrying the full seven-privilege set (SELECT/INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER) for both anon and authenticated — far broader than any observed consumer needs, since the census shows zero database dependents and zero database-dep consumers. The only defining SQL is in the legacy apex-resa source-lineage tree, and the remaining callsites are documentation (orchestration protocol examples, a schema reference listing, and the 29-view definer program spec), so nothing in the repo establishes that definer semantics are required or that anon access is intentional. Under the schema-placement policy the view is legacy public content, and the correct posture fix is to set security_invoker=true and revoke the anon/authenticated grants rather than relocate or retain as-is. A promote is not indicated: this is not a canonical model, and whether the legacy apex-resa orchestration lineage is live, dormant, or superseded cannot be determined from this packet's facts — the operator_declaration overlay should confirm before any drop is considered. Whether the grants are reachable through the Data API depends on the unresolved in_data_api_exposed_schema dimension. This is a provisional lean pending the six signed overlays (in_data_api_exposed_schema, advisor_findings, static_repo, runtime_logs, external_clients, operator_declaration); runtime_logs, external_clients, or in_data_api_exposed_schema evidence could still shift it (e.g., an active desktop-claude polling consumer per AI_ORCHESTRATION_PROTOCOL.md would require sequencing the revoke with that client).

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql:191)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view; grant provenance is unknown in this packet. The view is postgres-owned and enumerated in the 29-view definer program spec; absent security_invoker=true, a PostgreSQL view executes with owner privileges (PostgreSQL-semantic inference). Under those definer semantics, for any underlying table (ai_tasks, ai_agent_state) that enforces RLS, SELECT through the view would bypass caller RLS (PostgreSQL-semantic inference); whether those tables enforce RLS was not in this packet's facts. The columns exposed by the defining SQL are task id, title, task_type, project, domain, priority, status, assigned_agent, claimed_at, created_at, hours_claimed, and the joined agent_status — internal task titles, assignments, and status. Whether any of this is reachable by anon or authenticated Data-API callers depends on the unresolved in_data_api_exposed_schema dimension. The write privileges are likely inert — the view has a JOIN, an expression column, and ORDER BY, so it is not auto-updatable (PostgreSQL-semantic inference) — but they are grant-hygiene violations regardless.
- **Depends on:** `ai_tasks`, `ai_agent_state`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 5 total, areas {"docs": 4, "infra": 1}. 5 repo callsites (repo-grep evidence only, NOT the signed static_repo overlay): 4 in docs, 1 in infra. The infra hit is the defining SQL itself (infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql:191). Docs hits: two query examples in docs/architecture/control-plane-lineage/apex-resa/AI_ORCHESTRATION_PROTOCOL.md (lines 208, 245 — one filters assigned_to = 'desktop-claude', suggesting a documented agent-polling pattern), a listing in docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md:447, and enumeration in the 29-view definer program spec (docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232). No application-code consumers found in the repo.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - base relations ai_tasks / ai_agent_state are unqualified in the defining SQL (resolution via search_path, presumed public — PostgreSQL-semantic inference; not confirmed in this packet's facts)
  - documented desktop-claude polling pattern at AI_ORCHESTRATION_PROTOCOL.md:245 suggests a possible out-of-repo runtime consumer that only the runtime_logs and external_clients overlays can confirm or rule out
  - whether the legacy apex-resa AI-orchestration lineage is live, dormant, or superseded is not determinable from this packet's facts — operator_declaration needed to decide harden vs eventual decommission
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether public-schema Data-API exposure makes the anon/authenticated grants reachable via PostgREST)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay (to supersede the preliminary repo-grep callsite data)
  - signed runtime_logs overlay (any live SELECT traffic against v_active_tasks, especially agent-polling clients)
  - signed external_clients overlay (desktop-claude or other out-of-repo orchestration clients per AI_ORCHESTRATION_PROTOCOL.md)
  - signed operator_declaration overlay (whether the apex-resa AI-orchestration views are live, dormant, or superseded)
- **Labeled technical inferences (retained caveats):**
  - Definer-semantics premise: the facts file does not record view reloptions; absent security_invoker=true, PostgreSQL views execute with owner (definer) privileges. The view's enumeration in the 29-view definer program spec is consistent with this (PostgreSQL-semantic inference).
  - RLS-bypass exposure is conditional: it materializes only for an underlying table that enforces RLS, and whether ai_tasks or ai_agent_state enforce RLS was not in this packet's facts (PostgreSQL-semantic inference).
  - The granted INSERT/UPDATE/DELETE privileges cannot route through the view automatically: it contains a JOIN, an expression column (hours_claimed), and ORDER BY, so it is not auto-updatable (PostgreSQL-semantic inference).
  - Unqualified base-relation names in the defining SQL resolve via search_path; the public-schema presumption is inference, not observed fact (PostgreSQL-semantic inference).

### `public.v_agent_dashboard`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

v_agent_dashboard is a view owned by postgres aggregating AI-orchestration state from ai_agent_state, ai_tasks, and ai_handoffs, and the census observed anon and authenticated each holding all seven table-level privileges on it — far broader than any observed consumer need, since the census found zero database dependents and repo grep found zero application-code callsites (all 5 hits are docs, a deploy-script notice, or the CREATE VIEW itself). The repo CREATE VIEW sets no security_invoker option, so the view runs with definer semantics by PostgreSQL default (PostgreSQL-semantic inference; the live catalog reloptions were not a captured facts-file field), and the view is listed in the 29-view definer-view-program in the 2026-07-11 signed-overlay-evidence-design spec. Nothing in the definition requires definer semantics: it is a plain grouped SELECT with no privilege-bridging purpose stated anywhere in the facts. The source lineage (infra/database/source-lineage/apex-resa/automation-orchestration, with a sibling historical-deploy script) reads as legacy apex-resa material. As out-of-band context, not grounded in this packet's facts: the schema-placement policy frames public as legacy/compat-only, consistent with keeping this view in public while fixing posture. Harden accordingly: revoke the anon/authenticated grants and convert to security_invoker=true. Promote is not indicated because there is no evidence this embodies an active canonical model; compat is not indicated because no consumer migration is in evidence. This is provisional pending the six signed overlays (in_data_api_exposed_schema, advisor_findings, static_repo, runtime_logs, external_clients, operator_declaration); an operator declaration that the apex-resa orchestration protocol is fully retired could shift the disposition discussion toward compat, and evidence of an active runtime consumer would refine which grants to retain.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql:219)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view. Grant provenance was not observed in this packet. Because the repo definition sets no security_invoker option, the view runs with definer semantics under owner postgres (PostgreSQL-semantic inference), so for any underlying table (ai_agent_state/ai_tasks/ai_handoffs) that enforces RLS — base-table RLS status was not in this record's facts file — a SELECT through the view would bypass caller RLS (PostgreSQL-semantic inference). Whether anon or authenticated can actually reach the view over the Data API depends on the unresolved in_data_api_exposed_schema dimension; exposure is not established as fact. The write-side grants (DELETE/INSERT/UPDATE/TRUNCATE/TRIGGER/REFERENCES) are gratuitous for a grouped dashboard view that is not auto-updatable (PostgreSQL-semantic inference).
- **Depends on:** `ai_agent_state`, `ai_tasks`, `ai_handoffs`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 5 total, areas {"docs": 3, "infra": 2}. 5 repo-grep callsites, none in application code: docs (3) — an AI_ORCHESTRATION_PROTOCOL.md usage example ("SELECT * FROM v_agent_dashboard;"), a SCHEMA_REFERENCE.md inventory listing, and the 2026-07-11 signed-overlay-evidence-design spec's 29-view program list (self-referential to this program, not a consumer); infra (2) — a RAISE NOTICE test hint in historical-deploy/DEPLOY_ORCHESTRATION.sql and the defining CREATE VIEW in source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql. This is repo-grep evidence only, not the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - underlying relations are written unqualified in the defining SQL (ai_agent_state, ai_tasks, ai_handoffs); schema resolution assumed public but not proven from the facts file
  - activity status of the apex-resa AI-orchestration lineage is unknown (definition lives beside a historical-deploy script; zero application-code callsites); whether any live agent process still reads this view awaits the operator_declaration overlay
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether the view's schema is Data-API exposed, making the observed anon/authenticated privileges reachable over the API)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay (supersedes the preliminary repo-grep callsite data in this record)
  - signed runtime_logs overlay (any live SELECT traffic against v_agent_dashboard, especially by anon/authenticated)
  - signed external_clients overlay (Data-API / PostgREST / external tooling consumers)
  - signed operator_declaration overlay (whether the apex-resa AI-orchestration protocol — ai_agent_state/ai_tasks/ai_handoffs — is active or retired in prod, and whether definer semantics is intentionally required for any agent identity)
- **Labeled technical inferences (retained caveats):**
  - Definer semantics is inferred, not directly observed: the repo CREATE VIEW definition sets no security_invoker option and PostgreSQL defaults views to definer semantics (PostgreSQL-semantic inference); the view's listing in the 29-view definer-view-program in the 2026-07-11 spec corroborates. The live catalog reloptions value was not a captured facts-file field.
  - Grouped/aggregate views are not auto-updatable under PostgreSQL rules; given the GROUP BY and FILTER aggregates in the definition snippet, the granted write privileges (INSERT/UPDATE/DELETE) could not be exercised through the view itself (PostgreSQL-semantic inference, not an explicit facts-file field).
  - The dependency set {ai_agent_state, ai_tasks, ai_handoffs} is derived from the repo definition snippet, in which the relation names are unqualified; schema resolution to public is assumed, not proven from the facts file.

### `public.v_apparatus_approval_queue`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned view over six unqualified relations (apparatus, scopes, projects, clients, tasks, employees), presumed to resolve to public via search_path but not schema-qualified in the source SQL. It carries operationally sensitive data: pending-review apparatus rows joined to employee names, client names, project numbers, tech notes, and delay reasons. The census observed anon and authenticated each holding the full seven-privilege set on the view; grant provenance was not observed in this packet. Repo docs enumerate the view in the 29-view definer program, and for any underlying table that enforces RLS, definer semantics would let a caller read through the owner's context, bypassing caller RLS (PostgreSQL-semantic inference; whether these tables enforce RLS was not in this record's facts). Whether any Data-API caller can actually reach the view depends on the unresolved in_data_api_exposed_schema dimension. The census shows zero database dependents, and the repo grep found no application-code callsites — only two docs listings and the defining source-lineage SQL — so there is no evidenced consumer that requires definer semantics or broad grants. The view's lineage is apex-resa/pm-project-pss (from the repo path of its defining SQL); as out-of-band context, not grounded in this packet's facts: platform schema-placement policy treats public as legacy/compat, which supports hardening in place. The defect is posture, not location, so harden (set security_invoker=true and revoke anon/authenticated) is the right provisional lean rather than promote or compat. This remains provisional until the six signed overlays confirm no runtime or external consumers.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/08_apparatus_completion_workflow.sql:36)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view — the full relation-privilege set, far broader than any plausible read-only queue consumer needs. Grant provenance was not observed in this packet. The view is owned by postgres and is enumerated in the 29-view definer program in repo docs; for any underlying table that enforces RLS, SELECT through a definer view executes in the owner's context and bypasses caller RLS (PostgreSQL-semantic inference — whether apparatus, scopes, projects, clients, tasks, or employees enforce RLS was not in this record's facts). Whether the resulting employee names, client names, and tech notes are reachable by anon/authenticated Data-API callers depends on the unresolved in_data_api_exposed_schema dimension. The write-type privileges are expected to be inert because a multi-join view is not auto-updatable (PostgreSQL-semantic inference), but their presence still evidences a grant-hygiene failure.
- **Depends on:** `apparatus`, `scopes`, `projects`, `clients`, `tasks`, `employees`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 3 total, areas {"docs": 2, "infra": 1}. 3 repo callsites (repo-grep evidence only, NOT the signed static_repo overlay): 2 in docs (docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md line 447, listing legacy views; docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, enumerating the 29-view definer program) and 1 in infra, which is the defining SQL itself (infra/database/source-lineage/apex-resa/pm-project-pss/schema/08_apparatus_completion_workflow.sql line 36). No application-code consumers found; database_deps_found_consumers = 0.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - underlying relations in the definition are unqualified (apparatus, scopes, projects, clients, tasks, employees) — presumed to resolve to public via search_path but not schema-qualified in source
  - the defining SQL is source-lineage (apex-resa/pm-project-pss) and may not exactly match the live prod definition; live pg_get_viewdef and reloptions (security_invoker) are not in the facts file
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay confirming whether the public schema exposes this view to anon/authenticated Data-API callers
  - signed advisor_findings overlay (Supabase security advisor results for definer views)
  - signed static_repo overlay superseding the preliminary repo-grep callsite census
  - signed runtime_logs overlay showing zero (or which) API reads of v_apparatus_approval_queue
  - signed external_clients overlay confirming no external tool or dashboard queries the view
  - signed operator_declaration on whether any PM approval workflow/UI still depends on this queue view
- **Labeled technical inferences (retained caveats):**
  - Write-type privileges (INSERT, UPDATE, DELETE, TRUNCATE) are expected to be inert on this view because a multi-join view is not auto-updatable (PostgreSQL-semantic inference); the grants nonetheless indicate a grant-hygiene defect.
  - The definer classification rests on repo docs enumerating the view in the 29-view definer program plus PostgreSQL's default of definer-style execution when security_invoker is not set; the live reloptions were not captured in this packet's facts (PostgreSQL-semantic inference).
  - For any underlying table that enforces RLS, a postgres-owned definer view bypasses caller RLS (PostgreSQL-semantic inference); whether the six underlying relations enforce RLS was not observed in this packet.

### `public.v_apparatus_resources`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned view in prod public, treated as definer-semantics because security_invoker is not set — a claim anchored in the Phase-8 policy context, not this record's facts file, which does not record view reloptions. The census observed anon and authenticated each holding the full seven-privilege suite (SELECT through TRUNCATE) on the view; grant provenance is unknown in this packet. If public is a Data-API-exposed schema — an unresolved dimension in this record (in_data_api_exposed_schema: not_observed) — any anon or authenticated API caller could reach the view; reachability is therefore conditional, not established. Under definer semantics, reads through the view would execute with the owner's authority, bypassing caller RLS for any underlying table that enforces RLS (PostgreSQL-semantic inference; the underlying relations and their RLS state are not in this record's facts), and the granted write privileges could pass through if the view is auto-updatable (PostgreSQL-semantic inference; not assessable without the definition). The census shows zero database dependents and zero database-dep consumers, and the only repo callsites are two documentation files (a schema reference listing and the disposition-lane spec that enumerates it as one of the 29 definer-view program members); no application code references it. There is no defining SQL in the repo (definition_count 0), so definer semantics cannot be shown to be required and the underlying relations' sensitivity cannot be assessed — which argues for closing the exposure lever rather than retaining it. Provisional lean: convert to security_invoker=true and revoke anon/authenticated grants, pending the six signed overlays; nothing in the facts suggests it embodies a canonical model needing promote or an active migration needing compat.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view; grant provenance is unknown in this packet. Under definer semantics (per the Phase-8 policy context), a SELECT through the view executes with the owner's authority, so caller RLS would be bypassed for any underlying table that enforces RLS (PostgreSQL-semantic inference; the underlying relations and their RLS state are not in this record's facts). The write privileges could pass through only if the view is auto-updatable, which cannot be assessed without the definition (PostgreSQL-semantic inference). Either way, the observed seven-privilege grant to both API-facing roles is a maximal posture far broader than any read-only consumer would need.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 2 total, areas {"docs": 2}. 2 repo callsites, both in docs (repo-grep evidence only, NOT the signed static_repo overlay): docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md line 448 (schema reference listing) and docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232 (the 29-view definer-view program enumeration). No application, migration, or client-code callsites found.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo — underlying relations, data sensitivity, and auto-updatability cannot be assessed offline
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether public is a Data-API-exposed schema for this relation)
  - signed advisor_findings overlay (Supabase advisor findings for this view)
  - signed static_repo overlay (supersedes the preliminary repo-grep callsite evidence)
  - signed runtime_logs overlay (any live SELECT/write traffic against the view)
  - signed external_clients overlay (PostgREST/API consumers outside the repo)
  - signed operator_declaration overlay (operator statement on whether definer semantics or write grants are intentionally relied upon)
  - recovered view definition (live pg_get_viewdef or migration history) to enumerate underlying relations and assess auto-updatability before revoking write privileges
- **Labeled technical inferences (retained caveats):**
  - Definer status (security_invoker not set) is anchored in the Phase-8 policy context, an authorized anchor; this record's facts file does not record view reloptions.
  - Caller-RLS bypass under definer semantics applies only to underlying tables that enforce RLS; the view's underlying relations and their RLS state are not in this record's facts (PostgreSQL-semantic inference).
  - Write passthrough of the granted INSERT/UPDATE/DELETE privileges requires the view to be auto-updatable, which cannot be determined without the view definition (PostgreSQL-semantic inference).

### `public.v_apparatus_testing_status`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a presentation-layer convenience view ("Field crew view of apparatus testing queue") joining apparatus/scopes/projects with active-row filters — not a canonical model needing promotion, and nothing in the facts justifies owner-rights semantics. The census observed the view owned by postgres with anon AND authenticated each holding all seven relation privileges; under definer (owner-rights) view semantics, a SELECT by either role would execute with owner privileges and, for any underlying table that enforces RLS, bypass caller RLS (PostgreSQL-semantic inference — the RLS state of the base tables was not observed in this packet). Whether that read path is reachable through the Data API depends on the unresolved in_data_api_exposed_schema dimension. The census shows zero database dependents and zero inbound/outbound FKs, and all 9 repo callsites are docs/lineage artifacts (including the 29-view definer-view-program spec listing) with no application-code consumers, so hardening (security_invoker=true plus revoking anon/authenticated) has no repo-visible breakage surface. It is explicitly enumerated in the 29-view definer-view program, distinct from the two mcp_* views governed under Packet-01. Provisional harden pending the signed overlays across the six evidence dimensions — the "field crew" purpose hints at possible external/mobile consumers that only runtime_logs, external_clients, and operator_declaration can rule in or out.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 2 (docs/architecture/database-lineage/spec/VIEW_DEFINITIONS.md:285; infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql:223)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view; grant provenance was not observed in this packet. The view is postgres-owned and enumerated in the 29-view definer-view program; under definer semantics, SELECT by anon/authenticated would execute with owner privileges and, for any underlying table (apparatus, scopes, projects) that enforces RLS, bypass caller RLS (PostgreSQL-semantic inference — base-table RLS state was not in this packet's facts). This becomes a live exposure lever only if the view is Data-API reachable, which depends on the unresolved in_data_api_exposed_schema dimension. The write-side privileges (INSERT/UPDATE/DELETE) are not directly exercisable because a three-table join view is not auto-updatable (PostgreSQL-semantic inference), though the granted TRIGGER privilege could in principle permit an INSTEAD OF trigger that makes the view writable; harden's revocation covers both cases. Either way, the observed grant footprint to anon and authenticated is grossly broader than any plausible consumer need, which is exactly what harden targets.
- **Depends on:** `apparatus`, `scopes`, `projects`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 9 total, areas {"docs": 6, "infra": 3}. 9 repo callsites, all documentation or lineage: docs=6 (database-lineage README table row, VIEW_DEFINITIONS.md definition block, knowledge-domain SCHEMA_REFERENCE.md listing, and the 2026-07-11 signed-overlay-evidence-design spec enumerating it in the 29-view definer program) and infra=3 (source-lineage 04_views.sql DDL + comment). Zero application-code consumers found. This is preliminary repo-grep evidence only, NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - the two repo definitions diverge in the location column construction (string concatenation with || vs CONCAT_WS), so the canonical deployed definition on prod is unconfirmed from repo evidence
  - view comment declares a 'field crew' audience, implying possible external/mobile consumers that repo grep cannot resolve; must be settled by runtime_logs/external_clients/operator_declaration before revoking authenticated SELECT
- **Required evidence before any accepted decision:**
  - in_data_api_exposed_schema signed overlay (authoritative platform-config determination of whether public-schema exposure makes this view PostgREST-reachable)
  - advisor_findings signed overlay (Supabase advisor security_definer_view / exposed-view findings)
  - static_repo signed overlay (to supersede the preliminary grep-based callsite census)
  - runtime_logs signed overlay (any PostgREST/API reads of v_apparatus_testing_status, especially by anon/authenticated roles)
  - external_clients signed overlay (field-crew dashboards or mobile clients reading the view)
  - operator_declaration signed overlay (confirm no sanctioned field-crew consumer depends on definer semantics or anon/authenticated SELECT)
- **Labeled technical inferences (retained caveats):**
  - Definer (owner-rights) view execution bypasses caller RLS only for underlying tables that themselves enforce RLS; the RLS state of apparatus, scopes, and projects was not observed in this packet (PostgreSQL-semantic inference).
  - A three-table join view is not auto-updatable, so the granted INSERT/UPDATE/DELETE privileges are not directly exercisable; the granted TRIGGER privilege could in principle allow an INSTEAD OF trigger that makes the view writable (PostgreSQL-semantic inference).
  - The definer-semantics characterization rests on the view's enumeration in the 29-view definer-view-program spec; the security_invoker reloption state was not directly captured in this packet's facts file.

### `public.v_apparatus_type_resources`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a plain view (relkind v) owned by postgres in the prod public schema, enrolled in the 29-view definer-view-program roster (repo-doc evidence), with the maximal grant posture: the census observed anon and authenticated each holding all seven table-level privileges. Grant provenance was not observed in this packet and is unknown. The census found zero database dependents and zero database-side consumers, and the only repo callsites are two documentation mentions (a schema reference list and the 29-view program spec itself) — no application, migration, or API code references the view by name in the grep evidence. Under the definer semantics the program roster attributes to this view, reads through it would bypass caller RLS on any underlying relation that enforces RLS (PostgreSQL-semantic inference); because no defining SQL was found, the base relations are unknown. Whether the observed grants are reachable through the Data API depends on the unresolved in_data_api_exposed_schema dimension. Nothing in the facts justifies definer semantics or write-capable grants held by anon, so the provisional lean is harden: revoke anon/authenticated grants (at minimum the write privileges, likely SELECT too) and/or convert to security_invoker=true. The lean is provisional and cannot be executed yet: no defining SQL was found in the repo (definition_count=0), so the base relations are unknown, and the six signed evidence overlays are outstanding. If the signed overlays confirm zero runtime/external consumers, the operator may also consider whether the view is dead and eligible for retirement rather than mere hardening; that escalation needs operator_declaration.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view. Grant provenance was not observed in this packet and is unknown. Under definer semantics with owner postgres, a SELECT through the view would bypass caller RLS on any underlying relation that enforces RLS (PostgreSQL-semantic inference); because no defining SQL was found (definition_count=0), the set of base relations — and whether any of them enforce RLS — is unknown, so the bypassed surface is unquantified. Write privileges (INSERT/UPDATE/DELETE/TRUNCATE) could additionally flow through to base tables if the view is auto-updatable, which cannot be determined without the definition (PostgreSQL-semantic inference). Whether any of these grants are reachable via PostgREST depends on the unresolved in_data_api_exposed_schema dimension. This is the widest possible grant posture on the view itself and is far broader than the zero consumers observed in database deps and repo grep.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 2 total, areas {"docs": 2}. 2 repo callsites, both in docs (repo-grep evidence only, NOT the signed static_repo overlay): docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md line 448 (listed among apparatus views) and docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232 (the 29-view definer-view-program roster itself). No application, migration, or API code callsites found; database_deps found 0 consumers and dependent_objects is empty.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo (definition_count=0) — base relations unknown, so which (if any) enforce RLS is also unknown; the definition must be pulled from the prod catalog (pg_get_viewdef) before executing any hardening
  - zero observed consumers makes retire-vs-harden ambiguous; needs operator_declaration
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether public-schema exposure makes these grants reachable via PostgREST; reachability is unresolved until then)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay to supersede the repo-grep callsite data
  - signed runtime_logs overlay (any prod reads of the view via Data API or direct SQL)
  - signed external_clients overlay (non-repo consumers, e.g. reporting tools or PostgREST clients)
  - signed operator_declaration overlay (is this view still needed; retire vs harden)
  - view definition from prod catalog (pg_get_viewdef) to enumerate base relations and determine which, if any, enforce RLS, before applying security_invoker/revoke
- **Labeled technical inferences (retained caveats):**
  - The census records rls_enabled=false for this object, but RLS does not attach to plain views (relkind v); the field is immaterial for a view (PostgreSQL-semantic inference).
  - Whether write privileges (INSERT/UPDATE/DELETE/TRUNCATE) can flow through to base tables depends on the view being auto-updatable, which cannot be determined while the defining SQL is unknown (definition_count=0) (PostgreSQL-semantic inference).

### `public.v_approval_queue_summary`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a definer-semantics aggregate view (owner postgres, security_invoker not set) summarizing pending-review apparatus by project, exposing business metadata (project number/name, client name, project lead, pending hours/counts) drawn from four base tables (apparatus, scopes, projects, clients). Under definer semantics, for any underlying table that enforces RLS, caller RLS would not apply through this view (PostgreSQL-semantic inference; base-table RLS state was not observed in this packet's facts). The census observed anon and authenticated each holding the full seven-privilege set (SELECT through TRUNCATE) on the view — far broader than any plausible consumer of a read-only summary needs; grant provenance is unknown in this packet. The write privileges are expected to be inert on a grouped view (PostgreSQL-semantic inference) but remain grant-hygiene defects. The census shows zero database dependents and the only repo-grep callsites are two documentation files plus the defining source-lineage SQL itself — no application-code consumers appear in the preliminary grep evidence — so nothing in the facts justifies definer semantics or the observed grants. Harden (convert to security_invoker=true and revoke anon/authenticated) is the minimal-risk provisional lean; retain has no supporting facts, and promote/compat cannot be argued because no canonical-model duplication or migrating consumer is evidenced in the facts file. If the signed overlays confirm zero runtime/external consumers, the operator may later consider whether the view is a drop candidate, but that exceeds this reconciliation's vocabulary and evidence.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/08_apparatus_completion_workflow.sql:233)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view; grant provenance was not observed in this packet. Because the view runs with definer semantics under owner postgres, an anon/authenticated SELECT would not be subject to caller RLS on any underlying table that enforces RLS (PostgreSQL-semantic inference; base-table RLS state was not observed here) — a live exposure lever for project and client business metadata whose reachability through the Data API depends on the unresolved in_data_api_exposed_schema dimension. The write privileges are expected to be non-functional on an aggregate (GROUP BY) view (PostgreSQL-semantic inference) but are an over-grant and should be revoked regardless.
- **Depends on:** `apparatus`, `scopes`, `projects`, `clients`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 3 total, areas {"docs": 2, "infra": 1}. 3 repo-grep callsites (preliminary evidence, not the signed static_repo overlay): docs x2 (docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md listing views; docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md enumerating the 29-view definer program) and infra x1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/08_apparatus_completion_workflow.sql:233, the CREATE OR REPLACE VIEW itself). No application-code consumers appear in the grep evidence.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - base-table relations in the defining SQL are unqualified (apparatus/scopes/projects/clients); presumed public.* at creation but schema resolution not verifiable offline
  - zero database dependents and zero application-code callsites in the preliminary grep leave actual consumers entirely unevidenced; whether any anon/authenticated client reads this view (which harden would break) is unknown until the signed overlays land
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (config-backed: whether public is in the Data-API exposed-schemas platform config)
  - signed advisor_findings overlay (Supabase advisor security findings for this definer view)
  - signed static_repo overlay (to supersede the preliminary repo-grep callsite evidence)
  - signed runtime_logs overlay (any observed reads of v_approval_queue_summary in prod)
  - signed external_clients overlay (Data-API / PostgREST clients selecting the view as anon or authenticated)
  - signed operator_declaration overlay (operator statement on whether the legacy apex-resa PM completion-workflow consumers still exist)
- **Labeled technical inferences (retained caveats):**
  - Definer-semantics views (owner postgres, security_invoker not set) execute base-table access with the owner's privileges; for any underlying table that enforces RLS, caller RLS would not apply through this view. Whether apparatus/scopes/projects/clients enforce RLS was not observed in this packet (PostgreSQL-semantic inference).
  - The write privileges (INSERT/UPDATE/DELETE/TRUNCATE) are expected to be non-functional on this view because a grouped/aggregate view is not auto-updatable (PostgreSQL-semantic inference); they remain grant-hygiene defects regardless.

### `public.v_equipment_current_status`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

The census observed anon and authenticated each holding all seven table-level privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on this postgres-owned view joining equipment, employees, projects, and locations — employee-name and equipment-location data; grant provenance was not observed in this packet, and the observed breadth is far wider than any plausible consumer need. The view's source definition sets no security_invoker option, so it runs with definer semantics (PostgreSQL-semantic inference: views default to definer semantics), and for any underlying table that enforces RLS, a caller's SELECT on the view would bypass that RLS (PostgreSQL-semantic inference; the RLS state of the four base tables was not observed in this packet). Whether anon or authenticated can actually reach the view over the Data API depends on the unresolved in_data_api_exposed_schema dimension. The census shows zero database dependents and zero inbound/outbound FKs, and the only repo-grep callsites are two documentation listings plus the defining SQL itself in the apex-resa source-lineage tree — no application code reads it. That profile is consistent with legacy residue rather than a canonical model warranting promote (out-of-band context, not grounded in this packet's facts: the 2026-07-09 schema-placement policy treats public.* as legacy/compat only). Hardening (set security_invoker=true and revoke the anon/authenticated grants, retaining only what a proven consumer needs) closes the observed privilege surface without dropping the object; whether it can subsequently be retired or must become a compat shim depends on the runtime_logs and external_clients overlays. This is a provisional lean pending the six signed overlay dimensions and operator review; no evidence found here justifies retain, and no consumer-migration story exists to justify compat.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql:74)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view; grant provenance was not observed in this packet. The view runs with definer semantics under owner postgres (its source definition sets no security_invoker option — PostgreSQL-semantic inference, as views default to definer semantics), so if the view is reachable — reachability depends on the unresolved in_data_api_exposed_schema dimension — SELECT alone would let an anon caller read joined equipment/employee/project/location rows, and for any underlying table that enforces RLS that read would bypass it (PostgreSQL-semantic inference; the base tables' RLS state was not observed in this packet). This is the core exposure lever in the observed privileges. The write-side privileges are likely inert because a four-relation LEFT-JOIN view is not auto-updatable (PostgreSQL-semantic inference), but they are far broader than any read use requires and should be revoked regardless.
- **Depends on:** `equipment`, `employees`, `projects`, `locations`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 3 total, areas {"docs": 2, "infra": 1}. 3 repo-grep callsites: docs x2 (docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md line 449, a view inventory that lists the name literally; docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, a listing of the 29-view definer program whose captured snippet is truncated before this view's name appears — the hit is implied by the grep match rather than visible in the snippet) and infra x1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql line 74, which is the CREATE VIEW definition itself). No application-code consumers appear in the grep. This is repo-grep evidence only, NOT the signed static_repo overlay (static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - defining SQL lives in a shared source-lineage file (07_equipment_project_assignment.sql) that also creates v_project_equipment, v_equipment_movement_history, RLS policies, and a sync trigger — hardening actions must be scoped to this view, not the file
  - base relations in the view definition are unqualified in the source; presumed public-schema resolution is unverified offline
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether the schema containing this view is served by the Data API, from platform config)
  - signed advisor_findings overlay (Supabase security advisor results for definer views)
  - signed static_repo overlay to supersede the repo-grep callsite census
  - signed runtime_logs overlay (any PostgREST/API SELECT traffic against v_equipment_current_status)
  - signed external_clients overlay (non-repo consumers: dashboards, integrations, MCP clients)
  - signed operator_declaration overlay on whether the apex-resa equipment-tracking lane this view belongs to is live or superseded
- **Labeled technical inferences (retained caveats):**
  - A four-relation LEFT-JOIN view is not auto-updatable, so the observed write-side privileges (INSERT/UPDATE/DELETE) are likely inert — PostgreSQL-semantic inference from general PostgreSQL view semantics, not traceable to this packet's facts; the revoke recommendation does not depend on it.

### `public.v_equipment_movement_history`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a legacy apex-resa lineage view (defined in infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql:109) sitting in public with the full seven-privilege grant set observed for both anon and authenticated — grants vastly broader than any evidenced consumer needs, since the census shows zero database dependents and repo grep shows zero application callsites (only two docs listings plus the defining SQL itself). The census does not record per-view reloptions, so security_invoker state is not directly observed; definer semantics is the lane's working premise for public views, not an observed census field. On that premise, definer semantics are not clearly required here: the repo lineage file enables RLS on equipment_assignments with permissive USING(true) policies (repo evidence, not observed live state), so nothing in the repo evidence indicates the view depends on bypassing caller RLS. The provisional lean is therefore harden — set security_invoker=true and revoke anon/authenticated grants (at minimum the write/TRIGGER/TRUNCATE/REFERENCES privileges, and SELECT absent a declared consumer). A grep name match places it on the definer-view-program (29) list line in docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232 — the captured snippet truncates before the view name appears verbatim, so membership is inferred from the match rather than visible text — placing it in that program rather than Packet 01, which governs the two mcp_* views. This remains provisional: the repo definition may not match the live prod definition, and all six evidence dimensions (in_data_api_exposed_schema, advisor_findings, static_repo, runtime_logs, external_clients, operator_declaration) are unresolved, so an unknown live consumer could still surface before apply.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql:109)
- **Privileges (census-observed):** The census observed anon and authenticated each holding all seven relation privileges on the view (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE); grant provenance was not observed in this packet. The view is owned by postgres. If it runs with definer semantics (the lane's working premise — security_invoker state is not an observed census field), any anon/authenticated SELECT reads the five underlying tables with the owner's privileges, bypassing caller RLS for any underlying table that enforces it (PostgreSQL-semantic inference); whether prod base tables enforce RLS was not observed in this packet. Whether that read path is reachable through the Data API depends on the unresolved in_data_api_exposed_schema dimension. The write-side privileges are grant hygiene violations rather than a direct write path — a five-table join view is not auto-updatable (PostgreSQL-semantic inference) — but they exceed any evidenced consumer need, since no consumers are evidenced at all.
- **Depends on:** `equipment_assignments`, `equipment`, `employees`, `projects`, `locations`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 3 total, areas {"docs": 2, "infra": 1}. 3 repo-grep hits, none in application code: docs (2) — a name listing in docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md:450 and a name match on the definer-view-program (29) list line in docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232 (the captured snippet truncates before the view name appears verbatim) — and infra (1), which is the CREATE OR REPLACE VIEW statement itself in the apex-resa source-lineage schema file. No app, API, or client consumers appear in the grep. This is repo-grep evidence only, not the signed static_repo overlay (static_repo state: not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - repo definition is from the apex-resa source-lineage tree and may not match the live prod view definition; live catalog definition unverified offline
  - live prod base-table RLS posture not observed in this packet (the repo lineage snippet shows equipment_assignments RLS-enabled with permissive USING(true) policies, but that is repo evidence, not live state), so the practical exposure delta of invoker conversion is unconfirmed
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether public-schema Data-API exposure makes anon/authenticated access to this view reachable)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay (authoritative callsite scan superseding this record's preliminary repo grep)
  - signed runtime_logs overlay (any live query traffic against v_equipment_movement_history)
  - signed external_clients overlay (PostgREST/API/service-role consumers)
  - signed operator_declaration overlay (whether equipment movement history is an active workflow with any intended consumer, or a dead apex-resa lineage artifact)
  - live prod view definition, reloptions (security_invoker state), and base-table RLS state to confirm the repo lineage snippet matches production before applying security_invoker conversion
- **Labeled technical inferences (retained caveats):**
  - Definer semantics (security_invoker unset) is the lane's working premise for public views, not an observed census field; the census records owner=postgres and relkind=v with no per-view reloptions.
  - Definer-view-program (29) membership rests on a grep name match on the program-list line of docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232; the captured snippet truncates before the view name appears verbatim.
  - Caller-RLS bypass under definer semantics and the non-auto-updatability of a five-table join view are PostgreSQL-semantic inferences, not observed behavior; prod base-table RLS state was not observed in this packet.

### `public.v_guide_image_completeness`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned view (rls_enabled=false observed) enumerated in the 29-view definer program, and its effective grants are maximally broad: the census observed anon and authenticated each holding all seven relation privileges, including write-class privileges (DELETE/INSERT/UPDATE/TRUNCATE) that no reporting-style completeness view plausibly needs. Grant provenance was not observed in this packet. The census shows zero database dependents and zero database-dep consumers, and the only repo callsite is the disposition-lane spec that enumerates the 29-view program itself — no application, tooling, or migration consumer was found by grep (preliminary evidence, not the signed static_repo overlay). No defining SQL exists in the repo, so the base relations it reads cannot be enumerated offline; under definer semantics, reads through the view execute with the owner's rights, and for any underlying table that enforces RLS this would bypass caller RLS (PostgreSQL-semantic inference — base-table RLS status was not observed in this packet). That unauditability makes the broad-grant posture strictly worse: a potentially RLS-bypassing read path with no demonstrated consumer. Whether anon/authenticated can actually reach the view via the Data API depends on the unresolved in_data_api_exposed_schema dimension. The proportionate provisional action is to harden in place — revoke anon/authenticated grants and/or convert to security_invoker=true — rather than defer, because the observed privilege posture alone justifies the lean regardless of what the definition turns out to be. Promote/compat cannot be assessed without the definition; retain is unsupportable on these facts. Final action must wait on the six signed overlays plus retrieval of the live view definition.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view — all seven relation privileges. Grant provenance (explicit GRANT vs any default mechanism) was not observed in this packet. Because the view is postgres-owned and part of the definer-view program, a SELECT through it executes against the underlying tables with the owner's rights; for any underlying table that enforces RLS, that would bypass caller RLS (PostgreSQL-semantic inference — base-table RLS status was not observed in this packet). If the view is auto-updatable, the granted write privileges could also permit writes through it (PostgreSQL-semantic inference — the definition was not retrieved, so updatability is unknown). Whether anon/authenticated can reach the view over the Data API depends on the unresolved in_data_api_exposed_schema dimension. With zero identified consumers, the observed grants are clearly broader than any demonstrated need.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 1 total, areas {"docs": 1}. Exactly 1 repo callsite, in docs only: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232, which is the enumeration of the 29-view definer program itself — not an application, script, or migration consumer. This is preliminary repo-grep evidence only, NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo (definition_count=0) — base relations read under definer semantics cannot be enumerated offline; live pg_get_viewdef needed before final disposition
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (platform-config determination of whether public-schema exposure makes this view reachable via the Data API/PostgREST)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay (to supersede the preliminary repo-grep callsite data)
  - signed runtime_logs overlay (any Data-API/PostgREST or client reads of this view in prod)
  - signed external_clients overlay (non-repo consumers)
  - signed operator_declaration overlay (operator statement of the view's purpose and whether anon/authenticated access is intended)
  - live view definition from prod (pg_get_viewdef) to enumerate base relations, determine whether any of them enforce RLS, and confirm whether the view is auto-updatable
- **Labeled technical inferences (retained caveats):**
  - Definer-semantics caveat (PostgreSQL-semantic inference): reads through a postgres-owned definer view execute with the owner's rights, so for any underlying table that enforces RLS, caller RLS would be bypassed; base-table RLS status was not observed in this packet.
  - Auto-updatability caveat (PostgreSQL-semantic inference): simple PostgreSQL views are auto-updatable; if this view is auto-updatable, the granted INSERT/UPDATE/DELETE privileges could permit writes through it; the definition was not retrieved, so updatability is unknown.
  - This view is not one of the two mcp_* views governed by Packet-01, so Packet-01 defer-by-governance routing does not apply.

### `public.v_image_production_queue`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

The census observed anon and authenticated each holding all seven relation privileges (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER) on this postgres-owned view; grant provenance was not observed in this packet. The view is treated as definer-semantics per the lane's program policy anchor (reloptions were not directly observed in this facts file). Under definer semantics, reads through the view would bypass the caller's RLS for any underlying table that enforces RLS (PostgreSQL-semantic inference; base tables and their RLS state are unknown here), and the write grants could reach base tables if the view is simple/auto-updatable (PostgreSQL-semantic inference) — but whether anon or authenticated can actually reach the view over the Data API depends on the unresolved in_data_api_exposed_schema dimension. Nothing in the facts justifies that grant posture: zero database dependents, zero database-dep consumers, and the sole repo callsite is the disposition-lane governance spec enumerating the 29-view program — no application code references the name. With definition_count=0 there is no evidence that definer semantics are required at all. The provisional lean is harden: revoke the anon/authenticated grants (at minimum the write privileges, which no observed consumer requires) and convert to security_invoker=true, pending the signed overlays. It is not one of the two mcp_* Packet-01 views, so it belongs in the 29-view program; promote/compat cannot be assessed without a definition, and retain is unsupportable given the observed grant breadth versus zero observed consumers.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding all seven relation privileges (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER) on this postgres-owned view; grant provenance is unknown in this packet. The census also observed rls_enabled=false on the view itself, which is immaterial to posture: RLS does not govern view exposure — grants plus invoker/definer semantics do (PostgreSQL-semantic inference). If the schema is exposed via the Data API (unresolved: in_data_api_exposed_schema), unauthenticated callers could SELECT through the view, and under definer semantics such reads would bypass the caller's RLS for any underlying table that enforces RLS (PostgreSQL-semantic inference; base relations and their RLS state were not in this facts file). The write grants would permit writes through the view only if it is simple/auto-updatable (PostgreSQL-semantic inference; no definition available). This is the maximum-breadth grant posture, far broader than any observed consumer needs — none were observed.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 1 total, areas {"docs": 1}. One repo callsite total, area=docs: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, the signed-overlay evidence-design spec enumerating the 29-view definer program. The captured snippet is truncated before this view's name appears; attribution of that line to v_image_production_queue is inferred from callsite_count=1 and the visible 'Definer-view-program (29)' list prefix, not from directly visible text. Either way, the only repo mention of this view is the audit lane itself, not a consumer — no app, API, or migration callsites were found by grep. This is preliminary repo-grep evidence only, NOT the signed static_repo overlay (static_repo state: not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo (definition_count=0) — base relations unknown; cannot verify whether definer semantics are required or whether the view is auto-updatable, which determines whether the anon/authenticated write grants are exercisable through the view (PostgreSQL-semantic inference)
  - security_invoker state not directly observed in this facts file — the definer-semantics characterization derives from the lane's program policy anchor; reloptions need direct confirmation before the convert is sequenced
  - view purpose unknown — 'image production queue' does not map to any lane or consumer in the facts file; may be an orphan from a retired pipeline, which the operator_declaration overlay must confirm before revoke/convert is sequenced
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether public-schema exposure actually surfaces this view to anon/authenticated via PostgREST)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay (supersedes the preliminary repo-grep callsite evidence)
  - signed runtime_logs overlay (any PostgREST/API reads of v_image_production_queue in prod)
  - signed external_clients overlay (non-repo consumers: dashboards, scripts, third-party tools)
  - signed operator_declaration overlay (is the image-production pipeline live, dormant, or retired; is definer read-through intentionally relied on)
  - authoritative view definition (pg_get_viewdef from prod, since no repo definition exists) plus reloptions, to enumerate base relations, confirm security_invoker state directly, and determine auto-updatability before the revoke/security_invoker change is sequenced
- **Labeled technical inferences (retained caveats):**
  - Definer-semantics reads through a view bypass the caller's RLS only for underlying tables that enforce RLS; the base relations and their RLS state were not observed in this packet (PostgreSQL-semantic inference).
  - INSERT/UPDATE/DELETE grants on a view are exercisable against base tables only if the view is simple/auto-updatable (or has enabling triggers/rules); with definition_count=0, exploitability of the observed write grants is undetermined (PostgreSQL-semantic inference).
  - The definer-semantics (security_invoker not set) characterization derives from the lane's program policy anchor, not from directly observed reloptions; signed evidence should confirm the reloptions state directly.

### `public.v_image_sourcing_summary`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned definer view (security_invoker not set). The census observed anon and authenticated each holding all seven relation privileges on it; grant provenance was not observed in this packet. Whether those privileges are reachable by API callers depends on the unresolved in_data_api_exposed_schema dimension; if the schema is Data-API-exposed, any anon or authenticated caller could read whatever the view selects with owner privileges, and for any underlying table that enforces RLS a definer view bypasses caller RLS (PostgreSQL-semantic inference; base-table RLS status was not in this record's facts). The census shows zero database dependents, zero repo definitions, and the only repo callsite is the disposition-ledger design doc's enumeration of the 29-view definer program itself — no application code references it. With no evidence that definer semantics are required and no identifiable consumer needing anon/authenticated access, the proportionate provisional action is to harden: revoke anon/authenticated grants and convert to security_invoker=true. The absence of any defining SQL in the repo also makes this a candidate for outright removal, but that escalation needs operator_declaration plus the runtime_logs and external_clients overlays to confirm nothing unseen consumes it; harden is the safe posture fix in the meantime. Confidence is capped because the view's underlying relations are unknown (no definition found), so the actual exposure surface behind the definer semantics cannot be characterized from this packet's facts.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding all seven relation privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on the view; grant provenance was not observed in this packet. On a postgres-owned definer view, SELECT alone lets a caller read the underlying relations with owner rights, bypassing caller RLS for any underlying table that enforces RLS (PostgreSQL-semantic inference; whether the underlying tables enforce RLS was not observed). The write-shaped privileges are additionally a potential write path if the view is auto-updatable (PostgreSQL-semantic inference; not determinable without the view definition). Whether any of this is reachable by API callers depends on the unresolved in_data_api_exposed_schema dimension. The grants are plainly broader than any plausible consumer need — the census found zero consumers — so this is an active exposure lever pending hardening.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 1 total, areas {"docs": 1}. Exactly 1 repo callsite, in docs only: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, which is the design spec's enumeration of the 29-view definer program — a self-referential governance mention, not a consumer. No application, API, or tooling code references the view name anywhere in the repo. This is preliminary repo-grep evidence only, not the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo (definition_count=0) — underlying relations and exposure surface unknown; the dependencies list is empty for lack of evidence, not because the view reads nothing
  - cannot distinguish harden vs full removal (view appears orphaned: 0 database dependents, 0 application callsites, no repo definition) without the operator_declaration, runtime_logs, and external_clients overlays
- **Required evidence before any accepted decision:**
  - signed overlay: in_data_api_exposed_schema (authoritative platform config; determines whether the observed anon/authenticated privileges are reachable via PostgREST/Data-API)
  - signed overlay: advisor_findings (Supabase advisor security findings for this view)
  - signed overlay: static_repo (to supersede the preliminary repo-grep callsite evidence)
  - signed overlay: runtime_logs (any production reads against the view)
  - signed overlay: external_clients (PostgREST/Data-API or external tool usage)
  - signed overlay: operator_declaration (whether the view is still wanted; harden vs drop)
  - authoritative view definition from prod (pg_get_viewdef) to enumerate underlying relations and characterize the exposure surface behind the definer semantics
- **Labeled technical inferences (retained caveats):**
  - Definer-view RLS bypass is PostgreSQL-semantic inference: a definer view reads its underlying relations with owner privileges, bypassing caller RLS for any underlying table that enforces RLS; whether this view's underlying tables enforce RLS was not observed in this packet.
  - The write-shaped privileges (INSERT/UPDATE/DELETE) constitute an exercisable write path only if the view is auto-updatable, which cannot be determined without the view definition (PostgreSQL-semantic inference).

### `public.v_neta_test_details`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a view owned by postgres that the packet's definer-view program policy anchor characterizes as definer-semantics (security_invoker not set); the facts file itself carries no reloptions evidence for this. The census observed both anon and authenticated holding all seven relation privileges (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER) — a grant surface far broader than any consumer evidence supports; grant provenance was not observed in this packet. The census shows zero database dependents and zero database-dep consumers, and the only repo callsites are two documentation mentions (an architecture schema inventory and the 29-view definer-view program enumeration in the overlay-evidence design spec); no application code references the view. No defining SQL exists in the repo (definition_count=0), so definer necessity, underlying relations, and auto-updatability cannot be assessed from source. Under the packet's schema-placement policy anchor (2026-07-09: public = legacy/compat/shims only) and the definer-view exposure lever, the provisional lean is harden: revoke the anon/authenticated grants — at minimum the write privileges, which, if the view is auto-updatable, are a live write path through the view, and on a definer-semantics view such writes would not be constrained by caller RLS on any RLS-protected underlying relation (PostgreSQL-semantic inference) — and convert to security_invoker=true unless a signed overlay surfaces a consumer that requires definer semantics. Whether the observed grants are network-reachable depends on the unresolved in_data_api_exposed_schema dimension. If the signed overlays confirm zero consumers, the operator may later choose retirement instead, but that decision needs the overlay evidence; harden is the safe reversible posture now. This is a provisional proposal for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view; grant provenance is unknown in this packet. The view is characterized as definer-semantics per the packet's policy anchor (the facts file carries no reloptions evidence): under definer semantics, a SELECT by anon/authenticated would bypass caller RLS on any RLS-protected underlying relation (PostgreSQL-semantic inference) — with definition_count=0, the underlying relations and their RLS posture are unknown in this packet. The write privileges (INSERT/UPDATE/DELETE, plus TRUNCATE) would constitute a live write path through the view if it is auto-updatable (PostgreSQL-semantic inference; unverifiable here because no definition was recovered). RLS on the view relation itself is observed false (expected for plain views — PostgreSQL-semantic inference — meaning nothing constrains rows at the view layer). Whether any of this is reachable from the network depends on the unresolved in_data_api_exposed_schema dimension; exposure is not established as fact.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 2 total, areas {"docs": 2}. 2 repo callsites, both in docs (repo-grep evidence only, NOT the signed static_repo overlay): docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md:450 lists the view name in a schema inventory, and docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232 enumerates it within the 29-view definer-view program. No application-code, migration, or client callsites found in the repo grep.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo (definition_count=0) — underlying relations, definer necessity, and auto-updatability (write-path reachability) cannot be assessed from source; the definition must be recovered from the prod catalog via a governed channel
- **Required evidence before any accepted decision:**
  - signed overlay: in_data_api_exposed_schema (whether public-schema exposure makes the observed grants network-reachable)
  - signed overlay: advisor_findings (Supabase advisor security findings for this view)
  - signed overlay: static_repo (authoritative callsite census superseding the preliminary repo-grep data)
  - signed overlay: runtime_logs (any observed reads/writes against the view)
  - signed overlay: external_clients (PostgREST/API consumers of the view)
  - signed overlay: operator_declaration (intended consumers and whether definer semantics are required)
  - recovered view definition from the prod catalog (pg_get_viewdef) via a governed channel, to enumerate underlying relations and confirm auto-updatability before finalizing the harden scope
- **Labeled technical inferences (retained caveats):**
  - The definer-semantics characterization (security_invoker not set) rests on the packet's policy anchor for the 29-view definer-view program; the facts file itself carries no reloptions evidence for this view.
  - The empty dependencies list reflects the absence of any recovered definition (definition_count=0), not a verified absence of underlying relations; the final harden scope (which base relations are exposed, whether the view is auto-updatable) cannot be validated until pg_get_viewdef is recovered via a governed channel.
  - The claims that a definer-semantics view bypasses caller RLS on RLS-protected underlying relations, and that write privileges on an auto-updatable view constitute a live write path, are PostgreSQL-semantic inferences conditional on the unrecovered definition — not observations from this packet's facts.

### `public.v_pending_handoffs`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

The census observed the view as owner postgres with anon and authenticated each holding all seven relation privileges (SELECT/INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER) — far broader than any evidenced consumer needs: the census shows zero database dependents, and the preliminary repo grep surfaced no application-code callsites (3 docs references plus the defining SQL in the apex-resa source-lineage snapshot). Absent a security_invoker setting — none was recorded in the census — the view would execute with owner (definer) semantics (PostgreSQL-semantic inference), and nothing in the facts indicates definer semantics are required: the view is a simple pending-queue projection with no privilege-bridging rationale recorded. The defining SQL lives only under infra/database/source-lineage/apex-resa/automation-orchestration (legacy lineage material), consistent with a legacy shim rather than a canonical model, so promote is not indicated and retain is unjustified. Harden — set security_invoker=true and revoke anon/authenticated grants down to what consumers actually need (likely nothing) — is the right provisional lean; if the signed overlays confirm zero runtime/external consumers, the operator may later choose full retirement, but that exceeds this vocabulary. This is provisional pending the six signed overlay dimensions and stays inside the 29-view program (it is not one of the two mcp_* views governed under Packet-01).

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql:235)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view; grant provenance was not observed in this packet. If the view runs with definer (owner postgres) semantics — the PostgreSQL default for views absent security_invoker (PostgreSQL-semantic inference) — any anon/authenticated SELECT reads ai_handoffs and ai_tasks with owner privileges, which for any underlying table that enforces RLS would bypass the caller's RLS (PostgreSQL-semantic inference; base-table RLS status is not in this record's facts file). Whether that SELECT surface is reachable through the Data API depends on the unresolved in_data_api_exposed_schema dimension. The write-class grants are likely inert for direct DML because the join/filtered/computed-column definition is not auto-updatable (PostgreSQL-semantic inference), but they are grant-hygiene violations and would become live if INSTEAD OF triggers or rules were ever added. Net: both anon and authenticated were observed holding maximal relation privileges on an owner-postgres view whose read path, under definer semantics, would not be constrained by base-table RLS.
- **Depends on:** `ai_handoffs`, `ai_tasks`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 4 total, areas {"docs": 3, "infra": 1}. 4 repo callsites (preliminary repo-grep evidence, NOT the signed static_repo overlay): 3 in docs — an example query (SELECT * FROM v_pending_handoffs;) in docs/architecture/control-plane-lineage/apex-resa/AI_ORCHESTRATION_PROTOCOL.md:220, a name listing in docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md:450, and a grep match on the 29-definer-view program roster line in docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232 (the captured callsite text truncates before this view's name; its inclusion in the roster is inferred from the grep match, not directly visible in the captured text) — plus 1 in infra: the CREATE VIEW statement itself at infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql:235. The grep surfaced no application/runtime code callsites (callsite areas: docs 3, infra 1); that is an absence claim over this preliminary grep evidence.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - repo definition comes from the apex-resa source-lineage snapshot (infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql:235) and may not match the live prod definition
  - defining SQL uses unqualified relation names (ai_handoffs, ai_tasks); presumed public but the schema is not stated in the snippet
  - status of the apex-resa AI orchestration handoff workflow (live, deprecated, or superseded) is not established by the facts file
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (config-backed determination whether public.v_pending_handoffs is reachable via the Data API for anon/authenticated)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay to supersede the preliminary grep-based callsite census
  - signed runtime_logs overlay (any SELECT traffic against v_pending_handoffs)
  - signed external_clients overlay (non-repo consumers issuing the documented SELECT * FROM v_pending_handoffs query)
  - signed operator_declaration overlay (is the apex-resa ai_handoffs/ai_tasks orchestration workflow live, deprecated, or superseded?)
- **Labeled technical inferences (retained caveats):**
  - Inclusion of v_pending_handoffs in the 29-definer-view program roster line (docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232) is inferred from the grep match; the captured callsite text truncates before this view's name.
  - The absence of application/runtime code callsites is an absence claim over preliminary repo-grep evidence (callsite areas: docs 3, infra 1), not the signed static_repo overlay.
  - Definer (owner-privilege) execution semantics are inferred from PostgreSQL default view behavior; no security_invoker setting was recorded in the census (PostgreSQL-semantic inference).
  - The view's join/WHERE/ORDER BY/computed-column definition makes it not auto-updatable, so write-class grants are inert for direct DML unless INSTEAD OF triggers or rules are added (PostgreSQL-semantic inference).

### `public.v_project_equipment`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

The view is postgres-owned. The facts file records no security_invoker/reloptions attribute; the sole repo definition creates the view without a security_invoker option, and PostgreSQL views default to definer semantics absent that option (PostgreSQL-semantic inference). That sole repo definition lives under infra/database/source-lineage/apex-resa/ — legacy lineage import material rather than a canonical model needing promotion (out-of-band context, not grounded in this packet's facts: the schema-placement policy characterizes public as legacy/compat only). The census observed zero database dependents and zero inbound/outbound FKs, and the only repo-grep callsites are two documentation listings plus the defining SQL itself — no application-code consumer appears in the grep evidence. Meanwhile the census observed anon and authenticated each holding the full seven-privilege set (DELETE/INSERT/REFERENCES/SELECT/TRIGGER/TRUNCATE/UPDATE) on the view; grant provenance is unknown in this packet. That surface is grossly broader than the empty known-consumer set. If the schema is Data-API exposed — reachability depends on the unresolved in_data_api_exposed_schema dimension — an anon SELECT would read the underlying projects and equipment rows with the owner's rights, and for any underlying table that enforces RLS, definer semantics would bypass caller RLS (PostgreSQL-semantic inference; the RLS posture of projects and equipment is not in this record's facts). Nothing in the facts indicates definer semantics are required, so the provisional lean is harden: convert to security_invoker=true and revoke anon/authenticated grants (at minimum all write/TRIGGER/TRUNCATE/REFERENCES privileges). This remains provisional pending the signed overlays — a runtime or external consumer relying on definer semantics would force reconsideration toward compat.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql:98)
- **Privileges (census-observed):** The census observed anon and authenticated each holding all seven relation privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on the view; grant provenance is unknown in this packet. rls_enabled=false (views cannot carry their own RLS). Under the inferred definer semantics (owner postgres; see retained inference notes), an anon/authenticated SELECT would read the underlying projects and equipment tables with the owner's privileges, and for any underlying table that enforces RLS this would bypass caller RLS (PostgreSQL-semantic inference; base-table RLS posture is not in this record's facts). Whether that access is reachable via the Data-API depends on the unresolved in_data_api_exposed_schema dimension. The projects/equipment join makes the view non-auto-updatable (PostgreSQL-semantic inference), so the write grants are likely inert today, but they are gratuitous surface that should be revoked regardless.
- **Depends on:** `projects`, `equipment`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 3 total, areas {"docs": 2, "infra": 1}. 3 repo-grep callsites, none in application code: docs (2) — docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md line 451 (name listed in a schema inventory) and docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, a line enumerating the 29-view definer-view program; the recorded snippet for that line is truncated before this view's name would appear, so its membership in that enumeration is inferred from the grep hit, not visible verbatim in the recorded text. infra (1) — infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql line 98, which is the CREATE OR REPLACE VIEW definition itself. No known consumers. This is preliminary repo-grep evidence only, NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - sole repo definition is in a source-lineage (apex-resa legacy import) file; whether the deployed prod definition matches this snippet is unverified
  - security_invoker/reloptions state of the deployed view is not recorded in the facts file; definer semantics are inferred from the repo definition plus PostgreSQL view defaults (PostgreSQL-semantic inference)
  - RLS posture of underlying tables projects and equipment is not in the facts file, so the magnitude of any definer-bypass exposure cannot be quantified
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether public-schema Data-API exposure makes anon/authenticated access to the view reachable)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay (authoritative callsite census superseding the preliminary repo-grep evidence)
  - signed runtime_logs overlay (any production reads of the view, and by which role)
  - signed external_clients overlay (external callers selecting the view)
  - signed operator_declaration overlay (whether v_project_equipment is a live consumer surface or dormant apex-resa lineage residue)
  - observed security_invoker/reloptions state of the deployed view (to confirm or refute the inferred definer semantics)
  - verification that the deployed prod definition matches the source-lineage repo definition
  - RLS posture of underlying tables projects and equipment (to size the definer-bypass exposure)
- **Labeled technical inferences (retained caveats):**
  - Definer semantics are inferred, not observed: the facts file carries no security_invoker/reloptions attribute; the sole repo definition creates the view without a security_invoker option, and PostgreSQL views default to definer behavior absent it (PostgreSQL-semantic inference).
  - Definer views read their underlying tables with the owner's privileges, bypassing caller RLS on any underlying table that enforces it (PostgreSQL-semantic inference); whether projects or equipment enforce RLS was not observed in this packet.
  - The projects/equipment join makes the view non-auto-updatable under PostgreSQL rules, so the anon/authenticated write grants are likely inert; this is a PostgreSQL-semantic inference from the repo definition snippet, not observed behavior — revoking them is recommended regardless.

### `public.v_projects_active`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a definer view (owner postgres, security_invoker not set; the view is enumerated in the repo's 29-view definer-view-program spec) over active-project business data (project names, client names, sites, schedule status). The census observed anon and authenticated each holding all seven relation privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on the view — far broader than any plausible consumer need for a read-only reporting join; grant provenance was not observed in this packet. The census found zero database dependents and zero non-documentation callsites: all 9 repo hits are apex-resa lineage docs, the source-lineage schema file, and the 29-view program spec itself, so no evidence exists that definer semantics are required by any consumer. Per the disposition vocabulary, that is exactly the harden case: convert to security_invoker=true and revoke anon/authenticated grants while keeping the view in public as legacy lineage per the 2026-07-09 schema-placement policy. Promote is not indicated because both repo definitions originate from apex-resa source-lineage/docs artifacts, which the 2026-07-09 policy classifies as legacy content permitted to remain in public rather than a canonical model; compat is not indicated because no migrating consumers are evidenced. This is provisional: any of the six unresolved overlay dimensions (in_data_api_exposed_schema, advisor_findings, static_repo, runtime_logs, external_clients, operator_declaration) could reveal a live consumer that changes the revoke scope, though security_invoker conversion would likely still stand.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 2 (docs/architecture/database-lineage/spec/VIEW_DEFINITIONS.md:110; infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql:80)
- **Privileges (census-observed):** The census observed anon and authenticated each holding all seven relation privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on the view; grant provenance is unknown in this packet. RLS on the view itself is false (views cannot carry RLS). Because the view runs with definer semantics under owner postgres, for any underlying table (projects, clients, sites, locations) that enforces RLS, an anon/authenticated SELECT through the view would evaluate without the caller's RLS context (PostgreSQL-semantic inference; the RLS posture of the underlying tables was not in this facts file). Whether the view is reachable by unauthenticated PostgREST callers depends on the unresolved in_data_api_exposed_schema dimension; if that overlay confirms exposure, anon callers could read active-project business data (client names, sites, schedules, completion state). The write privileges are largely inert in practice because a multi-table LEFT JOIN view is not auto-updatable (PostgreSQL-semantic inference), but they constitute grant-hygiene violations that should be revoked regardless.
- **Depends on:** `projects`, `clients`, `sites`, `locations`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 9 total, areas {"docs": 6, "infra": 3}. 9 repo callsites (repo-grep evidence only, NOT the signed static_repo overlay): 6 in docs, 3 in infra. All are documentation/lineage artifacts — the apex-resa pm-project-pss lineage README table row (1 hit), the VIEW_DEFINITIONS.md spec (3 hits: section heading, CREATE statement, COMMENT), the SCHEMA_REFERENCE.md listing (1 hit), the 2026-07-11 signed-overlay-evidence-design spec enumerating the 29-view definer program (1 hit), and the source-lineage schema file infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql (3 hits: comment header, CREATE statement, COMMENT). No application-code, API, or client consumers appear anywhere in the repo grep.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - both repo definitions come from apex-resa lineage docs/source-lineage files, not applied migrations — the live prod definition may have drifted and is unverified offline
  - RLS state and grant posture of the underlying tables (projects, clients, sites, locations) are not in this facts file, so the actual exposure delta from definer semantics cannot be quantified; any RLS-bypass claim is PostgreSQL-semantic inference
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (config-backed determination of whether the view's schema is Data-API exposed and therefore PostgREST-reachable)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay to supersede the preliminary repo-grep callsite census
  - signed runtime_logs overlay (any PostgREST/API reads of v_projects_active)
  - signed external_clients overlay (dashboards, reporting tools, or integrations selecting the view)
  - signed operator_declaration overlay (operator statement on whether apex-resa pm-project-pss lineage consumers are live or retired)
- **Labeled technical inferences (retained caveats):**
  - Definer-semantics RLS bypass is conditional, not observed: for any underlying table (projects, clients, sites, locations) that enforces RLS, a SELECT through this postgres-owned definer view would evaluate without the caller's RLS context (PostgreSQL-semantic inference). The RLS posture of those tables was not observed in this packet.
  - The write privileges (DELETE, INSERT, TRIGGER, TRUNCATE, UPDATE) are assessed as largely inert because a multi-table LEFT JOIN view is not auto-updatable (PostgreSQL-semantic inference); the privilege grants themselves are observed fact and warrant revocation regardless.
  - Grant provenance for the observed anon/authenticated privilege sets is unknown in this packet; only effective privileges were censused.

### `public.v_projects_full`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

v_projects_full is a postgres-owned view carried in the 29-view definer program; the definer characterization (security_invoker not set) traces to the packet's policy block for these views, not to a per-view reloptions observation in the facts file. The census observed anon and authenticated each holding the full seven-privilege suite on the view; grant provenance is unknown in this packet. The view projects financial/commercial fields (contract_value, po_number, project_lead, client/site/location identity), so if the public schema is Data-API exposed — reachability depends on the unresolved in_data_api_exposed_schema dimension — the anon SELECT grant would make these fields readable by unauthenticated PostgREST callers. For any underlying table that enforces RLS, a definer view reads with the owner's privileges and bypasses caller RLS (PostgreSQL-semantic inference); the RLS state of projects/clients/sites/locations was not in this record's facts. The census shows zero database dependents and zero database-deps consumers, and all 15 repo callsites are documentation, lineage schema SQL, or disposition-tooling test fixtures — no application code reads it. The schema-placement-01 DESIGN and IRP-EVIDENCE callsites explicitly left the financial/ops views including v_projects_full OPEN and out of that packet's scope, so this 29-view program is the governing vehicle rather than defer. Definer semantics are not evidenced as required by any consumer, and the observed grants are broader than any known consumer needs, which is the textbook harden case: convert to security_invoker=true and/or revoke the anon/authenticated grants (the write-class privileges are likely inert since a multi-table join view is not auto-updatable (PostgreSQL-semantic inference), but they are grant-hygiene violations regardless). Provisional pending the six signed overlays; a runtime or external-client consumer discovered later could soften the grant revocation but would not justify retaining definer semantics on financially sensitive data.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 2 (docs/architecture/database-lineage/spec/VIEW_DEFINITIONS.md:27; infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql:15)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view; grant provenance is unknown in this packet. The view is owned by postgres and is treated as a definer view per the packet policy block (per-view security_invoker state is not in the facts file); under definer semantics any anon or authenticated SELECT reads all active projects — including contract_value, po_number, and client/site/branch detail — with the owner's privileges, and for any underlying table that enforces RLS this bypasses caller RLS (PostgreSQL-semantic inference; base-table RLS state was not observed in this record's facts). The write-class privileges are likely non-functional because a 4-table LEFT JOIN view is not auto-updatable (PostgreSQL-semantic inference), but they represent maximal over-grant; the SELECT grant to anon is the live exposure lever, with reachability contingent on the unresolved in_data_api_exposed_schema dimension.
- **Depends on:** `projects`, `clients`, `sites`, `locations`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 15 total, areas {"docs": 10, "infra": 5}. 15 repo callsites (repo-grep evidence only, NOT the signed static_repo overlay): 10 in docs, 5 in infra. Docs hits are database-lineage references (apex-resa/pm-project-pss QUICK_START.md, README.md, spec/VIEW_DEFINITIONS.md), knowledge-domain SCHEMA_REFERENCE.md, schema-placement-01 DESIGN.md/IRP-EVIDENCE.md (which explicitly list v_projects_full among financial/ops views left OPEN and out of Packet 01 scope), and the 2026-07-11 signed-overlay-evidence-design spec naming it in the 29-view definer-view program. Infra hits are the lineage source schema infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql (CREATE/COMMENT) and infra/database/schema-placement/tests/test_disposition_schema.py, where it is merely a fixture example oid. No application, API, or serving-runtime consumers appear in the repo.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - defining SQL sourced from repo lineage docs (VIEW_DEFINITIONS.md, source-lineage 04_views.sql), not a live pg_get_viewdef dump — deployed prod definition could drift from these snippets
  - base relations are written schema-unqualified in the view definition; presumed public but unverified offline
  - definer status (security_invoker not set) is policy-sourced from the 29-view program's policy block, not a per-view reloptions observation in the facts file
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether public schema exposure makes this view anon-reachable via PostgREST)
  - signed advisor_findings overlay (Supabase advisor security findings for definer views)
  - signed static_repo overlay to supersede the grep-based callsite census
  - signed runtime_logs overlay (any PostgREST/API reads of v_projects_full in prod)
  - signed external_clients overlay (dashboards, reporting tools, or integrations selecting the view)
  - signed operator_declaration overlay (operator statement on whether any consumer requires definer semantics or anon SELECT on this view)
  - live pg_get_viewdef and reloptions observation for the deployed view (confirm the prod definition matches the repo lineage snippets and the per-view security_invoker state)
- **Labeled technical inferences (retained caveats):**
  - The definer characterization (security_invoker not set) is policy-sourced: it comes from the packet policy block covering the 29-view definer program; the facts file carries no per-view reloptions field.
  - The RLS-bypass and not-auto-updatable claims in the prose are PostgreSQL-semantic inferences, not observations: whether any base table (projects/clients/sites/locations) enforces RLS, and whether the view carries instead-of triggers or rules, were not in this record's facts.

### `public.v_pss_dashboard`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

v_pss_dashboard is a postgres-owned view listed in the 29-view definer program; under definer semantics a caller's SELECT executes with the owner's privileges, so for any underlying table that enforces RLS the view would bypass caller RLS (PostgreSQL-semantic inference — the RLS state of the five underlying tables was not in this record's facts file). The census observed anon and authenticated each holding all seven table-level privileges on the view — the maximal-grant pattern — with no evidence any consumer needs it; grant provenance was not observed in this packet. The census shows zero database dependents and zero database-dep consumers; all 10 repo-grep callsites are docs (6) and infra (4) — the pm-project-pss README, definition text and comments in VIEW_DEFINITIONS.md and source-lineage 04_views.sql, a commented-out test query, a schema-reference listing, and the Ph8 signed-overlay-evidence spec (a docs callsite) naming it in the 29-view definer program — with no application code reading it. Out-of-band context, not grounded in this packet's facts: the view belongs to the legacy apex-resa pm-project-pss lineage, consistent with public-schema legacy/compat status under the 2026-07-09 schema-placement policy, so keeping it in public is acceptable. Its posture is not: convert to security_invoker=true and revoke the anon/authenticated grants (at minimum the six non-SELECT privileges, and SELECT absent a demonstrated consumer). One caution: the pm-project-pss README labels it "PSS portal dashboard", hinting at a possible portal client invisible to repo grep — the harden lean is provisional pending the runtime_logs, external_clients, and operator_declaration overlays. It is not an mcp_* view, so Packet-01 governance (the authorized policy anchor for the two mcp_* views) does not apply.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 2 (docs/architecture/database-lineage/spec/VIEW_DEFINITIONS.md:557; infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql:441)
- **Privileges (census-observed):** The census observed anon and authenticated each holding all seven table-level privileges (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER) on the view; grant provenance was not observed in this packet. The census also observed rls_enabled=false on the view relation itself. Because the view runs with definer semantics, an anon/authenticated SELECT reads pss_studies, pss_engineers, projects, clients, and pss_rfis with the owner's (postgres) privileges; for any of those underlying tables that enforces RLS, this bypasses caller RLS (PostgreSQL-semantic inference — base-table RLS state was not in this record's facts file). Whether that surface is reachable via PostgREST depends on the unresolved in_data_api_exposed_schema dimension. The write privileges are likely inert for direct DML — a multi-join view with a subquery is not auto-updatable (PostgreSQL-semantic inference) — but represent maximal, unjustified grant surface.
- **Depends on:** `pss_studies`, `pss_engineers`, `projects`, `clients`, `pss_rfis`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 10 total, areas {"docs": 6, "infra": 4}. 10 repo callsites, all in docs (6) and infra (4); none in application code. Docs hits: pm-project-pss README ("PSS portal dashboard"), VIEW_DEFINITIONS.md (definition + comment), SCHEMA_REFERENCE.md listing, and the 2026-07-11 signed-overlay-evidence spec (a docs callsite) naming it in the 29-view definer program. Infra hits: source-lineage 04_views.sql (definition + comment) and a commented-out SELECT in 12_pss_test_data.sql. This is repo-grep evidence only — NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - README describes the view as 'PSS portal dashboard' — a possible external portal consumer that repo grep cannot see; cannot rule out live external clients offline
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (config-backed determination whether public-schema exposure makes the observed anon/authenticated privileges reachable via PostgREST)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay (supersedes the preliminary repo-grep callsite data in the facts file)
  - signed runtime_logs overlay (any prod query traffic against v_pss_dashboard, especially under anon/authenticated roles)
  - signed external_clients overlay (whether a PSS portal or other external client selects this view)
  - signed operator_declaration (operator statement on whether the PSS portal lane is live and depends on this view)
- **Labeled technical inferences (retained caveats):**
  - Definer-view RLS bypass is conditional (PostgreSQL-semantic inference): it applies only to underlying tables that enforce RLS, and the RLS state of the five underlying tables was not in this record's facts file.
  - The view's multi-join, subquery-bearing definition is not auto-updatable, so the observed INSERT/UPDATE/DELETE privileges are likely inert for direct DML (PostgreSQL-semantic inference); they remain unjustified grant surface regardless.
  - The census observed rls_enabled=false on the view relation itself; for a definer view the operative exposure lever is bypass of RLS on the underlying tables, not RLS on the view.

### `public.v_scope_financials`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a view over scope-level financial performance data (quoted/recognized revenue, labor cost, gross margin, client names) carrying maximally broad observed grants: the census observed anon and authenticated each holding all seven privileges including SELECT. Grant provenance was not observed in this packet. The repo-lineage definition carries no security_invoker setting; if the live definition matches, the view executes with its owner's (postgres) rights, and for any underlying table that enforces RLS a caller's read would bypass that RLS (PostgreSQL-semantic inference; neither the live invoker setting nor base-table RLS posture is in this record's facts). Whether any caller can actually reach the view through the Data API depends on the unresolved in_data_api_exposed_schema dimension — exposure is not established in this packet. The census shows zero database dependents and zero database-dep consumers, and the 43 repo callsites are entirely docs, lineage specs, Lane-411 design packets, and disposition-tooling test fixtures — no application code reads it — so nothing in the facts evidences a consumer that requires definer semantics or these grants. The view descends from the apex-resa/pm-project-pss lineage (evidenced by the callsite paths); under the ratified schema-placement policy, public is legacy/compat only (out-of-band context, not grounded in this packet's facts). Lane 411 designed a seam.v_scope_financials successor, but that packet is explicitly a no-live design packet, so compat-to-a-live-canonical does not yet apply. Provisional lean: keep the name in public but convert to security_invoker=true and revoke anon/authenticated (at minimum all write-class privileges; SELECT too absent an evidenced consumer). Schema-placement-01 DESIGN.md left this view OPEN/out-of-scope for Packet 01, so it is not part of the mcp_* carve-out; its assignment to the 29-view definer program is inferred from that OPEN status, not directly observed. Final action must wait on the six signed overlay dimensions, since an unlogged external or runtime consumer could downgrade the revoke to invoker-conversion only.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 2 (docs/architecture/database-lineage/spec/VIEW_DEFINITIONS.md:321; infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql:255)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE — the full grant set, far broader than any read consumer needs. Grant provenance was not observed in this packet. If the live view lacks security_invoker (as in the repo-lineage definition), each role's SELECT reads scopes/projects/clients/scope_financial_summaries with the owner's (postgres) rights, bypassing caller RLS on any underlying table that enforces it (PostgreSQL-semantic inference; base-table RLS posture is not in this record's facts). The write-class grants are likely inert because the multi-join view is not auto-updatable (PostgreSQL-semantic inference), but they are unjustified exposure levers regardless. RLS on the view relation itself is observed false (views cannot carry RLS — PostgreSQL-semantic inference; posture depends entirely on grants plus invoker semantics).
- **Depends on:** `scopes`, `projects`, `clients`, `scope_financial_summaries`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 43 total, areas {"PROJECT_STATUS.md": 2, "docs": 17, "infra": 20, "ops": 4}. 43 repo callsites (repo-grep preliminary evidence, not the signed static_repo overlay): infra 20 (almost all schema-placement disposition-tooling test fixtures that use this view name as a sample object, plus the source-lineage 04_views.sql definition), docs 17 (lineage VIEW_DEFINITIONS.md, SCHEMA_REFERENCE.md, Lane-411 design packets referencing a seam.v_scope_financials successor, schema-placement-01 DESIGN/IRP noting this view remains OPEN/out-of-scope), ops 4 (Lane-411 handoff/closeout notes about the seam successor design), PROJECT_STATUS.md 2. No application-code consumers appear anywhere in the grep.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - Lane 411 designed a seam.v_scope_financials successor, but only as a no-live design packet — whether that seam migration is the intended exit path (which would shift this view toward compat/promote) is a cross-lane governance question needing operator input
  - definition evidence is from repo lineage docs (VIEW_DEFINITIONS.md, 04_views.sql), not a live pg_get_viewdef capture — the prod definition, including any security_invoker setting, could have drifted
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether public is in the Data-API exposed schemas set)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay to supersede the preliminary repo-grep callsite evidence
  - signed runtime_logs overlay (any prod SELECT traffic against public.v_scope_financials)
  - signed external_clients overlay (PostgREST/API-key consumers reading the view)
  - signed operator_declaration overlay, specifically: (a) whether any dashboard/reporting consumer depends on definer semantics, and (b) whether Lane 411's seam.v_scope_financials is the intended canonical successor
  - live pg_get_viewdef capture of the prod view, including its security_invoker reloption, to supersede the repo-lineage definition evidence
- **Labeled technical inferences (retained caveats):**
  - Definer execution semantics are inferred, not observed: the repo-lineage definition carries no security_invoker reloption, and a PostgreSQL view without security_invoker=true executes with its owner's rights (PostgreSQL-semantic inference); the live invoker setting was not captured in this packet's facts.
  - Membership in the 29-view definer program is inferred from schema-placement-01 DESIGN.md marking this view OPEN/out-of-scope for Packet 01 (i.e., not part of the mcp_* carve-out); the facts file's snippet of the program list truncates before this view's name, so direct list membership was not observed.
  - RLS bypass applies only to underlying tables that actually enforce RLS; whether scopes/projects/clients/scope_financial_summaries enforce RLS is not in this record's facts (PostgreSQL-semantic inference about definer-view behavior).
  - The write-class grants (DELETE/INSERT/TRUNCATE/UPDATE/TRIGGER/REFERENCES) are likely inert because the multi-join view is not auto-updatable (PostgreSQL-semantic inference); they remain unjustified exposure regardless.

### `public.v_scope_summary`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

v_scope_summary is a postgres-owned view enrolled in the 29-view definer-view program. The census observed anon and authenticated each holding the full seven-privilege set (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER) on the view; grant provenance was not observed and is unknown in this packet. The census shows zero database dependents and zero inbound/outbound FKs, and preliminary repo grep (not the signed static_repo overlay) finds only two documentation callsites: a schema-reference listing, and a grep match at line 232 of the 2026-07-11 signed-overlay evidence spec whose captured snippet is truncated before the view name — its enumeration within the 29-view definer-view program is inferred from that grep match, not visible in the snippet. No application, API, or migration code was found to reference it. Nothing in the facts justifies grants this broad, so the provisional lean is harden: revoke anon/authenticated and convert to security_invoker=true. Two cautions temper this: no defining SQL exists in the repo (definition_count=0), so the underlying relations cannot be enumerated offline — neither whether an invoker-rights conversion would break a legitimate consumer, nor, for any underlying table that enforces RLS, which policies would then govern (PostgreSQL-semantic inference) — and all six evidence dimensions (in_data_api_exposed_schema, advisor_findings, static_repo, runtime_logs, external_clients, operator_declaration) remain unsigned. Whether the view is reachable through the Data API depends on the unresolved in_data_api_exposed_schema dimension. If runtime_logs or external_clients evidence later shows a live consumer relying on definer semantics, the disposition should be revisited toward compat or retain; if the operator_declaration marks it dead, the operator may prefer removal — an option outside this packet's five-item disposition vocabulary — as the cheaper end state. This is a provisional proposal for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view — a grant breadth far exceeding any observed consumer need (zero database dependents; docs-only repo-grep callsites). Grant provenance was not observed; it is unknown in this packet. The view is postgres-owned and enrolled in the definer-view program; under definer semantics a SELECT by either role executes with the owner's rights, so for any underlying table that enforces RLS the read would bypass caller-level RLS (PostgreSQL-semantic inference — the underlying relations are not enumerated in this packet's facts). The write privileges are an additional exposure lever only if the view is auto-updatable or carries INSTEAD OF triggers/rules, which cannot be determined without the view definition (PostgreSQL-semantic inference). Whether any of this is reachable through the Data API (PostgREST) depends on the unresolved in_data_api_exposed_schema dimension; at the SQL-grant layer both public-facing roles currently hold the full seven-privilege set.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 2 total, areas {"docs": 2}. Repo grep (NOT the signed static_repo overlay) finds 2 callsites, both in docs: docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md:452 lists it alongside v_pss_dashboard and v_scope_financials, and a grep match at docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232 lands inside that spec's 29-view definer-view enumeration — the captured snippet is truncated before the view name, so its presence in that list is inferred from the grep match rather than visible in the snippet. No application, API, or migration code references were found; the name appears only in documentation.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo (definition_count=0) — underlying relations unknown; cannot assess offline whether a security_invoker conversion would break a legitimate consumer, nor, for any underlying table that enforces RLS, which policies would then govern (PostgreSQL-semantic inference)
  - view provenance and intended consumer unestablished — preliminary repo grep finds no application code or migrations referencing it; operator_declaration needed to distinguish dormant-legacy from externally-consumed
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any production reads of v_scope_summary)
  - signed external_clients overlay (non-repo consumers, e.g. BI tools or external dashboards)
  - signed operator_declaration overlay (is this view intended to live, and for whom)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed in_data_api_exposed_schema overlay (config-backed: whether the public schema / this view is reachable via PostgREST)
  - signed static_repo overlay to supersede the preliminary repo-grep callsite evidence
  - authoritative view definition from prod (pg_get_viewdef) to enumerate underlying relations and assess base-table RLS posture before any security_invoker conversion
- **Labeled technical inferences (retained caveats):**
  - The second repo-grep callsite's captured snippet is truncated before the view name; the view's enumeration in the 29-view definer-view program is inferred from the grep match, not visible in the snippet.
  - The facts file does not directly record the view's security_invoker reloption; the definer-view classification derives from the view's enrollment in the 29-view definer-view program.
  - Definer-rights RLS bypass applies only to underlying tables that enforce RLS; the underlying relations are not enumerated in this packet's facts (PostgreSQL-semantic inference).
  - Write privileges on a view are exercisable only if the view is auto-updatable or has INSTEAD OF triggers/rules; this cannot be determined without the view definition (PostgreSQL-semantic inference).

### `public.v_tcc_calc_input`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned definer view carried in the 29-view definer-view program, with all seven table-level privileges observed for both anon and authenticated, zero database dependents, zero inbound/outbound FKs, and a single docs-only repo callsite — no application code references it and no defining SQL was found in the repo. Definer semantics plus blanket anon write-capable grants on a view with no evidenced consumer is exactly the exposure posture the schema-placement policy targets: nothing in the facts justifies definer semantics or grants this broad. The provisional lean is harden: convert to security_invoker=true and revoke the anon/authenticated grants (at minimum the write privileges, which no view consumer should need). Promote is not indicated because with no repo definition there is no canonical model to relocate; compat is not indicated because there is no evidenced migrating consumer. One consideration is out-of-band context, not grounded in this packet's facts: the view's name suggests it may feed a TCC calc-engine consumer, so the signed runtime_logs, external_clients, and operator_declaration overlays must clear before any grant revocation is applied. Whether any such client could reach the view through the Data API depends on the unresolved in_data_api_exposed_schema dimension. This is a provisional proposal for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view; grant provenance was not observed in this packet. On a definer view owned by postgres, SELECT executes against the underlying relations with the owner's privileges, and for any underlying table that enforces RLS this would bypass caller RLS (PostgreSQL-semantic inference) — whether the base tables enforce RLS was not in this record's facts, and the base relations themselves are unknown because no defining SQL was found. If the view is auto-updatable, the INSERT/UPDATE/DELETE grants could pass writes through to base tables as postgres (PostgreSQL-semantic inference). PostgreSQL does not support TRUNCATE on views, so that grant is inert as held, though still inappropriate for these roles (PostgreSQL-semantic inference). With zero evidenced consumers, every one of these grants is broader than need; whether this surface is reachable via the Data API depends on the unresolved in_data_api_exposed_schema dimension.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 1 total, areas {"docs": 1}. One repo callsite total, in docs only: a grep hit at docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, inside the enumerated 29-view definer-view-program list in the census/spec artifact itself — not a consumer. The captured snippet at that line is truncated and does not visibly contain v_tcc_calc_input; the view's membership in that list at that line is inferred from the grep match, not directly observed in the snippet. No application, migration, or tooling callsites were found. This is preliminary repo-grep evidence only, not the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo — the view's base relations and exposure surface are unknown; dependencies could not be parsed from a definition (database census observed zero dependents)
  - the view name suggests a possible TCC calc-engine consumer (out-of-band context, not grounded in this packet's facts); any such runtime or external consumer must be ruled out via the runtime_logs, external_clients, and operator_declaration overlays before grant revocation
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any live reads or writes of public.v_tcc_calc_input)
  - signed external_clients overlay (out-of-repo clients selecting this view; Data-API/PostgREST reachability depends on the unresolved in_data_api_exposed_schema dimension)
  - signed operator_declaration overlay — whether any lane still depends on this view and whether it is intentionally orphaned
  - signed advisor_findings overlay (advisor security findings for this definer view)
  - signed in_data_api_exposed_schema overlay (whether the view sits in a Data-API-exposed schema; exposure is not established by this packet)
  - signed static_repo overlay to supersede the preliminary repo-grep callsite snapshot
  - authoritative view definition from the database (pg_get_viewdef), since no defining SQL was found in the repo — needed to enumerate base relations before changing definer semantics
- **Labeled technical inferences (retained caveats):**
  - The TRIGGER privilege observed for anon/authenticated would permit those roles to create INSTEAD OF triggers on the view — an additional write-path exposure lever beyond the DML grants (PostgreSQL-semantic inference).

### `public.v_tcc_etu_catalog`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

The census observed both anon and authenticated holding the full seven-privilege set (SELECT plus DELETE/INSERT/UPDATE/TRUNCATE/TRIGGER/REFERENCES) on this postgres-owned view; grant provenance was not observed in this packet. Those effective grants are demonstrably broader than any plausible consumer of a catalog-style read view, which per policy is a clean harden trigger even before consumer evidence lands. The view is enumerated in the repo design doc's 29-view definer-view program list, and PostgreSQL views execute with definer (owner) semantics unless security_invoker is set (PostgreSQL-semantic inference); no defining SQL exists in the repo (definition_count 0), no database dependents exist, and the only repo callsite is that design-doc listing, so nothing in the facts establishes that definer semantics are required. The name suggests a TCC electronic-trip-unit catalog surface (name-based inference, not an observed fact); whether the view is reachable via the Data API/PostgREST depends on the unresolved in_data_api_exposed_schema dimension, and if it is reachable a live page could read it — so the SELECT-path hardening step (security_invoker conversion and/or anon SELECT revoke) must be sequenced behind the runtime_logs, external_clients, and in_data_api_exposed_schema overlays to avoid breaking an unobserved consumer. The write-privilege revocations are lower-risk but not risk-free: TRUNCATE and REFERENCES are inert on views, while DELETE/INSERT/UPDATE can be live write paths if the view is auto-updatable (PostgreSQL-semantic inference), and with the definition unavailable that cannot be ruled out — so the write-privilege revocations are sequenced behind the runtime_logs overlay and the pg_get_viewdef capture rather than proposed unconditionally. This is a provisional lean for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view; grant provenance is unknown in this packet. RLS is not enabled on the view (observed), and a view does not itself provide caller RLS protection (PostgreSQL-semantic inference). PostgreSQL views execute with the owner's (definer) authority unless security_invoker is set, so for any underlying base table that enforces RLS, an anon/authenticated SELECT through this postgres-owned view would bypass caller RLS (PostgreSQL-semantic inference — the base relations and their RLS status are not in this packet's facts, and with definition_count 0 that surface is unquantified). Of the six non-SELECT privileges, TRUNCATE and REFERENCES are inert on views, but DELETE/INSERT/UPDATE may constitute live write paths if the view is auto-updatable (PostgreSQL-semantic inference); all six exceed any plausible consumer need for a catalog-style read view.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 1 total, areas {"docs": 1}. 1 repo callsite total, area = docs only: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, where the view appears in the enumerated 29-view definer-view program list. No application, migration, or tooling code references the name. This is preliminary repo-grep evidence only — it is NOT the signed static_repo overlay (static_repo state: not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo (definition_count 0) — base-relation dependencies unknown; the potential definer RLS-bypass surface and any auto-updatable write path cannot be quantified until pg_get_viewdef is captured from prod
  - view name suggests a TCC/ETU catalog serving surface (name-based inference) with possible live readers not visible to repo grep; SELECT-path hardening sequencing depends on runtime_logs, external_clients, and in_data_api_exposed_schema evidence
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether public is a Data-API-exposed schema and this view is therefore reachable via PostgREST)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay to supersede the preliminary repo-grep callsite evidence
  - signed runtime_logs overlay (any observed reads of or writes to the view in prod)
  - signed external_clients overlay (Data-API/PostgREST or other out-of-repo consumers)
  - signed operator_declaration overlay — specifically whether any live application surface (e.g. a TCC/ETU catalog page) reads this view and whether definer semantics are intentionally relied upon
  - prod view definition (pg_get_viewdef) to establish base-relation dependencies, determine whether the view is auto-updatable, and quantify the potential definer RLS-bypass surface
- **Labeled technical inferences (retained caveats):**
  - The suggestion that this view backs a live TCC/ETU catalog page is name-based inference from the object name, not a fact in this packet; it is used only to argue for cautious sequencing of SELECT-path hardening.
  - PostgreSQL views execute with definer (owner) semantics unless security_invoker is set; any caller-RLS bypass applies only to underlying tables that enforce RLS, and base-table RLS status is not in this packet's facts (PostgreSQL-semantic inference).
  - Simple PostgreSQL views are auto-updatable, so the granted DELETE/INSERT/UPDATE may be live write paths; with the view definition unavailable (definition_count 0) this cannot be ruled out (PostgreSQL-semantic inference). TRUNCATE and REFERENCES are inert on views.

### `public.v_tcc_etu_coefficients`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

The census observed anon and authenticated each holding the full seven-privilege set (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on this postgres-owned view — far broader than any plausible consumer need for a read-only coefficients view. The sole repo-grep callsite is a docs line in docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md that enumerates the 29-view definer-view program; the census attributes that hit to this view, though the captured snippet is truncated and does not visibly contain the view name (see retained inference notes). It is not one of the two mcp_* views governed under Packet-01. No database dependents exist, no defining SQL was found in the repo (definition_count=0), and no application, migration, or client code references the view, so revoking the anon/authenticated grants and/or setting security_invoker=true carries minimal apparent breakage risk pending signed overlays. Out-of-band context, not grounded in this packet's facts: the schema-placement policy treats broad public-schema view grants of this kind as exactly the exposure lever the definer-view program targets. The name suggests TCC-lane data that might argue for promote into a named schema, but with definition_count=0 that cannot be assessed; harden is the defensible provisional lean, with promote-vs-compat re-evaluable once the live view definition and the operator_declaration overlay arrive. This is a PROVISIONAL proposal for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on this view (owner: postgres; rls_enabled=false). Grant provenance was not observed in this packet. The security_invoker setting was not captured in this facts file; PostgreSQL views execute with definer semantics unless security_invoker=true, and the view's enumeration in the definer-view program is consistent with definer semantics (PostgreSQL-semantic inference). Under definer semantics, for any underlying table that enforces RLS, a SELECT through this view would bypass caller RLS and read with the owner's privileges (PostgreSQL-semantic inference); the view's underlying relations and their RLS state were not in this facts file. Whether these grants are reachable by anon Data-API/PostgREST clients depends on the unresolved in_data_api_exposed_schema dimension. The write-shaped privileges are surplus relative to the view's apparent read-only purpose and are proposed for revocation under harden; whether they are exercisable (auto-updatability) cannot be determined without the view definition.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 1 total, areas {"docs": 1}. 1 repo-grep callsite, in docs only: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, a line enumerating the 29-view definer-view program; the census attributes the hit to this view, but the captured snippet is truncated and does not visibly contain 'v_tcc_etu_coefficients'. No application, migration, or client code references were found by grep. This is preliminary repo-grep evidence only, NOT the signed static_repo overlay (static_repo: not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo (definition_count=0); underlying relations, security_invoker state, and definer-necessity cannot be assessed from repo sources
  - no application consumer identified (0 database dependents; sole repo-grep callsite is docs-only) — view may be orphaned; whether promote into a named TCC schema is the better end-state cannot be judged without the live view definition
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (config-backed Data-API exposure state for the public schema)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay (to supersede the preliminary repo-grep callsite evidence)
  - signed runtime_logs overlay (any live query traffic against the view)
  - signed external_clients overlay (dashboard/PostgREST/third-party consumers)
  - signed operator_declaration overlay (whether the TCC LV breaker lane still consumes this view or it is orphaned; whether definer semantics are intentionally required)
  - live view definition (pg_get_viewdef) to establish underlying relations and security_invoker state, and to adjudicate harden vs promote
- **Labeled technical inferences (retained caveats):**
  - The sole repo-grep callsite snippet is truncated and does not visibly contain 'v_tcc_etu_coefficients'; attribution of the 29-view definer-view program line to this view rests on the census's grep attribution rather than visible line text.
  - Definer execution semantics are inferred, not observed: the facts file does not capture the security_invoker reloption; PostgreSQL views default to definer semantics absent security_invoker=true, and enrollment in the definer-view program is consistent with that (PostgreSQL-semantic inference).
  - Whether the view is auto-updatable — which would make the write-shaped grants exercisable — cannot be determined without the view definition; simple views are auto-updatable under PostgreSQL semantics (PostgreSQL-semantic inference). The surplus-grant judgment under harden does not depend on this.

### `public.v_tcc_tmt_catalog`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned view with rls_enabled=false observed in the census; its definer mode (security_invoker not set) is taken from the 29-view definer-program policy anchor under which this record set was produced, not from a per-view attribute in this facts file. The census observed anon and authenticated each holding all seven table-level privileges on the view — DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE; grant provenance is unknown in this packet. That posture is indefensible for what the view's name indicates (a name-based inference) is a read-only TMT (thermal-magnetic trip) catalog view in the TCC lane: no database objects depend on it, no defining SQL was found in the repo, and the only repo-grep callsite is the disposition-program design doc itself, so nothing in the census justifies write grants. The provisional fix is to revoke all non-SELECT privileges from anon/authenticated immediately, and to decide anon SELECT retention and any security_invoker=true conversion once the in_data_api_exposed_schema, runtime_logs, and external_clients overlays confirm whether an anon-facing consumer actually reads it (a public TCC reference page is a plausible candidate — out-of-band context, not grounded in this packet's facts). Promote-to-named-schema is a plausible follow-on for a catalog model, but with definition_count=0 the view's underlying relations are unknown, so harden is the defensible lean and relocation is deferred to evidence. This remains provisional pending the six signed overlay dimensions and the operator declaration on intended consumers.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view; grant provenance is unknown in this packet. The view is owned by postgres and, per the definer-program policy anchor, runs in definer mode; under PostgreSQL semantics a definer view executes against its underlying relations with the owner's privileges, so for any underlying relation that enforces RLS, caller RLS would be bypassed (PostgreSQL-semantic inference — the underlying relations are unknown here, definition_count=0). If the view is simple enough to be auto-updatable, the observed write privileges could mutate underlying rows the same way (PostgreSQL-semantic inference). Whether any of this is reachable through the Data API depends on the unresolved in_data_api_exposed_schema dimension. What was observed is severe on its face: full seven-privilege grants to both anon and authenticated on a postgres-owned view.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 1 total, areas {"docs": 1}. 1 repo-grep callsite total, in docs only: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, where the view is merely enumerated as one of the 29-view definer program. No application, migration, or SQL callsites found by grep. This is preliminary repo-grep evidence, not the signed static_repo overlay, so out-of-repo consumers (e.g. Data-API clients — reachability itself contingent on the unresolved in_data_api_exposed_schema dimension) cannot be excluded from it.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo (definition_count=0) — underlying relations unknown, so the definer-privilege blast radius and auto-updatability cannot be enumerated
  - a possible anon-facing runtime consumer (e.g. a public TCC reference page — out-of-band context, not grounded in this packet's facts) cannot be confirmed or ruled out; this gates whether anon SELECT survives hardening
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether the public schema / this view is exposed via the Data API)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay to supersede the preliminary repo-grep callsite data
  - signed runtime_logs overlay (whether anything reads this view in prod, and under which roles)
  - signed external_clients overlay (Data-API / PostgREST clients touching the view — reachability contingent on the unresolved in_data_api_exposed_schema dimension)
  - signed operator_declaration overlay (whether an anon-visible TCC TMT catalog read is intended; whether anon SELECT may remain post-harden)
  - authoritative view definition (from prod catalog or repo) to enumerate underlying relations and assess definer blast radius and auto-updatability before any security_invoker conversion
- **Labeled technical inferences (retained caveats):**
  - Definer mode (security_invoker not set) is asserted by the 29-view definer-program policy anchor for this record set; the facts file carries no reloptions/security_invoker attribute, so it is not a per-view observation.
  - The 'TMT (thermal-magnetic trip) catalog' characterization and the read-only expectation are name-based inferences; with definition_count=0, nothing in the facts confirms the view's actual content.
  - dependencies=[] reflects that no underlying relations could be derived (definitions[] is empty in the facts file), not that the view is known to reference nothing.
  - Definer-view RLS bypass (for any underlying relation that enforces RLS) and simple-view auto-updatability are PostgreSQL-semantic inferences, not per-view observations; both require the authoritative view definition to confirm.

### `public.v_tcc_tmt_curve_data`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned view enumerated in the repo's 29-view definer-view program (per the docs callsite), and the census observed anon and authenticated each holding the maximal seven-privilege set on it — far broader than any read-only curve-data consumer could need; grant provenance was not observed in this packet. The census found zero database dependents and zero inbound/outbound FKs, and the only repo callsite is the disposition-ledger design doc that enumerates the 29-view program itself — no application code in the repo reads this view. No defining SQL exists in the repo (definition_count=0), so definer semantics cannot be shown to be required and the underlying relations the view exposes are unknown. Under the vocabulary, that is squarely harden: convert to security_invoker=true and revoke (at minimum) the write-class privileges from anon/authenticated. The name suggests it serves TCC thermal-magnetic-trip curve data (name-based inference only); with zero code callsites, any live consumer would be an external/dynamic client invisible to repo grep, and whether such a client can reach the view at all depends on the unresolved in_data_api_exposed_schema dimension. Anon SELECT revocation must therefore not be executed until the in_data_api_exposed_schema, runtime_logs, and external_clients overlays confirm or refute a live external consumer. Provisional pending the signed overlays and operator review.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges (census-observed):** The census observed anon and authenticated each holding the full privilege set on the view: SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER. Grant provenance was not observed in this packet. On a definer view owned by postgres, a caller's SELECT executes with the owner's privileges, and for any underlying table that enforces RLS, caller RLS would not apply (PostgreSQL-semantic inference); the view's underlying relations and their RLS posture were not observed because no definition was found. These grants are reachable by unauthenticated clients only if the view's schema is Data-API exposed, which depends on the unresolved in_data_api_exposed_schema dimension. The write-class grants (INSERT/UPDATE/DELETE/TRUNCATE) are an additional lever if the view is auto-updatable (PostgreSQL-semantic inference), which cannot be ruled out because no definition was found. The observed grants are unambiguously broader than any plausible consumer need.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 1 total, areas {"docs": 1}. 1 repo callsite, in docs only (callsite_areas: docs=1): docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, the disposition-ledger spec's own enumeration of the 29-view definer program — a self-referential governance mention, not a consumer. The captured snippet is truncated before this view's name appears, so its inclusion in that enumeration is inferred from the grep match rather than visible in the snippet text. No application, migration, or test code references the view name. This is repo-grep evidence only; the signed static_repo overlay does not yet exist (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL found in repo (definition_count=0): underlying relations, their RLS posture, and auto-updatability are all unknown
  - consumer surface ambiguous: zero code callsites means any live consumer would be external/dynamic and invisible to repo grep; whether such a consumer can reach the view depends on the unresolved in_data_api_exposed_schema dimension
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether this view's schema is Data-API exposed, making the observed anon grants reachable)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay (to supersede the preliminary repo-grep callsite evidence)
  - signed runtime_logs overlay (any SELECT traffic from anon/authenticated against this view)
  - signed external_clients overlay (Data-API / PostgREST clients reading v_tcc_tmt_curve_data)
  - signed operator_declaration overlay (operator statement of intended consumers — specifically whether any live application surface, e.g. a TCC curve page, reads this view — and whether definer semantics are intentionally required)
  - recovered view definition (e.g., pg_get_viewdef capture from prod) to establish the underlying relations, whether any of them enforce RLS, and whether the view is auto-updatable, before deciding the scope of grant revocation
- **Labeled technical inferences (retained caveats):**
  - Attribution of this view to the docs 29-view enumeration is inferred from the grep match; the captured callsite snippet truncates before this view's name appears.
  - rls_enabled=false was observed on this relation, but RLS applies to tables, not plain views; the observation carries no posture weight (PostgreSQL-semantic note).
  - Definer-view consequences cited in this record — caller queries executing with owner privileges, and caller RLS not applying to any underlying table that enforces RLS — are PostgreSQL-semantic inference; the underlying relations and their RLS posture were not observed in this packet.
  - Whether the view is auto-updatable (which would make the observed write-class grants exercisable) cannot be determined without the view definition (PostgreSQL-semantic inference).

### `public.vw_etu_browse`

**Proposed disposition (PROVISIONAL): `harden`** — confidence high

vw_etu_browse is a postgres-owned view (security_invoker not set, so it carries definer semantics) published side-by-side as a derived read-model during TCC Phase 5 Tier B Slice 2, with adoption into the runtime contract explicitly HELD (the runtime contract surface remains vw_trip_unit_cascade; G2-RULES-GUIDE gates D-2 and AG-2 block adoption pending a concrete consumer and trip-type identity harmonization). The census shows zero database dependents and zero database-dep consumers, and the repo's own historical consumer sweep recorded "vw_etu_browse: NONE FOUND" — all 43 repo-grep callsites are governance/handoff prose, not application code. Meanwhile the census observed anon and authenticated each holding all seven privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on the view; grant provenance is unknown in this packet. Because security_invoker is not set, reads through the view execute with the postgres owner's rights and would bypass caller RLS on any underlying table that enforces it (PostgreSQL-semantic inference); whether anon/authenticated can actually reach the view through the Data API depends on the unresolved in_data_api_exposed_schema dimension. With no recorded consumer to serve, these grants are unjustified surface. Harden is the robust lean regardless of overlay outcomes: at minimum revoke the write-class privileges and anon SELECT, and convert to security_invoker=true (the census records zero dependents and zero database-dep consumers, so no recorded consumer depends on definer semantics); if a hidden runtime/external consumer surfaces in the signed overlays, only the extent of grant narrowing changes, not the direction. This does not disturb the TCC-lane adoption gates — the view stays published; any future adoption packet (D-2) can re-grant deliberately. Not compat (no migrating consumers — none were found in this packet's evidence) and not promote (it is a derived read-model, not the canonical surface).

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (ops/agents/handoffs/2026-04-27-tcc-phase-5-tier-b-vw-etu-browse-execution-handoff.md:24)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view; grant provenance (explicit GRANT vs default privileges) was not observed in this packet and is unknown. RLS is not enabled on the view (observed). security_invoker is not set, so any SELECT through this postgres-owned view executes with the owner's rights; for any underlying table that enforces RLS, that would bypass caller RLS (PostgreSQL-semantic inference — the underlying relations and their RLS posture are not captured in this packet's facts). Actual anon/authenticated reachability via the Data API depends on the unresolved in_data_api_exposed_schema dimension. With zero recorded consumers, every one of these grants is unjustified surface; the write-class privileges are pure posture noise on a read-model view.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 43 total, areas {"docs": 1, "ops": 38, "reference": 4}. 43 repo callsites (repo-grep preliminary evidence, NOT the signed static_repo overlay): 38 in ops/agents/handoffs (TCC Phase 5 Tier B execution/governance packets, 2026-04-26 through 2026-04-29), 4 in reference/tcc/G2-RULES-GUIDE.md (F-10 side-by-side publication, D-2 adoption gate, AG-2 trip-type harmonization gate), 1 in docs/superpowers/specs (the 2026-07-11 signed-overlay design listing it among the 29-view definer program). No application-code consumers appear anywhere in the grep evidence; the 2026-04-27 consumer-need handoff records the repo-wide grep result "vw_etu_browse: NONE FOUND" and notes the view omits trip_type_id, which the /cascade consumers require — a structural mismatch that further confirms non-adoption.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - definition snippet in the facts file is a handoff narrative, not the view body SQL: FROM-clause relations cannot be parsed (the repo SQL mirror is referenced at source-domains/tcc_v5_backend/migrations/maint/vw_etu_browse.sql but not captured in the facts file); lineage parity with tcc_etu_sensors / vw_trip_unit_cascade implies derivation but is inference, not a parsed dependency list
  - cross-lane coordination: TCC G2-RULES-GUIDE gates D-2/AG-2 govern future ADOPTION of this view; hardening must record that any adoption reopen requires a deliberate grant/posture revisit under that gate, and the TCC lane should be notified of the posture change
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether Data API schema exposure makes this view reachable to anon/authenticated via PostgREST)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay (supersedes the preliminary repo-grep callsite evidence in the facts file)
  - signed runtime_logs overlay (confirm zero PostgREST/API reads of vw_etu_browse)
  - signed external_clients overlay (confirm no out-of-repo consumer)
  - signed operator_declaration overlay (operator confirms the TCC adoption HOLD still stands and no undocumented consumer exists)
  - actual view definition SQL (prod catalog dump or the repo mirror source-domains/tcc_v5_backend/migrations/maint/vw_etu_browse.sql) to enumerate underlying relations and verify their RLS posture before any security_invoker=true conversion
- **Labeled technical inferences (retained caveats):**
  - Definer-semantics exposure is PostgreSQL-semantic inference: with security_invoker unset on a postgres-owned view, reads execute with the owner's rights and would bypass caller RLS on any underlying table that enforces it; the underlying relations and their RLS posture are not captured in this packet's facts, and actual reachability further depends on the unresolved in_data_api_exposed_schema dimension.
  - The lineage-parity linkage (handoff-recorded row-count parity vw_etu_browse = 17,831 = tcc_etu_sensors = vw_trip_unit_cascade) implies derivation from the canonical ETU surface but is inference from narrative evidence, not a parsed dependency list; dependencies=[] reflects the absence of captured view body SQL.

### `public.vw_etu_calc_context`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a TCC Phase 5 Tier B derived ETU read-model that was authored, lineage-proven (17,831-row parity vs tcc_etu_sensors and vw_sensor_calc_context), and published side-by-side — but its runtime adoption was explicitly placed on HOLD, with vw_sensor_calc_context remaining the runtime contract surface and reopen governed by trigger D-1 in reference/tcc/G2-RULES-GUIDE.md. Tier B Slice 1 for this view is recorded closed PASS (DEC-006, per the 2026-04-28 handoff); the adoption HOLD is recorded separately in the 2026-04-27 adoption handoff. The census observed zero database dependents, and the 2026-04-27 consumer-need handoff records a scoped consumer grep (source-domains/tcc_v5_backend/, source-domains/neta-ett-study-material/Development/, frontend source files, and apex-power-ops-platform) returning "NONE FOUND"; all 35 repo callsites are handoff/governance/reference prose, not code. A view on which the census observed anon and authenticated holding all seven relation privileges, with no evidenced consumer of any kind, is unexposed-need attack surface at the database grant layer; whether that surface is additionally network-reachable through the Data API depends on the unresolved in_data_api_exposed_schema dimension. Hardening (security_invoker=true and/or revoke anon+authenticated) is compatible with the TCC HOLD: the view stays published for the future D-1 adoption packet, which can grant exactly what its concrete consumer needs. Promote was considered (it is arguably a canonical read-model belonging in a named schema) but relocation is premature while adoption itself is HOLD and owned by the TCC lane; defer was rejected because the security-posture question is separable from the adoption question, though the operator should confirm cross-lane coordination. Provisional pending the six signed overlays and recovery of the actual defining SQL.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (ops/agents/handoffs/2026-04-27-tcc-phase-5-tier-b-vw-etu-calc-context-execution-handoff.md:24)
- **Privileges (census-observed):** The census observed anon and authenticated each holding all seven relation privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on this postgres-owned view (security_invoker not set, rls_enabled=false). Grant provenance was not observed in this packet. Because security_invoker is not set, base-relation access through the view is evaluated as the view owner rather than the caller, so for any underlying relation that enforces RLS, caller policies would not apply (PostgreSQL-semantic inference); the base relations themselves (likely public.tcc_etu_sensors / public.vw_sensor_calc_context, ~17,831 rows per the lineage-parity proofs) are inferred, not parsed from a recovered definition, and whether they enforce RLS was not in this record's facts. Whether anon or authenticated can reach this view through the Data API depends on the unresolved in_data_api_exposed_schema dimension. The write-side privileges are a gratuitous over-grant on a derived read-model, and since no consumer of any kind is evidenced, the observed grants are strictly broader than need — the strongest possible case for revoking anon/authenticated and converting to security_invoker.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 35 total, areas {"docs": 1, "ops": 31, "reference": 3}. 35 repo callsites (repo-grep evidence only, NOT the signed static_repo overlay): 31 in ops (TCC Phase 5 Tier B execution/adoption/closeout handoffs, 2026-04-26 through 2026-04-29), 3 in reference (reference/tcc/G2-RULES-GUIDE.md — F-10 side-by-side publication fact and D-1 adoption reopen trigger), 1 in docs (the 2026-07-11 signed-overlay evidence design spec listing it among the 29-view definer program). Every callsite is governance/documentation prose; none is application code. Notably, the 2026-04-27 consumer-need handoff records a scoped consumer grep (source-domains/tcc_v5_backend/, source-domains/neta-ett-study-material/Development/, frontend source files, and apex-power-ops-platform) returning "NONE FOUND" for this view, and the 2026-04-27 adoption handoff records adoption HOLD, with vw_sensor_calc_context remaining the runtime contract surface.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - no defining SQL body found in repo: the single definition hit is handoff narrative around CREATE OR REPLACE VIEW with no FROM clause; base relations (likely public.vw_sensor_calc_context / public.tcc_etu_sensors per lineage-parity proofs) are inferred, not parsed — the repo SQL mirror source-domains/tcc_v5_backend/migrations/maint/vw_etu_calc_context.sql is referenced but its contents are not in the facts file
  - cross-lane governance: TCC Phase 5 Tier B Slice 1 for this view is recorded closed PASS (DEC-006, per the 2026-04-28 handoff) with adoption HOLD recorded separately (2026-04-27 adoption handoff) and a documented reopen trigger (G2-RULES-GUIDE D-1); hardening should be sequenced so it does not silently foreclose or complicate the documented adoption reopen path
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether the public schema / this view is PostgREST-exposed)
  - signed advisor_findings overlay (Supabase advisor security findings for this definer view)
  - signed static_repo overlay (to supersede the repo-grep callsite evidence; should carry the scope qualifier that the 2026-04-27 consumer grep covered an enumerated directory set, not literally the whole repo)
  - signed runtime_logs overlay (confirm zero production reads of vw_etu_calc_context)
  - signed external_clients overlay (confirm no out-of-repo consumers, e.g. tcc_v5_backend service deployments)
  - signed operator_declaration overlay (operator confirmation that TCC Tier B HOLD status stands and hardening may proceed independent of the D-1 adoption decision)
  - actual view definition SQL (pg_get_viewdef or source-domains/tcc_v5_backend/migrations/maint/vw_etu_calc_context.sql) to establish the true base-relation read set before converting to security_invoker
- **Labeled technical inferences (retained caveats):**
  - PostgreSQL-semantic inference: with security_invoker not set, base-relation access through this view is evaluated as the view owner (postgres), so for any underlying relation that enforces RLS, caller policies would not apply; whether the underlying relations enforce RLS was not in this record's facts file.
  - Base relations (likely public.tcc_etu_sensors and public.vw_sensor_calc_context) are inferred from lineage-parity proofs quoted in handoff prose, not parsed from a recovered view definition.
  - The 2026-04-27 consumer-need grep that returned NONE FOUND covered an enumerated directory set (source-domains/tcc_v5_backend/, source-domains/neta-ett-study-material/Development/, frontend source files, apex-power-ops-platform), not literally the entire repo; the signed static_repo overlay should carry this scope qualifier when it supersedes this evidence.

### `public.vw_sensor_calc_context`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is an actively consumed runtime contract surface for the TCC lane — reference/tcc/G2-RULES-GUIDE.md:262 names it a runtime contract surface that remains authoritative pending all gates, and the control-plane-api NETA router issues live SELECTs against it (services/neta/router.py:1597, 5307, 5369) — so retirement or relocation is not on the table here. The grant posture is the problem: the census observed anon and authenticated each holding all seven privileges (DELETE/INSERT/REFERENCES/SELECT/TRIGGER/TRUNCATE/UPDATE) on this postgres-owned view over five tcc_* base relations. Grant provenance was not observed in this packet, and no callsite in the facts shows any anon/authenticated consumer. Proposed hardening is staged: (1) revoke the anon/authenticated grants now — repo-grep callsites (preliminary evidence, not the signed static_repo overlay) show the consumers are the API service and SQL function bodies, not Data-API roles; (2) hold the security_invoker=true conversion until the serving-role and base-relation grant posture on tcc.* is proven, because fn_calculate_test_currents and fn_evaluate_test_results read this view from inside plpgsql bodies and invoker semantics could change what those reads resolve (PostgreSQL-semantic inference). Not promote, despite the schema-placement policy preferring named schemas: per ops/agents/inbox/done/2026-05-30-cc-d012-phase2-expand.md, the public.tcc_* base tables were relocated to tcc.* with public surfaces retained as views over tcc.*, and reference/tcc/G2-RULES-GUIDE.md (F-10) deliberately keeps this view as the runtime contract while Tier B successors (vw_etu_calc_context) mature under that lane's gates — relocation is that lane's decision; only the exposure posture is this packet's remit. Not defer, the plausible rival reading given the same G2 authoritative-pending-gates language: deferring would leave the observed anon/authenticated seven-privilege surface in place, while the proposed harden is bounded to grant posture and explicitly gates the security_invoker step on TCC-lane coordination, so it does not disturb the contract-surface guarantee. Provisional pending the six signed overlays.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (apps/control-plane-api/migrations/maint/vw_sensor_calc_context.sql:13)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE — the full seven-privilege set — on this view. Grant provenance was not observed in this packet. The view is postgres-owned with security_invoker not set and rls_enabled observed false (RLS is in any case not enforceable on plain views). If the view is PostgREST-reachable — unresolved pending the in_data_api_exposed_schema overlay — an anon/authenticated SELECT executes with owner privileges against tcc_etu_sensors, tcc_trip_styles, tcc_trip_types, tcc_manufacturers, and tcc_etu_sensor_maint, and for any of those base relations that enforces RLS such a read would bypass caller RLS (PostgreSQL-semantic inference; base-relation RLS posture was not in this record's facts). The write privileges are likely inert because a multi-table join view is not auto-updatable (PostgreSQL-semantic inference), but they remain grant-hygiene violations to revoke.
- **Depends on:** `tcc_etu_sensors`, `tcc_trip_styles`, `tcc_trip_types`, `tcc_manufacturers`, `tcc_etu_sensor_maint`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 66 total, areas {"apps": 29, "docs": 1, "infra": 3, "ops": 29, "reference": 4}. 66 repo callsites: apps 29, ops 29, infra 3, reference 4, docs 1. Notable consumers: control-plane-api NETA router live queries (services/neta/router.py:1597, 5304-5369), SQL function bodies fn_calculate_test_currents and fn_evaluate_test_results (SELECT ... FROM vw_sensor_calc_context in migrations/maint and supabase/migrations), a phase-3 validation script, plot-tcc and settings-route tests, and D012/TCC phase handoffs; reference/tcc/G2-RULES-GUIDE.md:262 names it a runtime contract surface remaining authoritative pending all gates. This is repo-grep evidence only, NOT the signed static_repo overlay. The census found 0 database dependents while grep shows two SQL functions reading the view — pg_depend does not track plpgsql-body references (PostgreSQL-semantic inference) — so database consumers are understated. Reconciliation: the D012 phase-0 characterization callsite (ops/agents/handoffs/2026-05-30-d012-phase0-live-characterization-closeout.md:403) lists only four base dependencies, omitting tcc_trip_types; the five-relation dependency list recorded here follows the view definition snippet (apps/control-plane-api/migrations/maint/vw_sensor_calc_context.sql), which joins all five relations.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - census dependent_objects is empty but repo grep shows fn_calculate_test_currents and fn_evaluate_test_results SELECT from this view inside plpgsql bodies — pg_depend does not track plpgsql-body references (PostgreSQL-semantic inference); posture changes must account for these unrecorded database consumers
  - cross-lane governance: TCC lane rules (reference/tcc/G2-RULES-GUIDE.md) hold this view as a runtime contract surface remaining authoritative pending all gates — security_invoker conversion or any relocation must be coordinated with that lane
  - serving-role dependency on definer semantics unproven: whether the control-plane-api serving role has direct grants on the tcc.* base relations is unobserved, gating the security_invoker=true step of the harden
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether public-schema exposure makes this view PostgREST-reachable)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay to supersede the grep-based callsite census
  - signed runtime_logs overlay (any anon/authenticated Data-API reads of this view in prod)
  - signed external_clients overlay
  - signed operator_declaration overlay: which role(s) the control-plane-api serving path uses and whether definer semantics are required for this view
  - grant/RLS posture of base relations tcc_etu_sensors, tcc_trip_styles, tcc_trip_types, tcc_manufacturers, tcc_etu_sensor_maint for the serving role, to clear the security_invoker conversion
  - TCC-lane sign-off that grant revocation does not disturb the runtime contract surface guarantees in reference/tcc/G2-RULES-GUIDE.md
- **Labeled technical inferences (retained caveats):**
  - The D012 phase-0 characterization table (ops/agents/handoffs/2026-05-30-d012-phase0-live-characterization-closeout.md:403) lists only four base dependencies for this view, omitting tcc_trip_types; the view definition snippet joins five relations including tcc_trip_types, and the five-relation list is authoritative here.
  - Write privileges on this view are assessed as likely inert because a multi-table join view is not auto-updatable (PostgreSQL-semantic inference); revocation is grant hygiene, not removal of a proven write path.
  - The definer-semantics consequences stated here (owner-privilege reads; caller-RLS bypass for any RLS-enforcing base relation) are PostgreSQL-semantic inference; base-relation RLS posture and serving-role grants on tcc.* were not observed in this packet.

### `public.vw_trip_unit_cascade`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

The view is an actively served read-model over the canonical tcc.* schema: 105 repo callsites (repo-grep evidence, not the signed static_repo overlay), with apps/control-plane-api/services/neta/router.py issuing direct SQL against it in roughly a dozen statements backing /api/v1/neta/cascade, /etu/breaker-alt-trips, and catalog/status; the /etu/breaker-cascade route also exercises it, per the Phase 4b inbox packet ("the 4a-fixed vw_trip_unit_cascade path") and the Phase 4a post-apply gate table rather than a router.py snippet naming that route. reference/tcc/G3-ROUTING-GUIDE.md names it the trip-unit cascade view backing /cascade, and an ops handoff states it "remains the runtime contract surface". All observed consumers are server-side direct-Postgres callers, yet the census observed anon and authenticated each holding the full seven-privilege set on this postgres-owned view — grant provenance was not observed in this packet — grants far broader than any evidenced consumer needs. If the public schema is exposed through the Data API (reachability depends on the unresolved in_data_api_exposed_schema dimension), the SELECT grant would let anon/authenticated API callers read the view, and because a view without security_invoker=true executes with its owner's privileges, such reads would not consult the caller's own privileges on the tcc.* base relations (PostgreSQL-semantic inference). The view was deliberately repointed to canonical tcc.* in D012 Phase 4a (migration 002), so promote/compat are not warranted; the defect is posture, not location. (Out-of-band context, not grounded in this packet's facts: the 2026-07-09 schema-placement policy accepts public serving shims over canonical named-schema models.) Provisional prescription: revoke anon/authenticated grants (at minimum all write-shaped privileges; SELECT too unless the signed external_clients overlay reveals a PostgREST/browser consumer), and evaluate security_invoker=true after confirming the control-plane-api serving role holds direct SELECT on the four tcc.* base relations. Execution is gated on the six signed overlay dimensions.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 4 (infra/database/migrations/tcc/002_phase4a_repoint_db_objects.sql:479; infra/database/migrations/tcc/002_phase4a_repoint_db_objects_down.sql:450; ops/agents/handoffs/2026-05-30-d012-phase4a-repoint-db-objects-closeout.md:31)
- **Privileges (census-observed):** The census observed anon and authenticated each holding DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on this postgres-owned view (rls_enabled=false, normal for a view). Grant provenance was not observed in this packet. The view reads tcc.manufacturers/trip_styles/etu_sensors/trip_types and appears in the repo's 29-definer-view program list; because a view without security_invoker=true executes with its owner's privileges, SELECT alone would let an anon/authenticated caller read the full cascade (~17,831 rows per the Phase 4a closeout captured in the facts file) without the caller's own privileges on the base relations being consulted, and — for any underlying table that enforces RLS — with that RLS evaluated against the owner rather than the caller (PostgreSQL-semantic inference; base-table RLS state is not in this record's facts). Whether these grants are reachable through the Data API depends on the unresolved in_data_api_exposed_schema dimension. The write-shaped privileges are likely inert because a multi-join view is not auto-updatable (PostgreSQL-semantic inference), but no evidenced consumer uses them and they should be revoked regardless.
- **Depends on:** `tcc.manufacturers`, `tcc.trip_styles`, `tcc.etu_sensors`, `tcc.trip_types`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 105 total, areas {"apps": 23, "docs": 1, "infra": 21, "ops": 49, "reference": 11}. 105 callsites (repo-grep evidence only — NOT the signed static_repo overlay, which is not_observed): apps=23, dominated by apps/control-plane-api/services/neta/router.py with 12 SQL-bearing lines (2767, 2773, 4353, 4455-4709, 5276; only line 2767 is demonstrably an f-string, and lines 2729/5231 are comments/docstrings, not SQL), plus schemas.py, main.py, tests, and operations-web lvbreakertcc wiring docs; infra=21, the authoritative CREATE OR REPLACE in infra/database/migrations/tcc/002_phase4a_repoint_db_objects.sql(:479) and its DOWN, plus corrections 018-025 that read the view in validation gates; ops=49, D012 phase 2-4b handoffs/inbox packets documenting the repoint and calling it the runtime contract surface; reference=11, TCC G2/G3 guides mapping it to GET /api/v1/neta/cascade and /etu/breaker-alt-trips; docs=1, the 29-definer-view program list. All observed consumers are server-side (API service, migrations, gates) — no browser/PostgREST callsite appears in the grep.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - security_invoker=true conversion requires confirming the control-plane-api serving role has direct SELECT grants on tcc.manufacturers, tcc.trip_styles, tcc.etu_sensors, tcc.trip_types (not in this record's facts file)
  - facts file records definition_count=4 but lists only 3 definition snippets; the DOWN-migration snippet is the historical pre-repoint body (references tcc_manufacturers_pre_rebuild) and was excluded from dependencies
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (whether public-schema Data-API exposure makes the observed anon/authenticated grants reachable)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed static_repo overlay (supersedes the repo-grep callsite census in this record)
  - signed runtime_logs overlay (confirm which roles actually query the view in prod)
  - signed external_clients overlay (rule out any PostgREST/browser consumer needing anon or authenticated SELECT)
  - signed operator_declaration overlay (ratify revoke scope and confirm the control-plane-api serving-role identity for this surface)
  - grant check: serving role's direct privileges on the four tcc.* base relations, prerequisite for any security_invoker conversion
- **Labeled technical inferences (retained caveats):**
  - Definer-view privilege semantics (a view without security_invoker=true executes with its owner's privileges) and the inertness of write-shaped privileges on a multi-join view are PostgreSQL-semantic inferences, not census observations.
  - Base-table RLS enforcement state for the four tcc.* relations was not captured in this record's facts; any RLS-related characterization is conditional on a base table actually enforcing RLS.
  - The ~17,831-row figure comes from the Phase 4a closeout and Tier-B parity handoff captured in the facts file, not from a census row estimate (row_estimate is not applicable to views).
  - The DOWN-migration definition snippet is the historical pre-repoint view body (it references tcc_manufacturers_pre_rebuild); the dependency list derives from the UP body at migration 002:479.

## Per-view records — `mcp_*` (separately identified; governed by Packet 01)

### `public.mcp_job_run_summary_v`

**Proposed disposition (PROVISIONAL): `defer`** — confidence high

This view is one of the two mcp_* summary views explicitly governed by schema-placement Packet 01 (an authorized policy anchor for this record), and the facts file corroborates that governance from multiple directions: the defining migration (apps/control-plane-api/supabase/migrations/20260328_000007_add_control_plane_tables.sql:175), the Packet-01 hardening migrations 20260710_000012/000013 plus rollbacks that enumerate it, the MCP_ACCEPTED_DEFINER_VIEWS allowlist in apps/control-plane-api/scripts/schema_drift_acl.py with drift tests whose allowlist predicate accepts SELECT for this view and whose failure messages read "anon/authenticated retains SELECT", and the 2026-07-11 signed-overlay spec listing it as a Packet-01b/6b exception kept separate from the 29-view v_*/vw_* program. Its security_invoker conversion was explicitly DEFERRED by Packet 01, so the 29-view program must not re-disposition it here. It has a live repo read consumer (services/control_plane/router.py:1254 reads FROM public.mcp_job_run_summary_v; repo-grep evidence, not the signed static_repo overlay), so it is not a dead shim. Disposition is therefore defer (governed-by-Packet-01), with one reconciliation item surfaced: the census observed anon/authenticated holding ALL privileges on the view, while the repo drift-ACL tests allowlist only SELECT for it (a SELECT-only retention expectation inferred from the predicate shape, verb == "SELECT"). The facts file's own fixtures (fixture.sql / fixture_7th.sql, commented "Grants matching prod.") model the pre-hardening prod state as GRANT ALL to anon/authenticated/service_role, which is consistent with the census reflecting a pre-apply snapshot rather than a contradiction; Packet 01 owns confirming whether migrations 20260710_000012/000013 have been applied on prod. Whether the observed grants are reachable via the Data API depends on the unresolved in_data_api_exposed_schema dimension. This is a provisional proposal for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 3 (apps/control-plane-api/supabase/migrations/20260328_000007_add_control_plane_tables.sql:175; docs/operations/schema-placement-01/evidence/tests/fixture.sql:99; docs/operations/schema-placement-01/evidence/tests/fixture_7th.sql:99)
- **Privileges (census-observed):** The census observed anon and authenticated each holding all seven privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on the view; grant provenance was not observed in this packet. Owner is postgres; rls_enabled=false was observed, the expected value for a view since views do not carry table-style RLS (PostgreSQL-semantic inference). The defining migration uses plain CREATE VIEW with no security_invoker reloption and the repo allowlist names it in MCP_ACCEPTED_DEFINER_VIEWS, consistent with security-definer semantics (PostgreSQL-semantic inference; not a direct catalog observation). Under definer semantics, SELECT alone lets anon/authenticated read through the view, and for any underlying table that enforces RLS such reads bypass the caller's RLS (PostgreSQL-semantic inference; the facts file does not record RLS state for public.mcp_local_action_queue or public.mcp_job_runs). Packet-01 DESIGN.md, a facts-file callsite, describes the view as joining requested_by-scoped rows such that any authenticated reader sees all requesters' rows. The write verbs exceed any plausible consumer need. Whether any of these grants are reachable via PostgREST/Data-API depends on the unresolved in_data_api_exposed_schema dimension. The repo's Packet-01 hardening migrations (20260710_000012 harden_mcp_public_exposure_core, 20260710_000013 retire_mcp_authenticated_contract) target these grants, and the drift-ACL tests' allowlist predicate accepts only SELECT for this view (SELECT-only expectation inferred from the predicate shape); the facts file's fixture.sql / fixture_7th.sql model pre-hardening prod as GRANT ALL to anon/authenticated/service_role, corroborating that the census full-ALL observation likely reflects a pre-apply snapshot — apply-state reconciliation belongs to Packet 01.
- **Depends on:** `public.mcp_local_action_queue`, `public.mcp_job_runs`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 34 total, areas {"apps": 18, "docs": 16}. 34 repo callsites (grep evidence only — NOT the signed static_repo overlay): 18 in apps, all under apps/control-plane-api — a live read consumer (services/control_plane/router.py:1254 "FROM public.mcp_job_run_summary_v"), the drift-ACL allowlist MCP_ACCEPTED_DEFINER_VIEWS (scripts/schema_drift_acl.py:45) with drift tests whose allowlist predicate accepts SELECT for this view and whose failure messages read "anon/authenticated retains SELECT" (tests/test_schema_drift_acl.py), the defining migration 20260328_000007, and Packet-01 hardening migrations 20260710_000012/000013 plus rollbacks. 16 in docs — schema-placement-01 DESIGN.md and evidence (codex audit, IRP synthesis, fingerprint/fixture/up-down-up test SQL, including fixture.sql / fixture_7th.sql modeling pre-hardening prod grants as GRANT ALL), and the 2026-07-11 signed-overlay-evidence spec naming it a Packet-01b/6b exception distinct from the 29-view program.
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - census-vs-Packet-01 apply-state discrepancy: census observed anon/authenticated holding ALL privileges while the repo drift-ACL tests allowlist only SELECT for this view (SELECT-only expectation inferred from the predicate shape); facts-file fixtures model pre-hardening prod as GRANT ALL, consistent with the census predating the 20260710_000012/000013 apply — confirm prod apply status via Packet 01
  - cross-lane governance: disposition (including any security_invoker conversion, explicitly deferred there) is owned by schema-placement Packet 01, not this 29-view reconciliation
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (config-backed: whether public is in the exposed schema set, determining whether the observed anon/authenticated grants are reachable via PostgREST/Data-API)
  - signed advisor_findings overlay (Supabase advisor security findings covering this view)
  - signed static_repo overlay to supersede the grep-based callsite census
  - signed runtime_logs overlay (whether anon/authenticated traffic actually reaches this view, or only the control-plane-api service path)
  - signed external_clients overlay (any PostgREST/Data-API or external reader of the view)
  - signed operator_declaration overlay (operator ratification that the Packet-01b/6b exception — definer semantics plus retained SELECT — remains intended)
  - Packet-01 apply-state confirmation for migrations 20260710_000012/000013 on prod to resolve the census full-ALL grant observation
- **Labeled technical inferences (retained caveats):**
  - Security-definer semantics are inferred, not directly observed: the defining migration uses plain CREATE VIEW with no security_invoker reloption, and the repo's MCP_ACCEPTED_DEFINER_VIEWS allowlist names the view (PostgreSQL-semantic inference: a view without security_invoker=true executes with definer semantics).
  - rls_enabled=false is the expected census value for a view; views do not carry table-style RLS (PostgreSQL-semantic inference).
  - For any underlying table that enforces RLS, reads through a security-definer view bypass the caller's RLS (PostgreSQL-semantic inference); the facts file does not record RLS state for public.mcp_local_action_queue or public.mcp_job_runs.
  - The SELECT-only retention expectation attributed to the drift-ACL tests is inferred from the allowlist predicate shape (obj == "mcp_job_run_summary_v" and verb == "SELECT") plus "retains SELECT" failure messages; the tests do not literally assert that no other verb is retained.

### `public.mcp_task_packet_summary_v`

**Proposed disposition (PROVISIONAL): `defer`** — confidence high

This view is one of the two mcp_* summary views explicitly governed by schema-placement Packet 01, which owns its anon-access hardening and explicitly deferred its security_invoker conversion (authorized policy anchor). The facts file's repo evidence confirms this governance: schema_drift_acl.py lists it in MCP_ACCEPTED_DEFINER_VIEWS, and the 2026-07-11 signed-overlay evidence design names it a "Packet-01b/6b exception... explicitly retained", separate from the 29-view program. It is an active runtime dependency -- control-plane-api router.py:690 reads FROM it in production code -- and Packet-01 hardening migrations 20260710_000012/000013 plus their rollback scripts target it by name, so any disposition taken here would collide with the Packet-01 actions evidenced in the repo. Nothing in the facts contradicts the Packet-01 governance assignment, so per the reconciliation policy the disposition is defer (governed-by-Packet-01), kept separately identified from the 29-view program. One material discrepancy must be routed to that packet rather than resolved here: the census observed anon and authenticated holding all seven privileges on this postgres-owned view over public.mcp_task_packets, which conflicts with the hardening those repo migrations implement; whether those migrations have been applied to the censused database was not observed in this packet. Because a simple single-table view meets PostgreSQL auto-updatability criteria, the observed write grants are a potential pass-through write path to the base table, not just a read exposure (PostgreSQL-semantic inference); whether any of these grants are reachable over the Data API depends on the unresolved in_data_api_exposed_schema dimension. Defer is therefore provisional governance routing, not a statement that the current posture is acceptable.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 3 (apps/control-plane-api/supabase/migrations/20260328_000007_add_control_plane_tables.sql:163; docs/operations/schema-placement-01/evidence/tests/fixture.sql:100; docs/operations/schema-placement-01/evidence/tests/fixture_7th.sql:100)
- **Privileges (census-observed):** The census observed anon and authenticated each holding all seven privileges (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER) on this postgres-owned view (census rls_enabled=false; RLS does not apply to views). Grant provenance was not observed in this packet. Repo evidence in the facts file characterizes the view as a security-definer surface (schema_drift_acl.py MCP_ACCEPTED_DEFINER_VIEWS; Packet-01 DESIGN.md "01b views (2, SECURITY DEFINER)"); this characterization comes from repo text, not a census-observed view attribute. For any underlying table that enforces RLS, a definer-style view executes under the view owner and bypasses the caller's RLS (PostgreSQL-semantic inference); whether public.mcp_task_packets enforces RLS was not captured in this record's facts file. Because the view is a simple single-table projection, it meets PostgreSQL auto-updatability criteria, so the observed INSERT/UPDATE/DELETE grants could pass writes through to the base table under owner rights (PostgreSQL-semantic inference). Whether any of these grants are reachable over the Data API depends on the unresolved in_data_api_exposed_schema dimension. The observed grants conflict with the Packet-01 hardening migrations present in the repo (20260710_000012 harden_mcp_public_exposure_core, 20260710_000013 retire_mcp_authenticated_contract); whether those migrations have been applied to the censused database was not observed here, and reconciling census state vs apply state belongs to Packet 01.
- **Depends on:** `public.mcp_task_packets`
- **Dependents (census):** (none observed in census)
- **Repository callsites (repo facts at pinned HEAD; preliminary, not the signed static_repo overlay):** 31 total, areas {"apps": 16, "docs": 15}. 31 repo-grep callsites: 16 in apps (all control-plane-api: schema_drift_acl.py declares it in MCP_ACCEPTED_DEFINER_VIEWS; services/control_plane/router.py:690 reads FROM public.mcp_task_packet_summary_v at runtime; migration 20260328_000007 creates it and 20260710_000012/000013 plus rollbacks harden/retire its grants; tests assert its presence and missing-relation handling) and 15 in docs (schema-placement-01 DESIGN.md and evidence -- codex audit, IRP synthesis, fingerprint/fixture/up-down-up test SQL -- plus the 2026-07-11 signed-overlay evidence design spec naming it a Packet-01b/6b exception, explicitly retained, distinct from the 29 v_*/vw_* views). This is repo-grep evidence only, NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: in_data_api_exposed_schema
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: static_repo (repo-grep callsites herein are preliminary evidence, not the signed overlay)
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - census-observed anon/authenticated ALL-privilege grants conflict with the Packet-01 hardening migrations present in the repo (20260710_000012/000013); whether those migrations have been applied to the censused database was not observed in this packet -- apply state vs census snapshot must be reconciled within Packet 01
  - cross-lane governance: security_invoker conversion explicitly deferred by Packet 01 -- this reconciliation must not preempt that packet's actions
- **Required evidence before any accepted decision:**
  - signed in_data_api_exposed_schema overlay (config-backed, not the pgrst.db_schemas GUC)
  - signed advisor_findings overlay
  - signed static_repo overlay
  - signed runtime_logs overlay
  - signed external_clients overlay
  - signed operator_declaration overlay (including Packet-01 apply-state declaration for migrations 20260710_000012/000013)
  - post-apply census recapture of anon/authenticated effective privileges on the two mcp_* summary views after the Packet-01 hardening migrations are applied
- **Labeled technical inferences (retained caveats):**
  - Definer-style views execute with the view owner's privileges; for any underlying table that enforces RLS, the caller's RLS is bypassed. Whether public.mcp_task_packets enforces RLS was not captured in this record's facts file (PostgreSQL-semantic inference).
  - As a simple single-table projection over public.mcp_task_packets, the view meets PostgreSQL auto-updatability criteria, so the observed anon/authenticated INSERT/UPDATE/DELETE grants are a potential pass-through write path to the base table under owner rights, not just a read exposure (PostgreSQL-semantic inference).
  - The view's security-definer characterization derives from repo text in the facts file (MCP_ACCEPTED_DEFINER_VIEWS in schema_drift_acl.py; Packet-01 DESIGN.md), not from a census-observed security_invoker attribute on the view itself.

---
*End of Phase 8 artifact (Phase-8C corrected). Next: Phase 8R operator ratification of the 31-view inventory, provisional dispositions, and evidence-collection cohort; Phase 9 signed-overlay collections (each its own GO) bind census sha256 `52962abea7c8b81f62e6331c169f9b6963bf546763a76898cf707d076cf94130`.*
