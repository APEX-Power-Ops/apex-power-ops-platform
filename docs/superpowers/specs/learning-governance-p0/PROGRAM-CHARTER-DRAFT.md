# Learning Program Charter - Draft

Status: OPERATOR-DIRECTED DESIGN - NOT YET PROMOTED

## Program Identity

- Program ID: `NETA-ETT-LEARNING`
- Initial bounded cohort: ET-010 through ET-014
- Parked identities: ET-017 / `ET-INS-PD`; ET-028 / `ET-SYS-MTSC`
- Current gate: `ET-PILOT-HOLD`

## Product Intent Decision

Adopt the staged product model. Stage boundaries are real governance gates;
later stages do not inherit authorization from an earlier stage.

### Stage 1: Internal Level II Learning and Readiness Pilot

The first product is named **Internal Level II Learning and Readiness Pilot**.
It is a bounded internal pilot for ET-010 through ET-014 that evaluates:

- whether governed source, rights, SME, content-version, and review controls can
  produce a trustworthy learning product;
- whether the selected learning products are useful and understandable to the
  admitted internal audience;
- whether platform delivery, evidence capture, and feedback can operate within
  an approved identity and privacy boundary; and
- which next bounded learning or field-enablement goal is justified by evidence.

Stage 1 is not a NETA-endorsed product, certification program, internal
qualification, competency determination, or guarantee of examination success.

### Later Stages

1. **Field-performance enablement:** connect accepted learning products to
   bounded work contexts and performance-support needs.
2. **Internal qualification decision:** proceed only after assessment validity,
   SME authority, employment policy, expiry, remediation, and appeal rules are
   independently approved.
3. **Exam-preparation decision:** treat as a distinct product posture with its
   own claims, metrics, rights review, and non-endorsement language.

Each later stage requires a new charter and operator decision.

## Proposed Program Outcome

Operate a governed learning program that can identify bounded needs, acquire
admissible evidence, create versioned content, obtain independent approvals,
release to an authorized audience, measure approved outcomes, and propose the
next goal without self-approval.

## Permitted Program-Management Activity

- backlog intake and deduplication;
- bounded goal drafting;
- dependency and gate sequencing;
- evidence and decision routing;
- status and roadmap maintenance;
- blocker, expiry, and supersession detection;
- recommendation of the next bounded goal.

## Mandatory Human Or Independent Decisions

- business outcome and priority;
- factual source rights and admissibility;
- final SME acceptance;
- learner-data purpose and privacy scope;
- release and withdrawal.

Agent analysis may prepare these decisions, but it cannot substitute for the
named human authority where this charter reserves a human decision.

## Current Holds

- No Slice 2d learner-data write.
- No new source-body inspection.
- No content authoring or rewriting.
- No import, render, deploy, or release.
- No hosted route activation.
- No cohort expansion.

## Authority Appointments And Mechanisms

| Role | Appointment or mechanism | State |
|---|---|---|
| Stakeholder/product owner | Jason Lyle Swenson; operator direction dated 2026-07-14 | appointed |
| Delegated Program Manager | Codex Program Manager role described in `APPOINTMENTS-AND-DELEGATIONS.md` | appointed for program administration; no reserved human authority |
| Primary task executor | Separate Codex instance, assigned by goal charter and permitted to delegate bounded tasks to agents | role established; per-goal identity required |
| Learning Technical Authority | Program-Manager-assigned reviewer identity independent from the executor for the reviewed version | mechanism established; per-goal appointment required |
| Rights/source authority | Jason Lyle Swenson under `APEX-SR-STANDING-2026-07-11` | standing policy authority identified; source-specific decisions remain required |
| SME/reviewer of record | Named appropriately qualified human for each technical content bundle | blocked until named and accepted per goal |
| Instructional-design reviewer | Independent human or delegated review agent, named per goal | mechanism established; assignment required |
| Platform/import owner | Primary executor may implement; operator separately authorizes data, import, environment, and production actions | mechanism established; operational GO required |
| Independent auditor | Separate Codex, Claude, human, or other reviewer that did not author the reviewed version | mechanism established; assignment required |
| Privacy/learner-data authority | Jason Lyle Swenson unless separately delegated in writing | appointed; each collection purpose still requires approval |
| Release authority | Jason Lyle Swenson | appointed; no release is currently authorized |

Role labels alone confer no authority. Every goal must bind the actual human,
Codex session, agent run, or review identity serving each applicable role.
