# Apex Jobs Trust And Promotion Contract

Date: 2026-05-08
Status: Active bounded hardening contract
Scope: exact trust semantics for `apex-jobs` within the admitted Olares AI backbone

## Purpose

This document makes the current `apex-jobs` trust boundary explicit.

It does not widen the admitted AI backbone. It records the current rules already enforced by the admitted `apex-jobs` surface and names the evidence needed for truthful promotion claims.

Use this file with:

1. `AI-BACKBONE-PARALLEL-HARDENING-BRIEF-2026-05-08.md`
2. `../authority/OLARES-AI-BACKBONE-FRAMEWORK-2026-05-08.md`
3. `../architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md`
4. `../../services/mcp/apex-jobs/build/http.js`
5. `../../tools/ai/verify_minimal_mcp_trio.py`

## Current Runtime Owner

The current trust owner remains `apex-jobs`.

Within the admitted backbone it owns:

1. run registration,
2. env tagging,
3. run completion status,
4. promotion refusal unless host evidence exists.

It does not own broader workflow queueing, autonomous orchestration, or service admission.

## Env Contract

`apex-jobs` currently accepts only two env values:

1. `sandbox`
2. `host`

Their semantics are:

1. `sandbox` means the run was executed in a local or development posture and may prove shell correctness, contract resolution, or bounded functional behavior.
2. `host` means the run was executed from the admitted Olares host posture and is the only env class that may satisfy packet-promotion evidence.

Implications:

1. `sandbox` proof may support implementation confidence, but it does not satisfy promotion gates.
2. `host` proof must still be successful and packet-attributed before it can support promotion.
3. No third env class is currently admitted.

## Run Record Minimums

Every `apex-jobs` run record that matters to completion should carry at least:

1. `run_id`
2. `env`
3. `service`
4. `packet_id` when the run supports packet work
5. `status`
6. `created_at`
7. `completed_at` for closed runs
8. operator notes when the result needs explanation

These are the current minimums for trustworthy run-ledger interpretation.

## Promotion Gate Contract

`promote_packet` must refuse promotion unless at least one run exists with all of the following:

1. matching `packet_id`
2. `env=host`
3. `status=success`

Current refusal contract:

1. absence of successful `env=host` evidence is a normal refusal state,
2. refusal is not treated as a runtime failure,
3. sandbox-only success must still refuse.

## Provenance Metadata Contract

The current backbone does not require `apex-jobs` to store every provenance field itself.

It does require AI-assisted outputs that support packet closure or future promotion to preserve provenance across repo-visible artifacts.

Minimum provenance fields for AI-assisted backbone work:

1. `packet_id`
2. execution surface or tool identity
3. env class used for evidence
4. validation command or evidence source
5. resulting run id when `apex-jobs` participated
6. final outcome: `PASS`, `FAIL`, `HOLD`, `UNAVAILABLE`, or equivalent truthful verdict

These fields may live in packet JSON, handoff notes, validation summaries, or other repo-visible evidence surfaces.

## Packet 172 Verification Note

Packet 172 adds one executable proof to the current boundary.

`tools/ai/verify_minimal_mcp_trio.py` now verifies that `promote_packet` refuses a synthetic packet id when no successful `env=host` run is on record, then completes the existing sandbox run start/end validation.

That check is a trust-boundary assertion, not a request to perform promotion.

## Non-Goals

This contract does not:

1. admit `ai_tasks`,
2. replace packet and handoff governance,
3. authorize broader orchestration services,
4. imply that sandbox proof is equivalent to host proof.