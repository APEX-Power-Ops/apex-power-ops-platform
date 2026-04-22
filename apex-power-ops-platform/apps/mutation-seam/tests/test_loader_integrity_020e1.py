"""
Packet 020e.1 — Loader Working-Copy Restoration And Integrity Gate

These tests are the minimum integrity gate declared by packet 020e.1.

Why this gate exists
--------------------
Packet 020f surfaced that `apps/mutation-seam/app/schedule/loader.py` was
present on disk but silently truncated mid-`upsert_baselines()` — the
file ended inside an unterminated triple-quoted SQL string. A stale
`__pycache__` entry could still satisfy `import app.schedule.loader`,
which meant any packet that claimed "loader tests are green" by running
pytest against an already-imported module could ship against a broken
working copy. The 020f handoff records this as the specific failure
mode future packets must not be allowed to repeat.

This file adds the minimum assertion needed to close that gap:

    1. The source file on disk parses cleanly via `ast.parse()` from
       bytes, so stale bytecode cannot mask a broken working copy.

    2. The restored public surface that packet 020c / 020d / 020f depend
       on is present as top-level definitions in the AST (not just
       importable — importable is satisfied by stale bytecode).

    3. The tail of the file contains a resolved `if __name__ == "__main__"`
       guard, so a future truncation that lops off the CLI epilogue will
       fail this gate before any test suite declares victory.

These checks are infrastructure-free: they do not import the loader, do
not require `psycopg2`, do not require `xerparser`, and do not require
FastAPI. They can run in any environment where the repo checkout is
readable.

Running:

    cd apps/mutation-seam
    python -m pytest tests/test_loader_integrity_020e1.py -v --noconftest
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest


MUTATION_SEAM_ROOT = Path(__file__).resolve().parents[1]
LOADER_PATH = MUTATION_SEAM_ROOT / "app" / "schedule" / "loader.py"


def _loader_source() -> str:
    assert LOADER_PATH.is_file(), (
        f"loader.py must exist at {LOADER_PATH!s}; a missing loader cannot be "
        "parse-checked and any packet depending on this gate is invalid"
    )
    return LOADER_PATH.read_text(encoding="utf-8")


def _loader_tree() -> ast.Module:
    return ast.parse(_loader_source())


# ---------------------------------------------------------------------------
# Gate 1 — the file on disk parses cleanly
# ---------------------------------------------------------------------------

def test_loader_source_parses_cleanly():
    """Source must `ast.parse()` — this catches the 020f truncation class
    (unterminated triple-quoted string) independently of stale bytecode."""
    src = _loader_source()
    try:
        ast.parse(src)
    except SyntaxError as e:  # pragma: no cover — this is the gate
        pytest.fail(
            f"loader.py failed ast.parse: {type(e).__name__}: {e}. "
            "A truncated or syntactically broken loader.py cannot be the "
            "basis for any packet's green-test claim. Restore the working "
            "copy before re-running packet tests."
        )


# ---------------------------------------------------------------------------
# Gate 2 — the public surface packet 020c / 020d / 020f depend on is present
# in the AST, not just importable (importable is satisfied by stale bytecode)
# ---------------------------------------------------------------------------

_REQUIRED_TOP_LEVEL_DEFS = {
    "translate_xer_status",          # UI-002a status translation
    "load_json_source",              # UI-002a JSON path
    "load_xer_source",               # 020d XER path
    "_build_xer_baseline_entries",   # 020d baseline compatibility layer
    "resolve_source",                # precedence
    "upsert_projects",               # UI-002a lanes
    "upsert_wbs",
    "upsert_tasks",
    "upsert_relationships",
    "_validate_baseline_entry",      # 020c validation
    "upsert_baselines",              # 020c baseline lane
    "run_load",                      # UI-002a + 020c dry-run + persisted
}


@pytest.mark.parametrize("required_def", sorted(_REQUIRED_TOP_LEVEL_DEFS))
def test_loader_defines_required_top_level_function(required_def: str):
    tree = _loader_tree()
    defined = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert required_def in defined, (
        f"loader.py is missing required top-level function {required_def!r}. "
        f"Present top-level functions: {sorted(defined)}"
    )


def test_loader_allowed_baseline_sources_constant_present():
    """020c authorizes exactly three baseline sources. If the constant is
    missing or renamed, packet claims cannot rely on it."""
    tree = _loader_tree()
    names = {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert "_ALLOWED_BASELINE_SOURCES" in names, (
        "loader.py must define the _ALLOWED_BASELINE_SOURCES constant "
        "(020c §3.2); its absence means baseline source validation was "
        "lost during a restoration."
    )


# ---------------------------------------------------------------------------
# Gate 3 — the CLI epilogue is resolved; a tail-truncation cannot slip past
# ---------------------------------------------------------------------------

def test_loader_has_resolved_cli_epilogue():
    """The loader.py module is expected to end with an `if __name__ ==
    "__main__":` guard invoking `main()`. If a future edit lops off the
    epilogue, this test fails immediately — rather than masquerading as
    a successful import from stale bytecode."""
    tree = _loader_tree()
    # Look for the `if __name__ == "__main__":` pattern at module scope.
    found = False
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test_node = node.test
        if (
            isinstance(test_node, ast.Compare)
            and isinstance(test_node.left, ast.Name)
            and test_node.left.id == "__name__"
            and len(test_node.ops) == 1
            and isinstance(test_node.ops[0], ast.Eq)
        ):
            comp = test_node.comparators[0]
            if isinstance(comp, ast.Constant) and comp.value == "__main__":
                found = True
                break
    assert found, (
        "loader.py must end with an `if __name__ == \"__main__\":` guard. "
        "A missing CLI epilogue is the tail-truncation class that packet "
        "020f surfaced; this gate exists so no future packet can ship "
        "against a silently truncated working copy."
    )


# ---------------------------------------------------------------------------
# Gate 4 — cross-reference the stamped 020c / 020d / 020f comments so
# accidental whole-file replacement (not just tail truncation) is caught
# ---------------------------------------------------------------------------

def test_loader_retains_packet_provenance_comments():
    """The loader carries inline `packet 020c` / `packet 020d` / UI-002a
    provenance comments. If a restoration silently drops those, the
    behavior may be preserved but the justification trail is lost; this
    gate forces the trail to stay visible in source."""
    src = _loader_source()
    required_markers = [
        "packet UI-002a",
        "packet 020c",
    ]
    missing = [m for m in required_markers if m not in src]
    assert not missing, (
        f"loader.py lost provenance markers: {missing}. Any restoration "
        "must preserve the inline packet-ID comments so the behavior's "
        "authorizing packet remains discoverable from source alone."
    )
