# Ops — Project Miner / Jupiter Estimator Intake → `ops.*` (Design)

> **Status:** DRAFT for operator review (2026-06-19). Staged locally; on approval, committed to
> `docs/superpowers/specs/2026-06-19-ops-project-miner-intake-design.md` in a worktree off
> `origin/ops/chip0-rebaseline`. **Next after approval:** `superpowers:writing-plans` → plan → build.
> **Supersedes** the staged Chip 3 recognition-ledger spec as the *immediate* packet; that design stays
> valid as the step AFTER this intake (recognition, now grounded in real Miner data).

**Goal:** Intake the won **Project Miner** (product: **Project Jupiter**) estimator workbook into the clean
`ops.*` schema as the platform's first real project — `projects` + 9 `scopes` + QTY-expanded `apparatus` +
4-category `scope_quote` + `scope_quote_line` + refreshed `standard_hours` — via a focused, reusable,
idempotent, reconciled extractor, TDD on host `ops_dev`.

**Architecture:** a Python (openpyxl) extractor reads the `.xlsm` → a normalized intake payload (JSON) →
validated against the workbook's own totals → loaded into `ops.*` by idempotent upserts keyed on stable
provenance. Re-runnable (Rev10 → future Rev11). Packaged reusably (the `records-import` precedent) so it
becomes the seed of ops roadmap Chip 5.

**Tech stack:** Python + `openpyxl` via `uv`; PostgreSQL 17 host `apex-dev-pg` / DB `ops_dev`; `psycopg`;
`pytest`.

---

## Global Constraints

- **Substrate = `ops.*` only.** `public.*` (concept) and `seam.*` (separate) are never touched.
- **Identity = the canonical `ops` spine** (Chip 1); **FIXED scope→apparatus binding** (Law 1).
- **Recognition firewall (Law 3):** no live revenue columns beyond the frozen `quoted_hours`/`quoted_revenue`
  snapshot on `ops.apparatus`; recognition *events* are a later chip.
- **Grain:** estimator line `× QTY` → **individual `ops.apparatus` units** (recognition grain, D-OPS-8), each
  `quote_line_id`-linked to its `scope_quote_line`, with provenance to the source row.
- **Idempotent / re-runnable:** stable provenance keys; upsert (re-running Rev10 = no-op; Rev11 = diffs).
- **Validated against the source:** every roll-up the workbook computes is re-derived and asserted (below).
- **TDD on host `ops_dev`** — re-apply `ops` `001`+`002` first (laptop `ops_dev` was dropped §257).
- **Both names:** the project record carries codename **Project Miner** + product **Project Jupiter**.

---

## Source (the workbook, characterized)

`C:\Users\jjswe\Desktop\Project Miner PM Planning\Cupertino - Miner Estimator PHX Bldg A & B MV Rev10.xlsm`
— client **STACK/Oracle "Project Jupiter"**, Santa Theresa NM (Doña Ana County); **NETA ATS**;
**contract = $4,692,078.98**.

**Sheets that matter:** 7 real scope sheets `A1) MV-Core`, `A2) MV-Mech`, `A3) MV-Production`, `A4) MV-Spine`,
`B1) MV-Mech`, `B2) MV-Production`, `B3) MV-Spine`; `Equipment Reference` (standard-hours catalog);
`Submittal Specs` (CSI-section coverage); `Print_Template` (project roll-up). 23 empty `N.X` template tabs are
ignored. 2 **Modular Chiller Plant** scopes appear only in the `Print_Template` roll-up ($94,186.80 each, hours
"estimated").

**Per-scope-sheet cell map** (constant across the 7):

| Datum | Cell(s) | → ops |
|---|---|---|
| Scope name | `B2` | `scopes.scope_name` |
| Total App Hours (J3) | `J3` | `scope_quote.total_quoted_hours` |
| Onsite / Offsite / Travel / Outside totals | `P14` / `P19` / `P26` / `P33` | `scope_quote.{onsite_labor,offsite_labor,travel,outside_services}` |
| Unit mult (M4) / % adjust (N4) | `M4` / `N4` | `scope_quote.{unit_multiplier,pct_adjust}` |
| Unadjusted (P3) / Adjusted (P4) | `P3` / `P4` | *validation only* (generated cols re-derive) |
| Apparatus line table | header `row 5`: `C`=QTY, `D`=NETA §, `E`=Apparatus Type, `F`=Notes, `G`=Drawing, `I`=Hrs/Unit, `J`=Hrs/Line; data from ~`row 7` until blank | `scope_quote_line` + expanded `apparatus` |
| Client / location / date | `E3` / `E4` / `C4` region | `projects.*` / `apparatus.building` etc. |

**`Equipment Reference`** (486 rows): NETA'25/'23 section, "Scope of Work" (= apparatus type), `ATS25`/`MTS23`
hours → `ops.standard_hours (apparatus_type, test_standard, default_hours, neta_section)`.

