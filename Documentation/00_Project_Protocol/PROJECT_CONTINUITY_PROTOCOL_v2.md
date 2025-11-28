# PROJECT CONTINUITY PROTOCOL v2.0
## RESA Power Project Tracker - Session Management & Knowledge Transfer

**Purpose**: Ensure zero knowledge loss between sessions, consistent documentation, and seamless continuity  
**Created**: November 19, 2025  
**Last Updated**: November 28, 2025  
**Version**: 2.0  
**Status**: ✅ ACTIVE

---

## 📋 DOCUMENT HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Nov 15, 2025 | Initial protocol created |
| 1.1-1.4 | Nov 15-19, 2025 | Incremental updates |
| 2.0 | Nov 28, 2025 | **Complete rewrite** - Updated to v1.5.1.0, 16 tables, 649 fields, added Box.com integration, VS Claude workflow, Import Pipeline, MCP server documentation |

---

## 🎯 PROJECT IDENTITY

### Core Information

| Attribute | Value |
|-----------|-------|
| **Project Name** | RESA Power Project Tracker |
| **Technology** | Microsoft Dataverse (Power Platform) |
| **Environment** | RESA-Dev |
| **Environment URL** | https://org99cd6c6e.crm.dynamics.com |
| **Tenant ID** | 270d5723-4b30-4f3b-b9cb-6527be741b42 |
| **Client ID** | 9df3350f-b3b4-47c4-97b5-499a8b02acc7 |
| **Solution Name** | RESAPowerProjectTracker (Unmanaged) |
| **Current Version** | v1.5.1.0 |
| **Table Prefix** | cr950_ |
| **Repository** | https://github.com/jasonlswenson-sys/RESA-Power-Project-Management |

### Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| **Project Lead** | Jason Swenson | Architecture, implementation, strategy |
| **Organization** | RESA Power | Southwest Region (Phoenix, Las Vegas, Denver, San Diego) |
| **Primary Users** | Field Technicians, Project Managers | Daily operations |

### Solution Scale

| Metric | Count | Notes |
|--------|-------|-------|
| **Tables** | 16 | 8 core + 6 v1.4.0.0 + 2 v1.5.0.0 |
| **Fields** | 649 | Custom fields across all tables |
| **Rollup/Calculated** | 65 | Automated aggregation fields |
| **Power Automate Flows** | 1 | Revenue Recognition (verified working) |
| **Views** | 10 | Created Nov 27, 2025 |

### The 16 Tables

**Core Tables (v1.0-v1.3):**
1. BusinessUnit - Multi-location support (Phoenix, Las Vegas, Denver, San Diego)
2. Projects - Top-level project containers
3. ProjectScope - Work breakdown by scope
4. Tasks - Logical groupings of apparatus
5. Apparatus - Individual equipment items
6. ScopeLaborDetail - Financial rates per scope
7. ApparatusRevenue - Revenue recognition records
8. ApparatusTypeMaster - NETA standards reference

**Added v1.4.0.0 (Nov 22, 2025):**
9. Client - Customer information
10. Site - Physical locations
11. Employee - Resource management
12. Quote - Estimating/proposals
13. ResourceAssignment - Project staffing
14. Equipment - Test equipment tracking

**Added v1.5.0.0 (Nov 23, 2025):**
15. ProjectFinancialSummary - Project-level financial rollups
16. ScopeFinancialSummary - Scope-level financial rollups

---

## 📁 FILE ORGANIZATION

### Root Directory: `C:\RESA_Power_Build\`

