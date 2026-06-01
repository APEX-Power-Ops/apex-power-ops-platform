# LV Breaker TCC Live-Wiring Scoping

Date: 2026-06-01

Scope: analysis only. No page, API, route, migration, or database changes were made for this scoping packet.

Primary SSoT anchors:
- `reference/tcc/00-MASTER-INDEX.md`: Single-Source-of-Truth Law and provenance tags.
- `reference/tcc/G0-TRIP-FAMILY-MODEL.md`: SST/ETU, TMT, EMT selection behavior and breaker-to-ETU bridge.
- `reference/tcc/G1-SCHEMA-GUIDE.md`: table and join graph.
- `reference/tcc/G2-RULES-GUIDE.md`: bridge governance, deferred work, and adoption gates.
- `reference/tcc/G3-ROUTING-GUIDE.md`: selection and calc dispatch routing.
- `reference/tcc/G4-CALC-GUIDE.md`: tolerance authority and field-trust matrix.

Implementation surfaces reviewed:
- `apps/operations-web/app/lvbreakertcc/page.tsx`
- `apps/operations-web/TCC_FIELD_TOLERANCES_MVP_SPEC_2026-05-31.md`
- `apps/operations-web/app/breaker-resource-explorer.tsx`
- `apps/operations-web/app/breaker-selection-panels.tsx`
- `apps/operations-web/lib/breaker-resources.ts`
- `apps/control-plane-api/services/neta/router.py`
- `apps/control-plane-api/services/neta/schemas.py`
- `infra/database/migrations/tcc/002_phase4a_repoint_db_objects.sql`
- `infra/database/migrations/tcc/006_brk_styles_sst_bridge.sql`
- `infra/database/migrations/tcc/007_brk_styles_source_id.sql`
- `packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_pickup.py`
- `packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_ltd.py`
- `packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_curves.py`
- `packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_delay_routing.py`

## 1. Current-State Map Of `page.tsx`

The route is a self-contained client component with a polished 3-step shell and no backend calls.
Its local comment explicitly says the numbers are representative placeholders and the real values
must come from the validated backend.

| Current item | What it does today | Keep / replace |
|---|---|---|
| `DEVICE` | Hardcodes Square D P Frame PX 2500A / Micrologic 6.0H, frame, sensor, plug, effective Ir. | REPLACE as data. KEEP the summary-card placement and compact identity presentation. |
| `ELEMENTS` | Hardcodes the 8 element cards: LTPU, LTD, STPU, STD, INST, GFPU, GFD, MAINT, including settings, disabled flags, and pickup bases. | REPLACE as data from selected sensor context, settings, and calc results. KEEP the 8-card concept and active/disabled styling. |
| `MULT_OPTS` | Fixed delay test-multiple choices from 1x through 6x in 0.5 increments. | KEEP as NETA test-current UI affordance, but derive allowed/default values per element where the API returns stricter options. |
| `DELAY_DEFAULT` | Fixed LTD=3x, STD=1.5x, GFD=1.5x. | KEEP defaults as UI defaults, but pass through explicit `*_test_multiple` to plot/calc routes. |
| `BANDS` | Hardcodes nominal, min, max, units, disabled state for the NETA tolerance table. | REPLACE with server-returned rows from `/calculate` or `/plot-tcc.table_rows`, gated by G4 field-trust status. |
| `SETTING_BY_EL`, `BASE_BY_EL` | Derived from hardcoded `ELEMENTS`. | REPLACE with selected settings and calculated test currents. |
| `PLOT`, `px`, `py`, `X_TICKS`, `Y_TICKS` | Log-log SVG geometry. | KEEP. The chart frame is presentational and can consume server points. |
| `NOMINAL`, `bandUp`, `bandLo`, `bandPath`, `MARKERS` | Hardcoded nominal curve, fake tolerance envelope, fake markers. | REPLACE. Server `curves` and `expected_markers` can feed nominal points; true tolerance band remains an engine-gated gap. |
| `STEPS` | Three-screen workflow: specs, settings, curve. | KEEP. This matches the operator workflow. |
| `KIND_CLASS` | Visual tag mapping for element categories. | KEEP, but drive category from live element metadata. |
| `step` state | Stepper state. | KEEP. |
| `maint` state | Client toggle for maintenance mode copy and banner. | KEEP. Wire it into `/calculate`, `/evaluate`, and `/plot-tcc` as `maint_mode`. |
| `mult` state in `Settings` | Tracks selected delay test multiples for LTD, STD, GFD. | KEEP. Send as `ltd_test_multiple`, `std_test_multiple`, `gfd_test_multiple` or the `/calculate` multiplier fields. |
| `measured` state in `Settings` | Local measured-value inputs and PASS/FAIL math against hardcoded `BANDS`. | KEEP as presentation state for read-only/no-persistence MVP. REPLACE nominal/min/max inputs with server data; optionally call `/evaluate` for server pass/fail. |
| `bandTestAt` logic | Recomputes test current labels from hardcoded bases and selected multiples. | REPLACE with server calculated test currents. |
| `% error` and PASS/FAIL table math | Computes `(measured - nominal) / nominal` and local in-band status. | KEEP only as client display math if server returns nominal/min/max. Prefer `/evaluate` for authoritative result semantics once measurements are in scope. |
| `Specifications` screen | Displays read-only hardcoded breaker/trip fields, reference links, notes, summary. | KEEP layout intent. REPLACE fields with live dual-axis selection, confirmation summary, and compatible plug/sensor identity. |
| `Settings` screen | Displays element cards, tolerance table, delay-multiple selects, measured inputs. | KEEP workflow. REPLACE data with `/context`, `/settings`, and `/calculate` results. |
| `Curve` screen | Displays static side info, legend, inline SVG, and static stats. | KEEP chart shell. REPLACE points, legend, stats, and markers with `/plot-tcc` response, with G4 caveats. |
| Inline `CSS` | Owns route-specific visual system. | KEEP unless the operator wants the LV page to inherit operations shell styling. If porting explorer controls, normalize only needed classes to avoid duplicating the old browser shell. |

