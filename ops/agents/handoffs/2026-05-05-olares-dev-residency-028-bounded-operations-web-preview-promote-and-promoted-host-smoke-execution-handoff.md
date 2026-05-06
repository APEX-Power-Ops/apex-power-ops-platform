# Olares Dev Residency 028 Bounded Operations-Web Preview Promote And Promoted-Host Smoke Execution Handoff

Date: 2026-05-05
Status: Complete
Packet: `ops/agents/packets/draft/2026-05-05-olares-dev-residency-028-bounded-operations-web-preview-promote-and-promoted-host-smoke-execution.json`
Scope: bounded hosted-runtime execution to promote the newest ready operations-web preview to production and rerun the governed promoted-host smoke

## Execution Result

1. `npx -y vercel promote https://apex-operations-t362sc9pa-jasonlswenson-sys-projects.vercel.app --scope jasonlswenson-sys-projects --yes` completed.
2. Follow-up inspection confirmed production alias `https://operations.apexpowerops.com` propagated to deployment `dpl_3rR9YukiwRwnMcdbKN87Hh87rpVr`.
3. Hosted route smoke still passed with `SMOKE_SUMMARY failed=0 passed=8`.
4. Public-host PM drivers now request `https://operations.apexpowerops.com/api/v1/schedule/drivers?...` instead of localhost.
5. Public-host approval surface now requests `https://operations.apexpowerops.com/api/v1/reads/*` instead of localhost, but those same-origin requests still return `404`.
6. The broader promoted-host browser smoke still reports two failures outside the Packet 025 static-surface slice:
	- `tests/browser-shell.apparatus.smoke.spec.ts`
	- `tests/browser-shell.relay.smoke.spec.ts`

## Next Candidate

`Olares Dev Residency 029 - Post-028 Public Mutation-Seam Deployment Boundary Decision`