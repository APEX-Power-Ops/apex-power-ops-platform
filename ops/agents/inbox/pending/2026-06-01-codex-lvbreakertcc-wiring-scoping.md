---
dispatch_id: 2026-06-01-codex-lvbreakertcc-wiring-scoping
target: CODEX
priority: 1
from: CC
created_at: 2026-06-01
authority: gated
predecessor: 2026-06-01-cc-tcc-d1-breaker-style-sst-bridge-reload
closeout: ops/agents/handoffs/2026-06-01-lvbreakertcc-wiring-scoping-closeout.md
---

# Scope the live-wiring of the LV Breaker TCC page (`/lvbreakertcc`) — gap analysis + proposed solutions + staging

**Lane:** TCC LV Breaker MVP → the field-tolerance product. **ANALYSIS / SCOPING ONLY — produce a DESIGN DOC, NOT code.** No edits to `page.tsx`, no API/route changes, no migrations, no DB/prod writes. Follow the inbox lifecycle (git mv pending→claimed + push BEFORE starting). Ground everything in the reference SSoT (`reference/tcc/` 00 + G0–G4 + GR) per the Single-Source-of-Truth Law, and the just-shipped D1 foundation.

## Context (the situation)
The new operator-facing page `apps/operations-web/app/lvbreakertcc/page.tsx` is a **clean-slate, web-polished MVP** built from the operator's `TCC_Calculator_v5.xlsx` concept. It is currently **100% frozen sample data** (Square D P-Frame PX 2500A / Micrologic 6.0H hardcoded; representative placeholder numbers) with **zero backend calls**. Its 3-screen flow:
1. **Specifications** — dual Breaker × Trip-Unit selection.
2. **Protection Settings** — 8 element cards (LTPU/LTD/STPU/STD/INST/GFPU/GFD/MAINT) + the NETA tolerance-bands table (Element / Setting / Test@ / Min / Max / Measured / %Error / Status) + maintenance toggle + 0.5×-step delay dropdowns.
3. **Time-Current Curve** — inline-SVG log-log curve (nominal + tolerance band + element markers).

The **data foundation is now in place** (D1, just shipped — STATE §104; migrations `006`/`007`; apex `5cb6adb1`):
- `tcc.vw_breaker_sst_bridge` — breaker style → compatible ETU sensor set (the SST bridge; ICCB 100 / MCCB 95.6 / PCB 97.5% match vs Access; `T8V-1600`→ABB PR332/P→5 sensors live).
- `tcc.etu_sensors` — per-sensor NETA pickup/time-delay tolerances (`*_tol_hi/lo`, `*_calc`, `*_step`, `*_name`, the delay calc codes) = the authoritative tolerance DATA (G4 field-trust matrix: PU tolerances are ship-safe).
- `tcc.brk_*_styles` now carry `source_id` + `tmt_use_sst` + `tmt_sst_{mfr,type,style}`.

**Existing groundwork to LEVERAGE (do NOT rebuild greenfield):**
- Field-tol MVP (`apps/operations-web/TCC_FIELD_TOLERANCES_MVP_SPEC_2026-05-31.md`) already built a guided selection cascade + TMT filter + per-sensor tolerance rendering against the DB (SC1/B1.1).
- The operations-web **explorer** already does dual breaker×trip-unit selection (manufacturer-axis cross-filter) via `/api/v1/neta/etu/*` + `/tmt/*` routes in `apps/control-plane-api/services/neta/router.py`.
- The relay **`POST /relay/plot-tcc`** endpoint is the working precedent for a server-computed TCC curve.

## What to produce (`apps/operations-web/app/lvbreakertcc/WIRING_SCOPING.md` — structured + actionable)
1. **Current-state map of `page.tsx`** — enumerate the frozen/hardcoded data (`ELEMENTS`, `BANDS`, `MULT_OPTS`, `DELAY_DEFAULT`, the sample breaker/trip-unit, the SVG curve points) and the client-side state + logic (step/maint/delay-mult/measured; the %Error + PASS/FAIL math; the live test-current recompute). Mark each part **presentational (KEEP)** vs **data (REPLACE)**.
2. **Per-screen data contract** — for each of the 3 screens, the exact data the live page needs (shape/fields), keyed to the validated schema. e.g. Specifications: breaker cascade + the bridge narrowing → compatible sensor set; Protection Settings: the selected sensor's element set + per-element tolerance bands (map each `etu_sensors` col → its NETA band + default test-multiplier); Curve: per-element computed curve points.
3. **Gap register** (table) — each data need → the backend surface that provides it TODAY (endpoint / view / calc, with `file:path`), or **GAP**. Classify each: **(a) wireable now** (data + surface exist; needs only the fetch + maybe a thin endpoint), **(b) needs a thin new endpoint** over existing data, **(c) needs engine/research** (the hard ones). Be explicit which is which.
4. **Curve (screen 3) deep-dive** — expected to be the main gap (the §102 TCC curve-plotting research backlog). Inventory what the calc-engine already computes (`packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_curves.py` native-Therm branch, `etu_delay_routing.py` SST delay routing; the relay `/plot-tcc` precedent; the EasyPower engine RE in the `project_easypower_engine_re` memory) vs. what's missing to render a faithful breaker TCC per element. Recommend an approach + flag fidelity caveats per the G4 field-trust matrix (trustworthy vs bounded curve numbers — e.g. INVEQ).
5. **Proposed solution per gap** — concrete approach + rough effort/risk (S/M/L) + dependencies.
6. **Staging recommendation** — propose the build sequence (a likely shape: **A** Specifications live-select + bridge narrowing → **B** Protection Settings live NETA tolerance bands [ships the field-tol MVP] → **C** Curve [engine-gated]), with the dependency graph + what value ships at each stage.
7. **Explorer-consolidation decision** — port the existing explorer's dual-axis selection logic into the LV page's Specifications screen and retire the explorer, or keep both? Recommend with reasoning (the operator has called the old operations-web shell a placeholder, not a long-term constraint).
8. **Decision points for the operator** — a crisp list of the choices needed before build.

## Boundaries / guardrails
- **ANALYSIS ONLY.** No code, no `page.tsx` edits, no route/API changes, no migrations, no DB writes. Single deliverable = the doc (+ closeout).
- Work from the **committed repo + the reference guides as the SSoT.** You likely cannot introspect the live Supabase — rely on `reference/tcc/` (esp. G1 schema, G3 routing/cascade, G4 calc + field-trust matrix, G0 the bridge) + migrations `005/006/007` as the schema truth. Where a claim needs live verification, **flag it** rather than assume.
- **Leverage, don't redo** — map onto the field-tol MVP + explorer + bridge work; call out reuse explicitly.
- **Surface decisions; do not commit architecture** — the operator decides. Cite the SSoT.
- PUBLIC repo — no secrets, no client/job identifiers, no DSN/keys.

## Acceptance
- `WIRING_SCOPING.md` exists with all 8 sections, each actionable: gaps classified a/b/c; per-screen data contracts keyed to real schema; the curve deep-dive grounded in the actual calc-engine code; a staged A→B→C (or better) sequence; the consolidation recommendation; the operator decision list.
- Every backend-surface claim cites a real `file:path` or guide section; every GAP is classified by type; fidelity caveats cite the G4 field-trust matrix.
- No code/schema changed. Then `git mv` claimed→done, commit, push; brief closeout at the handoffs path pointing to the doc.
