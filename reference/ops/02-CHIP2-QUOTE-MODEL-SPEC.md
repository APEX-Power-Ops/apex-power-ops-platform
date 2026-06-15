# Chip 2 — ops Quote Model — Spec

- **Status:** APPROVED (operator, 2026-06-15) — build in progress
- **Lane:** Operations (PM) · SSoT: [`00-MASTER-INDEX.md`](00-MASTER-INDEX.md) · Dev DB: `ops_dev` · builds on Chip 1 ([`01-CHIP1-IDENTITY-SPEC.md`](01-CHIP1-IDENTITY-SPEC.md))
- **Scope:** the **frozen-quote layer** — standard-hours catalog + per-project quote lines + per-scope quote facts + apparatus quote columns. **Deferred:** intake envelope / Packet B → Chip 5; recognition event ledger → Chip 3.

## 1. Approach

Encode the workbook-verified revenue model (SSoT §5/§5a) as the quote layer on the Chip 1 identity skeleton. **Per-project hours are first-class** (operator, 2026-06-15): the catalog is a *default*, never a constraint; the binding `hrs_per_unit` lives on the quote **line** and is overridable per project. The accounting identities are enforced by **generated columns** + a roll-up **trigger** wherever possible, so the model can't drift.

## 2. Schema (migration `002_quote_model.sql`)

- **`ops.test_standard`** enum — `'ATS'`, `'MTS'` (acceptance vs maintenance).

- **`ops.standard_hours`** — universal **DEFAULT** catalog (a Resources-lane candidate; lives in `ops` for now):
  `apparatus_type` · `test_standard` · `default_hours` (not null) · `neta_section` · `category` · audit. **`UNIQUE(apparatus_type, test_standard)`**. Reference/seed only — it never binds a quote.

- **`ops.scope_quote_line`** — the Estimator line + **home of per-project hours**:
  `scope_id` FK→`ops.scopes` · `apparatus_type` · `test_standard` · `qty` (not null) · **`hrs_per_unit`** (not null; seeded from the catalog default, **overridable per project**) · `line_hours` **GENERATED** = `qty × hrs_per_unit` · `catalog_default_hours` (the seed, for override provenance) · `designation` · `line_number` · provenance.

- **`ops.scope_quote`** — 1:1 with scope, **frozen at PM approval**. Inputs: the **4 categories** `onsite_labor`/`offsite_labor`/`travel`/`outside_services` · `unit_multiplier` (M4) · `pct_adjust` (N4) · `total_quoted_hours` (J3, maintained by trigger). **GENERATED**: `unadjusted_total` (P3 = Σ 4 categories) · `adjusted_total` (P4 = (Σ4)·M4·N4) · `blended_rate` = `P4 / NULLIF(J3,0)`. Plus `is_frozen` · `frozen_at`.

- **`ops.apparatus` +=** `quoted_hours` (inherited from its line, frozen) · `quoted_revenue` (frozen snapshot, populated at approval) · `quote_line_id` (FK→`scope_quote_line`, provenance).

- **`ops.v_apparatus_quote`** — view: live `quoted_revenue` = `apparatus.quoted_hours × scope_quote.blended_rate` (joined on scope). The serving/verification surface.

- **Trigger** `ops.maintain_scope_quote_hours()` — on `scope_quote_line` ins/upd/del, set `scope_quote.total_quoted_hours = Σ line_hours` for the scope (keeps J3 — and thus the blended rate — consistent as the estimator edits lines).

## 3. Laws (SSoT §4)

- **Law 3 firewall** holds — only **quoted** ($ frozen) values here; recognized revenue is the Chip 3 event ledger.
- **Per-project hours** first-class; catalog = default (the operator ruling).
- Generated columns enforce the accounting: `line_hours = qty·hrs_per_unit` · `P3 = Σ 4 categories` · `P4 = P3·M4·N4` · `blended = P4/J3`.

## 4. TDD (`test_002_quote_model.py`, on `ops_dev`, built atop 001)

1. tables + `test_standard` enum + apparatus quote columns + view exist.
2. `line_hours` generated correct (qty×hrs).
3. `scope_quote` generated correct: P3 = Σ4cats, P4 = P3·M4·N4, blended = P4/J3.
4. **J3 trigger:** insert a line → `scope_quote.total_quoted_hours` updates to Σ line_hours.
5. **catalog default ≠ binding:** overriding a line's `hrs_per_unit` leaves the `standard_hours` row unchanged.
6. **view identity:** a consistent scope (lines + exploded apparatus + scope_quote) → Σ `v_apparatus_quote.quoted_revenue` per scope = P4.
7. **reversibility:** `002` down → Chip 2 objects gone **but Chip 1 intact** (`ops.apparatus`/`ops.projects` present) → `002` up → back.

## 5. Deferred (explicit)

Intake envelope (Packet B) → Chip 5 · recognition event ledger + apparatus `quoted_revenue` freeze-population → Chip 3 · `standard_hours` → Resources migration when that lane materializes · catalog **seeding** (from `tblEquipment` / `public.apparatus_types`) → a follow-up/intake step.