**`Print_Template`** `R13` = total cost ($4,692,078.98); `R14–R22` = per-scope $ (the 7 MV + 2 chiller).

---

## Target schema (exact — Chips 1–2 on `ops/chip0-rebaseline`)

`ops.projects(project_number⎮project_name⎮status[ops.project_status]⎮quote_revision⎮quote_date⎮estimator⎮contract_value⎮business_unit⎮description⎮source⎮legacy_source_id⎮provenance_status⎮…)` ·
`ops.scopes(project_id⎮scope_number⎮scope_name⎮scope_type[ops.scope_type]⎮status⎮sort_order⎮source⎮legacy_source_id⎮…)` ·
`ops.scope_quote(scope_id PK⎮onsite_labor⎮offsite_labor⎮travel⎮outside_services⎮unit_multiplier⎮pct_adjust⎮total_quoted_hours⎮ + generated unadjusted_total/adjusted_total/blended_rate⎮is_frozen⎮…)` ·
`ops.scope_quote_line(scope_id⎮apparatus_type⎮test_standard[ops.test_standard]⎮qty⎮hrs_per_unit⎮ line_hours=qty*hrs_per_unit (generated)⎮catalog_default_hours⎮designation⎮line_number⎮…)` ·
`ops.apparatus(scope_id⎮task_id⎮apparatus_designation⎮apparatus_name⎮apparatus_type⎮status⎮drawing_reference⎮ +Chip2: quoted_hours⎮quoted_revenue⎮quote_line_id→scope_quote_line⎮ source⎮legacy_source_id⎮provenance_status⎮…)` ·
`ops.standard_hours(apparatus_type⎮test_standard⎮default_hours⎮neta_section⎮category⎮ unique(apparatus_type,test_standard))` ·
view `ops.v_apparatus_quote` derives `quoted_revenue = apparatus.quoted_hours × scope_quote.blended_rate`.

---

## Components & mapping

### 1. Extractor — `packages/ops-intake/` (reusable, CLI)
- `ops_intake.extract(xlsm_path) -> IntakePayload` (pydantic/dataclass): `project`, `scopes[]`, each scope with
  `quote` (4 cats + M4/N4 + J3) and `lines[]` (type/std/qty/hrs_per_unit/section/drawing/notes/line_number),
  plus `standard_hours[]` from `Equipment Reference`. Pure read; no DB.
- `ops_intake.validate(payload) -> [checks]` (see Validation).
- `ops_intake.load(payload, dsn, *, approve=False)` — idempotent upsert into `ops.*`; `approve=True` runs the
  freeze step.
- CLI: `ops-intake extract <xlsm> --out payload.json` · `ops-intake load payload.json --dsn … [--approve]`.

### 2. Load mapping (estimator → `ops.*`)
- **`ops.projects`** (1): `project_number` = `"MINER-PHX-AB-MV"` (derived, stable); `project_name` =
  `"Project Miner — PHX Bldg A & B MV"` (operator: ALL construction/PM references use **Project Miner**);
  `description` = "Public/product name: Project Jupiter — Oracle/STACK data-center campus, Doña Ana County NM.";
  `status` = `'Won'`; `quote_revision` = `"Rev10"`;
  `quote_date` from sheet date; `estimator` if present; `contract_value` = Σ scope `adjusted_total` (P4) =
  **$4,692,078.98**; `source` = workbook filename; `legacy_source_id` = `"project-miner"`;
  `provenance_status` `'draft'` → `'approved'` on `--approve`.
- **`ops.scopes`** (9): `scope_name` = sheet name; `scope_type` = `'OTHER'` (these are building/discipline
  groupings of mixed MV apparatus — the enum has no "MV"); `sort_order` by sheet order; `legacy_source_id` =
  sheet name. (2 chiller scopes: name from `Print_Template`, no apparatus — see decision 5.)
- **`ops.scope_quote`** (per scope): `onsite_labor=P14`, `offsite_labor=P19`, `travel=P26`,
  `outside_services=P33`, `unit_multiplier=M4`, `pct_adjust=N4`, `total_quoted_hours=J3`. Generated
  `unadjusted_total`/`adjusted_total`/`blended_rate` must equal sheet `P3`/`P4`/(P4÷J3).
- **`ops.scope_quote_line`** (per estimator line): `apparatus_type=E`, `test_standard='ATS'`, `qty=C`,
  `hrs_per_unit=I`, `catalog_default_hours` = `standard_hours` lookup, `designation` (col, if any),
  `line_number` = source row, `notes=F`. Generated `line_hours` must equal sheet `J` (Hrs/Line).
