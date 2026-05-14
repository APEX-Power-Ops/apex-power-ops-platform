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

The current frontier is no longer whether the helper works. Packet `2026-05-13-olares-dev-residency-830` remains the current helper-bootstrap-toolchains-python3-path validation floor after running the current-head host chain through `tools/ai/run_authoritative_host_packet.py` and proving the helper rejects copied host bootstrap artifacts whose `toolchains.python3.path` no longer preserves the expected host Python 3 path instead of accepting any copied bootstrap artifact whose packet id, repo head, bootstrap tool, bootstrap command, bootstrap output path, bootstrap host container root, bootstrap implementation root, bootstrap old-clone path, bootstrap old-clone existence, bootstrap toolchains preferred-Python path mirror, bootstrap toolchains node-path mirror, bootstrap toolchains pnpm materialized-path mirror, bootstrap toolchains calc-engine Python path mirror, bootstrap hold-boundary detail status, bootstrap hold-boundary minimal-MCP mirror, bootstrap hold-boundary deferred-ops decision, bootstrap hold-boundary deferred-ops mirror, bootstrap hold-boundary outputs mirror, bootstrap hold-boundary packet-id mirror, and preflight rest-state evidence merely look coherent. Packet `2026-05-13-olares-dev-residency-831` is the delegated dual-lane rehearsal floor on top of that helper contract after reusing the helper unchanged, landing the delegated split checklist at `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-EXECUTION-CHECKLIST-2026-05-13.md`, and returning the host to truthful `not-running` rest state with both lane tuples green. Packet `2026-05-13-olares-dev-residency-832` is the delegated operator prompt template floor on top of those preserved contracts after reusing the helper unchanged, landing `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-OPERATOR-PROMPT-TEMPLATE-2026-05-13.md`, publishing the closeout set, and returning the host to truthful `not-running` rest state again with authoritative-host parity restored. Packet `2026-05-13-olares-dev-residency-833` is the delegated coordinator closeout template floor on top of those same preserved contracts after reusing the helper unchanged, landing `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-COORDINATOR-CLOSEOUT-TEMPLATE-2026-05-13.md`, publishing the closeout set, and returning the host to truthful `not-running` rest state again with authoritative-host parity restored. Packet `2026-05-13-olares-dev-residency-834` is the delegated packet-definition template floor on top of those same preserved contracts after reusing the helper unchanged, landing `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-PACKET-TEMPLATE-2026-05-13.md`, publishing the closeout set, and returning the host to truthful `not-running` rest state again with authoritative-host parity restored. Packet `2026-05-13-olares-dev-residency-835` is the higher-level orchestration entry-surface alignment floor on top of those same preserved contracts after reusing the helper unchanged, aligning the orchestration status brief, the parallel-readiness checklist, and the workflow-first runbook to the published delegated Packet 831 through Packet 834 stack, publishing the closeout set, and returning the host to truthful `not-running` rest state again with authoritative-host parity restored. Packet `2026-05-13-olares-dev-residency-836` is the active plan and authority control-surface alignment floor on top of those same preserved contracts after reusing the helper unchanged, aligning the active execution plan, workspace authority framework, and Codex scaffold brief to the published delegated Packet 831 through Packet 835 stack, publishing the closeout set, and returning the host to truthful `not-running` rest state again with authoritative-host parity restored.

Keep the next work bounded in three ways:

