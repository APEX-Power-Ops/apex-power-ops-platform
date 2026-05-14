# Olares AI Orchestration Execution Plan

Date: 2026-05-10
Status: Active bounded execution plan
Scope: convert the current admitted Olares AI backbone into an executable near-term plan with phased steps, validation gates, and explicit stop conditions

## Purpose

This plan turns the current AI orchestration decision stack into one executable delivery surface.

It does not reopen broad orchestration design.

It exists to answer four concrete questions:

1. what the current AI orchestration target actually is,
2. what sequence should be executed next,
3. what must be validated at each phase,
4. what conditions block any wider orchestration move.

Use this plan with:

1. `../docs/architecture/OLARES-AI-ORCHESTRATION-DECISION-SURFACE-2026-05-07.md`,
2. `../docs/operations/OLARES-MVP-AI-ORCHESTRATION-STATUS-BRIEF-2026-05-10.md`,
3. `../docs/operations/OLARES-AI-PARALLEL-TASK-READINESS-CHECKLIST-2026-05-10.md`,
4. `../docs/authority/OLARES-AI-BACKBONE-FRAMEWORK-2026-05-08.md`,
5. `../docs/operations/APEX-JOBS-TRUST-AND-PROMOTION-CONTRACT-2026-05-08.md`,
6. `../docs/operations/OLARES-AI-OPERATOR-REAL-WORLD-VALIDATION-MATRIX-2026-05-12.md`,
7. `../docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-EXECUTION-CHECKLIST-2026-05-13.md`,
8. `../docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-OPERATOR-PROMPT-TEMPLATE-2026-05-13.md`,
9. `../docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-COORDINATOR-CLOSEOUT-TEMPLATE-2026-05-13.md`,
10. `../docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-PACKET-TEMPLATE-2026-05-13.md`.

## Current Target

The current target is not autonomous orchestration.

The current target is a controlled executor-governed model with these boundaries:

1. `apex-jobs` remains the run and promotion ledger,
2. packet and handoff governance remain the queue shape,
3. the admitted MCP family remains `apex-fs`, `apex-db`, and `apex-jobs`,
4. one bounded executor is the default,
5. two executors are allowed only for explicit non-overlapping lanes,
6. `ai_tasks` remains deferred.

## Outcome Definition

This plan is successful when all of the following are true:

1. the current AI lane can be resumed from one plan plus repo-visible evidence,
2. scaffold maintenance and trust hardening can run as either one lane or two disjoint lanes without boundary confusion,
3. every claimed completion still routes through `apex-jobs`, packet evidence, and host-gated promotion rules,
4. a future widening decision can only happen from explicit documented insufficiency rather than convenience.

## Phase Model

### Phase 0 - Preserve Current Baseline

Goal: keep the admitted boundary stable before any new follow-on work opens.

Required checks:

1. confirm `apex-jobs` is still the active run and promotion ledger,
2. confirm the admitted MCP family is still only `apex-fs`, `apex-db`, and `apex-jobs`,
3. confirm `ai_tasks` is still deferred,
4. confirm repo-owned authority docs still point at the repo-owned AI surfaces rather than parent-root or `.claude` residue.

Exit gate:

1. no active source states a broader controller, wider MCP family, or broader executor authority than the current decision surface allows.

### Phase 1 - Operational Readiness Consolidation

Goal: make the current lane easy to resume and audit.

Deliverables:

1. this execution plan,
2. aligned status brief, checklist, and decision-surface references,
3. one current statement of the near-term sequence and stop conditions.

Validation:

1. document references resolve cleanly,
2. no active surface contradicts the current executor or MCP boundary.

Exit gate:

1. an operator can answer "what do we do next" without reconstructing packet history.

### Phase 2 - Trust And Evidence Hardening

Goal: make the current bounded backbone safer and easier to verify.

Priority work:

1. keep `env=sandbox|host` contract examples exact and current,
2. keep `promote_packet` refusal rules explicit and testable,
3. keep provenance field requirements current,
4. keep MCP path, mount, and read or write posture current,
5. keep verifier commands and repo-visible artifact paths current.

Preferred output types:

1. docs,
2. verifier scripts,
3. canary artifacts,
4. packet-validation blocks,
5. handoff evidence.

Validation:

1. focused verifier or canary reruns for touched trust surfaces,
2. repo-visible evidence written to the admitted canary lanes,
3. no widened runtime or business-logic scope.

Exit gate:

1. the current trio can be revalidated without ambiguous evidence routing or stale examples.

### Phase 3 - Scaffold Maintenance

Goal: keep the admitted shells coherent without implying runtime completeness.

Priority work:

1. keep `services/mcp/apex-fs/`, `services/mcp/apex-db/`, and `services/mcp/apex-jobs/` scaffold shells coherent,
2. keep `infra/compose.dev.yml` and `.env.dev.template` aligned with the admitted trio,
3. keep `infra/olares/forms-engine/` as the only admitted staging-shell path,
4. keep canary and checklist surfaces honest about what is real versus deferred.

Validation:

