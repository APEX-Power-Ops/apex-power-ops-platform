# RESA Power Platform - UI Requirements Review

> **Purpose**: Help stakeholders visualize and decide on UI layout, workflows, and priorities  
> **Audience**: GM, Operations Management, Project Managers  
> **Date**: December 10, 2025

---

## Executive Summary

The database is built. We have **30 tables** tracking everything from projects and equipment testing to company assets and safety documents. Now we need to decide **how people will interact with this data**.

This document presents:
1. **User Roles** - Who needs access to what?
2. **Core Screens** - What pages/views do we need?
3. **Layout Options** - Different ways to organize the UI
4. **Workflow Questions** - How should processes flow?

**Please review and mark your preferences or add comments.**

---

## Part 1: User Roles & Access

### Who Will Use This System?

| Role | Primary Tasks | Access Level |
|------|---------------|--------------|
| **GM / Operations** | Overview dashboards, financial summaries, resource allocation | Full read, limited edit |
| **Project Manager** | Project setup, scope management, progress tracking | Full access to assigned projects |
| **Field Technician** | Mark apparatus complete, view test procedures, check equipment | Mobile-first, limited to assigned work |
| **Office Admin** | Client/site setup, data entry, report generation | Full data entry access |
| **External Engineer** | PSS document upload, RFI responses | Portal access only |

### Questions for Review:

1. **Are these roles accurate?** Should we add/remove any?
2. **Should technicians see financial data** (revenue, rates)?
3. **Do PMs need to see ALL projects** or only their assigned ones?

---

## Part 2: Dashboard Options

### Option A: Role-Based Home Screens

Each user sees a dashboard tailored to their role.

```
+---------------------------------------------------------------------+
|  RESA Power                              [Search] [Bell] [User]     |
+---------------------------------------------------------------------+
|                                                                     |
|  Welcome, John                              Today: Dec 10, 2025     |
|                                                                     |
|  +-------------+ +-------------+ +-------------+ +-------------+    |
|  | 12          | | 47          | | 3           | | $127,500    |    |
|  | Active      | | Apparatus   | | Overdue     | | Pending     |    |
|  | Projects    | | In Progress | | Tasks       | | Revenue     |    |
|  +-------------+ +-------------+ +-------------+ +-------------+    |
|                                                                     |
|  MY PROJECTS                                        [View All ->]   |
|  +-------------------------------------------------------------+   |
|  | LASNAP16 - LA DWP Substation   ========-- 78%   Due: 12/20  |   |
|  | DALGAR01 - Garney Construction ======---- 62%   Due: 01/15  |   |
|  | PHXRES02 - Phoenix Retail      ====------ 45%   Due: 01/30  |   |
|  +-------------------------------------------------------------+   |
|                                                                     |
|  RECENT ACTIVITY                                                    |
|  - Apparatus "MV Breaker #3" marked complete (2 hrs ago)            |
|  - New RFI received on LASNAP16 PSS Study (5 hrs ago)               |
|  - Equipment CAL-001 assigned to DALGAR01 (yesterday)               |
|                                                                     |
+---------------------------------------------------------------------+
```

**Pros**: Users see only what is relevant to them  
**Cons**: More development work, different views to maintain

---

### Option B: Universal Dashboard with Filters

Everyone sees the same layout, filters control what is shown.

```
+---------------------------------------------------------------------+
|  RESA Power                              [Search] [Bell] [User]     |
+---------------------------------------------------------------------+
|                                                                     |
|  FILTERS: [Location v] [PM v] [Status v] [Date Range v] [Clear]     |
|                                                                     |
|  +--------------------------------------------------------------+   |
|  |  PROJECTS          APPARATUS       REVENUE        EQUIPMENT  |   |
|  |  ------------------------------------------------------------   |
|  |  12 Active         156 Total       $425,000       45 Units   |   |
|  |  3 On Hold         89 Complete     $127,500       3 On Proj  |   |
|  |  28 Completed      47 In Progress  Pending        42 Avail   |   |
|  +--------------------------------------------------------------+   |
|                                                                     |
|  PROJECT LIST                              Sort: [Due Date v]       |
|  +----------------------------------------------------------------+ |
|  | # | Project      | Client   | PM    | Progress | Revenue | Due | |
|  +---+--------------+----------+-------+----------+---------+-----+ |
|  | 1 | LASNAP16     | LA DWP   | J.Doe | ==== 78% | $45,200 |12/20| |
|  | 2 | DALGAR01     | Garney   | M.Smi | ===- 62% | $38,100 |01/15| |
|  | 3 | PHXRES02     | Phoenix  | J.Doe | ==-- 45% | $22,800 |01/30| |
|  +----------------------------------------------------------------+ |
|                                                                     |
+---------------------------------------------------------------------+
```

