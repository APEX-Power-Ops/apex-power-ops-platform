# RESA Power Platform - Decision Log

**Created:** December 31, 2025  
**Purpose:** Systematic capture and resolution of all design decisions  
**Process:** Review each section, make decision, document rationale, update related docs  

---

## How to Use This Document

1. Work through sections in order (or jump to blocking items)
2. For each question: Discuss → Decide → Document rationale
3. Mark status: ⬜ Open | 🟡 In Discussion | ✅ Decided | ⏸️ Deferred
4. After decision: Update relevant project documentation
5. Move decided items to "Decisions Made" section at bottom

---

## Section 1: Strategic Foundation

### 1.1 Project Identity & Ownership

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 1.1.1 | What is the official project name for documentation? | ✅ | **APEX Platform** (LLC: APEX Power Operations, domain: apexpowerops.com) | Jason's IP, no RESA involvement. "Power" = electrical industry + powerful/capable. |
| 1.1.2 | Who are the stakeholders with input authority? | ✅ | **Jason (owner/decision-maker), Boss (consultant), Techs (user feedback)** | Jason decides all. Others provide advisory input. |
| 1.1.3 | What is the decision-making hierarchy? | ✅ | **Jason decides everything. Boss consulted on workflows, UI, role architecture.** | Clear ownership with advisory structure. |
| 1.1.4 | Is there a target date for "v1.0" or first real deployment? | ✅ | **No hard date. ASAP - operations is inefficient.** | Urgency from operational pain, not external deadline. |
| 1.1.5 | What does success look like in 3 months? 6 months? 12 months? | ⬜ | | Measurable milestones |

### 1.2 Scope Boundaries

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 1.2.1 | What is IN scope for Phase 1? | ⬜ | | Need explicit boundary |
| 1.2.2 | What is explicitly OUT of scope for Phase 1? | ⬜ | | Prevents scope creep |
| 1.2.3 | Is PSS Portal Phase 1 or deferred? | ⬜ | | Previous docs said deferred |
| 1.2.4 | Is Study Content/Training Phase 1 or deferred? | ⬜ | | Schema built, but priority? |
| 1.2.5 | Is TCC Calculator integration Phase 1 or deferred? | ⬜ | | Blue Sky said future |
| 1.2.6 | Is Connecteam replacement Phase 1 or deferred? | ⬜ | | Keep for scheduling initially? |

---

## Section 2: User & Access Design

### 2.1 User Roles

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 2.1.1 | What are the distinct user roles? | ⬜ | | Field Tech, PM, Admin, Executive, Jason(Super)? |
| 2.1.2 | What can a Field Tech see/do? | ⬜ | | Their assignments? All projects? |
| 2.1.3 | What can a PM see/do? | ⬜ | | Their location? All locations? |
| 2.1.4 | What can an Admin see/do? | ⬜ | | User management? All data? |
| 2.1.5 | What can an Executive see/do? | ⬜ | | Read-only dashboards? |
| 2.1.6 | How do roles map to the `employees` table? | ⬜ | | New column? Separate roles table? |

### 2.2 Authentication

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 2.2.1 | Authentication method for Phase 1? | ⬜ | | Email/password? Magic link? |
| 2.2.2 | Do users self-register or admin-created only? | ⬜ | | Controlled access preferred? |
| 2.2.3 | Is SSO/MSAL required for Phase 1? | ⬜ | | Or defer to later? |
| 2.2.4 | Password requirements? | ⬜ | | Standard or custom policy? |
| 2.2.5 | Session timeout policy? | ⬜ | | Especially for offline scenarios |

### 2.3 Multi-Location Access

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 2.3.1 | Can a user belong to multiple locations? | ⬜ | | AZ tech helping Denver? |
| 2.3.2 | Can a user see projects outside their location? | ⬜ | | Visibility vs. edit rights |
| 2.3.3 | How is location assignment managed? | ⬜ | | Primary location + temporary? |

---

## Section 3: Document Hub Design

