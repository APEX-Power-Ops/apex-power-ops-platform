# Estimator Takeoff Discovery Packet: Surge / SPD

Status: **NONBINDING DISCOVERY / OFFLINE DESIGN / INDEPENDENT-REVIEW HOLD**
Date: 2026-07-16
GO boundary: `EST-TAKEOFF-CATALOG-COVERAGE-001`
Baseline: detached `origin/main@bdec885a5cd2862da7907054646c9c0fb5df5ef2`

## 1. Purpose and limits

This packet identifies repository-visible questions for a possible Surge
Protective Device / Surge Arrester family. It is not a family-admission packet,
an implementation-ready specification, an estimating-authority decision, or a
request to change recognition behavior.

No proprietary source body was opened or copied. Exact catalog spelling,
including legacy spelling variants and typos, is preserved because `ref` is a
stable identity key.

## 2. Exact catalog surface

| Discovery candidate | Firm section | ATS hours | MTS hours | Unit |
|---|---:|---:|---:|---|
| `Arrester - SS, High Voltage (Set)` | `7.19` | 4 | 4 | `set` |
| `Arrester - SS, Medium Volatge (Set)` | `7.19` | 3.5 | 3.5 | `set` |
| `Arrestor - Medium Voltage (Set)` | `7.19` | 1.5 | 1.5 | `set` |
| `Arrestor (SPD) - Low Voltage` | `7.19` | 0.5 | 1 | `each` |

All four rows are active in
`packages/estimator-core/src/catalog/equipment-models.seed.json`. The catalog
contains two distinct medium-voltage set refs and preserves both `Arrester` and
`Arrestor` spellings. This packet does not collapse, correct, merge, or choose
between them.

Committed records metadata distinguishes LV SPD from MV/HV surge-arrester
procedures. That is contextual evidence only. The estimating catalog records the
coarser `7.19`, and no records-lane taxonomy is treated here as estimating
authority.

## 3. Current engine behavior

- `candidateKind` has no Surge / SPD member in
  `packages/estimator-takeoff/src/extraction/types.ts`;
- the apparatus-signature union and family emit dispatch have no Surge / SPD
  member;
- literal `SPD` is an explicit `NON_BREAKER` token in
  `packages/estimator-takeoff/src/signature/normalize.ts` and ordinarily reaches
  the non-breaker tail;
- spelled-out `surge`, `arrester`, or `arrestor` has no positive family
  recognizer or candidate map on the current baseline;
- breaker-shaped conflicts remain questions rather than an authority to create
  a surge candidate.

This packet does not change or reinterpret any of those facts.

## 4. Decisions that remain open

### S1 - family boundary and subtypes

Decide whether LV SPD and MV/HV arresters form one family contract with explicit
subtypes or separate admission slices. `SS` is not expanded anywhere found in
the repository and must not be guessed.

### S2 - exact ref discrimination

Resolve what evidence distinguishes the two active medium-voltage set refs and
whether either is a duplicate, legacy convention, or genuinely different scope.
No mapping may select between them from spelling or hours alone.

### S3 - standards scope

Define allowed ATS/MTS choices and the relation between coarse catalog section
`7.19` and any family-specific procedure. Existing generic takeoff voltage bands
are conventions, not proof that bus voltage alone is the correct surge-device
classification axis.

### S4 - packaging and quantity basis

For each `set` ref, define whether one priced unit means a three-phase bank, one
equipment location, a manufacturer package, or another grouping. Define how
three individual drawing symbols relate to one set. For the LV `each` ref,
resolve whether quantity is per enclosure, module, panel-integrated assembly, or
distinct tagged device.

### S5 - positive device evidence

Define evidence sufficient to establish a discrete device rather than a
transformer/switchgear accessory, note, cross-reference, or integrated feature.
Potential evidence dimensions include a discrete tag, voltage/rating evidence,
phase or set evidence, parent association, location, and source occurrence.
They remain questions, not proposed recognizer tokens.

### S6 - evidence-only versus pricing axes

Decide whether SPD type, arrester class, rated voltage, MCOV, installation class,
or parent equipment are merely evidence or actual candidate-ref axes. No such
axis is inferred from the catalog label in this packet.

### S7 - corpus admission

Do not select or admit this family until rights-cleared accepted estimates show
actual device occurrences, accepted grouping, selected refs, and parent versus
standalone treatment. Catalog presence alone supplies no frequency,
economic-impact, recall, or false-positive evidence.

Any future corpus use is also subject to the current, source-specific, scoped
Rights Authority evidence gate in
`estimator-takeoff-catalog-coverage-001.md` section 8.2. This discovery packet
does not satisfy that gate.

## 5. Evidence required for a future admission packet

Only redacted, content-addressed evidence references should enter the platform
packet. A future packet needs, at minimum:

1. accepted-estimate receipt references from more than one corpus case;
2. artifact and Gate 1 evidence hashes for each proposed device or set;
3. exact source occurrence references such as sheet/page/bounding-box identity,
   without embedding proprietary source bodies;
4. accepted parent/standalone disposition and voltage/rating basis;
5. accepted standard, packaging, quantity basis, and exact ref;
6. explicit negative examples for parent-integrated or accessory mentions;
7. parity to accepted final cents under pinned catalog, compiler, and rate
   authority.

## 6. Review disposition

Recommendation: **discovery only; not ready for family admission**. The four
catalog refs are bounded, but subtype boundaries, duplicate-looking MV refs,
set expansion, LV quantity, positive evidence, and parent association remain
unratified and corpus-unproven.

## 7. Non-authorizations

This packet does not authorize or change recognizers, `candidateKind`, family
mappings, catalog refs or hours, authority flags, schemas, APIs, receipts,
production state, deployments, source custody, family implementation, or family
ratification. `each` and `set` are not equated with drawing-symbol quantity. No
records-lane taxonomy is promoted into estimating authority.
