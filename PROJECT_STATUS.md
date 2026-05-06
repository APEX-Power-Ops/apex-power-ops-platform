# Apex Power Ops - Project Status

> **Last Updated**: May 6, 2026 (host workflow hardening closure and workspace authority consolidation)
> **Phase**: Operations Visibility schema live with first governed runtime consumer, NETA Import Complete, Olares bounded private lane operational with daily backup automation and host-owned encrypted offsite cadence
> **See Also**: `PROJECT_OVERVIEW.md` for full system architecture

---

## 🎯 Executive Summary

## 2026 Addendum: Olares Runtime And Private Lane

This document's main body still reflects the December 2025 application and
schema program state. The addendum below records the current bounded Olares
runtime truth so the active operator posture is not left buried only in
handoffs.

### Current Olares Boundary

| Surface | Status | Notes |
|---------|--------|-------|
| Olares workstation rerun surfaces | ✅ Restored | `forms-engine`, `p6-ingest`, canary wrappers, and bounded rerun docs are back in the workspace and validated |
| Governed installed-app set | ✅ Bounded | `forms-engine` and `p6-ingest` remain the only governed installed Olares apps |
| Private personal stack | ✅ Operational | `personal-notes` runs host-only on `127.0.0.1:5230` on the real Olares host |
| Workstation mesh SSH path | ✅ Restored | trusted operator path is `olares@100.64.0.1`, not the public FRP hostname |
| Workstation browser access | ✅ Proven | bounded SSH tunnel from local `127.0.0.1:5231` to host `127.0.0.1:5230` validated the live Memos UI |
| Local backup path | ✅ Tested | backup archive created under `/home/olares/apex-backups/personal/memos/` |
| Local restore path | ✅ Tested | forced restore completed successfully with pre-restore snapshot and post-restore HTTP 200 |
| Workstation backup copy | ✅ Tested | `backup-fetch` now creates the host archive and downloads a separate workstation copy under `$HOME\OlaresPersonalBackups\memos` |
| Workstation restore path | ✅ Tested | `restore-local` now uploads a workstation-held archive back to the host and completes the same forced restore flow successfully |
| Offsite backup mirror | ✅ Tested | `backup-fetch-sync` now mirrors the workstation backup set into `$HOME\OneDrive\OlaresPersonalBackups\memos` |
| Daily backup automation | ✅ Installed | workstation helper now installs the required daily Task Scheduler path for `backup-fetch-sync`; optional logon trigger is machine-policy-blocked and reported honestly |
| One-command operator proof | ✅ Available | `infra/private/run-personal-stack-remote.ps1 -Action status` reports compose state, HTTP health, SQLite summary, latest host backups, workstation backup copies, and the offsite mirror |
| Host-owned encrypted offsite backup | ✅ Tested | helper env was completed on the host, `status` confirmed the Backblaze repository is reachable, `init` confirmed it was already initialized, `backup` saved snapshot `542e7b9f`, and `restore-drill` validated recovery in the isolated drill path |
| Host-owned encrypted offsite automation | ✅ Installed | host helper deployed `/home/olares/code/personal/run-personal-notes-offsite-backup-host.sh`, installed `apex-personal-notes-offsite-backup.timer` for the daily `03:30 UTC` window with `20m` jitter, start-limit controls, and rotated file logs, and `run-now` saved snapshot `76b8155c` with retention prune |
| Host-owned encrypted restore-drill automation | ✅ Installed | host helper deployed `/home/olares/code/personal/run-personal-notes-offsite-restore-drill-host.sh`, installed `apex-personal-notes-offsite-restore-drill.timer` for the weekly Sunday `05:00 UTC` window with `20m` jitter, and `run-now` restored snapshot `76b8155c` into isolated drill root `/home/olares/apex-restore-drills/personal/memos/20260502T182526Z` |
| Next bounded private-lane action | 📝 Optional | keep rerunning the private-lane restore drill and timer status on operator cadence; open a new packet only for wider promotion, auth change, or ingress change |
| Public ingress for the private lane | 🚫 Deferred | the service remains intentionally host-only and outside the governed Olares-installed app surface |

### Current Olares Notes

