# Estimator Takeoff Catalog Coverage 001

Status: **CORRECTED OFFLINE DESIGN CANDIDATE / IMPLEMENTATION AND AUTHORITY HOLD**
Date: 2026-07-16
GO: `EST-TAKEOFF-CATALOG-COVERAGE-001`
Execution baseline: detached `origin/main@bdec885a5cd2862da7907054646c9c0fb5df5ef2`

## 1. Mandate

Produce, without implementation:

1. an exact 120-reference catalog coverage ledger;
2. a readiness matrix for the six recognized non-breaker families;
3. nonbinding Meter/PQM and Surge/SPD discovery packets;
4. a proposed Gate 2 candidate-contract delta for family policy, block-scoped
   output, packaging, quantity basis, authority, evidence, and canonical hashing;
5. a corpus-dependent priority recommendation.

This packet stops before implementation, push, PR, or family ratification.

## 2. Worktree and preservation proof

The design was authored in a fresh detached worktree created after fetching
current `origin/main`. Before fetch or related editing, the existing dirty
remediation worktree was preserved outside the repository at:

`/home/olares/code/apex/.codex-preservation/estimator-remediation-20260716T002335Z`

The snapshot contains the exact Git index, final tracked binary patch, separate
staged and unstaged patches, all 30 non-ignored untracked files in a tar archive,
before/after porcelain status, and SHA-256 manifests. The tracked patch is
342145 bytes. The SHA-256 of `manifest.sha256` is
`3f0bab8de36c59c8722647dbf90c990366978e072c35cfe38424b361a39ec283`.
The dirty tree was re-compared after fetch and remained unchanged.

## 3. Bound repository evidence

| Source | SHA-256 |
|---|---|
| `packages/estimator-core/src/catalog/equipment-models.seed.json` | `dfe59bc3c35a6d74388ca9b703fa276bc7ef9d184c973dfb9c0cc4e288a8c8d1` |
| `packages/estimator-takeoff/src/catalog/breaker-map.data.ts` | `5663b0efadc8971b776fc3d2a303e315ffa508a723fdedd06c30f8911bf0d535` |
| `packages/estimator-takeoff/src/catalog/breaker-map.ts` | `408c094cd8378690845bf306707815b886c710d3ba4318731f3cda8315cf3b37` |
| `packages/estimator-takeoff/src/catalog/relay-map.data.ts` | `e65919b8b77b826cc8959e57ed04c64d7a68c5d29675b8ed18af4e05e832524f` |
| `packages/estimator-takeoff/src/catalog/relay-map.ts` | `62359c2ecdf076318129f80160dcb48f22a9961895ee3c2a607b1d4b18bda657` |
| `packages/estimator-takeoff/src/catalog/gfp-map.data.ts` | `26c703fa33b17c400f9d56af6e6358c051459276282e0a01d9f6f0e2b3c74e3b` |
| `packages/estimator-takeoff/src/catalog/gfp-map.ts` | `8a5209656496d99a13f827a757b4246934dd6dc7b0b64db5b4e5aff805883787` |
| `packages/estimator-takeoff/src/catalog/instrument-transformer-map.data.ts` | `9e69bc0ce601908ecfcab86d008e2f60703bc6aeaee6c05bf6b2757a292cbd03` |
| `packages/estimator-takeoff/src/catalog/instrument-transformer-map.ts` | `5985017c6e15f85a1c0f422a4b280e428fb98ab2af3af1db2102000242c10e81` |
| `packages/estimator-takeoff/src/catalog/switch-map.data.ts` | `5ef205667224a13bbf5dce4dfac9ecb827df11b501c52262949c7d171c1fd4b1` |
| `packages/estimator-takeoff/src/catalog/switch-map.ts` | `421e211258c78fe4d03ab7b1797dc036a9fdf380302e5e818408ca7de893c07c` |
| `packages/estimator-takeoff/src/catalog/transfer-switch-map.data.ts` | `df3b2b5c74bde864c3e33d4d141e0e7cd21e33cccb9355fc371f3d48cf9f0e8f` |
| `packages/estimator-takeoff/src/catalog/transfer-switch-map.ts` | `604df7d4fa7df1dc1815a1544d267279e54dcadf98b8460a1b0ad53b9cd9b2f6` |
| `packages/estimator-takeoff/src/catalog/transformer-map.data.ts` | `a8a922fc429da81139ef884a17f50769bc6a5bba021a1dcb0e637d0bb333a0d7` |
| `packages/estimator-takeoff/src/catalog/transformer-map.ts` | `4672634eaa228e3329bc685bf5a72b4a20cb730251e8e42b1ef8d88bdea63006` |
| `packages/estimator-takeoff/src/extraction/types.ts` | `61395d28c19b0f496487ed4b74617949b29e4a8da5a23e6e3d56f71bee612f53` |
| `packages/estimator-takeoff/src/signature/normalize.ts` | `05b1e1ee384f4dcdb2bab4a7749e53e80ad270cc319296d2d43133e77ac4fd56` |
| `packages/estimator-takeoff/src/quantify/quantify.ts` | `60ffb9266616d4cb9eeaefa6e03c767c604df2860c043985d0ce1b93d2889b39` |
| `packages/estimator-takeoff/src/emit/emit.ts` | `78645f73e5e3347f990fa5363d2b90fe2aa218f7fcfc1ce5a415a407657736bb` |

