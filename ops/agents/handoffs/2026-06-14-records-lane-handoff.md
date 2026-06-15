# Records / NETA Field-Records Lane — Handoff

- **Date:** 2026-06-14
- **From:** lane build session (Claude)
- **To:** main-session executor (inheriting this lane)
- **Branch:** `claude/apex-power-ops-lane-0g1pzc` → **PR #4 (draft)**
- **Lane SSoT:** `reference/neta-records/`

> This lane is the in-house replacement for the legacy field-test datastore
> (asset register · NETA data sheets · test results · PM tracking), extended to
> own the full datasheet lifecycle (define forms → capture/store → reports).
> **Operator directive:** do NOT reintroduce the legacy vendor product name in any
> doc or identifier — it is the baseline to replace, not a target. Use "legacy
> field-test datastore"; identifiers are `legacy_import` / `legacy_source_id`.

---

## 1. HEAD

- **Lane work tip:** `0cbc606a` — *docs(neta): register preserved prior-art inputs*.
- This handoff note is committed **on top** of that; the branch tip after push is
  the handoff commit (the precise hash is reported in the handoff reply / `git log -1`).
- Everything is committed and pushed; working tree clean; branch 0 ahead of origin.

## 2. Dev DB — ⚠️ NONE. Nothing has been applied to any database.

- **No migrations have been applied anywhere this session.** All SQL is **file-only**
  (reviewed, not executed). There is no `neta` schema in any database yet.
- The **only** Supabase project that exists is the **governed PROD**:
  `fxoyniqnrlkxfligbxmg` ("apex-power-ops"). It has **NOT** been touched by this lane.
  Do not apply to it without governance approval.
- There is **no dev/staging Supabase project**. One must be stood up (a separate
  Supabase project, a local Postgres, or the `tcc-fidelity-staging` DB) before applying.
- **MCP servers present:** `claude_ai_Supabase` (points only at the prod project above)
  and `tcc-fidelity-staging` (a Postgres MCP — a *candidate* staging target, **not used
  or verified for neta** this session). Neither was written to for this lane.
- Net: the "8 tables / `neta.*`" described below exist **only as SQL files**, not in a DB.

## 3. Migrations — written, not applied

Location: `infra/database/migrations/neta/`

| File | Contents | State |
|---|---|---|
| `001_neta_enums.sql` | `neta` schema + **11 enums** | WRITTEN — not applied |
| `002_neta_tables.sql` | **8 tables** + sync-contract columns + reciprocal `datasheets↔pm_events` FK | WRITTEN — not applied |
| `003_neta_indexes.sql` | **25 indexes** (incl. partial unique on current template; partial PM-due) | WRITTEN — not applied |
| `004_neta_triggers_and_views.sql` | `updated_at` triggers (×8) + **2 views** (`v_asset_test_history`, `v_pm_due`) | WRITTEN — not applied |
| `00X_*_down.sql` (001–004) + `MANIFEST.md` | reverse migrations + manifest | WRITTEN |

- No local Postgres was available to even parse-check. **First real validation = apply
  `001`→`004` in order to a staging DB**, then `\dT neta.*` / `\dt neta.*`.

**Resulting schema once applied** — schema `neta`, **8 tables**:
`asset_classes`, `assets`, `datasheet_templates`, `datasheets`, `test_results`,
`pm_programs`, `pm_schedules`, `pm_events` (+ 2 views, 11 enums, 1 trigger fn,
8 `updated_at` triggers). Cross-schema links to `org.*`/`work.*` are **deferred soft
UUIDs** (no hard FK) — activation is Chip 8.

## 4. Lane docs (read these first) — `reference/neta-records/`

- `00-MASTER-INDEX.md` — charter, four pillars, guide map, data-model summary, **§6 held decisions**.
- `01-OFFLINE-SYNC-ARCHITECTURE.md` — **RULED**: installable PWA · fully-offline · PowerSync `uploadData` → `mutation-seam` → dedupe on `pm.idempotency_keys`; device-vs-server authority split.
- `02-LEGACY-BASELINE.md` — capability floor to replace + where to exceed it; one-time migration note (no schema copy committed).
- `03-PRIOR-ART-INPUTS.md` — register of host-only, non-authoritative inputs (`D:\PDB`, `NETA Procedures bundle.zip`, `RESA_Report_Scripts.zip`, `D:\apex-power-ops-platform`). Promote only via a chip.
- `PUNCHLIST.md` — 10-chip ladder. **Chip 1 done (drafted+validated). Chip 2 = next: field-coverage matrix** (parse NETA forms into `datasheet_templates.field_schema`).

## 5. In-flight / held decisions

- **D-FORMS — HELD.** The forms + report-generation domain has several early variants
  (`packages/forms-engine`, the `neta-forms` source repo, `packages/power-test-converters`,
  the `RESA_Report_Scripts` bundle). They need a consolidation ruling **before** report-gen
  is wired to `neta.*`. **Chip 7 (reporting) is blocked on this.** Reuse nothing / build
  nothing parallel until ruled.
- **D-SURFACE — per-chip.** UI surface placement (`apps/field-surface` capture PWA ·
  `apps/forms-studio` authoring · or a new app) decided when those chips start.
- **D-GIT — working model.** Chip-sized PRs into `main`; lane = charter + punch list, not a
  long-lived branch. PR #4 = Chip 1. (Operator was unsure; this is the recommended default.)

## 6. Gotchas the inheritor should know

- **Schema is unapplied** — before Chip 3 (sync) anything, stand up a dev/staging DB and
  apply `001`→`004`.
- **No vendor name** — operator directive; do not reintroduce it in docs/schema. The lane
  was scrubbed (commit `74ef1840`).
- **`power-test-converters`** is folded into this lane (PTM/DTAX tooling, Chips 9–10);
  workspace/CI wiring deferred.
- **Parked sibling branch `laptop-wip-neta-2026-06-13`** (LOCAL-ONLY, never pushed) holds
  **non-lane** control-plane/TCC WIP (`apps/control-plane-api/services/neta/router.py`,
  `tests/test_neta_plot_tcc.py`, three `uv.lock`s, `.vscode/tasks.json`,
  `reference/tcc/TASK-128-SCOPE.md`). **Not part of this lane** — do not merge it here.
- **`reference/neta-records/` is force-tracked** via a `.gitignore` exception (`reference/*`
  is otherwise ignored). Keep new lane docs under that path.
- **Host-only sources** (`D:\PDB`, etc.) are intentionally not committed (see `03`).
- **PR #4 CI** is Vercel deploy/preview only (this lane is SQL + docs); it was green.