1. The trusted access route is the restored private mesh path to `100.64.0.1`.
2. The public hostname `jlswen2121.olares.com` is treated as an FRP relay path, not the controlling host SSH surface.
3. The private personal lane is intentionally separate from the governed installed-app surface and does not imply public publication or formal APEX backup posture.
4. The private lane is now operationally complete in bounded scope: runtime, mesh SSH, browser tunnel, host backup, workstation-held backup copy, workstation-mediated offsite mirror, restore, daily backup automation, and status proof are all codified and validated.
5. The host-owned encrypted offsite backup lane is now live and validated in bounded scope: the Backblaze repository is reachable from the Olares host, a fresh `personal-notes` snapshot was written, and the restore drill recovered and validated that snapshot without touching the live runtime.
6. The workstation-mediated OneDrive mirror remains preserved as a secondary off-host copy path, not the only one.
7. The current bounded backup-governance follow-on is now closed through host-owned encrypted offsite automation, recurring restore-drill cadence, and hardened timer controls; the next approved moves remain limited to maintenance reruns unless a later packet intentionally widens scope.
8. The bounded hosted public PM lane is now also closed end-to-end: `https://mutation-seam.apexpowerops.com` serves the live hosted seam over HTTPS, `https://operations.apexpowerops.com` is cut to production deployment `dpl_8kQsnU68Jjej285HbWpEEdRVHDZv`, and the public same-origin PM plus governed promoted-host proof rerun green against the intended custom-domain target.
9. Current near-term program priority is now Olares-first developer-capability hardening and AI-workflow improvement rather than defaulting immediately back to Operations Visibility delivery. This priority shift is explicitly tied to the current field-heavy workload and the goal of reducing prompt-relay and handoff overhead while preserving Olares as the durable development anchor.
10. The first bounded Olares AI-workflow slice is now live in repo-visible form: the admitted minimal MCP trio (`apex-fs`, `apex-db`, `apex-jobs`) has a PowerShell/Bash operator kit, a verification script, a runbook, and updated authority docs that explicitly treat `apex-jobs` plus packet-handoff governance as the current trust boundary.
11. Validation for that first slice passed on the current workstation against the live trio at `127.0.0.1:8710-8712`: filesystem and database MCP contracts resolved, `select 1 as ok` passed, and `apex-jobs` recorded then closed run `1778073356984-cvgk75b3` while reporting active ledger path `/apex-data/apex-jobs-ledger.json`.
12. The same first slice now also passes from the Olares host posture. Over live mesh SSH, `/home/olares/code/apex/apex-power-ops-platform` adopted the already-running trio on `127.0.0.1:8710-8712`, the repaired Bash wrapper returned `PASS`, `select 1 as ok` passed again, and `apex-jobs` recorded then closed host-side run `1778073914623-g2t2zb9j` while health again reported ledger path `/apex-data/apex-jobs-ledger.json`.
13. The host proof exposed and closed two real Bash-surface gaps in the first-slice operator kit: envless host mirrors are now tolerated, and the Bash wrapper now supports adopted-mode operation against an already-running trio instead of assuming it must always start new listeners.
14. That publication and reconciliation gate is now also closed: commit `192f0ae1ef59d4d3f66479189a1dc06d627096be` (`Publish Olares AI workflow first-slice authority`) now governs the first-slice authority set on `origin/clean-main`, and `/home/olares/code/apex` has been restored to clean parity at the same commit.
15. The next post-publication decision is also closed: no `ai_tasks` bridge or wider executor-admission lane is opened yet. The minimal MCP trio plus `apex-jobs` and packet-handoff governance remains the current operational model until a concrete insufficiency is observed.
16. That follow-on publication and reconciliation gate is now also closed: commit `b037df57a823eb4898b32897ae3e1534a9108ee5` (`Publish Olares AI workflow packet 039 and 040 authority`) now governs the Packet 039 closeout and Packet 040 decision surfaces on `origin/clean-main`, and `/home/olares/code/apex` has been restored to clean parity at the same commit.
17. The Olares-first AI workflow tranche is parked at a stable published boundary and its operating model remains the minimal MCP trio plus `apex-jobs` and packet-handoff governance.
18. A new bounded authority objective has now been selected on top of that stable base: Packet 042 reopens only the default Operations Visibility business lane as the next bounded follow-on from the Olares-resident posture.
19. Packet 043 now selects the first truthful post-041 Operations Visibility slice: a bounded schema-deployment preflight around `Supabase/schema/09_schema_additions.sql` and `Supabase/schema/09b_enum_updates.sql`.
20. Packet 044 completed that live preflight and found the `09` schema tranche not execution-ready yet: none of the target columns, operations views, or enum additions were live; the public views in `09_schema_additions.sql` lacked explicit `security_invoker` treatment; and the Supabase advisor path appeared unavailable from this session.
21. Packet 045 remediated the repo-side public-view security posture: all 11 views in `Supabase/schema/09_schema_additions.sql` now use explicit `security_invoker` treatment.
22. Packet 046 then recovered a truthful Supabase management/advisor path from this session by activating the correct Supabase MCP management surfaces: project lookup plus security and performance advisor retrieval now work again against `resa-power-db`.
23. Packet 047 is now complete and applied the bounded `09` Operations Visibility schema tranche live. The first apply attempt exposed two source-local enum dependency defects, so the tranche source was hardened in-place before retry: `apparatus_availability` creation is now rerun-safe, assessment comparisons that reference future enum labels are text-based, and `v_master_operations` no longer assumes the `project_status` enum already contains `In Progress`.
24. Live post-apply verification is complete: the `apparatus_availability` type is present, all 28 target columns landed across `apparatus`, `tasks`, `scopes`, and `projects`, all 11 Operations Visibility views are live, all 11 carry `security_invoker = true`, the three `apparatus_assessment` enum additions are present, and representative views (`v_master_operations`, `v_apparatus_operational`) return live rows.
25. A refreshed Supabase security-advisor pass does not report any of the 11 new `09` views; remaining advisor debt is preexisting legacy surface outside this bounded tranche.
26. Packet 048 is now complete as the first runtime-consumption slice on top of the live `09` schema tranche: `apps/control-plane-api` now exposes a read-only `GET /api/v1/ops/master-operations` seam against `public.v_master_operations`, the focused pytest file passes `6/6`, and `apps/operations-web` now mounts the first governed browser consumer for that seam instead of reopening direct browser-side Supabase admission.
27. Frontend validation for Packet 048 passed through the app-local TypeScript compiler at `apps/operations-web/node_modules/.bin/tsc.cmd` after `pnpm` proved unavailable on the workstation path; editor diagnostics for the touched route, test, and browser-shell files are clean.
28. Packet 049 is now complete as a source-lineage boundary decision: the tracked lineage copy at `apex-power-ops-platform/infra/database/source-lineage/apex-resa/pm-project-pss/schema/09_schema_additions.sql` is intentionally stale reference input, not active migration authority, so the correct fix was explicit drift annotation rather than overwriting the imported snapshot.
29. The lineage note and tracked lineage SQL header now point future operators back to `Supabase/schema/09_schema_additions.sql` as the authoritative executable source and explicitly preserve the imported lineage body for provenance.
30. Packet 050 is now complete as the next adjacent Operations Visibility consumer slice: `apps/control-plane-api` now exposes `GET /api/v1/ops/schedule-health` against `public.v_schedule_health`, the focused pytest file passes `6/6`, and `apps/operations-web` now mounts a governed schedule-health panel alongside the existing master-operations consumer.
31. A live Supabase shape check confirmed `public.v_schedule_health` returns real rows in the current dataset, while `v_resource_allocation` is currently empty; that is why Packet 050 selected schedule health as the truthful next consumer instead of a speculative resource-allocation panel.
32. Packet 051 is now complete as the next adjacent Operations Visibility consumer slice: `apps/control-plane-api` now exposes `GET /api/v1/ops/project-apparatus-summary` against `public.v_project_apparatus_summary`, the focused pytest file passes `6/6`, and `apps/operations-web` now mounts a governed scope-KPI panel as the third browser consumer of the live `09` tranche.
33. A live Supabase shape check confirmed `public.v_project_apparatus_summary` returns real scope-level KPI rows in the current dataset, so Packet 051 selected it ahead of the remaining grouped category and blocker views.
34. Packet 052 is now complete as the next adjacent populated Operations Visibility consumer slice: `apps/control-plane-api` now exposes `GET /api/v1/ops/apparatus-by-category` against `public.v_apparatus_by_category`, the focused pytest file passes `6/6`, and `apps/operations-web` now mounts a governed grouped-category panel as the fourth browser consumer of the live `09` tranche.
35. A live Supabase shape check confirmed `public.v_apparatus_by_category` returns grouped apparatus rows in the current dataset; a first sample query exposed a local column-name mismatch (`percent_complete` vs. `completion_percent`), which was corrected before the slice was implemented.
36. Packet 053 is now complete as the remaining adjacent populated Operations Visibility consumer slice: `apps/control-plane-api` now exposes `GET /api/v1/ops/blockers-summary` against `public.v_blockers_summary`, the focused pytest file passes `6/6`, and `apps/operations-web` now mounts a governed blocker-aggregation panel as the fifth browser consumer of the live `09` tranche.
37. A live Supabase shape check confirmed `public.v_blockers_summary` returns grouped blocker rows in the current dataset with stable fields (`project_number`, `project_name`, `apparatus_type`, `availability`, `blocked_count`, `blocked_hours`, `sample_notes`), so the final populated adjacent consumer could be landed without speculative schema widening.
38. The remaining adjacent `09` views, `public.v_resource_allocation` and `public.v_equipment_needs`, remain live but empty in the current dataset, so the truthful next follow-on is to hold them until live data exists rather than fabricate browser surfaces around zero-row seams.
39. Packet 054 is now complete as a bounded Olares AI operator regression rerun after the Operations Visibility delivery burst: the admitted minimal MCP trio (`apex-fs`, `apex-db`, `apex-jobs`) passed the existing `verify` contract locally from `C:/APEX Platform/apex-power-ops-platform` and from the authoritative host mirror at `/home/olares/code/apex/apex-power-ops-platform` under packet id `2026-05-06-olares-dev-residency-054-minimal-mcp-trio-regression-rerun`.
40. That rerun proved the current Olares-first AI boundary remains intact without widening scope: both surfaces resolved MCP tool contracts, `select 1 as ok` passed through `apex-db`, and `apex-jobs` recorded and closed fresh successful runs (`1778086844597-ehrzzbh7` locally and `1778086865409-c98q1fgl` on host) while the host mirror stayed clean and the old observe-only clone remained untouched.
41. Packet 055 is now complete as the next bounded trigger-reevaluation decision for the still-deferred Operations Visibility seams: a fresh live Supabase count check reconfirmed `public.v_resource_allocation` and `public.v_equipment_needs` both remain at `0` rows, so no new truthful browser consumer opened after Packet 054.
42. That recheck preserved the current boundary instead of fabricating work: the populated consumer set remains closed through Packet 053, the admitted minimal MCP trio remains green through Packet 054, and the empty views stay explicitly deferred on data truth rather than implementation debt.
43. The truthful next follow-on is therefore still to hold the admitted first-slice AI boundary and the empty Operations Visibility seams as-is until a concrete insufficiency, live-data change, or separately bounded admission decision justifies a new packet.
44. Packet 056 is now complete as the bounded operator-cadence follow-on to that hold boundary: `tools/ai/check_deferred_ops_view_counts.py`, `tools/ai/run-olares-hold-boundary-check.ps1`, and `tools/ai/run-olares-hold-boundary-check.sh` now give the repo a single cadence surface for the current two trigger classes, and `.vscode/tasks.json` now exposes `Olares hold-boundary cadence check` for workstation reruns.
45. Local validation for Packet 056 passed truthfully through the new PowerShell wrapper: the minimal MCP trio still returned `PASS`, while the deferred-view helper returned `UNAVAILABLE` because the committed `.env.dev` contract resolves to the local developer database rather than a live Supabase DSN with the `09` views. That is the intended honest posture, not a hidden failure.
46. The current reopen trigger remains unchanged: use the new cadence surface with an authoritative live DSN such as `SEAM_DATABASE_URL` when a real deferred-view recheck is needed, and otherwise keep the lane on explicit hold instead of fabricating consumers or widening AI admission.
47. Packet 057 is now complete as the bounded host-portability closeout for that cadence surface: the first host rerun of `bash tools/ai/run-olares-hold-boundary-check.sh` failed because the helper depended on `sqlalchemy`, which is not available on the authoritative Olares mirror.
48. The repair kept the boundary tight instead of adding host dependencies: `tools/ai/check_deferred_ops_view_counts.py` now queries through the admitted `apex-db` MCP surface, and both `run-minimal-mcp-trio` wrappers now prefer `SEAM_DATABASE_URL` so the same bounded path can target a live DSN when one is explicitly supplied.
49. Host rerun then passed truthfully from `/home/olares/code/apex/apex-power-ops-platform`: `minimal_mcp=PASS`, `deferred_ops=UNAVAILABLE`, and the new decision text now correctly states that authoritative deferred-view rechecks require `apex-db` to be running against a live DSN such as `SEAM_DATABASE_URL`, not the default development database surface.
50. Packet 058 is now complete as the governed live-DSN follow-on to that cadence surface: `.secrets/SUPABASE_CREDENTIALS.md` provided the current bounded secret source, `tools/ai/check_deferred_ops_view_counts.py` now supports an explicit direct-connection path when a live DSN is intentionally supplied, and the PowerShell wrapper reran against the live Supabase session-pooler DSN with `minimal_mcp=PASS` and `deferred_ops=HOLD`.
51. That live proof converts the boundary from generic `UNAVAILABLE` into a real defer decision on data truth: authoritative counts for `public.v_resource_allocation` and `public.v_equipment_needs` both remain `0`, so the deferred Operations Visibility seams stay on hold because they are still empty, not because the cadence surface is missing.
52. The host mirror still cannot execute the same live-DSN recheck end to end because `/home/olares/code/apex/apex-power-ops-platform` currently lacks every local live-query fallback beyond the adopted default `apex-db` surface: no `sqlalchemy`, no `psql`, no resolvable `pg`, and no repo-local `services/mcp/apex-db` tree. The Bash wrapper was therefore hardened to degrade truthfully back to `UNAVAILABLE` instead of failing when that host posture is asked to use a live DSN.
53. Packet 059 is now complete as the post-058 boundary decision: a separate host-query-engine lane is not opened now because Packet 058 already established the controlling business truth from a governed live-DSN workstation path and no current Operations Visibility trigger depends on authoritative host-side live querying.
54. That decision preserves the lower-variance Olares boundary instead of solving the wrong problem: the next truthful reopen trigger remains a live-data change in `public.v_resource_allocation` or `public.v_equipment_needs`, not the fact that the current host mirror lacks an extra live-query engine.
55. The current hold posture is therefore explicit on both axes: workstation live-DSN reruns can produce a real `HOLD` or `REOPEN` verdict when needed, while `/home/olares/code/apex/apex-power-ops-platform` continues to return a truthful `UNAVAILABLE` for that same live-DSN path until a later packet proves a concrete need to widen host query capability.
56. Packet 060 is now complete as the post-059 dormancy verdict for this bounded Olares follow-on: because Packet 059 concluded no host-query-engine lane should open now and no other current packet candidate remains inside the admitted boundary, the truthful lane state is no longer merely active hold but dormant-until-trigger.
57. That dormancy state is narrow and evidence-bound, not abandonment: the lane remains authorable immediately if either deferred view gains live rows or a concrete later requirement specifically depends on authoritative live-DSN execution from `/home/olares/code/apex` rather than the already-proven workstation path.
58. Until one of those triggers appears, no new Olares packet is required for this hold-boundary branch; the published operator surface, live-DSN workstation proof, truthful host graceful-degrade behavior, and current `HOLD` verdict are the complete closeout state.
59. Packet 061 is now complete as the post-060 continuation decision for the broader Olares-first program: both currently active bounded follow-ons are now parked on truthful dormancy rules, so the next active lane is no longer empty-view hold work or simultaneous-worker reopening by default.
60. Packet 061 selects a planning-only host-resident developer-workflow hardening lane as the next truthful Olares-first follow-on. That choice consumes the current durable-host reality instead of reopening dormant branches: `/home/olares/code/apex` is already the authoritative mirror, the minimal MCP trio plus `apex-jobs` is already the active AI/operator boundary, and the remaining Olares-first value now lies in reducing host-resident development friction rather than widening product or infrastructure scope speculatively.
61. The selected next lane is still bounded and non-executing at this packet: it authorizes a later planning surface to inventory concrete host-resident workflow friction and pick one smallest hardening slice, while keeping the deferred Operations Visibility branch trigger-bound, the simultaneous-worker branch trigger-bound, broader AI-services expansion closed, and GitHub-canonical publication unchanged.
62. Packet 062 is now complete as that planning surface. The controlling friction is not missing host authority, but fragmented host entrypoints: the durable host cutover plan, the general operator bootstrap runbook, the minimal MCP runbook, and the current tasks surface all exist, but there is still no single repo-owned host bootstrap/status surface that tells an operator whether the canonical mirror, toolchain paths, minimal MCP boundary, and current hold-boundary posture are ready from `/home/olares/code/apex`.
63. Packet 062 therefore selects one smallest hardening slice for later execution: add a bounded host-resident workflow bootstrap/status operator surface, with a matching runbook and task entry, that reports mirror path/parity, host toolchain presence, minimal MCP readiness, and hold-boundary status without widening into installs, runtime mutation, or AI-service expansion.
64. That selected slice keeps the broader Olares-first program disciplined: it hardens the already-proven durable-host workflow directly, leaves both dormant branches closed until their triggers occur, and preserves GitHub-canonical publication plus the current minimal MCP trio trust boundary.
65. Packet 063 is now complete as the execution of that selected hardening slice. The repo now includes a bounded host bootstrap/status operator surface at `apex-power-ops-platform/tools/ai/run-olares-host-bootstrap-status.sh` that composes the already-admitted durable-host checks instead of inventing new runtime behavior.
66. That new surface reports one truthful host-resident readiness view only: parent-root host commit and cleanliness, old-clone observe-only state, materialized host toolchain presence, minimal MCP trio readiness, and the current hold-boundary result from the authoritative host posture.
67. Packet 063 also closes a nearby operator-surface defect uncovered during execution: the existing VS Code task for the hold-boundary cadence surface was still pointing at a non-existent parent-root `tools/ai` path, so the task now targets the real platform-root script location and the new host bootstrap/status task is added alongside it.
68. The execution remains tightly bounded: no installs, no package or lockfile mutation, no runtime or service mutation, no AI-services expansion, no Git hosting change, and no dormant-branch reopening were required to land the new host workflow status surface.
69. Packet 064 is now complete as the bounded publication and host-mirror resync gate for Packet 062 planning authority and Packet 063 execution authority. The host bootstrap/status operator surface, its task/runbook updates, and the continuation-planning artifacts are now published on `origin/clean-main` and mirrored back onto `/home/olares/code/apex` in clean parity.
70. That closeout preserves the intended lane discipline: the new host workflow hardening surface is now real and durable in the authoritative host mirror, while the deferred Operations Visibility hold branch and the simultaneous-worker branch both remain dormant under their published trigger rules.
71. A new current stakeholder-facing authority surface now exists for the Olares workspace operating model at `apex-power-ops-platform/docs/architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md`. It consolidates the live design constraints, governance rules, approved environment and tooling posture, operator process, and remaining implementation plan that were previously split across the framework, roadmap, cutover plans, and packet chain.
72. The root `WORKSPACE_DESIGN.md` and `WORKSPACE_PROTOCOL.md` files are now explicitly historical reference surfaces rather than current Olares governance. They remain useful as early conceptual context, but the current authoritative operating model is the GitHub-canonical parent-root mirror at `C:/APEX Platform` and `/home/olares/code/apex`, with `apex-power-ops-platform` as the active implementation surface and the laptop governed as a client-only surface.
73. The next truthful Olares follow-on after Packet 064 is therefore not generic workspace redesign. It is a bounded decision on whether any additional host-resident workflow-hardening slice is still needed now that the host bootstrap/status surface exists and the current design/governance/plan are consolidated into one repo-owned authority document.
74. That authority-consolidation tranche is now also published and mirrored: commit `ecfe18015c9c15cef16f3fb668fdfc56db7c909f` (`Consolidate Olares workspace authority`) is live on `origin/clean-main`, `/home/olares/code/apex` is restored to clean parity at the same commit, and `/home/olares/src/apex-power-ops-platform` remains preserved observe-only at `2836a2622309b4e146ca24f23b5bf87312c0c857` with status count `30`.
75. Packet 068 is now complete as the post-067 follow-on decision and selects one additional bounded workflow-hardening slice at the root entrypoint layer: the new Olares authority and host bootstrap surfaces are published, but the root `README.md` and `PROJECT_OVERVIEW.md` still left operators entering through stale or unqualified routing.
76. Packet 069 is now complete as that bounded execution slice. The root `README.md` now routes readers first to the live Olares authority and operator runbook, and `PROJECT_OVERVIEW.md` now carries a concise current Olares operating note so the 2025 platform snapshot is not mistaken for the current Olares workspace operating model.
77. That root-entrypoint tranche is now also published and mirrored: commit `75cecbb6f2ce72399c290257fe8e36d3f03cf322` (`Refresh Olares root entry routing`) is live on `origin/clean-main`, `/home/olares/code/apex` is restored to clean parity at the same commit, and `/home/olares/src/apex-power-ops-platform` remains preserved observe-only at `2836a2622309b4e146ca24f23b5bf87312c0c857` with status count `30`.
78. Packet 071 is now complete as the post-070 follow-on decision for the current host-workflow-hardening lane. With the durable-host bootstrap/status surface published, the current Olares workspace authority consolidated, and the root entrypoints refreshed, no additional host-workflow-hardening slice is justified on current evidence.
79. The truthful lane state therefore returns to explicit dormancy until new friction appears. Reopen this lane only if a concrete operator-routing, durable-host validation, publication-parity, or authority-discoverability problem emerges that is not already closed by the current runbook, status surface, and root entrypoint chain.
80. That dormancy decision is now also published and mirrored: commit `5006b2348d8170ecb97e9d1e1aa5c44f7cab6f22` (`Park Olares host workflow lane`) is live on `origin/clean-main`, `/home/olares/code/apex` is restored to clean parity at the same commit, and `/home/olares/src/apex-power-ops-platform` remains preserved observe-only at `2836a2622309b4e146ca24f23b5bf87312c0c857` with status count `30`.
81. Packet 073 is now complete as the post-072 governance-alignment decision. With the host-workflow-hardening lane explicitly dormant, the next concrete friction is the older Olares roadmap still presenting several generic Phase 2 through Phase 4 items as blank open queue work rather than as current trigger-based guardrails.
82. Packet 074 is now complete as that bounded roadmap-trigger realignment slice. The Olares roadmap now reclassifies those older generic backlog items into maintained rerun surfaces, preserved limitation boundaries, and trigger-gated governance rules so the repo-visible authority no longer implies that Olares remains an always-open execution epic.
83. Packet 075 is now complete as that publication and host-mirror resync closeout for the roadmap-trigger realignment tranche.
84. Packet 075 published the governance-realignment tranche in commit `aebe4f95a9502dc30772f06bd6b977cd6d70071f` (`Realign Olares roadmap triggers`), pushed `origin/clean-main`, restored `/home/olares/code/apex` to clean parity at the same commit, and preserved `/home/olares/src/apex-power-ops-platform` observe-only at `2836a2622309b4e146ca24f23b5bf87312c0c857` with status count `30`.
85. Packet 076 is now complete as the post-075 discoverability decision surface. With Olares back to explicit trigger-based dormancy, the next concrete friction is no longer missing host workflow hardening but fragmented lane-frontier visibility: later sessions still reconstruct current lane truth across status, authority, roadmap, and packet surfaces, and the Olares roadmap still cited a non-existent top-authority file in active dependency text.
86. Packet 077 is now complete as that bounded PM operating cockpit and authority-reference realignment slice. The repo now includes `apex-power-ops-platform/docs/architecture/APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md` as a compact current lane register, the active Olares authority doc now points to that cockpit as a companion surface, and the roadmap no longer relies on the missing `Infrastructure/APEX_Platform_Operating_Model_and_Governance.md` path in its active dependency and further-reading sections.
87. Packet 078 is now complete as the publication and host-mirror resync closeout for the PM operating cockpit tranche.
88. Packet 078 published the cockpit tranche in commit `0168bb955daa5010e9e222fbccbab3fa4f5e9aad` (`Add APEX PM lane cockpit`), pushed `origin/clean-main`, restored `/home/olares/code/apex` to clean parity at the same commit, and preserved `/home/olares/src/apex-power-ops-platform` observe-only at `2836a2622309b4e146ca24f23b5bf87312c0c857` with status count `30`.

