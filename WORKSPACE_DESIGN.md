# RESA Power - Optimal Development Environment Design

**Purpose:** Design workspace structure and protocols that optimize AI-assisted development  
**Stakeholders:** Jason (Owner), Desktop Claude, VS Code Claude  
**Created:** December 5, 2025

---

## Design Principles

### 1. Context Recovery in <30 Seconds
Every Claude session should be able to get fully oriented by reading 2-3 files.

### 2. Single Source of Truth
One authoritative location per artifact. No duplicates. No "which version?"

### 3. Decisions Persist Beyond Chat
Every architectural decision documented with rationale. Never re-debate.

### 4. Consistent Conventions
Naming, formatting, structure defined once, followed always.

### 5. Clear Handoff Protocol
Explicit "end of session" and "start of session" procedures.

### 6. Purpose-Driven Folders
Every folder has one clear purpose. Nothing miscellaneous.

---

## Proposed Folder Structure

```
C:\RESA_Power\                          # Clean root (renamed from RESA_Power_Build)
│
├── .claude/                            # AI COLLABORATION HUB
│   ├── PROJECT_STATE.md                # Current status - READ FIRST EVERY SESSION
│   ├── DECISIONS.md                    # Architectural decision log
│   ├── CONVENTIONS.md                  # Naming, formatting, style rules
│   ├── HANDOFF.md                      # Session transition protocol
│   └── PROMPTS/                        # Reusable prompt templates
│       ├── session_start.md
│       ├── code_review.md
│       └── schema_change.md
│
├── docs/                               # DOCUMENTATION (human + AI readable)
│   ├── ARCHITECTURE.md                 # System architecture overview
│   ├── DATA_MODEL.md                   # Entity relationship documentation
│   ├── API.md                          # API contracts and endpoints
│   ├── requirements/                   # Original requirements
│   │   ├── PSS_Portal_Requirements.md
│   │   └── Field_Testing_Requirements.md
│   └── decisions/                      # Detailed decision records (ADRs)
│       ├── 001_supabase_over_dataverse.md
│       ├── 002_schema_merge_approach.md
│       └── template.md
│
├── database/                           # DATABASE (single source of truth)
│   ├── schema/                         # Production schema files
│   │   ├── 00_enums.sql
│   │   ├── 01_core_schema.sql
│   │   ├── 02_pss_schema.sql
│   │   ├── 03_triggers.sql
│   │   ├── 04_views.sql
│   │   ├── 05_rls_policies.sql
│   │   └── SCHEMA_VERSION.md           # Version tracking
│   ├── seed/                           # Reference data
│   │   └── 10_seed_data.sql
│   ├── test/                           # Test data (not production)
│   │   ├── 11_test_data.sql
│   │   └── 12_pss_test_data.sql
│   ├── migrations/                     # Future schema changes
│   │   └── .gitkeep
│   └── README.md                       # Database setup guide
│
├── app/                                # APPLICATION CODE
│   ├── web/                            # Next.js web application
│   │   ├── src/
│   │   ├── package.json
│   │   └── ...
│   └── shared/                         # Shared types, utilities
│       ├── types/
│       └── utils/
│
├── scripts/                            # AUTOMATION SCRIPTS
│   ├── setup/                          # Environment setup
│   ├── deploy/                         # Deployment scripts
│   └── data/                           # Data migration scripts
│
├── archive/                            # ARCHIVED WORK (out of active scope)
│   ├── dataverse/                      # Old Dataverse artifacts
│   ├── schema_drafts/                  # Previous schema versions
│   └── README.md                       # What's here and why
│
└── README.md                           # Project overview
```

---

## Key Files Explained

### .claude/PROJECT_STATE.md
**Purpose:** Single file Claude reads FIRST every session  
**Updated:** End of every work session  
**Contains:**
- Current phase and focus
- What's complete (with file paths)
- What's in progress
- Blockers and open questions
- Immediate next actions
- Recent decisions (last 5)

**Format:**
```markdown
# Project State
**Last Updated:** 2025-12-05 18:30 MST  
**Updated By:** Desktop Claude  
**Current Phase:** Database Schema Merge

## Status
| Area | Status | Notes |
|------|--------|-------|
| Schema Design | ✅ Complete | Merged schema approved |
| SQL Files | 🔄 In Progress | 3/10 files generated |
| Test Data | ⏳ Pending | Waiting for schema |
| Web App | ⏳ Pending | After database |

## In Progress
- [ ] Generate 01_core_schema.sql
- [ ] Generate 02_pss_schema.sql

## Blockers
None

## Next Actions
1. Complete schema SQL files
2. VS Code Claude generates test data
3. Jason creates Supabase project

## Recent Decisions
- 2025-12-05: Merge both schema approaches (see DECISIONS.md #002)
- 2025-12-05: Defer time_entries to Phase 2
```