### 3.1 Folder Structure

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 3.1.1 | What is the top-level folder hierarchy? | ⬜ | | By Location? By Year? By Client? |
| 3.1.2 | Project folder naming convention? | ⬜ | | `[ProjectNumber]_[ClientName]_[ShortDesc]`? |
| 3.1.3 | Standard subfolders within each project? | ⬜ | | Drawings, Reports, SOPs, JSAs, etc.? |
| 3.1.4 | Where do company-wide documents live? | ⬜ | | Separate from project folders? |
| 3.1.5 | Where do NETA standards/reference docs live? | ⬜ | | /Reference/ folder? |
| 3.1.6 | Can users create custom folders? | ⬜ | | No - enforce structure? |

### 3.2 File Naming

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 3.2.1 | File naming convention? | ⬜ | | `[ProjectNum]_[Type]_[Desc]_v[N].[ext]`? |
| 3.2.2 | What document types are valid? | ⬜ | | Enum list needed |
| 3.2.3 | Who generates filename - user or system? | ⬜ | | System-generated enforces standard |
| 3.2.4 | How to handle files that don't fit convention? | ⬜ | | Reject? Admin override? |

### 3.3 Metadata & Search

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 3.3.1 | Required metadata fields on upload? | ⬜ | | Project, Type, Description, Date? |
| 3.3.2 | Optional metadata fields? | ⬜ | | Tags, Apparatus Type, NETA Section? |
| 3.3.3 | Full-text search of document contents? | ⬜ | | Phase 1 or later? Complex. |
| 3.3.4 | Search by metadata fields? | ⬜ | | Easier, probably Phase 1 |

### 3.4 Versioning & History

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 3.4.1 | Automatic versioning on re-upload? | ⬜ | | v1, v2, v3... |
| 3.4.2 | Can old versions be accessed? | ⬜ | | View history? Restore? |
| 3.4.3 | Can files be deleted or only archived? | ⬜ | | Audit trail concerns |
| 3.4.4 | Who can delete/archive? | ⬜ | | Admin only? |

### 3.5 Access Control

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 3.5.1 | Document-level permissions or folder-level? | ⬜ | | Folder simpler to manage |
| 3.5.2 | Can a tech see all documents or just project-related? | ⬜ | | Visibility scope |
| 3.5.3 | Are any documents restricted (HR, financials)? | ⬜ | | May need special handling |

---

## Section 4: Field Operations Workflow

### 4.1 Assignment & Visibility

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 4.1.1 | How is work assigned to a tech? | ⬜ | | PM assigns? Self-assign? Scheduler? |
| 4.1.2 | Does a tech see only their assignments or full project? | ⬜ | | Need to coordinate with others? |
| 4.1.3 | Can a tech reassign work to another tech? | ⬜ | | Or PM only? |
| 4.1.4 | How are multi-tech jobs handled? | ⬜ | | Same apparatus, multiple techs? |

### 4.2 Status Workflow

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 4.2.1 | What are the valid apparatus statuses? | ✅ | **NOT_STARTED, IN_PROGRESS, PENDING_REVIEW, COMPLETED, ISSUE_LOG** | Status is system-calculated from workflow state, except ISSUE_LOG which is manual. |
| 4.2.2 | Can status go backward? | ✅ | **Yes - Job Lead can reject PENDING_REVIEW → IN_PROGRESS** | Rejection sends back to tech with notes. |
| 4.2.3 | Does status change trigger any action? | ✅ | **COMPLETED (via approval) triggers revenue recognition** | approved_at timestamp = earned revenue. |
| 4.2.4 | Who can change status? | ✅ | **System sets most. Job Lead sets ISSUE_LOG and approves/rejects.** | Tech submits work, system transitions to PENDING_REVIEW. |

**Status Flow Diagram:**
```
NOT_STARTED
    ↓ (Tech begins work)
IN_PROGRESS
    ↓ (Tech submits)
PENDING_REVIEW
    ↓
├── COMPLETED (Job Lead approves → Revenue)
├── IN_PROGRESS (Job Lead rejects → Back to tech)
└── ISSUE_LOG (Can't complete / Failed testing)
```

