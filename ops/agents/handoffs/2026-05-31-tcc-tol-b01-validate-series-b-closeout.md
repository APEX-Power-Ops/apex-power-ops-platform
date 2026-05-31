# B0.1 Closeout - Square D MicroLogic Series B ETU tolerance validation

Date: 2026-05-31
Packet: `2026-05-31-cc-tcc-tol-b01-validate-series-b`
Target lane: CC
Mode: read-only live validation

## Scope

Validated the hosted `/api/v1/neta/settings/{sensor_id}` and `/api/v1/neta/plot-tcc`
field path against the reference method in
`apps/operations-web/TCC_FIELD_TOLERANCES_MVP_SPEC_2026-05-31.md`.

No DDL, migrations, or application code changes were made.

## Catalog Mapping

Live `vw_trip_unit_cascade` has a direct Square D MicroLogic Series B mapping for the
full SE tab:

| Reference tab | Live mapping | Sensors / notes |
| --- | --- | --- |
| Full SE main | Square D / `Micrologic Full` / `SE Series B` / `trip_type_id=325`, `trip_style_id=2455`, `tcc_number=678-10` | `sensor_id=30338` for 3000A; `sensor_id=30245` for 4000A |
| Std MX 250/400/600/800 | Square D / `Micrologic Std` / `MX` / `trip_type_id=326`, `trip_style_id=241`, `tcc_number=666-11` | 250=`1863`, 400=`1864`, 600=`26973`, 800=`1865` |
| Std 1600 | Square D / `Micrologic Std` / `PX-6B` / `trip_type_id=326`, `trip_style_id=231` | 1600=`1701`; `PX` 1600-LSG also exists as `14336` but has fixed/non-reference-like settings |

Mapping caveat: the packet's worked example says 4000A sensor with 3000A plug. The exact
`SE Series B` 4000A row (`sensor_id=30245`) only exposes plugs `3200` and `4000`.
The exact `SE Series B` 3000A row (`sensor_id=30338`) exposes plug `3000` and reproduces
the worked-example pickup currents. A non-Series-B `ICCB SE` 4000A row (`sensor_id=9000`)
also exposes plug `3000`, but its stored tolerances do not match the Series B reference.
The delta tables below therefore use `sensor_id=30338` for the worked-example current
shape and `sensor_id=1864` for one Std MX rating.

## Hosted Validation Payloads

Full SE Series B:
`sensor_id=30338`, plug `3000`, LTPU `0.5`, LTD delay setting `3`, STPU `2`,
STD test multiplier `1.5`, INST `3`, GFPU `640`, GFD test multiplier `1.5`.

Std MX 400:
`sensor_id=1864`, plug `400`, LTPU `0.5`, LTD delay setting `3`, STPU `2`,
STD test multiplier `1.5`, INST `3`, GFPU setting `0.2` (catalog per-unit setting,
80A effective), GFD test multiplier `1.5`.

Note: the hosted route currently overloads `ltd_setting`, `std_setting`, and
`gfd_setting` as both delay-band selectors and test multipliers. I used
reference-aligned multipliers (`3`, `1.5`, `1.5`) to validate the reference math.
When field-band open times are passed for STD/GFD, the route reports `test_multiple`
as the open time and computes incorrect delay test currents.

## Full SE Series B Delta Table

Sensor `30338`, plug `3000`.

| Element | Tool expected / lo / hi | Reference expected / lo / hi | Match? | Note |
| --- | --- | --- | --- | --- |
| LTPU | `1500 / 1387.5 / 1612.5` | `1500 / 1387.5 / 1612.5` | yes | Matches +/-7.5%. |
| STPU | `6000 / 5100 / 6900` | `6000 / 5100 / 6900` | yes | Matches +/-15%. |
| INST | `9000 / 7650 / 10350` | `9000 / 7650 / 10350` | yes | Matches +/-15% on this exact row. |
| GFPU | `640 / 512 / 640` | `640 / 576 / 704` | no | Live context stores GFPU tolerance as `-20% / 0%`; reference requires +/-10%. |
| LTD | current `4500`, time `3 / 3 / null` | current `4500`, time `null / 8.4 / 12` | no | Current matches; route reports direct band open time instead of reference formula `setting*0.7*(6/mult)^2` to `setting*(6/mult)^2`. |
| STD | current `9000`, time `0.06 / 0.06 / 0.1` | current `9000`, time `0.06 / 0.06 / 0.1` | yes | Matches first flat band when `1.5` multiplier is supplied. |
| GFD | current `960`, time `0.06 / 0.06 / 0.1` | current `960`, time `0.06 / 0.06 / 0.1` | yes | Matches first flat band when `1.5` multiplier is supplied. |

