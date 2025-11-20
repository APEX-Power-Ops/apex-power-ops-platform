# PROJECT CONTINUITY PROTOCOL
## RESA Power Project Tracker - Session Management & Knowledge Transfer

**Purpose**: Ensure zero knowledge loss between sessions, consistent documentation, and seamless continuity  
**Last Updated**: November 19, 2025  
**Version**: 1.3

---

## 🎯 PROJECT IDENTITY

### **Project Name**: RESA Power Project Tracker
### **Technology**: Microsoft Dataverse (Power Platform)
### **Environment**: RESAPowerPM (orgf05a3756.crm.dynamics.com)
### **Environment ID**: 7f8ca9fd-86dd-ec35-8967-888a63ed3c09
### **Organization ID**: 2a43137f-f9c3-f011-a9f5-6045bd003e31
### **Solution Name**: RESAPowerProjectTracker (Unmanaged)
### **Version**: v1.3.0.4 (exported successfully Nov 19, 2025)
### **Dataverse Version**: 9.2.25111.151
### **Repository**: https://github.com/jasonlswenson-sys/RESA-Power-Project-Management
### **Primary User**: Jason Swenson (Project Manager, Phoenix Services)
### **Organization**: RESA Power - Southwest Region (Phoenix, Las Vegas, Denver, San Diego)
### **Auditing**: Enabled (Forever retention)

---

## 📁 FILE ORGANIZATION STRUCTURE

### **Root Directory**: `C:\RESA_Power_Build\`

```
C:\RESA_Power_Build\
├── Documentation/
│   ├── 00_Project_Protocol/          ← YOU ARE HERE (Session management, protocols)
│   │   └── PROJECT_CONTINUITY_PROTOCOL.md
│   │
│   ├── 01_Architecture/              ← System design, personas, decisions
│   │   └── USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md (7 personas, 5 decisions)
│   │
│   ├── 02_Reviews_Analysis/          ← Gap analysis, field catalogs, inventories
│   │   ├── GAP_ANALYSIS_FINAL_REPORT.md (v1.2.0.3 complete analysis)
│   │   ├── V1_2_0_3_COMPLETE_FIELD_CATALOG.md (137 fields)
│   │   ├── CALCULATED_FIELDS_FORMULAS.md (28 formulas)
│   │   ├── CHOICE_FIELDS_OPTIONSETS.md (8 option sets)
│   │   └── DATA_VERIFICATION_FINDINGS.md (clean slate discovery)
│   │
│   ├── 03_Progress_Tracking/         ← Session summaries, status reports
│   │   ├── SESSION_SUMMARY_NOV15_ARCHITECTURAL_FOUNDATION.md
│   │   └── v1_2_0_2_Session_Artifacts/ (historical)
│   │
│   ├── 04_Data_Migration/            ← Excel analysis, migration scripts
│   │   └── EXCEL_ARCHITECTURE_ANALYSIS_COMPLETE.md
│   │
│   ├── 05_Build_Guides/              ← How-to guides, checklists
│   │   ├── COMPREHENSIVE_AUDIT_CHECKLIST.md
│   │   ├── ARCHITECTURE_CLEANUP_GUIDE.md
│   │   └── Export_Forms_Guide.md
│   │
│   ├── 06_Implementation_Guides/     ← Step-by-step implementation docs
│   │   └── (future: field additions, flow builds, etc.)
│   │
│   ├── 07_Application_Specs/         ← UI/UX specifications
│   │   └── FIELD_TECH_APPLICATION_SPEC.md (mobile app design)
│   │
│   └── 08_MCP_Automation/            ← Automation scripts
│       └── Export_Dataverse_Tables.ps1
│
├── Reference_Files/                   ← Source materials (DO NOT MODIFY)
│   ├── Dataverse_Solutions/
│   │   └── RESAPowerProjectTracker_1_1_0_1.zip (v1.2.0.3 export)
│   ├── Excel/
│   │   └── Project Tracker VBA Modules/ (11 .bas files)
│   └── Scripts/
│       └── LASNAP16_Import_C#_PowerBI.txt
│
└── Working_Files/                     ← Temporary/scratch work
    └── (exports, temp analysis, etc.)
```

---

## 📋 DOCUMENTATION STANDARDS

