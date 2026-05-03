# TCC Phase 5 Tier B Consumer Need And Adoption Reopen Triggers Handoff

Date: 2026-04-27
Packet: `2026-04-27-tcc-phase-5-tier-b-consumer-need-and-adoption-reopen-triggers`
Status: **Completed 2026-04-28. PASS — no qualifying consumer found for either Tier B view; HOLD on adoption persists.**
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-TIERB-CONSUMER-NEED-AND-ADOPTION-REOPEN-TRIGGERS-2026-04-27.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Project: rebuilt TCC runtime lane against Supabase `fxoyniqnrlkxfligbxmg`

## Execution Result

The consumer-need and adoption-reopen-trigger packet closed PASS on 2026-04-28.

Exact files changed:

1. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5-TIER-B-CONSUMER-NEED-AND-ADOPTION-REOPEN-TRIGGERS-2026-04-27.md`
2. `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
3. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-TIERB-CONSUMER-NEED-AND-ADOPTION-REOPEN-TRIGGERS-2026-04-27.md`

No DB migrations, no runtime/schema/router/test edits.

Exact consumers reviewed:

1. Repo-wide grep passes for `vw_etu_calc_context` and `vw_etu_browse` in `source-domains/tcc_v5_backend/`, `source-domains/neta-ett-study-material/Development/`, frontend source files, and `apex-power-ops-platform/ops/agents/handoffs/`.
2. Live `/context/{sensor_id}` in `services/neta/router.py:2912-2964`.
3. Live `/cascade` in `services/neta/router.py:2767-2905`.
4. Calc-engine `services/calc_engine/etu_ltd.py` direct `tcc_etu_ltd_params` access path.

Exact per-view consumer-need decision:

1. `vw_etu_calc_context`: **NONE FOUND**.
2. `vw_etu_browse`: **NONE FOUND**.

Exact browse harmonization prerequisite statement:

1. The trip-type identity harmonization prerequisite remains active and binding.
2. `vw_etu_browse` omits `trip_type_id` and exposes `trip_type_name`; `/cascade`, `CascadeTripType`, and `CascadeSensor` still require `trip_type_id` as an int FK.
3. Any future browse-adoption packet still requires a separately governed decision to either expose `trip_type_id` on the view without re-adopting the legacy natural-key CTE, or migrate the cascade models to `trip_type_name`.

Exact next-step ruling:

1. HOLD on adoption of both Tier B views persists.
2. Slice 3 remains separately GATED on a measurement packet that has not been authored.
3. The next governed move is conditional on either a future consumer-need execution packet that records a real consumer, or a Slice 3 measurement packet.
4. Neither follow-on packet is in scope here.

## Objective

This handoff delegates the next governed post-HOLD discovery packet.

Claude Code should execute only this slice:

1. determine whether any real current or near-term consumer on disk actually
   needs `vw_etu_calc_context`,
2. determine whether any real current or near-term consumer on disk actually
   needs `vw_etu_browse`,
3. if `vw_etu_browse` has a candidate consumer, state whether a separate
   trip-type identity harmonization packet is required before any adoption work
   can open,
4. return one exact next-step ruling naming either continued HOLD or the
   smallest truthful follow-on packet.

This handoff does **not** authorize runtime implementation, Slice 3 measurement,
Slice 3 materialized facets, Tier C normalization probes, or Phase 6 work.

## Confirmed Entry Gate

The packet is authorized because the required upstream state is already
recorded on disk:

1. Phase 4 acceptance remains closed and preserves the frozen validated ETU
   baseline.
2. Phase 5 Tier A remains closed PASS.
3. The Tier A review/alignment audit is closed PASS.
4. TASK-C is closed PASS for the spec section O safe direct-band surface.
5. Tier B Slice 1 `vw_etu_calc_context` is closed PASS.
6. Tier B Slice 2 `vw_etu_browse` is closed PASS.
7. The post-Slice-2 adoption and Slice 3 target decision packet is closed PASS
   with HOLD on adoption of both Tier B views.
8. No measured browse-latency or operator-simplicity target is currently
   recorded for Slice 3.

If any one of those statements fails when execution begins, stop and return a
blocker report instead of drafting an adoption or measurement follow-on.

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-TIERB-CONSUMER-NEED-AND-ADOPTION-REOPEN-TRIGGERS-2026-04-27.md`
2. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-TIERB-ADOPTION-AND-SLICE3-TARGET-DECISION-2026-04-27.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5-TIER-B-ADOPTION-AND-SLICE3-TARGET-DECISION-2026-04-27.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5-TIER-B-SLICE1-EVIDENCE-2026-04-27.md`
5. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5-TIER-B-SLICE2-EVIDENCE-2026-04-27.md`
6. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-POST-VALIDATION-NORMALIZATION-AND-OPTIMIZATION-2026-04-26.md`
7. `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
8. `source-domains/tcc_v5_backend/services/neta/router.py`
9. `source-domains/tcc_v5_backend/services/neta/schemas.py`
10. `source-domains/tcc_v5_backend/services/calc_engine/etu_ltd.py`

