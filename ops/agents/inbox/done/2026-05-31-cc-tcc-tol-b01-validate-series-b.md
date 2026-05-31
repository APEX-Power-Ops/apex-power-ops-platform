---
dispatch_id: 2026-05-31-cc-tcc-tol-b01-validate-series-b
target: CC
priority: 1
from: Desktop
created_at: 2026-05-31
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-05-31-tcc-tol-b01-validate-series-b-closeout.md
---

# B0.1 — Validate the tool's NETA tolerances against the Square D MicroLogic Series B reference (ETU)

**Lane:** TCC Field Tolerances MVP. **Spec of record:** `apps/operations-web/TCC_FIELD_TOLERANCES_MVP_SPEC_2026-05-31.md` (read it first — the per-element reference method is there). **READ-ONLY: no DDL, no code changes, no migrations.** This proves the engine's numbers are field-trustworthy before any sheet/UI is built. Follow the inbox lifecycle (claim-push before any work).

## Why
Field techs will rely on the tool's PU/TD tolerances. We have a trusted off-repo reference calculator for **Square D MicroLogic Series B** (Full SE main, Std MX 250-800, Std 1600). The tool's `tcc.*` catalog shares the EasyPower lineage that calculator was derived from, so the tool *should* reproduce it. Verify that it does — and characterize any delta.

## Reference method (the expected behavior — from the spec)
Per element, given a `setting` and `rating-plug`:
- **LTPU**: test current = `setting × plug`; band **±7.5%** → `[test×0.925, test×1.075]`.
- **STPU**: test current = `plug × setting`; band **±15%** → `[test×0.85, test×1.15]`.
- **INST**: test current = `setting × plug`; band **±15%**.
- **GFPU**: test current = `setting` (absolute amps); band **±10%** → `[test×0.9, test×1.1]`.
- **LTD**: test = `3× LTPU`; delay window `setting·0.7·(6/mult)²` → `setting·(6/mult)²`.
- **STD/GFD** (flat): delay LOOKUP at `1.5× pickup`; **STD\*/GFD\*** (I²t): LOOKUP rescaled by `((In·12)/test)²` (STD\*) and the GFPU basis (GFD\*).

Worked example (Full SE main, 4000A sensor, plug=3000, LTPU setting=0.5): LTPU test = 1500 A, MIN 1387.5, MAX 1612.5; STPU setting=2 → test 6000, MIN 5100, MAX 6900; GFPU=640 → MIN 576, MAX 704.

## Steps (read-only)
1. **Claim** (git mv pending→claimed, push) before any work.
2. **Locate** a Square D MicroLogic Series B trip unit in `tcc.*`: find the trip_type/trip_style/sensor rows for the Square D (manufacturer) MicroLogic Series B family that best match each reference tab (Full SE main; Std MX 250/400/600/800; Std 1600). Note the `trip_type_id`/`trip_style_id`/`sensor_id` and `compatible_plug_values`. If the catalog has no clean "Series B" descriptor, pick the closest MicroLogic match and **state the mapping assumption** explicitly.
3. **Pull the tool's tolerances** for ≥1 sensor per tab via the deployed path the field will use: `GET /settings/{sensor_id}` for the available setting domain, then `POST /plot-tcc` (with the chosen plug + settings) and read `table_rows` (`element, setting, test_multiple, expected_current, limit_low, limit_high, expected_time, time_limit_low, time_limit_high, calc_method`). Use the governed read-only DSN / hosted `control.apexpowerops.com` — DSN out-of-band, never printed.
4. **Compare** per element to the reference method above. Build a delta table: element | tool expected/lo/hi | reference expected/lo/hi | match? | note.
5. **Characterize deltas** — for any mismatch, determine the cause (different band rule, plug/sensor mapping, I²t rescale basis, absent-element handling) from `tcc.*` + the calc-engine, and say whether the *tool* or the *reference assumption* is right. Do NOT change code; this is diagnosis.

## Acceptance
- A per-element pass/delta table for at least the Full SE main + one Std MX rating.
- A clear verdict: does the tool reproduce the Series B reference within rounding? If not, the exact divergences + root cause, so Tier 2 (the tolerance sheet) can either trust the tool or target a fix.

## Guardrails
- READ-ONLY. No DDL/migrations/code. No `.env*` contents; DSN out-of-band. PUBLIC repo — no client/job identifiers in the closeout (refer to "the Series B reference calculator" generically).

## Closeout
Record: the catalog mapping (trip_type/style/sensor ids per tab + any assumption), the per-element delta tables, the verdict, and any root-caused divergence. Then `git mv` claimed→done, commit, push. **Next:** B2.1 (tolerance-sheet export) depends on this verdict; B0.2 (TMT characterization) is the parallel read-only item.
