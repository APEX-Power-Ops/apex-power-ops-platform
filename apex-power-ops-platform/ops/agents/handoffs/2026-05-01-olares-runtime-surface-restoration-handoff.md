# Olares Runtime Surface Restoration Handoff

Date: 2026-05-01
Status: Pass - missing bounded Olares workstation and rerun surfaces restored in the workspace snapshot
Authority: `docs/architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md`

## Purpose

This handoff records the bounded restoration of missing Olares workstation and
rerun surfaces that the post-closure checklist and roadmap still expected to be
present.

It does not reopen generic Olares expansion.

## Restored Surfaces

1. `packages/p6-ingest/` now exists as a real package-shaped lane with a bounded runtime contract and fixture summary contract
2. `packages/forms-engine/` now includes a bounded HTTP runtime shell for the MCP `apex-forms` bridge
3. `infra/compose.dev.yml` now restores the workstation-hosted dev stack definition for the bounded Olares shell
4. `infra/olares/forms-engine/` now carries the forms manifest plus bounded chart templates
5. `infra/olares/p6-ingest/` now carries the p6 manifest plus bounded chart templates
6. `tools/canary/run_canary.py` now refreshes the runtime-proof and staging outputs under `tests/canary/`
7. `tools/run-canary.ps1` and `tools/run-canary.sh` now restore the cross-platform workstation rerun wrapper surface
8. `tools/shell/common.ps1` and `tools/shell/common.sh` now restore the shared env-loading shell helpers expected by the canary wrapper
9. the missing rerun docs `OLARES-WORKSTATION-BRING-UP-CHECKLIST-2026-04-23.md`, `SERVICE-HOST-INSTALLED-PROOF-CHECKLIST-2026-04-23.md`, and `OLARES-FIRST-STORAGE-BRING-UP-RUNBOOK-2026-04-23.md` are present again as bounded rerun sources

## Validation Performed

1. focused `pytest` validation passed for `packages/p6-ingest/tests/test_contract.py`
2. focused `pytest` validation passed for `packages/forms-engine/tests/test_runtime.py`
3. `tools/run-canary.ps1` completed without error and refreshed the bounded runtime/staging canary outputs

## Result

The current workspace once again contains a bounded, executable Olares
workstation rerun surface instead of only post-closure narrative references and
committed canary artifacts.

The Olares lane remains post-closure and bounded:

1. use the restored rerun docs before authoring new first-run Olares material
2. use the restored canary wrapper and manifests as the current local evidence floor in this workspace snapshot
3. require a new explicit packet before onboarding any new Olares-managed app beyond `forms-engine` and `p6-ingest`
