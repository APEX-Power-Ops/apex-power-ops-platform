# Estimator Gate 2 Family Candidate Contract Delta

Status: **CORRECTED OFFLINE DESIGN CANDIDATE / IMPLEMENTATION HOLD**
Date: 2026-07-16
GO boundary: `EST-TAKEOFF-CATALOG-COVERAGE-001`
Baseline: detached `origin/main@bdec885a5cd2862da7907054646c9c0fb5df5ef2`

## 1. Purpose

Define a nonbinding major-version candidate-set sidecar that makes block-scoped
pricing profile, family policy, packaging, quantity basis, scope questions, and
line evidence explicit and canonically hashable before any Gate 2 resolver is
implemented.

This is a contract delta only. It changes no recognizer, `candidateKind`, family
map, catalog row, authority flag, API, schema, receipt, runtime, or deployment.

## 2. Bound baselines

### 2.1 Merged baseline

Current `origin/main` has no Gate 2 resolver or persistence contract. The merged
candidate projection is `ScopePendingLine` and
`ReconciliationReport.scopePending[]`:

- `packages/estimator-takeoff/src/buckets/types.ts`;
- `packages/estimator-takeoff/src/runner/report.ts`.

It currently carries `lineKey`, optional tag, `qty`, `candidateRefs`, optional
`provisionalDefaultRef`, `r1Ratified`, one free-text `scopeQuestion`, and a few
family-specific observations. It does not carry an explicit family, complete
source evidence, pricing-profile options, packaging options, or quantity
conversion semantics. `scope_pending` prevents a clean result.

Current matched-line emission groups all matched families into one output scope
per block and fixes that scope to `ATS` in
`packages/estimator-takeoff/src/emit/emit.ts`. Because one `ScopeDraft` carries
one `neta_standard`, Gate 2 must make one coherent block-level profile decision;
independent family answers cannot silently become multiple standards in the same
output scope.

### 2.2 Preserved remediation candidate

The separately preserved dirty remediation tree contains a later, unmerged
candidate proposal. It is read-only input to this design, not repository
authority:

| File | SHA-256 |
|---|---|
| `packages/estimator-takeoff/src/workflow/types.ts` | `6cf9e9e3b3256f982d2376ad29a7432c54532b55530b3f741416661a0da2c156` |
| `packages/estimator-takeoff/src/workflow/contracts.ts` | `4374fc0224551dfef36554ef64e11e44df71b568e78172c502e36e8873b5bb1a` |

That proposal adds candidate-set context, `recognizedQuantity`, breaker locking,
decision receipts, ATS/MTS selection, packaging, and canonical hashes. Its
candidate object still lacks family-scoped standards, packaging options,
quantity basis, structured questions, and line-scoped evidence. This delta
preserves its fields conceptually but does not copy implementation into this
worktree.

### 2.3 Signed-overlay boundary

The current signed-overlay evidence schema is intentionally limited to the six
schema-placement census dimensions in the July 11 design. It rejects assignments
to catalogs or other fields and therefore must not be reused to ratify estimator
families. This delta adopts only its control principles: signatures attest exact
artifact-byte integrity, bind a base and schema hash, reject duplicates and drift
fail closed, and never confer implementation or execution authorization.

Any future estimator-family evidence overlay or authority receipt needs its own
separately reviewed schema, signer policy, base bindings, publication tooling,
and technical-authority acceptance. This packet does not define or publish one;
the current false R1 flags continue to block product resolution.

## 3. Versioning decision

Do not rewrite the current reconciliation-report artifact. A future exporter may
emit that exact report byte sequence unchanged and emit a separate sidecar with
a new major schema version. Byte identity applies to the report artifact itself,
not to a semantic reserialization, the catalog seed, or the coverage ledger:

```ts
interface Gate2CandidateSetV2 {
  schemaVersion: 'takeoff_gate2_candidate_set_v2'
  context: Gate2CandidateSetContextV2
  scopeOutputContract: Gate2ScopeOutputContractV2
  familyAuthorityBindings: readonly Gate2FamilyAuthorityBindingV2[]
  familyScopes: readonly FamilyStandardScopeV2[]
  candidates: readonly Gate2CandidateV2[]
  candidateSetHash: Sha256Hex
}
```

No v1 object or hash is reinterpreted as v2. If a v1 candidate or decision is
ever persisted, it remains bound to its original schema and hash domain. A v2
resolution requires a newly generated v2 candidate set.

## 4. Proposed exact shapes

