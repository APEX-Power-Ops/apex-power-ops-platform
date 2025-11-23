# RESA Power Build - Complete Folder Structure Guide
**Last Updated**: November 23, 2025  
**Purpose**: Master reference for project organization

---

## 🎯 Overview

This document provides a comprehensive guide to the RESA Power Build project structure. After extensive cleanup on Nov 23, 2025, the project now has a clean, professional organization with clear separation between active and historical artifacts.

---

## 📁 ROOT DIRECTORY

**Essential Files Only** (Nov 23 cleanup - removed 10+ temp/old files)

```
RESA_Power_Build/
├── .gitignore                        # Git ignore patterns (updated with security rules)
├── PROJECT_CONTEXT.json              # Session continuity, AI context (16 tables, org99cd6c6e)
├── PROJECT_OVERVIEW.md               # Quick project reference
├── README.md                         # GitHub repository documentation
├── RESA_Power_Build.cdsproj          # Dataverse solution project file
└── RESA_Power_Build.code-workspace   # VS Code workspace configuration
```

**Removed from Root** (Nov 23):
- Credential files (moved to Documentation/99_Archive/Credentials/)
- Temporary notes (deleted: "I'm working on...", "The 401 error...")
- Old documentation (moved to 99_Archive/Old_Documentation/)
- Sensitive files (deleted: RESA-Dev-MCP-Access.txt)

---

## 📂 DOCUMENTATION/ (Primary Navigation Hub)

Organized by category (00-11 numbered folders + 99_Archive):

### **00_Project_Protocol/** - AI Session Management
```
├── PROJECT_CONTINUITY_PROTOCOL.md    # AI context management guidelines
```
**Purpose**: Guidelines for maintaining context across AI sessions
**Updated**: Nov 23 (environment aligned to org99cd6c6e)

### **00_START_HERE/** - Essential Onboarding
```
├── ACCELERATED_DEVELOPMENT_ENVIRONMENT_BLUEPRINT.md
├── AZURE_APP_REGISTRATION_GUIDE.md
├── CLAUDE_SESSION_ARTIFACTS_CATALOG.md
├── DATAVERSE_ACCESS_QUICK_REFERENCE.md
├── DATAVERSE_MCP_SETUP.txt            # Moved from root Nov 23
├── ENVIRONMENT_CONFIG_CORRECTED.md     # Single environment reference
├── FOLDER_STRUCTURE.md                 # This file
├── MEMORY_MCP_TESTING_GUIDE.md
├── MY_DEV_ENVIRONMENT.md
├── PLATFORM_ROADMAP_STRATEGIC_VISION.md
├── PROJECT_GUIDELINES_AND_WORKFLOWS.md
├── PROJECT_STATUS_TRACKER.md
├── QUICK_DOCUMENTATION_INDEX.md
├── Quick_Reference_Cheat_Sheet.md
├── REVENUE_ARCHITECTURE_QUICK_REFERENCE.md
├── SESSION_RESUME_CHECKLIST.md
├── START_HERE_Build_Guide.md
├── UPDATE_CONTEXT_GUIDE.md
└── VSCODE_SESSION_CONTINUITY.md
```
**Purpose**: First stop for new developers or resuming sessions
**Updated**: Nov 23 (all files audited, environment references corrected)

### **01_Architecture/** - System Design
```
├── Architecture_Diagrams.md
├── Desktop_Platform_Strategy.md
└── (other architecture docs)
```
**Purpose**: System architecture, design decisions, technical blueprints

### **02_Build_Guides/** - Implementation Guides
**Purpose**: Step-by-step build instructions, setup guides

### **02_Implementation/** - Implementation Details
**Purpose**: Detailed implementation documentation

### **03_Progress_Tracking/** - Status & Progress
```
├── DOCUMENTATION_AUDIT_SUMMARY_NOV23.md  # Nov 23 audit trail
├── V1_4_0_0_ROADMAP_AND_PRIORITIES.md    # Current roadmap
└── (other progress docs)
```
**Purpose**: Track development progress, milestones, audit trails
**Recent**: Documentation audit summary (Nov 23) - 75+ references corrected

### **04_Data_Migration/** - Data Transfer
**Purpose**: Data migration scripts, mapping documents, CSV processing

### **05_Reviews_Analysis/** - Code Reviews & Analysis
**Purpose**: Code reviews, architecture analysis, technical assessments