1. narrow build or lint slices for touched scaffold surfaces,
2. focused canary or smoke validation when shell behavior changes,
3. explicit proof that no new orchestration service was admitted.

Exit gate:

1. the scaffold lane remains truthful about what exists and what is still intentionally deferred.

### Phase 4 - Controlled Two-Lane Parallel Execution

Goal: enable a safe two-executor pattern without widening the orchestration boundary.

Current delegated proof floor for this phase:

1. Packet `2026-05-13-olares-dev-residency-830` remains the authoritative-host helper floor for this packet cadence.
2. Packet `2026-05-13-olares-dev-residency-831` remains the delegated split-governance checklist floor.
3. Packet `2026-05-13-olares-dev-residency-832` remains the delegated operator prompt template floor.
4. Packet `2026-05-13-olares-dev-residency-833` remains the delegated coordinator closeout template floor.
5. Packet `2026-05-13-olares-dev-residency-834` remains the delegated packet-definition template floor.
6. Packet `2026-05-13-olares-dev-residency-835` remains the higher-level orchestration entry-surface alignment floor.

Allowed shape:

1. one executor owns scaffold maintenance,
2. one executor owns trust, provenance, promotion, MCP-boundary, or canary hardening,
3. one final write owner exists for every touched file,
4. validation order and abort rules are written before edits start.

Required preconditions:

1. the split is packetized or handed off in writing,
2. file ownership is disjoint or final-write ownership is explicit,
3. publication and host-proof cadence remain centrally governed,
4. the work stays inside the admitted MCP trio and staging-shell boundary.

Implementation note:

1. when a new delegated two-lane packet opens, reuse the published Packet 831 checklist, Packet 832 operator prompt template, Packet 833 coordinator closeout template, and Packet 834 packet-definition template instead of hand-authoring those control blocks again.
2. preserve the Packet 839-aligned higher-level guidance posture, the Packet 838-aligned post-guidance control posture, the Packet 837-aligned live guidance posture, the Packet 835-aligned orchestration entry surfaces, and the Packet 836-aligned execution plan plus authority posture when classifying the next bounded slice.

Validation:

1. each lane validates its own touched surface,
2. one coherent completion record captures the combined outcome,
3. any promotion claim still requires real `env=host` evidence.

Exit gate:

1. a two-executor slice can finish without shared queue control, overlapping file ownership confusion, or widened runtime scope.

### Phase 5 - Widening Decision Gate

Goal: prevent convenience-driven scope creep.

Do not open a wider orchestration lane unless all of the following are true:

1. a concrete operator insufficiency is recorded,
2. the new boundary is named explicitly,
3. validation and abort rules are written before execution starts,
4. publication and host-proof rules remain intact,
5. a separate packet authorizes the widening.

Examples that remain blocked by default:

1. `ai_tasks` ownership,
2. more than two active executors in one mutation lane,
3. new orchestration services beyond the admitted trio,
4. auth or public-ingress widening,
5. business-logic mutation under cover of AI backbone work.

## Execution Sequence

Use this default near-term order:

1. preserve the current baseline,
2. consolidate the operational read surface,
3. choose one bounded follow-on slice,
4. classify that slice as trust-hardening or scaffold-maintenance,
5. decide one executor or two executors before implementation,
6. run the narrowest truthful validation,
7. capture repo-visible evidence,
8. publish only after the evidence is coherent.

## Step Template For A New Slice

When a new AI orchestration slice opens, answer these in order:

1. what exact boundary is changing,
2. is this trust hardening or scaffold maintenance,
3. does it require one executor or two,
4. who owns each touched file class,
5. what is the first focused validation command,
6. what evidence artifact or handoff block will close it,
7. what widening remains explicitly out of scope.

## Current Recommended Next Steps

The truthful next steps are:

1. keep this plan, the status brief, and the readiness checklist aligned,
2. use the real-world validation matrix to prove the host operator path before opening any new widening discussion,
3. open new work as one bounded delegated packet at a time and reuse the published Packet 831 through Packet 834 execution surfaces rather than hand-authoring control scaffolding,
4. preserve the Packet 839-aligned higher-level guidance posture, the Packet 838-aligned post-guidance control posture, the Packet 837-aligned live guidance posture, the Packet 835-aligned entry-surface posture, and the Packet 836-aligned execution plan plus authority posture while choosing the next disjoint lane objective,
5. prefer trust-hardening and evidence-routing improvements before any new shell widening,
6. use two executors only when the split is obviously disjoint and written down first,
7. keep host-evidence and promotion control central rather than executor-local.

## Stop Conditions

Stop and escalate if a proposed slice would:

1. admit a new orchestration service,
2. make `ai_tasks` the live queue owner,
3. widen auth, ingress, or hosting posture,
4. mutate application business logic under the AI backbone label,
5. claim completion without host-evidence where host-evidence is required.

## Interpretation Rule

This plan is an execution surface for the current admitted AI lane.

It is not authorization for broader autonomous orchestration, generic multi-agent mutation, or expansion beyond the admitted MCP trio.