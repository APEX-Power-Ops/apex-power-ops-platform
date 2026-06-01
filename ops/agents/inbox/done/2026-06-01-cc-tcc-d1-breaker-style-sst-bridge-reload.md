---
dispatch_id: 2026-06-01-cc-tcc-d1-breaker-style-sst-bridge-reload
target: CC
priority: 1
from: Desktop
created_at: 2026-06-01
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-06-01-tcc-d1-breaker-style-sst-bridge-reload-closeout.md
---

# D1 — Recover the breaker→ETU SST bridge: reload `brk_*_styles` (4 dropped cols + source_id + remap), then the bridge surface

**Lane:** TCC Master Reference — the **first big buildable** off the spec (the SST-bridge fix). **Cite + fix the guides first (SSoT Law).** Spec of record: `reference/tcc/G0-TRIP-FAMILY-MODEL.md` §3 (the bridge mechanism), `reference/tcc/G1-SCHEMA-GUIDE.md` §5 **D1** (dropped-column register) + §4.6, `reference/tcc/G2-RULES-GUIDE.md` **§3.2 BG-1..BG-5** (acceptance gates) + **§4.3** (the governance entry), `reference/tcc/G3-ROUTING-GUIDE.md` (the cascade + `GetDefaultTripInfo` stitch). Cross-vendor-validated by ETAP "Case 1" (G0/00 `[ETAPDOC]`). **Prod-schema, multi-phase, reversible-until-cutover — gated; expect per-phase confirmation.**

## Why (the recovered finding)
The breaker→ETU **SST bridge** — `BreakerXXXStyles.TMT_Use_SST` (gate) + `TMT_SST_{Mfr,Type,Style}` (name-composite) → `DatStyle(TYPE,STYLE)` → `STYLE_ID` → `DatSensor.StyleID` — is **app-code stitch** (`DevLibBreakerStyle.GetBreakerStyles` → `GetDefaultTripInfo`, INV-6), and its 4 source columns were **dropped at the Access→Supabase load** (a loader expecting a numeric `Manufacturers.ID` discarded the name-key). **Live-confirmed 2026-06-01:** `tcc.brk_{mccb,iccb,pcb}_styles` carry **none** of `tmt_use_sst/tmt_sst_mfr/tmt_sst_type/tmt_sst_style`; Access `BreakerMCCBStyles` has them populated (`TMT_Use_SST=1` on **1,680** MCCB styles, e.g. `ABB/PR212/MCCB`). **Impact:** the deployed explorer cross-filters **manufacturer-axis only** — it can't collapse 7,271 breaker styles to the compatible-sensor set (offers ~117 ABB trips instead of the 1 correct trip; `T8V-1600` should narrow to ABB PR332/P → 5 sensors). This blocks the field-tolerance MVP's breaker→compatible-sensor narrowing (G2 BG-5).

**Entangled residual (from the §103 breaker-parent reload):** `tcc.brk_mccb_styles` has **41 distinct orphan `breaker_id`** (`273,274,294,…,608`) that don't join to `tcc.brk_mccb`. These are the *gap* ids in the re-sequenced parent surrogate — the originally-dropped AC/DC twins that the parent reload re-inserted under **new** ids, leaving the styles pointing at the old gaps. **Fix it in the same reload** (a deliberate source-ID → parent-surrogate remap), per the §103 residual note.

## Phases (A–C this packet; D is a separate gated follow-on)
1. **Claim** (git mv pending→claimed, push) before starting.

2. **Phase A — reload `brk_*_styles` from Access (the foundational fix).** For each of `brk_{mccb,iccb,pcb}_styles`, re-load from Access `Breaker{MCCB,ICCB,PCB}Styles` (read-only, ACE.OLEDB.16.0, `D:\TCC_NEW.accdb`) so each tcc style row carries:
   - **`source_id`** = Access `BreakerXXXStyles.ID` (NEW — a stable join key; the current tables have none, which is *why* a clean re-carry/remap is otherwise impossible).
   - the **4 SST-bridge cols** `tmt_use_sst`, `tmt_sst_mfr`, `tmt_sst_type`, `tmt_sst_style` (source-faithful).
   - a **correctly-mapped `breaker_id`** → the canonical `tcc.brk_*` parent surrogate, resolved by the breaker natural key (`manufacturer_id, name(=Type), standard, ac_dc_code`) against the **post-§103 reloaded parents** (640/29/157) — this resolves the 41 orphans.
   - **Approach decision (recommend):** a fresh source-faithful reload keyed on `source_id` is cleaner than an in-place `ALTER ADD COLUMN + UPDATE`, because it fixes the dropped cols + the orphan remap + establishes `source_id` in one pass. Migration `006_brk_styles_sst_bridge_reload.sql`; reversible (keep the pre-reload rows or a down that restores the prior projection). **Preserve any FK'd surrogate ids** that downstream consumers depend on (check `vw_trip_unit_cascade` + router.py before re-keying).
   - **Verify:** style counts unchanged (10,335 / 608 / 3,279); 0 orphan `breaker_id` across all 3; `tmt_use_sst=1` count = 1,680 (mccb) and the iccb/pcb equivalents; the 4 cols non-null where Access has them.

