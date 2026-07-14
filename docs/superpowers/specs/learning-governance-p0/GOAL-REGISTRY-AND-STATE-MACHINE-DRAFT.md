# Goal Registry And State Machine - Draft

Status: PROPOSED DESIGN - NO EXECUTABLE SCHEMA

## Goal Types

`DISCOVER`, `GOVERN`, `ACQUIRE`, `AUTHOR`, `REVIEW`, `REVISE`, `RENDER`,
`IMPORT`, `PILOT`, `MEASURE`, `RELEASE`, and `RETIRE`.

## Minimum Goal Fields

- stable `goal_id` and `program_id`;
- goal type, title, status, priority, and objective;
- exact cohort identity and standards edition;
- authority and delegation references;
- named Program Manager, primary executor, Technical Authority, SME, and auditor
  assignments where applicable;
- exact input paths, object IDs, hashes, and availability states;
- allowed and forbidden actions;
- required gates and decision owners;
- measurable acceptance criteria;
- stop conditions;
- write class and target environment;
- budget, expiry, and freshness policy;
- output/evidence roots;
- next decision owner;
- current checkpoint and required checkpoint reviewer;
- supersession reference where applicable.

## Proposed State Machine

```text
proposed -> triaged -> chartered -> authorized -> in_progress
in_progress -> checkpoint_review -> in_progress
checkpoint_review -> revision_required -> in_progress
checkpoint_review -> verification -> operator_review
operator_review -> accepted -> promotion_ready -> released -> measured -> closed
```

Side states: `held`, `blocked`, `rejected`, `superseded`, `expired`, and
`withdrawn`.

Transitions are append-only decisions. Historical states are not overwritten.

## Automatic Continuation

Continuation is permitted only when the next task is already admitted, has the
same or lower write class, uses unchanged inputs/cohort/environment, requires no
new authority, remains within budget and expiry, and keeps the checker green.

The primary executor may continue between checkpoints within an authorized goal.
It may not authorize a new goal, change the cohort, waive a failed gate, assign
itself as independent reviewer, or cross a checkpoint reserved for the Program
Manager or operator.

Any rights, SME, learner-data, import, render, release, production, scope, or
environment decision stops execution.

The checkpoint sequence and handoff requirements are defined in
`CONTINUOUS-GOAL-LOOP.md`.

## Initial Goal Migration

The first migrated goal will represent the Level II G2 hold. Migration must not
change its state, target set, evidence status, or required owner returns.