### **File Naming Convention**:
```
[CATEGORY]_[DESCRIPTION]_[VERSION].md

Examples:
✅ GAP_ANALYSIS_FINAL_REPORT.md
✅ SESSION_SUMMARY_NOV15_ARCHITECTURAL_FOUNDATION.md
✅ USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md
✅ FIELD_TECH_APPLICATION_SPEC.md

❌ gap analysis.md (no spaces)
❌ notes.txt (no context)
❌ temp_doc_v3_final_FINAL.md (version chaos)
```

### **Document Header Template**:
```markdown
# [DOCUMENT TITLE]

**Purpose**: [Why this document exists]  
**Created**: [Date]  
**Last Updated**: [Date]  
**Version**: [X.Y - description of version]  
**Status**: [Draft/In Progress/Complete/Archived]

---
```

### **Markdown Standards**:
- Use `##` for major sections
- Use `###` for subsections
- Use `####` for detailed breakdowns
- Code blocks: Use ` ```language ` for syntax highlighting
- Tables: Use for comparisons, decision matrices
- Checkboxes: `- [ ]` for incomplete, `- [x]` for complete
- Emoji: Use sparingly for visual hierarchy (🎯 goals, ✅ complete, ❌ missing, ⚠️ caution)

---

## 🔄 SESSION END PROTOCOL

### **MANDATORY STEPS (In Order)**:

#### **1. Commit All Work to GitHub** ⚠️ CRITICAL

**Choose the method that fits your current context:**

---

### **METHOD A: Claude Desktop Automation** (GitHub MCP)
**When:** Using Claude Desktop for session work  
**How:** Claude can automatically commit via GitHub API  

**What Happens:**
1. Claude detects modified files
2. Creates commit with protocol-standard message
3. Pushes directly to main branch via GitHub API
4. Provides commit link for verification

**Advantages:**
- ✅ Fastest (fully automated)
- ✅ Protocol-compliant messages
- ✅ No manual steps
- ✅ Works from anywhere (API-based)

**Limitations:**
- ⚠️ Cannot handle merge conflicts (use manual git)
- ⚠️ Limited to 100MB file sizes
- ⚠️ Requires internet connection

**When to Use:**
- Session end automation
- Quick documentation updates
- Single-file commits
- Protocol-compliant quick saves

**When NOT to Use:**
- Learning git (use manual for learning)
- Complex merge scenarios
- Large binary files
- When you want manual review first

---

### **METHOD B: VS Code Git Integration**
**When:** Working in Visual Studio Code  
**How:** Use VS Code's built-in Source Control panel  

**Steps:**
1. Open Source Control panel (Ctrl+Shift+G)
2. Review changed files
3. Stage changes (click + icon or "Stage All Changes")
4. Enter commit message
5. Click ✓ Commit button
6. Click "Sync Changes" or Push button

**Advantages:**
- ✅ Visual diff viewing
- ✅ Integrated with code editing
- ✅ GitLens extensions available
- ✅ GUI-based (easier for beginners)

**When to Use:**
- Actively coding in VS Code
- Want to review diffs visually
- Prefer GUI over command line
- Working with code files

---

### **METHOD C: Manual Git Commands** (Always Available)
**When:** Learning git, complex operations, or automation fails  
**How:** Use Git Bash, PowerShell, or Command Prompt  

```powershell
cd C:\RESA_Power_Build
git add -A
git status  # Review what's being committed
git commit -m "[category]: [clear description]

[Detailed breakdown of changes]
- Item 1
- Item 2
- Item 3

[Status notes]"

git push origin main
```

**Advantages:**
- ✅ Full git capabilities
- ✅ Works offline (commit locally, push later)
- ✅ Best for learning git
- ✅ Handles complex scenarios (merge, rebase, etc.)
- ✅ Universal (works everywhere)

**When to Use:**
- Learning git fundamentals
- Complex git operations needed
- Automation methods fail
- Working offline
- Need full control

---

**Commit Message Format** (All Methods):
```
[category]: [Brief summary - 50 chars max]

[Detailed explanation]
- What was accomplished
- Why it matters
- What's next

