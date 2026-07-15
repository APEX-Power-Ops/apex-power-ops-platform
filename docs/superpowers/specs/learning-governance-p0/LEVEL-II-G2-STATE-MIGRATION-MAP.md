# Level II G2 Held-State Migration Map

Status: PROPOSED DESIGN - MIGRATION NOT EXECUTED

## Invariant State

- Goal state: `ET-PILOT-HOLD`
- Active targets: ET-010, ET-011, ET-012, ET-013, ET-014
- Parked: ET-017 / `ET-INS-PD`; ET-028 / `ET-SYS-MTSC`
- Authoring: not admitted
- Import/render/release: not admitted
- Learner-data and platform writes: not admitted

## Control Inputs To Reconcile

1. `2026-07-09-level-ii-electrical-theory-g0-next-goal-loop-prompt.md`
2. `2026-07-09-level-ii-electrical-theory-g1-revise-goal-loop-prompt.md`
3. `2026-07-09-level-ii-electrical-theory-g2-hold-operator-decision-prompt.md`
4. `2026-07-10-level-ii-electrical-theory-delegated-authority-requirements-admin-prompt.md`
5. `2026-07-10-level-ii-electrical-theory-g2-hold-owner-return-intake-prompt.md`

These files currently live in an untracked retained worktree. Their claims must
be verified against the referenced external artifacts before migration.

## Metadata To Migrate

- exact target identities and edition;
- artifact locators, hashes, and availability states;
- Stage 0, Stage 1, G1, and G2 reported decisions;
- five historical owner-return tracks plus the current learner identity/privacy
  gate;
- delegation references and limitations;
- blockers, stop conditions, and next decision owner;
- parked-target state.

## Metadata Not To Migrate As Authority

- learner-facing or source-body prose;
- unverified artifact claims;
- inferred rights or SME acceptance;
- recommendation text as an accepted decision;
- agent-authored final approvals;
- any implicit clearing of the hold.

## Current Readiness Tracks

1. Rights/source authority: standing policy owner identified; source-specific
   admissibility remains partial and does not clear the hold.
2. Named SME and acceptance criteria.
3. Platform/import mapping.
4. Render-package requirements.
5. Release authority.
6. Learner identity, data purpose, privacy, retention, and access authority.

Missing or partial returns on any of the six tracks preserve the hold. The sixth
track is a current governance requirement and must not be omitted merely because
the older prompt trail named five owner returns.

The staged product decision names this cohort's intended first product
**Internal Level II Learning and Readiness Pilot**. Naming the product does not
change the goal state or admit authoring.

## Migration Acceptance

The later migration must be idempotent, metadata-only, hash-bound, independently
reviewed, and prove before/after equality of goal state and exact cohort.
