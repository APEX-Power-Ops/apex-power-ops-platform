# Evidence And Decision Binding - Draft

Status: PROPOSED

## Core Rule

Evidence and decisions are separate immutable records. A decision references
exact evidence; changing evidence cannot silently change an accepted decision.

## Evidence Manifest Fields

- evidence ID and type;
- source/custody locator;
- exact byte hash or Git blob hash;
- object and cohort coverage;
- standards edition;
- collector/author identity and tool provenance;
- captured-at time and freshness policy;
- rights/privacy classification;
- availability and validation state;
- supersession relationship.

Content bodies may remain in an approved source-domain or document store. The
control plane stores locators, hashes, metadata, decisions, and release state,
not uncontrolled duplicate bodies.

## Decision Fields

- decision ID and type;
- decision owner and authority reference;
- reviewed object/version;
- evidence references;
- disposition: accepted, accepted-with-conditions, revision-required, held, or
  rejected;
- testable conditions and condition owners;
- timestamp, expiry, and re-review trigger;
- signature or governed Git identity as later ratified.

## Fail-Closed Rules

- Missing evidence remains missing.
- Unknown never becomes accepted by age or silence.
- File existence does not prove rights or acceptance.
- A decision cannot bind an unresolvable object version.
- Stale or superseded evidence cannot satisfy a fresh gate.
- An executor cannot author its own final approval record.