[Status/Notes]
```

**Categories**:
- `docs:` - Documentation changes
- `feat:` - New features/fields
- `fix:` - Bug fixes
- `refactor:` - Code/structure improvements
- `chore:` - Maintenance tasks
- `analysis:` - Research/analysis work
- `test:` - Testing and validation

**🎯 RECOMMENDATION:**
- **Learning git?** Use Method C (Manual) to understand the fundamentals
- **Working in VS Code?** Use Method B (VS Code) for integrated workflow
- **Session ending with Claude Desktop?** Use Method A (Automation) for speed
- **Complex git operation?** Always use Method C (Manual)

**Note:** All methods produce the same result - committed code in GitHub. Choose based on your current context and comfort level.

#### **2. Create/Update Session Summary**
**Location**: `Documentation/03_Progress_Tracking/SESSION_SUMMARY_[DATE]_[TOPIC].md`

**Template**:
```markdown
# SESSION SUMMARY - [DATE]
## [MAIN TOPIC]

**Session Duration**: [hours]  
**Focus**: [main objectives]  
**Status**: [outcome]

---

## WHAT WAS ACCOMPLISHED
[Bulleted list of concrete deliverables]

## KEY DECISIONS/INSIGHTS
[Important realizations or choices made]

## DOCUMENTS CREATED/UPDATED
[List with locations]

## NEXT STEPS
[Immediate/Short-term/Long-term]

## BLOCKERS/OPEN QUESTIONS
[Anything preventing progress]

---

**Session Status**: [Complete/Paused/Ongoing]  
**Next Review**: [When to pick this back up]
```

#### **3. Store Key Facts to Memory MCP** ⚠️ CRITICAL
**Execute this command at session end**:

⚠️ **IMPORTANT**: Memory MCP tools are only available in **fresh chat sessions**. If you don't see memory tools available:
- This is expected for existing sessions
- Memory will be available when you start your next fresh chat
- File-based documentation (Git + Session Summaries) provides full continuity

Store essential project state that must survive session restart:
- Current project status
- Critical technical facts
- Open decisions/blockers
- Document index
- Next steps

**What to Store** (see section below)

**To Test if Memory MCP is Available**:
```
Simply ask: "Can you create a memory entity for this project?"

If available: AI will show memory creation tools
If not available: AI will explain Memory MCP not loaded (expected in existing sessions)
```

#### **4. Update Todo List** (If significant progress)
**Location**: Conversation memory (tracked by AI)

Update phase statuses:
- Mark completed phases as ✅
- Update in-progress descriptions
- Add new phases if discovered
- Adjust time estimates based on learnings

#### **5. Verify All Critical Files Saved**
**Checklist**:
```
□ All .md documents committed to GitHub
□ Session summary created
□ Memory MCP updated
□ Todo list current
□ No unsaved work in editors
□ PowerShell scripts committed (if created)
□ Reference materials organized
```

---

## 🚀 SESSION RESUME PROTOCOL

### **SCENARIO 1: Continuing in Same Chat**

**What AI Has**:
- ✅ Full conversation history
- ✅ Todo list state
- ✅ Memory MCP facts
- ✅ GitHub access

**What YOU Say**:
```
Option A (Simple continuation):
"I'm back. Let's [specific task]."

Option B (After stakeholder meeting):
"Back from meeting. Here are the decisions:
1. [Decision 1]
2. [Decision 2]
Let's implement based on these."

Option C (Need context refresh):
"What were we working on? Remind me of status."
```

**What AI Will Do**:
- Check conversation history
- Recall todo list state
- Review last few messages
- Confirm current context
- Ask clarifying questions if needed

---

### **SCENARIO 2: New Chat Session**

**What AI Has**:
- ✅ Memory MCP facts (if stored)
- ✅ GitHub access (can read repo)
- ❌ Prior conversation history

**What YOU MUST Say** (Critical Opening):
```
"I'm working on RESA Power Project Tracker.

Context:
- Check Memory MCP for project facts
- Read SESSION_SUMMARY_[MOST_RECENT].md for last session
- Current focus: [what you want to work on]

Status: [where you left off or what changed]"
```

**What AI Will Do**:
1. Retrieve Memory MCP facts
2. Read specified session summary
3. Scan recent commits in GitHub
4. Ask clarifying questions about:
   - What changed since last session?
   - Any stakeholder decisions made?
   - What's the immediate goal?

---

### **SCENARIO 3: Long Break (Weeks/Months)**

**What YOU MUST Say**:
```
"Returning to RESA Power Project Tracker after [time].

