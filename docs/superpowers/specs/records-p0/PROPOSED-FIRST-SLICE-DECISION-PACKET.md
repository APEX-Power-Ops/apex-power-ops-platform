# Proposed First Records Slice — Operator Decision Packet

Status: **HELD — DECISION SUPPORT ONLY**
Goal: RECORDS-P0-AUTHORITY-AND-P1-ADMISSION-FRAMEWORK-001
Candidate: RECORDS-FIRST-SLICE-2026-07
Candidate kind: real
Decision status: proposed
Execution authorized: false
Implementation readiness: held
Recommendation status: proposed, not selected, not ratified
Selected candidate: none

## 1. Decision requested

Choose whether one of the three bounded candidates below should become the first
Records field-product acceptance slice, and resolve the eleven authority
questions in Section 6. This packet does not authorize implementation.

All three options use the same acceptance contract: one office user,
technician, project, apparatus, pinned template, offline capture, reconnect,
governed review, acceptance decision, and immutable evidence readback. Candidate
selection changes only the apparatus/template burden, not the proof standard.

## 2. Candidate comparison

| Candidate | State | Apparatus and template | Capture mode | Relative breadth | Strongest reason | Primary decision risks |
|---|---|---|---|---|---|---|
| RFS-GROUNDING | proposed; execution_authorized=false | grounding_system with ats_grounding_v1 | field entry | smallest; about 8 sections and 6 ATS groupings | Narrowest end-to-end field proof with meaningful measured values | acceptance method, IEEE 81 or manufacturer authority, attachments, standards-derived content posture |
| RFS-LV-CB | proposed; execution_authorized=false | cb_lv with ats_lv_cb_v1 | field entry | medium; about 11 sections | Representative inspection plus electrical and mechanical test workflow | selector and TCC dependencies, broader validation, settings and trip-data authority |
| RFS-DRY-XFMR | proposed; execution_authorized=false | small two-winding xfmr_dry with ats_dry_xfmr_v1 | field entry | widest; about 13 sections and 35 ATS groupings | Richest proof of mixed values, units, nameplate data, and evidence | much larger value surface, winding/configuration variants, acceptance-source complexity |

No candidate is accepted. The table is decision support, not a scoring model or
automatic selection.

## 3. Proposed recommendation

**Recommend RFS-GROUNDING for human decision.**

Reason: it is the smallest grounded slice that still exercises provisioning,
offline measurement capture, unit and range validation, reconnect,
idempotency, governed review, acceptance, and evidence readback. It minimizes
template breadth while preserving the hard product-path proof.

This recommendation does not ratify the template, its acceptance sources, its
content-use posture, or its implementation. It remains:

- decision_status = proposed
- execution_authorized = false
- selected = false

A named human authority must resolve REC-D009 and all other blocking decisions
before any implementation proposal can become ready.

## 4. Immutable candidate sources

### RFS-GROUNDING

- Source: reference/records/10-GROUNDING-DATASHEET-SPEC.md
- Git blob: f461df75e559b4256944d5c2f27885f56fc581b2
- SHA-256: af55fa3266bb7da32b022b18e1b1f8fd9758e46833913c96bd43ee4055edb339
- Proposed apparatus key: grounding_system
- Proposed template key: ats_grounding_v1
- Proposed capture mode: field entry

Required human review must confirm applicable method, source authority,
tolerances, unit behavior, environmental inputs, attachment policy, and
customer-visible content.

### RFS-LV-CB

- Source: reference/records/04-LV-CB-DATASHEET-SPEC.md
- Git blob: a18ac8a19f77df5b924112575aca8e924543edf6
- SHA-256: 2d3fb3a34d7e231f4ba5d42060a780f37c9c4c17b8cfb9e64e837d1dc806478f
- Proposed apparatus key: cb_lv
- Proposed template key: ats_lv_cb_v1
- Proposed capture mode: field entry

Required human review must settle selector data, protection/TCC authority,
settings provenance, trip-test interpretation, option sets, and evidence
attachments before implementation.

### RFS-DRY-XFMR

- Source: reference/records/06-TRANSFORMER-DATASHEET-SPEC.md
- Git blob: 9f92017c65d4d9aec137376486b25ebcc88495ea
- SHA-256: accb8b7540979f70f99a92203a40a8b7f6381309f8ca68d171a776202902a320
- Proposed apparatus key: xfmr_dry
- Proposed template key: ats_dry_xfmr_v1
- Proposed capture mode: field entry

Required human review must bound transformer configuration, winding count,
nameplate and test value variants, acceptance sources, units, calculations,
attachments, and customer-visible evidence.

## 5. What is not the field-product proof

The existing PTM transformer office-import work is a connected-office import
slice. It can inform parser and provenance design, but it does not prove an
installable client, zero-connectivity capture, durable local storage, device
assignment, reconnect, conflict behavior, field review, or non-owner evidence
readback.

