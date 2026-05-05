# Olares Phase 5 Packet 073 - Bounded Validation-Surface Decomposition Planning Handoff

Date: 2026-05-05

## Verdict

Packet 073 is complete as planning-only.

Planning decision:

`authorize_later_one_worker_test_surface_decomposition_execution_after_authority_publication`

## Planned Slice

The later execution packet may use exactly one mutation worker and exactly this test-only slice:

1. `apps/operations-web/tests/browser-shell.smoke.spec.ts`
2. `apps/operations-web/tests/browser-shell.apparatus.smoke.spec.ts`
3. `apps/operations-web/tests/browser-shell.relay.smoke.spec.ts`
4. `apps/operations-web/tests/browser-shell.static-surfaces.smoke.spec.ts`

The intended shape is to retire the current shared browser-smoke file and split its coverage into tracked, disjoint validation files:

1. apparatus-only coverage in `browser-shell.apparatus.smoke.spec.ts`
2. relay-only coverage in `browser-shell.relay.smoke.spec.ts`
3. static re-homed browser-surface coverage in `browser-shell.static-surfaces.smoke.spec.ts`

## Ownership Rule

The decomposition execution itself remains one-worker-only.

After publication and clean reconciliation, a later readiness verdict may consider whether future apparatus and relay workers can own separate test files. Packet 073 does not make that readiness claim.

## Required Next Packet

Before any execution, the next packet must publish Packet 071 through Packet 073 authority and resync the host mirror:

`Olares Phase 5 074 - Packet 071 Through Packet 073 Authority Publication And Host Mirror Resync Gate`

## Still Closed

The following remain closed:

1. source/application edits
2. validation-surface decomposition execution
3. simultaneous multi-worker source/test execution
4. second mutation worker execution
5. migration approval
6. runtime or service mutation
7. package or lockfile mutation
8. installs or package-manager activation/download
9. AI-services expansion
10. Gitea/code-hosting transition
11. canonical-hosting transition
12. remote rewrite
13. rollback or force/reset/clean
14. mutation of `/home/olares/src/apex-power-ops-platform`
