# Checker And Adversarial Test Design

Status: PROPOSED DESIGN - NO CHECKER IMPLEMENTATION

## Checker Responsibilities

The later offline checker should validate goal structure, stable identity,
authority references, input resolution, evidence freshness, decision binding,
state transitions, scope boundaries, expiry, output roots, and gate completeness.

## Required Negative Tests

The checker must reject at least:

1. duplicate goal IDs;
2. a numeric-range-inferred cohort;
3. ET-017 or ET-028 admitted as active targets;
4. an accepted goal with a missing authority appointment;
5. an author serving as final SME or auditor for the same version;
6. evidence without a resolvable path/object/hash;
7. a decision bound to a different content version;
8. unknown rights converted to accepted;
9. stale or expired evidence satisfying a gate;
10. automatic continuation across a higher write class;
11. continuation into a different environment or cohort;
12. a learner-data action without purpose/privacy authority;
13. import, render, deploy, or release without the named gate;
14. a held Level II goal changed to ready during metadata migration;
15. `ksa_mapped` accepted as a learner event without a ratified contract;
16. output or evidence paths escaping approved roots;
17. a superseded goal returning to execution;
18. a generic approval with no owner, evidence, or reviewed version.
19. the Program Manager and primary executor resolving to the same run identity;
20. an author or implementation agent serving as Technical Authority or
    independent auditor for the version it changed;
21. a primary executor starting a proposed next goal without a new CP1
    authorization;
22. checkpoint advancement without the required Program Manager or operator
    decision;
23. a standing rights policy treated as source-specific admissibility;
24. a `CANDIDATE` source treated as authoring-ready;
25. a checksum treated as proof of signer identity or authority;
26. a living source-register path satisfying a decision without a bound row or
    snapshot version;
27. agent consensus substituted for a named human SME, privacy, rights, or
    release decision; and
28. a later product stage inheriting authorization from Stage 1.

## Positive Fixtures

At minimum, include one valid design-only `GOVERN` goal and one faithfully held
Level II migration fixture. No positive fixture may imply content or learner-data
authorization.

The valid `GOVERN` fixture must use distinct Program Manager, primary executor,
and independent reviewer identities and must stop at its declared checkpoint.

## Implementation Gate

Schema and checker code require a separate GO after this design is ratified.