### 4.3 Availability States

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 4.3.1 | What does "Ready" mean operationally? | ⬜ | | Equipment accessible, safe to work |
| 4.3.2 | What does "On Hold" mean? | ⬜ | | Customer issue? Parts? Weather? |
| 4.3.3 | What does "Not Available" mean? | ⬜ | | Not yet accessible (construction)? |
| 4.3.4 | Who sets availability? | ⬜ | | Tech in field? PM? |
| 4.3.5 | Can a tech work on "On Hold" apparatus? | ⬜ | | Override with reason? |

### 4.4 Assessment Values

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 4.4.1 | What assessment values are valid? | ⬜ | | Pass, Fail, Marginal, Needs Repair, etc. |
| 4.4.2 | What's the difference between "Marginal" and "Minor Deficiency"? | ⬜ | | Need clear definitions |
| 4.4.3 | What's the difference between "Fail" and "Non-Serviceable"? | ⬜ | | Need clear definitions |
| 4.4.4 | Does assessment affect workflow? | ⬜ | | Fail requires follow-up? |

### 4.5 Hours Entry

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 4.5.1 | When does a tech enter hours? | ⬜ | | End of day? Per apparatus? |
| 4.5.2 | Are hours tied to specific apparatus or project-level? | ⬜ | | Schema supports apparatus-level |
| 4.5.3 | Do hours require approval? | ⬜ | | PM reviews before billing? |
| 4.5.4 | How do quoted hours vs actual hours reconcile? | ⬜ | | Alerts if over? |

### 4.6 Completion & Handoff

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 4.6.1 | What defines "complete" for an apparatus? | ⬜ | | Status set? Assessment entered? Hours logged? |
| 4.6.2 | Is there a review/approval step before final complete? | ✅ | **Yes - Job Lead approval triggers revenue recognition** | Tech submits → PENDING_REVIEW → Job Lead approves → COMPLETED. Approval timestamp = earned revenue. |
| 4.6.3 | What happens when all apparatus in a scope complete? | ⬜ | | Auto-update scope status? |
| 4.6.4 | What happens when all scopes complete? | ⬜ | | Project status update? Trigger billing? |

### 4.7 Field Requirements (Contextual Validation)

**Key Insight:** "Required" depends on WHEN and WHO. Power Apps failed by requiring everything upfront.

**Three Validation Contexts:**

| Context | Who | When | Purpose |
|---------|-----|------|--------|
| **Project Build** | PM / Import | Creating tracker from Estimator | Populate apparatus rows |
| **Field Work** | Tech | Submitting completed work | Capture test results |
| **Review/Approval** | Job Lead | Approving for revenue | Quality gate |

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 4.7.1 | What fields are required at **Project Build**? | ⬜ | | Core fields from Estimator JSON: Scope, Equipment Type, Hours, Section? |
| 4.7.2 | What fields are required at **Tech Submit**? | ⬜ | | Assessment (required), Task Delays (default 0), Notes (optional)? |
| 4.7.3 | What fields are required at **Job Lead Approval**? | ⬜ | | Just confirmation? Or additional fields? |
| 4.7.4 | What fields are "Business Recommended" but not blocking? | ⬜ | | Priority? Due Date? |
| 4.7.5 | Can validation rules be enforced in UI vs database? | ⬜ | | UI for UX, DB for integrity |
| 4.7.6 | What happens if required field is missing at submit? | ⬜ | | Block submit? Warning? |
| 4.7.7 | Should defaults auto-populate to reduce friction? | ⬜ | | Task Delays = 0, Availability = NOT_AVAILABLE? |

**Draft Field Requirements Matrix:**

| Field | Project Build | Tech Submit | Job Lead Approval | Notes |
|-------|---------------|-------------|-------------------|-------|
| scope | ✅ Required | - | - | From Estimator |
| equipment_type | ✅ Required | - | - | From Estimator |
| quoted_hours | ✅ Required | - | - | From Estimator |
| availability | Default: NOT_AVAILABLE | - | ⚠️ Recommended | Job Lead flips to AVAILABLE |
| priority | - | - | Optional | PM decision flag |
| due_date | - | - | ⚠️ Recommended | For overdue calc |
| assessment | - | ✅ Required | - | NETA test result |
| task_delays | - | ✅ Required (default 0) | - | Hours beyond quote |
| notes | - | Optional | Optional | Free text |
| has_issue | - | Optional | Optional | Flag for attention |

