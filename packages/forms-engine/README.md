# Apex Forms Engine

This package is the first bounded `forms-engine` import pilot into the unified Apex platform repo.

Current posture:
- imported from the approved engine-core scope in `NETA-Forms`
- limited to reusable generation logic and JSON schema assets
- intentionally excludes broad template trees, brand-asset source libraries, forms app-shell work, and forms-domain database integration

Included in this pilot:
- AHA PDF generator and activity data
- MOP Word/Excel generator scripts
- PSS fillable-requirements generator
- MOP JSON schema assets

Package layout:
- `src/apex_forms_engine/aha/` for AHA generation logic and activity data
- `src/apex_forms_engine/generators/` for document generators
- `src/apex_forms_engine/schemas/` for JSON schema assets
- `src/apex_forms_engine/artifacts/` for generated output during local runs

Deferred for later planning:
- app-shell work in `apps/forms-studio`
- broad template import and deduplication
- brand-asset normalization and storage governance
- forms-domain database and service contracts

Local runtime use:
- install the package in editable mode from `packages/forms-engine` with `python -m pip install -e .`
- run the package smoke validation with `apex-forms-smoke`
- from the Olares-hosted platform root, run the same bounded smoke path with `.venv/bin/python -m apex_forms_engine.smoke` and `PYTHONPATH=packages/forms-engine/src`
- Windows client fallback: run the same bounded smoke path with `C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe -m apex_forms_engine.smoke` and `PYTHONPATH=packages/forms-engine/src`
- run the root workspace task `Forms engine tests` for an executable regression check around the smoke harness
- run the root workspace task `Forms engine CI check` to mirror the package CI contract locally through `compileall` plus focused pytest
- repo-level CI now runs the same package regression slice through `.github/workflows/forms-engine-ci.yml`
- generated outputs land in `src/apex_forms_engine/artifacts/`
- generated smoke outputs in `src/apex_forms_engine/artifacts/` are intentionally gitignored so the validation path does not dirty the workspace
- use the root workspace task `Forms engine clean artifacts` when you want to remove regenerated local outputs after inspection

Current smoke surface:
- `MOP_Work_Script_Template.xlsx`
- `MOP_Cover_Page_Template.docx`
- `MOP_Scope_Controls_Template.docx`
- `MOP_Completion_Template.docx`
- `PSS_Data_Requirements_Fillable.pdf`
- `AHA-Blank-Master.pdf`
- `AHA-CW-BDC-Mech_A_SWBD-Load_Monitor_Installation.pdf`

Current known runtime note:
- the PSS fillable-requirements verification readback currently emits non-fatal `pypdf` duplicate-font warnings during smoke runs, but the artifacts are produced successfully