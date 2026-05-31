# TCC Field Tolerances MVP — build spec (2026-05-31)

## Goal
Field technicians can obtain **trusted PU/TD (pickup / time-delay) tolerances** for the breakers/trip-units they test — **ETU primary, TMT secondary** — at MVP quality (accurate and reachable, not external-user-polished). Tolerance values must agree with (a) a trusted reference methodology — a **Square D MicroLogic Series B trip-curve reference calculator** (RESA-internal, off-repo) — and (b) the NETA per-element test plan the backend already computes (`/plot-tcc` `table_rows`).

## Context / inputs
- Builds on the EasyPower-realign explorer (`TCC_EXPLORER_REALIGN_SPEC_2026-05-31.md`); the NETA tolerance table already renders for ETU.
- An independently-verified review (13/14 claims confirmed) found: the backend is richer than operations-web consumes; the demo-parity gaps are mostly **frontend orchestration** + **one TMT backend bug** + **one TMT/EMT bounded-surface caveat**. This MVP targets ONLY the field-tolerance need, NOT full demo-workflow parity.
- **Reference-of-record for ETU tolerance methodology** (the Series B calculator, 4 tabs: Full SE main / Std MX 250-800 / Std 1600). Per-element method = the validation target:
  - **LTPU**: test current = `setting × rating-plug`; band **±7.5%** (nominal `1.075 × setting × plug`, MIN/MAX = ∓7.5% of test).
  - **STPU / INST**: band **±15%** (`×0.85` / `×1.15`).
  - **GFPU**: band **±10%** (`×0.9` / `×1.1`).
  - **LTD**: test = `3× LTPU`; delay window `setting·0.7·(6/mult)²` → `setting·(6/mult)²` (mult = 1.5/2.0/3.0).
  - **STD / GFD** (flat): LOOKUP-table delay at `1.5× pickup`; **STD\*/GFD\*** (I²t) = LOOKUP rescaled by `((In·12)/test)²` (STD\*) / by GFPU basis (GFD\*).

## UPDATE — 2026-05-31 (post-B0.1 decision + reprioritization)
**B0.1 RESOLVED (operator domain call).** The Series B reference calculator was itself **built from the DB** — and built under selection difficulty (hard to pinpoint the exact trip unit when the catalog can't be filtered cleanly). Its band divergences (e.g. GFPU ±10% vs the DB's per-sensor −20%/0%; Std MX STPU/INST asymmetries) therefore reflect **the reference's imprecision, not a tool error.** **Decision: the DB per-sensor tolerances are authoritative.** B0.1 already verified the engine's pickup CURRENTS match exactly, so the tolerance OUTPUT is trusted **once the right trip unit is selected.**

**Reprioritization — the core MVP is now SELECTION CONFIRMATION.** The real work is normalizing the selection items so a tech can confidently pinpoint AND **confirm** the exact trip unit matching the physical breaker (whose DB tolerance is then authoritative). The tolerance sheet (B2.1, DB-based) is the payoff, gated on selection being confirmable + the `/plot-tcc` delay-field route fix. New core lane:
- **SC1 — Guided ETU cascade.** Consume `/cascade` (manufacturer → trip type → trip style → sensor, cross-filtered, plug-lens) so selection is a drill-down to the exact unit, not free-text guessing. (TMT/EMT analog where supported.)
- **SC2 — Selection-confirmation surface.** Show the distinguishing attributes of the selected unit (tcc_number, trip style, sensor desc/rating, compatible plugs) so a tech can match the screen to the nameplate and confirm.
- **SC3 — User-facing terminology normalization.** Map engineer/DB vocab (trip_type/style names, sensor descriptors, element codes) to tech-friendly labels — needs a normalization-mapping design pass (operator domain input).
- **SC4 — Filtering completeness.** B1.1 (TMT manufacturer filter) DONE; B1.2 ("0 MATCHES" display) + cross-filter integrity remain.

Supporting (tolerance-output correctness, not selection): the `/plot-tcc` delay-field route fix (separate selected-delay-band from NETA test multiplier; emit the reference LTD window) — needed before B2.1 emits correct delay rows.

## Build items (the list)

### Tier 0 — Ground truth (validate before building on the numbers)
- **B0.1 — Validate tool `table_rows` vs the Series B reference (ETU).** Match a Square D MicroLogic Series B sensor + settings in `tcc.*`; compare the tool's per-element `expected_current / limit_low / limit_high / test_multiple / expected_time / time_limit_low / time_limit_high` against the reference method for all 9 rows. **READ-ONLY.** The reference is authority; reconcile or characterize every delta. Acceptance: a per-element pass/delta table; the band rules (LTPU ±7.5%, STPU/INST ±15%, GFPU ±10%) confirmed or their divergence explained.
- **B0.2 — Characterize the TMT output.** What `/tmt/plot-tcc` actually returns for a thermal-mag breaker vs. the NETA TM test (long-time/overload trip-time + instantaneous pickup). **READ-ONLY.** Decide: is the pickup-band sufficient, or a real gap? Acceptance: a written verdict + the fields TMT does/doesn't carry.

### Tier 1 — Small verified fixes
- **B1.1 — TMT `manufacturer_id` filter.** Backend `/tmt/frames` currently accepts `manufacturer_name` only and silently drops `manufacturer_id` → the Axis-1 manufacturer dropdown is inert for TMT. Add `manufacturer_id` (and for symmetry `breaker_id`/`breaker_style_id`) to the signature + WHERE clause. Also characterize the orthogonal finding that `manufacturer_name=<known>` can return count=0 (data gap vs. name-matching). Parity-gated.
- **B1.2 — "0 MATCHES" Axis-1 display fix.** Frontend `breaker-resource-explorer.tsx` renders the Axis-1 count as `${breakerAxis?.count ?? 0}`, masking a null/failed fetch as a legitimate "0 matches" (an unfiltered cascade returns ~13,897). Render "unavailable"/loading when the fetch is null instead of `?? 0`.

### Tier 2 — Field deliverable
- **B2.1 — Tolerance-sheet export (the MVP minimum goal / north-star).** The Series B reference calculator IS the minimum bar for NETA field use: a **self-contained per-breaker sheet** that hands a tech everything they need — test currents, expected pickups, MIN/MAX tolerance bands, delay windows — so they do NOT go pull TCC curves and derive values on-site while testing. B2.1 produces that sheet, populated with **DB-authoritative** values, for a **confirmed** breaker/trip-unit (Element | Setting | Test current | Expected | MIN | MAX | Delay MIN/MAX | Method). Backend-driven export; a tech carries it. **Enabled by selection confirmation (SC1-SC4 — so it's the RIGHT sheet) + the `/plot-tcc` delay-field route fix (so the delay rows are correct).**

### Tier 3 — Deferred (post-MVP, per the review)
Guided `/cascade` consumption, editable settings controls, calculate/evaluate + measured-marker overlay, auth + saved plans/results. The **read-only vs. authenticated-persistence** decision gates this tier and is NOT on the field-tolerance critical path.

## Execution model
Dispatch-inbox, **gated**, parity-gated, reversible. **Dual-executor lanes:** read-only validation/characterization (B0.x) ∥ backend fixes (B1.x). This spec is the reference-of-record; dispatches cite it. Parity gates unchanged (ETU SQL parity 3/0, relay 6/6, catalog 63/17831). No client/job identifiers in this PUBLIC repo.