## 2. Per-Screen Data Contract

### Screen 1: Specifications

Purpose: let the operator select or confirm an LV breaker and the trip-family path. ETU should use the
recovered SST bridge to narrow to compatible sensors. TMT and EMT can remain secondary/fallback paths.

Recommended ETU selection state:

```ts
type LvBreakerEtuSelection = {
  family: 'etu'
  breaker: {
    breaker_class: 'ICCB' | 'MCCB' | 'PCB'
    manufacturer_id: number
    manufacturer_name: string
    breaker_id: number
    breaker_name: string
    breaker_style_id: number
    breaker_style_frame: string | null
    source_id?: number
  }
  bridge: {
    tmt_sst_mfr: string | null
    tmt_sst_type: string | null
    tmt_sst_style: string | null
    bridge_match_status: 'matched' | 'manufacturer_fallback' | 'unmatched'
  }
  trip_unit: {
    manufacturer_id: number
    manufacturer_name: string
    trip_type_id: number | null
    trip_type_name: string | null
    trip_style_id: number
    trip_style_name: string
    tcc_number: string | null
  }
  sensor: {
    sensor_id: number
    sensor_desc: string
    sensor_rating: number | null
    compatible_plug_values: number[]
  }
}
```

Schema and route keys:
- Breaker hardware comes from `tcc.brk_{iccb,mccb,pcb}` and `tcc.brk_{iccb,mccb,pcb}_styles`; see G1
  schema guide and `infra/database/migrations/tcc/005_brk_loadpath_unique_key_reload.sql`.
- The recovered bridge lives in `tcc.brk_*_styles.tmt_use_sst`, `tmt_sst_mfr`, `tmt_sst_type`,
  `tmt_sst_style`, and `source_id`; see `006_brk_styles_sst_bridge.sql` and `007_brk_styles_source_id.sql`.
- Compatible ETU narrowing data exists in `tcc.vw_breaker_sst_bridge` with `breaker_class`,
  `breaker_id`, `breaker_style_id`, `breaker_style_frame`, `tmt_sst_*`, `trip_style_id`,
  `sensor_id`, `sensor_rating`, and `sensor_description`.
- ETU trip cascade exists at `GET /api/v1/neta/cascade`; backed by `vw_trip_unit_cascade` in
  `router.py` and `schemas.py`.
- Existing breaker-axis route is `GET /api/v1/neta/etu/breaker-cascade`; it currently builds an
  `etu_breaker_combined` CTE over breaker tables and cross-filters by manufacturer only. It does not
  consume `vw_breaker_sst_bridge` yet.