**Pros**: Simpler to build, everyone learns one interface  
**Cons**: Can be overwhelming, may expose data some should not see

---

### Option C: Card-Based Navigation

Main screen shows "apps" or modules user can access.

```
+---------------------------------------------------------------------+
|  RESA Power                              [Search] [Bell] [User]     |
+---------------------------------------------------------------------+
|                                                                     |
|  +-----------------+  +-----------------+  +-----------------+      |
|  |  PROJECTS       |  |  FIELD WORK     |  |  FINANCIALS     |      |
|  |                 |  |                 |  |                 |      |
|  |  12 Active      |  |  47 In Progress |  |  $127K Pending  |      |
|  |  3 Need Action  |  |  8 Due Today    |  |  View Reports   |      |
|  |                 |  |                 |  |                 |      |
|  |  [Open ->]      |  |  [Open ->]      |  |  [Open ->]      |      |
|  +-----------------+  +-----------------+  +-----------------+      |
|                                                                     |
|  +-----------------+  +-----------------+  +-----------------+      |
|  |  EQUIPMENT      |  |  RESOURCES      |  |  PSS PORTAL     |      |
|  |                 |  |                 |  |                 |      |
|  |  45 Total       |  |  18 Technicians |  |  5 Active       |      |
|  |  2 Need Cal     |  |  3 Unassigned   |  |  2 Awaiting Doc |      |
|  |                 |  |                 |  |                 |      |
|  |  [Open ->]      |  |  [Open ->]      |  |  [Open ->]      |      |
|  +-----------------+  +-----------------+  +-----------------+      |
|                                                                     |
|  +-----------------+  +-----------------+  +-----------------+      |
|  |  TECH DOCS      |  |  CLIENTS        |  |  ADMIN          |      |
|  |                 |  |                 |  |                 |      |
|  |  NETA / SOPs    |  |  42 Clients     |  |  Settings       |      |
|  |  Safety Docs    |  |  156 Sites      |  |  Users          |      |
|  |                 |  |                 |  |                 |      |
|  |  [Open ->]      |  |  [Open ->]      |  |  [Open ->]      |      |
|  +-----------------+  +-----------------+  +-----------------+      |
|                                                                     |
+---------------------------------------------------------------------+
```

**Pros**: Clean, mobile-friendly, easy to understand  
**Cons**: Extra click to get anywhere, less information density

---

### Dashboard Preference:

**Which approach do you prefer?**
- [ ] Option A: Role-Based (different views per user type)
- [ ] Option B: Universal with Filters (everyone sees same layout)
- [ ] Option C: Card-Based Navigation (app-style modules)
- [ ] Hybrid: ________________________________

---

## Part 3: Project Detail Screen

When you click into a project, what should you see?

### Option A: Tabbed Layout

```
+---------------------------------------------------------------------+
|  <- Back    LASNAP16 - LA DWP Substation Modernization    [Edit]    |
+---------------------------------------------------------------------+
|  Client: LA DWP          PM: John Doe         Status: IN PROGRESS   |
|  Site: Main Substation   Due: Dec 20, 2025    Progress: ====- 78%   |
+---------------------------------------------------------------------+
|  [Overview] [Scopes] [Apparatus] [Equipment] [Documents] [Activity] |
+---------------------------------------------------------------------+
|                                                                     |
|  OVERVIEW TAB CONTENT:                                              |
|                                                                     |
|  FINANCIAL SUMMARY                                                  |
|  +----------------------------------------------------------------+ |
|  | Contract Value    | Recognized Revenue | Pending    | Invoiced | |
|  | $125,000          | $97,500            | $27,500    | $85,000  | |
|  +----------------------------------------------------------------+ |
|                                                                     |
|  SCOPE BREAKDOWN                                                    |
|  +----------------------------------------------------------------+ |
|  | Scope 1: Switchgear Testing      ========-- 85%    $45,000    | |
|  | Scope 2: Transformer Testing     =======--- 72%    $38,000    | |
|  | Scope 3: Cable Testing           =====----- 55%    $22,000    | |
|  | Scope 4: Relay Calibration       ========-- 80%    $20,000    | |
|  +----------------------------------------------------------------+ |
|                                                                     |
+---------------------------------------------------------------------+
```

