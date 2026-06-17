# Chip 2b - Instrument-Transformer Datasheets (`ats_ct_v1` + `ats_vt_v1` + `ats_cvt_v1`)

> **Status:** BUILT + validated - 2026-06-17. Migration `015` + `gen_it_template.py` +
> `test_015_it_template.py` (17/17 on `records_dev`). The sixth 2b family; **the first
> capture-mode-aware build and the first PowerDB-anchored family** (post-235 ratification).
> Cite `00-MASTER-INDEX.md` §4, the shared `field_schema` contract (`04-LV-CB-DATASHEET-SPEC.md` §2),
> the NETA 2a reference (`records.neta_*`), and the PowerDB cover forms (see §5).

---

## 1. Three leaf-bound sheets

| Sheet | Leaf | Procedure | Sections | Coverage | PowerDB anchor |
|---|---|---|---|---|---|
| `ats_ct_v1` | `it_ct` | 7.10.1 (Current Transformer) | 12 | **18** ATS (9 VM + 9 elec) | 27660 Multi-Winding CT |
| `ats_vt_v1` | `it_vt` | 7.10.2 (Voltage / Potential Transformer) | 11 | **18** ATS (11 VM + 7 elec) | 27600 PT/VT |
| `ats_cvt_v1` | `it_cvt` | 7.10.3 (Coupling-Capacitor VT) | 12 | **20** ATS (11 VM + 9 elec) | 99000 CVT |

Each leaf maps to exactly one NETA procedure -> one sheet per leaf (the clean recipe, like the
cables - no selector to fold, no shared-procedure parent-binding). PowerDB serves PT and VT from
one form (27600), matching the single `it_vt` leaf (PT = potential = voltage transformer).
NETA 7.10.4 (high-accuracy ITs) carries no ATS battery and gets no sheet.

---

## 2. Sections

**CT (12):** nameplate (CtType bar/window, ANSI/IEC saturation standard, ratio, accuracy class) ·
visual_mechanical (8 rows) · insulation_resistance (secondary-to-ground 1000 Vdc + bar-type primary,
Table 100.5) · **ratio_polarity** · **excitation** (knee point + V/I curve) · burden · dielectric_withstand
(Table 100.9) · power_factor · grounding · test_equipment · comments_deficiencies · **attachments**.

**VT (11):** nameplate · visual_mechanical (10 rows, incl. fuse sizes + as-left) ·
insulation_resistance (winding-to-winding / -ground, Table 100.5) · **ratio_polarity** (turns-ratio
all taps + H1-X1) · burden · dielectric_withstand · **power_factor** · grounding · test_equipment ·
comments_deficiencies · **attachments**.

