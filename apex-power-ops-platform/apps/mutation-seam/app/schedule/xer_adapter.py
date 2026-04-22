"""
Apex-owned XER adapter — packet 020g-a.

Purpose
-------
Packet 020f empirically established that the installed PyP6Xer 1.016.00
`Reader` exposes the schedule-bearing collections under names that do
NOT match the ones `load_xer_source()` originally assumed:

    Apex loader assumed       Real PyP6Xer 1.016.00 attribute
    ---------------------     -------------------------------
    reader.tasks              reader.activities
    reader.projwbs            reader.wbss
    reader.taskpreds          reader.relations
    reader.projects           reader.projects           (matches)

And crucially: PyP6Xer 1.016.00 does NOT parse `PROJBASELINE` or
`BASELINEPROJECT` rows at all — its `create_object()` dispatcher has no
branch for them, so even a perfectly-formed baseline-bearing `.xer`
yields an empty baseline-linkage surface on the Reader.

This module is the narrow, Apex-owned, import-only adapter selected as
packet 020g-a's "Strategy A" (parser-side reconciliation) from the
`PM-DOMAIN-XER-TOOLS-LONG-TERM-VALUE-PLAN-2026-04-18.md` planning memo.

It does three things, and only those three things:

1.  `ApexXerSource` — wrap a PyP6Xer Reader (or any duck-typed stand-in)
    and expose a normalized surface the loader can rely on regardless of
    which attribute-name spelling the underlying parser uses.
    The attribute probe is explicit, parameterized, and preserves the
    already-documented 020d compatibility-layer intent.

2.  `parse_baseline_rows_raw()` — a narrow `%T`-headed-section scanner
    that reads the XER file directly (UTF-8, ignoring decode errors, the
    same way PyP6Xer does) and yields `PROJBASELINE` / `BASELINEPROJECT`
    rows as simple namespace objects with the P6 column names already
    expected by `_build_xer_baseline_entries()` in the loader.
    This is the narrowest possible baseline shim: it does NOT re-parse
    any other `%T` section, does NOT replace the PyP6Xer Reader for
    PROJECT / TASK / TASKPRED / PROJWBS, and does NOT mutate the file.

3.  `ApexXerSource.from_xer_path()` + `_sanitize_xer_for_pyp6xer()` —
    packet UI-002g-host-followup-2 addition. PyP6Xer 1.016.00's
    `WBS.__init__` accesses a large set of optional WBS columns
    (`obs_id`, `sum_data_flag`, `status_code`, `phase_id`, `guid`, …)
    without null-guarding; if the `%F` header of a PROJWBS section
    omits them, `params.get('obs_id').strip()` crashes at Reader
    construction time. The 020h sanitized golden fixture deliberately
    omits those columns per its fixture-contract §3, so PyP6Xer cannot
    even construct a Reader over it. `_sanitize_xer_for_pyp6xer()`
    pre-processes the XER text in memory, appending the missing
    unguarded-access columns to the PROJWBS `%F` header and padding
    each `%R` row with empty-string fills, writes the result to a
    temp file, and lets the Reader consume THAT path instead. The
    original fixture on disk is never modified. The sanitized copy
    is used ONLY for Reader construction — the original `xer_path`
    is still what the raw-section shim (item 2) reads for
    PROJBASELINE/BASELINEPROJECT rows. Only the PROJWBS section is
    touched; all other `%T` sections pass through verbatim.

Boundary rules preserved (020a / 020b / 020c / 020d / 020e.1 / 020f):

    * Read-only, import-only. No SQL, no DB writes, no bridge routes,
      no PM UI, no write-surface broadening.
    * No synthetic fabrication. If the file contains no PROJBASELINE /
      BASELINEPROJECT section, `parse_baseline_rows_raw()` returns an
      empty list. Baseline entries are emitted downstream only when
      matched baseline tasks actually exist.
    * No current-plan overload. The adapter's task / wbs / taskpred
      surface is used by live-project import only; baseline-project
      filtering is still done by `_build_xer_baseline_entries()` on the
      loader side, unchanged.
    * Explicit rather than implicit. Every name the adapter substitutes
      is listed in the `_ATTRIBUTE_ALIASES` table below so the
      reconciliation is discoverable from source alone.
"""
from __future__ import annotations

