# APEX PM Lane Operating Cockpit

Date: 2026-05-06
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

1. `C:/APEX Platform/apex-power-ops-platform/docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`
2. `C:/APEX Platform/apex-power-ops-platform/docs/architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md`
3. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
4. lane-specific roadmap, implementation plan, or packet frontier
5. this cockpit

## Start-Here Order

For normal PM and technical-authority operation, use this order:

1. `PROJECT_STATUS.md`
2. `docs/architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md`
3. this cockpit
4. the lane-specific roadmap or packet frontier
5. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md` when host or operator proof is involved

## Current Lane Register

| Lane | State | Current Truth | Next Truthful Move | Reopen Trigger Or Guardrail | Primary Validation Surface |
|------|-------|---------------|--------------------|-----------------------------|----------------------------|
| Olares developer residency and operator hardening | Hold with bounded reopen triggers | The build-guide stack, adjacent authority framework, workstation rerun checklist, AI first-slice runbook, minimal-trio runtime decision, and current-looking repo-root parent-root task labels are now normalized in line with Olares-first execution, GitHub-canonical publication, client-only laptop posture, premium-plan-first AI use, optional local models, and the admitted minimal MCP trio. | Return to hold unless a different adjacent authority, operator, visual, or current-looking provenance-routing mismatch appears. | Do not reintroduce laptop-first durable state, mandatory Ollama assumptions, broader AI-service scope, wrapper-level Codex admission, silent publication-boundary exceptions, or current-looking parent-root helper labels inside active repo-root surfaces. | `Olares host bootstrap status` or `bash apex-power-ops-platform/tools/ai/run-olares-host-bootstrap-status.sh` |
| Olares AI/operator boundary | Active bounded baseline | The admitted minimal boundary remains `apex-fs`, `apex-db`, and `apex-jobs`; Claude Code is the packetized wrapper surface, Codex remains an approved interactive surface outside that wrapper, and the trio is operator-on-demand by default rather than always-on host baseline. | Rerun only when operator drift appears, a concrete insufficiency is recorded, or a later packet explicitly selects durable-runtime admission. | Do not open `ai_tasks`, broader executor admission, speculative orchestration rollout, wrapper-level Codex integration, or always-on trio runtime without a separate packet. | `tools/ai/run-minimal-mcp-trio.ps1` or `tools/ai/run-minimal-mcp-trio.sh` |
| Operations Visibility runtime consumers | Hold on remaining empty seams | The populated `09`-tranche consumers are landed through Packet 053; `v_resource_allocation` and `v_equipment_needs` remain empty and therefore held. | Wait for live rows or a separately justified consumer need before opening another browser/API slice. | Do not fabricate UI or API work around zero-row seams. | `tools/ai/run-olares-hold-boundary-check.ps1` with an authoritative live DSN such as `SEAM_DATABASE_URL` |
| Control-plane read seam delivery | Active business-delivery lane | Governed browser consumers should continue to route through `apps/control-plane-api`, not direct browser-side Supabase admission. | Select the next business-facing seam from platform priority, not from Olares convenience work. | Keep focused API slices bounded and test-backed. | Focused `pytest` for the touched route plus local or promoted-host smoke when applicable |
| Governed PM route promotion | Active proof-backed runtime lane | The promoted PM approval flow now carries approval-context detail fidelity across tracer, schedule, drivers, and variance siblings; the focused approval-context Playwright smoke passes, and the full `smoke:pm-live-data` reran green locally against `apps/mutation-seam` on `127.0.0.1:8000` plus `apps/operations-web` on `localhost:3000`. | Keep promoting adjacent PM slices through the governed route shell only when they can be proven with focused browser smoke plus live-data ingress proof. | Do not reopen direct browser-side data admission, drop approval-origin return context, or treat shell-level loading noise as route failure before hydrated settlement is confirmed. | `apps/operations-web/tests/browser-shell.approval-context.smoke.spec.ts`, then `corepack pnpm --dir "c:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web smoke:pm-live-data -- --operations-web-base-url http://127.0.0.1:3000 --mutation-seam-base-url http://127.0.0.1:8000` |
| Relay and specialized TCC engineering | Conditional, packet-gated | The relay read-only ladder is closed; no write lane is open by default. ETU deeper-fidelity follow-on remains optional and not currently required. | Reopen only from concrete operator evidence, measured need, or an explicit planning packet. | Do not widen into write workflows or new runtime adoption from historical planning residue alone. | Lane-specific focused tests and packet-defined validation |
| Publication and host parity | Always-required closeout gate | Olares authority claims are not complete until the standalone canonical repo is updated and `/home/olares/code/apex/apex-power-ops-platform` is restored to parity. | End every bounded Olares slice with repo-root publication and host resync. | Do not leave authoritative Olares docs or packet state workstation-local only. | `git -C "c:/APEX Platform/apex-power-ops-platform" push origin clean-main` plus host repo-root parity proof |

## Default PM Routing Rules

1. Choose the smallest lane with concrete friction, not the broadest possible frontier.
2. Prefer the next bounded Olares migration dependency whenever split-residency or laptop-risk friction would otherwise persist.
3. Treat Olares as the governing execution environment for all Apex Ops work; do not create new laptop-dependent practices by default.
4. Treat zero-row data seams as hold or dormancy outcomes, not as invitations to invent work.
5. Keep browser work behind governed control-plane seams unless a later packet explicitly changes that boundary.
6. Treat publication and host parity as part of completion, not as optional follow-up.

## Minimum Effective Tooling

The current minimum effective operating stack is:

1. GitHub on `clean-main` as canonical origin,
2. standalone repo-root git publication with host-native staging and staged-diff review over `/home/olares/code/apex/apex-power-ops-platform`,
3. mesh SSH to the Olares host,
4. authoritative host implementation repo at `/home/olares/code/apex/apex-power-ops-platform`,
5. host-materialized `pnpm` and calc-engine Python toolchains,
6. bounded Olares operator scripts under `apex-power-ops-platform/tools/ai/`,
7. Claude Code plus Codex monthly-plan surfaces before any optional local-model expansion,
8. focused route, typecheck, or packet-specific validation instead of broad reruns.

## Operating Notes

1. The laptop remains a client surface. Do not rely on it as the only holder of durable project state or as the place where lane-specific process exceptions accumulate.
2. The historical host clone at `/home/olares/src/apex-power-ops-platform` remains observe-only.
3. If a lane needs a new runtime, install, trust-boundary, hosting, or auth change, that is a new packet, not a silent follow-on.
4. If a current frontier cannot be summarized in this cockpit without rereading multiple packet chains, that is new discoverability drift and should be corrected as a bounded governance slice.