Please review:
1. Memory MCP stored facts
2. All SESSION_SUMMARY documents in chronological order
3. Most recent Git commits
4. Current todo list state

Then summarize:
- Where we left off
- What was completed
- What's pending
- What I should review before continuing"
```

**What AI Will Do**:
1. Read ALL session summaries
2. Review Git commit history
3. Retrieve Memory MCP
4. Generate comprehensive status report
5. Recommend review materials
6. Confirm current understanding before proceeding

---

## 💾 MEMORY MCP STORAGE PROTOCOL

### **WHAT to Store** (Keep Under 10 Items - Most Critical Only):

```
CATEGORY 1: PROJECT IDENTITY
- Project name, tech stack, environment URL
- Repository location
- Current version being worked on

CATEGORY 2: TECHNICAL STATE
- Entity count (8), field count (137), formula count (28)
- Clean slate status (0 records in all tables)
- Critical architecture: BusinessUnit = multi-location

CATEGORY 3: CURRENT STATUS
- Phase completion (Phase 1-3 complete, 4-7 pending)
- Blockers (awaiting stakeholder decisions)
- Priority items (revenue automation P0)

CATEGORY 4: CRITICAL DECISIONS
- What's been decided (e.g., "BusinessUnit is critical, NOT unused")
- What's pending (5 architectural decisions need stakeholder input)

CATEGORY 5: DOCUMENT INDEX
- Primary doc: USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md
- Session summary: SESSION_SUMMARY_NOV15_ARCHITECTURAL_FOUNDATION.md
- Gap analysis: GAP_ANALYSIS_FINAL_REPORT.md
```

### **HOW to Store to Memory MCP**:

**Command Format**:
```
Store these facts to Memory MCP:

Key Fact 1: [concise statement]
Key Fact 2: [concise statement]
...
Key Fact 10: [concise statement]
```

**Example**:
```
Store these facts to Memory MCP:

1. Project: RESA Power Project Tracker, Dataverse v1.3.0.4, orgf05a3756.crm.dynamics.com (RESAPowerPM Sandbox)
2. Repository: https://github.com/jasonlswenson-sys/RESA-Power-Project-Management (branch: clean-main)
3. Technical: 8 tables, 137+ fields, 30 formulas, 9 choice fields, 1 Power Automate flow
4. Tables: BusinessUnit, Projects, ProjectScope, Tasks, Apparatus, ApparatusRevenue, ScopeLaborDetail, ApparatusTypeMaster
5. Critical: BusinessUnit = multi-location (Phoenix/Vegas/Denver/San Diego), NOT unused despite 0 records
6. Status: v1.3.0.4 production ready, auditing enabled Nov 19, clean slate environment (safe for changes)
7. Ready to Implement: Date Tracking (18 rollup fields, 2.5-3 hrs, HIGH value) - spec complete
8. In Planning: Revenue Rollups (needs KPI requirements), Master Build Spec completion (30 min)
9. Key Docs: PROJECT_STATUS_TRACKER.md (navigation), MASTER_BUILD_SPECIFICATION.md v2.0, SESSION_RESUME_CHECKLIST.md
10. Latest Session: Documentation alignment Nov 19 - corrected table names (Location→BusinessUnit, Scope_Financial_Config→ScopeLaborDetail)
```

### **WHEN to Update Memory MCP**:
- ✅ End of every major session
- ✅ After critical decisions are made
- ✅ When project status changes significantly
- ✅ When new blockers emerge
- ❌ NOT for minor edits or small updates

---

## 🔍 CONTEXT RECOVERY PROTOCOL

### **If AI Says "I Don't Remember This Project"**:

**Step 1: Trigger Memory Retrieval**
```
YOU: "This is RESA Power Project Tracker. Check Memory MCP."
AI: [Retrieves stored facts]
```

**Step 2: Point to Session Summary**
```
YOU: "Read Documentation/03_Progress_Tracking/SESSION_SUMMARY_NOV15_ARCHITECTURAL_FOUNDATION.md"
AI: [Reads document, gets full context]
```

**Step 3: Confirm Understanding**
```
AI: "I now understand:
- You're working on [project]
- Current status is [X]
- Last session accomplished [Y]
- You want to [Z]
Is this correct?"

