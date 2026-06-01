# Closeout: LV Breaker TCC live-wiring lane (Stages A–B + dual-axis backend)

Date: 2026-06-01
Lane: TCC LV Breaker MVP → the field-tolerance product
Status: **Stages A + B (ETU) + dual-axis backend SHIPPED + verified live on prod.** Dual-axis frontend + Stage C remain.
Predecessor: `2026-06-01-codex-lvbreakertcc-wiring-scoping` (`WIRING_SCOPING.md`) + the D1 SST-bridge recovery (STATE §104).

This is the authoritative record of the live-wiring build. The reference guides (G0–G4/00) and STATE/memory summarize from here.

## What shipped (all `apex-power-ops-platform` `main`; each smoke-tested on prod)

| Slice | Commit | What |
|---|---|---|
| **A0** | `b9520af6` | `GET /etu/bridge-sensors` — breaker style → compatible ETU sensor set over `tcc.vw_breaker_sst_bridge`; 3 unit tests |
| **A1** | `5f60eb32` | `/lvbreakertcc` Screen 1 **LIVE** — family-dispatched selection (ETU bridge-narrow · TMT · EMT); full 3-family fetch layer already existed in `lib/breaker-resources.ts` |
| **A-fix** | `2af6c077` | `bridge_only` param on `/etu/breaker-cascade` — ETU tab shows only ETU-capable breakers (MCCB 640→130); "Breaker Style" relabeled "Frame Size" (it is `s.frame`) |
| **collision** | `fda37944` | `/etu/bridge-sensors` cross-class id collision fixed (`breaker_class` disambiguation) — **operator-caught** |
| **Stage B** | `f4e6a227` | Screen 2 **LIVE** for ETU — editable settings (`/settings`) → `POST /calculate` → DB-authoritative NETA tolerance bands; measured %Error + PASS/FAIL vs live limits; per-row G4 trust labels |
| **bridge_xfilter** | `05fe82f8` | bridge-aware **bidirectional** cross-filter (opt-in) on `/cascade` + `/etu/breaker-cascade` — replaces manufacturer-only (130→1 / 1562→4) |

## Live verification (prod: `control.apexpowerops.com` + `operations.apexpowerops.com`)
- `/etu/bridge-sensors?breaker_style_id=311&breaker_class=ICCB` → 5 ABB PR332/P sensors (`T8V-1600`).
- `bridge_only`: MCCB **640 → 130** ETU-capable breakers; all-class `{ICCB:27, MCCB:130, PCB:97}`.
- collision: style `1510` → **3 DT 510 R-Frame (MCCB) only**, not the 13 with the foreign PCB MPS-C-2000 bleed-in.
- Stage B: LTPU 0.9×1000 → 900 A test, band **945–1080** (DB-authoritative); STPU/INST likewise.
- `bridge_xfilter`: breaker→trip **130 trip styles → 1**; trip→breaker **1562 breakers → 4**.

## Key findings (propagated to the guides)
1. **Per-class serial-id OVERLAP hazard.** `brk_{iccb,mccb,pcb}` and their `*_styles` use independent per-class serial ids that **collide** (style `1510` is both an MCCB *DT 510* and a PCB *MPS-C-2000*). The real key is the **`(class, id)` pair**. Now applied in `bridge_only`, `/etu/bridge-sensors`, and `bridge_xfilter`. → **G1 hazard note.**
2. **The cross-filter fix is SHIPPED** (was `[DEFERRED]` / "proposed"): bridge-aware **bidirectional** cross-filter (`bridge_xfilter`), opt-in so the explorer's manufacturer-only behavior is untouched. → **G2 BG-5, G3 A3, 00.**
3. **Field-trust on the LV page (G4).** Pickup bands (LTPU/STPU/INST/GFPU) = DB-authoritative per-sensor tolerances (field-safe, "DB" badge); delay rows (LTD/STD/GFD) flagged **"verify"** pending the delay-band route fix (the route still conflates the selected band with the NETA test multiplier).

## Residuals / next
- **Dual-axis FRONTEND** (the visible payoff; task #25): add the trip-unit axis to the ETU selector, **co-equal**, both axes passing `bridge_xfilter` so each narrows the other; sensor reachable from either end. (Operator decision 2026-06-01: co-equal.)
- **TMT/EMT Screen 2** — bounded settings/context display (G4: bounded surfaces).
- **Stage C** — live per-family curve (`/plot-tcc`) + the `route_delay_curve` engine patch (promotes delay rows from "verify" → "DB").
- **D4** (`TMT_*` helper cols) still open — now a trivial `source_id`-join.
- **Pre-existing test failure** — `test_etu_search_count_query_reuses_plug_join_and_scope_filters` (stale exact-param-dict assertion, doesn't account for `q_exact`/`q_prefix`); reproduces on clean `f4e6a227`, **NOT from this lane**. Needs a 1-line test fix.

## Boundaries honored
Read-only against governed Supabase (the D1 write was a prior-session authorized write). No secrets / client / job identifiers in this PUBLIC repo. Scoped `git add`. `tsc --noEmit` + `next build` green each deploy; pytest green except the noted pre-existing failure.