```ts
type RecognizedFamily =
  | 'breaker'
  | 'relay'
  | 'gfp'
  | 'instrument_transformer'
  | 'switch_disconnect'
  | 'transfer_switch'
  | 'transformer'

type PricingProfile = 'ATS' | 'MTS'

type ScopeOutputMode = 'one_scope_per_block' | 'per_family_scope'

type CanonicalBboxCoordinate = string

type Gate2PackagingEvidenceCode =
  | 'none'
  | 'set_token'
  | 'set_of_3'
  | 'three_phase'
  | 'individual_token'
  | 'symbol_group'

interface Gate2CandidateSetContextV2 {
  gate1ReceiptId: Id
  gate1ReceiptHash: Sha256Hex
  gate1ReceiptSchemaVersion: 'apex.estimator-gate1-receipt/v1'
  gate1ReceiptStatus: 'accepted'
  gate1IsCurrent: true
  gate1EvidenceHash: Sha256Hex
  artifactSchemaVersion: 'apex.drawing-extraction/v1'
  artifactContentHash: Sha256Hex
  sourceReportSchemaVersion: 'apex.takeoff-reconciliation-report/v1'
  sourceReportContentHash: Sha256Hex
  sourceReportArtifactHash: Sha256Hex
  producerManifestSchemaVersion: 'apex.producer-manifest/v1'
  producerManifestHash: Sha256Hex
  upstreamHashContractVersion: 'apex.estimator-gate2-upstream-hashes/v1'
  coordinateCanonicalizationVersion: 'apex.bbox-jcs-binary64/v1'
  intakeScopeId: Id
  projectId: Id
  revisionId: Id
  lineSetId: Id
  candidateSetId: Id
  catalogVersion: string
  catalogHash: Sha256Hex
  compilerVersion: string
  compilerHash: Sha256Hex
  familyContractFiles: readonly Gate2FamilyContractFileV2[]
  familyContractManifestHash: Sha256Hex
}

interface Gate2FamilyContractFileV2 {
  repositoryPath: string
  contentHash: Sha256Hex
}

interface Gate2ScopeOutputContractV2 {
  schemaVersion: 'apex.estimator-scope-output-contract/v1'
  mode: ScopeOutputMode
  implementationVersion: string
  implementationHash: Sha256Hex
  perFamilyScopeAuthority: Gate2ScopeOutputAuthorityBindingV2 | null
}

interface Gate2AuthorizedFamilyScopeV2 {
  block: string
  family: RecognizedFamily
  familyAuthorityReceiptHash: Sha256Hex
}

interface Gate2ScopeOutputAuthorityBindingV2 {
  receiptId: Id
  receiptSchemaVersion: 'apex.estimator-scope-output-authority-receipt/v1'
  receiptHash: Sha256Hex
  receiptStatus: 'accepted'
  isCurrent: true
  projectId: Id
  revisionId: Id
  lineSetId: Id
  candidateSetId: Id
  authorizedScopes: readonly Gate2AuthorizedFamilyScopeV2[]
  implementationHash: Sha256Hex
  acceptedByPersonId: Id
  authorityAppointmentId: Id
  authorityAppointmentSchemaVersion: 'apex.authority-appointment/v1'
  authorityAppointmentHash: Sha256Hex
  acceptedAt: string
  effectiveAt: string
  expiresAt: string
  supersedesReceiptId: Id | null
  supersessionReason: string | null
}

interface Gate2FamilyAuthorityBindingV2 {
  authorityKey: string
  block: string
  family: RecognizedFamily
  contractId: Id
  contractSchemaVersion: 'apex.estimator-family-contract/v1'
  contractHash: Sha256Hex
  authorizedProjectionSetHash: Sha256Hex
  receiptId: Id
  receiptSchemaVersion: 'apex.estimator-family-authority-receipt/v1'
  receiptHash: Sha256Hex
  receiptStatus: 'accepted'
  isCurrent: true
  scopeKind: 'candidate_set'
  scopedProjectId: Id
  scopedRevisionId: Id
  scopedLineSetId: Id
  scopedCandidateSetId: Id
  upstreamHashContractVersion: 'apex.estimator-gate2-upstream-hashes/v1'
  gate1EvidenceHash: Sha256Hex
  artifactContentHash: Sha256Hex
  sourceReportContentHash: Sha256Hex
  sourceReportArtifactHash: Sha256Hex
  catalogHash: Sha256Hex
  compilerHash: Sha256Hex
  familyContractManifestHash: Sha256Hex
  allowedScopeOutputModes: readonly ScopeOutputMode[]
  breakerAuthorityMode: 'not_applicable' | 'locked_ref_requires_family_authority'
  acceptedByPersonId: Id
  authorityAppointmentId: Id
  authorityAppointmentSchemaVersion: 'apex.authority-appointment/v1'
  authorityAppointmentHash: Sha256Hex
  acceptedAt: string
  effectiveAt: string
  expiresAt: string
  supersedesReceiptId: Id | null
  supersessionReason: string | null
}

interface FamilyStandardScopeV2 {
  standardScopeKey: string
  familyAuthorityKey: string
  block: string
  family: RecognizedFamily
  canonicalNetaSectionProposal: string | null
  pricingProfileOptions: readonly ['ATS', 'MTS']
  scopeQuestionCode: string
  scopeQuestion: string
  familyScopeHash: Sha256Hex
}

interface Gate2CandidateV2 {
  // Existing merged/remediation concepts retained:
  lineKey: string
  sourceLineHash: Sha256Hex
  candidateRefs: readonly string[]
  candidateSetHash: Sha256Hex
  recognizedQuantity: number
  lockedBreakerRef: string | null
  provisionalDefaultRef: string | null
  r1Ratified: boolean

  // Proposed delta:
  family: RecognizedFamily
  block: string
  familyAuthorityKey: string
  familyContractProjectionHash: Sha256Hex
  standardScopeKey: string
  refOptions: readonly Gate2RefOptionV2[]
  packagingOptions: readonly Gate2PackagingOptionV2[]
  observedPackaging: Gate2ObservedPackagingV2
  quantityBasis: Gate2QuantityBasisV2
  scopeQuestions: readonly Gate2ScopeQuestionV2[]
  evidenceRefs: readonly Gate2EvidenceRefV2[]
  candidateContentHash: Sha256Hex
}

interface Gate2RefOptionV2 {
  ref: string
  lifecycleStatus: 'active'
  catalogUnit: 'each' | 'set'
  profileApplicability: Readonly<{
    ATS: { section: string | null; supported: boolean }
    MTS: { section: string | null; supported: boolean }
  }>
  packagingOptionIds: readonly string[]
}

interface Gate2PackagingOptionV2 {
  optionId: string
  label: string
  applicableRefs: readonly string[]
  pricingUnitRule:
    | 'one_catalog_each_per_device'
    | 'one_catalog_set_per_package'
    | 'operator_resolved_conversion'
  packageSize: number | null
  proposedPricingQuantity: number | null
  conversionEvidenceInputIndices: readonly number[]
}

interface Gate2ObservedPackagingV2 {
  evidenceCode: Gate2PackagingEvidenceCode
  evidenceInputIndices: readonly number[]
  observedOptionId: string | null
  phaseCount: number | null
  requiresExplicitDecision: boolean
}

interface Gate2QuantityBasisV2 {
  recognitionUnit: 'distinct_device'
  recognizedQuantity: number
  resolutionMode: 'fixed_one_to_one' | 'select_packaging_option'
  conversionEvidenceRequired: boolean
}

interface Gate2ScopeQuestionV2 {
  code: string
  prompt: string
  required: boolean
  answerKind: 'pricing_profile' | 'ref' | 'packaging' | 'quantity' | 'inclusion'
  optionIds: readonly string[]
}

interface Gate2EvidenceRefV2 {
  inputIndex: number
  lineKey: string
  sheet: string
  page: number
  bbox: readonly [CanonicalBboxCoordinate, CanonicalBboxCoordinate,
    CanonicalBboxCoordinate, CanonicalBboxCoordinate]
  evidenceKind: 'one-line' | 'panel-schedule' | 'switchgear-schedule' | 'power-plan'
  role: 'counted' | 'supporting'
  sourceRowHash: Sha256Hex
}
```

The types are a review target, not code authorized by this packet.

The accepted Gate 1 reference is indivisible. A candidate-set validator requires
the exact receipt ID, receipt hash, receipt schema version, literal accepted
status, literal currentness, and evidence hash. The current browser-only Gate 1
export on `origin/main` is not an authoritative accepted/current server receipt,
so it cannot satisfy a product v2 candidate context. It may feed only an
explicitly non-product offline preview until a separately authorized Gate 1
receipt contract exists.

## 5. Field semantics

### Family and standard scope

`family` is limited to the seven families already recognized by the current
engine. Meter/PQM and Surge/SPD are not added. `FamilyStandardScopeV2` is a
candidate-policy/question grouping keyed by `(block, family)`; it is not by
itself permission to emit a separate `ScopeDraft`. Every family scope and every
candidate carries the same `familyAuthorityKey`, which must resolve to exactly
one valid authority binding with the same block and family.

`familyContractFiles` is the canonical, path-sorted dependency manifest for
family candidate generation. It contains unique repository-relative paths and
SHA-256 hashes of exact file bytes. On this baseline it must include all seven
`src/catalog/*-map.data.ts` files, all seven corresponding `*-map.ts` matcher
files, and every additional transitive source dependency that can change family,
candidate-ref order, provisional default, ratification state, or catalog-gap
behavior. An accepted takeoff-compiler build-provenance contract must prove that
closure; the extraction `producerManifestHash` does not. No such
compiler-provenance contract exists on this baseline, which is an additional
implementation hold. An unlisted dependency or byte drift fails validation. The
validator recomputes
`familyContractManifestHash` from the declared entries and requires exact
equality. `compilerHash` separately hashes the exact built candidate-compiler
artifact bytes, not a version label.

