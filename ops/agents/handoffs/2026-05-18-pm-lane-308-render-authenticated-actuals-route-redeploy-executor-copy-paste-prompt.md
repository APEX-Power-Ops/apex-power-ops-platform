# PM Lane 308 - Render-Authenticated Actuals Route Redeploy Executor Prompt

You are the authenticated Render executor for PM Lane 308.

Use your authenticated Render surface to inspect and redeploy only the existing mutation-seam service, then rerun bounded hosted smoke for the Temp Power actuals-capture review routes.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Packet: `ops/agents/packets/draft/2026-05-18-pm-lane-308-project-miner-temp-power-actuals-capture-review-render-authenticated-redeploy-gate.json`
- Handoff: `ops/agents/handoffs/2026-05-18-pm-lane-308-project-miner-temp-power-actuals-capture-review-render-authenticated-redeploy-gate-handoff.md`
- Target service: `apex-platform-mutation-seam`
- Target hosted base URL: `https://mutation-seam.apexpowerops.com`
- Current blocker: `HOSTED_MUTATION_SEAM_REDEPLOY_REQUIRED_BEFORE_ANY_ACTUALS_ROUTE_HOSTED_PROOF`

Start with:

```powershell
cd "C:/APEX Platform/apex-power-ops-platform"
git pull --ff-only
git status --short --branch
git rev-parse HEAD
git ls-remote origin clean-main
```

At packet authoring, hosted smoke showed both live seam hosts still omitted:

1. `POST /api/v1/mutations/temp-power-actuals-capture-reviews`
2. `GET /api/v1/reads/temp-power-actuals-capture-review-status`

Both hosts returned framework `404 Not Found` for the actuals readback route.

## Objective

Redeploy the existing Render mutation-seam service from current `clean-main` and rerun the bounded hosted smoke until one of these outcomes is proven truthfully:

Preferred outcome:

`HOSTED_ACTUALS_ROUTE_REDEPLOY_PASS_READINESS_GREEN`

Fallback truthful block:

`BLOCKED_HOSTED_ACTUALS_ROUTE_STILL_ABSENT_AFTER_REDEPLOY`

Auth failure outcome:

`BLOCKED_RENDER_AUTH_UNAVAILABLE_ACTUALS_ROUTE_REDEPLOY`

## Allowed Actions

1. inspect the existing Render service `apex-platform-mutation-seam`
2. confirm repository `jasonlswenson-sys/apex-power-ops`, branch `clean-main`, working directory `apps/mutation-seam`
3. confirm deployment metadata matches `apps/mutation-seam/render.yaml`
4. confirm non-secret env posture only, without printing secret values
5. trigger a redeploy of the existing service from current `clean-main`
6. rerun bounded hosted smoke for the Temp Power actuals routes
7. inspect logs only far enough to classify any remaining blocker without revealing secrets
8. write one executor closeout file with exact evidence

## Not Allowed

- do not send `POST /api/v1/mutations/temp-power-actuals-capture-reviews`
- do not send `POST /api/v1/mutations/temp-power-customer-preview-reviews`
- do not create a new Render service
- do not change DNS, auth, ingress, or public host topology
- do not run SQL writes or schema migrations
- do not rotate or print secrets
- do not widen customer delivery, finance, or source-writeback authority

## Required Hosted Validation

Run these after redeploy:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-temp-power-actuals-review
```

If the custom domain still looks stale, rerun the same bounded probe against the Render hostname only for disambiguation:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://apex-platform-mutation-seam.onrender.com --include-temp-power-actuals-review
```

Read-only route checks after redeploy should confirm all of the following:

1. OpenAPI contains `/api/v1/mutations/temp-power-actuals-capture-reviews`
2. OpenAPI contains `/api/v1/reads/temp-power-actuals-capture-review-status`
3. `GET /api/v1/reads/temp-power-actuals-capture-review-status` no longer returns framework `404 Not Found`
4. the readback preserves `customer_delivery_authority=not_admitted`
5. the readback preserves `finance_authority=not_admitted`
6. the readback preserves `source_writeback_authority=not_admitted`
7. the readback preserves `durable_delivery_event=false`

## Closeout File

Create exactly one closeout:

`ops/agents/handoffs/2026-05-18-pm-lane-308-render-authenticated-actuals-route-redeploy-executor-closeout.md`

Use this template:

`ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md`

Include:

1. source commit tested
2. existing Render service name
3. authenticated surface used, without exposing secrets
4. deployed repo/branch/working-directory verdict
5. deploy metadata verdict against `apps/mutation-seam/render.yaml`
6. redeploy evidence
7. exact hosted smoke command outputs
8. whether custom domain and Render hostname matched or diverged after redeploy
9. final outcome label
10. guardrail confirmation

Final outcome must be exactly one of:

1. `HOSTED_ACTUALS_ROUTE_REDEPLOY_PASS_READINESS_GREEN`
2. `BLOCKED_RENDER_AUTH_UNAVAILABLE_ACTUALS_ROUTE_REDEPLOY`
3. `BLOCKED_HOSTED_ACTUALS_ROUTE_STILL_ABSENT_AFTER_REDEPLOY`
4. `BLOCKED_RENDER_DEPLOY_FAILED_ACTUALS_ROUTE_REDEPLOY`
5. `BLOCKED_RENDER_REQUIRES_NON_ADMITTED_INFRA_CHANGE_ACTUALS_ROUTE_REDEPLOY`

If final outcome is `BLOCKED_HOSTED_ACTUALS_ROUTE_STILL_ABSENT_AFTER_REDEPLOY` and the hosted evidence proves the service is already on current `clean-main`, route the repo-local follow-on to:

`ops/agents/handoffs/2026-05-18-pm-lane-313-actuals-route-post-redeploy-code-build-defect-investigation-prompt.md`

## Stop Conditions

1. stop if Render auth is unavailable
2. stop if repair would require a new service, DNS change, auth change, ingress widening, secret rotation, SQL write, or schema migration
3. stop if hosted proof would require a live mutation POST
4. stop if the service is already on current `clean-main` and the routes are still absent, because that becomes PM Lane 313 rather than more redeploy repetition