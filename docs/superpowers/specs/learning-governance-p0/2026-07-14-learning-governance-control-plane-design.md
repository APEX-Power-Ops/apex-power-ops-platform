# Learning Governance Control Plane Design

Date: 2026-07-14

Status: OPERATOR-DIRECTED DESIGN - IMPLEMENTATION NOT RATIFIED

## Objective

Define a tracked, machine-checkable learning governance control plane that can
administer bounded continuous goals without allowing an executor to approve its
own rights, technical correctness, business priority, learner-data use, or
release.

## Current State Preserved

- Learning packages are a development prototype, not a governed hosted product.
- The Slice 2d rehearsal is held because `ksa_mapped` is not part of the accepted
  event vocabulary implemented by the package, database, API, and tests.
- Hosted learning activation is held pending verified identity, authorization,
  and privacy contracts.
- The Level II pilot remains `ET-PILOT-HOLD` for ET-010 through ET-014.
- ET-017 / `ET-INS-PD` and ET-028 / `ET-SYS-MTSC` remain parked.
- Existing untracked notes and external workrepo artifacts are evidence inputs,
  not canonical gate state.
- The Windows Box tree is reachable from Olares through the verified read-only
  mapping in `SOURCE-ACCESS-AND-CUSTODY-MAP.md`; reachability does not authorize
  source-body access or resolve any source-specific gate.

## Proposed Control Plane

The later implementation packet may propose these tracked surfaces:

```text
docs/learning/governance/
  PROGRAM-CHARTER.md
  ROLE-AND-DECISION-RIGHTS.md
  CONTENT-AND-ASSESSMENT-LIFECYCLE.md
  DELEGATION-POLICY.md
  PRIMARY-EXECUTOR-INSTRUCTIONS.md
  CONTINUOUS-GOAL-LOOP.md

ops/learning/goals/
  GOAL-REGISTRY.yaml
  schema/goal.schema.json
  check_goals.py
  active/
  archive/

ops/learning/roadmap/
  ROADMAP.yaml
  BACKLOG.yaml

ops/learning/decisions/<goal-id>/
ops/learning/evidence/manifests/
ops/learning/checkpoints/<goal-id>/
knowledge/learning/release-manifests/
knowledge/learning/mappings/
```

These paths are design targets only. This packet does not create or activate
them.

## Design Workstreams

1. Ratify program purpose, target audience, and measurable outcomes.
2. Define human and delegated roles, appointments, expiry, and conflicts.
3. Define the canonical goal object and state-transition contract.
4. Separate immutable evidence from authority decisions.
5. Define automatic-continuation limits and mandatory stop conditions.
6. Define an offline checker and adversarial negative-test contract.
7. Map the existing Level II prompt trail into held structured state.
8. Define the separately gated Slice 2d reconciliation packet.

## Operator Decisions Recorded In This Revision

- Product intent is the staged model, beginning with **Internal Level II
  Learning and Readiness Pilot**.
- Jason Lyle Swenson is stakeholder/product owner, standing rights-policy
  authority, privacy authority unless separately delegated, and release
  authority.
- A delegated Codex Program Manager administers goals, assignments, evidence
  routing, checkpoints, and roadmap recommendations within this charter.
- A separate Codex instance serves as primary task executor and may delegate
  bounded work to agents.
- Technical Authority and independent audit roles must be assigned to identities
  that did not author the reviewed version.
- The Program Manager may coordinate all roles but may not synthesize agent work
  into human rights, SME, privacy-purpose, business-priority, or release approval.

## Decisions Still Required Per Goal

- exact executor and reviewer identities;
- a named qualified SME and content-version-bound acceptance;
- source-specific rights decisions under the standing policy;
- learner-data purpose and privacy conditions;
- import, environment, deployment, and release authorization.

Unknown per-goal appointments remain explicit blockers; they do not inherit from
agent execution roles.

## Acceptance For This Design Packet

- Every proposed role has explicit allowed and forbidden decisions.
- Goal identity, scope, cohort, inputs, evidence, gates, and expiry are defined.
- Evidence and decisions bind to exact versions and hashes.
- Automatic continuation cannot cross a human, write, environment, or scope gate.
- The Level II migration map preserves its hold and exact target set.
- The checker design includes false-green and self-approval negative cases.
- Slice 2d reconciliation remains a separate no-live-write follow-up.
- Cross-engine review finds no unresolved high-severity design contradiction.

## Stop Condition

Stop after operator and cross-engine review. Implementation, content work, and
external evidence intake require separate authorization.
