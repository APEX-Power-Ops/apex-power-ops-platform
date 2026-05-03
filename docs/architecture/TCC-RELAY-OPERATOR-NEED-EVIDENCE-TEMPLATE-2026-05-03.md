# TCC Relay Operator-Need Evidence Template

Date: 2026-05-03
Status: Reusable evidence template
Scope: Capture candidate-specific operator-need evidence in a form that can support a later Phase 3 implementation scoping packet without reopening the relay lane prematurely

## Purpose

The closed Phase 3 relay design memo requires concrete operator-need evidence before any later relay write packet may open.

That evidence must be specific to one deferred candidate, not to relay writes in general.

This template exists to capture that evidence in a governed, reusable shape.

This template does not reopen implementation.

It does not authorize a packet by itself.

## Governing Standard

Use this template only after all of the following are true:

1. the Phase 2 read-only compare slice has been live for a measurable operator-use window,
2. the evidence comes from real operator usage of the governed compare surface,
3. the gap maps to one specific deferred candidate,
4. the evidence is strong enough to justify a later Phase 3 implementation scoping discussion.

The allowed candidate set is currently limited to:

1. saved relay comparisons,
2. named study workspaces or persisted relay selections,
3. authored operator notes or reviewable comparison artifacts,
4. other persisted relay workflow state.

## Minimum Acceptance Standard

An evidence artifact using this template should contain all of the following:

1. operator role or cohort,
2. project or site context,
3. the exact governed read-only surface used,
4. the exact deferred candidate being requested,
5. the concrete task the operator could not complete,
6. the exact workaround used today,
7. the operational cost or risk of that workaround,
8. why the current read-only compare surface is insufficient,
9. why the gap maps to this candidate and not a broader platform feature,
10. explicit confirmation that the request is not asking to reopen browser-side relay math, recommendation, ranking, optimizer behavior, or browser-direct database access.

If any of those items is missing, the evidence should be treated as incomplete.

## Copy-Paste Template

Use the following structure for a future evidence note.

```text
# TCC Relay Operator-Need Evidence - [Candidate Name]

Date:
Status: Draft operator-need evidence
Scope: Candidate-specific evidence only; does not open implementation

## Operator Context

1. Operator role or cohort:
2. Organization or project:
3. Site or lineup context:
4. Approximate usage window:

## Governing Surface Used

1. Promoted host or governed browser surface used:
2. Exact compare workflow performed:
3. Whether the operator had stdlib access: yes or no

## Requested Candidate

Candidate requested:

1. saved relay comparisons, or
2. named study workspaces or persisted relay selections, or
3. authored operator notes or reviewable comparison artifacts, or
4. other persisted relay workflow state.

## Concrete Failure In Current Read-Only Use

Describe the exact task the operator could not complete with the current compare surface.

Required details:

1. what the operator was trying to do,
2. why the read-only compare surface was insufficient,
3. whether the failure happened once or repeatedly,
4. whether it blocked field execution, review, or handoff.

## Current Workaround

Describe the actual workaround being used now.

Examples:

1. screenshots,
2. manual re-search and re-selection,
3. sidecar notes outside the governed surface,
4. verbal or email handoff,
5. engineer-mediated stdlib lookup.

## Operational Cost Or Risk

Record the real cost or risk created by the workaround.

Examples:

1. repeated manual reconstruction,
2. loss of continuity across shifts,
3. risk of comparing the wrong pair,
4. review delay,
5. inability for technicians without stdlib access to complete the intended workflow.

## Candidate Mapping

State clearly why this evidence maps to the named candidate and not to a broader or different feature.

Required statement:

1. this evidence supports [candidate name] specifically because [...]

## Explicit Non-Requests

State clearly what this evidence is not requesting.

At minimum:

1. no browser-side relay math,
2. no recommendation, ranking, or optimizer behavior,
3. no browser-direct database access,
4. no silent reopening of the Phase 2 browser implementation lane,
5. no broader platform workspace or approval surface unless separately authorized.

## Recommendation

Use one of these outcomes only:

1. sufficient to discuss a Phase 3 implementation scoping packet for [candidate name], or
2. informative but not yet sufficient to reopen the lane.
```

## Quality Bar Notes

The strongest evidence usually has these properties:

1. tied to a real technician, engineer, or reviewer workflow,
2. tied to a real site or project,
3. tied to repeated usage or a real blocked handoff,
4. narrow enough to map to one candidate,
5. explicit about what remains out of scope.

Weak evidence usually looks like this:

1. generic interest in writes,
2. broad statements that technicians do not have stdlib access without naming the missing task,
3. requests that collapse saved comparisons, workspaces, notes, and approvals into one blended ask,
4. requests that implicitly reopen forbidden behaviors.

## Bottom Line

Use this template to capture a real operator workflow gap in the governed compare surface.

Do not use it to reopen the relay lane by implication.

Only a later Phase 3 implementation scoping packet can do that.