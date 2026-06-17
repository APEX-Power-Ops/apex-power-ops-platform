# NETA Records — Master Index (NETA Field-Records Lane)

> **The single source of truth for the NETA field-records domain of the APEX
> power-ops platform — the in-house replacement for the legacy field-test
> datastore.** Every packet, migration, and surface in this lane starts here and
> cites the section it relies on. If reality and this index disagree, the index is
> fixed *first* (SSoT Law, inherited from the TCC lane) — never silently worked around.

- **Status:** SEEDED — lane opened 2026-06-12; Chip 1 (data model) drafted + **validated against the legacy field-test baseline** (`02-LEGACY-BASELINE.md`, 2026-06-13); sync direction RULED (`01-OFFLINE-SYNC-ARCHITECTURE.md` §2); **generalized 2026-06-15 to `records.*` / `form_*` + a `form_type` discriminator + the `equipment_model_id` core-spine seam, applied + reversibility-validated on local Postgres `records_dev`** (substrate `FRAMEWORK-EXECUTION-PROTOCOL.md` / `MASTER-SCHEMA.md`)
- **Owner:** APEX NETA Records lane (operator: Jason Swenson)
- **Home:** `reference/records/` (version-controlled beside the migrations it cites)

---

## 0. Why this lane exists

NETA testing firms today run their field business on a licensed, Windows-centric,
vendor-locked test-data datastore: equipment lists, standardized test data sheets,
captured results with auto pass/fail, and preventive-maintenance scheduling. That
incumbent is the **baseline this lane has to replace — the floor, not the goal.**

This lane builds the in-house records platform on our own Supabase/Postgres +
Next.js stack so that it not only matches that floor but moves past it:

- the asset register, data sheets, results, and PM cadence are **our data**, not a
  vendor silo (open, queryable, no lock-in);
- field capture works **fully offline** (vaults/substations) and reconciles cleanly
  to a single source of truth — no per-tech local copies + manual sync + duplicate entry;
- results flow into the platform's existing project/work, TCC, and reporting lanes
  instead of being trapped in a separate tool.

The legacy datastore is referenced only as the capability baseline (see
`02-LEGACY-BASELINE.md`); the platform is not modelled on it and does not embed a
copy of it.

---

## 1. The four pillars

| # | Pillar | Baseline analogue | Owns |
|---|---|---|---|
| 1 | **Asset register** | Equipment / "test objects" | The equipment under test: nameplate, hierarchy (substation→switchgear→device), status, condition. Keystone — everything anchors to an asset. |
| 2 | **NETA data sheets** | Test forms / test cards | Versioned blank form definitions (per NETA standard + asset class) and the filled instances bound to an asset + job visit. |
| 3 | **Test results** | Captured readings + pass/fail | One reading per template field, with the acceptance window and assessment self-contained so pass/fail works offline. |
| 4 | **PM tracking** | Maintenance scheduling | Recurrence programs (NETA MTS cadence), per-asset schedules with next-due, and the maintenance events that close the loop back to a data sheet. |

---

## 2. The SSoT Law (inherited from the TCC lane)

1. **Cite before you build.** Every packet names the section(s) it depends on.
2. **Update before you work around.** If a packet finds reality diverging from this
   index, its first deliverable is the index correction — not a silent workaround.
3. **No orphan truth.** A fact that matters lives in a guide here, tagged with its
   source. Scratch notes and discovery artifacts are evidence, not the source.
4. **Date what you decide.** Rulings carry the date they were made.

---

## 3. The guide map

| Guide | Owns | Cite it when… | Status |
|---|---|---|---|
| **[00 — Master Index](00-MASTER-INDEX.md)** | The lane charter, the four pillars, the guide map, the data model summary | orienting to the lane | this file |
| **[01 — Offline-Sync Architecture](01-OFFLINE-SYNC-ARCHITECTURE.md)** | Provisioning / offline capture / reconcile; the device vs server authority split; the PowerSync + mutation-seam write path; the decisions of record | touching any `records.*` table, sync rule, or the field PWA | **RULED 2026-06-12** (D1 PWA · D2 fully-offline · D3 PowerSync) |
| **[02 — Legacy Baseline](02-LEGACY-BASELINE.md)** | The capability floor the platform must replace and surpass: the equipment categories, the entity/field concepts, the control model, where we must exceed the incumbent, and the one-time-migration note | scoping what to build/beat, or planning the legacy-data migration | **CAPTURED 2026-06-13** |
| **[03 — Prior Art & Inputs](03-PRIOR-ART-INPUTS.md)** | Register of preserved early attempts + raw inputs (host-only, non-authoritative): the legacy export, the NETA procedure PDFs, the early report scripts, an old platform snapshot | looking for source material to review/resume, or before re-importing anything | **LIVING — opened 2026-06-14** |
| **[Punch List](PUNCHLIST.md)** | Forward tracker: the sequenced chips from data model → asset catalog → data sheet capture → PM scheduling → reporting → legacy-data migration | planning what to build next, or recording a chip closed | **LIVING — created 2026-06-12** |

