# TCC Relay Phase 3 Write Workflow Design Decision Memo

Date: 2026-05-03
Status: Closed PASS in repo; design-only decision memo; no implementation opened
Scope: Decide whether any relay write workflow should open now after Phase 2 read-only compare proved value, and if so fix the exact mutation boundary, auth, review, rollback, and provenance posture

## Purpose

Phase 2 closed PASS in repo and on promoted host on 2026-05-03.

This memo answers, in design space only, the bounded Phase 3 question:

1. should any relay write workflow open now,
2. if any candidate survives, where does the mutation boundary live,
3. what auth, review, rollback, and provenance controls would be required,
4. what proof must exist before a later implementation packet could open.

This memo does not open implementation.

It does not edit `apps/`, `packages/`, or `infra/` runtime surfaces.

It does not introduce schema, ingress, or auth changes.

## Governing Inputs

This memo is grounded in:

1. `TCC-RELAY-GOVERNANCE-INDEX-2026-05-03.md`
2. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md`
3. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md`
4. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-operations-web-promoted-host-redeploy-blocker-handoff.md`
5. `TCC-RELAY-EXPLORATORY-COMPARE-CONCEPT-ADOPTION-MEMO-2026-05-03.md`
6. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-3-write-workflow-design-handoff.md`
7. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-3-write-workflow-design-authoring-handoff.md`
8. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-3-write-workflow-design-authoring-completion-handoff.md`

If any summary in this memo conflicts with the relay governance index, the adjacent Phase 2 and Phase 3 handoff trail, or a later repo-local closure record, the more specific repo-local surface wins.

## Confirmed Floor

Before evaluating any write candidate, this memo treats the following as fixed:

1. the five-tranche read-only relay implementation ladder is closed PASS,
2. Phase 1 hosted proof is closed PASS,
3. the first bounded Phase 2 compare slice is closed PASS in repo,
4. the promoted host `https://operations.apexpowerops.com` serves the recovered compare-slice bundle and the promoted-host smoke ended `PROMOTED_HOST_SUMMARY failed=0`,
5. no recommendation, optimizer, browser-side relay math, or browser-direct database access exists in the landed lane,
6. source-faithful per-side identity (`td_section_source_id`, `relay_device_source_id`, `family_name`, `storage_kind`) is preserved on both compare sides,
7. unsupported and partially supported sections remain visible with explicit warnings.

That floor is the read-only proof surface against which any write candidate is judged.

## Candidate Inventory

The Phase 3 execution packet names four candidate write workflows that are directly implied by the now-proven compare slice. This memo evaluates only those four. It does not invent additional candidates.

### Candidate A: Saved relay comparisons

Description: persist a `(primary_td_section_id, compare_td_section_id)` pair under an operator account so the operator can re-open the same compare in a later session without re-searching.

Direct implication of the Phase 2 surface: yes, weakly. The compare panel already accepts both IDs from a search and reconstructs the read-only views on demand from governed surfaces.

### Candidate B: Named study workspaces or persisted relay selections

Description: a named container holding one or more saved comparisons, optional ordering, optional cross-session continuity, optional sharing among operators on the same project.

Direct implication of the Phase 2 surface: indirect. The compare slice does not produce or imply a workspace concept; this candidate would introduce a multi-comparison container abstraction that did not exist before this memo.

### Candidate C: Authored operator notes or reviewable comparison artifacts

Description: free-form operator-authored prose attached to a saved comparison, optionally reviewable or approvable, optionally exportable as a comparison artifact.

Direct implication of the Phase 2 surface: indirect. The compare slice surfaces sourced relay truth and explicit unsupported warnings. Authored content is materially distinct from sourced content and would require its own provenance lane.

### Candidate D: Other persisted relay workflow state

Description: lower-stakes UI state persistence, for example recent searches, last-viewed TD-section, or last compare pair, persisted per operator.

Direct implication of the Phase 2 surface: weakly direct, but only as ergonomic state, not as authored content.

## Classification

For each candidate, this memo classifies as one of:

1. **NO-GO**: must not be reopened by any later packet without first reopening at the post-ladder follow-on planning level,
2. **defer-later**: legitimately a candidate for a future relay phase, but not implementation-worthy now and not implementation-worthy purely on the strength of the Phase 2 read-only proof,
3. **implementation-worthy only after a later execution packet**: would survive into a later execution lane if and only if a separately authored execution packet opens it.

### Candidate A — Saved relay comparisons → defer-later

Why defer-later, not implementation-worthy now:

1. Phase 2 has been live on the promoted host for less than one calendar day, so there is no operator-need evidence yet,
2. the read-only compare slice already accepts both IDs from a single search and reconstructs the views; the marginal value of persistence is real but unproven,
3. opening this candidate without operator-need evidence would silently cross from the bounded Phase 2 read-only proof floor into an implementation lane that the post-ladder authority deliberately deferred until after read-only operator value is demonstrated.

Why not NO-GO:

1. saved comparisons are the smallest, lowest-risk write candidate directly tied to the proven compare contract,
2. permanently rejecting this candidate would prejudge a question the post-ladder authority deliberately left open.

### Candidate B — Named study workspaces or persisted relay selections → defer-later

Why defer-later, not implementation-worthy now:

1. workspaces introduce lifecycle, sharing, ownership, archive, and visibility concepts that did not exist in the Phase 2 surface,
2. these are platform concerns broader than relay, so opening them in a relay-only lane risks a lane mismatch,
3. workspaces silently cross into the no-go items the Phase 3 execution packet explicitly blocks (browser save or submit actions, persisting relay operator state) without first proving that a smaller candidate is insufficient.

Why not NO-GO:

1. workspaces remain a legitimate platform-shaped product question that may surface again from non-relay lanes (for example coordination workspaces) and should not be retired here.

### Candidate C — Authored operator notes or reviewable comparison artifacts → defer-later, with strong constraints

Why defer-later, not implementation-worthy now:

1. authored notes and reviewable artifacts cross materially into approval-shaped behavior, which the Phase 3 execution packet explicitly blocks,
2. authored content sits adjacent to sourced relay truth and creates a high risk of identity collapse or sourced-versus-authored confusion,
3. the exploratory compare memo already classified procedural injection guidance, tester tips, and approval-oriented narrative framing as defer-later or reject-for-current-lane,
4. opening operator notes now would require either widening the compare surface into an authoring surface or introducing a new authoring surface, neither of which is on the bounded Phase 3 design table.

Why not NO-GO:

1. authored review artifacts may have real engineering-review value once writes exist at all, but their first home is unlikely to be the relay lane in isolation.

### Candidate D — Other persisted relay workflow state → defer-later, low-priority

Why defer-later, not implementation-worthy now:

1. persisting recent searches, last-viewed TD-section, or last compare pair is the smallest write candidate but it still requires a mutation lane, an auth model, and provenance,
2. the Phase 2 surface does not depend on this state,
3. the marginal operator ergonomics gain does not justify opening the no-write protection without a separately authored execution packet.

Why not NO-GO:

1. low-stakes UI-state persistence may later be the right minimum-viable opening for relay writes precisely because it carries the smallest authored-content risk.

### Summary Classification

| Candidate | Classification |
| --- | --- |
| A. Saved relay comparisons | defer-later |
| B. Named study workspaces or persisted relay selections | defer-later |
| C. Authored operator notes or reviewable comparison artifacts | defer-later, with strong constraints |
| D. Other persisted relay workflow state | defer-later, low-priority |
| Other write workflows beyond the four above | NO-GO under this memo unless a later packet enumerates them explicitly |

## Truthful Phase 3 Answer

No relay write workflow should open now.

The truthful answer to the bounded Phase 3 question is that:

1. Phase 2 read-only proof has been live for less than one calendar day,
2. there is no documented operator-need evidence supporting any of the four candidates,
3. opening any write candidate now would consume the no-write protection that the post-ladder authority deliberately preserved as the gate between read-only operator value and write-class implementation,
4. all four candidates are defer-later, not implementation-worthy under the current proof state,
5. no candidate is permanently NO-GO under this memo, but no candidate is currently implementation-worthy either.

This memo therefore closes the Phase 3 design question with the explicit decision that no relay write workflow opens from this packet.

## Mutation Boundary Decision For Any Future Survivor

Even though no candidate opens implementation now, the design execution packet requires this memo to fix the exact mutation boundary that any later survivor would adopt. Fixing it now prevents future implementation packets from quietly choosing a wrong lane.

The mutation-boundary decision is:

1. any future relay write workflow MUST land in `apps/mutation-seam/`,
2. it MUST NOT land in `apps/control-plane-api/`, because that lane is explicitly the read-only control-plane surface and conflating reads with mutations would re-open behaviors that the landed ladder protected,
3. it MUST NOT land in `apps/operations-web/` as a browser-direct mutation, because the browser lane already explicitly blocks browser-direct database access and browser-side relay math,
4. it MUST NOT land in `packages/calc-engine/` because the shared calc lane is sourced runtime truth, not authored content,
5. it MUST NOT land in `infra/database/` as a direct DDL or DML extension, because the schema and migration lane is governed separately and may not be widened by a write-workflow packet alone.

Justification:

1. `apps/mutation-seam/` already exists in the post-ladder follow-on planning packet as the named home for governed mutations,
2. that lane carries an explicit boundary, an explicit auth model, and an explicit provenance posture by design,
3. routing a future relay write through `apps/mutation-seam/` keeps the read-only control-plane API contract intact,
4. it also keeps any future relay write subject to the same review and rollback discipline that any other mutation through that lane already obeys.

If a later packet proposes routing relay writes anywhere other than `apps/mutation-seam/`, that packet must explicitly justify the override at the post-ladder follow-on planning level, not at the Phase 3 implementation level.

