# RESA Power Project - Current State

**Last Updated:** December 2, 2025, 6:45 PM  
**Updated By:** Web Claude (Opus 4.5)  
**Session Type:** Schema Audit

---

## Quick Context (30 Second Read)

RESA Power Project Tracker is undergoing a **ground-up V2 rebuild** in a new Dataverse environment (org7bdbc942). The core hierarchy tables (Client → Site → Project → Scope → ScopeLaborDetail) are deployed and working with verified relationships. Tasks and Apparatus tables exist but are empty. Revenue recognition tables are **intentionally not yet deployed** - that's the active work stream. We're at the point of defining the workflow and splitting tasks between Claude instances.

**Current Phase:** Schema Foundation Complete → Revenue Recognition Design  
**Environment:** org7bdbc942.crm.dynamics.com (V2 - Dev)  
**Solution Version:** V2 Fresh Build

---

## Active Work Items

| Priority | Item | Status | Owner | Notes |
|----------|------|--------|-------|-------|
| P0 | Define Revenue Recognition Workflow | 🟡 IN PROGRESS | Jason + Both Claudes | Splitting workload soon |
| P0 | Deploy ApparatusRevenue table | ⚪ NOT STARTED | TBD | Blocked by workflow definition |
| P0 | Deploy ApparatusTypeMaster table | ⚪ NOT STARTED | TBD | Needed for NETA hours lookup |
| P1 | Update MCP server entity map | ⚪ NOT STARTED | TBD | Use V2 naming conventions |
| P1 | Create Task test data | ⚪ NOT STARTED | TBD | Blocked by schema completion |
| P1 | Create Apparatus test data | ⚪ NOT STARTED | TBD | Blocked by Task data |
| P2 | Deploy Employee table | ⚪ NOT STARTED | Future | For technician tracking |
| P2 | Deploy Quote table | ⚪ NOT STARTED | Future | For estimate conversion |

---

## Last Session

- **Date:** December 2, 2025
- **Duration:** ~45 minutes
- **Focus:** Comprehensive schema audit of org7bdbc942 environment

**Accomplishments:**
1. ✅ Verified 9 tables exist with correct V2 naming
2. ✅ Confirmed all lookup relationships working (Client→Site→Project→Scope→ScopeLaborDetail)
3. ✅ Documented complete field schemas for all populated tables
4. ✅ Identified 7 missing tables (by design - not yet deployed)
5. ✅ Created comprehensive audit report: `Documentation\SCHEMA_AUDIT_org7bdbc942_Dec2025.md`
6. ✅ Created session management system (this file structure)

**Blockers Encountered:**
- None - audit completed successfully

---

## Next Steps (Priority Order)

1. **Jason to split workload** between Web Claude and VS Claude for revenue recognition work
2. **Define ApparatusRevenue table schema** - fields, relationships, calculated fields
3. **Define ApparatusTypeMaster schema** - NETA standard hours by apparatus type
4. **Build Power Automate flow** for revenue recognition trigger
5. **Create test data pipeline** - Tasks and Apparatus records

---

## Environment Details

| Setting | Value |
|---------|-------|
| **Dataverse URL** | https://org7bdbc942.crm.dynamics.com |
| **Tenant ID** | 270d5723-4b30-4f3b-b9cb-6527be741b42 |
| **Client ID** | 9df3350f-b3b4-47c4-97b5-499a8b02acc7 |
| **Publisher Prefix** | cr950_ |
| **Environment Type** | Development (V2 Fresh Build) |

### Tables Deployed (9)
- cr950_clients ✅
- cr950_sites ✅
- cr950_projects ✅
- cr950_scopes ✅
- cr950_scopelabordetails ✅
- cr950_tasks ✅ (empty)
- cr950_apparatuses ✅ (empty)
- cr950_estimators ✅
- cr950_locations ✅ (empty)

### Tables NOT YET Deployed (7)
- cr950_apparatusrevenues ❌
- cr950_apparatustypemasters ❌
- cr950_employees ❌
- cr950_quotes ❌
- cr950_resourceassignments ❌
- cr950_equipment ❌
- cr950_businessunits ❌ (replaced by locations)

---

## Key File Locations

| Purpose | Path |
|---------|------|
| **Session Files** | `C:\RESA_Power_Build\Sessions\` |
| **Schema Audit** | `Documentation\SCHEMA_AUDIT_org7bdbc942_Dec2025.md` |
| **Flow Migration Guide** | `Documentation\FLOW_SCHEMA_AUDIT_DEC2025.md` |
| **MCP Server Config** | `MCP_Servers\resa-dataverse-mcp\.env` |
| **Previous Audits** | `Documentation\03_Progress_Tracking\` |

---

## Test Data Present

| Table | Records | Sample |
|-------|---------|--------|
| Clients | 1 | Garney |
| Sites | 1 | Central Mesa Reuse Plant |
| Projects | 1 | 677562 - Central Mesa Reuse Plant |
| Scopes | 1 | IPS NETA ATS |
| ScopeLaborDetails | 1 | $61,025.63 / 333.75 hrs / $182.85 rate |
| Estimators | 1 | Garney - Central Mesa Reuse (Rev 2) |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-02 | Ground-up V2 rebuild | Clean schema design for defined workflow |
| 2025-12-02 | V2 entity naming | Cleaner names: projects, scopes, scopelabordetails |
| 2025-12-02 | Location replaces BusinessUnit | Simpler hierarchy |
| 2025-12-02 | Revenue tables deployed later | Part of active workflow design |

---

## Notes for Next Claude Instance

- The MCP server `resa-dataverse` is configured for org7bdbc942 but entity map may need V2 name updates
- PowerShell direct queries work fine (see audit report for examples)
- Scope type is stored as TEXT ("ATS") not option set in V2
- All money fields have `_base` counterparts (base currency)
- Lookup fields use `_cr950_[field]_value` pattern

---

*State file maintained per SESSION_PROTOCOL.md*
