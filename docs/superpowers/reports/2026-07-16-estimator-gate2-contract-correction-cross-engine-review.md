# EST-TAKEOFF-CATALOG-COVERAGE-001 Gate 2 Contract Correction Cross-Engine Review

Status: **CLEAN**

Review completed: `2026-07-16T02:56:26Z`

## 1. Reviewed object

- Repository baseline: `bdec885a5cd2862da7907054646c9c0fb5df5ef2`
- `origin/main` at review completion: `bdec885a5cd2862da7907054646c9c0fb5df5ef2`
- Formal bounded C1-C7 review prompt SHA-256:
  `ea1eb9e7aba2136734ca65d253baf747879e3772233f8b989672c22ab4757db2`
- Review mode: read-only, findings first, exact frozen artifacts
- Scope: the seven Gate 2 contract corrections only

| Frozen artifact | SHA-256 |
|---|---|
| `docs/superpowers/packets/estimator-takeoff-catalog-coverage-001-ledger.csv` | `6538e737642b7ac09bc718d8812d70d4f3bf547b55cdcbb6c94dd4acdcf2319a` |
| `docs/superpowers/packets/estimator-takeoff-catalog-coverage-001.md` | `3b8304562cffaf685fb1f8726fa7cad57e145ed9f7728bdad213bb4657589a42` |
| `docs/superpowers/packets/estimator-takeoff-meter-pqm-discovery.md` | `a67138268ac06f9041cbae03809695b898c54917af611aaf1ded3103ae8b1eb1` |
| `docs/superpowers/packets/estimator-takeoff-surge-spd-discovery.md` | `50c04251b4db519a5cc4ea95ad032e516df97fed2f1e8fd7e7881f62a8a8f44d` |
| `docs/superpowers/specs/2026-07-16-estimator-gate2-family-candidate-contract-delta.md` | `f1947f21fc6e5a7ab0c77fe6579b69433a4157df26ff93be9e9c266024bff48b` |

## 2. Engine execution evidence

### 2.1 Codex

- CLI: `codex-cli 0.144.4`
- Requested and recorded model: `gpt-5.4`
- Initial read-only thread: `019f68bf-33ce-7c01-a13a-eaee6a926ada`
- Recovery read-only thread: `019f68ce-374e-7b52-9c8f-d5167606f5f0`
- Final recovery verdict: `CLEAN`
- Final check statuses: `C1 PASS`, `C2 PASS`, `C3 PASS`, `C4 PASS`,
  `C5 PASS`, `C6 PASS`, `C7 PASS`
- Final findings: empty

The initial ephemeral execution could not read the frozen files because its
sandbox rejected file reads with
`bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`. Its fallback
workspace-read job remained queued. It returned one execution finding, `X1`,
and explicitly stated that it could not determine C1-C7. Because the
ephemeral invocation persisted no rollout, the emitted thread ID could not be
resumed. The same bounded campaign therefore used one recovery execution with
the original scope and exact artifact bytes supplied inline. The recovery
called no review tools and returned all seven checks `PASS` with no findings.

Codex's final evidence identified:

- C1: the bbox canonicalization contract and invariant 20 define one RFC 8785
  binary64 ASCII string representation and reject negative zero and non-finite
  values;
- C2: the complete packaging and quantity projection and ordered projection
  set are bound to the accepted candidate-set-scoped family authority;
- C3: breaker lock selects only the mechanical reference, while family
  authority remains mandatory before resolution or emission;
- C4: the closed upstream hash registry defines or import-pins every preimage,
  while the downstream v2 decision receipt remains an explicit hold;
- C5: family answers must converge on one block profile, and per-family output
  requires exact pair-scoped authority and a bound implementation;
- C6: source-specific current Rights Authority decisions are eligibility gates
  and are bound into the future ranking receipt; and
- C7: the checklist preserves the required equality, overlap-guard, discovery,
  report-byte, and sidecar distinctions.

### 2.2 Claude Code