The dependency manifest and an R1 boolean prove code identity only; neither is
estimating authority. For every `(block, family)` represented in a candidate set,
the validator must load the exact family-contract bytes identified by
`contractId`, validate schema `apex.estimator-family-contract/v1`, recompute
`contractHash`, and verify the current accepted authority receipt identified by
the binding. The contract must define the complete ref, standard, packaging,
quantity-conversion, scope-question, and output-mode policy. Candidate generation
must derive those policy fields from that contract without additions, omissions,
or defaults outside it. Source-specific observed packaging and recognized
quantity derive from the bound evidence under the pinned compiler; the contract
defines how those observations project into allowed options and proposed pricing
quantities, and the candidate-set-scoped authority receipt accepts the exact
resulting projection.

`familyContractProjectionHash` binds the complete candidate policy projection:
the linked family scope, ref options, all packaging options including conversion
evidence requirements and proposed pricing quantities, quantity basis, and every
scope-question template. The authority receipt binds
`authorizedProjectionSetHash`, the ordered set of those projection hashes for
its exact `(block, family)`. A contract hash without a current accepted receipt,
or a receipt that does not bind the exact projection set, is insufficient.

A valid family authority binding is accepted, current, effective, unexpired at
resolution time, signed or otherwise verified under the separately ratified
receipt contract, and issued by the person named by the hash-bound authority
appointment. It must bind the candidate family, exact contract and projection
hashes, Gate 1 evidence, artifact/report content and report bytes, upstream hash
registry, catalog/compiler/family-dependency hashes, permitted output modes, and
exact project/revision/line-set/candidate-set scope. V2 deliberately does not
treat a globally accepted policy template as acceptance of source-specific
observed packaging or computed quantities. A reusable global receipt would need
a different non-candidate-specific projection contract and a new reviewed
version.
The candidate set's selected `scopeOutputContract.mode` must be an exact member
of every represented family's `allowedScopeOutputModes`.

Scope mismatch, supersession, revocation, appointment drift, expiry, or an
unrecognized receipt/preimage version fails closed. No family on this baseline
has such a receipt; all current false R1 flags remain an additional hold rather
than a substitute for one.

Use `pricingProfile`, not an unqualified `standard`, in future decision shapes so
`MTS` cannot be confused with a manual transfer switch. The canonical NETA
section is a cited proposal from the family design, not a mapping key. Exact ref
membership remains authoritative because current family maps document section
drift and overload.

### ScopeDraft output contract

The merged output contract creates exactly one native scope per block and each
`ScopeDraft` has one `neta_standard`. Therefore
`scopeOutputContract.mode:'one_scope_per_block'` is the only mode compatible with
this baseline. All accepted family pricing-profile answers in a block must equal
one block decision; the resolver emits that profile once for the block. Any
conflicting family answers, missing family answer, or attempted silent
last-writer/default merge blocks resolution and envelope emission.

`per_family_scope` is not enabled merely because candidate questions are grouped
by family. It is valid only when all of the following are true:

1. `scopeOutputContract.perFamilyScopeAuthority` is a current accepted,
   effective, unexpired receipt whose project/revision/line-set/candidate-set,
   exact authorized `(block, family)` pairs, authority appointment, and
   implementation hash match exactly; every authorized pair must carry the exact
   corresponding family-authority receipt hash, and the authorized-pair set must
   equal the candidate set's complete family-scope set with no omission or extra;
2. every affected family authority binding explicitly includes
   `per_family_scope` in `allowedScopeOutputModes`;
3. the bound implementation contract deterministically emits one distinct scope
   per `(block, family)` with collision-free IDs/names and complete line
   assignment; and
4. that implementation exists under the bound hash.

The current emitter satisfies none of those per-family conditions, so a v2
validator on this baseline must reject that mode. Its one-scope-per-block
cardinality is evidence only: its hard-coded `ATS` value is not a valid v2 output
implementation. For
`one_scope_per_block`, `perFamilyScopeAuthority` must be `null`; a stray receipt
cannot widen the output contract.

### Breaker authority

The exact `BREAKER_MAP` replay and `lockedBreakerRef` establish deterministic
mechanical ref selection only. They do not authorize ATS/MTS choice, catalog-hour
use, packaging, quantity, price, resolution, or emission. A breaker candidate
requires the same valid family-contract and authority-receipt checks as every
other family, with
`breakerAuthorityMode:'locked_ref_requires_family_authority'`. The accepted
contract may authorize the locked ref's policy projection but may never change
the ref. A non-breaker binding must use `breakerAuthorityMode:'not_applicable'`.
Without valid breaker family authority, the matched breaker remains evidence in
the candidate set and cannot enter a v2 resolved or emitted product path.

### Ref options

`candidateRefs` and `refOptions[].ref` must be identical and in identical order.
Every ref must exist in the bound catalog snapshot, be active, and remain within
the candidate family map. They must also equal the replayed compiler line's exact
candidate-ref projection in exact order: the bound report's
`scopePending[].candidateRefs` for a scope-pending line, or the singleton matched
report ref for a breaker line. Every counted scope-pending disposition must carry
the same ordered group. Each option's `lifecycleStatus`, `catalogUnit`, and ATS/MTS
section must exactly equal the bound catalog row. `supported` is true if and only
if that profile has both a non-null section and a finite positive hours value in
the bound catalog; hours are not copied into this candidate contract.

For a breaker candidate, `lockedBreakerRef` is non-null, resolves to exactly one
active `candidateRefs`/`refOptions` member, equals the ref on every counted
`matched` report disposition, and must equal the selected ref in any resolution.
For every non-breaker candidate it is `null`. `provisionalDefaultRef` is `null` or
resolves to exactly one candidate ref; it never bypasses an answer.
`r1Ratified` must equal the literal flag in the bound family contract rather than
a producer-supplied assertion.

### Packaging

Packaging is never inferred from ref spelling or `unit_of_issue`. Candidate
generation records observed evidence and a closed list of packaging option
objects. Every `refOptions[].packagingOptionIds` entry must identify exactly one
candidate packaging option, and every packaging option's `applicableRefs` must be
a nonempty subset of `candidateRefs`. Those two link arrays must encode the same
relation: a ref lists an option ID if and only if that option lists the ref. A
selected ref and selected packaging option must share that declared link in both
directions. A required packaging question must be explicitly answered even when
one provisional option exists. `not_applicable` is an explicit option where a
family contract allows it; missing data is not equivalent to not applicable.
`observedPackaging.observedOptionId` is either `null` or identifies exactly one
option in the same candidate's closed `packagingOptions`; observed evidence never
creates an undeclared option.

`one_catalog_each_per_device` may apply only to refs whose bound `catalogUnit` is
`each`; `one_catalog_set_per_package` may apply only to refs whose bound unit is
`set`. An option spanning mixed units, or intentionally converting a set-named
`each` catalog row, must use `operator_resolved_conversion` with the required
evidence and explicit decision. A fixed rule/unit mismatch is rejected rather
than interpreted from ref spelling.

### Quantity basis

