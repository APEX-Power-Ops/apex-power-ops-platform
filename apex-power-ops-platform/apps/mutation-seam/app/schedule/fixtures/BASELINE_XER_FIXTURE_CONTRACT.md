# Baseline-Bearing XER Fixture Contract

**Packet:** `2026-04-18-pm-schema-020f`
**Status:** authoritative fixture contract — golden-fixture admission default
**Owner:** PM Real XER Verification Author
**Scope:** governs what a `.xer` file must contain before it may be admitted as a golden fixture for the schedule loader's baseline lane (`load_xer_source` → `upsert_baselines`, per packets 020b / 020c / 020d)

This contract is authority-level. It does **not** author SQL, does **not** modify the loader, and does **not** add bridge routes or PM UI behavior. Its sole purpose is to let later XER-tools packets (020g+) admit concrete `.xer` files against a known, enforceable surface.

---

## 1. Why this contract exists

Packet 020b fixed the XER → APEX baseline mapping semantics. Packet 020c landed the `schedule.baseline_events` persistence lane and `upsert_baselines()`. Packet 020d wired the XER parser to emit `baselines` entries into that lane behind a compatibility-layer attribute probe.

Packet 020f then went to actually *verify* the real host parser. The verification surfaced that:

1. The current installed PyP6Xer `Reader` surface (v1.016.00) does **not** expose any `projbaselines` / `baselineprojects` collection, and its class model does **not** include a PROJBASELINE or BASELINEPROJECT row type.
2. The canonical Primavera XER tables the P6 side actually uses to carry baseline linkage (`PROJBASELINE`, sometimes `BASELINEPROJECT`) are **not** parsed by PyP6Xer 1.016.00 at all, so a baseline-bearing `.xer` routed through the current loader emits zero baseline entries even when the raw file is fully valid.
3. Community-sourced XER samples in the PM-Pro-Guide corpus that have the word "Baseline" in their filename (e.g. `Baseline Zone 2 Rev.01.xer`) are **not** baseline-bearing in the P6 sense — they are single-PROJECT exports whose `sum_base_proj_id` is NULL and whose `%T` sections contain no PROJBASELINE / BASELINEPROJECT rows.

Because of (1)–(3), the loader cannot today "just read" a random `.xer` from the field and produce baseline truth. A fixture we call "golden" must therefore be explicitly shaped against this contract so both the current no-op path and any future parser upgrade (or side-channel baseline reader) can be validated deterministically.

---

## 2. Definitions

- **Live project** — the `PROJECT` row whose activities represent the plan RESA is working against. In APEX terms, this is the row that backs `schedule.projects` after a normal import.
- **Baseline project** — a separate `PROJECT` row whose activities are a frozen copy of the live project at a point in time. Identified via `PROJBASELINE.base_proj_id` (or `BASELINEPROJECT.base_proj_id` in older exports).
- **Baseline linkage** — a row in the `PROJBASELINE` / `BASELINEPROJECT` table that binds a baseline `proj_id` to the live `proj_id` it belongs to.
- **Matched baseline task** — a baseline-project `TASK` row whose `task_code` equals a live-project `TASK` row's `task_code`. Its `target_start_date` / `target_end_date` become the live task's `baseline_start_at` / `baseline_end_at`.
- **Preferred baseline** — when a live project has more than one `PROJBASELINE` row, the one whose `base_proj_id` equals the live `PROJECT.sum_base_proj_id`.

---

## 3. Required content

A `.xer` file MAY be admitted as a golden fixture under `apps/mutation-seam/app/schedule/fixtures/` only if it contains, at minimum:

### 3.1 Sections

The exported XER MUST contain **all** of these `%T`-headed sections with at least one row each:

- `PROJECT` — at least two rows (one live, one baseline)
- `PROJWBS` — the live project's WBS hierarchy
- `TASK` — live-project activities AND baseline-project activities (same `task_code` values on both sides for matched rows)
- `TASKPRED` — the live project's predecessor relationships
- **`PROJBASELINE`** (or `BASELINEPROJECT` in older exports) — at least one row

A fixture that lacks a `PROJBASELINE` / `BASELINEPROJECT` section is **not** eligible for admission as a baseline-bearing golden fixture. It may still be admitted as a **live-only** fixture for unrelated tests, but it MUST NOT be used to claim baseline-lane coverage.

### 3.2 PROJECT rows

- Exactly one row is the live project; its `sum_base_proj_id` points at the baseline project that the live project considers canonical. `sum_base_proj_id` MAY be NULL if the fixture is deliberately exercising the "no preferred baseline" reconciliation case (020b §4.3 item 4), in which case the fixture's companion `README.md` MUST explicitly call that out.
- At least one row is a baseline project. Its `proj_short_name` SHOULD include the baseline name (for example `Stack DC — Original Baseline`).

### 3.3 PROJBASELINE / BASELINEPROJECT rows

