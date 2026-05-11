# Olares Dev Residency 006 Operator Execution Prompt

Date: 2026-05-05
Status: Historical copy-paste prompt surface
Packet: `ops/agents/packets/draft/2026-05-05-olares-dev-residency-006-packet-001-through-packet-005-authority-publication-and-host-mirror-resync-gate.json`
Scope: execute the bounded authority-publication and host-mirror resync gate for Dev Residency Packet 001 through Packet 005 without widening scope

Historical note:

This prompt preserves a pre-cutover publication instruction from before the canonical repo boundary moved to `C:/APEX Platform/apex-power-ops-platform` and `/home/olares/code/apex/apex-power-ops-platform` on 2026-05-07. Do not reuse it as a current operator prompt without translating the git-root and publication-boundary instructions to the standalone repo root.

## Use

Copy the prompt below into the next execution session when you want to close
Packet 006.

## Prompt

```text
Execute Olares Dev Residency 006 as a bounded authority-publication and host-mirror resync gate.

Read first:
1. apex-power-ops-platform/ops/agents/packets/draft/2026-05-05-olares-dev-residency-006-packet-001-through-packet-005-authority-publication-and-host-mirror-resync-gate.json
2. apex-power-ops-platform/ops/agents/handoffs/2026-05-05-olares-dev-residency-006-packet-001-through-packet-005-authority-publication-and-host-mirror-resync-gate-handoff.md
3. apex-power-ops-platform/ops/agents/packets/draft/2026-05-05-olares-dev-residency-001-developer-host-cutover-preflight-and-execution-planning.json
4. apex-power-ops-platform/ops/agents/packets/draft/2026-05-05-olares-dev-residency-002-canonical-host-residency-and-toolchain-revalidation.json
5. apex-power-ops-platform/ops/agents/packets/draft/2026-05-05-olares-dev-residency-003-bounded-host-toolchain-availability-decision.json
6. apex-power-ops-platform/ops/agents/packets/draft/2026-05-05-olares-dev-residency-004-bounded-host-toolchain-materialization-authority-decision.json
7. apex-power-ops-platform/ops/agents/packets/draft/2026-05-05-olares-dev-residency-005-minimum-host-toolchain-materialization-execution.json
8. apex-power-ops-platform/ops/agents/handoffs/2026-05-05-olares-dev-residency-001-operator-execution-prompt.md
9. apex-power-ops-platform/docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-MILESTONE-PLAN-2026-05-05.md
10. apex-power-ops-platform/docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-TECHNICAL-PLAN-2026-05-05.md
11. apex-power-ops-platform/docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-MILESTONE-1-ACCEPTANCE-CHECKLIST-2026-05-05.md
12. apex-power-ops-platform/ops/agents/handoffs/2026-05-03-olares-phase-5-next-task-and-prompt-routing-handoff.md
13. apex-power-ops-platform/plan/infrastructure-olares-full-implementation-roadmap-1.md

Objective:
Historically, this prompt published the local Dev Residency Packet 001 through Packet 005 authority set through the then-active parent-root boundary, pushed clean-main, and fast-forwarded /home/olares/code/apex non-destructively so the host mirror carried the governed cutover, toolchain, and validation evidence before any later client-only or delivery-readiness decision depended on it.

Execution rules:
1. stage only the bounded Dev Residency docs and authority surfaces named by Packet 006
2. exclude .vercelignore, older Packet 039 drift, older Packet 057 drift, older Packet 062 drift, unrelated authority drift, source edits, package or lockfile mutation, runtime or service mutation, and old-clone mutation
3. parse Packet 001 through Packet 006 JSON before commit
4. run git diff --cached --check and inspect staged paths before commit
5. commit and push only if the staged scope is exact
6. fast-forward /home/olares/code/apex non-destructively only after publication succeeds
7. observe /home/olares/src/apex-power-ops-platform only; do not mutate it
8. record the published commit, commit message, push result, host pre/post commit, and status counts in repo-visible closeout

Required outputs:
1. a concise execution verdict: complete or blocked
2. the exact staged publication scope
3. the published commit and commit message if publication succeeds
4. /home/olares/code/apex pre-sync and post-sync commit/status evidence
5. /home/olares/src/apex-power-ops-platform commit/status evidence with explicit observe-only wording
6. explicit confirmation that no source, package, lockfile, runtime, service, ingress, hosting-transition, remote-rewrite, rollback, force, reset, clean, or old-clone mutation scope was opened
7. repo-visible updates only if needed to close Packet 006 truthfully

If Packet 006 succeeds:
1. mark Packet 006 complete
2. update routing and roadmap so the next packet is unambiguous
3. do not treat publication hygiene as feature-delivery approval
4. route the next step to a later client-only posture or resumed delivery readiness decision packet, not immediate feature work

If Packet 006 is blocked:
1. stop at the exact blocker
2. do not fake closeout authority
3. leave the next packet routing explicit and truthful
```