1. reuse Packet `2026-05-13-olares-dev-residency-836` as the active plan and authority control-surface alignment floor, Packet `2026-05-13-olares-dev-residency-835` as the higher-level orchestration entry-surface alignment floor, Packet `2026-05-13-olares-dev-residency-834` as the delegated packet-definition template floor, Packet `2026-05-13-olares-dev-residency-833` as the delegated coordinator closeout template floor, Packet `2026-05-13-olares-dev-residency-832` as the delegated operator prompt template floor, Packet `2026-05-13-olares-dev-residency-831` as the delegated dual-lane rehearsal floor, Packet `2026-05-13-olares-dev-residency-830` as the helper-bootstrap-toolchains-python3-path floor, Packet `2026-05-13-olares-dev-residency-829` as the helper-bootstrap-toolchains-preferred-python-path floor, Packet `2026-05-13-olares-dev-residency-828` as the helper-bootstrap-toolchains-node-path floor, Packet `2026-05-13-olares-dev-residency-827` as the helper-bootstrap-toolchains-calc-engine-python-path floor, Packet `2026-05-13-olares-dev-residency-826` as the helper-bootstrap-toolchains-pnpm-materialized-path floor, Packet `2026-05-13-olares-dev-residency-825` as the helper-bootstrap-hold-boundary-packet-id floor, Packet `2026-05-13-olares-dev-residency-824` as the helper-bootstrap-hold-boundary-outputs floor, Packet `2026-05-13-olares-dev-residency-823` as the helper-bootstrap-hold-boundary-deferred-ops floor, Packet `2026-05-13-olares-dev-residency-822` as the helper-bootstrap-hold-boundary-deferred-ops-decision floor, Packet `2026-05-13-olares-dev-residency-821` as the helper-bootstrap-hold-boundary-minimal-mcp floor, Packet `2026-05-13-olares-dev-residency-820` as the helper-bootstrap-hold-boundary-status floor, Packet `2026-05-13-olares-dev-residency-819` as the helper-bootstrap-old-clone-exists floor, Packet `2026-05-13-olares-dev-residency-818` as the helper-bootstrap-old-clone-path floor, Packet `2026-05-13-olares-dev-residency-817` as the helper-bootstrap-container-root floor, Packet `2026-05-13-olares-dev-residency-816` as the helper-bootstrap-implementation-root floor, Packet `2026-05-13-olares-dev-residency-815` as the helper-bootstrap-output-path floor, Packet `2026-05-13-olares-dev-residency-814` as the helper-bootstrap-command floor, Packet `2026-05-13-olares-dev-residency-813` as the helper-bootstrap-tool floor, Packet `2026-05-13-olares-dev-residency-812` as the helper-verifier-command floor, Packet `2026-05-13-olares-dev-residency-811` as the helper-artifact-command floor, Packet `2026-05-13-olares-dev-residency-810` as the helper-artifact-tool floor, Packet `2026-05-13-olares-dev-residency-809` as the helper-artifact-self-path floor, Packet `2026-05-13-olares-dev-residency-808` as the helper-promotion-record-timestamp floor, Packet `2026-05-13-olares-dev-residency-807` as the helper-promotion-metadata floor, Packet `2026-05-13-olares-dev-residency-806` as the helper-host-metadata floor, Packet `2026-05-13-olares-dev-residency-805` as the helper-support-backing floor, Packet `2026-05-13-olares-dev-residency-804` as the helper-host-success-set floor, Packet `2026-05-13-olares-dev-residency-803` as the helper-supporting-run floor, Packet `2026-05-13-olares-dev-residency-802` as the helper-cross-artifact floor, Packet `2026-05-13-olares-dev-residency-800` as the helper-parity floor, and Packet `2026-05-13-olares-dev-residency-798` as the underlying current-head authoritative-host runtime floor,
2. reuse Packet `2026-05-13-olares-dev-residency-797` summary-helper conventions so later packets still emit one repo-visible coordinator summary artifact instead of hand-copying verifier and promotion tuples into closeout text,
3. prefer another delegated packet that reuses the published Packet 831 split checklist, the published Packet 832 operator prompt template, the published Packet 833 coordinator closeout template, and the published Packet 834 packet-definition template rather than broadening controller scope or reconstructing ownership and abort rules ad hoc, while preserving the higher-level orchestration entry surfaces in the Packet 835-aligned posture and the active execution plan, workspace authority framework, and Codex scaffold brief in the Packet 836-aligned posture.

