# Chip 2b — LV Circuit-Breaker Datasheet Spec (the first real `field_schema`)

> **Status:** BUILT + validated — 2026-06-17. Red-lined leans applied. Migration `010` +
> `gen_lv_cb_template.py` + `test_010_lv_cb_template.py` (17/17 on `records_dev`).
> Branch `records/chip2b-lv-cb` (dev-only; not on prod, not PR'd).
> The first concrete datasheet built on the Chip-2 foundation. Cite `00-MASTER-INDEX.md` §4,
> the Chip-2 field-field design (memory `records-chip2-form-field-design`), and the NETA 2a
> reference (`records.neta_*`, migrations `005`/`006`).
>
> **Sourcing law (load-bearing):** authoritative field CONTENT = NETA 7.6.1.x (the `records.neta_*`
> seed) + the incumbent's proven sheet as a STRUCTURE witness (PowerDB form 15055, vendor
> Translate-PXD) + operator review. The witness informs *what a real sheet captures and how it
> renders*; it is never copied verbatim, and nothing is fabricated. Field-trust applies:
> acceptance = manufacturer tolerance; absent a basis, the window is withheld, never invented.

---

## 1. Decisions locked (this chip)

| ID | Decision |
|---|---|
| **Model** | ONE composite `cb_lv` template with a **construction-type selector** (Power / Insulated-Case / Molded-Case) driving `visible_if`. Not three templates. (operator, 2026-06-17) |
| **R-A** | Acceptance-window fields are first-class and carry a declarative **`tolerance_source`** binding to the TCC engine; the **values resolve at provisioning (Chip 5)** and ride down to the device. The template is built to be *served by* lvbreakertcc — the designed intent — but stays offline-native. |
| **R-B** | Keep **all 16 NETA 7.6.1.2 visual/mechanical items** as the spine; render compactly with the witness's Inspected / Condition / Clean-Lube qualifiers. |
| **R-C** | **Nameplate identity = asset attributes** (`records.assets`, `data_source: inherited`); **As-Found/As-Left settings + test readings = per-visit submission fields** (`data_source: data`); **header** (job/customer/ambient/tested-by) = platform context, not template fields. |
| **No DDL** | Everything lives in `records.form_templates.field_schema` (JSONB). Readings resolve to flat `records.form_field_values.field_key` instances at capture time. |

---

## 2. The `field_schema` contract (reusable across families)

`field_schema` is a JSON **object** (not the bare `[]` default):

```jsonc
{
  "version": 1,
  "family": "lv_circuit_breaker",
  "selections": [            // drive visible_if; first-class, typed
    { "tag": "construction_type", "label": "Breaker construction",
      "value_kind": "selection", "options": ["power","insulated_case","molded_case"],
      "ties_to": "equipment_model" }   // -> TCC identity -> tolerance windows (Chip 5)
  ],
  "sections": [
    { "key": "...", "title": "...", "kind": "fields" | "table",
      "neta_basis": "7.6.1.2",          // provenance, optional
      "visible_if": "<expr over selection tags>",   // optional
      // kind=fields:
      "fields": [ <control>, ... ],
      // kind=table:
      "table": { "row_dim": { "tag": "...", "label": "...", "rows": ["...","..."] },
                 "columns": [ <control>, ... ] }
    }
  ]
}
```

A **control**:

```jsonc
{ "tag": "ltpu_amps", "label": "Long-time pickup", "value_kind": "numeric",
  "unit": "A",
  "data_source": "data" | "inherited" | "calc",
  "options": [...],                       // for value_kind=selection
  "neta_ref": "7.6.1.2.B.3",              // back-ref to the NETA item it satisfies
  "acceptance": { "basis": "mfr_tolerance", "fallback_table": "100.7" },  // field-trust basis
  "tolerance_source": { "engine": "tcc", "function": "long",
                        "inputs": ["trip_unit","al_long_pickup","al_long_delay","al_long_curve"] },
  "formula": null                          // data_source=calc only; ENGINE deferred (D-FORMS)
}
```

- `value_kind` ∈ `numeric | boolean | text | selection | date | graph` (per §225). Visual/mechanical
  items use `selection` with options `["sat","unsat","na"]` plus a sibling `*_note` text.
- `data_source`: `inherited` (from the asset), `data` (tech enters), `calc` (computed — reserved;
  engine deferred to D-FORMS).
- `acceptance` / `tolerance_source` are **declared here, resolved at provisioning (Chip 5).** The
  template never carries a fabricated number.
- A field-schema **validator** (TDD, this chip) enforces this shape + the coverage invariant below.

---

## 3. LV-CB composite — sections (Power branch; as built = 11 sections)

Header (Asset ID, Position, Substation, Job #, Customer, Date, Ambient Temp, Humidity, Tested-By,
Page) is **platform context** — supplied by `assets` + `form_submissions`, **not** in `field_schema`.

