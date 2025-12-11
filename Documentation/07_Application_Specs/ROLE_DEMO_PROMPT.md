# RESA Power - Role-Based Demo Prompt

> **Purpose:** Single v0.dev prompt that creates an interactive prototype with role switching  
> **Goal:** Get stakeholder feedback on what each role should see/do  
> **Instructions:** Copy this entire prompt into v0.dev, then share the preview link

---

## THE PROMPT (Copy Everything Below This Line)

```
Create an interactive role-based dashboard prototype for RESA Power, an electrical testing company. Include a role switcher that completely changes the UI based on selected role.

## Core Requirements

### Role Switcher (Always Visible)
- Dropdown in top-right corner of header, next to user avatar
- Label shows current role: "Viewing as: [Role Name]"
- Options: Executive, Project Manager, Estimator, Field Technician, Office Admin
- When role changes, entire dashboard transforms - different nav, different widgets, different data scope
- Add a subtle banner below header: "🔍 DEMO MODE - Switch roles to see different views"

### Sidebar Navigation (Collapsible Groups)
- Use accordion-style expandable menu groups
- Each group has a category icon and chevron toggle
- Clicking group header expands/collapses menu items
- Some items show badges: notification counts, "🚧 Coming Soon", "🔜 Phase 2"
- Sidebar can be collapsed to icons only (hamburger toggle)
- Remember expanded/collapsed state

### Future Enhancement Styling
- Items marked "Coming Soon" or "Phase 2" show a muted style (50% opacity)
- Clicking them shows a placeholder page with feature preview and "Request Early Access" button
- This demonstrates platform vision without implying it's ready

### Tech Stack
- shadcn/ui components (including Accordion, Collapsible)
- Tailwind CSS
- Lucide React icons
- React useState for role switching and sidebar state

---

## EXECUTIVE VIEW (Default)

### Sidebar Navigation (Collapsible Groups)

**Navigation should have expandable/collapsible menu groups with chevron icons:**

**📊 OPERATIONS** (expanded by default)
- Dashboard (active, Home icon)
- Projects (Folder icon)
- Clients (Building2 icon)
- Apparatus (Cpu icon)

**👥 RESOURCES** (collapsed by default)
- Employees (Users icon)
- Equipment (Wrench icon)
- Scheduling (Calendar icon) — shows "🚧 Coming Soon" badge

**📋 SERVICES** (expanded by default)
- Power System Studies (Zap icon, badge "12")
- Estimates (Calculator icon)
- Reports (FileText icon)

**� REFERENCE MATERIALS** (collapsed by default)
- NETA Standards (BookOpen icon)
- SOPs (ClipboardList icon)
- Safety Documents (ShieldAlert icon)
- Equipment Manuals (Book icon)
- Drawings (FileImage icon)

**🛡️ SAFETY** (collapsed by default)
- Safety Dashboard (ShieldCheck icon) — shows "🚧 Coming Soon" badge
- JHA Forms (ClipboardCheck icon) — shows "🚧 Coming Soon" badge
- Incident Reports (AlertTriangle icon) — shows "🚧 Coming Soon" badge

**💰 FINANCE** (collapsed by default)
- Financials (DollarSign icon)
- Invoicing (Receipt icon) — shows "🔜 Phase 2" label

**⚙️ ADMIN** (collapsed by default)
- Admin Settings (Settings icon, lock badge)
- User Management (UserCog icon)
- Integrations (Plug icon) — shows "🔜 Phase 2" label

**Sidebar Footer:**
- Collapse/expand all toggle
- "v2.0 - Dec 2025" version text
- Help/Support link

### Dashboard Content

**Header Row:**
- "Executive Dashboard" title
- Date range selector: This Month / This Quarter / This Year / Custom
- Location filter: All Locations / Phoenix / Denver / Las Vegas / San Diego

**Stats Cards Row (4 cards):**
1. Total Revenue
   - Value: $2,847,500
   - Subtext: "Quoted this quarter"
   - Trend: +12% vs last quarter (green arrow up)

2. Recognized Revenue
   - Value: $1,923,400
   - Subtext: "67.5% of quoted"
   - Progress bar showing 67.5%

3. Gross Margin
   - Value: 38.2%
   - Subtext: "Target: 40%"
   - Color: amber (below target)
   - Decision callout: Small "?" icon - tooltip: "DECISION: What's the target margin?"

4. Active Projects
   - Value: 47
   - Subtext: "Across 5 locations"
   - Breakdown hover: Phoenix (18), Denver (12), Las Vegas (9), San Diego (8)

**Second Row - Charts:**
Left (60%): Bar Chart - "Revenue by Location"
- Stacked bars showing Quoted (blue) vs Recognized (green) by location
- X-axis: Phoenix, Denver, Las Vegas, San Diego

Right (40%): Pie Chart - "Revenue by Service Type"  
- Testing: 65%
- Engineering Studies: 20%
- Emergency Services: 10%
- Thermal Imaging: 5%

**Third Row - Tables:**
Left: "Projects Needing Attention"
- Table with columns: Project, Client, Issue, Days Overdue
- Red highlight on overdue items
- Sample data:
  - LASNAP16, GSL, "Scope not invoiced", 15 days
  - DENTX-089, Acme Corp, "Testing incomplete", 7 days
  - ORLFL-234, Beta Inc, "Missing documentation", 3 days

Right: "Top Performers This Month"
- Table: Employee, Revenue Recognized, # Projects
- Sample data with 5 employees

**Decision Points Section (Highlighted Box):**
Yellow background box titled "📋 Questions for Review"
- "Should executives see individual employee performance metrics?"
- "What financial data should roll up to this view?"
- "Are there KPIs we're missing?"

---

## POWER SYSTEM STUDIES VIEW (Accessible from Sidebar - All Roles Except Tech)

A dedicated module for tracking PSS, Arc Flash, and Coordination studies.

### Header:
- "Power System Studies" title
- "New Study" button (blue, plus icon)
- Filter: Study Type dropdown (All, PSS, Arc Flash, Coordination)
- Filter: Status dropdown

### Stats Cards Row (4):
1. Active Studies: 12
   - "In progress with engineer"
   
2. Awaiting Documents: 8
   - Subtext: "Client action needed"
   - Red highlight if any > 7 days
   
3. Draft Reviews: 3
   - "Ready for client approval"
   
4. Avg Days to Complete: 34
   - Trend vs. last quarter

### Pipeline/Kanban Board:
Horizontal columns showing study status flow:

| Intake | Awaiting Docs | With Engineer | Draft Review | Final/Complete |
|--------|---------------|---------------|--------------|----------------|
| 2 | 8 | 7 | 3 | 15 |

Cards in each column show:
- Project name, Client name
- Days in status (red if overdue threshold)
- Engineer name (Shaw Engineering, etc.)
- Drag-drop to move between columns (demo interaction)

### Studies Table (Below Kanban):
Columns: Job #, Project Name, Client, Study Type (badge), Engineer, Status (badge), Days in Status, Docs Status, PO Amount
- Sort by any column
- Expandable rows showing document checklist

Sample Data Rows:
| Job # | Project | Client | Type | Engineer | Status | Days | Docs |
|-------|---------|--------|------|----------|--------|------|------|
| 629266 | SWA Tech Ops | Rosendin | PSS | Shaw | Partial Docs | 5 | 3/5 |
| 627687 | Hydro | DP Electric | Arc Flash | Shaw | Stickers Pending | 12 | 5/5 |
| 659189 | Airport Center | ICON | PSS + AF | Shaw | Draft Submitted | 3 | 5/5 |
| 673518 | P7 Lift Station | City of Buckeye | PSS | Shaw | In Progress | 8 | 4/5 |
| 626206 | Scottsdale Ranch Park | K2 | Arc Flash | - | Awaiting Docs | 21 | 1/5 |

### Document Tracker Panel (Right Side or Expandable):
When a study is selected, show document checklist:
- ☑ Single-Line Diagram (received 11/5)
- ☑ Panel Schedules (received 11/5)
- ☑ Transformer Data (received 11/5)
- ☐ Utility Fault Current (requested, 5 days overdue)
- ☐ Main Breaker Info (requested, 5 days overdue)

With "Send Reminder" button for outstanding items.

### Decision Callout:
"🔌 POWER SYSTEM STUDIES QUESTIONS"
- "Is PSS tracking separate from main Projects or integrated?"
- "Who can create/edit studies? (Sales, PM, Admin)"
- "Automated reminder emails at 3/7/14 days?"
- "RFI tracking needed within studies?"
- "Client portal for document upload?"

---

## ESTIMATES VIEW (New Sidebar Tab)

For creating, managing, and tracking project estimates/quotes.

### Header:
- "Estimates" title
- "Create Estimate" button (blue, plus icon)
- Toggle: Active / Won / Lost / All

### Stats Cards Row (4):
1. Open Estimates: 18
   - Value: $847,500
   
2. Pending Approval: 6
   - "Awaiting customer response"
   
3. Win Rate (YTD): 58%
   - Subtext: "Target: 65%"
   - Color: amber if below target
   
4. Avg Estimate Value: $38,200
   - Trend indicator

### Estimates Table:
Columns: Estimate #, Project/Opportunity Name, Client, Service Type, Total Value, Status, Created Date, Estimator, Actions

Sample Data:
| Est # | Project | Client | Services | Value | Status | Date | By |
|-------|---------|--------|----------|-------|--------|------|-----|
| E-2024-0147 | Main Campus Upgrade | State University | Testing + PSS | $125,000 | Sent | 12/05 | J. Smith |
| E-2024-0146 | Distribution Center | Amazon | Testing | $67,500 | Draft | 12/04 | M. Johnson |
| E-2024-0145 | Warehouse A | Target | Arc Flash | $12,000 | Won | 12/01 | J. Smith |
| E-2024-0144 | Hospital Wing C | Mercy Health | Full Service | $89,000 | Lost | 11/28 | K. Davis |
| E-2024-0143 | Data Center | Microsoft | Testing | $245,000 | Negotiating | 11/25 | M. Johnson |

Status badges:
- Draft: gray
- Sent: blue
- Negotiating: purple
- Won: green
- Lost: red

### Estimate Detail Preview (Modal or Slide-out):
When clicking an estimate, show summary:

**Header:**
- Estimate # E-2024-0147
- Client: State University
- Created by: J. Smith on 12/05/2024

**Services Breakdown Table:**
| Service | Qty | Rate | Total |
|---------|-----|------|-------|
| Substation Testing | 1 | $45,000 | $45,000 |
| Switchgear Testing | 12 | $2,500 | $30,000 |
| Transformer Testing | 8 | $3,500 | $28,000 |
| Power System Study | 1 | $15,000 | $15,000 |
| Mobilization | 1 | $7,000 | $7,000 |

**Totals:**
- Subtotal: $125,000
- Discount: $0
- **Total: $125,000**

**Actions:** Edit, Duplicate, Send to Client, Convert to Project, Mark Won, Mark Lost

### Quick Create Panel (Slide-out):
- Client selector (searchable)
- Project/Opportunity name
- Service type checkboxes (Testing, PSS, Arc Flash, Engineering)
- Location/Site
- "Add Line Items" section
- Notes/Special terms
- Generate from Template button

### Decision Callout:
"📝 ESTIMATES QUESTIONS"
- "Does estimate creation happen here or in Excel first?"
- "Who can approve/send estimates? (Estimator, Manager, Both)"
- "Standard pricing tables or manual entry?"
- "Link estimates to won Projects automatically?"
- "Track revision history of estimates?"
- "Integration with existing Excel estimator tools?"

---

## REPORTS VIEW (Sidebar Tab - Generates Project Reports/Proposals)

For creating professional PDF reports from project data with auto-populated templates.

### Header:
- "Report Generator" title
- "Create Report" button (blue, plus icon)
- Tabs: All Reports | My Reports | Pending Review

### Stats Cards Row (4):
1. Reports Generated: 156
   - "This month"
   
2. Pending Review: 8
   - "Awaiting manager approval"
   
3. Finalized: 142
   - "Ready for delivery"
   
4. Avg Generation Time: 2.3 min
   - "From submit to PDF"

### Recent Reports Table:
Columns: Report #, Project, Client, Type (badge), Employee, Status (badge), Generated, Actions

Sample Data:
| Report # | Project | Client | Type | By | Status | Date |
|----------|---------|--------|------|-----|--------|------|
| RPT-2024-0892 | Sundance TIAC | Stellar Energy | ATS | K. Ellertson | Finalized | 12/10 |
| RPT-2024-0891 | Main Campus | State University | MTS | A. Smith | Pending | 12/10 |
| RPT-2024-0890 | Data Center | Microsoft | ATS | K. Ellertson | Draft | 12/09 |
| RPT-2024-0889 | Hospital Wing | Mercy Health | IR | M. Johnson | Finalized | 12/08 |

Status badges:
- Draft: gray
- Generated: blue
- Pending Review: amber
- Finalized: green

### Report Type Badges:
- ATS (Acceptance Testing): blue
- MTS (Maintenance Testing): green
- IR (Infrared/Thermal): orange
- Combined: purple

### "Create Report" Modal (3-Step Wizard):

**Step 1: Select Project**
```
┌────────────────────────────────────────┐
│ Step 1 of 3: Select Project            │
├────────────────────────────────────────┤
│                                        │
│  Search: [Type to search projects...] │
│                                        │
│  Recent Projects:                      │
│  ○ Sundance TIAC - Stellar Energy     │
│  ○ Main Campus - State University     │
│  ○ Data Center Expansion - Microsoft  │
│                                        │
│                    [Cancel]  [Next →] │
└────────────────────────────────────────┘
```

**Step 2: Report Details (Auto-Populated)**
```
┌────────────────────────────────────────┐
│ Step 2 of 3: Report Details            │
├────────────────────────────────────────┤
│                                        │
│  Report Type: [ATS - Acceptance ▼]     │
│                                        │
│  ── Auto-Filled from Project ──        │
│  Client: Stellar Energy        (auto)  │
│  Site: Sundance TIAC           (auto)  │
│  Address: 4567 Industrial Blvd (auto)  │
│                                        │
│  ── Editable Fields ──                 │
│  Date: [12/11/2025]                    │
│  Attn: [Terry Johnson         ]        │
│  RE: [Acceptance Testing Report]       │
│                                        │
│  Equipment to Include:                 │
│  ☑ ATS-1 - Main Switchgear   (Pass)   │
│  ☑ ATS-2 - Generator Transfer (Pass)  │
│  ☐ ATS-3 - Emergency Panel   (Pending)│
│                                        │
│  Employee: [Kole Ellertson ▼]          │
│                                        │
│                  [← Back]  [Next →]    │
└────────────────────────────────────────┘
```

**Step 3: Review & Generate**
```
┌────────────────────────────────────────┐
│ Step 3 of 3: Review & Generate         │
├────────────────────────────────────────┤
│                                        │
│  ┌────────────────────────────────┐   │
│  │   REPORT PREVIEW               │   │
│  │   ┌──────────────────────────┐ │   │
│  │   │  [RESA Logo]             │ │   │
│  │   │                          │ │   │
│  │   │  Acceptance Testing      │ │   │
│  │   │  Report                  │ │   │
│  │   │                          │ │   │
│  │   │  Stellar Energy          │ │   │
│  │   │  Sundance TIAC           │ │   │
│  │   │  December 11, 2025       │ │   │
│  │   └──────────────────────────┘ │   │
│  └────────────────────────────────┘   │
│                                        │
│  Sections Included:                    │
│  ☑ Cover Page                          │
│  ☑ Summary Letter                      │
│  ☑ Scope of Work                       │
│  ☑ Results & Recommendations           │
│  ☑ Equipment Summary Table             │
│  ☑ Test Data Sheets                    │
│  ☐ Thermal Images (none available)     │
│                                        │
│        [← Back]  [Generate Report]     │
└────────────────────────────────────────┘
```

**Step 4: Success State**
```
┌────────────────────────────────────────┐
│ ✓ Report Generated Successfully        │
├────────────────────────────────────────┤
│                                        │
│  Report #: RPT-2024-0893               │
│  File: Stellar_Energy_ATS_Report.pdf   │
│  Size: 2.4 MB                          │
│                                        │
│  [Preview PDF]  [Download]  [Email]    │
│                                        │
│  ────────────────────────────────────  │
│  Status: Generated                     │
│  [Mark as Finalized]                   │
│  [Create Another Report]               │
│                                        │
└────────────────────────────────────────┘
```

### Decision Callout:
"📄 REPORT GENERATION QUESTIONS"
- "Who can generate reports? (Any tech, or assigned only)"
- "Manager approval required before finalizing?"
- "Auto-email to client option?"
- "Version history / revision tracking?"
- "Templates customizable per client?"
- "Batch generation for multi-site projects?"

---

## PROJECT MANAGER VIEW

### Changes from Executive:
- Sidebar: Remove "Financials" and "Admin Settings"
- Add "My Team" to sidebar

### Dashboard Content

**Header:** "My Projects Dashboard"

**Filters:**
- Only shows their assigned projects
- Banner: "Showing 12 projects assigned to you"

**Stats Cards (4):**
1. My Active Projects: 12
2. Tasks Due This Week: 28
3. Team Members: 6
4. Projects On Track: 9 of 12 (pie indicator)

**Decision Callout Card (Yellow):**
"💰 FINANCIAL VISIBILITY QUESTION"
- "Can PMs see project-level revenue and margins?"
- Toggle demo: Show/Hide Financial Card
- If shown: displays "Project Revenue: $425,000 | Margin: 34%"
- If hidden: displays placeholder "Financial data restricted"

**Main Content:**
Left: "My Projects" table
- Columns: Project #, Name, Client, Status, Progress, Tasks Remaining
- Click opens project detail (can be placeholder modal)

Right: "My Team's Workload"
- List of team members with task count
- Visual bar showing capacity
- "DECISION: Should PMs assign tasks directly?"

**Calendar Widget:**
- Week view showing scheduled field work
- "DECISION: Integrate with Outlook/Google Calendar?"

---

## ESTIMATOR VIEW

### Sidebar Changes:
- Dashboard
- My Quotes (with badge showing count)
- Opportunities
- Clients
- Pricing Tools
- Win/Loss Analysis

### Dashboard Content

**Header:** "Estimator Dashboard"

**Stats Cards:**
1. Open Opportunities: 23
   - Value: $1.2M potential
   
2. Quotes Pending: 8
   - "Awaiting customer response"
   
3. Win Rate: 62%
   - This quarter (green if above target)
   - "DECISION: What's target win rate?"
   
4. Average Quote Value: $45,200
   - Trend vs last quarter

**Pipeline Funnel Visualization:**
- Stages: Lead → Qualified → Quoted → Negotiating → Won/Lost
- Show count and value at each stage
- Colored by stage

**Main Content:**
"My Opportunities" table
- Columns: Opportunity, Client, Value, Stage, Days in Stage, Probability
- Sort by probability or value
- Actions: View, Edit Quote, Mark Won, Mark Lost

**Decision Callout:**
"🔒 SENSITIVE DATA QUESTION"
- "Can estimators see competitor pricing?"
- "Can estimators see margin targets?"
- "Should won/lost reasons be tracked?"

---

## FIELD TECHNICIAN VIEW

### Complete UI Change - Mobile-First Design

**No Sidebar** - Bottom navigation instead:
- Home (dashboard)
- My Work
- Equipment
- Documents
- Profile

### Dashboard Content (Card-based, vertical scroll)

**Header:** 
- "Welcome back, Mike" (tech name)
- Today's date
- Sync status indicator (green = synced)

**Today's Schedule Card:**
- Card showing today's assignments
- Time, Location, Project, Task type
- "Start" button for current task
- Map link icon

**This Week Card:**
- 5 assignments this week
- Calendar strip view (Mon-Fri with dots)

**Quick Actions:**
- Large buttons: "Start Test", "View Checklist", "Submit Report"
- "DECISION: What quick actions do techs need?"

**Recent Equipment Card:**
- Last 3 pieces of equipment tested
- Quick access to re-open

**Decision Callouts:**
"📱 MOBILE EXPERIENCE QUESTIONS"
- "Do techs have company phones or use personal?"
- "Offline capability required? (no cell service in substations)"
- "Photo capture needed during tests?"
- "Digital signature for completion?"

---

## OFFICE ADMIN VIEW

### Sidebar:
- Dashboard
- Projects (all, read-mostly)
- Clients
- Scheduling
- Documents
- Data Entry

### Dashboard Content

**Header:** "Operations Dashboard"

**Stats:**
1. Projects This Month: 28
2. Documents Pending: 12
3. Schedule Conflicts: 2 (red)
4. Data Entry Queue: 45 items

**Main Sections:**

"Scheduling Overview" (Calendar)
- Week view of all technician assignments
- Color coded by technician
- Drag-drop to reassign (demo interaction)
- "DECISION: Can admin reassign techs?"

"Document Checklist"
- Projects missing required documents
- Upload buttons
- Status: Missing, Uploaded, Approved

"Data Entry Queue"
- Items needing to be entered
- Source: field notes, customer emails
- "DECISION: What data entry is manual vs automated?"

**Decision Callout:**
"👤 ADMIN PERMISSIONS QUESTIONS"
- "Can admin edit project details or just view?"
- "Can admin see any financial information?"
- "Who approves schedule changes?"

---

## SHARED COMPONENTS (All Roles)

### Header Bar
- RESA Power logo (left)
- Search bar (center) - "Search projects, clients, equipment..."
- Notifications bell with badge
- Role switcher dropdown
- User avatar with dropdown: Profile, Settings, Sign Out

### Footer
- "DEMO VERSION - Not connected to real data"
- Link placeholder: "Give Feedback"

---

## STYLING REQUIREMENTS

Colors:
- Primary Blue: #1e40af
- Success Green: #22c55e  
- Warning Amber: #f59e0b
- Error Red: #ef4444
- Background: #f8fafc
- Cards: white with shadow-sm

Decision Callout Boxes:
- Yellow/amber background (#fef3c7)
- Left border: amber (#f59e0b)
- Icon: clipboard or question mark
- Clear question text

Cards:
- Rounded-lg
- White background
- Subtle shadow
- Consistent padding (p-6)

Make sure role switching is immediate and dramatic - the entire layout should visibly change to demonstrate what each user type experiences.
```