The existing quantifier's `qty` means distinct counted apparatus. It is not
automatically pricing quantity. Most current family proposals are 1:1 device
economics, but instrument-transformer candidates expose why the distinction is
required: set-named catalog refs do not consistently use catalog unit `set`.

`Gate2CandidateV2.recognizedQuantity` must exactly equal
`quantityBasis.recognizedQuantity`, the bound compiler line's `qty`, the matching
bound report `scopePending[].qty` when present, and the number of complete
`role:counted` evidence refs/report dispositions for that line. A fixed one-to-one
basis requires every packaging option to propose that same positive integer. A
packaging-selected basis requires each admissible option to carry its own pricing
rule, package size, and proposed pricing quantity. `packageSize` means the
positive safe-integer number of recognized apparatus units represented by one
catalog pricing unit.
For `one_catalog_each_per_device`, it must equal `1`. For every resolved option,
`recognizedQuantity % packageSize` must equal zero and
`proposedPricingQuantity` must exactly equal
`recognizedQuantity / packageSize` as a positive safe integer. An
`operator_resolved_conversion` uses the same arithmetic only after cited evidence
establishes the package size. Unknown package size, zero or unsafe values,
conflicting evidence, a non-integral quotient, or any mismatched proposed
quantity requires both `packageSize:null` and `proposedPricingQuantity:null` for
that unresolved option and blocks its selection. Every package conversion must
be evidence-backed and explicitly accepted. Each
`conversionEvidenceInputIndices` member must resolve to exactly one evidence ref
in the same candidate. A resolved option requires a nonempty evidence list when
`conversionEvidenceRequired` is true, its rule is
`operator_resolved_conversion`, or its package size is not `1`; the cited source
rows must support the exact divisor under the bound compiler. A fixed 1:1 option
may use an empty conversion-evidence list only when the exact complete projection
is present in the loaded family contract and its current accepted authority
receipt binds the resulting projection-set hash.

### Scope questions

Replace the single free-text question as the authority contract with stable,
typed questions. Human-readable prompts remain hashed evidence; question codes
and answer kinds control completeness. A provisional default is a display hint
only and never an accepted answer.

Every candidate must contain exactly one required `pricing_profile` question
whose code, prompt, and `['ATS', 'MTS']` option order exactly equal its uniquely
linked `FamilyStandardScopeV2`. The bound family contract must expose the complete
canonical ordered question-template projection for each replayed line. Candidate
questions must equal that projection field-for-field on `code`, `prompt`,
`required`, `answerKind`, and ordered `optionIds`; no template may be omitted,
added, weakened, or rewritten. An empty, substituted, or duplicated
standard-scope question fails validation.

### Evidence

Evidence references bind candidates to the already accepted artifact without
embedding proprietary source bodies. The sidecar carries location metadata and
row hashes only. The set-level context binds the artifact, producer manifest,
Gate 1 receipt, report, catalog, compiler, and family-contract dependency
manifest.

Fractional bounding-box coordinates use
`coordinateCanonicalizationVersion:'apex.bbox-jcs-binary64/v1'`. Each source JSON
coordinate is parsed as an IEEE 754 binary64 value, must be finite, and must not
be negative zero. It is serialized using the exact ECMAScript number
serialization required by RFC 8785 (June 2020) section 3.2.2.3, with no extension
or implementation-specific rounding, and carried in the sidecar as that ASCII
string. Thus `10`, `0.125`, and an RFC-8785-required exponent form are strings in
the Gate 2 token encoder, never fractional numeric tokens. Numeric equality,
fixed decimal scales, locale formatting, trailing-zero preservation, and
producer-chosen precision are not accepted substitutes. The report disposition,
artifact row, evidence ref, and source-row preimage must compare the four
canonical coordinate strings exactly and in order.

Each evidence ref must match exactly one disposition in the bound source report
on `inputIndex`, `lineKey`, `sheet`, `page`, `bbox`, and evidence kind. Its
`lineKey` must exactly equal the enclosing candidate's `lineKey`. `role:counted`
maps only to a `matched` or `scope_pending` disposition; `role:supporting` maps
only to an `associated_source` disposition. A candidate's evidence refs are the
complete one-for-one projection of those three admissible disposition statuses
for its line key: no report member may be omitted, borrowed from another line,
or added. The row hash must also recompute from the same indexed row in the bound
artifact.

The validator replays the exact compiler identified by `compilerHash` over the
accepted artifact and Gate 1 inputs. It requires one compiler line whose
`lineKey`, recognized family, emitted `block`, quantity, counted member indices,
and associated-source indices exactly equal the candidate projection. Family is
the replayed signature kind, with the contract's explicit
`switch`-to-`switch_disconnect` name mapping; block is the replayed matched or
scope-pending line block, including the current block-or-sheet fallback. The
recomputed `sourceLineHash` below must equal the declared value. A candidate
cannot relabel valid evidence under another family or block.

Before projecting any candidate, the validator hashes the exact in-hand report
artifact bytes to `sourceReportArtifactHash`, parses those same bytes under the
bound report schema, and reproduces `sourceReportContentHash` from the parsed
document. The replay must then regenerate the complete reconciliation-report
document and reproduce that content hash exactly; it never rewrites the bound
report artifact to make the hashes agree. The unique eligible
line-key set independently derived from replay output must equal the unique
eligible line-key set independently derived from the bound report, including
status and counted/associated membership. Any compiler-only or report-only line,
status difference, or membership difference invalidates the entire set.

Candidate-set membership is a bijection, not a producer-selected subset. The
eligible replayed line set is every unique bound-report line key having at least
one `matched` disposition or at least one `scope_pending` disposition. Every such
line produces exactly one v2 candidate, and every v2 candidate resolves to one
such line. Current catalog-gap and other unmatched lines produce no candidate but
remain in the bound report and block complete-envelope emission. Missing,
duplicate, or extra candidates invalidate the set before hashing.

`observedPackaging.evidenceInputIndices` is another closed projection of the
same candidate evidence refs. `evidenceCode:'none'` requires an empty list plus
`observedOptionId:null` and `phaseCount:null`. Every other evidence code requires
a nonempty list, and the cited bound source rows must deterministically produce
that exact code and phase count under the bound compiler. Every observed or
conversion evidence index therefore resolves to a specific same-line report
disposition and artifact row; a free-floating code is invalid.

## 6. Family-scoped proposal matrix

These rows summarize existing family-design proposals; they do not ratify them.

| Family | Section proposal | Packaging question | Quantity proposal | Required scope decision |
|---|---|---|---|---|
| breaker | `7.6` family context | explicit `not_applicable` unless a later breaker contract says otherwise | distinct device, 1:1 catalog `each` | ATS/MTS profile; locked ref cannot change |
| relay | `7.9` | explicit `not_applicable` | distinct relay device, never per protective element | application tier, inclusion, ATS/MTS |
| GFP | `7.14` | explicit `not_applicable` | standalone device, proposed 1:1 | confirm standalone scope and exact ref |
| instrument transformer | `7.10` proposal; catalog section is noisy | `individual`, `set`, or unresolved | per-ref conversion; unresolved set evidence blocks | type, packaging, quantity, ref, ATS/MTS |
| switch/disconnect | `7.5` | construction is a ref axis, not silently packaging | one physical device even when three-phase | voltage/type/construction ref and ATS/MTS |
| transfer switch | `7.22.3` proposal | base versus iso-bypass evidence must be explicit | distinct device, proposed 1:1 | automatic/manual, bypass, ref, ATS/MTS |
| transformer | `7.2` | explicit `not_applicable`; test tier remains separate | distinct transformer, proposed 1:1 | dry/oil tier, LTC scope, ref, ATS/MTS |

