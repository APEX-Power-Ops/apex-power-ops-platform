# Chip 2b - Grounding-System Datasheet (`ats_grounding_v1`)

> **Status:** BUILT + validated - 2026-06-17. Migration `016` + `gen_grounding_template.py` +
> `test_016_grounding_template.py` (13/13 on `records_dev`). The seventh 2b family; the smallest
> (one leaf, 6 ATS). **NOT PowerDB-anchored** (no grounding form in the RESA PowerDB corpus) -> the
> NETA-derived recipe the pre-IT families used. Cite `00-MASTER-INDEX.md` §4, the shared `field_schema`
> contract (`04-LV-CB-DATASHEET-SPEC.md` §2), and the NETA 2a reference (`records.neta_*`).

---

## 1. One leaf-bound sheet

| Sheet | Leaf | Procedure | Sections | Coverage |
|---|---|---|---|---|
| `ats_grounding_v1` | `grounding_system` | 7.13 (Grounding Systems) | 8 | **6** ATS (3 VM + 3 elec) |

No selector, no parent-binding, no PowerDB anchor - the clean minimal recipe.

---

## 2. Sections

**(8):** identification (NEC Art. 250 compliance, electrode type, drawings ref) · visual_mechanical
(2 rows: physical/mechanical + torque) · **bolted_resistance** (B.1, low-resistance ohmmeter) ·
**ground_resistance** (B.2, fall-of-potential / IEEE 81) · **point_to_point** (B.3, main system to
equipment frames / system neutral / derived neutrals) · test_equipment · comments_deficiencies ·
**attachments**.

Coverage: A.1 -> identification; A.2 + A.3 -> visual_mechanical; B.1 -> bolted_resistance;
B.2 -> ground_resistance; B.3 -> point_to_point.

---

## 3. Coverage + R-A

> **Coverage invariant (gen fail-fast + `test_016`):** the union of every section's `neta_covers`
> equals the full required set from `records.neta_test_items` for 7.13 (`standard='ats'`, category in
> {visual_mechanical, electrical}). No silent drops; no phantom refs.

R-A - a grounding system has no integral trip curve **and no NETA IR/dielectric acceptance table**:

| Measurement | basis | engine |
|---|---|---|
| Ground resistance (fall-of-potential) | design limit / IEEE 81 / NEC | `mfr` |
| Bolted-connection resistance | mfr / comparison | `mfr` |
| Point-to-point resistance | low / uniform vs design (comparison) | (acceptance, no window) |
| Bolt torque (VM) | Table 100.12 | (acceptance basis on the VM row) |

Engines used: **`mfr` only** (validator-enforced subset {neta_table, mfr}; **no `tcc`**, and - unlike
the IT/cable sheets - **no `neta_table` window**, because 7.13 has no IR/dielectric table; torque
100.12 is an acceptance basis, not a tolerance_source). The `mfr` engine is the slot the future
mfr-tolerance layer serves. Windows declared, resolved at provisioning (Chip 5), never fabricated.

---

## 4. Capture-mode + provenance

The universal **`attachments` cover section** (Path 1, `capture_mode:cover_attach`) applies - a
ground-grid study or fall-of-potential report can be attached as the cover/evidence. But **there is
no instrument bridge for ground testers** (the three PowerDB bridges are CT-Analyzer / DTAX / PTM
only), so this sheet declares `capture.modes = [field, cover_attach]` - **no `instrument_import`
mode**, and no section is an import target. This is the honest per-family capture contract: the
modes reflect what the sheet actually supports. (Cf. `09-IT-DATASHEET-SPEC.md` §4 for the full
capture-mode contract introduced with IT.)

---

## 5. Notes / deferred

- **Not PowerDB-anchored:** no grounding form exists in the RESA PowerDB corpus, so the field
  structure is NETA-derived (the pre-IT recipe). If a PowerDB grounding form is exported later, the
  sheet can be re-anchored on demand (the IT-onward anchoring scope, ratified post-§235).
- **Deferred (not this chip):** window-value resolution (Chip 5), the calc engine (D-FORMS),
  instrument import (Chip 10 - not applicable here absent a ground-tester bridge). This chip delivers
  the template + validator + coverage matrix, seeded on `records_dev` (not yet prod).