```
C:\RESA_Power_Build\
├── Documentation/
│   ├── 00_Project_Protocol/          ← SESSION MANAGEMENT (this doc)
│   │   └── PROJECT_CONTINUITY_PROTOCOL.md
│   │
│   ├── 00_START_HERE/                ← QUICK REFERENCES
│   │   ├── PROJECT_STATUS_TRACKER.md     (navigation hub)
│   │   ├── CLAUDE_DESKTOP_SESSION_STARTER.md
│   │   ├── PROJECT_GUIDELINES_AND_WORKFLOWS.md
│   │   └── QUICK_REFERENCE.md
│   │
│   ├── 01_Architecture/              ← SYSTEM DESIGN
│   │   ├── MASTER_BUILD_SPECIFICATION.md  (16 tables, 649 fields)
│   │   ├── REVENUE_ARCHITECTURE.md
│   │   ├── HOURS_ARCHITECTURE_GUIDE.md
│   │   └── USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md
│   │
│   ├── 02_Implementation/            ← BUILD SPECIFICATIONS
│   │   ├── REVENUE_RECOGNITION_FLOW_SPEC.md  (v1.5.0.1 - verified)
│   │   └── [other implementation specs]
│   │
│   ├── 03_Progress_Tracking/         ← SESSION SUMMARIES
│   │   ├── SESSION_SUMMARY_[DATE]_[TOPIC].md
│   │   ├── VERSION_HISTORY.md
│   │   └── VS_CLAUDE_MASTER_BUILD_TASK.md
│   │
│   ├── 06_Implementation_Guides/     ← HOW-TO GUIDES
│   │   ├── IMPORT_PIPELINE_SOP.md        (Excel → Dataverse)
│   │   └── [other guides]
│   │
│   └── 99_Archive/                   ← DEPRECATED DOCS
│
├── Solution_Exports/                 ← VERSION CONTROL
│   ├── v1.5.0.0_extracted/
│   │   ├── customizations.xml            (source of truth)
│   │   └── Workflows/
│   └── v1.5.1.0/                         (latest)
│
├── MCP_Servers/                      ← AUTOMATION
│   ├── resa-dataverse-mcp/               (Dataverse operations)
│   ├── resa-docs-mcp/                    (Documentation generation)
│   └── resa-testing-mcp/                 (Validation tools)
│
├── Reference_Files/                  ← SOURCE MATERIALS
│   ├── Excel/
│   │   ├── Estimator VBA Modules/
│   │   └── _DATAVERSE_IMPORT_*.json
│   └── Dataverse_Solutions/
│
├── Scripts/                          ← AUTOMATION SCRIPTS
│   └── PowerShell/
│       ├── Update-ProjectContext.ps1
│       └── Create-DataverseViews.ps1
│
└── PROJECT_CONTEXT.json              ← CRITICAL STATE FILE
```

### Box.com Integration (Mobile Access)

**Purpose**: Access documentation from any device (phone, tablet, web Claude)

**Location**: Box.com folder structure mirrors GitHub repository

**30 Organized Folders:**
- 00_START_HERE - Quick references
- 01_Architecture - System design
- 02_Implementation - Build specs
- 03_Progress_Tracking - Session summaries
- [continues to mirror Documentation structure]

**Sync Protocol**: After major documentation updates, sync to Box.com

---

## 🔧 MCP SERVER STATUS

### Available Servers

| Server | Status | Purpose | Notes |
|--------|--------|---------|-------|
| **resa-dataverse-dev** | ✅ Partial | Dataverse CRUD | Query works, Create has 404 issues |
| **resa-docs** | ✅ Working | Generate table documentation | Fully functional |
| **resa-testing** | ✅ Working | Validate rollup fields | Fully functional |
| **filesystem** | ✅ Working | Local file operations | Standard MCP |
| **github** | ✅ Working | Repository operations | Commits, reads |
| **memory** | ✅ Optional | Knowledge graph | For persistent facts |

### Dataverse API Notes

```
QUERY (GET): Use PLURAL EntitySetName
  cr950_projectses, cr950_apparatuses, cr950_scopelabordetailses

CREATE (POST): Use SINGULAR table name
  cr950_projects, cr950_apparatus, cr950_scopelabordetails

LOOKUPS: Use OData bind format
  "cr950_Project@odata.bind": "/cr950_projectses(guid)"
```

---

## 📥 IMPORT PIPELINE

### Excel → Dataverse Workflow

```
Excel Estimator (.xlsm)
    ↓ VBA Export (Alt+F8 → ExportToDataverse)
JSON File (_DATAVERSE_IMPORT_*.json)
    ↓ Node.js Import (node import-estimator.js)
Dataverse Tables
    ↓ PM Review
Task Creation (manual grouping)
    ↓ Flow Trigger
Revenue Recognition (automated)
```

### What Gets Created

| Entity | Source | Notes |
|--------|--------|-------|
| Client | Dataverse_Import sheet | 1 per import |
| Site | Dataverse_Import sheet | 1 per import |
| Project | Dataverse_Import sheet | 1 per import |
| Scopes | Active scope sheets | Typically 1-6 |
| ScopeLaborDetail | Scope financial data | 1 per scope |
| Apparatus | Scope sheets | Typically 50-500 |

### Key Files

