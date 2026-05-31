# Relay Live Validation Parity Closeout

Dispatch: `2026-05-30-cc-relay-live-validation-parity`
Executor: Codex
Date: 2026-05-31
Status: Complete

## Claim

- Claim commit pushed: `c0588449` (`claim: 2026-05-30-cc-relay-live-validation-parity by codex`)
- Predecessor was already done: `2026-05-30-cc-tcc-phase-g3-relay-live-population`
- Live DB access used the read-only pooler DSN from `/home/olares/apex-secrets/olares/ai-live-dsn.env`; no DSN value was printed.

## Part A — Live Smoke No Longer Skips

Updated `apps/control-plane-api/tests/test_neta_relay_live_integration.py` so the smoke test searches up to 12 supported relay sections and chooses the first section with non-empty `settings.preview_options`.

Current live selection:

| Field | Value |
| --- | --- |
| selected TD-section | `5075` |
| family | `bsl` |
| storage kind | `constants` |
| preview options | `3` |

Validation:

- `PYTHONPATH=../../packages/calc-engine/src:. .venv/bin/python -m pytest tests/test_neta_relay_live_integration.py -q -rs`
- Result: `1 passed, 1 warning`
- No skip.

## Part B — Live SQL Parity Probe

Added:

- `apps/control-plane-api/scripts/probe_live_relay_sql_parity.py`
- `apps/control-plane-api/scripts/relay_parity_matrix.json`

The probe reads reference data directly from live `work.tcc_relay_*` tables and compares it to `POST /api/v1/neta/relay/plot-tcc`. It does not import or call the relay calc-engine evaluators.

The external Windows-path spec named in the dispatch was not present in this clone. Formula characterization was therefore cross-checked against the repo-owned decoded relay family implementation and frozen golden fixtures, then reimplemented independently inside the probe.

Reference methods:

| Family | Storage | Independent reference |
| --- | --- | --- |
| TCP | points | exact stored SQL points from `work.tcc_relay_curve_points_tcp` at exact stored current multiples |
| IEC | constants | `time_dial * v_k / (current_multiple ** v_e - 1)`, with `dt_after` / `dt_min_time` floor handling |
| MEQ | constants | `(v_a + v_b/delta + v_d/delta^2 + v_e/delta^3) * time_dial`, where `delta = current_multiple - v_c` |
| BSL | constants | `time_dial * (v_a / (current_multiple ** v_n - v_c) + v_b) + v_k` |
| SWZ | constants | `time_dial * (v_b / (current_multiple ** v_e - 1) + v_a)` |
| PCD | constants | `time_dial * (v_a / (current_multiple ** v_c - 1) + v_b)` |

Tolerances:

| Storage | Absolute seconds | Relative seconds |
| --- | ---: | ---: |
| points | `1e-6` | `1e-9` |
| constants | `1e-6` | `1e-6` |

Frozen cohort:

| Scenario | Family | TD-section | Option |
| --- | --- | ---: | --- |
| `relay-live-tcp-digitrip-mv-i4t-5084` | TCP | `5084` | parent `18922`, source ordinal `2`, time dial `0.2` |
| `relay-live-iec-bulletin-857fd-ni-34479` | IEC | `34479` | parent `34480`, curve ordinal `10` |
| `relay-live-meq-bulletin-857fd-mi-34493` | MEQ | `34493` | parent `34494`, curve ordinal `10` |
| `relay-live-bsl-dt3000-ansi-mod-inv-5075` | BSL | `5075` | parent `16157`, curve ordinal `10` |
| `relay-live-swz-bulletin-857fd-lti-34486` | SWZ | `34486` | parent `34487`, curve ordinal `10` |
| `relay-live-pcd-dpu445h-ext-inverse-35216` | PCD | `35216` | parent `35217`, curve ordinal `10` |

Probe validation:

- `PYTHONPATH=../../packages/calc-engine/src:. .venv/bin/python scripts/probe_live_relay_sql_parity.py --artifact-path ''`
- Result: `RESULT PASS: live relay SQL parity holds across 6 seeded scenario(s); families: bsl, iec, meq, pcd, swz, tcp; warnings: 0; failures: 0`
- DB source: governed live Supabase via `APEX_OLARES_LIVE_DSN` / `work.tcc_relay_*`
- Route source: `https://control.apexpowerops.com`

## Regression

- `PYTHONPATH=src ../../apps/control-plane-api/.venv/bin/python -m pytest tests/test_relay_golden_fixtures.py -q`
- Result: `19 passed`

## Boundary

Changed only test/script/fixture surfaces:

- live relay integration smoke test
- relay parity probe script
- relay parity matrix

No relay calc-engine, route, schema, data, or frontend changes were made. Existing unrelated local residue (`pnpm-lock.yaml`, `output/`, and canary actual JSON files) was left untouched.