---

## EMPLOYEES VIEW (Sidebar → Resources → Employees)

Team management and employee profiles.

### Header:
- "Employee Directory" title
- "Add Employee" button
- Search bar: "Search by name, role, certification..."
- Filters: Location dropdown, Role dropdown, Certification dropdown

### Stats Cards Row (4):
1. Total Employees: 47
   - "Across all locations"
   
2. Field Technicians: 32
   - "NETA certified"
   
3. On Project Today: 28
   - "Currently assigned"
   
4. Certifications Expiring: 3
   - "Within 90 days" (amber)

### Employee Grid/Table View Toggle:

**Grid View (Default):**
Cards showing:
- Profile photo or avatar
- Name, Title
- Location badge (Phoenix, Denver, etc.)
- NETA Level badge (I, II, III, IV)
- Status indicator (Available/On Project/PTO)
- Current assignment (if any)

**Table View:**
| Name | Role | Location | NETA Level | Status | Current Project | Certs Expire |
|------|------|----------|------------|--------|-----------------|--------------|
| Aaron Carter | Lead Tech | Phoenix | III | On Project | Sturgeon 635418 | Mar 2026 |
| Austin Painter | Tech | Phoenix | II | On Project | Central Mesa | Oct 2025 |
| Tyler Sorg | Tech | Phoenix | II | Available | - | Dec 2025 |

