# Definer-view reconciliation — Phase 8 (PROVISIONAL, offline)

2026-07-13 · disposition-ledger lane · operator GO "Phase 8 only" · **stops for Phase 8R operator ratification**

## Scope and standing disclaimers

- OFFLINE reconciliation only: no database, production, external-API, overlay-collection, signing, or SQL action was taken.
- Every disposition below is a PROVISIONAL PROPOSAL. This artifact creates **no accepted decisions and no accepted cluster manifest**.
- Per the evidence rule, `runtime_logs`, `external_clients`, `operator_declaration`, `advisor_findings`, and Data-API exposure configuration are UNRESOLVED for every view until their signed overlays exist (Phase 9). Repo callsite data here is grep evidence at the pinned HEAD, not the signed `static_repo` overlay.

## Provenance pins

- Branch `schema-placement/definer-view-recon-2026-07-13` off clean `main@fdb5fc384c5f9c4c442f45cff530f7599f14a406`.
- Source census `infra/database/schema-placement/evidence/census-prod-20260713T154550Z.json`, sha256 `52962abea7c8b81f62e6331c169f9b6963bf546763a76898cf707d076cf94130` (re-hashed before derivation), repo_sha `7a70cb6322a29a59f36db67e8665a95e3c20cc01`, observed_at `2026-07-13T15:45:51.086245+00:00`.
- Method: deterministic census/grep facts extraction, then one analyst + one independent adversarial verifier per view (62 agents) + a cohort conflict check; 0 disputed proposals; controller synthesis. Facts grounded ONLY in the census and repo text at HEAD.

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

1. **Broad write grants on definer views (census-observed):** anon holds privileges beyond SELECT on 31/31 views; authenticated on 31/31. On definer views over RLS-protected tables this is both a read-through and (for auto-updatable single-table views) a potential write path. Whether these grants are REACHABLE depends on the unresolved Data-API exposure configuration — a Phase 9 overlay question, surfaced here, not resolved.
2. **Views with no defining SQL in the repo (12):** `public.v_apparatus_resources`, `public.v_apparatus_type_resources`, `public.v_guide_image_completeness`, `public.v_image_production_queue`, `public.v_image_sourcing_summary`, `public.v_neta_test_details`, `public.v_scope_summary`, `public.v_tcc_calc_input`, `public.v_tcc_etu_catalog`, `public.v_tcc_etu_coefficients`, `public.v_tcc_tmt_catalog`, `public.v_tcc_tmt_curve_data`. Their upstream dependencies cannot be derived offline; each carries a per-view blocker.
3. **`mcp_*` census-vs-Packet-01 apply-state question:** the census observes anon/authenticated ALL-privileges on both `mcp_*` views while Packet-01 drift tests model a SELECT-only hardened target — consistent with the Packet-01 A1/A2 APPLY still being HELD (per that lane), but flagged for Packet-01 reconciliation, not this program.

## Provisional 3–5-view cohort proposal (Phase 8 item 8)

**Proposed cohort (operator lean, checked): `public.v_active_tasks`, `public.v_agent_dashboard`, `public.v_pending_handoffs`**

- Cohort conflict check recommendation: **confirm**
- Conflicts found: none
- Amended cohort suggested: `public.v_active_tasks`, `public.v_agent_dashboard`, `public.v_pending_handoffs`
- Rationale: Confirm the 3-view cohort as-is for the first disposition cluster. Static-repo conflicts: none. All three facts files show zero apps/ callsites (callsite_areas = docs+infra only; infra hits are the defining CREATE VIEW in infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql plus one RAISE NOTICE test hint in historical-deploy/DEPLOY_ORCHESTRATION.sql), zero database dependents (dependent_objects=[], database_deps_found_consumers=0), zero FKs, and no involvement in other packets/lanes — none is an mcp_* Packet-01 view, and their only program reference is the 29-view roster itself. Coherence is exceptionally strong: all three are defined in the SAME source file, cover a closed 3-table domain (ai_tasks, ai_agent_state, ai_handoffs — the union of their dependencies, with no heavier view sharing them per the facts), carry identical posture (postgres-owned definer view, full 7-privilege default grants to anon+authenticated, docs-only consumers), share the same provisional disposition (harden), and share ONE decisive unresolved question — whether the apex-resa AI-orchestration lineage is live or retired — so a single operator_declaration overlay resolves the cluster. Keep it lean at 3: the only other roster-visible candidates (v_apparatus_*, v_equipment_movement_history, v_neta_test_details) belong to different domains (apparatus/NETA), have no facts files in this packet, and adding them would break the one-lineage/one-declaration property and exceed the offline evidence base. Advisory caveats for Phase 8R (not conflicts): (1) AI_ORCHESTRATION_PROTOCOL.md documents example queries against all three views, including a desktop-claude polling pattern on v_active_tasks (line 245) — a possible shared out-of-repo runtime consumer; the runtime_logs and external_clients overlays must land before executing any grant revocation, and the shared consumer actually argues FOR clustering since the harden can be sequenced once for all three. (2) Per the evidence rule, all five signed overlays (runtime_logs, external_clients, operator_declaration, advisor_findings, Data-API exposure configuration) remain unresolved for every view, and the callsite data here is repo-grep evidence only, not the signed static_repo overlay — this confirmation is provisional and advisory; the operator ratifies in Phase 8R.

This cohort is NOT accepted by this artifact; acceptance is Phase 8R (operator ratification), and any cluster manifest is Phase 11.

## Per-view records — 29-view program

### `public.v_active_tasks`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

v_active_tasks is a postgres-owned definer view over the AI-orchestration task queue (ai_tasks LEFT JOIN ai_agent_state) with the full seven-privilege grant set (SELECT/INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER) to both anon and authenticated — far broader than any observed consumer needs, since the census shows zero database dependents and zero database-dep consumers. The only defining SQL is in the legacy apex-resa source-lineage tree, and the remaining callsites are documentation (orchestration protocol examples, schema reference, and the 29-view definer program spec), so nothing in the repo establishes that definer semantics are required or that anon access is intentional. Under the schema-placement policy the view is legacy public content, and the correct posture fix is to set security_invoker=true and revoke anon/authenticated grants rather than relocate or retain as-is. A promote is not indicated: this is not a canonical model, and the live orchestration workstream (apex-jobs) is a separate lane, which raises the possibility the view is dead legacy — the operator declaration overlay should confirm before any drop is considered. This is a provisional lean pending the five signed overlays; runtime logs or Data-API exposure evidence could still shift it (e.g., an active desktop-claude polling consumer per AI_ORCHESTRATION_PROTOCOL.md would require sequencing the revoke with that client).

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql:191)
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view (the default-grant pattern). Because the view runs with definer semantics under postgres ownership, SELECT lets anonymous or authenticated Data-API callers read ai_tasks and ai_agent_state rows bypassing any caller RLS on those base tables — internal task titles, assignments, agent heartbeats, and status. The write privileges are probably inert (the LEFT JOIN makes the view non-auto-updatable) but are grant-hygiene violations regardless. Actual exploitability depends on Data-API schema exposure, which is not_observed in the facts.
- **Depends on:** `ai_tasks`, `ai_agent_state`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 5 total, areas {"docs": 4, "infra": 1}. 5 repo callsites (grep evidence only, NOT the signed static_repo overlay): 4 in docs, 1 in infra. The infra hit is the defining SQL itself (infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql:191). Docs hits: two query examples in docs/architecture/control-plane-lineage/apex-resa/AI_ORCHESTRATION_PROTOCOL.md (lines 208, 245 — one filters assigned_to = 'desktop-claude', suggesting a documented agent-polling pattern), a listing in docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md:447, and enumeration in the 29-view definer program spec (docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232). No application-code consumers found in the repo.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - base relations ai_tasks / ai_agent_state are unqualified in the defining SQL (presumed public via search_path; not confirmed in facts)
  - documented desktop-claude polling pattern in AI_ORCHESTRATION_PROTOCOL.md suggests a possible out-of-repo runtime consumer that only runtime_logs/external_clients overlays can confirm or rule out
  - unclear whether the legacy apex-resa orchestration lineage is superseded by the current orchestration lane — operator declaration needed to decide harden vs eventual decommission
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any live SELECT traffic against v_active_tasks, especially agent-polling clients)
  - signed external_clients overlay (desktop-claude or other out-of-repo orchestration clients per AI_ORCHESTRATION_PROTOCOL.md)
  - signed operator_declaration overlay (whether apex-resa AI-orchestration views are live, dormant, or superseded)
  - signed advisor_findings overlay (Supabase advisor security findings for this definer view)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes the anon grant reachable via PostgREST)
  - signed static_repo overlay to replace the provisional repo-grep callsite data
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor overstatement in privilege_summary: it claims SELECT exposes 'agent heartbeats', but the v_active_tasks definition snippet selects only a.status AS agent_status from ai_agent_state — last_heartbeat appears only in the adjacent v_agent_dashboard definition, not this view. The exposed columns are task id/title/task_type/project/domain/priority/status/assigned_agent/claimed_at/created_at/hours_claimed plus agent_status. Does not change the harden conclusion (task titles/assignments/status exposure alone justifies it).
  - Ungrounded-but-peripheral rationale claim: 'the live orchestration workstream (apex-jobs) is a separate lane' is not traceable to the facts file or the policy block (apex-jobs appears in neither). It is hedged, non-load-bearing, and the dead-vs-live question is correctly routed to the operator_declaration overlay, so it does not affect the disposition — but it should be struck or attributed to out-of-band context in the final record.
  - Verified clean: dependencies re-derived from the definition snippet (FROM ai_tasks t LEFT JOIN ai_agent_state a) are exactly {ai_tasks, ai_agent_state} — none missed, none invented; adjacent objects in the same file snippet (ai_handoffs, ai_task_history, v_agent_dashboard, v_pending_handoffs) belong to other CREATE statements and were correctly excluded.
  - Verified clean: all five awaiting-signed-overlay blockers present, plus the static_repo grep-only caveat, plus three appropriate view-specific blockers (unqualified base relations, documented desktop-claude polling pattern at AI_ORCHESTRATION_PROTOCOL.md:245, legacy apex-resa supersession question). Privilege facts (7 privs x anon+authenticated, observed), zero dependents, zero database-dep consumers, 5 callsites (4 docs / 1 infra), and not_observed Data-API exposure all match the facts file. View is not mcp_*, so Packet-01 defer governance does not apply; harden per the policy's 'grants broader than consumers need / definer semantics not clearly required' test is the best-fitting disposition (retain fails on grant breadth, compat/promote lack any canonical-model or migration evidence, defer is unwarranted since facts suffice for a provisional lean).
  - Note: the non-auto-updatable claim ('probably inert' write privileges) is correct per the snippet — the view has a JOIN, expression columns, and ORDER BY, so INSERT/UPDATE/DELETE cannot route through it automatically; appropriately hedged.

### `public.v_agent_dashboard`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

v_agent_dashboard is a definer-semantics view (owner postgres, security_invoker not set) aggregating AI-orchestration state from ai_agent_state, ai_tasks, and ai_handoffs, and both anon and authenticated hold ALL seven table-level privileges on it — far broader than any observed consumer need, since the census found zero database dependents and repo grep found zero application-code callsites (all 5 hits are docs, a deploy-script notice, or the CREATE VIEW itself). Nothing in the definition requires definer semantics: it is a plain grouped SELECT with no privilege-bridging purpose stated anywhere in the facts. The source lineage (infra/database/source-lineage/apex-resa/automation-orchestration, with a sibling historical-deploy script) reads as legacy apex-resa material, consistent with the schema-placement policy's framing of public as legacy/compat only — so keep it in public but fix posture: revoke anon/authenticated grants and convert to security_invoker=true. Promote is not indicated because there is no evidence this embodies an active canonical model; compat is not indicated because no consumer migration is in evidence. This is provisional pending the five signed overlays; an operator declaration that the apex-resa orchestration protocol is fully retired could upgrade this to a drop/compat discussion, and evidence of an active runtime consumer would refine which grants to retain.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql:219)
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view (observed). Because the view runs with definer semantics under owner postgres, any anon or authenticated SELECT bypasses caller RLS on the underlying ai_agent_state/ai_tasks/ai_handoffs tables — a live exposure lever if the public schema is Data-API exposed (exposure config itself is not yet observed). The write-side grants (DELETE/INSERT/UPDATE/TRUNCATE/TRIGGER/REFERENCES) are gratuitous for a grouped, non-auto-updatable dashboard view and indicate default GRANT ALL hygiene debt rather than intentional design.
- **Depends on:** `ai_agent_state`, `ai_tasks`, `ai_handoffs`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 5 total, areas {"docs": 3, "infra": 2}. 5 repo-grep callsites, none in application code: docs (3) — an AI_ORCHESTRATION_PROTOCOL.md usage example ("SELECT * FROM v_agent_dashboard;"), a SCHEMA_REFERENCE.md inventory listing, and the 2026-07-11 signed-overlay-evidence-design spec's 29-view program list (self-referential to this program, not a consumer); infra (2) — a RAISE NOTICE test hint in historical-deploy/DEPLOY_ORCHESTRATION.sql and the defining CREATE VIEW in source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql. This is repo-grep evidence only, NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in facts file is repo-grep evidence only, not the signed static_repo overlay
  - underlying relations are written unqualified in the defining SQL (ai_agent_state, ai_tasks, ai_handoffs); schema resolution assumed public but not proven from the facts file
  - activity status of the apex-resa AI-orchestration lineage is unknown (definition lives beside a historical-deploy script; zero app-code callsites); whether any live agent process still reads this view needs operator declaration
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any live SELECT traffic against v_agent_dashboard, esp. by anon/authenticated)
  - signed external_clients overlay (Data-API / PostgREST / external tooling consumers)
  - signed operator_declaration overlay: is the apex-resa AI-orchestration protocol (ai_agent_state/ai_tasks/ai_handoffs) active or retired in prod, and is definer semantics intentionally required for any agent identity
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes anon SELECT reachable over the API)
  - signed static_repo overlay to supersede the ad-hoc grep callsite data
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor: rationale's forward-looking phrase 'drop/compat discussion' references 'drop', which is outside the five-term disposition vocabulary; acceptable because it is framed as a future discussion contingent on a signed operator_declaration overlay, not as the proposed disposition.
  - Minor: 'non-auto-updatable dashboard view' in privilege_summary is an inference from PostgreSQL auto-updatable-view rules (grouped/aggregate views are not auto-updatable), not an explicit facts-file field; the inference is correct given the GROUP BY + FILTER aggregates in the definition snippet.
  - Verified: dependencies re-derived from the definition snippet are exactly {ai_agent_state, ai_tasks, ai_handoffs}; adjacent DDL in the same source file (v_pending_handoffs, triggers, ai_task_history, seed INSERT) was correctly excluded.
  - Verified: all five mandated 'awaiting signed overlay' blockers present, plus the static_repo repo-grep caveat and two sound view-specific blockers (unqualified relation names; unknown activity of the apex-resa orchestration lineage).

