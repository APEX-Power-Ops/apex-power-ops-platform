---
dispatch_id: 2026-05-31-cc-tcc-tol-sc1-guided-cascade
target: CC
priority: 1
from: Desktop
created_at: 2026-05-31
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-05-31-tcc-tol-sc1-guided-cascade-closeout.md
---

# SC1 — Guided ETU cascade (consume `/cascade`) so a tech pinpoints + confirms the exact trip unit

**Lane:** TCC Field Tolerances MVP — **Selection Confirmation** (the core lane). **Spec of record:** `apps/operations-web/TCC_FIELD_TOLERANCES_MVP_SPEC_2026-05-31.md` (read the `UPDATE` section — the DB tolerances are authoritative; the work is letting a tech land on + confirm the RIGHT unit). **Frontend-led (operations-web); the backend route already exists; reversible; parity-gated.** Follow the inbox lifecycle (claim-push before editing). Independent of the route-delay-fields dispatch (different files) — a dual-executor lane.

## Why
Today operations-web selects ETU trip units by **free-text search** (`/etu/search`) + breaker-manufacturer filter — which makes it hard to "zero in" on the exact trip unit. The backend already exposes a **guided cascade** (`GET /api/v1/neta/cascade`: manufacturer → trip type → trip style → sensor, cross-filtered, with a plug-value lens) that operations-web does NOT consume. Wiring it gives the EasyPower-style drill-down that lets a tech confirm the exact unit before reading its (DB-authoritative) tolerances.

## Do
1. **Claim** (git mv pending→claimed, push) before editing.
2. **Add a cascade client** to `apps/operations-web/lib/breaker-resources.ts` (`fetchCascade`) calling `GET /api/v1/neta/cascade` with the cascade params it accepts (verify the live contract first: manufacturer_id / trip_type_id / trip_style_id / sensor_id selectors + the returned cross-filtered option lists + plug_values). Add the response types.
3. **Add a guided cascade UI** in the ETU path of `breaker-resource-explorer.tsx`: progressive dropdowns Manufacturer → Trip Type → Trip Style → Sensor, each populated from the cascade's cross-filtered option lists (selecting one narrows the others). Keep the existing free-text `/etu/search` available as a secondary/fallback, but make the **guided cascade the primary ETU selection path**. On final selection, hand the chosen `sensor_id` (+ plug) into the existing context/settings/plot flow unchanged.
4. **Fold in B1.2 — the "0 MATCHES" display fix:** the Axis-1 breaker count renders as `${breakerAxis?.count ?? 0}` (~`breaker-resource-explorer.tsx:540`), masking a null/failed fetch as a real "0 matches". Render "—"/"loading"/"unavailable" when the fetch is null/pending instead of `?? 0`.
5. **Selection-confirmation surface (light, SC2 seed):** on the loaded selection, surface the distinguishing attributes already available (manufacturer, trip type, trip style, `tcc_number` if present, sensor desc/rating, compatible plug values) near the loaded panel so a tech can match the screen to the nameplate. (No new backend.)

## Acceptance
- The ETU path offers a working guided cascade: picking a manufacturer narrows trip types; trip type narrows styles; style narrows sensors; cross-filters reflect the live `/cascade` option lists. Final selection loads context/settings/plot as before.
- "0 MATCHES" no longer shows when the breaker-axis fetch is null/failed (only a real 0 shows 0).
- The loaded selection shows the confirm attributes (tcc_number/style/sensor/plugs).
- No regression: operations-web typecheck + build pass; breaker Playwright smoke passes (extend it to assert the cascade drill-down drives a load); ETU SQL parity 3/0, catalog 63/17831 unaffected (no backend change).

## Guardrails
- **Frontend composition + a read-only cascade client only.** No backend route changes, no DDL, no schema. The tolerance values are DB-authoritative (do not recompute client-side). Scoped `git add` (the listed files + smoke + closeout). DSN out-of-band; no `.env*` contents. PUBLIC repo — no client/job identifiers.

## Closeout
Record: the `/cascade` contract used, the cascade UI flow, the B1.2 fix, the confirm-attributes surfaced, local test results, commit hash(es), Vercel deploy confirmation, and the post-deploy check (cascade drill-down works hosted). Then `git mv` claimed→done, commit, push. **Next in this lane:** SC3 (terminology normalization — design pending operator input) and B2.1 (the tolerance sheet).
