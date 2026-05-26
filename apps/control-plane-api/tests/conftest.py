from pathlib import Path
import sys

import pytest


APP_ROOT = Path(__file__).resolve().parents[1]
CALC_PACKAGE_SRC = APP_ROOT.parents[1] / "packages" / "calc-engine" / "src"

for candidate in (APP_ROOT, CALC_PACKAGE_SRC):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Treat filename-suffixed integration modules as opt-in integration tests."""
    for item in items:
        item_path = Path(str(getattr(item, "path", getattr(item, "fspath", ""))))
        if item_path.name.endswith("_integration.py"):
            item.add_marker(pytest.mark.integration)
