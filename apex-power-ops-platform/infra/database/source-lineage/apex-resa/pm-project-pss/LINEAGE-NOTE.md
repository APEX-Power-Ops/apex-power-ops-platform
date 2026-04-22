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
