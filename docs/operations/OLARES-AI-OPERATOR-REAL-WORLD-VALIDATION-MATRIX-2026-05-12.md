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
| Promotion-gate rehearsal | proves the trust boundary is real rather than implied | 1. confirm sandbox-only validation exists 2. verify sandbox-only `promote_packet` refusal 3. capture one successful `env=host` run 4. rerun promotion on the same packet id through `tools/ai/capture_apex_jobs_promotion.py` when positive-gate evidence is the packet goal | sandbox-only promotion must refuse; host-qualified success may promote only after matching successful host evidence exists | refusal detail, host run id, promotion record, helper artifact path, packet closeout note tying packet id to evidence |
| Two-executor rehearsal | proves coordination rules work without widening orchestration | 1. define one scaffold lane and one trust-hardening lane 2. declare final write ownership before edits 3. validate each lane independently 4. run one coordinator-owned final check across the declared files 5. publish one coherent completion record | the slice should complete without file-ownership confusion, queue ambiguity, or widened runtime scope; any ownership drift or failed lane validation should end as `ABORTED`, not partial success | packet or handoff ownership block, per-lane validation results, one combined coordinator validation result, one explicit abort record when the rehearsal stops |

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

For any later two-executor rehearsal after Packet 786, require one additional coordinator-owned evidence pattern:

1. the packet names lane A and lane B ownership before edits start,
2. each lane records its own touched files, validation command, and validation result under the same packet id,
3. the coordinator records one final combined validation result scoped to the declared rehearsal files,
4. any ownership drift, shared-file drift, or failed lane validation is recorded as `ABORTED` for the packet,
5. only a packet with both lane tuples and the coordinator tuple may be treated as a completed rehearsal.

Current baseline note:

1. Packet `2026-05-13-olares-dev-residency-786` already proved the first completed coordinator-owned two-executor rehearsal.
2. Later rehearsal packets should preserve this coordinator-owned evidence pattern rather than describing that first rehearsal as still pending.

## Stop Conditions

Stop and reopen the boundary deliberately if any scenario would require:

1. `ai_tasks` ownership,
2. a new orchestration service beyond the admitted trio,
3. auth or public-ingress widening,
4. a hidden host dependency that cannot be expressed in repo-owned docs and evidence,
5. business-logic mutation under cover of validation work.

## Current Recommendation

The next truthful work is the active coordinator-owned dual-lane Packet `2026-05-13-olares-dev-residency-799`, not a new generic hardening slice and not new orchestration features.

That packet should stay bounded in two ways:

1. reuse Packet `2026-05-13-olares-dev-residency-798` as the current-head authoritative-host floor for bootstrap, strict verification, positive-gate promotion capture, coordinator summary composition, and truthful teardown,
2. reuse Packet `2026-05-13-olares-dev-residency-797` summary-helper conventions so the packet emits one repo-visible coordinator summary artifact instead of hand-copying verifier and promotion tuples into closeout text.

For the current-head host chain, prefer one repo-owned helper-driven execution surface rather than reconstructing the bounded host sequence by hand. Once it is available, `tools/ai/run_authoritative_host_packet.py` is the preferred execution surface for that chain.

Do not treat Packet 799, the current-head host floor, or the planned helper as permission to widen the controller, runtime posture, admitted service family, queue ownership, or business-logic scope.

## Packet 791 Alignment Note

Packet `2026-05-13-olares-dev-residency-791` is the current concrete model for the promotion-gate rehearsal row above.

It proves the matrix row now has two complementary repo-owned proof surfaces:

1. `tools/ai/verify_minimal_mcp_trio.py` covers the negative guard by proving sandbox-only promotion refusal,
2. `tools/ai/capture_apex_jobs_promotion.py` covers the positive gate by recording the successful matching `env=host` run, `list_runs` visibility, and `promote_packet` success on the same packet id,
3. the authoritative host can return to truthful `not-running` state after both proofs complete.