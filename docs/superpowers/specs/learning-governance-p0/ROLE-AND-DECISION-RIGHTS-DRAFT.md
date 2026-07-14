# Learning Role And Decision Rights - Draft

Status: PROPOSED

## Separation Rule

No executor may simultaneously serve as author, final SME, independent auditor,
and release authority for the same artifact. Delegation must be explicit,
versioned, scoped, and time-bounded.

## Proposed Rights Matrix

| Decision | Program Manager | Technical Authority | Stakeholder | Rights | SME | Platform | Auditor | Release |
|---|---|---|---|---|---|---|---|---|
| Backlog priority | propose | consult | approve | consult | consult | consult | observe | consult |
| Goal charter | draft/administer | approve technical boundary | approve outcome/scope | approve rights work | approve SME work | approve platform work | verify | consult |
| Source admissibility | route | consult | informed | approve | consult | informed | verify evidence | informed |
| Technical content | coordinate | enforce rubric | informed | consult | approve | informed | verify | informed |
| Schema/import contract | coordinate | approve | informed | informed | consult | implement/approve operation | verify | informed |
| Learner-data collection | coordinate | approve contract | approve purpose | informed | consult | implement | verify | informed |
| Release | recommend | technical signoff | approve or delegate | sign off | sign off | readiness signoff | audit | approve/execute |
| Roadmap change | draft | assess impact | approve priority | consult | consult | consult | verify | consult |

## Agent Boundary

An agent may administer a delegated Program Manager or Technical Authority role
for design and technical validation when an appointment permits it. An agent may
not fabricate or substitute for:

- source rights;
- business priority;
- external SME credentials or final acceptance;
- learner consent or privacy authority;
- release approval.

## Decision Record Requirements

Every accepted decision must name the decision owner, authority reference,
reviewed object/version, evidence references, conditions, timestamp, expiry or
re-review trigger, and disposition.
