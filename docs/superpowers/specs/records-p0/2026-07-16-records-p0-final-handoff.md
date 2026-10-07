# Records P0/P1 Final Handoff

Status: **HELD — BOUNDED CORRECTION; DELTA RE-REVIEW REQUIRED, NOT AUTHORIZED**
Goal: RECORDS-P0-AUTHORITY-AND-P1-ADMISSION-FRAMEWORK-001
Decision status: proposed
Execution authorized: false
Implementation readiness: held

This handoff packages the Records P0 authority reconciliation and P1 admission
framework for bounded review and a draft-held pull request. It does not
authorize implementation or operations.

## 1. Outcome

The canonical Records status now distinguishes five things that were previously
conflated:

1. Repository implementation: ordered migrations 001 through 049 exist.
2. Retained production evidence: the governed 2026-07-07 campaign recorded the
   substrate as applied, all six Records roles as NOLOGIN at closeout, Data API
   exclusion, and no credential minted during that campaign.
3. Current external state: not freshly queried by this goal; no claim is made
   that an external dormant secret cannot exist today.
4. Serving posture: dormant, with no admitted consumer.
5. Product acceptance: no operational Records product exists.

Canonical state key:

Records-State-Key: migration_tip=049; evidence_as_of=2026-07-07;
substrate=prod-applied-dormant; data_api=excluded; prod_role_login=none;
product_runtime=not-admitted.

Migrations 001 through 049 must not be replayed.

## 2. Frozen bindings

| Binding | Value |
|---|---|
| Base commit | bdec885a5cd2862da7907054646c9c0fb5df5ef2 |
| Base tree | b3f91a2392e0afd7b545bab2b6441c7ed6e27432 |
| Framework content commit | a3fe240928d42ca9f4cbaf9526b5444aa46dc062 |
| Framework content tree | e3719d8ac777fd1f2e7cd92be0d5000b1139135b |
| Prior bounded-review head | cafa297d728172d946fd775da763bf5b78a01b4c |
| Prior bounded-review tree | d06b750e4fa23648097759d1560800e8aa213ec0 |
| Audit SHA-256 | 5db6a3a0582eac515c55f1c66496ae46e64541b65325e66430346adf20cbeb43 |

The exact publication head and tree are re-derived only after review metadata is
finalized and the bounded review loop is complete. Git objects cannot
self-identify their own eventual commit SHA inside their content; the draft PR
body and operator return packet carry the exact reviewed publication pair.

## 3. Changed-path manifest

The final branch is restricted to exactly these thirteen paths:

1. .github/workflows/records-authority-admission-ci.yml
2. docs/lanes/README.md
3. docs/superpowers/specs/records-p0/2026-07-16-records-p0-final-handoff.md
4. docs/superpowers/specs/records-p0/2026-07-16-records-p0-review-record.md
5. docs/superpowers/specs/records-p0/PRODUCT-ADMISSION-FRAMEWORK.md
6. docs/superpowers/specs/records-p0/PROPOSED-FIRST-SLICE-DECISION-PACKET.md
7. docs/superpowers/specs/records-p0/records-admission-manifest.json
8. docs/superpowers/specs/records-p0/test_records_status_authority.py
9. docs/superpowers/specs/records-p0/test_validate_records_admission.py
10. docs/superpowers/specs/records-p0/validate_records_admission.py
11. infra/database/migrations/records/MANIFEST.md
12. reference/records/CURRENT-STATE.md
13. reference/records/PUNCHLIST.md

No SQL, application, package, importer, serving-contract, or retained
production-evidence blob is authorized to change. The authorized external
review projection for prior head cafa297d contained these thirteen changed
paths only. Its sole migration path was the migration MANIFEST.md; it contained
no migration SQL body. Migration filenames and status were checked locally in
the full checkout and supplied as context, not independently reconstructed by
the external reviewers.

## 4. Ratified precedents preserved

The framework preserves six prior choices without treating them as product
acceptance:

- REC-R001: installable PWA client.
- REC-R002: fully offline field operation.
- REC-R003: PowerSync sync engine.
- REC-R004: separate direct server-side role DSNs.
- REC-R005: Records excluded from the Data API.
- REC-R006: owner, superuser, service-level bypass, and BYPASSRLS identities
  forbidden from runtime service.

The present serving-role ceiling is records_api, records_intake_writer, and
records_auditor. It is not permission to activate any role or issue a DSN.

## 5. Proposed first-slice support

