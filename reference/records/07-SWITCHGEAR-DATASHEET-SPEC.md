# Chip 2b - Switchgear + Panelboard Datasheet Spec (`ats_switchgear_v1` + `ats_panelboard_v1`)

> **Status:** BUILT + validated - 2026-06-17. Migration `013` + `gen_switchgear_template.py` +
> `test_013_switchgear_template.py` (15/15 on `records_dev`). The fourth 2b family; the first to
> introduce **parent-node binding** (a datasheet that serves multiple leaves sharing one procedure).
> Cite `00-MASTER-INDEX.md` §4, the shared `field_schema` contract (`04-LV-CB-DATASHEET-SPEC.md` §2),
> and the NETA 2a reference (`records.neta_*`, migrations `005`/`006`).
>
> **Sourcing law:** authoritative field CONTENT = NETA 7.1.1 (switchgear/switchboard assemblies) and
> 7.1.2 (panelboards) + operator review. Field-trust applies: acceptance = manufacturer tolerance or
> the labeled NETA-table fallback; absent a basis, the window is withheld, never invented.

---

## 1. The new structural wrinkle (and the decision)

Breakers and transformers had **one NETA procedure per leaf** -> one datasheet per leaf. Switchgear
does not: the `switchgear` parent has **five leaves**, but **four share NETA 7.1.1** -
`swgr_lv_switchboard`, `swgr_mv_metalclad`, `swgr_padmount`, `swgr_vfi` - and `swgr_panelboard` is its
own `7.1.2`. A `form_templates` row binds to **one** `asset_class_id`, so the shared-procedure sheet
cannot 1:1-bind to a leaf.

**Decision (operator-approved):** TWO sheets -

| Sheet | Covers | Binding | Selector |
|---|---|---|---|
| `ats_switchgear_v1` | 7.1.1 (35 ATS) | **parent `switchgear`** | `assembly_type {lv_switchboard, mv_metalclad, padmount, vfi}` |
| `ats_panelboard_v1` | 7.1.2 (14 ATS) | leaf `swgr_panelboard` | - |

- **Parent-binding** is the deliberate novelty: the 7.1.1 sheet attaches at the parent node (whose name
  *is* "Switchgear and Switchboard Assemblies" = 7.1.1), matching the shell's "NETA attaches at the
  parent, inherited by leaves" principle. Assets still classify to the specific leaf; provisioning
  (Chip 5) resolves a leaf's datasheet by walking leaf -> parent. (Alternatives weighed + rejected:
  binding to an arbitrary "primary" leaf; a template<->leaf many-to-many - deferred unless needed.)
- **`assembly_type` is context**, not a coverage gate: the four 7.1.1 leaves share the procedure
  identically (the breakers/CTs/VTs *inside* a lineup are separate assets on their own sheets), so the
  selector drives display context + minor emphasis, never drops a NETA item.
- **Panelboard stays separate** (mirrors the transformer dry/liquid + the leaf-bound breaker split):
  7.1.2 is a leaner, distinct procedure and its own leaf.

---

## 2. Coverage (per-sheet invariant)

| Sheet | Procedure | Sections | Coverage |
|---|---|---|---|
| `ats_switchgear_v1` | 7.1.1 | 13 | **35** ATS (20 VM + 15 elec) |
| `ats_panelboard_v1` | 7.1.2 | 6 | **14** ATS (12 VM + 2 elec) |

> **Coverage invariant (gen fail-fast + `test_013`):** per sheet, the union of every section's
> `neta_covers` equals the full required set from `records.neta_test_items` for the sheet's procedure
> (`standard='ats'`, category in {visual_mechanical, electrical}). No silent drops; no phantom refs.

**Cross-ref borrows covered** (not fabricated assembly fields): the 7.1.1 sheet carries instrument
transformers (7.10), surge arresters (7.19), ground resistance (7.13), and metering (7.11) as
cross-reference items - the actual tests live on those apparatus' / sections' own datasheets. The
panelboard's ground-resistance (7.13) is likewise a cross-reference.

---

## 3. Sections

**Switchgear (13):** nameplate · visual_mechanical (17 rows) · insulation_resistance (per bus section,
Table 100.1, + control wiring) · dielectric_withstand (per bus section, Table 100.2) · bolted_resistance
· instrument_transformers (7.10 xref + CPT + VT) · metering (7.11 xref) · ground_resistance (7.13 xref)
· functional (current-injection · system-function ECS · space heaters · phasing) · surge_arresters (7.19
xref) · partial_discharge (opt) · test_equipment · comments_deficiencies.

**Panelboard (6):** nameplate · visual_mechanical (11 rows) · insulation_resistance (per bus section,
Table 100.1) · ground_resistance (7.13 xref) · test_equipment · comments_deficiencies.

---

## 4. R-A tolerance sources

A switchgear/panelboard assembly has no integral trip curve, so `tolerance_source.engine` is:

| Measurement | basis | engine |
|---|---|---|
| Bus insulation resistance | Table 100.1 (fallback) / mfr | `neta_table` (100.1) |
| Dielectric withstand (per bus) | Table 100.2 (fallback) / mfr | `neta_table` (100.2) |
| Bolt torque (VM) | Table 100.12 | (acceptance) |
| Bolted-connection resistance | mfr | `mfr` |

Engines used: `neta_table` + `mfr` only (validator-enforced; **no `tcc`**). Panelboard's only measured
electrical value is bus IR (`neta_table` 100.1); it has no mfr-measured value (its bolted connections
are the VM torque row), so the `mfr` slot applies to the switchgear sheet. The `mfr` engine is the
slot the future mfr-tolerance layer serves with zero template change. Windows declared, resolved at
provisioning (Chip 5), never fabricated.

---

## 5. Notes / deferred

- **Parent-binding precedent:** this is the first records datasheet bound to a non-leaf class. It is
  schema-legal (`form_templates.asset_class_id` FK accepts any class) and semantically right for a
  procedure shared across sibling leaves. If more shared-procedure families appear and a leaf needs
  multiple/overriding templates, revisit with a template<->leaf many-to-many (D-FORMS-adjacent).
- **Deferred (not this chip):** the calc engine (`data_source: calc` fields) = D-FORMS; window-value
  resolution from NETA tables / mfr = Chip 5 (provisioning). This chip delivers the two template
  definitions + validator + coverage matrices, seeded on `records_dev` (not yet prod).