YOU: "Yes" or "No, here's what changed..."
```

---

## 📊 PROJECT STATUS TRACKING

### **How to Check Current Status**:

**Option 1: Read Most Recent Session Summary**
- Location: `Documentation/03_Progress_Tracking/`
- Filename pattern: `SESSION_SUMMARY_[DATE]_[TOPIC].md`
- Sort by date, read most recent

**Option 2: Check Git Commit History**
```powershell
cd C:\RESA_Power_Build
git log --oneline -10  # Last 10 commits
git log --since="2 days ago" --oneline  # Recent commits
```

**Option 3: Review Todo List** (Ask AI)
```
YOU: "What's the current todo list state?"
AI: [Shows current phase completion]
```

**Option 4: Memory MCP Recall** (Ask AI)
```
YOU: "Retrieve RESA Power Project Tracker facts from Memory MCP"
AI: [Shows stored facts]
```

---

## 🎯 DECISION TRACKING

### **How We Track Architectural Decisions**:

**Document**: `USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md` (Section: CRITICAL ARCHITECTURAL DECISIONS)

**For Each Decision**:
```markdown
### DECISION [N]: [Question]

#### OPTION A: [Name]
**What It Means**: [Plain English]
**System Impact**: [Fields/Views/Security required]
**Pros**: [Benefits]
**Cons**: [Drawbacks]
**Cascade Effects**: [What else changes]

#### OPTION B: [Name]
[Same structure]

#### OPTION C: [Name] ✅ [RECOMMENDED] or [STAKEHOLDER CHOICE]
[Same structure]

**Status**: 
- [ ] Pending stakeholder input
- [x] Decided: [Decision] on [Date] by [Who]

