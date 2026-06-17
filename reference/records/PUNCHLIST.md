# NETA Records — Punch List (forward tracker)

> **Forward tracker for the NETA Records lane** (not a descriptive guide): the
> sequenced chips from foundation to a field-ready platform that replaces — and
> surpasses — the legacy field-test datastore. Chip away the smallest durable bite
> first. Cite `00-MASTER-INDEX.md`, `01-OFFLINE-SYNC-ARCHITECTURE.md`, and the
> capability floor in `02-LEGACY-BASELINE.md`.

- **Status:** LIVING — created 2026-06-12
- **Method:** each chip is a bounded, reversible, independently-reviewable landing.

---

## The ladder

| Chip | Scope | Depends on | Status |
|---|---|---|---|
| **1 — Data model foundation** | `records` schema: 8 tables (asset_classes, assets, form_templates, form_submissions, form_field_values, pm_programs, pm_schedules, pm_events) + indexes + updated_at triggers + 2 read views; sync-contract columns on device-authoritative tables. Up/down migrations + MANIFEST. | — | **DRAFTED 2026-06-12 · BASELINE-VALIDATED 2026-06-13** (`infra/database/migrations/records/001–004`; refinements in `02` §5) |
| **2a — NETA reference layer** | Seed the authoritative NETA standard into the DB (`records.neta_procedures` / `neta_test_items` / `neta_tables`) from the NETA master equipment table (ANSI/NETA ATS-2025 / MTS-2023). Reusable across all classes; the field-trust acceptance basis. | 1 | **DONE 2026-06-15** — `005`/`006` (72 / 3,920 / 43), `test_005` 7/7 on `records_dev`; branch `records/chip2a-neta-reference` |
| **2-shell — Family taxonomy** | Seed `asset_classes` as a 2-level, NETA-anchored shell: **27 NETA-category parents** (19 active + 8 future) + **40 practical leaf apparatus classes** (every active NETA procedure homed). Parents carry the `neta_category` anchor (NETA attaches once, inherited by leaves); leaves carry templates/assets. Granularity soft — split a leaf later with no restructure. | 1, 2a | **DONE 2026-06-15** — `007` + `gen_shell_seed.py`, `test_007` 13/13 on `records_dev`; branch `records/chip2-shell` |
| **2-backfill — NETA procedure links** | `asset_class_neta_procedure` (leaf→procedure, RESERVED excluded, one primary/leaf) + `neta_procedure_xref` (the procedure→procedure graph: `crossref` composition + `in_accordance` method-borrowing). Scopes each leaf's NETA universe so the 2b divergence is a precise leaf-grain query; composites resolve constituents via the graph + the asset tree. | 1, 2a, 2-shell | **DONE 2026-06-16** — `008`/`009` (61 links + 70 edges), `test_008` 8/8 on `records_dev`; branch `records/chip2-shell` |
| **2b — Datasheet templates (filter + curate)** | Author `form_templates.field_schema` per **leaf class** by **referencing + filtering** the leaf's linked Chip-2a NETA items + the common-datasheet practical fields (the legacy LV power-CB form witnesses the real sheet). The NETA-vs-common-datasheet divergence surfaces as a query (`neta_test_items` LEFT JOIN field refs, scoped to the leaf's linked procedures) for operator ruling — not a copy. First real ATS sheet = LV power circuit breaker. | 2a, 2-shell, 2-backfill, `02` | **LV CB + MV/HV CB DONE.** LV (`010` + `gen_lv_cb_template.py`, `test_010` 17/17; `ats_lv_cb_v1`, 11 sections, `construction_type` selector, NETA 7.6.1.2 = 25 items, `tolerance_source`→tcc; **merged PR #7** `5970e1db`; spec `04`). MV/HV (`011` + `gen_mv_cb_template.py`, `test_011` 21/21; `ats_mvhv_cb_v1`, 15 sections, `interrupting_medium` selector air/oil/vacuum/sf6, **union coverage = 122 items** across 7.6.1.3/7.6.2/7.6.3/7.6.4, `tolerance_source`→**neta_table+mfr** NOT tcc — MV/HV has no integral trip curve; spec `05`). TRANSFORMERS (`012` + `gen_xfmr_template.py`, `test_012` 17/17; TWO leaf-bound composites — `ats_dry_xfmr_v1` [`xfmr_dry`, 13 sections, `dry_class` small/large fold] + `ats_liquid_xfmr_v1` [`xfmr_liquid`, 17 sections, 7.2.2], **BOTH fold 2W/3W via `winding_config`**; coverage 35 + 39; `tolerance_source`→neta_table(100.5)+mfr; spec `06`). Remaining families (switchgear/cables/...) = 2b repeats. |
| **3 — Sync substrate** | Stand up PowerSync (sync rules for the asset-subtree bucket; `uploadData` connector → mutation-seam; idempotency key per mutation). Hosting decision (Olares self-host vs Cloud). | 1 | TODO |
| **4 — Field PWA (capture)** | Installable offline PWA: open assigned job, render a data sheet from `field_schema`, capture readings to local SQLite, auto pass/fail vs the acceptance window, queue to outbox. | 1, 3 | TODO |
| **5 — Provisioning (office)** | Office surface: build job → asset list → assign templates → set acceptance windows (seed from TCC calc) + PM cadence → push bucket to device. | 1, 2, 3 | TODO |
| **6 — PM scheduling engine** | Recompute `pm_schedules.next_due_at` on event completion; the `v_pm_due` dashboard; overdue surfacing. | 1, 4 | TODO |
| **7 — Reporting / export** | Render a completed data sheet to a report (PDF/Word); batch job report. | 1, 4, D-FORMS | **HELD** — blocked on the forms/report-domain restructuring decision (`00` §6 D-FORMS); do not wire to `forms-engine` or any variant until ruled |
| **8 — FK activation** | Promote the deferred soft UUID links (`records`→`org.sites`/`org.clients`, `records`→`work.projects`/`work_packages`) to hard FKs once seed ordering is settled. | 1, 5 | TODO |
| **9 — Legacy-data migration** | One-time import from the legacy datastore into `records.*` (`source = legacy_import`, `legacy_source_id` preserved; keyed by `job_number`). Mapping derived from the operator-held export at this chip — not committed (`02` §6). | 1, 8, converters | TODO |
| **10 — Instrument / format import** | Pull readings off field test sets (serial/USB/Bluetooth) into `form_field_values`, and convert legacy test-data formats (PTM/DTAX) via `packages/power-test-converters` (now lane-owned). A capability of the incumbent to match; isolated lane. | 4 | DEFERRED |

---

## Notes

- **Chips 3 + 4 are the offline proof.** Until a tech can run a full job with the
  network off and reconcile cleanly, the lane has not met its defining requirement
  (`01` §1, D2).
- **Acceptance windows are provisioned, not computed in the field** — they ride down
  with the template so pass/fail is offline-native (`01` §5).
- **Single-writer holds through Chip 9.** Multi-tech concurrent capture on one sheet
  would reopen the conflict model (`01` §3) and is not on this ladder.
- **The legacy datastore is a baseline, not a target** — chips are scoped to clear
  and surpass the floor in `02`, not to clone it.
- **Forms/report domain is HELD** (`00` §6 D-FORMS): several early variants
  (`forms-engine`, `neta-forms`, `power-test-converters`) await a consolidation ruling
  before Chip 7 / report-gen proceeds.
- **UI surface placement is per-chip** (`00` §6 D-SURFACE) — not pre-assigned here.
- **Git model:** chip-sized PRs into `main` (`00` §6 D-GIT).