### **06_Implementation_Guides/** - How-To Guides
```
├── MANUAL_ROLLUP_FIELD_CREATION_GUIDE.md  # Updated Nov 23 (field names corrected)
└── (other implementation guides)
```
**Purpose**: Detailed how-to guides for specific implementations

### **06_MCP_Automation/** - MCP Server Documentation
```
├── MCP_SERVER_EXECUTIVE_SUMMARY.md
├── MCP_SERVER_QUICK_START.md       # Updated Nov 23 (credentials corrected)
└── (MCP-related docs)
```
**Purpose**: Model Context Protocol server documentation
**Status**: Ready for Monday MCP development

### **07_Application_Specs/** - Application Specifications
**Purpose**: Detailed application specifications, requirements

### **08_Testing_QA/** - Testing & Quality Assurance
**Purpose**: Test plans, QA procedures, validation results

### **09_Training_Materials/** - User Training
**Purpose**: Training guides, user documentation, tutorials

### **10_Analytics_Reporting/** - Analytics & Reports
**Purpose**: Analytics definitions, report specifications, Power BI documentation

### **11_Mobile_Apps/** - Mobile Application
**Purpose**: Mobile app design, development documentation

### **99_Archive/** - Historical Reference
```
├── Credentials/                    # Created Nov 23
│   ├── .gitignore                 # Ignore all files in this directory
│   ├── Github_generate_token.pdf
│   ├── RESA-Dev-MCP-Access Certificates & Secrets.pdf
│   └── RESA-Dev-MCP-Access.pdf
│
├── Old_Documentation/             # Created Nov 23
│   ├── API formatting for Column Creation.md
│   ├── Claude Chat Session overview 1121225.md
│   ├── CREDENTIALS_AND_ENVIRONMENT_ANALYSIS_OUTDATED.md
│   ├── D365_Project_Operations_Integration_Analysis.md
│   └── RESA_Power_Project_MASTER_REFERENCE.md
│
└── (other archived documents)
```
**Purpose**: Historical artifacts, outdated documents, superseded guides
**Security**: Credentials/ folder excluded from git via .gitignore

---

## 📜 SCRIPTS/ - Automation & Utilities

**Organized Structure** (Nov 23 cleanup):

### **PowerShell/** - Main PowerShell Scripts
```
PowerShell/
├── Dataverse-Functions.ps1         # Core function library (stays in root)
│
├── Active/                         # Current use scripts
│   ├── Test-DataverseConnection.ps1
│   ├── Test-MCPAuthentication.ps1
│   ├── Update-Documentation-Environments.ps1  # Created Nov 23
│   ├── Verify-ApparatusDateFields.ps1
│   ├── Update-ProjectContext.ps1
│   ├── Field_Creation_Manual_Guide.ps1        # Updated Nov 23 (org99cd6c6e)
│   ├── Fix-API-Permissions-Guide.ps1
│   ├── Import-DataverseTables.ps1
│   └── Implement-KPIFields.ps1
│
├── Archive/                        # Completed task scripts
│   ├── Add-V1.4.0.0-Lookups.ps1           # COMPLETED
│   ├── Add-DateTrackingFields.ps1          # COMPLETED Nov 23
│   ├── Create-FinancialSummaryTables.ps1   # COMPLETED
│   ├── Create-NewDataverseTables.ps1       # COMPLETED
│   ├── Add_Future_Proofing_Fields.ps1      # COMPLETED
│   ├── Add_Future_Proofing_Fields_PAC.ps1  # COMPLETED
│   ├── Delete-RollupFieldContainers.ps1    # COMPLETED
│   ├── create_tables_webapi.ps1            # COMPLETED
│   └── fix_solution_xml.ps1                # COMPLETED
│
├── Rollup_Scripts/                 # Upcoming v1.5.0.0 implementation
│   ├── Add-RollupFields-FullyConfigured.ps1
│   ├── Add-RollupFields.ps1
│   ├── Create-RollupFields-Complete.ps1
│   ├── Create-RollupFields-Guide.md
│   └── KPI_FIELDS_README.md
│
└── Templates/                      # Reusable script templates
```

**Environment**: All active scripts updated to org99cd6c6e (Nov 23)  
**Documentation**: Scripts/README.md (created Nov 23)

### **Python/** - Python Scripts
```
├── migrate_data.py                 # Data migration utility
```

### **Archived/** - Historical Scripts
**Purpose**: Old scripts from previous iterations

---

## 📊 LOGS/ - Application Logs

**Clean Structure** (Nov 23 cleanup):

