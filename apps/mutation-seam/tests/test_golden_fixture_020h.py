"""
Packet 020h — golden-fixture admission test.

This test is the focused, fixture-specific contract test that the
packet-020f BASELINE_XER_FIXTURE_CONTRACT.md §4 item 3 demands for
admitting a concrete sanitized `.xer` file under
`apps/mutation-seam/app/schedule/fixtures/`.

Scope
-----
It exercises the loader's landed 020g-a parser-reconciliation substrate
(`ApexXerSource` + `parse_baseline_rows_raw`) against the on-disk
fixture `stack_data_center_baseline_sanitized.xer` and asserts:

    1.  live-lane counts (projects / wbs / tasks / relationships) match
        the fixture's declared live lane,
    2.  the emitted `baselines` entry carries the declared
        `p6_baseline_proj_id`, `baseline_name`, and matched
        `schedule_task_id` values,
    3.  at least one declared negative case is exercised:
          - Case 1 (A90 baseline-only) — absent from live-task lane,
          - Case 2 (A99 live-only) — present in live-task lane but
            absent from the baseline entry's matched tasks,
    4.  `_validate_baseline_entry()` passes against the emitted entry
        (contract §4 item 4).

Substrate note
--------------
PyP6Xer 1.016.00 crashes when asked to parse the fixture's XER directly
because its Reader classes require many columns this minimal fixture
deliberately omits. That is by design: the fixture is shaped against the
P6 XER semantics in BASELINE_XER_FIXTURE_CONTRACT §3, not against
PyP6Xer's unrelated internal column requirements.

The test therefore drives the loader through the SAME landed 020g-a
substrate path the packet-020e.2 tests use: a Reader stand-in that
speaks PyP6Xer 1.016.00's real attribute names (`activities`, `wbss`,
`relations`, `projects`) and carries SimpleNamespace rows whose field
values exactly mirror the on-disk fixture's `%R` records. Meanwhile
the raw-section shim (`parse_baseline_rows_raw`) operates on the real
fixture file on disk — so this test continues to PROVE the fixture's
declared `PROJBASELINE` section is discoverable and deterministic.

Scope guarantees
----------------
* No SQL. No DB connection. No bridge route. No PM UI. No
  schedule-write broadening.
* No side-car companion-JSON. The abandoned 020g-b companion-JSON
  substrate is not referenced.
* Read-only against the admitted fixture. The fixture file is never
  mutated by the test.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import List

import pytest

from app.schedule.loader import (
    _validate_baseline_entry,
    load_xer_source,
)


FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "app" / "schedule" / "fixtures"
    / "stack_data_center_baseline_sanitized.xer"
)

FIXTURE_README_PATH = (
    Path(__file__).resolve().parent.parent
    / "app" / "schedule" / "fixtures"
    / "stack_data_center_baseline_sanitized.README.md"
)


# ---------------------------------------------------------------------------
# Declared-truth constants — these mirror the fixture README §2–§5 exactly.
# If the fixture is re-authored, both sides MUST be updated together.
# ---------------------------------------------------------------------------

LIVE_PROJ_ID = "1001"
LIVE_PROJ_NAME = "StackDC"

BASELINE_PROJ_ID = "9998"
BASELINE_PROJ_NAME = "StackDC-BL-R01"

BASELINE_LABEL = "Stack DC — Original Baseline R01"

LIVE_TASK_CODES = ("A10", "A20", "A30", "A99")       # includes negative case 2
BASELINE_TASK_CODES = ("A10", "A20", "A30", "A90")   # includes negative case 1
MATCHED_TASK_CODES = ("A10", "A20", "A30")

# Dates from the fixture file (verified by reading the `.xer` rows).
LIVE_TASK_DATES = {
    "A10": ("2026-05-04 07:00", "2026-05-05 17:00"),
    "A20": ("2026-05-06 07:00", "2026-05-08 17:00"),
    "A30": ("2026-05-11 07:00", "2026-05-15 17:00"),
    "A99": ("2026-05-18 07:00", "2026-05-22 17:00"),
}
BASELINE_TASK_DATES = {
    "A10": ("2026-04-27 07:00", "2026-04-28 17:00"),
    "A20": ("2026-04-29 07:00", "2026-05-01 17:00"),
    "A30": ("2026-05-04 07:00", "2026-05-08 17:00"),
    "A90": ("2026-05-11 07:00", "2026-05-13 17:00"),
}


# ---------------------------------------------------------------------------
# Reader stand-in — speaks PyP6Xer 1.016.00's real attribute names.
# ---------------------------------------------------------------------------

class _FixtureReader:
    """Mirrors the fixture's `%R` rows under the real PyP6Xer
    1.016.00 collection names. The `ApexXerSource` adapter's
    `_ATTRIBUTE_ALIASES` table will normalize these to the loader's
    logical names (`projects`, `tasks`, `projwbs`, `taskpreds`)."""

    def __init__(self, path: str, *, projects, activities, wbss, relations):
        self.path = path
        self.projects = list(projects)
        self.activities = list(activities)
        self.wbss = list(wbss)
        self.relations = list(relations)


def _project_row(proj_id, name, *, sum_base_proj_id,
                 plan_start, plan_end, last_recalc, scd_end):
    return SimpleNamespace(
        proj_id=proj_id,
        proj_short_name=name,
        name=name,
        sum_base_proj_id=sum_base_proj_id,
        plan_start_date=plan_start,
        plan_end_date=plan_end,
        act_start_date=None,
        act_end_date=None,
        last_recalc_date=last_recalc,
        scd_end_date=scd_end,
    )


def _task_row(task_id, proj_id, wbs_id, task_code, task_name, status,
              dur_hr, start, end):
    return SimpleNamespace(
        task_id=task_id,
        proj_id=proj_id,
        wbs_id=wbs_id,
        task_code=task_code,
        task_name=task_name,
        status_code=status,
        task_type="TT_Task",
        target_drtn_hr_cnt=dur_hr,
        target_start_date=start,
        target_end_date=end,
        act_start_date=None,
        act_end_date=None,
        total_float_hr_cnt=0,
        free_float_hr_cnt=0,
        driving_path_flag=False,
        cstr_type=None,
        cstr_date=None,
    )


def _wbs_row(wbs_id, proj_id, wbs_name, short_name, seq, node_flag, parent):
    return SimpleNamespace(
        wbs_id=wbs_id,
        proj_id=proj_id,
        wbs_name=wbs_name,
        wbs_short_name=short_name,
        seq_num=seq,
        proj_node_flag=node_flag,
        parent_wbs_id=parent,
    )


def _rel_row(task_pred_id, proj_id, pred_task_id, succ_task_id,
             pred_type, lag):
    return SimpleNamespace(
        task_pred_id=task_pred_id,
        proj_id=proj_id,
        pred_task_id=pred_task_id,
        task_id=succ_task_id,
        pred_type=pred_type,
        lag_hr_cnt=lag,
    )


def _build_fixture_reader_factory():
    """Build a Reader factory whose in-memory contents mirror the
    on-disk fixture's `%R` rows 1-for-1.

    The baseline-linkage lane is intentionally NOT loaded into the
    Reader — PyP6Xer 1.016.00 does not surface it, so the adapter's
    raw-section shim must reach through to the physical fixture file
    on disk. That is the key 020g-a substrate invariant this test
    exercises."""
    projects = [
        _project_row(
            LIVE_PROJ_ID, LIVE_PROJ_NAME,
            sum_base_proj_id=BASELINE_PROJ_ID,
            plan_start="2026-05-04 07:00",
            plan_end="2026-06-01 17:00",
            last_recalc="2026-04-18 00:00",
            scd_end="2026-06-01 17:00",
        ),
        _project_row(
            BASELINE_PROJ_ID, BASELINE_PROJ_NAME,
            sum_base_proj_id=None,
            plan_start="2026-04-27 07:00",
            plan_end="2026-05-15 17:00",
            last_recalc="2026-02-01 00:00",
            scd_end="2026-05-15 17:00",
        ),
    ]

    wbss = [
        _wbs_row("5001", LIVE_PROJ_ID, "StackDC Root", "ROOT",
                 seq=1, node_flag="Y", parent=None),
    ]

    # Live-project tasks
    activities = [
        _task_row("7001", LIVE_PROJ_ID, "5001", "A10",
                  "Mobilize", "TK_NotStart", 16,
                  *LIVE_TASK_DATES["A10"]),
        _task_row("7002", LIVE_PROJ_ID, "5001", "A20",
                  "Demo existing switchgear", "TK_NotStart", 24,
                  *LIVE_TASK_DATES["A20"]),
        _task_row("7003", LIVE_PROJ_ID, "5001", "A30",
                  "Install new busway", "TK_NotStart", 40,
                  *LIVE_TASK_DATES["A30"]),
        _task_row("7004", LIVE_PROJ_ID, "5001", "A99",
                  "Commissioning tests", "TK_NotStart", 40,
                  *LIVE_TASK_DATES["A99"]),
        # Baseline-project tasks (same wbs_id is OK — loader filters by proj_id)
        _task_row("7101", BASELINE_PROJ_ID, "5001", "A10",
                  "Mobilize", "TK_Complete", 16,
                  *BASELINE_TASK_DATES["A10"]),
        _task_row("7102", BASELINE_PROJ_ID, "5001", "A20",
                  "Demo existing switchgear", "TK_Complete", 24,
                  *BASELINE_TASK_DATES["A20"]),
        _task_row("7103", BASELINE_PROJ_ID, "5001", "A30",
                  "Install new busway", "TK_Complete", 40,
                  *BASELINE_TASK_DATES["A30"]),
        _task_row("7190", BASELINE_PROJ_ID, "5001", "A90",
                  "Retired lift plan", "TK_Complete", 24,
                  *BASELINE_TASK_DATES["A90"]),
    ]

    relations = [
        _rel_row("9001", LIVE_PROJ_ID, "7001", "7002", "PR_FS", 0),
    ]

    def _factory(path):
        return _FixtureReader(
            path,
            projects=projects,
            activities=activities,
            wbss=wbss,
            relations=relations,
        )

    return _factory


@pytest.fixture
def install_fixture_reader(monkeypatch):
    """Install the Reader stand-in via `xerparser.Reader` monkeypatch.

    The loader imports `from xerparser import Reader` lazily inside
    `load_xer_source`; setting the attribute on the `xerparser` module
    makes that import resolve to our factory without touching the
    real PyP6Xer 1.016.00 code path."""
    import xerparser

    monkeypatch.setattr(
        xerparser, "Reader", _build_fixture_reader_factory(),
        raising=False,
    )


# ---------------------------------------------------------------------------
# Admission-level tests
# ---------------------------------------------------------------------------

def test_fixture_files_present_on_disk():
    """Sanity: the admitted fixture and its README must exist at the
    canonical paths declared in the README §1. If this fails, the
    fixture admission itself is broken and the rest of the test is
    meaningless."""
    assert FIXTURE_PATH.is_file(), (
        f"admitted fixture missing at {FIXTURE_PATH!s}"
    )
    assert FIXTURE_README_PATH.is_file(), (
        f"fixture README missing at {FIXTURE_README_PATH!s}"
    )


def test_fixture_declares_required_baseline_section():
    """Contract §3.1 — the fixture must carry a PROJBASELINE section.
    This is the entire reason the file is admitted as
    *baseline-bearing* rather than live-only."""
    from app.schedule.xer_adapter import scan_xer_section_names

    sections = scan_xer_section_names(FIXTURE_PATH)
    assert "PROJECT" in sections
    assert "PROJWBS" in sections
    assert "TASK" in sections
    assert "TASKPRED" in sections
    assert "PROJBASELINE" in sections, (
        f"contract §3.1: fixture MUST carry a PROJBASELINE section; "
        f"sections seen = {sections!r}"
    )


def test_fixture_raw_shim_reads_canonical_baseline_linkage():
    """Contract §3.3 — the raw-section shim must discover the single
    canonical PROJBASELINE row, with the P6 `base_proj_id` column
    name and a human-readable `base_type_name` label."""
    from app.schedule.xer_adapter import parse_baseline_rows_raw

    rows = parse_baseline_rows_raw(FIXTURE_PATH)
    assert len(rows) == 1, (
        f"fixture declares exactly one PROJBASELINE row; got {len(rows)}"
    )
    row = rows[0]
    assert row.proj_id == LIVE_PROJ_ID
    assert row.base_proj_id == BASELINE_PROJ_ID
    assert row.base_type_name == BASELINE_LABEL
    assert row.last_update_date == "2026-02-01 00:00"


def test_loader_emits_declared_live_lane_counts(install_fixture_reader):
    """Contract §4 item 3 bullet 1 — live-lane counts match the README:
    exactly one live project, one WBS, four live tasks, one
    relationship. The baseline project and its four tasks MUST NOT
    leak into the live lane."""
    payload, source_file = load_xer_source(FIXTURE_PATH)

    assert source_file == FIXTURE_PATH.name

    live_proj_ids = [p["p6_project_id"] for p in payload["projects"]]
    assert live_proj_ids == [LIVE_PROJ_ID], (
        f"baseline project {BASELINE_PROJ_ID!r} must not leak into "
        f"live projects; got {live_proj_ids!r}"
    )
    assert payload["projects"][0]["name"] == LIVE_PROJ_NAME

    live_wbs_projects = [w["schedule_project_id"] for w in payload["wbs_nodes"]]
    assert live_wbs_projects == [f"sched-proj-{LIVE_PROJ_ID}"], (
        f"WBS rows for baseline project must be filtered; got "
        f"{live_wbs_projects!r}"
    )
    assert len(payload["wbs_nodes"]) == 1

    live_task_codes = sorted(t["task_code"] for t in payload["tasks"])
    assert tuple(live_task_codes) == LIVE_TASK_CODES, (
        f"live task_code set must be {LIVE_TASK_CODES!r}; got "
        f"{live_task_codes!r}"
    )
    assert len(payload["tasks"]) == 4

    assert len(payload["relationships"]) == 1
    rel = payload["relationships"][0]
    assert rel["schedule_project_id"] == f"sched-proj-{LIVE_PROJ_ID}"
    assert rel["predecessor_task_id"] == "sched-task-7001"
    assert rel["successor_task_id"] == "sched-task-7002"
    assert rel["rel_type"] == "PR_FS"


def test_loader_emits_deterministic_baseline_entry(install_fixture_reader):
    """Contract §4 item 3 bullets 2-3 — deterministic baseline emission:

      * exactly one entry,
      * `p6_baseline_proj_id` matches the declared baseline project,
      * `baseline_name` matches the declared `base_type_name` label,
      * matched `schedule_task_id` set covers {A10, A20, A30} with
        baseline dates that come from the `71xx` TASK rows, not the
        live `70xx` rows (§3.6 non-overload invariant).
    """
    payload, _ = load_xer_source(FIXTURE_PATH)

    baselines = payload["baselines"]
    assert len(baselines) == 1, (
        f"fixture admits exactly one baseline entry; got "
        f"{len(baselines)}: {baselines!r}"
    )
    entry = baselines[0]

    assert entry["baseline_source"] == "p6_import"
    assert entry["schedule_project_id"] == f"sched-proj-{LIVE_PROJ_ID}"
    assert entry["p6_baseline_proj_id"] == BASELINE_PROJ_ID
    assert entry["baseline_name"] == BASELINE_LABEL
    assert entry["source_file"] == FIXTURE_PATH.name

    matched_task_ids = sorted(t["schedule_task_id"] for t in entry["tasks"])
    assert matched_task_ids == [
        "sched-task-7001",   # A10
        "sched-task-7002",   # A20
        "sched-task-7003",   # A30
    ], (
        f"matched schedule_task_id set must cover {MATCHED_TASK_CODES!r}; "
        f"got {matched_task_ids!r}"
    )
    assert len(entry["tasks"]) == 3

    # Dates come from BASELINE rows, not LIVE rows. This is the
    # regression wedge for a future loader change that silently copies
    # live `target_*` into baseline fields (contract §3.6).
    dates_by_task_id = {
        t["schedule_task_id"]: (t["baseline_start"], t["baseline_finish"])
        for t in entry["tasks"]
    }
    assert dates_by_task_id["sched-task-7001"] == BASELINE_TASK_DATES["A10"]
    assert dates_by_task_id["sched-task-7002"] == BASELINE_TASK_DATES["A20"]
    assert dates_by_task_id["sched-task-7003"] == BASELINE_TASK_DATES["A30"]
    # Live-row dates MUST differ — proves non-overload.
    for code in ("A10", "A20", "A30"):
        assert LIVE_TASK_DATES[code] != BASELINE_TASK_DATES[code], (
            f"fixture §3.6 requires baseline dates differ from live "
            f"for matched task {code!r}; README/fixture drift suspected."
        )


def test_emitted_entry_passes_validate_baseline_entry(install_fixture_reader):
    """Contract §4 item 4 — the emitted entry must satisfy the 020c
    persistence lane's validator without raising."""
    payload, _ = load_xer_source(FIXTURE_PATH)

    assert payload["baselines"], "no baselines emitted to validate"
    for entry in payload["baselines"]:
        _validate_baseline_entry(entry)  # must not raise


