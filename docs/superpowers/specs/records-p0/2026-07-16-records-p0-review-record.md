# Records P0/P1 Bounded Review Record

Status: **HELD — BOUNDED CORRECTION; DELTA RE-REVIEW REQUIRED, NOT AUTHORIZED**
Goal: RECORDS-P0-AUTHORITY-AND-P1-ADMISSION-FRAMEWORK-001
Recorded: 2026-07-16 UTC
Decision status: proposed
Execution authorized: false

This record freezes the evidence and review protocol for the Records authority
reconciliation and admission framework. It is not product, implementation, or
production acceptance.

## 1. Immutable review inputs

| Item | Value |
|---|---|
| Audit canonical baseline commit | 1dd49da1266d4ea793dd990ac50252c3278a1145 |
| Audit canonical baseline tree | 514c4d20959a10062ebbb4cb48e5a35b6a71d480 |
| Selected base commit | bdec885a5cd2862da7907054646c9c0fb5df5ef2 |
| Selected base tree | b3f91a2392e0afd7b545bab2b6441c7ed6e27432 |
| Framework content commit | a3fe240928d42ca9f4cbaf9526b5444aa46dc062 |
| Framework content tree | e3719d8ac777fd1f2e7cd92be0d5000b1139135b |
| Prior bounded-review head | cafa297d728172d946fd775da763bf5b78a01b4c |
| Prior bounded-review tree | d06b750e4fa23648097759d1560800e8aa213ec0 |
| Assessment input SHA-256 | 5db6a3a0582eac515c55f1c66496ae46e64541b65325e66430346adf20cbeb43 |
| Assessment role | input only; no gate, decision, or execution authority |

The audit reported canonical Records scope at
1dd49da1266d4ea793dd990ac50252c3278a1145. A base-to-base comparison produced
no output for the following frozen scope between that commit and the selected
base:

- docs/lanes/README.md
- reference/records/
- infra/database/migrations/records/
- docs/operations/RECORDS-PROD-APPLY-EVIDENCE-2026-07-07.md
- docs/superpowers/specs/records-p0/
- .github/workflows/records-ci.yml
- packages/records-import/

Therefore no Records or authorized-status delta needed reconciliation between
the audit snapshot and selected base. This proof concerns repository history
only; it does not refresh external production state.

The July assessment inspected the broad Records implementation, including
migrations 001 through 049. The later formal external review did not repeat
that audit. Its mechanically restricted projection contained only the thirteen
changed paths listed in the handoff. The only migration path in that projection
was infra/database/migrations/records/MANIFEST.md; no migration SQL body was
included. The bounded review verified by Git name/status that no .sql path
changed. The full-checkout status test's migration-filename result was supplied
as local context only, not independently reproduced from SQL bodies by either
external reviewer.

## 2. Review scope

The prior bounded-review target at cafa297d contains four logical commits:

1. 051f7fc1 — red-first status contradiction test.
2. 8cefd7af — canonical 001-049 dormant-authority reconciliation.
3. a3fe2409 — held P0/P1 framework, decision packet, machine manifest,
   fail-closed checker/tests, and DB-free CI.
4. cafa297d — review record, handoff, and exact freeze metadata.

The bounded correction comprises exactly one fifth local commit across five
already authorized paths: this record, the companion handoff, the authority
workflow, the validator, and its DB-free regression suite. It changes no
manifest state, SQL, runtime, importer, serving contract, retained evidence, or
production surface. Its exact resulting head and tree are derived after commit
and reported outside Git content.

Any separately authorized delta reviewer must inspect the prior-reviewed head
to corrected-head diff and confirm the complete selected-base-to-head history
still preserves:

- status consistency and retained-evidence qualifiers;
- separation of ratified precedent, open decision, invariant, evidence, and
  promotion authority;
- real-candidate proposed and unauthorized state;
- immutable base, audit, artifact, authority, and slice bindings;
- false-green rejection behavior;
- exact path and commit-history enforcement;
- absence of SQL, runtime, importer, serving-contract, and production-evidence
  changes;
- absence of schema, credential, deployment, or production authority.

## 3. Verification evidence

The prior bounded-review head was verified before its two authorized external
reviews:

| Check | Prior result at cafa297d |
|---|---|
| Status authority tests | 6 passed |
| Admission validator tests | 11 passed |
| Combined DB-free discovery | 17 passed |
| Real manifest validation | HELD; no diagnostics; REC-D001 through REC-D011 unresolved |
| Synthetic satisfiability fixture | SATISFIABLE_FIXTURE; execution_authorized=false |
| Python compile | passed |
| Workflow YAML parse | passed |
| Whitespace check | passed |
| SQL/runtime/importer/serving/evidence writes | none |

The bounded correction adds six validator regressions and was verified before
commit as follows:

| Check | Correction result |
|---|---|
| Status authority tests | 6 passed |
| Admission validator tests | 17 passed |
| Combined DB-free discovery | 23 passed |
| Authorized local audit artifact | actual SHA-256 equals manifest and expected digest; `audit_artifact_verified=true` |
| Real manifest validation | HELD; no diagnostics; REC-D001 through REC-D011 unresolved |
| Publication-specific result expectation | exact HELD required; synthetic satisfiability fixture exits nonzero |
| Direct Git-history positive fixture | valid multi-commit candidate passes with `verify_git_diff=true` |
| Direct Git-history fail-closed fixture | transient unauthorized add/delete path is rejected despite a valid final diff |
| CI audit mode | external binding only; exact HELD required; `audit_artifact_verified=false` |
| SQL/runtime/importer/serving/evidence writes | none |

The exact clean-worktree, every-commit history, final changed paths, Python
compile, YAML parse, and whitespace checks are rerun after the correction is
committed. Their derived head and tree necessarily live outside this Git
content and are returned to the operator.