### `public.v_apparatus_approval_queue`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned definer view (security_invoker not set) over six public tables carrying operationally sensitive data: pending-review apparatus rows joined to employee names, client names, project numbers, tech notes, and delay reasons. Both anon and authenticated hold the full seven-privilege set, so any Data-API caller could read this queue with the owner's RLS bypass if the schema is exposed. The census shows zero database dependents and zero app-code callsites — the only repo references are two docs listings and the source-lineage SQL that defines it — so there is no evidenced consumer that requires definer semantics or broad grants. The view is legacy apex-resa/pm-project-pss lineage, which is consistent with public-as-legacy placement policy; the defect is posture, not location, so harden (set security_invoker=true and revoke anon/authenticated) is the right provisional lean rather than promote or compat. This remains provisional until the five signed overlays confirm no runtime or external consumers.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/08_apparatus_completion_workflow.sql:36)
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view (observed) — the full default-grant set, far broader than any plausible read-only queue consumer needs. Because the view runs with definer semantics under owner postgres, anon SELECT alone bypasses caller RLS on apparatus, scopes, projects, clients, tasks, and employees, exposing employee names, client names, and tech notes to unauthenticated Data-API callers if public is an exposed schema (exposure config itself is not yet observed). The write-type privileges are likely inert on this multi-join view (not auto-updatable) but confirm grant-hygiene failure.
- **Depends on:** `apparatus`, `scopes`, `projects`, `clients`, `tasks`, `employees`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 3 total, areas {"docs": 2, "infra": 1}. 3 repo callsites (grep evidence only, NOT the signed static_repo overlay): 2 in docs (docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md line 447 listing legacy views; docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232 enumerating the 29-view definer program) and 1 in infra, which is the defining SQL itself (infra/database/source-lineage/apex-resa/pm-project-pss/schema/08_apparatus_completion_workflow.sql line 36). No application-code consumers found; database_deps_found_consumers = 0.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - underlying relations in the definition are unqualified (apparatus, scopes, projects, clients, tasks, employees) — presumed public via search_path but not schema-qualified in source
  - the defining SQL is source-lineage (apex-resa/pm-project-pss) which may not exactly match the live prod definition; live pg_get_viewdef not in the facts file
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay showing zero (or which) PostgREST/API reads of v_apparatus_approval_queue
  - signed external_clients overlay confirming no external tool or dashboard queries the view
  - signed operator_declaration on whether any PM approval workflow/UI still depends on this queue view
  - signed advisor_findings overlay (Supabase security advisor result for definer views)
  - signed Data-API exposure configuration overlay confirming whether public schema exposes this view to anon/authenticated
  - signed static_repo overlay superseding the grep-only callsite census
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor: rationale asserts the view is 'over six public tables' as fact, while the schema is only presumed (relations are unqualified in the source SQL); the proposal already self-corrects this in unresolved_blockers, so it is a wording tension, not an ungrounded claim.
  - Minor: privilege_summary calls the seven privileges 'the full default-grant set' — the facts observe the privileges but not their provenance; 'full relation-privilege set' would be strictly traceable.
  - Minor: the claim that write-type privileges are 'likely inert (not auto-updatable)' is Postgres-rule inference, not in the facts file; it is hedged with 'likely' and is correct for a multi-join view, but should remain flagged as inference.
  - Verified: dependencies re-derived independently from the definition snippet as exactly {apparatus, scopes, projects, clients, tasks, employees} — nothing missed, nothing invented (trigger/function DDL in the same snippet correctly excluded).
  - Verified: all five mandated 'awaiting signed overlay' blockers present, plus the static_repo grep-only caveat and two apt view-specific blockers (unqualified relations; source-lineage vs live pg_get_viewdef drift).
  - Verified: not an mcp_* Packet-01 view, so the defer carve-out does not apply; harden is the best fit — retain/compat/promote/defer each fail on the observed facts (zero dependents, zero evidenced consumers, full anon/authenticated grants, legacy lineage consistent with public-as-legacy placement).

### `public.v_apparatus_resources`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned definer view (security_invoker not set) in prod public with the full seven-privilege suite (SELECT through TRUNCATE) granted to both anon and authenticated, meaning any Data-API caller could read — and, if the view is auto-updatable, write — its underlying rows with the owner's RLS-bypassing authority. The census shows zero database dependents and zero database-dep consumers, and the only repo callsites are two documentation files (a schema reference listing and the disposition-lane spec that enumerates it as one of the 29 definer-view program members); no application code references it. There is no defining SQL in the repo (definition_count 0), so definer semantics cannot be shown to be required and the underlying relations' sensitivity cannot be assessed — which argues for closing the exposure lever rather than retaining it. Provisional lean: convert to security_invoker=true and revoke anon/authenticated grants, pending the five signed overlays; nothing in the facts suggests it embodies a canonical model needing promote or an active migration needing compat.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view (observed). Because the view runs with definer semantics under owner postgres, any anon/authenticated SELECT bypasses caller RLS on the underlying tables, and the write privileges could pass through if the view is auto-updatable — a maximal legacy GRANT-ALL posture far broader than any read-only consumer would need.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 2 total, areas {"docs": 2}. 2 repo callsites, both in docs (repo-grep evidence only, NOT the signed static_repo overlay): docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md line 448 (schema reference listing) and docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232 (the 29-view definer-view program enumeration). No application, migration, or client-code callsites found.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - no defining SQL found in repo — underlying relations, data sensitivity, and auto-updatability cannot be assessed offline
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any live SELECT/write traffic against the view)
  - signed external_clients overlay (PostgREST/API consumers outside the repo)
  - signed operator_declaration overlay (operator statement on whether definer semantics or write grants are intentionally relied upon)
  - signed advisor_findings overlay (Supabase advisor findings for this view)
  - signed Data-API exposure configuration overlay (whether public is an exposed schema for this relation)
  - signed static_repo overlay to supersede the repo-grep callsite data
  - recovered view definition (live pg_get_viewdef or migration history) to enumerate underlying relations and assess auto-updatability before revoking write privileges
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor: the rationale asserts 'security_invoker not set' as fact; this traces to the policy block (a permitted anchor), not the facts file, which does not record reloptions — a one-word provenance tag ('per policy context') would make it fully self-documenting.
  - Minor: privilege_summary calls the posture 'legacy GRANT-ALL' — the legacy characterization is an inference from the privilege pattern, not an observed fact; harmless but worth phrasing as inference.
  - No material issues: disposition, rationale claims, empty dependencies (definition_count 0 means no snippet exists to derive from), all five awaiting-signed-overlay blockers, the static_repo repo-grep caveat, and the view-specific missing-definition blocker all verify against the facts file; the view is not an mcp_* Packet-01 view, so defer-by-governance does not apply.

### `public.v_apparatus_testing_status`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a presentation-layer convenience view ("Field crew view of apparatus testing queue") joining apparatus/scopes/projects with active-row filters — not a canonical model needing promotion, and nothing in the facts justifies definer semantics. It is a postgres-owned definer view with anon AND authenticated holding all seven table privileges, so any anon caller can SELECT through it with owner privileges, bypassing RLS on the three base tables. The census shows zero database dependents and zero inbound/outbound FKs, and all 9 repo callsites are docs/lineage artifacts (including the 29-view definer-view-program spec listing) with no application-code consumers, so hardening (security_invoker=true plus revoking anon/authenticated) has no repo-visible breakage surface. It is explicitly enumerated in the 29-view definer-view program, distinct from the Packet-01 mcp_* views. Provisional harden pending the five signed overlays — the "field crew" purpose hints at possible external/mobile consumers that only runtime_logs, external_clients, and an operator declaration can rule in or out.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 2 (docs/architecture/database-lineage/spec/VIEW_DEFINITIONS.md:285; infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql:223)
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view (observed). Because the view is owned by postgres with definer semantics (security_invoker not set), SELECT by anon/authenticated executes with owner privileges and bypasses caller RLS on the underlying apparatus, scopes, and projects tables — a live exposure lever if the view is Data-API reachable. The write-side privileges (INSERT/UPDATE/DELETE/TRUNCATE) are inert in practice since a three-table join view is not auto-updatable, but the grant footprint is grossly broader than any plausible consumer need; PUBLIC-style blanket grants like this are exactly what harden targets.
- **Depends on:** `apparatus`, `scopes`, `projects`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 9 total, areas {"docs": 6, "infra": 3}. 9 repo callsites, all documentation or lineage: docs=6 (database-lineage README table row, VIEW_DEFINITIONS.md definition block, knowledge-domain SCHEMA_REFERENCE.md listing, and the 2026-07-11 signed-overlay-evidence-design spec enumerating it in the 29-view definer program) and infra=3 (source-lineage 04_views.sql DDL + comment). Zero application-code consumers found. Note: this is repo-grep evidence only, NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data is repo-grep evidence only; signed static_repo overlay not yet produced
  - the two repo definitions diverge in the location column construction (string concatenation with || vs CONCAT_WS), so the canonical deployed definition on prod is unconfirmed from repo evidence
  - view comment declares a 'field crew' audience, implying possible external/mobile consumers that repo grep cannot resolve; must be settled by runtime_logs/external_clients/operator_declaration before revoking authenticated SELECT
- **Required evidence before any accepted decision:**
  - runtime_logs signed overlay (any PostgREST/API reads of v_apparatus_testing_status, especially anon/authenticated role)
  - external_clients signed overlay (field-crew dashboards or mobile clients reading the view)
  - operator_declaration (confirm no sanctioned field-crew consumer depends on definer semantics or anon/authenticated SELECT)
  - advisor_findings signed overlay (Supabase advisor security_definer_view / exposed-view findings)
  - Data-API exposure configuration signed overlay (whether public schema exposure makes this view PostgREST-reachable)
  - signed static_repo overlay to supersede the grep-based callsite census
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor wording: privilege_summary calls the grants 'PUBLIC-style blanket grants' — the observed grants are to anon and authenticated specifically, not the PUBLIC pseudo-role; the characterization is rhetorical, not a factual error.
  - Minor understatement: the claim that write-side privileges are 'inert in practice' overlooks that the granted TRIGGER privilege could in principle allow an INSTEAD OF trigger that makes the join view writable; harden's revocation covers this anyway, so it does not affect the disposition.
  - Minor tone mismatch: the rationale asserts the anon RLS-bypass read path somewhat unconditionally, while the privilege_summary correctly conditions live exposure on the unresolved Data-API reachability overlay; the SQL-level claim is still accurate per the policy block's definer-semantics anchor.

### `public.v_apparatus_type_resources`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a definer-semantics view (security_invoker not set) owned by postgres in the prod public schema, with the maximal grant posture: anon and authenticated each hold all seven table-level privileges. The census found zero database dependents and zero database-side consumers, and the only repo callsites are two documentation mentions (a schema reference list and the 29-view program spec itself) — no application code references the view by name in the grep evidence. Nothing in the facts justifies definer semantics or write-capable grants to anonymous roles, so the provisional lean is harden: revoke anon/authenticated grants (at minimum the write privileges, likely SELECT too) and/or convert to security_invoker=true. The lean is provisional and cannot be executed yet: no defining SQL was found in the repo, so the exact RLS-bypass surface (which base tables it reads) is unknown, and the five signed evidence overlays are outstanding. If the signed overlays confirm zero runtime/external consumers, the operator may also consider whether the view is dead and eligible for retirement rather than mere hardening; that escalation needs operator declaration.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view (observed). Because the view runs with definer semantics under owner postgres, any anon/authenticated SELECT through it bypasses caller RLS on whatever base relations it reads — and since the defining SQL is unknown, the bypassed surface is unquantified. Write privileges (INSERT/UPDATE/DELETE/TRUNCATE) could additionally flow through to base tables if the view is auto-updatable. This is the widest possible exposure posture for a definer view and is far broader than the zero consumers observed in database deps and repo grep.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 2 total, areas {"docs": 2}. 2 repo callsites, both in docs (repo-grep evidence only, NOT the signed static_repo overlay): docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md line 448 (listed among apparatus views) and docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232 (the 29-view definer-view-program roster itself). No application, migration, or API code callsites found; database_deps found 0 consumers and dependent_objects is empty.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in facts file is repo-grep evidence only, not the signed static_repo overlay
  - no defining SQL found in repo (definition_count=0) — base relations and RLS-bypass surface unknown; definition must be pulled from prod catalog (pg_get_viewdef) before executing any hardening
  - zero observed consumers makes retire-vs-harden ambiguous; needs operator declaration
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any prod reads of the view via Data API or direct SQL)
  - signed external_clients overlay (non-repo consumers, e.g. reporting tools or PostgREST clients)
  - signed operator_declaration overlay (is this view still needed; retire vs harden)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes these grants reachable via PostgREST)
  - signed static_repo overlay to supersede the repo-grep callsite data
  - view definition from prod catalog (pg_get_viewdef) to enumerate base relations and confirm the RLS-bypass surface before applying security_invoker/revoke
- **Adversarial verifier notes (agrees=true; informative):**
  - Non-blocking note: the facts record rls_enabled=false for the view; RLS does not apply to plain views (relkind v), so this is immaterial and the proposal correctly omits it — no change needed.
  - Non-blocking note: the privilege_summary's claim that writes 'could flow through to base tables if the view is auto-updatable' is properly hedged speculation, since with definition_count=0 auto-updatability is unknowable from the facts; it is framed as conditional, so it does not count as an ungrounded claim.

### `public.v_approval_queue_summary`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a definer-semantics aggregate view (owner postgres, security_invoker not set) summarizing pending-review apparatus by project, exposing business metadata (project number/name, client name, project lead, pending hours/counts) drawn from four RLS-bearing base tables that the definer view would bypass. Both anon and authenticated hold the full seven-privilege set (SELECT through TRUNCATE), which is far broader than any plausible consumer of a read-only summary needs; the write privileges are almost certainly inert on a grouped view but are still grant-hygiene defects. The census shows zero database dependents and the only repo callsites are two documentation files plus the defining source-lineage SQL itself — no application code reads it — so nothing in the facts justifies definer semantics or the current grants. Harden (convert to security_invoker=true and revoke anon/authenticated) is the minimal-risk provisional lean; retain has no supporting facts, and promote/compat cannot be argued because no canonical-model duplication or migrating consumer is evidenced in the facts file. If the signed overlays confirm zero runtime/external consumers, the operator may later consider whether the view is a drop candidate, but that exceeds this reconciliation's vocabulary and evidence.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/08_apparatus_completion_workflow.sql:233)
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view (observed). Because the view runs with definer semantics under owner postgres, any anon/authenticated SELECT bypasses caller RLS on the underlying apparatus/scopes/projects/clients tables — a live exposure lever for project and client business metadata if the public schema is Data-API exposed (that exposure dimension is not yet observed). The write privileges are likely non-functional on an aggregate (GROUP BY) view but represent default-privilege over-grant and should be revoked regardless.
- **Depends on:** `apparatus`, `scopes`, `projects`, `clients`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 3 total, areas {"docs": 2, "infra": 1}. 3 repo-grep callsites (NOT the signed static_repo overlay): docs x2 (docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md listing views; docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md enumerating the 29-view definer program) and infra x1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/08_apparatus_completion_workflow.sql:233, the CREATE OR REPLACE VIEW itself). No application-code consumers appear in the grep evidence.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in facts file is repo-grep evidence only, not the signed static_repo overlay
  - base-table relations in the defining SQL are unqualified (apparatus/scopes/projects/clients); presumed public.* at creation but schema resolution not verifiable offline
  - zero database dependents and zero app-code callsites leave actual consumers entirely unevidenced; whether any anon/authenticated client reads this view (which harden would break) is unknown until overlays land
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any observed reads of v_approval_queue_summary in prod)
  - signed external_clients overlay (Data-API / PostgREST clients selecting the view as anon or authenticated)
  - signed operator_declaration overlay (operator statement on whether the legacy apex-resa PM completion-workflow consumers still exist)
  - signed advisor_findings overlay (Supabase advisor security findings for this definer view)
  - config-backed Data-API exposure overlay (is public in the exposed-schemas platform config)
  - signed static_repo overlay to supersede the repo-grep callsite evidence
- **Adversarial verifier notes (agrees=true; informative):**
  - Rationale claims the four base tables are 'RLS-bearing' and privilege_summary says the view 'bypasses caller RLS on the underlying apparatus/scopes/projects/clients tables'; the facts file records RLS state only for the view itself (rls_enabled=false) and contains no RLS facts about the base tables. The policy block supports the general definer-bypass mechanism but not the specific base-table RLS assertion. Hedge as 'would bypass any base-table RLS' — a wording fix; not disposition-changing since harden stands on the observed seven-privilege anon/authenticated grants and unjustified definer semantics alone.