```mermaid
pie title Project Completion Status
    "Complete" : 78
    "In Progress" : 12
    "Planned" : 10
```

| Milestone | Status | Notes |
|-----------|--------|-------|
| Supabase Schema Design | ✅ Complete | 30 tables, 38+ ENUMs, 12+ triggers |
| Database Deployment | ✅ Complete | All migrations applied |
| Test Data Load | ✅ Complete | LASNAP16 project (47 apparatus) |
| Web App Connection | ✅ Complete | Next.js app fetching from Supabase |
| UI Specification | ✅ Complete | Full spec + v0.dev prompts |
| Role-Based Demo | ✅ Ready | 5-role interactive prototype |
| **NETA Procedures Import** | ✅ Complete | 66 procedures (ATS + MTS) |
| **NETA Test Items** | ✅ Complete | 956 test items across standards |
| **Operations Schema** | ✅ Deployed | `09` tranche live and verified on Supabase |
| Revenue Recognition Flow | ⏳ Ready | Triggers deployed, needs UI testing |
| PSS Portal | 📋 Schema Ready | 6 tables deployed, UI not started |
| Production Deployment | 🔜 Planned | Dev environment only |

---

## 🔥 Current Focus: Operations Visibility (Session 7 Output)

### Requirements Discovery Complete