---

### Option B: Sidebar Navigation

```
+---------------------------------------------------------------------+
|  <- Back    LASNAP16 - LA DWP Substation Modernization    [Edit]    |
+----------------+----------------------------------------------------+
|                |                                                    |
|  PROJECT MENU  |  FINANCIAL SUMMARY                                 |
|                |  +----------------------------------------------+  |
|  > Overview    |  | Contract    | Recognized | Pending | Invoiced|  |
|    Scopes      |  | $125,000    | $97,500    | $27,500 | $85,000 |  |
|    Apparatus   |  +----------------------------------------------+  |
|    Equipment   |                                                    |
|    Documents   |  PROJECT DETAILS                                   |
|    Team        |  +----------------------------------------------+  |
|    Activity    |  | Client:     LA DWP                           |  |
|                |  | Site:       Main Substation, 123 Power Ave   |  |
|  ------------- |  | PM:         John Doe                         |  |
|                |  | Start:      Oct 15, 2025                     |  |
|  QUICK ACTIONS |  | Due:        Dec 20, 2025                     |  |
|                |  | Status:     IN PROGRESS                      |  |
|  + Add Scope   |  | Progress:   78% Complete                     |  |
|  + Add Task    |  +----------------------------------------------+  |
|  Reports       |                                                    |
|                |  RECENT ACTIVITY                                   |
|                |  - MV Breaker #3 completed - 2 hrs ago             |
|                |  - Relay panel testing started - yesterday         |
|                |                                                    |
+----------------+----------------------------------------------------+
```

---

### Option C: Single Scrolling Page

```
+---------------------------------------------------------------------+
|  <- Back    LASNAP16 - LA DWP Substation Modernization    [Edit]    |
+---------------------------------------------------------------------+
|                                                                     |
|  +-------------------------------------------------------------+   |
|  | LA DWP  -  Main Substation  -  John Doe  -  IN PROGRESS     |   |
|  |                                                              |   |
|  | Progress: ================================---------- 78%     |   |
|  | Due: Dec 20, 2025 (10 days)                                  |   |
|  +-------------------------------------------------------------+   |
|                                                                     |
|  FINANCIALS --------------------------------------------------------|
|                                                                     |
|     $125,000          $97,500           $27,500          $85,000    |
|     Contract          Recognized        Pending          Invoiced   |
|                                                                     |
|  SCOPES (4) ------------------------------------------------ [+Add] |
|                                                                     |
|  +- Scope 1: Switchgear Testing ------------------------------+    |
|  |  ========-- 85%    12/14 Apparatus    $45,000    [View ->] |    |
|  +------------------------------------------------------------+    |
|  +- Scope 2: Transformer Testing -----------------------------+    |
|  |  =======--- 72%    8/11 Apparatus     $38,000    [View ->] |    |
|  +------------------------------------------------------------+    |
|                                                                     |
|  APPARATUS (47 total) --------------------------------------- [+Add]|
|                                                                     |
|  | Name              | Type          | Status      | Assessment |   |
|  | MV Breaker #1     | Circuit Brkr  | Complete    | Acceptable |   |
|  | MV Breaker #2     | Circuit Brkr  | Complete    | Minor Def  |   |
|  | MV Breaker #3     | Circuit Brkr  | Complete    | Acceptable |   |
|  | Transformer T1    | Transformer   | In Progress | --         |   |
|  | [Show all 47...]                                              |   |
|                                                                     |
|  EQUIPMENT ON SITE -------------------------------------- [+Assign] |
|                                                                     |
|  | Asset Tag   | Description      | Assigned To  | Cal Due     |   |
|  | TTR-001     | Turns Ratio Test | This Project | 03/15/2026  |   |
|  | DLRO-003    | Micro-Ohmmeter   | This Project | 06/01/2026  |   |
|                                                                     |
+---------------------------------------------------------------------+
```

