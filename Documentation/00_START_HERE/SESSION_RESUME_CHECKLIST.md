# SESSION RESUME CHECKLIST
## Quick Start Guide for Continuing Work on RESA Power Project Tracker

**Purpose**: This document provides a systematic verification process when resuming work, whether you're returning after a break or a new AI instance is picking up where the previous session left off.

**Last Updated**: November 22, 2025  
**Current Version**: v1.3.0.5 (importing to isolated dev environment)

**🚨 CRITICAL UPDATE**: Now using isolated personal dev environment (org99cd6c6e.crm.dynamics.com) after RESA IT deleted original environment. All MCP development happens here. Production deployments manual only.

---

## 🚀 QUICK START (30 Seconds)

### **Step 1: Verify Development Environment**
📄 **Location**: `Documentation/00_START_HERE/MY_DEV_ENVIRONMENT.md`

**What to verify**:
- ✅ Dev Environment: org99cd6c6e.crm.dynamics.com (YOUR safe environment)
- ❌ Production: org99cd6c6e.crm.dynamics.com (NEVER connect MCP here)
- ✅ Solution v1.3.0.5 imported
- ✅ Backups in 3 locations (local, GitHub, Box)

### **Step 2: Check Git Status**
```powershell
cd C:\RESA_Power_Build
git status
git log --oneline -5
```

**What to verify**:
- ✅ Working on `clean-main` branch
- ✅ Solution exports backed up
- ✅ Recent commits show v1.3.0.5

### **Step 3: Current Status**
📄 **Read**: `Documentation/00_START_HERE/PROJECT_STATUS_TRACKER.md`

**Current Focus** (Nov 22, 2025):
1. **Setting up isolated dev environment** (IN PROGRESS)
2. **Configuring Azure app registration** (NEXT)
3. **MCP server setup with safeguards** (NEXT)
4. **Test MCP connection safely** (NEXT)

---

## 📋 COMPREHENSIVE VERIFICATION CHECKLIST

### **Phase 1: Project Context Verification** (5 minutes)

#### **1.1 Environment Check**
```powershell
# DEVELOPMENT Environment (isolated, safe for MCP)
$env:DEV_DATAVERSE_URL = "https://org99cd6c6e.crm.dynamics.com"
$env:DEV_ENVIRONMENT_NAME = "Jason Swenson's Environment"

# PRODUCTION Environment (RESA, NEVER use with MCP)
$env:PROD_DATAVERSE_URL = "https://org99cd6c6e.crm.dynamics.com"

# Verify you're using DEV
Write-Host "Using DEV environment: $env:DEV_DATAVERSE_URL" -ForegroundColor Green
Write-Host "Production blocked for MCP: $env:PROD_DATAVERSE_URL" -ForegroundColor Red
```

**Expected**:
- ✅ Dev Environment: `org99cd6c6e.crm.dynamics.com`  
- ✅ Solution v1.3.0.5 in dev
- ❌ MCP NEVER points to production (org04ad071f)

**If not authenticated**:
```powershell
pac auth create --environment https://org99cd6c6e.crm.dynamics.com
```

---

#### **1.2 Current Version Verification**
📄 **Read**: `Documentation/00_START_HERE/PROJECT_STATUS_TRACKER.md` (Current State section)

**Verify these facts**:
- ✅ **Version**: v1.3.0.4 (production ready)
- ✅ **Tables**: 8 (BusinessUnit, Projects, ProjectScope, Tasks, Apparatus, ApparatusRevenue, ScopeLaborDetail, ApparatusTypeMaster)
- ✅ **Total Fields**: 137+ custom fields
- ✅ **Formulas**: 30 calculated columns operational
- ✅ **Flows**: 1 Power Automate flow (revenue recognition trigger)
- ✅ **Auditing**: Enabled on Nov 19, 2025

**If facts don't match**:
- Read latest session summary in `Documentation/03_Progress_Tracking/`
- Check git log for recent changes
- May need to export current solution to verify

---

#### **1.3 Critical Naming Conventions**
⚠️ **IMPORTANT**: Documentation was aligned Nov 19, 2025

**Correct Names** (as of v1.3.0.4):
| Original Spec | Actual Implementation | Status |
|--------------|----------------------|---------|
| "Location" | **"BusinessUnit"** | ✅ Corrected in v2.0 docs |
| "Scope_Financial_Config" | **"ScopeLaborDetail"** | ✅ Corrected in v2.0 docs |