Key questions answered this session - see `.claude/SESSION_2025-12-11_SCHEMA_OPERATIONS.md`:

1. **Pain Point**: Connecteam shows WHO/WHERE/WHEN, not WHAT can be worked or WHY blocked
2. **Current Workaround**: Excel trackers built to fill visibility gaps
3. **Scaling Problem**: 5→15 projects broke "fits in your head" approach
4. **Success Criteria**: Centralized real-time visibility of everything
5. **MVP**: Operations dashboard answering resource allocation questions

### Schema Additions Deployed And First Runtime Consumer Landed

| File | Contents | Status |
|------|----------|--------|
| `09_schema_additions.sql` | Operational fields + 11 views | ✅ Live on Supabase |
| `09b_enum_updates.sql` | Assessment enum alignment | ✅ Applied live |
| `apps/control-plane-api/services/ops/router.py` | Governed `v_master_operations` read seam | ✅ First consumer API landed |
| `apps/operations-web/app/master-operations-explorer.tsx` | First browser consumer of the governed seam | ✅ Mounted in browser shell |
| `apps/control-plane-api/services/ops/router.py` | Governed `v_schedule_health` read seam | ✅ Adjacent consumer API landed |
| `apps/operations-web/app/schedule-health-explorer.tsx` | Second browser consumer of the governed seam set | ✅ Mounted in browser shell |
| `apps/control-plane-api/services/ops/router.py` | Governed `v_project_apparatus_summary` read seam | ✅ Third consumer API landed |
| `apps/operations-web/app/project-apparatus-summary-explorer.tsx` | Third browser consumer of the governed seam set | ✅ Mounted in browser shell |
| `apps/control-plane-api/services/ops/router.py` | Governed `v_apparatus_by_category` read seam | ✅ Fourth consumer API landed |
| `apps/operations-web/app/apparatus-by-category-explorer.tsx` | Fourth browser consumer of the governed seam set | ✅ Mounted in browser shell |
| `apps/control-plane-api/services/ops/router.py` | Governed `v_blockers_summary` read seam | ✅ Fifth consumer API landed |
| `apps/operations-web/app/blockers-summary-explorer.tsx` | Fifth browser consumer of the governed seam set | ✅ Mounted in browser shell |
| `EXCEL_TO_DATABASE_MAPPING.md` | Field transformation guide | ✅ Complete |

