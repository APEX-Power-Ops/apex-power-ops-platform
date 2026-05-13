# Olares Dev Residency 704 - Active AI Minimal-Trio Up Adoption Payload/State Exactness Regression Coverage Handoff

Date: 2026-05-12
Status: Complete
Packet: `2026-05-12-olares-dev-residency-704`

## Purpose

Close the remaining weaker assertions in the minimal-trio `up` adoption truthfulness surface by proving exact wrapper outputs, exact forwarded ownership-probe refusal payloads, and exact adopted-state persistence after normalizing only the generated timestamp field.

## Execution Result

Packet 704 is complete.

Extended `tests/test_minimal_mcp_up_adoption_truthfulness.py` so the current PowerShell and Bash `up` wrapper surface now proves:

1. exact `{"status":"adopted"}` outputs when a live owned trio is already running,
2. exact `{"status":"already-running"}` outputs when managed state points at live processes,
3. exact forwarded ownership-probe payloads for workspace-root and README-preview mismatches,
4. exact adopted-state persistence after normalizing only the dynamic `started_at` field.

This packet also models the Bash adopted-state path and endpoint block exactly via the shell boundary, including the shell-resolved `/mnt/c/...` ledger path.

A follow-up scan found no remaining selected-field assertion pattern in `tests/test_minimal_mcp_up_adoption_truthfulness.py`, so the file is now saturated at exact-capable depth.

## Validation Notes

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_up_adoption_truthfulness.py -q -k "powershell_up_reports_adopted_when_live_trio_exists or powershell_up_refuses_adoption_when_live_trio_reports_foreign_workspace_root or bash_up_reports_adopted_when_live_trio_exists or bash_up_refuses_adoption_when_live_trio_reports_foreign_workspace_root"` failed once because the workspace-root mismatch helper did not include README preview fields, then passed after aligning with `tools/ai/check_apex_fs_ownership.py`.
2. `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_up_adoption_truthfulness.py -q` passed after the exactness helper update.
3. a follow-up scan found no remaining selected-field assertion pattern in `tests/test_minimal_mcp_up_adoption_truthfulness.py`.

## Boundaries Preserved

This packet does not open:

1. changes to `tools/ai/run-minimal-mcp-trio.ps1`,
2. changes to `tools/ai/run-minimal-mcp-trio.sh`,
3. changes to `tools/ai/check_apex_fs_ownership.py`,
4. broader orchestration or admitted-boundary changes.
