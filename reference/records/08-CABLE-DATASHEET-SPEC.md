# Chip 2b - Cable Datasheet Spec (`ats_lv_cable_v1` + `ats_mvhv_cable_v1`)

> **Status:** BUILT + validated - 2026-06-17. Migration `014` + `gen_cable_template.py` +
> `test_014_cable_template.py` (13/13 on `records_dev`). The fifth 2b family; first of the
> operator-priority queue (cables -> IT -> grounding -> SA -> motors). The clean recipe: two
> leaf-bound single-procedure sheets, no selector folding, no parent-binding.
> Cite `00-MASTER-INDEX.md` §4, the shared `field_schema` contract (`04-LV-CB-DATASHEET-SPEC.md` §2),
> and the NETA 2a reference (`records.neta_*`).

---

## 1. Two leaf-bound sheets

| Sheet | Leaf | Procedure | Sections | Coverage |
|---|---|---|---|---|
| `ats_lv_cable_v1` | `cable_lv` | 7.3.2 (LV, 600 V max) | 6 | **11** ATS (8 VM + 3 elec) |
| `ats_mvhv_cable_v1` | `cable_mv` | 7.3.3 (MV/HV) | 11 | **18** ATS (10 VM + 8 elec) |

Each leaf maps to exactly one NETA procedure -> one sheet per leaf, the same clean pattern as the
breakers (no selector to fold, no shared-procedure parent-binding).

---

## 2. Sections

**LV (6):** nameplate · visual_mechanical (7 rows) · insulation_resistance (per conductor, 500/1000 Vdc)
· continuity (continuity + parallel-conductor uniform resistance) · test_equipment · comments_deficiencies.

**MV/HV (11):** nameplate · visual_mechanical (9 rows) · insulation_resistance (conductor-to-shield,
Table 100.1) · **shield_continuity** · **tdr** · **jacket_integrity** · **dielectric_withstand** (VLF/DC/AC)
· **tan_delta** (Table 100.6.6/.7) · **partial_discharge** (online + offline) · test_equipment ·
comments_deficiencies.

The **bolded** MV sections are the shielded-cable HV battery that LV (600 V) doesn't carry - the only
real difference between the two sheets.

---

## 3. Coverage + R-A

> **Coverage invariant (gen fail-fast + `test_014`):** per sheet, the union of every section's
> `neta_covers` equals the full required set from `records.neta_test_items` for the sheet's procedure
> (`standard='ats'`, category in {visual_mechanical, electrical}). No silent drops; no phantom refs.

R-A - a cable has no integral trip curve, so `tolerance_source.engine` is:

| Measurement | basis | engine |
|---|---|---|
| MV IR (conductor-to-shield) | Table 100.1 (fallback) / mfr | `neta_table` (100.1) |
| MV tan-delta | Table 100.6.6 / .7 (fallback) / mfr | `neta_table` (100.6.6) |
| LV IR | comparison vs prior/similar/mfr | `mfr` |
| MV dielectric withstand | mfr | `mfr` |
| Bolt torque (VM) | Table 100.12 | (acceptance) |

Engines used: `neta_table` + `mfr` only (validator-enforced; **no `tcc`**). LV cable IR has no NETA
acceptance table (procedure-defined test voltage; judged by comparison/mfr) -> it's the LV sheet's
`mfr` slot. The `mfr` engine is the slot the future mfr-tolerance layer serves with zero template
change. Windows declared, resolved at provisioning (Chip 5), never fabricated.

---

## 4. Notes / deferred

- The MV offline-PD / tan-delta optional tests cite NETA Tables 100.6.3-100.6.7 (PD + tan-delta
  acceptance) which are seeded in `records.neta_tables`; the field captures the measured values and
  the windows resolve at provisioning.
- **Deferred (not this chip):** the calc engine (`data_source: calc`) = D-FORMS; window-value
  resolution from NETA tables / mfr = Chip 5 (provisioning). This chip delivers the two template
  definitions + validator + coverage matrices, seeded on `records_dev` (not yet prod).