| File | Location | Purpose |
|------|----------|---------|
| VBA Module | Reference_Files/Excel/Estimator VBA Modules/DataverseExport.bas | Export macro |
| Import Script | MCP_Servers/resa-dataverse-mcp/import-estimator.js | Node.js import |
| SOP | Documentation/06_Implementation_Guides/IMPORT_PIPELINE_SOP.md | Full procedure |

---

## 🔄 REVENUE RECOGNITION FLOW

### Status: ✅ VERIFIED WORKING (Nov 27, 2025)

### Trigger
- Apparatus.Completion_Status changed to "Complete" (value = 2)

### What Happens
1. Flow checks if Date_Completed is empty (using `empty()` function)
2. If empty, sets Date_Completed = utcNow()
3. Gets related Scope record
4. Lists ScopeLaborDetail for rate lookup
5. Checks for existing revenue (duplicate prevention)
6. Creates ApparatusRevenue record with:
   - Apparatus Hours
   - Effective Labor Rate
   - Revenue Amount (calculated: Hours × Rate)
   - Revenue Status = RECOGNIZED
   - Revenue Recognition Date = utcNow()

### Critical Fix (Nov 27, 2025)

**Problem**: `contains()` function fails on null DateTime values

**Solution**: Use `empty()` function with equality check:
```
empty(triggerOutputs()?['body/cr950_datecompleted']) is equal to true
```

### Test Results (Nov 27, 2025)

| Field | Result |
|-------|--------|
| Date Completed | 2025-11-28T04:17:47Z ✅ |
| Revenue Amount | $869.63 ✅ |
| Calculation | 2.5 hrs × $347.85 = $869.63 ✅ |

---

## 👥 MULTI-CLAUDE WORKFLOW

### When Working with Multiple Claude Instances

**Scenario**: Claude Desktop + VS Claude (or web Claude) simultaneously

**Protocol**:

1. **Designate Lead Instance**
   - One instance owns the session
   - Other instances work on delegated tasks

2. **Task Delegation Format**
   - Create task brief document
   - Specify: Objective, scope, constraints, deliverables
   - Example: `VS_CLAUDE_MASTER_BUILD_TASK.md`

3. **Handoff Points**
   - Lead instance creates task brief
   - Delegate instance reads brief, executes, reports back
   - Lead instance verifies and integrates

4. **Avoid Conflicts**
   - Don't edit same files simultaneously
   - Coordinate git commits
   - Use clear ownership of deliverables

### Example Task Brief Template

```markdown
# Task Brief: [TITLE]

**Assigned To**: VS Claude / Web Claude
**Created By**: Claude Desktop
**Date**: [DATE]
**Priority**: [P0/P1/P2]

## Objective
[Clear statement of what needs to be done]

## Scope
- Include: [what to do]
- Exclude: [what not to do]

## Source Files
[List files to read/reference]

## Deliverables
[Specific outputs expected]

## Constraints
[Any limitations or requirements]

## Verification
[How to confirm task is complete]
```

---

## 📝 DOCUMENTATION STANDARDS

### File Naming Convention

```
[CATEGORY]_[DESCRIPTION].md

✓ IMPORT_PIPELINE_SOP.md
✓ SESSION_SUMMARY_NOV27_REVENUE_FLOW.md
✓ REVENUE_RECOGNITION_FLOW_SPEC.md

✗ import pipeline.md (no spaces)
✗ notes.txt (no context)
✗ temp_doc_v3_final_FINAL.md (version chaos)
```

### Document Header Template

```markdown
# [DOCUMENT TITLE]

**Version**: [X.Y]
**Last Updated**: [Date]
**Status**: [Draft/Active/Deprecated]
**Owner**: [Who maintains this]

---

## Purpose
[Why this document exists]

---
```

### Version Numbering

**Solution Versions**: `v{Major}.{Minor}.{Patch}.{Build}`
- Major: Breaking changes, new table categories
- Minor: New tables or significant features
- Patch: Field additions, formula changes
- Build: Bug fixes, view changes

**Examples**:
- v1.4.0.0 - Added 6 new tables
- v1.5.0.0 - Added 65 rollup fields
- v1.5.0.1 - Fixed revenue flow condition
- v1.5.1.0 - Added views, Assigned Employee lookup

---

## ▶️ SESSION START PROTOCOL

### Step 1: Read Context Files (MANDATORY)

**Order matters:**