No matrix row is resolution-ready until its complete projection is derived from
the exact family contract and covered by a valid authority binding. The breaker
row's locked ref is not an exception.

## 7. Canonical ordering and hashing

Every nested object is closed-shape and exact-version validated. Reject unknown
keys, unknown enum values, coercions, duplicate refs, duplicate question codes,
duplicate evidence indices, duplicate candidate identities
`(standardScopeKey, lineKey)`, duplicate family-scope identities `(block,
family)`, duplicate family-authority identities or receipt IDs, duplicate
family-contract paths, duplicate scope-output authorized `(block, family)`
pairs, duplicate permitted output modes, non-positive quantities, and
noncanonical ordering. Authority scope arrays must be nonempty, supersession ID
and reason must be both null or both nonempty, and authority timestamps must be
canonical UTC instants satisfying `acceptedAt <= effectiveAt <= operationTime <
expiresAt`.

Canonical order:

1. pricing profiles: `ATS`, then `MTS`;
2. scope-output authorized scopes: `(block, family)` with the corresponding
   family-authority receipt hash; permitted output modes: `one_scope_per_block`,
   then `per_family_scope`;
3. family-authority bindings: `(block, family, authorityKey)`;
4. family-contract files: `repositoryPath`;
5. family scopes: `(block, family, standardScopeKey)`;
6. candidates: `(standardScopeKey, lineKey)`;
7. candidate refs and ref options: the exact candidate-map order, with both arrays
   identical; this binds any ranking/display semantics;
8. packaging options: stable option-ID order defined by the family contract;
9. scope questions: stable question-code order defined by the family contract;
10. evidence: `(inputIndex, lineKey, role, sourceRowHash)`.

All string comparisons use unsigned lexicographic comparison of UTF-8 bytes, not
locale collation. Hash inputs use this exact recursive byte encoding:

```text
null     -> n
false    -> b0
true     -> b1
integer  -> i<INT>;
string   -> s<COUNT>:<UTF-8 bytes>
array    -> a<COUNT>:[<encoded element 0>...<encoded element N>]

INT      -> 0 | -?[1-9][0-9]*
COUNT    -> 0 | [1-9][0-9]*
```

Only nulls, booleans, safe integers, strings, and arrays enter a hash preimage.
Objects are first projected into the fixed-order token arrays specified here.
Numbers with fractions, negative zero, non-finite values, Unicode normalization,
or implicit string coercion are rejected. Integers are limited to
`[-9007199254740991, 9007199254740991]`. `INT`, string byte lengths, and array
counts have no leading zero, leading plus, whitespace, or alternate spelling;
zero is exactly `0`. Strings must be valid Unicode scalar sequences and are
hashed as supplied strict UTF-8; unpaired surrogates and silent normalization are
rejected. SHA-256 output is lowercase 64-character hexadecimal text.

### 7.1 Upstream hash contract registry

`upstreamHashContractVersion:'apex.estimator-gate2-upstream-hashes/v1'`
selects the following closed registry. No hash may be treated as an opaque string
or reinterpreted under a different serializer. If an implementation cannot load
the exact schema/preimage version, it rejects the candidate set.

`RAW_SHA256(bytes)` means SHA-256 over the exact in-hand bytes, with no newline,
prefix, decoding, reserialization, or second read. `CanonicalEncode(value)`
means the recursive encoder defined above.

| Hash field | Exact preimage contract |
|---|---|
| `gate1ReceiptHash` | imported `apex.estimator-gate1-receipt/v1` array below; UTF-8 `JSON.stringify`, then SHA-256 |
| `gate1EvidenceHash` | `apex.estimator-gate1-evidence-hash/v1` composite below |
| `artifactContentHash` | `GATE1_CONTENT_SHA256` of the accepted `apex.drawing-extraction/v1` artifact document |
| `sourceReportContentHash` | `GATE1_CONTENT_SHA256` of the parsed report document, which must validate exact schema `apex.takeoff-reconciliation-report/v1` |
| `sourceReportArtifactHash` | `RAW_SHA256` of the exact report artifact bytes supplied beside the v2 sidecar; parsing those same bytes must produce the document hashed by `sourceReportContentHash` |
| `producerManifestHash` | `RAW_SHA256` of the accepted `apex.producer-manifest/v1` manifest bytes |
| `catalogHash` | `RAW_SHA256` of the exact immutable catalog-snapshot bytes identified by `catalogVersion`; on this baseline that is `equipment-models.seed.json` |
| `compilerHash` | `RAW_SHA256` of one deterministic executable compiler bundle identified by `compilerVersion`; a version label or source commit alone is invalid |
| `familyContractFiles[].contentHash` | `RAW_SHA256` of the exact repository file bytes at the bound checkout |
| `contractHash` | `RAW_SHA256` of the exact accepted family-contract artifact bytes; parsing those same bytes must validate exact schema `apex.estimator-family-contract/v1` |
| `authorityAppointmentHash` | `RAW_SHA256` of the exact accepted authority-appointment artifact bytes under its versioned appointment schema |
| family `receiptHash` | `apex.estimator-family-authority-receipt/v1` token preimage below |
| scope-output `receiptHash` | `apex.estimator-scope-output-authority-receipt/v1` token preimage below |
| `implementationHash` | `RAW_SHA256` of the exact deterministic output-implementation bundle identified by `implementationVersion` |

Schema provenance is also closed. `apex.drawing-extraction/v1` is imported from
merged `packages/estimator-takeoff/src/extraction/types.ts` SHA-256
`61395d28c19b0f496487ed4b74617949b29e4a8da5a23e6e3d56f71bee612f53`.
`apex.takeoff-reconciliation-report/v1` is the design-local name for the exact
closed JSON projection of merged `packages/estimator-takeoff/src/runner/report.ts`
SHA-256 `581313acdddfe96400aa05b7b9700492db5fc6964c2b20a3cbe9c15494c4bba7`;
the merged report does not claim that version itself. `apex.producer-manifest/v1`
is imported only from preserved unmerged `src/extraction/manifest.ts` SHA-256
`c964b243c3b054f2e76bbf4c143774132badaaeb620b81dcc5a3ce6e049d53f3`.
The family-contract and authority-receipt schemas proposed here are not accepted
schemas on the baseline. Their absence blocks validation rather than permitting
an implementation to infer a shape from these TypeScript review sketches.

`GATE1_CONTENT_SHA256` imports the merged browser Gate 1 algorithm, pinned to
`apps/operations-web/lib/gate1-canonical.ts` SHA-256
`93b2729430a3ed108fbc82d8156693f6657bb7bc7c3f6e8efe4610f6a3f30ebc`
and its call site `apps/operations-web/lib/gate1.ts` SHA-256
`ab5541bc5487a28b17fb0f965c953351793eae42b69f4bd4648d9c61f7932b76`:

```text
GATE1_CONTENT_SHA256(document) = SHA256(UTF8(JSON.stringify(sortDeep(document))))

sortDeep(array)  = array.map(sortDeep), preserving array order
sortDeep(object) = a new null-prototype object whose own enumerable string keys
                   are inserted in default ECMAScript Array.sort order, with
                   each value recursively sortDeep-transformed
sortDeep(value)  = value for every JSON primitive
```

Inputs must first pass their exact closed JSON schema and contain no `undefined`,
functions, symbols, bigints, non-finite numbers, negative zero, or unpaired
surrogates. The import preserves the baseline algorithm; it does not relabel it
as RFC 8785. Gate 1 assertions are already embedded in the accepted artifact and
therefore need no second opaque assertion-set hash.

The Gate 1 receipt import is pinned to the preserved remediation proposal:
`workflow/types.ts` SHA-256
`6cf9e9e3b3256f982d2376ad29a7432c54532b55530b3f741416661a0da2c156`
and `workflow/contracts.ts` SHA-256
`4374fc0224551dfef36554ef64e11e44df71b568e78172c502e36e8873b5bb1a`.
It is exact input, not merged authority; product v2 remains blocked until the
receipt contract itself is accepted. In the imported v1 names,
`artifactHash == artifactContentHash` and `evidenceHash == gate1EvidenceHash`.
Its preimage is:

```text
SHA256(UTF8(JSON.stringify([
  "apex.estimator-gate1-receipt/v1",
  receiptId, receiptStatus, isCurrent,
  intakeScopeId, projectId, revisionId, lineSetId,
  artifactSchemaVersion, producerManifestSchemaVersion,
  artifactContentHash, producerManifestHash, gate1EvidenceHash,
  acceptedByPersonId, capabilityGrantId, acceptedAt, idempotencyKey,
  supersedesReceiptId, supersessionReason
])))

gate1EvidenceHash = SHA256(CanonicalEncode([
  "apex.estimator-gate1-evidence-hash/v1",
  artifactSchemaVersion,
  artifactContentHash,
  producerManifestSchemaVersion,
  producerManifestHash,
  sourceReportSchemaVersion,
  sourceReportContentHash,
  sourceReportArtifactHash
]))
```

Every version/hash pair above is recomputed before candidate validation. In
particular, a Gate 1 receipt whose embedded evidence hash does not equal the
composite above fails even if its own receipt hash is internally valid.

`sourceRowHash` uses the same encoding and this exact preimage:

```text
SHA256(CanonicalEncode([
  "apex.takeoff.source-row/v1",
  artifactContentHash,
  inputIndex,
  raw,
  tag ?? null,
  sheet,
  page,
  [canonicalBbox0, canonicalBbox1, canonicalBbox2, canonicalBbox3],
  evidenceKind,
  busVoltageV ?? null,
  block ?? null,
  mountingHint ?? null,
  candidateKind ?? null
]))
```

The sidecar carries only the resulting hash and location metadata; it does not
embed `raw` or another proprietary source body. Unknown artifact-row keys are
rejected before this projection rather than retained outside the hash.

The following are the exact object projections. Each named `...Tokens` value is
the displayed array, and plural projections are arrays produced in the canonical
order from this section. No field is omitted, inserted, renamed, or reordered:

```text
familyContractFileTokens(context) = context.familyContractFiles.map(file => [
  file.repositoryPath,
  file.contentHash
])

scopeOutputAuthorityPayloadTokens(authority) = [
  authority.receiptId,
  authority.receiptSchemaVersion,
  authority.receiptStatus,
  authority.isCurrent,
  authority.projectId,
  authority.revisionId,
  authority.lineSetId,
  authority.candidateSetId,
  authority.authorizedScopes.map(scope => [
    scope.block,
    scope.family,
    scope.familyAuthorityReceiptHash
  ]),
  authority.implementationHash,
  authority.acceptedByPersonId,
  authority.authorityAppointmentId,
  authority.authorityAppointmentSchemaVersion,
  authority.authorityAppointmentHash,
  authority.acceptedAt,
  authority.effectiveAt,
  authority.expiresAt,
  authority.supersedesReceiptId,
  authority.supersessionReason
]

scopeOutputAuthorityBindingTokens(authority) = [
  scopeOutputAuthorityPayloadTokens(authority),
  authority.receiptHash
]

scopeOutputContractTokens(contract) = [
  contract.schemaVersion,
  contract.mode,
  contract.implementationVersion,
  contract.implementationHash,
  contract.perFamilyScopeAuthority == null
    ? null
    : scopeOutputAuthorityBindingTokens(contract.perFamilyScopeAuthority)
]

familyAuthorityReceiptPayloadTokens(binding) = [
  binding.authorityKey,
  binding.block,
  binding.family,
  binding.contractId,
  binding.contractSchemaVersion,
  binding.contractHash,
  binding.authorizedProjectionSetHash,
  binding.receiptId,
  binding.receiptSchemaVersion,
  binding.receiptStatus,
  binding.isCurrent,
  binding.scopeKind,
  binding.scopedProjectId,
  binding.scopedRevisionId,
  binding.scopedLineSetId,
  binding.scopedCandidateSetId,
  binding.upstreamHashContractVersion,
  binding.gate1EvidenceHash,
  binding.artifactContentHash,
  binding.sourceReportContentHash,
  binding.sourceReportArtifactHash,
  binding.catalogHash,
  binding.compilerHash,
  binding.familyContractManifestHash,
  binding.allowedScopeOutputModes,
  binding.breakerAuthorityMode,
  binding.acceptedByPersonId,
  binding.authorityAppointmentId,
  binding.authorityAppointmentSchemaVersion,
  binding.authorityAppointmentHash,
  binding.acceptedAt,
  binding.effectiveAt,
  binding.expiresAt,
  binding.supersedesReceiptId,
  binding.supersessionReason
]

familyAuthorityBindingTokens(binding) = [
  familyAuthorityReceiptPayloadTokens(binding),
  binding.receiptHash
]

orderedFamilyAuthorityBindingTokens = familyAuthorityBindings
  .map(binding => familyAuthorityBindingTokens(binding))

contextTokens(context) = [
  context.gate1ReceiptId,
  context.gate1ReceiptHash,
  context.gate1ReceiptSchemaVersion,
  context.gate1ReceiptStatus,
  context.gate1IsCurrent,
  context.gate1EvidenceHash,
  context.artifactSchemaVersion,
  context.artifactContentHash,
  context.sourceReportSchemaVersion,
  context.sourceReportContentHash,
  context.sourceReportArtifactHash,
  context.producerManifestSchemaVersion,
  context.producerManifestHash,
  context.upstreamHashContractVersion,
  context.coordinateCanonicalizationVersion,
  context.intakeScopeId,
  context.projectId,
  context.revisionId,
  context.lineSetId,
  context.candidateSetId,
  context.catalogVersion,
  context.catalogHash,
  context.compilerVersion,
  context.compilerHash,
  familyContractFileTokens(context),
  context.familyContractManifestHash
]

familyScopeTokens(scope) = [
  scope.standardScopeKey,
  scope.familyAuthorityKey,
  scope.block,
  scope.family,
  scope.canonicalNetaSectionProposal,
  ["ATS", "MTS"],
  scope.scopeQuestionCode,
  scope.scopeQuestion
]

refOptionTokens(candidate) = candidate.refOptions.map(option => [
  option.ref,
  option.lifecycleStatus,
  option.catalogUnit,
  [
    ["ATS", option.profileApplicability.ATS.section,
      option.profileApplicability.ATS.supported],
    ["MTS", option.profileApplicability.MTS.section,
      option.profileApplicability.MTS.supported]
  ],
  option.packagingOptionIds
])

packagingOptionTokens(candidate) = candidate.packagingOptions.map(option => [
  option.optionId,
  option.label,
  option.applicableRefs,
  option.pricingUnitRule,
  option.packageSize,
  option.proposedPricingQuantity,
  option.conversionEvidenceInputIndices
])

observedPackagingTokens(candidate) = [
  candidate.observedPackaging.evidenceCode,
  candidate.observedPackaging.evidenceInputIndices,
  candidate.observedPackaging.observedOptionId,
  candidate.observedPackaging.phaseCount,
  candidate.observedPackaging.requiresExplicitDecision
]

quantityBasisTokens(candidate) = [
  candidate.quantityBasis.recognitionUnit,
  candidate.quantityBasis.recognizedQuantity,
  candidate.quantityBasis.resolutionMode,
  candidate.quantityBasis.conversionEvidenceRequired
]

scopeQuestionTokens(candidate) = candidate.scopeQuestions.map(question => [
  question.code,
  question.prompt,
  question.required,
  question.answerKind,
  question.optionIds
])

evidenceRefTokens(candidate) = candidate.evidenceRefs.map(evidence => [
  evidence.inputIndex,
  evidence.lineKey,
  evidence.sheet,
  evidence.page,
  [evidence.bbox[0], evidence.bbox[1], evidence.bbox[2], evidence.bbox[3]],
  evidence.evidenceKind,
  evidence.role,
  evidence.sourceRowHash
])

countedLineMemberTokens(candidate) = candidate.evidenceRefs
  .filter(evidence => evidence.role == "counted")
  .map(evidence => [evidence.inputIndex, evidence.sourceRowHash])

supportingLineMemberTokens(candidate) = candidate.evidenceRefs
  .filter(evidence => evidence.role == "supporting")
  .map(evidence => [evidence.inputIndex, evidence.sourceRowHash])

familyContractProjectionTokens(candidate, scope) = [
  "apex.estimator-family-contract-projection/v1",
  candidate.familyAuthorityKey,
  scope.familyScopeHash,
  candidate.lineKey,
  candidate.sourceLineHash,
  candidate.candidateRefs,
  candidate.lockedBreakerRef,
  candidate.provisionalDefaultRef,
  candidate.r1Ratified,
  refOptionTokens(candidate),
  packagingOptionTokens(candidate),
  observedPackagingTokens(candidate),
  quantityBasisTokens(candidate),
  scopeQuestionTokens(candidate)
]
```