---

### Project Detail Preference:

**Which layout do you prefer?**
- [ ] Option A: Tabbed (click tabs to switch sections)
- [ ] Option B: Sidebar (persistent menu on left)
- [ ] Option C: Single Scroll (everything on one long page)
- [ ] Preference: ________________________________

---

## Part 4: Field Tech Mobile View

Technicians need a mobile-friendly interface. What should they see?

### Option A: Task-Focused (Daily Work List)

```
+-------------------------------+
|  =  RESA Power        Bell    |
+-------------------------------+
|                               |
|  Good morning, Mike!          |
|                               |
|  TODAYS WORK                  |
|  +---------------------------+|
|  | LASNAP16                  ||
|  | LA DWP Substation         ||
|  |                           ||
|  | 8 apparatus remaining     ||
|  | [Start Work ->]           ||
|  +---------------------------+|
|                               |
|  APPARATUS TO TEST            |
|  +---------------------------+|
|  | O  MV Breaker #4          ||
|  |    Circuit Breaker        ||
|  |    Est: 2.5 hrs           ||
|  +---------------------------+|
|  | O  MV Breaker #5          ||
|  |    Circuit Breaker        ||
|  |    Est: 2.5 hrs           ||
|  +---------------------------+|
|  | O  Transformer T2         ||
|  |    Power Transformer      ||
|  |    Est: 4.0 hrs           ||
|  +---------------------------+|
|                               |
|  [View Test Procedures]       |
|  [Upload Photos]              |
|                               |
+-------------------------------+
```

---

### Option B: Checklist Style (Simple Check-Off)

```
+-------------------------------+
|  =  RESA Power        Bell    |
+-------------------------------+
|                               |
|  LASNAP16 - Switchgear Scope  |
|  -----------------------------|
|                               |
|  Progress: ========-- 78%     |
|  12 of 14 complete            |
|                               |
|  +---------------------------+|
|  | [X] MV Breaker #1         ||
|  | [X] MV Breaker #2         ||
|  | [X] MV Breaker #3         ||
|  | [ ] MV Breaker #4    [->] ||
|  | [ ] MV Breaker #5         ||
|  | [X] MV Breaker #6         ||
|  | [X] MV Breaker #7         ||
|  | ...                       ||
|  +---------------------------+|
|                               |
|  [Mark Selected Complete]     |
|                               |
+-------------------------------+
```

---

### Option C: Equipment-First (Detailed Per-Item)

```
+-------------------------------+
|  =  RESA Power        Bell    |
+-------------------------------+
|                               |
|  [Search apparatus...]        |
|                               |
|  CURRENT PROJECT              |
|  LASNAP16 - LA DWP            |
|                               |
|  +---------------------------+|
|  |       MV Breaker #4       ||
|  |     -----------------     ||
|  |     Circuit Breaker       ||
|  |     Eaton VCP-W 15kV      ||
|  |                           ||
|  |  Est. Hours: 2.5          ||
|  |  Delay Hours: 0           ||
|  |                           ||
|  |  +---------------------+  ||
|  |  | NETA Procedure      |  ||
|  |  | SOP                 |  ||
|  |  | Safety (JSA)        |  ||
|  |  | Datasheet           |  ||
|  |  +---------------------+  ||
|  |                           ||
|  |  [Mark Complete]          ||
|  |  [Add Delay Hours]        ||
|  |  [Report Issue]           ||
|  |                           ||
|  +---------------------------+|
|                               |
|  [<- Prev]         [Next ->]  |
|                               |
+-------------------------------+
```

---

### Mobile View Preference:

**Which mobile approach works best for techs?**
- [ ] Option A: Task-Focused (daily work list)
- [ ] Option B: Checklist (simple check-off)
- [ ] Option C: Equipment-First (detailed per-item view)
- [ ] Combination: ________________________________

---

## Part 5: Key Workflow Questions