```
1. PROJECT_CONTEXT.json
   Location: C:\RESA_Power_Build\PROJECT_CONTEXT.json
   Contains: Environment, version, last session, critical facts

2. Most Recent Session Summary
   Location: Documentation/03_Progress_Tracking/SESSION_SUMMARY_*.md
   Find: Sort by date, read most recent

3. PROJECT_STATUS_TRACKER.md (if needed)
   Location: Documentation/00_START_HERE/PROJECT_STATUS_TRACKER.md
   Contains: Comprehensive status overview
```

### Step 2: Confirm Understanding

**Before doing any work, state:**

```
"Current state:
- Solution version: v1.5.1.0
- Last session accomplished: [X]
- Next priority flagged: [Y]

What would you like to work on?"
```

### Step 3: Verify Environment

**If doing Dataverse work:**
- Confirm environment: org99cd6c6e.crm.dynamics.com
- Never use any other environment URL
- Check MCP server connectivity if needed

---

## ⏹️ SESSION END PROTOCOL

### Step 1: Git Commit & Push (MANDATORY)

**All documentation changes must be committed:**

```powershell
cd C:\RESA_Power_Build
git add -A
git status  # Review changes
git commit -m "[category]: [description]

- Item 1
- Item 2
- Item 3"
git push origin main
```

**Commit Categories:**
- `docs:` - Documentation changes
- `feat:` - New features/fields
- `fix:` - Bug fixes
- `refactor:` - Structure improvements
- `chore:` - Maintenance tasks

### Step 2: Create Session Summary (MANDATORY)

**Location**: `Documentation/03_Progress_Tracking/SESSION_SUMMARY_[DATE]_[TOPIC].md`

**Template:**

```markdown
# SESSION SUMMARY - [DATE]
## [MAIN TOPIC]

**Session Duration**: [hours]
**Solution Version**: [before] → [after] (if changed)
**Focus**: [main objectives]
**Status**: [outcome]

---

## ✅ ACCOMPLISHED

- [Concrete deliverable 1]
- [Concrete deliverable 2]
- [Concrete deliverable 3]

## 🔑 KEY DECISIONS/INSIGHTS

- [Decision or realization 1]
- [Decision or realization 2]

## 📄 DOCUMENTS CREATED/UPDATED

| Document | Action | Location |
|----------|--------|----------|
| [Name] | Created/Updated | [Path] |

## ⏭️ NEXT STEPS

**Immediate:**
- [ ] [Next task 1]
- [ ] [Next task 2]

**Flagged for Future:**
- [ ] [Future task]

## 🚧 BLOCKERS/OPEN QUESTIONS

- [Any blocking issues]
- [Questions needing answers]

---

**Session Status**: Complete
**Next Priority**: [What to do next]
```

### Step 3: Update PROJECT_CONTEXT.json (MANDATORY)

**Option A: PowerShell Script**
```powershell
.\Scripts\PowerShell\Update-ProjectContext.ps1 -SessionTopic "Topic" -QuickUpdate
```

**Option B: Manual Update**
- Update `lastUpdated` timestamp
- Update `sessionId` to current date + topic
- Update `currentStatus` section
- Add any new `criticalFacts`

### Step 4: Solution Export (IF SCHEMA CHANGED)

**When to export:**
- Added/modified fields
- Added/modified tables
- Changed relationships
- Modified calculated fields
- Added views

**How to export:**
1. Power Apps → Solutions → RESAPowerProjectTracker
2. Export → Unmanaged
3. Save to `Solution_Exports/v{X.Y.Z.W}/`
4. Extract ZIP
5. Update version in PROJECT_CONTEXT.json

### Step 5: Verify Checklist

```
☐ All work committed to GitHub
☐ Session summary created
☐ PROJECT_CONTEXT.json updated
☐ Solution exported (if schema changed)
☐ No unsaved work in editors
☐ Can answer: "What accomplished? What's next?"
```

**If any item unchecked: Do not end session until fixed.**

---

## 🔄 CONTEXT RECOVERY

### If Starting Fresh (New Chat)

**Standard Opening:**

```
I'm working on the RESA Power Project Tracker.

Please read these files in order:
1. C:\RESA_Power_Build\PROJECT_CONTEXT.json
2. Most recent file in C:\RESA_Power_Build\Documentation\03_Progress_Tracking\

Then tell me:
- Current solution version
- What was accomplished last session
- What's flagged as next priority

Then ask what I'd like to work on.
```

### If Claude Says "I Don't Remember"

**Recovery Steps:**

1. Point to PROJECT_CONTEXT.json
2. Point to most recent session summary
3. Provide key facts:
   - Environment: org99cd6c6e.crm.dynamics.com
   - Version: v1.5.1.0
   - Tables: 16
   - Fields: 649

