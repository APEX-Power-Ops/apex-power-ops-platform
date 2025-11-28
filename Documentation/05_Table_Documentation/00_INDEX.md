# RESA Power Table Documentation Index

**Generated:** November 23, 2025  
**Purpose:** Master index for all 16 RESA Power Dataverse tables  
**Status:** 🔄 Just Started (6% complete)  
**Box Folder:** [Table Documentation - RESA Power](https://app.box.com/folder/352615082326)

---

## 📊 Documentation Progress

| # | Table Name | Display Name | Relationships | Rollup Fields | Status | File |
|---|------------|--------------|---------------|---------------|--------|------|
| 1 | cr950_projects | Projects | 29 | 6 date tracking | ✅ Complete | [01_Projects_Documentation.md](./01_Projects_Documentation.md) |
| 2 | cr950_projectscope | Project Scope | 22 | 6 date tracking | 🔄 Generated | 02_ProjectScope_Documentation.md |
| 3 | cr950_tasks | Tasks | TBD | 6 date tracking | ⏳ Pending | 03_Tasks_Documentation.md |
| 4 | cr950_apparatus | Apparatus | TBD | None | ⏳ Pending | 04_Apparatus_Documentation.md |
| 5 | cr950_apparatusrevenue | Apparatus Revenue | TBD | None | ⏳ Pending | 05_ApparatusRevenue_Documentation.md |
| 6 | cr950_scopelabordetails | Scope Labor Detail | TBD | None | ⏳ Pending | 06_ScopeLaborDetail_Documentation.md |
| 7 | cr950_scopefinancialsummary | Scope Financial Summary | TBD | 7 revenue rollups | ⏳ Pending | 07_ScopeFinancialSummary_Documentation.md |
| 8 | cr950_projectfinancialsummary | Project Financial Summary | TBD | 7 revenue rollups | ⏳ Pending | 08_ProjectFinancialSummary_Documentation.md |
| 9 | cr950_apparatustypemaster | Apparatus Type Master | TBD | None | ⏳ Pending | 09_ApparatusTypeMaster_Documentation.md |
| 10 | cr950_client | Clients | TBD | None | ⏳ Pending | 10_Clients_Documentation.md |
| 11 | cr950_site | Sites | TBD | None | ⏳ Pending | 11_Sites_Documentation.md |
| 12 | cr950_employee | Employees | TBD | None | ⏳ Pending | 12_Employees_Documentation.md |
| 13 | cr950_quote | Quotes | TBD | None | ⏳ Pending | 13_Quotes_Documentation.md |
| 14 | cr950_resourceassignment | Resource Assignments | TBD | None | ⏳ Pending | 14_ResourceAssignments_Documentation.md |
| 15 | cr950_equipment | Equipment | TBD | None | ⏳ Pending | 15_Equipment_Documentation.md |
| 16 | cr950_businessunit | Business Units | TBD | None | ⏳ Pending | 16_BusinessUnits_Documentation.md |

**Progress:** 1/16 Complete (6%) | 1/16 Generated (6%) | 14/16 Remaining  
**Rollup Fields:** 32 total (18 date tracking + 14 revenue) - Added in v1.5.0.0

---

## 🎯 Table Categories

### Core Project Hierarchy (4 tables)
1. **Projects** ✅ - Top-level container (6 date rollups)
2. **Project Scope** 🔄 - Work breakdown (6 date rollups)
3. **Tasks** ⏳ - Task organization (6 date rollups)
4. **Apparatus** ⏳ - Individual test items (source data for rollups)

### Financial Tables (4 tables)
5. **Apparatus Revenue** ⏳ - Revenue recognition
6. **Scope Labor Detail** ⏳ - Budget & rates
7. **Scope Financial Summary** ⏳ - Scope-level revenue rollups (7 fields)
8. **Project Financial Summary** ⏳ - Project-level revenue rollups (7 fields)

### Master Data (1 table)
9. **Apparatus Type Master** ⏳ - Standard test types

### Customer/Site (2 tables)
10. **Clients** ⏳ - Customer information
11. **Sites** ⏳ - Work locations

### Resources (3 tables)
12. **Employees** ⏳ - Technician roster
13. **Resource Assignments** ⏳ - Project staffing
14. **Equipment** ⏳ - Tools & instruments

### Sales (1 table)
15. **Quotes** ⏳ - Estimating & proposals

### Organizational (1 table)
16. **Business Units** ⏳ - RESA locations

---

## 📋 Quick Reference

### Table Name Format Rules

| Display Name | ❌ Wrong (Singular) | ✅ Correct (Plural EntitySetName) |
|--------------|--------------------|---------------------------------|
| Projects | cr950_projects | cr950_projectses |
| Project Scope | cr950_projectscope | cr950_projectscopes |
| Tasks | cr950_tasks | cr950_taskses |
| Apparatus | cr950_apparatus | cr950_apparatuses |
| Apparatus Revenue | cr950_apparatusrevenue | cr950_apparatusrevenues |
| Scope Labor Detail | cr950_scopelabordetails | cr950_scopelabordetails |
| **Scope Financial Summary** | cr950_scopefinancialsummary | cr950_scopefinancialsummaries |
| **Project Financial Summary** | cr950_projectfinancialsummary | cr950_projectfinancialsummaries |
| Apparatus Type Master | cr950_apparatustypemaster | cr950_apparatustypemasters |
| Clients | cr950_client | cr950_clients |
| Sites | cr950_site | cr950_sites |
| Employees | cr950_employee | cr950_employees |
| Quotes | cr950_quote | cr950_quotes |
| Resource Assignments | cr950_resourceassignment | cr950_resourceassignments |
| Equipment | cr950_equipment | cr950_equipments |
| Business Units | cr950_businessunit | cr950_businessunits |

---

## 🔗 Relationship Summary (from completed docs)

### Projects Table (29 relationships)
**Key Parents:**
- Client (cr950_client)
- Site (cr950_site)
- Business Unit Location (cr950_businessunit)

**Key Children:**
- Project Scopes (cr950_projectscope)
- Tasks (cr950_tasks)
- Apparatus (cr950_apparatus)
- Apparatus Revenue (cr950_apparatusrevenue)
- Resource Assignments (cr950_resourceassignment)
- Equipment (cr950_equipment)
- Quotes (cr950_quote)

### Project Scope Table (22 relationships)
**Key Parent:**
- Project (cr950_projects)

**Key Children:**
- Tasks (cr950_tasks)
- Apparatus (cr950_apparatus)
- Scope Labor Details (cr950_scopelabordetails) - 1:1 relationship

---

## 📐 Known Issues

**Issue 1: Display Names**
- Generated docs show `[object Object]` instead of friendly names
- **Impact:** Cosmetic only
- **Workaround:** Names documented in this index
- **Status:** Fix scheduled (30 minutes)

**Issue 2: Field Counts**
- Shows 0 fields in all documentation
- **Impact:** Field details not in automated docs
- **Workaround:** Reference MASTER_BUILD_SPECIFICATION.md or Power Apps
- **Status:** Under investigation (permissions issue suspected)

---

## 🚀 Next Steps

**Immediate:**
1. ✅ Generate documentation for remaining 12 tables
2. ✅ Upload all docs to Box for mobile access
3. ⏳ Begin rollup field validation testing

**Short-Term:**
1. Fix display name formatting in templates
2. Investigate field metadata visibility
3. Add field lists manually to documentation
4. Create visual relationship diagrams

**Medium-Term:**
1. Generate ERD diagrams for each table
2. Create usage examples with real data
3. Document calculated fields
4. Document rollup fields

---

## 📱 Mobile Access

**Box Folder:** https://app.box.com/folder/352615082326

All table documentation will be uploaded to Box for easy mobile reference during field work.

---

## 🛠️ Generation Commands

### Generate Documentation
```bash
# In Claude Desktop:
"Generate table documentation for cr950_[tablename]"
```

### Query Table
```bash
# Using resa-dataverse-dev:
query_dataverse("cr950_[tablename]s", null, null, 10)  # Note: plural form
```

---

## 📝 Notes

- All documentation generated using resa-docs-mcp v1.0.0
- Environment: org99cd6c6e.crm.dynamics.com (DEV)
- Generator tools operational as of Nov 24, 2025
- Documentation includes relationship mapping but not field details (pending fix)

---

## 📚 Related Documentation

- **Rollup Field Audit:** [SOLUTION_v1.5.0.0_AUDIT_REPORT.md](../03_Progress_Tracking/SOLUTION_v1.5.0.0_AUDIT_REPORT.md)
- **MCP Server Status:** [MCP_STATUS_REPORT_20251123.md](../06_Implementation_Guides/MCP_STATUS_REPORT_20251123.md)
- **Table Name Reference:** [TABLE_NAMES_REFERENCE.md](../../MCP_Servers/resa-dataverse-mcp/TABLE_NAMES_REFERENCE.md)
- **Master Build Spec:** [MASTER_BUILD_SPECIFICATION.md](../01_Architecture/MASTER_BUILD_SPECIFICATION.md)

---

**Last Updated:** 2025-11-23T22:30:00Z  
**Next Update:** After completing all 16 table docs  
**Owner:** Jason Swenson
