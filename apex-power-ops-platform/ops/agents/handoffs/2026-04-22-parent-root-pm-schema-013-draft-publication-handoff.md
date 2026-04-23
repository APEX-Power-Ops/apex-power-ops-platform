# Parent-Root PM-Schema 013 Draft Publication Handoff
## Date: 2026-04-22
## Updated by: GitHub Copilot (GPT-5.4)
## Scope: Active next-step packet for the bounded `pm-schema-013` work-package write family under `C:/APEX Platform/apex-power-ops-platform`

## 1. Summary

The active shared packages, active app lanes, residual scaffold/doc surfaces, infra-database lane, docs lane, ops knowledge-control-plane registry lane, ops legacy-governance lane, ops knowledge-resource-operations lane, the forms-import draft pair, the `001af` draft, the `apex-unification-001` draft pair, the `knowledge-import-001` draft pair, the `pm-schema-009` draft family, the `pm-schema-010` draft trio, the `pm-schema-011` dependency-activation family, and the `pm-schema-012` identity and joined-read family are now published on parent-root `clean-main`.

The next smallest remaining substantive packet is the `pm-schema-013` work-package write family, which currently stages cleanly at 3 files. This packet introduces the next coherent PM work-package write sequence without widening into the task-write `pm-schema-014` family.

## 2. Why This Packet Is Next

Measured from the parent git root at `C:/APEX Platform` on 2026-04-22 after the `pm-schema-012` draft publication:

1. remaining untracked top-level distribution is `ops` 456, `knowledge` 974, `archive` 2516, plus 2 excluded generated app artifacts
2. the remaining `ops/agents` backlog is still split into `handoffs` 333 and `packets/draft` 123
3. `git add -n --` on the bounded `pm-schema-013` family stages exactly these three files cleanly:
   - `2026-04-14-pm-schema-013-pm-work-package-write-surface-minimal.json`
   - `2026-04-14-pm-schema-013i-pm-work-package-write-surface-integration-smoke.json`
   - `2026-04-14-pm-schema-013j-pm-work-package-write-response-crew-join.json`
4. the three files form one coherent work-package write sequence: minimal write surface, integration smoke, and write-response enrichment

## 3. Packet Intent

Use this packet to introduce the bounded `pm-schema-013` work-package write family:

1. `2026-04-14-pm-schema-013-pm-work-package-write-surface-minimal.json`
2. `2026-04-14-pm-schema-013i-pm-work-package-write-surface-integration-smoke.json`
3. `2026-04-14-pm-schema-013j-pm-work-package-write-response-crew-join.json`

## 4. Exact Packet Contents

From the parent git root at `C:/APEX Platform`, the bounded packet paths are:

1. `apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013-pm-work-package-write-surface-minimal.json`
2. `apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013i-pm-work-package-write-surface-integration-smoke.json`
3. `apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013j-pm-work-package-write-response-crew-join.json`

Current measured contents: 3 files.

## 5. Why This Packet Is Bounded Correctly

This packet is intentionally narrow:

1. it keeps the full `pm-schema-013` work-package write sequence together instead of splitting write implementation, runtime smoke, and response shaping
2. it stays within work-package writes and avoids widening into the task-write `pm-schema-014` family
3. it avoids the 333-file handoff backlog and the remaining 120-file draft backlog beyond this family
4. it does not widen into `knowledge/` or `archive/`

## 6. Operator Execution Path

Preferred task path from `C:/APEX Platform/apex-power-ops-platform`:

1. run `Preview parent-root pm-schema 013 draft packet`
2. run `Stage parent-root pm-schema 013 draft packet` only when the preview is correct
3. run `Parent-root pm-schema 013 draft packet staged diff`

Direct parent-root path if tasks are not used:

```powershell
Set-Location 'C:/APEX Platform'
git add -n -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013-pm-work-package-write-surface-minimal.json apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013i-pm-work-package-write-surface-integration-smoke.json apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013j-pm-work-package-write-response-crew-join.json
git add -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013-pm-work-package-write-surface-minimal.json apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013i-pm-work-package-write-surface-integration-smoke.json apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013j-pm-work-package-write-response-crew-join.json
git diff --cached -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013-pm-work-package-write-surface-minimal.json apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013i-pm-work-package-write-surface-integration-smoke.json apex-power-ops-platform/ops/agents/packets/draft/2026-04-14-pm-schema-013j-pm-work-package-write-response-crew-join.json
```

## 7. Validation Expectation

Before commit, the smallest relevant checks are:

1. `git add -n` preview of the exact three paths
2. staged diff review for those three draft packet files only

This lane is packet-definition JSON, so diff discipline matters more than executable validation.

## 8. Do Not Do

1. do not widen this packet into `pm-schema-014`, later `pm-schema`, `pm-schema-ui`, or other `ops/agents/packets/draft` files
2. do not mix this packet with `ops/agents/handoffs`
3. do not mix this packet with `knowledge/` or `archive/`
4. do not reopen already-published application, package, scaffold, infra, docs, or earlier `ops/` packets

## 9. Follow-On After This Packet

If this packet lands cleanly, the next logical lanes are:

1. the `pm-schema-014` task-write family if it remains the smallest coherent next move
2. the next smallest coherent `ops/agents/packets/draft` family after `pm-schema-014`
3. broader `ops/agents` packet strategy decisions
4. `knowledge/` packet(s)
5. `archive/` strategy decisions rather than automatic publication