# Lane 501 Reconciliation Strategy

## Strategy Summary

The R3 Miner Temp Power workbook still resolves as `flat_quote`, not `scope_sheets`. That means no explicit workbook-owned scope objects exist today.

The truthful scope-design surface is therefore:

1. preserve the extractor as the read-only source of line-item and apparatus-candidate truth
2. preserve the current production apparatus rows as the review target
3. derive proposed scopes from the already-present section-backed `seam.workpackages` rows
4. update only `seam.apparatus.scope_id` in Lane 502 after explicit admission

For the 2026-05-21 sample, the design generator found:

1. `184` extractor apparatus candidates
2. `184` existing apparatus rows
3. `184` confident matches
4. `0` unmatched existing rows
5. `0` unmatched extractor rows
6. `0` conflicts

## Matching Algorithm

Priority order:

1. `source_candidate_apparatus_id`
   Existing field: `seam.apparatus.data.source_candidate_apparatus_id`
   Extractor field: `expanded_apparatus_candidates[].candidate_id`
   Rationale: exact source-candidate identity survives from the Lane 278 import and is the strongest deterministic key.

2. `source_line_id + name`
   Existing fields: `seam.apparatus.data.source_line_id`, `seam.apparatus.data.name`
   Extractor fields: `expanded_apparatus_candidates[].line_id`, `display_name`
   Rationale: fallback when exact candidate id is missing but line identity and expanded apparatus display name still align.

3. `source_row + source_designation + source_apparatus_type + name`
   Existing fields: `source_row`, `source_designation`, `source_apparatus_type`, `name`
   Extractor fields: `source_row`, `designation`, `apparatus_type`, `display_name`
   Rationale: final deterministic fallback when the line id is absent but the expanded row-shape still matches.

Rejected as insufficient for confident matching:

1. `source_row + source_designation + source_apparatus_type`
   Reason: repeated-quantity rows collide because one workbook row expands into multiple apparatus candidates.

Tie-breaking rules:

1. If the highest-priority available key resolves to exactly one existing row, the candidate is `matched`.
2. If the same key resolves to more than one existing row, the candidate is `conflicting`.
3. If no key resolves to any existing row, the candidate is `unmatched_extractor`.
4. If an existing row is matched by more than one extractor candidate, both sides become `conflicting`.

Confidence levels:

1. `confident` means matched by `source_candidate_apparatus_id`.
2. `probable` means matched only by fallback key 2 or 3.
3. `none` means no existing row matched.

## Scope Derivation Strategy

Because the workbook has no active scope sheets, Lane 501 does not invent a new workbook-owned scope layer.

Instead, the contract derives proposed scopes from existing `seam.workpackages` rows that already carry:

1. `source_section`
2. `planned_hours`
3. `source_drawing_refs`
4. `source_candidate_workpackage_id`

Scope identifier rule:

1. Preserve the project prefix: `pm-import-project-miner-temp-power`
2. Preserve the workpackage numeric suffix
3. Emit `scope` instead of `wp`

Example:

1. `pm-import-project-miner-temp-power-wp-001` -> `pm-import-project-miner-temp-power-scope-001`

This gives Lane 502 a deterministic `scope_id` target without on-the-fly identifier computation.

## Outcome Categories

`matched`

1. Existing `seam.apparatus` row uniquely identified.
2. Lane 502 may `UPDATE seam.apparatus.scope_id` only.
3. No other apparatus column is touched.

`unmatched_existing`

1. Existing apparatus row is absent from current extractor output.
2. Lane 502 leaves the row untouched.
3. The report surfaces it for operator review.

`unmatched_extractor`

1. Extractor candidate has no existing apparatus row.
2. Lane 502 may only consider `INSERT` after explicit operator review and admission.
3. The candidate remains visible in the intermediate contract with `id = null`.

`conflicting`

1. Multiple existing rows match one extractor candidate, or one existing row matches multiple candidates.
2. Lane 502 leaves all involved rows untouched.
3. Manual resolution is required before admission.

## Acceptance Criteria

Lane 501 produces a reconciliation state that is ready for Lane 502 admission review only when all of the following are true:

1. `conflicting = 0`
2. `matched + unmatched_extractor = total extractor candidate count`
3. `matched + unmatched_existing = total existing apparatus row count`
4. Every proposed apparatus `scope_id` resolves to a scope object present in the same intermediate contract
5. The reconciliation report hash is stable and recorded in both the reconciliation JSON and the intermediate JSON
6. The no-write SQL log contains only `SELECT` or `WITH` statements

For the 2026-05-21 sample, all criteria above passed.

## Explicit Admission Gate

Lane 502 must refuse all writes unless the operator supplies an admission phrase that includes the exact reconciliation hash:

`1b87397b17ffecd27679073d9645012d5663533ad344e15110c91258993d6130`

Hash algorithm:

1. Take the nested `report_body` object from the reconciliation JSON sibling.
2. Serialize with JSON sorted keys and compact separators `(',', ':')`.
3. Encode as UTF-8.
4. Compute SHA-256 over those bytes.

Lane 502 must recompute that value at runtime and abort if the supplied phrase or the on-disk report body does not match.