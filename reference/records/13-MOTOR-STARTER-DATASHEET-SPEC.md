# Chip 2b - Motor-Starter Datasheets (`ats_lv_motor_starter_v1` + `ats_mv_motor_starter_v1`)

> **Status:** BUILT + validated - 2026-06-17. Migration `019` + `gen_motor_starter_template.py` +
> `test_019_motor_starter_template.py` (14/14 on `records_dev`). The first **post-priority-queue**
> family (NETA 7.16 motor control) and the second **PowerDB-anchored** build (after IT). Cite
> `00-MASTER-INDEX.md` §4, the shared `field_schema` contract (`04-LV-CB-DATASHEET-SPEC.md` §2), the
> capture-mode contract (`09-IT-DATASHEET-SPEC.md` §4), and the NETA 2a reference (`records.neta_*`).

---

## 1. Two leaf-bound sheets (the complete 7.16.1 procedures)

| Sheet | Leaf | Procedure | Sections | Coverage |
|---|---|---|---|---|
| `ats_lv_motor_starter_v1` | `motor_starter_lv` | 7.16.1.1 (LV motor starter) | 8 | **14** ATS (9 VM + 5 elec) |
| `ats_mv_motor_starter_v1` | `motor_starter_mv` | 7.16.1.2 (MV motor starter) | 12 | **29** ATS (12 VM + 17 elec) |

Each leaf maps to exactly one **complete** procedure (clean leaf-bound recipe; acnp links correct from
the backfill). Anchored to the RESA PowerDB cover forms **31000 Motor Starter Test** (LV) + **31300 MV
Vacuum Motor Starter** (the nameplate / CPT-fuse-overload / vacuum-bottle / contact-resistance
structure) — NETA stays the coverage authority.

---

## 2. MCC scope ruling (the shape decision)

NETA 7.16 has **four** leaves in the taxonomy, but only two carry own test items:

| Leaf | Procedure | NETA `status` | Disposition |
|---|---|---|---|
| `motor_starter_lv` | 7.16.1.1 | `complete` (14 items) | **sheet built** |
| `motor_starter_mv` | 7.16.1.2 | `complete` (29 items) | **sheet built** |
| `mcc_lv` | 7.16.2.1 | `crossref` (0 own items) | **deferred → composition** |
| `mcc_mv` | 7.16.2.2 | `crossref` (0 own items) | **deferred → composition** |

The two **MCC** procedures are pure `crossref`: they define MCC testing **only by reference** —
7.1 (bus) + 7.5.1.x (switches) + 7.6 (circuit breakers) + 7.16.1.x (starters). A standalone MCC
datasheet would **invent content NETA does not define**, so the MCC leaves are deferred to **asset-tree
composition**: an MCC asset is a parent with bus / switch / breaker / starter child assets, each
rendered on its own already-built sheet (7.1 switchgear ✓, 7.6 breakers ✓, 7.16.1.x starters ✓ here).
The **one not-yet-built constituent** for full MCC composition is **7.5 switches**. The ruling is
reversible — MCC "cover" sheets can be added later (a small additive migration) if the field UX wants a
single top-level MCC record; that is a Chip-4/5 provisioning concern, not a 2b template-authoring one.

---

## 3. Sections (test families)

**LV (8):** nameplate · visual_mechanical (8 rows) · insulation_resistance (IR each pole + control
wiring) · protective_devices (motor protection 7.9 + breakers 7.6.1.1) · functional (operational test) ·
test_equipment · comments_deficiencies · attachments.

**MV (12):** nameplate · visual_mechanical (11 rows) · insulation_resistance (contactor IR + control
wiring) · **vacuum_integrity** (MAC test + vacuum-bottle integrity) · **dielectric_withstand** ·
**contact_resistance** (contact/pole + blowout-coil + power-fuse) · functional (energize/armature +
system function test) · **associated_devices** (the cross-reference borrows: CPT 7.1.B.8 / starting
xfmr 7.2.1 / starting reactor 7.20.3 / motor protection 7.9 / IT 7.10 / metering 7.11) · auxiliary
(cubicle space heater) · test_equipment · comments_deficiencies · attachments.

The MV-only sections (vacuum_integrity, contact_resistance, associated_devices, dielectric_withstand)
are the medium-voltage / vacuum-contactor battery; the LV sheet is lean (no vacuum interrupter, fewer
borrows).

---

## 4. Coverage + R-A

> **Coverage invariant (gen fail-fast + `test_019`):** per sheet, the union of every section's
> `neta_covers` equals the full required set from `records.neta_test_items` for the procedure. No
> silent drops; no phantom refs.

A motor starter has **no integral trip curve** (its protection is an external overload / 7.9 device), so
R-A is `neta_table` + `mfr`, never `tcc`:

| Measurement | basis | engine |
|---|---|---|
| Insulation resistance | Table **100.1** (min IR by nominal rating) | `neta_table` |
| Motor protection devices | mfr published data (else 7.9) | `mfr` |
| Dielectric withstand (MV) | mfr published data (else Table 100.9) | `mfr` |
| Bolt torque (VM) | Table 100.12 | (acceptance basis) |

Engines used: **`neta_table` (IR → 100.1)** + **`mfr` (motor-protection / dielectric)** — validator-
enforced subset {neta_table, mfr}, **no `tcc`**. IR is the neta_table acceptance slot on both sheets;
the mfr slot is the motor-protection control (LV + MV) and the MV dielectric. Windows resolved at
provisioning (Chip 5).

---

## 5. Capture-mode

Both sheets carry the universal **`attachments` cover section** (Path 1; a starter/MCC OEM commissioning
report attaches here). **No starter instrument bridge** is wired (the three PowerDB bridges are
CT-Analyzer / DTAX / PTM, none starter-specific), so `capture.modes = [field, cover_attach]` — no
`instrument_import` section.

---

## 6. Notes / deferred

- **First post-queue family:** the operator-priority 2b queue (breakers → … → motors) was complete;
  motor control (7.16) extends it on the same recipe.
- **PowerDB-anchored** (31000 / 31300) but NOT instrument-bridged — anchoring informed the sheet
  structure; capture stays field + cover.
- **Deferred:** window-value resolution (Chip 5); MCC composite sheets (only if a field-UX call wants a
  top-level MCC record — otherwise composition handles it); 7.5 switches is the remaining MCC
  constituent not yet built. This chip delivers the two starter templates + validator + coverage
  matrices, seeded on `records_dev` (not yet prod).
