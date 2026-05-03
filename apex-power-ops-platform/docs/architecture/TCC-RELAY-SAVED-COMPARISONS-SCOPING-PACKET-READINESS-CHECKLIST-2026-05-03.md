# TCC Relay Saved Comparisons Scoping-Packet Readiness Checklist

Date: 2026-05-03
Status: Pre-authoring readiness checklist
Scope: Record the exact preconditions that must be satisfied before a separate Phase 3 implementation scoping packet for Candidate A may be authored

## Purpose

The closed Phase 3 relay design lane did not authorize a write packet.

It did, however, identify Candidate A, saved relay comparisons, as the smallest plausible future survivor if real operator evidence later justifies reopening a scoped write discussion.

This checklist exists to make that reopening threshold explicit.

This file is not a scoping packet.

It does not reopen implementation.

## Governing Inputs

This checklist is grounded in:

1. `docs/architecture/TCC-RELAY-PHASE-3-WRITE-WORKFLOW-DESIGN-DECISION-MEMO-2026-05-03.md`
2. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-3-write-workflow-design-authoring-completion-handoff.md`
3. `docs/architecture/TCC-RELAY-OPERATOR-NEED-EVIDENCE-TEMPLATE-2026-05-03.md`
4. `docs/architecture/TCC-RELAY-OPERATOR-NEED-EVIDENCE-DRAFT-SAVED-RELAY-COMPARISONS-2026-05-03.md`

If any later reopening attempt conflicts with the Phase 3 decision memo, the decision memo wins.

## Candidate In Scope

This checklist is only for Candidate A:

1. saved relay comparisons,
2. meaning intentional preservation and later recall of a chosen compare pair,
3. not workspaces,
4. not authored notes,
5. not approval or review artifacts,
6. not generalized persisted relay state.

## Minimum Evidence Triggers Before Scoping-Packet Authoring

All of the following should be true before a Candidate A implementation scoping packet is authored.

1. The Phase 2 read-only compare surface has been live for a measurable operator-use window, not just the first day of promotion.
2. An authored operator request artifact exists and is captured in governed form.
3. At least one real technician, site, or project case is documented from live governed compare usage.
4. That case shows that the current read-only compare surface was insufficient because the same compare pair needed to be intentionally revisited later.
5. The workaround is explicitly documented, for example screenshots, manual re-selection, or engineer-mediated stdlib reconstruction.
6. The operational cost is explicitly documented, for example rework, continuity loss, compare-pair selection risk, or technician dependence on stdlib-capable personnel.
7. The evidence maps specifically to saved relay comparisons and does not actually require a workspace, notes, approval surface, or a broader platform feature.
8. The request explicitly does not reopen browser-side relay math, recommendation, ranking, optimizer behavior, or browser-direct database access.

If any of those triggers is missing, the scoping packet should remain unwritten.

## Required Scoping-Packet Content Once Triggers Are Met

If the checklist above is satisfied, the later Candidate A scoping packet should explicitly include:

1. the exact candidate name, saved relay comparisons,
2. the exact operator evidence artifact or artifacts being relied on,
3. the exact bounded user need being solved,
4. the fixed mutation boundary at `apps/mutation-seam/`,
5. the auth posture from the closed Phase 3 decision memo,
6. the review posture from the closed Phase 3 decision memo,
7. the rollback posture from the closed Phase 3 decision memo,
8. the provenance posture from the closed Phase 3 decision memo,
9. a non-reopen statement preserving the no-go items,
10. an explicit statement that the packet is scoped only to Candidate A and not to broader relay writes.

## Blocking Conditions

Any of the following blocks scoping-packet authoring:

1. only anticipated future usefulness exists, but no live governed compare usage example exists,
2. the evidence is really asking for multi-comparison grouping or sharing, which would map to workspaces instead,
3. the evidence is really asking for authored commentary or review handoff, which would map to notes or artifacts instead,
4. the request is framed as a broad technician-access or stdlib-replacement ask without naming the saved-comparison failure,
5. the request implies forbidden browser behavior or direct database access,
6. the measurable operator-use window has not yet passed.

## Recommended Immediate Collection Target

The next best evidence to collect is one real technician-use note in this shape:

1. technician role,
2. site or project name,
3. exact compare pair used,
4. exact moment the pair had to be revisited,
5. actual workaround used,
6. operational cost caused by the lack of saved recall.

That is the smallest truthful input that can turn the current authored request into stronger reopening evidence.

## Bottom Line

Candidate A is the most plausible later write survivor, but it still needs real governed-use evidence before a scoping packet should be authored.

Use this checklist to decide when that threshold has actually been met.