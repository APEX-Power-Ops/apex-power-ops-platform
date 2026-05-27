# APEX PM Lane Operating Cockpit

Date: 2026-05-06 (originally authored)
v2 refresh: 2026-05-26 PM cycle 3 (matrix #68 substrate-currency + structural refactor)
Status: Active PM and operator companion surface
Scope: compact current lane register, frontier routing, validation defaults, and reopen triggers for rapid project execution

## Purpose

This document is the compact current-state companion to the broader authority surfaces.

It exists to reduce session-start reconstruction work.

Use it to answer these questions quickly:

1. which lane is actually active now,
2. which lanes are closed or trigger-gated,
3. what the next truthful move is in each lane,
4. which validation surface should run before a lane is reopened,
5. which boundaries must not be widened by default.

## Authority And Use

This document is an execution cockpit, not the top governance source.

If this document conflicts with a governing surface, resolve conflicts in this order:

1. `docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`
2. `docs/architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md`
3. `docs/authority/APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md`
4. `docs/authority/WORKSPACE-REGISTRY-2026-05-23.md`
5. `docs/authority/REPO-PASSPORT-STANDARD-2026-05-23.md`
6. `PROJECT_STATUS.md`
7. lane-specific roadmap, implementation plan, or packet frontier
8. this cockpit

**Authority chain currency note (v2 refresh):** the OLARES-ONE plan (2026-05-06) carries inline substrate-currency updates per matrix #31 + matrix #65 (see Tier 1 freshness pass closeout 2026-05-26 PM cycle 3). The protocol (2026-05-15) carries inline PATTERN-005 cross-reference. The registry + passport-standard (2026-05-23) are the front-door companions referenced by the OLARES-ONE plan §Front-door workspace companions.

## Start-Here Order

For normal PM and technical-authority operation, use this order:

1. `PROJECT_STATUS.md`
2. `docs/architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md`
3. this cockpit
4. the lane-specific roadmap or packet frontier
5. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md` when host or operator proof is involved

**Lane-engagement orientation (v2 refresh):** when newly engaging an under-attention authority chain or lane cluster, author or consult a lane-engagement orientation report (PATTERN-005 worked example: `C:/APEX Platform/.claude/PLATFORM/OLARES-WORKSPACE-ORIENTATION-2026-05-26.md`) before authoring dispatches against drift-prone substrate (PATTERN-007 discovery-first orientation).

## Current Lane Register

**Structural refactor (v2):** the 7-lane register is now expressed as per-lane subsections rather than a single wide table. Cell density made paragraph-length Current Truth content fight readability in the original table format. Each subsection preserves the same five fields: State / Current Truth / Next Truthful Move / Reopen Trigger Or Guardrail / Primary Validation Surface.

**Lane count update (v2):** 7 → 8 lanes. New 8th lane (PM Schema substrate evolution — Era 2.4 packet wave) captures matrix #65 v2 synthesis impact + Packets A+B authoring + RLS-policy authoring substrate that did not have a coherent lane home pre-2026-05-26.

---

### Lane 1: Olares developer residency and operator hardening

**State:** Hold with bounded reopen triggers

**Current Truth:** The build-guide stack, adjacent authority framework, workstation rerun checklist, AI first-slice runbook, minimal-trio runtime decision, and the full surviving parent-root task-label family in the active repo task surface are now normalized in line with Olares-first execution, GitHub-canonical publication, client-only laptop posture, premium-plan-first AI use, optional local models, and the admitted minimal MCP trio.

**Next Truthful Move:** Return to hold unless a different adjacent authority, operator, visual, or current-looking provenance-routing mismatch appears.

**Reopen Trigger Or Guardrail:** Do not reintroduce laptop-first durable state, mandatory Ollama assumptions, broader AI-service scope, wrapper-level Codex admission, silent publication-boundary exceptions, or current-looking parent-root helper labels inside active repo-root surfaces.

**Primary Validation Surface:** `Olares host bootstrap status` or `bash apex-power-ops-platform/tools/ai/run-olares-host-bootstrap-status.sh`

---

### Lane 2: Olares AI/operator boundary

**State:** Active bounded baseline

**Current Truth:** The admitted minimal boundary remains `apex-fs`, `apex-db`, and `apex-jobs`; Claude Code is the packetized wrapper surface, Codex remains an approved interactive surface outside that wrapper, and the trio is operator-on-demand by default rather than always-on host baseline. GHCR PAT rotation closed 2026-05-25 per matrix #2 (operator-managed long-lived `read:packages` PAT in `image-service-ghcr-auth` secret; replaces ephemeral PAT pattern; cross-reference `reference_credential_handling_pat_out_of_band_discipline.md`).

**Next Truthful Move:** Rerun only when operator drift appears, a concrete insufficiency is recorded, or a later packet explicitly selects durable-runtime admission.

**Reopen Trigger Or Guardrail:** Do not open `ai_tasks`, broader executor admission, speculative orchestration rollout, wrapper-level Codex integration, or always-on trio runtime without a separate packet.

**Primary Validation Surface:** `tools/ai/run-minimal-mcp-trio.ps1` or `tools/ai/run-minimal-mcp-trio.sh`

---

### Lane 3: Operations Visibility runtime consumers

**State:** Hold on remaining empty seams

**Current Truth:** The populated `09`-tranche consumers are landed through Packet 053; `v_resource_allocation` and `v_equipment_needs` remain empty and therefore held.

**Next Truthful Move:** Wait for live rows or a separately justified consumer need before opening another browser/API slice.

**Reopen Trigger Or Guardrail:** Do not fabricate UI or API work around zero-row seams.

**Primary Validation Surface:** `tools/ai/run-olares-hold-boundary-check.ps1` with an authoritative live DSN such as `SEAM_DATABASE_URL`

---

### Lane 4: Control-plane read seam delivery

**State:** Active business-delivery lane

**Current Truth:** Governed browser consumers should continue to route through `apps/control-plane-api`, not direct browser-side Supabase admission.

**Next Truthful Move:** Select the next business-facing seam from platform priority, not from Olares convenience work.

**Reopen Trigger Or Guardrail:** Keep focused API slices bounded and test-backed.

**Primary Validation Surface:** Focused `pytest` for the touched route plus local or promoted-host smoke when applicable

---

### Lane 5: Governed PM route promotion

**State:** Active proof-backed runtime lane

**Current Truth:** The promoted PM approval flow now carries approval-context detail fidelity across tracer, schedule, drivers, and variance siblings. PM Lanes 277-284 admitted writes are authorized per `docs/authority/APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md` §7C (Temp Power import + assignment + readiness + durable field record + production tracking + customer completion + financial handoff baseline). PM Lane 411 Rev A-C revrec architecture (`seam.apparatus_financials` + `seam.project_contract_snapshots` + `seam.scope_labor_details` + `seam.apparatus_revenue_events`) establishes "recognition firewall: operational actuals are NOT in the recognition data path" principle per `PROJECT_STATUS.md` + matrix #65 v2 plan §8. The focused approval-context Playwright smoke passes, and the full `smoke:pm-live-data` reran green locally against `apps/mutation-seam` on `127.0.0.1:8000` plus `apps/operations-web` on `localhost:3000`.

**Next Truthful Move:** Keep promoting adjacent PM slices through the governed route shell only when they can be proven with focused browser smoke plus live-data ingress proof. Cross-cut substrate work (RLS-policy authoring; Era 2.4 Packets C-G; column-level Field Tech read restriction) routes through Lane 8 (PM Schema substrate evolution).

**Reopen Trigger Or Guardrail:** Do not reopen direct browser-side data admission, drop approval-origin return context, or treat shell-level loading noise as route failure before hydrated settlement is confirmed.

**Primary Validation Surface:** `apps/operations-web/tests/browser-shell.approval-context.smoke.spec.ts`, then `corepack pnpm --dir "c:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web smoke:pm-live-data -- --operations-web-base-url http://127.0.0.1:3000 --mutation-seam-base-url http://127.0.0.1:8000`

---

### Lane 6: Relay and specialized TCC engineering

**State:** Conditional, packet-gated

**Current Truth:** The relay read-only ladder is closed; no write lane is open by default. ETU deeper-fidelity follow-on remains optional and not currently required. Matrix #28 tcc_v5_backend Phase 3 1A→1D arc closed 2026-05-26 (SOURCE-DOMAIN/PROVENANCE posture; calc-engine promotion via matrix #30 complete; tcc remains source-domain provenance home). **Matrix #28 4th tier (added 2026-05-26 PM cycle 3 via matrix #65 v2 discovery):** Supabase `public.*` contains a TCC Reference domain (62 `tcc_*` + 20 `*_pre_rebuild` base tables = 82 total) functioning as a 4th tier alongside the three-tier TCC posture (NETA source-domain authority + `tcc_v5_backend` implementation provenance + `apex-power-ops-platform/packages/calc-engine` canonical promoted). No semantic resolution attempted by matrix #65; future TCC public-reference custody/migration treatment may be authored as a separate matrix item.

**Next Truthful Move:** Reopen only from concrete operator evidence, measured need, or an explicit planning packet. tcc_v5_backend repo passport authoring (matrix #67) is the highest-cross-cut-density next safe move per workspace registry §Next Safe Move.

**Reopen Trigger Or Guardrail:** Do not widen into write workflows or new runtime adoption from historical planning residue alone. Do not modify the 82-table TCC Reference domain in `public.*` without a dedicated matrix item.

**Primary Validation Surface:** Lane-specific focused tests and packet-defined validation

---

### Lane 7: Publication and host parity

**State:** Always-required closeout gate

**Current Truth:** Olares authority claims are not complete until the standalone canonical repo is updated and `/home/olares/code/apex/apex-power-ops-platform` is restored to parity.

**Next Truthful Move:** End every bounded Olares slice with repo-root publication and host resync.

**Reopen Trigger Or Guardrail:** Do not leave authoritative Olares docs or packet state workstation-local only. Outer-repo `C:/APEX Platform/` umbrella container is local-only divergence (matrix #32) and remains UNPUSHED indefinitely — never push outer repo to its `RESA-Power-Project-Management.git` origin.

**Primary Validation Surface:** `git -C "c:/APEX Platform/apex-power-ops-platform" push origin clean-main` plus host repo-root parity proof

---

### Lane 8: PM Schema substrate evolution (Era 2.4 packet wave) — NEW v2

**State:** Active substrate-authoring lane (post-matrix-#65 v2 synthesis)

**Current Truth:** PM Schema Foundation Plan v2 LANDED 2026-05-26 PM cycle 3 (Codex Cloud executor; matrix #65 closure). v2 hybrid synthesis (public.* spine concepts + seam.* PM mutation/audit/revenue patterns + net-new `pm_core` for NEW tables only per matrix #33 Q1 Option (c)). Lane 411 "recognition firewall" principle load-bearing per v2 §8 (operational actuals NOT in recognition data path; frozen quote data is recognition source; `recognized_amount` is event-truth; "actual revenue" is invalid recognition vocabulary). Era 2.4 SQL packet sequence revised A-G per v2 §15 (RLS first). **Packets A + B EXECUTED + REVIEWED 2026-05-26 PM cycle 3:** Packet A = RLS policy design for 66 public + 11 seam RLS-OFF tables (`.claude/PLATFORM/ERA_2_4_PACKET_A_RLS_POLICY_DESIGN_2026-05-26.md` + 9 SQL design files); Packet B = `pm_core` namespace + intake envelope (`intake_runs` + `intake_source_files` + `intake_validation_findings` + 4 enums; `.claude/PLATFORM/ERA_2_4_PACKET_B_PM_CORE_INTAKE_ENVELOPE_DESIGN_2026-05-26.md` + 7 SQL design files). **Revision addendum AUTHORED for Packet A** (`.claude/PLATFORM/ERA_2_4_PACKET_A_REVISION_ADDENDUM_2026-05-26.md`) capturing 6-role taxonomy correction (`apex_pm` / `apex_operations` / `apex_field_lead` / `apex_field_tech` / `apex_admin` / `apex_estimator` + `service_role` + `anon`; `apex_finance` REMOVED, revenue folds to PM per matrix #79) + Field Tech column-level read restriction (NEW design beyond Packet A scope; can read all operational data EXCEPT hours/revenue/$ columns; column GRANTs + VIEW hybrid lean). Identity/auth substrate closed via matrix #72 Option (c) hybrid (Supabase Auth canonical via `auth.jwt() -> 'app_metadata' ->> 'apex_role'`; seam.users preserved as read-model/audit). **Critical security advisory:** 66 public + 11 seam.* tables have RLS DISABLED per v2 §2.2 SQL inspection (matrix #66 + matrix #78 broader-policy follow-on); core PM tables (projects / scopes / tasks / apparatus / apparatus_revenue / financial_summaries) included; anyone with anon key can currently read or modify every row per Supabase MCP advisory.

**Next Truthful Move:** Packet A revision execution path operator-decides — §5A targeted SQL revisions (~30-60 min Desktop) / §5B Packet A v2 re-dispatch (~6-10 hr Codex) / §5C hybrid. Once revision lands, Era 2.4 Packets C/D/E/F/G authoring per v2 §15 sequence. Matrix #78 (broader-policy follow-on: PSS customer-facing + AI/MCP control plane + existing broad `using true` policies) gated on matrix #77 backlog audit. Matrix #70 (legacy `actual_revenue` column disposition) actionable now.

**Reopen Trigger Or Guardrail:** Do NOT apply RLS `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` statements live without dry-run + Supabase MCP `get_advisors` review + operator authorization (PATTERN-006 schema-closure verification). Do NOT widen `pm_core` namespace beyond NEW tables (Option c per matrix #33 Q1; existing public.*/seam.* tables stay in their namespaces). Do NOT rename existing seam.* Lane 411 tables without a dedicated migration packet (matrix #71 custody decision pending). Do NOT model full financial authority (AP/AR/GL/billing/payroll) in `pm_core` (matrix #33 Q6 scope correction — revenue-recognition-by-completion only).

**Primary Validation Surface:** Codex Cloud dispatch handoffs at `.claude/HANDOFFS/`; Supabase MCP `get_advisors` (security advisory categories); read-only `pg_policies` query for existing policy audit; PATTERN-006 schema-closure verification before any cutover packet authorization. Operator decision walkthrough record at matrix #79.

---

## Default PM Routing Rules

1. Choose the smallest lane with concrete friction, not the broadest possible frontier.
2. Prefer the next bounded Olares migration dependency whenever split-residency or laptop-risk friction would otherwise persist.
3. Treat Olares as the governing execution environment for all Apex Ops work; do not create new laptop-dependent practices by default.
4. Treat zero-row data seams as hold or dormancy outcomes, not as invitations to invent work.
5. Keep browser work behind governed control-plane seams unless a later packet explicitly changes that boundary.
6. Treat publication and host parity as part of completion, not as optional follow-up.
7. **(v2 addition)** Route PM-schema substrate work (Era 2.4 packet wave / RLS-policy authoring / `pm_core` table design / revenue-recognition vocabulary) through Lane 8, not Lane 5. Lane 5 promotes runtime through governed routes; Lane 8 authors the substrate those routes depend on. Cross-coordinate when promotion + substrate intersect.

## Minimum Effective Tooling

The current minimum effective operating stack is:

1. GitHub on `clean-main` as canonical origin,
2. standalone repo-root git publication with host-native staging and staged-diff review over `/home/olares/code/apex/apex-power-ops-platform`,
3. mesh SSH to the Olares host,
4. authoritative host implementation repo at `/home/olares/code/apex/apex-power-ops-platform`,
5. host-materialized `pnpm` and calc-engine Python toolchains,
6. bounded Olares operator scripts under `apex-power-ops-platform/tools/ai/`,
7. Claude Code plus Codex monthly-plan surfaces before any optional local-model expansion,
8. focused route, typecheck, or packet-specific validation instead of broad reruns,
9. **(v2 addition)** Supabase MCP for read-only schema/policy/advisory inspection on PM-schema substrate work (matrix #65 substrate cluster); write access reserved for explicit cutover packets.

## Operating Notes

1. The laptop remains a client surface. Do not rely on it as the only holder of durable project state or as the place where lane-specific process exceptions accumulate.
2. The historical host clone at `/home/olares/src/apex-power-ops-platform` remains observe-only.
3. If a lane needs a new runtime, install, trust-boundary, hosting, or auth change, that is a new packet, not a silent follow-on.
4. If a current frontier cannot be summarized in this cockpit without rereading multiple packet chains, that is new discoverability drift and should be corrected as a bounded governance slice. **(PATTERN-005 ancestor — formalized 2026-05-26 PM cycle 3 in `C:/APEX Platform/.claude/PLATFORM/METHODOLOGY_PATTERNS.md`.)**
5. **(v2 addition)** When the cockpit is updated for substrate-currency, anchor matrix item numbers + packet IDs explicitly in the relevant lane subsection. Drift = "this cockpit can no longer route an operator to the canonical current-state evidence without a matrix lookup."
6. **(v2 addition)** Security-advisory awareness: until matrix #66 RLS-policy authoring lane lands a Packet A cutover, the Supabase `public.*` + `seam.*` row gravity that backs Lane 5 + Lane 8 is exposed to anyone with the anon key. Do not author dispatches that assume RLS is enforced; do not introduce browser-side direct admission to either schema until Packet A cutover lands.

---

*v2 refresh authored 2026-05-26 PM cycle 3 (matrix #68 closure). Original 2026-05-06 lane register preserved in git history; v2 introduces per-lane subsections + matrix #65 v2 substrate impact in Lane 5/6/NEW-Lane-8 + matrix #66 security-advisory awareness + matrix #28 4th-tier in Lane 6 + matrix #2 PAT model in Lane 2 + matrix #72 identity hybrid in Lane 8 + matrix #79 6-role taxonomy in Lane 8. Cross-cuts CC Tier 1 freshness pass closeout enhancement #1 (table → per-lane subsections).*
