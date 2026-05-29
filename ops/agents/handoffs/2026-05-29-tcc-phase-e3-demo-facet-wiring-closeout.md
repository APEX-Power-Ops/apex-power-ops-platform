# TCC Phase E3 - Demo Facet Wiring Closeout

Date: 2026-05-29
Status: PASS for frontend-only local facet-grid wiring and DB-less browser proof
Purpose: Record the bounded Phase E3 demo-port wiring for Runtime 017 without reopening backend scope or blocking on the live DB gap

---

## 1. Outcome

Phase E3 is locally implemented as a frontend-only demo slice.

Admitted change surface:

1. wired the TMT filter grid in `apps/control-plane-api/demo/neta_tcc.html` to `GET /api/v1/neta/tmt/facets`
2. wired the EMT filter grid in `apps/control-plane-api/demo/neta_tcc.html` to `GET /api/v1/neta/emt/facets`
3. added focused DB-less browser proofs for the TMT and EMT facet-grid loops
4. tightened one ETU browser wait to assert on rendered compatibility text instead of the transient loading state

Preserved boundaries:

1. no backend edits
2. no ETU route edits
3. no relay edits
4. no hosted claim
5. no live-DB dependency for E3 proof

---

## 2. Wiring Implemented

TMT:

1. converted the TMT filter controls from static/freeform inputs to facet-backed selects
2. lazy-loaded the TMT facet grid when the TMT panel is activated
3. refreshed the TMT facet grid on each filter change
4. re-ran the facet request once when a stale downstream selection was invalidated so the remaining dropdowns repopulate from the reduced valid scope
5. kept the existing frame search, context load, settings load, and nominal-plot workflow intact

EMT:

1. converted the EMT filter controls from raw numeric/text inputs to facet-backed selects
2. lazy-loaded the EMT facet grid when the EMT panel is activated
3. refreshed the EMT facet grid on each filter change
4. re-ran the facet request once when a stale downstream selection was invalidated so the remaining dropdowns repopulate from the reduced valid scope
5. kept the existing frame search, section load, settings load, and raw-point plot workflow intact

Implementation note:

1. the browser proof covers the grid -> facet call -> render -> cross-filter loop with mocked facet responses; it does not claim live DB-backed family parity

---

## 3. Files Touched

1. `apps/control-plane-api/demo/neta_tcc.html`
2. `apps/control-plane-api/tests/test_demo_browser.py`

---

## 4. Validation

Focused E3 browser proof:

1. `../../.venv/bin/pytest tests/test_demo_browser.py -k 'facet_grid_cross_filters'`
   - result: `2 passed`

Facet route regression proof:

1. `../../.venv/bin/pytest tests/test_neta_tmt_facets_route.py tests/test_neta_emt_facets_route.py`
   - result: `4 passed`

Bounded ETU/TMT/EMT browser regression proof:

1. `../../.venv/bin/pytest tests/test_demo_browser.py -k 'test_tmt_ or test_emt_ or test_etu_'`
   - result: `10 passed, 12 deselected`

Static diagnostics:

1. `get_errors` on the touched demo HTML and browser test file returned no diagnostics

---

## 5. Inbox Flow Confirmation

1. the repo-owned self-serve inbox flow worked end-to-end in this lane: claim from `pending/`, execute the bounded slice, write the closeout, and close the dispatch from `claimed/` to `done/`

---

## 6. Deferred Follow-On

Not started in this slice:

1. Phase F live validation against governed Supabase via `APEX_OLARES_LIVE_DSN`
2. hosted parity or deployment work
3. any backend follow-on for richer TMT label resolution beyond the current facet value surface