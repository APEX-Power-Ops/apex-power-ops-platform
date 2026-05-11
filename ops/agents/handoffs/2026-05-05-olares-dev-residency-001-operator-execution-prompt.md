# Olares Dev Residency 001 Operator Execution Prompt

Date: 2026-05-05
Status: Historical copy-paste prompt surface
Packet: `ops/agents/packets/draft/2026-05-05-olares-dev-residency-001-developer-host-cutover-preflight-and-execution-planning.json`
Scope: execute the planning-only Packet 001 cutover decision cleanly and leave the next packet routing unambiguous

Historical note:

Packet 001 is already closed. This prompt is retained as the original planning prompt for that decision surface, not as a live operator prompt for current repo-root work.

## Use

Copy the prompt below into the next execution session when you want to close
Packet 001.

## Prompt

```text
Execute Olares Dev Residency 001 as a planning-only packet.

Read first:
1. apex-power-ops-platform/ops/agents/packets/draft/2026-05-05-olares-dev-residency-001-developer-host-cutover-preflight-and-execution-planning.json
2. apex-power-ops-platform/ops/agents/handoffs/2026-05-05-olares-dev-residency-001-developer-host-cutover-preflight-and-execution-planning-handoff.md
3. apex-power-ops-platform/docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-MILESTONE-PLAN-2026-05-05.md
4. apex-power-ops-platform/docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-TECHNICAL-PLAN-2026-05-05.md
5. apex-power-ops-platform/docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-MILESTONE-1-ACCEPTANCE-CHECKLIST-2026-05-05.md
6. apex-power-ops-platform/plan/infrastructure-olares-full-implementation-roadmap-1.md
7. Infrastructure/Olares_Workspace_Authority_Framework.md
8. Infrastructure/Olares_Build_Guide.md
9. apex-power-ops-platform/ops/agents/handoffs/2026-05-03-olares-phase-5-095-packet-093-and-packet-094-authority-publication-and-host-mirror-resync-gate-handoff.md

Objective:
Decide whether the Olares developer-host cutover phase is now the controlling prerequisite for resumed feature delivery, and whether the first execution lane should remain Olares Dev Residency 002 - Canonical Host Residency And Toolchain Revalidation.

Execution rules:
1. planning only; do not execute Packet 002
2. do not mutate runtimes, packages, public ingress, hosting posture, or the old clone
3. do not reopen the dormant Phase 5 simultaneous-worker lane
4. preserve GitHub as canonical and `/home/olares/code/apex` as the intended host mirror
5. use the Milestone 1 acceptance checklist to sharpen what Packet 002 must prove

Required outputs:
1. a concise planning verdict: affirmative or not affirmative
2. the ordered proof slices that must close before resumed product delivery
3. explicit confirmation of what remains closed during cutover
4. a statement of whether Packet 002 remains the correct next execution packet
5. repo-visible updates only if needed to close Packet 001 truthfully

If the verdict is affirmative:
1. keep Olares Dev Residency 002 as the live next packet
2. state that Packet 002 is authored but not yet executed
3. route execution to the Milestone 1 checklist and the Packet 002 handoff

If the verdict is not affirmative:
1. explain the blocking fact precisely
2. do not execute or promote Packet 002
3. update the routing surface so the next packet is not ambiguous
```