# Estimator Takeoff Discovery Packet: Meter / PQM

Status: **NONBINDING DISCOVERY / OFFLINE DESIGN / INDEPENDENT-REVIEW HOLD**
Date: 2026-07-16
GO boundary: `EST-TAKEOFF-CATALOG-COVERAGE-001`
Baseline: detached `origin/main@bdec885a5cd2862da7907054646c9c0fb5df5ef2`

## 1. Purpose and limits

This packet identifies repository-visible questions for a possible standalone
Meter / Power Quality Meter family. It is not a family-admission packet, an
implementation-ready specification, an estimating-authority decision, or a
request to change recognition behavior.

No proprietary source body was opened or copied. The packet uses only committed
catalog metadata, current engine contracts, and committed reference metadata.

## 2. Exact catalog surface

| Classification | Exact catalog ref | Firm section | ATS hours | MTS hours | Unit |
|---|---|---:|---:|---:|---|
| standalone discovery candidate | `Meter - Electromechanical (Single Element)` | `7.11` | 1 | 1.5 | `each` |
| standalone discovery candidate | `Meter - PQM/Microprocessor Based` | `7.11` | 2.5 | 3 | `each` |
| cross-family guard, not a standalone Meter / PQM candidate | `Protective Relay (Multi-function w Meter)` | `7.9` | 8 | 10 | `each` |

The exact rows are in
`packages/estimator-core/src/catalog/equipment-models.seed.json`. The adjacent
relay ref is already one of the nine relay scope-candidate refs in
`packages/estimator-takeoff/src/catalog/relay-map.data.ts`; treating it as a
second meter line would risk duplicate accounting.

The catalog contains both ATS and MTS economics. That fact does not decide which
standard applies to a drawing occurrence, whether the catalog is complete, or
whether the hours are applicable to a particular accepted estimate.

## 3. Current engine behavior

- `candidateKind` has no Meter / PQM member in
  `packages/estimator-takeoff/src/extraction/types.ts`.
- the apparatus-signature union and family emit dispatch have no Meter / PQM
  member;
- `PQM` and `METER` are explicit `NON_BREAKER` tokens in
  `packages/estimator-takeoff/src/signature/normalize.ts`;
- a normal standalone row therefore has no positive Meter / PQM recognizer or
  candidate map on the current baseline;
- relay recognition runs before the `NON_BREAKER` tail, so only relay-anchored
  evidence can currently reach the provisional `multifunction_meter` relay tier;
- `RELAY_R1_RATIFIED` remains `false`.

This packet does not change or reinterpret any of those facts.

## 4. Decisions that remain open

### M1 - family boundary

Decide whether the family is limited to physically standalone meters. A
protective relay with metering, switchgear metering context, an ATS accessory,
and a standalone meter must not become interchangeable merely because each uses
the word `meter`.

### M2 - standards scope

The firm catalog records coarse section `7.11`. Committed records metadata
distinguishes electromechanical/solid-state and microprocessor procedures, but
records taxonomy is contextual evidence, not estimating authority. A technical
authority must decide the allowed ATS/MTS standard choices for each candidate
ref and the treatment of solid-state meters that are not clearly covered by the
two exact catalog labels.

### M3 - packaging and quantity basis

`each` cannot be assumed to mean one extracted symbol. Resolve whether
`Single Element` describes a physical package, a measured element, or an
economic multiplier; whether one physical PQM is always one priced unit; and how
one-line/schedule duplicates collapse to a distinct-device count.

### M4 - positive device evidence

Define the minimum evidence that establishes a standalone device rather than
metering context. Questions include whether a discrete tag is mandatory, which
model/device nouns are admissible, how a parent association is represented, and
which one-line or schedule occurrence is authoritative.

### M5 - cross-family exclusion

Define a fail-closed precedence rule for:

- `Protective Relay (Multi-function w Meter)` versus a standalone meter;
- instrument-transformer evidence versus a meter;
- switchgear, panel, ATS, or other parent-apparatus metering context;
- multiple occurrences of the same tagged device.

No textual alias may create two priced candidates from one physical device.

### M6 - corpus admission

Do not select or admit this family until rights-cleared accepted estimates show
actual standalone-meter occurrences, accepted ref choices, quantity treatment,
and cross-family outcomes. Catalog presence alone supplies no frequency,
economic-impact, recall, or false-positive evidence.

Any future corpus use is also subject to the current, source-specific, scoped
Rights Authority evidence gate in
`estimator-takeoff-catalog-coverage-001.md` section 8.2. This discovery packet
does not satisfy that gate.

## 5. Evidence required for a future admission packet

Only redacted, content-addressed evidence references should enter the platform
packet. A future packet needs, at minimum:

1. accepted-estimate receipt references from more than one corpus case;
2. artifact and Gate 1 evidence hashes for each proposed device;
3. exact source occurrence references such as sheet/page/bounding-box identity,
   without embedding proprietary source bodies;
4. accepted parent/standalone disposition;
5. accepted standard, packaging, quantity basis, and exact ref;
6. explicit negative examples for relay-with-metering and parent-apparatus
   metering context;
7. parity to accepted final cents under pinned catalog, compiler, and rate
   authority.

## 6. Review disposition

Recommendation: **discovery only; not ready for family admission**. The two
standalone refs are a bounded candidate universe, but the family boundary,
quantity semantics, positive evidence, and relay/parent exclusion rules remain
unratified and corpus-unproven.

## 7. Non-authorizations

This packet does not authorize or change recognizers, `candidateKind`, family
mappings, catalog refs or hours, authority flags, schemas, APIs, receipts,
production state, deployments, source custody, family implementation, or family
ratification. `each` is not equated with drawing-symbol quantity. No records-lane
taxonomy is promoted into estimating authority.
