# TCC Tolerance Route Delay Fields Closeout

Dispatch: `2026-05-31-codex-tcc-tol-route-delay-fields`
Executor: Codex
Date: 2026-05-31
Result: PASS

## Summary

Separated `/api/v1/neta/plot-tcc` delay-band selection from NETA delay test multiples. The route remains backward-compatible with the legacy overloaded `ltd_setting`, `std_setting`, and `gfd_setting` fields, while new callers can now send explicit band/open-time fields and explicit delay test multiples.

Implementation commit: `e388c8eb`

## Request Contract

Added optional `PlotTccRequest` fields:

- `ltd_delay_setting`, `std_delay_setting`, `gfd_delay_setting`
- `ltd_test_multiple`, `std_test_multiple`, `gfd_test_multiple`

Resolution behavior:

- Explicit new delay fields select the delay band/open-time.
- Explicit new multiple fields drive `fn_calculate_test_currents`.
- Legacy `*_setting` values that exactly match a live delay-band open time are treated as band selectors and use the NETA default multiple: LTD `3x`, STD/GFD `1.5x`.
- Legacy values that do not match a live band keep the prior multiplier behavior.

The nominal plot curve selection, expected markers, and table rows now all use the resolved band selector. The SQL helper parameters use the resolved test multiple, so the delay test current is no longer derived from a band open-time.

## LTD Window Fix

For `/plot-tcc` LTD delay rows, the route now emits the reference delay window when a selected LTD band and test multiple are available:

`selected_band * 0.7 * (6 / multiple)^2` through `selected_band * (6 / multiple)^2`

STD and GFD continue to resolve their flat open/clear band windows from the selected band rows.

## Series B Validation

Local route validation used the canonical read-only live DSN via `TestClient`, without printing secret values.

Fixture:

- Sensor: `30338`
- Plug: `3000`
- LTPU: `1.0`
- STPU: `2.0`
- GFPU: `640.0`
- LTD band: `3.0`, LTD multiple: `3.0`
- STD band: `0.06`, STD multiple: `1.5`
- GFD band: `0.06`, GFD multiple: `1.5`

Observed `/plot-tcc` delay rows:

- STD `expected_current`: `9000.0`
- GFD `expected_current`: `960.0`
- LTD `time_limit_low`: `8.399999999999999`
- LTD `time_limit_high`: `12.0`

This confirms the B0.1 failure mode is repaired: STD is no longer `360`, GFD is no longer `38.4`, and LTD emits the reference window.

## Validation

Local focused backend test:

```text
PYTHONPATH=. .venv/bin/python -m pytest tests/test_neta_plot_tcc.py -q
37 passed, 1 warning
```

Operations-web compatibility:

- `npm run typecheck`: PASS
- `npm run build`: PASS
- `npx playwright test tests/browser-shell.breaker.smoke.spec.ts`: PASS, `1 passed`

Hosted no-regression gates:

- ETU SQL parity: PASS, `3` seeded scenarios, evaluate warnings `0`
- Relay SQL parity: PASS, `6` seeded scenarios, warnings `0`, failures `0`
- `GET /api/v1/neta/catalog/status`: `catalog=live`, manufacturers `63`, sensors `17831`
- `GET /api/v1/neta/tmt/facets`: `200`, total matching frames `40264`, facets `6`
- `GET /api/v1/neta/emt/facets`: `200`, total matching frames `805`, facets `5`

## Hosted Deploy

Render deploy confirmation: PASS. After push, polling `https://control.apexpowerops.com/api/v1/neta/plot-tcc` showed the new behavior on attempt 4.

Post-deploy route check:

- STD `expected_current`: `9000.0`
- GFD `expected_current`: `960.0`
- LTD `time_limit_low`: `8.399999999999999`
- LTD `time_limit_high`: `12.0`

## Notes

No DDL, migrations, or secret material were introduced.