**CVT (12):** nameplate (capacitor sections CN/C1/C2, # stacks) · visual_mechanical (10 rows) ·
**bolted_resistance** (low-resistance ohmmeter) · insulation_resistance (Table 100.5) ·
**ratio_polarity** (all taps + C93.1) · burden · dielectric_withstand · **capacitance_pf** (the
CVT-specific capacitor-section battery: measured capacitance + PF/DF) · grounding · test_equipment ·
comments_deficiencies · **attachments**.

The **bolded** sections are the instrument-fillable / device-specific battery; `attachments` is the
universal cover affordance (see §4).

---

## 3. Coverage + R-A

> **Coverage invariant (gen fail-fast + `test_015`):** per sheet, the union of every section's
> `neta_covers` equals the full required set from `records.neta_test_items` for the sheet's procedure
> (`standard='ats'`, category in {visual_mechanical, electrical}). No silent drops; no phantom refs.

R-A - an instrument transformer has no integral trip curve, so `tolerance_source.engine` is:

| Measurement | basis | engine |
|---|---|---|
| IR (winding / bar-type primary) | Table 100.5 (fallback) / mfr | `neta_table` (100.5) |
| Dielectric withstand | Table 100.9 | `neta_table` (100.9) |
| Insulation PF / DF | mfr published data | `mfr` |
| Bolt torque (VM) | Table 100.12 | (acceptance) |
| Ratio error / burden | nameplate / IEEE C57.13.1 comparison | (acceptance, no window) |

Engines used: `neta_table` + `mfr` only (validator-enforced; **no `tcc`**). The `mfr` engine (PF/DF)
is the slot the future mfr-tolerance layer serves with zero template change. Windows declared,
resolved at provisioning (Chip 5), never fabricated.

---

## 4. Capture-mode contract (NEW - IT is the first capture-mode-aware build)

The post-235 ratification: one template, **two fill modes** (Path 1 cover + Path 2 import), Path 2
a superset of Path 1. The `field_schema` contract gains:

- **Template `capture` block:** `{"modes":["field","instrument_import","cover_attach"],"default":"field"}`.
- **`attachments` section (Path 1 - datasheet-as-cover):** `kind:"attachment"`, `capture_mode:"cover_attach"`,
  an `attachment` control for the mfr/OEM report + `report_source` + a `report_satisfies` flag.
  It claims **no** NETA coverage (it is not a test) - the cover wraps a report; the sheet's own
  sections still carry the requirement coverage.
- **`instrument_import` sections (Path 2 - import native results):** `capture_mode:"instrument_import"`
  + an `import` hint `{tool, profile}` naming the bridge. The harvested control `tag` is the Path-2
  import target id (the same tag the bridge writes).

Bridge map (the three existing PowerDB converters become the **Chip-10** importer, reused verbatim):

| Sheet.section | tool | profile |
|---|---|---|
| CT.ratio_polarity | `ct_analyzer` | `CT_RatioAccuracy` |
| CT.excitation | `ct_analyzer` | `CT_ExcitationCurve` |
| VT.ratio_polarity | `ptm` | `TX_TTR` |
| VT.power_factor | `dtax` | `TX_PFDF` |
| CVT.ratio_polarity | `ptm` | `TX_TTR` |
| CVT.capacitance_pf | `dtax` | `TX_PFDF` |

**Scope of this chip = the template (declarative) side only.** The importer EXECUTION (parse the
instrument export -> normalized Tag,Value -> fill) is **Chip 10**, reusing `ctan_to_powerdb.py` /
`dtax_to_powerdb.py` / `ptm_to_powerdb.py` + their YAML mapping profiles + the codified data-hygiene
rules (Doble `-1.79e308` sentinel = NULL, preserve value+units, UTC date normalization).

---

## 5. PowerDB anchor provenance

This is the first family whose field structure is **anchored to the RESA PowerDB cover forms**
(`OneDrive\...\PowerDB Forms\`): 27660 Multi-Winding CT, 27600 PT/VT, 99000 CVT. The harvestable
layer is the `.csv` "Translate PXD" export (`Native Text | Translation | Type | Tag Name |
Coordinates`) plus the `.pdf` render - the `.pxd` is a compiled binary whose tag names are not
reliably extractable. NETA remains the **coverage authority** (the §3 invariant); PowerDB supplies
the real field set NETA's abstract item list does not enumerate (CtType bar/window, ANSI/IEC
saturation standard, the PF connection matrix, the CVT capacitor-section battery). They compose:
NETA = what must be covered; PowerDB = the actual fields/columns/options the techs use.

---

## 6. Notes / deferred

- **Window-value resolution** from NETA tables / mfr = Chip 5 (provisioning); the **calc engine**
  (`data_source: calc`) = D-FORMS. **Instrument import EXECUTION** = Chip 10 (§4).
- Prior-family PowerDB cross-check / backfill (15055 LV PCB, 92520/92525/92550 breakers, 56910/93500/94500
  xfmr, 13050 VLF cable) is **available on demand** (operator exports), not done in this chip.
- This chip delivers the three template definitions + the capture-mode contract extension + validator
  + coverage matrices, seeded on `records_dev` (not yet prod).
