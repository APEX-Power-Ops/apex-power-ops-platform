# Parent-Root Operations-Web Runtime Publication Handoff
## Date: 2026-04-22
## Updated by: GitHub Copilot (GPT-5.4)
## Scope: Active next-step packet for bounded recursive `apps/operations-web` runtime introduction under `C:/APEX Platform/apex-power-ops-platform`

## 1. Summary

The bootstrap, Class A scaffold, and package source tranches are already published on parent-root `clean-main`.

The next natural publication step should still avoid broad subtree cutover. The smallest remaining app-lane follow-on is a bounded recursive runtime packet for `apps/operations-web`:

1. `app/`
2. `lib/`
3. `next-env.d.ts`
4. `public/`
5. `scripts/`
6. `tests/`
7. `DEPLOYMENT_VALIDATION.md`

This packet introduces the active operations browser runtime, its static PM review assets, its smoke scripts, and its lane-local validation note without widening into generated browser residue or other app lanes.

## 2. Why This Packet Is Next

Measured from the parent git root at `C:/APEX Platform` on 2026-04-22:

1. `apps/operations-web` has 27 untracked files total and already has tracked manifests
2. one of those files is generated residue under `test-results/`, which should stay out of publication
3. excluding `test-results/`, the runtime packet is 26 files total
4. this is still materially smaller than the larger remaining app-lane backlogs:
   - `apps/mutation-seam`: 65 untracked files
   - `apps/control-plane-api`: 186 untracked files
5. the lane already carries explicit smoke and build scripts in its tracked manifest, so it can be validated as a coherent app-lane packet

## 3. Packet Intent

Use this packet to introduce the recursive runtime surface for the smallest active browser lane that already has its manifests and top-level config published:

1. Next app shell files under `app/`
2. lane-local helpers under `lib/`
3. public review assets under `public/`
4. smoke scripts and browser tests
5. the local deployment-validation note for the lane

Do not treat this packet as authorization to publish generated `.next/`, `node_modules/`, or `test-results/` residue.

## 4. Exact Packet Contents

From the parent git root at `C:/APEX Platform`, the bounded packet paths are:

1. `apex-power-ops-platform/apps/operations-web/DEPLOYMENT_VALIDATION.md`
2. `apex-power-ops-platform/apps/operations-web/app`
3. `apex-power-ops-platform/apps/operations-web/lib`
4. `apex-power-ops-platform/apps/operations-web/next-env.d.ts`
5. `apex-power-ops-platform/apps/operations-web/public`
6. `apex-power-ops-platform/apps/operations-web/scripts`
7. `apex-power-ops-platform/apps/operations-web/tests`

Explicit exclusions:

1. `apex-power-ops-platform/apps/operations-web/.next`
2. `apex-power-ops-platform/apps/operations-web/node_modules`
3. `apex-power-ops-platform/apps/operations-web/test-results`
4. ignored `.env.example` handling remains governed by the lane `.gitignore`

## 5. Why This Packet Is Bounded Correctly

This packet is intentionally narrow:

1. it introduces only the live runtime-bearing and validation-bearing operations-web surfaces
2. it excludes generated browser residue and local cache output
3. it does not mix in `apps/mutation-seam` or `apps/control-plane-api`
4. it leaves broader `ops/` historical bulk out of the review surface
5. it creates a clean first recursive app-lane publication after the package tranche

## 6. Operator Execution Path

Preferred task path from `C:/APEX Platform/apex-power-ops-platform`:

1. run `Preview parent-root operations-web runtime packet`
2. run `Stage parent-root operations-web runtime packet` only when the preview is correct
3. run `Parent-root operations-web runtime packet staged diff`

Direct parent-root path if tasks are not used:

```powershell
Set-Location 'C:/APEX Platform'
git add -n -- apex-power-ops-platform/apps/operations-web/DEPLOYMENT_VALIDATION.md apex-power-ops-platform/apps/operations-web/app apex-power-ops-platform/apps/operations-web/lib apex-power-ops-platform/apps/operations-web/next-env.d.ts apex-power-ops-platform/apps/operations-web/public apex-power-ops-platform/apps/operations-web/scripts apex-power-ops-platform/apps/operations-web/tests
git add -- apex-power-ops-platform/apps/operations-web/DEPLOYMENT_VALIDATION.md apex-power-ops-platform/apps/operations-web/app apex-power-ops-platform/apps/operations-web/lib apex-power-ops-platform/apps/operations-web/next-env.d.ts apex-power-ops-platform/apps/operations-web/public apex-power-ops-platform/apps/operations-web/scripts apex-power-ops-platform/apps/operations-web/tests
git diff --cached -- apex-power-ops-platform/apps/operations-web/DEPLOYMENT_VALIDATION.md apex-power-ops-platform/apps/operations-web/app apex-power-ops-platform/apps/operations-web/lib apex-power-ops-platform/apps/operations-web/next-env.d.ts apex-power-ops-platform/apps/operations-web/public apex-power-ops-platform/apps/operations-web/scripts apex-power-ops-platform/apps/operations-web/tests
```

## 7. Validation Expectation

Before commit, the smallest relevant checks are:

1. `git add -n` preview of the exact packet paths
2. staged diff review for those operations-web paths only
3. lane-local executable checks such as `typecheck` and the focused browser smoke path if the environment is available

This packet is a recursive app-lane runtime tranche, so executable validation matters more than it did for the scaffold-only packet.

## 8. Do Not Do

1. do not replace this bounded packet with `git add -- apex-power-ops-platform/apps/operations-web`
2. do not include `.next`, `node_modules`, or `test-results`
3. do not widen the packet into `apps/mutation-seam` or `apps/control-plane-api`
4. do not mix this packet with historical `ops/agents/handoffs/` bulk

## 9. Follow-On After This Packet

If this packet lands cleanly, the next logical tranches are:

1. `apps/mutation-seam` recursive runtime packet
2. `apps/control-plane-api` recursive runtime packet
3. selective `docs/` and `ops/` authority packets needed to operate the expanded app lanes

Those follow-ons remain separate from this operations-web runtime packet.