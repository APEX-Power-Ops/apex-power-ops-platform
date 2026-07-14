# Goal LEARN-GOV-P1-CHECKER-001

Status: PROPOSED - NOT AUTHORIZED

## Objective

Implement an offline, deterministic control plane for learning goals,
appointments, evidence references, decisions, checkpoints, transitions, and the
roadmap. Preserve the held Level II state exactly.

## Entry Gates

- P0 design accepted at CP6 by `LEARN-GOV-P0-CP6-2026-07-14`;
- exact P0 commit pinned;
- separate Codex primary executor assigned;
- independent Technical Authority and auditor assigned; and
- separate implementation GO issued.

## Allowed

- create schemas, fixtures, validators, and offline tests under approved
  repository roots;
- encode the required negative tests from the P0 checker design;
- create faithfully held ET-010..014 fixtures; and
- run local offline tests and linting.

## Forbidden

- source-body or learner-content work;
- learner-data, database, API, browser, or external-system access;
- import, render, deploy, release, or production work;
- changing the Level II cohort or hold state; and
- using a positive fixture to imply source, SME, privacy, or release acceptance.

## Acceptance

- schema and semantic checker fail closed;
- Program Manager, executor, and reviewer identities cannot collapse;
- every negative case enumerated by the accepted P0 checker design has an
  adversarial test (28 cases in this design revision);
- state transitions and checkpoint owners are enforced;
- living evidence cannot satisfy a decision without immutable binding;
- the held Level II fixture remains set-equal before and after migration; and
- full branch review finds no unresolved high-severity false-green path.

## Next Decision

Separate operator CP1 authorization. This proposal is permitted but not
authorized by the P0 CP6 decision.
