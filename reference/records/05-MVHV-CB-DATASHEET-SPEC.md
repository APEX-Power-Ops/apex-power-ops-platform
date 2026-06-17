# Chip 2b - MV/HV Circuit-Breaker Datasheet Spec (`ats_mvhv_cb_v1`)

> **Status:** BUILT + validated - 2026-06-17. Migration `011` + `gen_mv_cb_template.py` +
> `test_011_mvhv_cb_template.py` (21/21 on `records_dev`). The second real datasheet on the Chip-2
> foundation; the first to exercise the **multi-procedure union** coverage invariant.
> Cite `00-MASTER-INDEX.md` §4, the Chip-2 field-field design (memory
> `records-chip2-form-field-design`), the LV sheet spec `04-LV-CB-DATASHEET-SPEC.md` (shared
> `field_schema` contract), and the NETA 2a reference (`records.neta_*`, migrations `005`/`006`).
>
> **Sourcing law (load-bearing):** authoritative field CONTENT = NETA 7.6.1.3 / 7.6.2 / 7.6.3 / 7.6.4
> (the `records.neta_*` seed) + operator review. The incumbent's house library (Prime Engineering
> `*Prime Engineering*` family, read structure-only) confirms the *module-library, build-to-need*
> shape and that "MV/HV is the rich set." Field-trust applies: acceptance = manufacturer tolerance or
> the labeled NETA-table fallback; absent a basis, the window is withheld, never invented.

---

## 1. Decisions locked (this chip)

| ID | Decision |
|---|---|
| **Model** | ONE composite `cb_mvhv` template with an **interrupting-medium selector** (air / oil / vacuum / SF6) driving `visible_if`. Not four templates. The four media ARE four NETA procedures; the composite covers their union and gates each medium's deltas. (operator, 2026-06-17 - "Approved") |
| **R-A** (operator-confirmed) | Acceptance-window fields carry a declarative **`tolerance_source`**, but for MV/HV the source is **`neta_table` + `mfr`, NOT `tcc`** - an MV/HV breaker has **no integral trip curve** (protection is external protective relays, NETA 7.9 / relaytcc). Values resolve at provisioning (Chip 5) and ride down to the device. The `mfr` engine is the slot the future mfr-tolerance layer plugs into with zero template change ("ideally down the road the mfr layer would serve this family as well" - operator). |
| **R-B** | Keep **all** NETA visual/mechanical items across the four media as the spine; render compactly with the Inspected / Condition / Clean-Lube grid. Each item's medium gate is auto-derived from the procedures that list it. |
| **R-C** | **Nameplate identity = asset attributes** (`data_source: inherited`); **As-Found/As-Left readings = per-visit submission fields** (`data_source: data`); **header** = platform context, not template fields. |
| **No DDL** | Everything lives in `records.form_templates.field_schema` (JSONB). Same contract as the LV sheet (`04` §2). |

---

## 2. The `field_schema` contract

Identical to the LV sheet - see `04-LV-CB-DATASHEET-SPEC.md` §2 (object `{version, family, selections,
sections}`; controls carry `tag/label/value_kind/unit?/options?/data_source/neta_ref?/acceptance?/
tolerance_source?`). The MV/HV differences are **content**, not contract:

- **Selector** is `interrupting_medium` (options `air|oil|vacuum|sf6`, `ties_to: equipment_model`) plus
  `mounting` (drawout/fixed) and a `tests_performed` multiselect.
- **`visible_if` is auto-derived**: a concept present in all four procedures has no gate; a delta is
  gated to exactly the media whose NETA procedure lists it (e.g. `arc_chutes` -> air; `oil_level` ->
  oil; `contact_gap` -> vacuum; `sf6_gas` -> sf6).
- **`tolerance_source.engine` is `neta_table` or `mfr`** (validator-enforced; never `tcc`).

---

## 3. MV/HV-CB composite - sections (as built = 15 sections)