import codecs
import csv
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Explicit, table-driven attribute-name reconciliation.
#
# Each entry is:
#   (logical_name_used_by_loader, tuple of real-reader attribute names to try in order)
#
# The loader's existing `_get_collection` probe checked *multiple* legacy
# spellings — that intent is preserved here, but is now centralized in one
# authoritative table so the reconciliation is explicit (per 020g-a scope
# item 2 and validation_step 1) and cannot drift between call sites.
# ---------------------------------------------------------------------------
_ATTRIBUTE_ALIASES: Sequence[Tuple[str, Tuple[str, ...]]] = (
    # Logical name used inside load_xer_source / _build_xer_baseline_entries
    #                          Real PyP6Xer 1.016.00 name first, legacy spellings after.
    ("projects",               ("projects",)),
    ("tasks",                  ("activities", "tasks")),
    ("projwbs",                ("wbss", "projwbs")),
    ("taskpreds",              ("relations", "taskpreds", "predecessors")),
    # Baseline-linkage surface. PyP6Xer 1.016.00 does not parse these at
    # all; the raw-section shim populates them on the adapter instead.
    ("projbaselines",          ("projbaselines", "projbaseline",
                                "baselineprojects", "baselineproject")),
)

# Baseline `%T` section names the raw-section shim recognizes. P6 exports
# typically use `PROJBASELINE`; older / alternate exports use
# `BASELINEPROJECT`. Both carry the same `proj_id` / `base_proj_id`
# semantics per 020b §2 and the fixture contract §2.
_BASELINE_SECTION_NAMES = ("PROJBASELINE", "BASELINEPROJECT")


# ---------------------------------------------------------------------------
# PROJWBS column-completion shim — packet UI-002g-host-followup-2.
#
# PyP6Xer 1.016.00's `xerparser.model.classes.wbs.WBS.__init__` reads the
# following optional P6 WBS columns with `params.get('<col>').strip()` —
# i.e., no None-guard. If the XER's PROJWBS `%F` header omits any of
# them, the corresponding `params.get(...)` returns None and `.strip()`
# raises AttributeError at Reader construction time, before the adapter
# can even see the Reader.
#
# The 020h sanitized golden fixture deliberately omits these columns per
# its `%F\tPROJWBS` contract (see BASELINE_XER_FIXTURE_CONTRACT.md §3 and
# the 020h admission handoff §5). Mutating the admitted fixture would
# invalidate its contract; patching third-party PyP6Xer is forbidden by
# packet scope. The narrowest Apex-owned remedy is to pre-process the
# XER text in memory and hand PyP6Xer a Reader-construction-safe copy
# whose PROJWBS section simply *has* the columns PyP6Xer assumes are
# always present, filled with empty strings (the same value P6 would
# emit for a blank optional column). This is not a data change — the
# sanitized copy is used ONLY for Reader construction; the admitted
# fixture on disk is byte-for-byte unchanged, and the raw-section shim
# (parse_baseline_rows_raw) still reads from the original path.
#
# The list below is derived verbatim by inspection of PyP6Xer 1.016.00's
# WBS.__init__ method. Every name appears as the argument to a
# `params.get(...).strip()` expression that is NOT guarded by an outer
# `if params.get(...):` truthy check. Guarded accesses (e.g. `wbs_id`,
# `proj_id`, `parent_wbs_id`, `plan_open_state`) are omitted because
# they tolerate missing values safely.
# ---------------------------------------------------------------------------
_PROJWBS_REQUIRED_UNGUARDED_COLUMNS = (
    "obs_id",
    "seq_num",
    "proj_node_flag",
    "sum_data_flag",
    "status_code",
    "wbs_short_name",
    "wbs_name",
    "phase_id",
    "ev_user_pct",
    "ev_etc_user_value",
    "orig_cost",
    "indep_remain_total_cost",
    "ann_dscnt_rate_pct",
    "dscnt_period_type",
    "indep_remain_work_qty",
    "anticip_start_date",
    "anticip_end_date",
    "ev_compute_type",
    "ev_etc_compute_type",
    "guid",
    "tmpl_guid",
)