---

## 4. Data model summary (Chip 1)

The `records` schema (migrations under `infra/database/migrations/records/`). Eight
foundation tables; cross-schema links to `org.*`/`work.*` are **deferred soft UUID**
columns pending an FK-activation chip (mirrors the work→org deferred-FK pattern).

```
asset_classes ──┐
                ├─< assets >──< form_submissions >──< form_field_values
                │       │            │  (template field readings + pass/fail)
                │       │            └── fulfilled-by ── pm_events
form_templates ────┘                                   │
        │                                                    │
        └──< pm_programs >──< pm_schedules >──< pm_events >──┘
              (cadence)        (per-asset       (occurrences,
                                next-due)         link back to the
                                                  data sheet that closed them)
```

- **`assets`** is the keystone; `parent_asset_id` models the substation tree.
- **`form_templates.field_schema`** (JSONB) makes the form catalog *data, not
  code* — versioned, `is_current` enforced one-per-`template_code`.
- **`form_field_values`** carries `expected/min_acceptable/max_acceptable` + `assessment`
  so auto pass/fail is self-contained (works offline).
- **`pm_events`** links to the `form_submissions` row that fulfilled it — closing the
  asset → PM → data sheet → results loop.
- Device-authoritative tables (`form_submissions`, `form_field_values`, `pm_events`) carry the
  sync contract columns (`origin_device`, `client_rev`, `client_captured_at`,
  `synced_at`) — see `01` §3.
- **Baseline-validated refinements** (see `02` §5): `form_submissions.as_found_as_left`
  (sheet-level), `form_submissions.job_number` (the external join key), `assets` GPS +
  region/jobsite/plant/substation hierarchy, and `field_value_kind = graph`.

**Chip 2a — NETA reference layer (2026-06-15).** Three reference tables seed the
authoritative NETA standard into the DB, loaded accurately from the NETA master
equipment table (ANSI/NETA ATS-2025 / MTS-2023): `neta_procedures` (72 sections),
`neta_test_items` (3,920 ATS+MTS items × {`visual_mechanical` | `electrical` |
`test_value_*` | `crossref`}), and `neta_tables` (43 acceptance tables — e.g. Table 100.1
insulation-resistance values, the field-trust acceptance basis). Datasheets
(`form_templates.field_schema`, Chip 2b) **reference + filter** this layer rather than
copy it — so the NETA-vs-common-datasheet divergence is a query, not a maintained
matrix. Migrations `005`/`006` (generator `gen_neta_seed.py`); validated by
`test_005_neta_reference.py` on `records_dev`.

**Chip 2-shell — Family taxonomy (2026-06-15).** `asset_classes` is seeded as a
**2-level, NETA-anchored shell**: 27 **parents** = the NETA equipment categories (19
active + 8 future/inactive), each carrying `neta_category` — the anchor into
`neta_procedures.category`; and 40 **leaf** classes = the practical apparatus a tech
selects (e.g. `cb_lv` / `cb_mvhv`; `it_ct` / `it_vt` / `it_cvt`), hung off a parent
via `parent_class_id`. NETA sections + tables attach **once** at the parent and are
inherited by every leaf (no duplication); `form_templates` + `assets` attach at the
**leaf** in later chips. Granularity is soft — a leaf can split later with no
restructuring. Migration `007` (generator `gen_shell_seed.py`); validated by
`test_007_asset_class_shell.py` (13 tests) on `records_dev`. Every active NETA
procedure has a leaf home (incl. the motor-control 2×2, the load tap-changer, and
DC machines); the 2 MCC composition procedures carry their refs as `crossref` items.

**Chip 2-backfill — leaf↔procedure links + the procedure graph (2026-06-16).** Two
tables scope each leaf's NETA universe and capture how procedures reference one
another: `asset_class_neta_procedure` (61 leaf→procedure links; RESERVED excluded; one
`is_primary` per leaf) and `neta_procedure_xref` (70 edges — 8 `crossref` composition,
e.g. MCC → bus/switches/breakers/starters; 62 `in_accordance` method-borrowing, e.g.
LTC 7.12.3 → 7.2.2). `to_procedure_id` resolves exact-section refs; category-level refs
(7.1, 7.6) stay raw. So a leaf's applicable NETA = its linked procedures (the Chip-2b
divergence is a precise leaf-grain query), and composites resolve constituents through
the graph + the asset tree. Migrations `008`/`009` (generator `gen_backfill_seed.py`);
validated by `test_008_backfill.py` (8 tests).

