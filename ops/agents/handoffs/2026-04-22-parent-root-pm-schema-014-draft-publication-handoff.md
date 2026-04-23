# Parent-Root PM-Schema 014 Draft Publication Handoff
## Date: 2026-04-22
## Updated by: GitHub Copilot (GPT-5.4)
## Scope: Active next-step packet for the bounded `pm-schema-014` task-write pair under `C:/APEX Platform/apex-power-ops-platform`

## 1. Summary

The active shared packages, active app lanes, residual scaffold/doc surfaces, infra-database lane, docs lane, ops knowledge-control-plane registry lane, ops legacy-governance lane, ops knowledge-resource-operations lane, the forms-import draft pair, the `001af` draft, the `apex-unification-001` draft pair, the `knowledge-import-001` draft pair, the `pm-schema-009` draft family, the `pm-schema-010` draft trio, the `pm-schema-011` dependency-activation family, the `pm-schema-012` identity and joined-read family, and the `pm-schema-013` work-package write family are now published on parent-root `clean-main`.

The next smallest remaining substantive packet is the `pm-schema-014` task-write pair, which currently stages cleanly at 2 files. This packet introduces the next coherent PM task-write sequence without widening into larger later-runtime packets.

## 2. Why This Packet Is Next

Measured from the parent git root at `C:/APEX Platform` on 2026-04-22 after the `pm-schema-013` draft publication:

1. remaining untracked top-level distribution is `ops` 453, `knowledge` 974, `archive` 2516, plus 2 excluded generated app artifacts
2. the remaining `ops/agents` backlog is still split into `handoffs` 333 and `packets/draft` 120
3. `git add -n --` on the bounded `pm-schema-014` pair stages exactly these two files cleanly:
   - `2026-04-14-pm-schema-014-pm-task-write-surface-minimal.json`
   - `2026-04-14-pm-schema-014i-pm-task-write-surface-integration-smoke.json`
4. the two files form one coherent task-write sequence: minimal write surface and integration smoke

## 3. Packet Intent

Use this packet to introduce the bounded `pm-schema-014` task-write pair:

1. `2026-04-14-pm-schema-014-pm-task-write-surface-minimal.json`
2. `2026-04-14-pm-schema-014i-pm-task-write-surface-integration-smoke.json`

## 4. Exact Packet Contents

From the parent git root at `C:/APEX Platform`, the bounded packet paths are:

1. `apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-014-pm-task-write-surface-minimal.json`
2. `apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-014i-pm-task-write-surface-integration-smoke.json`

Current measured contents: 2 files.

## 5. Why This Packet Is Bounded Correctly

This packet is intentionally narrow:

1. it keeps the full `pm-schema-014` task-write sequence together instead of splitting runtime write implementation from its integration smoke
2. it stays within task writes and avoids widening into later PM runtime or UI families
3. it avoids the 333-file handoff backlog and the remaining 118-file draft backlog beyond this pair
4. it does not widen into `knowledge/` or `archive/`

## 6. Operator Execution Path

Preferred task path from `C:/APEX Platform/apex-power-ops-platform`:

1. run `Preview parent-root pm-schema 014 draft packet`
2. run `Stage parent-root pm-schema 014 draft packet` only when the preview is correct
3. run `Parent-root pm-schema 014 draft packet staged diff`

Direct parent-root path if tasks are not used:

```powershell
Set-Location 'C:/APEX Platform'
git add -n -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-014-pm-task-write-surface-minimal.json apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-014i-pm-task-write-surface-integration-smoke.json
git add -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-014-pm-task-write-surface-minimal.json apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-014i-pm-task-write-surface-integration-smoke.json
git diff --cached -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-014-pm-task-write-surface-minimal.json apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-014i-pm-task-write-surface-integration-smoke.json
```

## 7. Validation Expectation

Before commit, the smallest relevant checks are:

1. `git add -n` preview of the exact two paths
2. staged diff review for those two draft packet files only

This lane is packet-definition JSON, so diff discipline matters more than executable validation.

## 8. Do Not Do

1. do not widen this packet into later `pm-schema`, `pm-schema-ui`, or other `ops/agents/packets/draft` files
2. do not mix this packet with `ops/agents/handoffs`
3. do not mix this packet with `knowledge/` or `archive/`
4. do not reopen already-published application, package, scaffold, infra, docs, or earlier `ops/` packets

## 9. Follow-On After This Packet

If this packet lands cleanly, the next logical lanes are:

1. the next smallest coherent `ops/agents/packets/draft` family after `pm-schema-014`
2. broader `ops/agents` packet strategy decisions
3. `knowledge/` packet(s)
4. `archive/` strategy decisions rather than automatic publication