def _sanitize_xer_for_pyp6xer(xer_path: Path) -> Path:
    """Return a path whose PROJWBS section is guaranteed to have every
    column PyP6Xer 1.016.00's `WBS.__init__` reads unguarded.

    If the original file already satisfies that requirement, the
    original path is returned unchanged. Otherwise, a sanitized copy is
    written to a tempfile and that tempfile's path is returned. The
    caller is responsible for deleting the tempfile after Reader
    construction finishes (see `ApexXerSource.from_xer_path`).

    Sanitization rules:

    * Only the PROJWBS section is inspected. All other `%T` sections
      pass through verbatim, byte-for-byte (including PROJBASELINE,
      PROJECT, TASK, TASKPRED, CALENDAR, and any future section).
    * Within PROJWBS: the `%F` header gains, appended at the end, any
      names from `_PROJWBS_REQUIRED_UNGUARDED_COLUMNS` that were not
      already present. Existing header names keep their positions.
    * Within PROJWBS: every `%R` record is right-padded with empty
      strings so its value count equals the new header length.
      Existing row values keep their positions and values.
    * The fixture on disk is never modified.

    This matches what P6 would have written if the fixture's author had
    simply left every optional column blank instead of omitting them
    from the `%F` header.
    """
    path = Path(xer_path)
    if not path.is_file():
        return path

    # Read with PyP6Xer's decode semantics.
    with codecs.open(str(path), encoding="utf-8", errors="ignore") as fh:
        original_text = fh.read()

    # First pass — do we even need to sanitize?
    lines = original_text.splitlines(keepends=False)
    in_projwbs_probe = False
    projwbs_headers: List[str] = []
    for line in lines:
        fields = line.split("\t")
        tag = fields[0] if fields else ""
        if tag == "%T":
            in_projwbs_probe = (
                len(fields) >= 2 and fields[1].strip() == "PROJWBS"
            )
            continue
        if in_projwbs_probe and tag == "%F":
            projwbs_headers = [h.strip() for h in fields[1:]]
            break  # Only need the first `%F` inside PROJWBS to decide.

    missing = [
        c for c in _PROJWBS_REQUIRED_UNGUARDED_COLUMNS
        if c not in projwbs_headers
    ]
    if not missing:
        return path

    # Second pass — rewrite only the PROJWBS section.
    rewritten: List[str] = []
    in_projwbs = False
    augmented_headers: List[str] = []
    for line in lines:
        fields = line.split("\t")
        tag = fields[0] if fields else ""
        if tag == "%T":
            in_projwbs = (
                len(fields) >= 2 and fields[1].strip() == "PROJWBS"
            )
            rewritten.append(line)
            continue
        if in_projwbs and tag == "%F":
            existing = [h.strip() for h in fields[1:]]
            to_add = [
                c for c in _PROJWBS_REQUIRED_UNGUARDED_COLUMNS
                if c not in existing
            ]
            augmented_headers = existing + to_add
            rewritten.append("\t".join(["%F"] + augmented_headers))
            continue
        if in_projwbs and tag == "%R":
            values = fields[1:]
            # Right-pad so zip() in Reader produces values for every
            # column, not just the leading ones the fixture wrote.
            while len(values) < len(augmented_headers):
                values.append("")
            rewritten.append("\t".join(["%R"] + values))
            continue
        rewritten.append(line)

    final_text = "\n".join(rewritten)
    if original_text.endswith("\n"):
        final_text += "\n"

    # Write sanitized copy to a NamedTemporaryFile. `delete=False` so
    # Reader can re-open it on platforms that don't allow two concurrent
    # handles to a single NamedTemporaryFile (i.e., Windows). The
    # caller is responsible for `Path(...).unlink()` after Reader use.
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        errors="ignore",
        suffix=".xer",
        prefix="apex_xer_sanitized_",
        delete=False,
    )
    try:
        tmp.write(final_text)
    finally:
        tmp.close()
    return Path(tmp.name)