### Employee Detail Panel (Slide-out):
- Contact info
- Certification list with expiration dates
- Current/recent project history
- Skills/equipment qualifications
- Schedule visibility (link to Scheduling)
- Performance metrics (hours billed, projects completed)

### Decision Callout:
"👥 EMPLOYEES MODULE QUESTIONS"
- "Import from existing HR system or standalone?"
- "Should techs see each other's schedules?"
- "Certification renewal workflow needed?"
- "Track training/continuing education?"

---

## EQUIPMENT VIEW (Sidebar → Resources → Equipment)

Company-owned test equipment tracking.

### Header:
- "Equipment Inventory" title  
- "Add Equipment" button
- Search bar
- Filters: Type, Location, Status, Calibration Status

### Stats Cards Row (4):
1. Total Equipment: 156
   - "In inventory"
   
2. On Project: 89
   - "Currently assigned"
   
3. Available: 52
   - "Ready for assignment"
   
4. Calibration Due: 8
   - "Within 30 days" (amber warning)

### Equipment Table:
| Asset # | Description | Type | Location | Status | Assigned To | Cal Due |
|---------|-------------|------|----------|--------|-------------|---------|
| EQ-001 | Megger DLRO10X | DLRO | Phoenix | On Project | LASNAP16 | Jan 2026 |
| EQ-015 | Doble F6150 | Relay Tester | Denver | Available | - | Feb 2026 |
| EQ-023 | Flir E96 | Thermal | Las Vegas | On Project | Casino Project | Dec 2025 ⚠️ |