### `public.v_equipment_current_status`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a definer-semantics view owned by postgres joining equipment, employees, projects, and locations — employee-name and equipment-location data that would bypass base-table RLS for any caller with SELECT. Both anon and authenticated hold ALL seven privileges on it, the signature of a blanket GRANT ALL, which is far broader than any plausible consumer need. The census shows zero database dependents and zero inbound/outbound FKs, and the only repo callsites are two documentation listings plus the defining SQL itself in the apex-resa source-lineage tree — no application code reads it, consistent with legacy/compat residue under the 2026-07-09 schema-placement policy rather than a canonical model warranting promote. Hardening (set security_invoker=true and revoke anon/authenticated grants, retaining only what a proven consumer needs) closes the exposure lever without dropping the object; whether it can subsequently be retired or must become a compat shim depends on the runtime and external-client overlays. This is a provisional lean pending the five signed overlays and operator review; no evidence found here justifies retain, and no consumer-migration story exists to justify compat.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql:74)
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view (observed). Because the view runs with definer semantics under owner postgres, SELECT alone lets an unauthenticated (anon) caller read joined equipment/employee/project/location rows while bypassing any RLS on the underlying tables — the core exposure lever. The write-side privileges are likely inert (a four-relation LEFT-JOIN view is not auto-updatable) but indicate blanket GRANT ALL hygiene debt and should be revoked regardless.
- **Depends on:** `equipment`, `employees`, `projects`, `locations`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 3 total, areas {"docs": 2, "infra": 1}. 3 repo-grep callsites: docs x2 (docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md line 449 view inventory; docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232 listing the 29-view definer program) and infra x1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql line 74, which is the CREATE VIEW definition itself). No application-code consumers appear in the grep. This is repo-grep evidence only, NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in facts file is repo-grep evidence only, not the signed static_repo overlay
  - defining SQL lives in a shared source-lineage file (07_equipment_project_assignment.sql) that also creates v_project_equipment, v_equipment_movement_history, RLS policies, and a sync trigger — hardening actions must be scoped to this view, not the file
  - base relations in the definition are unqualified in the source; presumed public-schema resolution is unverified offline
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any PostgREST/API SELECT traffic against v_equipment_current_status)
  - signed external_clients overlay (non-repo consumers: dashboards, integrations, MCP clients)
  - operator_declaration on whether the apex-resa equipment-tracking lane is live or superseded by the ops.* lane
  - signed advisor_findings overlay (Supabase security advisor results for definer views)
  - signed Data-API exposure configuration overlay (whether public views are served by the Data API)
  - signed static_repo overlay to supersede the repo-grep callsite census
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor: the rationale's claim that a four-relation LEFT-JOIN view is not auto-updatable is general PostgreSQL knowledge, not traceable to the facts file or policy block; it is appropriately hedged ('likely inert') and the revoke recommendation does not depend on it.
  - Minor: the docs callsite at docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232 has its text truncated in the facts file before v_equipment_current_status appears ('...v_appa'); the grep hit implies the name is on that line, but the visible snippet does not literally show it.
  - Minor: 'signature of a blanket GRANT ALL' is an inference from the seven-privilege pattern rather than an observed GRANT statement; reasonable, and clearly framed as interpretation of the observed privilege arrays.

### `public.v_equipment_movement_history`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a legacy apex-resa lineage view (defined in infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql:109) sitting in public with definer semantics and the full seven-privilege grant set to both anon and authenticated — grants vastly broader than any evidenced consumer needs, since the census shows zero database dependents and repo grep shows zero application callsites (only two docs listings plus the defining SQL itself). Definer semantics are not clearly required: the same lineage file enables RLS on equipment_assignments with permissive USING(true) policies, so nothing in the repo evidence indicates the view depends on bypassing caller RLS. The provisional lean is therefore harden — set security_invoker=true and revoke anon/authenticated grants (at minimum the write/TRIGGER/TRUNCATE/REFERENCES privileges, and SELECT absent a declared consumer). It is listed as one of the 29-definer-view program members in docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md, so it belongs to this program, not to Packet 01. This remains provisional: the repo definition may not match the live prod definition, and the five evidence overlays (runtime logs, external clients, operator declaration, advisor findings, Data-API exposure) are all unresolved, so an unknown live consumer could still surface before apply.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql:109)
- **Privileges:** anon and authenticated each hold all seven relation privileges on the view (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) per observed census. Because the view is owned by postgres with security_invoker unset (definer semantics), any anon/authenticated SELECT reads the five underlying tables with the owner's privileges, bypassing caller RLS — a live exposure lever if the public schema is Data-API exposed (exposure state itself not yet observed). The write-side privileges are grant hygiene violations rather than a direct write path (a five-table join view is not auto-updatable), but they exceed any evidenced consumer need, since no consumers are evidenced at all.
- **Depends on:** `equipment_assignments`, `equipment`, `employees`, `projects`, `locations`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 3 total, areas {"docs": 2, "infra": 1}. 3 repo-grep hits, none in application code: docs (2) — a name listing in docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md:450 and membership in the 29-definer-view program list in docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232 — and infra (1), which is the CREATE OR REPLACE VIEW statement itself in the apex-resa source-lineage schema file. No app, API, or client consumers appear in the grep. This is repo-grep evidence only, not the signed static_repo overlay (static_repo state: not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - repo definition is from the apex-resa source-lineage tree and may not match the live prod view definition; live catalog definition unverified offline
  - base-table RLS posture in prod (equipment_assignments permissive USING(true) per lineage snippet) unverified, so the practical exposure delta of invoker conversion is unconfirmed
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any live query traffic against v_equipment_movement_history)
  - signed external_clients overlay (PostgREST/API/service-role consumers)
  - signed static_repo overlay (authoritative callsite scan superseding this grep)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes anon SELECT reachable)
  - operator declaration: whether equipment movement history is an active workflow with any intended consumer, or a dead apex-resa lineage artifact
  - live prod view definition and base-table RLS state to confirm the repo lineage snippet matches production before applying security_invoker conversion
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor (non-blocking): the 29-definer-view-program membership claim cites docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232, but the callsite snippet in the facts file is truncated before v_equipment_movement_history appears in the list text; membership is inferred from the grep hit on that line rather than visible verbatim text. The inference is sound (the callsite record exists because the name matched), but the proposal could note the truncation.
  - Minor (non-blocking): the rationale states security_invoker is unset; this comes from the policy block's blanket definer-semantics premise, not from an explicit per-view field in the facts file (the facts record owner=postgres and relkind=v but no reloptions). Consistent with policy, but the provenance is the policy anchor, not an observed census field.

### `public.v_guide_image_completeness`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned definer view (security_invoker not set, rls_enabled=false) whose grants are maximally broad: anon and authenticated each hold all seven relation privileges, including write-class privileges (DELETE/INSERT/UPDATE/TRUNCATE) that no reporting-style completeness view plausibly needs. The census shows zero database dependents and zero database-dep consumers, and the only repo callsite is the disposition-lane spec that enumerates the 29-view program itself — i.e., no application, tooling, or migration consumer was found by grep. No defining SQL exists in the repo, so the base relations it reads under owner rights cannot be enumerated offline, which makes the definer+broad-grant posture strictly worse: an unauditable RLS bypass with no demonstrated consumer. The proportionate provisional action is to harden in place — revoke anon/authenticated grants and/or convert to security_invoker=true — rather than defer, because the privilege posture alone justifies the lean regardless of what the definition turns out to be. Promote/compat cannot be assessed without the definition; retain is unsupportable on these facts. Final action must wait on the five signed overlays plus retrieval of the live view definition.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view (the default-PUBLIC full-grant footprint). Because the view is owned by postgres with definer semantics, any anon/authenticated SELECT executes against the underlying tables with the owner's rights, bypassing caller RLS entirely; if the view is auto-updatable, the write privileges could also permit writes through it. With zero identified consumers, this is maximal exposure with no demonstrated need — grants are clearly broader than consumers require.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 1 total, areas {"docs": 1}. Exactly 1 repo callsite, in docs only: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232, which is the enumeration of the 29-view definer program itself — not an application, script, or migration consumer. This is repo-grep evidence only, NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - no defining SQL found in repo (definition_count=0) — base relations read under definer semantics cannot be enumerated; live pg_get_viewdef needed before final disposition
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any PostgREST/Data-API or client reads of this view in prod)
  - signed external_clients overlay (non-repo consumers)
  - signed operator_declaration overlay (operator statement of the view's purpose and whether anon/authenticated access is intended)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes this view reachable via PostgREST)
  - signed static_repo overlay (to supersede the grep-only callsite data)
  - live view definition from prod (pg_get_viewdef) to enumerate base relations and confirm whether definer semantics touch RLS-protected tables and whether the view is auto-updatable
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor (wording, not disposition-affecting): privilege_summary calls the seven-privilege footprint 'the default-PUBLIC full-grant footprint' — the facts file records only effective privileges for anon/authenticated, not whether they arise from default PUBLIC grants or explicit GRANTs; the provenance attribution is an inference beyond the facts. Recommend rephrasing to 'all seven relation privileges (consistent with, but not proven to be, a default-PUBLIC grant footprint)'.
  - Verified clean: all rationale claims trace to the facts file or policy block; dependencies=[] is correct given definitions=[] (definition_count=0); all five mandatory awaiting-signed-overlay blockers present plus the static_repo grep-only caveat and the view-specific missing-definition blocker; view is not an mcp_* Packet-01 view, so defer-by-governance does not apply; harden is the best-fitting provisional disposition since the anon/authenticated full-privilege posture on a postgres-owned definer view with zero observed consumers justifies the lean regardless of the unretrieved definition.

### `public.v_image_production_queue`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a definer-semantics view (security_invoker not set) owned by postgres with the broadest possible grant surface: anon and authenticated each hold all seven privileges (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER), so any anonymous caller can read through it with caller RLS bypassed, and write privileges could reach base tables if the view is auto-updatable. Nothing in the facts justifies that posture: zero database dependents, zero database-dep consumers, and the only repo callsite is the disposition-lane governance spec itself listing the 29-view program — no application code references the name. With definition_count=0 there is no evidence that definer semantics are required at all. The provisional lean is harden: revoke anon/authenticated grants (at minimum the write privileges, which no view legitimately needs granted to anon) and convert to security_invoker=true, pending the signed overlays. It is not one of the two mcp_* Packet-01 views, so it belongs in the 29-view program; promote/compat cannot be assessed without a definition, and retain is unsupportable given the grant breadth versus zero observed consumers.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold ALL seven relation privileges (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER) on a postgres-owned definer view. Under definer semantics this means unauthenticated Data-API callers (if the schema is exposed — unresolved) can SELECT with base-table RLS bypassed, and the write grants could permit anon writes through the view if it is simple/auto-updatable. This is the maximum-exposure posture; the grants are far broader than any observed consumer needs (none were observed).
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 1 total, areas {"docs": 1}. One repo callsite total, area=docs: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, which is the signed-overlay evidence-design spec enumerating the 29-view definer program — i.e., the only repo mention of this view is the audit lane itself, not a consumer. No app, API, or migration callsites were found by grep. This is repo-grep evidence only, NOT the signed static_repo overlay (static_repo state: not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration (in_data_api_exposed_schema not_observed; authoritative only from platform config)
  - static_repo callsite data above is repo-grep evidence only, not the signed static_repo overlay (static_repo: not_observed)
  - no defining SQL found in repo (definition_count=0) — base relations unknown; cannot verify whether definer semantics are required or whether the view is auto-updatable (which determines whether the anon/authenticated write grants are exploitable)
  - view purpose unknown — 'image production queue' does not map to any lane or consumer in the facts file; may be an orphan from a retired pipeline, which an operator declaration must confirm before revoke/convert
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any PostgREST/API reads of v_image_production_queue in prod)
  - signed external_clients overlay (non-repo consumers: dashboards, scripts, third-party tools)
  - signed operator_declaration overlay (is the image-production pipeline live, dormant, or retired; is definer read-through intentionally relied on)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (whether public schema exposure actually surfaces this view to anon/authenticated via PostgREST)
  - signed static_repo overlay to supersede the repo-grep callsite evidence
  - authoritative view definition (pg_get_viewdef from prod, since no repo definition exists) to enumerate base relations and determine auto-updatability before the revoke/security_invoker change is sequenced
- **Adversarial verifier notes (agrees=true; informative):**
  - Non-blocking: proposal omits the observed rls_enabled=false fact; immaterial for a view (posture is set by grants + security_invoker, not RLS on the view itself) but could be cited for completeness.
  - Non-blocking: the single callsite's text snippet in the facts file is truncated before v_image_production_queue's name appears; the claim that the 29-view program list is the matching line is a reasonable inference from callsite_count=1 and the visible 'Definer-view-program (29)' prefix, not directly visible text.
  - Non-blocking: 'security_invoker not set' is grounded in the policy block rather than an explicit field in the facts file; the policy block authorizes this, but the eventual signed evidence should confirm reloptions directly.

### `public.v_image_sourcing_summary`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned definer view (security_invoker not set) with the full default grant set to both anon and authenticated, so any API-reachable caller could read whatever the view selects with owner privileges, bypassing RLS on the underlying tables. The census shows zero database dependents, zero repo definition, and the only repo callsite is the disposition-ledger design doc itself listing the 29-view program — no application code references it. With no evidence that definer semantics are required and no identifiable consumer needing anon/authenticated access, the proportionate provisional action is to harden: revoke anon/authenticated grants and convert to security_invoker=true. The absence of any defining SQL in the repo also makes this a candidate for outright removal, but that escalation needs operator declaration plus the runtime/external-client overlays to confirm nothing unseen consumes it; harden is the safe posture fix in the meantime. Confidence is capped because the view's underlying relations are unknown (no definition found), so the actual exposure surface behind the definer bypass cannot be characterized from repo facts.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold ALL seven relation privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on the view — the classic unpruned default-PUBLIC posture. On a postgres-owned definer view, SELECT alone lets any anon or authenticated caller read the underlying base tables with owner rights, bypassing caller RLS; the write-shaped privileges are additionally a potential write path if the view is auto-updatable. Grants are plainly broader than any plausible consumer need (census found zero consumers), so this is an active exposure lever pending hardening.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 1 total, areas {"docs": 1}. Exactly 1 repo callsite, in docs only: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, which is the design spec's enumeration of the 29-view definer program — a self-referential governance mention, not a consumer. No application, API, or tooling code references the view name anywhere in the repo. This is repo-grep evidence only, NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - no defining SQL found in repo (definition_count=0) — underlying relations and exposure surface unknown; dependencies list is empty for lack of evidence, not because the view reads nothing
  - static_repo callsite data is repo-grep evidence only, not the signed static_repo overlay
  - cannot distinguish harden vs full removal (view appears orphaned: 0 dependents, 0 app callsites, no repo definition) without operator declaration and runtime/external-client overlays
- **Required evidence before any accepted decision:**
  - signed overlay: runtime_logs (any production SELECTs against the view)
  - signed overlay: external_clients (PostgREST/Data-API or external tool usage)
  - signed overlay: operator_declaration (is the view still wanted; harden vs drop)
  - signed overlay: advisor_findings (Supabase advisor security findings for this view)
  - signed overlay: Data-API exposure configuration (whether public schema exposure makes anon SELECT reachable via PostgREST)
  - signed static_repo overlay (to supersede the raw grep evidence)
  - authoritative view definition from prod (pg_get_viewdef) to enumerate underlying relations and characterize the definer-bypass exposure surface
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor wording only (non-blocking): privilege_summary calls the grants 'the classic unpruned default-PUBLIC posture', but the facts file records only effective privileges for anon/authenticated, not the grant mechanism; the default-PUBLIC attribution is an inference beyond the facts. Disposition, rationale, dependencies (correctly empty, flagged as evidence-absence), and all five mandatory awaiting-signed-overlay blockers plus the static_repo grep-only caveat verify cleanly against the facts file.

### `public.v_neta_test_details`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a definer-semantics view (owner postgres, security_invoker not set) on which both anon and authenticated hold ALL seven relation privileges (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER) — a grant surface far broader than any consumer evidence supports. The census shows zero database dependents, zero database-dep consumers, and the only repo callsites are two documentation mentions (an architecture schema reference and the 29-view program enumeration in the overlay-evidence design spec); no application code references the view. No defining SQL exists in the repo, so definer semantics cannot be shown to be required by the definition, and nothing in the facts justifies retaining the current posture. Under the 2026-07-09 schema-placement policy (public = legacy/compat/shims only) and the definer-view exposure lever, the provisional lean is harden: revoke anon/authenticated grants (at minimum the write privileges, which on an auto-updatable view are a live write path that bypasses caller RLS) and convert to security_invoker=true unless a signed overlay surfaces a consumer that requires definer semantics. If the signed overlays confirm zero consumers, the operator may later choose retirement instead, but that decision needs the overlay evidence; harden is the safe reversible posture now. This is a provisional proposal for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view (observed). Because the view runs with definer semantics under owner postgres, any SELECT by anon/authenticated bypasses RLS on the underlying tables; the write privileges (INSERT/UPDATE/DELETE, plus TRUNCATE) additionally constitute a potential unauthenticated write path through the view if it is auto-updatable — unverifiable here because no definition was found. RLS on the view relation itself is false (normal for views, but it means nothing constrains rows at the view layer). Whether this is actually reachable from the network depends on Data-API exposure configuration, which is not_observed pending the config-backed overlay.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 2 total, areas {"docs": 2}. 2 repo callsites, both in docs (repo-grep evidence only, NOT the signed static_repo overlay): docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md:450 lists the view name in a schema inventory, and docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232 enumerates it within the 29-view definer-view program. No application-code, migration, or client callsites found in the repo grep.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only; awaiting signed overlay: static_repo
  - no defining SQL found in repo (definition_count=0) — underlying relations, definer necessity, and auto-updatability (write-path reachability) cannot be assessed from source; definition must be recovered from the prod catalog via a governed channel
- **Required evidence before any accepted decision:**
  - signed overlay: runtime_logs (any observed reads/writes against the view)
  - signed overlay: external_clients (PostgREST/API consumers of the view)
  - signed overlay: operator_declaration (intended consumers and whether definer semantics are required)
  - signed overlay: advisor_findings (Supabase advisor security findings for this view)
  - signed overlay: Data-API exposure configuration (whether public schema exposure makes the grants network-reachable)
  - signed overlay: static_repo (authoritative callsite census superseding the repo-grep data)
  - recovered view definition from prod catalog (pg_get_viewdef) to enumerate dependencies and confirm auto-updatability before finalizing the harden scope
- **Adversarial verifier notes (agrees=true; informative):**
  - Wording quibble only: privilege_summary asserts SELECT 'bypasses RLS on the underlying tables', but with definition_count=0 the underlying relations and whether they carry RLS are unknown; the claim is grounded in the policy block's definer-semantics anchor and the proposal itself flags the unrecovered definition, so it is hedged elsewhere but could be phrased conditionally ('would bypass RLS on any RLS-protected base relations').
  - Minor traceability note: 'security_invoker not set' is grounded in the verbatim policy block, not in any field of the facts file; acceptable because the policy anchor states definer semantics for these views, but worth knowing the facts file itself carries no reloptions evidence.
  - Dependencies list is empty because no definition snippet exists to derive from (definition_count=0); this is correct and properly flagged as a blocker, but it means the final harden scope (which base relations are exposed, whether the view is auto-updatable) cannot be validated until pg_get_viewdef is recovered via a governed channel — already captured in required_evidence.

### `public.v_pending_handoffs`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

The view is a definer-semantics view owned by postgres over ai_handoffs JOIN ai_tasks, with anon and authenticated each holding ALL seven privileges (SELECT/INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER) — far broader than any evidenced consumer needs, since the census shows zero database dependents and repo grep finds no application-code callsites (3 docs references plus the defining SQL in the apex-resa source-lineage snapshot). Nothing in the facts indicates definer semantics are required: the view is a simple pending-queue projection with no privilege-bridging rationale recorded. The defining SQL lives only under infra/database/source-lineage/apex-resa/automation-orchestration (legacy lineage material), consistent with a legacy shim rather than a canonical model, so promote is not indicated and retain is unjustified. Harden — convert to security_invoker=true and revoke anon/authenticated grants down to what consumers actually need (likely nothing) — is the right provisional lean; if the signed overlays confirm zero runtime/external consumers, the operator may later choose full retirement, but that exceeds this vocabulary. This is provisional pending the five signed overlays and stays inside the 29-view program (it is not one of the two mcp_* Packet-01 views).

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql:235)
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view (observed). Because the view runs with definer semantics under owner postgres, any anon/authenticated SELECT (e.g., via Data API if the schema is exposed — exposure itself unresolved) reads ai_handoffs and ai_tasks with owner privileges, bypassing any caller RLS on those base tables. The write-class grants are likely inert for direct DML (join view is not auto-updatable) but are grant-hygiene violations and would become live if INSTEAD OF triggers/rules were ever added. Net: maximal default grants on a definer view = full RLS bypass for reads by both anon and authenticated.
- **Depends on:** `ai_handoffs`, `ai_tasks`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 4 total, areas {"docs": 3, "infra": 1}. 4 repo callsites (grep evidence only, NOT the signed static_repo overlay): 3 in docs — an example query in docs/architecture/control-plane-lineage/apex-resa/AI_ORCHESTRATION_PROTOCOL.md:220, a name listing in docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md:450, and the 29-definer-view program roster in docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232 — plus 1 in infra: the CREATE VIEW statement itself at infra/database/source-lineage/apex-resa/automation-orchestration/schema/10_ai_orchestration.sql:235. No application/runtime code consumers appear anywhere in the repo grep.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in facts file is repo-grep evidence only, not the signed static_repo overlay
  - repo definition comes from the apex-resa source-lineage snapshot (infra/database/source-lineage/...) and may not match the live prod definition
  - defining SQL uses unqualified relation names (ai_handoffs, ai_tasks); presumed public but schema not stated in the snippet
  - status of the apex-resa AI orchestration handoff workflow (live vs superseded by the durable orchestration lane) is not established by the facts file
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any SELECT traffic against v_pending_handoffs)
  - signed external_clients overlay (non-repo consumers, e.g., Desktop/other-host tooling issuing the documented SELECT * FROM v_pending_handoffs)
  - signed operator_declaration overlay (is the apex-resa ai_handoffs/ai_tasks orchestration workflow live, deprecated, or superseded?)
  - signed advisor_findings overlay (Supabase advisor security findings for this definer view)
  - config-backed Data-API exposure overlay (is public schema/view reachable via PostgREST for anon/authenticated?)
  - signed static_repo overlay to supersede the grep-based callsite census
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor (non-blocking): static_callsite_summary states the docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232 roster line includes v_pending_handoffs, but the facts file's text for that callsite is truncated before the view name appears; the inclusion is a reasonable inference from the grep match, not directly visible text.
  - Minor (non-blocking): the claim 'No application/runtime code consumers appear anywhere in the repo grep' is supported only indirectly by callsite_areas {docs:3, infra:1}; it is an absence claim over grep evidence, which the proposal itself already flags as not the signed static_repo overlay.