- Search fallback exists at `GET /api/v1/neta/etu/search`.
- Catalog status exists at `GET /api/v1/neta/catalog/status`.

TMT/EMT secondary contract:
- TMT browse/settings/plot exists through `/tmt/facets`, `/tmt/frames`, `/tmt/context/{frame_id}`,
  `/tmt/settings/{frame_id}`, and `/tmt/plot-tcc`.
- EMT browse/settings/raw-point plot exists through `/emt/facets`, `/emt/frames`,
  `/emt/context/{frame_id}`, `/emt/settings/{section_id}`, and `/emt/plot-tcc`.
- Per G0, TMT is breaker-integral and EMT has no stored breaker-to-EMT default. Those should not be
  forced through the ETU bridge.

### Screen 2: Protection Settings

Purpose: turn the selected sensor/frame into a field-tolerance surface with element settings,
test currents, tolerance limits, measured values, and pass/fail.

Recommended ETU data bundle:

```ts
type LvProtectionSettings = {
  context: SensorCalcContext
  available_settings: AvailableSettingsResponse
  selected_settings: {
    plug_rating: number
    ltpu_setting?: number
    ltd_delay_setting?: number
    ltd_test_multiple: number
    stpu_setting?: number
    std_delay_setting?: number
    std_test_multiple: number
    inst_setting?: number
    gfpu_setting?: number
    gfd_delay_setting?: number
    gfd_test_multiple: number
    multiplier_value?: number
    c_factor?: number
    maint_mode: boolean
  }
  calculation: CalculateResponse
  measurements: Array<{ element: string; measured_current?: number; measured_time?: number }>
}
```

Field mapping:
- `SensorCalcContext` from `/context/{sensor_id}` provides element availability, `*_calc`, per-sensor
  `*_tol_hi`/`*_tol_lo`, step sizes, delay-routing fields, and maintenance capability. The route reads
  `vw_sensor_calc_context`.
- `AvailableSettingsResponse` from `/settings/{sensor_id}` provides plug values, pickup settings, LTD
  settings, STD settings, GFD settings, and LTD multipliers from `tcc.etu_plugs`,
  `tcc.etu_*_pickups`, `tcc.etu_ltd_bands`, `tcc.etu_std_bands`, and `tcc.etu_gfd_bands`.
- `POST /calculate` returns element rows shaped as `TestCurrentElement`: `element`, `kind`,
  `test_current`, `limit_low`, `limit_high`, `multiplier`, `time_limit_low`, `time_limit_high`,
  `delay_seconds`, `calc_method`, and warnings.
- `POST /evaluate` exists for measured-value pass/fail, but the current LV page can keep local measured
  state if persistence is intentionally out of scope.

G4 trust mapping for the NETA table:
- Pickup tolerances from `*_tol_hi`/`*_tol_lo`: ship now, PROVEN data.
- Pickup currents for calc methods 0-7: ship now, PROVEN arithmetic.
- LTD window: ship, with `DS2_DLY_PTY` caveat.
- STD/GFD direct-band route 0: ship.
- STPU override constant-mode tolerance: ship with override tolerance pair.
- STD/GFD INVEQ route 2: flag and withhold field-sheet promotion until captured EasyPower fixtures
  promote Therm; hard-exclude GF ANSI rows.
- I2X route 1, GE TUSTD/TUG, WEG OCR Type A pickup, and INST override curve math: unsupported/withheld
  unless a future engine packet closes them.

### Screen 3: Time-Current Curve

Purpose: render a faithful enough breaker TCC preview without claiming field-trust for uncertified
curve numbers.

Existing route contract:

```ts
type LvCurvePayload = {
  meta: PlotMeta
  warnings: string[]
  curves: Array<{ id: string; element: string; phase: string; line_style: string; points: { amps: number; seconds: number }[] }>
  expected_markers: PlotExpectedMarker[]
  measured_markers: PlotMeasuredMarker[]
  table_rows: PlotTableRow[]
}
```

Route:
- `POST /api/v1/neta/plot-tcc` exists and returns frontend-ready curves, markers, and table rows.
- Existing explorer code already renders those curves through `BreakerStaticCurveChart` in
  `apps/operations-web/app/breaker-selection-panels.tsx`.