### Equipment Detail Panel:
- Full specs
- Assignment history (where it's been)
- Calibration history
- Maintenance log
- Current location/project
- QR code for mobile scanning

### Decision Callout:
"🔧 EQUIPMENT MODULE QUESTIONS"
- "Barcode/QR scanning for check-in/out?"
- "GPS tracking on high-value items?"
- "Integrate with calibration vendor?"
- "Auto-alerts before calibration expires?"

---

## SCHEDULING VIEW (Sidebar → Resources → Scheduling)

**🚧 FUTURE ENHANCEMENT - Phase 2**

### Placeholder UI:
Large card with visual mockup showing:

```
┌─────────────────────────────────────────────────────────────────────┐
│  📅 SCHEDULING MODULE                                    🚧 Coming  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐                      │
│   │ Mon │ Tue │ Wed │ Thu │ Fri │ Sat │ Sun │                      │
│   ├─────┼─────┼─────┼─────┼─────┼─────┼─────┤                      │
│   │░░░░░│░░░░░│░░░░░│░░░░░│░░░░░│     │     │  ← Aaron C.          │
│   │░░░░░│░░░░░│░░░░░│░░░░░│░░░░░│     │     │  ← Tyler S.          │
│   │▓▓▓▓▓│▓▓▓▓▓│▓▓▓▓▓│     │     │     │     │  ← Austin P.         │
│   │     │░░░░░│░░░░░│░░░░░│░░░░░│     │     │  ← Josh G.           │
│   └─────┴─────┴─────┴─────┴─────┴─────┴─────┘                      │
│                                                                     │
│   Legend: ░░░ Project A   ▓▓▓ Project B   ▒▒▒ PTO                  │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ 📍 This view will show:                                     │  │
│   │   • Weekly/monthly calendar grid                            │  │
│   │   • Drag-and-drop shift assignment                          │  │
│   │   • Project-based color coding                              │  │
│   │   • Conflict detection                                      │  │
│   │   • PTO/unavailability blocking                             │  │
│   │   • Hours summary per employee                              │  │
│   │   • Integration with Connecteam (import/export)             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   Current Solution: Connecteam App                                  │
│   Phase 2 Goal: Native scheduling with project visibility          │
│                                                                     │
│   [Learn More]                          [Request Early Access]      │
└─────────────────────────────────────────────────────────────────────┘
```

### Integration Note Box:
"Currently managing schedules in Connecteam? This module will provide:
- **Project Visibility**: See which projects techs are assigned to (Connecteam limitation)
- **Apparatus-Level Assignment**: Assign techs to specific equipment within a project  
- **Automatic Hours Tracking**: Sync scheduled hours to project budgets
- **Two-Way Sync**: Option to sync with Connecteam during transition"

### Decision Callout:
"📅 SCHEDULING MODULE QUESTIONS"
- "Replace Connecteam entirely or sync with it?"
- "What's the biggest Connecteam pain point? (Project visibility confirmed)"
- "Who creates/edits schedules? (PM, Lead, Admin)"
- "Approval workflow for schedule changes?"
- "Mobile clock-in/out needed?"
- "Travel time tracking between sites?"

---

## REFERENCE MATERIALS VIEW (Sidebar → Reference Materials)

**📚 DOCUMENT LIBRARY - Available Now (Ready for Content)**

### Header:
- "📚 Reference Materials" title
- Search bar: "Search documents..."
- Filter dropdowns: Document Type | Equipment Category | Date Added
- Upload button (Admin only): "+ Upload Document"

### Tab Navigation (Sub-tabs):
```
[ NETA Standards ] [ SOPs ] [ Safety Docs ] [ Equipment Manuals ] [ Drawings ]
      (active)
```

### Content Area - Card Grid:

```
┌─────────────────────────────────────────────────────────────────────┐
│  📚 REFERENCE MATERIALS                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [ NETA Standards ] [ SOPs ] [ Safety Docs ] [ Manuals ] [ Drawings]│
│        (active)                                                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🔍 Search documents...                    [Equipment ▼] [+ Upload]│
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ 📖 NETA ATS-2025 │  │ 📖 NETA MTS-2023 │  │ 📖 NETA ECS-2024 │  │
│  │ Acceptance       │  │ Maintenance      │  │ Commissioning    │  │
│  │ Testing Spec     │  │ Testing Spec     │  │ Spec             │  │
│  │                  │  │                  │  │                  │  │
│  │ 📁 PDF • 2.4 MB  │  │ 📁 PDF • 3.1 MB  │  │ 📁 PDF • 1.8 MB  │  │
│  │ [View] [Link]    │  │ [View] [Link]    │  │ [View] [Link]    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ 📖 NETA ETT-2022 │  │ 📋 Section 7.3   │  │ 📋 Section 7.6   │  │
│  │ Tech Training    │  │ Transformers     │  │ Switchgear       │  │
│  │                  │  │ (Power)          │  │ (MV)             │  │
│  │                  │  │                  │  │                  │  │
│  │ 📁 PDF • 1.2 MB  │  │ 📁 Procedure     │  │ 📁 Procedure     │  │
│  │ [View] [Link]    │  │ [View] [Tests]   │  │ [View] [Tests]   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### SOPs Tab Content:
```
┌─────────────────────────────────────────────────────────────────────┐
│  Standard Operating Procedures                      [+ New SOP]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ 📋 SOP-001       │  │ 📋 SOP-002       │  │ 📋 SOP-003       │  │
│  │ HV Testing       │  │ Relay Testing    │  │ Oil Sampling     │  │
│  │ Procedure        │  │ Procedure        │  │ Procedure        │  │
│  │                  │  │                  │  │                  │  │
│  │ Rev: 3.2         │  │ Rev: 2.0         │  │ Rev: 1.5         │  │
│  │ Updated: 11/2025 │  │ Updated: 09/2025 │  │ Updated: 10/2025 │  │
│  │ [View] [Edit]    │  │ [View] [Edit]    │  │ [View] [Edit]    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Equipment Manuals Tab Content:
```
┌─────────────────────────────────────────────────────────────────────┐
│  Equipment Manuals                    [Equipment Type ▼] [+ Upload] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ 📕 ABB VD4       │  │ 📕 Eaton VCP-W   │  │ 📕 SEL-751       │  │
│  │ Vacuum Breaker   │  │ Circuit Breaker  │  │ Relay Manual     │  │
│  │                  │  │                  │  │                  │  │
│  │ Manufacturer:    │  │ Manufacturer:    │  │ Manufacturer:    │  │
│  │ ABB              │  │ Eaton            │  │ SEL              │  │
│  │ 📁 PDF • 8.2 MB  │  │ 📁 PDF • 5.4 MB  │  │ 📁 PDF • 12.1 MB │  │
│  │ [View] [Download]│  │ [View] [Download]│  │ [View] [Download]│  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Drawings Tab Content:
```
┌─────────────────────────────────────────────────────────────────────┐
│  Technical Drawings               [Project ▼] [Type ▼] [+ Upload]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ 📐 LASNAP16      │  │ 📐 LASNAP16      │  │ 📐 General       │  │
│  │ One-Line         │  │ Relay Settings   │  │ Typical MV       │  │
│  │ Diagram          │  │ Diagram          │  │ Switchgear       │  │
│  │                  │  │                  │  │                  │  │
│  │ Project: LASNAP16│  │ Project: LASNAP16│  │ Project: (none)  │  │
│  │ 📁 DWG • 1.2 MB  │  │ 📁 PDF • 0.8 MB  │  │ 📁 DWG • 2.3 MB  │  │
│  │ [View] [Download]│  │ [View] [Download]│  │ [View] [Download]│  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Document Detail Modal (on View click):
```
┌──────────────────────────────────────────────────────────────────┐
│  📖 NETA ATS-2025 - Acceptance Testing Specification      [✕]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Document Type: NETA Standard                                    │
│  File Size: 2.4 MB                                               │
│  Uploaded: Dec 1, 2025                                           │
│  Last Viewed: Dec 10, 2025                                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 🔗 Linked Equipment Types:                               │   │
│  │   • Power Transformers (Section 7.3)                     │   │
│  │   • Medium Voltage Switchgear (Section 7.6)              │   │
│  │   • Low Voltage Circuit Breakers (Section 7.14)          │   │
│  │   • Protective Relays (Section 7.9)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  [Open PDF]  [Download]  [Copy Link]  [Unlink from Equipment]   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Right Sidebar - Quick Links Panel:
```
Recently Viewed:
• NETA ATS-2025 (2 hours ago)
• SOP-001 HV Testing (yesterday)
• ABB VD4 Manual (3 days ago)

Popular Documents:
• NETA MTS-2023 (47 views)
• SOP-002 Relay Testing (32 views)
• SEL-751 Manual (28 views)
```

### Decision Callout:
"📚 REFERENCE MATERIALS QUESTIONS"
- "Where are manuals currently stored? (SharePoint, file server, Dropbox?)"
- "Who uploads/maintains documents? (Admin only, or all roles?)"
- "Link documents to specific apparatus types for quick access?"
- "Version control needed for SOPs?"
- "Offline access required for field techs?"
- "Integration with existing document management system?"

### Database Tables Supporting This:
- `neta_procedures` - NETA section procedures  
- `neta_test_items` - Individual tests within procedures
- `sops` - Standard operating procedures
- `safety_documents` - Safety-related documents
- `datasheets` - Equipment datasheets/manuals
- `apparatus_type_resources` - Links documents to equipment types

---

## SAFETY VIEW (Sidebar → Safety → Safety Dashboard)

**🚧 FUTURE ENHANCEMENT - Phase 2**

### Placeholder UI:

```
┌─────────────────────────────────────────────────────────────────────┐
│  🛡️ SAFETY MANAGEMENT                                   🚧 Coming │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│   │ 📋 JHAs       │  │ 🔒 LOTO       │  │ ⚠️ Incident   │          │
│   │    Forms      │  │   Permits     │  │   Reports     │          │
│   │               │  │               │  │               │          │
│   │  [Coming]     │  │  [Coming]     │  │  [Coming]     │          │
│   └───────────────┘  └───────────────┘  └───────────────┘          │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ 📍 Planned Features:                                        │  │
│   │   • Job Hazard Analysis (JHA) digital forms                 │  │
│   │   • LOTO permit tracking with approval workflow             │  │
│   │   • Incident reporting and investigation tracking           │  │
│   │   • Safety certification tracking by employee               │  │
│   │   • PPE inventory and assignment                            │  │
│   │   • Toolbox talk sign-off documentation                     │  │
│   │   • Near-miss reporting                                     │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   [Learn More]                          [Request Early Access]      │
└─────────────────────────────────────────────────────────────────────┘
```

### Decision Callout:
"🛡️ SAFETY MODULE QUESTIONS"
- "Digital JHA forms required before work starts?"
- "LOTO permit workflow with approvals?"
- "Link safety docs to specific apparatus types?"
- "Incident reporting and tracking?"
- "Integration with existing safety software?"

---

## How to Use This Demo

### Step 1: Generate in v0.dev
1. Go to [v0.dev](https://v0.dev)
2. Paste the entire prompt above
3. Wait for generation (may take 30-60 seconds)
4. v0 will likely generate a multi-file React component

### Step 2: Iterate if Needed
Common follow-up prompts:
- "Make the role switcher more prominent"
- "Add more sample data to the tables"
- "Make the decision callouts stand out more"
- "Add a mobile view toggle for the tech dashboard"

### Step 3: Share the Preview
- v0.dev provides a shareable link
- Send to your boss: "Click around and switch roles - tell me what's missing or wrong"
- Take notes on his reactions

### Step 4: Capture Feedback
Watch for / ask about:
- What did he click first?
- What questions did he ask?
- What did he say was missing?
- Which role views made sense vs confused him?
- What financial data should/shouldn't be visible?

---

## Questions Embedded in Demo

The demo includes visual callouts for these decisions:

### Executive View
- [ ] What is the target gross margin?
- [ ] What KPIs are we missing?
- [ ] Should individual employee metrics be visible?
- [ ] What financial rollups matter most?

### Power System Studies
- [ ] Is PSS tracking separate from main Projects or integrated?
- [ ] Who can create/edit studies? (Sales, PM, Admin)
- [ ] Automated reminder emails at 3/7/14 days?
- [ ] RFI tracking needed within studies?
- [ ] Client portal for document upload?
- [ ] Engineer assignment workflow?

### Estimates
- [ ] Does estimate creation happen here or in Excel first?
- [ ] Who can approve/send estimates? (Estimator, Manager, Both)
- [ ] Standard pricing tables or manual entry?
- [ ] Link estimates to won Projects automatically?
- [ ] Track revision history of estimates?
- [ ] Integration with existing Excel estimator tools?

### Reports
- [ ] Who can generate reports? (Any tech, or assigned to project only)
- [ ] Manager approval required before finalizing?
- [ ] Auto-email to client option?
- [ ] Version history / revision tracking?
- [ ] Templates customizable per client?
- [ ] Batch generation for multi-site projects?

### Employees
- [ ] Import from existing HR system or standalone?
- [ ] Should techs see each other's schedules?
- [ ] Certification renewal workflow needed?
- [ ] Track training/continuing education?
- [ ] Employee self-service portal?

### Equipment
- [ ] Barcode/QR scanning for check-in/out?
- [ ] GPS tracking on high-value items?
- [ ] Integrate with calibration vendor?
- [ ] Auto-alerts before calibration expires?
- [ ] Equipment reservation system?

### Scheduling (Future)
- [ ] Replace Connecteam entirely or sync with it?
- [ ] What's the biggest Connecteam pain point? 
- [ ] Who creates/edits schedules? (PM, Lead, Admin)
- [ ] Approval workflow for schedule changes?
- [ ] Mobile clock-in/out needed?
- [ ] Travel time tracking between sites?

### Safety (Future)
- [ ] Digital JHA forms required before work starts?
- [ ] LOTO permit workflow with approvals?
- [ ] Link safety docs to specific apparatus types?
- [ ] Incident reporting and tracking?
- [ ] Integration with existing safety software?

### Project Manager View
- [ ] Can PMs see project-level revenue/margins?
- [ ] Can PMs assign tasks to team members?
- [ ] Calendar integration with Outlook/Google?
- [ ] What defines "their" projects - assigned PM only?

### Estimator View
- [ ] Can estimators see competitor pricing history?
- [ ] Should they see margin targets for pricing decisions?
- [ ] Track win/loss reasons for each opportunity?
- [ ] What's the target win rate?

### Field Technician View
- [ ] Company phones or personal devices?
- [ ] Offline capability required?
- [ ] Photo capture during tests?
- [ ] Digital signatures for completion?
- [ ] What quick actions are most important?

### Office Admin View
- [ ] Can admin edit or only view project data?
- [ ] Can admin see any financial data?
- [ ] Can admin reassign technicians?
- [ ] Who approves schedule changes?

### General
- [ ] Do we need a Client Portal (external users)?
- [ ] Multi-location access control? (Phoenix can't see Denver?)
- [ ] Integration needs? (QuickBooks, Outlook, GPS?)

---

## After the Demo Meeting

Come back with his answers and we'll:
1. Finalize the role definitions
2. Create the database schema for roles/permissions  
3. Build RLS policies in Supabase
4. Update the UI spec with confirmed role views
