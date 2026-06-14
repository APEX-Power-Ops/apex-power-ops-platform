# NETA Records — Master Index (NETA Field-Records Lane)

> **The single source of truth for the NETA field-records domain of the APEX
> power-ops platform — the in-house replacement for the legacy field-test
> datastore.** Every packet, migration, and surface in this lane starts here and
> cites the section it relies on. If reality and this index disagree, the index is
> fixed *first* (SSoT Law, inherited from the TCC lane) — never silently worked around.

- **Status:** SEEDED — lane opened 2026-06-12; Chip 1 (data model) drafted + **validated against the legacy field-test baseline** (`02-LEGACY-BASELINE.md`, 2026-06-13); sync direction RULED (`01-OFFLINE-SYNC-ARCHITECTURE.md` §2)
- **Owner:** APEX NETA Records lane (operator: Jason Swenson)
- **Home:** `reference/neta-records/` (version-controlled beside the migrations it cites)

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
| **[01 — Offline-Sync Architecture](01-OFFLINE-SYNC-ARCHITECTURE.md)** | Provisioning / offline capture / reconcile; the device vs server authority split; the PowerSync + mutation-seam write path; the decisions of record | touching any `neta.*` table, sync rule, or the field PWA | **RULED 2026-06-12** (D1 PWA · D2 fully-offline · D3 PowerSync) |
| **[02 — Legacy Baseline](02-LEGACY-BASELINE.md)** | The capability floor the platform must replace and surpass: the equipment categories, the entity/field concepts, the control model, where we must exceed the incumbent, and the one-time-migration note | scoping what to build/beat, or planning the legacy-data migration | **CAPTURED 2026-06-13** |
| **[Punch List](PUNCHLIST.md)** | Forward tracker: the sequenced chips from data model → asset catalog → datasheet capture → PM scheduling → reporting → legacy-data migration | planning what to build next, or recording a chip closed | **LIVING — created 2026-06-12** |

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
- **Baseline-validated refinements** (see `02` §5): `datasheets.as_found_as_left`
  (sheet-level), `datasheets.job_number` (the external join key), `assets` GPS +
  region/jobsite/plant/substation hierarchy, and `result_value_kind = graph`.

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
| `forms-engine` / `forms-studio` / `power-test-converters` | Existing forms + report-generation + format-converter variants. **Candidate** report/export + authoring surfaces for this lane — but their consolidation is an open decision (see §6, D-FORMS). Do not wire report-gen to `neta.*` until that is ruled. |
| `infra/.../source-lineage/apex-resa` NETA procedures/test items | Reference seed for `datasheet_templates.field_schema` (later chip). |

---

## 6. Open lane decisions (held)

This lane owns the full datasheet lifecycle — **define forms → capture/store → generate
reports** — but two structural calls are deliberately deferred, recorded here so they
are decided, not drifted into:

| ID | Decision | State | Notes |
|---|---|---|---|
| **D-FORMS** | How the forms + report-generation domain is structured | **HELD 2026-06-14** | Several early variants exist (`packages/forms-engine`, the `neta-forms` source repo, `packages/power-test-converters`). They need a proper consolidation/restructuring decision before report-gen is wired to `neta.*`. Until ruled: reuse nothing by default, build nothing parallel. |
| **D-SURFACE** | Where the lane's UI surfaces live (`apps/field-surface` capture PWA · `apps/forms-studio` authoring · or a new `apps/neta-*`) | **DECIDE PER-CHIP** | Settle when the capture chip (punch list Chip 4) and authoring/report chips actually start. Schema + charter work proceeds meanwhile. |
| **D-GIT** | Branch/merge model | **WORKING: chip-sized PRs → `main`** | Lane = this charter + punch list, not a long-lived branch. Each chip is a small PR; merge to `main` often. Revisit only if divergence becomes painful. |

`power-test-converters` (PTM/DTAX format conversion) is folded into this lane as
import/export tooling (punch list Chips 9–10), pending its place in the D-FORMS rework.

---

## 7. Maintenance

- Each guide carries its own status line; bump it when a chip lands.
- When the data model changes, update §4 here and the migration MANIFEST together.
- A change to the offline/sync decisions (`01` §2) amends `01` **first**, then the schema.
