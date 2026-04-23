# Parent-Root Apex-Unification-001B Draft Publication Handoff
## Date: 2026-04-22
## Updated by: GitHub Copilot (GPT-5.4)
## Scope: Active next-step packet for the bounded `apex-unification-001b` Supabase PM/project/PSS lineage tranche movement singleton under `C:/APEX Platform/apex-power-ops-platform`

## 1. Summary

The first cross-family unification tranche is now advanced through `apex-unification-001a`.

The next smallest remaining substantive packet is `apex-unification-001b`, which stages cleanly at 1 file. It is the newly unblocked adjacent lineage tranche in the same unification family and is narrower than switching sideways into the broader `knowledge-import-001a` low-weight knowledge landing packet.

## 2. Why This Packet Is Next

Measured from the parent git root at `C:/APEX Platform` on 2026-04-22 after the `apex-unification-001a` draft publication:

1. remaining untracked top-level distribution is `ops` 400, `knowledge` 974, `archive` 2516, plus 2 excluded generated app artifacts
2. the remaining `ops/agents` backlog is still split into `handoffs` 333 and `packets/draft` 67
3. `git add -n --` on the bounded `apex-unification-001b` packet stages exactly this file cleanly:
   - `2026-04-13-apex-unification-001b-supabase-pm-project-pss-lineage-tranche-movement.json`
4. `apex-unification-001b` explicitly depends on landed `apex-unification-001a`, and its dependency note requires `001a` to land first
5. `knowledge-import-001a` still stages cleanly, but it is a broader low-weight knowledge landing slice rather than the next adjacent unification tranche

## 3. Packet Intent

Use this packet to introduce the bounded `apex-unification-001b` Supabase PM/project/PSS lineage tranche movement singleton:

1. `2026-04-13-apex-unification-001b-supabase-pm-project-pss-lineage-tranche-movement.json`

## 4. Exact Packet Contents

From the parent git root at `C:/APEX Platform`, the bounded packet path is:

1. `apex-power-ops-platform/ops/agents/packets/draft/2026-04-13-apex-unification-001b-supabase-pm-project-pss-lineage-tranche-movement.json`

Current measured contents: 1 file.

## 5. Why This Packet Is Bounded Correctly

This packet is intentionally narrow:

1. it introduces only the lineage-only movement tranche for approved Supabase PM/project/PSS SQL, seed, and supporting documentation slices
2. it is explicitly constrained to lineage/reference homes and does not authorize active PM schema promotion, runtime code changes, or automation movement
3. it stays inside the same unification family already opened by `apex-unification-001a`
4. it remains narrower than switching to the broader `knowledge-import-001a` landing work

## 6. Operator Execution Path

Preferred task path from `C:/APEX Platform/apex-power-ops-platform`:

1. run `Preview parent-root apex-unification-001b draft packet`
2. run `Stage parent-root apex-unification-001b draft packet` only when the preview is correct
3. run `Parent-root apex-unification-001b draft packet staged diff`

Direct parent-root path if tasks are not used:

```powershell
Set-Location 'C:/APEX Platform'
git add -n -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-13-apex-unification-001b-supabase-pm-project-pss-lineage-tranche-movement.json
git add -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-13-apex-unification-001b-supabase-pm-project-pss-lineage-tranche-movement.json
git diff --cached -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-13-apex-unification-001b-supabase-pm-project-pss-lineage-tranche-movement.json
```

## 7. Validation Expectation

Before commit, the smallest relevant checks are:

1. `git add -n` preview of the exact path
2. staged diff review for that draft packet file only

This lane is packet-definition JSON, so diff discipline matters more than executable validation.

## 8. Do Not Do

1. do not widen this packet into later unification tranches or knowledge-import packets
2. do not mix this packet with `ops/agents/handoffs`

## 9. Follow-On After This Packet

If this packet lands cleanly, re-evaluate whether `knowledge-import-001a` or the next unification slice is the truthful next bounded follow-on.