### .claude/DECISIONS.md
**Purpose:** Permanent record of all architectural decisions  
**Updated:** When decisions are made  
**Contains:**
- Decision ID and date
- Context/problem
- Decision made
- Alternatives considered
- Rationale

**Format:**
```markdown
# Architectural Decisions

## DEC-001: Supabase Over Dataverse
**Date:** 2025-12-04  
**Status:** Approved  
**Context:** Need database for PSS Portal and Field Testing  
**Decision:** Use Supabase PostgreSQL instead of Microsoft Dataverse  
**Rationale:** Lower cost, simpler auth, better DX, minimal existing data  
**Alternatives Rejected:** Continue Dataverse (complex, expensive)

## DEC-002: Schema Merge Approach
**Date:** 2025-12-05  
**Status:** Approved  
**Context:** Two parallel schema implementations exist  
**Decision:** Merge Desktop Claude automation + VS Code Claude DX  
**Rationale:** Best of both approaches  
**Details:** See SCHEMA_AUDIT_REPORT.md
```

### .claude/CONVENTIONS.md
**Purpose:** Consistent standards across all work  
**Updated:** Rarely (only when conventions change)  
**Contains:**
- File naming rules
- SQL formatting standards
- Code style guide
- Documentation format
- Git commit conventions

**Example:**
```markdown
# Conventions

## File Naming
- SQL files: snake_case, numbered prefix (00_, 01_, ...)
- Markdown: UPPER_CASE for root docs, Title_Case for nested
- Code: Follow framework conventions (Next.js, etc.)

## SQL Standards
- Keywords: UPPERCASE (SELECT, CREATE TABLE)
- Identifiers: snake_case (project_status, created_at)
- ENUMs: UPPER_SNAKE_CASE values ('IN_PROGRESS')
- Tables: Plural (projects, scopes, tasks)
- Primary keys: Always `id UUID`
- Timestamps: Always `created_at`, `updated_at`

## Documentation
- Every file has header comment with purpose
- README.md in every folder
- Decisions documented immediately
```

### .claude/HANDOFF.md
**Purpose:** Protocol for session transitions  
**Contains:**
- How to end a session
- How to start a session
- How to hand off between Claude instances

**Format:**
```markdown
# Session Handoff Protocol

## Ending a Session
1. Update PROJECT_STATE.md with current status
2. List any incomplete work with file paths
3. Note any blockers or open questions
4. Commit all files (if using Git)

## Starting a Session
1. Read .claude/PROJECT_STATE.md FIRST
2. Read .claude/DECISIONS.md if context needed
3. Check .claude/CONVENTIONS.md if generating files
4. Ask human: "Based on PROJECT_STATE, should I continue X or is there a new priority?"

## Handoff Between Claudes
1. Source Claude updates PROJECT_STATE.md
2. Source Claude lists specific files for target to review
3. Human confirms handoff with target Claude
4. Target Claude reads PROJECT_STATE.md and listed files
5. Target Claude confirms understanding before proceeding
```

---

## Session Workflow

### Start of Session
```
Human: [Opens new chat or continues conversation]

Claude: *Reads .claude/PROJECT_STATE.md*

Claude: "I see we're in the Database Schema Merge phase. Last session 
completed 00_enums.sql and 01_core_schema.sql. In progress: 
02_pss_schema.sql. Should I continue with that, or has 
priority changed?"
Human: "Continue with the schema."

Claude: *Works on 02_pss_schema.sql*
```

### End of Session
```
Claude: "Session complete. I've updated PROJECT_STATE.md:
- Completed: 02_pss_schema.sql, 03_triggers.sql
- In progress: 04_views.sql (80% done)
- Next: Finish views, then RLS policies

Files modified:
- database/schema/02_pss_schema.sql (new)
- database/schema/03_triggers.sql (new)
- database/schema/04_views.sql (partial)
- .claude/PROJECT_STATE.md (updated)"
```

### Cross-Claude Handoff
```
Desktop Claude: "Handoff to VS Code Claude:

I've completed:
- database/schema/00_enums.sql
- database/schema/01_core_schema.sql
- database/schema/02_pss_schema.sql

PROJECT_STATE.md updated. VS Code Claude should:
1. Read PROJECT_STATE.md
2. Review my schema files
3. Generate test data in database/test/"

VS Code Claude: *Reads PROJECT_STATE.md*

VS Code Claude: "Got it. I see Desktop Claude completed the schema files.
I'll now generate test data that references the new ENUMs and tables.
Starting with 11_test_data.sql..."
```