**Chip 2b — first datasheet (LV circuit breaker, 2026-06-17).** The first
`form_templates` row (`ats_lv_cb_v1`, bound to the `cb_lv` leaf): ONE composite template
whose `construction_type` selector (power / insulated_case / molded_case) gates the
molded-case deltas via `visible_if` — not three templates. The `field_schema` (11 sections)
**references + filters** the leaf's linked NETA 7.6.1.2 items; a **coverage invariant**
(validator-enforced) proves every ATS visual-mechanical + electrical item maps to a control —
no silent drops. Acceptance windows are **declared** (each carries a `tolerance_source` → the
TCC engine) but **resolved at provisioning (Chip 5)**, never fabricated into the template —
the designed lvbreakertcc→datasheet seam. Migration `010` (generator
`gen_lv_cb_template.py`); validated by `test_010_lv_cb_template.py` (17 tests). Full spec:
`04-LV-CB-DATASHEET-SPEC.md`.

**Chip 2b — MV/HV circuit breaker (2026-06-17).** The second datasheet (`ats_mvhv_cb_v1`,
bound to the `cb_mvhv` leaf) and the first to span **multiple NETA procedures**: ONE composite
whose `interrupting_medium` selector (air / oil / vacuum / SF6) gates each medium's deltas via
`visible_if`, covering the **union of all four procedures** (7.6.1.3 air, 7.6.2 oil, 7.6.3 vacuum,
7.6.4 SF6). The `field_schema` (15 sections) carries a **122-item union coverage invariant** across
the four — every ATS visual-mechanical + electrical item maps to a control, no silent drops, no
phantom refs. **R-A is apparatus-appropriate:** an MV/HV breaker has **no integral trip curve**
(protection is external relays, 7.9 / relaytcc), so acceptance windows declare a `tolerance_source`
of **`neta_table`** (IR 100.1, dielectric 100.19, pickup 100.20, SF6 gas 100.13) or **`mfr`** (contact
resistance, contact timing — the future mfr-tolerance-layer slot) — **never `tcc`**. Windows resolve
at provisioning (Chip 5), never fabricated. Migration `011` (generator `gen_mv_cb_template.py`);
validated by `test_011_mvhv_cb_template.py` (21 tests). Full spec: `05-MVHV-CB-DATASHEET-SPEC.md`.

**Chip 2b — transformers (2026-06-17).** The third 2b family and the first chip to ship **two
leaf-bound composites** in one migration: `ats_dry_xfmr_v1` (→ `xfmr_dry`; folds small 7.2.1.1 +
large 7.2.1.2 via a `dry_class` selector; 13 sections; 35-item union coverage) and
`ats_liquid_xfmr_v1` (→ `xfmr_liquid`; 7.2.2; 17 sections; 39 items, incl. LTC 7.12.3 / instrument-
transformer 7.10 / surge-arrester 7.19 cross-ref borrows). **Both fold two-winding / three-winding**
via a `winding_config` selector that gates the tertiary-winding (H-Y/X-Y/Y-G) measurement rows —
measurement granularity, not coverage. **R-A:** `tolerance_source` = `neta_table` (IR→**Table 100.5**,
torque→100.12) or `mfr` (winding resistance, bushing PF, turns-ratio — the future mfr-layer slot);
oil/DGA = standard-basis (ASTM D923 / IEEE C57.104); never `tcc`. Per-sheet coverage invariants
validator-enforced. Migration `012` (generator `gen_xfmr_template.py`); validated by
`test_012_xfmr_template.py` (17 tests). Full spec: `06-TRANSFORMER-DATASHEET-SPEC.md`.

**Chip 2b — switchgear + panelboard (2026-06-17).** The fourth 2b family, and the first to introduce
**parent-node binding**. The `switchgear` parent has 5 leaves, but **four share NETA 7.1.1**
(`swgr_lv_switchboard` / `swgr_mv_metalclad` / `swgr_padmount` / `swgr_vfi`) and `swgr_panelboard` is its
own `7.1.2` — so a sheet can't 1:1-bind to a leaf. Two sheets: **`ats_switchgear_v1`** (7.1.1; 13
sections; 35 ATS; an `assembly_type` selector for the 4 types; **bound to the PARENT `switchgear` node**
because four leaves share the procedure — assets classify to the leaf and resolve up at provisioning)
and **`ats_panelboard_v1`** (7.1.2; 6 sections; 14 ATS; leaf-bound to `swgr_panelboard`). IT (7.10) /
surge-arrester (7.19) / ground (7.13) / metering (7.11) items are cross-ref borrows covered, not
fabricated. **R-A:** `tolerance_source` = `neta_table` (IR→100.1, dielectric→100.2, torque→100.12) or
`mfr` (bolted-connection resistance); never `tcc`. Per-sheet coverage invariants validator-enforced.
Migration `013` (generator `gen_switchgear_template.py`); validated by `test_013_switchgear_template.py`
(15 tests). Full spec: `07-SWITCHGEAR-DATASHEET-SPEC.md`.

