# Claude Desktop Session Starter

**Purpose:** Bootstrap any Claude Desktop session with RESA Power project context  
**Last Updated:** November 27, 2025  
**Solution Version:** v1.5.0.0  

---

## 🚀 COPY THIS TO START A NEW SESSION

```
I'm continuing work on the RESA Power Project Tracker - a Dataverse-based project management system for electrical testing projects (NETA standards).

PROJECT LOCATION: C:\RESA_Power_Build

BEFORE DOING ANYTHING ELSE, read these files in order:
1. C:\RESA_Power_Build\PROJECT_CONTEXT.json (critical facts, environment, current status)
2. C:\RESA_Power_Build\Documentation\00_START_HERE\PROJECT_STATUS_TRACKER.md (comprehensive status)
3. Find and read the MOST RECENT file in C:\RESA_Power_Build\Documentation\03_Progress_Tracking\ (latest session work)

CRITICAL FACTS (verify against PROJECT_CONTEXT.json):
- Environment: https://org99cd6c6e.crm.dynamics.com (DEV ONLY - never production)
- Solution: v1.5.0.0 with 16 tables, 649 fields, 65 rollup/calculated fields
- Table prefix: cr950_
- API queries use PLURAL names (cr950_projectses)
- API create/update uses SINGULAR names (cr950_projects)

After reading those files, tell me:
1. Current solution version and status
2. What was accomplished in the most recent session
3. What's flagged as next priority

Then ask what I'd like to work on.
```

---

## 📋 QUICK FACTS (November 27, 2025)

### Environment
| Item | Value |
|------|-------|
| Dataverse URL | https://org99cd6c6e.crm.dynamics.com |
| Tenant ID | 270d5723-4b30-4f3b-b9cb-6527be741b42 |
| Client ID | 9df3350f-b3b4-47c4-97b5-499a8b02acc7 |
| App Name | RESA-Dev-MCP-Access |

### Solution Stats (v1.5.0.0)
| Item | Count |
|------|-------|
| Tables | 16 |
| Total Fields | 649 |
| Rollup/Calculated | 65 |
| Power Automate Flows | 1 (Revenue Recognition) |

### The 16 Tables
**Core (8):** Projects, ProjectScope, Tasks, Apparatus, ApparatusRevenue, ScopeLaborDetail, ApparatusTypeMaster, BusinessUnit

**New v1.4.0.0 (6):** Client, Site, Employee, Quote, ResourceAssignment, Equipment

**New v1.5.0.0 (2):** ProjectFinancialSummary, ScopeFinancialSummary

---

## 📁 KEY FILE LOCATIONS

| Document | Path |
|----------|------|
| **Project Context** | `PROJECT_CONTEXT.json` |
| **Status Tracker** | `Documentation/00_START_HERE/PROJECT_STATUS_TRACKER.md` |
| **Session Summaries** | `Documentation/03_Progress_Tracking/SESSION_SUMMARY_*.md` |
| **Master Build Spec** | `Documentation/01_Architecture/MASTER_BUILD_SPECIFICATION.md` |
| **Revenue Architecture** | `Documentation/01_Architecture/REVENUE_ARCHITECTURE.md` |
| **Import Pipeline SOP** | `Documentation/06_Implementation_Guides/IMPORT_PIPELINE_SOP.md` |
| **Solution Export** | `Solution_Exports/v1.5.0.0_extracted/customizations.xml` |

---

## 🔧 MCP SERVERS AVAILABLE

| Server | Purpose | Status |
|--------|---------|--------|
| `filesystem` | Read/write C:\RESA_Power_Build | ✅ Working |
| `resa-dataverse-dev` | Dataverse CRUD operations | ✅ Query works, Create has issues |
| `resa-testing` | Rollup validation, test tools | ✅ Working |
| `resa-docs` | Documentation generation | ✅ Working |
| `memory` | Knowledge graph | ✅ Optional |
| `github` | Repository operations | ✅ Working |