**Field Counts** (actual vs original spec):
| Table | Original Spec | Actual v1.3.0.4 | Notes |
|-------|--------------|----------------|-------|
| Projects | 7 fields | **19 fields** | Includes 8 rollups |
| ProjectScope | 39 fields | **14 fields** | Original count was error |
| ScopeLaborDetail | 30 fields | **49 fields** | Complex financial config |

📄 **Reference**: `Documentation/01_Architecture/MASTER_BUILD_SPECIFICATION.md` (v2.0)

---

### **Phase 2: Documentation Currency Check** (3 minutes)

#### **2.1 Key Documents Status**

**Must-Read Documents** (in order):
1. ✅ **PROJECT_STATUS_TRACKER.md** (00_START_HERE) - Master navigation
2. ✅ **MASTER_BUILD_SPECIFICATION.md v2.0** (01_Architecture) - System design
3. ✅ **STATUS_FIELD_ARCHITECTURE.md** (01_Architecture) - Choice fields with state transitions
4. ✅ Latest Session Summary (03_Progress_Tracking) - Recent work context

**Quick Verification**:
```powershell
# Check when key docs were last updated
Get-ChildItem "C:\RESA_Power_Build\Documentation\00_START_HERE\PROJECT_STATUS_TRACKER.md" | Select-Object Name, LastWriteTime
Get-ChildItem "C:\RESA_Power_Build\Documentation\01_Architecture\MASTER_BUILD_SPECIFICATION.md" | Select-Object Name, LastWriteTime
Get-ChildItem "C:\RESA_Power_Build\Documentation\01_Architecture\STATUS_FIELD_ARCHITECTURE.md" | Select-Object Name, LastWriteTime
```

**Expected** (as of Nov 19, 2025):
- PROJECT_STATUS_TRACKER.md: Created Nov 19
- MASTER_BUILD_SPECIFICATION.md: Updated to v2.0 Nov 19
- STATUS_FIELD_ARCHITECTURE.md: Created Nov 19

**If dates are older**: Check `Documentation/03_Progress_Tracking/` for more recent session summaries

---

#### **2.2 Archive vs Current**

**Active Documentation** (use these):
- `Documentation/00_START_HERE/` - Navigation and quick references
- `Documentation/01_Architecture/` - System design and specifications
- `Documentation/02_Build_Guides/` - Implementation guides
- `Documentation/03_Progress_Tracking/` - Session summaries

**Archived Documentation** (reference only):
- `Documentation/99_Archive/` - Old versions, tone adjustments, migration docs

**Warning Signs of Outdated Info**:
- 🚫 References to "Location" table (should be BusinessUnit)
- 🚫 References to "Scope_Financial_Config" (should be ScopeLaborDetail)
- 🚫 Field counts: Projects=7, ProjectScope=39 (outdated)
- 🚫 Documents dated before Nov 15, 2025 (pre-Gap Analysis)

---

### **Phase 3: Technical State Verification** (5 minutes)

#### **3.1 Solution Export Check**

**Verify latest export exists**:
```powershell
# Check for solution export
Get-ChildItem "C:\RESA_Power_Build\Solution_Exports\v1.3.0.4\" -Recurse | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize
```

**Expected**:
- ✅ Folder: `Solution_Exports/v1.3.0.4/`
- ✅ Files: `RESA-Dev.zip` and `customizations.xml`
- ✅ Date: Nov 19, 2025 or later

**If missing or older**:
```powershell
# Export current solution
cd C:\RESA_Power_Build
pac solution export --name RESA-Dev --path ".\Solution_Exports\v1.3.0.4\RESA-Dev.zip" --managed false
```

---

#### **3.2 Choice Fields Verification**

📄 **Reference**: `Documentation/01_Architecture/STATUS_FIELD_ARCHITECTURE.md`

**Critical Choice Fields** (9 total):
1. **Project_Status** (4 values): Quoted → Planning → Active → Completed
2. **NETA_Standard** (2 values): ATS, MTS
3. **Task_Status** (4 values): Not Started → In Progress → Complete → Blocked
4. **Completion_Status** (5 values): Not Started → In Progress → Complete, On Hold, Cancelled
5. **Apparatus_Assessment** (3 values): Acceptable, Minor Deficiency, Non-Serviceable
6. **Witness_Test** (5 values): ATS, MTS, ECS, Spec, Other
7. **Revenue_Status** (6 proposed): NOT YET IMPLEMENTED
8. **Priority** (4 values): UNUSED - decision needed on removal
9. **Availability** (4 values): UNUSED - decision needed

