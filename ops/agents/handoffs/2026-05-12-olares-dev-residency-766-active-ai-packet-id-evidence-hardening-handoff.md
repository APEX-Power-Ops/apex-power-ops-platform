# Packet 766 Handoff - AI Packet-ID Evidence Hardening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-766`
- Lane: active AI/operator boundary truthfulness
- Scope: shared shell packet-id helpers, Bash and PowerShell minimal-trio wrappers, Bash and PowerShell hold-boundary wrappers, Bash host-bootstrap wrapper, focused packet-id regression coverage, and authoritative-host malformed-artifact cleanup
- Change type: packet-id validation hardening plus host residue cleanup

## Why This Packet
Packet 765 closed the managed-start readiness race, but the next adjacent defect was still visible in the authoritative host evidence lane.

Observed residue:

1. earlier SSH quoting drift had already produced malformed repo-visible artifact filenames on the authoritative mirror,
2. those malformed files included `tests/canary/host-bootstrap-status/actual/host-bootstrap-status-  .json` and `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-\.json`,
3. the shared packet-id helpers and wrapper entrypoints were still willing to pass raw packet-id values straight into output filenames.

That meant packet-id truthfulness was still too trusting even after the startup surfaces were repaired.

## What Changed
- Updated `tools/shell/common.sh` and `tools/shell/common.ps1` so env-sourced packet ids are rejected unless they match `^[A-Za-z0-9][A-Za-z0-9._-]*$`.
- Updated these wrappers to validate explicit packet ids before writing any repo-visible state or artifact path:
  - `tools/ai/run-minimal-mcp-trio.sh`
  - `tools/ai/run-minimal-mcp-trio.ps1`
  - `tools/ai/run-olares-hold-boundary-check.sh`
  - `tools/ai/run-olares-hold-boundary-check.ps1`
  - `tools/ai/run-olares-host-bootstrap-status.sh`
- Extended focused regression coverage in:
  - `tests/test_shell_common_packet_id_truthfulness.py`
  - `tests/test_minimal_mcp_started_truthfulness.py`
- Published the Bash-side guard files to the authoritative host mirror and verified that invalid packet ids now fail before artifact creation.
- Removed the old malformed host artifact files that predated the guard.

## Validation
- Focused local executable validation:
  - `./.venv/Scripts/python.exe -m pytest tests/test_shell_common_packet_id_truthfulness.py tests/test_minimal_mcp_started_truthfulness.py -k "packet_id or test_bash_up_reports_started_and_persists_managed_state" -q`
  - Result: pass (`11 passed`).
- Authoritative-host validation:
  - `bash tools/ai/run-olares-host-bootstrap-status.sh "bad packet id"`
  - Result: exit `1`, stderr `Invalid packet id 'bad packet id'. Packet ids must match ^[A-Za-z0-9][A-Za-z0-9._-]*$.`, and no malformed artifact file was created.
- Authoritative-host cleanup:
  - removed:
    - `tests/canary/host-bootstrap-status/actual/host-bootstrap-status-  .json`
    - `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-\.json`

## Outcome
Packet 766 closes the evidence-path hardening gap that remained after the host startup repairs.

The current boundary is now clearer:

1. startup truthfulness is repaired through Packets 764 and 765,
2. packet-id truthfulness now prevents malformed repo-visible artifact names from recurring,
3. publication parity is still an explicit later gate because the authoritative host mirror currently carries bounded unpublished working-tree repairs rather than published canonical history.

## Boundaries Preserved
- No new MCP service admitted.
- No `ai_tasks` queue authority admitted.
- No auth, ingress, or business-logic widening admitted.
- No live-DSN claim was made.
- No valid proof artifact was removed; only malformed host residue from the earlier quoting drift was deleted.