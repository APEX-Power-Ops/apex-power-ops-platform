"""Real-subprocess regressions for the interpreter contract (RI2 findings 1 + 3).

The P0-A CLIs are launched from an injected child that already holds the production
DSN. An executable ``.pth`` file in the interpreter's site-packages (Python has an
editable-install one) runs during ``site`` startup — BEFORE the script's preamble,
governance guards, or target binding. ``python -I`` does NOT close this: ``-I`` implies
``-s`` (no user site) and ``-E``/``-P`` (no PYTHONPATH / no unsafe sys.path[0]) but NOT
``-S``, so ``site`` still runs and still executes ``.pth`` lines. Only ``-S`` (no_site)
suppresses that.

These tests build a throwaway venv with a sentinel ``.pth`` that records whether it ran
and what environment it saw, then launch each CLI under it:

* under the required ``-I -S`` the sentinel NEVER runs and never sees the injected secret;
* under ``-I`` alone the CLI is REFUSED fail-closed (``interpreter_not_isolated_no_site``)
  — and the sentinel demonstrably DID run with the secret visible, proving ``-S`` (not
  ``-I``) is the load-bearing control.

No database or network. Runnable under pytest OR directly:

    python tests/test_interpreter_contract.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import venv
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1]  # .../pm_ops_p0
PRESERVE = PKG_DIR / "preserve_evidence.py"
FINALIZE = PKG_DIR / "finalize_closeout.py"

# a marker the injected secret would land in if the sentinel .pth executes
_INJECTED_SECRET = "PROD_SECRET_dc0ffee"
_FAKE_DSN = f"postgresql://u:{_INJECTED_SECRET}@db.example/db"


def _make_venv_with_sentinel(root: Path) -> tuple[Path, Path]:
    """Create a throwaway venv whose site-packages holds an executable sentinel .pth.

    The .pth (a single ``import ...`` line, the form ``site`` executes) writes the
    marker file, recording the injected DSN it observed. Returns (python, marker_path).
    """
    venv.create(root / "venv", with_pip=False)
    python = root / "venv" / "bin" / "python"
    if not python.exists():  # pragma: no cover - non-POSIX layout
        python = root / "venv" / "Scripts" / "python.exe"
    site_packages = next((root / "venv" / "lib").glob("python*/site-packages"))
    marker = root / "SENTINEL_RAN"
    # one physical line; reads os.environ so a "did it see the secret" assertion is possible
    (site_packages / "zzz_sentinel.pth").write_text(
        "import os, pathlib; "
        f"pathlib.Path({str(marker)!r}).write_text('ran secret=' + "
        "os.environ.get('FAKE_DSN', '<unset>'))\n"
    )
    return python, marker


def _run(python: Path, flags: list[str], script: Path) -> subprocess.CompletedProcess:
    # `--help` exits 0 AFTER the __main__ interpreter gate passes; under a refused
    # interpreter the gate exits 1 before argparse ever sees --help.
    return subprocess.run(
        [str(python), *flags, str(script), "--help"],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "FAKE_DSN": _FAKE_DSN},
    )


def _assert_cli_interpreter_contract(script: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="p0a-interp-") as d:
        root = Path(d)
        python, marker = _make_venv_with_sentinel(root)

        # (1) correct invocation `-I -S`: site is off, so the sentinel .pth NEVER runs
        # and never observes the injected secret; the gate passes and --help exits 0.
        marker.unlink(missing_ok=True)
        r = _run(python, ["-I", "-S"], script)
        assert r.returncode == 0, (script.name, r.returncode, r.stdout, r.stderr)
        assert not marker.exists(), f"{script.name}: sentinel .pth executed under -I -S"

        # (2) misinvocation `-I` only (no -S): the CLI REFUSES fail-closed, and the
        # sentinel demonstrably RAN at startup with the secret visible — the exact
        # pre-guard execution window `-S` closes (RI2 finding 1).
        marker.unlink(missing_ok=True)
        r = _run(python, ["-I"], script)
        assert r.returncode == 1, (script.name, r.returncode, r.stdout, r.stderr)
        assert "interpreter_not_isolated_no_site" in r.stdout, (script.name, r.stdout)
        assert marker.exists(), f"{script.name}: sentinel should run under -I (site on)"
        assert _INJECTED_SECRET in marker.read_text(), (
            f"{script.name}: sentinel under -I saw the injected secret (vuln -S closes)"
        )


def test_preserve_evidence_cli_interpreter_contract():
    _assert_cli_interpreter_contract(PRESERVE)


def test_finalize_closeout_cli_interpreter_contract():
    _assert_cli_interpreter_contract(FINALIZE)


# ------------------------------------------------------------------- runner


def _run_all() -> int:
    funcs = [
        v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)
    ]
    failures = 0
    for fn in funcs:
        try:
            fn()
            print(f"[PASS] {fn.__name__}")
        except Exception as exc:  # noqa: BLE001 - test runner
            failures += 1
            print(f"[FAIL] {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(funcs) - failures}/{len(funcs)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run_all())
