# TCC Relay Phase 1 Public Control-Plane Readiness Remediation Handoff

Date: 2026-04-30
Status: Resolved in hosted environment on 2026-05-01
Parent phase: `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-1-HOSTED-PROOF-AND-PROMOTION-PACKET-2026-04-30.md`
Parent preflight: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-1-hosted-proof-and-promotion-preflight-handoff.md`

---

## Objective

Repair the public control-plane readiness blocker that was preventing relay hosted proof from closing green.

---

## Verified facts

The following public-host command was executed:

1. `c:/APEX Platform/.venv/Scripts/python.exe apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com --skip-authenticated-checks --require-apparatus-study-route`

Observed facts from that run:

1. `GET /health` returned `200`
2. OAuth discovery returned `200`
3. `GET /mcp` returned `200`
4. OpenAPI returned `200`
5. the governed apparatus route returned handler-owned `503`, not framework `404`
6. readiness returned `status: not_ready`
7. readiness exposed database authentication failure against `aws-0-us-west-2.pooler.supabase.com`

A hosted rerun on 2026-05-01 confirmed the same deployed failure shape:

1. readiness still failed on password authentication for user `postgres`,
2. the failing host remained `aws-0-us-west-2.pooler.supabase.com` on port `5432`,
3. discovery, MCP, OpenAPI, and the governed apparatus route still proved the app surface itself was up.

Hosted validation later on 2026-05-01 confirmed the fix:

1. the live Render pod `mhr8c` served a `DATABASE_URL` exactly matching the governed session-pooler credential,
2. `psycopg2.connect(os.environ['DATABASE_URL'])` succeeded from inside the Render shell,
3. rerunning `smoke_deployed_control_plane.py` against `https://control.apexpowerops.com` returned `READY_STATUS 200` with payload `status: ready` and `database: connected`,
4. the overall smoke result became `RESULT PASS`.

---

## Root cause

This was a deployed `DATABASE_URL` secret persistence problem in Render, not an app-code failure.

Verified path:

1. the deployed runtime already had the correct host, username, port, and database path,
2. the first differing character against the governed URL was at index `43`, which is the start of the password segment,
3. local validation against the governed session-pooler credential succeeded,
4. earlier Render edits targeted a hidden secret field and did not replace the runtime password,
5. saving the revealed secret value and forcing a fresh environment-update deploy propagated the correct password.

---

## Resolution

The hosted fix was applied on the Render service `apex-platform-control-plane-api` by rewriting the revealed `DATABASE_URL` secret to the governed session-pooler credential and allowing the resulting environment-update deploy to complete.

Related hosted variables still worth verifying as normal operational hygiene:

1. `DATABASE_URL`
2. `SUPABASE_URL`
3. `SUPABASE_ANON_KEY`
4. `SUPABASE_SERVICE_ROLE_KEY`
5. `SUPABASE_JWKS_URL`

The resolved `DATABASE_URL` shape was:

1. `postgresql://postgres.fxoyniqnrlkxfligbxmg:[password]@aws-0-us-west-2.pooler.supabase.com:5432/postgres`

---

## Required rerun after remediation

The required hosted rerun completed:

1. `c:/APEX Platform/.venv/Scripts/python.exe apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com --skip-authenticated-checks --require-apparatus-study-route`

Observed success criteria:

1. readiness reports database connected,
2. overall result is no longer failing on readiness,
3. the route remains handler-owned and non-framework-404.