class ApexXerSource:
    """Normalized read-only view over a PyP6Xer Reader (or duck-typed stand-in).

    Usage:

        from xerparser.reader import Reader
        from app.schedule.xer_adapter import ApexXerSource

        reader = Reader(str(xer_path))
        source = ApexXerSource.from_reader(reader, xer_path=xer_path)

        for project in source.projects: ...
        for task    in source.tasks:    ...
        for wbs     in source.projwbs:  ...
        for rel     in source.taskpreds: ...
        for blink   in source.projbaselines: ...

    Attributes exposed are always iterable (may be empty lists). They are
    materialized lazily on first access so an unused collection costs
    nothing.

    The adapter deliberately exposes the *loader's logical names* — not
    the real parser names. That keeps every call site inside the loader
    stable under future parser upgrades: if PyP6Xer grows a real
    `projbaselines` surface, only this adapter needs to change.
    """

    def __init__(
        self,
        reader: Any,
        *,
        xer_path: Optional[Path] = None,
    ) -> None:
        self._reader = reader
        self._xer_path = Path(xer_path) if xer_path is not None else None
        self._cache: dict[str, List[Any]] = {}
        # Trace of which real attribute name (or `raw-section-shim`) was
        # selected for each logical name. Populated lazily; useful for
        # tests and handoff diagnostics.
        self._resolution: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_reader(
        cls,
        reader: Any,
        *,
        xer_path: Optional[Path] = None,
    ) -> "ApexXerSource":
        return cls(reader, xer_path=xer_path)

    @classmethod
    def from_xer_path(cls, xer_path: "Path | str") -> "ApexXerSource":
        """Construct an `ApexXerSource` directly from an XER file path.

        Packet UI-002g-host-followup-2 entry point. Applies the narrow
        PROJWBS column-completion shim (see
        `_sanitize_xer_for_pyp6xer()` above) so PyP6Xer 1.016.00's
        `Reader` class can survive construction against fixtures with
        minimal PROJWBS column sets (specifically the 020h sanitized
        golden fixture, whose `%F\\tPROJWBS` header deliberately omits
        OBS / GUID / EV / ANTICIPATED-DATE columns).

        The original fixture on disk is never modified. If the file
        already has every PyP6Xer-required column, no sanitization
        happens and the original path is handed to `Reader()` directly.
        Otherwise a sanitized copy is written to a tempfile, passed to
        `Reader()`, and unlinked once Reader construction returns.

        The returned `ApexXerSource` is constructed with the ORIGINAL
        `xer_path`, not the sanitized tempfile. This keeps the
        `parse_baseline_rows_raw()` raw-section shim (item 2 of the
        module docstring) reading from the admitted fixture, which is
        the truthful surface for PROJBASELINE/BASELINEPROJECT rows.

        Use this classmethod from the loader (and any host-side entry
        point that constructs a Reader from a file). Use
        `from_reader()` directly only when you already have a Reader
        instance (e.g., unit tests that substitute a fake).
        """
        path = Path(xer_path)
        # Deferred import keeps the adapter importable in sandbox tests
        # that never actually construct a real Reader. We resolve Reader
        # through two lookup paths, in order:
        #
        #   1. `xerparser.Reader` — does NOT exist in PyP6Xer 1.016.00
        #      natively, but is the attribute the 020g-a tests create via
        #      `monkeypatch.setattr(xerparser, "Reader", _factory,
        #      raising=False)` to inject a duck-typed Reader. Checking
        #      this path first preserves existing test semantics without
        #      requiring a single test edit.
        #   2. `xerparser.reader.Reader` — the real canonical location
        #      of the Reader class in PyP6Xer 1.016.00. Production code
        #      (and host bootstrap) always lands here.
        #
        # The fallback is explicit rather than try/except so the control
        # flow remains readable and the test-path vs production-path
        # split is visible from source alone.
        import xerparser  # type: ignore
        Reader = getattr(xerparser, "Reader", None)
        if Reader is None:
            from xerparser.reader import Reader  # type: ignore

        sanitized = _sanitize_xer_for_pyp6xer(path)
        try:
            reader = Reader(str(sanitized))
        finally:
            # Clean up the tempfile if sanitization actually produced one.
            # `sanitized == path` when no sanitization was needed.
            if sanitized != path:
                try:
                    sanitized.unlink()
                except OSError:
                    pass
        return cls.from_reader(reader, xer_path=path)

    # ------------------------------------------------------------------
    # Logical-surface properties — the ONLY names the loader should use
    # ------------------------------------------------------------------

    @property
    def projects(self) -> List[Any]:
        return self._collection_for("projects")

    @property
    def tasks(self) -> List[Any]:
        return self._collection_for("tasks")

    @property
    def projwbs(self) -> List[Any]:
        return self._collection_for("projwbs")

    @property
    def taskpreds(self) -> List[Any]:
        return self._collection_for("taskpreds")

    @property
    def projbaselines(self) -> List[Any]:
        """Baseline-linkage rows (`PROJBASELINE` / `BASELINEPROJECT`).

        Resolution order:
          1. a real collection attribute on the underlying reader
             (future-proof — a PyP6Xer upgrade could grow one),
          2. the raw-section shim, which re-reads the XER file directly
             for `%T\\tPROJBASELINE` / `%T\\tBASELINEPROJECT` rows.

        When neither source produces rows, the empty list is returned;
        the loader then emits zero baselines, honoring the 020b §5 /
        020d §2.1 no-fabrication rule.
        """
        if "projbaselines" in self._cache:
            return self._cache["projbaselines"]

        rows = self._try_reader_aliases("projbaselines")
        if rows:
            self._resolution["projbaselines"] = "reader-attribute"
            self._cache["projbaselines"] = rows
            return rows

        # Fall back to the raw-section shim. This is the narrow scope
        # authorized by 020g-a scope item 2.
        if self._xer_path is not None:
            shim_rows = parse_baseline_rows_raw(self._xer_path)
            if shim_rows:
                self._resolution["projbaselines"] = "raw-section-shim"
                self._cache["projbaselines"] = shim_rows
                return shim_rows

        self._resolution["projbaselines"] = "empty"
        self._cache["projbaselines"] = []
        return []

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def resolution_trace(self) -> dict[str, str]:
        """Return which real attribute (or `raw-section-shim` / `empty`)
        each logical surface resolved to. Populated lazily — only
        surfaces that have been accessed appear in the trace."""
        # Prime all logical names so the trace is complete for callers
        # that just want to see the full resolution map.
        for logical_name, _ in _ATTRIBUTE_ALIASES:
            _ = getattr(self, logical_name)
        return dict(self._resolution)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _collection_for(self, logical_name: str) -> List[Any]:
        if logical_name in self._cache:
            return self._cache[logical_name]
        rows = self._try_reader_aliases(logical_name)
        self._cache[logical_name] = rows
        return rows

    def _try_reader_aliases(self, logical_name: str) -> List[Any]:
        aliases = _aliases_for(logical_name)
        for real_name in aliases:
            if not hasattr(self._reader, real_name):
                continue
            value = getattr(self._reader, real_name)
            if value is None:
                continue
            try:
                rows = list(value)
            except TypeError:
                # Not iterable; skip and keep probing.
                continue
            if rows:
                self._resolution[logical_name] = real_name
                return rows
        self._resolution.setdefault(logical_name, "empty")
        return []


