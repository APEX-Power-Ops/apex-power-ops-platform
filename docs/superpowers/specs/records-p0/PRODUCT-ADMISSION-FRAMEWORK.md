# Records P0/P1 Product-Admission Framework

Status: **HELD**
Goal: RECORDS-P0-AUTHORITY-AND-P1-ADMISSION-FRAMEWORK-001
Candidate kind: real
Decision status: proposed
Execution authorized: false
Implementation readiness: held
Effective date: none

This document separates already-ratified architectural precedents from decisions
that still require a named human authority. It is a decision framework, not a
product specification, deployment plan, schema authorization, or operational
approval.

## 1. Frozen assessment boundary

| Binding | Frozen value |
|---|---|
| Canonical base commit | bdec885a5cd2862da7907054646c9c0fb5df5ef2 |
| Canonical base tree | b3f91a2392e0afd7b545bab2b6441c7ed6e27432 |
| Assessment input | 2026-07-14 Records platform and field-execution audit |
| Assessment SHA-256 | 5db6a3a0582eac515c55f1c66496ae46e64541b65325e66430346adf20cbeb43 |
| Retained production evidence date | 2026-07-07 |
| Migration ceiling | 001 through 049 |
| Substrate posture | production-applied and deliberately dormant |
| Product posture | no admitted consumer and no operational Records product |

Canonical state key: Records-State-Key: migration_tip=049;
evidence_as_of=2026-07-07; substrate=prod-applied-dormant; data_api=excluded;
prod_role_login=none; product_runtime=not-admitted.

The July audit is assessment input only. It grants no decision, schema,
credential, deployment, production, or acceptance authority. Durable claims in
this framework are independently bound to canonical repository artifacts in
records-admission-manifest.json.

## 2. Admission semantics

A candidate is admitted only when all of the following are simultaneously true:

1. Every open human decision has a named authority, an immutable decision
   artifact, a digest, a timestamp, and a supersession rule.
2. Every non-negotiable technical invariant has executable, non-owner evidence.
3. The exact first slice and its acceptance signatory are ratified.
4. A later implementation proposal is separately reviewed and explicitly
   authorized.
5. Production activation is separately authorized after implementation evidence.

No partial satisfaction upgrades the current candidate. Unknown, placeholder,
AI-inferred, unsigned, mutable, or stale authority fails closed.

The only real candidate in this packet therefore remains:

- decision_status = proposed
- execution_authorized = false
- implementation_readiness = held

A synthetic accepted fixture exists only in unit tests to prove that the checker
is satisfiable. It is labeled synthetic and cannot authorize any real action.

## 3. Authority layers

The framework keeps four authority layers distinct:

| Layer | What it can establish | What it cannot establish here |
|---|---|---|
| Ratified precedent | A previously decided architectural direction | Product readiness or runtime activation |
| Human decision | A signed choice for a named open question | Implementation correctness |
| Technical evidence | Machine-checked proof against an invariant | Business acceptance or authority |
| Promotion authorization | Explicit approval for a reviewed exact artifact | Any broader or future change |

Repository presence, passing tests, a live schema, a branch, a pull request, and
an automatic preview are evidence or transport. None is decision authority.

## A. Ratified precedents

The following choices are inherited and must not be silently re-decided inside a
future implementation. Their complete immutable authority records live in the
machine manifest.

### REC-R001 — Installable PWA client

The field client direction is an installable progressive web application. A
static web shell is not an installable PWA and does not satisfy this precedent.

Authority anchor: reference/records/01-OFFLINE-SYNC-ARCHITECTURE.md at blob
f02390980ac8d6f4dd97081481061eb911dd48b9 and SHA-256
ad404a27384e0262f3b0b005083c1c3d63314032ae4bd2b333be32d5c53628c0.

### REC-R002 — Fully offline field operation

The field workflow must complete for hours or days with zero connectivity.
Online-first capture with retry is not an equivalent interpretation.

Authority anchor: the same ruled architecture artifact as REC-R001.

### REC-R003 — PowerSync sync engine

PowerSync is the selected Postgres-to-local sync transport. It distributes
scoped data and carries an outbox; it is not authentication, authorization,
lifecycle, review, or acceptance authority.

Authority anchor: the same ruled architecture artifact as REC-R001.

### REC-R004 — Direct server-side role/DSN serving

A future admitted server consumer must use a separate direct-role DSN for each
allowed connecting role. Shared Data API claims or an application-only role
label are not equivalent boundaries.

Authority anchors:

- reference/records/SERVING_CONTRACT.md at blob
  009abd4765b7f5ef30f0cecc408d111721f871ef and SHA-256
  d38a111046a7717e8ea5da82cfce4f2269602b8d0c61bff35d2d9211d04db1fa
- reference/records/SERVING_CONTRACT.yaml at blob
  96eae45f751754e8ce50413a3e8448c866c05026 and SHA-256
  e9b25be4c65665eebe19ea17b45a8769d5b9f63515b49531cf45432d12f4c8b6

The serving ceiling is records_api, records_intake_writer, and records_auditor.
That ceiling is not permission to make any role login-capable or issue a DSN.

Retained production evidence observed six dormant roles: records_api,
records_intake_writer, records_auditor, records_owner, records_fn_owner, and
records_reclaim_owner. The v2 serving-contract inventory names five roles and
does not enumerate the persistent owner-only records_reclaim_owner role. This
known documentation gap is a held follow-up; it neither expands the three-role
serving ceiling nor weakens the six-role NOLOGIN observation.

### REC-R005 — Data API exclusion

The records schema remains excluded from the Supabase Data API. Exposure cannot
be used as an expedient for the first slice.

Authority anchors: the same v2 serving-contract pair as REC-R004.

### REC-R006 — Privileged identities forbidden from runtime service

No schema owner, function owner, superuser, service-level bypass identity, or
BYPASSRLS identity may be a runtime service identity. In particular,
records_owner and records_fn_owner never receive runtime DSNs.

Authority anchors: the same v2 serving-contract pair as REC-R004.

### Precedent amendment rule

A future proposal may amend a precedent only through a separate, explicitly
signed authority artifact that names the precedent code, binds the superseded
artifact and digest, explains downstream impact, and lands before dependent
schema, client, sync, credential, or runtime work. Silence, code drift, an AI
recommendation, or a pull-request merge is not a supersession decision.

## B. Open human decisions

Every decision below has state unresolved. Stable codes must be preserved in
later packets and evidence.

### REC-D001 — First consumer and accountable authorities

Name the first serving consumer, its accountable product owner, its release
acceptor, and the authority boundary of each. A team name without a responsible
human and acceptance duty is insufficient.

### REC-D002 — Authorization tenancy and row scope

Choose the release model: single firm, project-scoped, customer-multitenant, or
another explicit model. Define organization, customer, project, site, crew, and
row-scope relationships, including denial behavior.

### REC-D003 — Authoritative identity sources

Name the authoritative sources and stable identifiers for office humans,
technicians, reviewers, devices, and service principals. Define how verified
issuer, audience, signature, expiry, and principal mapping are established.

### REC-D004 — Device assignment and revocation

Define device enrollment, technician and project assignment, reassignment,
loss, revocation, session expiry, offline revocation limits, and recovery.

### REC-D005 — Source-content use posture

Approve which reference or standards-derived content may exist in the
repository, production database, synchronized device store, export, report, and
customer-visible surface. Define custody, licensing, and lineage requirements
for each location.

### REC-D006 — Lifecycle, review separation, and amendments

Define states, permitted transitions, reviewer independence, rejection,
reopening, correction, supersession, and approved-evidence amendment semantics.
Intake authority must not self-assert final acceptance.

### REC-D007 — Retention and recoverability

Define retention periods, legal hold, deletion, tombstones, backup scope,
restore objectives, restore testing, and the relationship between deletion and
immutable accepted evidence.

### REC-D008 — Asset-tag scope and soft-reference reconciliation

Define tag uniqueness scope and the accountable owner of project, customer,
work, technician, and asset soft-reference reconciliation. Define quarantine
and correction behavior for unresolved references.

### REC-D009 — Exact first vertical slice

Ratify one apparatus class, one template version, and one capture mode for the
first complete field proof. The recommendation in the decision packet remains
proposed until a named human authority signs it.

### REC-D010 — PowerSync hosting, operations, and custody

Choose managed or self-hosted PowerSync and name operational ownership, data
custody, region, access, observability, incident response, backup, and exit
responsibilities.

### REC-D011 — Acceptance evidence and signatory

Define the evidence bundle that proves the first product slice and name the
human signatory. Component tests, schema presence, a preview deployment, or an
AI review cannot substitute for product acceptance.

## C. Non-negotiable technical invariants

These invariants constrain any later implementation regardless of the human
choices above.

### REC-I001 — Verified authentication

Every request must verify issuer, audience, signature, expiry, and intended
token use before mapping a principal. Anonymous fallback and caller-supplied
role or scope claims are rejected.

### REC-I002 — Server-side scope and cross-project denial

