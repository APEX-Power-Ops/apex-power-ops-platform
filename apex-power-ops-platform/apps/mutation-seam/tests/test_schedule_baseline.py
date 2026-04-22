"""
Tests for the packet 020c persisted schedule-baseline lane.

These tests run in the sandbox and therefore cannot reach the host Postgres.
They exercise:

* `_validate_baseline_entry` — the pure validation function that enforces
  baseline_source whitelist, required-field presence, and source-specific
  invariants (p6_import requires p6_baseline_proj_id;
  internal_capture requires captured_by_actor_id).
* `upsert_baselines` against a fake `cur` stand-in that records SQL calls
  without touching a real database, so the non-overload rule, the event
  ledger write, and the preserve-existing branch can be asserted.
* The fixture's baseline section round-trips through the validator
  without error.
* The loader's `run_load(dry_run=True)` surfaces baseline validation
  errors before any DB write, because a broken baseline should fail
  early, not silently.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.schedule.loader import (
    _ALLOWED_BASELINE_SOURCES,
    _validate_baseline_entry,
    load_xer_source,
    upsert_baselines,
    run_load,
)


FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "app" / "schedule" / "fixtures" / "stack_data_center.json"
)


# ---------------------------------------------------------------------------
# Pure-logic tests — _validate_baseline_entry
# ---------------------------------------------------------------------------

def _base_entry(**overrides):
    entry = {
        "baseline_source": "p6_import",
        "baseline_name": "Original",
        "schedule_project_id": "sched-proj-001",
        "p6_baseline_proj_id": "SDCX-2026-BL1",
        "tasks": [{
            "schedule_task_id": "sched-task-001",
            "baseline_start":  "2026-04-20T07:00:00Z",
            "baseline_finish": "2026-04-24T17:00:00Z",
        }],
    }
    entry.update(overrides)
    return entry


def test_allowed_sources_constant():
    assert set(_ALLOWED_BASELINE_SOURCES) == {
        "p6_import", "internal_capture", "rebaseline",
    }


def test_valid_p6_import_entry_passes():
    _validate_baseline_entry(_base_entry())


def test_unknown_source_rejected():
    with pytest.raises(ValueError, match="baseline_source"):
        _validate_baseline_entry(_base_entry(baseline_source="auto_freeze"))


def test_missing_required_field_rejected():
    entry = _base_entry()
    entry.pop("baseline_name")
    with pytest.raises(ValueError, match="missing required field"):
        _validate_baseline_entry(entry)


def test_p6_import_requires_baseline_proj_id():
    entry = _base_entry()
    entry.pop("p6_baseline_proj_id")
    with pytest.raises(ValueError, match="p6_baseline_proj_id"):
        _validate_baseline_entry(entry)


def test_internal_capture_requires_actor():
    with pytest.raises(ValueError, match="captured_by_actor_id"):
        _validate_baseline_entry(_base_entry(
            baseline_source="internal_capture",
            p6_baseline_proj_id=None,
        ))


def test_internal_capture_accepts_actor():
    _validate_baseline_entry(_base_entry(
        baseline_source="internal_capture",
        p6_baseline_proj_id=None,
        captured_by_actor_id="pm-001",
    ))


def test_rebaseline_does_not_require_actor():
    # rebaseline may be automatic (scheduled job) or actor-driven; not strictly required.
    _validate_baseline_entry(_base_entry(
        baseline_source="rebaseline",
    ))


def test_baseline_task_missing_date_rejected():
    entry = _base_entry()
    entry["tasks"][0].pop("baseline_finish")
    with pytest.raises(ValueError, match="baseline_finish"):
        _validate_baseline_entry(entry)


def test_fixture_baselines_pass_validation():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    for entry in payload.get("baselines", []):
        _validate_baseline_entry(entry)  # should not raise


# ---------------------------------------------------------------------------
# upsert_baselines — uses a scripted cursor stand-in so the behavior can be
# exercised without a real database.
# ---------------------------------------------------------------------------

class FakeCursor:
    """Minimal cur stand-in. Records .execute calls and can pre-load SELECT
    responses that are returned in order by .fetchone()."""

    def __init__(self, select_responses=None):
        self.calls = []
        self._responses = list(select_responses or [])
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.calls.append((sql.strip().split()[0].upper(), sql, params))

    def fetchone(self):
        if not self._responses:
            return None
        return self._responses.pop(0)


def test_empty_baselines_is_noop():
    cur = FakeCursor()
    results = upsert_baselines(cur, [])
    assert results == []
    assert cur.calls == []


def test_upsert_baselines_happy_path_writes_event_and_updates():
    # 4 tasks, all previously un-baselined (SELECT returns (None,))
    cur = FakeCursor(select_responses=[(None,), (None,), (None,), (None,)])
    entry = _base_entry()
    entry["tasks"] = [
        {"schedule_task_id": f"sched-task-00{i+1}",
         "baseline_start": f"2026-04-{20+i}T07:00:00Z",
         "baseline_finish": f"2026-04-{24+i}T17:00:00Z"}
        for i in range(4)
    ]
    results = upsert_baselines(cur, [entry])
    assert len(results) == 1
    r = results[0]
    assert r["baseline_source"] == "p6_import"
    assert r["stats"]["matched_tasks"] == 4
    assert r["stats"]["preserved_existing_tasks"] == 0
    assert r["stats"]["unmatched_baseline_tasks"] == []
    # Verify SQL shape: INSERT into baseline_events (1), then for each task:
    # SELECT (1) + UPDATE (1), and finally one UPDATE to the event ledger.
    # So 1 + (4*2) + 1 = 10 SQL calls.
    assert len(cur.calls) == 10
    # First call must write the event ledger row with status in_progress.
    first_kind, first_sql, _first_params = cur.calls[0]
    assert first_kind == "INSERT"
    assert "schedule.baseline_events" in first_sql
    assert "in_progress" in first_sql
    # Last call is the status=success update.
    last_kind, last_sql, _last_params = cur.calls[-1]
    assert last_kind == "UPDATE"
    assert "baseline_events" in last_sql
    assert "status = 'success'" in last_sql


def test_upsert_baselines_preserves_existing_non_rebaseline():
    # 2 tasks: first already has a baseline, second does not.
    existing_ts = "2026-01-01T00:00:00Z"
    cur = FakeCursor(select_responses=[(existing_ts,), (None,)])
    entry = _base_entry()
    entry["tasks"] = [
        {"schedule_task_id": "sched-task-001",
         "baseline_start": "2026-04-20T07:00:00Z",
         "baseline_finish": "2026-04-24T17:00:00Z"},
        {"schedule_task_id": "sched-task-002",
         "baseline_start": "2026-04-27T07:00:00Z",
         "baseline_finish": "2026-05-04T17:00:00Z"},
    ]
    results = upsert_baselines(cur, [entry])
    r = results[0]
    assert r["stats"]["preserved_existing_tasks"] == 1
    assert r["stats"]["matched_tasks"] == 1
    assert r["stats"]["unmatched_baseline_tasks"] == []
    # The SQL trace must include at most one UPDATE to schedule.tasks.
    task_updates = [c for c in cur.calls
                    if c[0] == "UPDATE" and "schedule.tasks" in c[1]]
    assert len(task_updates) == 1


def test_upsert_baselines_rebaseline_overwrites_existing():
    existing_ts = "2026-01-01T00:00:00Z"
    cur = FakeCursor(select_responses=[(existing_ts,)])
    entry = _base_entry(baseline_source="rebaseline")
    entry["tasks"] = [{
        "schedule_task_id": "sched-task-001",
        "baseline_start":  "2026-04-20T07:00:00Z",
        "baseline_finish": "2026-04-24T17:00:00Z",
    }]
    results = upsert_baselines(cur, [entry])
    r = results[0]
    assert r["stats"]["matched_tasks"] == 1
    assert r["stats"]["preserved_existing_tasks"] == 0


def test_upsert_baselines_unmatched_task_surfaces_in_stats():
    # SELECT returns None (task not found)
    cur = FakeCursor(select_responses=[None])
    entry = _base_entry()
    entry["tasks"] = [{
        "schedule_task_id": "sched-task-missing",
        "baseline_start":  "2026-04-20T07:00:00Z",
        "baseline_finish": "2026-04-24T17:00:00Z",
    }]
    results = upsert_baselines(cur, [entry])
    r = results[0]
    assert r["stats"]["matched_tasks"] == 0
    assert r["stats"]["preserved_existing_tasks"] == 0
    assert r["stats"]["unmatched_baseline_tasks"] == ["sched-task-missing"]


# ---------------------------------------------------------------------------
# run_load dry-run propagation
# ---------------------------------------------------------------------------

def test_dry_run_includes_baseline_events_count():
    result = run_load(json_override=FIXTURE_PATH, dry_run=True)
    assert result["dry_run"] is True
    assert result["stats"]["baseline_events"] == 1
    # Sanity: the other stats still pass through unchanged.
    assert result["stats"]["projects"] == 1
    assert result["stats"]["tasks"] == 4
    assert result["stats"]["relationships"] == 3


def test_dry_run_surfaces_bad_baseline_entry(tmp_path):
    """If the fixture's baselines fail validation, the dry-run should
    raise rather than silently report success.
    """
    bad_payload = {
        "source": {"type": "json-fixture", "source_file": "bad.json"},
        "projects": [],
        "wbs_nodes": [],
        "tasks": [],
        "relationships": [],
        "baselines": [{
            "schedule_project_id": "sched-proj-001",
            "baseline_source": "bogus_source",   # not in whitelist
            "baseline_name": "x",
            "tasks": [],
        }],
    }
    bad_path = tmp_path / "bad_fixture.json"
    bad_path.write_text(json.dumps(bad_payload), encoding="utf-8")
    with pytest.raises(ValueError, match="baseline_source"):
        run_load(json_override=bad_path, dry_run=True)


# ===========================================================================
# Packet 020e.2 — re-authored packet-020d parser-side tests
#
# The original three packet-020d tests below were lost with the pre-020e.1
# `loader.py` truncation event surfaced by packet 020f. Packet 020e.2
# re-authors them against the governed 020g-a parser-reconciliation
# substrate (the Apex-owned `ApexXerSource` adapter + narrow
# `parse_baseline_rows_raw` shim). The original 020d claim of "20 passed"
# on this file is therefore restored truthfully, not by fabrication.
#
# Notes on substrate alignment:
#   * Readers are stood up under the REAL PyP6Xer 1.016.00 attribute names
#     (`activities`, `wbss`, `relations`) via `_FakeXerParserReader` —
#     never under the pre-020e.1 `tasks` / `projwbs` / `taskpreds`
#     assumptions.
#   * Baseline-linkage rows are driven through the raw-section shim by
#     writing a `%T PROJBASELINE` or `%T BASELINEPROJECT` section into a
#     synthetic XER file on disk; no `projbaselines` attribute is
#     fabricated on the Reader stand-in, which is truthful to
#     PyP6Xer 1.016.00 (which exposes no such collection).
# ===========================================================================

from types import SimpleNamespace
from typing import List


def _p20e2_project(proj_id: str, name: str, *, sum_base_proj_id=None) -> SimpleNamespace:
    return SimpleNamespace(
        proj_id=proj_id, proj_short_name=name, name=name,
        plan_start_date=None, plan_end_date=None,
        act_start_date=None, act_end_date=None,
        last_recalc_date=None, scd_end_date=None,
        sum_base_proj_id=sum_base_proj_id,
    )


def _p20e2_task(task_id: str, proj_id: str, task_code: str, *,
                target_start="2026-04-20 07:00", target_end="2026-04-24 17:00",
                task_name="Sample") -> SimpleNamespace:
    return SimpleNamespace(
        task_id=task_id, proj_id=proj_id, task_code=task_code,
        task_name=task_name,
        target_start_date=target_start, target_end_date=target_end,
        act_start_date=None, act_end_date=None,
        wbs_id=None, status_code="TK_NotStart",
        target_drtn_hr_cnt=40, total_float_hr_cnt=0, free_float_hr_cnt=0,
        driving_path_flag=False, cstr_type=None, cstr_date=None, task_type=None,
    )


def _p20e2_wbs(wbs_id: str, proj_id: str, wbs_name="WBS") -> SimpleNamespace:
    return SimpleNamespace(
        wbs_id=wbs_id, proj_id=proj_id, wbs_name=wbs_name,
        wbs_short_name=None, seq_num=1, proj_node_flag=None, parent_wbs_id=None,
    )


def _p20e2_rel(task_pred_id: str, proj_id: str, pred: str, succ: str) -> SimpleNamespace:
    return SimpleNamespace(
        task_pred_id=task_pred_id, proj_id=proj_id,
        pred_task_id=pred, task_id=succ, pred_type="FS", lag_hr_cnt=0,
    )


class _P20E2FakeReader:
    """Stand-in for `xerparser.reader.Reader` in these three re-authored
    packet-020d tests. It speaks PyP6Xer 1.016.00's REAL attribute names
    (`activities`, `wbss`, `relations`), matching what the landed
    `ApexXerSource` adapter normalizes from. It deliberately exposes NO
    `projbaselines` / `baselineprojects` collection, because PyP6Xer
    1.016.00 itself does not — baseline-linkage rows must flow through
    the raw-section shim (`parse_baseline_rows_raw`) on the XER file
    path supplied at `load_xer_source` time."""

    def __init__(self, path: str, *, projects=(), activities=(),
                 wbss=(), relations=()):
        self.path = path
        self.projects = list(projects)
        self.activities = list(activities)
        self.wbss = list(wbss)
        self.relations = list(relations)


def _p20e2_install_fake_reader(monkeypatch, *, projects, tasks, wbs_nodes, rels):
    import xerparser

    def _factory(path):
        return _P20E2FakeReader(
            path,
            projects=projects,
            activities=tasks,
            wbss=wbs_nodes,
            relations=rels,
        )

    monkeypatch.setattr(xerparser, "Reader", _factory, raising=False)


def _p20e2_write_xer(
    path: Path,
    *,
    projects: List[tuple],           # list of (proj_id, name, sum_base_proj_id)
    tasks: List[tuple],              # list of (task_id, proj_id, task_code, tstart, tend)
    baseline_links: List[tuple],     # list of (proj_id, base_proj_id, label)
    include_projwbs: bool = True,
    include_taskpred: bool = True,
    baseline_section: str = "PROJBASELINE",
) -> None:
    """Minimal `%T`-headed XER text exercising the exact columns the
    loader + adapter care about. Matches the fixture-contract decode
    semantics (utf-8, tab-delimited, `%T`/`%F`/`%R` framing)."""
    lines: List[str] = []
    lines.append("ERMHDR\t16.2\t2026-04-18")

    lines.append("%T\tPROJECT")
    lines.append("\t".join(["%F", "proj_id", "proj_short_name",
                            "sum_base_proj_id"]))
    for pid, name, sum_base in projects:
        lines.append("\t".join(["%R", pid, name, sum_base or ""]))

    if include_projwbs:
        lines.append("%T\tPROJWBS")
        lines.append("\t".join(["%F", "wbs_id", "proj_id", "wbs_name",
                                "wbs_short_name", "seq_num"]))
        for pid, name, _ in projects:
            lines.append("\t".join(["%R", f"w-{pid}", pid, f"{name} root",
                                    "root", "1"]))

    lines.append("%T\tTASK")
    lines.append("\t".join(["%F", "task_id", "proj_id", "task_code",
                            "task_name", "target_start_date",
                            "target_end_date", "status_code"]))
    for tid, pid, code, tstart, tend in tasks:
        lines.append("\t".join(["%R", tid, pid, code, f"Task {code}",
                                tstart, tend, "TK_NotStart"]))

    if include_taskpred:
        lines.append("%T\tTASKPRED")
        lines.append("\t".join(["%F", "task_pred_id", "proj_id",
                                "pred_task_id", "task_id",
                                "pred_type", "lag_hr_cnt"]))

    if baseline_links:
        lines.append(f"%T\t{baseline_section}")
        lines.append("\t".join(["%F", "proj_id", "base_proj_id",
                                "base_type_name", "last_update_date"]))
        for pid, bpid, label in baseline_links:
            lines.append("\t".join(["%R", pid, bpid, label,
                                    "2026-01-15 00:00"]))

    lines.append("%E")
    path.write_text("\n".join(lines), encoding="utf-8")


def test_load_xer_source_emits_baselines_and_filters_baseline_projects(tmp_path, monkeypatch):
    """Re-authored packet-020d test 1 — proves two invariants together:

      (a) baseline-project rows (`9998`) are excluded from the live lane
          (projects, tasks, wbs_nodes, relationships) even though they
          are physically present in the Reader collections,
      (b) matched baseline dates flow through to `payload["baselines"]`
          in the `p6_import` entry shape that `upsert_baselines()`
          already consumes.

    Substrate note: the Reader stand-in exposes tasks / wbs / rels under
    PyP6Xer 1.016.00's real names (activities / wbss / relations); the
    baseline-linkage row is supplied via a `%T PROJBASELINE` section in
    the synthetic XER file on disk, so the raw-section shim fires."""
    xer = tmp_path / "filters_and_emits.xer"
    _p20e2_write_xer(
        xer,
        projects=[("1001", "Live",     "9998"),
                  ("9998", "Baseline", None)],
        tasks=[("1", "1001", "A01", "2026-04-20 07:00", "2026-04-24 17:00"),
               ("2", "9998", "A01", "2026-04-18 07:00", "2026-04-22 17:00")],
        baseline_links=[("1001", "9998", "Original Baseline")],
    )
    projects = [_p20e2_project("1001", "Live", sum_base_proj_id="9998"),
                _p20e2_project("9998", "Baseline")]
    tasks = [_p20e2_task("1", "1001", "A01"),
             _p20e2_task("2", "9998", "A01",
                         target_start="2026-04-18 07:00",
                         target_end  ="2026-04-22 17:00")]
    wbs_nodes = [_p20e2_wbs("w-1001", "1001", "Live root"),
                 _p20e2_wbs("w-9998", "9998", "Baseline root")]
    rels = [_p20e2_rel("r1", "1001", "1", "1")]

    _p20e2_install_fake_reader(monkeypatch,
                               projects=projects, tasks=tasks,
                               wbs_nodes=wbs_nodes, rels=rels)

    payload, _src_name = load_xer_source(xer)

    # (a) Live lane EXCLUDES the baseline project (9998) everywhere.
    live_proj_ids = [p["p6_project_id"] for p in payload["projects"]]
    assert live_proj_ids == ["1001"], (
        f"baseline-project row 9998 must not leak into live projects; "
        f"got {live_proj_ids!r}"
    )
    live_task_p6 = [t["p6_task_id"] for t in payload["tasks"]]
    assert live_task_p6 == ["1"], (
        f"tasks owned by baseline project 9998 must be filtered; got {live_task_p6!r}"
    )
    live_wbs_projects = [w["schedule_project_id"] for w in payload["wbs_nodes"]]
    assert live_wbs_projects == ["sched-proj-1001"], (
        f"WBS rows for baseline project 9998 must be filtered; got {live_wbs_projects!r}"
    )
    assert len(payload["relationships"]) == 1

    # (b) Matched baseline dates are emitted in p6_import entry shape.
    baselines = payload["baselines"]
    assert len(baselines) == 1
    entry = baselines[0]
    assert entry["baseline_source"]     == "p6_import"
    assert entry["baseline_name"]       == "Original Baseline"
    assert entry["schedule_project_id"] == "sched-proj-1001"
    assert entry["p6_baseline_proj_id"] == "9998"
    assert entry["source_file"]         == xer.name
    assert len(entry["tasks"]) == 1
    matched = entry["tasks"][0]
    assert matched["schedule_task_id"] == "sched-task-1"
    assert matched["baseline_start"]   == "2026-04-18 07:00"
    assert matched["baseline_finish"]  == "2026-04-22 17:00"


def test_load_xer_source_uses_sum_base_proj_id_to_pick_canonical_baseline(tmp_path, monkeypatch):
    """Re-authored packet-020d test 2 — proves that when a live project
    has MULTIPLE baseline-linkage rows, the loader's
    `_build_xer_baseline_entries` uses `PROJECT.sum_base_proj_id` to
    select the canonical baseline, rather than arbitrary first-match.

    Substrate note: two `%T PROJBASELINE` rows for live project `1001`
    are written into the XER file — one linking to baseline project
    `9998`, another linking to baseline project `9997`. The live
    `PROJECT` row's `sum_base_proj_id` is `9998`. The emitted entry
    MUST point at `9998`, not `9997`."""
    xer = tmp_path / "multi_baseline.xer"
    _p20e2_write_xer(
        xer,
        projects=[("1001", "Live",       "9998"),
                  ("9998", "Baseline A", None),
                  ("9997", "Baseline B", None)],
        tasks=[("1",  "1001", "A01", "2026-04-20 07:00", "2026-04-24 17:00"),
               ("21", "9998", "A01", "2026-04-18 07:00", "2026-04-22 17:00"),
               ("31", "9997", "A01", "2025-12-10 07:00", "2025-12-14 17:00")],
        baseline_links=[
            ("1001", "9998", "Canonical Baseline"),
            ("1001", "9997", "Stale Baseline"),
        ],
    )
    projects = [_p20e2_project("1001", "Live",       sum_base_proj_id="9998"),
                _p20e2_project("9998", "Baseline A"),
                _p20e2_project("9997", "Baseline B")]
    tasks = [_p20e2_task("1",  "1001", "A01"),
             _p20e2_task("21", "9998", "A01",
                         target_start="2026-04-18 07:00",
                         target_end  ="2026-04-22 17:00"),
             _p20e2_task("31", "9997", "A01",
                         target_start="2025-12-10 07:00",
                         target_end  ="2025-12-14 17:00")]

    _p20e2_install_fake_reader(monkeypatch,
                               projects=projects, tasks=tasks,
                               wbs_nodes=[], rels=[])

    payload, _src = load_xer_source(xer)

    baselines = payload["baselines"]
    assert len(baselines) == 1, (
        f"canonical selection must collapse multiple links to one entry; "
        f"got {len(baselines)}: {baselines!r}"
    )
    entry = baselines[0]
    assert entry["p6_baseline_proj_id"] == "9998", (
        f"sum_base_proj_id=9998 on live project; canonical entry must "
        f"point at 9998, not 9997. Got {entry['p6_baseline_proj_id']!r}"
    )
    assert entry["baseline_name"] == "Canonical Baseline"
    # Dates come from the `9998` baseline task, not the `9997` one.
    assert entry["tasks"][0]["baseline_start"]  == "2026-04-18 07:00"
    assert entry["tasks"][0]["baseline_finish"] == "2026-04-22 17:00"

    # Both baseline projects are still filtered out of the live lane.
    live_proj_ids = [p["p6_project_id"] for p in payload["projects"]]
    assert live_proj_ids == ["1001"], (
        f"both baseline projects (9998, 9997) must be excluded from live "
        f"lane; got {live_proj_ids!r}"
    )


def test_load_xer_source_does_not_fabricate_baselines_without_assoc_rows(tmp_path, monkeypatch):
    """Re-authored packet-020d test 3 — proves the no-fabrication rule
    (020b §5, 020d §2.1 item 5, fixture contract §3.6): a XER carrying
    a baseline-clone PROJECT but NO `PROJBASELINE` / `BASELINEPROJECT`
    associative section MUST produce zero baseline entries.

    This test additionally re-confirms the live-lane filter still holds
    via the `sum_base_proj_id` fallback on `PROJECT` rows: the baseline
    clone is still excluded from `payload["projects"]` / `tasks[]` /
    `wbs_nodes[]` / `relationships[]` because the loader's
    baseline_project_ids set is computed from both baseline-linkage
    rows AND `sum_base_proj_id` hints, so a hint-only file still
    prevents clone pollution."""
    xer = tmp_path / "hint_only_no_assoc.xer"
    _p20e2_write_xer(
        xer,
        projects=[("1001", "Live",     "9998"),
                  ("9998", "Baseline", None)],
        tasks=[("1", "1001", "A01", "2026-04-20 07:00", "2026-04-24 17:00"),
               ("2", "9998", "A01", "2026-04-18 07:00", "2026-04-22 17:00")],
        baseline_links=[],  # deliberately NO %T PROJBASELINE section
    )
    projects = [_p20e2_project("1001", "Live", sum_base_proj_id="9998"),
                _p20e2_project("9998", "Baseline")]
    tasks = [_p20e2_task("1", "1001", "A01"),
             _p20e2_task("2", "9998", "A01",
                         target_start="2026-04-18 07:00",
                         target_end  ="2026-04-22 17:00")]
    wbs_nodes = [_p20e2_wbs("w-1001", "1001", "Live root"),
                 _p20e2_wbs("w-9998", "9998", "Baseline root")]

    _p20e2_install_fake_reader(monkeypatch,
                               projects=projects, tasks=tasks,
                               wbs_nodes=wbs_nodes, rels=[])

    payload, _src = load_xer_source(xer)

    # Primary 020d invariant: NO baseline entries fabricated.
    assert payload["baselines"] == [], (
        f"no PROJBASELINE / BASELINEPROJECT rows → payload['baselines'] "
        f"must be []; got {payload['baselines']!r}"
    )

    # Adjacent 020d invariant: baseline clone still filtered from live lane
    # via `sum_base_proj_id` fallback (not via the missing associative row).
    live_proj_ids = [p["p6_project_id"] for p in payload["projects"]]
    assert live_proj_ids == ["1001"], (
        f"baseline clone (9998) must still be filtered via sum_base_proj_id "
        f"even when no linkage row is present; got {live_proj_ids!r}"
    )
    live_task_p6 = [t["p6_task_id"] for t in payload["tasks"]]
    assert live_task_p6 == ["1"], (
        f"baseline-project tasks must be filtered even when no linkage row "
        f"is present; got {live_task_p6!r}"
    )
    live_wbs_projects = [w["schedule_project_id"] for w in payload["wbs_nodes"]]
    assert live_wbs_projects == ["sched-proj-1001"]