# Estimator Gate 2 R1 And Gate 1 Scope Focused Review

Status: **CLEAN**

Date: 2026-07-16
Held parent commit: `7c435f61fafbd495ceabbf5aed9c73d91243bce1`
Branch: `estimator-takeoff/catalog-coverage-001-gate2-correction`

## 1. Scope

This is the one bounded Codex and Claude post-review campaign required to check
only:

1. literal `r1Ratified === true` before any candidate becomes resolved, priced,
   or emitted;
2. false R1 as blocked-preview-only and non-waivable by any receipt or authority
   artifact;
3. missing breaker R1 authority as fail-closed;
4. exact loaded Gate 1 receipt equality for `intakeScopeId`, `projectId`,
   `revisionId`, and `lineSetId`;
5. the focused falsification cases for those gates;
6. supersession of the prior CLEAN record without loss of its provenance; and
7. the adjacent resolution gate, including rejection of the preserved unmerged
   v1 resolver as a v2 bypass.

The campaign did not redo ledger, discovery, family-count, meter-overlap,
source-hash, or Rights Authority corpus analysis. It authorized no runtime,
catalog, schema, family-map, corpus, authority, deployment, production, push, or
PR change.

## 2. Frozen review inputs

| Artifact | SHA-256 |
|---|---|
| `docs/superpowers/specs/2026-07-16-estimator-gate2-family-candidate-contract-delta.md` | `619df35ebf257062bad7824dabdf899aafe66594515d6db73365b399367fe5d0` |
| `docs/superpowers/reports/2026-07-16-estimator-gate2-contract-correction-cross-engine-review.md` | `fab6f76d7af1410a9ef71d35cd536ca40648aa04ea4ee55b9f3795a28924763c` |

Adjacent read-only evidence was limited to the merged breaker map, merged R1
declarations and emitter, the preserved Gate 1 scope validation, and the
preserved v1 resolver used as a negative control. The held branch does not track
`packages/estimator-takeoff/src/workflow/contracts.ts`.

- Initial P1-P6 prompt SHA-256:
  `f0e8f26cd3f299d195853f8fffc8247d5ff8c4d665c518200244142a3f4a7cfd`
- Same-campaign X1 disposition prompt SHA-256:
  `bfd8547c25be9f5f45461c84f4efcde856a7b7cb80d6d1d2b84b5c3b4d315ac7`

## 3. Engine provenance

### 3.1 Codex

- CLI: `codex-cli 0.144.4`
- Model: `gpt-5.4`
- Thread: `019f690a-bae3-73f1-8cd8-3a71f1414f6b`
- Mode: read-only, exact evidence supplied inline
- Initial verdict: `FINDINGS`
- Final same-thread verdict: `CLEAN`
- Final checks: `P1 PASS`, `P2 PASS`, `P3 PASS`, `P4 PASS`, `P5 PASS`,
  `P6 PASS`
- Final findings: empty

### 3.2 Claude Code

- CLI: `Claude Code 2.1.183`
- Requested alias: `opus`
- Exact model: `claude-opus-4-8`
- Session: `92f9c690-c659-4d22-95dc-734d96af8184`
- Mode: safe mode, no tools, exact evidence supplied inline
- Initial verdict: `CLEAN`
- Final same-session verdict: `CLEAN`
- Final checks: `P1 PASS`, `P2 PASS`, `P3 PASS`, `P4 PASS`, `P5 PASS`,
  `P6 PASS`
- Final findings: empty

## 4. Finding and disposition

Codex initially returned one high-severity finding:

| ID | Initial evidence | Required disposition | Applied disposition |
|---|---|---|---|
| `X1` | Preserved unmerged v1 `resolveGate2Decisions` can construct `status:'resolved'` without a visible literal R1 or breaker-R1-unavailable predicate | Do not accept P1, P2, or P6 while that adjacent path appears to be a conforming resolver | The delta now identifies the preserved v1 function as negative evidence, states that it is absent from the held commit, prohibits its use/import/wrapping/hash binding as v2, requires all gates on the same future v2 path before any resolved construction, and adds `PRESERVED-V1-RESOLVER-BYPASS` as a rejected falsifier |

No runtime file was changed. Both reviewers then continued in their same thread
or session against the updated frozen hash. Codex closed `X1`; Claude confirmed
the disposition remained clean. This was one review campaign with a finding and
same-campaign disposition, not a second ledger or discovery review.

## 5. Final check evidence

| Check | Codex | Claude | Final evidence |
|---|---|---|---|
| P1 | PASS | PASS | Section 5 R1 gate, section 7 operation gate, and invariant 25 require literal true before resolved, priced, or emitted output |
| P2 | PASS | PASS | Breaker lock remains mechanical only; missing independently bound breaker R1 is false and blocked despite otherwise-valid family authority |
| P3 | PASS | PASS | The exact loaded Gate 1 receipt is schema/hash validated and all four scope fields are independently compared by literal equality |
| P4 | PASS | PASS | False R1, unavailable breaker R1, each individual scope mismatch, exact-match scope-only pass, and preserved-v1 bypass cases have explicit expected results |
| P5 | PASS | PASS | The prior record is visibly superseded while retaining its hashes, engine versions, run/session identifiers, verdicts, findings, and dispositions |
| P6 | PASS | PASS | No product resolution exists until a conforming v2 implementation applies all new and pre-existing gates before constructing resolved, priced, or emitted output |

## 6. Local validation

- Before this record, the bounded diff contained exactly the corrected contract
  delta and superseded prior review record.
- Ledger and both discovery packet paths were unchanged.
- The seven requested R1 and Gate 1 falsification cases were machine-located.
- The added preserved-v1 bypass falsifier was machine-located.
- All three original review run/session identifiers remain present in the
  superseded record.
- `git diff --check` passed.
- No runtime, catalog, schema, corpus, family-map, authority, deployment, or
  production path changed.

## 7. Outcome

The bounded documentation correction is clean for P1-P6. It may be committed
locally with this review record on the existing held branch. This review does
not authorize push, PR, merge, implementation, pricing, resolution, emission,
deployment, or production use.
