# Packet 773b Handoff - AI Workstation Live-DSN Managed Baseline Proof

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-773b`
- Lane: active AI/operator boundary validation execution
- Scope: live workstation baseline proof with governed DSN plus wrapper alias repair after default-port adoption residue surfaced
- Change type: bounded wrapper fix, targeted regression coverage, real-world validation proof, and runbook/status closeout

## Why This Packet
Packet 772 published the non-git credential-sourcing path.

The next truthful move was to actually run the workstation live-DSN baseline.

That execution exposed a real local defect:

1. the governed DSN could be loaded from the non-git credentials surface,
2. the hold-boundary wrapper honored it,
3. but the minimal-trio wrappers still ignored `APEX_OLARES_LIVE_DSN`,
4. so `verify_minimal_mcp_trio` degraded `db_query` with `Database connection is not configured.`

After the alias repair landed, the next rerun on the default ports still adopted an already-running local trio and therefore did not prove the managed baseline path.

The controlled proof packet was the fresh-port rerun.

## What Changed
- Updated `tools/ai/run-minimal-mcp-trio.ps1` so `Get-DbConnectionString` now prefers `APEX_OLARES_LIVE_DSN` before `SEAM_DATABASE_URL`.
- Updated `tools/ai/run-minimal-mcp-trio.sh` so `get_db_connection_string` now prefers `APEX_OLARES_LIVE_DSN` before `SEAM_DATABASE_URL`.
- Added focused regression coverage in `tests/test_minimal_mcp_started_truthfulness.py`:
  - PowerShell runtime proof that the DB child process receives `APEX_DB_CONNECTION_STRING` when only `APEX_OLARES_LIVE_DSN` is set,
  - Bash precedence proof that the wrapper resolves `APEX_OLARES_LIVE_DSN` before the older fallback variables.
- Updated the governed live-DSN sourcing runbook to match current wrapper precedence.
- Updated the workstation baseline runbook to stop on default-port adoption residue unless the packet is explicitly testing adoption behavior.
- Updated `PROJECT_STATUS.md` through Packet 773b.

## Validation
- Focused regression checks:
  - `python -m pytest tests/test_minimal_mcp_started_truthfulness.py -k "operator_live_dsn or prefers_operator_live_dsn" -q`
- Real-world execution proof:
  - initial default-port rerun adopted an already-running local trio and still showed a degraded DB query on that adopted runtime,
  - fresh-port managed rerun under `2026-05-12-olares-dev-residency-773b` produced:
    - `up = started`,
    - `status = managed-running`,
    - `verify = PASS` with `db_query.status = pass`,
    - `deferred_ops = HOLD`,
    - `down = stopped`.

Repo-visible artifacts:
- `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-12-olares-dev-residency-773.json`
- `tests/canary/deferred-ops-view-counts/actual/deferred-ops-view-counts-2026-05-12-olares-dev-residency-773.json`
- `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-12-olares-dev-residency-773b.json`
- `tests/canary/deferred-ops-view-counts/actual/deferred-ops-view-counts-2026-05-12-olares-dev-residency-773b.json`

## Outcome
The workstation live-DSN baseline is now executable from the governed non-git credential source.

The local blocker was not the DSN anymore.

It was one wrapper alias gap plus local default-port adoption residue.

The alias gap is fixed.

The workstation proof now shows the intended truth surface on a managed trio:

1. admitted MCP trio verifies cleanly,
2. live DB query succeeds,
3. deferred Operations Visibility seams still truthfully hold,
4. no host-qualified promotion claim is made from workstation evidence.

## Boundaries Preserved
- No new MCP service was admitted.
- No `ai_tasks` queue authority was admitted.
- No secrets were written into the repo.
- No auth or ingress scope widened.
- No business-logic mutation lane was opened.