Immutable comparison anchor:

- Source: reference/records/14-CAPTURE-MODE-IMPORT-SPEC.md
- Git blob: 378501ed523b1a0bbf218dfd559b0d2e191203cc
- SHA-256: 71ef99d353cde389d813c3ddcad2eb7110c5d2f414fc6cba8959a3cecf8c13fe

No source artifact body or customer content is included in this packet.

## 6. Batched unresolved operator decisions

Return one signed decision artifact that preserves each stable code, records the
chosen answer, identifies the authority, binds the exact artifact and digest,
provides an effective timestamp, and states a supersession rule.

### REC-D001 — First consumer and accountable authorities

Provide:

- consumer name and runtime boundary;
- accountable product owner;
- release acceptor;
- product-acceptance signatory, if different;
- responsibility and escalation boundary for each.

Current state: unresolved. Default action: hold.

### REC-D002 — Authorization tenancy and row scope

Choose and define one explicit release model:

- single-firm;
- project-scoped;
- customer-multitenant; or
- another fully specified model.

Include customer, organization, project, site, crew, and row-scope mappings and
negative cross-scope behavior.

Current state: unresolved. Default action: hold.

### REC-D003 — Authoritative identity sources

Name the authoritative human, device, and service-principal identity systems,
stable identifiers, token issuer and audience, verification owner, principal
mapping, and offboarding behavior.

Current state: unresolved. Default action: hold.

### REC-D004 — Device assignment and revocation

Define enrollment, assignment, reassignment, shared-device policy, lost-device
response, offline revocation horizon, session expiry, key rotation, and recovery.

Current state: unresolved. Default action: hold.

### REC-D005 — Source-content use posture

For repository, production database, device sync store, exports, reports, and
customer display, state allowed, forbidden, or conditional. Name the licensing
and custody authority and required lineage or redaction.

Current state: unresolved. Default action: do not store, sync, export, or serve
unapproved standards-derived content.

### REC-D006 — Lifecycle, reviewer separation, and amendments

Define states and transitions; who may submit, review, accept, reject, reopen,
amend, and supersede; reviewer separation; reason requirements; and how accepted
versions remain reconstructable.

Current state: unresolved. Default action: no acceptance path.

### REC-D007 — Retention and recoverability

Define retention, legal hold, deletion, tombstone, backup, restore objectives,
restore testing, evidence survival, and customer deletion obligations.

Current state: unresolved. Default action: no production data admission.

### REC-D008 — Asset-tag scope and soft-reference reconciliation

Define tag uniqueness scope and the owner and service-level objective for
reconciling project, customer, work, technician, and asset references. Define
quarantine, correction, and unresolved-reference handling.

Current state: unresolved. Default action: no cross-domain acceptance claim.

### REC-D009 — Exact first vertical slice

Select one candidate or explicitly reject all. Bind the apparatus key, template
key and version, capture mode, accepted evidence inputs, attachments posture,
and source authority.

Current state: unresolved. Proposed recommendation: RFS-GROUNDING. The
recommendation is not selected or ratified.

### REC-D010 — PowerSync hosting, operations, and custody

Choose managed or self-hosted service and name the operator, data custodian,
region, tenant boundary, support, observability, incident, backup, exit, and
vendor-risk responsibilities.

Current state: unresolved. Default action: no sync implementation.

### REC-D011 — Acceptance evidence and signatory

Name the signatory and specify required evidence for installability,
zero-connectivity use, restart survival, identity and device binding, scope
denials, exact replay, stale revision rejection, governed review, immutable
acceptance, readback, rollback, observability, and recovery.

Current state: unresolved. Default action: no product acceptance.

## 7. Fixed acceptance evidence contract

Selection does not change these required proof points:

1. Named office user creates the bounded project and provisioned package.
2. Named technician and enrolled device receive only the authorized scope.
3. One apparatus is bound to one immutable template version.
4. Package completeness is proven before network loss.
5. Field capture completes with zero connectivity.
6. Local state and outbox survive application and device restart.
7. Reconnect produces one atomic server result.
8. Same-key/same-body retry returns the exact result.
9. Same-key/different-body, stale revision, foreign device, and cross-project
   requests are rejected.
10. A separate authorized reviewer executes a governed lifecycle transition.
11. Acceptance preserves the exact template, inputs, values, units, options,
    actors, device, revisions, decision inputs, result, and amendment chain.
12. A non-owner read identity reconstructs the accepted evidence.
13. Revocation, rollback, audit review, and restore behavior are evidenced.

A passing subset is not acceptance.

## 8. Explicit non-authority

This packet authorizes no schema or migration, database access, role or grant,
login activation, credential or secret, Data API exposure, API, PWA, PowerSync
configuration, importer, deployment, source-content use, production action, or
product acceptance.

A future signed response changes only the decisions it explicitly binds.
Implementation and promotion remain separate reviewed operator approvals.