*Status: ⬜ Open - needs business decision on each field*

---

## Section 5: Offline Functionality

### 5.1 Offline Scope

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 5.1.1 | What features MUST work offline? | ⬜ | | View assignments, mark complete, enter hours? |
| 5.1.2 | What features are OK to be online-only? | ⬜ | | Document upload? PM dashboard? |
| 5.1.3 | How much data should be cached offline? | ⬜ | | Assigned work only? Full project? |
| 5.1.4 | Should documents be available offline? | ⬜ | | Pre-download assigned resources? |

### 5.2 Sync Behavior

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 5.2.1 | How often should sync attempt when online? | ⬜ | | Real-time? Every 5 min? Manual? |
| 5.2.2 | What happens on sync failure? | ⬜ | | Retry? Queue? Alert user? |
| 5.2.3 | How are sync conflicts resolved? | ⬜ | | Last write wins? Field tech wins? Flag for review? |
| 5.2.4 | Is there a visual indicator for sync status? | ⬜ | | Offline badge? Last synced time? |

### 5.3 Conflict Scenarios

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 5.3.1 | Tech marks complete offline, PM changes to "On Hold" online. Who wins? | ⬜ | | Need clear rule |
| 5.3.2 | Two techs edit same apparatus offline. Who wins? | ⬜ | | Should this even be possible? |
| 5.3.3 | Tech enters hours offline, actual gets changed online. Merge or overwrite? | ⬜ | | Likely additive |

---

## Section 6: Data & Integration

### 6.1 Excel Import/Export

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 6.1.1 | Which Excel format is the import standard? | ⬜ | | Garney tracker structure? |
| 6.1.2 | Is import a one-time migration or ongoing? | ⬜ | | Until app replaces Excel |
| 6.1.3 | Can users export data back to Excel? | ⬜ | | Familiar reporting format |
| 6.1.4 | What validation happens on import? | ⬜ | | Reject bad data? Flag for review? |

### 6.2 PowerDB Integration

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 6.2.1 | What data comes from PowerDB? | ⬜ | | Job numbers? Client info? |
| 6.2.2 | Sync direction: PowerDB → Supabase only, or bidirectional? | ⬜ | | Read-only initially |
| 6.2.3 | Sync frequency? | ⬜ | | Daily? Hourly? On-demand? |
| 6.2.4 | How to handle PowerDB data that doesn't match schema? | ⬜ | | Transform rules |

### 6.3 Future Integrations

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 6.3.1 | Connecteam - what data would sync? | ⬜ | | Schedule? Time tracking? |
| 6.3.2 | Estimator tool - how does it integrate? | ⬜ | | Import quotes? Shared apparatus types? |
| 6.3.3 | TCC Calculator - what's the touch point? | ⬜ | | Project linking? Data handoff? |

---

## Section 7: Technical Standards

### 7.1 Code & File Organization

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 7.1.1 | Coding style guide? | ⬜ | | Prettier config? ESLint rules? |
| 7.1.2 | File naming convention for code? | ⬜ | | kebab-case? PascalCase for components? |
| 7.1.3 | Folder structure for Next.js app? | ⬜ | | App router? Feature-based? |
| 7.1.4 | Where do shared types/interfaces live? | ⬜ | | `/types/` folder? |
| 7.1.5 | Where do API calls live? | ⬜ | | `/lib/api/` or `/services/`? |

### 7.2 Database Conventions

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 7.2.1 | Table naming: singular or plural? | ⬜ | | Current: plural (projects, scopes) |
| 7.2.2 | Column naming convention? | ⬜ | | snake_case (current) |
| 7.2.3 | UUID vs serial for IDs? | ⬜ | | Current: UUID |
| 7.2.4 | Soft delete (is_active) or hard delete? | ⬜ | | Current: soft delete |
| 7.2.5 | Audit columns on all tables? | ⬜ | | created_at, updated_at, created_by? |

