"""
P6 schedule-context loader — packet UI-002a.

Lands P6-derived schedule context into the `schedule.*` tables.

Source precedence
-----------------
1. If a `.xer` file is present under `app/schedule/fixtures/`, parse it via
   `PyP6Xer` and translate into the schedule shape.
2. Otherwise, load the JSON fixture `stack_data_center.json`.

Boundary rules (see Source-Of-Truth memo §3 + packet UI-002a prompt)
--------------------------------------------------------------------
* This loader is the ONLY module that writes to `schedule.*`.
* It does NOT write to `seam.*`, `work.*`, `org.*`, or `identity.*`.
* It does NOT route writes through the governed mutation seam — schedule
  context is imported integration state, not operational mutation state, and
  does not claim completion or approval authority.
* Runs in a single transaction with an append-only `schedule.sync_log` row
  so the integration ledger is deterministic and recoverable.

Usage
-----
    python -m app.schedule.loader [--xer path/to/file.xer]
                                  [--json path/to/file.json]
                                  [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import traceback
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # pragma: no cover - defer error until run_load is called
    psycopg2 = None  # type: ignore

_HERE = Path(__file__).resolve().parent
_FIXTURES = _HERE / "fixtures"
_DEFAULT_JSON = _FIXTURES / "stack_data_center.json"


# ---------------------------------------------------------------------------
# XER enum translation — keep aligned with APEX_Schema_V2/P6_Enum_Alignment.md
# ---------------------------------------------------------------------------

XER_STATUS_TO_APEX: Dict[str, str] = {
    "TK_NotStart": "not_started",
    "TK_Active":   "active",
    "TK_Complete": "complete",
}


def translate_xer_status(xer_status: Optional[str]) -> Optional[str]:
    """Translate an XER TK_* status to the APEX stored enum.

    Unknown/missing XER values fall through to None; the bridge surfaces the
    raw `p6_status` so callers can see what was imported.
    """
    if xer_status is None:
        return None
    return XER_STATUS_TO_APEX.get(xer_status)


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------

def load_json_source(json_path: Path) -> Tuple[Dict[str, Any], str]:
    """Load a hand-authored JSON fixture. Returns (payload, source_file_basename)."""
    with json_path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return payload, json_path.name


def _pyp6xer_available() -> bool:
    try:
        import xerparser  # noqa: F401  # PyP6Xer distributes the `xerparser` module
        return True
    except ImportError:
        return False


def _stringify(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value: Any) -> Optional[int]:
    """Coerce a value to int, returning None for empty strings and
    non-numeric inputs. Added under UI-002g-host-followup-2 so the WBS
    transform can feed PyP6Xer's string-passthrough `seq_num` and the
    PROJWBS column-completion shim's empty-string fills into SQL INT
    columns without crashing `upsert_wbs`.

    This is a narrowly-scoped loader fix for a pre-existing transform bug
    that was masked when the 020h fixture could not survive Reader
    construction. Coercing to int here keeps the SQL insert signature
    unchanged and does not broaden the write surface.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


_RELATIONSHIP_TYPE_MAP = {
    # P6 canonical codes with PR_ prefix → DB check-constraint-accepted codes.
    "PR_FS": "FS",  # Finish to Start
    "PR_SS": "SS",  # Start to Start
    "PR_FF": "FF",  # Finish to Finish
    "PR_SF": "SF",  # Start to Finish
    # Bare two-letter forms pass through unchanged.
    "FS": "FS",
    "SS": "SS",
    "FF": "FF",
    "SF": "SF",
}


def _normalize_rel_type(value: Any) -> str:
    """Normalize a P6 predecessor type to the bare two-letter form the
    `schedule.relationships.rel_type_valid` check constraint expects.

    Added under UI-002g-host-followup-2 for the same narrowly-scoped
    reason as `_int_or_none`: the 020h fixture's TASKPRED section emits
    P6's canonical `PR_FS` form, which PyP6Xer passes through verbatim,
    but the DB's check constraint only accepts `FS` / `SS` / `FF` / `SF`.
    The JSON fixture path supplied pre-stripped codes so this was
    previously untested against the DB constraint.
    """
    if value is None:
        return "FS"
    text = str(value).strip().upper()
    if not text:
        return "FS"
    return _RELATIONSHIP_TYPE_MAP.get(text, text)


def _get_first_attr(obj: Any, *names: str) -> Any:
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return None


def _get_collection(obj: Any, *names: str) -> List[Any]:
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value:
                return list(value)
    return []