- Each row MUST carry both `proj_id` (the live project) and `base_proj_id` (the baseline project). At least one row MUST use the P6 column naming (`base_proj_id`) — do not hand-author a fixture that only uses the PyP6Xer-internal synonym.
- Each row SHOULD carry a human-readable label (`base_type_name` or equivalent). This label propagates to `schedule.baseline_events.baseline_name` per 020b §4.4.

### 3.4 TASK rows on the baseline project

- For every matched baseline task on the live project, the corresponding baseline-project TASK row MUST have non-NULL `target_start_date` and `target_end_date`. Baseline TASK rows with NULL targets are silently ignored by the loader (020d §2.1 item 3); a fixture that relies on NULL baseline dates to cover a negative case MUST declare that intent.
- The baseline-project TASK rows MUST use the **same `task_code` values** as their live-project counterparts for every row the fixture claims to be matched. `task_id` values MUST NOT be reused between projects — P6 assigns them per project and the matching rule is `task_code`, not `task_id`.

### 3.5 Negative-case coverage (at least two of the following)

A golden fixture MUST include at least **two** of these negative-case rows, so the loader's reconciliation classes in 020b §4.3 stay exercised:

1. A baseline-project activity with a `task_code` that does **not** exist on the live project. (Reconciliation class 1.)
2. A live-project activity that has no baseline counterpart, even though a `PROJBASELINE` row exists. (Reconciliation class 2 — informational.)
3. A `PROJBASELINE` row whose `base_proj_id` has no matching baseline `PROJECT` row in the XER. (Reconciliation class 3 — malformed export.)
4. A second `PROJBASELINE` row on the same live project where `sum_base_proj_id` is NULL, so the loader must skip emission for that live project. (Reconciliation class 4.)

The fixture's companion `README.md` MUST enumerate which negative cases it carries and which `task_code` values embody them.

### 3.6 Non-overload invariants

A golden fixture MUST NOT be shaped in a way that would induce the loader to violate any of these invariants:

- **No synthetic fabrication** — the baseline dates MUST originate from baseline-project TASK rows, not from the live project's `target_*` fields.
- **No current-plan overload** — matched baseline rows MUST differ from the live project's `target_*` for at least one activity, so a future regression that silently copies live `target_*` into `baseline_*` is detectable.
- **No export-lane coupling** — a golden fixture is never used to validate XER export behavior under 020b §5.4; it is import-lane-only.

---

## 4. Admission process

Admission of a concrete `.xer` as a golden fixture is governed by its own packet (020g or later). To be admitted, the file MUST:

1. Be sanitized for client PII — no real owner names, no real facility addresses, no real costs.
2. Be accompanied by a `README.md` under `apps/mutation-seam/app/schedule/fixtures/` declaring:
   - the exact live and baseline `proj_id` values,
   - the canonical `PROJBASELINE` row it relies on,
   - the set of matched `task_code` values,
   - the negative cases it carries (§3.5),
   - its provenance (operator, sanitization script, source XER hash).
3. Carry a focused test in `apps/mutation-seam/tests/` that asserts, against the admitted fixture:
   - the loader's live projects/wbs/tasks counts,
   - the emitted `baselines` entries' `p6_baseline_proj_id` and `baseline_name`,
   - at least one matched `schedule_task_id`,
   - at least one declared negative case is exercised (unmatched `task_code`, malformed linkage, or skipped-emission for an ambiguous canonical baseline).
4. Pass the `_validate_baseline_entry()` contract already enforced by the 020c persistence lane.

---

## 5. Parser-surface prerequisite

Because PyP6Xer 1.016.00 does **not** surface PROJBASELINE / BASELINEPROJECT rows, the loader will today emit **zero** baseline entries even for a contract-compliant fixture. Before a concrete admitted `.xer` fixture can produce meaningful test coverage, one of the following MUST land in its own separately authorized packet:

- **Option A — parser-side reader shim**: add a baseline-linkage reader (either a PyP6Xer fork / PR adding `projbaselines` / `baselineprojects`, or a narrow in-repo `%T\tPROJBASELINE` / `%T\tBASELINEPROJECT` scanner) that the loader's compatibility layer can detect via the same `_get_collection` probe names it already checks.
- **Option B — out-of-band baseline companion**: accept a side-car JSON under `fixtures/` with the shape already consumed by `upsert_baselines()`, while the primary `.xer` provides the live project. This bypasses the need for parser work and remains inside 020c's already-landed contract.

This fixture contract does **not** pre-authorize either option — it only constrains what the admitted fixture must look like once one of them lands.

---

## 6. Compliance statement

This document:

1. Authors no SQL. Authors no DDL. Authors no migration.
2. Does not modify `apps/mutation-seam/app/schedule/loader.py`.
3. Does not modify `APEX_Schema_V2/XER_Import_Export_Spec.md` or the 020a / 020b authority memos.
4. Adds no bridge route and changes no response shape.
5. Does not modify the PM UI or any other client code.
6. Preserves and extends the "no synthetic client-side baseline fabrication" rule.

---

*Authored under packet `2026-04-18-pm-schema-020f`. Fixture-contract only; no runtime changes.*
