# LTPU/STPU Tolerance Characterization Closeout

Dispatch: `2026-05-30-cc-ltpu-stpu-tolerance-characterization`
Executor: Codex
Date: 2026-05-31
Status: Complete — characterization outcome (a), no calc-engine fix warranted.

## Claim

- Claim commit pushed: `d82813b4` (`claim: 2026-05-30-cc-ltpu-stpu-tolerance-characterization by codex`)
- Predecessor was already done: `2026-05-30-cc-relay-live-validation-parity`
- Characterization used the read-only pooler DSN from `/home/olares/apex-secrets/olares/ai-live-dsn.env`; no DSN value was printed.

## Characterization Verdict

LTPU/STPU mirror the INST/GFPU finding in the operationally important sense:

- there are **zero** present LTPU elements with NULL tolerance
- there are **zero** present STPU elements with NULL tolerance
- every STPU NULL tolerance row is `stpu_calc = -1`
- LTPU has no NULL tolerance rows at all

Therefore the current `0.0` NULL-tolerance fallback does not under-serve any present LTPU/STPU element. No NETA general `±10` fallback should be reintroduced for LTPU/STPU pickup tolerance.

## Live Counts

Summary across all `17,831` live `tcc_etu_sensors` rows:

| Element | Present calc | Absent calc `-1` | Calc NULL | Any tolerance NULL | Present with NULL tolerance | Absent with NULL tolerance | Absent with stale present tolerance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LTPU | 17,791 | 40 | 0 | 0 | 0 | 0 | 40 |
| STPU | 15,259 | 2,572 | 0 | 205 | 0 | 205 | 2,367 |

Pickup-row cross-check:

| Element | Calc class | Tolerance state | Pickup rows | Sensors |
| --- | --- | --- | --- | ---: |
| LTPU | absent `-1` | both present | has pickup rows | 1 |
| LTPU | absent `-1` | both present | no pickup rows | 39 |
| LTPU | present | both present | has pickup rows | 17,656 |
| LTPU | present | both present | no pickup rows | 135 |
| STPU | absent `-1` | both NULL | has pickup rows | 13 |
| STPU | absent `-1` | both NULL | no pickup rows | 192 |
| STPU | absent `-1` | both present | has pickup rows | 273 |
| STPU | absent `-1` | both present | no pickup rows | 2,094 |
| STPU | present | both present | has pickup rows | 14,960 |
| STPU | present | both present | no pickup rows | 299 |

Present-element tolerance diversity:

| Element | Present sensors | Distinct tolerance pairs | `tol_lo` range | `tol_hi` range | `-10/+10` count |
| --- | ---: | ---: | --- | --- | ---: |
| LTPU | 17,791 | 57 | `-20.00` to `50.00` | `0.00` to `120.00` | 3,662 |
| STPU | 15,259 | 34 | `-24.33` to `0.0` | `0.0` to `56.67` | 11,416 |

This confirms the spec posture: live present-element tolerances are data-derived and varied, not a uniform general `±10` fallback.

## Spec Basis

`packages/calc-engine/src/apex_calc_engine/services/calc_engine/NETA_TEST_PLAN_SPEC.md` states that pickup tolerance for LTPU and STPU comes from `tcc_etu_sensors.ltpu_tol_hi/lo` and `stpu_tol_hi/lo`, and warns: "Always use the per-sensor values, never assume ±10%."

The current calc-engine path already matches that characterization:

- `_calc_element` returns `None` before tolerance calculation when `calc_method` is `ETUCalcMethod.NONE` / `-1`
- `_calc_tolerance` defensively treats NULL `tol_lo/hi` as `0.0`, producing a zero-width band only if a NULL tolerance is ever evaluated

Because live present LTPU/STPU rows never have NULL tolerance, no calc-engine edit is required.

## Regression Added

Added `packages/calc-engine/tests/test_etu_pickup_tolerances.py`:

- absent pickup calc returns no result before tolerance-band calculation
- defensive NULL tolerance evaluation produces a zero-width band

No production calc code changed.

## Validation

- `PYTHONPATH=src ../../apps/control-plane-api/.venv/bin/python -m pytest tests/test_etu_pickup_tolerances.py tests/test_stpu_override.py -q`
- Result: `9 passed`

Hosted ETU parity sanity check:

- `PYTHONPATH=. .venv/bin/python scripts/probe_live_etu_sql_parity.py --base-url https://control.apexpowerops.com --artifact-path ''`
- Result: `RESULT PASS: live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 0`

Diff hygiene:

- `git diff --check -- packages/calc-engine/tests/test_etu_pickup_tolerances.py`
- Result: clean

## Boundary

Changed only:

- `packages/calc-engine/tests/test_etu_pickup_tolerances.py`

No calc-engine implementation, SQL, route, schema, data, frontend, or dependency files were changed. Existing unrelated local residue (`pnpm-lock.yaml`, `output/`, and canary actual JSON files) was left untouched.
