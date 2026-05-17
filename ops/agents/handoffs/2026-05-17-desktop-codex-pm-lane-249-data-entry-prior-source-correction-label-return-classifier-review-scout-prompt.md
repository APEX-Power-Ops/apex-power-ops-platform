# Desktop Codex Prompt - PM Lane 249 Data Entry Prior Source-Correction Label Return Classifier Review Scout

Date: 2026-05-17

## Assignment

Review PM Lane 249 as a read-only scout.

The lane classifies `REQUEST_SOURCE_CORRECTION_NO_LIVE` as an already-applied Ground Resistance source-correction label, not a valid PM Lane 238 Data Entry warning disposition.

## Review Questions

1. Does the packet clearly state that `REQUEST_SOURCE_CORRECTION_NO_LIVE` already belongs to the PM Lane 236 `Ground Resistance Test Lot` correction?
2. Does it avoid implying that the active `PROJECT_DATA_ENTRY_FORMULA_ERRORS` warning is accepted, corrected, or closed?
3. Does it preserve the requirement for exactly one PM Lane 238 Data Entry label?
4. Does it avoid creating any live approval/import/source-write authority?

## Guardrails

Do not edit product code. Do not stage, commit, or push. Do not access hosted services. Do not read workbook or source PDF contents. Do not run macros. Do not accept the warning. Do not approve the candidate. Do not create approval/import/field/customer/production/finance/business-state records. Return findings only.