**Verification Method**:
- Export solution and check customizations.xml for option sets
- Or check in Power Apps maker portal: Tables → [TableName] → Columns → [ChoiceField]

**If values don't match STATUS_FIELD_ARCHITECTURE.md**:
- User may have customized (this is okay)
- Update STATUS_FIELD_ARCHITECTURE.md with actual values
- Document in "Customization Log" section

---

#### **3.3 Formula and Rollup Verification**

📄 **Reference**: `Documentation/00_START_HERE/PROJECT_STATUS_TRACKER.md` (Current State section)

**Expected Counts**:
- ✅ **30 Formulas**: 28 documented in Master Index + 2 additional
- ✅ **Rollups**: 8 on Projects, 8 on ProjectScope (Date Tracking adds 18 more in v1.4.0.0)

**Quick Verification in Power Apps**:
1. Navigate to Power Apps maker portal
2. Tables → Projects → Columns
3. Filter by "Behavior" = "Calculated" or "Rollup"
4. Count should match expected

**If counts don't match**:
- User may have added/removed formulas
- Update PROJECT_STATUS_TRACKER.md "Current State" section
- Document changes in session summary

---

### **Phase 4: Work State Assessment** (5 minutes)

#### **4.1 Todo List Review**

📄 **Check**: Any todo list files or task tracking

**As of Nov 19, 2025**:
- ✅ Completed: Master Build Spec v2.0, Choice Field Architecture, Currency Verification
- ⏳ Pending: Date Tracking (spec complete), Revenue Rollups (needs requirements)

---

#### **4.2 Ready to Implement Assessment**

📄 **Reference**: `Documentation/00_START_HERE/PROJECT_STATUS_TRACKER.md` (Ready to Implement section)

**Available Tasks with Complete Specs**:

| Task | Time | Business Value | Spec Location | Status |
|------|------|---------------|---------------|--------|
| **Date Tracking** | 2.5-3 hrs | HIGH | DATE_TRACKING_IMPLEMENTATION.md | ✅ Ready |
| **Future-Proofing Fields** | 2-3 hrs | OPTIONAL | FUTURE_PROOFING_FIELDS_GUIDE.md | ✅ Ready (if integration planned) |

**Tasks Needing Requirements**:

| Task | Planning Time | Blockers |
|------|--------------|----------|
| **Revenue Rollups** | 1-2 hrs | Need business KPI requirements |
| **Forms/Views Specs** | 2-4 hrs | Low priority (current forms working) |
| **Dashboard Requirements** | 2-4 hrs | Need to understand current Excel KPIs |

---

#### **4.3 Blockers and Dependencies**

**Current Blockers** (as of Nov 19, 2025):
- ❌ None for Date Tracking implementation
- ⚠️ Revenue Rollups: Need answers to questions in PROJECT_STATUS_TRACKER.md "In Planning" section

**Dependencies to Check**:
```powershell
# Verify PAC CLI available
pac --version

# Verify solution connection
pac solution list

# Verify org connection
pac org who
```

**If dependencies missing**:
- Install Power Platform CLI: `winget install Microsoft.PowerPlatformCLI`
- Authenticate: `pac auth create --environment https://org99cd6c6e.crm.dynamics.com`

---

### **Phase 5: Decide Next Action** (2 minutes)

#### **5.1 Recommended Priority** (Nov 19, 2025)

**Option A: Date Tracking (v1.4.0.0)** ⭐ **RECOMMENDED**
- **Time**: 2.5-3 hours
- **Value**: HIGH (schedule visibility, capacity planning, KPI reporting)
- **Spec**: `Documentation/02_Implementation/DATE_TRACKING_IMPLEMENTATION.md`
- **Phases**: 
  1. Add 3 date fields to Apparatus (15 min)
  2. Add 6 rollup fields to Tasks (20 min)
  3. Add 6 rollup fields to ProjectScope (20 min)
  4. Add 6 rollup fields to Projects (20 min)
  5. Create 6 KPI views (30 min)
- **Why now**: Highest ROI, complete spec, no blockers

