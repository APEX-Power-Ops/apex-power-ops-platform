# Chip 2b - Rotating-Machinery Datasheets (`ats_induction_motor_v1` + `ats_synchronous_machine_v1` + `ats_dc_machine_v1`)

> **Status:** BUILT + validated - 2026-06-17. Migration `018` + `gen_motor_template.py` +
> `test_018_motor_template.py` (14/14 on `records_dev`). The ninth 2b family and **the largest**
> (84 ATS items across three sheets). **NOT PowerDB-anchored** (no motor form in the corpus) ->
> NETA-derived. Cite `00-MASTER-INDEX.md` §4, the shared `field_schema` contract
> (`04-LV-CB-DATASHEET-SPEC.md` §2), and the NETA 2a reference (`records.neta_*`).

---

## 1. Three leaf-bound sheets

| Sheet | Leaf | Procedure | Sections | Coverage |
|---|---|---|---|---|
| `ats_induction_motor_v1` | `rm_induction` | 7.15.1 (AC induction) | 14 | **27** ATS (11 VM + 16 elec) |
| `ats_synchronous_machine_v1` | `rm_synchronous` | 7.15.2 (synchronous) | 15 | **37** ATS (11 VM + 26 elec) |
| `ats_dc_machine_v1` | `rm_dc` | 7.15.3 (DC) | 11 | **20** ATS (10 VM + 10 elec) |

Each leaf maps to exactly one procedure (clean recipe, no selector / split / parent-binding; acnp
links already correct from the backfill). `mcc_*` / `motor_starter_*` / `engine_generator` are
separate families (7.16 / 7.22), not 7.15.

---

## 2. Sections (test families)

The 84 items are grouped into test-family sections (not one section per item):

**Induction (14):** nameplate · visual_mechanical (10 rows) · bolted_resistance · insulation_resistance
(IEEE 43: IR + PI + bearing IR) · dielectric_withstand · winding_resistance (stator) · power_factor
(+ tip-up) · surge_comparison · protective_devices (SPD 7.19/7.20 + starter 7.16 cross-refs) ·
auxiliary (RTD + space heater) · running_tests (vibration, bearing temp, CSA, PD) · test_equipment ·
comments · attachments.

**Synchronous (15):** induction's set **+ `field_excitation`** (field voltage-drop, excitation hipot
IEEE 421.3, diode/SCR, exciter-field set, field timers, acceleration record, V-curve, PF-relay op);
IR also carries the rotor/exciter IR, winding_resistance also the field winding.

**DC (11):** nameplate · visual_mechanical (9 rows) · bolted_resistance · insulation_resistance ·
dielectric_withstand (hipot, NEMA MG 1) · **field_excitation** (field voltage-drop, surge comparison,
commutator bar-to-bar, field polarity) · running_tests (armature/field current vs nameplate, vibration) ·
protective_devices · test_equipment · comments · attachments.

---

## 3. Coverage + R-A

> **Coverage invariant (gen fail-fast + `test_018`):** per sheet, the union of every section's
> `neta_covers` equals the full required set from `records.neta_test_items` for the procedure. No
> silent drops; no phantom refs.

R-A - rotating machinery tests to **IEEE 43** (IR / polarization index), **NEMA MG 1** (hipot), and
mfr data, **not a NETA acceptance table**:

| Measurement | basis | engine |
|---|---|---|
| Insulation resistance / PI | IEEE Std 43 (min IR = kV + 1 Mohm) | `mfr` |
| Dielectric / high-potential | IEEE / NEMA MG 1 | `mfr` |
| Winding / field resistance | mfr | `mfr` |
| Power factor / dissipation | mfr | `mfr` |
| Bolt torque (VM) | Table 100.12 | (acceptance basis) |

Engines used: **`mfr` only** (validator-enforced subset {neta_table, mfr}; **no `tcc`**, and - like
grounding - **no `neta_table` window**, because motors test to IEEE 43 / NEMA, not a NETA table). The
IR section is the mfr (IEEE 43) acceptance slot on every sheet. Windows resolved at provisioning.

---

## 4. Capture-mode

Both/all three carry the universal **`attachments` cover section** (Path 1; a Doble/Baker motor
report attaches here). No motor instrument bridge is wired (the three PowerDB bridges are
CT-Analyzer / DTAX / PTM; the emerging DTAX winding-resistance work is not committed/wired), so
`capture.modes = [field, cover_attach]` - no `instrument_import` section.

---

## 5. Notes / deferred

- **Not PowerDB-anchored** -> NETA-derived; re-anchorable on demand if a PowerDB motor form is exported.
- **Generator note:** the gen factored shared test-family sections (bolted-R, dielectric, PF, surge,
  protective, auxiliary) - these are **deep-copied per sheet** in `assign_covers` so each machine's
  `neta_covers` lands on its own copy (a shared-mutable-dict aliasing bug was caught + fixed in TDD).
- **Deferred:** window-value resolution (Chip 5); the calc engine (D-FORMS); a motor Doble/DTAX import
  profile (Chip 10 - ties to the in-flight winding-resistance converter work). This chip delivers the
  three templates + validator + coverage matrices, seeded on `records_dev` (not yet prod).