## Std MX 400 Delta Table

Sensor `1864`, plug `400`.

| Element | Tool expected / lo / hi | Reference expected / lo / hi | Match? | Note |
| --- | --- | --- | --- | --- |
| LTPU | `200 / 185 / 215` | `200 / 185 / 215` | yes | Matches +/-7.5%. |
| STPU | `800 / 730 / 900` | `800 / 680 / 920` | no | Live context stores `-8.75% / +12.5%`; reference requires +/-15%. |
| INST | `1200 / 1110 / 1320` | `1200 / 1020 / 1380` | no | Live override tolerance is effectively `-7.5% / +10%`; reference requires +/-15%. |
| GFPU | `80 / 56 / 80` | `80 / 72 / 88` | no | Catalog setting `0.2` is 80A effective, but live context stores `-30% / 0%`; reference requires +/-10%. |
| LTD | current `600`, time `3 / 3 / null` | current `600`, time `null / 8.4 / 12` | no | Same direct-band-vs-reference-formula issue as Full SE. |
| STD | current `1200`, time `0.07 / 0.07 / 0.1` | current `1200`, time `0.07 / 0.07 / 0.1` | yes | Matches first flat band when `1.5` multiplier is supplied. |
| GFD | current `120`, time `0.07 / 0.07 / 0.1` | current `120`, time `0.07 / 0.07 / 0.1` | yes | Matches first flat band when `1.5` multiplier is supplied. |

## Route Contract Finding

The deployed field route cannot fully express the reference delay method today:

- `std_setting=1.5` gives the reference STD test current and falls back to the first
  STD band for timing.
- `std_setting=<band open_time>` gives the selected band timing but changes
  `test_multiple` to the open time and produces a wrong test current.
- The same issue applies to `gfd_setting`; LTD has the same single-field ambiguity
  but `ltd_setting=3` happens to match the fixed LTD test multiplier.

Observed with exact SE Series B `sensor_id=30338` and band-open-time payload:

| Element | Tool `test_multiple` | Tool `expected_current` | Reference expected current |
| --- | ---: | ---: | ---: |
| STD | `0.06` | `360` | `9000` |
| GFD | `0.06` | `38.4` | `960` |

## Verdict

The hosted tool does **not** fully reproduce the Series B reference within rounding.

What is trustworthy now:

- Series B LTPU/STPU/INST pickup currents and bands match the reference on the exact
  `SE Series B` row tested.
- Std MX LTPU matches.
- STD/GFD flat delay rows can match the first band if the caller supplies `1.5` as
  the multiplier.

What needs a targeted fix before Tier 2 sheet export can trust `table_rows`:

- GFPU tolerance should be normalized to +/-10% for the Series B reference surface;
  live context currently carries legacy asymmetric GFPU tolerances.
- Std MX STPU/INST/GFPU tolerances use catalog-specific asymmetric values rather than
  the reference bands.
- LTD timing should emit the reference delay window, not direct band open time only.
- Delay request/response modeling needs separate fields for selected delay band and
  NETA test multiplier, otherwise field payloads using band open times corrupt STD/GFD
  test currents.

## Read-Only Verification

- Queried live `vw_trip_unit_cascade` and `vw_sensor_calc_context` with the canonical
  live DSN sourced out-of-band; no DSN value was printed.
- Called hosted `GET /api/v1/neta/settings/{sensor_id}` and
  `POST /api/v1/neta/plot-tcc` on `https://control.apexpowerops.com`.
- No schema, migration, or code writes were performed.
