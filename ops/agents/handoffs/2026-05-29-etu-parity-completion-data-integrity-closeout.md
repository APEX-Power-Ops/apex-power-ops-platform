# ETU Parity Completion And Data-Integrity Expansion - Closeout

Date: 2026-05-29
Status: PASS with one documented evaluate-side warning
Purpose: Record the bounded host-side completion of ETU parity breadth and the first data-integrity matrix expansion without widening the route-owned ETU contract

---

## 1. Outcome

The previously blocked ETU parity breadth task is now closed truthfully.

Bounded host-side execution completed the live parity matrix expansion while preserving the existing ETU authority contract:

- no ETU route edits were made
- no SQL helper was promoted to runtime authority
- no TMT or EMT widening occurred
- no hosted parity claim was made
- no push was performed

Final live probe result:

- scenario count: `3`
- pass count: `2`
- warn count: `1`
- blocked requirements: `0`

Per-scenario status:

- `sensor-25-ge-mvt-rms9-800-normal`: PASS
- `sensor-26-ge-mvt-rms9-600-live-derived`: PASS
- `sensor-17892-abb-ekip-dip-lvpcb-lsi-100-live-derived`: WARN

The remaining warning is evaluate-side only. Settings parity held across all three scenarios.

---

## 2. Bounded Changes

Files touched:

- `apps/control-plane-api/scripts/etu_parity_matrix.json`
- `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py`
- `PROJECT_STATUS.md`

Bounded outcome:

- upgraded the sensor `26` matrix row from a stale mock-era minimal seed to a live route-derived ETU scenario
- admitted a third scenario from live cascade discovery using alternate trip style `1541` (`ABB · Ekip Dip · LVPCB LSI`, sensor `17892`)
- cleared the historical blocked requirement from the matrix
- added `source_of_truth` notes to every matrix row and surfaced those notes in the parity artifact
- preserved the existing policy that settings mismatches fail hard while evaluate mismatches remain warnings

Route-derived source facts used for expansion:

- sensor `26` live route settings expose active `STPU`, `INST`, `GFPU`, and `GFD` sections; the earlier no-GFPU/minimal seed was no longer truthful
- sensor `17892` was selected from live `vw_trip_unit_cascade` discovery as a non-`trip_style:3`, fixed-plug, no-GFPU ETU row

---

## 3. Validation

Validation commands and results:

1. Alternate-trip-style candidate discovery through the runtime-owned catalog view
   - command: repo-local SQL query against `vw_trip_unit_cascade` plus `tcc_etu_plugs`
   - result: truthful non-`trip_style:3` candidates identified, including sensor `17892`
2. One-off parity check for the two live-derived candidate rows
   - command: repo-local Python wrapper loading `probe_live_etu_sql_parity.py` via `importlib` and probing sensor `26` plus sensor `17892`
   - result:
     - sensor `26`: `pass`
     - sensor `17892`: `warn`
3. Full matrix validation
   - command: `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py --base-url http://127.0.0.1:8010`
   - result: `RESULT PASS: live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 1`

Artifact written:

- `output/dev/control-plane-live-etu-sql-parity.json`

Artifact summary:

- `pass_count: 2`
- `warn_count: 1`
- `warning_count: 1`
- `blocked_requirements: []`

---

## 4. Remaining Warning

The only remaining warning is on sensor `17892` and is limited to evaluate parity.

Observed divergence:

- API `INST.limit_low/high`: `127.5` / `172.5`
- SQL `INST.limit_low/high`: `135.0` / `165.0`

All three scenarios matched on settings, including `ltd_settings`, so the remaining gap is not a settings-surface defect and does not reopen the route-owned contract.

---

## 5. Contract Check

No contract drift was introduced.

Verified preserved boundaries:

- `apps/control-plane-api/services/neta/router.py` remained the ETU runtime authority
- `fn_sensor_available_settings` and `fn_evaluate_test_results` remained parity-only helper surfaces
- no router or helper implementation edits were made in this packet
- no hosted deployment or hosted probe was attempted
- no write-path, schema, or product-surface widening occurred

This closes the admitted parity-completion/data-integrity host-side packet truthfully, with one evaluate-only SQL-helper warning preserved for later bounded follow-up if needed.