Server authority maps the verified principal to allowed customer, project,
site, crew, and row scope. The client never chooses its effective database role
or expands scope. Negative cross-project evidence is mandatory.

### REC-I003 — Atomic idempotency claim

The server atomically claims route plus idempotency key plus canonical request
hash in the same transaction boundary as the mutation, audit event, and stored
exact response. A failure rolls back the claim and mutation together; no
half-claimed or half-applied result is admissible.

### REC-I004 — Exact replay semantics

A duplicate key with the same request hash returns the exact committed response.
The same key with a different body is rejected. In-flight and failed claims
have explicit, tested behavior.

### REC-I005 — Device binding and monotonic revision

Device-originated writes bind principal, enrolled device, assignment, project,
submission, and monotonic client revision. Stale or foreign-device writes fail;
compare-and-swap or an equivalent race-safe guard is required.

### REC-I006 — Separate office and device authority

Office provisioning/reference authority and device capture authority remain
separate. Devices cannot silently mutate server-authoritative reference data,
and office actors cannot impersonate device provenance.

### REC-I007 — Governed lifecycle transitions

Lifecycle changes pass through narrow server-side transitions with actor,
reason, previous state, next state, and authorization evidence. Direct intake
updates cannot create or rewrite accepted state.

### REC-I008 — Template and value validation

Every value agrees with the assigned template version, field key, requiredness,
kind, unit, option set, and applicable acceptance inputs. Cross-template,
unknown-field, invalid-unit, and contradictory writes fail. Incremental offline
drafts may persist only in a governed draft state; transition to review or
acceptance must reject missing required values.

### REC-I009 — Immutable accepted evidence

Acceptance creates a reconstructable immutable snapshot or equivalent
content-addressed evidence. Corrections are controlled amendments that preserve
the accepted version, actor, reason, decision inputs, and supersession chain.

## 4. Fixed first-slice acceptance contract

Candidate breadth may vary, but the acceptance contract does not:

1. One named office user provisions one project.
2. One technician and one enrolled device are assigned.
3. One apparatus receives one pinned template.
4. The package is available before connectivity is removed.
5. The technician completes the template with zero connectivity.
6. Capture survives app and device restart.
7. Reconnect drains a durable outbox through the governed write path.
8. Duplicate retry is idempotent and stale or conflicting revision is rejected.
9. A separate authorized reviewer performs the governed decision.
10. The accepted evidence is read back through a non-owner read identity.
11. The evidence bundle reconstructs the exact template, values, units,
    provenance, decision inputs, actors, revisions, and amendment state.

The complete path must be proved under non-owner identities. Manual SQL,
owner credentials, prototype token decoding, a browser-only rendering smoke, or
an office import does not satisfy the contract.

## 5. Admission gates

| Gate | Required result | Current state |
|---|---|---|
| P0 authority reconciliation | Canonical status agrees on migrations 001-049 and dormant posture | satisfied in this branch |
| P1 decision authority | REC-D001 through REC-D011 signed and bound | held |
| P2 implementation design | Exact reviewed design proves REC-I001 through REC-I009 | not authorized |
| P3 consumer admission | Named runtime, least privilege, credentials, rollback, real-login tests | not authorized |
| P4 product proof | Fixed acceptance contract passes end to end | not implemented |
| P5 production acceptance | Named signatory accepts exact evidence and promotion | not authorized |

A later gate cannot compensate for an earlier held gate.

## 6. Runtime and authority guardrails

- records schema Data API exposure remains false.
- Runtime owner, function-owner, postgres, superuser, service-role, and
  BYPASSRLS identities are forbidden.
- Migrations 001 through 049 must not be replayed.
- No role activation, login alteration, grant, credential, secret, schema,
  database, API, PWA, PowerSync, importer, deployment, or production action is
  authorized by this framework.
- No unresolved decision may be reported as accepted, ratified, approved,
  implementation-ready, or execution-authorized.
- No AI output may populate an authority identity or approval.
- Automatic preview deployment, if unavoidable after publication, is neither
  product evidence nor acceptance and must not be promoted or supplied secrets.

## 7. Machine enforcement and interpretation

The file records-admission-manifest.json is the machine-readable candidate.
validate_records_admission.py checks its immutable bindings, authority metadata,
state vocabulary, unresolved decision codes, privileged-identity exclusions,
Data API posture, artifact digests, changed-path allowlist, and authority
emission flags.

A successful checker result for the real candidate means only:

- the framework is internally consistent;
- its bindings are current for the reviewed base;
- unresolved decisions are explicitly reported; and
- the candidate is correctly HELD.

It never means implementation or execution is authorized.
