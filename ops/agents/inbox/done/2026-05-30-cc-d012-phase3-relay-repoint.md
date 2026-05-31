---
dispatch_id: 2026-05-30-cc-d012-phase3-relay-repoint
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-d012-phase3-breaker-repoint
closeout: ops/agents/handoffs/2026-05-30-d012-phase3-relay-repoint-closeout.md
---

# Decision-012 Phase 3 (RELAY) — repoint relay SQL `work.tcc_relay_*` → `tcc.*` + flip the guard to `tcc`

**Lane:** Decision-012, Phase 3, **relay half** (completes Phase 3; breaker half done `70c7127a`). **Operator-authorized.** The relay catalog tables now live in `tcc.*` (prefix dropped) with back-compat views at `work.tcc_relay_*`. This phase repoints the relay app SQL + the relay availability guard to `tcc.*`. **CODE-ONLY — no DB DDL.** Reversible by reverting the commit (DB untouched), parity-gated. Follow the inbox lifecycle (claim-push BEFORE editing).

## Scope — the 21 relay tables, `tcc_relay*`/`tcc_relays` → `tcc.relay*`/`tcc.relays`
Drop the `tcc_` prefix into schema `tcc`. The 21: `tcc_relays`, `tcc_relay_devices`, `tcc_relay_line_sections`, `tcc_relay_td_sections`, `tcc_relay_ranges`, `tcc_relay_discrete_values`, `tcc_relay_curves_{iec,swz,bsl,meq,pcd,lrm,rxd,egc,tcp}`, `tcc_relay_curve_rows_{iec,swz,bsl,meq,pcd}`, `tcc_relay_curve_points_tcp`.

Three edit kinds (all in `apps/control-plane-api/services/neta/router.py` + relay probes/tests):
1. **Route SQL (≈28 in router.py):** `work.tcc_relay_devices` → `tcc.relay_devices`, etc. (schema `work` → `tcc`, drop `tcc_` prefix).
2. **Guard table list `_RELAY_WORK_SCHEMA_TABLES` (router.py ~line 191):** entries `"tcc_relay_devices"` → `"relay_devices"`, `"tcc_relays"` → `"relays"`, etc. (these are the bare table names the guard checks within its schema).
3. **The guard itself `_relay_work_schema_tables_available` (router.py ~line 343):** flip `get_table_names(schema="work")` + `get_view_names(schema="work")` → **`schema="tcc"`**. (The `tcc.relay_*` are real base tables, so the view-union is now belt-and-suspenders — keep it; harmless.) Also update `_RELAY_CATALOG_UNAVAILABLE_DETAIL` (~line 202) wording away from "work-schema" → "tcc-schema". Optionally rename the constant `_RELAY_WORK_SCHEMA_TABLES` → `_RELAY_TCC_SCHEMA_TABLES` for clarity (cosmetic; keep all references consistent if you do).

Also check `_RELAY_ANALYTICAL_FAMILY_CONFIG` (~line 159) for any embedded table names and repoint if present (the curve-family config maps family_code → curve column sets; repoint only if it names tables).

### ⚠ ATOMICITY — guard + routes + list in ONE commit
The route SQL flip (`work.*` → `tcc.*`) and the guard schema flip (`work` → `tcc`) MUST land in the **same commit/deploy**. If a route queried `tcc.relay_*` while the guard still checked `work` (or vice-versa), a mid-deploy state would 503 or error. One atomic commit avoids any inconsistent window.

### DO NOT touch
- **Breaker tables** (already on `tcc.*` from `70c7127a`) — leave them.
- The relay back-compat views in `work` (Phase 4 drops them). No DB DDL here.

## Execute (gated)

1. **Claim** (`git mv` pending→claimed, commit, push) BEFORE editing.

2. **Enumerate first (report in closeout):** grep relay table tokens (`work.tcc_relay*`, bare `tcc_relay*`/`tcc_relays`) across router.py + relay probes (`scripts/probe_live_relay_sql_parity.py`, any relay helper) + relay tests; per-file counts. Confirm the guard list + guard schema + every route SQL site are all accounted for.

3. **Repoint** all three edit kinds + relay probes/tests, in ONE commit. Keep breaker refs untouched.

4. **Build/test local:** run the control-plane relay test subset + the view-aware-guard tests from `8fdc7fd7` (update those tests if they assert `schema="work"` — they should now assert `tcc`); report pass counts. Push to `main` → Render autoDeploys.

5. **Post-deploy parity-gate (relay SQL now hits `tcc.*` directly; behavior IDENTICAL):** wait for deploy (poll readiness), then against `https://control.apexpowerops.com`:
   - `scripts/probe_live_relay_sql_parity.py` → **PASS 6/6** (bsl/iec/meq/pcd/swz/tcp).
   - `GET /api/v1/neta/relay/sections?supported_only=true&limit=3` → 200, real rows.
   - a relay `context` + `settings` + `plot-tcc` round-trip on one section (e.g. pick a td_section_source_id from `sections`) → 200 with curve data.
   - breaker sanity (must be UNAFFECTED): `scripts/probe_live_etu_sql_parity.py` → 3/0; `GET /api/v1/neta/catalog/status` → 200 `{63,17831}`.
   - **Any FAIL → `git revert` the commit, push (restores `work.*` SQL + `work` guard over the still-present views), report.** Code-only; no DB action.

6. **Surface for Phase 4 (do NOT fix):** report any DB functions/views whose bodies reference old relay names (`work.tcc_relay_*`) — likely none (relay is the newer ladder, no known DB-function layer), but confirm via `pg_get_functiondef`/`pg_views`. This + the breaker Phase-4 list (`fn_calculate_test_currents`, `fn_sensor_available_settings`, `vw_trip_unit_cascade`→`tcc_manufacturers_pre_rebuild`) is the full Phase-4 DB-object prerequisite set.

## Guardrails
- **Relay app SQL + guard ONLY.** No breaker re-touch. No DB DDL, no view/function-body edits, no view drops (Phase 4). No migration SQL.
- Scoped `git add` (repointed app files + closeout). DSN out-of-band; no `.env*` contents.

## Closeout
Record: enumeration counts, the atomic diff summary (route SQL + guard list + guard schema + detail message + any probe/test), local test result, commit hash, Render deploy confirmation, the post-deploy parity-gate table (relay PASS + breaker-unaffected), whether a revert was needed, and the Phase-4 relay DB-object findings. Then `git mv` claimed→done, commit, push, return to Desktop. **On PASS, Phase 3 is COMPLETE — the entire app reads `tcc.*`; the old-name back-compat views (public + work) have no app consumers left.** Next lane = Phase 4 (repoint the DB function/view bodies, then drop the back-compat views + `_pre_rebuild`/`_v2`, gated + irreversible, after soak).