```
Logs/
├── .gitignore                                      # Exclude system logs
├── README.md                                       # Retention policy (Nov 23)
│
├── Apparatus_DateFields_20251123_112718.json      # Nov 23 verification
├── Apparatus_DateFields_20251123_114037.json      # Nov 23 verification
└── (other recent logs <30 days)
│
└── Archive/                                        # Historical logs
    ├── DateTrackingFields_20251122_185426.json    # Archived Nov 23
    ├── FinancialSummaryTables_20251122_185447.json
    ├── FinancialSummaryTables_20251122_185535.json
    └── (other archived logs)
```

**Retention Policy** (Nov 23):
- **Root**: Last 30 days + milestone verifications
- **Archive**: 30-90 days old
- **Delete**: >90 days (optional, unless milestone)

**Types**:
- `.json` - Verification results (field audits, table checks)
- `.log` - System logs (MCP server, Claude Desktop, runtime)

---

## 📦 SOLUTION_EXPORTS/ - Dataverse Solution Versions

**Organized by Version** (Nov 23 cleanup):

```
Solution_Exports/
├── README.md                                   # Quick reference (Nov 23)
├── VERSION_HISTORY.md                          # Complete version docs (Nov 23)
│
├── RESAPowerProjectTracker_1_4_0_0.zip        # Current ZIP export
├── RESAPowerProjectTracker_1_3_0_5.zip        # Rollback ZIP
│
├── v1.4.0.0/                                  # CURRENT (Nov 22, 2025)
│   ├── [Content_Types].xml
│   ├── customizations.xml                     # 16 tables definition
│   ├── solution.xml
│   └── ... (other export files)
│
├── v1.3.0.5/                                  # ROLLBACK (Nov 14, 2025)
│   └── ... (14 tables - safety net)
│
└── Archive/                                   # Historical versions
    ├── v1.3.0.1/                              # Archived Nov 23
    ├── v1.3.0.2/                              # Archived Nov 23
    ├── v1.3.0.3/                              # Archived Nov 23
    └── v1.3.0.4/                              # Archived Nov 23
```

**Retention Policy**:
- **Active**: Current version (v1.4.0.0) + last stable rollback (v1.3.0.5)
- **Archive**: Older versions (reference only)
- **Delete**: >6 months or superseded (optional)

**Version Numbering**: `v{MAJOR}.{MINOR}.{PATCH}.{BUILD}`

---

## 📁 OTHER KEY DIRECTORIES

### **CSV_Templates/** - Data Import Templates
```
├── 00_Locations_Template.csv
├── 01_Projects_Template.csv
├── 02_Scopes_Template.csv
├── 03_Tasks_Template.csv
├── 04_Apparatus_Template.csv
├── 04_Apparatus_Type_Master.csv
├── 05_Scope_Financial_Config_Template.csv
├── 06_Apparatus_Revenue_Template.csv
├── README.md
└── New_Tables/                     # Templates for 6 new tables
```
**Purpose**: CSV templates for bulk data import to Dataverse

### **Import_Data/** - Active Data Files
```
├── Project_Import.csv
├── Scopes_Import.csv
└── Tasks_Import.csv
```
**Purpose**: Active data files ready for import

### **LASNAP16/** - Excel Reference Files
```
├── GSL - Switch Estimator (Updated).xlsm
├── LASNAP16_Dashbaord.pbit
└── RESA Power - LASNAP16 MASTER.xlsm
```
**Purpose**: Original Excel application reference, Power BI dashboard

### **MCP_Servers/** - Model Context Protocol Servers
```
├── README.md
└── resa-dataverse-mcp/             # Dataverse MCP server implementation
    ├── src/
    ├── package.json
    └── (server code)
```
**Purpose**: MCP server implementations for AI integrations
**Status**: Ready for Monday development

### **Reference_Files/** - Reference Materials
```
├── Diagrams/                       # Architecture diagrams, flowcharts
├── Excel/                          # Excel reference files
├── PDFs/                           # PDF documentation
└── PowerBI/                        # Power BI report files
```
**Purpose**: Reference materials, examples, specifications

### **Working/** - Temporary Working Files
**Purpose**: Temporary workspace for active development (not committed to git)

---

## 🔒 SECURITY & GIT

### **.gitignore** (Updated Nov 23)

**Added Security Patterns**:
```gitignore
# === SENSITIVE CREDENTIALS ===
**/Credentials/
RESA-Dev-MCP-Access.txt
**/MCP-Access*.txt
*.env
.env.local
**/*secret*.txt
**/*password*.txt
**/*token*.txt
**/claude_desktop_config.json

# === TEMPORARY FILES ===
I'm working on*.txt
The *error*.txt
**/*temp*.txt
```