Required additions before treating Screen 3 as faithful:
- Route-level dispatch should consume `etu_delay_routing.route_delay_curve` instead of calling
  `IEEEInverseTimeSolver` directly for STD/GFD nominal curves.
- The response should expose per-element trust status from G4, not just generic warnings.
- The placeholder tolerance envelope (`bandUp`/`bandLo`) must be removed until a real envelope is
  defined. A nominal curve plus field-test markers is safer than a fake band.
- INVEQ Therm curve numbers must remain caveated until captured EasyPower point fixtures pass.
- ANSI GF INVEQ, GE-TU, WEG OCR Type A, and INST override curve paths must surface unsupported status
  instead of silently producing defaults.

## 3. Gap Register

Classification:
- (a) wireable now: data and usable surface exist; mostly frontend fetch/state/render work.
- (b) thin new endpoint: database or engine data exists, but no suitable route or response shape exists.
- (c) engine/research: fidelity depends on unresolved or gated calc work.

| Data need | Backend surface today | Classification | Notes |
|---|---|---:|---|
| Catalog summary | `GET /api/v1/neta/catalog/status`; `router.py`; `vw_trip_unit_cascade`. | (a) | Already used by `BreakerResourceExplorer`. |
| ETU trip cascade | `GET /api/v1/neta/cascade`; `router.py`; `schemas.py`; `vw_trip_unit_cascade`. | (a) | Existing route accepts breaker filters but only narrows by breaker manufacturer today. |
| ETU free-text fallback | `GET /api/v1/neta/etu/search`; `router.py`; `breaker-resources.ts`. | (a) | Useful when bridge match is absent or operator searches by trip unit. |
| Breaker axis browse | `GET /api/v1/neta/etu/breaker-cascade`; `router.py` CTE over `tcc.brk_*`. | (a) | Existing dual-axis UX can be ported from explorer. |
| True breaker-style -> compatible ETU sensor narrowing | `tcc.vw_breaker_sst_bridge` in `006_brk_styles_sst_bridge.sql`; no route uses it yet. | (b) | Add endpoint or bridge mode so `/lvbreakertcc` can collapse compatible sensors beyond manufacturer axis. |
| Stable Access style identity | `source_id` on all `tcc.brk_*_styles`; `007_brk_styles_source_id.sql`. | (a)/(b) | Data exists; expose only if UI needs source identity/debug details. |
| Selection confirmation fields | `/context/{sensor_id}` plus cascade/search result; `ResolvedEquipmentSummary` in schemas. | (a) | TCC number may need route/view confirmation because `SensorCalcContext` schema does not directly declare it. |
| Compatible plug values | `/settings/{sensor_id}` and `/cascade` plug lens; `tcc.etu_plugs`. | (a) | Existing explorer already falls back to search-compatible plugs. |
| Element availability and calc flags | `/context/{sensor_id}`; `vw_sensor_calc_context`; `SensorCalcContext`. | (a) | Use `has_*` and `*_calc` to enable/disable element cards. |
| Per-sensor pickup tolerances | `tcc.etu_sensors.*_tol_hi/*_tol_lo`; `/context`; `/calculate`. | (a) | G4 PROVEN data. Must supersede canned NETA defaults. |
| Pickup and delay setting options | `/settings/{sensor_id}`; direct table reads in `router.py`. | (a) | Already expanded for UI option sets. |
| NETA field-test rows | `/calculate` and `/plot-tcc.table_rows`; `fn_calculate_test_currents`; route-owned delay surface enrichment. | (a)/(b) | Wire now for pickup and direct-band. Add explicit trust/status fields before field-sheet-grade delay promotion. |
| Measured pass/fail | `/evaluate`; or client local math against server limits. | (a) | For read-only preview, local state is enough. Persistence is out of scope. |
| Maintenance mode | `maint_mode` in `/calculate`, `/evaluate`, `/plot-tcc`; maint fields in context and pickup calculator. | (a) | Keep client toggle; pass it to server. Surface warnings. |
| ETU nominal curve points | `POST /plot-tcc`; `_generate_nominal_plot_curves`; `etu_ltd.py`; `etu_curves.py`. | (a)/(c) | Existing payload renders; curve fidelity is bounded and needs dispatch/trust cleanup. |
| Dispatch-aware STD/GFD curve routing | `etu_delay_routing.py` has `route_delay_curve`; `/plot-tcc` does not appear to use it. | (b)/(c) | Thin route patch plus fidelity gates. |
| Faithful tolerance envelope on curve | No faithful endpoint found. Current LV page has fake `bandUp`/`bandLo`. | (c) | Needs engine definition and G4 trust gating. Do not ship fake band. |
| INVEQ Therm curve field promotion | `CalcThermEq` recovered and patched in `etu_curves.py`; G4 says captured fixtures remain. | (c) | Engine work is smaller than before, but still gate-controlled. |
| GF ANSI INVEQ | `CalcAnsiEqGF` recovered but hard-excluded in dispatch. | (c) | Needs family-aware solver path and captured fixtures, or permanent exclusion decision. |
| I2X, GE-TU, WEG OCR, INST override curve math | Some dispatch exists; several paths are deferred/stubbed in G4. | (c) | Must show unsupported/withheld states. |
| TMT selection/settings/plot | `/tmt/*` routes and existing explorer UI. | (a) for browse, (c) for field-grade curve/tolerance parity | Good secondary route, but not the first field-tol MVP path. |
| EMT selection/settings/raw points | `/emt/*` routes and existing explorer UI. | (a) for browse, (c) for runtime parity | EMT has no stored breaker default per G0. Treat as runtime-selected catalog path. |
| Reference links/resources | `page.tsx` hardcodes links; `GET /apparatus/{apparatus_id}/resources` is apparatus-scoped. | (b)/(c) | Need a trip-style/breaker-style resource mapping if links must be live. Otherwise omit or keep manual placeholders outside MVP. |

