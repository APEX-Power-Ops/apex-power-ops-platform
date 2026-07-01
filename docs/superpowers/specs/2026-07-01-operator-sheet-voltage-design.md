# Operator Sheet-Voltage Assertion - Design

**Status:** Ratified (operator, 2026-07-01) - both decisions + sheet lists. Additive two-repo feature.
**Lanes:** estimator-takeoff worktree `/home/olares/code/apex/apex-sheetvolt` (branch `estimator-takeoff/sheet-voltage` off main `50d21daa`) + drawing-nav `master @ eff8a55` (local tool).

## Goal
Let the operator attest a whole one-line sheet's LV bus voltage in ONE assertion, pricing tagged AND tagless breaker rows on that sheet - the honest, durable form of the block-voltage move. Replaces the `busVoltageV` injection hack, which mislabels an operator assumption as machine-`detected`.

## Ratified decisions
- **Precedence: tag-assert > detected > sheet-assert.** Sheet-voltage fills ONLY rows with no per-tag assertion and no detected voltage; it never overrides a detected bus voltage or a per-tag assertion (so E01-24..27's detected 480 is untouched). No sheet-vs-detected conflict finding (sheet defers).
- **Provenance: `voltageBasis='asserted'` + assertion `source='operator_sheet_voltage'` + a reconciliation WARNING finding** surfacing the assumption. NO new `VoltageBasis` enum value (extra blast radius for little value).
- **Sheet lists (operator attestation): A E01-05..E01-12, B E01-05..E01-09 = 480V LV. E01-01..E01-04 excluded (MV/mixed one-lines).**

## Changes

### estimator-takeoff (governed engine)
1. `src/extraction/types.ts VoltageAssertion`: add `sheets?: string[]`; extend `source` to `'cli' | 'gate1' | 'operator_sheet_voltage'`. `tags` may be empty IFF `sheets` is non-empty.
2. `src/extraction/parse.ts validateAssertionShape`: require `voltageV` number; `tags` must be `string[]` (may be empty); `sheets` must be `string[]` or undefined; at least one of tags/sheets non-empty (else fail).
3. `src/buckets/types.ts VoltageAssertionCode` += `'voltage_assertion_unknown_sheet'`, `'voltage_assertion_sheet_conflict'`, `'voltage_assertion_sheet_applied'`.
4. `src/signature/voltage-assertions.ts applyVoltageAssertions`:
   - Collect sheet pairs from assertions carrying `sheets` (voltageV positive int, else existing `invalid_voltage` error path).
   - Group by sheet; a sheet with >1 distinct asserted voltage -> `voltage_assertion_sheet_conflict` error + taint that sheet (excluded).
   - A sheet not present in any `apparatus.sheet` -> `voltage_assertion_unknown_sheet` error.
   - In the per-apparatus resolve, AFTER tag-effective and the detected check: for a row with no effective tag assertion AND `busVoltageV === undefined` AND its `sheet` in the sheet-effective map -> set `busVoltageV = sheetV`, `voltageBasis = 'asserted'`. (Strict precedence tag > detected > sheet.)
   - Emit ONE `'warning'` `voltage_assertion_sheet_applied` finding per applied sheet group: "N row(s) priced under operator sheet-voltage assumption (sheets: [...], <V>V; source operator_sheet_voltage)".
5. Existing tag-assertion behavior (taint/duplicate/unknown/conflict, operator-wins-over-detected with warning) is UNCHANGED.

### drawing-nav (producer, local tool)
6. `extract --assert-sheet-voltage V:SHEET[,SHEET...]` (repeatable) -> `parse_sheet_voltage_assertions` -> append `{voltageV, tags: [], sheets: [...], source: 'operator_sheet_voltage', actor?, note?}` to `art["voltageAssertions"]` (merged with any `--assert-voltage` tag assertions). Existing `--assert-voltage` untouched.

## Tests (TDD)
- Engine: (a) sheet fills an undetected + untagged row -> busVoltageV set, basis 'asserted'; (b) detected voltage on a sheet-asserted sheet WINS (row stays basis 'detected', no override); (c) a per-tag assertion WINS over a sheet assertion for the same row; (d) unknown sheet -> `voltage_assertion_unknown_sheet` error; (e) conflicting sheet voltage -> `voltage_assertion_sheet_conflict` + taint; (f) `voltage_assertion_sheet_applied` warning surfaced with the right count; (g) assertion with empty tags AND empty/absent sheets -> `voltage_assertion_invalid_shape` (engine) / fail (parse); (h) tag-only regression: existing tag assertions behave identically.
- parse.ts: sheet-only assertion parses; tags-only unchanged; neither non-empty -> fail.
- drawing-nav: `--assert-sheet-voltage 480:E01-05,E01-06` writes `{voltageV:480, tags:[], sheets:['E01-05','E01-06'], source:'operator_sheet_voltage'}`; `--assert-voltage` unchanged; combining both merges.
- Full suite: 5 family goldens + E01-11 byte-identical (additive); ASCII-only.

## Constraints
ASCII-only authored code/comments/strings; additive (all existing paths unchanged); 5 family goldens + E01-11 byte-identical; Codex + opus IRP mandatory; merge OPERATOR-GATED (engine -> main, drawing-nav -> master).

## Then (produce the honest number)
drawing-nav re-extract A/B with `--assert-sheet-voltage 480:E01-05,E01-06,E01-07,E01-08,E01-09,E01-10,E01-11,E01-12` (A) and `480:E01-05,E01-06,E01-07,E01-08,E01-09` (B); run `run-artifact --allow-open-items`; report as "LV breaker partial preview with operator sheet-voltage assertions" (~$207k), the sheet-applied warning visible, MV E01-01..04 deferred, the frameless panelboard-MCB edge footnoted.