**Additional Ignores**:
- `Logs/` - System logs excluded from git
- `Working/` - Temporary files excluded
- `.vs/`, `.vscode/settings.json` - IDE-specific files

### **Credential Management** (Nov 23)
- ✅ Credential PDFs moved to `Documentation/99_Archive/Credentials/`
- ✅ Credentials folder has `.gitignore` (ignore all files)
- ✅ Deleted `RESA-Dev-MCP-Access.txt` (sensitive secrets)
- ✅ All credential patterns added to root `.gitignore`
- ✅ No sensitive files tracked in git

---

## 📊 PROJECT STATISTICS (Nov 23, 2025)

### **Solution**
- **Version**: v1.4.0.0
- **Tables**: 16 (8 core + 6 new + 2 financial)
- **Fields**: 291+
- **Lookups**: 10 operational relationships
- **Formulas**: 30 formula fields
- **Environment**: org99cd6c6e.crm.dynamics.com (ONLY active environment)

### **Documentation**
- **Folders**: 13 categories (00-11 + 99_Archive)
- **Status**: ✅ CLEAN (Nov 23 audit - 75+ outdated references removed)
- **Key Files**: 40+ active guides, 10+ archived
- **Audit**: Complete trail in DOCUMENTATION_AUDIT_SUMMARY_NOV23.md

### **Scripts**
- **Active**: 9 current use scripts
- **Archived**: 9 completed task scripts
- **Rollup**: 5 scripts ready for v1.5.0.0
- **Status**: ✅ ORGANIZED (Nov 23 - environment updated, structured)

### **Logs**
- **Recent**: 2 Nov 23 verification results + system logs
- **Archived**: 3 historical verifications
- **Policy**: 30-day retention in root
- **Status**: ✅ CLEAN (Nov 23 - retention policy established)

### **Solution Exports**
- **Active**: 2 versions (v1.4.0.0 current, v1.3.0.5 rollback)
- **Archived**: 4 old versions (v1.3.0.1-4)
- **Status**: ✅ ORGANIZED (Nov 23 - version history documented)

---

## 🗓️ CLEANUP HISTORY

### **November 23, 2025 - Complete Project Cleanup**

**Phase 1: Root Directory** (30-60 min)
- ✅ Moved credential PDFs to 99_Archive/Credentials/
- ✅ Deleted sensitive RESA-Dev-MCP-Access.txt
- ✅ Archived 4 old documentation files
- ✅ Deleted 5 temporary files
- ✅ Updated .gitignore with security patterns
- **Result**: Clean root with only 6 essential files

**Phase 2: Scripts Folder** (45-90 min)
- ✅ Created Active/, Archive/, Rollup_Scripts/ structure
- ✅ Archived 9 completed task scripts
- ✅ Organized 9 active scripts
- ✅ Updated 2 scripts: orgf05a3756 → org99cd6c6e
- ✅ Created Scripts/README.md
- **Result**: Clear separation of current vs historical scripts

**Phase 3: Logs Folder** (20-30 min)
- ✅ Created Logs/Archive/ folder
- ✅ Archived logs older than Nov 23
- ✅ Created Logs/README.md (retention policy)
- ✅ Created Logs/.gitignore
- **Result**: Clean logs with 30-day retention policy

**Phase 4: Solution_Exports** (30-45 min)
- ✅ Created Solution_Exports/Archive/ folder
- ✅ Archived v1.3.0.1-4 (kept v1.3.0.5 for rollback)
- ✅ Created VERSION_HISTORY.md
- ✅ Created README.md
- **Result**: Clear current vs rollback vs historical versions

**Phase 5: Documentation Audit** (2-3 hours earlier in day)
- ✅ Updated 13 core documentation files
- ✅ Removed 50+ outdated environment references
- ✅ Removed 25+ old credential references
- ✅ Corrected 13 table count errors (14 → 16)
- ✅ Created automation script (Update-Documentation-Environments.ps1)
- ✅ Created comprehensive audit summary
- **Result**: Zero ambiguity, single environment reference everywhere

**Total Time Invested**: ~5-7 hours  
**Total Files Modified**: 40+ files  
**Total Files Archived**: 18+ files  
**Total Files Deleted**: 6 sensitive/temp files  
**Git Commits**: 4 major commits

---

## 🚀 FOLDER USAGE GUIDELINES