Header (Asset ID, Position, Substation, Job #, Customer, Date, Ambient, Tested-By, Page) is **platform
context** - supplied by `assets` + `form_submissions`, not in `field_schema`.

| # | Section `key` | kind | basis | medium gate | Notes |
|---|---|---|---|---|---|
| 1 | `nameplate` | fields | 7.6.1.3 | - | identity `inherited` (mfr, model, medium, kV, A, kA, BIL, mechanism, control V, mounting, poles) + nameplate-vs-drawings |
| 2 | `visual_mechanical` | **table** | 7.6.1.3 | per-row auto | 25 inspection rows; common core + air/oil/vacuum/SF6 deltas; Inspected/Condition/Clean-Lube grid |
| 3 | `operation_counter` | fields | - | - | AF/AL counter (numerics don't fit the VM grid) |
| 4 | `contact_timing` | table | - | tests | per-pole close/open AF/AL ms; `tolerance_source` -> **mfr** |
| 5 | `insulation_resistance` | table | - | - | per pole + across-open + control-wiring; `reading_mohm` -> **neta_table 100.1**; TCF |
| 6 | `contact_resistance` | table | - | per-row | contact/pole + static + dynamic + bus-bolted + blowout-coil (medium-gated); uohm/pole -> **mfr** |
| 7 | `dielectric_withstand` | table | - | tests | hipot per phase -> **neta_table 100.19**; + vacuum-bottle integrity + MAC (vacuum-gated rows) |
| 8 | `power_factor` | table | - | tests | breaker open/closed + bushings; acceptance = comparison (no NETA table) |
| 9 | `pickup_coils` | table | - | tests | trip/close coil min pickup AF/AL -> **neta_table 100.20** |
| 10 | `insulating_liquid` | fields | 7.6.2 | **oil** | dielectric breakdown, IFT, neutralization, water, PF (ASTM D923) |
| 11 | `sf6_gas` | fields | 7.6.4 | **sf6** | moisture -> **neta_table 100.13**, purity, decomposition, pressure |
| 12 | `auxiliary` | fields | 7.6.1.3 | per-field | close/trip, trip-free, anti-pump, test-position (air), trip-by-protective-device (oil/vac/sf6), heaters |
| 13 | `instrument_transformers` | fields | 7.10 | oil/vac/sf6 | **cross-reference only** - the 7.10 borrow is recorded on the IT datasheet, not here (covered, not fabricated) |
| 14 | `test_equipment` | table | - (QA) | - | cal-traceable witness footer |
| 15 | `comments_deficiencies` | fields | - | - | repeating text |

> **As-built note (honest delta from the 14-ish I previewed):** the instrumented MV tests that don't
> fit a checkbox - contact timing, dielectric/hipot, power-factor, minimum pickup - each became their
> own measured section (vs the LV sheet, which had fewer of them), and the oil/SF6 fluid-gas analyses
> are their own gated sections. Hence **15 sections**. Coverage is unchanged - every NETA item is still
> mapped; the breakout is a rendering choice, not a scope change.

---

## 4. Coverage matrix - the union invariant (proves 100% of prescribed items map)

The four procedures share a large common core and diverge at the medium-specific deltas. The composite
covers the **union of all ATS visual_mechanical + electrical items across all four** - **122 items**
(air 19+10, oil 19+14, vacuum 16+13, SF6 18+13). Each composite concept declares the per-medium refs it
satisfies (`{section}.{A|B}.{item_number}`); the section's `neta_covers` is their union.

- **Common core** (all 4 media): nameplate, phys/mech, anchorage, maint devices, clean, mechanical
  operation, torque (100.12), lubrication, mechanism-motion, coil-signature, thermography, contact
  timing, op counter; IR (100.1), control-wiring IR, dielectric (100.19), power-factor (breaker +
  bushing), min pickup (100.20), heaters.
- **Drawout deltas:** cell-fit (air+vac), racking (air+oil+vac).
- **Air:** arc chutes, puffer, moving/stationary contacts; blowout-coil resistance.
- **Oil:** oil level, breather, hydraulic/compressor, pneumatic/hydraulic alarms, internal inspection;
  static + dynamic + bus-bolted resistance; insulating-liquid sample (ASTM D923); tank-loss-index (PF).
- **Vacuum:** contact-gap; MAC test; vacuum-bottle integrity.
- **SF6:** SF6-system inspect, gas-leak test, gas sample (100.13), gas-pressure alarms; static+dynamic
  resistance.
- **Borrowed (cross-ref):** instrument transformers per 7.10 (oil/vac/sf6) - covered as a cross-reference
  line; the actual IT test lives on the Instrument-Transformer datasheet.

> **Coverage invariant (validator-enforced, `gen` fail-fast + `test_011`):** the union of every section's
> `neta_covers` equals the full 122-item required set read from `records.neta_test_items` for the four
> procedures (`standard='ats'`, category in {visual_mechanical, electrical}). No silent drops; no phantom
> refs (every covered ref is a real item).

---

## 5. Interrupting-medium conditional summary (the composite, one selector)

| Medium | NETA proc | Distinct sections / rows shown |
|---|---|---|
| Air (MV) | 7.6.1.3 | arc chutes, puffer, contacts; blowout-coil resistance row; (drawout: cell-fit, racking) |
| Oil (MV/HV) | 7.6.2 | `insulating_liquid` section; oil-level/breather/hydraulic/alarms VM rows; static+dynamic+bolted R |
| Vacuum (MV) | 7.6.3 | vacuum-bottle integrity + MAC rows; contact-gap VM row; (drawout: cell-fit, racking) |
| SF6 | 7.6.4 | `sf6_gas` section; SF6-system/gas-leak/gas-alarm VM rows; static+dynamic R |

The common core renders for every medium; only the deltas above gate in/out. This is exactly why one
composite + selector beats four templates - the medium difference is a set of `visible_if` flags.

---

## 6. Notes / deferred

- **R-A is apparatus-appropriate, not abandoned.** The declarative `tolerance_source` seam is unchanged
  from LV; it simply names the right engine per apparatus: LV breaker -> `tcc` (integral trip curve),
  MV/HV breaker -> `neta_table` + `mfr` (no trip curve), relay -> `relaytcc` (its own datasheet). The
  future mfr-tolerance layer serves the `mfr` slot with no template change.
- **No integral protection on the breaker.** MV/HV overcurrent protection is the external relay (7.9);
  the breaker datasheet records mechanical/dielectric/contact condition. "Trip by each protective device"
  is a breaker pass/fail; the relay's pickup/timing tolerances live on the relay datasheet.
- **Deferred (not this chip):** the calc engine (`data_source: calc` - TCF, corrected IR, pass/fail) =
  D-FORMS; window-value resolution from NETA tables / mfr = Chip 5 (provisioning). This chip delivers the
  template definition + validator + coverage matrix, seeded on `records_dev`.
