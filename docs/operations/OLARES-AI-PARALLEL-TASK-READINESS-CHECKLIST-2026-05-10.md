# Olares AI Parallel Task Readiness Checklist

Date: 2026-05-10
Status: Active bounded execution checklist
Scope: concrete next-step checklist for moving from the current admitted Olares AI backbone toward controlled executor-governed parallel-task ability without widening orchestration scope

## Purpose

This checklist turns the current AI backbone and hardening rules into a practical next-step execution surface.

Use it when a session needs to progress the admitted backbone toward safer parallel task capability without reopening broader orchestration, queue, runtime, or hosting work.

Use this checklist with:

1. `OLARES-MVP-AI-ORCHESTRATION-STATUS-BRIEF-2026-05-10.md`,
2. `../../plan/OLARES-AI-ORCHESTRATION-EXECUTION-PLAN-2026-05-10.md`,
3. `AI-BACKBONE-PARALLEL-HARDENING-BRIEF-2026-05-08.md`,
4. `APEX-JOBS-TRUST-AND-PROMOTION-CONTRACT-2026-05-08.md`,
5. `../architecture/OLARES-AI-ORCHESTRATION-DECISION-SURFACE-2026-05-07.md`,
6. `../authority/OLARES-AI-BACKBONE-FRAMEWORK-2026-05-08.md`,
7. `OLARES-AI-OPERATOR-REAL-WORLD-VALIDATION-MATRIX-2026-05-12.md`.

## Readiness Goal

The immediate goal is not open-ended autonomous parallelism.

The immediate goal is a controlled two-lane model in which:

1. scaffold authoring owns shell structure for the admitted backbone,
2. hardening work owns trust, provenance, promotion, MCP-boundary, and canary contracts,
3. promotion and publication remain governed by `apex-jobs` and repo-visible evidence.

Single-executor execution remains the default.

Open a second executor only when the packet or handoff explicitly proves non-overlapping ownership.

## Checklist A - Preserve The Current Baseline

- confirm `apex-jobs` remains the active run and promotion ledger
- confirm packet and handoff governance remain the active work-queue shape
- confirm the admitted MCP family is still only `apex-fs`, `apex-db`, and `apex-jobs`
- confirm `ai_tasks` is still deferred unless a separate packet explicitly opens it
- confirm current authority docs still point at repo-owned AI backbone and orchestration surfaces

## Checklist B - Executor Assignment

- decide whether the slice is a one-executor or two-executor packet before implementation starts
- name the executor that owns each touched file class or directory lane
- name the executor that owns validation capture and the executor that owns publication prep when those differ
- keep one final write owner per shared file even when review or prep is split across executors
- abort the split if ownership cannot be stated in one short packet or handoff block

## Checklist C - Parallel Hardening Work

- tighten the exact `env=sandbox|host` contract and examples for `apex-jobs`
- keep both `promote_packet` refusal requirements and positive-gate helper-backed success proof explicit and testable
- define or tighten provenance metadata fields required for AI-generated output
- keep the documented MCP filesystem and database boundary rules current, including roots, mounts, and read/write posture
- keep the canary admission and evidence bundle current for the admitted backbone
- route verifier commands, results, and attached evidence through packet JSON validation fields and handoff validation blocks when those surfaces are in scope
- keep optional verifier JSON artifacts inside `tests/canary/mcp-contract/actual/` and reference them from packet JSON or handoff evidence when emitted
- keep optional promotion JSON artifacts inside `tests/canary/mcp-contract/actual/` and reference them from packet JSON or handoff evidence when emitted

## Checklist D - Scaffold Maintenance Work

- keep `services/mcp/apex-fs/`, `services/mcp/apex-db/`, and `services/mcp/apex-jobs/` scaffold shells coherent
- keep `infra/compose.dev.yml` and `.env.dev.template` aligned with the admitted backbone contract
- keep the forms-engine staging shell as the only admitted staging-chart path
- keep canary stubs and shell-level validation surfaces honest about what is deferred
- avoid implying runtime completeness where only scaffold readiness exists

## Checklist E - Coordination Rules

