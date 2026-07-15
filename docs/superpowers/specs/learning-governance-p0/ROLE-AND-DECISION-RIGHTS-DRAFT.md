# Learning Role And Decision Rights - Draft

Status: OPERATOR-DIRECTED DESIGN - NOT YET ENFORCED

## Separation Rule

No executor may approve its own work as Technical Authority, final SME,
independent auditor, rights authority, or release authority for the same
artifact version. Delegation must be explicit, versioned, scoped, and bounded to
a goal or review period.

## Proposed Rights Matrix

| Decision | Program Manager | Primary executor | Technical Authority | Stakeholder | Rights | SME | Platform | Auditor | Release |
|---|---|---|---|---|---|---|---|---|---|
| Backlog priority | propose/administer | provide estimates | assess feasibility | approve | consult | consult | consult | observe | consult |
| Goal charter | draft/administer | validate executability | approve technical boundary | approve outcome/scope | approve rights work | approve SME work | approve platform boundary | verify | consult |
| Source admissibility | route/check completeness | collect permitted metadata | consult | informed | approve | consult | informed | verify evidence binding | informed |
| Technical content | coordinate/check gates | author or revise when admitted | enforce rubric/sign off | informed | consult | approve final technical content | informed | verify independence/evidence | informed |
| Schema/import contract | coordinate | implement when admitted | approve contract | informed | informed | consult | approve operation or request GO | verify | informed |
| Learner-data collection | coordinate | implement when admitted | approve technical contract | approve purpose | informed | consult | approve operation or request GO | verify | informed |
| Checkpoint advancement | approve within admitted goal | recommend with evidence | approve technical checkpoint when required | reserved decisions only | reserved decisions only | reserved decisions only | operational decisions only | verify | reserved decisions only |
| Release | recommend | prepare immutable candidate | technical signoff | approve product posture | sign off | sign off | readiness signoff | audit | approve/execute |
| Roadmap change | draft/administer | propose | assess impact | approve priority | consult | consult | consult | verify | consult |

## Agent Boundary

The delegated Program Manager may assign a separate Codex instance as primary
executor and may assign bounded agents as implementers, analysts, test authors,
or reviewers. An agent may administer a Technical Authority or independent
audit role only when it did not author the reviewed version and the goal charter
names the assignment. An agent may not fabricate or substitute for:

- source rights;
- business priority;
- external SME credentials or final acceptance;
- learner consent or privacy authority;
- release approval.

Agent and model outputs are evidence inputs. They become decisions only when the
decision owner named by this matrix accepts them in a version-bound record.

## Decision Record Requirements

Every accepted decision must name the decision owner, authority reference,
reviewed object/version, evidence references, conditions, timestamp, expiry or
re-review trigger, and disposition.

For agent roles, the record must also include the executor or reviewer run ID,
model/tool identity when available, branch/commit, and whether the identity
authored the reviewed version.
