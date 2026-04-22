# Parent-Root Control-Plane Support Publication Handoff
## Date: 2026-04-22
## Updated by: GitHub Copilot (GPT-5.4)
## Scope: Active next-step packet for bounded `apps/control-plane-api` support-surface introduction under `C:/APEX Platform/apex-power-ops-platform`

## 1. Summary

The bootstrap, Class A scaffold, package source, operations-web runtime, mutation-seam runtime, and control-plane runtime-core tranches are already published on parent-root `clean-main`.

The next natural publication step should still avoid broad subtree cutover. After the control-plane core landed, the remaining untracked residue in `apps/control-plane-api` split into a 58-file support packet and a 66-file residual test backlog. The smaller follow-on is the support packet:

1. `_invariant_probe_019g.py`
2. `api/`
3. `DEPLOYMENT_VALIDATION.md`
4. `migrations/`
5. `PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md`
6. `scripts/` (remaining support scripts)
7. `supabase/`
8. `utils/`

This packet introduces the remaining control-plane operational and migration surfaces without widening into the still-separate broader test backlog.

## 2. Why This Packet Is Next

Measured from the parent git root at `C:/APEX Platform` on 2026-04-22 after the control-plane core publication:

1. remaining untracked files under `apps/control-plane-api` total 124
2. the top-level distribution is:
   - `tests`: 66
   - `migrations`: 23
   - `scripts`: 20
   - `supabase`: 10
   - `_invariant_probe_019g.py`: 1
   - `api`: 1
   - `DEPLOYMENT_VALIDATION.md`: 1
   - `PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md`: 1
   - `utils`: 1
3. the non-test support residue totals 58 files, which is smaller and more coherent than immediately widening into the residual 66-file test backlog
4. this keeps schema, operational, and support surfaces together while preserving a separate later review surface for the remaining test bulk

## 3. Packet Intent

Use this packet to introduce the remaining support surfaces for the control-plane lane after the runtime core is already tracked:

1. migration SQL and helper scripts
2. Supabase migration lane artifacts
3. operational helper scripts and validation docs
4. lane-local support modules not needed for the first runtime-core publication

Do not treat this packet as authorization to publish the remaining control-plane test backlog in the same review unit.

## 4. Exact Packet Contents

From the parent git root at `C:/APEX Platform`, the bounded packet paths are:

1. `apex-power-ops-platform/apps/control-plane-api/_invariant_probe_019g.py`
2. `apex-power-ops-platform/apps/control-plane-api/api`
3. `apex-power-ops-platform/apps/control-plane-api/DEPLOYMENT_VALIDATION.md`
4. `apex-power-ops-platform/apps/control-plane-api/migrations`
5. `apex-power-ops-platform/apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md`
6. `apex-power-ops-platform/apps/control-plane-api/scripts`
7. `apex-power-ops-platform/apps/control-plane-api/supabase`
8. `apex-power-ops-platform/apps/control-plane-api/utils`

Explicit exclusions:

1. the remaining untracked `tests/` backlog
2. any already-published runtime-core paths under `config.py`, `main.py`, `demo/`, `models/`, `services/`, and the focused runtime-core test slice

## 5. Why This Packet Is Bounded Correctly

This packet is intentionally narrow:

1. it captures the remaining non-test support surfaces for the control-plane lane
2. it keeps the 66-file residual test backlog separate for a later review unit
3. it avoids reopening already-published runtime-core files
4. it avoids widening into unrelated repo surfaces outside `apps/control-plane-api`

## 6. Operator Execution Path

Preferred task path from `C:/APEX Platform/apex-power-ops-platform`:

1. run `Preview parent-root control-plane support packet`
2. run `Stage parent-root control-plane support packet` only when the preview is correct
3. run `Parent-root control-plane support packet staged diff`

Direct parent-root path if tasks are not used:

```powershell
Set-Location 'C:/APEX Platform'
git add -n -- apex-power-ops-platform/apps/control-plane-api/_invariant_probe_019g.py apex-power-ops-platform/apps/control-plane-api/api apex-power-ops-platform/apps/control-plane-api/DEPLOYMENT_VALIDATION.md apex-power-ops-platform/apps/control-plane-api/migrations apex-power-ops-platform/apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md apex-power-ops-platform/apps/control-plane-api/scripts apex-power-ops-platform/apps/control-plane-api/supabase apex-power-ops-platform/apps/control-plane-api/utils
git add -- apex-power-ops-platform/apps/control-plane-api/_invariant_probe_019g.py apex-power-ops-platform/apps/control-plane-api/api apex-power-ops-platform/apps/control-plane-api/DEPLOYMENT_VALIDATION.md apex-power-ops-platform/apps/control-plane-api/migrations apex-power-ops-platform/apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md apex-power-ops-platform/apps/control-plane-api/scripts apex-power-ops-platform/apps/control-plane-api/supabase apex-power-ops-platform/apps/control-plane-api/utils
git diff --cached -- apex-power-ops-platform/apps/control-plane-api/_invariant_probe_019g.py apex-power-ops-platform/apps/control-plane-api/api apex-power-ops-platform/apps/control-plane-api/DEPLOYMENT_VALIDATION.md apex-power-ops-platform/apps/control-plane-api/migrations apex-power-ops-platform/apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md apex-power-ops-platform/apps/control-plane-api/scripts apex-power-ops-platform/apps/control-plane-api/supabase apex-power-ops-platform/apps/control-plane-api/utils
```

## 7. Validation Expectation

Before commit, the smallest relevant checks are:

1. `git add -n` preview of the exact packet paths
2. staged diff review for those support paths only
3. narrow validation commands only where they map directly to the staged support content

This packet is more support-heavy than the runtime-core packet, so diff discipline matters more than broad executable revalidation.

## 8. Do Not Do

1. do not replace this bounded packet with `git add -- apex-power-ops-platform/apps/control-plane-api`
2. do not include the remaining untracked `tests/` backlog in this packet
3. do not reopen already-published control-plane runtime-core files
4. do not mix this packet with unrelated repo-wide cleanup or historical `ops/` bulk

## 9. Follow-On After This Packet

If this packet lands cleanly, the next logical tranches are:

1. remaining control-plane test backlog packet
2. selective `docs/` and `ops/` authority packets needed to operate the fully introduced control-plane lane

Those follow-ons remain separate from this control-plane support packet.