- let scaffold work own shell structure
- let hardening work own trust and evidence contracts
- let a one-executor packet stay one-executor unless a second lane produces real leverage
- prefer docs, tests, checklists, and contract notes over shared implementation edits
- if both lanes must touch one file, record that coordination explicitly in packet or handoff evidence
- abort any split that would blur runtime widening with contract tightening in the same slice

## Checklist F - Stop Conditions

- stop if a change would admit a new orchestration service beyond the current trio
- stop if a change would promote `ai_tasks` into queue ownership without a separate packet
- stop if a change would widen auth, public ingress, or canonical hosting posture
- stop if a change would mutate business logic in `apps/` under cover of backbone work
- stop if a change would claim host-complete proof without real `env=host` evidence

## Checklist G - Gate For Any Wider Parallel Lane

A wider parallel-task lane should open only if all of the following are true:

1. a concrete insufficiency or operator friction is documented,
2. the non-overlap and ownership model is explicit,
3. validation and abort rules are written before execution starts,
4. publication and host-proof cadence remain governed,
5. a separate packet explicitly authorizes the widened boundary.

## Checklist H - Real-World Validation Cadence

- rerun the workstation live-DSN baseline before interpreting host-side changes
- run one host managed cold-start drill before treating the operator path as stable
- run one host adopted-runtime drill before treating adoption behavior as trustworthy
- keep one packet id threaded across bootstrap, verifier, deferred-ops, and packet or handoff evidence for the same scenario
- rehearse sandbox-only promotion refusal separately from host-qualified promotion success
- do not open a two-executor rehearsal until the single-lane host path is already coherent

Current proof floor for this cadence:

- Packet 791 is the current helper-backed host promotion proof floor for the single-lane path
- Packet 786 is the current completed first two-lane rehearsal floor for the coordinator-owned split pattern

## Checklist I - First Two-Lane Rehearsal Evidence Pattern

Use this exact coordinator-owned pattern for any later two-lane rehearsal packet after Packet 786.

Write the block before edits start and keep it short:

- name one packet id for the whole rehearsal and thread it through every lane note, validation result, and closeout record
- name lane A and lane B with the exact files each lane may edit, plus one final write owner per file
- name one lane-level validation step per lane and one coordinator-owned final validation step that checks the combined result
- record one abort owner and one abort rule: if either lane needs a file outside its declared set or cannot complete its validation, both lanes stop and the packet records `ABORTED` rather than silently reassigning work
- record one evidence tuple per lane: touched files, validation command, validation result, and whether the lane finished `PASS` or `ABORTED`
- record one coordinator completion tuple for the packet: ownership remained disjoint, both lane validations ran, no abort rule fired, and the combined evidence is repo-visible
- when a later rehearsal needs one packet-scoped artifact instead of hand-copied tuples, compose the verifier and promotion evidence through `tools/ai/build_ai_packet_evidence_summary.py`
- when a later rehearsal uses `tools/ai/run_authoritative_host_packet.py`, treat the helper artifact as valid only if the imported bootstrap, verifier, promotion, and coordinator-summary artifacts all match the same packet id, remain `PASS`, preserve the imported bootstrap `tool` value truthfully for the expected repo-owned bootstrap surface, preserve the imported bootstrap `command` value truthfully for the expected packet-scoped bootstrap invocation plus output path, preserve the imported bootstrap `output_artifact` value truthfully for the expected bootstrap artifact path, preserve the same accepted host run id through `host_success_runs` and `supporting_run_ids`, preserve the same host-success run-id set between the imported promotion artifact and the coordinator summary, keep every promoted supporting run id backed by the recorded successful host runs, keep the accepted host-success support on `env=host` and the same service as the accepted host run, keep the imported verifier `command` truthful for the expected packet-scoped verifier invocation plus output and profile arguments, keep copied promotion and coordinator-summary `artifact_path` values truthful for the copied files, keep copied promotion and coordinator-summary `tool` values truthful for the expected repo-owned helper surfaces, and keep copied promotion and coordinator-summary `command` values truthful for the expected packet-scoped repo helper invocation plus artifact arguments

For the first rehearsal, prefer a coordinator block that reads like this in packet or closeout evidence:

- lane A ownership: declared files only, with final write ownership explicit
- lane B ownership: declared files only, with final write ownership explicit
- lane A validation: one narrow command or diagnostic scoped to lane A files
- lane B validation: one narrow command or diagnostic scoped to lane B files
- abort rule: stop both lanes on ownership drift, shared-file drift, or failed lane validation
- coordinator closeout: publish one packet-level completion note only after both lane tuples are present

Current baseline note:

- Packet 786 already proved the first completed coordinator-owned two-lane rehearsal using this pattern
- Packet 797 now proves the next coordinator-owned follow-on can keep a trust-hardening code lane and a scaffold-alignment doc lane disjoint while emitting one packet-scoped summary artifact for the preserved Packet 791 proof surfaces
- Packet 801 now proves the preferred authoritative-host helper surface can stay inside the same coordinator-owned pattern while locally rejecting mismatched imported verifier, promotion, or coordinator-summary artifacts instead of treating copied files as sufficient proof
- Packet 803 now proves the same helper surface also rejects promotion-support drift when the accepted host run id is no longer preserved through `host_success_runs` and `supporting_run_ids`
- Packet 804 now proves the same helper surface also rejects coordinator-summary host-success-run drift when the imported promotion artifact and the coordinator summary preserve different `host_success_runs` sets even though the accepted host run id is still present
- Packet 805 now proves the same helper surface also rejects promotion artifacts whose `supporting_run_ids` claim a promoted supporting run that is not backed by the recorded successful host runs
- Packet 806 now proves the same helper surface also rejects supporting runs that drift off `env=host` or off the accepted host service even when the packet id, run id, and success status still look coherent
- Packet 807 now proves the same helper surface also rejects promotion tuples whose top-level `env` or `service` drift away from the accepted host run across the imported promotion artifact or coordinator summary even when the nested run metadata still looks coherent
- Packet 808 now proves the same helper surface also rejects coordinator summaries whose promotion-record `promoted_at` timestamp drifts away from the imported promotion artifact even when the packet id and supporting-run ids still look coherent
- Packet 809 now proves the same helper surface also rejects copied promotion artifacts and copied coordinator summaries whose own top-level `artifact_path` no longer matches the copied file even when the packet id, run metadata, and promotion metadata still look coherent
- Packet 810 now proves the same helper surface also rejects copied promotion artifacts and copied coordinator summaries whose top-level `tool` no longer matches the expected repo-owned helper surface even when the packet id, run metadata, promotion metadata, and self `artifact_path` still look coherent
- Packet 811 now proves the same helper surface also rejects copied promotion artifacts and copied coordinator summaries whose top-level `command` no longer matches the expected packet-scoped repo helper invocation even when the packet id, run metadata, promotion metadata, self `artifact_path`, and top-level `tool` still look coherent
- Packet 812 now proves the same helper surface also rejects copied verifier artifacts whose top-level `command` no longer matches the expected packet-scoped verifier invocation even when the packet id, result, and profile still look coherent
- Packet 813 now proves the same helper surface also rejects copied host bootstrap artifacts whose top-level `tool` no longer matches the expected repo-owned bootstrap surface even when the packet id, repo head, and preflight rest-state evidence still look coherent
- Packet 814 now proves the same helper surface also rejects copied host bootstrap artifacts whose top-level `command` no longer matches the expected packet-scoped bootstrap invocation plus output path even when the packet id, repo head, bootstrap tool, and preflight rest-state evidence still look coherent
- Packet 815 now proves the same helper surface also rejects copied host bootstrap artifacts whose `output_artifact` no longer matches the expected packet-scoped bootstrap artifact path even when the packet id, repo head, bootstrap tool, bootstrap command, and preflight rest-state evidence still look coherent
- later packets should preserve and reuse this pattern rather than describing the first rehearsal as still pending

## Current Recommendation

Use the current AI backbone as a controlled executor model: one executor by default, or two executors only when scaffold maintenance and trust hardening can stay disjoint.

Do not treat the existence of those two lanes as approval for autonomous orchestration, multi-worker mutation, or generic parallel source execution.