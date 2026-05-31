---
dispatch_id: 2026-05-31-codex-tcc-tol-route-delay-fields
target: CODEX
priority: 1
from: Desktop
created_at: 2026-05-31
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-05-31-tcc-tol-route-delay-fields-closeout.md
---

# Route fix — separate the `/plot-tcc` delay band-selector from the NETA test multiplier (so delay rows are correct)

**Lane:** TCC Field Tolerances MVP — tolerance-output correctness (prerequisite for the B2.1 sheet's delay rows). **Spec of record:** `apps/operations-web/TCC_FIELD_TOLERANCES_MVP_SPEC_2026-05-31.md`. **Backend-led; parity-gated; backward-compatible.** Follow the inbox lifecycle. Independent of the SC1 guided-cascade dispatch (different files) — a dual-executor lane.

## The bug (found in B0.1 validation — see `ops/agents/handoffs/2026-05-31-tcc-tol-b01-validate-series-b-closeout.md`)
`POST /api/v1/neta/plot-tcc` **overloads** `ltd_setting` / `std_setting` / `gfd_setting` as BOTH the delay-band selector AND the NETA test multiplier:
- When the caller passes the NETA test multiplier (e.g. STD/GFD = `1.5`, LTD = `3`), the route returns the right delay test current but falls back to the first delay band for timing.
- When the caller passes the selected **band open-time** (the real field setting), `test_multiple` becomes that open-time and the **test current is corrupted** — B0.1 observed STD `expected_current=360` (reference `9000`) and GFD `38.4` (reference `960`) for SE Series B sensor 30338.
- LTD additionally emits the direct band open-time instead of the reference delay **window** `setting·0.7·(6/mult)²` → `setting·(6/mult)²`.

## Do
1. **Claim** (git mv pending→claimed, push) before editing.
2. **Separate the concerns in the `/plot-tcc` request + delay calc** (`apps/control-plane-api/services/neta/router.py`): introduce distinct inputs for (a) the **selected delay band / open-time** (what the breaker is set to) and (b) the **NETA test multiple** used to compute the delay test current (LTD 3×, STD/GFD 1.5× per the reference). The delay **test current** must derive from the multiple-against-pickup (not the band time); the delay **expected time / window** must derive from the selected band. Keep it ONE route, **backward-compatible** (existing callers that pass the multiplier in `*_setting` keep working; add the new optional fields).
3. **Emit the reference LTD window**: when the NETA multiple is provided, LTD `time_limit_low/high` should reflect `setting·0.7·(6/mult)²` → `setting·(6/mult)²` (e.g. SE Series B LTD setting 2 at 3× → window ~8.4 to 12), not the flat band open-time. Confirm STD/GFD flat bands still resolve correctly from the selected band.
4. **Re-validate against the Series B reference** (the B0.1 method, read-only): for SE Series B sensor 30338 @ plug 3000, confirm STD test current = 9000 (not 360), GFD = 960 (not 38.4), and the LTD window matches the reference at the documented multiples. Use the governed read-only DSN / hosted control-plane; DSN out-of-band.

## Acceptance
- `/plot-tcc` delay rows: test currents derive from the NETA multiple (STD/GFD 9000/960 for the B0.1 case, not 360/38.4); LTD emits the reference window; STD/GFD flat bands correct.
- Backward-compatible: prior callers unaffected.
- No regression: ETU SQL parity 3/0; relay parity 6/6; catalog 63/17831; tmt/emt facets 200.

## Guardrails
- Backend code-only (`router.py` + the plot/delay calc + a focused route test). No DDL/migration. **Tolerance VALUES stay DB-authoritative** — this fixes how the delay *test current vs band-time* is modeled, NOT the tolerance bands (those are the DB's). Scoped `git add`. DSN out-of-band; no `.env*` contents. PUBLIC repo — no client/job identifiers.

## Closeout
Record: the request-field change (old overloaded field → separated band vs multiple), the LTD-window fix, the re-validation numbers vs the Series B reference (STD 9000 / GFD 960 / LTD window), local test result, commit hash, Render deploy confirmation, and the no-regression gate. Then `git mv` claimed→done, commit, push.