**Option B: Revenue Rollup Requirements Gathering**
- **Time**: 1-2 hours
- **Value**: MEDIUM-HIGH
- **Next Steps**: Answer questions in PROJECT_STATUS_TRACKER.md "In Planning" section
  - What revenue KPIs needed?
  - By project? By scope? By time period?
  - Historical trends needed?
- **Then**: Spec rollups (30-45 min), implement (30-45 min)

**Option C: Complete Master Build Spec v2.0**
- **Time**: 30 minutes
- **Value**: LOW (remaining sections follow established patterns)
- **Sections**: Tasks, Apparatus, ScopeLaborDetail
- **Why later**: Documentation maintenance, not blocking

---

#### **5.2 Implementation Workflow**

**For Date Tracking (Recommended)**:

1. **Review Spec** (5 min):
   ```powershell
   # Read the implementation guide
   code "C:\RESA_Power_Build\Documentation\02_Implementation\DATE_TRACKING_IMPLEMENTATION.md"
   ```

2. **Phase 1: Apparatus Date Fields** (15 min):
   - Navigate to Power Apps maker portal
   - Tables → Apparatus → Columns → + New column
   - Add: Anticipated_Start_Date, Actual_Start_Date, Date_Completed (all Date Only type)

3. **Phase 2-4: Rollup Fields** (60 min):
   - Follow DATE_TRACKING_IMPLEMENTATION.md step-by-step
   - 6 rollups per table (Tasks, ProjectScope, Projects)
   - Pattern: Earliest_Anticipated_Start, Earliest_Actual_Start, etc.

4. **Phase 5: KPI Views** (30 min):
   - Create 6 views per spec
   - Upcoming Work (Anticipated Start next 14 days)
   - Overdue (Date Completed null, Anticipated Start < today)
   - Etc.

5. **Export and Test** (30 min):
   - Export as v1.4.0.0
   - Import to test environment
   - Verify rollups calculate correctly
   - Test views with sample data

6. **Commit and Document** (15 min):
   - Git commit solution export
   - Create session summary
   - Update PROJECT_STATUS_TRACKER.md

---

## 🔍 VERIFICATION QUICK REFERENCE

### **"Is This Document Current?" Test**

**Green Flags** ✅:
- Uses "BusinessUnit" (not "Location")
- Uses "ScopeLaborDetail" (not "Scope_Financial_Config")
- Field counts: Projects=19, ProjectScope=14, ScopeLaborDetail=49
- Dated Nov 15, 2025 or later
- References v1.3.0.4 or later
- Located in active documentation folders (not 99_Archive)

**Red Flags** 🚫:
- Uses "Location" table name
- Uses "Scope_Financial_Config" table name
- Field counts: Projects=7, ProjectScope=39
- Dated before Nov 15, 2025 (pre-Gap Analysis)
- References v1.2.x or earlier
- Located in 99_Archive folder

---

### **"What Should I Work On?" Decision Tree**

```
START
  │
  ├─ Need to understand project? 
  │    └─ YES → Read PROJECT_STATUS_TRACKER.md → Read latest session summary
  │    └─ NO → Continue
  │
  ├─ Ready to implement features?
  │    └─ YES → Date Tracking ready (2.5-3 hrs, high value)
  │    └─ NO → Continue
  │
  ├─ Need to gather requirements?
  │    └─ YES → Revenue Rollups planning (1-2 hrs)
  │    └─ NO → Continue
  │
  ├─ Documentation maintenance?
  │    └─ YES → Complete Master Spec sections (30 min)
  │    └─ NO → Continue
  │
  └─ Not sure? → Read latest session summary in 03_Progress_Tracking/
```

---

## 📞 TROUBLESHOOTING

### **Problem: Can't authenticate to environment**
```powershell
# Clear existing auth
pac auth clear

# Re-authenticate
pac auth create --environment https://org99cd6c6e.crm.dynamics.com

# Verify
pac org who
```

---

### **Problem: Documentation seems outdated**
1. Check `Documentation/03_Progress_Tracking/` for latest session summary
2. Check git log: `git log --oneline -10`
3. Look for dates Nov 15 or later (Gap Analysis alignment)
4. If using pre-Nov 15 docs, they may have outdated table names

---

### **Problem: Field counts don't match specs**
1. This is OKAY if user customized
2. Export current solution: `pac solution export --name RESA-Dev`
3. Count actual fields in Power Apps maker portal
4. Update PROJECT_STATUS_TRACKER.md "Current State" section
5. Document changes in new session summary