## Auth Requirements For Any Future Survivor

Any later relay write packet must, at minimum:

1. require authenticated identity using the platform's existing operator authentication path, not a relay-specific bypass,
2. require an explicit relay-write capability flag separate from relay-read,
3. require operator-to-organization scoping so that a relay write cannot cross organization boundaries silently,
4. require server-side enforcement of the capability flag at the mutation seam, not browser-side gating only,
5. forbid token-only or unauthenticated relay writes,
6. forbid widening any existing read-only relay endpoint to accept mutations.

## Review Requirements For Any Future Survivor

Any later relay write packet must, at minimum:

1. emit a structured audit record for each successful and failed write attempt,
2. record the source TD-section identity stamps that were resolved at write time, not after,
3. record the operator identity, organization scope, capability flag, and request signature,
4. preserve the audit record independently of the written object so that deletion of the object does not erase the audit trail,
5. forbid unattributed writes,
6. forbid silent retries that would create duplicate authored objects under different timestamps.

## Rollback Requirements For Any Future Survivor

Any later relay write packet must, at minimum:

1. be append-only at the storage layer, with destructive deletion forbidden,
2. expose supersession or soft-deletion semantics rather than overwrite-in-place,
3. preserve every prior version of any authored content,
4. permit per-write rollback by referencing the supersession history, not by direct mutation of the prior record,
5. forbid bulk destructive rollback that would erase audit history,
6. obey the post-ladder rollback rule that rollback for governance changes does not roll back upstream proof.

## Provenance Requirements For Any Future Survivor

Any later relay write packet must, at minimum:

1. record `td_section_source_id`, `relay_device_source_id`, `family_name`, and `storage_kind` for every TD-section referenced by the written object,
2. record the governed surface fingerprint that was rendered at write time so that later reads can detect divergence,
3. record whether the source TD-section was supported, partially supported, or unsupported at write time, including the governed `unsupported_reason` string when present,
4. distinguish authored content from sourced content in storage and in any later read surface, so that authored prose can never be presented as sourced runtime truth,
5. forbid identity collapse, template substitution, or auto-selection across compare sides,
6. forbid presenting the written object as a recommendation, ranking, or optimizer output.

## Proof Required Before Any Later Implementation Packet Could Open

Before a later execution packet may open implementation for any of the four candidates, all of the following must hold:

1. Phase 2 read-only proof must have been live and unchanged in product behavior for at least a measurable operator-use window, not for one calendar day,
2. concrete operator-need evidence must exist for the specific candidate being opened, not for relay writes in general — at minimum:
   - an authored operator request artifact, or
   - a documented site or project case where the read-only compare surface is provably insufficient and the gap maps to that specific candidate,
3. a separately authored Phase 3 implementation scoping packet must exist and must name the candidate, the mutation seam, and the proof shape,
4. a separately authored Phase 3 implementation execution packet must exist and must restate the auth, review, rollback, and provenance posture from this memo,
5. a `apps/mutation-seam/` lane readiness check must confirm that the seam can accept relay writes without widening any browser-direct database access path,
6. a non-reopen statement must reaffirm that opening writes does not silently reopen browser-side relay math, recommendation, optimizer, or ranking behavior,
7. a no-go restatement must confirm that the deferred non-relay candidates (workspaces, authored notes as approval surfaces, training tabs, site-specific narrative overlays) remain out of scope of the relay lane unless a separately authored authority packet opens them.

If any of those preconditions is missing, the later execution packet must close as blocked rather than as opened.

## Explicitly NO-GO Under This Memo

Independent of any future packet, this memo records that the following remain NO-GO under the current authority stack:

1. relay writes that bypass `apps/mutation-seam/`,
2. browser-side relay math, recommendation, ranking, or optimizer behavior introduced through a write workflow,
3. browser-direct database access introduced through a write workflow,
4. authored content presented as sourced relay runtime truth,
5. write paths that collapse per-side source identity on compare,
6. write paths that hide or simplify unsupported or partially supported state on compare,
7. write paths that reopen the five-tranche relay ladder or default to a Tranche 6 expansion,
8. write paths that import the exploratory compare POC's site-specific narrative or training framing into the relay lane.

## Disposition

The Phase 3 design-authoring slice closes PASS with the explicit decision:

1. no relay write workflow opens from this packet,
2. all four named candidates are classified as defer-later under the current proof state,
3. the mutation boundary for any later survivor is fixed at `apps/mutation-seam/`,
4. auth, review, rollback, and provenance posture is fixed for any later survivor,
5. the preconditions for opening a later implementation packet are explicit.

## Bottom Line

The truthful Phase 3 answer is that the bounded read-only compare proof floor is too new to justify opening any relay write surface.

The right next governance move after this memo is no implementation move at all in the relay lane.

If operator-need evidence later materializes for any of the four named candidates, the path forward is a separately authored Phase 3 implementation scoping packet that obeys the mutation-boundary, auth, review, rollback, and provenance posture fixed here.
