# Parent-Root PM-Schema-020G-A Draft Publication Handoff
## Date: 2026-04-22
## Updated by: GitHub Copilot (GPT-5.4)
## Scope: Active next-step packet for the bounded `pm-schema-020g-a` parser-surface reconciliation and baseline shim singleton under `C:/APEX Platform/apex-power-ops-platform`

## 1. Summary

The active shared packages, active app lanes, residual scaffold/doc surfaces, infra-database lane, docs lane, ops knowledge-control-plane registry lane, ops legacy-governance lane, ops knowledge-resource-operations lane, the forms-import draft pair, the `001af` draft, the `apex-unification-001` draft pair, the `knowledge-import-001` draft pair, the `pm-schema-009` draft family, the `pm-schema-010` draft trio, the `pm-schema-011` dependency-activation family, the `pm-schema-012` identity and joined-read family, the `pm-schema-013` work-package write family, the `pm-schema-014` task-write pair, the `pm-schema-015` assignment-write pair, the `pm-schema-016` dependency-write singleton, the `pm-schema-017` execution-issue-write singleton, the `pm-schema-018` progress-snapshot-write singleton, the top-level `pm-schema-019` write-surface consolidation singleton, the full `pm-schema-019f` through `pm-schema-019k` follow-on chain, the `pm-schema-ui-002g` comparative schedule analytics read surface and host validation singleton, the `pm-schema-ui-002g` host-variance shell wiring and browser validation singleton, the `pm-schema-ui-002e-host` drivers shell wiring and browser validation singleton, the `pm-schema-ui-002f-host` tracer shell wiring and browser validation singleton, the `pm-schema-ui-001` field apparatus workflow prototype design singleton, the `pm-schema-ui-002` gantt layer comparison decision singleton, the `pm-schema-ui-003` PM approval queue prototype design singleton, the `pm-schema-ui-004` lead operations surface prototype design singleton, the `pm-schema-ui-005` cross-surface integration spec singleton, the `pm-schema-ui-006` mutation seam API spec and implementation scaffold singleton, the full `pm-schema-ui-001a` through `pm-schema-ui-001e` implementation chain, the `pm-schema-ui-002a` P6 schedule context import and read bridge implementation singleton, the `pm-schema-ui-002b` read-only Gantt prototype implementation singleton, the `pm-schema-ui-002c` baseline overlay and read-model hardening singleton, the `pm-schema-ui-002d` baseline overlay re-issue singleton, and the full `pm-schema-020a` through `pm-schema-020f` plus `pm-schema-020e.1` baseline substrate, ingestion, host-verification, and integrity-gate chain are now published on parent-root `clean-main`.

The next smallest remaining substantive packet is the parser-surface `pm-schema-020g-a` reconciliation and baseline-shim singleton, which stages cleanly at 1 file. The remaining parser-test and fixture-admission substrate explicitly depends on this path.

## 2. Why This Packet Is Next

Measured from the parent git root at `C:/APEX Platform` on 2026-04-22 after the `pm-schema-020e.1` draft publication:

1. remaining untracked top-level distribution is `ops` 416, `knowledge` 974, `archive` 2516, plus 2 excluded generated app artifacts
2. the remaining `ops/agents` backlog is still split into `handoffs` 333 and `packets/draft` 83
3. `git add -n --` on the bounded `pm-schema-020g-a` packet stages exactly this file cleanly:
   - `2026-04-18-pm-schema-020g-a-parser-surface-reconciliation-and-baseline-shim.json`
4. `pm-schema-020g-a` is now dependency-safe after `020e.1` and `020f`, and the later `020e.2` and `020h` substrate explicitly waits on this reconciliation path rather than the alternative `020g-b` lane

## 3. Packet Intent

Use this packet to introduce the bounded `pm-schema-020g-a` parser-surface reconciliation and baseline shim singleton:

1. `2026-04-18-pm-schema-020g-a-parser-surface-reconciliation-and-baseline-shim.json`

## 4. Exact Packet Contents

From the parent git root at `C:/APEX Platform`, the bounded packet path is:

1. `apex-power-ops-platform/ops/agents/packets/draft/2026-04-18-pm-schema-020g-a-parser-surface-reconciliation-and-baseline-shim.json`

Current measured contents: 1 file.

## 5. Why This Packet Is Bounded Correctly

This packet is intentionally narrow:

1. it introduces only the parser-surface reconciliation and baseline-shim slice and does not widen into later parser-test reauthoring, fixture admission, bridge routes, PM UI work, SQL, or broad parser rewrites
2. it preserves dependency order by landing the required parser substrate before `020e.2` and `020h`
3. it avoids the 333-file handoff backlog and the remaining 82-file draft backlog beyond this singleton
4. it does not widen into `knowledge/` or `archive`

## 6. Operator Execution Path

Preferred task path from `C:/APEX Platform/apex-power-ops-platform`:

1. run `Preview parent-root pm-schema-020g-a draft packet`
2. run `Stage parent-root pm-schema-020g-a draft packet` only when the preview is correct
3. run `Parent-root pm-schema-020g-a draft packet staged diff`

Direct parent-root path if tasks are not used:

```powershell
Set-Location 'C:/APEX Platform'
git add -n -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-18-pm-schema-020g-a-parser-surface-reconciliation-and-baseline-shim.json
git add -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-18-pm-schema-020g-a-parser-surface-reconciliation-and-baseline-shim.json
git diff --cached -- apex-power-ops-platform/ops/agents/packets/draft/2026-04-18-pm-schema-020g-a-parser-surface-reconciliation-and-baseline-shim.json
```

## 7. Validation Expectation

Before commit, the smallest relevant checks are:

1. `git add -n` preview of the exact path
2. staged diff review for that draft packet file only

This lane is packet-definition JSON, so diff discipline matters more than executable validation.

## 8. Do Not Do

1. do not widen this packet into `020e.2`, `020h`, `020g-b`, bridge routes, PM UI work, SQL, or broad parser rewrites
2. do not imply the alternative `020g-b` lane is jointly required when downstream notes explicitly prefer `020g-a`
3. do not mix this packet with `ops/agents/handoffs`

## 9. Follow-On After This Packet

If this packet lands cleanly, the next logical lanes are:

1. the bounded `pm-schema-020e.2` parser-test reauthoring singleton
2. then the bounded `pm-schema-020h` concrete sanitized golden fixture admission singleton