### If Documentation Conflicts

**Resolution Order:**
1. `Solution_Exports/v{latest}/customizations.xml` - Absolute truth for schema
2. `PROJECT_CONTEXT.json` - Truth for current state
3. Most recent session summary - Truth for recent work
4. Architecture documents - May be stale, verify against XML

---

## 🚨 CRITICAL KNOWLEDGE

### Facts That MUST Survive Every Session

1. **Environment URL**: org99cd6c6e.crm.dynamics.com (ONLY this one)

2. **Solution Version**: v1.5.1.0 (as of Nov 28, 2025)

3. **Table Count**: 16 tables (not 8 - that's outdated)

4. **Field Count**: 649 fields (not 137 - that's outdated)

5. **Revenue Flow**: WORKING (verified Nov 27, 2025)
   - Uses `empty()` function for null check
   - Creates ApparatusRevenue when Apparatus marked Complete

6. **BusinessUnit Entity is CRITICAL**
   - Represents multi-location architecture
   - Phoenix, Las Vegas, Denver, San Diego
   - DO NOT remove or deprecate

7. **API Naming**:
   - Query: PLURAL names (cr950_projectses)
   - Create: SINGULAR names (cr950_projects)

8. **Table Prefix**: cr950_

### Documents to Never Delete

| Document | Purpose |
|----------|---------|
| PROJECT_CONTEXT.json | Current state |
| MASTER_BUILD_SPECIFICATION.md | Complete schema |
| REVENUE_ARCHITECTURE.md | Financial system |
| REVENUE_RECOGNITION_FLOW_SPEC.md | Flow documentation |
| IMPORT_PIPELINE_SOP.md | Import process |
| This protocol | Session management |

---

## 🔧 TROUBLESHOOTING

### Problem: "Flow not triggering"

**Check:**
1. Is flow turned ON in Power Automate?
2. Is Completion_Status being set to 2 (Complete)?
3. Check flow run history for errors
4. Verify ScopeLaborDetail exists for the Scope

### Problem: "Can't connect to Dataverse"

**Check:**
1. Correct environment URL (org99cd6c6e.crm.dynamics.com)
2. .env file has correct credentials
3. Azure App Registration is valid
4. Token not expired

### Problem: "Import script failing"

**Check:**
1. JSON file exists and is valid
2. Node.js environment set up
3. .env file in correct location
4. Check for 401 (auth) or 400 (data) errors

### Problem: "Documentation is inconsistent"

**Resolution:**
1. customizations.xml is truth for schema
2. SESSION_SUMMARY is truth for recent work
3. Update stale documents or mark deprecated

---

## ✅ QUICK REFERENCE CHECKLIST

### Session Start
```
☐ Read PROJECT_CONTEXT.json
☐ Read most recent SESSION_SUMMARY
☐ State current version and status
☐ Confirm what user wants to work on
```

### Session End
```
☐ Git commit all changes
☐ Create session summary
☐ Update PROJECT_CONTEXT.json
☐ Export solution (if schema changed)
☐ Verify no unsaved work
```

### Before Dataverse Work
```
☐ Confirm environment: org99cd6c6e.crm.dynamics.com
☐ Know current version: v1.5.1.0
☐ Table prefix: cr950_
☐ API names: plural for query, singular for create
```

### Before Documentation Work
```
☐ Check if document exists
☐ Check version/date of existing doc
☐ Use proper naming convention
☐ Include header with version/date
```

---

## 📊 VERSION HISTORY SUMMARY

| Version | Date | Key Changes |
|---------|------|-------------|
| v1.0.0.0 - v1.3.0.4 | Oct-Nov 2025 | Foundation: 8 tables, 137 fields |
| v1.4.0.0 | Nov 22, 2025 | Added 6 tables: Client, Site, Employee, Quote, ResourceAssignment, Equipment |
| v1.5.0.0 | Nov 23, 2025 | Added 65 rollup fields, 2 financial summary tables |
| v1.5.0.1 | Nov 27, 2025 | Fixed revenue flow condition (empty() function) |
| v1.5.1.0 | Nov 28, 2025 | Added 10 views, Assigned Employee lookup |

---

**PROTOCOL STATUS**: Active  
**LAST UPDATED**: November 28, 2025  
**OWNER**: Jason Swenson + Claude AI  
**REVIEW FREQUENCY**: After each version bump or major session