### New Operational Views Designed

| View | Purpose |
|------|---------|
| `v_master_operations` | Multi-project "God View" |
| `v_project_apparatus_summary` | Per-project KPIs |
| `v_resource_allocation` | Where to send people |
| `v_equipment_needs` | Test equipment planning |
| `v_blockers_summary` | What's stopping progress |

---

## 📊 Phase 1.6 Resource Linking (Complete)

```mermaid
flowchart LR
    subgraph "Ready Now"
        direction TB
        R1[📊 Executive Dashboard]
        R2[📋 Project List]
        R3[🏢 Client Management]
        R4[⚙️ Apparatus Tracking]
        R5[📄 Report Generator]
    end
    
    subgraph "In Specification"
        direction TB
        S1[👷 Field Tech View]
        S2[📐 Estimator Dashboard]
        S3[👔 PM Dashboard]
        S4[🏛️ Admin Settings]
    end
    
    subgraph "Phase 2"
        direction TB
        P1[⚡ PSS Portal]
        P2[👤 Engineer Login]
        P3[📁 Document Upload]
        P4[❓ RFI Workflow]
    end
    
    R1 --> S1
    S4 --> P1
    
    style R1 fill:#22c55e,color:#fff
    style R2 fill:#22c55e,color:#fff
    style R3 fill:#22c55e,color:#fff
    style R4 fill:#22c55e,color:#fff
    style R5 fill:#22c55e,color:#fff
    style S1 fill:#3b82f6,color:#fff
    style S2 fill:#3b82f6,color:#fff
    style S3 fill:#3b82f6,color:#fff
    style S4 fill:#3b82f6,color:#fff
    style P1 fill:#94a3b8,color:#fff
    style P2 fill:#94a3b8,color:#fff
    style P3 fill:#94a3b8,color:#fff
    style P4 fill:#94a3b8,color:#fff
```

