# PowerDB Parity — Punch List (forward tracker)

> **Forward tracker for the NETA Records lane** (not a descriptive guide): the
> sequenced chips from foundation to PowerDB parity. Chip away the smallest durable
> bite first. Cite `00-MASTER-INDEX.md` and `01-OFFLINE-SYNC-ARCHITECTURE.md`.

- **Status:** LIVING — created 2026-06-12
- **Method:** each chip is a bounded, reversible, independently-reviewable landing.

---

## The ladder

| Chip | Scope | Depends on | Status |
|---|---|---|---|
| **1 — Data model foundation** | `neta` schema: 8 tables (asset_classes, assets, datasheet_templates, datasheets, test_results, pm_programs, pm_schedules, pm_events) + indexes + updated_at triggers + 2 read views; sync-contract columns on device-authoritative tables. Up/down migrations + MANIFEST. | — | **DRAFTED 2026-06-12 · PowerDB-VALIDATED 2026-06-13** (`infra/database/migrations/neta/001–004`; refinements in `02` §5) |
| **2 — Template seed / field-coverage matrix** | Parse the 845 active PowerDB `Device_Type` forms (start transformer + circuit-breaker families) into `datasheet_templates.field_schema` per the `02` §3 control model; prove every tag maps. Cross-reference the `apex-resa` NETA procedures/test items. First real ATS sheet (LV power circuit breaker). | 1, `02` | TODO — **next** |
| **3 — Sync substrate** | Stand up PowerSync (sync rules for the asset-subtree bucket; `uploadData` connector → mutation-seam; idempotency key per mutation). Hosting decision (Olares self-host vs Cloud). | 1 | TODO |
| **4 — Field PWA (capture)** | Installable offline PWA: open assigned job, render a data sheet from `field_schema`, capture readings to local SQLite, auto pass/fail vs the acceptance window, queue to outbox. | 1, 3 | TODO |
| **5 — Provisioning (office)** | Office surface: build job → asset list → assign templates → set acceptance windows (seed from TCC calc) + PM cadence → push bucket to device. | 1, 2, 3 | TODO |
| **6 — PM scheduling engine** | Recompute `pm_schedules.next_due_at` on event completion; the `v_pm_due` dashboard; overdue surfacing. | 1, 4 | TODO |
| **7 — Reporting / export** | Render a completed data sheet to PDF/Word via `forms-engine`; batch job report. | 1, 4 | TODO |
| **8 — FK activation** | Promote the deferred soft UUID links (`neta`→`org.sites`/`org.clients`, `neta`→`work.projects`/`work_packages`) to hard FKs once seed ordering is settled. | 1, 5 | TODO |
| **9 — PowerDB migration** | One-time import from a legacy PowerDB instance into `neta.*` (`provenance_source = powerdb_import`, `powerdb_source_id` preserved for round-trip/dedupe). | 1, 8 | TODO |
| **10 — Instrument import** | Pull readings directly off Megger/test sets (serial/USB/Bluetooth) into `test_results`. Major PowerDB differentiator; isolated lane. | 4 | DEFERRED |

---

## Notes

- **Chips 3 + 4 are the offline proof.** Until a tech can run a full job with the
  network off and reconcile cleanly, the lane has not met its defining requirement
  (`01` §1, D2).
- **Acceptance windows are provisioned, not computed in the field** — they ride down
  with the template so pass/fail is offline-native (`01` §5).
- **Single-writer holds through Chip 9.** Multi-tech concurrent capture on one sheet
  would reopen the conflict model (`01` §3) and is not on this ladder.