### Dataverse API Notes
- **Query (GET):** Use plural EntitySetName → `cr950_projectses`, `cr950_apparatuses`
- **Create (POST):** Use singular table name → `cr950_projects`, `cr950_apparatus`
- **Lookups:** Use `@odata.bind` format → `"cr950_Project@odata.bind": "/cr950_projectses(guid)"`

---

## ⚠️ COMMON MISTAKES TO AVOID

1. **Wrong environment** - Only use org99cd6c6e.crm.dynamics.com
2. **Old table names** - It's `BusinessUnit` not `Location`, `ScopeLaborDetail` not `Scope_Financial_Config`
3. **Query with singular** - API queries need PLURAL table names
4. **Outdated docs** - Master Build Spec claims v1.3.0.4, reality is v1.5.0.0
5. **Assuming state** - Always read PROJECT_CONTEXT.json first

---

## 📝 DOCUMENTATION DEBT (As of Nov 27, 2025)

The audit identified these docs need updating:

| Document | Issue | Priority |
|----------|-------|----------|
| MASTER_BUILD_SPECIFICATION.md | Claims v1.3.0.4, missing 8 tables | P1 - Assigned to VS Claude |
| REVENUE_RECOGNITION_FLOW_SPEC.md | Missing Nov 17 fixes + Revenue Recognition Date | P1 |
| REVENUE_ARCHITECTURE.md | Claims v1.3.0.0, missing financial summary tables | P2 |

**Source of Truth:** `Solution_Exports/v1.5.0.0_extracted/customizations.xml`

---

## 🎯 CURRENT PRIORITIES (Nov 27, 2025)

### Just Completed
- ✅ Estimator to Dataverse import pipeline (VBA + JSON + Node.js)
- ✅ 143 apparatus imported for Central Mesa Reuse Plant test
- ✅ ScopeLaborDetail record created manually (import script v2 pending)
- ✅ Documentation audit identifying version drift
- ✅ Import Pipeline SOP created

### In Progress
- 🔄 Master Build Spec update (assigned to VS Claude)
- 🔄 Revenue Recognition Flow Spec update

### Next Up
- Revenue flow test (flow is currently OFF)
- Deploy import-estimator-v2.js with ScopeLaborDetail creation

---

## 🏁 SESSION END PROTOCOL

Before ending a session:

```
Please create a session summary at:
C:\RESA_Power_Build\Documentation\03_Progress_Tracking\SESSION_SUMMARY_[DATE]_[TOPIC].md

Include:
1. What was accomplished
2. Key decisions made
3. Files created/modified
4. Next steps
5. Any blockers

Then update PROJECT_CONTEXT.json with:
- lastUpdated timestamp
- sessionId 
- Any new criticalFacts discovered
- currentStatus updates
```

---

## 📞 TASK-SPECIFIC STARTERS

### For Dataverse Work
```
RESA Power at C:\RESA_Power_Build
Read PROJECT_CONTEXT.json first.

Dataverse environment: org99cd6c6e.crm.dynamics.com
Use resa-dataverse-dev MCP for queries.

Task: [describe your Dataverse task]
```

### For Documentation Work
```
RESA Power at C:\RESA_Power_Build
Read PROJECT_CONTEXT.json and Documentation/00_START_HERE/PROJECT_STATUS_TRACKER.md

Documentation audit completed Nov 27 - see Documentation/08_Testing_QA/DOCUMENTATION_AUDIT_20251127.md

Task: [describe documentation task]
```

### For Import/Automation Work
```
RESA Power at C:\RESA_Power_Build
Read PROJECT_CONTEXT.json

Key files:
- Reference_Files/Excel/Estimator VBA Modules/DataverseExport.bas
- MCP_Servers/resa-dataverse-mcp/import-estimator.js
- Documentation/06_Implementation_Guides/IMPORT_PIPELINE_SOP.md

Task: [describe automation task]
```

---

*This document should be updated whenever major milestones are reached or project structure changes.*
