# Olares Dev Residency 023 Post-022 Operations Visibility Live-Data Boundary Decision Handoff

Date: 2026-05-05
Status: Complete
Packet: `ops/agents/packets/draft/2026-05-05-olares-dev-residency-023-post-022-operations-visibility-live-data-boundary-decision.json`
Scope: bounded next-step decision after Packet 022 based on the direct control path for the current live-data failures

## Verdict

Packet 023 opens a bounded public-host API-origin remediation planning slice.

## Evidence

1. `apps/operations-web/public/pm-review/drivers.js`, `schedule.js`, `tracer.js`, and `variance.js` hardcode `http://localhost:8000/api/v1/schedule`.
2. `apps/operations-web/public/pm-review/approval-surface.html` hardcodes `http://localhost:8000/api/v1/mutations` and `http://localhost:8000/api/v1/reads`.
3. `apps/operations-web/public/lead-ops/index.html` hardcodes the same localhost reads and mutations bases.
4. `apps/operations-web/public/integration-dashboard/index.html` already uses an origin-aware local-vs-public branch, which is the nearest local reference for a bounded follow-on.
5. Packet 021 already proved render-level shell viability, so more browser comparison would not resolve the live-data boundary.

## Next Candidate

`Olares Dev Residency 024 - Bounded Public-Host API Origin Remediation Planning`