### **When Adding New Files**

**Documentation**:
- Current guides → `Documentation/00_START_HERE/`
- Build guides → `Documentation/02_Build_Guides/`
- Progress tracking → `Documentation/03_Progress_Tracking/`
- Old/superseded → `Documentation/99_Archive/`

**Scripts**:
- Active development → `Scripts/PowerShell/Active/`
- Completed tasks → `Scripts/PowerShell/Archive/`
- Reusable patterns → `Scripts/PowerShell/Templates/`
- Upcoming features → Specific subfolder (e.g., Rollup_Scripts/)

**Logs**:
- Current verifications → `Logs/` (root)
- Old logs (>30 days) → `Logs/Archive/`

**Solution Exports**:
- New version → `Solution_Exports/v{VERSION}/`
- Old versions → `Solution_Exports/Archive/`

### **When Cleaning Up**

**Monthly Tasks**:
- Archive logs >30 days old
- Review Scripts/Active/ for completed tasks
- Update VERSION_HISTORY.md if new solution exported
- Update PROJECT_CONTEXT.json with current state

**Quarterly Tasks**:
- Review Documentation/99_Archive/ (delete if >6 months)
- Review Solution_Exports/Archive/ (delete if superseded)
- Review Scripts/Archive/ (delete if no longer relevant)
- Update this FOLDER_STRUCTURE.md if organization changes

**Security Checks**:
- Verify no sensitive files in git: `git status | Select-String credential`
- Check .gitignore effectiveness: `git ls-files | Select-String password`
- Ensure Credentials/ folder excluded from commits

---

## 📋 QUICK NAVIGATION

**Starting a New Session?**
1. Read `PROJECT_CONTEXT.json` (current state)
2. Check `Documentation/00_START_HERE/SESSION_RESUME_CHECKLIST.md`
3. Review `Documentation/00_START_HERE/PROJECT_STATUS_TRACKER.md`

**Need Documentation?**
1. Start: `Documentation/00_START_HERE/QUICK_DOCUMENTATION_INDEX.md`
2. Implementation: `Documentation/06_Implementation_Guides/`
3. Architecture: `Documentation/01_Architecture/`

**Running Scripts?**
1. Active scripts: `Scripts/PowerShell/Active/`
2. Core library: `Scripts/PowerShell/Dataverse-Functions.ps1`
3. Reference: `Scripts/README.md`

**Looking for Old Versions?**
1. Documentation: `Documentation/99_Archive/`
2. Scripts: `Scripts/PowerShell/Archive/`
3. Solutions: `Solution_Exports/Archive/`
4. Logs: `Logs/Archive/`

---

## 🎯 FOLDER ORGANIZATION PRINCIPLES

**Established Nov 23, 2025:**

1. **Separation of Concerns**: Active vs Archive vs Historical
2. **Clear Retention Policies**: 30 days (logs), 2 versions (solutions)
3. **Security First**: Credentials excluded from git, sensitive patterns ignored
4. **Documentation Everything**: Every folder has README.md
5. **Environment Consistency**: One environment (org99cd6c6e) everywhere
6. **Numbered Categories**: Documentation folders 00-11 (easy navigation)
7. **Archive Pattern**: 99_Archive for historical reference
8. **Clean Root**: Only essential project files in root directory

---

## 📞 SUPPORT & REFERENCES

**Key Documents**:
- Environment setup: `ENVIRONMENT_CONFIG_CORRECTED.md`
- Session resume: `SESSION_RESUME_CHECKLIST.md`
- Current status: `PROJECT_STATUS_TRACKER.md`
- MCP servers: `MCP_SERVER_QUICK_START.md`
- This guide: `FOLDER_STRUCTURE.md`

**Current Environment** (Nov 23, 2025):
- URL: https://org99cd6c6e.crm.dynamics.com
- Tenant: 270d5723-4b30-4f3b-b9cb-6527be741b42
- Client ID: 9df3350f-b3b4-47c4-97b5-499a8b02acc7
- App: RESA-Dev-MCP-Access

**Next Major Milestones**:
1. Build resa-testing-mcp server (20-30 hours)
2. Implement 32 rollup fields (3-5 hours)
3. Create 6 KPI views (1 hour)
4. Release v1.5.0.0 (early Dec 2025)

---

**Document Created**: November 23, 2025  
**Last Cleanup**: November 23, 2025  
**Next Review**: December 23, 2025  
**Status**: ✅ COMPLETE - Project ready for intensive development phase
