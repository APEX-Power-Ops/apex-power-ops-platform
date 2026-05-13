# Olares AI Delegated Dual-Lane Execution Checklist

Date: 2026-05-13
Status: Active delegated execution checklist
Scope: reusable bounded split pattern for delegated dual-lane packets after Packet 830

## Purpose

Use this checklist when a later Olares AI/operator packet delegates one live evidence lane and one disjoint scaffold or publication lane under coordinator ownership.

The goal is bounded rehearsal, not controller widening. Packet `2026-05-13-olares-dev-residency-830` remains the helper-bootstrap-toolchains-python3-path floor, and later delegated packets must reuse that helper floor unless a separate packet explicitly reopens helper hardening.

## Baseline

Before execution starts, confirm all of the following:

1. `apex-fs`, `apex-db`, and `apex-jobs` remain the only admitted MCP services.
2. `apex-jobs` remains the run and promotion ledger.
3. `ai_tasks` remains deferred and does not arbitrate executor ownership.
4. No auth, ingress, runtime posture, controller scope, or business logic change is in scope.
5. The packet names one packet id and threads it through every lane artifact, validation result, and closeout record.

## Lane Ownership

Declare ownership before any mutation:

1. Lane A owns the helper-driven live evidence tuple only when the packet explicitly names the Packet-specific files under `tests/canary/host-bootstrap-status/actual/` and `tests/canary/mcp-contract/actual/`.
2. Lane B owns exactly one disjoint scaffold, checklist, or guidance surface when the packet names that file directly.
3. Shared publication surfaces stay coordinator-owned and are updated only after both lane tuples are green.
4. Each file has one final write owner.
5. Any file outside the declared lane or coordinator surfaces is out of scope for the packet.

## Validation Order

Run validation in this order:

1. Run the focused helper truthfulness suite before any live helper run.
2. Run the unchanged authoritative-host helper for the packet id only after the focused helper suite passes.
3. Validate the Lane B scaffold with the narrowest repo-available document check.
4. Confirm the live host returned to truthful `not-running` rest state.
5. Update coordinator-owned shared publication surfaces only after Lane A, Lane B, and host rest-state checks are green.
6. Finish with authoritative-host parity restoration or record the exact parity blocker if the packet authorizes a bounded generated-artifact collision remediation.

## Abort Rules

Record `ABORTED` instead of partial success if any of these conditions occur:

1. The helper code or helper tests need mutation in a packet that only authorizes helper reuse.
2. Either lane needs a file outside its declared ownership.
3. A new MCP service, `ai_tasks` ownership, auth change, ingress change, runtime mutation, controller widening, or business-logic mutation is required.
4. The focused helper truthfulness suite fails after reaching the test file.
5. The live helper run fails or cannot return the host to truthful `not-running` rest state.
6. Lane B cannot validate its declared scaffold surface.
7. Shared publication edits would be needed before both lane tuples are green.

## Coordinator Closeout

The coordinator closeout must include:

1. Lane A tuple: focused helper command and result, live helper command and result, exact emitted artifact names, final host rest-state result.
2. Lane B tuple: touched file, validation method, validation result, and exact scaffold scope.
3. Coordinator tuple: shared publication files, combined validation result, authoritative-host parity result, and final verdict of `PASS` or `ABORTED`.
4. Boundary confirmation that no helper mutation, controller widening, service admission widening, auth change, ingress change, runtime mutation, or business-logic mutation was opened.

## Packet 831 Application

Packet `2026-05-13-olares-dev-residency-831` is the first delegated dual-lane rehearsal on top of the Packet 830 helper floor.

For Packet 831:

1. Lane A reuses `tools/ai/run_authoritative_host_packet.py` unchanged for the admitted apex-fs, apex-db, and apex-jobs trio.
2. Lane B owns this checklist only.
3. The coordinator owns `PROJECT_STATUS.md` and the Packet 831 closeout handoff only after both lanes validate.
4. The next step remains another bounded delegated packet or a closeout-routing decision, not controller widening.