## 4. Curve Deep-Dive

Existing implementation pieces:
- `ETUPickupCalculator` in `etu_pickup.py` computes LTPU, STPU, INST, GFPU pickup currents from
  `tcc.etu_sensors.*_calc`, plug, multiplier, C factor, STPU override, and maintenance-mode data.
- `ETULTDCalculator` in `etu_ltd.py` implements LTD methods 1-5 and reads `tcc.etu_ltd_params`,
  `tcc.etu_ltd_bands`, and `tcc.etu_sensor_params`.
- `IEEEInverseTimeSolver` in `etu_curves.py` loads `tcc.etu_std_equations` and
  `tcc.etu_gfd_equations`. It now detects the native Therm row shape and evaluates the recovered
  `CalcThermEq` formula using `c4`/`c5`.
- `etu_delay_routing.py` encodes `SSTDelayCalc` for STD/GFD routes, including INVEQ dispatch,
  I2X band-anchor routing, TUSTD/TUG unsupported diagnostics, WEG OCR Type A exclusion, and GF ANSI
  INVEQ exclusion.
- `POST /plot-tcc` in `router.py` already returns curves, expected markers, measured markers, and a
  companion table. It is the correct frontend precedent.
- `POST /relay/plot-tcc` is the closest route precedent for a server-computed preview contract with
  explicit warnings and unsupported-family behavior.

Main curve gaps:
1. The current LV page curve is entirely fake: static `NOMINAL`, static markers, and a synthetic
   tolerance band.
2. `/plot-tcc` currently calls `IEEEInverseTimeSolver` directly in `_generate_nominal_plot_curves`
   for STD/GFD. That bypasses the explicit dispatch contract in `etu_delay_routing.py`, so it is not
   the field-trust gate by itself.
3. A faithful breaker TCC is not just raw section curves. It needs selected settings, pickup currents,
   LTD/STD/INST/GFD section curves, open/clear phases, route-specific unsupported diagnostics,
   maintenance-mode behavior, and possibly merged composite curves. `etu_merge.py` exists as a merge
   utility, but the reviewed plot route does not appear to use it for the LV page contract.
4. G4 still gates field promotion for Therm INVEQ until captured EasyPower point fixtures validate the
   patched native formula path. GF ANSI is explicitly excluded. GE-TU, WEG OCR Type A, I2X details,
   and INST override remain constrained by G4.
5. No faithful tolerance envelope surface was found. The route can provide nominal curves and markers;
   a shaded tolerance band needs a separate, trust-classified definition.

Recommended curve approach:
- Stage C1: replace LV hardcoded SVG points with `/plot-tcc` curves and markers, but label it
  "server preview" and show route warnings. Remove the fake tolerance envelope.
