# Olares AI Operator Real-World Validation Matrix

Date: 2026-05-12
Status: Active bounded validation surface
Scope: concrete real-world validation order for the admitted Olares AI/operator boundary without widening orchestration scope

## Purpose

This document turns the current AI/operator boundary into an executable real-world validation surface.

It does not admit broader orchestration.

It exists to answer four practical questions:

1. what should be revalidated first,
2. which scenarios matter most in the real operator path,
3. what evidence must be captured for each scenario,
4. what must still stop rather than being treated as a pass.

Use this file with:

1. `../../plan/OLARES-AI-ORCHESTRATION-EXECUTION-PLAN-2026-05-10.md`,
2. `OLARES-AI-PARALLEL-TASK-READINESS-CHECKLIST-2026-05-10.md`,
3. `APEX-JOBS-TRUST-AND-PROMOTION-CONTRACT-2026-05-08.md`,
4. `../architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md`,
5. `OLARES-AI-WORKSTATION-LIVE-DSN-BASELINE-RUNBOOK-2026-05-12.md`,
6. `OLARES-AI-HOST-MANAGED-COLD-START-DRILL-RUNBOOK-2026-05-12.md`,
7. `OLARES-AI-GOVERNED-LIVE-DSN-SOURCING-RUNBOOK-2026-05-12.md`,
8. `../../PROJECT_STATUS.md`.

## Validation Goal

The current goal is not generic AI expansion.

The current goal is to prove that the admitted boundary is truthful and repeatable in the operator paths that matter most:

1. workstation live-DSN comparison,
2. host managed cold start,
3. host adopted-runtime binding,
4. promotion-gate rehearsal,
5. one bounded two-executor rehearsal after single-lane proof is stable.

## Preconditions

Before running any scenario below, confirm all of the following:

1. the admitted MCP family is still only `apex-fs`, `apex-db`, and `apex-jobs`,
2. `apex-jobs` remains the run and promotion ledger,
3. the scenario has one explicit packet id,
4. the expected evidence paths remain repo-visible under `tests/canary/`,
5. no scenario widens auth, public ingress, queue ownership, or business-logic scope.

## Scenario Matrix

| Scenario | Why it matters | Preferred command sequence | Expected truthful result | Required evidence |
|----------|----------------|----------------------------|--------------------------|-------------------|
| Workstation live-DSN baseline | preserves the authoritative comparison point before host changes are interpreted | 1. export or set a governed live DSN 2. run `run-minimal-mcp-trio` `up` 3. run `verify` 4. run hold-boundary against the live DSN 5. run `down` | `minimal_mcp=PASS` and `deferred_ops=HOLD` unless live business rows have genuinely changed | minimal-trio verifier artifact, deferred-ops artifact, packet validation note, resulting `apex-jobs` run id when captured |
| Host managed cold-start drill | proves the Olares mirror can start from rest and produce a coherent operator evidence bundle | 1. use the dedicated host managed cold-start drill runbook 2. run host bootstrap status 3. run host `run-minimal-mcp-trio.sh up` 4. run `verify` 5. run host hold-boundary against a governed live DSN when present 6. run `down` | bootstrap should be truthful before startup, then the managed trio should verify cleanly; `deferred_ops=UNAVAILABLE` remains truthful unless a bounded host query path has been admitted and works | host-bootstrap artifact, minimal-trio verifier artifact, deferred-ops artifact, packet/handoff evidence block |
| Host adopted-runtime drill | proves the wrappers bind only to the correct already-running trio and reject foreign ownership or stale state | 1. start the trio once 2. rerun host bootstrap status 3. rerun host `status` and `verify` without a second startup 4. run hold-boundary if the readiness gate is satisfied | status should report `adopted-running` only when live readiness and ownership checks are both true; stale or foreign listeners must degrade or refuse adoption | host-bootstrap artifact, minimal status artifact, verifier artifact, captured refusal or degradation evidence when adoption is denied |
| Promotion-gate rehearsal | proves the trust boundary is real rather than implied | 1. confirm sandbox-only validation exists 2. verify sandbox-only `promote_packet` refusal 3. capture one successful `env=host` run 4. rerun promotion on the same packet id | sandbox-only promotion must refuse; host-qualified success may promote only after matching successful host evidence exists | refusal detail, host run id, promotion record, packet closeout note tying packet id to evidence |
| Two-executor rehearsal | proves coordination rules work without widening orchestration | 1. define one scaffold lane and one trust-hardening lane 2. declare final write ownership before edits 3. validate each lane independently 4. publish one coherent completion record | the slice should complete without file-ownership confusion, queue ambiguity, or widened runtime scope | packet or handoff ownership block, per-lane validation results, one combined completion record |

## Recommended Execution Order

Run the scenarios in this order:

1. workstation live-DSN baseline,
2. host managed cold-start drill,
3. host adopted-runtime drill,
4. promotion-gate rehearsal,
5. two-executor rehearsal only after the first four are stable.

Do not invert that order unless a packet explicitly says why.

## Failure Interpretation Rules

Interpret failures narrowly:

1. `UNAVAILABLE` on host deferred-ops is a truthful bounded result when no admitted live-query path exists there,
2. sandbox-only promotion refusal is a pass for the trust boundary, not a missing feature,
3. stale managed or adopted state degrading to `not-running` is a pass for truthfulness,
4. ownership refusal against foreign listeners is a pass for boundary protection,
5. only a clean host-qualified evidence chain may support later promotion claims.

## Exit Gates

Treat the current boundary as real-world validated only when all of the following are true:

1. one packet id can be traced across bootstrap, verifier, and deferred-ops artifacts for the same scenario,
2. workstation and host results differ only where the current boundary already explains the difference,
3. promotion refusal and host-qualified promotion both behave exactly as documented,
4. all emitted evidence is repo-visible and suitable for packet or handoff closeout,
5. no scenario silently widened runtime or queue authority.

## Stop Conditions

Stop and reopen the boundary deliberately if any scenario would require:

1. `ai_tasks` ownership,
2. a new orchestration service beyond the admitted trio,
3. auth or public-ingress widening,
4. a hidden host dependency that cannot be expressed in repo-owned docs and evidence,
5. business-logic mutation under cover of validation work.

## Current Recommendation

The next truthful work is host-side real-world validation, not new orchestration features.

If operator friction remains after the matrix above is green, the best follow-on is one bounded trust-hardening slice such as richer `apex-jobs` evidence attachment or a named validation-profile surface.

Do not treat that possible follow-on as permission to widen the controller, runtime posture, or admitted service family.