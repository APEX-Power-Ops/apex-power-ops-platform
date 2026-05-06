# Olares Dev Residency 024 Bounded Public-Host API Origin Remediation Planning Handoff

Date: 2026-05-05
Status: Complete
Packet: `ops/agents/packets/draft/2026-05-05-olares-dev-residency-024-bounded-public-host-api-origin-remediation-planning.json`
Scope: bounded planning for source-local API-origin remediation on the public static Operations Visibility surfaces

## Verdict

Packet 024 selects a bounded source-local API-origin remediation execution slice.

## Evidence

1. The public PM review and lead surfaces hardcode `http://localhost:8000` directly in their page assets.
2. `apps/operations-web/public/integration-dashboard/index.html` already provides a nearby local-vs-public origin-aware base pattern.
3. Direct public-host probes to `https://operations.apexpowerops.com/api/v1/schedule/projects` and `https://operations.apexpowerops.com/api/v1/reads/approval-queue` returned `404`.
4. Therefore the next implementation slice can truthfully remove the wrong-origin dependency, but cannot truthfully promise live-data success.

## Next Candidate

`Olares Dev Residency 025 - Bounded Public Static Surface API Origin Remediation Execution`