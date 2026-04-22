import importlib
import sys
from pathlib import Path

from apex_forms_engine import smoke


EXPECTED_ARTIFACTS = [
    smoke.ARTIFACTS_DIR / "MOP_Work_Script_Template.xlsx",
    smoke.ARTIFACTS_DIR / "MOP_Cover_Page_Template.docx",
    smoke.ARTIFACTS_DIR / "MOP_Scope_Controls_Template.docx",
    smoke.ARTIFACTS_DIR / "MOP_Completion_Template.docx",
    smoke.ARTIFACTS_DIR / "PSS_Data_Requirements_Fillable.pdf",
    smoke.ARTIFACTS_DIR / "AHA-Blank-Master.pdf",
    smoke.ARTIFACTS_DIR / "AHA-CW-BDC-Mech_A_SWBD-Load_Monitor_Installation.pdf",
]


def _remove_expected_artifacts() -> None:
    for path in EXPECTED_ARTIFACTS:
        if path.exists():
            path.unlink()


def test_forms_engine_smoke_generates_expected_artifacts() -> None:
    _remove_expected_artifacts()

    try:
        assert smoke.main() == 0

        for path in EXPECTED_ARTIFACTS:
            assert path.exists(), f"Expected smoke artifact missing: {path.name}"
            assert path.stat().st_size > 0, f"Expected smoke artifact to be non-empty: {path.name}"
    finally:
        _remove_expected_artifacts()


def test_pss_generator_import_has_no_artifact_side_effects() -> None:
    pss_output = smoke.ARTIFACTS_DIR / "PSS_Data_Requirements_Fillable.pdf"
    if pss_output.exists():
        pss_output.unlink()

    sys.modules.pop("apex_forms_engine.generators.build_fillable_requirements", None)
    importlib.import_module("apex_forms_engine.generators.build_fillable_requirements")

    assert not pss_output.exists(), "Importing the PSS generator should not write artifacts"