### `public.v_project_equipment`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

The view is a postgres-owned definer view (security_invoker not set) whose only repo definition lives under infra/database/source-lineage/apex-resa/ — legacy lineage import material, consistent with the schema-placement policy's characterization of public as legacy/compat only, and not evidence of a canonical model needing promotion. The census shows zero database dependents and zero inbound/outbound FKs, and the only repo callsites are two documentation listings plus the defining SQL itself — no application-code consumer appears anywhere in the grep evidence. Meanwhile anon and authenticated both hold the full seven-privilege set (DELETE/INSERT/REFERENCES/SELECT/TRIGGER/TRUNCATE/UPDATE), which is grossly broader than the empty known-consumer set and, combined with definer semantics, lets unauthenticated callers read projects/equipment rows with the owner's rights, bypassing any RLS on those tables. Nothing in the facts indicates definer semantics are required, so the provisional lean is harden: convert to security_invoker=true and revoke anon/authenticated grants (at minimum all write/TRIGGER/TRUNCATE/REFERENCES privileges). This remains provisional pending the signed overlays — a runtime or external consumer relying on definer semantics would force reconsideration toward compat.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql:98)
- **Privileges:** anon and authenticated each hold all seven relation privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on the view; rls_enabled=false (views cannot carry their own RLS). Because the view runs with definer semantics under owner postgres, any anon/authenticated SELECT reads the underlying projects and equipment tables with the owner's privileges, bypassing caller RLS on those base tables — an active exposure lever if the schema is Data-API exposed (exposure config not yet observed). The join makes the view non-auto-updatable, so the write grants are likely inert today, but they are gratuitous surface that should be revoked regardless.
- **Depends on:** `projects`, `equipment`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 3 total, areas {"docs": 2, "infra": 1}. 3 repo-grep callsites, none in application code: docs (2) — docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md line 451 (name listed in a schema inventory) and docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232 (enumerated as one of the 29-view definer-view program); infra (1) — infra/database/source-lineage/apex-resa/pm-project-pss/schema/07_equipment_project_assignment.sql line 98, which is the CREATE OR REPLACE VIEW definition itself. No known consumers. This is repo-grep evidence only, NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - sole repo definition is in a source-lineage (apex-resa legacy import) file; whether the deployed prod definition matches this snippet is unverified
  - RLS posture of underlying tables projects and equipment is not in the facts file, so the magnitude of the definer-bypass exposure cannot be quantified
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any production reads of the view, and by which role)
  - signed external_clients overlay (PostgREST/Data-API or other external callers selecting the view)
  - signed static_repo overlay (authoritative callsite census superseding this grep evidence)
  - signed advisor_findings overlay (Supabase advisor security findings for definer views)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes anon SELECT reachable)
  - operator declaration on whether v_project_equipment is a live consumer surface or dormant apex-resa lineage residue
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor: the docs/superpowers spec callsite snippet in the facts file is truncated before v_project_equipment would appear; the rationale's claim that the view is 'enumerated as one of the 29-view definer-view program' is inferred from the grep hit on that line, not visible verbatim in the recorded text.
  - Minor: 'security_invoker not set' is grounded in the policy block's blanket statement about these views, not in an observed field of the facts file (the facts carry no reloptions/security_invoker attribute); the proposal should ideally attribute it to the policy anchor.
  - Minor: the 'join makes the view non-auto-updatable, so write grants are likely inert' claim is a PostgreSQL-semantics inference from the definition snippet, not an observed fact — correctly hedged with 'likely', and the proposal rightly recommends revoking the write grants regardless.

### `public.v_projects_active`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a definer view (owner postgres, security_invoker not set) over active-project business data (project names, client names, sites, schedule status) with the full seven-privilege grant set (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) held by both anon and authenticated — grants far broader than any plausible consumer need for a read-only reporting join. The census found zero database dependents and zero non-documentation callsites: all 9 repo hits are apex-resa lineage docs, the source-lineage schema file, and the 29-view program spec itself, so no evidence exists that definer semantics are required by any consumer. Per the disposition vocabulary, that is exactly the harden case: convert to security_invoker=true and revoke anon/authenticated grants while keeping the view in public as legacy lineage per the 2026-07-09 schema-placement policy. Promote is not indicated because the view mirrors legacy apex-resa lineage rather than a canonical model (the canonical PM lane lives elsewhere), and compat is not indicated because no migrating consumers are evidenced. This is provisional: any of the five unsigned overlay dimensions (runtime logs, external clients, operator declaration, advisor findings, Data-API exposure) could reveal a live consumer that changes the revoke scope, though security_invoker conversion would likely still stand.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 2 (docs/architecture/database-lineage/spec/VIEW_DEFINITIONS.md:110; infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql:80)
- **Privileges:** anon and authenticated each hold ALL seven relation privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on the view; RLS on the view is false (views cannot carry RLS). Because the view runs with definer semantics under owner postgres, any anon/authenticated SELECT bypasses caller RLS on the underlying projects/clients/sites/locations tables — if the view sits in a Data-API exposed schema (unresolved), unauthenticated callers can read active-project business data (client names, sites, schedules, completion state). The write privileges are largely inert in practice (a multi-table LEFT JOIN view is not auto-updatable) but constitute grant-hygiene violations that should be revoked regardless.
- **Depends on:** `projects`, `clients`, `sites`, `locations`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 9 total, areas {"docs": 6, "infra": 3}. 9 repo callsites (repo-grep evidence only, NOT the signed static_repo overlay): 6 in docs, 3 in infra. All are documentation/lineage artifacts — apex-resa pm-project-pss lineage README table row, VIEW_DEFINITIONS.md spec (definition + comment), SCHEMA_REFERENCE.md listing, the 2026-07-11 signed-overlay-evidence-design spec enumerating the 29-view definer program, and the source-lineage schema file infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql (definition + comment). No application-code, API, or client consumers appear anywhere in the repo grep.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - both repo definitions come from apex-resa lineage docs/source-lineage files, not applied migrations — live prod definition may have drifted and is unverified offline
  - RLS state and grant posture of the underlying tables (projects, clients, sites, locations) are not in this facts file, so the actual exposure delta from definer semantics cannot be quantified
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any PostgREST/API reads of v_projects_active)
  - signed external_clients overlay (dashboards, reporting tools, or integrations selecting the view)
  - signed operator_declaration overlay (operator statement on whether apex-resa pm-project-pss lineage consumers are live or retired)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes the view anon-reachable via PostgREST)
  - signed static_repo overlay to supersede the repo-grep callsite census