---

## Migration Plan: Current → Optimal

### Phase 1: Create Structure (30 min)
```powershell
# Create new structure
mkdir C:\RESA_Power
mkdir C:\RESA_Power\.claude
mkdir C:\RESA_Power\.claude\PROMPTS
mkdir C:\RESA_Power\docs
mkdir C:\RESA_Power\docs\requirements
mkdir C:\RESA_Power\docs\decisions
mkdir C:\RESA_Power\database
mkdir C:\RESA_Power\database\schema
mkdir C:\RESA_Power\database\seed
mkdir C:\RESA_Power\database\test
mkdir C:\RESA_Power\database\migrations
mkdir C:\RESA_Power\app
mkdir C:\RESA_Power\scripts
mkdir C:\RESA_Power\archive
```

### Phase 2: Migrate Content (1 hour)
| Source | Destination | Action |
|--------|-------------|--------|
| RESA_Power_Build\Documentation\ | RESA_Power\docs\ | Move + reorganize |
| RESA_Power_Build\Supabase\*.sql | RESA_Power\archive\schema_drafts\ | Archive old versions |
| RESA_Power_Build\Database_Setup\ | RESA_Power\archive\schema_drafts\ | Archive old versions |
| PSS Portal requirements docs | RESA_Power\docs\requirements\ | Move |
| Audit reports | RESA_Power\docs\decisions\ | Move + convert to ADRs |

### Phase 3: Create Control Files (30 min)
- Create PROJECT_STATE.md with current status
- Create DECISIONS.md with recent decisions
- Create CONVENTIONS.md with standards
- Create HANDOFF.md with protocols

### Phase 4: Generate Fresh Schema (2 hours)
- Generate schema files directly into database/schema/
- Generate seed data into database/seed/
- Generate test data into database/test/
- No old files to conflict with

---

## Git Integration (Optional but Recommended)

### If Using Git
```
C:\RESA_Power\
├── .git/                   # Git repository
├── .gitignore              # Ignore sensitive files
├── .claude/                # Tracked - collaboration hub
├── docs/                   # Tracked - documentation
├── database/               # Tracked - schema is code
├── app/                    # Tracked - application code
├── scripts/                # Tracked - automation
└── archive/                # Tracked - historical reference
```

### .gitignore
```
# Environment
.env
.env.local
*.local

# Dependencies
node_modules/
.npm/

# Build outputs
.next/
dist/
build/

# IDE
.vscode/settings.json
.idea/

# OS
.DS_Store
Thumbs.db

# Secrets (never commit)
**/secrets/
*.pem
*.key
```

### Benefits
- Full history of all changes
- Branch for experiments
- Easy rollback
- GitHub backup
- CI/CD integration later

---

## Environment Variables

### Local Development (.env.local)
```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOi...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...  # Server only, never expose

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Production (.env.production)
```bash
# Set in hosting platform (Vercel, etc.)
# Never commit production secrets
```

---

## Implementation Steps

### Step 1: Jason Approves Structure
Review this document. Confirm folder structure works for you.

### Step 2: Create Workspace
I can create the folder structure now, or you can do it manually.

### Step 3: Create Control Files
I create the .claude/ files with current project state.

### Step 4: Archive Old Work
Move existing files to archive/ with clear README.

### Step 5: Generate Fresh Schema
Generate all SQL files directly into new structure.

### Step 6: Initialize Git (Optional)
Set up version control if desired.

---

## Questions for Jason

1. **Root folder name:** `C:\RESA_Power\` or keep `C:\RESA_Power_Build\`?

2. **Git repository:** 
   - Yes, local only
   - Yes, GitHub/Azure DevOps
   - No, folder backup is fine

3. **Archive old work:** 
   - Move to archive/ subfolder
   - Move to separate location
   - Delete (I don't recommend this)

4. **VS Code Claude access:** Can VS Code Claude access the same folder path? Need to confirm for handoff protocol.

---

## Summary

**This workspace design gives us:**

| Benefit | How |
|---------|-----|
| 30-second context recovery | PROJECT_STATE.md read first |
| No version confusion | Single source of truth per artifact |
| No re-debating decisions | DECISIONS.md is permanent record |
| Consistent output | CONVENTIONS.md defines standards |
| Clean handoffs | HANDOFF.md protocol |
| Clear organization | Purpose-driven folders |
| Historical reference | archive/ preserves old work |

**Ready to implement?**

---

*Workspace design by Desktop Claude | December 5, 2025*
