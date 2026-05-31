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

## Build items (the list)

### Tier 0 — Ground truth (validate before building on the numbers)
- **B0.1 — Validate tool `table_rows` vs the Series B reference (ETU).** Match a Square D MicroLogic Series B sensor + settings in `tcc.*`; compare the tool's per-element `expected_current / limit_low / limit_high / test_multiple / expected_time / time_limit_low / time_limit_high` against the reference method for all 9 rows. **READ-ONLY.** The reference is authority; reconcile or characterize every delta. Acceptance: a per-element pass/delta table; the band rules (LTPU ±7.5%, STPU/INST ±15%, GFPU ±10%) confirmed or their divergence explained.
- **B0.2 — Characterize the TMT output.** What `/tmt/plot-tcc` actually returns for a thermal-mag breaker vs. the NETA TM test (long-time/overload trip-time + instantaneous pickup). **READ-ONLY.** Decide: is the pickup-band sufficient, or a real gap? Acceptance: a written verdict + the fields TMT does/doesn't carry.

### Tier 1 — Small verified fixes
- **B1.1 — TMT `manufacturer_id` filter.** Backend `/tmt/frames` currently accepts `manufacturer_name` only and silently drops `manufacturer_id` → the Axis-1 manufacturer dropdown is inert for TMT. Add `manufacturer_id` (and for symmetry `breaker_id`/`breaker_style_id`) to the signature + WHERE clause. Also characterize the orthogonal finding that `manufacturer_name=<known>` can return count=0 (data gap vs. name-matching). Parity-gated.
- **B1.2 — "0 MATCHES" Axis-1 display fix.** Frontend `breaker-resource-explorer.tsx` renders the Axis-1 count as `${breakerAxis?.count ?? 0}`, masking a null/failed fetch as a legitimate "0 matches" (an unfiltered cascade returns ~13,897). Render "unavailable"/loading when the fetch is null instead of `?? 0`.

### Tier 2 — Field deliverable
- **B2.1 — Tolerance-sheet export.** Given a breaker/trip-unit (+ as-set settings), emit a printable per-element PU/TD tolerance sheet in the reference format (Element | Setting | Test current | Expected | MIN | MAX | Delay MIN/MAX | Method). Backend-driven export; a tech carries the sheet. Depends on B0.1 (trusted numbers).

### Tier 3 — Deferred (post-MVP, per the review)
Guided `/cascade` consumption, editable settings controls, calculate/evaluate + measured-marker overlay, auth + saved plans/results. The **read-only vs. authenticated-persistence** decision gates this tier and is NOT on the field-tolerance critical path.

## Execution model
Dispatch-inbox, **gated**, parity-gated, reversible. **Dual-executor lanes:** read-only validation/characterization (B0.x) ∥ backend fixes (B1.x). This spec is the reference-of-record; dispatches cite it. Parity gates unchanged (ETU SQL parity 3/0, relay 6/6, catalog 63/17831). No client/job identifiers in this PUBLIC repo.
