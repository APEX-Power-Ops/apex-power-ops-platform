# 027 F-79-01 — prod apply transcript (evidence)

- **Migration:** `027_sst_mismatch_classkey_fix.sql` (#79 F-79-01)
- **Object:** `tcc.vw_breaker_sst_mismatch` — `CREATE OR REPLACE VIEW`, partition key `(breaker_class, breaker_style_id)` (was bare `breaker_style_id`)
- **Target:** governed Supabase prod `fxoyniqnrlkxfligbxmg` (apex-power-ops, PG 17)
- **Method:** MCP `apply_migration`, name `f79_01_sst_mismatch_classkey_fix`
- **Date:** 2026-06-26
- **Authorization:** operator explicit "apply 027" (027 only; 028 NOT applied)

## Preflight (read-only, pre-apply)
- `before_count` = **8**
- live view body = **byte-identical** to the assumed old body (`027_..._down`); partition was bare `breaker_style_id`; no drift from the 2026-06-25 sandbox restore.

## Apply
- `apply_migration` → `{"success": true}`

## Post-checks (read-only, post-apply)
| field | value |
|---|---|
| before_count | 8 |
| after_count | **53** |
| delta | **+45** |
| partition_is_class_keyed | true |
| monotonic_ok (after >= 8) | true |

## Assessment
- Structurally valid. after_count (53) **matches the sandbox dry-run exactly** → no prod/sandbox data divergence → no data-delta note required.
- 45 previously-hidden cross-class SST rating mismatches are now surfaced in the diagnostic view.
- Reversible via `027_sst_mismatch_classkey_fix_down.sql` (restores the bare-key body).

## Scope discipline
- **028 (F-79-02) NOT applied** — held for a separate operator go.
- F-79-03 / F-79-04 remain parked (triangulation / Access authority).