- Stage C2: patch the plot route to call `route_delay_curve` for STD/GFD and to return
  `trust_status` per curve/table row, aligned with G4.
- Stage C3: add captured EasyPower fixtures for representative Therm INVEQ rows. Promote only the
  rows G4 allows. Keep GF ANSI excluded unless the operator authorizes an ANSI solver path.
- Stage C4: decide whether composite breaker curves are required for MVP or whether per-element
  curves plus expected markers are enough for the field-tolerance workflow.

Fidelity caveat:
- Per G4, pickup tolerances and pickup currents are field-sheet safe now.
- Direct-band STD/GFD and LTD windows are shippable under the matrix.
- INVEQ and several solver families are not field-sheet safe yet. The UI must not let a curve preview
  imply field-trust where G4 says "withhold" or "unsupported."

## 5. Proposed Solution Per Gap

| Gap | Proposed solution | Effort | Risk |
|---|---|---:|---:|
| LV page has no fetch layer | Import/reuse `breaker-resources.ts` types/fetch helpers or extract LV-specific wrappers over the same routes. | S | Low |
| Specs screen has no dual-axis state | Port the ETU portions of `BreakerResourceExplorer` state: breaker axis, trip axis, reset behavior, selected sensor, context load. | M | Medium because state reset bugs can create stale selections. |
| True bridge narrowing has no route | Add a thin read-only endpoint over `tcc.vw_breaker_sst_bridge`, or add a `compatible_only` mode to `/cascade` and `/etu/breaker-cascade`. | S/M | Medium because it changes selection semantics and must preserve manufacturer-fallback behavior for unmatched bridge rows. |
| Selection confirmation needs nameplate-grade identity | Reuse `ResolvedEquipmentSummary`, add `tcc_number`/bridge-status fields where absent, and show compatible plugs. | S | Low |
| Protection cards are hardcoded | Drive element cards from `/context`, `/settings`, and selected values. Use `has_*` and `*_calc=-1` to disable. | M | Medium because settings have per-sensor sparsity. |
| NETA table hardcoded | Populate from `/calculate` or `/plot-tcc.table_rows`; include G4 trust status and warnings. | M | Medium because delay rows must not over-claim INVEQ/I2X/unsupported paths. |
| Measured local math uses fake bands | Keep local inputs, but compute against server limits; optionally call `/evaluate` when measured values change or when user clicks Evaluate. | S/M | Low for local, medium for server debounce/UX. |
| Maintenance mode is UI-only | Thread `maint_mode` through calculate/evaluate/plot requests and display server warnings. | S | Low |
| Curve uses fake points and band | Consume `/plot-tcc` for nominal curves and expected markers; delete fake band. | M | Medium because empty/unsupported curve states must be well designed. |
| Plot route is not dispatch-aware enough for field trust | Patch server route to use `route_delay_curve` and expose trust classifications. | M/L | High due to calc fidelity and regression burden. |
| INVEQ field promotion | Capture EasyPower fixtures for Therm, then promote only passing families. Keep ANSI excluded unless separately authorized. | L | High because it depends on external captured fixtures and operator trust decision. |
| TMT/EMT in LV workflow | Keep family selector but ship ETU first. Wire TMT/EMT browse using existing routes as bounded secondary surfaces. | M | Medium because TMT/EMT should not look equivalent to ETU field-trust. |
| Reference links | Defer unless a real resource mapping is available. Do not keep fake PDF links as if live. | S/M | Low if omitted; medium if a new mapping is needed. |

## 6. Staging Recommendation

Recommended sequence: A -> B -> C, with a temporary diagnostic explorer retained until Stage B is verified.

### Stage A: Specifications live-select plus bridge narrowing

Value shipped:
- The LV page stops being a frozen demo.
- Operator can choose breaker class/manufacturer/breaker/style and see compatible ETU sensors.
- The D1 bridge finally affects UX, not just schema.

Work:
- Port the explorer's dual-axis ETU controls into `Specifications`.
- Add the thin bridge endpoint or route mode over `tcc.vw_breaker_sst_bridge`.
- Preserve manufacturer fallback for bridge misses per G0/G2.
- Store selected breaker context and selected ETU sensor for downstream screens.

