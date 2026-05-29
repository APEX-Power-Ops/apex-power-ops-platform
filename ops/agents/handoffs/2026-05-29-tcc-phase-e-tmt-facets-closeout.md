# TCC Phase E1 - TMT Facets Closeout

Date: 2026-05-29
Status: PASS for backend-first local route implementation and non-live family proof
Purpose: Record the bounded Phase E1 TMT facet-route implementation for Runtime 017 without widening into demo wiring or unrelated route work

---

## 1. Outcome

Phase E1 is locally implemented as a bounded backend-first slice.

Admitted change surface:

1. added `GET /api/v1/neta/tmt/facets`
2. added `TMTFacet` and `TMTFacetsResponse` schema support
3. added focused route tests for the new endpoint

Preserved boundaries:

1. no ETU route edits
2. no relay edits
3. no demo wiring changes
4. no hosted-parity claim
5. no push

---

## 2. Implemented Contract

Route:

1. `GET /api/v1/neta/tmt/facets`

Accepted query params:

1. `breaker_class`
2. `manufacturer_id`
3. `breaker_id`
4. `breaker_style_id`
5. `frame_size`
6. `amp_rating`

Response shape:

1. `facets: list[TMTFacet]`
2. `total_matching_frames: int`
3. `active_filters: dict`

Facet fields confirmed against current repo schema and joins:

1. `breaker_class` -> `tcc_tmt_frames.breaker_class`
2. `manufacturer_id` -> breaker parent tables `tcc_brk_{iccb,mccb,pcb}.manufacturer_id`
3. `breaker_id` -> breaker parent tables `tcc_brk_{iccb,mccb,pcb}.id`
4. `breaker_style_id` -> breaker-style tables `tcc_brk_{iccb,mccb,pcb}_styles.id`
5. `frame_size` -> `tcc_tmt_frames.size`
6. `amp_rating` -> `tcc_tmt_amps.rating`

Implementation note:

1. the route derives a unioned TMT catalog across ICCB, MCCB, and PCB frame/style/breaker tables, then computes per-facet distinct values by applying all active filters except the facet currently being derived

---

## 3. Files Touched

1. `apps/control-plane-api/services/neta/router.py`
2. `apps/control-plane-api/services/neta/schemas.py`
3. `apps/control-plane-api/tests/test_neta_tmt_facets_route.py`

---

## 4. Validation

Focused new-route proof:

1. `PYTHONPATH=apps/control-plane-api .venv/bin/python -m pytest apps/control-plane-api/tests/test_neta_tmt_facets_route.py -q`
   - result: `2 passed`

Non-live family route proof:

1. `PYTHONPATH=apps/control-plane-api .venv/bin/python -m pytest apps/control-plane-api/tests/test_neta_tmt_facets_route.py apps/control-plane-api/tests/test_neta_emt_facets_route.py apps/control-plane-api/tests/test_neta_tmt_routes.py apps/control-plane-api/tests/test_neta_emt_routes.py -q`
   - result: `17 passed`

Static diagnostics:

1. `get_errors` on the touched router, schemas, and new TMT/EMT facet tests returned no diagnostics

Attempted broader live-family rerun:

1. existing `apps/control-plane-api/tests/test_neta_tmt_live_integration.py` failed on this host with `psycopg2.OperationalError` connecting to `localhost:5432`
2. this is recorded as workspace-environment limitation, not as a TMT facet-route regression

---

## 5. Deferred Follow-On

Not started in this slice:

1. E3 demo wiring for live facet-driven TMT filter grids
2. family smoke rerun against a locally reachable real DB-backed host
3. hosted parity or deployment work

Next truthful TMT move is E3 only after the backend contract is admitted sufficient and a local deployed host is available for browser proof.