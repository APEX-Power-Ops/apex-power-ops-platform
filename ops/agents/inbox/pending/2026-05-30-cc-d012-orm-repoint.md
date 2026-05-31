---
dispatch_id: 2026-05-30-cc-d012-orm-repoint
target: CC
priority: 1
from: Desktop
created_at: 2026-05-31
authority: gated
predecessor: 2026-05-30-cc-d012-phase4b-drop-final
closeout: ops/agents/handoffs/2026-05-30-d012-orm-repoint-closeout.md
---

# Decision-012 — repoint the SQLAlchemy ORM models `tcc_*` → `tcc.*` (closes the Phase-3 gap the drop exposed)

**Lane:** Decision-012, consumer-repoint completion. The Phase-4b terminal drop succeeded (catalog physically unified) but exposed a surface Phase 3 missed: the **SQLAlchemy ORM models** in `apps/control-plane-api/models/` declare **bare old names** (`__tablename__ = 'tcc_etu_sensors'`, `ForeignKey('tcc_etu_sensors.id')`) that resolved to the back-compat views until they were dropped. Result: ETU `/evaluate` curve-generation returns `relation "tcc_etu_sensors" does not exist` (graceful warning; sensors 25/26/17892). **CODE-ONLY change — no DB DDL.** Reversible (revert commit). Parity-gated. Follow the inbox lifecycle (claim-push BEFORE editing).

## Scope — every ORM model declaring a bare old TCC name → `tcc.*` schema-qualified
Files (confirmed via grep at `8a3f1619`): `models/breakers.py`, `models/etu_bands.py`, `models/etu_core.py`, `models/etu_curves.py`, `models/etu_equations.py`, `models/etu_pickups.py`, `models/reference.py`, `models/tmt.py`. (31 models; breaker/ETU/TMT/manufacturers/trip. **No relay ORM** — relay is raw-SQL only; leave `models/work.py`/`work_enums.py` unless they reference an old TCC catalog name. **No EMT ORM.**)

For EACH model whose `__tablename__` is a bare old TCC name (`tcc_brk_*`, `tcc_emt*` if any, `tcc_etu_*`, `tcc_manufacturers`, `tcc_tmt_*`, `tcc_trip_*`):
1. **`__tablename__`**: drop the `tcc_` prefix → the bare table name (e.g. `'tcc_etu_sensors'` → `'etu_sensors'`).
2. **Schema**: add `'schema': 'tcc'` to `__table_args__`. If `__table_args__` is absent, add `__table_args__ = {'schema': 'tcc'}`. If it's a dict, add the key. If it's a tuple (constraints/indexes), append a trailing dict `{'schema': 'tcc'}` (SQLAlchemy form) or merge into an existing trailing dict.
3. **`ForeignKey('tcc_X.col')`** → **`ForeignKey('tcc.X.col')`** (schema-qualified, prefix dropped) — e.g. `ForeignKey('tcc_etu_sensors.id')` → `ForeignKey('tcc.etu_sensors.id')`.
4. **Check `relationship(...)`, `primaryjoin=`, `secondary=`, `remote_side=`** for any bare old-name string references → qualify the same way.

Consistency: a schema-qualified `ForeignKey('tcc.etu_sensors.id')` requires the referenced model to also carry `__table_args__ = {'schema': 'tcc'}` — make sure every referenced model is repointed too (they all are in scope). SQLAlchemy resolves FK strings as `<schema>.<table>.<col>` when schema is set.

Also check `apps/control-plane-api/services/neta/schemas.py` (flagged with old-name tokens): if any are **live** references repoint them; if they are comments/docstrings, update for hygiene. **Do NOT touch** `apps/control-plane-api/migrations/*.py` (one-time historical transfer scripts, not runtime consumers) — but confirm they are not imported by the running app.

## Execute (gated)

1. **Claim** (`git mv` pending→claimed, push) BEFORE editing.

2. **Enumerate (report):** list every ORM model + its current `__tablename__`/FKs and the target. Confirm the full set (per-file). Confirm `models/work.py`/`work_enums.py` carry no old TCC catalog names (relay is raw-SQL). Confirm `migrations/*.py` are not runtime-imported.

3. **Repoint** all in-scope models + any live `schemas.py` refs. Mechanical, schema-qualification only — no logic change.

4. **Local validation:** run the control-plane test suite subset covering ETU/breaker/TMT + any ORM/curve-generation tests; report pass counts. Confirm the app imports cleanly (SQLAlchemy metadata resolves all FKs across the `tcc` schema — a mapper-configuration error will surface at import/`configure_mappers`).

5. **Commit + push** (scoped `git add` of `models/*.py` + any `schemas.py` + closeout). Render autodeploys.

6. **Post-deploy gate — the regression must clear:**
   - `scripts/probe_live_etu_sql_parity.py` → **PASS 3/0 with evaluate warnings = 0** (the 3 curve-gen warnings gone).
   - Re-check the 3 affected sensors (25, 26, 17892): ETU evaluate/curve-generation returns curves, no `UndefinedTable`.
   - Full regression: breaker `catalog/status` 63/17831; `etu/search` + `tmt/facets` + `emt/facets` 200; `settings/29442` + `context/29442` + `etu/breaker-cascade?sensor_id=29442` 200 (29442 still `531/NA`); relay parity 6/6 + `relay/sections` 200.
   - **Any FAIL → `git revert` the repoint commit, push, report** (code-only; DB untouched).

## Guardrails
- **ORM/app code ONLY.** No DB DDL, no view recreation, no migration SQL. Schema-qualification only (no model logic changes).
- Scoped `git add` (`models/*.py` + `schemas.py` if edited + closeout). DSN out-of-band; no `.env*` contents.

## Closeout
Record: the per-file ORM enumeration + repoint, local test result (incl. clean mapper configuration), commit hash, Render deploy confirmation, the post-deploy gate table (esp. ETU evaluate warnings now 0 + the 3 sensors fixed), and whether a revert was needed. Then `git mv` claimed→done, commit, push, return to Desktop. **On PASS, Decision-012 is COMPLETE end-to-end — catalog physically unified in `tcc.*` AND every consumer surface (raw SQL + ORM) repointed; no references to the retired old names remain.**