Within these projections, `packagingOptionIds` follows the candidate's canonical
`packagingOptions` order with inapplicable IDs omitted; `applicableRefs` follows
canonical `candidateRefs` order with inapplicable refs omitted; and each
question's `optionIds` follows its family-contract order. These arrays reject
duplicates and any member outside their bound closed set. Observed and conversion
evidence-index arrays follow canonical `evidenceRefs` order with uncited rows
omitted and reject any index that does not resolve exactly once in that candidate.
`orderedFamilyScopeHashes`
is the declared `familyScopeHash` from each canonically ordered family scope, and
`orderedCandidateContentHashes` is the declared `candidateContentHash` from each
canonically ordered candidate, after each declared hash has been recomputed and
validated against its exact projection. For a binding, `linkedFamilyScope` is
the unique scope with the same authority key, block, and family, and
`orderedCandidateProjectionHashesForBinding` is the
`familyContractProjectionHash` from every canonically ordered candidate carrying
that exact authority key. Empty or cross-scope projection sets are invalid.

Hashes use these fixed-order token arrays rather than raw object JSON:

```text
scopeOutputAuthority.receiptHash = SHA256(CanonicalEncode([
  "apex.estimator-scope-output-authority-receipt/v1",
  scopeOutputAuthorityPayloadTokens(scopeOutputAuthority)
]))

familyAuthorityBinding.receiptHash = SHA256(CanonicalEncode([
  "apex.estimator-family-authority-receipt/v1",
  familyAuthorityReceiptPayloadTokens(familyAuthorityBinding)
]))

familyContractManifestHash = SHA256(CanonicalEncode([
  "apex.takeoff.gate2-family-contract-manifest/v2",
  familyContractFileTokens(context)
]))

recomputedSourceLineHash(candidate, context) = SHA256(CanonicalEncode([
  "apex.takeoff.gate2-source-line/v2",
  context.artifactContentHash,
  context.sourceReportSchemaVersion,
  context.sourceReportContentHash,
  context.compilerHash,
  context.familyContractManifestHash,
  candidate.lineKey,
  candidate.family,
  candidate.block,
  candidate.recognizedQuantity,
  candidate.candidateRefs,
  candidate.lockedBreakerRef,
  candidate.provisionalDefaultRef,
  candidate.r1Ratified,
  countedLineMemberTokens(candidate),
  supportingLineMemberTokens(candidate)
]))

candidate.sourceLineHash == recomputedSourceLineHash(candidate, context)

candidate.familyContractProjectionHash = SHA256(CanonicalEncode(
  familyContractProjectionTokens(candidate, linkedFamilyScope)
))

familyProjectionSetHash(binding) = SHA256(CanonicalEncode([
  "apex.estimator-family-contract-projection-set/v1",
  binding.authorityKey,
  binding.contractHash,
  linkedFamilyScope.familyScopeHash,
  orderedCandidateProjectionHashesForBinding
]))

binding.authorizedProjectionSetHash == familyProjectionSetHash(binding)

candidateContentTokens(candidate) = [
  "apex.takeoff.gate2-candidate/v2",
  candidate.lineKey,
  candidate.sourceLineHash,
  candidate.family,
  candidate.block,
  candidate.familyAuthorityKey,
  candidate.familyContractProjectionHash,
  candidate.standardScopeKey,
  candidate.candidateRefs,
  candidate.recognizedQuantity,
  candidate.lockedBreakerRef,
  candidate.provisionalDefaultRef,
  candidate.r1Ratified,
  refOptionTokens(candidate),
  packagingOptionTokens(candidate),
  observedPackagingTokens(candidate),
  quantityBasisTokens(candidate),
  scopeQuestionTokens(candidate),
  evidenceRefTokens(candidate)
]

candidateContentHash = SHA256(CanonicalEncode(candidateContentTokens(candidate)))

familyScopeHash = SHA256(CanonicalEncode([
  "apex.takeoff.gate2-family-scope/v2",
  familyScopeTokens(scope)
]))

candidateSetHash = SHA256(CanonicalEncode([
  "apex.takeoff.gate2-candidate-set/v2",
  contextTokens(context),
  scopeOutputContractTokens(scopeOutputContract),
  orderedFamilyAuthorityBindingTokens,
  orderedFamilyScopeHashes,
  orderedCandidateContentHashes
]))
```