### 5.1 Apparatus Completion Flow

**IMPLEMENTED: Two-Stage Approval Workflow**

See **Part 5A** above for full details. Key points:

- Tech submits apparatus -> Status = "Pending Review" (NO revenue yet)
- Lead reviews and approves -> Status = "Complete" + Revenue created
- Lead can reject -> Returns to "In Progress" with notes

**Tech captures on submission:**
- [x] Actual hours worked
- [x] Assessment (Acceptable / Minor / Major Deficiency / Non-Serviceable)
- [x] Delay hours and reason (customer-caused delays)
- [x] Notes
- [ ] Photos (future enhancement)

**Lead can override during approval:**
- Hours (if tech estimate seems wrong)
- Assessment (if tech judgment needs correction)

---

### 5.2 Equipment Assignment Flow

When equipment needs to move to a project:

**Option A: PM Assigns Equipment**
```
PM goes to Project -> Equipment tab -> [Assign Equipment] -> 
Select from available list -> Confirm
```

**Option B: Equipment Manager Assigns**
```
Admin goes to Equipment -> Find item -> [Assign] -> 
Select project -> Set dates -> Confirm
```

**Option C: Technician Requests**
```
Tech views project -> [Request Equipment] -> 
Creates request -> Manager approves -> Auto-assigned
```

**Preference**: ________________________________

---

### 5.3 Who Needs Financial Visibility?

| Information | GM | PM | Tech | Admin |
|-------------|----|----|------|-------|
| Contract value | ? | ? | ? | ? |
| Recognized revenue | ? | ? | ? | ? |
| Labor rates | ? | ? | ? | ? |
| Scope costs | ? | ? | ? | ? |
| Invoice status | ? | ? | ? | ? |

Mark Y/N for each cell.

---

## Part 6: Module Priority

We cannot build everything at once. **Please rank these modules 1-10** (1 = build first):

| Module | Description | Rank |
|--------|-------------|------|
| **Project Dashboard** | List projects, basic stats, click to view | ___ |
| **Project Detail** | Scopes, tasks, apparatus hierarchy | ___ |
| **Field Tech Mobile** | Mark apparatus complete on phone | ___ |
| **Equipment Tracking** | Where is our test equipment? | ___ |
| **Financial Reports** | Revenue recognition, billing status | ___ |
| **Resource/Tech Docs** | NETA procedures, SOPs, safety docs | ___ |
| **Employee Allocation** | Who is assigned where? | ___ |
| **Client/Site Management** | Add/edit customers and locations | ___ |
| **PSS Portal** | External engineer document exchange | ___ |
| **Admin/Settings** | User management, system config | ___ |

---

## Part 7: Data Already Available

Here is what the database tracks (for context on what screens can show):

### Projects and Work
- **Projects**: Name, client, site, PM, dates, status, financials
- **Scopes**: Work packages within projects (testing, studies, etc.)
- **Tasks**: Individual work items within scopes
- **Apparatus**: Equipment being tested (breakers, transformers, etc.)

### Financial
- **Revenue**: Auto-calculated when apparatus complete
- **Labor Rates**: Standard, overtime, double-time per scope
- **Summaries**: Rolled up at scope and project level

### Equipment and Resources
- **Test Equipment**: Company-owned gear (serials, cal dates)
- **Equipment Assignments**: Track where equipment is and history
- **NETA Procedures**: Standard test procedures by equipment type
- **SOPs**: Company standard operating procedures
- **Safety Documents**: JSAs, hazard alerts

### People and Organizations
- **Employees**: Staff with roles, departments, certifications
- **Clients**: Customer companies
- **Sites**: Physical locations
- **External Engineers**: For PSS studies

### PSS (Power System Studies)
- **Studies**: Project tracking for engineering studies
- **Documents**: Required docs per study type
- **RFIs**: Information requests to clients

---

## Part 8: Available Database Views

These pre-built views make certain screens easier to build:

