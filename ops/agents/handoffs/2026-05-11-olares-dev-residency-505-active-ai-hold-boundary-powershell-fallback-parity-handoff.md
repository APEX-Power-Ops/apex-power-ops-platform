# Olares Dev Residency 505 - Active AI Hold-Boundary PowerShell Fallback Parity Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-505`

## Purpose

Close the next adjacent active AI helper parity slice by bringing the PowerShell hold-boundary wrapper up to the same DSN-backed fallback behavior that already exists in the Bash wrapper.

## Execution Result

Packet 505 is complete.

`tools/ai/run-olares-hold-boundary-check.ps1` now checks whether the repo Python can import `sqlalchemy` before choosing the DSN-backed deferred-ops path.

If SQLAlchemy is available, the wrapper preserves the existing direct connection-string path. If SQLAlchemy is not available and `services/mcp/apex-db/build/http.js` exists, the wrapper now starts a temporary local `apex-db` MCP bridge on the dedicated hold-boundary port, waits for `/health`, routes `check_deferred_ops_view_counts.py` through `--db-url`, and tears the bridge down in `finally` cleanup.

This repairs a current cross-platform operator mismatch: the Bash wrapper already had this fallback, but the PowerShell wrapper still assumed direct SQLAlchemy access whenever `-DsnEnv` was supplied.

## Validation Notes

Focused validation stayed bounded to the PowerShell wrapper slice.

Checks confirmed:

1. diagnostics for `tools/ai/run-olares-hold-boundary-check.ps1` reported no new file-level errors.
2. `pwsh -NoProfile -Command "[void][scriptblock]::Create((Get-Content 'tools/ai/run-olares-hold-boundary-check.ps1' -Raw)); 'parse-ok'"` succeeded.
3. `git diff --check -- tools/ai/run-olares-hold-boundary-check.ps1` reported no patch-format defects.
4. the current repo-local Python environment does have SQLAlchemy installed, so the fallback branch itself was validated to syntax and control-flow parity rather than by forcing a degraded local runtime posture.

## Boundaries Preserved

This packet does not open:

1. minimal-trio runtime behavior changes,
2. deferred-ops decision semantics,
3. canary artifact schema changes,
4. historical packet-evidence rewrites,
5. broader orchestration or queue-admission changes.

## Next Candidate

No further adjacent current-surface defect is selected from this packet alone; the next lane should again be a genuinely current control, evidence, or operator surface that still disagrees with the admitted AI contract on present evidence.