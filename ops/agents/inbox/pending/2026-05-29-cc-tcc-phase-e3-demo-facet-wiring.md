---
dispatch_id: 2026-05-29-cc-tcc-phase-e3-demo-facet-wiring
target: CC
priority: 1
from: Desktop
created_at: 2026-05-29
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-05-29-tcc-phase-e3-demo-facet-wiring-closeout.md
---

# TCC Runtime 017 Phase E3 — wire TMT + EMT demo facet grids to the new endpoints

**Lane:** TCC Runtime 017 (matrix #83), Phase E3 (demo port) per `ops/agents/handoffs/2026-05-28-tcc-runtime-017-remaining-end-to-end-task-list.md` §3.E. This is also the **first live test of the dispatch inbox** — you reached it by draining your own inbox, not by operator relay. Confirm that worked in the closeout.

**Precondition:** the Phase E1/E2 facet routes must be COMMITTED first — `GET /api/v1/neta/tmt/facets` (router.py ~3358) + `GET /api/v1/neta/emt/facets` (~3593) + their schemas + tests. (As of authoring these were uncommitted on the host; commit + push them before starting E3 so E3 builds on a clean base.)

## Task
Wire the TMT and EMT filter grids in `apps/control-plane-api/demo/neta_tcc.html` to the new facet endpoints so the dropdowns cross-filter on live data (currently they populate from hardcoded/cached data). On page load and on each filter change: call `GET /tmt/facets?...` (resp. `/emt/facets?...`) with the current selections, repopulate the six dropdowns from the response `facets`, and narrow the others. Match the reference demo's facet-driven behavior (`source-domains/tcc_v5_backend/demo/neta_tcc.html`).

## Guardrails
- **Frontend wiring only — no backend changes.** E1/E2 already shipped the routes; if you find a route gap, STOP + reclassify as a backend follow-on (do not edit router.py here).
- **DB-less browser proof:** prove the grid → facet-call → render → cross-filter loop with **mocked facet responses** (same pattern as the Phase D `test_demo_browser.py` DB-less mocks). Route-level correctness is already covered by the E1/E2 route tests; E3 proves the UI wiring. Do not block E3 on the live-DB gap.
- No TMT/EMT/relay/ETU contract changes; no hosted claim.
- Exclude residue (`.vscode/tasks.json`, `output/`).

## Validation
- Focused browser test green (the TMT/EMT facet-wiring slice) from the repo-local `.venv` (Chromium is provisioned).
- Keep existing facet route tests + ETU surfaces green.

## Closeout (per inbox protocol)
- Write the closeout to the `closeout:` path above; record: the wiring done, the browser proof result, and a one-line confirmation that the inbox self-serve flow worked end-to-end (claim → execute → close).
- Commit your work, then `git mv` this dispatch from `claimed/` to `done/`, commit, push. Return to Desktop for review.