**Rationale**: [Why this choice]
```

### **When Decision is Made**:
1. Update the decision document
2. Mark status as decided
3. Document rationale
4. Update Memory MCP with decision
5. Create implementation task in todo list
6. Commit to GitHub

---

## 🚨 CRITICAL KNOWLEDGE - NEVER LOSE THIS

### **Facts That MUST Survive Every Session**:

1. **BusinessUnit Entity is CRITICAL**
   - Represents multi-location architecture
   - Phoenix, Las Vegas, Denver, San Diego
   - DO NOT remove or deprecate
   - Initial analysis said "0 records, unused" - THIS WAS WRONG

2. **Clean Slate Environment**
   - All tables have 0 records
   - Safe to make breaking changes
   - No data migration concerns
   - Verified via Export_Dataverse_Tables.ps1

3. **Current Architecture**
   - 8 entities: Projects, ProjectScope, Tasks, Apparatus, ApparatusRevenue, ScopeLaborDetail, BusinessUnit, ApparatusTypeMaster
   - 137 custom fields documented
   - 28 calculated fields (rollups)
   - 8 option sets (choice fields)

4. **Revenue Recognition Trigger**
   - When: Apparatus.Completion_Status = "Complete" (value 2)
   - Action: Create ApparatusRevenue record
   - Status: INCOMPLETE (5 fields + flow missing)
   - Priority: P0 - BLOCKING

5. **7 User Personas**
   - Field Tech, Job Lead, PM, Operations Coordinator, Account Manager, Location Manager, Regional VP
   - Current system supports: Field Tech, PM (partial), Regional VP (architecture only)
   - Missing support: Job Lead, Ops Coordinator, Account Manager

6. **5 Pending Architectural Decisions**
   - Work Assignment Model (Individual/Team/Hybrid)
   - Team Structure (Formal/Dynamic)
   - Visibility Boundaries (My work/Team work/All work)
   - Accountability Tracking (Assigned/Completed/Contributors)
   - Multi-Location Coordination (Strict/Flexible)
   - Status: Awaiting stakeholder input

7. **Documents to Never Delete**
   - USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md (master design)
   - GAP_ANALYSIS_FINAL_REPORT.md (v1.2.0.3 complete inventory)
   - V1_2_0_3_COMPLETE_FIELD_CATALOG.md (137 fields)
   - SESSION_SUMMARY_NOV15_ARCHITECTURAL_FOUNDATION.md (foundation work)

8. **Repository = Source of Truth**
   - GitHub: https://github.com/jasonlswenson-sys/RESA-Power-Project-Tracker
   - All work must be committed
   - Documents are definitive
   - If conflict between memory and GitHub, GitHub wins
   - Solution exports stored in `Solution_Exports/` for version control

---

## 🛠️ TROUBLESHOOTING

### **Problem: "I can't find the project context"**
**Solution**:
1. Check Memory MCP: "Retrieve RESA Power Project Tracker facts"
2. Read session summary: `SESSION_SUMMARY_NOV15_ARCHITECTURAL_FOUNDATION.md`
3. Check Git log: `git log --oneline -5`

### **Problem: "Memory MCP retrieval failed"**
**Solution**:
1. Don't panic - GitHub has everything
2. Read session summary manually
3. Ask AI to read specific documents from GitHub
4. Rebuild context from documents

### **Problem: "I don't remember what we decided"**
**Solution**:
1. Check `USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md` decision sections
2. Search session summaries for "DECISION" or "decided"
3. Check git commits for "decision" keyword

### **Problem: "Documentation is inconsistent"**
**Solution**:
1. GitHub version is truth
2. Session summary points to correct docs
3. If conflict, check git commit dates (newest wins)

### **Problem: "I'm starting after a long break"**
**Solution**:
1. Read ALL session summaries chronologically
2. Review Git commit history
3. Check Memory MCP for stored facts
4. Ask AI to summarize current state
5. Verify understanding before making changes

---

## ✅ SESSION END CHECKLIST (Print This)

**Before Closing Session**:

□ **Git**: All work committed and pushed to main  
□ **Session Summary**: Created/updated in `03_Progress_Tracking/`  
□ **Memory MCP**: Key facts stored (10 max)  
□ **Todo List**: Updated if significant progress  
□ **Documents**: All saved with clear headers  
□ **No Loose Ends**: No "I'll document this later"  

**Verify You Can Answer**:
□ What did I accomplish today?  
□ Where is that work documented?  
□ What's the next step?  
□ What's blocking progress?  
□ Where would I start next session?  

**If Any "No" Above**: Don't end session until fixed.

---

## 📖 QUICK REFERENCE

### **Most Important Documents**:
1. `PROJECT_CONTINUITY_PROTOCOL.md` (this document)
2. `SESSION_SUMMARY_[LATEST].md` (what happened last)
3. `USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md` (system design)
4. `GAP_ANALYSIS_FINAL_REPORT.md` (what exists)

### **Most Important Commands**:
```powershell
# Save work
git add -A && git commit -m "message" && git push origin main

# Check status
git status
git log --oneline -5

# Navigate
cd C:\RESA_Power_Build
```

### **Most Important AI Prompts**:
```
# Retrieve context
"Check Memory MCP for RESA Power Project Tracker"
"Read SESSION_SUMMARY_NOV15_ARCHITECTURAL_FOUNDATION.md"
"Show me the current todo list"

# Start work
"I'm back from stakeholder meeting with decisions"
"Let's implement [specific task]"

# Verify understanding
"Summarize where we left off"
"What's blocking progress?"
```

---

## 📝 VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|  
| 1.0 | Nov 15, 2025 | Initial protocol created - Foundation complete, awaiting stakeholder decisions |
| 1.1 | Nov 16, 2025 | Excel architecture analyzed, VBA documented, Excel MCP foundation ready |
| 1.2 | Nov 16, 2025 | Added context-based git commit methods (Claude Desktop/VS Code/Manual) with clear guidance on when to use each |
| 1.3 | Nov 19, 2025 | Updated environment details (correct IDs, repository URL), added Memory MCP testing instructions, corrected solution name to RESAPowerProjectTracker, updated Memory MCP storage template to v1.3.0.4 state |

---

**STATUS**: Protocol active and current - Environment details verified Nov 19, 2025  
**LAST SESSION**: Nov 19, 2025 - Documentation alignment, Memory MCP testing guide created  
**NEXT REVIEW**: After first fresh session with Memory MCP test  
**OWNER**: Jason Swenson + AI Assistant (Claude)