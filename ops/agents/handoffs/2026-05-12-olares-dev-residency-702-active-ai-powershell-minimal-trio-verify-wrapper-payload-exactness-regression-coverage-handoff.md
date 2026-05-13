# Olares Dev Residency 702 - Active AI PowerShell Minimal-Trio Verify Wrapper Payload Exactness Regression Coverage Handoff

Date: 2026-05-12
Status: Complete
Packet: `2026-05-12-olares-dev-residency-702`

## Purpose

Close the remaining weaker assertions in the PowerShell minimal-trio verify-wrapper surface by proving the emitted verifier payload exactly across the stored-packet-id, explicit-packet-id, and blocked-output branches.

## Execution Result

Packet 702 is complete.

Extended `tests/test_minimal_mcp_powershell_verify_truthfulness.py` with shared expected-payload helpers so the PowerShell wrapper now proves:

1. state packet-id fallback emits the full verifier payload exactly,
2. explicit `-PacketId` precedence emits the full verifier payload exactly and leaves no stale artifact behind,
3. stdout and the written verify artifact are byte-for-byte the same JSON on successful wrapper paths,
4. blocked output-path failure preserves the full payload exactly minus the OS-shaped top-level write error.

The only normalization left in the file is the generated `jobs_promote_guard.packet_id` suffix.

## Validation Notes

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_powershell_verify_truthfulness.py -q -k "uses_state_packet_id_when_not_provided or prefers_explicit_packet_id_over_state"` failed once on a local test-harness assumption that the fixture returned URLs, then passed after reading the seeded `.env.dev` values instead.
2. `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_powershell_verify_truthfulness.py -q` passed after the exactness helpers and blocked-output assertion upgrade.
3. a follow-up scan found no remaining selected-field assertion pattern in `tests/test_minimal_mcp_powershell_verify_truthfulness.py`.

## Boundaries Preserved

This packet does not open:

1. changes to `tools/ai/run-minimal-mcp-trio.ps1`,
2. changes to `tools/ai/verify_minimal_mcp_trio.py`,
3. broader orchestration or admitted-boundary changes.
