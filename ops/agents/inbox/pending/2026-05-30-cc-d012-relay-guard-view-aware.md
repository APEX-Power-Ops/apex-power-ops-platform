---
dispatch_id: 2026-05-30-cc-d012-relay-guard-view-aware
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-d012-phase2-expand-retry
closeout: ops/agents/handoffs/2026-05-30-d012-relay-guard-view-aware-closeout.md
---

# Decision-012 Phase 2 enabler — make the relay catalog guard VIEW-AWARE (unblocks back-compat views)

**Lane:** Decision-012, Phase-2 enabler. **Operator-authorized per-phase.** Code-only change to the hosted control-plane + a Render deploy + a non-regression verify. **No DB DDL in this dispatch.** Follow the inbox lifecycle (claim-push BEFORE editing).

## Why (what the EXPAND retry caught)
The Phase-2 EXPAND retry (`2026-05-30-cc-d012-phase2-expand-retry`) committed clean, but the post-commit gate found relay routes returning `503 relay catalog unavailable`, so DOWN was run and prod fully restored. Root cause: the relay guard `_relay_work_schema_tables_available` in `apps/control-plane-api/services/neta/router.py` (≈lines 336-346) checks existence with:
```python
existing = set(inspector.get_table_names(schema="work"))
return all(table in existing for table in _RELAY_WORK_SCHEMA_TABLES)
```
**SQLAlchemy's `Inspector.get_table_names()` excludes views.** EXPAND turns `work.tcc_relay_*` into back-compat **views** (the base tables move to `tcc.*`), so the guard sees 0 relay tables → 503. This patch makes the guard count views too, so the back-compat-view strategy works for relay. It is **non-regressive today** (base tables still satisfy it) and **forward-correct** (views satisfy it after EXPAND).

## Execute (gated)

1. **Claim** (`git mv` pending→claimed, commit, push) BEFORE editing.

2. **Blast-radius characterization FIRST (report in closeout):** grep the control-plane for any OTHER schema-introspection existence guards that the back-compat-view strategy could also trip — e.g. `get_table_names`, `has_table(`, `information_schema.tables` with `table_type = 'BASE TABLE'`, `pg_tables` (which also excludes views), `relkind = 'r'`. List every hit with file:line and whether it gates a breaker or relay route. **If you find another base-table-only guard on a route path, STOP and report it** (we'd rather fold its fix in here than discover it as a third gate failure during the EXPAND re-run).

3. **Patch** `_relay_work_schema_tables_available` to union views into the existence set:
   ```python
   existing = set(inspector.get_table_names(schema="work")) | set(inspector.get_view_names(schema="work"))
   return all(table in existing for table in _RELAY_WORK_SCHEMA_TABLES)
   ```
   Keep the `"work" not in schemas` short-circuit and the `except Exception: return False` exactly as-is. Minimal diff — no behavior change beyond counting views.

4. **Test:** add/extend a focused unit test (mock or fake inspector is fine — no live DB needed) proving the guard returns `True` when the relay names are present **only as views** (`get_table_names` → [], `get_view_names` → the relay names), and still `True` when present as base tables, and `False` when neither. Run the control-plane test subset that covers this; report pass counts.

5. **Commit + push** (scoped `git add` of `router.py` + the test file only — do NOT touch the migration SQL, which is already committed). Push to `main` → Render autoDeploys the control-plane.

6. **Non-regression verify against the LIVE hosted control-plane (pre-EXPAND, base tables still in place)** — confirm the patch changed nothing while base tables are present:
   - `scripts/probe_live_etu_sql_parity.py` → PASS 3/0.
   - `scripts/probe_live_relay_sql_parity.py` → PASS 6/6.
   - `GET https://control.apexpowerops.com/api/v1/neta/catalog/status` → 200, `{63, 17831}`.
   - `GET https://control.apexpowerops.com/api/v1/neta/relay/sections` → 200, real rows.
   Wait for the Render deploy to land before running these (poll the route until the new build is live). All must stay green.

## Guardrails
- **Code + deploy + verify ONLY.** No DB DDL, no EXPAND re-run (that's the next dispatch), no route SQL repoint (Phase 3), no view/`_pre_rebuild` drops (Phase 4).
- Scoped `git add` (router.py + test). DSN out-of-band; no `.env*` contents.
- The view-case is proven on prod only when EXPAND re-runs; here we prove the logic via unit test + prove non-regression on the live base-table state.

## Closeout
Record: the blast-radius grep results (every introspection guard found + breaker/relay/route disposition), the diff applied, test result, commit hash, Render deploy confirmation, and the 4 live non-regression checks. Then `git mv` claimed→done, commit, push, return to Desktop. **Next after this:** re-dispatch the EXPAND retry — with a view-aware guard live, the post-commit gate's relay checks should pass.
