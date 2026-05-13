# Packet 789 Handoff - Active AI Wrapper Profile Routing And Strict Artifact

## Packet
- Packet ID: `2026-05-13-olares-dev-residency-789`
- Lane: bounded AI/operator wrapper and evidence hardening
- Scope: route named verifier profiles through the minimal-trio wrappers and capture the first repo-visible strict-profile artifact
- Change type: wrapper contract hardening plus packet-local evidence capture

## Why This Packet
Packet `2026-05-13-olares-dev-residency-788` added the named validation-profile surface to the direct verifier helper.

The next bounded follow-on was to make that same surface reachable through the operator wrappers and to record one real artifact showing the stricter profile running through a packet-local wrapper path instead of only through helper tests.

## What Changed
- Updated `tools/ai/run-minimal-mcp-trio.ps1` so `verify` accepts `-ValidationProfile baseline|strict-db-query` and forwards the selected profile to `tools/ai/verify_minimal_mcp_trio.py`.
- Updated `tools/ai/run-minimal-mcp-trio.sh` so `verify <packet-id> [profile]` validates and forwards the same named profile surface.
- Extended `tests/test_minimal_mcp_powershell_verify_truthfulness.py` and `tests/test_minimal_mcp_bash_verify_truthfulness.py` so wrapper truthfulness coverage matches the current verifier payload shape and proves explicit `strict-db-query` routing.
- Captured the first repo-visible strict-profile verifier artifact at `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-13-olares-dev-residency-789.json` through the PowerShell wrapper against the live admitted trio.
- Updated the validation-profile doc, canary evidence bundle, and status ledger so Packet 789 is recorded as the wrapper-routing and first-strict-artifact floor.

## Validation
- Validation command: `.\.venv\Scripts\python.exe -m pytest tests/test_minimal_mcp_bash_verify_truthfulness.py tests/test_minimal_mcp_powershell_verify_truthfulness.py -q`
- Validation result: `10 passed`
- Validation command: `pwsh -NoProfile -File tools/ai/run-minimal-mcp-trio.ps1 -Action status`
- Validation result: `unmanaged-running` on `8810` through `8812` before the packet run
- Validation command: `pwsh -NoProfile -File tools/ai/run-minimal-mcp-trio.ps1 -Action up -PacketId 2026-05-13-olares-dev-residency-789`
- Validation result: `adopted`
- Validation command: `pwsh -NoProfile -File tools/ai/run-minimal-mcp-trio.ps1 -Action verify -PacketId 2026-05-13-olares-dev-residency-789 -ValidationProfile strict-db-query`
- Validation result: `PASS` with run id `1778684065163-1pnakvu6` and artifact `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-13-olares-dev-residency-789.json`
- Validation command: `pwsh -NoProfile -File tools/ai/run-minimal-mcp-trio.ps1 -Action down`
- Validation result: `stopped`
- Validation command: `pwsh -NoProfile -File tools/ai/run-minimal-mcp-trio.ps1 -Action status`
- Validation result: `unmanaged-running` after wrapper teardown, matching the pre-existing live trio baseline on `8810` through `8812`

## Repo-Visible Evidence
- `tools/ai/run-minimal-mcp-trio.ps1`
- `tools/ai/run-minimal-mcp-trio.sh`
- `tests/test_minimal_mcp_powershell_verify_truthfulness.py`
- `tests/test_minimal_mcp_bash_verify_truthfulness.py`
- `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-13-olares-dev-residency-789.json`
- `docs/operations/OLARES-AI-VALIDATION-PROFILES-2026-05-13.md`
- `docs/operations/AI-BACKBONE-CANARY-EVIDENCE-BUNDLE-2026-05-08.md`
- `PROJECT_STATUS.md`
- `ops/agents/handoffs/2026-05-13-olares-dev-residency-789-active-ai-wrapper-profile-routing-and-strict-artifact-handoff.md`

## Outcome
Packet `2026-05-13-olares-dev-residency-789` closes both bounded follow-ons that remained after Packet 788.

The named verifier profile surface is now reachable through the operator wrappers, and the repo now holds one real packet-scoped `strict-db-query` artifact emitted through that wrapper path instead of relying on helper-only proof.

Because this packet adopted an already-live unmanaged trio rather than starting managed wrapper-owned processes, the truthful post-run runtime baseline returns to `unmanaged-running` once wrapper state is removed.

The next bounded follow-on, if needed, is authoritative-host strict-profile evidence or another similarly narrow evidence-hardening slice, not wider controller or queue admission.

## Boundaries Preserved
- No new MCP service was admitted.
- No `ai_tasks` ownership was admitted.
- No auth, ingress, or runtime scope widened.
- No product or business-logic surface changed.