- **Adversarial verifier notes (agrees=true; informative):**
  - Rationale clause 'the canonical PM lane lives elsewhere' is not traceable to the facts file or the policy block (extra-file context). Non-blocking: the promote-rejection independently stands on the grounded evidence that both definitions originate from apex-resa source-lineage/docs artifacts (infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql and docs/architecture/database-lineage/*), which the 2026-07-09 policy classifies as legacy content permitted to remain in public. Recommend trimming the clause or re-anchoring it to the operator_declaration overlay when signed.
  - Minor wording imprecision in static_callsite_summary: VIEW_DEFINITIONS.md actually contributes 3 hits (section heading line 106, CREATE line 110, COMMENT line 134) and 04_views.sql contributes 3 hits (comment header line 79, CREATE line 80, COMMENT line 104); the summary describes each as 'definition + comment', omitting the heading/comment-header hit. Totals (9 = 6 docs + 3 infra) and the all-documentation/lineage characterization are correct, so this is a wording quibble only.

### `public.v_projects_full`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

v_projects_full is a postgres-owned definer view (security_invoker not set) whose anon and authenticated effective privileges are the full seven-privilege suite, exposing project financial/commercial fields (contract_value, po_number, project_lead, client/site/location identity) to any Data-API caller with RLS on the four base tables bypassed. The census shows zero database dependents and zero database-deps consumers, and all 15 repo callsites are documentation, lineage schema SQL, or disposition-tooling test fixtures — no application code reads it. The schema-placement-01 DESIGN and IRP-EVIDENCE callsites explicitly left the financial/ops views including v_projects_full OPEN and out of that packet's scope, so this 29-view program is the governing vehicle rather than defer. Definer semantics are not evidenced as required by any consumer, and grants are plainly broader than any known consumer needs, which is the textbook harden case: convert to security_invoker=true and/or revoke anon/authenticated grants (the write privileges are likely inert since a multi-table join view is not auto-updatable, but they are grant-hygiene violations regardless). Provisional pending the five signed overlays; a runtime or external-client consumer discovered later could soften the grant revocation but would not justify retaining definer semantics on financially sensitive data.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 2 (docs/architecture/database-lineage/spec/VIEW_DEFINITIONS.md:27; infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql:15)
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view (observed). Because the view is owned by postgres and lacks security_invoker, any anon or authenticated SELECT reads all active projects — including contract_value, po_number, and client/site/branch detail — with the owner's privileges, bypassing caller RLS on projects/clients/sites/locations. The write-class privileges are almost certainly non-functional (a 4-table LEFT JOIN view is not auto-updatable) but represent maximal over-grant; the SELECT grant to anon is the live exposure lever.
- **Depends on:** `projects`, `clients`, `sites`, `locations`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 15 total, areas {"docs": 10, "infra": 5}. 15 repo callsites (repo-grep evidence only, NOT the signed static_repo overlay): 10 in docs, 5 in infra. Docs hits are database-lineage references (apex-resa/pm-project-pss QUICK_START.md, README.md, spec/VIEW_DEFINITIONS.md), knowledge-domain SCHEMA_REFERENCE.md, schema-placement-01 DESIGN.md/IRP-EVIDENCE.md (which explicitly list v_projects_full among financial/ops views left OPEN and out of Packet 01 scope), and the 2026-07-11 signed-overlay-evidence-design spec naming it in the 29-view definer-view program. Infra hits are the lineage source schema infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql (CREATE/COMMENT) and infra/database/schema-placement/tests/test_disposition_schema.py, where it is merely a fixture example oid. No application, API, or serving-runtime consumers appear in the repo.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in facts file is repo-grep evidence only, not the signed static_repo overlay
  - defining SQL sourced from repo lineage docs (VIEW_DEFINITIONS.md, source-lineage 04_views.sql), not a live pg_get_viewdef dump — deployed prod definition could drift from these snippets
  - base relations are written schema-unqualified in the definition; presumed public but unverified offline
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any PostgREST/API reads of v_projects_full in prod)
  - signed external_clients overlay (dashboards, reporting tools, or integrations selecting the view)
  - signed operator_declaration overlay (operator statement on whether any consumer requires definer semantics or anon SELECT on this view)
  - signed advisor_findings overlay (Supabase advisor security findings for definer views)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes this view anon-reachable via PostgREST)
  - signed static_repo overlay to supersede the grep-based callsite census
- **Adversarial verifier notes (agrees=true; informative):**
  - Wording lean: rationale says the view is 'exposing ... to any Data-API caller' but in_data_api_exposed_schema is not_observed in the facts file; the proposal does list the Data-API exposure overlay as an unresolved blocker and required evidence, so this is hedged structurally, but the rationale sentence should be conditioned ('if the public schema is Data-API exposed')
  - Wording lean: 'with RLS on the four base tables bypassed' asserts a bypass of base-table RLS, but the facts file contains no observation of RLS state on projects/clients/sites/locations; the definer-bypass mechanism is grounded in the policy block, yet whether any policies exist to be bypassed is unverified offline
  - Minor: the 'security_invoker not set' claim traces to the policy block's blanket statement for these views, not to a per-view observed field in the facts file (which has no reloptions entry); consistent with the mandate but worth flagging as policy-sourced rather than facts-observed

### `public.v_pss_dashboard`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

v_pss_dashboard is a definer-semantics view (owner postgres, security_invoker not set) whose SELECT bypasses caller RLS on five underlying relations, and both anon and authenticated hold the full seven table-level privileges on it — the maximal-grant pattern with no evidence any consumer needs it. The census shows zero database dependents and zero database-dep consumers; all 10 repo callsites are docs (6) and infra source-lineage (4) — definition text, a commented-out test query, and the Ph8 spec listing it in the 29-view definer program — with no application code reading it. The view belongs to the legacy apex-resa pm-project-pss lineage, consistent with public-schema legacy/compat status under the 2026-07-09 schema-placement policy, so keeping it in public is acceptable but its posture is not: convert to security_invoker=true and revoke anon/authenticated grants (at minimum the six non-SELECT privileges, and SELECT absent a demonstrated consumer). One caution: the pm-project-pss README labels it "PSS portal dashboard", hinting at a possible portal client invisible to repo grep — so the harden lean is provisional pending the runtime_logs/external_clients overlays and operator declaration. It is not an mcp_* view, so Packet 01 governance does not apply.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 2 (docs/architecture/database-lineage/spec/VIEW_DEFINITIONS.md:557; infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql:441)
- **Privileges:** anon and authenticated each hold ALL seven table-level privileges (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER) on the view. Because the view runs with definer semantics, any anon/authenticated SELECT reads pss_studies, pss_engineers, projects, clients, and pss_rfis with the owner's (postgres) privileges, bypassing caller RLS on those tables — an active exposure lever if the public schema is Data-API exposed (unresolved). The write privileges are likely inert for direct DML (multi-join + subquery view is not auto-updatable) but represent maximal, unjustified grant surface.
- **Depends on:** `pss_studies`, `pss_engineers`, `projects`, `clients`, `pss_rfis`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 10 total, areas {"docs": 6, "infra": 4}. 10 repo callsites, all in docs (6) and infra (4); none in application code. Docs hits: pm-project-pss README ("PSS portal dashboard"), VIEW_DEFINITIONS.md (definition + comment), SCHEMA_REFERENCE.md listing, and the 2026-07-11 signed-overlay-evidence spec naming it in the 29-view definer program. Infra hits: source-lineage 04_views.sql (definition + comment) and a commented-out SELECT in 12_pss_test_data.sql. This is repo-grep evidence only — NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in facts file is repo-grep evidence only, not the signed static_repo overlay
  - README describes the view as 'PSS portal dashboard' — a possible external portal consumer that repo grep cannot see; cannot rule out live external clients offline
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any prod query traffic against v_pss_dashboard, especially anon/authenticated roles)
  - signed external_clients overlay (whether a PSS portal or other external client selects this view)
  - signed operator_declaration (operator statement on whether the PSS portal lane is live and depends on this view)
  - signed advisor_findings overlay (Supabase advisor security findings for this definer view)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes anon SELECT reachable via PostgREST)
  - signed static_repo overlay to supersede the repo-grep callsite data in the facts file
- **Adversarial verifier notes (agrees=true; informative):**
  - Non-blocking wording quibble: rationale's example list ('definition text, a commented-out test query, and the Ph8 spec listing') could be misread as placing the Ph8 spec callsite in the infra group; it is a docs callsite (docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232). The static_callsite_summary attributes it correctly, so no false claim.
  - Non-blocking omission: facts record rls_enabled=false for the view itself; proposal does not mention it. Immaterial — for a definer view the exposure lever is bypass of RLS on the five underlying tables, which the proposal covers.

### `public.v_scope_financials`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a definer-semantics view over scope-level financial performance data (quoted/recognized revenue, labor cost, gross margin, client names) with maximally broad grants: anon and authenticated each hold all seven privileges including SELECT, so if the public schema is Data-API exposed, unauthenticated callers can read company financials with RLS bypassed on the underlying tables. The census shows zero database dependents and zero database-dep consumers, and the 43 repo callsites are entirely docs, lineage specs, Lane-411 design packets, and disposition-tooling test fixtures — no application code reads it — so nothing in the facts evidences a consumer that requires definer semantics or these grants. The view descends from the legacy apex-resa/pm-project-pss lineage (public = legacy per the schema-placement policy), and Lane 411 designed a seam.v_scope_financials successor, but that packet is explicitly a no-live design packet, so compat-to-a-live-canonical does not yet apply. Provisional lean: keep the name in public but convert to security_invoker=true and revoke anon/authenticated (at minimum all write-class privileges; SELECT too absent an evidenced consumer). Schema-placement-01 DESIGN.md explicitly left this view OPEN/out-of-scope for Packet 01, so it belongs to the 29-view definer program, not the mcp_* carve-out. Final action must wait on the five signed overlays, since an unlogged external or runtime consumer could downgrade the revoke to invoker-conversion only.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 2 (docs/architecture/database-lineage/spec/VIEW_DEFINITIONS.md:321; infra/database/source-lineage/apex-resa/pm-project-pss/schema/04_views.sql:255)
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE (observed) — the full grant set, far broader than any read consumer needs. On a definer view this means both roles' SELECT reads scopes/projects/clients/scope_financial_summaries with the owner's (postgres) rights, bypassing caller RLS; the write-class grants are likely inert because the multi-join view is not auto-updatable, but they are unjustified exposure levers regardless. RLS on the view relation itself is false (views cannot carry RLS; posture depends entirely on grants + invoker semantics).
- **Depends on:** `scopes`, `projects`, `clients`, `scope_financial_summaries`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 43 total, areas {"PROJECT_STATUS.md": 2, "docs": 17, "infra": 20, "ops": 4}. 43 repo callsites (repo-grep evidence only, NOT the signed static_repo overlay): infra 20 (almost all schema-placement disposition-tooling test fixtures that use this view name as a sample object, plus the source-lineage 04_views.sql definition), docs 17 (lineage VIEW_DEFINITIONS.md, SCHEMA_REFERENCE.md, Lane-411 design packets referencing a seam.v_scope_financials successor, schema-placement-01 DESIGN/IRP noting this view remains OPEN/out-of-scope), ops 4 (Lane-411 handoff/closeout notes about the seam successor design), PROJECT_STATUS.md 2. No application-code consumers appear anywhere in the grep.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - Lane 411 designed a seam.v_scope_financials successor but only as a no-live design packet — whether that seam migration is the intended exit path (which would shift this view toward compat/promote) is a cross-lane governance question needing operator input
  - definition evidence is from repo lineage docs (VIEW_DEFINITIONS.md, 04_views.sql), not a live pg_get_viewdef capture — prod definition could have drifted
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any prod SELECT traffic against public.v_scope_financials)
  - signed external_clients overlay (PostgREST/API-key consumers reading the view)
  - signed operator_declaration overlay, specifically: (a) whether any dashboard/reporting consumer depends on definer semantics, and (b) whether Lane 411's seam.v_scope_financials is the intended canonical successor
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (is public in the exposed schemas set)
  - signed static_repo overlay to supersede the raw grep callsite evidence
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor: the rationale asserts membership in the 29-view definer program; the facts file's snippet of docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232 truncates before v_scope_financials would appear, so direct list membership is inferred (not mcp_*, left OPEN/out-of-scope by schema-placement-01 DESIGN.md line 118) rather than directly observed. Inference is sound but should be labeled as such.
  - Minor: definer semantics (security_invoker not set) is asserted from the policy block, not from a field in the facts file; the only in-facts corroboration is a test fixture (test_collect_disposition.py line 98) which is fixture data, not evidence. The proposal's existing 'definition could have drifted' blocker partially covers this, but an explicit note that invoker-setting evidence comes from the policy anchor would be cleaner.
  - Verified clean: dependencies re-derived from the definition snippet are exactly scopes, projects, clients, scope_financial_summaries (match); all seven anon/authenticated privileges observed; zero dependents and zero database-dep consumers; all 43 callsites are docs/test-fixture/handoff material with no application code; all five awaiting-signed-overlay blockers plus the static_repo grep caveat are present.

### `public.v_scope_summary`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

v_scope_summary is a postgres-owned definer view (security_invoker not set) with the full seven-privilege grant set (SELECT through TRUNCATE) held by both anon and authenticated — the classic blanket-default-privileges posture the schema-placement policy targets. The census shows zero database dependents and zero inbound/outbound FKs, and repo grep finds only two documentation callsites (a schema-reference listing and the 2026-07-11 signed-overlay evidence spec that enumerates it in the 29-view definer-view program) — no application code reads it. Nothing in the facts justifies definer semantics or grants this broad, so the provisional lean is harden: revoke anon/authenticated and convert to security_invoker=true. Two cautions temper this: no defining SQL exists in the repo, so the underlying relations (and whether invoker-rights would break a legitimate consumer) cannot be verified offline, and the five evidence dimensions (runtime logs, external clients, operator declaration, advisor findings, Data-API exposure) remain unsigned. If runtime/external evidence later shows a live consumer relying on definer semantics, the disposition should be revisited toward compat or retain; if the operator declares it dead, drop rather than harden may be the cheaper end state. This is a provisional proposal for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view — a blanket grant far exceeding any observed consumer need (zero DB dependents, zero code callsites). Because the view runs with definer semantics and is owned by postgres, SELECT by either role reads the underlying tables with the owner's rights, bypassing caller RLS entirely; the write privileges are an additional exposure lever if the view is auto-updatable. Whether this is reachable through the Data API (PostgREST) is unresolved pending the config-backed exposure overlay, but at the SQL-grant layer both public-facing roles currently have unrestricted access.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 2 total, areas {"docs": 2}. Repo grep (NOT the signed static_repo overlay) finds 2 callsites, both in docs: docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md:452 lists it alongside v_pss_dashboard and v_scope_financials, and docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md:232 enumerates it within the 29-view definer-view program. No application, API, or migration code references were found — the name appears only in documentation.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - no defining SQL found in repo (definition_count=0) — underlying relations unknown; cannot assess offline whether security_invoker conversion would break a legitimate consumer or which base-table RLS would then govern
  - static_repo callsite data in facts file is repo-grep evidence only, not the signed static_repo overlay
  - view is not represented in application code or migrations in-repo, so its provenance and intended consumer are unestablished — operator declaration needed to distinguish dormant-legacy from externally-consumed
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any production reads of v_scope_summary)
  - signed external_clients overlay (non-repo consumers, e.g. BI tools or external dashboards)
  - signed operator_declaration overlay (is this view intended to live, and for whom)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - config-backed Data-API exposure overlay (is public schema / this view reachable via PostgREST)
  - signed static_repo overlay to supersede the ad-hoc grep evidence
  - authoritative view definition from prod (pg_get_viewdef) to enumerate underlying relations and verify base-table RLS posture before security_invoker conversion
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor: the second callsite's quoted text in the facts file is truncated ('...public.v_appa') and does not literally show 'v_scope_summary'; the claim that the 2026-07-11 spec enumerates this view in the 29-view program rests on the reasonable inference that the grep matched the view name at that line. Not a refutation — the callsite record exists because the name matched — but the proposal states it slightly more firmly than the visible snippet supports.
  - Minor wording: the rationale references 'drop' as a possible cheaper end state, which is outside the five-item disposition vocabulary; it is framed only as a future operator option contingent on an operator_declaration overlay, not as the proposed disposition, so it does not affect correctness.
  - Verification summary: all load-bearing claims trace to the facts file (postgres owner; seven privileges for both anon and authenticated; zero dependents; 0/0 FKs; 2 docs-only callsites; definition_count=0; Data-API and advisor states not_observed); dependencies=[] is the only derivable answer given definitions=[]; all five awaiting-signed-overlay blockers plus the static_repo grep caveat are present; the view is not mcp_*-governed so the Packet-01 defer carve-out does not apply; no alternative disposition fits the facts better than harden.

### `public.v_tcc_calc_input`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned definer view (security_invoker not set) with the full seven table-level privileges granted to both anon and authenticated, yet the census shows zero database dependents, zero inbound/outbound FKs, and the only repo callsite is the disposition-lane spec document itself listing it among the 29-view program — no application code references it and no defining SQL was found in the repo. Definer semantics plus blanket anon write-capable grants on a view with no evidenced consumer is exactly the exposure posture the schema-placement policy targets: nothing in the facts justifies definer semantics or grants this broad. The provisional lean is harden: convert to security_invoker=true and revoke anon/authenticated grants (at minimum the write privileges, which no view consumer should ever need). Promote is not indicated because with no repo definition there is no canonical model to relocate, and compat is not indicated because there is no evidenced migrating consumer. The name suggests it feeds the TCC calc engine (relay/lvbreaker lane), so a runtime or Data-API consumer outside the repo is plausible — the signed runtime_logs, external_clients, and operator_declaration overlays must clear before any grant revocation is applied. This is a provisional proposal for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view (observed). On a definer view owned by postgres, SELECT lets those roles read the underlying relations with the owner's privileges, bypassing caller RLS entirely; if the view is auto-updatable, the write grants (INSERT/UPDATE/DELETE, plus TRUNCATE) could also pass through to base tables as postgres. With zero evidenced consumers, every one of these grants is broader than need — this is the definer-view exposure lever the policy flags, at its widest setting.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 1 total, areas {"docs": 1}. One repo callsite total, in docs only: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, where the view appears in the enumerated 29-view definer-view-program list — i.e., the census/spec artifact itself, not a consumer. No application, migration, or tooling callsites found. This is repo-grep evidence only, not the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - no defining SQL found in repo — the view's base relations and exposure surface are unknown; dependencies could not be parsed
  - view name suggests it feeds the TCC calc engine (relay/lvbreaker TCC lane); a runtime or external Data-API consumer outside this repo is plausible and possible cross-lane governance must be ruled out before grant revocation
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any live reads of v_tcc_calc_input, especially from the TCC calc engine)
  - signed external_clients overlay (Data-API/PostgREST or other out-of-repo clients selecting this view)
  - signed operator_declaration overlay — specifically whether the relay/lvbreaker TCC calc lane still depends on this view and whether it is intentionally orphaned
  - signed advisor_findings overlay (Supabase advisor security findings for this definer view)
  - signed Data-API exposure configuration overlay (whether public/this view is exposed via the Data API)
  - signed static_repo overlay to supersede the repo-grep callsite snapshot
  - authoritative view definition from the database (pg_get_viewdef) since no defining SQL exists in the repo — needed to enumerate base relations before changing definer semantics
- **Adversarial verifier notes (agrees=true; informative):**
  - Wording quibble: privilege_summary says the TRUNCATE grant 'could also pass through to base tables' if the view is auto-updatable; PostgreSQL does not support TRUNCATE on views at all, so that grant is inert (though still inappropriate to hold). Does not affect the disposition.
  - Evidence nuance: the facts file's callsite text snippet is truncated ('...public.v_appa') and does not visibly contain 'v_tcc_calc_input'; the claim that the view appears in the 29-view list at that line is a reasonable inference from the grep hit, but the proposal states it as directly observed.
  - Omission (non-material, strengthens harden): the TRIGGER privilege held by anon/authenticated would permit creating INSTEAD OF triggers on the view — an additional exposure lever not mentioned in the privilege_summary.

### `public.v_tcc_etu_catalog`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a definer-semantics view (security_invoker not set) owned by postgres, and the census shows both anon and authenticated holding the full seven-privilege set (SELECT plus DELETE/INSERT/UPDATE/TRUNCATE/TRIGGER/REFERENCES) — grants demonstrably broader than any plausible consumer of a catalog-style read view, which per policy is a clean harden trigger even before consumer evidence lands. No defining SQL exists in the repo (definition_count 0), no database dependents exist, and the only repo callsite is the disposition-ledger design doc that lists the 29-view program, so nothing in the facts establishes that definer semantics are required. The name suggests a TCC electronic-trip-unit catalog surface that could plausibly be read by a live page via the Data API, so the SELECT-path hardening step (security_invoker conversion and/or anon SELECT revoke) must be sequenced behind the runtime_logs, external_clients, and Data-API exposure overlays to avoid breaking an unobserved consumer; the write-privilege revocations (DELETE/INSERT/UPDATE/TRUNCATE/TRIGGER/REFERENCES) carry no such risk for a view and can be proposed unconditionally. This is a provisional lean for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on the view (RLS not enabled; not applicable to views for caller protection anyway). Because the view runs with definer semantics under owner postgres, any anon/authenticated SELECT bypasses caller RLS and reads the underlying base relations with owner authority — and since the defining SQL is not in the repo, the blast radius of that bypass is unquantified. The six non-SELECT privileges are almost certainly inert-but-dangerous surplus on a catalog view and exceed any consumer need.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 1 total, areas {"docs": 1}. 1 repo callsite total, area = docs only: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, where the view appears in the enumerated 29-view definer-view program list. No application, migration, or tooling code references the name. This is repo-grep evidence only — it is NOT the signed static_repo overlay (static_repo state: not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in facts is repo-grep evidence only, not the signed static_repo overlay
  - no defining SQL found in repo (definition_count 0) — dependencies unknown; definer-bypass blast radius unquantified until pg_get_viewdef is captured from prod
  - view name suggests a TCC/ETU catalog serving surface with possible live external readers not visible to repo grep; SELECT-path hardening sequencing depends on that evidence
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any observed reads of the view in prod)
  - signed external_clients overlay (Data-API/PostgREST or other out-of-repo consumers)
  - signed operator_declaration overlay — specifically whether any live application surface (e.g. a TCC/ETU catalog page) reads this view and whether definer semantics are intentionally relied upon
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (whether public is an exposed schema and this view is reachable via PostgREST)
  - signed static_repo overlay to supersede the ad-hoc grep evidence
  - prod view definition (pg_get_viewdef) to establish base-relation dependencies and quantify the definer RLS-bypass surface
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor overstatement: the rationale claims the six non-SELECT privilege revocations 'carry no such risk for a view and can be proposed unconditionally.' TRUNCATE and REFERENCES are genuinely inert on PostgreSQL views, but simple views can be auto-updatable, making DELETE/INSERT/UPDATE potentially live write paths — and with definition_count 0 the facts cannot rule that out. The write-path revocations should be sequenced behind the runtime_logs overlay and the pg_get_viewdef capture (both already listed as blockers), not proposed unconditionally. Does not change the harden disposition.
  - The claim that the view backs a live TCC/ETU catalog page is name-based inference, not a fact from the file; it is properly hedged ('suggests', 'could plausibly') and only used to argue for extra SELECT-path caution, so it is acceptable — noted for the record.

### `public.v_tcc_etu_coefficients`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

The census shows a postgres-owned definer view whose anon and authenticated roles both hold the full privilege set, far broader than any plausible consumer need for a read-only coefficients view; per the schema-placement policy this is exactly the exposure lever the 29-view program targets, and the sole repo callsite confirms it is enrolled in that definer-view program (it is not one of the two Packet-01 mcp_* views). No database dependents exist, no defining SQL was found in the repo, and the only repo-grep callsite is the disposition-ledger spec doc itself — no application code references it — so revoking anon/authenticated and/or converting to security_invoker=true carries minimal apparent breakage risk pending signed overlays. The name suggests TCC-lane data that might argue for promote into a named schema, but with definition_count=0 that cannot be assessed; harden is the defensible provisional lean, with promote-vs-compat re-evaluable once the live view definition and operator declaration arrive. This is a PROVISIONAL proposal for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on this view (owner: postgres; rls_enabled=false, security_invoker not set). Because it runs with definer semantics, any anon or authenticated SELECT bypasses caller RLS and reads the underlying relations with the owner's privileges — an unauthenticated read path if the schema is Data-API exposed (exposure state not yet observed). The write-shaped privileges are surplus grants regardless of whether the view is auto-updatable and should be revoked; nothing in the facts justifies definer semantics or grants this broad.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 1 total, areas {"docs": 1}. 1 repo callsite, in docs only: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, where the view appears in the enumerated 29-view definer-view program list. No application, migration, or client code references found by grep. This is repo-grep evidence only, NOT the signed static_repo overlay (static_repo state: not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration (in_data_api_exposed_schema not_observed)
  - no defining SQL found in repo (definition_count=0); dependency relations unknown and definer-necessity cannot be assessed from repo sources
  - static_repo callsite data is repo-grep evidence only, not the signed static_repo overlay
  - no application consumer identified anywhere (0 database dependents, docs-only callsite) — view may be orphaned; whether promote into a named TCC schema is the better end-state cannot be judged without the live view definition
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any live query traffic against the view)
  - signed external_clients overlay (dashboard/PostgREST/third-party consumers)
  - signed operator_declaration (whether the TCC LV breaker lane still consumes this view or it is orphaned; whether definer semantics are intentionally required)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - config-backed Data-API exposure overlay (authoritative pgrst schema exposure for public)
  - signed static_repo overlay (to supersede the grep-only callsite evidence)
  - live view definition (pg_get_viewdef) to establish underlying relations and to adjudicate harden vs promote
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor: the facts file's callsite text snippet is truncated and does not visibly contain 'v_tcc_etu_coefficients'; the claim that the view is 'enrolled' in the 29-view definer-view program rests on the census attributing that grep hit to this view's entry, which is a fair reading but is inference from census attribution rather than visible line text.
  - Minor wording: the rationale calls the sole callsite 'the disposition-ledger spec doc itself'; the facts record it as docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md (the signed-overlay evidence-design spec). Same lane, slightly loose characterization — not a factual error.
  - Nit: privilege_summary asserts write-shaped grants 'should be revoked' regardless of auto-updatability — a defensible policy judgment under harden, but auto-updatability itself is unknowable with definition_count=0; the proposal handles this acceptably by flagging the missing definition as a blocker.

### `public.v_tcc_tmt_catalog`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned definer view (security_invoker not set, rls_enabled false) whose grants are maximally broad: anon and authenticated both hold all seven table-level privileges, including DELETE, INSERT, TRUNCATE, and UPDATE — indefensible for what its name indicates is a read-only TMT (thermal-magnetic trip) catalog view in the TCC lane. No database objects depend on it, no defining SQL exists in the repo, and the only repo callsite is the disposition-program design doc itself, so nothing in the census justifies definer semantics or write grants. The provisional fix is to revoke all non-SELECT privileges from anon/authenticated immediately and convert to security_invoker=true (or revoke anon SELECT) once the Data-API and runtime overlays confirm whether an anon-facing page (e.g. a public TCC reference page) actually reads it. Promote-to-named-schema is a plausible follow-on (a catalog model arguably belongs beside the tcc.* catalog), but with definition_count=0 the view's underlying relations are unknown, so harden is the defensible lean and relocation is deferred to evidence. This remains provisional pending the five signed overlays and an operator declaration on intended consumers.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, and UPDATE on the view. Because it is a definer view owned by postgres, any caller reaching it (e.g. via the Data API with the anon key, if the public schema is exposed — exposure state not yet observed) reads the underlying relations with the owner's privileges, bypassing their RLS entirely; and if the view is simple enough to be auto-updatable, the write privileges could mutate the underlying catalog rows the same way. This is the worst-case grant posture for a definer view: full write-surface granted to the anonymous role on an RLS-bypassing object.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 1 total, areas {"docs": 1}. 1 repo callsite total, in docs only: docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, where the view is merely enumerated as one of the 29-view definer program. No application, migration, or SQL callsites found by grep. This is repo-grep evidence only — NOT the signed static_repo overlay — so out-of-repo consumers (e.g. Data-API clients such as a deployed TCC page) cannot be excluded from it.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - no defining SQL found in repo (definition_count=0) — underlying relations unknown, so the definer-bypass blast radius and auto-updatability cannot be enumerated
  - possible anon-facing runtime consumer (public TCC reference page) cannot be confirmed or ruled out from repo grep, which gates whether anon SELECT survives hardening
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (does anything SELECT this view in prod; which roles)
  - signed external_clients overlay (Data-API / PostgREST clients touching the view, e.g. anon-key page reads)
  - signed operator_declaration (is a public/anon-visible TCC TMT catalog read intended; may anon SELECT remain post-harden)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (is public schema / this view exposed via PostgREST)
  - signed static_repo overlay to supersede the grep-only callsite data
  - authoritative view definition (from prod catalog or repo) to enumerate underlying relations and assess auto-updatability before any security_invoker conversion
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor traceability note (not disagreement): the claim 'security_invoker not set' is grounded in the policy block's blanket statement about these 29 views, not in any field of the facts file (the JSON has no reloptions/security_invoker attribute). This is acceptable under the stated policy anchors but the rationale could cite the policy block rather than implying it was observed per-view.
  - Minor wording quibble: 'TMT (thermal-magnetic trip)' and 'read-only catalog view' are name-based inferences, which the rationale itself acknowledges ('what its name indicates'); with definition_count=0 nothing in the facts confirms the view's content. The proposal handles this correctly by gating anon-SELECT retention and any security_invoker conversion on the definition and overlays, so no material impact.
  - Verification detail: dependencies=[] is the only derivable answer — definitions[] is empty in the facts file, so no relations can be re-derived and none were invented or missed; the proposal correctly carries 'underlying relations unknown' as a view-specific blocker instead of guessing.
  - All five mandatory awaiting-signed-overlay blockers (runtime_logs, external_clients, operator_declaration, advisor_findings, Data-API exposure configuration) are present, the grep-only static_repo caveat is present, and two sound view-specific blockers are added. Privilege claims (anon+authenticated each holding DELETE/INSERT/REFERENCES/SELECT/TRIGGER/TRUNCATE/UPDATE), owner=postgres, rls_enabled=false, dependents=[], callsite_count=1 (docs only, the 2026-07-11 signed-overlay-evidence-design doc line 232), and definition_count=0 all match the facts file exactly. The view is not one of the two mcp_* Packet-01 views, so defer-to-Packet-01 does not apply. Harden is the correct provisional lean: grants are demonstrably broader than any evidenced consumer (zero DB dependents, zero non-doc callsites), and promote cannot be established from the facts because the underlying relations are unknown.

### `public.v_tcc_tmt_curve_data`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a postgres-owned definer view (security_invoker not set, rls_enabled=false) whose grants are the maximal seven-privilege set to both anon and authenticated — the classic blanket-grant posture, far broader than any read-only curve-data consumer could need. The census found zero database dependents, zero inbound/outbound FKs, and the only repo callsite is the disposition-ledger design doc that enumerates the 29-view program itself — i.e., no application code in the repo reads this view. No defining SQL exists in the repo (definition_count=0), so definer semantics cannot be shown to be required, and the underlying relations it exposes are unknown. Under the vocabulary, that is squarely harden: convert to security_invoker=true and revoke (at minimum) the write-class privileges from anon/authenticated, with the anon SELECT decision gated on the Data-API and runtime overlays. The name suggests it serves TCC thermal-magnetic-trip curve data, plausibly to a public-facing page via the Data-API rather than via repo-visible code, so anon SELECT revocation must not be executed until the runtime_logs, external_clients, and Data-API exposure overlays confirm or refute a live external consumer. Provisional pending those signed overlays and operator review.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 0
- **Privileges:** anon and authenticated each hold the full privilege set on the view: SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER (observed). On a definer view owned by postgres, anon SELECT executes with owner privileges and bypasses caller RLS on every underlying relation — a direct exposure lever to unauthenticated clients if the view is in a Data-API-exposed schema (exposure config not yet observed). The write-class grants (INSERT/UPDATE/DELETE/TRUNCATE) are an additional lever if the view is auto-updatable, which cannot be ruled out because no definition was found. Grants are unambiguously broader than any plausible consumer need.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 1 total, areas {"docs": 1}. 1 repo callsite, in docs only (callsite_areas: docs=1): docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md line 232, which is the disposition-ledger spec's own enumeration of the 29-view definer program — a self-referential governance mention, not a consumer. No application, migration, or test code references the view name. This is repo-grep evidence only; the signed static_repo overlay does not yet exist (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - no defining SQL found in repo (definition_count=0): dependencies, underlying-relation RLS posture, and auto-updatability are all unknown
  - consumer surface ambiguous: zero code callsites means any live consumer would be external/dynamic (e.g., Data-API client such as a TCC curve page), which repo grep cannot see
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any SELECT traffic from anon/authenticated against this view)
  - signed external_clients overlay (Data-API / PostgREST clients reading v_tcc_tmt_curve_data)
  - signed operator_declaration overlay (operator statement of intended consumers, specifically whether any live TCC page reads this view, and whether definer semantics are intentionally required)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (whether public is an exposed schema for this project, making anon grants reachable)
  - signed static_repo overlay (to supersede the raw repo-grep callsite data)
  - recovered view definition (e.g., pg_get_viewdef capture from prod) to establish base relations, their RLS posture, and whether the view is auto-updatable before deciding scope of grant revocation
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor: the facts-file callsite text snippet is truncated before this view's name is visible; the claim that the docs enumeration includes v_tcc_tmt_curve_data is a safe inference from the grep match, not literally shown in the snippet.
  - Minor: rls_enabled=false is inert for a plain view (RLS applies to tables); citing it as posture evidence is decorative — the load-bearing facts are postgres ownership, definer semantics, and the blanket seven-privilege grants, which the proposal also cites correctly.
  - Confirmed: all five awaiting-signed-overlay blockers present, static_repo repo-grep caveat present, dependencies correctly empty (definition_count=0), not an mcp_* Packet-01 view, and harden is the best-fit disposition; no alternative disposition is better supported by the facts.

### `public.vw_etu_browse`

**Proposed disposition (PROVISIONAL): `harden`** — confidence high

vw_etu_browse is a postgres-owned definer view published "side-by-side as a derived read-model" during TCC Phase 5 Tier B Slice 2, with adoption into the runtime contract explicitly HELD (runtime contract remains vw_trip_unit_cascade; G2-RULES-GUIDE gates D-2 and AG-2 block adoption pending a concrete consumer and trip-type identity harmonization). The census shows zero database dependents, zero database-dep consumers, and the repo's own historical consumer sweep recorded "vw_etu_browse: NONE FOUND" — all 43 callsites are governance/handoff prose, not application code. Meanwhile anon and authenticated each hold the full seven-privilege set on a definer view, an unjustified RLS-bypass exposure lever with no known consumer to serve. Harden is the robust lean regardless of overlay outcomes: at minimum revoke the write-class privileges and anon SELECT, and convert to security_invoker=true (nothing depends on definer semantics per the facts); if a hidden runtime/external consumer surfaces in the signed overlays, only the extent of grant narrowing changes, not the direction. This does not disturb the TCC-lane adoption gates — the view stays published; any future adoption packet (D-2) can re-grant deliberately. Not compat (no migrating consumers — it never had any) and not promote (it is a derived read-model, not the canonical surface).

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (ops/agents/handoffs/2026-04-27-tcc-phase-5-tier-b-vw-etu-browse-execution-handoff.md:24)
- **Privileges:** anon and authenticated both hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE (observed) — the full default-grant set. RLS is not enabled on the view (views cannot carry it) and security_invoker is not set, so any anon/authenticated SELECT executes with the postgres owner's rights against the underlying ETU tables, bypassing caller RLS entirely. With zero recorded consumers, every one of these grants is unjustified surface; the write-class privileges are pure posture noise on a read-model view.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 43 total, areas {"docs": 1, "ops": 38, "reference": 4}. 43 repo callsites (grep evidence only — NOT the signed static_repo overlay): 38 in ops/agents/handoffs (TCC Phase 5 Tier B execution/governance packets, 2026-04-26 through 2026-04-29), 4 in reference/tcc/G2-RULES-GUIDE.md (F-10 side-by-side publication, D-2 adoption gate, AG-2 trip-type harmonization gate), 1 in docs/superpowers/specs (the 2026-07-11 signed-overlay design listing it among the 29-view definer program). No application-code consumers anywhere; the 2026-04-27 consumer-need handoff records repo-wide grep result "vw_etu_browse: NONE FOUND" and notes the view omits trip_type_id, which the /cascade consumers require — a structural mismatch that further confirms non-adoption.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - definition snippet is a handoff narrative, not the view body SQL: FROM-clause relations cannot be parsed (repo SQL mirror referenced at source-domains/tcc_v5_backend/migrations/maint/vw_etu_browse.sql but not captured in the facts file); lineage parity with tcc_etu_sensors / vw_trip_unit_cascade implies derivation but is inference, not a parsed dependency list
  - cross-lane coordination: TCC G2-RULES-GUIDE gates D-2/AG-2 govern future ADOPTION of this view; hardening must record that any adoption reopen requires a deliberate grant/posture revisit under that gate, and the TCC lane should be notified of the posture change
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (confirm zero PostgREST/API reads of vw_etu_browse)
  - signed external_clients overlay (confirm no out-of-repo consumer)
  - signed operator_declaration overlay (operator confirms TCC adoption HOLD still stands and no undocumented consumer exists)
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes this view anon-reachable via PostgREST)
  - signed static_repo overlay (supersedes the grep-only callsite evidence in the facts file)
  - actual view definition SQL (prod catalog dump or the repo mirror source-domains/tcc_v5_backend/migrations/maint/vw_etu_browse.sql) to enumerate underlying relations and verify RLS posture on them before security_invoker=true conversion
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor wording: privilege_summary calls the seven privileges 'the full default-grant set' — the facts file shows the observed grants but says nothing about their provenance (default privileges vs explicit GRANT); harmless characterization, not a factual error affecting disposition.
  - Minor grounding note: 'bypassing caller RLS entirely' rests on the policy block's definer-semantics anchor (security_invoker not set) rather than an observed field in the facts file; this is permitted grounding, and the proposal correctly holds actual anon reachability open pending the Data-API exposure overlay.
  - Strength, not defect: dependencies=[] is correct — the sole 'definition' in the facts is a handoff narrative with no parseable FROM clause, and the proposal properly downgrades the tcc_etu_sensors/vw_trip_unit_cascade lineage-parity linkage to explicit inference in unresolved_blockers rather than asserting it as a dependency.

### `public.vw_etu_calc_context`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is a TCC Phase 5 Tier B derived ETU read-model that was authored, lineage-proven (17,831-row parity vs tcc_etu_sensors and vw_sensor_calc_context), and published side-by-side — but its runtime adoption was explicitly placed on HOLD, with vw_sensor_calc_context remaining the runtime contract surface and reopen governed by trigger D-1 in reference/tcc/G2-RULES-GUIDE.md. The census shows zero database dependents and the 2026-04-27 consumer-need handoff records a repo-wide grep result of "NONE FOUND" for consumers; all 35 repo callsites are handoff/governance/reference prose, not code. A definer view with full anon/authenticated privileges (including SELECT bypassing RLS on its bases) that no consumer reads is pure unexposed-need attack surface. Hardening (security_invoker=true and/or revoke anon+authenticated) is compatible with the TCC HOLD: the view stays published for the future D-1 adoption packet, which can grant exactly what its concrete consumer needs. Promote was considered (it is arguably a canonical read-model belonging in a named schema) but relocation is premature while adoption itself is HOLD and owned by the TCC lane; defer was rejected because the security-posture question is separable from the adoption question, though the operator should confirm cross-lane coordination. Provisional pending the five signed overlays and recovery of the actual defining SQL.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (ops/agents/handoffs/2026-04-27-tcc-phase-5-tier-b-vw-etu-calc-context-execution-handoff.md:24)
- **Privileges:** anon and authenticated each hold ALL seven relation privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on this postgres-owned definer view (security_invoker not set, rls_enabled=false). SELECT through definer semantics bypasses caller RLS on the underlying ETU context tables (~17,831 sensor-context rows per lineage proofs), so any anon Data-API caller could read the full base data if the schema is API-exposed (exposure config not yet observed). The write-side privileges are a gratuitous over-grant on a derived read-model. Since no consumer of any kind is evidenced, current grants are strictly broader than need — the strongest possible case for revoking anon/authenticated and converting to security_invoker.
- **Depends on:** (no defining SQL found in repo — dependencies unresolved offline)
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 35 total, areas {"docs": 1, "ops": 31, "reference": 3}. 35 repo callsites (repo-grep evidence only, NOT the signed static_repo overlay): 31 in ops (TCC Phase 5 Tier B execution/adoption/closeout handoffs, 2026-04-26 through 2026-04-29), 3 in reference (reference/tcc/G2-RULES-GUIDE.md — F-10 side-by-side publication fact and D-1 adoption reopen trigger), 1 in docs (the 2026-07-11 signed-overlay evidence design spec listing it among the 29-view definer program). Every callsite is governance/documentation prose; none is application code. Notably, the 2026-04-27 consumer-need handoff itself records a repo-wide consumer grep returning "NONE FOUND" and marks adoption HOLD, with vw_sensor_calc_context remaining the runtime contract surface.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - no defining SQL body found in repo: the single definition hit is handoff narrative around CREATE OR REPLACE VIEW with no FROM clause; base relations (likely public.vw_sensor_calc_context / public.tcc_etu_sensors per lineage-parity proofs) are inferred, not parsed — the repo SQL mirror source-domains/tcc_v5_backend/migrations/maint/vw_etu_calc_context.sql is referenced but its contents are not in the facts file
  - cross-lane governance: TCC Phase 5 Tier B closed this view PASS with adoption HOLD (DEC-006) and a documented reopen trigger (G2-RULES-GUIDE D-1); hardening should be sequenced so it does not silently foreclose or complicate the documented adoption reopen path
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (confirm zero production reads of vw_etu_calc_context)
  - signed external_clients overlay (confirm no out-of-repo consumers, e.g. tcc_v5_backend service deployments)
  - signed operator_declaration overlay (operator confirmation that TCC Tier B HOLD status stands and hardening may proceed independent of the D-1 adoption decision)
  - signed advisor_findings overlay (Supabase advisor security findings for this definer view)
  - signed Data-API exposure configuration overlay (whether public schema/this view is PostgREST-exposed)
  - signed static_repo overlay (to supersede the repo-grep callsite evidence)
  - actual view definition SQL (pg_get_viewdef or source-domains/tcc_v5_backend/migrations/maint/vw_etu_calc_context.sql) to establish the true base-relation read set before converting to security_invoker
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor: privilege_summary asserts SELECT 'bypasses caller RLS on the underlying ETU context tables' as if the base-relation read set were known, but the same proposal's blockers correctly state the bases are inferred, not parsed (no FROM clause in the sole definition snippet), and the facts contain no observation that the base tables have RLS enabled — the bypass claim is a policy-block-derived potential, not an observed fact; phrasing should be conditional.
  - Minor: rationale compresses 'closed PASS with adoption HOLD (DEC-006)' into one clause; the facts tie DEC-006 to the Tier B Slice 1 closed-PASS (2026-04-28 handoff line 33) while the HOLD is recorded separately in the 2026-04-27 adoption handoff (line 38). Traceable but slightly conflated attribution.
  - Minor: the 'repo-wide grep' characterization inherits the source handoff's own wording, but the underlying grep scope enumerated at the 2026-04-27 consumer-need handoff line 24 is a specific directory list (tcc_v5_backend, neta-ett-study-material/Development, frontend sources, apex-power-ops-platform), not literally the whole repo — worth carrying the scope qualifier into the signed static_repo overlay when it supersedes this evidence.
  - Verified clean: callsite counts (35 = 1 docs + 31 ops + 3 reference, all .md prose), zero dependents/consumers, full 7-priv anon+authenticated grants, postgres owner, rls_enabled=false, dependencies=[] with correct inferred-bases caveat, and all five awaiting-signed-overlay blockers plus the static_repo repo-grep caveat are present. Not an mcp_* Packet-01 view, so harden (not defer) is the correct vocabulary fit; the defer alternative is adequately neutralized by the cross-lane sequencing blocker and the operator_declaration evidence requirement.

### `public.vw_sensor_calc_context`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

This is an actively consumed runtime contract surface for the TCC lane — reference/tcc/G2-RULES-GUIDE.md declares it "authoritative pending all gates," and the control-plane-api NETA router issues live SELECTs against it (router.py:1597, 5307, 5369), so retirement or relocation is not on the table here. The grant posture, however, is indefensible: anon and authenticated each hold ALL seven privileges (DELETE/INSERT/REFERENCES/SELECT/TRIGGER/TRUNCATE/UPDATE) on a postgres-owned definer view over five tcc_* base tables, a pattern consistent with legacy default-PUBLIC grants rather than any deliberate consumer need — no evidence in the facts shows any anon/authenticated consumer. Proposed hardening is staged: (1) revoke anon/authenticated grants now (low risk — repo consumers are the API service and SQL functions, not Data-API roles); (2) hold the security_invoker=true conversion until the serving-role and base-table grant posture on tcc.* is proven, because fn_calculate_test_currents and fn_evaluate_test_results read this view from inside function bodies and invoker semantics could change what they resolve. Not promote, despite policy preferring named schemas: the TCC lane already relocated base tables to tcc.* and deliberately kept this public view as the stable contract while Tier B successors (vw_etu_calc_context) mature under that lane's gates — relocation is that lane's decision, only the exposure posture is this packet's remit. Provisional pending the five signed overlays.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 1 (apps/control-plane-api/migrations/maint/vw_sensor_calc_context.sql:13)
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE — the full seven-privilege set, consistent with default PUBLIC grants rather than deliberate design. On a definer view owned by postgres (security_invoker not set, RLS n/a on the view), any anon/authenticated SELECT — if public is Data-API exposed, which is unresolved — reads tcc_etu_sensors, tcc_trip_styles, tcc_trip_types, tcc_manufacturers, and tcc_etu_sensor_maint with owner privileges, bypassing caller RLS on those base tables. The write privileges are likely inert (multi-table join is not auto-updatable) but remain grant-hygiene violations to revoke.
- **Depends on:** `tcc_etu_sensors`, `tcc_trip_styles`, `tcc_trip_types`, `tcc_manufacturers`, `tcc_etu_sensor_maint`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 66 total, areas {"apps": 29, "docs": 1, "infra": 3, "ops": 29, "reference": 4}. 66 repo callsites: apps 29, ops 29, infra 3, reference 4, docs 1. Notable consumers: control-plane-api NETA router live queries (services/neta/router.py:1597, 5304-5369), SQL function bodies fn_calculate_test_currents and fn_evaluate_test_results (SELECT ... FROM vw_sensor_calc_context in migrations/maint and supabase/migrations), phase-3 validation script, plot-tcc and settings-route tests, and D012/TCC phase handoffs; reference/tcc/G2-RULES-GUIDE.md names it the authoritative runtime contract surface pending gates. This is repo-grep evidence only, NOT the signed static_repo overlay. Note the census found 0 database dependents while grep shows two SQL functions reading the view — pg_depend does not track plpgsql-body references, so database consumers are understated.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - census dependent_objects is empty but repo grep shows fn_calculate_test_currents and fn_evaluate_test_results SELECT from this view inside plpgsql bodies (pg_depend blind spot); posture changes must account for these unrecorded database consumers
  - cross-lane governance: TCC lane rules (reference/tcc/G2-RULES-GUIDE.md) hold this view as the authoritative runtime contract surface pending gates — security_invoker conversion or any relocation must be coordinated with that lane
  - serving-role dependency on definer semantics unproven: whether the control-plane-api role has direct grants on the tcc.* base tables is unobserved, gating the security_invoker=true step of the harden
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (any anon/authenticated Data-API reads of this view in prod)
  - signed external_clients overlay
  - signed operator_declaration: which role(s) the control-plane-api serving path uses and whether definer semantics are required for this view
  - signed advisor_findings overlay (Supabase advisor security findings for this view)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes this view PostgREST-reachable)
  - signed static_repo overlay to supersede the grep-based callsite census
  - grant/RLS posture of base relations tcc_etu_sensors, tcc_trip_styles, tcc_trip_types, tcc_manufacturers, tcc_etu_sensor_maint for the serving role, to clear the security_invoker conversion
  - TCC-lane sign-off that grant revocation does not disturb the runtime contract surface guarantees in G2-RULES-GUIDE.md
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor: the rationale claim that 'the TCC lane already relocated base tables to tcc.*' rests on a truncated callsite snippet (ops/agents/inbox/done/2026-05-30-cc-d012-phase2-expand.md: 'public.tcc_* ... survive as views over tcc.*'); it is supported but indirect — the final ledger entry should cite that callsite explicitly.
  - Minor: the facts' D012 phase0 characterization callsite (ops/agents/handoffs/2026-05-30-d012-phase0-live-characterization-closeout.md line 403) lists only four base dependencies, omitting tcc_trip_types; the proposal's five-relation dependency list is correct per the definition snippet, but a one-line reconciliation note would preempt a reviewer flagging the discrepancy.
  - Minor: defer (governed-by-TCC-lane) is a plausible rival reading given G2-RULES-GUIDE.md's 'authoritative pending all gates' language; the proposal adequately defeats it by bounding the harden to grant posture and gating the security_invoker step on TCC coordination, but the ledger should record explicitly why defer was rejected.
  - Minor wording: privilege_summary says 'RLS n/a on the view' while the facts record rls_enabled observed=false; harmless (RLS is not enforceable on plain views), but 'observed false' would be more precise.

### `public.vw_trip_unit_cascade`

**Proposed disposition (PROVISIONAL): `harden`** — confidence medium

The view is an actively served read-model over the canonical tcc.* schema: 105 repo callsites, with apps/control-plane-api/services/neta/router.py issuing direct SQL against it in at least a dozen statements backing /api/v1/neta/cascade, /etu/breaker-cascade, /etu/breaker-alt-trips and catalog/status, and reference/tcc/G3-ROUTING-GUIDE.md naming it the trip-unit cascade view backing /cascade; an ops handoff states it "remains the runtime contract surface". All observed consumers are server-side direct-Postgres callers, yet anon and authenticated each hold the full seven-privilege set on a postgres-owned definer view — grants far broader than any evidenced consumer needs, and an RLS-bypass lever if the public schema is Data-API exposed (unresolved). Placement is acceptable under the 2026-07-09 policy (a public serving shim over canonical tcc.* models), and it was deliberately repointed to canonical tcc.* in D012 Phase 4a (migration 002), so promote/compat are not warranted; the defect is posture, not location. Provisional prescription: revoke anon/authenticated grants (at minimum all write-shaped privileges; SELECT too unless a signed overlay reveals a PostgREST/browser consumer), and evaluate security_invoker=true after confirming the control-plane-api serving role holds direct SELECT on the four tcc.* base relations. Execution is gated on the five signed overlays.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 4 (infra/database/migrations/tcc/002_phase4a_repoint_db_objects.sql:479; infra/database/migrations/tcc/002_phase4a_repoint_db_objects_down.sql:450; ops/agents/handoffs/2026-05-30-d012-phase4a-repoint-db-objects-closeout.md:31)
- **Privileges:** anon and authenticated each hold DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on this postgres-owned definer view (security_invoker not set; rls_enabled=false, normal for a view). Because it is a definer view over tcc.manufacturers/trip_styles/etu_sensors/trip_types, SELECT alone would let any anon/authenticated Data-API caller read the full ~17,831-row cascade with base-table access controls bypassed — contingent on public-schema Data-API exposure, which is not_observed. The write-shaped privileges are likely inert (multi-join view is not auto-updatable) but are default-PUBLIC grant residue that no evidenced consumer uses and should be revoked regardless.
- **Depends on:** `tcc.manufacturers`, `tcc.trip_styles`, `tcc.etu_sensors`, `tcc.trip_types`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 105 total, areas {"apps": 23, "docs": 1, "infra": 21, "ops": 49, "reference": 11}. 105 callsites (repo-grep evidence only — NOT the signed static_repo overlay, which is not_observed): apps=23, dominated by apps/control-plane-api/services/neta/router.py (direct f-string SQL at ~14 lines incl. 2767, 2773, 4353, 4455-4709, 5276) plus schemas.py, main.py, tests, and operations-web lvbreakertcc wiring docs; infra=21, the authoritative CREATE OR REPLACE in infra/database/migrations/tcc/002_phase4a_repoint_db_objects.sql(:479) and its DOWN, plus corrections 018-025 that read the view in validation gates; ops=49, D012 phase 2-4b handoffs/inbox packets documenting the repoint and calling it the runtime contract surface; reference=11, TCC G2/G3 guides mapping it to GET /api/v1/neta/cascade and /etu/breaker-alt-trips; docs=1, the 29-definer-view program list. All observed consumers are server-side (API service, migrations, gates) — no browser/PostgREST callsite appears in the grep.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - security_invoker=true conversion requires confirming the control-plane-api serving role has direct SELECT grants on tcc.manufacturers, tcc.trip_styles, tcc.etu_sensors, tcc.trip_types (not in facts file)
  - facts file records definition_count=4 but lists only 3 definition snippets; the DOWN-migration snippet is the historical pre-repoint body (references tcc_manufacturers_pre_rebuild) and was excluded from dependencies
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (confirm which roles actually query the view in prod)
  - signed external_clients overlay (rule out any PostgREST/browser consumer needing anon or authenticated SELECT)
  - signed operator_declaration (ratify revoke scope and confirm control-plane-api serving-role identity for this surface)
  - signed advisor_findings overlay (Supabase advisor security findings for definer views in public)
  - signed Data-API exposure configuration overlay (whether public schema exposure makes the anon SELECT grant reachable)
  - signed static_repo overlay superseding the repo-grep callsite census
  - grant check: serving role's direct privileges on the four tcc.* base relations, prerequisite for any security_invoker conversion
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor wording: static_callsite_summary says 'direct f-string SQL at ~14 lines' — only router.py:2767 is demonstrably an f-string in the facts; lines 2729 and 5231 are comments/docstrings, so the SQL-bearing count is closer to 12. Does not affect the disposition.
  - Minor wording: rationale attributes /etu/breaker-cascade backing to router.py SQL; the facts support this via the phase4b inbox packet (line 52: 'the 4a-fixed vw_trip_unit_cascade path') and the Phase 4a gate table rather than a router.py snippet naming that route directly. Claim stands, provenance is ops/inbox docs.
  - Verified clean: dependencies re-derived from the migration 002:479 UP body are exactly tcc.manufacturers, tcc.trip_styles, tcc.etu_sensors, tcc.trip_types; all five awaiting-signed-overlay blockers present; callsite_count 105 matches the listed array and area sums; definition_count=4 vs 3 snippets discrepancy is real and correctly disclosed.

## Per-view records — `mcp_*` (separately identified; governed by Packet 01)

### `public.mcp_job_run_summary_v`

**Proposed disposition (PROVISIONAL): `defer`** — confidence high

This view is one of the two mcp_* summary views explicitly governed by schema-placement Packet 01, and the facts file corroborates that governance from multiple directions: the defining migration (20260328_000007_add_control_plane_tables.sql:175), the Packet-01 hardening migrations 20260710_000012/000013 plus rollbacks that enumerate it, the MCP_ACCEPTED_DEFINER_VIEWS allowlist in apps/control-plane-api/scripts/schema_drift_acl.py with tests asserting anon/authenticated retain SELECT, and the 2026-07-11 signed-overlay spec listing it as a Packet-01b/6b exception kept separate from the 29-view v_*/vw_* program. Its security_invoker conversion was explicitly DEFERRED by Packet 01, so the 29-view program must not re-disposition it here. It has a live repo consumer (control-plane router.py:1254 reads FROM public.mcp_job_run_summary_v), so it is not a dead shim. Disposition is therefore defer (governed-by-Packet-01), with one reconciliation item surfaced: the census snapshot observed anon/authenticated holding ALL privileges, which is inconsistent with the Packet-01 hardened target state (SELECT-only retained) that the repo drift tests expect — Packet 01 needs to confirm whether the census predates the A1/A2 apply or the hardening has not yet landed on prod. This is a provisional proposal for operator review, not an accepted decision.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 3 (apps/control-plane-api/supabase/migrations/20260328_000007_add_control_plane_tables.sql:175; docs/operations/schema-placement-01/evidence/tests/fixture.sql:99; docs/operations/schema-placement-01/evidence/tests/fixture_7th.sql:99)
- **Privileges:** Census observed anon AND authenticated each holding all seven privileges (DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE) on the view; RLS not enabled (views cannot carry RLS), owner postgres, definer semantics. On a definer view, SELECT alone lets anon/authenticated read through caller RLS on the underlying public.mcp_local_action_queue and public.mcp_job_runs tables (Packet-01 DESIGN.md notes the view joins requested_by-scoped rows, so any authenticated reader sees all requesters' rows). The write verbs are grant-surface noise beyond any plausible consumer need. The repo contains Packet-01 migrations (20260710_000012 harden_mcp_public_exposure_core, 000013 retire_mcp_authenticated_contract) whose drift tests expect only SELECT retained for anon/authenticated on this view — the observed full-ALL grants suggest the census snapshot predates or contradicts that apply; reconciliation belongs to Packet 01.
- **Depends on:** `public.mcp_local_action_queue`, `public.mcp_job_runs`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 34 total, areas {"apps": 18, "docs": 16}. 34 repo callsites (grep evidence only — NOT the signed static_repo overlay): 18 in apps, all under apps/control-plane-api — a live read consumer (services/control_plane/router.py:1254 "FROM public.mcp_job_run_summary_v"), the drift-ACL allowlist MCP_ACCEPTED_DEFINER_VIEWS (scripts/schema_drift_acl.py:45) with tests asserting anon/authenticated retain SELECT (tests/test_schema_drift_acl.py), the defining migration 20260328_000007, and Packet-01 hardening migrations 20260710_000012/000013 plus rollbacks. 16 in docs — schema-placement-01 DESIGN.md and evidence (codex audit, IRP synthesis, fingerprint/fixture/up-down-up test SQL), and the 2026-07-11 signed-overlay-evidence spec naming it a Packet-01b/6b exception distinct from the 29-view program.
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - census-vs-Packet-01 apply-state discrepancy: observed anon/authenticated ALL privileges conflicts with the Packet-01 hardened target (SELECT-only retained) that repo drift tests expect; confirm census snapshot timing vs migrations 20260710_000012/000013 prod apply status
  - cross-lane governance: disposition (including any security_invoker conversion, explicitly deferred there) is owned by schema-placement Packet 01, not this 29-view reconciliation
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay (does anon/authenticated traffic actually hit this view, or only the control-plane-api service path)
  - signed external_clients overlay (any PostgREST/Data-API or external reader of the view)
  - signed operator_declaration overlay (operator ratification that the Packet-01b/6b exception — definer semantics + retained SELECT — remains intended)
  - signed advisor_findings overlay (Supabase advisor security findings for definer views in public)
  - config-backed Data-API exposure overlay (whether public is in the exposed schema set, making the ALL grants reachable via PostgREST)
  - signed static_repo overlay to supersede the grep-based callsite census
  - Packet-01 apply-state confirmation for migrations 20260710_000012/000013 on prod to resolve the observed full-ALL grant discrepancy
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor (non-blocking): rationale/privilege_summary says repo drift tests expect 'only SELECT retained'; the test text at apps/control-plane-api/tests/test_schema_drift_acl.py:51 is an allowlist predicate (verb == "SELECT") plus 'retains SELECT' messages — 'only' is an inference from the predicate shape, though a fair one.
  - Minor (non-blocking): the census-vs-Packet-01 discrepancy framing could cite fixture.sql/fixture_7th.sql ('Grants matching prod.' with GRANT ALL to anon, authenticated, service_role) as direct facts-file corroboration that full-ALL was the modeled pre-hardening prod state, which supports the 'census predates the apply' branch of the reconciliation item rather than a true contradiction.
  - Verified: dependencies re-derived from migration 20260328_000007:175 definition are exactly public.mcp_local_action_queue and public.mcp_job_runs (LEFT JOIN LATERAL) — proposal matches; dependents observed empty — matches; callsite counts 34/18 apps/16 docs match the facts file exactly; all five awaiting-signed-overlay blockers plus the static_repo grep caveat are present.

### `public.mcp_task_packet_summary_v`

**Proposed disposition (PROVISIONAL): `defer`** — confidence high

This view is one of the two mcp_* summary views explicitly governed by schema-placement Packet 01, which already owns its anon-access hardening and explicitly DEFERRED its security_invoker conversion; the repo evidence confirms this governance (schema_drift_acl.py lists it in MCP_ACCEPTED_DEFINER_VIEWS, and the 2026-07-11 signed-overlay evidence design names it a "Packet-01b/6b exception... explicitly retained", separate from the 29-view program). It is an active runtime dependency: control-plane-api router.py:690 reads FROM it in production code, and hardening migrations 20260710_000012/000013 plus rollback scripts target it by name, so any disposition taken here would collide with in-flight Packet-01 actions. Nothing in the facts contradicts the Packet-01 governance assignment, so per the reconciliation policy the disposition is defer (governed-by-Packet-01), kept separately identified from the 29-view program. One material discrepancy must be routed to that packet rather than resolved here: the census observes anon and authenticated still holding ALL seven privileges on this postgres-owned definer view over public.mcp_task_packets, which appears to predate or contradict the applied-hardening claim -- and because a simple single-table view is auto-updatable, those write grants are a potential pass-through write path, not just a read exposure. Defer is therefore provisional governance routing, not a statement that the current posture is acceptable.

- **Identity:** owner `postgres`, definer-semantics view, repo definitions found: 3 (apps/control-plane-api/supabase/migrations/20260328_000007_add_control_plane_tables.sql:163; docs/operations/schema-placement-01/evidence/tests/fixture.sql:100; docs/operations/schema-placement-01/evidence/tests/fixture_7th.sql:100)
- **Privileges:** Census-observed: anon and authenticated each hold ALL seven privileges (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER) on this postgres-owned definer view (security_invoker not set, RLS false/not applicable). Under definer semantics, anon SELECT reads public.mcp_task_packets bypassing that table's RLS; and since the view is a simple single-table projection (auto-updatable in Postgres), the INSERT/UPDATE/DELETE grants could pass writes through to the base table under owner rights. This observed state conflicts with the Packet-01 hardening migrations present in the repo (20260710_000012 harden_mcp_public_exposure_core, 20260710_000013 retire_mcp_authenticated_contract), suggesting the census snapshot predates their apply (consistent with the per-action apply HOLD); reconciling census vs apply state belongs to Packet 01.
- **Depends on:** `public.mcp_task_packets`
- **Dependents (census):** (none observed in census)
- **Static repo callsites (grep evidence, NOT the signed static_repo overlay):** 31 total, areas {"apps": 16, "docs": 15}. 31 repo-grep callsites: 16 in apps (all control-plane-api: schema_drift_acl.py declares it in MCP_ACCEPTED_DEFINER_VIEWS; services/control_plane/router.py:690 reads FROM public.mcp_task_packet_summary_v at runtime; migrations 20260328_000007 create it and 20260710_000012/000013 plus rollbacks harden/retire its grants; tests assert its presence and missing-relation handling) and 15 in docs (schema-placement-01 DESIGN.md and evidence -- codex audit, IRP synthesis, fingerprint/fixture/up-down-up test SQL -- plus the 2026-07-11 signed-overlay evidence design spec naming it a Packet-01b/6b exception, explicitly retained, distinct from the 29 v_*/vw_* views). This is repo-grep evidence only, NOT the signed static_repo overlay (consumer_evidence_states.static_repo = not_observed).
- **Unresolved blockers:**
  - awaiting signed overlay: runtime_logs
  - awaiting signed overlay: external_clients
  - awaiting signed overlay: operator_declaration
  - awaiting signed overlay: advisor_findings
  - awaiting signed overlay: Data-API exposure configuration
  - static_repo callsite data in the facts file is repo-grep evidence only, not the signed static_repo overlay
  - census-observed anon/authenticated ALL-privilege grants conflict with the Packet-01 hardening migrations present in the repo (20260710_000012/000013); apply state vs census snapshot must be reconciled within Packet 01 (per-action apply HOLD)
  - cross-lane governance: security_invoker conversion explicitly deferred by Packet 01 -- this reconciliation must not preempt that packet's actions
- **Required evidence before any accepted decision:**
  - signed runtime_logs overlay
  - signed external_clients overlay
  - signed operator_declaration overlay (including Packet-01 apply-state declaration for migrations 20260710_000012/000013)
  - signed advisor_findings overlay
  - signed Data-API exposure configuration overlay (config-backed, not pgrst.db_schemas GUC)
  - signed static_repo overlay
  - post-apply census recapture of anon/authenticated effective privileges on the two mcp_* summary views once Packet-01 A-actions land
- **Adversarial verifier notes (agrees=true; informative):**
  - Minor traceability defect (not disposition-affecting): the privilege_summary parenthetical '(consistent with the per-action apply HOLD)' and the required_evidence phrase 'once Packet-01 A-actions land' import lane knowledge found in neither the facts file nor the policy block; the underlying discrepancy claim (census-observed ALL-privilege anon/authenticated grants vs. repo hardening migrations 20260710_000012/000013 vs. the policy's 'anon access hardening already applied' statement) is itself fully grounded. Recommend trimming or attributing those two fragments.
  - Verified clean: disposition defer matches the policy anchor's explicit routing for the two mcp_* summary views; dependencies re-derived from the 20260328_000007 definition as exactly [public.mcp_task_packets] (no missed/invented relations; update_updated_at in the snippet is a trigger on preceding tables, not a view dependency); dependents [] matches dependent_objects/database_deps_found_consumers; callsite arithmetic 31 = 16 apps + 15 docs recounted and correct; all five awaiting-signed-overlay blockers plus the static_repo repo-grep caveat present; auto-updatable pass-through-write concern is a sound derivation from the simple single-table projection.

---
*End of Phase 8 artifact. Next: Phase 8R operator ratification of cohort + evidence requirements; Phase 9 signed-overlay collections (each its own GO) bind census sha256 `52962abea7c8b81f62e6331c169f9b6963bf546763a76898cf707d076cf94130`.*