### UI Specification Documents

| Document | Location | Purpose |
|----------|----------|---------|
| `UI_SPECIFICATION_GUIDE.md` | `Documentation/07_Application_Specs/` | Complete design system, 927 lines |
| `ROLE_DEMO_PROMPT.md` | `Documentation/07_Application_Specs/` | v0.dev prompt - 5 role views, 1193 lines |
| `REPORT_GENERATOR_DEMO_PROMPT.md` | `Documentation/07_Application_Specs/` | Standalone report flow |
| `FIELD_TECH_APPLICATION_SPEC.md` | `Documentation/07_Application_Specs/` | Mobile field app requirements |

### Role-Based Dashboard Features

```mermaid
mindmap
  root((Apex Power Ops<br/>Dashboards))
    Executive
      Revenue KPIs
      Project Pipeline
      Multi-location View
      Financial Trends
    Project Manager
      Active Projects
      Resource Allocation
      Budget vs Actual
      Schedule Tracking
    Estimator
      Quote Pipeline
      Win Rate
      Pending Approvals
      Historical Data
    Field Technician
      My Assignments
      Today's Work
      Apparatus Status
      Quick Entry
    Office Admin
      All Projects
      User Management
      Reports
      System Settings
```

---

## 📊 Database Statistics (Dec 11, 2025)

