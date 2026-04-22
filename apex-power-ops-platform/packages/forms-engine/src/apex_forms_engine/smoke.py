"""Package-local smoke validation for the bounded forms-engine import."""

from __future__ import annotations

from pathlib import Path

from apex_forms_engine.aha.aha_data.load_monitor import ACTIVITY as LOAD_MONITOR_ACTIVITY
from apex_forms_engine.aha.aha_generator import generate_aha
from apex_forms_engine.generators.build_fillable_requirements import build_fillable_requirements
from apex_forms_engine.generators.generate_completion_docx import build_document as build_completion_document
from apex_forms_engine.generators.generate_mop_cover_docx import build_document
from apex_forms_engine.generators.generate_scope_controls_docx import build_document as build_scope_controls_document
from apex_forms_engine.generators.generate_work_script_xlsx import build_workbook


ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def _artifact_size_kb(path: Path) -> str:
    return f"{path.stat().st_size / 1024:.1f} KB"


def main() -> int:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    build_workbook()
    build_document()
    build_scope_controls_document()
    build_completion_document()
    build_fillable_requirements()
    generate_aha()
    generate_aha(LOAD_MONITOR_ACTIVITY)

    expected = [
        ARTIFACTS_DIR / "MOP_Work_Script_Template.xlsx",
        ARTIFACTS_DIR / "MOP_Cover_Page_Template.docx",
        ARTIFACTS_DIR / "MOP_Scope_Controls_Template.docx",
        ARTIFACTS_DIR / "MOP_Completion_Template.docx",
        ARTIFACTS_DIR / "PSS_Data_Requirements_Fillable.pdf",
        ARTIFACTS_DIR / "AHA-Blank-Master.pdf",
        ARTIFACTS_DIR / "AHA-CW-BDC-Mech_A_SWBD-Load_Monitor_Installation.pdf",
    ]

    missing = [path.name for path in expected if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Smoke validation missing expected artifacts: {', '.join(missing)}")

    print("forms-engine smoke validation complete")
    for path in expected:
        print(f"- {path.name} ({_artifact_size_kb(path)})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())