def _aliases_for(logical_name: str) -> Tuple[str, ...]:
    for name, aliases in _ATTRIBUTE_ALIASES:
        if name == logical_name:
            return aliases
    raise KeyError(
        f"unknown logical surface {logical_name!r}; must be one of: "
        f"{tuple(name for name, _ in _ATTRIBUTE_ALIASES)}"
    )


# ---------------------------------------------------------------------------
# Raw-section shim for PROJBASELINE / BASELINEPROJECT
#
# The scanner reads the XER file directly using the same decode/delimiter
# rules PyP6Xer uses (codecs.open utf-8 errors='ignore', tab-delimited
# CSV, `%T` / `%F` / `%R` directives). It intentionally ignores every
# other `%T` section — those remain the PyP6Xer Reader's responsibility.
# ---------------------------------------------------------------------------

def parse_baseline_rows_raw(xer_path: Path) -> List[SimpleNamespace]:
    """Return PROJBASELINE / BASELINEPROJECT rows as attribute-bearing
    namespace objects.

    Each returned row carries whatever columns the XER's `%F` header line
    declared, using `P6 column names` directly (e.g. `proj_id`,
    `base_proj_id`, `base_type_name`, `last_update_date`). Missing
    columns surface as `None`.

    The loader's `_build_xer_baseline_entries()` already uses
    `_get_first_attr(row, "base_proj_id", "baseline_proj_id")` etc., so
    namespace attributes are the shape it expects — no further
    translation is performed here.

    A file with no baseline section returns `[]`. A file whose baseline
    section is present but empty also returns `[]`.
    """
    path = Path(xer_path)
    if not path.is_file():
        return []

    rows: List[SimpleNamespace] = []

    with codecs.open(str(path), encoding="utf-8", errors="ignore") as fh:
        stream = csv.reader(fh, delimiter="\t")
        current_table: Optional[str] = None
        current_headers: List[str] = []
        for record in stream:
            if not record:
                continue
            tag = record[0]
            if tag == "%T":
                if len(record) >= 2:
                    current_table = record[1].strip()
                    current_headers = []
                else:
                    current_table = None
                    current_headers = []
                continue
            # Only parse headers / rows while we're inside a baseline section.
            if current_table not in _BASELINE_SECTION_NAMES:
                continue
            if tag == "%F":
                current_headers = [h.strip() for h in record[1:]]
                continue
            if tag == "%R":
                values = record[1:]
                pairs = dict(zip(current_headers, values))
                rows.append(_normalize_baseline_row(pairs))
                continue

    return rows


