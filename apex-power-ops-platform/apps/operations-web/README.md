# Operations Web

`apps/operations-web` is the first governed browser app shell for the APEX platform.

Current scope:

1. provide a real frontend package and source tree
2. establish the first browser-side env contract
3. consume the first live study-resource read through the governed control-plane API rather than direct browser database access
4. host the preserved cross-surface browser validation dashboard under `/integration-dashboard/index.html`
5. host the re-homed lead operations prototype under `/lead-ops/index.html`
6. host the first re-homed PM read-only review slice under `/pm-review/index.html`
7. host the re-homed PM approval prototype shell under `/pm-review/approval-surface.html`
8. host the re-homed PM schedule slice under `/pm-review/schedule.html`
9. host the re-homed PM upstream tracer slice under `/pm-review/tracer.html`
10. host the re-homed PM variance slice under `/pm-review/variance.html`

Current non-goals:

1. no direct import of `C:/APEX Platform/Supabase/lib/supabase.ts` yet
2. no service-role or admin env values
3. no direct mutation wiring to backend services in the current packet lane
4. no direct browser-side Supabase reads for the legacy RESA query surface

Recommended local commands:

```bash
pnpm --dir C:/APEX Platform/apex-power-ops-platform install
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web dev
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web smoke:hosted -- --base-url https://your-host.example
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web smoke:browser
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web smoke:promoted-host -- --operations-web-base-url https://your-operations-web-host.example --control-plane-base-url https://your-control-plane-host.example --skip-authenticated-checks
```

Workspace task shortcuts:

1. use the root workspace task `Operations web browser smoke` for the local Playwright proof
2. use the root workspace task `Operations web promoted-host smoke` when `OPERATIONS_WEB_BASE_URL` is set for a deployed browser host; that task already defaults the control-plane host to `https://control.apexpowerops.com`