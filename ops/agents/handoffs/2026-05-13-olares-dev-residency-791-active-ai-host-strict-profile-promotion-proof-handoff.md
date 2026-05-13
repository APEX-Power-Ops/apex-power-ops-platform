# Packet 791 Handoff - Active AI Host Strict Profile Promotion Proof

## Packet
- Packet ID: `2026-05-13-olares-dev-residency-791`
- Lane: bounded AI/operator promotion-eligible authoritative-host follow-on
- Scope: pair same-packet authoritative-host strict verifier evidence with successful `env=host` run and `promote_packet` proof through a repo-owned helper
- Change type: repo-side provenance helper hardening plus authoritative-host runtime evidence publication

## Why This Packet
Packet `2026-05-13-olares-dev-residency-790` proved the first authoritative-host `strict-db-query` verifier artifact and truthful host rest-state return.

The next two bounded lanes still named by the status ledger were tightly adjacent:

1. a promotion-eligible authoritative-host follow-on so strict-profile proof was not isolated from the real `apex-jobs` gate,
2. a similarly narrow repo-side provenance hardening slice so that positive-gate promotion evidence was captured through a reusable helper instead of one-off shell material.

## What Changed
- Added `tools/ai/capture_apex_jobs_promotion.py` to record one packet-scoped successful run, verify `list_runs` visibility, and capture `promote_packet` success as repo-visible JSON.
- Added `tests/test_capture_apex_jobs_promotion_truthfulness.py` for helper success, env packet-id, ad hoc packet-id, missing-run, and promotion-error branches.
- Ran the authoritative host wrapper path for Packet `2026-05-13-olares-dev-residency-791` and captured a `strict-db-query` verifier artifact at `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-13-olares-dev-residency-791.json`.
- Used the new helper on the authoritative host to record a successful `env=host` run and successful `promote_packet` result at `tests/canary/mcp-contract/actual/apex-jobs-promotion-2026-05-13-olares-dev-residency-791.json`.
- Updated the trust contract and status ledger so Packet 791 is the current promotion-eligible strict-profile floor.

## Validation
- Focused helper tests: `& "c:\APEX Platform\apex-power-ops-platform\.venv\Scripts\python.exe" -m pytest tests/test_capture_apex_jobs_promotion_truthfulness.py -q`
- Focused helper test result: `5 passed`
- Host preflight: `ssh olares-mesh "cd /home/olares/code/apex/apex-power-ops-platform && bash tools/ai/run-minimal-mcp-trio.sh status"`
- Host preflight result: `{"status":"not-running"}`
- Host strict verifier run: `ssh olares-mesh "cd /home/olares/code/apex/apex-power-ops-platform && set -a && . /home/olares/apex-secrets/olares/ai-live-dsn.env && set +a && bash tools/ai/run-minimal-mcp-trio.sh up 2026-05-13-olares-dev-residency-791 && bash tools/ai/run-minimal-mcp-trio.sh verify 2026-05-13-olares-dev-residency-791 strict-db-query && bash tools/ai/run-minimal-mcp-trio.sh down && bash tools/ai/run-minimal-mcp-trio.sh status"`
- Host strict verifier result: `started`, verifier `PASS`, `stopped`, then `{"status":"not-running"}`
- Host promotion helper run: `ssh olares-mesh "cd /home/olares/code/apex/apex-power-ops-platform && bash tools/ai/run-minimal-mcp-trio.sh up 2026-05-13-olares-dev-residency-791 && /usr/bin/python3 tools/ai/capture_apex_jobs_promotion.py --packet-id 2026-05-13-olares-dev-residency-791 --output tests/canary/mcp-contract/actual/apex-jobs-promotion-2026-05-13-olares-dev-residency-791.json && bash tools/ai/run-minimal-mcp-trio.sh down && bash tools/ai/run-minimal-mcp-trio.sh status"`
- Host promotion helper result: `started`, helper `PASS`, `stopped`, then `{"status":"not-running"}`
- Host promotion detail: successful `env=host` run id `1778685975474-kwumiag5`
- Host promotion detail: promoted at `2026-05-13T15:26:15.479Z`

## Repo-Visible Evidence
- `tools/ai/capture_apex_jobs_promotion.py`
- `tests/test_capture_apex_jobs_promotion_truthfulness.py`
- `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-13-olares-dev-residency-791.json`
- `tests/canary/mcp-contract/actual/apex-jobs-promotion-2026-05-13-olares-dev-residency-791.json`
- `docs/operations/APEX-JOBS-TRUST-AND-PROMOTION-CONTRACT-2026-05-08.md`
- `PROJECT_STATUS.md`
- `ops/agents/handoffs/2026-05-13-olares-dev-residency-791-active-ai-host-strict-profile-promotion-proof-handoff.md`

## Outcome
Packet `2026-05-13-olares-dev-residency-791` closes the two bounded follow-ons that remained after Packet 790.

The positive promotion gate is now covered by a reusable repo-owned helper with focused regression coverage, and the authoritative host now has a same-packet proof that strict-profile verifier evidence can coexist with a real successful `env=host` run and successful `promote_packet` result.

The next bounded follow-on, if any, is another similarly narrow provenance, rehearsal, or evidence-hardening slice, not wider controller or queue admission.

## Boundaries Preserved
- No new MCP service was admitted.
- No `ai_tasks` ownership was admitted.
- No auth, ingress, or runtime scope widened.
- The host was returned to truthful `not-running` rest state after both Packet 791 runtime chains.