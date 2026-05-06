# APEX RESA PM Project PSS Source Lineage

This directory preserves the bounded PM/project/PSS Supabase lineage tranche imported during packet `2026-04-13-apex-unification-001b`.

Status:
- Source-lineage only
- Reference input for future comparison and decomposition work
- Not active migration authority
- Not approved as the current PM schema baseline

Imported slices:
- `schema/00_enums.sql` through `08_apparatus_completion_workflow.sql`
- `schema/09_schema_additions.sql`
- `data/10_seed_data.sql`
- `data/11_test_data.sql`
- `data/12_pss_test_data.sql`

Explicit exclusions from this tranche:
- `schema/09b_enum_updates.sql`
- `schema/10_ai_orchestration.sql`
- `schema/11_ai_orchestration_functions.sql`
- `schema/12_study_content.sql`
- `data/20_neta_procedures.sql`
- `data/21_neta_test_items.sql`
- `data/21_neta_test_items_batch2.sql`
- deployment utilities and environment files
- runtime code and active PM authority documents

Provenance:
- Source root: `C:\APEX Platform\Supabase`
- Imported by copy only; original source files remain in place

Known divergence after 2026-05-06 Operations Visibility execution:
- `schema/09_schema_additions.sql` in this lineage directory is now intentionally stale relative to the authoritative `C:\APEX Platform\Supabase\schema\09_schema_additions.sql`.
- Packets 045 through 047 hardened the authoritative source with rerun-safe `apparatus_availability` creation, `security_invoker` view options, and enum-compatible text comparisons before the live Supabase apply.
- This lineage copy is preserved as the imported source-lineage snapshot and must not be treated as active migration authority or blindly copied back over the authoritative source.
- Packet 049 records the current rule: preserve the lineage body for provenance, but annotate the drift explicitly so future comparison and decomposition work does not misclassify this file as current truth.