## 4. Adversarial findings and resolutions

These are preparatory checks, not substitutes for the two authorized review
engines.

### Resolved: progressive offline drafts versus incomplete acceptance

The first framework draft said partial submissions fail. That could be read as
forbidding incremental offline draft persistence before lifecycle semantics are
ratified. The invariant now allows governed draft persistence and rejects
missing required values only at transition to review or acceptance.

### Resolved: semantic relabeling

The first checker version validated stable code inventories but did not bind
each code to exact semantics. A malicious relabel could preserve the codes while
changing PWA, identity, invariant, or slice meaning. The compact checker now
binds exact precedent subject/choice, decision title, invariant title, and slice
apparatus/template/mode/source tuples. Regression probes cover the false-green.

### Resolved: incomplete immutable bindings

The first checker accepted hash-shaped locators without proving every required
artifact and Git blob. It now requires the exact audit locator, exact artifact
inventory, frozen canonical digests, and commit/path-to-blob resolution at the
selected base. In authorized local-artifact mode it recomputes the exact audit
bytes and requires actual, manifest, and expected SHA-256 values to be equal.
CI deliberately uses visibly named external-binding-only mode because that
runner does not possess the authorized audit artifact; it reports
`audit_artifact_verified=false` and is not proof of the artifact bytes.
Regression probes cover missing or altered audit bytes, altered audit path,
and forged source blobs.

### Resolved: final-tree-only scope checking

The first history check inspected only the final net diff. A forbidden file
could have been added and removed in separate commits. The checker now rejects
merge commits, examines NUL-delimited name/status data for every candidate
commit, rejects transient paths and non-add/modify statuses, then independently
checks the final exact diff.

### Resolved: mutable review checkout and test mutation

The first workflow used the pull-request merge ref and ran tests before the
manifest gate. It now checks out the exact PR head or push SHA, validates the
manifest/history first, runs tests only in a dependent fresh checkout, and
proves the test checkout remains clean.

### Resolved: publication result classification

General fixture validation continues to accept either HELD or
SATISFIABLE_FIXTURE when no publication expectation is requested. The
publication workflow now requires the exact result HELD. A satisfiable fixture
therefore cannot make the publication-specific command succeed.

### Resolved: complete authority and candidate binding

Each ratified precedent is now bound to its exact supersession rule as well as
its code, subject, and choice. The real candidate identifier is frozen to
`RECORDS-FIRST-SLICE-2026-07`. Regression probes reject drift in every
supersession rule and candidate-id substitution.

### Resolved: direct Git-history proof

The validator suite now exercises `verify_git_diff=true` against disposable
repositories. One fixture proves the valid multi-commit path. A second adds
and later deletes an unauthorized path, then proves history inspection rejects
the candidate even though its final diff is otherwise valid.

## 5. Authorized formal review record

The two authorized reviews applied only to prior head cafa297d, tree d06b750e,
the mechanically bounded thirteen-path byte projection, and necessary Git
metadata. They did not authorize secrets, source bodies, database data,
production access, unrelated content, edits, publication, or clearance.

An initial Codex attempt, session
`019f6bf5-f81a-7291-8ab4-79c68e1bc46f`, exceeded that projection by reading
memory, AGENTS.md, README material, authority listings, and bootstrap context.
It was terminated without a final result. It is non-authoritative, excluded
from the formal review record, and grants no approval. No secret, database, or
production content was reported as observed.

A bounded host Codex attempt, session
`019f6c00-ac2e-77c3-8bdf-c26f134f4d0f`, could not start because its sandbox
failed to configure loopback. It produced no review result.

The substantive bounded Codex review ran in Docker with CLI 0.144.4,
configured model `gpt-5.6-sol` at `xhigh`, session
`019f6c0a-8f22-7493-ab60-cddf7d9449ec`. It reviewed the exact thirteen-path
byte projection and reported no High or Low findings and three P2/Medium
findings:

1. the publication command could succeed for a satisfiable synthetic fixture;
2. precedent supersession rules were not compared exactly; and
3. the candidate identifier was not compared to its frozen value.

The independent Claude review used CLI 2.1.183, requested `opus` and resolved
to `claude-opus-4-8` at high effort, with tools disabled and no retained
session. Its session was `360e035e-d2c0-4cf5-b790-eff637883a60`; the reviewed
patch digest was
`cc0877ea3a8e14c055f3be7a2771d5e135620d8faf6d0345cb52c2054e9f89ba`.
It reported no High or Medium findings and three Low limitations: no direct
Git-history fixture, no SQL-body visibility in the bounded projection, and no
recomputation of the local audit artifact digest.

This correction closes all three Codex findings plus the direct-Git and
audit-digest Low limitations. The SQL limitation remains explicit and
contextual; the correction does not broaden the projection to migration SQL.
The prior reviews do not cover this correction, and no external delta review
is authorized in the present step.

## 6. Review disposition rule

Publication is allowed only after:

1. both formal reviews have completed;
2. no confirmed High or Medium finding remains;
3. any bounded correction and separately authorized focused delta re-review
   are complete;
4. the branch is clean;
5. exact base, reviewed head, reviewed tree, changed paths, and checks are
   re-derived; and
6. current origin/main has no post-base delta in an authorized Records path.

A successful review does not change decision_status, execution_authorized, or
implementation readiness. It only establishes that this held authority packet
is reviewable for a draft pull request.

## 7. Explicit non-authority

This review record authorizes no merge, migration, database access, role or
grant, login activation, credential or secret, Data API exposure, API, PWA,
PowerSync, importer, deployment, source-content use, production action, or
product acceptance.