def test_declared_negative_case_2_live_only_is_exercised(install_fixture_reader):
    """Contract §3.5 + README §4 — Case 2 (A99 live-only):

      * `A99` MUST appear in the live-task lane, and
      * `A99` MUST NOT appear as a matched task in the emitted
        baseline entry.

    Proves the loader does not synthesize a baseline-dated copy for a
    live-only activity."""
    payload, _ = load_xer_source(FIXTURE_PATH)

    live_codes = {t["task_code"] for t in payload["tasks"]}
    assert "A99" in live_codes, (
        "negative case 2 (A99 live-only) must appear in the live-task lane"
    )

    # Walk the matched set and assert A99 is absent. The fixture README
    # claims the matched-set is exactly {A10, A20, A30}; Case 2
    # compliance turns on A99 *not* being there.
    entry = payload["baselines"][0]
    matched_live_tasks = {
        t["schedule_task_id"] for t in entry["tasks"]
    }
    assert "sched-task-7004" not in matched_live_tasks, (
        "negative case 2 (A99 live-only) must NOT be in the baseline "
        "entry's matched tasks; the loader would have fabricated a "
        "baseline-dated copy for it, violating contract §3.6."
    )


def test_declared_negative_case_1_baseline_only_is_exercised(install_fixture_reader):
    """Contract §3.5 + README §4 — Case 1 (A90 baseline-only):

    `A90` MUST NOT appear in the live-task lane — it belongs only to
    the baseline project (7190, proj 9998) and the loader's baseline
    filter MUST keep it from leaking.
    """
    payload, _ = load_xer_source(FIXTURE_PATH)

    live_codes = {t["task_code"] for t in payload["tasks"]}
    assert "A90" not in live_codes, (
        "negative case 1 (A90 baseline-only) must NOT appear in the "
        "live-task lane; the loader's baseline-project filter has "
        "regressed."
    )

    live_task_ids = {t["p6_task_id"] for t in payload["tasks"]}
    assert "7190" not in live_task_ids, (
        "baseline-project task_id 7190 must never surface as a live task"
    )