| View | What It Shows | Good For |
|------|---------------|----------|
| v_projects_full | Projects with client/site names, financials | Project list dashboard |
| v_projects_active | Only active projects | Quick access |
| v_scope_summary | Scopes with project context | Project detail |
| v_scope_financials | Scope-level financial breakdown | Financial reports |
| v_apparatus_testing_status | Apparatus completion status | Field tech views |
| v_equipment_current_status | Equipment location/assignment | Equipment dashboard |
| v_project_equipment | Equipment per project | Project equipment tab |
| v_equipment_movement_history | Equipment audit trail | Equipment history |
| v_employee_roster | Employee list with details | Resource management |
| v_neta_test_details | NETA procedures expanded | Tech reference |
| v_apparatus_resources | Apparatus linked resources | Field reference |
| v_pss_dashboard | PSS study overview | PSS portal |

---

## Next Steps

1. **Review this document** and mark your preferences
2. **Add comments** where you have questions or different ideas
3. **Rank the modules** by priority
4. **Schedule a 30-min discussion** to walk through choices

Once we have your input, we can create detailed specs for the highest-priority modules and begin UI development with clear requirements.

---

*Document created: December 10, 2025*  
*For questions: Contact Jason*

---

## Part 5A: Apparatus Completion Workflow (CRITICAL)

### Two-Stage Approval Architecture

Revenue is only recognized when a **Lead/PM approves** the tech's submission, not when the tech marks it complete. This prevents premature revenue recognition and reduces errors.

```
+---------------------------------------------------------------------+
|                    APPARATUS COMPLETION FLOW                        |
+---------------------------------------------------------------------+
|                                                                     |
|  TECH (Mobile App)                    LEAD/PM (Dashboard)           |
|  -----------------                    -------------------           |
|                                                                     |
|  1. Tech completes testing                                          |
|     |                                                               |
|     v                                                               |
|  2. Tech opens apparatus                                            |
|     and fills in:                                                   |
|     - Actual hours worked                                           |
|     - Assessment (Acceptable/                                       |
|       Minor/Major Deficiency)                                       |
|     - Delay hours (if any)                                          |
|     - Notes                                                         |
|     |                                                               |
|     v                                                               |
|  3. Tech taps [Submit for Review]                                   |
|     |                                                               |
|     +---------------+                                               |
|                     |                                               |
|                     v                                               |
|              Status = "Pending Review"                              |
|              (NO revenue yet)                                       |
|                     |                                               |
|                     +------------------+                            |
|                                        |                            |
|                                        v                            |
|                             4. Item appears in                      |
|                                Lead's Approval Queue                |
|                                        |                            |
|                                        v                            |
|                             5. Lead reviews:                        |
|                                - Hours reasonable?                  |
|                                - Assessment correct?                |
|                                - Delay justified?                   |
|                                        |                            |
|                          +-------------+-------------+              |
|                          |                           |              |
|                          v                           v              |
|                     [APPROVE]                   [REJECT]            |
|                          |                           |              |
|                          v                           v              |
|                   Status = "Complete"         Status = "In Progress"|
|                          |                    (back to tech w/note) |
|                          v                                          |
|                   REVENUE RECORD CREATED                            |
|                   (automatic trigger)                               |
|                                                                     |
+---------------------------------------------------------------------+
```

### Lead Approval Queue Screen

```
+---------------------------------------------------------------------+
|  <- Back           Approval Queue                    [Filter v]     |
+---------------------------------------------------------------------+
|                                                                     |
|  PENDING APPROVALS (12)                          3 overdue (>24hr)  |
|                                                                     |
|  +----------------------------------------------------------------+ |
|  | LASNAP16 - LA DWP Substation                     5 pending     | |
|  | Oldest: 2 hrs ago                                              | |
|  | [Review Items ->]                                              | |
|  +----------------------------------------------------------------+ |
|  | DALGAR01 - Garney Construction                   4 pending     | |
|  | Oldest: 6 hrs ago                                              | |
|  | [Review Items ->]                                              | |
|  +----------------------------------------------------------------+ |
|  | PHXRES02 - Phoenix Retail                        3 pending     | |
|  | Oldest: 28 hrs ago  [!OVERDUE]                                 | |
|  | [Review Items ->]                                              | |
|  +----------------------------------------------------------------+ |
|                                                                     |
+---------------------------------------------------------------------+
```

### Individual Item Review Screen

