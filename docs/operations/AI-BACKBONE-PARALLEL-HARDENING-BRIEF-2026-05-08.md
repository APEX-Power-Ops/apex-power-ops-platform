# AI Backbone Parallel Hardening Brief

Date: 2026-05-08
Status: Active bounded parallel-work brief
Scope: adjacent hardening lane that may run in parallel with first-pass backbone scaffold authoring

## Purpose

This brief defines the safest adjacent hardening slice that can run in parallel while a bounded Codex scaffold pass is underway.

It exists to keep the backbone trustworthy without forcing the scaffold pass to also solve runtime-hardening semantics in the same edit slice.

## Parallel Hardening Objectives

The parallel hardening lane may author or tighten only these contract areas:

1. `apex-jobs` env-tag contract,
2. promotion refusal and required `env=host` evidence,
3. provenance metadata rules for AI-generated output,
4. MCP filesystem and database boundary rules,
5. canary admission and evidence requirements for the backbone.

## Allowed Output Types

1. contract docs,
2. checklist docs,
3. validation notes,
4. non-destructive tests or stubs around admitted behavior,
5. packet and handoff evidence describing the hardening lane.

## Forbidden Output Types

1. new orchestration services,
2. queue-owner replacement,
3. auth or public-ingress widening,
4. business-logic edits outside the trust boundary,
5. refactors to the same implementation files already being used for first-pass scaffold work unless coordination is explicit.

## Recommended Parallel Tasks

1. write the exact `env=sandbox|host` contract and examples for `apex-jobs`,
2. specify the minimum evidence required before `promote_packet` may succeed,
3. define the required provenance metadata fields and where they must surface,
4. document MCP boundary rules for allowed roots, mounts, and read/write posture,
5. define the canary proof bundle for the backbone lane.

## Coordination Rules

1. treat the Codex scaffold pass as the owner of shell structure,
2. treat the parallel hardening lane as the owner of trust and evidence contracts,
3. prefer docs, tests, and checklist surfaces over shared implementation edits,
4. if a hardening change must touch a scaffolded file, record that coordination explicitly in packet or handoff evidence.

## Success Condition

This lane is successful when the trust rules around the admitted backbone are clearer, tighter, and more testable, while the scaffold lane remains free to build the shell without implicit runtime expansion.