## First Anchors

Start from the already-closed decision evidence and the live runtime contracts
rather than re-exploring the whole repo.

### Consumer-need anchors

1. the HOLD reasoning and re-open triggers in the post-Slice-2 decision packet,
2. the current `/context/{sensor_id}` contract,
3. the current `/cascade` contract,
4. any active planning or operator-facing file that explicitly asks for one of
   the wider derived shapes.

Local hypothesis for the first slice:

- no qualifying consumer is currently recorded on disk, so the likely truthful
  result is continued HOLD unless an active planning or runtime artifact says
  otherwise.

Cheapest falsifying check:

- search the accepted runtime, planning, and operator-facing artifacts for a
  concrete consumer that explicitly needs `context + ltd_params` or one-call
  browse child-relation flags.

### Harmonization anchor

1. `vw_etu_browse` omits `trip_type_id` in favor of `trip_type_name`,
2. `/cascade` and related schemas currently consume `trip_type_id`.

Local hypothesis for the browse branch:

- even if a `vw_etu_browse` consumer appears, browse adoption is still blocked
  until the trip-type identity posture is governed explicitly.

Cheapest falsifying check:

- determine whether the candidate consumer can use `trip_type_name` directly or
  whether it still requires the current `trip_type_id` contract.

## Execution Order

### 1. Reconfirm the boundary

Required outcomes:

1. The entry gate still holds.
2. Slice 3 remains out of scope and separately gated on measurement.
3. No later doc has quietly reopened adoption already.

### 2. Review current consumers and active asks

Required outcomes:

1. Current runtime contract consumers are stated exactly.
2. Any candidate planned consumer is file-backed.
3. The wider view shape needed by each candidate is stated exactly.

Execution rules:

1. Prefer existing runtime or planning artifacts over speculative product ideas.
2. If a consumer cannot be tied to a file-backed artifact, do not count it.
3. Keep `vw_etu_calc_context` and `vw_etu_browse` decisions separate.

### 3. Publish the next-step ruling

Required outcomes:

1. One exact per-view consumer-need decision is published.
2. Any `vw_etu_browse` harmonization prerequisite is named exactly.
3. One exact next packet or hold state is published.

Execution rules:

1. Do not convert lack of evidence into implied adoption momentum.
2. Do not turn this packet into Slice 3 target-setting.
3. Prefer the smallest truthful follow-on packet if a real consumer exists.

## Hard Limits

1. No runtime implementation in this packet.
2. No measurement design or benchmark target-setting for Slice 3.
3. No Slice 3 materialized facet work in this packet.
4. No Tier C or Phase 6 widening.
5. No invented consumer narratives.

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. exact files changed,
2. exact consumers reviewed,
3. exact per-view consumer-need decision,
4. exact browse harmonization prerequisite statement,
5. exact next-step ruling.

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| A file-backed consumer inventory is returned | PASS | PASS |
| Per-view consumer-need posture is stated exactly | PASS | PASS |
| Any browse harmonization prerequisite is named exactly | PASS | PASS |
| One explicit next-step ruling is published | PASS | PASS |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Claude Code is
executing a bounded consumer-need discovery gate, not reopening adoption or
inventing a measurement target. If no qualifying consumer is found on disk,
preserve the HOLD and return that exact ruling instead of improvising a follow-on
implementation slice.