# Chip 2b - Surge-Protection Datasheets (`ats_lv_spd_v1` + `ats_mvhv_arrester_v1`)

> **Status:** BUILT + validated - 2026-06-17. Migration `017` + `gen_surge_template.py` +
> `test_017_surge_template.py` (16/16 on `records_dev`). The eighth 2b family. **NOT PowerDB-anchored**
> (no surge form in the corpus) -> NETA-derived. **First chip to also perform a taxonomy split**
> (operator ruling - see §1). Cite `00-MASTER-INDEX.md` §4, the shared `field_schema` contract
> (`04-LV-CB-DATASHEET-SPEC.md` §2), and the NETA 2a reference (`records.neta_*`).

---

## 1. The leaf split (operator ruling, 2026-06-17)

NETA 7.19 is **two genuinely different apparatus** under one shell leaf (`surge_arrester`): 7.19.1
(LV surge protective device) and 7.19.2 (MV/HV surge arrester). Offered composite-vs-split; the
operator chose **split**. So migration `017` does a small **taxonomy split** before the templates:

- adds the leaf **`spd_lv`** (Surge Protective Device, Low-Voltage) under the `surge_protection` parent;
- relinks **7.19.1 -> `spd_lv`** (primary) and drops the stale `surge_arrester -> 7.19.1` link;
- `surge_arrester` keeps **7.19.2** (primary).

The down migration reverses all of it (restores `surge_arrester -> 7.19.1`, drops the leaf).

| Sheet | Leaf | Procedure | Sections | Coverage |
|---|---|---|---|---|
| `ats_lv_spd_v1` | `spd_lv` (NEW) | 7.19.1 (LV SPD) | 7 | **8** ATS (6 VM + 2 elec) |
| `ats_mvhv_arrester_v1` | `surge_arrester` | 7.19.2 (MV/HV arrester) | 9 | **12** ATS (8 VM + 4 elec) |

---

## 2. Sections

**LV SPD (7):** nameplate (MCOV, protection modes, SPD type 1/2/3) · visual_mechanical (5 rows) ·
**functional_status** (self-test, alarms, status indicators, surge counter) · **grounding** (per 7.13) ·
test_equipment · comments_deficiencies · attachments.

**MV/HV arrester (9):** nameplate (arrester class station/intermediate/distribution, MCOV, discharge
class) · visual_mechanical (7 rows, incl. stroke-counter mounted + reading) · **bolted_resistance** ·
**insulation_resistance** (phase terminal-to-ground, Table 100.1) · **grounding** (per 7.13) ·
**watts_loss** (substation class) · test_equipment · comments_deficiencies · attachments.

---

## 3. Coverage + R-A

> **Coverage invariant (gen fail-fast + `test_017`):** per sheet, the union of every section's
> `neta_covers` equals the full required set from `records.neta_test_items` for the procedure
> (`standard='ats'`, category in {visual_mechanical, electrical}). No silent drops; no phantom refs.

| Measurement | basis | engine |
|---|---|---|
| MV/HV arrester IR (terminal-to-ground) | Table 100.1 (fallback) / mfr | `neta_table` (100.1) |
| MV/HV watts-loss | mfr published data | `mfr` |
| Grounding connection (both sheets, per 7.13) | design / IEEE 81 | `mfr` |
| Bolt torque (VM) | Table 100.12 | (acceptance basis) |

Engines used: `neta_table` + `mfr` only (validator-enforced; **no `tcc`**). **LV SPD has no NETA
measurement table** -> its only `tolerance_source` is the `mfr` grounding slot (its electrical items
are a functional self-test + the 7.13 grounding cross-ref). Windows declared, resolved at provisioning.

---

## 4. Capture-mode

Both sheets carry the universal **`attachments` cover section** (Path 1; a Doble arrester report can
be attached). There is **no instrument bridge for surge testing** in the toolkit (the three PowerDB
bridges are CT-Analyzer / DTAX / PTM), so both declare `capture.modes = [field, cover_attach]` -
no `instrument_import`. (A Doble arrester DTAX profile could be added at Chip 10 later; the
watts-loss / IR tests are classic Doble, so the cover path carries that report today.)

---

## 5. Notes / deferred

- **Not PowerDB-anchored** (no surge form in the RESA corpus) -> NETA-derived; re-anchorable on demand.
- **The leaf split is the first taxonomy mutation inside a 2b chip** - kept idempotent (UUID5 +
  ON CONFLICT) and fully reversible in `_down`. Net acnp count is unchanged (move, not add).
- **Deferred:** window-value resolution (Chip 5); the calc engine (D-FORMS); a surge/Doble import
  profile (Chip 10). This chip delivers the split + two templates + validator + coverage matrices,
  seeded on `records_dev` (not yet prod).