No external or proprietary source body was used.

## 4. Exact 120-reference coverage classification

The machine-checkable ledger is:

`docs/superpowers/packets/estimator-takeoff-catalog-coverage-001-ledger.csv`

Ledger SHA-256:
`6538e737642b7ac09bc718d8812d70d4f3bf547b55cdcbb6c94dd4acdcf2319a`.

It preserves all 120 source-order refs and their exact unit, ATS/MTS section,
hours, lifecycle, coverage class, engine family, classification basis, and
discovery tag.

### 4.1 Mechanical engine partition

The engine partition is exact, mutually exclusive, and exhaustive:

| Engine coverage | Count | Percent | Meaning |
|---|---:|---:|---|
| direct breaker rule refs | 12 | 10.0% | exact refs returned by `BREAKER_MAP`; this is the only auto-priced family path |
| recognized non-breaker scope-candidate refs | 38 | 31.7% | exact refs in the six family candidate maps; every runtime line remains `scope_pending` or a catalog gap |
| no takeoff map | 70 | 58.3% | catalog rows that are neither direct breaker rules nor non-breaker candidate refs |
| **total** | **120** | **100%** | all rows accounted exactly once |

Catalog section, hours, unit, and label similarity do not create engine coverage.
Map membership is exact-ref based.

### 4.2 Nonbinding design annotation of the 70 unmapped refs

This offline packet subdivides the 70 unmapped refs without changing runtime:

| Ledger class | Count | Runtime meaning |
|---|---:|---|
| `discovery_only_unmapped` | 6 | two standalone Meter/PQM refs and four Surge/SPD refs identified for discovery only |
| `catalog_only_unmapped` | 64 | no current takeoff map and no discovery annotation in this packet |

`Protective Relay (Multi-function w Meter)` remains one of the nine relay
scope-candidate refs. The ledger adds `meter_pqm_overlap_guard`; it does not
reclassify the ref as a standalone meter.

### 4.3 Exact mapped-family counts

| Engine family | Exact mapped refs | Current outcome |
|---|---:|---|
| breaker | 12 | direct matched rule when signature evidence is complete |
| relay | 9 | scope pending |
| GFP | 1 | scope pending |
| instrument transformer | 9 | scope pending or explicit catalog gap |
| switch/disconnect | 11 | scope pending or explicit catalog gap |
| transfer switch | 3 | scope pending or explicit catalog gap |
| transformer | 5 | scope pending or explicit catalog gap |

All 120 catalog rows are active and have no merge target on this baseline. That
does not prove catalog completeness or pricing authority.

## 5. Six-family readiness matrix

Readiness states mean:

- **present**: committed deterministic contract exists;
- **partial**: contract exists but leaves an admitted ambiguity or defect;
- **absent**: no product contract exists;
- **held**: authority or corpus evidence is explicitly missing.