For the current-head host chain, prefer one repo-owned helper-driven execution surface rather than reconstructing the bounded host sequence by hand. `tools/ai/run_authoritative_host_packet.py` is the preferred execution surface for that chain, and its local `PASS` now requires imported host bootstrap evidence showing a truthful top-level bootstrap `tool`, a truthful top-level bootstrap `command` that still parses to the expected packet-scoped bootstrap invocation plus output path, a truthful `output_artifact` value that still names the expected bootstrap artifact path, a truthful `host_container_root` value that still names the expected host container root, a truthful `implementation_root` value that still names the expected host repo root, a truthful `git.old_clone.path` value that still names the expected historical host clone path, a truthful `git.old_clone.exists` value that still preserves the expected historical host clone presence, a truthful `toolchains.preferred_python.path` value that still preserves the expected host preferred Python path, a truthful `toolchains.python3.path` value that still preserves the expected host Python 3 path, a truthful `toolchains.node.path` value that still preserves the expected host Node path, a truthful `toolchains.pnpm_materialized.path` value that still preserves the expected host pnpm materialized path, a truthful `toolchains.calc_engine_python.path` value that still preserves the expected host calc-engine Python path, a truthful `hold_boundary.minimal_mcp_detail.status` value that still preserves the expected host rest-state mirror, a truthful `hold_boundary.minimal_mcp` value that still preserves the expected host hold-boundary mirror, a truthful `hold_boundary.deferred_ops_decision` value that still preserves the expected host hold-boundary decision, a truthful `hold_boundary.deferred_ops` value that still preserves the expected host hold-boundary deferred-ops mirror, a truthful `hold_boundary.outputs` value that still preserves the expected host hold-boundary outputs mirror, a truthful `hold_boundary.packet_id` value that still preserves the expected host hold-boundary packet-id mirror, matching repo head, `status_count = 0`, and truthful preflight `not-running` state, an imported verifier artifact whose top-level `command` still parses to the expected packet-scoped verifier invocation plus output and profile arguments, plus a coordinator summary that still names the matching verifier and promotion artifacts, the same accepted host run id, the same supporting run ids that appear in the imported promotion artifact, the same host-success run-id set that appears in the imported promotion artifact, promoted supporting run ids that are all backed by the recorded successful host runs, supporting run metadata that stays on `env=host` and the same accepted host service, a top-level promotion `env` plus `service` tuple that stays aligned with that same accepted host env/service, a promotion-record `promoted_at` timestamp that stays aligned with the imported promotion artifact, top-level `artifact_path` values on the imported promotion artifact and coordinator summary that still identify the copied files truthfully, top-level `tool` values on the imported promotion artifact and coordinator summary that still identify the expected repo-owned helper surfaces truthfully, and top-level `command` values on the imported promotion artifact and coordinator summary that still parse to the expected packet-scoped repo helper invocation plus artifact arguments.

Do not treat Packet 830, the helper-bootstrap-toolchains-python3-path floor, Packet 829, the helper-bootstrap-toolchains-preferred-python-path floor, Packet 828, the helper-bootstrap-toolchains-node-path floor, Packet 827, the helper-bootstrap-toolchains-calc-engine-python-path floor, Packet 826, the helper-bootstrap-toolchains-pnpm-materialized-path floor, Packet 825, the helper-bootstrap-hold-boundary-packet-id floor, Packet 824, the helper-bootstrap-hold-boundary-outputs floor, Packet 823, the helper-bootstrap-hold-boundary-deferred-ops floor, Packet 822, the helper-bootstrap-hold-boundary-deferred-ops-decision floor, Packet 821, the helper-bootstrap-hold-boundary-minimal-mcp floor, Packet 820, the helper-bootstrap-hold-boundary-status floor, Packet 819, the helper-bootstrap-old-clone-exists floor, Packet 818, the helper-bootstrap-old-clone-path floor, Packet 817, the helper-bootstrap-container-root floor, Packet 816, the helper-bootstrap-implementation-root floor, Packet 815, the helper-bootstrap-output-path floor, Packet 814, the helper-bootstrap-command floor, Packet 813, the helper-bootstrap-tool floor, Packet 812, the helper-verifier-command floor, Packet 811, the helper-artifact-command floor, Packet 810, the helper-artifact-tool floor, Packet 809, the helper-artifact-self-path floor, Packet 808, the helper-promotion-record-timestamp floor, Packet 807, the helper-promotion-metadata floor, Packet 806, the helper-host-metadata floor, the earlier helper-support-backing, helper-host-success-set, helper-supporting-run, helper-cross-artifact, and helper-parity floors, or the helper-driven host chain as permission to widen the controller, runtime posture, admitted service family, queue ownership, or business-logic scope.

## Packet 791 Alignment Note

Packet `2026-05-13-olares-dev-residency-791` is the current concrete model for the promotion-gate rehearsal row above.

It proves the matrix row now has two complementary repo-owned proof surfaces:

1. `tools/ai/verify_minimal_mcp_trio.py` covers the negative guard by proving sandbox-only promotion refusal,
2. `tools/ai/capture_apex_jobs_promotion.py` covers the positive gate by recording the successful matching `env=host` run, `list_runs` visibility, and `promote_packet` success on the same packet id,
3. the authoritative host can return to truthful `not-running` state after both proofs complete.