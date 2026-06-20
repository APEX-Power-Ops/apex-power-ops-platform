# Lanes & charters

Operational realization of **L3** in `.claude/PLATFORM/APEX-PLATFORM-OPERATING-ARCHITECTURE-2026-06-18.md`
(substrate). A *lane* is an isolated unit of parallel work: **one git worktree + one branch +
one dev DB/schema + a disjoint write-boundary**. Disjoint write-boundaries are what make
concurrent lanes (CC + Codex + a 2nd Claude) safe — they were the missing guardrail behind the
`power-test-converters` collision footgun.

Promotion/run accounting for lane work flows through the `apex-jobs` task bus
(`packages/apex-jobs`) with `env=sandbox|host` + human-approval gates (Invariants §2.1–2.4).

## Charter template

```
# Lane: <name>
- **Scope:** <one sentence — what this lane is allowed to change>
- **Branch:** <branch>           **Worktree:** <path>
- **Dev DB / schema:** <db>.<schema>   (host apex-dev-pg :5432)
- **Write-boundary (OWNS):** <paths/globs this lane may modify>
- **Must NOT touch:** <explicit exclusions — other lanes' WIP, prod, etc.>
- **Gates (human-approval):** <which of {prod_write, business_state, spend, schema, external_service}>
- **Escalation / owner:** <who resolves conflicts; how to abort>
- **Status:** active | held | merged
```

A lane is "done" only when its branch is pushed and its completion is recorded as state
(SSoT-not-chat) — not merely when chat says so.

---

## Active lanes

### Lane: records (PowerDB-replacement / NETA records)
- **Scope:** the in-house records forms engine + NETA reference/datasheet data — DEV ONLY.
- **Branch:** `records/chip10-import`   **Worktree:** `/home/olares/code/apex/apex-records-lane`
- **Dev DB / schema:** `records_dev` → `records.*` (+ `neta.*` reference)
- **Write-boundary (OWNS):** `infra/database/migrations/records/**`, `packages/records-*/**`,
  the datasheet/import tooling under `tools/powerdb/**`.
- **Must NOT touch:** the parallel `packages/power-test-converters/**` WIP (unstaged, untouched);
  prod Supabase.
- **Gates:** `schema` (every migration), `business_state`.
- **Escalation / owner:** CC (technical authority). Abort = leave branch unpushed-of-the-bad-commit; never force-push shared history.
- **Status:** **held** — "nothing ships until it's all done" (Chip 10c DTAX-read still pending). Stays unmerged.

### Lane: ops (PM revenue / recognition)
- **Scope:** the Operations PM lane — Estimator intake → per-apparatus revenue → progress billing — DEV ONLY.
- **Branch:** `ops/chip0-rebaseline`   **Worktree:** (laptop / on-demand)
- **Dev DB / schema:** `ops_dev` → `work.*`
- **Write-boundary (OWNS):** `packages/ops-*/**`, `infra/database/migrations/ops/**`.
- **Must NOT touch:** `records.*`; prod.
- **Gates:** `schema`, `business_state` (revenue is operator-authoritative), `spend`.
- **Escalation / owner:** CC + operator (revenue = operator authority).
- **Status:** active (Chips 0/1/2 built on `ops_dev`; not PR'd).

### Lane: learning (enablement / capture + ROI)
- **Scope:** the flagship learning lane — contextual resource surfacing (Slice 1, merged) + the capture/tracking path (Slice 2) — DEV ONLY.
- **Branch:** `learning/slice2-capture`   **Worktree:** `/home/olares/code/apex/apex-learning-lane`
- **Dev DB / schema:** `learning_dev` → `public.*` (frozen rev-2.3/2.4 baseline; lane isolation = the database, per separate-DB-per-lane D-ARCH-1)
- **Write-boundary (OWNS):** `infra/database/migrations/learning/**`, `packages/learning-capture/**`,
  `packages/learning-resolver/**` (Slice-1 hardening), `packages/learning-projections/**` (Slice 2b), `apps/control-plane-api/services/learning/**`
  (+ the `-e ../../packages/learning-capture` line in `requirements.txt`; + the learning-router guard in `main.py`),
  `apps/operations-web/app/learning-demo/**`, `apps/operations-web/lib/learning-*.ts`,
  `apps/operations-web/tests/learning-*.spec.ts`, `docs/superpowers/{specs,plans}/2026-06-20-learning-slice2*`.
- **Must NOT touch:** `records.*` / `ops.*` migrations + packages; the parallel `packages/power-test-converters/**` WIP; prod Supabase.
- **Gates (human-approval):** `schema` (each `learning_dev` migration apply; `001`/`002` **DONE 2026-06-20**; Slice 2b migrations pending); promotion (merge to main) is operator-gated.
- **Escalation / owner:** CC (technical authority); operator gates schema apply + merge.
- **Status:** active (Slice 2a MERGED, PR #23 → `c9c2b6a8`; **`learning_dev` apply DONE + e2e-verified 2026-06-20** — capture vertical LIVE; Slice 2b projections next; data acquisition = value gate).

> Merged/closed lanes (orchestration/chip3-apex-jobs, docs/chip2-governance-supersede) are pruned;
> their work is on `main`.