3. **Phase B — fold the orphan remap into Phase A** (above) — there is no separate step; the natural-key `breaker_id` mapping in the reload *is* the orphan fix. Just confirm 0 orphans post-reload on all 3 style tables.

4. **Phase C — the BG-4 dedicated bridge surface.** Build a joinable surface (e.g. `tcc.vw_breaker_sst_bridge` / `vw_etu_breaker_contract_bridge`) that realizes the stitch: `brk_*_styles` (where `tmt_use_sst=1`) `tmt_sst_{mfr,type,style}` → `tcc.trip_styles`(TYPE,STYLE) → `style_id` → `tcc.etu_sensors.style_id`, exposing `(breaker class, breaker_id, breaker_style source_id) → compatible sensor_id set`. **Do NOT overload `vw_trip_unit_cascade`** (19 cols, all trip-unit-side, zero breaker-style cols — BG-4 requires a *new* surface). **Verify** match-rates vs Access live-join (target ICCB ~100% / MCCB ~95.6% / PCB ~97.5%; unmatched = genuine catalog gaps, not load loss) and the `T8V-1600 → ABB PR332/P → 5 sensors` worked example.

5. **Guides first (SSoT Law):** G1 §5 D1 → CLOSED (cols re-carried + `source_id` added) + §4.6 orphan note closed; G2 §3.2 BG-3/BG-4 → met, §4.3 status → recovered; G0 §3 (the live bridge surface name); 00 open-validation register. G3 §A (the cross-filter narrowing now has a surface).

## Decision points (surface in the closeout; default to the recommended call)
- **Reload vs in-place ALTER** for the 4 cols — *recommend reload-with-`source_id`* (fixes cols + orphans + key in one pass). If any surrogate `id` is FK'd by a consumer, preserve it (upsert by `source_id`, don't renumber).
- **`tmt_sst_mfr` storage** — keep the source-faithful **name** string (the stitch is name-keyed via `tcc.trip_styles`/manufacturer-alias); do NOT coerce to a numeric FK (that coercion is the original D1 bug).
- **Bridge surface as a view vs materialized** — start as a plain view (counts are small); measure before materializing (mirror the G2 AG-3 "no invented targets" rule).

## Acceptance (Phases A–C)
- `tcc.brk_*_styles` carry `source_id` + the 4 `tmt_sst_*` cols (source-faithful); **0 orphan `breaker_id`** on all 3; counts 10,335/608/3,279 unchanged; `tmt_use_sst=1`=1,680 mccb.
- The bridge surface returns the compatible-sensor set for a breaker style; `T8V-1600`→ABB PR332/P→5 sensors; live match-rates ≈ ICCB 100 / MCCB 95.6 / PCB 97.5%.
- Guides updated per SSoT Law (G1 D1/§4.6 CLOSED, G2 BG-3/BG-4/§4.3, G0 §3, 00). No regression: ETU/relay live SQL parity PASS; the deployed explorer unchanged (Phase C adds a surface, doesn't wire UX yet).

## Phase D — the cross-filter UX (BG-5) = SEPARATE GATED FOLLOW-ON
Wiring the explorer to narrow breaker-style → compatible sensors (beyond manufacturer-axis) is **BG-5**, a UX change on `operations-web` — author it as its own packet AFTER A–C verify, so the data/schema foundation is proven before the surface is consumed. Do NOT bundle it here.

## Guardrails
- **Authorized governed-Supabase write** (migration + reload) — this is the SST-bridge remediation. Access opened **read-only**. Governed `tcc.*` posture = public-read/service-write (G2 §4.7); writes via migration/service-role. Scoped `git add`. DSN/keys out-of-band; no `.env*` contents; PUBLIC repo — no client/job identifiers, no project ref/keys in the trail. **Reversible until any cutover; per-phase confirmation expected.**

## Closeout
Record: the reload migration, `source_id` strategy, the 4-col + orphan-remap verification (0 orphans, counts, `tmt_use_sst=1`), the bridge surface definition + match-rates + the `T8V-1600` worked example, the guide sections amended, tests/parity, commit hash(es). Then `git mv` claimed→done, commit, push. **Next:** Phase D (BG-5 cross-filter UX) packet.