| Family | Recognition and quantity | Candidate coverage | Standards / packaging / scope | Authority | Corpus | Gate 2 readiness |
|---|---|---|---|---|---|---|
| relay | **present**: device-first; distinct tagged devices; never per protective element | **partial**: 9 tiers; orphan ANSI 86/79/25/27/59/81 have no home | **partial**: application tier question exists; ATS/MTS and typed evidence are not resolved | **held**: `RELAY_R1_RATIFIED=false` | **absent** | **not ready** |
| GFP | **partial**: strong standalone/parent exclusion and distinct-device count; explicit non-LV contradiction is not rejected | **partial**: one ref; single-ref-covers-all convention unratified | **partial**: confirm question exists; family/standard/evidence contract absent | **held**: `GFP_R1_RATIFIED=false` | **absent** | **not ready** |
| instrument transformer | **present recognition / incomplete pricing quantity**: type, voltage, packaging evidence, and distinct-device count exist | **partial**: 9 refs; LV/HV PT gaps are explicit | **blocked**: individual/set conversion is unresolved and catalog set naming/unit is inconsistent | **held**: `ITX_R1_RATIFIED=false` | **absent** | **not ready; quantity design blocker** |
| switch/disconnect | **present**: device-first type/voltage/fused evidence; one physical device even when three-phase | **partial**: 11 refs; vacuum, LV non-fused/open, and several HV constructions are gaps | **partial**: construction/default and open/enclosed conventions remain unratified | **held**: `SWITCH_R1_RATIFIED=false` | **absent** | **not ready** |
| transfer switch | **present recognition**: tagged ATS/MTS/STS, automation, bypass, voltage, and distinct-device count | **partial with defect**: 3 refs; static/manual-bypass are gaps; functional-testing ref excluded; matcher does not enforce declared MV gap | **partial**: automatic/manual/bypass question exists; profile and MV rules unresolved | **held**: `TRANSFER_R1_RATIFIED=false` | **absent** | **not ready; MV leakage blocker** |
| transformer | **present**: guarded power-transformer recognition and distinct-device count | **partial**: 3 dry and 2 pad-mount-oil tiers; other liquid/LTC/adders remain gaps or deferrals | **partial**: tier/default/LTC and ATS/MTS decisions are not resolved | **held**: `R1_RATIFIED=false` | **absent** | **not ready** |

### 5.1 Cross-cutting blockers

1. all six family branches produce `scope_pending` or `catalog_gap`; only breaker
   rules enter `matchedLines`;
2. all six R1 estimating-authority flags are false;
3. `ScopePendingLine` carries candidates but no accepted ref, pricing profile,
   resolved quantity, line evidence hash, or authority receipt;
4. the merged emitter hardcodes `ATS` for matched breaker scopes;
5. instrument-transformer set/individual pricing quantity cannot be derived from
   current `qty` or `unit_of_issue`;
6. transfer-switch map data declares MV a gap, but the matcher does not examine
   voltage class;
7. GFP's LV-only convention does not currently reject contradictory MV/HV
   evidence;
8. current goldens use Gate 2 stand-ins, not a product resolver;
9. no governed rights-cleared corpus of completed accepted estimates proves any
   non-breaker ref/quantity/profile choice.

These are review findings, not implementation authorization.

## 6. Gate 2 candidate-contract delta

The proposed major-version sidecar is specified in:

`docs/superpowers/specs/2026-07-16-estimator-gate2-family-candidate-contract-delta.md`

It preserves the current report, binds the merged candidate projection and the
separately preserved remediation proposal, and adds:

- explicit recognized family and `(block, family)` pricing-profile scope;
- exact ref options and profile applicability;
- observed and allowed packaging;
- distinction between recognized device count and pricing quantity;
- stable typed scope questions;
- content-addressed line evidence without source bodies;
- canonical fractional bounding-box coordinates;
- candidate-set-scoped family authority over the complete policy projection;
- one-profile-per-block convergence for the merged one-scope-per-block emitter;
- closed-shape validation and exact versioned hash preimages.

It does not add Meter/PQM or Surge/SPD to the recognized-family union.

## 7. Discovery packets

- `docs/superpowers/packets/estimator-takeoff-meter-pqm-discovery.md`
- `docs/superpowers/packets/estimator-takeoff-surge-spd-discovery.md`

Both packets identify exact catalog candidates, present engine behavior, open
accounting/packaging/evidence questions, cross-family guards, corpus evidence
requirements, and explicit non-authorizations. Neither is a family-admission
packet.

## 8. Corpus-dependent priority recommendation

### 8.1 Current recommendation

**Select no next family from repository catalog coverage alone.** No governed
accepted-estimate corpus is present on this baseline, so a ranking would be an
implementation-convenience opinion rather than product evidence.

First admit the rights-cleared completed-estimate corpus required by the platform
audit. Then inventory every unresolved accepted apparatus occurrence against
this exact ledger.