- CLI: `Claude Code 2.1.183`
- Requested alias: `opus`
- Exact response model: `claude-opus-4-8`
- Session ID: `26d065c5-0f32-4de0-b6b3-af7852a5b272`
- Final verdict: `CLEAN`
- Final check statuses: `C1 PASS`, `C2 PASS`, `C3 PASS`, `C4 PASS`,
  `C5 PASS`, `C6 PASS`, `C7 PASS`
- Final findings: empty

The first process using this UUID remained silent for approximately 25 minutes
and never created a conversation. It was terminated; `--resume` then confirmed
`No conversation found with session ID`. The same UUID was reused in safe mode
with no tools and the exact frozen artifact bytes supplied inline. The recovery
initialized with exact model `claude-opus-4-8` and returned successfully.

Claude's final evidence independently identified:

- C1: `apex.bbox-jcs-binary64/v1` defines finite IEEE 754 binary64 parsing,
  RFC 8785 number serialization into an ASCII string, exact ordered comparison,
  and rejection of alternate numeric forms;
- C2: `familyContractProjectionHash`, the ordered projection-set hash, and the
  candidate-set-scoped authority binding cover refs, packaging, observed
  packaging, quantity basis, proposed quantities, evidence, and questions;
- C3: `locked_ref_requires_family_authority` prevents breaker lock from
  authorizing standard, packaging, quantity, price, resolution, or emission;
- C4: the registry separates raw-byte, canonical, and Gate 1 content hashes,
  import-pins preserved contracts, and refuses to invent the downstream v2
  decision/receipt preimage;
- C5: the current emitter has one native scope per block, conflicting or
  missing family profile answers fail closed, and `per_family_scope` is invalid
  without exact output authority and implementation binding;
- C6: every ranked corpus case requires a current, effective, unexpired,
  source-specific Rights Authority decision whose appointment and receipt
  identities are included in the ranking receipt; and
- C7: the ledger remains exhaustive, the six discovery-only rows remain
  distinct from mapped relay ref `093`, and a future sidecar cannot reinterpret
  the unchanged merged report artifact bytes.

## 3. Findings and dispositions

| ID | Classification | Disposition |
|---|---|---|
| Codex `X1` | Execution environment only; no reviewed artifact was read and no design claim was made | Resolved inside the same frozen campaign by the no-tool inline-evidence recovery thread; not an artifact finding |
| Claude initial hang | Execution transport only; no conversation or review result existed | Resolved by reusing the same session UUID in safe mode with no tools and inline evidence |
| Codex recovery findings | None | No correction required |
| Claude findings | None | No correction required |

No frozen artifact was edited after either successful review result. The
execution recoveries changed only evidence transport. They did not change the
formal prompt scope, baseline, artifact bytes, or artifact hashes.

## 4. Local machine checks

- Ledger verifier: `PASS`; 120 unique rows in exact source order.
- Ledger partition: 12 `priced_breaker_rule`, 38
  `recognized_scope_pending_candidate`, 6 `discovery_only_unmapped`, and 64
  `catalog_only_unmapped`.
- Mapped family counts: breaker 12, relay 9, GFP 1, instrument transformer 9,
  switch 11, transfer switch 3, transformer 5.
- Relay meter-overlap guard: remains mapped to relay ref `093`.
- Source hashes declared in the coverage packet: all 19 recomputed `PASS`.
- Ratification state: all six R1 flags remain false.
- Trailing whitespace scan across the five frozen artifacts: `PASS`.
- Frozen artifact hashes after both engine reviews: exact matches to section 1.
- Worktree content before this review record: exactly the five untracked frozen
  documentation artifacts and no tracked diff.
- Preserved original dirty worktree status SHA-256:
  `6db395231602f54ab71fa08b29d750e80a85c79985156390e2a3dce4e7facc8a`.
- No runtime, catalog, schema, corpus, family, authority, deployment, or
  production file changed.

## 5. Review outcome

The bounded Gate 2 contract correction is clean for C1-C7. It may be committed
as the five frozen documentation artifacts plus this review record on the named
local branch. This review grants no authority to implement a family, alter the
catalog or ledger, ingest corpus material, resolve Gate 2, emit scope, deploy,
push, or open a pull request.
