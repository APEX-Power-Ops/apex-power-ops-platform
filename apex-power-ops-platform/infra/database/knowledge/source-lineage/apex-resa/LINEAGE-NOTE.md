# APEX RESA Knowledge Schema And Import Source Lineage

This directory preserves the bounded knowledge-schema and import-assets Supabase tranche imported during packet `2026-04-13-apex-unification-001d`.

Status:
- Knowledge-domain source lineage only
- Reference input for future knowledge-schema comparison and import decomposition work
- Not active schema authority
- Not a replacement for the active published knowledge lane

Imported slices:
- `schema/12_study_content.sql`
- `data/20_neta_procedures.sql`
- `data/21_neta_test_items.sql`
- `data/21_neta_test_items_batch2.sql`
- `scripts/import_neta_data.py`

Explicit exclusions from this tranche:
- PM/project/PSS lineage SQL and seed assets
- automation and orchestration SQL or protocol assets
- deployment utilities and environment files
- publication HTML, manifests, mappings, templates, and visual assets already living in the knowledge domain
- runtime code and active authority documents

Provenance:
- Source root: `C:\APEX Platform\Supabase`
- Imported by copy only; original source files remain in place