### 8.2 Eligibility gate

A family is rankable only when the admitted corpus provides:

1. for every corpus case, a current, effective, unexpired, source-specific Rights
   Authority decision binding the exact register row/snapshot, source locator,
   owner/publisher/edition, artifact/content/release version, intended use,
   lawful-access and applicable permission/license basis, allowed and prohibited
   transformations, audience/distribution, conditions, re-review triggers, and
   affected target/content/release; missing, stale, superseded, revoked, expired,
   or scope-mismatched evidence excludes the entire case;
2. accepted source, artifact, Gate 1, Gate 2, and final-estimate evidence
   references for its occurrences;
3. accepted family/ref, pricing profile, inclusion, packaging, and quantity;
4. negative cross-family examples sufficient to measure collision risk;
5. deterministic parity to accepted hours and final cents under pinned catalog,
   compiler, and rate authority;
6. a bounded disposition for every corpus occurrence, including catalog gaps;
7. no unresolved implementation defect that can offer an invalid candidate set.

At this design date the appointed Rights Authority record is
`LEARN-RIGHTS-2026-07-11`; a future ranking must use that still-current
appointment or an explicitly superseding current appointment. An agent, packet
author, technical reviewer, producer-manifest flag, or source custodian cannot
substitute for the human Rights Authority decision.

The transfer-switch MV leak and the instrument-transformer quantity gap therefore
block those families even if corpus frequency is high until their contracts are
independently corrected and reviewed.

### 8.3 Ranking rule after eligibility

Rank eligible families lexicographically using corpus-derived measures, not
invented weights:

1. accepted unresolved labor-hour exposure, descending;
2. accepted distinct-device occurrence count, descending;
3. share of occurrences with complete positive evidence, descending;
4. candidate-ref ambiguity and catalog-gap rate, ascending;
5. packaging/quantity conversion uncertainty, ascending;
6. cross-family collision rate, ascending;
7. number of distinct accepted estimates represented, descending.

If otherwise tied, prefer one of the six already recognized families over a new
discovery family because its fail-closed recognition and regression surface
already exist. This tie-break does not ratify the family.

Meter/PQM or Surge/SPD becomes rankable only if corpus evidence shows material
accepted work that is currently unmapped and its family boundary, accounting,
packaging, quantity, and evidence decisions have been independently ratified.

### 8.4 Output of the future ranking

The ranking record must bind:

- corpus manifest and case hashes;
- exact Rights Authority appointment ID/schema/hash plus every admitted
  source-specific decision receipt ID/schema/hash, effective/expiry timestamps,
  disposition, conditions, re-review trigger, and bound register/source/
  owner/edition/artifact/content/release/intended-use scope;
- this ledger hash;
- catalog, compiler, producer, and rate hashes;
- exact metric values and exclusions;
- named technical-authority review;
- selected family or explicit no-selection outcome.

It is a recommendation receipt, not family implementation or pricing authority.

## 9. Independent-review checklist

Reviewers should verify:

1. ledger has exactly 120 unique refs in catalog source order and matches every
   projected catalog field exactly; ledger bytes are independently bound by the
   declared ledger SHA-256 rather than claimed identical to catalog bytes;
2. exact map membership yields 12 direct, 38 scope-candidate, and 70 unmapped;
3. the six `discovery_only_unmapped` annotations are within the 70 unmapped refs;
   the separate `meter_pqm_overlap_guard` annotation remains on the mapped relay
   ref and does not reclassify it;
4. all six R1 flags remain false and no family is described as priced;
5. transfer MV and GFP voltage findings are correctly characterized;
6. a future exporter leaves the exact merged report artifact bytes unchanged,
   emits the v2 sidecar separately, and does not reinterpret old hashes;
7. quantity semantics do not derive from ref spelling or `unit_of_issue`;
8. discovery packets do not create aliases, defaults, candidate kinds, or
   authority;
9. priority remains corpus-dependent and produces no current family selection;
10. exactly five design artifacts changed before bounded review; the only
    additional final artifact is the cross-engine review record.

## 10. Stop condition and non-authorizations

Stop here for independent review. This packet does not authorize implementation,
recognizer changes, `candidateKind` changes, family-map changes, catalog ref/hour
changes, authority-flag changes, schema, API, receipt, production, deployment,
source-body ingestion, dependency installation, push, PR, or family ratification.
