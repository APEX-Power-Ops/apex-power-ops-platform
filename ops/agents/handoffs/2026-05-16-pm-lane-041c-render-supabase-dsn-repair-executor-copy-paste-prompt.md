# PM Lane 041C - Render Supabase DSN Repair Executor Prompt

You are Desktop Codex acting as the authenticated hosted executor for PM Lane 041C.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Minimum source floor: `59ab1fd6e2ad247f2ee8ebf30a6720d88e296760`
- Packet: `ops/agents/packets/draft/2026-05-16-pm-lane-041c-render-supabase-dsn-repair.json`
- Prior closeouts:
  - `ops/agents/handoffs/2026-05-15-pm-lane-041a-vercel-operations-web-promotion-closeout-handoff.md`
  - `ops/agents/handoffs/2026-05-15-pm-lane-041b-render-mutation-seam-redeploy-classification-closeout-handoff.md`

Start with:

```powershell
cd "C:/APEX Platform/apex-power-ops-platform"
git pull --ff-only
git status --short --branch
git rev-parse HEAD
```

## Objective

Repair the existing Render mutation-seam hosted database connection so DB-backed approval/schedule reads stop returning `500`, while preserving the already-green PM intake hosted reads.

Render access is no longer the blocker. The remaining blocker is classified as a Supabase pooler DSN/authentication issue:

- service: `apex-platform-mutation-seam`
- root directory: `apps/mutation-seam`
- PM intake reads: all four currently return `200`
- failing reads: approval queue and schedule reads return `500`
- log classification: Supabase pooler `ECIRCUITBREAKER` from too many authentication failures

## Allowed

1. Confirm the correct `SEAM_DATABASE_URL` from an authorized secret source.
2. Compare the Render `SEAM_DATABASE_URL` to the authorized value using secret-safe evidence only.
3. Update the existing Render `SEAM_DATABASE_URL` if stale or wrong.
4. Wait for Supabase pooler auth circuit breaker cool-down if needed.
5. Restart or redeploy the existing Render service.
6. Rerun the validation commands below.
7. Create one closeout file:
   `ops/agents/handoffs/2026-05-16-pm-lane-041c-render-supabase-dsn-repair-closeout-handoff.md`

## Not Allowed

- Do not print, paste, commit, or quote the DSN or any secret value.
- Do not rotate the Supabase password unless a later explicit stakeholder instruction admits rotation.
- Do not run SQL writes.
- Do not create or run schema migrations.
- Do not replay fixtures.
- Do not create a new Render service.
- Do not change DNS, auth, ingress, or service topology.
- Do not admit approval persistence or import mutation.
- Do not create project, workpackage, task, issue, assignment, schedule, status, durable field record, work order, production tracking, or autonomous AI business-state mutation.
- If the correct DSN cannot be confirmed, stop and close out with a blocker instead of guessing.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform` after DSN confirmation/update and service restart/redeploy:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Also inspect Render logs after restart/redeploy and classify whether the Supabase pooler `ECIRCUITBREAKER` is gone, cooling down, or still present.

## Closeout Requirements

The closeout must include:

1. source commit tested,
2. existing Render service name,
3. secret-safe method used to confirm the DSN,
4. whether the Render env var was updated, without exposing the value,
5. restart/redeploy evidence,
6. exact validation command outputs,
7. Render log classification,
8. final verdict: `PASS`, `PARTIAL_PASS_COOLDOWN_PENDING`, or `BLOCKED_DSN_SOURCE_UNCONFIRMED`,
9. guardrail confirmation.

Commit and push only the closeout file if a closeout is created. Then fast-forward Olares and confirm `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`.
