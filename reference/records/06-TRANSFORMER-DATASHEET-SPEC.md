# Chip 2b - Transformer Datasheet Spec (`ats_dry_xfmr_v1` + `ats_liquid_xfmr_v1`)

> **Status:** BUILT + validated - 2026-06-17. Migration `012` + `gen_xfmr_template.py` +
> `test_012_xfmr_template.py` (17/17 on `records_dev`). The third 2b family; the first chip to
> ship **two leaf-bound composites** in one migration and the first to fold the **two-winding /
> three-winding** dimension.
> Cite `00-MASTER-INDEX.md` §4, the shared `field_schema` contract (`04-LV-CB-DATASHEET-SPEC.md`
> §2), and the NETA 2a reference (`records.neta_*`, migrations `005`/`006`).
>
> **Sourcing law (load-bearing):** authoritative field CONTENT = NETA 7.2.1.1 / 7.2.1.2 (dry) and
> 7.2.2 (liquid) + operator review. The incumbent's 2W-xfmr form (`56910`) is a *structure* witness
> only. Field-trust applies: acceptance = manufacturer tolerance or the labeled NETA-table fallback;
> absent a basis, the window is withheld, never invented.

---

## 1. Decisions locked (this chip)

| ID | Decision |
|---|---|
| **Model** | TWO **leaf-bound** composites (matching `cb_lv` / `cb_mvhv`), one per transformer leaf: `ats_dry_xfmr_v1` -> `xfmr_dry`, `ats_liquid_xfmr_v1` -> `xfmr_liquid`. Dry and liquid are distinct apparatus (liquid carries a whole fluid/gas/LTC/bushing battery dry lacks) and each binds to its own leaf - not one parent-bound composite. (operator, 2026-06-17 - "Approved") |
| **Fold 2W/3W** (operator) | BOTH sheets fold two-winding and three-winding via a **`winding_config` selector** that gates the tertiary-winding measurement rows (H-Y, X-Y, Y-G) in the IR / turns-ratio / winding-resistance / power-factor tables. It is **measurement granularity, not NETA coverage** - the same NETA items apply regardless of winding count. |
| **Fold small/large (dry)** | The dry sheet folds NETA 7.2.1.1 (small/LV) + 7.2.1.2 (large) via a **`dry_class` selector**; large gates in the full electrical battery (winding resistance, core IR, power-factor, excitation, applied-voltage, PD) + cooling-fan / temp-indicator / surge-arrester visuals. Small dry = the lean sheet. |
| **R-A** (apparatus-appropriate) | A transformer has no integral trip curve, so `tolerance_source.engine` is **`neta_table`** (IR -> **Table 100.5**, torque -> 100.12) or **`mfr`** (winding resistance, bushing PF, turns-ratio vs nameplate - the future mfr-layer slot); oil/DGA acceptance is **standard-basis** (ASTM D923 / IEEE C57.104), descriptive (no resolved window). Never `tcc`. Windows declared, resolved at provisioning (Chip 5). |
| **No DDL** | Both sheets live in `records.form_templates.field_schema` (JSONB), same contract as the breaker sheets. |

---

## 2. Coverage (per-sheet union invariant)

| Sheet | Leaf | NETA procedures | Sections | Coverage |
|---|---|---|---|---|
| `ats_dry_xfmr_v1` | `xfmr_dry` | 7.2.1.1 (small) ∪ 7.2.1.2 (large) | 13 | **35** ATS items (20 VM + 15 elec) |
| `ats_liquid_xfmr_v1` | `xfmr_liquid` | 7.2.2 | 17 | **39** ATS items (20 VM + 19 elec) |

> **Coverage invariant (gen fail-fast + `test_012`):** per sheet, the union of every section's
> `neta_covers` equals the full required set from `records.neta_test_items` for the sheet's
> procedures (`standard='ats'`, category ∈ {visual_mechanical, electrical}). No silent drops; no
> phantom refs. The dry sheet aligns the small and large procedures (large is essentially a
> superset of small); each composite row declares the per-procedure refs it satisfies.

**Borrows covered as cross-references** (not fabricated transformer fields): liquid → load tap-changer
(7.12.3), instrument transformers (7.10), surge arresters (7.19); dry-large → surge arresters (7.19).
The actual tests live on those apparatus' own datasheets.

---

## 3. Sections

**Dry (13):** nameplate · visual_mechanical · insulation_resistance · turns_ratio · winding_resistance(L)
· power_factor(L) · excitation_current(L) · dielectric_withstand(L) · bolted_resistance · functional(L)
· surge_arresters(L, xref) · test_equipment · comments_deficiencies.  *(L) = gated to `dry_class=large`.*

**Liquid (17):** nameplate · visual_mechanical · insulation_resistance · turns_ratio · winding_resistance
· power_factor (windings + bushings) · excitation_current · advanced_diagnostics (SFRA / leakage reactance
/ DFR) · insulating_liquid (ASTM D923 screen + DGA) · gas_blanket (dew point + O₂, gated to gas-blanketed)
· load_tap_changer (7.12.3 xref + dynamic resistance) · bolted_resistance · auxiliary (neutral grounding +
space heaters) · instrument_transformers (7.10 xref) · surge_arresters (7.19 xref) · test_equipment ·
comments_deficiencies.

### The 2W/3W fold (both sheets)
- **insulation_resistance** rows: H-X, H-G, X-G (always) + **H-Y, X-Y, Y-G** (`visible_if winding_config=three_winding`) + core (optional).
- **turns_ratio** rows: H-X (always) + **H-Y, X-Y** (3W); columns = tap, nameplate ratio (inherited), measured, deviation% (acceptance ±0.5%, `tolerance_source`→mfr).
- **winding_resistance** rows: H, X (always) + **Y** (3W).
- **power_factor** rows: CH, CL, CHL (always) + **CT** (3W) [+ bushing row, liquid].

---

## 4. R-A tolerance sources (the declared seam)

| Measurement | basis | engine |
|---|---|---|
| Insulation resistance | Table 100.5 (fallback) / mfr | `neta_table` (100.5) |
| Bolt torque | Table 100.12 | (acceptance) |
| Turns ratio | within 0.5% of nameplate (IEEE C57) | `mfr` |
| Winding resistance | compare phases / prior / mfr | `mfr` |
| Power-factor (windings + bushings) | comparison vs prior/similar/Doble | `mfr` |
| Bolted-connection resistance | mfr | `mfr` |
| Insulating liquid / DGA | ASTM D923 / IEEE C57.104 | standard-basis (descriptive) |
| Applied voltage (hipot) | IEEE C57.12.91 | standard-basis (descriptive) |

Engines used: `neta_table` + `mfr` only (validator-enforced; **no `tcc`**). The `mfr` engine is the slot
the future mfr-tolerance layer serves with zero template change.

---

## 5. Notes / deferred

- **Why two sheets, not one composite:** dry vs liquid is a bigger split than the breaker media -
  liquid's fluid/gas/LTC/bushing apparatus has no dry analogue. Folding them would bury a dry-transformer
  tech under ~20 gated-off liquid sections. The taxonomy splits them into two leaves; templates bind to
  leaves; so two clean sheets. The dry sheet still folds its small/large procedures, and both fold 2W/3W.
- **Deferred (not this chip):** the calc engine (`data_source: calc` - DAR/PI, deviation%, pass/fail) =
  D-FORMS; window-value resolution from NETA tables / mfr = Chip 5 (provisioning). This chip delivers the
  two template definitions + validator + coverage matrices, seeded on `records_dev` (not yet prod).