- **`ops.apparatus`** (QTY-expanded): for a line with `qty=N`, emit N rows — `apparatus_designation` =
  `"<apparatus_type> <seq>"` (per scope; provenance to line+unit index), `apparatus_type=E`, `scope_id`,
  `quote_line_id` → the line, `quoted_hours = hrs_per_unit`, `drawing_reference=G`, `status='Not Started'`,
  `legacy_source_id` = `"<sheet>:row<r>:u<i>"`. `quoted_revenue` left null at draft; **frozen at `--approve`**
  to `quoted_hours × scope.blended_rate` (Chip 2 semantics), and `provenance_status`→`'approved'`.
- **`ops.standard_hours`**: upsert from `Equipment Reference` on `(apparatus_type, test_standard)`.

### 3. Approve / freeze step (`--approve`)
Sets `apparatus.quoted_revenue = quoted_hours × scope_quote.blended_rate`, `scope_quote.is_frozen=true`,
`provenance_status='approved'` across the project. (Recognition, a later chip, reads the frozen
`quoted_revenue`.) Idempotent.

---

## Validation (trust gates — each becomes a test against the real workbook)
1. Per scope: `Σ scope_quote_line.line_hours == J3`.
2. Per scope: `onsite+offsite+travel+outside == P3` (sheet unadjusted).
3. Per scope: `P3 × M4 × N4 == P4` (sheet adjusted; generated `adjusted_total` matches).
4. Per **apparatus-bearing (MV) scope** (post-approve): `Σ apparatus.quoted_revenue == scope P4` (== `Print_Template` R-row). *(Chiller scopes have no apparatus — exempt.)*
5. Project: `Σ all-9-scope adjusted_total == contract_value == $4,692,078.98` (`Print_Template` R13), within $1 — i.e. 7 MV ($4,503,705.39) + 2 chiller lumps ($188,373.60).
6. `count(apparatus) == Σ scope_quote_line.qty` (QTY-expansion integrity).
7. Re-running `load` on the same payload changes 0 rows (idempotency).

## Data flow
```
.xlsm ─extract─▶ IntakePayload(JSON) ─validate(1–6)─▶ load (idempotent upsert) ─▶ ops.* (draft)
                                                                  └─ --approve ─▶ freeze quoted_revenue + provenance
```

## Idempotency / re-import keys
project = `legacy_source_id 'project-miner'` (or `project_number`); scope = `(project, sheet-name)`;
line = `(scope, line_number)`; apparatus = `(quote_line, unit_index)`; standard_hours =
`(apparatus_type, test_standard)`. All upsert-by-key.

## In scope
`packages/ops-intake/` extractor+validator+loader+CLI; re-apply `ops` `001`+`002` to host `ops_dev`; load
Project Miner (projects/scopes/scope_quote/scope_quote_line/apparatus/standard_hours) + approve/freeze; full
TDD; SSoT/`MANIFEST` note.

## Out of scope (later packets)
Review/edit UI; the recognition ledger (Chip 3, next); production tracking; prod deployment of `ops.*`;
multi-workbook generalization beyond this canonical structure; real per-unit apparatus designations from
drawings (placeholder designations now).

## Branch & merge
`ops/chip5-miner-intake` (or continue the lane) off `origin/ops/chip0-rebaseline`; whole-lane merge to `main`
stays operator-gated.

## Testing (TDD, host `ops_dev`)
- Extractor unit tests on a **small synthetic `.xlsx` fixture** mirroring the cell map (fast, committed).
- Reconciliation **integration test** against the real workbook (`skipif` the Desktop file is absent) —
  asserts validations 1–6 + the $4,692,078.98 total.
- Loader tests against host `ops_dev` (DSN pinned; mirror the Chip 1–2 / jobs conftest:
  `127.0.0.1:5432`, role + `DEV_PG_PASSWORD`, `sslmode=disable`). Exact commands in the plan.

## Open decisions (my leans — flag any to flip)
1. **Both-names — RESOLVED (operator 2026-06-19): construction/PM = "Project Miner".**
   `project_name="Project Miner — PHX Bldg A & B MV"`, `legacy_source_id='project-miner'`; public/product name
   **"Project Jupiter"** captured in `description` only. No schema change.
2. **`scope_type`** for the mixed-MV scopes = `'OTHER'` (enum lacks "MV"). **Lean: OTHER.**
3. **QTY-expansion** to apparatus units (vs line-grain). **Lean: expand** (recognition grain).
4. **`quoted_revenue` freeze** = two-phase (draft load → `--approve` freezes). **Lean: two-phase.**
5. **Chiller scopes** = include as 2 scopes, **no apparatus**; the $94,187 lump (from `Print_Template`, not a
   scope sheet, so undifferentiated) is captured in `scope_quote` as a **single flagged category** with
   `provenance_status='estimate'` + note ("lump-sum, hours estimated, pending final") so the project total
   reconciles. **Lean: include as flagged estimate; defer apparatus + category split.**
6. **`test_standard` = ATS** project-wide (sheets marked ATS). **Lean: ATS.**
7. **Apparatus designations** derived (`"<type> <seq>"`) — real tags come later from drawings. **Lean: derive.**