### Table Counts

| Table | Records | Change |
|-------|---------|--------|
| `neta_procedures` | **33** | +33 (NEW) |
| `neta_test_items` | **77** | +77 (NEW) |
| `apparatus` | 47 | - |
| `apparatus_types` | 15 | - |
| `tasks` | 12 | - |
| `resource_assignments` | 8 | - |
| `scope_labor_details` | 6 | - |
| `pss_document_templates` | 6 | - |
| `locations` | 5 | - |
| `employees` | 5 | - |
| `scopes` | 4 | - |
| `estimators` | 2 | - |
| `projects` | 1 | - |
| `clients` | 1 | - |
| `sites` | 1 | - |

### Schema Summary

| Component | Count | Details |
|-----------|-------|---------|
| **Tables** | 30 | Core(5) + Hierarchy(4) + Equipment(3) + Financial(4) + Resource(1) + PSS(6) + NETA(7) |
| **ENUMs** | 38+ | All status types, roles, assessments |
| **Triggers** | 12+ | Rollup counts, revenue recognition, audit |
| **Views** | 15+ | Dashboard aggregations |
| **Indexes** | ~50 | Performance optimization |

---

## 🗺️ Implementation Roadmap

```mermaid
gantt
    title Apex Power Ops Development Roadmap
    dateFormat YYYY-MM-DD
    
    section Phase 1 - Foundation
    Schema Design           :done, p1a, 2025-12-01, 3d
    Database Deployment     :done, p1b, 2025-12-04, 1d
    Test Data Load          :done, p1c, 2025-12-05, 1d
    Web App Connection      :done, p1d, 2025-12-05, 1d
    UI Specification        :done, p1e, 2025-12-11, 1d
    
    section Phase 1.6 - Resource Linking
    NETA ATS Import         :active, p16a, 2025-12-11, 2d
    NETA MTS/ECS/ETT Import :p16b, after p16a, 2d
    Type-Procedure Mapping  :p16c, after p16b, 1d
    Resource Content        :p16d, after p16c, 2d
    Mobile Resource UI      :p16e, after p16d, 2d
    
    section Phase 1.7 - Field Testing App
    Project Detail Page     :f1, after p16e, 2d
    Apparatus Completion    :f2, after f1, 2d
    Revenue Testing         :f3, after f2, 1d
    Real Data Import        :f4, after f3, 2d
    
    section Phase 2 - Auth & PSS
    Supabase Auth           :a1, 2025-12-28, 3d
    RLS Policies            :a2, after a1, 2d
    PSS Portal UI           :p2a, 2026-01-06, 5d
    Document Management     :p2b, after p2a, 3d
    
    section Phase 3 - Production
    Production Deploy       :p3, 2026-01-20, 3d
```

