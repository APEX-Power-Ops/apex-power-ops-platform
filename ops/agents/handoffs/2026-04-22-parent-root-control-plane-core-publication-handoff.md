# Historical Parent-Root Control-Plane Core Publication Handoff
## Date: 2026-04-22
## Updated by: GitHub Copilot (GPT-5.4)
## Scope: Historical record for the published bounded `apps/control-plane-api` runtime-core introduction under `C:/APEX Platform/apex-power-ops-platform`

## 1. Summary

Historical note: this handoff records one bounded parent-root publication record from before the canonical repo boundary moved to `C:/APEX Platform/apex-power-ops-platform` on 2026-05-07. It remains packet-history provenance, not a live operator instruction surface for current repo operations.

Current routing:

1. use `PROJECT_STATUS.md` for the current residue-retirement lane and latest completed packets,
2. use `docs/architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the remaining post-cutover boundary closeout queue,
3. use this handoff only when historical provenance is needed for the earlier parent-root publication or checkpoint record preserved here.

The bootstrap, Class A scaffold, package source, operations-web runtime, and mutation-seam runtime tranches are already published on parent-root `clean-main`.

The next natural publication step after those tranches still avoided broad subtree cutover. The remaining active app lane was `apps/control-plane-api`, but its full backlog was larger than a single clean packet. The bounded follow-on was the control-plane runtime core that already had focused executable proof:

1. `config.py`
2. `main.py`
3. `demo/`
4. `docs/contracts/CHATGPT-REMOTE-CONTROL-PLANE-TOOL-SCHEMAS-2026-03-28.json`
5. `models/`
6. `services/`
7. `scripts/smoke_deployed_control_plane.py`
8. focused test slice under `tests/`

This packet introduced the live FastAPI runtime, MCP and route handlers, the demo HTML required by the consent-route surface, the public-host smoke helper, and the focused tests already used to validate the bounded runtime core.

Publication outcome:

1. committed on parent-root `clean-main` as `d8c498b`
2. pushed to `origin/clean-main` on 2026-04-22
3. closed as the published control-plane runtime-core follow-on to the mutation-seam tranche

## 2. Why This Packet Is Next

Measured from the parent git root at `C:/APEX Platform` on 2026-04-22:

1. the remaining untracked `apps/control-plane-api` backlog is still the largest active lane
2. a bounded runtime-core pathset stages cleanly at 62 files while avoiding the wider migration, script, supabase, and test backlog
3. this core slice is the portion already exercised by the focused validation command:
   - `tests/test_oauth_consent_route.py`
   - `tests/test_mcp_transport.py`
   - `tests/test_supabase_mcp_transport.py`
   - `tests/test_github_mcp_transport.py`
   - `tests/test_smoke_deployed_control_plane.py`
   - `tests/test_health.py`
4. that focused slice passed on 2026-04-22 once the local venv was aligned with already-declared dependencies in `requirements.txt`
5. publishing this runtime core first keeps the remaining control-plane backlog separable into later support packets

## 3. Packet Intent

This packet introduced the active control-plane runtime core and its focused validation surfaces:

1. FastAPI entrypoint and DB configuration
2. route, auth, MCP, NETA, ops, work, and control-plane services
3. ORM models required by the runtime
4. demo HTML files required by the public consent and demo routes
5. the deployed-surface smoke helper script
6. the focused tests that already validate this slice

Do not treat this historical packet as authorization to publish the full control-plane backlog in one step.

## 4. Exact Packet Contents

From the parent git root at `C:/APEX Platform`, the bounded packet paths are:

1. `apex-power-ops-platform/apps/control-plane-api/config.py`
2. `apex-power-ops-platform/apps/control-plane-api/main.py`
3. `apex-power-ops-platform/apps/control-plane-api/demo`
4. `apex-power-ops-platform/apps/control-plane-api/docs/contracts/CHATGPT-REMOTE-CONTROL-PLANE-TOOL-SCHEMAS-2026-03-28.json`
5. `apex-power-ops-platform/apps/control-plane-api/models`
6. `apex-power-ops-platform/apps/control-plane-api/services`
7. `apex-power-ops-platform/apps/control-plane-api/scripts/smoke_deployed_control_plane.py`
8. `apex-power-ops-platform/apps/control-plane-api/tests/__init__.py`
9. `apex-power-ops-platform/apps/control-plane-api/tests/test_control_plane.py`
10. `apex-power-ops-platform/apps/control-plane-api/tests/test_github_mcp_transport.py`
11. `apex-power-ops-platform/apps/control-plane-api/tests/test_health.py`
12. `apex-power-ops-platform/apps/control-plane-api/tests/test_mcp_transport.py`
13. `apex-power-ops-platform/apps/control-plane-api/tests/test_oauth_consent_route.py`
14. `apex-power-ops-platform/apps/control-plane-api/tests/test_smoke_deployed_control_plane.py`
15. `apex-power-ops-platform/apps/control-plane-api/tests/test_supabase_mcp_transport.py`

Explicit exclusions:

1. `apex-power-ops-platform/apps/control-plane-api/migrations`
2. `apex-power-ops-platform/apps/control-plane-api/supabase`
3. the wider `scripts/` backlog outside `smoke_deployed_control_plane.py`
4. the wider `tests/` backlog outside the focused runtime-core slice
5. `docs/` content outside the single contract JSON used by the focused helper test
6. `api/`, `utils/`, and other remaining support surfaces until a later bounded packet proves they need introduction

## 5. Why This Packet Is Bounded Correctly

This packet is intentionally narrow:

1. it captures the live runtime and the focused public/MCP test surfaces already validated together
2. it excludes the migration backlog, Supabase migration lane, and broader operator scripts
3. it keeps the remaining control-plane test bulk separate from the first runtime-core publication
4. it avoids reopening broader `ops/` historical bulk or non-control-plane paths

## 6. Historical Execution Path

Preferred task path from `C:/APEX Platform/apex-power-ops-platform` when this packet was executed:

1. run `Preview parent-root control-plane core packet`
2. run `Stage parent-root control-plane core packet` only when the preview is correct
3. run `Parent-root control-plane core packet staged diff`

Direct parent-root path if tasks are not used:

```powershell
Set-Location 'C:/APEX Platform'
git add -n -- apex-power-ops-platform/apps/control-plane-api/config.py apex-power-ops-platform/apps/control-plane-api/main.py apex-power-ops-platform/apps/control-plane-api/demo apex-power-ops-platform/apps/control-plane-api/docs/contracts/CHATGPT-REMOTE-CONTROL-PLANE-TOOL-SCHEMAS-2026-03-28.json apex-power-ops-platform/apps/control-plane-api/models apex-power-ops-platform/apps/control-plane-api/services apex-power-ops-platform/apps/control-plane-api/scripts/smoke_deployed_control_plane.py apex-power-ops-platform/apps/control-plane-api/tests/__init__.py apex-power-ops-platform/apps/control-plane-api/tests/test_control_plane.py apex-power-ops-platform/apps/control-plane-api/tests/test_github_mcp_transport.py apex-power-ops-platform/apps/control-plane-api/tests/test_health.py apex-power-ops-platform/apps/control-plane-api/tests/test_mcp_transport.py apex-power-ops-platform/apps/control-plane-api/tests/test_oauth_consent_route.py apex-power-ops-platform/apps/control-plane-api/tests/test_smoke_deployed_control_plane.py apex-power-ops-platform/apps/control-plane-api/tests/test_supabase_mcp_transport.py
git add -- apex-power-ops-platform/apps/control-plane-api/config.py apex-power-ops-platform/apps/control-plane-api/main.py apex-power-ops-platform/apps/control-plane-api/demo apex-power-ops-platform/apps/control-plane-api/docs/contracts/CHATGPT-REMOTE-CONTROL-PLANE-TOOL-SCHEMAS-2026-03-28.json apex-power-ops-platform/apps/control-plane-api/models apex-power-ops-platform/apps/control-plane-api/services apex-power-ops-platform/apps/control-plane-api/scripts/smoke_deployed_control_plane.py apex-power-ops-platform/apps/control-plane-api/tests/__init__.py apex-power-ops-platform/apps/control-plane-api/tests/test_control_plane.py apex-power-ops-platform/apps/control-plane-api/tests/test_github_mcp_transport.py apex-power-ops-platform/apps/control-plane-api/tests/test_health.py apex-power-ops-platform/apps/control-plane-api/tests/test_mcp_transport.py apex-power-ops-platform/apps/control-plane-api/tests/test_oauth_consent_route.py apex-power-ops-platform/apps/control-plane-api/tests/test_smoke_deployed_control_plane.py apex-power-ops-platform/apps/control-plane-api/tests/test_supabase_mcp_transport.py
git diff --cached -- apex-power-ops-platform/apps/control-plane-api/config.py apex-power-ops-platform/apps/control-plane-api/main.py apex-power-ops-platform/apps/control-plane-api/demo apex-power-ops-platform/apps/control-plane-api/docs/contracts/CHATGPT-REMOTE-CONTROL-PLANE-TOOL-SCHEMAS-2026-03-28.json apex-power-ops-platform/apps/control-plane-api/models apex-power-ops-platform/apps/control-plane-api/services apex-power-ops-platform/apps/control-plane-api/scripts/smoke_deployed_control_plane.py apex-power-ops-platform/apps/control-plane-api/tests/__init__.py apex-power-ops-platform/apps/control-plane-api/tests/test_control_plane.py apex-power-ops-platform/apps/control-plane-api/tests/test_github_mcp_transport.py apex-power-ops-platform/apps/control-plane-api/tests/test_health.py apex-power-ops-platform/apps/control-plane-api/tests/test_mcp_transport.py apex-power-ops-platform/apps/control-plane-api/tests/test_oauth_consent_route.py apex-power-ops-platform/apps/control-plane-api/tests/test_smoke_deployed_control_plane.py apex-power-ops-platform/apps/control-plane-api/tests/test_supabase_mcp_transport.py
```

## 7. Validation Expectation

Before commit, the smallest relevant checks are:

1. `git add -n` preview of the exact packet paths
2. staged diff review for those control-plane paths only
3. the focused pytest slice:

```powershell
Set-Location 'C:/APEX Platform/apex-power-ops-platform/apps/control-plane-api'
$env:DATABASE_URL='postgresql://postgres:postgres@localhost:5432/postgres'
& 'C:/APEX Platform/.venv/Scripts/python.exe' -m pytest tests/test_oauth_consent_route.py tests/test_mcp_transport.py tests/test_supabase_mcp_transport.py tests/test_github_mcp_transport.py tests/test_smoke_deployed_control_plane.py tests/test_health.py -q
```

This packet was suitable for executable validation because it already mapped cleanly to the focused control-plane runtime proof.

## 8. Do Not Do

1. do not replace this bounded packet with `git add -- apex-power-ops-platform/apps/control-plane-api`
2. do not widen the packet into `migrations`, `supabase`, or the wider `scripts` backlog
3. do not include the broader test backlog beyond the focused runtime-core slice
4. do not mix this packet with historical `ops/agents/handoffs/` bulk or other lanes

## 9. Follow-On After This Packet

If this packet lands cleanly, the next logical tranches are:

1. control-plane support packet for migrations, Supabase SQL, remaining operational scripts, and still-untracked lane-local support surfaces
2. remaining control-plane validation and browser/demo test packet
3. selective `docs/` and `ops/` authority packets needed to operate the fully introduced control-plane lane

Those follow-ons remain separate from this now-published control-plane runtime-core packet.