**Chip 2b — cables (2026-06-17).** The fifth 2b family; first of the operator-priority queue
(cables → IT → grounding → SA → motors). Back to the clean recipe — two leaf-bound single-procedure
sheets: **`ats_lv_cable_v1`** (`cable_lv` → 7.3.2, LV 600 V max; 6 sections; 11 ATS) and
**`ats_mvhv_cable_v1`** (`cable_mv` → 7.3.3, MV/HV; 11 sections; 18 ATS — adds the shielded-cable HV
battery: shield continuity, TDR, jacket integrity, dielectric withstand, tan-delta, partial discharge).
**R-A:** `tolerance_source` = `neta_table` (MV IR→100.1, tan-delta→100.6.6, torque→100.12) or `mfr`
(LV IR comparison, MV dielectric withstand); never `tcc`. Per-sheet coverage invariants
validator-enforced. Migration `014` (generator `gen_cable_template.py`); validated by
`test_014_cable_template.py` (13 tests). Full spec: `08-CABLE-DATASHEET-SPEC.md`.

> **Note — `records` vs `pm` schema:** the `pm` schema holds POST idempotency infra
> only. The maintenance *domain* data lives here as `records.pm_*`. The two are
> complementary, not duplicates: `pm.idempotency_keys` is what makes the `records.*`
> field-record sync replay-safe (see `01` §4).

---

## 5. Relationship to existing lanes (no duplication)

| Existing surface | Relationship |
|---|---|
| `work.*` / `mutation-seam` (`seam.*`) | Project/work execution + the governed write pipeline. `records.*` field records **sync through** the mutation-seam; `form_submissions.project_ref`/`work_package_ref` soft-link to it. |
| `pm.idempotency_keys` | The durable dedupe store that makes offline sync replay-safe. |
| `tcc.*` + `calc-engine` | Time-current-curve reference + calc. **Seeds** acceptance windows for breaker/relay data sheets during provisioning. |
| `forms-engine` / `forms-studio` / `power-test-converters` | Existing forms + report-generation + format-converter variants. **Candidate** report/export + authoring surfaces for this lane — but their consolidation is an open decision (see §6, D-FORMS). Do not wire report-gen to `records.*` until that is ruled. |
| `infra/.../source-lineage/apex-resa` NETA procedures/test items | Reference seed for `form_templates.field_schema` (later chip). |

---

## 6. Open lane decisions (held)

This lane owns the full form lifecycle — **define forms → capture/store → generate
reports** — but two structural calls are deliberately deferred, recorded here so they
are decided, not drifted into:

| ID | Decision | State | Notes |
|---|---|---|---|
| **D-FORMS** | How the forms + report-generation domain is structured | **HELD 2026-06-14** | Several early variants exist (`packages/forms-engine`, the `neta-forms` source repo, `packages/power-test-converters`, and the `RESA_Report_Scripts` bundle in `03`). They need a proper consolidation/restructuring decision before report-gen is wired to `records.*`. Until ruled: reuse nothing by default, build nothing parallel. Inputs catalogued in `03-PRIOR-ART-INPUTS.md`. |
| **D-SURFACE** | Where the lane's UI surfaces live (`apps/field-surface` capture PWA · `apps/forms-studio` authoring · or a new `apps/neta-*`) | **DECIDE PER-CHIP** | Settle when the capture chip (punch list Chip 4) and authoring/report chips actually start. Schema + charter work proceeds meanwhile. |
| **D-GIT** | Branch/merge model | **WORKING: chip-sized PRs → `main`** | Lane = this charter + punch list, not a long-lived branch. Each chip is a small PR; merge to `main` often. Revisit only if divergence becomes painful. |

`power-test-converters` (PTM/DTAX format conversion) is folded into this lane as
import/export tooling (punch list Chips 9–10), pending its place in the D-FORMS rework.

---

## 7. Maintenance

- Each guide carries its own status line; bump it when a chip lands.
- When the data model changes, update §4 here and the migration MANIFEST together.
- A change to the offline/sync decisions (`01` §2) amends `01` **first**, then the schema.
