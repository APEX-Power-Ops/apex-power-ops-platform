# APEX RESA Automation And Orchestration Source Lineage

This directory preserves the bounded automation and orchestration Supabase lineage tranche imported during packet `2026-04-13-apex-unification-001c`.

Status:
- Source-lineage only
- Reference input for future control-plane decomposition and comparison work
- Not active migration authority
- Not approved as the current control-plane schema baseline

Imported slices:
- `schema/09b_enum_updates.sql`
- `schema/10_ai_orchestration.sql`
- `schema/11_ai_orchestration_functions.sql`

Explicit exclusions from this tranche:
- deployment utilities such as `deploy.ps1` and `DEPLOY_*.sql`
- environment files such as `.env.example`
- app utility code such as `lib/supabase.ts`
- PM/project/PSS lineage SQL and seeds
- knowledge-schema and import assets
- runtime code and active control-plane authority documents

Provenance:
- Source root: `C:\APEX Platform\Supabase`
- Imported by copy only; original source files remain in place
