# Slice 2d Contract Reconciliation Follow-Up

Status: PROPOSED FOLLOW-UP - NOT AUTHORIZED

## Problem

The Slice 2d runbook requires a `ksa_mapped` acquisition action, while the
implemented event vocabulary accepts only:

- `resource_viewed`;
- `resource_completed`;
- `assessment_completed`;
- `self_assessment`.

The rehearsal cannot be admitted until the runbook, evidence template, CLI,
database, API, tests, and product semantics use one contract.

## Recommended Direction

Treat KSA mapping as content/model evidence derived from the accepted mapping
graph, not as a learner behavior event, unless a separately ratified business
requirement proves that a new event is necessary.

## Follow-Up Packet Scope

- inventory every `ksa_mapped` reference;
- define the authoritative event and evidence vocabulary;
- align the runbook and evidence template;
- define database/API/package compatibility requirements;
- specify negative and end-to-end tests;
- preserve existing event history;
- remain offline and perform no learner-data write.

## Explicit Exclusions

- no Slice 2d rehearsal;
- no event insertion;
- no database migration or API deployment;
- no hosted route activation;
- no content authoring;
- no Level II hold change.

Technical Authority approval and a separate implementation GO are required.
