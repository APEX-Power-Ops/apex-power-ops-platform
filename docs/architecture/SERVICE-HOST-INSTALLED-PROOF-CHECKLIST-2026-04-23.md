# Service Host Installed Proof Checklist

Date: 2026-04-23
Status: Active rerun surface
Scope: bounded rerun path for installed-proof evidence for `forms-engine` and `p6-ingest`

## Purpose

Use this checklist when installed-proof evidence for `forms-engine` or
`p6-ingest` needs to be refreshed after route, chart, runtime, or ingress drift.

This checklist does not authorize onboarding a new Helm-managed Olares app.

## Current Evidence Floor

1. `infra/olares/forms-engine/OlaresManifest.yaml`
2. `infra/olares/forms-engine/templates/configmap.yaml`
3. `infra/olares/forms-engine/templates/service.yaml`
4. `infra/olares/forms-engine/templates/deployment.yaml`
5. `infra/olares/p6-ingest/OlaresManifest.yaml`
6. `infra/olares/p6-ingest/templates/configmap.yaml`
7. `infra/olares/p6-ingest/templates/service.yaml`
8. `infra/olares/p6-ingest/templates/deployment.yaml`
9. `packages/forms-engine/src/apex_forms_engine/runtime.py`
10. `packages/p6-ingest/src/apex_p6_ingest/runtime.py`
11. `services/mcp/apex-forms/build/runtime-client.js`
12. `services/mcp/apex-p6/build/runtime-client.js`
13. `tests/canary/forms-engine-staging-manifest/actual/OlaresManifest.yaml`
14. `tests/canary/forms-engine-staging-render/actual/rendered-chart.yaml`
15. `tests/canary/p6-ingest-staging-manifest/actual/OlaresManifest.yaml`
16. `tests/canary/p6-ingest-staging-render/actual/rendered-chart.yaml`
17. `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md`

## Rerun Steps

1. verify that the forms and p6 manifest files under `infra/olares/` still describe the expected host names, OIDC client ids, and middleware contracts
2. verify that the chart template files under `infra/olares/forms-engine/templates/` and `infra/olares/p6-ingest/templates/` remain present
3. run the bounded canary wrapper from the workstation checklist to refresh runtime and staging evidence
4. confirm that the refreshed `tests/canary/forms-engine-dev-runtime/actual/health.json` still reports `service=forms-engine`
5. confirm that the refreshed `tests/canary/p6-ingest-dev-runtime/actual/health.json` still reports `service=p6-ingest`
6. confirm that the refreshed `tests/canary/p6-ingest-dev-runtime/actual/summary.json` still exposes the admitted Stack Data Center baseline summary
7. confirm that the refreshed staging manifest and rendered-chart outputs match the current files under `infra/olares/`

## Exit Condition

Installed-proof rerun readiness remains valid when the runtime contracts,
manifest outputs, and rendered-chart outputs for `forms-engine` and
`p6-ingest` all refresh from the bounded workstation shell without opening new
service scope.
