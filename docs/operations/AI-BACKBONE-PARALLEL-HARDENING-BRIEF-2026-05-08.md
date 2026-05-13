# AI Backbone Parallel Hardening Brief

Date: 2026-05-08
Status: Active bounded parallel-work brief
Scope: adjacent hardening lane pattern for later coordinator-owned parallel packets inside the admitted backbone

## Purpose

This brief defines the safest adjacent hardening slice that can run in parallel with a bounded scaffold or maintenance lane inside the admitted backbone.

It exists to keep the backbone trustworthy without forcing the paired lane to also solve runtime-hardening semantics in the same edit slice.

Use this brief with:

1. `APEX-JOBS-TRUST-AND-PROMOTION-CONTRACT-2026-05-08.md`
2. `AI-BACKBONE-CANARY-EVIDENCE-BUNDLE-2026-05-08.md`
3. `../authority/OLARES-AI-BACKBONE-FRAMEWORK-2026-05-08.md`

## Parallel Hardening Objectives

The parallel hardening lane may author or tighten only these contract areas:

1. `apex-jobs` env-tag contract,
2. promotion refusal, positive-gate proof, and required `env=host` evidence,
3. provenance metadata rules for AI-generated output,
4. MCP filesystem and database boundary rules,
5. canary admission and evidence requirements for the backbone.

## Allowed Output Types

1. contract docs,
2. checklist docs,
3. validation notes,
4. non-destructive tests or stubs around admitted behavior,
5. packet and handoff evidence describing the hardening lane,
6. bounded repo-owned helper surfaces that only drive the already admitted host chain and capture repo-visible evidence for the same packet id.

## Forbidden Output Types

1. new orchestration services,
2. queue-owner replacement,
3. auth or public-ingress widening,
4. business-logic edits outside the trust boundary,
5. refactors to the same implementation files already being used for first-pass scaffold work unless coordination is explicit.

## Recommended Parallel Tasks

1. write the exact `env=sandbox|host` contract and examples for `apex-jobs`,
2. specify the minimum evidence required before `promote_packet` may succeed and the helper or artifact path that records it,
3. define the required provenance metadata fields and where they must surface,
4. document MCP boundary rules for allowed roots, mounts, and read/write posture,
5. define the canary proof bundle for the backbone lane,
6. author or tighten one helper-driven runtime/evidence capture lane that reuses the admitted host chain without adding a new controller, service, or queue owner.

## Coordination Rules

1. treat the Codex scaffold pass as the owner of shell structure,
2. treat the parallel hardening lane as the owner of trust and evidence contracts,
3. prefer docs, tests, checklist surfaces, and bounded repo-owned helper wrappers over shared implementation edits,
4. if a hardening change must touch a scaffolded file, record that coordination explicitly in packet or handoff evidence.

## Current Alignment Note

Packet `2026-05-13-olares-dev-residency-786` is the current completed rehearsal floor for the first coordinator-owned two-lane packet.

Packet `2026-05-13-olares-dev-residency-791` is the current promotion-proof floor for the positive gate on the same hardened `apex-jobs` path.

Packet `2026-05-13-olares-dev-residency-797` is the current coordinator-summary helper convention for later dual-lane packets through `tools/ai/build_ai_packet_evidence_summary.py`.

Packet `2026-05-13-olares-dev-residency-798` is the current-head authoritative-host floor for later dual-lane packets on the admitted host path.

Packet `2026-05-13-olares-dev-residency-823` is the current helper-bootstrap-hold-boundary-deferred-ops validation floor: `tools/ai/run_authoritative_host_packet.py` now fails closed unless the imported host bootstrap artifact proves the expected packet id, preserves the expected repo-owned bootstrap `tool` value, preserves a top-level `command` value that parses to the expected packet-scoped bootstrap invocation plus output path, preserves an `output_artifact` value that truthfully identifies the expected packet-scoped bootstrap artifact path, preserves a `host_container_root` value that truthfully identifies the expected host container root, preserves an `implementation_root` value that truthfully identifies the expected host repo root, preserves a `git.old_clone.path` value that truthfully identifies the expected historical host clone path, preserves a `git.old_clone.exists` value that truthfully identifies the expected historical host clone presence, preserves a `hold_boundary.minimal_mcp_detail.status` value that truthfully identifies the expected host rest-state mirror, preserves a `hold_boundary.minimal_mcp` value that truthfully identifies the expected host hold-boundary mirror, preserves a `hold_boundary.deferred_ops_decision` value that truthfully identifies the expected host hold-boundary decision, preserves a `hold_boundary.deferred_ops` value that truthfully identifies the expected host hold-boundary deferred-ops mirror, shows a clean host worktree, the same repo head, and a truthful preflight `not-running` status, unless the imported verifier artifact preserves the expected packet id, `PASS` result, validation profile, and a top-level `command` value that parses to the expected packet-scoped verifier invocation plus output and profile arguments, unless the imported coordinator summary still points at the matching verifier and promotion artifacts while preserving the same accepted host run id, unless that accepted host run id is preserved all the way through `host_success_runs` and `supporting_run_ids` on both the promotion artifact and the coordinator summary, unless the coordinator summary preserves the same host-success run-id set as the imported promotion artifact, unless every promoted supporting run id is backed by the recorded successful host runs, unless the accepted supporting runs stay on `env=host` and the same service as the accepted host run, unless the top-level promotion `env` plus `service` tuple also stays aligned with that same accepted host env/service across both the imported promotion artifact and the coordinator summary, unless the coordinator summary promotion record preserves the same `promoted_at` timestamp as the imported promotion artifact, unless the imported promotion artifact plus the imported coordinator summary both preserve top-level `artifact_path` values that truthfully identify the copied files, unless those imported promotion and coordinator-summary artifacts also preserve top-level `tool` values that truthfully identify the expected repo-owned helper surfaces, and unless those imported promotion and coordinator-summary artifacts also preserve top-level `command` values that parse to the expected packet-scoped repo helper invocation plus artifact arguments.

For current-head host-chain packets, prefer one bounded helper-driven execution lane over ad hoc command reconstruction. `tools/ai/run_authoritative_host_packet.py` is the preferred repo-owned execution surface for that chain when later packets must both run the host path and verify imported parity evidence plus cross-artifact coherence locally.

Use this brief for later disjoint parallel packets only when those floors remain preserved rather than reopened as open questions, and keep the helper lane bounded to runtime/evidence capture on the already admitted trio.

## Success Condition

This lane is successful when the trust rules around the admitted backbone are clearer, tighter, and more testable, while the scaffold lane remains free to build the shell without implicit runtime expansion.