### 7.3 Git Workflow

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 7.3.1 | Branching strategy? | ⬜ | | main + feature branches? |
| 7.3.2 | Commit message format? | ⬜ | | Conventional commits? |
| 7.3.3 | Who can merge to main? | ⬜ | | Desktop Claude after review? |
| 7.3.4 | Code review required? | ⬜ | | Desktop reviews VS Code work? |

---

## Section 8: AI Orchestration

### 8.1 Workflow Definition

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 8.1.1 | Is the `ai_tasks` table the primary work queue? | ⬜ | | Or use simpler HANDOFFS system? |
| 8.1.2 | What task types are valid? | ⬜ | | create, enhance, review, assemble, etc. |
| 8.1.3 | What are the task priorities and their meanings? | ⬜ | | critical, high, normal, low, background |
| 8.1.4 | How long should a task take before it's "stuck"? | ⬜ | | Alert threshold |

### 8.2 Agent Responsibilities

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 8.2.1 | What is Desktop Claude's primary responsibility? | ⬜ | | Orchestration, QC, complex reasoning |
| 8.2.2 | What is VS Code Claude's primary responsibility? | ⬜ | | UI development, implementation |
| 8.2.3 | When should Codex be used? | ⬜ | | Bulk generation? Or not at all? |
| 8.2.4 | What requires human (Jason) decision? | ⬜ | | Business logic, priorities, approvals |

### 8.3 Quality Gates

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 8.3.1 | What defines "done" for a task? | ⬜ | | Code works? Tests pass? Documented? |
| 8.3.2 | What requires Desktop Claude review? | ⬜ | | All VS Code work? Only complex? |
| 8.3.3 | What requires Jason review? | ⬜ | | Business logic? User-facing? |

---

## Section 9: UI/UX Design

### 9.1 Design System

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 9.1.1 | Color scheme? | ⬜ | | Brand colors? Dark mode? |
| 9.1.2 | Component library? | ⬜ | | shadcn/ui (current choice) |
| 9.1.3 | Mobile-first or desktop-first? | ⬜ | | Laptops primary, but responsive |
| 9.1.4 | Accessibility requirements? | ⬜ | | WCAG level? |

### 9.2 Navigation

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 9.2.1 | Main navigation structure? | ⬜ | | Sidebar? Top nav? Role-based? |
| 9.2.2 | How do users switch between views? | ⬜ | | Dashboard → Project → Apparatus |
| 9.2.3 | Breadcrumb navigation? | ⬜ | | For deep drill-downs |

### 9.3 Key Screens (Priority Order)

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 9.3.1 | What is the "home" screen for a field tech? | ⬜ | | My assignments today? |
| 9.3.2 | What is the "home" screen for a PM? | ⬜ | | Project list? Dashboard? |
| 9.3.3 | What views are essential for MVP? | ⬜ | | List screens vs. detail screens |

---

## Section 10: Reporting & Analytics

### 10.1 Standard Reports

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 10.1.1 | What reports are needed for Phase 1? | ⬜ | | Project status? Hours? Revenue? |
| 10.1.2 | Who can run reports? | ⬜ | | PM? Admin? |
| 10.1.3 | Export formats needed? | ⬜ | | PDF? Excel? |

### 10.2 Dashboards

| # | Question | Status | Decision | Rationale |
|---|----------|--------|----------|-----------|
| 10.2.1 | Executive dashboard - what metrics? | ⬜ | | Revenue, utilization, pipeline? |
| 10.2.2 | PM dashboard - what metrics? | ⬜ | | Project progress, blockers, hours? |
| 10.2.3 | Tech dashboard - what metrics? | ⬜ | | Personal completion rate? |

---

## Decisions Made

*Move items here after decision is finalized and documented*

### Template:

| # | Question | Decision | Rationale | Date | Documented In |
|---|----------|----------|-----------|------|---------------|
| X.X.X | Question text | The decision | Why | YYYY-MM-DD | File path |

---

## Change Log

| Date | Section | Change | By |
|------|---------|--------|-----|
| 2025-12-31 | All | Initial creation | Desktop Claude |

---

*This is a living document. Update as decisions are made.*
