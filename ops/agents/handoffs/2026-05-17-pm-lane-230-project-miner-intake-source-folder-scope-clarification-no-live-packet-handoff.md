# PM Lane 230 Handoff - Project Miner Intake Source Folder Scope Clarification No-Live Packet

Date: 2026-05-17

## Objective

Record Jason's clarification that current folder contents in the Project Miner PM Planning folder are expected project intake sources except two excluded planning/import workbooks.

## Decision Label

`PROJECT_MINER_INTAKE_SOURCE_FOLDER_SCOPE_CLARIFICATION_NO_LIVE_METADATA_ONLY_NO_CONTENT_READ_NO_WRITE`

## Selected Outcome

`SOURCE_FOLDER_CONFIRMED_EXCLUDE_MASTER_AND_GARNEY_TRACKER_METADATA_ONLY_BUILDING_A_LV_POSSIBLE_FUTURE_SCOPE`

## Current Expected Intake Sources

Metadata-only source set:

1. `15_ELECTRICAL_COMBINED.pdf`
2. `Building B IFC.pdf`
3. `Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm`
4. `EQUIPMENT INVENTORY - 2026.xlsx`
5. `Estimator R3 - Project Miner Temp Power Testing.xlsm`
6. `Miner Temp SLD-AP-BCARRASCO.pdf`
7. `Phx Tech Testing Capability Matrix 032726.xlsx`

Excluded from current intake source set:

1. `RESA Power - Project Data Entry MASTER.xlsm`
2. `Garney- Central Mesa Reuse Tracker #677562.xlsm`

## Scope Notes

1. Building A low-voltage work may become additional future scope.
2. Building A low-voltage is not currently awarded or admitted as executable scope.
3. Any Building A low-voltage review, import, proposal, field plan, or customer commitment needs later scope confirmation and separate packet admission.

## Required Work

1. Record the folder-level source clarification.
2. Keep the expected source set metadata-only.
3. Keep excluded workbooks as planning/reference surfaces, not current intake sources.
4. Keep Building A low-voltage parked until award/scope confirmation.
5. Keep content review blocked until explicit content-review admission.

## Guardrails

Do not:

1. open workbook worksheets,
2. inspect formulas or tables,
3. run macros,
4. write back to workbooks,
5. read PDF page contents,
6. create durable fingerprints,
7. promote source truth beyond metadata-only candidate status,
8. dispatch Desktop Codex for Project Miner source classification,
9. access hosted services or credentials,
10. run approval POSTs,
11. create approval rows,
12. import a project,
13. create tasks, owners, due dates, assignments, or issues,
14. issue field direction,
15. create customer commitments,
16. create production or finance outputs,
17. mutate PM business state.

## Next Input Required

Ask Jason:

```text
May Codex perform a bounded local content review of the current expected intake source set?

Current expected intake sources:
1. 15_ELECTRICAL_COMBINED.pdf
2. Building B IFC.pdf
3. Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm
4. EQUIPMENT INVENTORY - 2026.xlsx
5. Estimator R3 - Project Miner Temp Power Testing.xlsm
6. Miner Temp SLD-AP-BCARRASCO.pdf
7. Phx Tech Testing Capability Matrix 032726.xlsx

Excluded:
1. RESA Power - Project Data Entry MASTER.xlsm
2. Garney- Central Mesa Reuse Tracker #677562.xlsm

Allowed review if approved:
- read workbook/PDF contents locally,
- do not run macros,
- do not write back,
- do not import,
- do not create tasks/owners/dates/field direction/customer commitments,
- produce only a source map and exception list.
```

Also ask:

```text
Should possible Building A low-voltage scope remain parked until award/scope confirmation?
```

## Validation

Required checks:

1. Packet JSON parse.
2. Guardrail search across touched Lane 230 files.
3. Corrupted-token scan.
4. Null-byte check.
5. `git diff --check`.
6. Staged-file check before commit.