---

## 📋 Task Breakdown by Phase

### Phase 1.6: Resource Linking (Current)

| Task | Owner | Status | Description |
|------|-------|--------|-------------|
| Import ATS procedures | ✅ Desktop | Done | 33 procedures loaded |
| Import ATS test items | VS Code | ⚠️ 5/33 | Continuing from handoff |
| Import MTS-2023 | TBD | ⏳ | ~similar structure |
| Import ECS-2024 | TBD | ⏳ | ~similar structure |
| Import ETT-2022 | TBD | ⏳ | ~similar structure |
| Map apparatus_types | TBD | ⏳ | Populate neta_section columns |
| Create junction records | TBD | ⏳ | apparatus_type_resources |
| Add sample SOPs | TBD | ⏳ | Company procedures |
| Add safety docs | TBD | ⏳ | JSAs, bulletins |
| Resource lookup UI | TBD | ⏳ | Mobile component |

### Phase 1.7: Field Testing App

| Task | Complexity | Description |
|------|------------|-------------|
| Project detail page | Medium | Show scopes, tasks, apparatus hierarchy |
| Apparatus completion UI | Medium | Mark complete with delay hours |
| Test revenue trigger | Low | Complete apparatus, verify revenue |
| Import Garney data | Medium | Real project from Excel tracker |

### Phase 2: PSS Portal

| Task | Complexity | Description |
|------|------------|-------------|
| Engineer portal UI | High | External user interface |
| Supabase Auth setup | Medium | Email/password for engineers |
| Document upload | Medium | Storage bucket integration |
| RFI workflow | Medium | Status transitions, notifications |

---

## 🔧 Technical Reference

### Supabase Connection

```
Project:     resa-power-db
Ref:         fxoyniqnrlkxfligbxmg
API URL:     https://fxoyniqnrlkxfligbxmg.supabase.co
Environment: Development
```

### Legacy External Web App Snapshot

```
External Path: C:\Users\jjswe\Projects\resa-web-app
Framework:   Next.js 16.0.5 (App Router)
React:       19.2.0
UI:          shadcn/ui + Radix + Tailwind CSS
```

### Key Files

| Purpose | Path |
|---------|------|
| Session State | `.claude/STATE.md` |
| Task Coordination | `.claude/COORDINATION.md` |
| NETA Import Handoff | `Supabase/scripts/NETA_IMPORT_HANDOFF.md` |
| UI Specifications | `Documentation/07_Application_Specs/` |
| Schema Reference | `Supabase/SCHEMA_REFERENCE.md` |
| Supabase Client | `legacy external app: resa-web-app/src/lib/supabase.ts` |

---

## 🏷️ Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-05 | 1.0.0 | Initial Supabase deployment |
| 2025-12-05 | 1.0.1 | LASNAP16 test data loaded |
| 2025-12-10 | 1.1.0 | Resource Linking schema deployed |
| 2025-12-11 | 1.2.0 | UI Specification complete |
| 2025-12-11 | **1.3.0** | NETA import started (33 procedures, 77 test items) |
| 2026-05-01 | **1.4.0** | Olares bounded private lane closed operationally: host runtime, mesh SSH, tunnel access, tested backup/restore, and operator proof surface |

---

*Document Version: 1.4.0 | Last Updated: May 1, 2026*
