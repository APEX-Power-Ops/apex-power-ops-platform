# NETA Records — PowerDB Source Map

> **The authoritative mapping from the legacy PowerDB schema to the `neta` domain.**
> This is the validated ground truth the Chip-1 schema was checked against. When a
> question is "how does PowerDB do X / where does field Y go," answer from here.

- **Status:** CAPTURED 2026-06-13 from the live Phoenix-region database
- **Owner:** APEX NETA Records lane
- **Home:** `reference/neta-records/` (cited by `00-MASTER-INDEX.md` and the `neta/` migrations)

---

## 1. Source of record (host-only, not committed)

The PowerDB material lives on the operator workstation at **`D:\PDB\`** — outside
the repo and **gitignored on purpose** (same treatment as the TCC `.accdb`). This
doc is the committed synthesis; the raw data stays at the source.

| Artifact (`D:\PDB\`) | What it is |
|---|---|
| `prod_rgn_Services-Phoenix.mdf` (1.1 GB) | Live SQL Server region DB (read-only mirror of `resa.sync.powerdb.us:45037`) |
| `POWERDB_SCHEMA_COMPREHENSIVE_AUDIT.md` | The 80-table / 1,209-column audit + GUID/FK maps |
| `PowerDB_Schema_Audit.csv` · `_ForeignKeys.csv` · `_GUID_Columns.csv` | Machine-readable schema (1,209 cols / 45 FKs / 163 GUIDs) |
| `Asset Export.csv` · `Job Export.csv` · `Result Export.csv` | UTF-16 data exports (assets / jobs / results) |
| `*_Form_Controls.csv`, decoded `*.pxd` → `_data.json` | Per-form **field/control inventory** (the tag list) |
| `PdbTemplate.xlsx`, `FormUpdate.xlsx`, `RTMSTemplates/` | Form/report templates |

**Scale:** 80 tables · 1,209 columns · 149 jobs (139 active) · 9,690 results
(7,572 active) · 884 forms (845 active) · 10,189 equipment records (9,524 active).

---

## 2. Entity mapping (PowerDB → `neta`)

| PowerDB table | Role | `neta` target | Notes |
|---|---|---|---|
| `Relay` | Equipment **master** record | `neta.assets` | The persistent asset (PowerDB calls equipment "Relay" regardless of type). Keystone. |
| `Device_Type` | Test **form** definition | `neta.datasheet_templates` | `DeviceName`→title, `Family`→asset_class, `MaintPeriod`→pm interval, `FormNumber`, `IEEEDevice` |
| `Results_Header` | A filled test **instance** | `neta.datasheets` | One row per (asset × form × visit). Carries `AsFoundAsLeft`, `TestStatusGUID`, Org1-8, Tester, TestDate |
| `Results_Values`/`_FP`/`_String`/`_Digital`/`_Graph` | Typed per-field **readings** | `neta.test_results` | The typed split → `result_value_kind` (numeric/numeric/text/boolean/graph) |
| `PdbJob` | Job / project | `work.projects` (soft `project_ref` + `job_number`) | **`JobNumber` is the universal join key**, not a GUID |
| `PdbAddrInfo` / `PdbAddrHeader` | Sites / companies | `org.sites` / `org.clients` (soft `site_ref`/`client_ref`) | |
| `Device_Type.Family` (16 families) | Equipment categories | `neta.asset_classes` | See §4 |
| `PdbTestStatus` | Test-status vocabulary | `neta.datasheets.test_status_label` (+ `overall_assessment`) | Richer than pass/fail |
| `PdbCompliance` / `AssetAttribute` | Compliance / custom attrs | (later chip) | |

### Identity & soft-delete conventions (carried into import logic, not schema)
- Primary keys are `nvarchar(20)` **GUIDs** (`JobGUID`, `ResultsGUID`, `DeviceGUID`,
  `RelayGUID`, `AddrGUID`) → preserved in `powerdb_source_id` for round-trip/dedupe.
- **`JobNumber`** (human-readable) is the cross-system link → `datasheets.job_number`.
- Every major table uses `bIsDel` (0=active/1=deleted) and `bLocked`; `RegionGuid`
  scopes by region. Import filters `bIsDel=0`.

---

## 3. Field / control model (answers "is every tag accounted for?")

A `Device_Type` form is a **hierarchy of controls** (subforms / embedded
worksheets). Each control row (`*_Form_Controls.csv`) carries:

| PowerDB control attribute | Meaning | `field_schema` key |
|---|---|---|
| `Tag Name` | Stable field id | `tag` |
| `Control Type` | Text / Numeric / Dropdown / Graphic / Embedded WS / Subform | `control_type` |
| `Data Type` | `Data` (stored) · `Job Specific` (inherited from job) · calc | `data_source` |
| `Control Path / Parent Name(s)` | Subform nesting | `parent` |
| `Read Only` | computed/label vs enterable | `readonly` |
| `Location (X/Y)` | print layout | (deferred — not needed for capture) |

So the **complete field inventory = the 845 active `Device_Type` forms × their
controls.** `neta.datasheet_templates.field_schema` is the open container that holds
them; `neta.test_results` (keyed by `field_key` = `tag`) holds the captured value.
Proving 100% coverage is **Chip 2** — parse each family's forms into `field_schema`.

> **`Job Specific` fields are NOT stored per sheet** — they're inherited from the
> job (JobNumber, Customer, Address, User, Page). The importer denormalizes them or
> resolves them via `project_ref`; they are not `test_results` rows.

---

## 4. Form families → asset classes (NETA crosswalk)

`Device_Type.Family` (form counts) → seed for `neta.asset_classes`:

| Family | Forms | NETA § |
|---|---|---|
| CIRCUIT BREAKER | 217 | 7.6 |
| RELAYS | 77 | 7.9 |
| CABLES | 70 | 7.3 |
| TRANSFORMERS | 52 | 7.2 |
| INSTRUMENT TRANSFORMERS | 36 | 7.10 |
| MISCELLANEOUS | 37 | — |
| BATTERIES | 31 | 7.17 |
| MOTOR CONTROL CENTERS | 24 | 7.16 |
| SWITCHBOARDS | 24 | 7.1 |
| GROUND MAT / GROUNDING | 19 | 7.13 |
| LOADBREAK SWITCHES | 16 | 7.5 |
| TRANSFER SWITCHES | 14 | 7.11 |
| GENERATORS | 13 | 7.15 |
| POWER FACTOR TESTS | 13 | — |
| INFRARED | 12 | thermography |
| INSULATION FLUID | 10 | 7.2 |

---

## 5. Refinements folded into Chip 1 (migration `001`/`002`/`003`)

Decisions the real schema forced, with where they landed:

| # | Finding from PowerDB | Schema change |
|---|---|---|
| R1 | `Results_Header.AsFoundAsLeft` is **sheet-level** (6-char), not per-field | `neta.as_found_as_left_enum` + `datasheets.as_found_as_left` (a maintenance visit = two sheets) |
| R2 | Assets carry a Region›Jobsite›Plant›Substation›Org5-8 hierarchy + GPS | `assets.region/jobsite/plant/substation` flat strings (import fidelity) + `gps_lat`/`gps_long`; tree stays on `parent_asset_id` |
| R3 | Typed result tables incl. `Results_Graph` | added `graph` to `result_value_kind_enum` |
| R4 | `JobNumber` is the universal cross-system key | `datasheets.job_number` (+ index) alongside soft `project_ref` |
| R5 | `PdbTestStatus` richer than pass/fail | `datasheets.test_status_label` (import fidelity) beside `overall_assessment` |
| R6 | Forms are a hierarchical control tree (type/data-source/parent/readonly) | `field_schema` comment ruled to the PowerDB control model |
| R7 | `Device_Type.MaintPeriod` defines PM cadence on the form/type | confirms `pm_programs.template_id` + interval (no change) |

---

## 6. Deferred / open (honesty register)

- **Per-form field parsing** (Chip 2) — the `field_schema` population from the 845
  forms is not done; coverage is *structurally* possible, not yet *proven*.
- **Custom columns** — `PdbJob.Info1-10`, `Results_Header.UserStr0-9/UserNum0-4/`
  `UserDate0-2` are generic extension fields; not yet modeled (candidate: a
  `custom_fields jsonb`).
- **Compliance / attributes** — `PdbCompliance`, `AssetAttribute`, `ResultAttribute`
  not yet mapped.
- **Archive/history tables** (`*Archive`, `ResultsHdrBinary_HIST`) — out of scope.
- **Sync server** — `resa.sync.powerdb.us:45037` is read-only; write-back to PowerDB
  requires Megger approval. Our replacement does not depend on it.
