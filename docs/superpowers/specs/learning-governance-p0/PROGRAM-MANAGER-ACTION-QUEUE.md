# Learning Program Manager Action Queue

Date: 2026-07-14

Status: CP5 SYNTHESIS COMPLETE - OPERATOR CP6 DECISION REQUIRED

## Program Manager Assessment

The program can make substantial progress without source-body access, content
authoring, learner-data activity, database access, import, render, deployment,
or release. The critical path is governance and authority, not content volume.

The next useful work is divided into one serial control-plane path and several
parallel owner-return paths.

## Critical Path

| Order | Goal | Why it is next | Entry condition |
|---:|---|---|---|
| 1 | Finish `LEARN-GOV-P0-001` | Establishes the authority and checkpoint contract for every later goal | Operator CP6 decision |
| 2 | `LEARN-GOV-P1-CHECKER-001` | Makes goal, role, evidence, transition, and hold rules machine-enforced | Accepted P0 design; separate offline implementation GO |
| 3 | Canonical held-state migration | Moves the exact Level II state into the checked registry without changing it | Checker green; metadata-only migration GO |
| 4 | Owner-return convergence | Completes rights, SME, platform, render, release, and privacy tracks | Separate goals and named decision owners |
| 5 | Authoring admission | Admits the smallest coherent Stage-1 content tranche | Every applicable track accepted and current |

## Work That Can Proceed In Parallel After P0 Acceptance

### A. Rights Decision Preparation

Goal: `LEARN-RIGHTS-DECISIONS-001`.

Permitted work:

- bind the 12 source-register rows to the current snapshot;
- prepare one decision packet per materially different source/use;
- identify missing lawful-access, license, owner, edition, and intended-use
  evidence;
- recommend `accepted_reference_only`, `conditional`, `candidate`, `replace`, or
  `prohibited`; and
- route the packets to Jason as rights authority.

Unlock conditions:

- For the five Kuphaldt PDF rows, produce lawful-access provenance or replace the
  source with a rights-clear alternative.
- For the two OpenStax rows, revalidate official terms and intended reference-only
  use, then obtain a version-bound rights decision.
- Keep all five derived-hold rows blocked unless their provenance is resolved.

No source body or learner-facing use is admitted by this work.

### B. SME Appointment And Rubric

Goal: `LEARN-SME-APPOINTMENT-001`.

Permitted work:

- define minimum qualifications and conflict rules;
- define the exact technical/safety review rubric;
- define version binding, dispositions, expiry, and re-review triggers;
- prepare the appointment and reviewer-of-record forms; and
- create an SME review queue for ET-010..014.

Unlock condition: the stakeholder must name a qualified human SME or approved
candidate pool. Agent review cannot satisfy this gate.

### C. Content And Assessment Bundle Design

Goal: `LEARN-CONTENT-BUNDLE-001`.

Permitted work:

- design source, claim, citation, content-version, question-version, mapping,
  review, release, and supersession records;
- define separate exposure, practice, assessment, proficiency, and qualification
  states; and
- define prospective validation without migrating or editing current content.

Unlock condition: Technical Authority and rights/platform review of the design.

### D. Identity, Privacy, And Learner-Data Design

Goal: `LEARN-IDENTITY-AUTH-001`.

Permitted work:

- design verified actor and learner identity linkage;
- define learner, manager, SME, administrator, and auditor capabilities;
- define data purpose, retention, correction, de-identification, and access; and
- define negative-auth and end-to-end acceptance requirements.

Unlock condition: stakeholder/privacy-authority approval of audience, purpose,
retention, and access policy. No live route or learner data is needed for design.

### E. Slice 2d Contract Reconciliation

Goal: `LEARN-SLICE2D-CONTRACT-001`.

Permitted work:

- inventory every `ksa_mapped` reference in the repository;
- specify KSA mapping as content/model evidence unless a contrary business need
  is approved;
- align the proposed runbook, CLI, database, API, tests, and evidence semantics;
  and
- design negative and end-to-end tests.

Unlock condition: separate design GO and Technical Authority review. No event
write or rehearsal is admitted.

### F. Platform, Render, And Release Requirements

Permitted work:

- map accepted metadata to proposed `knowledge`, `learning`, identity, and audit
  domains without SQL;
- define immutable import and rollback manifests;
- define module, quick-reference, worked-example, practice, diagram, and
  interactive containers without populating learner content;
- define accessibility and render acceptance; and
- define the internal-only release audience, withdrawal, and non-endorsement
  contract.

Unlock conditions: separate design goals and the appropriate Technical
Authority, platform, privacy, and release-owner decisions.

## Operator Inputs That Unlock The Most Work

1. CP6 acceptance or revision of the P0 governance design.
2. A named qualified SME or candidate pool for Stage 1.
3. Confirmation of the initial internal learner audience and proposed pilot size.
4. Rights evidence for the Kuphaldt source or approval to replace it.
5. Approval to prepare the offline P1 checker under a separate goal.
6. Approval to run the rights and SME packets in parallel after P0 acceptance.

## Work Still Prohibited

- opening learning source bodies not admitted by a goal;
- learner-facing content or assessment authoring;
- treating `REFERENCE_ONLY` as permission to copy or closely paraphrase;
- learner-data reads or writes;
- the Slice 2d rehearsal;
- database, API, import, render, hosted activation, deployment, or release;
- expanding beyond ET-010..014; and
- activating ET-017 or ET-028.

## Recommended Sequencing Decision

Issue the P0 CP6 decision. On acceptance, authorize the offline checker as the
primary executor's first implementation goal. In parallel, authorize the
metadata-only rights decision packet and the SME appointment/rubric packet.
Those three paths remove the largest governance blockers without exposing
learners, source bodies, or production systems.