```
+---------------------------------------------------------------------+
|  <- Queue     Review Submission                                     |
+---------------------------------------------------------------------+
|                                                                     |
|  MV Breaker #4                                                      |
|  Circuit Breaker - Eaton VCP-W 15kV                                 |
|  LASNAP16 > Switchgear Testing > MV Equipment                       |
|                                                                     |
|  +--------------------------------------------------------------+  |
|  | SUBMITTED BY          | Mike Thompson                        |  |
|  | SUBMITTED             | Dec 10, 2025 2:34 PM (2 hrs ago)     |  |
|  +--------------------------------------------------------------+  |
|  | QUOTED HOURS          | 2.5 hrs                              |  |
|  | ACTUAL HOURS          | 3.0 hrs        [Edit]                |  |
|  | VARIANCE              | +0.5 hrs (20% over)                  |  |
|  +--------------------------------------------------------------+  |
|  | ASSESSMENT            | Acceptable     [Edit v]              |  |
|  +--------------------------------------------------------------+  |
|  | DELAY HOURS           | 0.5 hrs                              |  |
|  | DELAY REASON          | Waited for client to de-energize     |  |
|  +--------------------------------------------------------------+  |
|  | TECH NOTES            |                                      |  |
|  | "Breaker tested good. Replaced worn arc chutes per client    |  |
|  | request. Lubricated operating mechanism."                    |  |
|  +--------------------------------------------------------------+  |
|                                                                     |
|  REVENUE IMPACT                                                     |
|  Rate: $125/hr x 3.0 hrs = $375.00                                  |
|                                                                     |
|  +---------------------------+  +-----------------------------+     |
|  |      [APPROVE]            |  |    [REJECT WITH REASON]     |     |
|  +---------------------------+  +-----------------------------+     |
|                                                                     |
|  [<- Previous Item]                           [Next Item ->]        |
|                                                                     |
+---------------------------------------------------------------------+
```

### Tech Mobile Submission Screen

```
+-------------------------------+
|  =  RESA Power        Bell    |
+-------------------------------+
|                               |
|  <- Back to List              |
|                               |
|  COMPLETE APPARATUS           |
|  MV Breaker #4                |
|  ----------------------------|
|                               |
|  Quoted Hours: 2.5            |
|                               |
|  Actual Hours Worked:         |
|  +-------------------------+  |
|  |  3.0                    |  |
|  +-------------------------+  |
|                               |
|  Assessment:                  |
|  +-------------------------+  |
|  |  Acceptable           v |  |
|  +-------------------------+  |
|  - Acceptable                 |
|  - Minor Deficiency           |
|  - Major Deficiency           |
|  - Non-Serviceable            |
|                               |
|  Delay Hours (customer-caused)|
|  +-------------------------+  |
|  |  0.5                    |  |
|  +-------------------------+  |
|                               |
|  Delay Reason:                |
|  +-------------------------+  |
|  | Waited for client to   |  |
|  | de-energize            |  |
|  +-------------------------+  |
|                               |
|  Notes:                       |
|  +-------------------------+  |
|  | Breaker tested good.   |  |
|  | Replaced worn arc      |  |
|  | chutes per client...   |  |
|  +-------------------------+  |
|                               |
|  +-------------------------+  |
|  |   SUBMIT FOR REVIEW    |  |
|  +-------------------------+  |
|                               |
|  (Lead will review before     |
|   marking complete)           |
|                               |
+-------------------------------+
```

### Workflow Status Indicators

| Status | Color | Meaning |
|--------|-------|---------|
| Not Started | Gray | Work not begun |
| In Progress | Blue | Tech actively working |
| **Pending Review** | **Orange** | **Submitted, awaiting lead approval** |
| Complete | Green | Approved, revenue recognized |
| Cancelled | Red | Work cancelled |

### Database Support

This workflow is fully implemented in the database:

| Function | Purpose |
|----------|---------|
| `submit_apparatus_for_review()` | Tech submits - sets status to Pending Review |
| `approve_apparatus_completion()` | Lead approves - triggers revenue creation |
| `reject_apparatus_submission()` | Lead rejects - returns to In Progress with note |
| `v_apparatus_approval_queue` | View of all pending items for lead review |
| `v_approval_queue_summary` | Dashboard summary by project |