A later, separately accepted v2 resolution contract must bind the immutable v2
candidate-set hash, scope output contract, ordered block-profile decisions,
every current family-authority receipt hash, explicit answers, and accepted Gate
2 decision receipts. This candidate contract deliberately does not invent that
downstream hash. The preserved unmerged v1 decision receipt is insufficient for
v2 because it lacks the complete typed-answer projection. No product resolution
may exist until the downstream v2 decision/receipt preimage is separately
defined and accepted.

In `one_scope_per_block` mode there is exactly one block-profile decision and one
`outputScopeKey` per block; every family decision in that block references the
same block decision record and pricing profile. In `per_family_scope` mode the
authorized output contract supplies distinct deterministic keys and the future
resolution contract evaluates each authorized `(block, family)` separately.
Actor identity and server time belong in the resolution/receipt layer, not the
candidate hash.

No resolver may return `status:'resolved'`, no workflow may transition to
`priced`, and no emitter may construct a native envelope unless every family
binding and any required scope-output authority binding passes schema, preimage,
hash, currentness, appointment, scope, effective/expiry, supersession, and
projection checks at that operation time. Candidate generation may expose a
blocked preview without authority; resolution and emission may not.

Validation order avoids a recursive hash: compute `candidateContentHash` without
the declared `candidateSetHash` or declared `candidateContentHash`; compute the
set hash from the resulting ordered candidate hashes; then require the set-level
and every candidate-level declared `candidateSetHash` to equal that result.

## 8. Fail-closed invariants

1. no provisional default becomes a selection without an explicit accepted
   answer;
2. selected ref is active, belongs to the bound candidate set, supports the
   selected pricing profile, and is bidirectionally linked to the selected
   packaging option;
3. breaker `lockedBreakerRef` is the exact active matched-report ref and exact
   selected ref, but is not standards, packaging, quantity, hours, resolution,
   or emission authority; breaker resolution still requires a valid breaker
   family binding; non-breaker lock fields are `null`, and provisional defaults
   are `null` or exact candidate members;
4. every candidate has the exact required standard-scope question from its
   linked family scope, its complete question list equals the bound family
   template projection field-for-field, and every required standard, packaging,
   quantity, inclusion, and scope question has exactly one valid answer;
5. each candidate `standardScopeKey` resolves to exactly one family scope whose
   key, block, and family equal the candidate; scope keys and `(block, family)`
   scope identities are unique, no scope is orphaned, and no candidate may
   inherit a scope by fallback; family scope grouping never implies a separate
   output `ScopeDraft`;
6. candidate, quantity-basis, compiler-line, report-line, and counted-evidence
   recognized quantities are equal, and each resolved packaging option's
   proposed pricing quantity equals the exact integral quotient of recognized
   quantity by package size; the complete packaging and quantity projection is
   hash-identical to the projection set accepted by family authority;
7. every packaging option ID is unique, every ref-to-option link resolves, every
   packaging-question option belongs to the candidate's closed option set, and
   `observedOptionId` is `null` or resolves to exactly one option in that set;
   fixed each/set pricing rules match every applicable ref's exact catalog unit,
   while mixed or exceptional units require operator-resolved conversion;
8. observed and conversion evidence indices resolve only to same-candidate
   evidence refs and deterministically support their declared code, phase count,
   package size, and quantity; unknown packaging, missing required evidence, or
   non-integral quantity conversion blocks;
9. every upstream hash is recomputed under the exact closed v1 registry before
   use; unknown versions, opaque pass-through hashes, source/report/catalog/
   compiler/family-scope/candidate/ordering drift, family-contract-file drift, or
   manifest drift requires regeneration and new decisions;
10. unresolved candidates, catalog gaps, invalid family authority, or invalid
    scope-output authority prevent resolution and complete-envelope emission;
11. candidate generation never mints refs, hours, standards, aliases, or family
   authority;
12. the Gate 1 receipt reference is exact, accepted, and current; an ID or
    evidence hash alone is insufficient;
13. a valid hash or signature is evidence integrity, not implementation,
   deployment, mutation, or product authorization;
14. candidate identities `(standardScopeKey, lineKey)` are unique within the
   candidate set;
15. candidate evidence is an exact, role-compatible projection of bound report
   dispositions for the same line key and indexed artifact rows; cross-line,
   missing, and extra evidence fails closed;
16. replayed compiler family, block, quantity, membership, ratification flag, and
   matched breaker ref equal the candidate fields and recomputed source-line
   hash; relabeling or producer assertions fail closed;
17. eligible replayed matched and scope-pending lines and v2 candidates form an
   exact one-to-one set; omission, duplication, and invention fail closed;
18. candidate refs, provisional default, ratification flag, and breaker lock
   equal the exact replayed compiler/report projection, including ref order;
19. full compiler replay reproduces the bound reconciliation report and eligible
   line set exactly before the candidate/report bijection is evaluated;
20. each bbox coordinate has exactly one RFC-8785 binary64 string form; numeric
   comparison, rounding, trailing-zero variants, negative zero, and non-finite
   values fail closed;
21. each `(block, family)` has exactly one valid accepted/current/effective/
   unexpired candidate-set-scoped authority binding whose contract, projection
   set, appointment, Gate 1/artifact/report context, catalog, compiler,
   family-dependency manifest, and exact project/revision/line-set/candidate-set
   scope match before resolution or emission, and every binding permits the
   candidate set's selected output mode;
22. in `one_scope_per_block` mode all family profile answers in a block are
   identical and bind one block decision; conflicts fail closed;
23. `per_family_scope` requires the exact separate output-authority receipt,
   one-to-one bound family-authority receipt hashes, family permissions, and
   bound implementation; it is invalid on the current emitter; and
24. receipt signatures or hashes prove integrity and acceptance only within
   their exact authority scope; they do not authorize implementation, deployment,
   production mutation, push, or PR.

## 9. Independent-review decisions

The bounded independent review must decide only whether these corrections close
the named design defects without implementation:

1. fractional bbox coordinates have one exact RFC-8785 binary64 string form;
2. complete ref, packaging, observed-packaging, quantity, and question
   projections are hash-bound to a current accepted candidate-set-scoped family
   authority receipt;
3. breaker locking selects only the mechanical ref and never substitutes for
   valid family authority before resolution or emission;
4. every candidate-set upstream hash has an exact versioned preimage contract,
   while undefined downstream v2 decision receipts remain an explicit hold;
5. `(block, family)` questions converge to one block profile for the merged
   one-`ScopeDraft` output contract, and conflicts fail closed;
6. per-family scopes require exact pair-scoped authority plus a bound implemented
   emitter and are invalid on the current baseline; and
7. signatures, hashes, accepted receipts, and this review do not authorize
   implementation, deployment, push, or PR.

## 10. Non-authorizations

This design does not authorize implementation, dependency changes, recognizer or
`candidateKind` changes, family-map edits, catalog edits, authority-flag changes,
schema or API work, receipt publication, source-body ingestion, production access,
deployment, push, PR, family ratification, or pricing acceptance.
