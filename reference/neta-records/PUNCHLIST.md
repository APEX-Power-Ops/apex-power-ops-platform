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
| **1 — Data model foundation** | `neta` schema: 8 tables (asset_classes, assets, datasheet_templates, datasheets, test_results, pm_programs, pm_schedules, pm_events) + indexes + updated_at triggers + 2 read views; sync-contract columns on device-authoritative tables. Up/down migrations + MANIFEST. | — | **DRAFTED 2026-06-12 · BASELINE-VALIDATED 2026-06-13** (`infra/database/migrations/neta/001–004`; refinements in `02` §5) |
| **2 — Template seed / field-coverage matrix** | Parse the incumbent's test forms (start transformer + circuit-breaker families) into `datasheet_templates.field_schema` per the `02` §3 control model; prove every field maps. Cross-reference the `apex-resa` NETA procedures/test items. First real ATS sheet (LV power circuit breaker). | 1, `02` | TODO — **next** |
| **3 — Sync substrate** | Stand up PowerSync (sync rules for the asset-subtree bucket; `uploadData` connector → mutation-seam; idempotency key per mutation). Hosting decision (Olares self-host vs Cloud). | 1 | TODO |
| **4 — Field PWA (capture)** | Installable offline PWA: open assigned job, render a data sheet from `field_schema`, capture readings to local SQLite, auto pass/fail vs the acceptance window, queue to outbox. | 1, 3 | TODO |
| **5 — Provisioning (office)** | Office surface: build job → asset list → assign templates → set acceptance windows (seed from TCC calc) + PM cadence → push bucket to device. | 1, 2, 3 | TODO |
| **6 — PM scheduling engine** | Recompute `pm_schedules.next_due_at` on event completion; the `v_pm_due` dashboard; overdue surfacing. | 1, 4 | TODO |
| **7 — Reporting / export** | Render a completed data sheet to a report (PDF/Word); batch job report. | 1, 4, D-FORMS | **HELD** — blocked on the forms/report-domain restructuring decision (`00` §6 D-FORMS); do not wire to `forms-engine` or any variant until ruled |
| **8 — FK activation** | Promote the deferred soft UUID links (`neta`→`org.sites`/`org.clients`, `neta`→`work.projects`/`work_packages`) to hard FKs once seed ordering is settled. | 1, 5 | TODO |
| **9 — Legacy-data migration** | One-time import from the legacy datastore into `neta.*` (`source = legacy_import`, `legacy_source_id` preserved; keyed by `job_number`). Mapping derived from the operator-held export at this chip — not committed (`02` §6). | 1, 8, converters | TODO |
| **10 — Instrument / format import** | Pull readings off field test sets (serial/USB/Bluetooth) into `test_results`, and convert legacy test-data formats (PTM/DTAX) via `packages/power-test-converters` (now lane-owned). A capability of the incumbent to match; isolated lane. | 4 | DEFERRED |

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
