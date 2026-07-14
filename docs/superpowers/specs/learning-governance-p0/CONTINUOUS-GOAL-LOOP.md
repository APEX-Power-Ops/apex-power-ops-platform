# Continuous Learning Goal Loop

Status: OPERATOR-DIRECTED DESIGN - NO AUTOMATION IMPLEMENTED

## Objective

Provide a resumable loop in which a delegated Program Manager can intake,
charter, assign, review, and close bounded learning goals while a separate Codex
instance executes admitted work. The loop may continue automatically only
between already-approved checkpoints.

## Loop

```text
intake
  -> CP0 program-manager triage
  -> CP1 charter and operator authorization
  -> CP2 evidence and authority readiness
  -> bounded execution
  -> CP3 program-manager progress review
  -> independent verification
  -> CP4 technical-authority and audit review
  -> CP5 program-manager synthesis
  -> CP6 operator decision
  -> CP7 closeout and next-goal proposal
  -> intake
```

The arrow from `CP7` to `intake` creates a new proposal only. It does not
authorize the proposed goal.

## Checkpoints

### CP0: Program Manager Triage

The Program Manager confirms the request belongs to the program, deduplicates it,
identifies the intended product stage, and recommends disposition. No executor
work begins.

Required output: proposed goal ID, objective, cohort, expected value, risks, and
recommended next owner.

### CP1: Charter And Authorization

The Program Manager drafts the exact goal charter. The stakeholder or operator
approves outcome, scope, budget, and any reserved action. The Program Manager
appoints the primary executor and review roles.

Required output: accepted goal charter and exact GO. A template or recommended GO
does not authorize execution.

### CP2: Evidence And Authority Readiness

The primary executor inventories inputs without crossing forbidden content or
system boundaries. The Program Manager checks that evidence, appointments,
rights state, SME path, and output roots are sufficient for the admitted work.

Required output: readiness scorecard. Unknown or conflicting evidence blocks the
affected work.

### CP3: Program Manager Progress Review

Occurs after each bounded tranche, material design decision, or 3-5 target
micro-cluster. The Program Manager checks scope, quality, evidence binding,
agent ownership, and remaining budget.

Disposition: continue, revise, narrow, hold, cancel, or escalate to the operator.

### CP4: Technical Authority And Independent Audit

Reviewers who did not author the reviewed version test specification fidelity,
technical correctness, false-green paths, and integration reality. Human SME
review is separately required for technical learner-facing content.

Required output: findings-first review record, dispositions, and exact reviewed
version.

### CP5: Program Manager Synthesis

The Program Manager reconciles findings, verifies required fixes, checks role
separation, and recommends an operator disposition. The Program Manager cannot
convert unresolved reserved decisions into acceptance.

### CP6: Operator Decision

The operator accepts, accepts with conditions, requires revision, holds, rejects,
or authorizes a separately gated promotion action. Rights, privacy, production,
release, and material scope decisions occur here or in a more specific operator
gate.

### CP7: Closeout And Next-Goal Proposal

The Program Manager records final state, outputs, decisions, residual risks,
supersession, and a proposed next bounded goal. The executor stops.

## Automatic Continuation Rules

The executor may continue without another operator message only when all of
these are true:

- CP1 admitted the next task explicitly;
- the Program Manager has not imposed an intervening checkpoint;
- inputs, cohort, edition, environment, and output roots are unchanged;
- the task has the same or lower write class;
- no new rights, SME, privacy, import, render, release, or production authority
  is required;
- no failed or stale evidence gate exists;
- the assigned executor and reviewer separation remains valid; and
- budget and expiry remain valid.

Failure of any condition returns the goal to a checkpoint. Silence never means
continue.

## Continuous Program Manager Review

The Program Manager maintains a current queue and reviews:

- every new intake at CP0;
- every goal before execution at CP1;
- every evidence boundary at CP2;
- each bounded tranche at CP3;
- every independent review at CP4;
- every acceptance recommendation at CP5; and
- every closeout and next-goal proposal at CP7.

The operator reviews CP1 and CP6 whenever the goal includes a reserved decision.

## Resumption After Interruption

On resumption, do not infer state from chat. Re-read the goal record, latest
checkpoint, decision records, branch state, and evidence hashes. If they disagree,
hold the goal and ask the Program Manager to reconcile the canonical state.