| # | Section `key` | kind | NETA basis | `visible_if` | Notes |
|---|---|---|---|---|---|
| 1 | `nameplate` | fields | A.1 | — | identity `inherited` from asset (R-C) + nameplate-vs-drawings check |
| 2 | `visual_mechanical` | **table** | A.2–A.14, A.16 | drawout rows gated | Inspected / Condition / Clean-Lube / value / note grid |
| 3 | `operation_counter` | fields | A.15 | drawout | counter AF/AL — split out (numerics don't fit the VM grid) |
| 4 | `settings_lsig` | table | A.14 | `trip_unit_class=electronic` | As-Found / As-Left L·S·I·G (pickup·factor·delay·curve) |
| 5 | `insulation_resistance` | table | B.1 | — | ▸100.1; 7 rows; TCF + temp |
| 6 | `contact_resistance` | table | B.2 | — | µΩ per pole; 50%-deviation rule |
| 7 | `primary_injection` | table | B.3–6 | tests ∋ primary_injection | pickup/timing core; per-pole; min/max → `tolerance_source` |
| 8 | `secondary_injection` | fields | B.7 | tests ∋ secondary_injection | optional trip-unit function test |
| 9 | `auxiliary` | fields | B.8–9 | charging gated | aux features + charging mechanism |
| 10 | `test_equipment` | table | — (QA) | — | cal-traceable; witness footer |
| 11 | `comments_deficiencies` | fields | — | — | repeating text |

> **As-built note:** the operation counter (A.15) is its own small section, not a row in the
> visual-mechanical condition grid — its as-found/as-left readings are numeric and don't fit the
> Inspected/Condition/Clean-Lube columns. Coverage is unchanged (A.15 still mapped); 11 sections.

### 3.1 `nameplate` (inherited from asset)
`manufacturer`, `breaker_type/model`, `trip_unit`, `frame_size_A`, `sensor_tap_A`, `rating_plug_A`,
`catalog_no`, `serial_no`, `cubicle_code`, `mounting`, `poles`, `voltage_rating`, `interrupting_rating`.
Plus `nameplate_vs_drawings` (selection sat/unsat/na) — satisfies NETA VM #1.

### 3.2 `visual_mechanical` — the 16 NETA items (each = selection[sat/unsat/na] + note)
| field `tag` | NETA | `visible_if` |
|---|---|---|
| `vm_phys_mech_condition` | A.2 | — |
| `vm_anchorage_align_ground` | A.3 | — |
| `vm_maintenance_devices` | A.4 | power, insulated_case |
| `vm_clean` | A.5 | — |
| `vm_arc_chutes` | A.6 | power, insulated_case |
| `vm_contacts_condition_align` | A.7 | — |
| `vm_contact_wipe_dims` | A.8 | power, insulated_case |
| `vm_mech_operator_align_tests` | A.9 | — |
| `vm_torque` (+ `vm_torque_value`) | A.10 | — | acceptance ▸100.12 |
| `vm_cell_fit_element_align` | A.11 | power, insulated_case |
| `vm_racking_mechanism` | A.12 | power, insulated_case |
| `vm_lubrication` | A.13 | — |
| `vm_settings_per_coord_study` | A.14 | — | cross-refs §3 settings |
| _(A.15 operation counter → its own `operation_counter` section; numerics don't fit this grid)_ | A.15 | power, insulated_case |
| `vm_thermography` (optional) | A.16 | — | ▸Section 9 |

> The `visible_if power, insulated_case` rows ARE the composite deltas — a molded-case breaker is a
> sealed, non-drawout unit (no racking, cell-fit, arc-chute access, maintenance devices, counter).
> This is exactly why one composite + selector beats three templates: the subtype difference is a
> handful of `visible_if` flags, not a separate sheet.

### 3.3 `settings_lsig` (table) — As-Found / As-Left
- `row_dim`: function ∈ `[long, short, instantaneous, ground]`
- columns: `af_pickup`, `af_factor`, `af_delay`, `af_curve`, `al_pickup`, `al_factor`, `al_delay`, `al_curve` (all `data`)
- satisfies NETA A.14; the As-Left settings are the basis the §6 windows resolve against.

### 3.4 `insulation_resistance` (table) — ▸ Table 100.1
- `row_dim`: measurement ∈ `[pole1-2, pole2-3, pole1-3, P-G (closed), across-open-pole, control_wiring, line-to-load]`
- columns: `test_voltage` (data), `reading_mohm` (data), `equip_temp` (data), `tcf` (calc-reserved), `corrected_mohm` (calc-reserved)
- acceptance: `{basis: mfr, fallback_table: 100.1}`; control wiring threshold ≥ 2 MΩ (NETA TV B.3).

### 3.5 `contact_resistance` (table)
- `row_dim`: pole ∈ `[A, B, C]`; columns: `micro_ohms` (data), `temp` (data)
- acceptance: `{basis: mfr, rule: "investigate >50% deviation pole-to-pole"}`.

### 3.6 `primary_injection` (table) — the pickup/timing core + acceptance windows
- `row_dim`: function ∈ `[long, short, instantaneous, ground]`
- columns: `pickup_amps` (data), `test_multiple` (data), `test_amps` (data),
  `trip_time_af` (data), `trip_time_al` (data),
  `min_time` (**tolerance_source** → tcc), `max_time` (**tolerance_source** → tcc), `result` (calc-reserved pass/fail)
- per-pole timing (`_pole_#`) supported via the table `grow` mechanism.
- acceptance: LT/ST/GF ▸ mfr curve (fallback 100.7); instantaneous ▸ mfr (fallback 100.8).
- **This section is the lvbreakertcc field-tolerances sheet** — `min_time`/`max_time` are exactly the
  TCC engine's `MANUFACTURER;TRIP UNIT;CURVE;DELAY;CURRENT MULTIPLE` window, resolved at Chip 5.

### 3.7 `secondary_injection` (optional), 3.8 `auxiliary`
- `secondary_injection`: trip-unit function-by-secondary-injection (NETA B.7, optional).
- `auxiliary`: `aux_zone_interlock`, `aux_trip_pickup_indicators`, `aux_electrical_close_trip`,
  `aux_trip_free`, `aux_antipump`, `aux_battery_condition`, `aux_charging_mechanism` (NETA B.8–9), each selection+note.

### 3.9 `test_equipment` (table), 3.10 `comments_deficiencies`
- `test_equipment`: `manufacturer`, `model`, `type`, `serial_id`, `cal_date`, `cal_due` (witness footer; QA traceability — not a NETA test item but required for a defensible report).
- `comments_deficiencies`: repeating `comment` / `deficiency` text.

---

## 4. NETA 7.6.1.2 coverage matrix (proves 100% of prescribed items map)

**Visual/Mechanical (A.1–A.16) → all mapped** to §3.1–§3.2 (`nameplate_vs_drawings` + 15 `vm_*` fields + counter).
**Electrical (B.1–B.9) → all mapped:** B.1→§3.4 IR · B.2→§3.5 contact-R · B.3 LT / B.4 ST / B.5 GF / B.6 Inst →§3.6 primary-injection rows · B.7→§3.7 secondary · B.8 aux / B.9 charging →§3.8.
**Acceptance criteria (TV-visual A.×4 + TV-electrical B.×10) → field-level `acceptance`/`tolerance_source` metadata** on the corresponding control (not separate fields): torque▸100.12, thermography▸§9, settings▸coord-study, counter-advances; IR▸100.1, contact-R 50%-rule, control-wiring≥2MΩ, LT/ST/GF/Inst▸mfr-curve(100.7/100.8), aux▸mfr, charging▸mfr.

> **Coverage invariant (validator-enforced):** every `records.neta_test_items` row for the linked
> procedures with `standard='ats'` and `category` ∈ {visual_mechanical, electrical} resolves to a
> control whose `neta_ref` cites its section item — or is explicitly listed under §6 "omitted" with a
> reason. No silent drops.

---

## 5. Construction-type conditional summary (the composite, one selector)

| Subtype | NETA proc | Drawout? | Gated-OFF sections/fields |
|---|---|---|---|
| Power (LVPCB) | 7.6.1.2 | yes | — (full sheet) |
| Insulated-Case (ICCB) | 7.6.1.1.2 | yes | (none of the drawout deltas) |
| Molded-Case (MCCB) | 7.6.1.1.1 | **no** | `vm_maintenance_devices`, `vm_arc_chutes`, `vm_contact_wipe_dims`, `vm_cell_fit_element_align`, `vm_racking_mechanism`, counter; settings table only if electronic trip |

---

## 6. Open red-line items (for the operator)

1. **VM item set** — confirm all 16 stay, or flag any genuinely not field-recorded on a real power-CB sheet. (R-B lean: keep all 16.)
2. **`settings_lsig` factor vs pickup** — the witness splits "pickup setting" and "pickup factor" (× Ir). Keep both columns, or just the resulting pickup amps? (Lean: keep both — the factor is what the tech dials.)
3. **IR measurement rows** — the row set in §3.4 is my read of NETA "phase-phase, phase-ground closed, across each open pole" + witness (control wiring, line-to-load). Confirm the row list.
4. **Per-pole timing** — capture trip time per pole (witness does), or one time per function? (Lean: per-pole, via table `grow`.)
5. **Voltage drop @ LT test current** — witness has it; NETA doesn't. Keep as a practical field? (Lean: keep, `data`, no acceptance.)

**Deferred (not this chip):** the calc engine (`data_source: calc` fields — TCF, corrected IR, pass/fail) = D-FORMS; window value resolution from TCC = Chip 5 (provisioning). This chip delivers the **template definition + validator + coverage matrix**, seeded on `records_dev`.
