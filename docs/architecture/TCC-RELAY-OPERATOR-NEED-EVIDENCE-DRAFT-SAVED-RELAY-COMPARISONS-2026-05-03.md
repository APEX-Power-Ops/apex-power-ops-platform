# TCC Relay Operator-Need Evidence Draft - Saved Relay Comparisons

Date: 2026-05-03
Status: Draft candidate-specific evidence artifact
Scope: Draft operator-need evidence for Candidate A only; does not reopen implementation or authorize a packet by itself

## Purpose

This draft converts the currently stated operator rationale into a candidate-specific evidence note.

It is intentionally narrow.

It exists to show the shape of acceptable evidence for the smallest plausible Phase 3 survivor: saved relay comparisons.

This draft is not yet treated as sufficient reopening proof by itself.

## Candidate Requested

Candidate A: saved relay comparisons.

Requested behavior in bounded form:

1. allow a governed compare pair to be intentionally preserved,
2. allow that same compare pair to be reopened later without requiring a fresh manual rebuild,
3. keep the request limited to saved relay comparisons rather than workspaces, approvals, or authored narrative.

## Operator Context

Current stated operator rationale:

1. technicians will need this browser-based relay ability,
2. those technicians will not have direct stdlib access,
3. the governed compare surface therefore becomes their relay-comparison entry point rather than a supplemental surface.

Role framing used by this draft:

1. field technician or technician-adjacent relay user,
2. working from the governed Phase 2 compare surface,
3. lacking direct access to stdlib for repeated lookup or compare reconstruction.

## Governing Surface Used

The relevant governed surface is the Phase 2 read-only relay compare slice on the promoted host.

This draft assumes the workflow uses the existing compare surface rather than stdlib and asks what happens when the same compare must be revisited later.

## Concrete Failure In Current Read-Only Use

The draft evidence claim is:

1. a technician without stdlib access can use the governed browser compare to inspect a relay pair,
2. but if that same technician needs to revisit the exact same pair later, the current read-only surface does not preserve the pair for recall,
3. the technician must manually reconstruct the compare by re-finding the same source pair,
4. that reconstruction burden falls specifically on the cohort that lacks stdlib access.

In bounded form, the insufficiency is not that the compare surface is unavailable.

The insufficiency is that the compare surface cannot intentionally retain and later reopen a previously chosen pair for the same technician workflow.

## Current Workaround

The likely current workaround, expressed in draft form, is:

1. the technician captures screenshots or external notes,
2. or the technician repeats manual search and explicit re-selection of the same compare pair,
3. or the technician relies on an engineer with stdlib access to reconstruct the same comparison outside the governed browser surface.

This draft should be replaced later with the exact real workaround observed in field use.

## Operational Cost Or Risk

The claimed operational cost in this draft is:

1. repeated manual reconstruction of the same compare pair,
2. higher risk of selecting the wrong relay pair on re-entry,
3. reduced continuity across shifts or follow-up review,
4. extra dependence on stdlib-capable personnel even though the governed browser compare exists specifically to broaden access.

The strongest version of this draft would later replace those claims with a real site or project example.

## Candidate Mapping

This draft maps to Candidate A specifically because:

1. the core need is persistence of one intentionally chosen compare pair,
2. it does not require a multi-comparison workspace container,
3. it does not require authored notes, approvals, or narrative artifacts,
4. it does not require broader persisted operator state beyond preserving and reopening a chosen compare.

This draft therefore supports saved relay comparisons, not relay writes in general.

## Explicit Non-Requests

This draft does not request:

1. named study workspaces,
2. authored operator notes,
3. review or approval artifacts,
4. browser-side relay math,
5. recommendation, ranking, or optimizer behavior,
6. browser-direct database access,
7. silent reopening of the Phase 2 browser implementation lane beyond the saved-comparison candidate.

## Evidence Gaps Still Remaining

This draft is intentionally not treated as final reopening proof because it still lacks:

1. a measurable operator-use window for the live Phase 2 compare surface,
2. a dated operator request artifact from a real technician workflow,
3. a documented site or project case showing the exact compare pair that had to be reconstructed,
4. a confirmed real-world workaround and its concrete cost,
5. confirmation that the need is repeated enough to justify opening a scoped write discussion.

## Recommended Next Collection Step

To convert this draft into stronger evidence, capture one real operator-use case in this shape:

1. technician role,
2. site or project name,
3. the exact two-sided compare task performed,
4. the exact moment where the technician needed to reopen the same pair later,
5. the exact workaround used,
6. the specific cost or risk created by that workaround.

## Recommendation

Current recommendation:

1. treat this document as a draft evidence note only,
2. use it to guide collection of a real operator request artifact,
3. if real field use later confirms the same gap, use that evidence to support a separately authored Phase 3 implementation scoping packet for Candidate A only.

## Bottom Line

The technician-without-stdlib rationale is most credibly shaped as evidence for saved relay comparisons, not for relay writes in general.

This draft captures that mapping in governed form.

It does not yet reopen the lane.