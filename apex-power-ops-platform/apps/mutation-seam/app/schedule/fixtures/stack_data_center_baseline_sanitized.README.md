# Golden Fixture — `stack_data_center_baseline_sanitized.xer`

**Packet:** `2026-04-18-pm-schema-020h`
**Contract:** `apps/mutation-seam/app/schedule/fixtures/BASELINE_XER_FIXTURE_CONTRACT.md` (authored under packet 020f)
**Substrate:** landed parser-reconciliation path from packet `2026-04-18-pm-schema-020g-a`
**Status:** admitted as the first sanitized baseline-bearing golden fixture under the 020f contract
**Scope:** import-lane only; no SQL, no bridge route, no PM UI, no schedule-write surface change

This README is the authoritative provenance and compliance record for the adjacent fixture file `stack_data_center_baseline_sanitized.xer`. It exists to satisfy §4.2 of the 020f fixture contract and to let the companion test in `apps/mutation-seam/tests/test_golden_fixture_020h.py` assert deterministic baseline emission against a known, enforceable surface.

---

## 1. Identity and provenance

- **Fixture path:** `apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.xer`
- **Export header:** `ERMHDR 16.2 2026-04-18 Project APEX StackDC-BaselineGolden-020h USER_APEX Databases mm/dd/yyyy USD`
- **Origin:** synthetic. This fixture was hand-authored under packet 020h against the 020f contract. It is **not** derived from a real client XER export and carries no sanitized artifacts of a real RESA project. All project names, project ids, task codes, and dates are invented for this fixture.
- **Sanitization:** because the fixture is synthetic, there is no upstream PII to scrub. The file contains no owner names, no facility addresses, no costs, no real vendor identifiers. `proj_url` values use the non-routable marker scheme `sanitized://stackdc/...`. The only human-readable label that could be mistaken for a real program is the baseline label `"Stack DC — Original Baseline R01"`, which is deliberately kept to exercise the `base_type_name` → `schedule.baseline_events.baseline_name` propagation path (020b §4.4).
- **Source hash:** not applicable — synthetic authorship under 020h. Future re-authoring MUST bump the baseline R-number (`R02`, `R03`, …) in both the `PROJECT.proj_short_name` of the baseline row and the `PROJBASELINE.base_type_name` label.
- **Operator:** authored under packet 020h by the PM Golden Fixture Admission role.

---

## 2. Project ids and baseline linkage

The fixture carries exactly two `PROJECT` rows and exactly one `PROJBASELINE` row, shaped so the loader's canonical baseline selection is deterministic.

| Role                  | `proj_id` | `proj_short_name`       | Notes                                                                                  |
| --------------------- | --------- | ----------------------- | -------------------------------------------------------------------------------------- |
| Live project          | `1001`    | `StackDC`               | `sum_base_proj_id = 9998` → points at the canonical baseline below                    |
| Baseline project      | `9998`    | `StackDC-BL-R01`        | `sum_base_proj_id` is empty; this row is baseline-only and MUST NOT surface as a live project |

The canonical `PROJBASELINE` row is:

```
proj_id           = 1001
base_proj_id      = 9998
base_type_name    = "Stack DC — Original Baseline R01"
last_update_date  = 2026-02-01 00:00
```

This row uses the **P6 column naming** (`base_proj_id`), satisfying contract §3.3's requirement that at least one row not rely on PyP6Xer's internal synonym. The loader's matched-baseline pipeline should therefore emit a single entry whose:

- `p6_baseline_proj_id` = `"9998"`
- `baseline_name` = `"Stack DC — Original Baseline R01"`
- matched tasks carry baseline dates from the `9998` TASK rows, not from the live `1001` TASK rows (§3.6 invariant).

---

## 3. Matched task_code set

The fixture defines three matched task_codes. Every matched baseline TASK row has non-NULL `target_start_date` and `target_end_date`, satisfying contract §3.4.

| `task_code` | Live `task_id` | Baseline `task_id` | Matched? |
| ----------- | -------------- | ------------------ | -------- |
| `A10`       | `7001`         | `7101`             | yes      |
| `A20`       | `7002`         | `7102`             | yes      |
| `A30`       | `7003`         | `7103`             | yes      |

Matched **set:** `{A10, A20, A30}`.

`task_id` values are **not** reused across projects (§3.4 second sentence): live task ids are in the `70xx` band and baseline task ids are in the `71xx` band. The matching rule is `task_code`, not `task_id`.

---

## 4. Declared negative cases (§3.5 compliance)

The fixture carries exactly two of the contract's four negative-case classes. This satisfies the "at least two" requirement of §3.5.

### Case 1 — baseline-only activity (reconciliation class 1)

- `task_code`: `A90`
- Baseline `task_id`: `7190`
- Baseline `task_name`: `"Retired lift plan"`
- Lives only on baseline project `9998`; no live-project counterpart exists.
- Purpose: proves the loader does **not** fabricate a live-side activity from a baseline-only row and does **not** include `A90` in the live task lane output.

### Case 2 — live-only activity (reconciliation class 2 — informational)