def _baseline_label(baseline_row: Any, project_lookup: Dict[str, Any], baseline_proj_id: str) -> str:
    explicit = _stringify(_get_first_attr(
        baseline_row,
        "base_type_name",
        "baseline_name",
        "base_proj_name",
        "base_proj_short_name",
        "name",
    ))
    if explicit:
        return explicit
    baseline_project = project_lookup.get(baseline_proj_id)
    project_name = _stringify(_get_first_attr(
        baseline_project,
        "proj_short_name",
        "name",
        "proj_name",
    ))
    if project_name:
        return project_name
    return f"P6 Baseline {baseline_proj_id}"


def _build_xer_baseline_entries(
    *,
    xer_path: Path,
    project_rows: List[Any],
    baseline_rows: List[Any],
    raw_task_rows: List[Any],
    live_task_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    project_lookup = {
        proj_id: project
        for project in project_rows
        if (proj_id := _stringify(getattr(project, "proj_id", None)))
    }
    live_tasks_by_project_and_code: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for task in live_task_rows:
        proj_id = _stringify(task.get("schedule_project_id", "").removeprefix("sched-proj-"))
        task_code = _stringify(task.get("task_code"))
        if proj_id and task_code:
            live_tasks_by_project_and_code[(proj_id, task_code)] = task

    baseline_task_rows: Dict[str, List[Any]] = {}
    for task in raw_task_rows:
        proj_id = _stringify(getattr(task, "proj_id", None))
        if proj_id:
            baseline_task_rows.setdefault(proj_id, []).append(task)

    selected_rows_by_live_project: Dict[str, Any] = {}
    rows_by_live_project: Dict[str, List[Any]] = {}
    for row in baseline_rows:
        live_proj_id = _stringify(_get_first_attr(row, "proj_id", "project_id"))
        baseline_proj_id = _stringify(_get_first_attr(row, "base_proj_id", "baseline_proj_id"))
        if live_proj_id and baseline_proj_id:
            rows_by_live_project.setdefault(live_proj_id, []).append(row)

    for live_proj_id, rows in rows_by_live_project.items():
        if len(rows) == 1:
            selected_rows_by_live_project[live_proj_id] = rows[0]
            continue
        preferred_baseline_id = _stringify(
            _get_first_attr(project_lookup.get(live_proj_id), "sum_base_proj_id")
        )
        if preferred_baseline_id:
            for row in rows:
                if _stringify(_get_first_attr(row, "base_proj_id", "baseline_proj_id")) == preferred_baseline_id:
                    selected_rows_by_live_project[live_proj_id] = row
                    break

    baselines_out: List[Dict[str, Any]] = []
    for live_proj_id, row in selected_rows_by_live_project.items():
        baseline_proj_id = _stringify(_get_first_attr(row, "base_proj_id", "baseline_proj_id"))
        if not baseline_proj_id:
            continue

        matched_tasks: List[Dict[str, Any]] = []
        for baseline_task in baseline_task_rows.get(baseline_proj_id, []):
            task_code = _stringify(getattr(baseline_task, "task_code", None))
            if not task_code:
                continue
            live_task = live_tasks_by_project_and_code.get((live_proj_id, task_code))
            if live_task is None:
                continue
            baseline_start = getattr(baseline_task, "target_start_date", None)
            baseline_finish = getattr(baseline_task, "target_end_date", None)
            if baseline_start is None or baseline_finish is None:
                continue
            matched_tasks.append({
                "schedule_task_id": live_task["id"],
                "baseline_start": baseline_start,
                "baseline_finish": baseline_finish,
            })

        if not matched_tasks:
            continue

        baselines_out.append({
            "baseline_source": "p6_import",
            "baseline_name": _baseline_label(row, project_lookup, baseline_proj_id),
            "schedule_project_id": f"sched-proj-{live_proj_id}",
            "p6_baseline_proj_id": baseline_proj_id,
            "source_file": xer_path.name,
            "tasks": matched_tasks,
        })

    return baselines_out


def load_xer_source(xer_path: Path) -> Tuple[Dict[str, Any], str]:
    """Parse a real P6 XER file via PyP6Xer.

    Returns the same payload shape as the JSON fixture so the downstream
    upserter does not need to branch by source type.

    NOTE: this translator supports the narrow subset the packet calls out —
    PROJECT, PROJWBS, TASK, TASKPRED, and baseline-bearing PROJBASELINE /
    BASELINEPROJECT links. It intentionally omits RSRC/TASKRSRC and
    CALENDAR (deferred per packet scope).

    Reader-surface reconciliation (packet 020g-a)
    --------------------------------------------
    The real PyP6Xer 1.016.00 Reader exposes schedule-bearing collections
    under names that do NOT match this loader's original assumptions
    (`activities` vs `tasks`, `wbss` vs `projwbs`, `relations` vs
    `taskpreds`). PyP6Xer 1.016.00 also does not parse PROJBASELINE /
    BASELINEPROJECT rows at all. Both gaps are closed by the Apex-owned
    `ApexXerSource` adapter (see `app/schedule/xer_adapter.py`), which
    normalizes real-Reader attribute names and falls back to a narrow
    raw-section shim for baseline-linkage rows. This loader therefore
    reads ONLY through the adapter's logical surface names.
    """
    # Packet UI-002g-host-followup: aligned with xer_adapter.py (line 104), which
    # already uses `from xerparser.reader import Reader`. The top-level
    # `from xerparser import Reader` worked against the mocked Reader used in
    # sandbox tests but fails against PyP6Xer 1.016.00 (current PyPI), where
    # `Reader` lives under the `xerparser.reader` submodule. This is a 1-line
    # import path correction; it changes no semantics, no SQL, no response
    # shape, no variance behavior.
    #
    # Packet UI-002g-host-followup-2: Reader construction is now handled by
    # ApexXerSource.from_xer_path(), which applies the narrow PROJWBS
    # column-completion shim needed for PyP6Xer 1.016.00 to parse the 020h
    # golden fixture (whose minimal %F\tPROJWBS header omits OBS / GUID /
    # EV / anticipated-date columns that PyP6Xer's WBS.__init__ accesses
    # unguarded). The Reader import is retained here because (a) the 020g-a
    # `_FakeXerParserReader`-based tests already exercise the from_reader
    # path directly and do not touch from_xer_path, and (b) keeping the
    # import live documents that this loader is still a PyP6Xer-backed
    # consumer regardless of which adapter entry point it uses.
    from xerparser.reader import Reader  # type: ignore  # noqa: F401

    from app.schedule.xer_adapter import ApexXerSource  # local import to keep cold-start tidy

    source = ApexXerSource.from_xer_path(xer_path)

    project_rows = list(source.projects)
    raw_task_rows = list(source.tasks)
    baseline_rows = list(source.projbaselines)

    baseline_project_ids = {
        baseline_proj_id
        for baseline_row in baseline_rows
        if (baseline_proj_id := _stringify(_get_first_attr(baseline_row, "base_proj_id", "baseline_proj_id")))
    }
    baseline_project_ids.update({
        baseline_proj_id
        for project in project_rows
        if (baseline_proj_id := _stringify(_get_first_attr(project, "sum_base_proj_id")))
    })

    projects_out: List[Dict[str, Any]] = []
    wbs_out: List[Dict[str, Any]] = []
    tasks_out: List[Dict[str, Any]] = []
    rels_out: List[Dict[str, Any]] = []

    # Projects — live schedule projects only. Baseline-project rows are used
    # solely as provenance + frozen-date sources for the separate baseline lane.
    for p in project_rows:
        proj_id = str(getattr(p, "proj_id", ""))
        if proj_id in baseline_project_ids:
            continue
        projects_out.append({
            "id":                 f"sched-proj-{proj_id}",
            "p6_project_id":      proj_id,
            "name":               getattr(p, "proj_short_name", "") or getattr(p, "name", "") or "",
            "scope_project_id":   None,  # scope linking is resolved by the bridge, not the loader
            "data_date":          getattr(p, "last_recalc_date", None),
            "planned_start":      getattr(p, "plan_start_date", None),
            "planned_finish":     getattr(p, "plan_end_date", None),
            "actual_start":       getattr(p, "act_start_date", None),
            "actual_finish":      getattr(p, "act_end_date", None),
            "must_finish_by":     getattr(p, "scd_end_date", None),
        })

    # WBS (adapter-normalized: real PyP6Xer attribute is `wbss`)
    for w in source.projwbs:
        wbs_id  = str(getattr(w, "wbs_id", ""))
        proj_id = str(getattr(w, "proj_id", ""))
        if proj_id in baseline_project_ids:
            continue
        parent  = getattr(w, "parent_wbs_id", None)
        wbs_out.append({
            "id":                   f"sched-wbs-{wbs_id}",
            "p6_wbs_id":            wbs_id,
            "schedule_project_id":  f"sched-proj-{proj_id}",
            "parent_wbs_id":        f"sched-wbs-{parent}" if parent else None,
            "name":                 getattr(w, "wbs_name", "") or "",
            "short_name":           getattr(w, "wbs_short_name", None),
            # Packet UI-002g-host-followup-2: coerce empty-string to None for
            # INT columns. Previously the fixture never survived PyP6Xer
            # Reader construction so this path was untested against the
            # real parser; with the 020h fixture now reachable, PyP6Xer's
            # string passthrough on `seq_num` and the `""` fill the PROJWBS
            # shim supplies for an unflagged root node both land here and
            # would crash `upsert_wbs`'s SQL (INT col) on insert.
            "seq":                  _int_or_none(getattr(w, "seq_num", None)),
            "level":                _int_or_none(getattr(w, "proj_node_flag", None)),
        })

    # Tasks
    for t in raw_task_rows:
        tid     = str(getattr(t, "task_id", ""))
        proj_id = str(getattr(t, "proj_id", ""))
        if proj_id in baseline_project_ids:
            continue
        wbs_id  = getattr(t, "wbs_id", None)
        tasks_out.append({
            "id":                   f"sched-task-{tid}",
            "p6_task_id":           tid,
            "schedule_project_id":  f"sched-proj-{proj_id}",
            "schedule_wbs_id":      f"sched-wbs-{wbs_id}" if wbs_id else None,
            "scope_id":             None,
            "p6_status":            getattr(t, "status_code", None),
            "apex_status":          translate_xer_status(getattr(t, "status_code", None)),
            "task_code":            getattr(t, "task_code", None),
            "task_name":            getattr(t, "task_name", "") or "",
            "task_type":            getattr(t, "task_type", None),
            "duration_hours":       getattr(t, "target_drtn_hr_cnt", None),
            "planned_start":        getattr(t, "target_start_date", None),
            "planned_finish":       getattr(t, "target_end_date", None),
            "actual_start":         getattr(t, "act_start_date", None),
            "actual_finish":        getattr(t, "act_end_date", None),
            "total_float_hours":    getattr(t, "total_float_hr_cnt", None),
            "free_float_hours":     getattr(t, "free_float_hr_cnt", None),
            "critical_flag":        bool(getattr(t, "driving_path_flag", False)),
            "constraint_type":      getattr(t, "cstr_type", None),
            "constraint_date":      getattr(t, "cstr_date", None),
        })

    # Relationships (TASKPRED; adapter-normalized: real PyP6Xer attribute is `relations`)
    for r in source.taskpreds:
        rid     = str(getattr(r, "task_pred_id", ""))
        proj_id = str(getattr(r, "proj_id", ""))
        if proj_id in baseline_project_ids:
            continue
        pred    = str(getattr(r, "pred_task_id", ""))
        succ    = str(getattr(r, "task_id", ""))
        rels_out.append({
            "id":                    f"sched-rel-{rid}",
            "p6_taskpred_id":        rid,
            "schedule_project_id":   f"sched-proj-{proj_id}",
            "predecessor_task_id":   f"sched-task-{pred}",
            "successor_task_id":     f"sched-task-{succ}",
            # Packet UI-002g-host-followup-2: the payload preserves P6's
            # raw `pred_type` (e.g., `PR_FS`) so the 020h fixture's
            # read-surface test (`test_loader_emits_declared_live_lane_counts`)
            # continues to see XER truth. Normalization to the bare
            # two-letter form the `schedule.relationships.rel_type_valid`
            # check constraint expects happens at SQL insert time in
            # `upsert_relationships` — the write-surface adaptation, not
            # a read-surface mutation.
            "rel_type":              getattr(r, "pred_type", "FS") or "FS",
            "lag_hours":             getattr(r, "lag_hr_cnt", 0) or 0,
        })

    baselines_out = _build_xer_baseline_entries(
        xer_path=xer_path,
        project_rows=project_rows,
        baseline_rows=baseline_rows,
        raw_task_rows=raw_task_rows,
        live_task_rows=tasks_out,
    )

    return (
        {
            "source": {
                "type":        "xer",
                "source_file": xer_path.name,
                "data_date":   None,
            },
            "projects":      projects_out,
            "wbs_nodes":     wbs_out,
            "tasks":         tasks_out,
            "relationships": rels_out,
            "baselines":     baselines_out,
        },
        xer_path.name,
    )


def resolve_source(xer: Optional[Path], json_override: Optional[Path]) -> Tuple[Dict[str, Any], str, str]:
    """Pick a source file based on explicit precedence and return
    ``(payload, source_type, source_file)``.

    Precedence (authored under backend-hygiene packet
    PM-SEAM-BACKEND-HYGIENE-002):

        1. Explicit ``xer=<path>`` (CLI ``--xer``) → parsed via PyP6Xer,
           ``source_type = "xer"``.
        2. Explicit ``json_override=<path>`` (CLI ``--json``) → parsed as
           JSON, ``source_type = "json-fixture"``.
        3. Default JSON fixture ``stack_data_center.json`` →
           ``source_type = "json-fixture"``.

    Intentionally does NOT auto-discover ``*.xer`` files in the fixtures
    directory. On-disk XER fixtures (e.g. packet 020h's
    ``stack_data_center_baseline_sanitized.xer``) are admitted under
    per-packet golden-fixture contracts and MUST be consumed explicitly
    by their owning test via ``load_xer_source(path)`` or
    ``run_load(xer=path, ...)``. Promoting any such file into the
    default dry-run path would silently override the canonical
    JSON-fixture contract asserted by
    ``test_loader_dry_run_against_fixture`` and would violate the 020h
    fixture README's §8 item #2 ("Do not modify
    ``apps/mutation-seam/app/schedule/loader.py``").
    """
    if xer and xer.exists():
        if not _pyp6xer_available():
            raise RuntimeError(
                f"PyP6Xer is required to parse {xer.name}. Install it with "
                f"`pip install PyP6Xer` or remove/rename the file to fall back "
                f"to the JSON fixture."
            )
        payload, src = load_xer_source(xer)
        return payload, "xer", src

    path = json_override or _DEFAULT_JSON
    payload, src = load_json_source(path)
    return payload, "json-fixture", src


# ---------------------------------------------------------------------------
# Upsert machinery
# ---------------------------------------------------------------------------

def _coerce_dt(v: Any) -> Any:
    """Pass-through for datetimes and ISO strings; psycopg2 handles both."""
    if v is None:
        return None
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v
    return v  # let psycopg2 cast the ISO string


def upsert_projects(cur, rows: List[Dict[str, Any]], *, source_file: str) -> int:
    for r in rows:
        cur.execute(
            """
            INSERT INTO schedule.projects
                (id, p6_project_id, name, scope_project_id,
                 data_date, planned_start, planned_finish,
                 actual_start, actual_finish, must_finish_by,
                 last_imported_at, source_file, data)
            VALUES (%s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    now(), %s, '{}'::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                name             = EXCLUDED.name,
                scope_project_id = EXCLUDED.scope_project_id,
                data_date        = EXCLUDED.data_date,
                planned_start    = EXCLUDED.planned_start,
                planned_finish   = EXCLUDED.planned_finish,
                actual_start     = EXCLUDED.actual_start,
                actual_finish    = EXCLUDED.actual_finish,
                must_finish_by   = EXCLUDED.must_finish_by,
                last_imported_at = now(),
                source_file      = EXCLUDED.source_file
            """,
            (
                r["id"], r["p6_project_id"], r["name"], r.get("scope_project_id"),
                _coerce_dt(r.get("data_date")),
                _coerce_dt(r.get("planned_start")), _coerce_dt(r.get("planned_finish")),
                _coerce_dt(r.get("actual_start")),  _coerce_dt(r.get("actual_finish")),
                _coerce_dt(r.get("must_finish_by")),
                source_file,
            ),
        )
    return len(rows)


def upsert_wbs(cur, rows: List[Dict[str, Any]]) -> int:
    # Insert roots first, then children, so parent_wbs_id soft-references are
    # always already present at read time.
    ordered = sorted(rows, key=lambda r: (r.get("parent_wbs_id") is not None, r.get("seq") or 0))
    for r in ordered:
        cur.execute(
            """
            INSERT INTO schedule.wbs_nodes
                (id, p6_wbs_id, schedule_project_id, parent_wbs_id,
                 name, short_name, seq, level, data)
            VALUES (%s, %s, %s, %s,
                    %s, %s, %s, %s, '{}'::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                name          = EXCLUDED.name,
                short_name    = EXCLUDED.short_name,
                seq           = EXCLUDED.seq,
                level         = EXCLUDED.level,
                parent_wbs_id = EXCLUDED.parent_wbs_id
            """,
            (
                r["id"], r["p6_wbs_id"], r["schedule_project_id"], r.get("parent_wbs_id"),
                r["name"], r.get("short_name"), r.get("seq"), r.get("level"),
            ),
        )
    return len(rows)


def upsert_tasks(cur, rows: List[Dict[str, Any]]) -> int:
    for r in rows:
        cur.execute(
            """
            INSERT INTO schedule.tasks
                (id, p6_task_id, schedule_project_id, schedule_wbs_id, scope_id,
                 p6_status, apex_status, task_code, task_name, task_type,
                 duration_hours, planned_start, planned_finish,
                 actual_start, actual_finish,
                 total_float_hours, free_float_hours, critical_flag,
                 constraint_type, constraint_date, data)
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s, '{}'::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                schedule_wbs_id   = EXCLUDED.schedule_wbs_id,
                scope_id          = EXCLUDED.scope_id,
                p6_status         = EXCLUDED.p6_status,
                apex_status       = EXCLUDED.apex_status,
                task_code         = EXCLUDED.task_code,
                task_name         = EXCLUDED.task_name,
                task_type         = EXCLUDED.task_type,
                duration_hours    = EXCLUDED.duration_hours,
                planned_start     = EXCLUDED.planned_start,
                planned_finish    = EXCLUDED.planned_finish,
                actual_start      = EXCLUDED.actual_start,
                actual_finish     = EXCLUDED.actual_finish,
                total_float_hours = EXCLUDED.total_float_hours,
                free_float_hours  = EXCLUDED.free_float_hours,
                critical_flag     = EXCLUDED.critical_flag,
                constraint_type   = EXCLUDED.constraint_type,
                constraint_date   = EXCLUDED.constraint_date
            """,
            (
                r["id"], r["p6_task_id"], r["schedule_project_id"], r.get("schedule_wbs_id"), r.get("scope_id"),
                r.get("p6_status"), r.get("apex_status"), r.get("task_code"), r["task_name"], r.get("task_type"),
                r.get("duration_hours"),
                _coerce_dt(r.get("planned_start")), _coerce_dt(r.get("planned_finish")),
                _coerce_dt(r.get("actual_start")), _coerce_dt(r.get("actual_finish")),
                r.get("total_float_hours"), r.get("free_float_hours"), bool(r.get("critical_flag")),
                r.get("constraint_type"), _coerce_dt(r.get("constraint_date")),
            ),
        )
    return len(rows)


def upsert_relationships(cur, rows: List[Dict[str, Any]]) -> int:
    for r in rows:
        cur.execute(
            """
            INSERT INTO schedule.relationships
                (id, p6_taskpred_id, schedule_project_id,
                 predecessor_task_id, successor_task_id, rel_type, lag_hours, data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, '{}'::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                predecessor_task_id = EXCLUDED.predecessor_task_id,
                successor_task_id   = EXCLUDED.successor_task_id,
                rel_type            = EXCLUDED.rel_type,
                lag_hours           = EXCLUDED.lag_hours
            """,
            (
                r["id"], r["p6_taskpred_id"], r["schedule_project_id"],
                r["predecessor_task_id"], r["successor_task_id"],
                # Packet UI-002g-host-followup-2: normalize at the
                # write surface against `rel_type_valid`. Payload keeps
                # raw P6 form for read-surface tests; SQL coerces.
                _normalize_rel_type(r["rel_type"]), r.get("lag_hours", 0),
            ),
        )
    return len(rows)


# ---------------------------------------------------------------------------
# Baseline lane (packet 020c) — upserts authorized baseline truth ONLY.
#
# Honoring 020a and 020b:
#   * No synthetic fabrication. If a baseline entry is absent, baseline
#     columns remain untouched.
#   * Never overwrite the live `planned_*` columns. `upsert_tasks` does not
#     reference baseline columns in its ON CONFLICT SET clause, and this
#     module writes only the baseline_* columns — the two lanes are
#     structurally separated.
#   * Non-overload: if a task already has a non-NULL baseline and the new
#     entry's source is not 'rebaseline', the existing value is preserved
#     and the row is counted as `preserved_existing` in stats.
#   * The baseline event ledger row is created in the same transaction as
#     the per-task updates so ledger and facts cannot diverge.
# ---------------------------------------------------------------------------


_ALLOWED_BASELINE_SOURCES = ("p6_import", "internal_capture", "rebaseline")


def _validate_baseline_entry(entry: Dict[str, Any]) -> None:
    """Field-presence + source-whitelist check. Raises ValueError on violation."""
    for required in ("baseline_name", "baseline_source", "schedule_project_id"):
        if not entry.get(required):
            raise ValueError(f"baseline entry missing required field: {required}")
    src = entry["baseline_source"]
    if src not in _ALLOWED_BASELINE_SOURCES:
        raise ValueError(
            f"baseline_source={src!r} not in {_ALLOWED_BASELINE_SOURCES}"
        )
    if src == "p6_import" and not entry.get("p6_baseline_proj_id"):
        raise ValueError(
            "baseline_source='p6_import' requires p6_baseline_proj_id "
            "(per 020b §3.3 — the baseline PROJECT must be identified)."
        )
    if src == "internal_capture" and not entry.get("captured_by_actor_id"):
        raise ValueError(
            "baseline_source='internal_capture' requires captured_by_actor_id "
            "(per 020a §3.6 — actor attestation is mandatory)."
        )
    tasks = entry.get("tasks") or []
    if not isinstance(tasks, list):
        raise ValueError("baseline entry `tasks` must be a list")
    for t in tasks:
        for required in ("schedule_task_id", "baseline_start", "baseline_finish"):
            if not t.get(required):
                raise ValueError(
                    f"baseline task missing required field: {required}"
                )


def upsert_baselines(
    cur,
    baselines: List[Dict[str, Any]],
    *,
    default_source_file: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Upsert each authorized baselining event and apply its per-task baseline
    dates onto matched `schedule.tasks` rows.

    Returns a list of per-event result dicts so the caller can surface them in
    the load-level stats and keep the integration ledger honest.

    Matching strategy:
        * JSON fixtures and internal_capture entries provide
          `schedule_task_id` directly; the task is looked up by primary key.
        * p6_import entries still need to provide matched
          `schedule_task_id`s (the XER-side parser does the `task_code`
          match per 020b §3.3 before calling this function).

    This function NEVER:
        * writes the live `planned_*` columns,
        * writes rows in any other schema (`seam.*`, `work.*`, `org.*`,
          `identity.*`), or
        * overwrites a non-NULL baseline unless `baseline_source='rebaseline'`.
    """
    results: List[Dict[str, Any]] = []
    if not baselines:
        return results

    for entry in baselines:
        _validate_baseline_entry(entry)

        event_id = entry.get("id") or (
            f"blev-{_dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')}"
            f"-{uuid.uuid4().hex[:8]}"
        )
        source = entry["baseline_source"]
        name   = entry["baseline_name"]
        proj   = entry["schedule_project_id"]
        tasks  = entry.get("tasks") or []

        # Open the event ledger row in the same transaction.
        cur.execute(
            """
            INSERT INTO schedule.baseline_events
                (id, schedule_project_id, baseline_source, baseline_name,
                 p6_baseline_proj_id, source_file,
                 captured_at, captured_by_actor_id,
                 status, stats)
            VALUES (%s, %s, %s, %s,
                    %s, %s,
                    COALESCE(%s::timestamptz, now()), %s,
                    'in_progress', '{}'::jsonb)
            """,
            (
                event_id, proj, source, name,
                entry.get("p6_baseline_proj_id"),
                entry.get("source_file") or default_source_file,
                _coerce_dt(entry.get("captured_at")),
                entry.get("captured_by_actor_id"),
            ),
        )

        matched = 0
        preserved_existing = 0
        unmatched = []

        for t in tasks:
            sched_task_id = t["schedule_task_id"]
            # Read the current baseline state to enforce non-overload.
            cur.execute(
                "SELECT baseline_start_at FROM schedule.tasks WHERE id = %s",
                (sched_task_id,),
            )
            row = cur.fetchone()
            if row is None:
                unmatched.append(sched_task_id)
                continue
            existing_baseline_start = row[0]
            if existing_baseline_start is not None and source != "rebaseline":
                # 020b §5.3 — preserve existing baseline; non-destructive.
                preserved_existing += 1
                continue
            cur.execute(
                """
                UPDATE schedule.tasks
                   SET baseline_start_at = %s,
                       baseline_end_at   = %s,
                       baseline_name     = %s,
                       baseline_source   = %s,
                       baselined_at      = COALESCE(%s::timestamptz, now()),
                       baseline_event_id = %s
                 WHERE id = %s
                """,
                (
                    _coerce_dt(t["baseline_start"]),
                    _coerce_dt(t["baseline_finish"]),
                    name,
                    source,
                    _coerce_dt(entry.get("captured_at")),
                    event_id,
                    sched_task_id,
                ),
            )
            matched += cur.rowcount

        stats = {
            "matched_tasks":            matched,
            "preserved_existing_tasks": preserved_existing,
            "unmatched_baseline_tasks": unmatched,
            "total_baseline_rows":      len(tasks),
        }
        cur.execute(
            """
            UPDATE schedule.baseline_events
               SET status = 'success',
                   stats  = %s::jsonb
             WHERE id = %s
            """,
            (json.dumps(stats), event_id),
        )

        results.append({
            "id":                    event_id,
            "schedule_project_id":   proj,
            "baseline_source":       source,
            "baseline_name":         name,
            "p6_baseline_proj_id":   entry.get("p6_baseline_proj_id"),
            "source_file":           entry.get("source_file") or default_source_file,
            "stats":                 stats,
        })

    return results


# ---------------------------------------------------------------------------
# Sync log + transactional run_load
# ---------------------------------------------------------------------------

def _insert_sync_log_start(cur, *, source_type: str, source_file: str) -> str:
    sync_id = f"sync-{_dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')}-{uuid.uuid4().hex[:8]}"
    cur.execute(
        """
        INSERT INTO schedule.sync_log
            (id, source_type, source_file, started_at, status, stats)
        VALUES (%s, %s, %s, now(), 'in_progress', '{}'::jsonb)
        """,
        (sync_id, source_type, source_file),
    )
    return sync_id


def _update_sync_log_success(cur, sync_id: str, stats: Dict[str, Any]) -> None:
    cur.execute(
        """
        UPDATE schedule.sync_log
           SET status      = 'success',
               finished_at = now(),
               stats       = %s::jsonb
         WHERE id = %s
        """,
        (json.dumps(stats, default=str), sync_id),
    )


def _update_sync_log_failure(cur, sync_id: str, err: str) -> None:
    cur.execute(
        """
        UPDATE schedule.sync_log
           SET status      = 'failure',
               finished_at = now(),
               stats       = %s::jsonb
         WHERE id = %s
        """,
        (json.dumps({"error": err}), sync_id),
    )


def _dry_run_cursor():
    """A recording cursor for dry-runs that still exercises the same code
    paths upsert_baselines takes against a live cursor, without touching
    a real database.

    Returns None for every SELECT so non-existent task branches are taken;
    this keeps dry-run as validation-only without claiming persistence.
    """

    class _DryCursor:
        def __init__(self) -> None:
            self.rowcount = 0

        def execute(self, sql: str, params: Any = None) -> None:
            # Record shape only; nothing persists.
            self.rowcount = 0

        def fetchone(self):
            return None

    return _DryCursor()


def run_load(
    *,
    xer: Optional[Path] = None,
    json_override: Optional[Path] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Run the schedule-context load.

    Boundary rules (UI-002a §3 + 020b / 020c):
        * Single transaction wrapping sync_log open → upserts → sync_log close
        * Baseline upserts run in the SAME transaction via upsert_baselines
        * dry_run=True validates the payload shape (including baseline
          entries) and returns per-lane counts without opening a DB
          connection. Baseline validation failures are surfaced as
          ValueError so the caller sees the problem before a host run.
    """
    payload, source_type, source_file = resolve_source(xer, json_override)

    projects      = list(payload.get("projects", []))
    wbs_nodes     = list(payload.get("wbs_nodes", []))
    tasks         = list(payload.get("tasks", []))
    relationships = list(payload.get("relationships", []))
    baselines     = list(payload.get("baselines", []))

    # Validate baselines eagerly so the dry-run branch cannot silently
    # report success against a structurally broken payload (see 020c §4).
    for entry in baselines:
        _validate_baseline_entry(entry)

    stats: Dict[str, Any] = {
        "projects":        len(projects),
        "wbs_nodes":       len(wbs_nodes),
        "tasks":           len(tasks),
        "relationships":   len(relationships),
        "baseline_events": len(baselines),
    }

    if dry_run:
        # Exercise upsert_baselines against a recording cursor so the
        # branching in that function stays covered by dry-run. Baseline
        # UPDATEs against non-existent tasks will surface as unmatched
        # in the returned per-event stats, which is the correct dry-run
        # semantic — dry-run never claims matched writes.
        dry_cur = _dry_run_cursor()
        dry_baseline_results = upsert_baselines(
            dry_cur, baselines, default_source_file=source_file
        )
        return {
            "dry_run":     True,
            "source_type": source_type,
            "source_file": source_file,
            "stats":       stats,
            "baseline_results": dry_baseline_results,
        }

    if psycopg2 is None:
        raise RuntimeError(
            "psycopg2 is not installed; cannot run persisted load. "
            "Install psycopg2-binary in the mutation-seam runtime."
        )

    dsn = os.environ.get("SEAM_DATABASE_URL")
    if not dsn:
        raise RuntimeError(
            "SEAM_DATABASE_URL is not set; the schedule loader requires "
            "an apex_pm_stage DSN for persisted runs."
        )

    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            sync_id = _insert_sync_log_start(
                cur, source_type=source_type, source_file=source_file
            )
            try:
                upsert_projects(cur, projects, source_file=source_file)
                upsert_wbs(cur, wbs_nodes)
                upsert_tasks(cur, tasks)
                upsert_relationships(cur, relationships)
                baseline_results = upsert_baselines(
                    cur, baselines, default_source_file=source_file
                )
                _update_sync_log_success(cur, sync_id, stats)
            except Exception as e:
                tb = traceback.format_exc()
                _update_sync_log_failure(cur, sync_id, f"{type(e).__name__}: {e}\n{tb}")
                raise
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "dry_run":          False,
        "source_type":      source_type,
        "source_file":      source_file,
        "stats":            stats,
        "baseline_results": baseline_results,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m app.schedule.loader",
        description=(
            "Load P6 schedule context (projects, WBS, tasks, relationships, "
            "baselines) into schedule.* tables from a JSON fixture or a .xer file."
        ),
    )
    p.add_argument("--xer", type=Path, default=None,
                   help="Path to a .xer file to parse via PyP6Xer.")
    p.add_argument("--json", dest="json_override", type=Path, default=None,
                   help="Path to an alternate JSON fixture (overrides default).")
    p.add_argument("--dry-run", action="store_true",
                   help="Validate and report counts without writing to the DB.")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        result = run_load(
            xer=args.xer, json_override=args.json_override, dry_run=args.dry_run
        )
    except Exception as e:
        sys.stderr.write(f"schedule loader failed: {type(e).__name__}: {e}\n")
        return 1
    sys.stdout.write(json.dumps(result, default=str, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())