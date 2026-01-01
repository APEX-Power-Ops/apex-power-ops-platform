# APEX Platform - Master Project Document

**Version:** 1.0  
**Created:** 2025-12-31  
**Owner:** Jason Swenson  
**Last Updated:** 2025-12-31

---

## Table of Contents

1. [Project Identity](#1-project-identity)
2. [Roles & Responsibilities](#2-roles--responsibilities)
3. [File Structure](#3-file-structure)
4. [Session Protocols](#4-session-protocols)
5. [Handoff Protocols](#5-handoff-protocols)
6. [Change Management](#6-change-management)
7. [Naming Conventions](#7-naming-conventions)
8. [Quality Standards](#8-quality-standards)
9. [Decision Authority](#9-decision-authority)
10. [Technical Stack](#10-technical-stack)

---

## 1. Project Identity

### 1.1 Ownership

| Item | Value |
|------|-------|
| **Project Name** | APEX Platform |
| **Company** | APEX Power Operations, LLC |
| **Domain** | apexpowerops.com |
| **Owner** | Jason Swenson |
| **IP Status** | 100% owned by Jason - no external involvement in development |

### 1.2 What This Is

APEX Platform is an operations management system for field service companies, initially deployed for electrical testing operations. It provides:

- **Project Tracking** - Visibility from tech level through VP
- **Document Hub** - Centralized, structured document management
- **Field Operations** - Offline-capable work management for technicians
- **Resource Linking** - NETA standards, procedures, and equipment data

### 1.3 What This Is NOT

- Not a RESA Power project (they have no involvement)
- Not dependent on any external timeline or approval
- Not limited to electrical testing (architecture is extensible)

---

## 2. Roles & Responsibilities

### 2.1 Jason (Owner)

**Authority:** All decisions - strategic, technical, business logic

**Responsibilities:**
- Set priorities and direction
- Approve major features before deployment
- Provide domain expertise and business rules
- Bridge between Claude instances
- Final quality approval

**Time Commitment:** 4-6 hours/day, mornings/evenings primarily

### 2.2 Desktop Claude (Orchestrator)

**Primary Context:** Claude.ai with Desktop Commander + Supabase MCP

**Responsibilities:**
- Strategic discussions with Jason
- Architecture and design decisions
- Database schema work
- Documentation and specifications
- Task specification for VS Code Claude
- Quality review of VS Code work
- Complex reasoning and analysis

**Does NOT:**
- Make business logic decisions without Jason
- Change priorities without Jason's approval
- Implement UI components (VS Code's domain)

### 2.3 VS Code Claude (Implementer)

**Primary Context:** VS Code/Cursor with full project access + Supabase MCP

**Responsibilities:**
- Application code (Next.js/React)
- UI component development
- Local testing and verification
- Bug fixes in application code
- Implementation of specified tasks

**Does NOT:**
- Change specifications without Desktop Claude approval
- Modify database schema without coordination
- Make architecture decisions unilaterally

### 2.4 Coordination Model

```
Jason
  │
  ├── Sets priorities, makes decisions
  │
  ▼
Desktop Claude
  │
  ├── Translates priorities to task specs
  ├── Reviews completed work
  │
  ▼
VS Code Claude
  │
  └── Implements specified tasks
```

**Critical:** Jason is the only bridge between Claude instances. There is no direct communication.

---

## 3. File Structure

### 3.1 Project Root

```
C:\RESA_Power_Build\
├── .claude/                    # Claude coordination (see below)
├── .git/                       # Git repository
├── Documentation/              # Project documentation
├── Reference_Files/            # Source materials, Excel files
├── spec/                       # Specifications
├── Supabase/                   # Database assets
│   ├── schema/                 # SQL migration files
│   ├── data/                   # Seed and test data
│   └── docs/                   # Database documentation
├── _archive/                   # Archived files
├── README.md                   # Project introduction
└── [app files when created]
```

### 3.2 Claude Coordination Directory

```
.claude/
├── MASTER.md           # This file - read once, reference as needed
├── STATE.md            # Current status - read EVERY session
├── SESSION_LOG.md      # Append-only history
├── BACKLOG.md          # Prioritized work queue
├── DECISION_LOG.md     # All decisions with rationale
├── HANDOFFS/
│   ├── TO_DESKTOP.md   # Messages for Desktop Claude
│   └── TO_VSCODE.md    # Messages for VS Code Claude
└── _archive/           # Old files, preserved for reference
```

### 3.3 File Purposes

| File | Purpose | Who Updates | When to Read |
|------|---------|-------------|--------------|
| MASTER.md | Project rules and standards | Desktop Claude + Jason | Once per new context, reference as needed |
| STATE.md | Current status, blockers, active work | Both Claudes | EVERY session start |
| SESSION_LOG.md | Historical record | Both Claudes | When context needed |
| BACKLOG.md | Work queue | Jason (priority), Desktop (items) | When picking up work |
| DECISION_LOG.md | Decisions and rationale | Both Claudes | When decision needed |
| TO_DESKTOP.md | Inbox for Desktop Claude | VS Code Claude | Desktop session start |
| TO_VSCODE.md | Inbox for VS Code Claude | Desktop Claude | VS Code session start |

---

## 4. Session Protocols

### 4.1 Session Start (MANDATORY)

Every Claude session MUST begin with:

1. **Read STATE.md** - Understand current status
2. **Check HANDOFFS/** - Read your inbox (TO_DESKTOP.md or TO_VSCODE.md)
3. **Acknowledge** - Confirm what you found with Jason or in SESSION_LOG.md

**Do NOT proceed with work until these steps are complete.**

### 4.2 During Session

- Work on assigned/agreed tasks
- Update STATE.md if status changes significantly
- Note any blockers or decisions needed
- Keep Jason informed of progress

### 4.3 Session End (MANDATORY)

Before ending any session:

1. **Update STATE.md** - Current status, what's complete, what's blocked
2. **Write handoff** - If work continues with other Claude, write to their inbox
3. **Append to SESSION_LOG.md** - Summary of session

**Session Log Entry Format:**

```markdown
## YYYY-MM-DD HH:MM - [Desktop/VS Code] Claude

**Duration:** ~X min
**Focus:** [Brief description]

**Completed:**
- [Item 1]
- [Item 2]

**In Progress:**
- [Item] - [status/blocker]

**Decisions Made:**
- [Decision]: [Rationale]

**Handed Off:**
- [Description of handoff, if any]

---
```

### 4.4 Session Resume (New Context)

When starting a fresh session with no prior context:

1. Read MASTER.md (this file) - understand the rules
2. Read STATE.md - understand current status
3. Read recent SESSION_LOG.md entries - understand recent history
4. Check your inbox in HANDOFFS/
5. Proceed with work

---

## 5. Handoff Protocols

### 5.1 When to Create a Handoff

Create a handoff message when:
- Work is ready for the other Claude to continue
- A blocker requires the other Claude's capabilities
- Information must be shared that affects both contexts
- A decision was made that the other Claude needs to know

### 5.2 Handoff Message Format

```markdown
## YYYY-MM-DD HH:MM - From [Desktop/VS Code/Jason]

**Subject:** [Brief description]
**Priority:** [High/Medium/Low]
**Action Required:** [Yes/No]
**Blocking:** [Yes/No]

### Context
[Why this handoff exists]

### Details
[Specific information, file paths, decisions]

### What You Need to Do
[Clear action items]

### Questions/Notes
[Any open questions or additional context]

---
```

### 5.3 Processing Handoffs

When you find a message in your inbox:
1. Read and understand it
2. Acknowledge receipt in SESSION_LOG.md
3. Complete the requested actions
4. Clear the message (delete or archive) after processing
5. Write response to other Claude's inbox if needed

---

## 6. Change Management

### 6.1 Change Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| **0 - Independent** | No cross-cutting impact | Proceed, update STATE.md after |
| **1 - Notify** | Minor shared impact | Update STATE.md before AND after |
| **2 - Coordinate** | Significant shared impact | Handoff required before proceeding |
| **3 - Approve** | Major change | Jason approval required |

### 6.2 Examples by Level

**Level 0 - Independent:**
- Reading files or database
- Creating isolated new files
- Styling/UI tweaks
- Bug fixes in owned code
- Adding comments or documentation

**Level 1 - Notify:**
- New components or pages
- Test data changes
- Documentation updates
- New API endpoints

**Level 2 - Coordinate:**
- Database schema changes (any DDL)
- Changes to shared interfaces/types
- Specification modifications
- Breaking changes to existing code

**Level 3 - Approve:**
- New major features
- Architecture changes
- Priority changes
- Scope changes
- Deployment decisions

---

## 7. Naming Conventions

### 7.1 Files

| Type | Convention | Example |
|------|------------|---------|
| Documentation | UPPER_SNAKE_CASE.md | PROJECT_STATUS.md |
| Code files | kebab-case | project-list.tsx |
| React components | PascalCase | ProjectList.tsx |
| SQL migrations | NN_description.sql | 01_create_tables.sql |
| Session files | YYYY-MM-DD_description.md | 2025-12-31_schema_work.md |

### 7.2 Code

| Type | Convention | Example |
|------|------------|---------|
| Variables | camelCase | projectId |
| Functions | camelCase | getProjectById |
| Components | PascalCase | ProjectCard |
| Constants | UPPER_SNAKE_CASE | MAX_RETRY_COUNT |
| Types/Interfaces | PascalCase | ProjectStatus |
| Database tables | snake_case, plural | project_scopes |
| Database columns | snake_case | created_at |

### 7.3 Git

| Type | Convention | Example |
|------|------------|---------|
| Branch names | feature/description | feature/project-list |
| Commit messages | type: description | feat: add project list view |

**Commit Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

---

## 8. Quality Standards

### 8.1 Definition of Done

A task is DONE when:

- [ ] Code compiles without errors
- [ ] Follows naming conventions (Section 7)
- [ ] No TypeScript/ESLint errors
- [ ] Tested locally (VS Code) or verified via query (Desktop)
- [ ] STATE.md updated
- [ ] SESSION_LOG.md entry added
- [ ] Handoff written if work continues elsewhere

### 8.2 Code Standards

- TypeScript strict mode
- Explicit types (avoid `any`)
- Components under 200 lines (split if larger)
- Functions under 50 lines (split if larger)
- Meaningful variable names
- Comments for non-obvious logic

### 8.3 Documentation Standards

- Update docs when code changes
- Include examples where helpful
- Keep docs close to code they describe
- Date all significant updates

---

## 9. Decision Authority

### 9.1 Jason Decides

- All priorities
- Business logic and rules
- User-facing behavior
- Scope (in/out)
- Timeline and deadlines
- Deployment approvals
- Feature acceptance

### 9.2 Desktop Claude Decides (Within Guidelines)

- Technical architecture patterns
- Database schema design
- Code organization
- Task breakdown and specifications
- Documentation structure
- Quality assessment of VS Code work

### 9.3 VS Code Claude Decides (Within Guidelines)

- Implementation details
- Component structure
- Local optimizations
- Testing approach
- UI layout (within specifications)

### 9.4 Escalation Path

```
VS Code Claude
  │
  ├── Technical questions → Desktop Claude
  ├── Specification questions → Desktop Claude
  │
  ▼
Desktop Claude
  │
  ├── Business logic questions → Jason
  ├── Priority questions → Jason
  │
  ▼
Jason
  │
  └── Final authority on all decisions
```

---

## 10. Technical Stack

### 10.1 Current Stack

| Layer | Technology |
|-------|------------|
| Database | Supabase PostgreSQL |
| Auth | Supabase Auth (Phase 1) |
| Backend | Supabase (Edge Functions if needed) |
| Frontend | Next.js 15 + React |
| UI Components | shadcn/ui + Tailwind |
| Offline Storage | IndexedDB (via Dexie.js) |
| Deployment | Vercel |

### 10.2 Database

- **Project Reference:** fxoyniqnrlkxfligbxmg
- **Schema:** 40+ tables deployed
- **Data:** NETA procedures and test items loaded

### 10.3 Application

- **Location:** C:\Users\jjswe\Projects\resa-web-app (to be renamed)
- **Status:** Supabase client configured, UI not built

---

## Appendix: Quick Reference

### Session Start Checklist

- [ ] Read STATE.md
- [ ] Check HANDOFFS/TO_[YOUR_CONTEXT].md
- [ ] Acknowledge in SESSION_LOG.md or to Jason

### Session End Checklist

- [ ] Update STATE.md
- [ ] Write handoff if needed
- [ ] Append to SESSION_LOG.md

### Key File Paths

| What | Where |
|------|-------|
| This document | .claude/MASTER.md |
| Current status | .claude/STATE.md |
| Work queue | .claude/BACKLOG.md |
| Session history | .claude/SESSION_LOG.md |
| Decisions | .claude/DECISION_LOG.md |
| Database schema | Supabase/schema/ |
| Specifications | spec/ |

---

*This is a living document. Update as processes evolve.*