Three grounded candidates are compared:

| Code | Proposed slice | State |
|---|---|---|
| RFS-GROUNDING | grounding_system plus ats_grounding_v1 field entry | proposed; unauthorized; unselected |
| RFS-LV-CB | cb_lv plus ats_lv_cb_v1 field entry | proposed; unauthorized; unselected |
| RFS-DRY-XFMR | small two-winding xfmr_dry plus ats_dry_xfmr_v1 field entry | proposed; unauthorized; unselected |

RFS-GROUNDING is recommended only for human decision because it is the
narrowest complete field proof. It is not selected or ratified.

The connected PTM transformer office-import slice is explicitly not the
zero-connectivity field-product proof.

## 6. Fixed acceptance contract

Candidate selection cannot weaken the required path:

one office user, one technician, one project, one apparatus, one pinned
template, offline capture, reconnect, governed review, acceptance decision, and
immutable evidence readback.

The proof also requires restart survival, exact idempotent replay,
same-key/different-body rejection, stale revision rejection, foreign-device and
cross-project denial, reviewer separation, accepted-version reconstruction,
revocation, rollback, audit review, and recovery evidence under non-owner
identities.

## 7. Batched unresolved operator decisions

Every item remains unresolved and must be answered by a named human authority
with an immutable locator, SHA-256 digest, timestamp, and supersession rule.

- REC-D001 — first consumer, accountable owner, and release acceptor.
- REC-D002 — authorization tenancy and row-scope model.
- REC-D003 — authoritative human, device, and service-principal identity sources.
- REC-D004 — device assignment and revocation.
- REC-D005 — source-content posture across repository, production, device,
  export, report, and customer surfaces.
- REC-D006 — lifecycle, reviewer separation, and amendment semantics.
- REC-D007 — retention, legal hold, deletion, backup, and restore.
- REC-D008 — asset-tag scope and soft-reference reconciliation ownership.
- REC-D009 — exact first apparatus, template, and capture mode.
- REC-D010 — PowerSync hosting, operations, and custody.
- REC-D011 — acceptance evidence and signatory.

No missing answer defaults to approval.

## 8. Verification contract

The DB-free gate must report:

- all 23 focused tests passing: 6 status tests and 17 validator tests;
- real manifest result HELD;
- execution_authorized=false;
- REC-D001 through REC-D011 unresolved;
- no diagnostics;
- the exact authorized local audit bytes recomputed with actual, manifest, and
  expected SHA-256 values equal and `audit_artifact_verified=true`;
- clean worktree;
- no merge commit in the candidate history;
- only add/modify operations on the exact thirteen paths in every commit;
- final Git diff equal to the manifest;
- frozen base tree and canonical Git blobs resolving exactly.

Direct disposable-repository tests must prove both the valid
`verify_git_diff=true` path and fail-closed rejection of a transient
unauthorized add/delete path. CI lacks the authorized external audit artifact,
so its explicitly named external-binding-only mode must report
`audit_artifact_verified=false`; that mode is not publication proof. The CI
publication command must require the exact admission result HELD.

The synthetic accepted fixture proves checker satisfiability only. It always
emits execution_authorized=false and cannot be used as real authority.

## 9. Review and publication state

Formal review results for prior head cafa297d and tree d06b750e are recorded in
the companion bounded review record. The substantive Codex review was the
bounded Docker run; the earlier over-broad attempt was terminated and excluded
as non-authoritative. The prior reviews do not cover this correction. No delta
review, push, draft pull request, merge, deployment, publication, or hold
clearance is authorized by this handoff.

If separately authorized after a focused delta review, publication remains
limited to the exact reviewed branch
records/p0-authority-admission-framework and one mechanically draft-held pull
request targeting main with title:

HELD — RECORDS P0/P1 AUTHORITY AND ADMISSION FRAMEWORK ONLY

Before push, origin/main and every authorized Records path must be rechecked
against the frozen base. After push, the remote head, draft state, and expected
checks must be verified. Automatic preview deployments may be acknowledged but
must not be inspected, supplied secrets, promoted, or treated as acceptance.

## 10. Explicit stop

This handoff authorizes no ready-for-review conversion, merge, squash, rebase,
force-push, history rewrite, issue closure, schema, database, role, grant,
credential, secret, Data API, API, PWA, PowerSync, importer, deployment,
source-content, production, or product-acceptance action.

Any implementation or operational step requires a separate explicit operator
GO after the unresolved decisions are ratified.