- `task_code`: `A99`
- Live `task_id`: `7004`
- Live `task_name`: `"Commissioning tests"`
- Lives only on live project `1001`; no baseline-project counterpart exists.
- Purpose: proves that when a live activity has no matched baseline task_code, the loader still emits the live task normally but does not synthesize a baseline-dated copy for it. `A99` MUST appear in the live task lane and MUST NOT surface in the emitted baseline entry's matched-tasks payload.

### Not carried

- Reconciliation class 3 (malformed `PROJBASELINE.base_proj_id` pointing at a non-existent PROJECT row) is **not** exercised by this fixture. A separate fixture may admit it later.
- Reconciliation class 4 (ambiguous canonical baseline with NULL `sum_base_proj_id`) is **not** exercised by this fixture. It is already covered by the in-memory parser test `test_load_xer_source_uses_sum_base_proj_id_to_pick_canonical_baseline` under packet 020e.2, so admitting a second on-disk fixture for it is out of scope for 020h.

---

## 5. Non-overload invariants (§3.6 compliance)

The fixture is deliberately shaped so baseline dates differ from live dates for **every** matched task_code. This gives regression detectors a deterministic wedge: any future loader change that silently copies live `target_*` into `baseline_*` will break the companion test immediately.

| `task_code` | Live `target_start_date` | Baseline `target_start_date` | Live `target_end_date` | Baseline `target_end_date` |
| ----------- | ------------------------ | ---------------------------- | ---------------------- | -------------------------- |
| `A10`       | `2026-05-04 07:00`       | `2026-04-27 07:00`           | `2026-05-05 17:00`     | `2026-04-28 17:00`         |
| `A20`       | `2026-05-06 07:00`       | `2026-04-29 07:00`           | `2026-05-08 17:00`     | `2026-05-01 17:00`         |
| `A30`       | `2026-05-11 07:00`       | `2026-05-04 07:00`           | `2026-05-15 17:00`     | `2026-05-08 17:00`         |

All three matched rows carry **non-NULL** baseline dates, so none of them are silently skipped by the loader's null-guard (020d §2.1 item 3).

---

## 6. Required sections present (§3.1 compliance)

| Section         | Rows | Notes                                                                     |
| --------------- | ---- | ------------------------------------------------------------------------- |
| `PROJECT`       | 2    | one live (`1001`), one baseline (`9998`)                                  |
| `PROJWBS`       | 1    | live-project root WBS (`5001`, name `StackDC Root`)                       |
| `TASK`          | 8    | 4 live (`A10`, `A20`, `A30`, `A99`) + 4 baseline (`A10`, `A20`, `A30`, `A90`) |
| `TASKPRED`      | 1    | live-project FS relationship `7002 ← 7001`                                |
| `PROJBASELINE`  | 1    | canonical `1001 → 9998` linkage with P6 `base_proj_id` column naming      |

All five required `%T` sections are present with at least one row each, and the `PROJBASELINE` section is the reason this fixture is eligible as a **baseline-bearing** golden fixture rather than a live-only one.

---

## 7. How the companion test exercises this fixture

The focused test `apps/mutation-seam/tests/test_golden_fixture_020h.py` asserts, against the loader's landed 020g-a substrate path (parser-reconciliation adapter for Reader-surface facts, raw-section shim for the PROJBASELINE lane):

1. Live-lane counts — exactly one live project (`1001`), one WBS (`5001`), four live tasks (`A10`, `A20`, `A30`, `A99`), and one relationship.
2. Emitted baseline entries — exactly one entry, with `p6_baseline_proj_id = "9998"` and `baseline_name = "Stack DC — Original Baseline R01"`.
3. At least one matched `schedule_task_id` — covers all three of `A10`, `A20`, `A30` with baseline dates from the `71xx` TASK rows.
4. At least one declared negative case exercised — Case 2 (`A99` live-only, present in live task lane, absent from baseline entry's matched tasks) is asserted explicitly; Case 1 (`A90` baseline-only, absent from live task lane) is asserted implicitly through the live-task count.
5. `_validate_baseline_entry()` passes against the emitted entry (contract §4 item 4).

This is the minimum set of assertions the 020f contract admits; broader assertions against `upsert_baselines()` or `schedule.baseline_events` belong to a host-disposition packet, not to the fixture admission packet.

---

## 8. Compliance statement

This fixture and this README:

1. Author no SQL. Author no DDL. Author no migration.
2. Do not modify `apps/mutation-seam/app/schedule/loader.py`.
3. Do not modify `APEX_Schema_V2/XER_Import_Export_Spec.md` or the 020a / 020b authority memos.
4. Add no bridge route and change no response shape.
5. Do not modify the PM UI or any other client code.
6. Preserve and extend the "no synthetic client-side baseline fabrication" rule: every baseline date in this fixture originates from a baseline-project TASK row, and no live `target_*` field is copied into a baseline field.
7. Do not assume the abandoned `020g-b` companion-JSON substrate; the companion test targets the landed `020g-a` parser-reconciliation substrate only.

---

*Authored under packet `2026-04-18-pm-schema-020h`. Fixture-admission only; no runtime changes.*