def _normalize_baseline_row(pairs: dict[str, Any]) -> SimpleNamespace:
    """Return a namespace carrying the raw P6 columns plus lightly-typed
    aliases the loader's `_get_first_attr()` may probe.

    We intentionally do NOT invent fields. If `proj_id` is missing, it is
    present as `None`. The loader's validator still fails closed (via
    `_validate_baseline_entry`) when a baseline entry would end up
    missing a required field, preserving the 020c §3.2 contract.
    """
    def _opt(name: str) -> Optional[str]:
        v = pairs.get(name)
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    ns = SimpleNamespace(
        # Primary P6 column names (what the loader's `_build_xer_baseline_entries`
        # probes via `_get_first_attr` / `_stringify`).
        proj_id          = _opt("proj_id"),
        base_proj_id     = _opt("base_proj_id"),
        # Synonym the 020d compatibility layer already looks for.
        baseline_proj_id = _opt("base_proj_id"),
        # Human-readable label → propagates to schedule.baseline_events.baseline_name.
        base_type_name   = _opt("base_type_name"),
        last_update_date = _opt("last_update_date"),
    )
    # Also expose every original column under its raw name, so future
    # loader probes (e.g. `base_proj_short_name`) find it without
    # another adapter edit.
    for raw_key, raw_val in pairs.items():
        if not raw_key:
            continue
        key = raw_key.strip()
        if not key or hasattr(ns, key):
            continue
        setattr(ns, key, _opt(raw_key))
    return ns


# ---------------------------------------------------------------------------
# Convenience: probe a raw XER file for its `%T` section names without
# fully parsing. Used by tests and runbook diagnostics.
# ---------------------------------------------------------------------------

def scan_xer_section_names(xer_path: Path) -> List[str]:
    """Return the list of `%T`-headed section names present in the file,
    in the order they first appear. Read-only, best-effort, ignoring
    decode errors the same way PyP6Xer does."""
    path = Path(xer_path)
    if not path.is_file():
        return []
    seen: List[str] = []
    with codecs.open(str(path), encoding="utf-8", errors="ignore") as fh:
        stream = csv.reader(fh, delimiter="\t")
        for record in stream:
            if record and record[0] == "%T" and len(record) >= 2:
                name = record[1].strip()
                if name and name not in seen:
                    seen.append(name)
    return seen


__all__ = (
    "ApexXerSource",
    "parse_baseline_rows_raw",
    "scan_xer_section_names",
    # Exposed for diagnostics + tests only; loader code should not read these.
    "_ATTRIBUTE_ALIASES",
    "_BASELINE_SECTION_NAMES",
    "_PROJWBS_REQUIRED_UNGUARDED_COLUMNS",
    "_sanitize_xer_for_pyp6xer",
)
