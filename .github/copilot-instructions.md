# RESA Power Project - Copilot Instructions

> Repo-owned copy established 2026-05-07 so the active Copilot workspace instructions live inside the canonical repo boundary. Keep the parent-root `.github/copilot-instructions.md` aligned until broader `.github/` reconciliation is complete.

## Project Context

RESA Power electrical testing company project management platform.
**Database**: Supabase (PostgreSQL) - migrated from Dataverse December 2025
**Web App**: Next.js 16 at `C:\Users\jjswe\Projects\resa-web-app`
**Repository**: RESA-Power-Project-Management on GitHub

## CRITICAL: Schema Reference

**Read `docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md` for database schema.**
**Read `PROJECT_STATUS.md` for current progress and next steps.**

## Critical Files to Read First

1. `PROJECT_STATUS.md` - Overall status, what's done, what's remaining
2. `docs/authority/README.md` - Current authority routing inside the canonical repo
3. `ops/agents/handoffs/` - Recent packet handoffs and closeout evidence
4. `docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md` - Database tables, views, triggers

## Key Table Names (Supabase)

```
clients                - Customer companies
sites                  - Client facility locations
locations              - RESA branch offices
projects               - Main project records
scopes                 - Project phases/work packages
tasks                  - Work items within scopes
apparatus              - Equipment being tested
apparatus_revenue      - Revenue recognition records
employees              - RESA staff
estimators             - Quote creators
```

## Supabase Configuration

- **Project**: resa-power-db (fxoyniqnrlkxfligbxmg)
- **API URL**: https://fxoyniqnrlkxfligbxmg.supabase.co
- **Credentials**: `.secrets/SUPABASE_CREDENTIALS.md`
- **Schema Files**: `Supabase/schema/*.sql`

## Web App Configuration

- **Location**: `C:\Users\jjswe\Projects\resa-web-app`
- **Supabase Client**: `src/lib/supabase.ts`
- **Dev Server**: `npm run dev` -> http://localhost:3000

## Session Protocol

- **On Start**: Read `PROJECT_STATUS.md`, `docs/authority/README.md`, and `docs/architecture/knowledge-domain/apex-resa/SCHEMA_REFERENCE.md`; inspect the latest file under `ops/agents/handoffs/` when continuing an active packet lane
- **During**: Capture bounded follow-on ideas in repo-owned architecture, plan, or handoff surfaces rather than reviving parent-root `.claude` coordination files
- **On End**: Update `PROJECT_STATUS.md` if milestones completed and add a handoff under `ops/agents/handoffs/` when a bounded packet closes