---

### **Problem: Choice field values different than documented**
1. This is OKAY - user customizations are valid
2. Export solution and check customizations.xml
3. Update STATUS_FIELD_ARCHITECTURE.md with actual values
4. Add entry to "Customization Log" section explaining change

---

### **Problem: Not sure what version is deployed**
```powershell
# Check solution version in environment
pac solution list

# Check latest export folder
Get-ChildItem "C:\RESA_Power_Build\Solution_Exports\" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

---

### **Problem: Memory MCP not available in current session**

**Background**: Memory MCP server is configured in Claude Desktop config (`Documentation/claude_desktop_config.json`) but only loads for fresh chat sessions.

**Status** (as of Nov 19, 2025):
- ✅ Memory MCP server is configured correctly via npx
- ✅ Server auto-starts when Claude Desktop launches
- ✅ Configuration uses: `npx -y @modelcontextprotocol/server-memory`
- ⚠️ Tools only available in NEW chat sessions (not existing sessions)

**To Test Memory MCP** (for next session):
1. Start a fresh Claude Desktop chat
2. Type: "Can you create a memory entity?"
3. If memory tools are available, you'll see tool options

**Memory MCP Tools** (when available):
- `create_entities` - Store project facts/decisions
- `create_relations` - Link related concepts
- `search_nodes` - Retrieve stored information
- `open_nodes` - Access specific memories
- `delete_entities` - Remove outdated information

**Current Approach**:
- This project uses **file-based documentation** instead of Memory MCP
- Documentation system is actually **better suited** for complex projects
- Reasons:
  - Git version control for all documentation
  - Easy to review/diff changes over time
  - Searchable with grep/semantic search
  - Portable across AI sessions and human review
  - No dependency on specific MCP availability

**Verdict**: Memory MCP works correctly but is optional. Documentation system provides superior continuity for this project type.

---

## 🎯 SUCCESS CRITERIA

**Before starting work, verify**:
- ✅ Read latest session summary
- ✅ Git on clean-main branch, no unexpected changes
- ✅ Know current version (v1.3.0.4 as of Nov 19)
- ✅ Understand table naming (BusinessUnit, ScopeLaborDetail)
- ✅ Identified next task from PROJECT_STATUS_TRACKER.md
- ✅ Have spec document for chosen task (if implementing)
- ✅ PAC CLI authenticated to environment

**After completing work, verify**:
- ✅ Solution exported with new version number
- ✅ Git committed with descriptive message
- ✅ Session summary created in 03_Progress_Tracking/
- ✅ PROJECT_STATUS_TRACKER.md updated (mark completed, note changes)
- ✅ No uncommitted changes (or documented why)

---

## 📚 ESSENTIAL READING ORDER

**For New AI Instance Starting Work**:
1. **This document** (SESSION_RESUME_CHECKLIST.md) - 15 min
2. **Latest session summary** (03_Progress_Tracking/) - 10 min
3. **PROJECT_STATUS_TRACKER.md** (00_START_HERE/) - 15 min
4. **Spec for chosen task** (e.g., DATE_TRACKING_IMPLEMENTATION.md) - 20 min

**Total**: ~60 minutes to be fully oriented and ready to implement

---

## 🔄 SESSION END PROTOCOL

**When finishing work** (either human or AI):

1. **Export Solution** (if changes made):
   ```powershell
   pac solution export --name RESA-Dev --path ".\Solution_Exports\v1.X.X.X\RESA-Dev.zip" --managed false
   ```

2. **Commit to Git**:
   ```powershell
   git add .
   git commit -m "feat/docs/fix: [description]"
   git push origin clean-main
   ```

3. **Create Session Summary**:
   - File: `Documentation/03_Progress_Tracking/SESSION_SUMMARY_[DATE]_[TOPIC].md`
   - Include: Accomplished, decisions, next steps, blockers

4. **Update PROJECT_STATUS_TRACKER.md**:
   - Move completed items from "Ready to Implement" to "Current State"
   - Update field counts if changed
   - Add notes about decisions made

5. **Verify Checklist**:
   - □ Solution exported (if changed)
   - □ Git committed and pushed
   - □ Session summary created
   - □ Status tracker updated
   - □ No loose ends documented

---

**END OF RESUME CHECKLIST**

*Use this document at the start of every session to ensure continuity and avoid confusion.*
