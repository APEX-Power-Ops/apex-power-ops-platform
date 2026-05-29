# TCC Runtime 017 Phase C ETU Ready-To-Port Parity Slice - Closeout Handoff

Date: 2026-05-28
Status: Closed PASS for the admitted Phase C slice
Purpose: Record the bounded ETU demo parity slice that added breaker-context provenance disclosure and richer plug-compatibility workflow without opening new backend routes or drifting into later family work

---

## 1. Outcome

Phase C is closed PASS.

The admitted ETU demo slice is now implemented in the active control-plane demo with one bounded supporting backend repair discovered during live proof:

- breaker-context provenance is now disclosed in the ETU summary as selected or derived state
- the ETU plug-compatibility workflow now exposes an explicit compatibility validation action, result rendering, and explanatory copy
- `/api/v1/neta/cascade` was hardened so combined plug and breaker-half filters remain truthful under the existing contract

No new route was added. The richer plug workflow was kept on the existing route surface:

- `GET /api/v1/neta/cascade`
- `GET /api/v1/neta/etu/search`

The bounded implementation commit is:

- `fa8b99d829087a4c57973ed1c459d6d4e9d2f539` - `Add ETU Phase C provenance and plug compatibility`

---

## 2. Governing Files

Implementation and tests in the bounded commit:

- `apps/control-plane-api/demo/neta_tcc.html`
- `apps/control-plane-api/services/neta/router.py`
- `apps/control-plane-api/tests/test_cascade_route.py`
- `apps/control-plane-api/tests/test_demo_browser.py`
- `apps/control-plane-api/tests/test_demo_route.py`

---

## 3. Contract Decision

The Phase C pre-check held the original stop condition:

- if the ETU parity slice required a new backend route, stop and reclassify

That stop condition did not trigger.

Findings:

- breaker-context provenance could be carried on the existing `breaker_context_source` shape already returned by the active stack
- plug compatibility could be expressed by combining the existing cascade narrowing path with the existing ETU search path that already accepts `plug_value`

Because the contract gap did not materialize, the slice remained eligible for bounded implementation.

---

## 4. Validation

Focused route validation passed with the repo-local interpreter because `pytest` was not on `PATH`:

1. `.venv\Scripts\python.exe -m pytest apps/control-plane-api/tests/test_demo_route.py apps/control-plane-api/tests/test_etu_search_route.py apps/control-plane-api/tests/test_cascade_route.py -q`
   - initial implementation pass: `41 passed in 2.06s`
   - after first cascade hardening patch: `42 passed in 3.91s`
   - final post-fix pass: `42 passed in 1.83s`

Focused browser pytest was present but not executable in that repo-local venv because the Playwright package was missing; the required browser binaries were already cached on the workstation:

1. `.venv\Scripts\python.exe -m pytest apps/control-plane-api/tests/test_demo_browser.py -k "provenance or plug" -q`
   - result: `2 skipped, 18 deselected in 1.79s`

Live browser proof on the local host then closed the validation gap:

1. `uvicorn main:app --host 127.0.0.1 --port 8010`
2. Browser proof on `http://127.0.0.1:8010/demo/neta-tcc`
   - live badge confirmed: `LIVE - 63 manufacturers, 17831 sensors`
   - derived provenance confirmed in the ETU summary:
     - label: `(derived)`
     - source: `trip_style_sensor_rating`
   - selected provenance confirmed after breaker-half selection:
     - label: `(selected)`
     - source: `breaker_half_selection`
   - plug impact explanation rendered for the `300A` lens without throwing
   - explicit compatibility action returned compatible sensors for plug `300A`

Representative compatibility result text observed during live proof:

- `2 compatible sensors for plug 300A.`
- `GE - MVT RMS-9 - ICCB - sensor 400 (400A)`
- `GE - MVT RMS-9 - ICCB - sensor 800 (800A)`
- `Compatibility-validation only - plug remains downstream of upstream identity resolution.`

Screenshots were captured for:

- the ETU summary with provenance tag
- the plug compatibility result panel

---

## 5. Supporting Backend Repair Discovered During Proof

The UI slice exposed a latent ambiguity defect in `/api/v1/neta/cascade` when `plug_value` and breaker-half filters were combined.

Two local repairs were required:

1. qualify the count path as `COUNT(DISTINCT v.sensor_id)` once the plug join is active
2. build the joined-query `WHERE` clause with prefix `v.` so the shared filter builder does not emit bare `sensor_id`

These were not new-contract changes. They were truthfulness repairs inside the existing cascade route required to keep the admitted Phase C workflow working on real data.

---

## 6. Boundaries Preserved

This Phase C slice did not:

- add `/api/v1/neta/etu/sensors-matching-plug`
- add any other new backend route
- widen into TMT facet work
- widen into EMT facet work
- claim hosted parity
- perform any push
- include unrelated workspace residue such as `.vscode/tasks.json` or `output/`

The slice stopped exactly at the admitted ETU surfaces plus the minimum cascade-query hardening needed for truthful live behavior.

---

## 7. Git Posture

The implementation commit was created as a bounded local commit and left unrelated residue out of scope:

- commit: `fa8b99d829087a4c57973ed1c459d6d4e9d2f539`
- push status: not pushed

Any later work on ETU control-path helpers, TMT facets, EMT facets, or hosted deployment should open as new bounded packets rather than extending this Phase C closeout.