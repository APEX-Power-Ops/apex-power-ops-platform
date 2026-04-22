# Parent-Root Package Source Publication Handoff
## Date: 2026-04-22
## Updated by: GitHub Copilot (GPT-5.4)
## Scope: Active next-step packet for bounded recursive package-source introduction under `C:/APEX Platform/apex-power-ops-platform`

## 1. Summary

The bootstrap slice and the Class A scaffold tranche are already published on parent-root `clean-main`.

The next natural publication step should still avoid broad subtree cutover. The smallest code-bearing follow-on is a bounded recursive packet for the shared package lanes:

1. `packages/forms-engine/src`
2. `packages/forms-engine/tests`
3. `packages/calc-engine/src`
4. `packages/calc-engine/tests`

This packet introduces executable shared package logic and tests without pulling in the larger app-lane backlog under `apps/control-plane-api`, `apps/mutation-seam`, or `apps/operations-web`.

## 2. Why This Packet Is Next

Measured from the parent git root at `C:/APEX Platform` on 2026-04-22:

1. `packages/forms-engine` has 16 untracked files and already has tracked manifests
2. `packages/calc-engine` has 32 untracked files and already has tracked manifests
3. both lanes are materially smaller than the current app-lane backlogs:
   - `apps/control-plane-api`: 186 untracked files
   - `apps/mutation-seam`: 65 untracked files
   - `apps/operations-web`: 27 untracked files, but with browser/public/test residue that should remain a separate packet
4. the calc-engine lane already has a focused offline test path, which makes this tranche cheaper to validate than the larger app-lane follow-ons

## 3. Packet Intent

Use this packet to introduce the recursive source and test trees for the two shared package lanes that already have published manifests:

1. package implementation modules
2. package test surfaces
3. package fixture assets required by those tests

Do not treat this packet as authorization to publish deferred `packages/api-contracts` or to widen into app lanes.

## 4. Exact Packet Contents

From the parent git root at `C:/APEX Platform`, the bounded packet paths are:

1. `apex-power-ops-platform/packages/forms-engine/src`
2. `apex-power-ops-platform/packages/forms-engine/tests`
3. `apex-power-ops-platform/packages/calc-engine/src`
4. `apex-power-ops-platform/packages/calc-engine/tests`

Current measured size:

1. `packages/forms-engine/src` and `packages/forms-engine/tests`: 16 untracked files total
2. `packages/calc-engine/src` and `packages/calc-engine/tests`: 32 untracked files total
3. combined packet size: 48 untracked files total

## 5. Why This Packet Is Bounded Correctly

This packet is intentionally narrow:

1. it admits recursive source only for the smallest already-scaffolded package lanes
2. it keeps the larger app-lane backlogs out of the review surface for now
3. it avoids `archive/`, `knowledge/`, and historical `ops/` bulk entirely
4. it preserves the deferred status of `packages/api-contracts`
5. it provides executable follow-on value because package tests can validate the tranche immediately

## 6. Operator Execution Path

Preferred task path from `C:/APEX Platform/apex-power-ops-platform`:

1. run `Preview parent-root package source packet`
2. run `Stage parent-root package source packet` only when the preview is correct
3. run `Parent-root package source packet staged diff`

Direct parent-root path if tasks are not used:

```powershell
Set-Location 'C:/APEX Platform'
git add -n -- apex-power-ops-platform/packages/forms-engine/src apex-power-ops-platform/packages/forms-engine/tests apex-power-ops-platform/packages/calc-engine/src apex-power-ops-platform/packages/calc-engine/tests
git add -- apex-power-ops-platform/packages/forms-engine/src apex-power-ops-platform/packages/forms-engine/tests apex-power-ops-platform/packages/calc-engine/src apex-power-ops-platform/packages/calc-engine/tests
git diff --cached -- apex-power-ops-platform/packages/forms-engine/src apex-power-ops-platform/packages/forms-engine/tests apex-power-ops-platform/packages/calc-engine/src apex-power-ops-platform/packages/calc-engine/tests
```

## 7. Validation Expectation

Before commit, the smallest relevant checks are:

1. `git add -n` preview of the exact packet paths
2. staged diff review for those package paths only
3. focused package tests:
   - `packages/calc-engine/tests/test_golden_fixtures.py`
   - `packages/forms-engine/tests/test_smoke.py`

This packet is suitable for executable validation because it is source-and-test-bearing, not just publication-shape scaffolding.

## 8. Do Not Do

1. do not replace this bounded packet with `git add -- apex-power-ops-platform/packages`
2. do not widen the packet into `packages/api-contracts`
3. do not mix this packet with `apps/control-plane-api`, `apps/mutation-seam`, or `apps/operations-web`
4. do not silently include generated browser outputs like `test-results/` from other lanes

## 9. Follow-On After This Packet

If this packet lands cleanly, the next logical tranches are the app-lane recursive publications, each kept separate:

1. `apps/operations-web` recursive runtime packet
2. `apps/mutation-seam` recursive runtime packet
3. `apps/control-plane-api` recursive runtime packet
4. selective `docs/` and `ops/` authority packets needed to operate those expanded lanes

Those follow-ons remain separate from this package-source packet.