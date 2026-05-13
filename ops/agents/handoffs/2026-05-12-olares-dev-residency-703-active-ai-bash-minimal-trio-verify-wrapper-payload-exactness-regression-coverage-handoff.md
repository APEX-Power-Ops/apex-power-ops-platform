# Olares Dev Residency 703 - Active AI Bash Minimal-Trio Verify Wrapper Payload Exactness Regression Coverage Handoff

Date: 2026-05-12
Status: Complete
Packet: `2026-05-12-olares-dev-residency-703`

## Purpose

Close the remaining weaker assertions in the Bash minimal-trio verify-wrapper surface by proving the emitted verifier payload exactly across the stored-packet-id, explicit-packet-id, and blocked-output branches.

## Execution Result

Packet 703 is complete.

Extended `tests/test_minimal_mcp_bash_verify_truthfulness.py` with shared expected-payload helpers so the Bash wrapper now proves:

1. state packet-id fallback emits the full verifier payload exactly,
2. explicit packet-id precedence emits the full verifier payload exactly and leaves no stale artifact behind,
3. stdout and the written verify artifact are byte-for-byte the same JSON on successful wrapper paths,
4. blocked output-path failure preserves the full payload exactly minus the OS-shaped top-level write error.

This packet also models the Bash-specific command shape exactly: the shell-resolved interpreter from `get_apex_preferred_python`, the shell repo root from `get_apex_repo_root`, the `/mnt/c/...` verify artifact path in command metadata, and the fake Bash server's shared five-tool list across all three endpoints.

The only normalization left in the file is the generated `jobs_promote_guard.packet_id` suffix.

## Validation Notes

Checks confirmed:

1. a direct payload probe of `bash tools/ai/run-minimal-mcp-trio.sh verify` established the Bash-specific command shape and shared tool-list behavior before editing.
2. `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_bash_verify_truthfulness.py::test_bash_verify_uses_state_packet_id_when_not_provided -q` failed once on Windows-vs-Bash output-path modeling, then passed after the expected command helper switched to the shell repo root.
3. `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_bash_verify_truthfulness.py -q` passed after the exactness helpers and blocked-output assertion upgrade.
4. a follow-up scan found no remaining selected-field assertion pattern in `tests/test_minimal_mcp_bash_verify_truthfulness.py`.

## Boundaries Preserved

This packet does not open:

1. changes to `tools/ai/run-minimal-mcp-trio.sh`,
2. changes to `tools/ai/verify_minimal_mcp_trio.py`,
3. broader orchestration or admitted-boundary changes.
