"""
Packet 020g-a — Parser-Surface Reconciliation And Baseline Shim

These tests are deterministic and infrastructure-free. They do not
require a live database, do not require a network, and do not depend
on the specific PyP6Xer version installed — they drive the adapter
with both duck-typed Reader stand-ins AND synthetic on-disk XER text,
so the validation holds across future PyP6Xer upgrades.

They cover three proof obligations declared by the packet prompt:

    1. Reader-surface reconciliation is explicit, not implied
       (`_ATTRIBUTE_ALIASES` table drives normalization, and the
       adapter emits a per-surface resolution trace).

    2. The narrow raw-section shim for PROJBASELINE / BASELINEPROJECT
       parses contract-compliant `%T`-headed sections without
       touching any other section the PyP6Xer Reader already owns.

    3. The adapter drives deterministic loader assertions — a
       contract-compliant baseline-bearing synthetic XER produces
       exactly the `baselines` entry shape `upsert_baselines()` already
       consumes, with no synthetic fabrication when linkage is absent.

Running:

    cd apps/mutation-seam
    python -m pytest tests/test_xer_adapter_020g_a.py -v --noconftest
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Iterable, List

import pytest

from app.schedule.xer_adapter import (
    ApexXerSource,
    _ATTRIBUTE_ALIASES,
    _BASELINE_SECTION_NAMES,
    parse_baseline_rows_raw,
    scan_xer_section_names,
)


# ---------------------------------------------------------------------------
# Helpers — build duck-typed Reader stand-ins and synthetic raw XER text
# ---------------------------------------------------------------------------

def _fake_reader(**collections: Iterable) -> SimpleNamespace:
    """Return a SimpleNamespace that quacks like a PyP6Xer Reader. Only
    the attribute names passed as kwargs are exposed."""
    return SimpleNamespace(**{name: list(rows) for name, rows in collections.items()})


def _task(task_id: str, proj_id: str, task_code: str, *,
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


def _project(proj_id: str, name: str, *, sum_base_proj_id=None) -> SimpleNamespace:
    return SimpleNamespace(
        proj_id=proj_id, proj_short_name=name, name=name,
        plan_start_date=None, plan_end_date=None,
        act_start_date=None, act_end_date=None,
        last_recalc_date=None, scd_end_date=None,
        sum_base_proj_id=sum_base_proj_id,
    )


def _wbs(wbs_id: str, proj_id: str, wbs_name="WBS") -> SimpleNamespace:
    return SimpleNamespace(
        wbs_id=wbs_id, proj_id=proj_id, wbs_name=wbs_name,
        wbs_short_name=None, seq_num=1, proj_node_flag=None, parent_wbs_id=None,
    )


def _rel(task_pred_id: str, proj_id: str, pred: str, succ: str) -> SimpleNamespace:
    return SimpleNamespace(
        task_pred_id=task_pred_id, proj_id=proj_id,
        pred_task_id=pred, task_id=succ, pred_type="FS", lag_hr_cnt=0,
    )


def _baseline_link(proj_id: str, base_proj_id: str, label="Original") -> SimpleNamespace:
    return SimpleNamespace(
        proj_id=proj_id, base_proj_id=base_proj_id,
        baseline_proj_id=base_proj_id, base_type_name=label,
        last_update_date=None,
    )


def _write_synthetic_xer(
    path: Path,
    *,
    projects: List[tuple],          # list of (proj_id, name, sum_base_proj_id)
    tasks: List[tuple],             # list of (task_id, proj_id, task_code, tstart, tend)
    baseline_links: List[tuple],    # list of (proj_id, base_proj_id, label)
    include_projwbs: bool = True,
    include_taskpred: bool = True,
    baseline_section: str = "PROJBASELINE",
) -> None:
    """Write a minimal `%T`-headed XER text exercising only the columns
    the loader and adapter care about. Keeps field counts aligned with
    the `%F` header so the csv reader treats them as valid rows."""
    lines: List[str] = []
    lines.append("ERMHDR\t16.2\t2026-04-18")

    # PROJECT
    lines.append("%T\tPROJECT")
    lines.append("\t".join(["%F", "proj_id", "proj_short_name",
                            "sum_base_proj_id"]))
    for pid, name, sum_base in projects:
        lines.append("\t".join(["%R", pid, name, sum_base or ""]))

    # PROJWBS (optional; keeps test matrix small)
    if include_projwbs:
        lines.append("%T\tPROJWBS")
        lines.append("\t".join(["%F", "wbs_id", "proj_id", "wbs_name",
                                "wbs_short_name", "seq_num"]))
        for pid, name, _ in projects:
            lines.append("\t".join(["%R", f"w-{pid}", pid, f"{name} root",
                                    "root", "1"]))

    # TASK
    lines.append("%T\tTASK")
    lines.append("\t".join(["%F", "task_id", "proj_id", "task_code",
                            "task_name", "target_start_date",
                            "target_end_date", "status_code"]))
    for tid, pid, code, tstart, tend in tasks:
        lines.append("\t".join(["%R", tid, pid, code, f"Task {code}",
                                tstart, tend, "TK_NotStart"]))

    # TASKPRED (optional)
    if include_taskpred:
        lines.append("%T\tTASKPRED")
        lines.append("\t".join(["%F", "task_pred_id", "proj_id",
                                "pred_task_id", "task_id",
                                "pred_type", "lag_hr_cnt"]))

    # PROJBASELINE / BASELINEPROJECT
    if baseline_links:
        assert baseline_section in _BASELINE_SECTION_NAMES, (
            "test helper misuse"
        )
        lines.append(f"%T\t{baseline_section}")
        lines.append("\t".join(["%F", "proj_id", "base_proj_id",
                                "base_type_name", "last_update_date"]))
        for pid, bpid, label in baseline_links:
            lines.append("\t".join(["%R", pid, bpid, label,
                                    "2026-01-15 00:00"]))

    lines.append("%E")
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Explicit reconciliation — `_ATTRIBUTE_ALIASES` table is source-of-truth
# ---------------------------------------------------------------------------

def test_alias_table_covers_every_logical_surface_in_packet_scope():
    """Packet 020g-a scope item 1 names activities / wbss / relations
    explicitly. The alias table must carry them, with the REAL names
    listed BEFORE legacy spellings so correct resolution wins when both
    surfaces coexist (e.g. tests using stand-ins that set both)."""
    alias_map = {name: aliases for name, aliases in _ATTRIBUTE_ALIASES}
    assert "activities" in alias_map["tasks"]
    assert "wbss"       in alias_map["projwbs"]
    assert "relations"  in alias_map["taskpreds"]
    # Legacy spellings must also be tolerated (020d compatibility intent).
    assert "tasks"      in alias_map["tasks"]
    assert "projwbs"    in alias_map["projwbs"]
    assert "taskpreds"  in alias_map["taskpreds"]


def test_alias_prefers_real_pyp6xer_name_when_both_exist():
    """If a duck-typed reader exposes BOTH the real and legacy names,
    the real PyP6Xer 1.016.00 attribute must win because it is listed
    first. This guards against a future parser upgrade silently
    preferring the legacy spelling."""
    real_rows = [object()]
    legacy_rows = [object(), object()]
    reader = _fake_reader(activities=real_rows, tasks=legacy_rows,
                          wbss=real_rows, projwbs=legacy_rows,
                          relations=real_rows, taskpreds=legacy_rows)
    src = ApexXerSource.from_reader(reader)
    assert src.tasks     == real_rows
    assert src.projwbs   == real_rows
    assert src.taskpreds == real_rows
    trace = src.resolution_trace()
    assert trace["tasks"]     == "activities"
    assert trace["projwbs"]   == "wbss"
    assert trace["taskpreds"] == "relations"


def test_alias_falls_through_to_legacy_name_when_real_absent():
    """A reader that only exposes the legacy 020d compatibility names
    must still satisfy the logical surface. This preserves the 020d
    attribute-probe intent so older PyP6Xer-like stand-ins keep working."""
    reader = _fake_reader(tasks=[object()], projwbs=[object()],
                          taskpreds=[object()])
    src = ApexXerSource.from_reader(reader)
    assert src.tasks and src.projwbs and src.taskpreds
    trace = src.resolution_trace()
    assert trace["tasks"]     == "tasks"
    assert trace["projwbs"]   == "projwbs"
    assert trace["taskpreds"] == "taskpreds"


def test_empty_reader_resolves_every_surface_to_empty():
    reader = _fake_reader()
    src = ApexXerSource.from_reader(reader)
    assert src.projects == []
    assert src.tasks    == []
    assert src.projwbs  == []
    assert src.taskpreds == []
    assert src.projbaselines == []
    trace = src.resolution_trace()
    for logical_name, _ in _ATTRIBUTE_ALIASES:
        assert trace[logical_name] == "empty", (
            f"empty resolution expected for {logical_name!r}; got {trace[logical_name]!r}"
        )


# ---------------------------------------------------------------------------
# 2. Raw-section baseline shim — narrow, bounded, no fabrication
# ---------------------------------------------------------------------------

def test_parse_baseline_rows_raw_returns_empty_when_file_missing(tmp_path):
    assert parse_baseline_rows_raw(tmp_path / "does_not_exist.xer") == []


def test_parse_baseline_rows_raw_returns_empty_when_no_baseline_section(tmp_path):
    xer = tmp_path / "no_baseline.xer"
    _write_synthetic_xer(
        xer,
        projects=[("1001", "Live", None)],
        tasks=[("1", "1001", "A01", "2026-04-20 07:00", "2026-04-24 17:00")],
        baseline_links=[],   # no PROJBASELINE section
    )
    assert parse_baseline_rows_raw(xer) == []
    # And the section probe confirms the file really has no baseline section.
    section_names = scan_xer_section_names(xer)
    assert "PROJBASELINE"    not in section_names
    assert "BASELINEPROJECT" not in section_names


def test_parse_baseline_rows_raw_projbaseline_section(tmp_path):
    xer = tmp_path / "with_baseline.xer"
    _write_synthetic_xer(
        xer,
        projects=[("1001", "Live", "9998"),
                  ("9998", "Baseline", None)],
        tasks=[("1", "1001", "A01", "2026-04-20 07:00", "2026-04-24 17:00"),
               ("2", "9998", "A01", "2026-04-18 07:00", "2026-04-22 17:00")],
        baseline_links=[("1001", "9998", "Original Baseline")],
    )
    rows = parse_baseline_rows_raw(xer)
    assert len(rows) == 1
    row = rows[0]
    assert row.proj_id == "1001"
    assert row.base_proj_id == "9998"
    assert row.baseline_proj_id == "9998"   # synonym the loader probes
    assert row.base_type_name == "Original Baseline"


def test_parse_baseline_rows_raw_baselineproject_section(tmp_path):
    """Older exports emit `BASELINEPROJECT` rather than `PROJBASELINE`.
    The shim must recognize both per the fixture contract §2."""
    xer = tmp_path / "old_style.xer"
    _write_synthetic_xer(
        xer,
        projects=[("1001", "Live", "9998"),
                  ("9998", "Baseline", None)],
        tasks=[("1", "1001", "A01", "2026-04-20 07:00", "2026-04-24 17:00"),
               ("2", "9998", "A01", "2026-04-18 07:00", "2026-04-22 17:00")],
        baseline_links=[("1001", "9998", "Archived Baseline")],
        baseline_section="BASELINEPROJECT",
    )
    rows = parse_baseline_rows_raw(xer)
    assert len(rows) == 1
    assert rows[0].proj_id == "1001"
    assert rows[0].base_proj_id == "9998"


def test_shim_does_not_fabricate_when_section_absent(tmp_path):
    """No `PROJBASELINE` / `BASELINEPROJECT` → no baseline rows, even if
    the file has a `sum_base_proj_id` hint on a live PROJECT. 020b §5
    / 020d §2.1 item 3 forbid fabrication."""
    xer = tmp_path / "hint_only.xer"
    _write_synthetic_xer(
        xer,
        projects=[("1001", "Live", "9998"),
                  ("9998", "Clone", None)],
        tasks=[("1", "1001", "A01", "2026-04-20 07:00", "2026-04-24 17:00"),
               ("2", "9998", "A01", "2026-04-18 07:00", "2026-04-22 17:00")],
        baseline_links=[],   # no explicit PROJBASELINE section
    )
    assert parse_baseline_rows_raw(xer) == []


# ---------------------------------------------------------------------------
# 3. End-to-end: adapter drives deterministic loader assertions
# ---------------------------------------------------------------------------

class _FakeXerParserReader:
    """Stand-in for `xerparser.reader.Reader`. Constructed from a file
    path, it reads nothing from disk — the tests preload its collections
    directly. This lets us exercise `load_xer_source()` end-to-end without
    requiring PyP6Xer to successfully parse synthetic XER text."""

    def __init__(self, path: str, *, projects=(), activities=(), wbss=(),
                 relations=()):
        self.path = path
        self.projects = list(projects)
        self.activities = list(activities)   # real PyP6Xer 1.016.00 name
        self.wbss = list(wbss)               # real PyP6Xer 1.016.00 name
        self.relations = list(relations)     # real PyP6Xer 1.016.00 name


def _install_fake_reader(monkeypatch, *, projects, tasks, wbs_nodes, rels):
    """Patch `xerparser.Reader` (the name `load_xer_source` imports) so
    it ignores file content and returns our seeded collections under
    the REAL PyP6Xer 1.016.00 attribute names."""
    import xerparser

    def _factory(path):
        return _FakeXerParserReader(
            path,
            projects=projects,
            activities=tasks,
            wbss=wbs_nodes,
            relations=rels,
        )

    monkeypatch.setattr(xerparser, "Reader", _factory, raising=False)


def test_load_xer_source_reads_through_adapter_using_real_names(tmp_path, monkeypatch):
    """load_xer_source() must import live projects + tasks + wbs + relationships
    when the underlying Reader exposes them under PyP6Xer 1.016.00's real
    attribute names (activities / wbss / relations), not the legacy ones."""
    xer = tmp_path / "synth.xer"
    _write_synthetic_xer(
        xer,
        projects=[("1001", "Live", "9998"),
                  ("9998", "Baseline", None)],
        tasks=[("1", "1001", "A01", "2026-04-20 07:00", "2026-04-24 17:00"),
               ("2", "9998", "A01", "2026-04-18 07:00", "2026-04-22 17:00")],
        baseline_links=[("1001", "9998", "Original Baseline")],
    )

    projects   = [_project("1001", "Live", sum_base_proj_id="9998"),
                  _project("9998", "Baseline")]
    tasks      = [_task("1", "1001", "A01"),
                  _task("2", "9998", "A01",
                        target_start="2026-04-18 07:00",
                        target_end  ="2026-04-22 17:00")]
    wbs_nodes  = [_wbs("w-1001", "1001", "Live root")]
    rels       = [_rel("r1", "1001", "1", "2")]

    _install_fake_reader(monkeypatch,
                         projects=projects, tasks=tasks,
                         wbs_nodes=wbs_nodes, rels=rels)

    from app.schedule.loader import load_xer_source
    payload, src_name = load_xer_source(xer)

    # Live-project filtering must still work: baseline project (9998) MUST NOT
    # appear in the live lane outputs.
    live_proj_ids = [p["p6_project_id"] for p in payload["projects"]]
    assert live_proj_ids == ["1001"]
    live_task_p6 = [t["p6_task_id"] for t in payload["tasks"]]
    assert live_task_p6 == ["1"]
    # WBS + relationships survived the live-project filter.
    assert len(payload["wbs_nodes"]) == 1
    assert len(payload["relationships"]) == 1


def test_load_xer_source_emits_baseline_entry_via_raw_shim(tmp_path, monkeypatch):
    """This is the decisive 020g-a proof: a contract-compliant baseline-
    bearing input — where the Reader has NO baseline collection but the
    XER file carries a PROJBASELINE section — MUST emit exactly one
    baselines entry through the raw-section shim."""
    xer = tmp_path / "baseline_bearing.xer"
    _write_synthetic_xer(
        xer,
        projects=[("1001", "Live",     "9998"),
                  ("9998", "Baseline", None)],
        tasks=[("1", "1001", "A01", "2026-04-20 07:00", "2026-04-24 17:00"),
               ("2", "9998", "A01", "2026-04-18 07:00", "2026-04-22 17:00")],
        baseline_links=[("1001", "9998", "Original Baseline")],
    )

    projects  = [_project("1001", "Live", sum_base_proj_id="9998"),
                 _project("9998", "Baseline")]
    tasks     = [_task("1", "1001", "A01"),
                 _task("2", "9998", "A01",
                       target_start="2026-04-18 07:00",
                       target_end  ="2026-04-22 17:00")]

    _install_fake_reader(monkeypatch,
                         projects=projects, tasks=tasks,
                         wbs_nodes=[], rels=[])

    from app.schedule.loader import load_xer_source
    payload, _ = load_xer_source(xer)

    baselines = payload["baselines"]
    assert len(baselines) == 1, (
        f"expected exactly one baseline entry via raw-section shim; "
        f"got {len(baselines)}: {baselines!r}"
    )
    entry = baselines[0]
    assert entry["baseline_source"]     == "p6_import"
    assert entry["baseline_name"]       == "Original Baseline"
    assert entry["schedule_project_id"] == "sched-proj-1001"
    assert entry["p6_baseline_proj_id"] == "9998"
    assert entry["source_file"]         == xer.name
    # Exactly one matched task (A01 lives on both projects).
    assert len(entry["tasks"]) == 1
    matched = entry["tasks"][0]
    assert matched["schedule_task_id"] == "sched-task-1"
    assert matched["baseline_start"]   == "2026-04-18 07:00"
    assert matched["baseline_finish"]  == "2026-04-22 17:00"


def test_load_xer_source_emits_no_baselines_when_linkage_absent(tmp_path, monkeypatch):
    """Fabrication rule (020b §5, fixture contract §3.6): without a
    PROJBASELINE / BASELINEPROJECT row, the loader MUST emit zero
    baseline entries even if a baseline clone PROJECT exists."""
    xer = tmp_path / "no_linkage.xer"
    _write_synthetic_xer(
        xer,
        projects=[("1001", "Live",     "9998"),
                  ("9998", "Baseline", None)],
        tasks=[("1", "1001", "A01", "2026-04-20 07:00", "2026-04-24 17:00"),
               ("2", "9998", "A01", "2026-04-18 07:00", "2026-04-22 17:00")],
        baseline_links=[],   # deliberate — no PROJBASELINE row
    )

    projects  = [_project("1001", "Live", sum_base_proj_id="9998"),
                 _project("9998", "Baseline")]
    tasks     = [_task("1", "1001", "A01"),
                 _task("2", "9998", "A01",
                       target_start="2026-04-18 07:00",
                       target_end  ="2026-04-22 17:00")]

    _install_fake_reader(monkeypatch,
                         projects=projects, tasks=tasks,
                         wbs_nodes=[], rels=[])

    from app.schedule.loader import load_xer_source
    payload, _ = load_xer_source(xer)
    assert payload["baselines"] == []


def test_adapter_baseline_resolution_trace_distinguishes_reader_vs_shim(tmp_path):
    """The adapter's resolution trace must mark baseline-linkage origin
    as either `reader-attribute`, `raw-section-shim`, or `empty`. This
    is the explicit-rather-than-implied evidence required by 020g-a
    validation step 2."""
    # Case A: reader-attribute wins (future-parser-upgrade path).
    reader_with_surface = _fake_reader(
        projbaselines=[_baseline_link("1001", "9998")]
    )
    src_a = ApexXerSource.from_reader(reader_with_surface, xer_path=None)
    assert len(src_a.projbaselines) == 1
    assert src_a.resolution_trace()["projbaselines"] == "reader-attribute"

    # Case B: shim supplies rows when reader is silent (current PyP6Xer 1.016.00 path).
    xer = tmp_path / "baseline.xer"
    _write_synthetic_xer(
        xer,
        projects=[("1001", "Live", "9998"), ("9998", "BL", None)],
        tasks=[("1", "1001", "A01", "2026-04-20 07:00", "2026-04-24 17:00")],
        baseline_links=[("1001", "9998", "Original")],
    )
    src_b = ApexXerSource.from_reader(_fake_reader(), xer_path=xer)
    assert len(src_b.projbaselines) == 1
    assert src_b.resolution_trace()["projbaselines"] == "raw-section-shim"

    # Case C: no reader surface AND no file → empty.
    src_c = ApexXerSource.from_reader(_fake_reader(), xer_path=None)
    assert src_c.projbaselines == []
    assert src_c.resolution_trace()["projbaselines"] == "empty"


# ---------------------------------------------------------------------------
# 4. Non-overload safety — adapter MUST NOT introduce schedule-write surfaces
# ---------------------------------------------------------------------------

def test_adapter_module_has_no_schedule_write_surfaces():
    """The adapter module must expose only read-only surfaces. No SQL
    strings, no DB import, no bridge / router imports. If a future edit
    adds any of those, this test fails loudly and the packet claim
    ('import-only, no schedule-write broadening') is broken."""
    adapter_path = Path(__file__).resolve().parents[1] / "app" / "schedule" / "xer_adapter.py"
    src = adapter_path.read_text(encoding="utf-8")
    forbidden = ["INSERT INTO", "UPDATE ", "DELETE FROM", "psycopg2",
                 "fastapi", "APIRouter", "app.routers"]
    found = [needle for needle in forbidden if needle in src]
    assert not found, (
        f"xer_adapter.py must remain read-only and import-only; forbidden "
        f"token(s) present: {found}"
    )
