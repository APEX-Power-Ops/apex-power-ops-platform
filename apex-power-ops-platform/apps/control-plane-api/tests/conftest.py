from pathlib import Path
import sys


APP_ROOT = Path(__file__).resolve().parents[1]
CALC_PACKAGE_SRC = APP_ROOT.parents[1] / "packages" / "calc-engine" / "src"

for candidate in (APP_ROOT, CALC_PACKAGE_SRC):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)