Dependencies:
- `006_brk_styles_sst_bridge.sql` and `007_brk_styles_source_id.sql` already landed.
- Needs read-only API patch only if no existing route is repurposed.

### Stage B: Protection Settings live NETA tolerance bands

Value shipped:
- This is the field-tolerance MVP core.
- The operator can confirm a sensor, pick settings/plug, and see DB-authoritative test currents and
  tolerance bands.

Work:
- Wire `/context/{sensor_id}` and `/settings/{sensor_id}`.
- Build request payloads for `/calculate`.
- Render element cards and NETA table from server rows.
- Add G4 trust labels for delay rows.
- Keep measured inputs local or call `/evaluate` when operator requests evaluation.

Dependencies:
- Stage A selected sensor.
- G4 gating rules.

### Stage C: Curve preview and then faithful curve promotion

Value shipped:
- A server-driven curve preview replaces placeholder SVG numbers.
- Later, after engine gates, the curve can become field-trustworthy where G4 permits.

Work:
- Wire `/plot-tcc` curves/markers into the existing inline SVG.
- Remove synthetic tolerance band.
- Patch `/plot-tcc` to use delay dispatch and return trust statuses.
- Add captured EasyPower fixtures for Therm INVEQ before promoting those curve numbers.

Dependencies:
- Stage B selected settings.
- Calc-engine fixture work for full fidelity.

Optional Stage D: export and persistence

Value shipped:
- A printable/exportable field sheet and/or saved test plan.

Boundary:
- Requires an operator decision on read-only vs authenticated persistence. Not needed for Stages A/B.

## 7. Explorer-Consolidation Decision

Recommendation: port the explorer's ETU dual-axis selection logic into `/lvbreakertcc`, keep the current
`BreakerResourceExplorer` temporarily as a diagnostic/reference panel, then retire or hide it after the
LV page reaches Stage B parity.

Reasoning:
- The operator workflow is the LV TCC page, not a generic browser. The LV page owns the correct
  sequence: specifications -> protection settings -> curve.
- The existing explorer already proves the route contracts and state transitions. It should be mined
  for behavior rather than rebuilt from scratch.
- Keeping both as long-term primary surfaces risks divergent filtering, route usage, and G4 trust
  labeling.
- The old operations-web shell is explicitly a placeholder-like surface in repo copy; the LV page is
  the better destination for field-tolerance product behavior.

Retirement trigger:
- `/lvbreakertcc` supports ETU breaker-axis selection, trip-axis narrowing, selected-sensor confirmation,
  `/context`, `/settings`, and `/calculate` NETA rows with G4 warnings.
- A smoke run verifies that a bridge-backed breaker style narrows to compatible sensor rows.

Keep temporarily:
- Leave `BreakerResourceExplorer` on `operation.apexpowerops.com` until Stage B ships and a separate
  removal packet approves hiding/removal. It is still useful for TMT/EMT bounded browsing.

## 8. Decision Points For The Operator

1. Should Stage A add a new endpoint over `tcc.vw_breaker_sst_bridge`, or should existing
   `/cascade` and `/etu/breaker-cascade` gain a compatible-bridge mode?
2. Should the first build be ETU-only, with TMT/EMT left in the explorer until later, or should the
   LV page carry the family selector from day one?
3. For Stage B, should measured values stay local/read-only, or should the page call `/evaluate` for
   server pass/fail on demand?
4. Should the MVP show bounded curve preview in Stage C1, or hide the curve screen until dispatch-aware
   plot routing and G4 trust statuses are present?
5. Is a nominal-only curve acceptable for MVP, or is a faithful tolerance envelope required before the
   curve screen is considered useful?
6. Should INVEQ Therm be displayed with caveats before captured EasyPower fixtures, or withheld from
   field-facing curve output until fixtures pass?
7. Should GF ANSI INVEQ stay permanently excluded for MVP, or should a separate ANSI solver packet be
   opened?
8. What is the minimum nameplate-confirmation vocabulary for the operator: breaker style frame,
   source ID, TCC number, sensor description/rating, compatible plugs, or more?
9. Should fake/manual reference links be removed until live resource mappings exist, or kept as
   non-live placeholders during design review?
10. When Stage B is verified in `/lvbreakertcc`, should the generic breaker explorer be hidden from the
    main operations page or moved behind a diagnostic/admin route?
