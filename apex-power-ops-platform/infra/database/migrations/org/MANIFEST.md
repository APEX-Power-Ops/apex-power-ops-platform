# Org Domain SQL Migration Manifest
## Packet: 2026-04-14-pm-schema-011b
## Target: Local PostgreSQL staging database `apex_pm_stage`

## Execution Order

Execute these files in strict sequential order against the target database:

| Order | File | Contents | Dependencies |
| --- | --- | --- | --- |
| 1 | `001_org_schema.sql` | `org` schema creation | None |
| 2 | `002_org_tables.sql` | 4 core tables with PKs, internal FKs, UNIQUE constraints | Requires 001 (schema) |
| 3 | `003_org_triggers.sql` | `updated_at` auto-maintenance trigger function + 4 triggers | Requires 002 (tables) |

## Quick Execution

```bash
# Execute in order against the existing staging database
psql -d apex_pm_stage -f 001_org_schema.sql
psql -d apex_pm_stage -f 002_org_tables.sql
psql -d apex_pm_stage -f 003_org_triggers.sql
```

## Object Summary

| Category | Count | Details |
| --- | --- | --- |
| Schema | 1 | `org` |
| Enum types | 0 | None required for minimum design |
| Tables | 4 | clients, sites, business_units, contracts |
| Internal FKs | 2 | sites.client_id -> clients, contracts.client_id -> clients |
| UNIQUE constraints | 4 | clients.client_code, sites.(client_id, site_code), business_units.code, contracts.contract_code |
| Trigger functions | 1 | org.fn_set_updated_at |
| Triggers | 4 | updated_at on all 4 tables |

## Relationship to PM/Work Domain

This org bundle does NOT activate any PM/work foreign keys. The six deferred FK columns in `work.projects` and `work.work_packages` remain as bare UUID columns. FK activation is deferred to packet 011d after seed-data population (011c).

| Deferred PM/Work FK | Target | Activation Packet |
| --- | --- | --- |
| `work.projects.client_id` | `org.clients` | 011d |
| `work.projects.site_id` | `org.sites` | 011d |
| `work.projects.business_unit_id` | `org.business_units` | 011d |
| `work.projects.contract_id` | `org.contracts` | 011d |
| `work.work_packages.client_id` | `org.clients` | 011d |
| `work.work_packages.site_id` | `org.sites` | 011d |

## Clean Rebuild (org only)

```bash
# Drop org schema and recreate
psql -d apex_pm_stage -c "DROP SCHEMA IF EXISTS org CASCADE;"
psql -d apex_pm_stage -f 001_org_schema.sql
psql -d apex_pm_stage -f 002_org_tables.sql
psql -d apex_pm_stage -f 003_org_triggers.sql
```
