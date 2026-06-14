# NETA Records — Master Index (PowerDB Replacement Lane)

> **The single source of truth for the NETA field-records domain of the APEX
> power-ops platform — the in-house replacement for PowerDB.** Every packet,
> migration, and surface in this lane starts here and cites the section it relies
> on. If reality and this index disagree, the index is fixed *first* (SSoT Law,
> inherited from the TCC lane) — never silently worked around.

- **Status:** SEEDED — lane opened 2026-06-12; Chip 1 (data model) drafted + **validated against the live PowerDB schema** (`02-POWERDB-SOURCE-MAP.md`, 2026-06-13); sync direction RULED (`01-OFFLINE-SYNC-ARCHITECTURE.md` §2)
- **Owner:** APEX NETA Records lane (operator: Jason Swenson)
- **Home:** `reference/neta-records/` (version-controlled beside the migrations it cites)

---

## 0. Why this lane exists

NETA testing firms run their field business on **PowerDB** (Megger's test-data
manager): equipment lists, standardized test data sheets, captured results with
auto pass/fail, and preventive-maintenance scheduling. PowerDB is a licensed,
Windows-centric, vendor-locked datastore. This lane builds the **in-house
replacement** on the platform's own Supabase/Postgres + Next.js stack so that:

- the asset register, data sheets, results, and PM cadence are **our data**, not a
  vendor silo;
- field capture works **fully offline** (vaults/substations) and reconciles cleanly;
- results flow into the platform's existing project/work, TCC, and reporting lanes
  instead of being trapped in a separate tool.

---

## 1. The four pillars

| # | Pillar | PowerDB analogue | Owns |
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
| **[01 — Offline-Sync Architecture](01-OFFLINE-SYNC-ARCHITECTURE.md)** | Provisioning / offline capture / reconcile; the device vs server authority split; the PowerSync + mutation-seam write path; the decisions of record | touching any `neta.*` table, sync rule, or the field PWA | **RULED 2026-06-12** (D1 PWA · D2 fully-offline · D3 PowerSync) |
| **[02 — PowerDB Source Map](02-POWERDB-SOURCE-MAP.md)** | The authoritative PowerDB→`neta` table/field mapping, the 16 form-family→asset-class crosswalk, the field/control model, and the refinements folded into the schema | importing from PowerDB, or asking "where does PowerDB field X go" | **CAPTURED 2026-06-13** (live Phoenix DB: 80 tables / 1,209 cols) |
| **[PowerDB Parity Punch List](POWERDB-PARITY-PUNCHLIST.md)** | Forward tracker: the sequenced chips from data model → asset catalog → datasheet capture → PM scheduling → reporting → PowerDB migration | planning what to build next, or recording a chip closed | **LIVING — created 2026-06-12** |

---

## 4. Data model summary (Chip 1)

The `neta` schema (migrations under `infra/database/migrations/neta/`). Eight
foundation tables; cross-schema links to `org.*`/`work.*` are **deferred soft UUID**
columns pending an FK-activation chip (mirrors the work→org deferred-FK pattern).

```
asset_classes ──┐
                ├─< assets >──< datasheets >──< test_results
                │       │            │  (template field readings + pass/fail)
                │       │            └── fulfilled-by ── pm_events
datasheet_templates ────┘                                   │
        │                                                    │
        └──< pm_programs >──< pm_schedules >──< pm_events >──┘
              (cadence)        (per-asset       (occurrences,
                                next-due)         link back to the
                                                  data sheet that closed them)
```

- **`assets`** is the keystone; `parent_asset_id` models the substation tree.
- **`datasheet_templates.field_schema`** (JSONB) makes the form catalog *data, not
  code* — versioned, `is_current` enforced one-per-`template_code`.
- **`test_results`** carries `expected/min_acceptable/max_acceptable` + `assessment`
  so auto pass/fail is self-contained (works offline).
- **`pm_events`** links to the `datasheets` row that fulfilled it — closing the
  asset → PM → data sheet → results loop.
- Device-authoritative tables (`datasheets`, `test_results`, `pm_events`) carry the
  sync contract columns (`origin_device`, `client_rev`, `client_captured_at`,
  `synced_at`) — see `01` §3.
- **PowerDB-validated refinements** (see `02` §5): `datasheets.as_found_as_left`
  (sheet-level), `datasheets.job_number` (the universal join key), `assets` GPS +
  Region/Jobsite/Plant/Substation hierarchy, and `result_value_kind = graph`.

> **Note — `neta` vs `pm` schema:** the `pm` schema holds POST idempotency infra
> only. The maintenance *domain* data lives here as `neta.pm_*`. The two are
> complementary, not duplicates: `pm.idempotency_keys` is what makes the `neta.*`
> field-record sync replay-safe (see `01` §4).

---

## 5. Relationship to existing lanes (no duplication)

| Existing surface | Relationship |
|---|---|
| `work.*` / `mutation-seam` (`seam.*`) | Project/work execution + the governed write pipeline. `neta.*` field records **sync through** the mutation-seam; `datasheets.project_ref`/`work_package_ref` soft-link to it. |
| `pm.idempotency_keys` | The durable dedupe store that makes offline sync replay-safe. |
| `tcc.*` + `calc-engine` | Time-current-curve reference + calc. **Seeds** acceptance windows for breaker/relay data sheets during provisioning. |
| `forms-engine` | Document generation (AHA/MOP/PSS). Becomes the **report/export** renderer for completed `neta` data sheets (Pillar reporting chip). |
| `infra/.../source-lineage/apex-resa` NETA procedures/test items | Reference seed for `datasheet_templates.field_schema` (later chip). |

---

## 6. Maintenance

- Each guide carries its own status line; bump it when a chip lands.
- When the data model changes, update §4 here and the migration MANIFEST together.
- A change to the offline/sync decisions (`01` §2) amends `01` **first**, then the schema.
