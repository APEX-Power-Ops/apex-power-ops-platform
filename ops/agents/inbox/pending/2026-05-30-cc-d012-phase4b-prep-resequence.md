---
dispatch_id: 2026-05-30-cc-d012-phase4b-prep-resequence
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-d012-phase4b-drop-backcompat
closeout: ops/agents/handoffs/2026-05-30-d012-phase4b-prep-resequence-closeout.md
---

# Decision-012 Phase 4b PREP — clear shared-sequence couplings before the drop (REVERSIBLE)

**Lane:** Decision-012, Phase 4b prep. The 4b terminal-drop dry-run correctly **failed under `RESTRICT`** (prod untouched): `public.tcc_etu_sensor_maint_pre_rebuild` (a SAFE-TO-DROP table) **owns** `public.tcc_etu_sensor_maint_id_seq`, and the **canonical** `tcc.etu_sensor_maint.id` default still depends on that same sequence — so the drop would orphan the canonical default. There may be **more** such couplings (any canonical `tcc.*` whose id default points at a sequence owned by a SAFE-TO-DROP `_pre_rebuild` table). This dispatch **characterizes ALL of them and reassigns the sequences to their canonical owners** — a reversible change — then **re-proves the 4b drop dry-run is clean**. **No drops in this dispatch.** Follow the inbox lifecycle (claim-push BEFORE running).

## Execute (gated)

1. **Claim** (`git mv` pending→claimed, push) BEFORE running.

2. **Characterize ALL sequence couplings (read-only; report the full map).** For EACH of the 11 drop-set tables (10 SAFE-TO-DROP `_pre_rebuild` — `gfd_equations`, `inst_curves`, `ltd_params`, `ltpu_multipliers`, `plugs`, `sensor_maint`, `sensor_params`, `settings`, `std_equations`, `stpu_overrides` — plus `tcc_etu_sensor_maint_v2`):
   - List every sequence **OWNED BY** any of its columns (`pg_depend` deptype `a` from `pg_class` seq → table column).
   - For each owned sequence, list every OTHER column whose DEFAULT references it (scan `pg_attrdef`/`pg_get_expr` + `pg_depend`), flagging any that belongs to a **KEPT** object (canonical `tcc.*`, MUST-KEEP `_pre_rebuild`, `tcc_test_plans`, anything not in the drop-set).
   - **Coupling = a sequence owned by a drop-set table that a KEPT column default depends on.** Produce the table: `sequence | owned-by (drop-set) | kept dependents`. (Also note the reverse — a drop-set table whose id default points at a KEPT-owned sequence — as informational; that's not a blocker.)

3. **Author the reversible prep migration** `infra/database/migrations/tcc/003_phase4b_prep_resequence.sql` (UP) + `003_phase4b_prep_resequence_down.sql` (DOWN). For EACH coupling:
   - **Required:** `ALTER SEQUENCE <seq> OWNED BY <canonical_kept_column>;` (detaches ownership from the drop-set table so the later drop won't cascade the sequence).
   - **Cleanup (recommended, since we're unifying):** `ALTER SEQUENCE <seq> SET SCHEMA tcc;` and rename to the dropped-prefix form (e.g. `tcc_etu_sensor_maint_id_seq` → `tcc.etu_sensor_maint_id_seq`) IF it moves cleanly. Verify the canonical default still resolves after the move (nextval defaults rebind by OID — confirm via `pg_get_expr`/an insert-test in the dry-run).
   - DOWN reverses ownership + schema/rename. One transaction; guards (assert each sequence ends owned by the canonical column).

4. **Dry-run the prep** (`BEGIN` → apply UP → verify each sequence reassigned + canonical defaults intact → `ROLLBACK`).

5. **Apply the prep** (commit the 2 migration files, apply UP with `COMMIT`). Prep changes ONLY sequence ownership/schema → no row/behavior change.

6. **Re-prove the 4b drop is now clean (DRY-RUN ONLY — do NOT commit a drop).** Author the drop SQL locally (same set as the stopped 4b attempt: 60 views + 10 SAFE `_pre_rebuild` + `tcc_etu_sensor_maint_v2`, `RESTRICT`), run it as `BEGIN` → apply → catalog-check → `ROLLBACK`. **Confirm it now passes RESTRICT with ZERO errors and must-keep intact.** Discard the local drop artifact — the terminal drop is a separate dispatch (`004`). If the drop dry-run surfaces YET ANOTHER blocker, STOP and report it (do not force).

7. **Post-prep gate (behavior identical — only sequence metadata changed):** ETU parity 3/0; relay parity 6/6; breaker `catalog/status` 200 `{63,17831}`; `settings/29442` + `context/29442` 200; relay `sections` 200.

## Guardrails
- **Sequence reassignment ONLY (reversible).** NO `DROP` of any view/table in this dispatch. No row changes, no app changes, no MUST-KEEP table changes.
- DSN out-of-band; no `.env*` contents. Scoped `git add` (the 2 prep migration files + closeout).

## Closeout
Record: the full coupling map (every sequence owned by a drop-set table + its kept dependents), the prep UP/DOWN authored, dry-run + apply results, the **confirmation that the 4b drop dry-run now passes clean under RESTRICT**, the post-prep gate table, and any new blocker found. Then `git mv` claimed→done, commit, push, return to Desktop. **Next = the terminal 4b drop re-run (`004_phase4b_drop_backcompat`), gated, with Desktop's go/no-go.**
