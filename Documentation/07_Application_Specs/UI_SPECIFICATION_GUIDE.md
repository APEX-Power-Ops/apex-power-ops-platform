# RESA Power - UI Specification Guide

> Comprehensive design specifications for the RESA Power Project Management Platform  
> **Version:** 1.0.0 | **Last Updated:** December 11, 2025  
> **Stack:** Next.js 16 + React 19 + shadcn/ui + Tailwind CSS

---

## Table of Contents

1. [Design System Foundation](#1-design-system-foundation)
2. [Component Library](#2-component-library)
3. [Page Layouts](#3-page-layouts)
4. [Feature Specifications](#4-feature-specifications)
5. [v0.dev Prompt Templates](#5-v0dev-prompt-templates)

---

## 1. Design System Foundation

### 1.1 Color Palette

```
Primary Colors:
- Brand Blue: #1e40af (buttons, links, active states)
- Brand Blue Light: #3b82f6 (hover states, accents)
- Brand Blue Dark: #1e3a8a (headers, emphasis)

Neutral Colors:
- Background: #f8fafc (page background)
- Card Background: #ffffff
- Border: #e2e8f0
- Text Primary: #1e293b
- Text Secondary: #64748b
- Text Muted: #94a3b8

Status Colors:
- Success/Complete: #22c55e (green)
- Warning/Pending: #f59e0b (amber)
- Error/Failed: #ef4444 (red)
- Info/In Progress: #3b82f6 (blue)
- Neutral/Draft: #6b7280 (gray)
```

### 1.2 Typography

```
Font Family: Inter (or system-ui fallback)

Headings:
- H1: 2.25rem (36px), font-bold, tracking-tight
- H2: 1.875rem (30px), font-semibold
- H3: 1.5rem (24px), font-semibold
- H4: 1.25rem (20px), font-medium

Body:
- Large: 1.125rem (18px)
- Default: 1rem (16px)
- Small: 0.875rem (14px)
- XSmall: 0.75rem (12px)
```

### 1.3 Spacing Scale

```
- xs: 0.25rem (4px)
- sm: 0.5rem (8px)
- md: 1rem (16px)
- lg: 1.5rem (24px)
- xl: 2rem (32px)
- 2xl: 3rem (48px)
```

### 1.4 Border Radius

```
- sm: 0.25rem (4px) - badges, small elements
- md: 0.375rem (6px) - buttons, inputs
- lg: 0.5rem (8px) - cards, modals
- xl: 0.75rem (12px) - large cards
- full: 9999px - avatars, pills
```

---

## 2. Component Library

### 2.1 Status Badges

| Status | Background | Text | Border | Use Case |
|--------|-----------|------|--------|----------|
| Opportunity | bg-amber-100 | text-amber-800 | border-amber-200 | New/potential projects |
| Sold | bg-blue-100 | text-blue-800 | border-blue-200 | Won, not started |
| In Progress | bg-green-100 | text-green-800 | border-green-200 | Active work |
| On Hold | bg-orange-100 | text-orange-800 | border-orange-200 | Paused |
| Complete | bg-slate-100 | text-slate-800 | border-slate-200 | Finished |
| Cancelled | bg-red-100 | text-red-800 | border-red-200 | Terminated |

**Apparatus Test Status:**
| Status | Background | Text |
|--------|-----------|------|
| Tested - Pass | bg-green-100 | text-green-800 |
| Tested - Fail | bg-red-100 | text-red-800 |
| Pending | bg-amber-100 | text-amber-800 |
| Not Tested | bg-slate-100 | text-slate-600 |

### 2.2 Cards

**Stats Card:**
```
- White background, rounded-lg, shadow-sm
- Icon in colored circle (top-left or left)
- Large number (2xl font, bold)
- Label below (sm font, muted)
- Optional trend indicator (+12% ↑)
```

**Project Card:**
```
- White background, rounded-lg, shadow-sm, hover:shadow-md
- Header: Project name (font-semibold), status badge
- Body: Client name, location, dates
- Footer: Progress bar, apparatus count
- Click: Navigate to project detail
```

**Apparatus Card:**
```
- White background, rounded-lg, border
- Icon based on equipment type
- Equipment type, manufacturer, model
- Serial number (monospace font)
- Status badge, last test date
```

### 2.3 Data Tables

**Standard Configuration:**
```
- Sticky header with sort indicators
- Alternating row backgrounds (optional)
- Row hover: bg-slate-50
- Cell padding: py-3 px-4
- Border-bottom on rows
- Actions column: icon buttons or dropdown menu
```

**Required Features:**
- Column sorting (click header)
- Search/filter bar above table
- Pagination below (10/25/50/100 per page)
- Row selection checkboxes (for bulk actions)
- Empty state with illustration

### 2.4 Forms

**Input Fields:**
```
- Label above input (font-medium, text-sm)
- Input: h-10, rounded-md, border, focus:ring-2
- Helper text below (text-sm, text-muted)
- Error state: border-red-500, text-red-600
- Required indicator: red asterisk
```

**Form Layout:**
```
- Single column for mobile
- Two columns for wider screens (md:grid-cols-2)
- Section headers with descriptions
- Logical grouping with spacing
```

### 2.5 Navigation

**Sidebar (Desktop):**
```
- Width: 256px (w-64)
- Fixed position, full height
- Logo at top
- Nav items: icon + label, py-2 px-3
- Active: bg-blue-50, text-blue-700, left border
- Hover: bg-slate-50
- Collapsible to icons only (w-16)
```

**Top Bar:**
```
- Height: 64px (h-16)
- Logo/title left
- Search bar center (optional)
- User menu right (avatar + dropdown)
- Notifications icon with badge
```

---

## 3. Page Layouts

### 3.1 Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│  SIDEBAR  │            TOP BAR                      │
│           ├─────────────────────────────────────────┤
│  Logo     │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      │
│           │  │Stat │ │Stat │ │Stat │ │Stat │      │
│  Nav      │  │Card │ │Card │ │Card │ │Card │      │
│  Items    │  └─────┘ └─────┘ └─────┘ └─────┘      │
│           │                                         │
│           │  ┌─────────────────┐ ┌────────────┐    │
│           │  │                 │ │            │    │
│           │  │   Chart/Table   │ │  Activity  │    │
│           │  │                 │ │   Feed     │    │
│           │  │                 │ │            │    │
│           │  └─────────────────┘ └────────────┘    │
└───────────┴─────────────────────────────────────────┘
```

### 3.2 List Page Layout

```
┌─────────────────────────────────────────────────────┐
│  Page Title                        [+ New Button]   │
├─────────────────────────────────────────────────────┤
│  [Search........]  [Filter ▼]  [Filter ▼]  [More]  │
├─────────────────────────────────────────────────────┤
│  □  Column 1    Column 2    Column 3    Actions    │
├─────────────────────────────────────────────────────┤
│  □  Row 1 data  data        data        ⋮          │
│  □  Row 2 data  data        data        ⋮          │
│  □  Row 3 data  data        data        ⋮          │
├─────────────────────────────────────────────────────┤
│  Showing 1-10 of 156         [◄] [1] [2] [3] [►]   │
└─────────────────────────────────────────────────────┘
```

### 3.3 Detail Page Layout

```
┌─────────────────────────────────────────────────────┐
│  ← Back   Project Name              [Edit] [More ▼]│
│           Client Name • Status Badge               │
├─────────────────────────────────────────────────────┤
│  [Overview] [Scopes] [Apparatus] [Tasks] [Finance] │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌───────────────────┐   │
│  │   Main Content       │  │   Sidebar Info    │   │
│  │   (Tab Content)      │  │   - Key Details   │   │
│  │                      │  │   - Quick Stats   │   │
│  │                      │  │   - Actions       │   │
│  │                      │  │                   │   │
│  └──────────────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 3.4 Form Page Layout

```
┌─────────────────────────────────────────────────────┐
│  ← Cancel            Create New Project             │
├─────────────────────────────────────────────────────┤
│         Step 1 ──●── Step 2 ──○── Step 3           │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────┐   │
│  │  Section Title                               │   │
│  │  Description text here                       │   │
│  │                                              │   │
│  │  Label *              Label                  │   │
│  │  [Input Field     ]   [Input Field      ]   │   │
│  │                                              │   │
│  │  Label *                                     │   │
│  │  [Dropdown Select               ▼]          │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│                           [Back]  [Next Step →]    │
└─────────────────────────────────────────────────────┘
```

---

## 4. Feature Specifications

### 4.1 Main Dashboard

**Stats Row (4 cards):**
1. **Active Projects** - Count of status = 'In Progress'
2. **Revenue This Month** - Sum of recognized revenue, current month
3. **Pending Tasks** - Count of incomplete tasks
4. **Overdue Items** - Tasks past due date

**Recent Projects Table:**
- Columns: Project #, Name, Client, Status, Progress
- 5-10 rows, sorted by last updated
- "View All" link to projects list

**Activity Feed:**
- Recent system activity
- Icon + description + timestamp
- "Project LASNAP16 status changed to In Progress"

### 4.2 Projects Module

**Projects List Page:**
- Filters: Status, Client, Location, Date Range, Estimator
- Columns: Project #, Name, Client, Status, Location, Start Date, Revenue, Progress
- Quick actions: View, Edit, Duplicate, Archive

**Project Detail Page:**

*Overview Tab:*
- Project info card (dates, estimator, PM, location)
- Financial summary card (quoted, recognized, margin)
- Recent activity

*Scopes Tab:*
- List of scopes as expandable cards
- Each shows: name, type, status, revenue progress
- Expand to see tasks within scope

*Apparatus Tab:*
- Grid or table of equipment
- Filter by type, status
- Quick add button

*Tasks Tab:*
- Kanban board OR table view toggle
- Group by scope or status
- Drag-drop to change status (if Kanban)

*Financials Tab:*
- Detailed breakdown
- Scope-by-scope table
- Charts for visual representation

### 4.3 Apparatus Module

**Apparatus List:**
- Filters: Equipment Type, Status, Project, Client
- Columns: Type, Manufacturer, Model, Serial #, Status, Project, Last Test
- Expandable rows for test details

**Apparatus Detail:**
- Equipment info header
- Test history timeline
- Linked procedures (NETA, SOPs)
- Documents/photos
- Revenue recognition status

### 4.4 Clients Module

**Clients List:**
- Search by name/code
- Columns: Code, Name, # Projects, # Sites, Total Revenue
- Click to view client detail

**Client Detail:**
- Client info header
- Sites list (accordion or table)
- Projects history
- Contact information
- Financial summary

### 4.5 Power System Studies Module

**PSS List Page:**
- Stats: Active Studies, Awaiting Documents, Draft Reviews, Avg Completion Days
- Kanban board with columns: Intake → Awaiting Docs → With Engineer → Draft Review → Complete
- Filters: Study Type (PSS, Arc Flash, Coordination), Status, Engineer, Client
- Columns: Job #, Project Name, Client, Study Type, Engineer, Status, Days in Status, Docs Status

**Study Types:**
- PSS (Power System Study)
- Arc Flash
- PSS + Arc Flash (Combined)
- Coordination (Protective Device Coordination)

**Status Flow:**
```
Intake → Awaiting Documents → Partial Documents → Ready for Engineer → 
In Progress → RFI Pending → Draft Submitted → Revisions Requested → 
Report Approved → Stickers Pending → Closed
```

**Document Tracking:**
Per-study checklist showing:
- Single-Line Diagram
- Utility Fault Current Data
- Main Breaker Information
- Panel Schedules
- Transformer Data

Status per document: Received, Requested, Overdue (with days)

**RFI Management:**
- RFI list per study
- Priority levels: Low, Medium, High, Urgent
- Status: Open, Responded, Closed
- Response tracking with dates

### 4.6 Estimates Module

**Estimates List Page:**
- Stats: Open Estimates (with $value), Pending Approval, Win Rate %, Avg Estimate Value
- Filters: Status (Draft, Sent, Negotiating, Won, Lost), Estimator, Date Range
- Columns: Estimate #, Project/Opportunity, Client, Services, Total Value, Status, Date, Estimator

**Estimate Statuses:**
- Draft (gray) - In progress
- Sent (blue) - Delivered to customer
- Negotiating (purple) - Active discussions
- Won (green) - Converted to project
- Lost (red) - Did not win

**Estimate Detail:**
- Header: Estimate #, Client, Created By, Date
- Line items table: Service, Quantity, Rate, Total
- Summary: Subtotal, Discount, Total
- Notes/Terms section
- Revision history (optional)

**Actions:**
- Edit, Duplicate, Send to Client
- Convert to Project (when Won)
- Mark Won/Lost with reason capture

**Quick Create:**
- Client selector
- Service type checkboxes
- Template selection
- Line item builder

### 4.7 Field Tech Interface (Mobile-First)

**Work Queue:**
- Cards for assigned tasks
- Swipe actions (start, complete)
- Priority indicators
- Offline capability badge

**Test Checklist:**
- Equipment header (type, serial, location)
- Collapsible test sections
- Large touch targets
- Pass/Fail/NA toggles
- Notes expansion
- Photo capture
- Submit with signature

---

## 5. v0.dev Prompt Templates

### 5.1 Dashboard Prompt

```
Create a project management dashboard using shadcn/ui and Tailwind CSS with:

Layout:
- Collapsible sidebar (256px) with logo, nav items with icons for Dashboard, Projects, Clients, Apparatus, Reports, Settings
- Top bar with search, notifications bell with badge, user avatar dropdown

Stats Row (4 cards):
- Active Projects: number with blue icon, "+3 this week" trend
- Monthly Revenue: dollar amount with green icon, percentage vs last month  
- Pending Tasks: number with amber icon
- Overdue Items: number with red icon if > 0

Main Content:
- Left (2/3): Recent Projects table with columns: Project #, Name, Client, Status (colored badge), Progress (bar), with "View All" link
- Right (1/3): Activity feed with icon, description, relative timestamp

Color scheme: Professional blue (#1e40af) primary, slate grays, white cards with subtle shadows
```

### 5.2 Projects List Prompt

```
Create a projects list page using shadcn/ui and Tailwind CSS:

Header:
- Page title "Projects" on left
- "New Project" button (blue, with plus icon) on right

Filters Bar:
- Search input with magnifying glass icon
- Status dropdown: All, Opportunity, Sold, In Progress, On Hold, Complete
- Client dropdown (searchable)
- Location dropdown
- Date range picker
- "Clear Filters" text button

Data Table:
- Checkbox column for bulk selection
- Sortable columns: Project # (monospace), Name (linked), Client, Status (badge), Location, Start Date, Revenue (right-aligned, currency), Progress (bar with percentage)
- Row hover state, click navigates to detail
- Actions column: three-dot menu with View, Edit, Duplicate, Archive options

Pagination:
- "Showing 1-10 of 156 projects"
- Page size selector: 10, 25, 50, 100
- Page number buttons with prev/next arrows

Status badges:
- Opportunity: amber-100 bg, amber-800 text
- Sold: blue-100 bg, blue-800 text
- In Progress: green-100 bg, green-800 text
- Complete: slate-100 bg, slate-600 text

Empty state if no results: illustration, "No projects found", "Try adjusting your filters"
```

### 5.3 Project Detail Prompt

```
Create a project detail page using shadcn/ui and Tailwind CSS:

Header:
- Back arrow link "← Projects"
- Project name (h1), Client name (text-muted), Status badge inline
- Right side: "Edit" button (outline), "Actions" dropdown (Export, Duplicate, Archive)

Tab Navigation:
- Tabs: Overview, Scopes (4), Apparatus (12), Tasks (28), Financials, Documents
- Numbers in parentheses show counts
- Active tab has blue underline

Overview Tab Content:
Left Column (2/3):
- "Project Details" card with 2-column grid: Dates (Start, End), Location, Estimator, Project Manager, Description (full width)
- "Financial Summary" card: 4 mini stats (Quoted, Recognized, Remaining, Margin %)

Right Column (1/3):
- "Quick Actions" card with buttons: Add Scope, Add Apparatus, View Report
- "Recent Activity" card with 5 latest activities (icon, text, timestamp)

Use consistent card styling: white bg, rounded-lg, shadow-sm, p-6
```

### 5.4 Apparatus Table Prompt

```
Create an apparatus/equipment list table using shadcn/ui and Tailwind CSS:

Filters:
- Search by serial number or manufacturer
- Equipment Type dropdown (Circuit Breaker, Transformer, Switchgear, Relay, etc.)
- Test Status dropdown (All, Tested-Pass, Tested-Fail, Pending, Not Tested)
- Project dropdown

Table:
- Expandable rows (click chevron to expand)
- Columns: Expand chevron, Equipment Type (with icon), Manufacturer, Model, Serial # (monospace font), Status (badge), Project (linked), Last Test Date
- Expanded content shows: Test results summary, linked procedures, notes

Status badges:
- Tested-Pass: green-100/green-800
- Tested-Fail: red-100/red-800  
- Pending: amber-100/amber-800
- Not Tested: slate-100/slate-600

Bulk Actions toolbar (appears when rows selected):
- "X items selected"
- Buttons: Change Status, Assign to Project, Export, Delete

Equipment type icons (use Lucide):
- Circuit Breaker: Zap
- Transformer: Box
- Switchgear: LayoutGrid
- Relay: Activity
- Cable: Cable
- Motor: Cog
```

### 5.5 Multi-Step Form Prompt

```
Create a multi-step project creation form using shadcn/ui, Tailwind CSS, and React Hook Form patterns:

Progress Indicator:
- 3 steps shown horizontally: "Client & Basics" → "Location & Team" → "Initial Scope"
- Current step: filled blue circle, completed: checkmark, upcoming: gray outline
- Connecting lines between steps

Step 1 - Client & Basics:
- Client select (searchable dropdown, required)
- "New Client" link below dropdown
- Project Name (text input, required)
- Description (textarea, optional)
- Opportunity checkbox with label "This is an opportunity (not yet sold)"

Step 2 - Location & Team:
- Site select (filtered by selected client, searchable)
- "New Site" link if none exist
- RESA Location dropdown (Phoenix, Denver, Las Vegas, San Diego)
- Estimator select
- Project Manager select
- Start Date picker
- Expected End Date picker

Step 3 - Initial Scope:
- Scope Name (text input)
- Scope Type dropdown (Testing, Engineering, Emergency, Thermal, etc.)
- Revenue Type toggle: "Time & Materials" | "Fixed Fee"
- If Fixed Fee: Quoted Amount (currency input)
- "Add Another Scope" button
- List of added scopes with remove option

Footer:
- Left: "Cancel" link
- Right: "Back" button (steps 2-3), "Next" or "Create Project" button (primary blue)

Form validation: Show inline errors, disable Next until required fields valid
```

### 5.6 Financial Dashboard Prompt

```
Create a financial dashboard for a project management app using shadcn/ui, Tailwind CSS, and Recharts:

Filters Bar:
- Date range: This Month, Last Month, This Quarter, This Year, Custom
- Location dropdown (multi-select)
- Project Manager dropdown

Stats Cards Row:
- Total Quoted Revenue: large dollar amount, "from X projects"
- Recognized Revenue: amount with percentage of quoted
- Gross Margin: percentage with color indicator (green if >40%, amber 20-40%, red <20%)
- Outstanding: quoted minus recognized

Charts Row:
- Left (60%): Bar chart "Quoted vs Recognized by Month" - dual bars, last 6 months
- Right (40%): Donut chart "Revenue by Scope Type" - Testing, Engineering, Emergency, Other

Revenue Table:
- Columns: Project, Client, Quoted, Recognized, Remaining, Margin %, Status
- Sortable by any column
- Progress bar in Recognized column showing % of quoted
- Totals row at bottom

Export: "Export to Excel" button in top right
```

### 5.7 Mobile Field Tech Checklist Prompt

```
Create a mobile-optimized test checklist interface using shadcn/ui and Tailwind CSS:

Header (sticky):
- Back arrow, "Test Checklist" title
- Equipment badge: "Circuit Breaker" with icon
- Sync status indicator (green dot = synced, amber = pending)

Equipment Info Card:
- Manufacturer: Eaton
- Model: VCP-W
- Serial: 12345-ABC (monospace, tap to copy)
- Location: Building A, Room 101

Progress Bar:
- "12 of 28 items complete" with percentage

Test Sections (Accordion):
- Section header: name, completion count, expand/collapse chevron
- Expanded shows test items

Test Item Row:
- Test description text
- Three toggle buttons: Pass (green) | Fail (red) | N/A (gray)
- Notes icon (shows count if notes exist)
- Tap notes icon to expand textarea

Section Example - "Visual & Mechanical":
- [ ] Enclosure condition - no damage or corrosion
- [ ] Proper labeling and nameplates
- [ ] Arc flash labels present
- [ ] Operating mechanism functions properly

Bottom Bar (sticky):
- "Add Photo" button with camera icon (shows count)
- "Save & Continue" primary button
- "Submit Complete" button (only enabled when all required items done)

Mobile considerations:
- Large touch targets (min 44px)
- Swipe between sections
- Pull to refresh
- Offline indicator banner at top if disconnected
```

---

## 6. Role-Based Views

> **See Also:** [ROLE_DEMO_PROMPT.md](ROLE_DEMO_PROMPT.md) for the interactive demo

### 6.1 Role Definitions

| Role | Description | Data Scope |
|------|-------------|------------|
| **Executive** | Owners, VP-level | All data, all locations, full financials |
| **Project Manager** | PMs, supervisors | Their assigned projects, team workload |
| **Estimator** | Quote creators | Opportunities, pricing, win/loss |
| **Field Technician** | Field techs | Their assignments, test checklists |
| **Office Admin** | Coordinators | All projects, scheduling, no financials |

### 6.2 Navigation by Role

**Sidebar uses collapsible menu groups. Items marked 🚧 are Phase 2.**

```
Menu Group           Item                 Exec   PM    Est   Tech  Admin
────────────────────────────────────────────────────────────────────────
📊 OPERATIONS
                     Dashboard             ✓     ✓      ✓     ✓     ✓
                     Projects              ✓     ✓      ✓     ✓     ✓
                     Clients               ✓     ✓      ✓     ✗     ✓
                     Apparatus             ✓     ✓      ✗     ✓     ✓

👥 RESOURCES
                     Employees             ✓     ✓      ✗     ✗     ✓
                     Equipment             ✓     ✓      ✗     ✓     ✓
                     Scheduling 🚧         ✓     ✓      ✗     ✗     ✓

📋 SERVICES
                     Power System Studies  ✓     ✓      ✓     ✗     ✓
                     Estimates             ✓     ✗      ✓     ✗     ✗
                     Reports               ✓     ✓      ✓     ✗     ✓

� REFERENCE MATERIALS
                     NETA Standards        ✓     ✓      ✓     ✓     ✓
                     SOPs                  ✓     ✓      ✗     ✓     ✓
                     Safety Documents      ✓     ✓      ✗     ✓     ✓
                     Equipment Manuals     ✓     ✓      ✓     ✓     ✓
                     Drawings              ✓     ✓      ✓     ✓     ✓

🛡️ SAFETY (Phase 2)
                     Safety Dashboard 🚧   ✓     ✓      ✗     ✓     ✓
                     JHA Forms 🚧          ✓     ✓      ✗     ✓     ✓
                     Incident Reports 🚧   ✓     ✓      ✗     ✓     ✓

💰 FINANCE
                     Financials            ✓     ✗      ✗     ✗     ✗
                     Invoicing 🚧          ✓     ✗      ✗     ✗     ✗

⚙️ ADMIN
                     Admin Settings        ✓     ✗      ✗     ✗     ✗
                     User Management       ✓     ✗      ✗     ✗     ✗
                     Integrations 🚧       ✓     ✗      ✗     ✗     ✗
```

### 6.3 Module Status Reference

| Module | Status | Database Ready | UI Ready |
|--------|--------|---------------|----------|
| Dashboard | ✅ Active | Yes | In Progress |
| Projects | ✅ Active | Yes | In Progress |
| Clients | ✅ Active | Yes | Basic |
| Apparatus | ✅ Active | Yes | Basic |
| Employees | ✅ Active | Yes | Placeholder |
| Equipment | ✅ Active | Yes | Placeholder |
| Scheduling | 🚧 Phase 2 | Partial | Planned |
| PSS Studies | ✅ Active | Yes | Placeholder |
| Estimates | ✅ Active | Partial | Placeholder |
| Reports | ✅ Active | Yes | Placeholder |
| **Reference Materials** | | | |
| → NETA Standards | ✅ Active | Yes (needs data import) | Placeholder |
| → SOPs | ✅ Active | Yes (table exists) | Placeholder |
| → Safety Docs | ✅ Active | Yes (table exists) | Placeholder |
| → Equipment Manuals | ✅ Active | Yes (datasheets table) | Placeholder |
| → Drawings | 🚧 Phase 2 | No | Planned |
| **Safety Management** | | | |
| → Safety Dashboard | 🚧 Phase 2 | Partial | Planned |
| → JHA Forms | 🚧 Phase 2 | No | Planned |
| → Incident Reports | 🚧 Phase 2 | No | Planned |
| Financials | ✅ Active | Yes | Placeholder |
| Invoicing | 🔜 Phase 3 | No | Not Started |
| Integrations | 🔜 Phase 3 | No | Not Started |

### 6.4 Dashboard Widgets by Role

**Executive Dashboard:**
- Revenue stats (quoted, recognized, margin)
- Revenue by location chart
- Revenue by service type chart
- Projects needing attention
- Employee performance (optional)

**Project Manager Dashboard:**
- My active projects count
- Tasks due this week
- Team workload visualization
- My projects table
- Calendar/schedule view

**Estimator Dashboard:**
- Open opportunities (count + value)
- Pending quotes
- Win rate percentage
- Pipeline funnel
- Opportunities table

**Field Tech Dashboard (Mobile):**
- Today's schedule
- This week preview
- Quick action buttons
- Recent equipment
- Sync status

**Office Admin Dashboard:**
- Projects this month
- Documents pending
- Schedule conflicts
- Data entry queue
- Technician schedule calendar

### 6.5 Sensitive Field Visibility

| Field | Exec | PM | Est | Tech | Admin |
|-------|------|-----|-----|------|-------|
| Gross margin % | ✓ | ? | ✗ | ✗ | ✗ |
| Labor costs | ✓ | ✗ | ✗ | ✗ | ✗ |
| Hourly rates | ✓ | ✗ | ? | ✗ | ✗ |
| Company revenue | ✓ | ✗ | ✗ | ✗ | ✗ |
| Project revenue | ✓ | ? | ✓ | ✗ | ✗ |
| Client contact | ✓ | ✓ | ✓ | ✗ | ✓ |

*? = Decision needed - ask stakeholder*

### 6.6 Implementation Pattern

```typescript
// Role context hook
const { user, role, permissions } = useAuth();

// Permission check helper
const can = (permission: string) => permissions.includes(permission);

// Conditional rendering
{can('view:financials') && <FinancialsTab />}
{can('edit:projects') && <EditButton />}

// Data filtering
const projects = can('view:all-projects') 
  ? allProjects 
  : allProjects.filter(p => p.pm_id === user.id);
```

---

## Appendix A: Icon Reference

Using **Lucide React** icons (included with shadcn/ui):

| Concept | Icon Name |
|---------|-----------|
| Dashboard | LayoutDashboard |
| Projects | FolderKanban |
| Clients | Building2 |
| Apparatus | Wrench |
| Tasks | CheckSquare |
| Reports | BarChart3 |
| Settings | Settings |
| User | User |
| Search | Search |
| Filter | Filter |
| Add | Plus |
| Edit | Pencil |
| Delete | Trash2 |
| More Actions | MoreVertical |
| Success | CheckCircle |
| Warning | AlertTriangle |
| Error | XCircle |
| Info | Info |
| Calendar | Calendar |
| Clock | Clock |
| Money | DollarSign |
| Location | MapPin |
| Document | FileText |
| Camera | Camera |
| Download | Download |

---

## Appendix B: Responsive Breakpoints

Following Tailwind CSS defaults:

| Breakpoint | Min Width | Use Case |
|------------|-----------|----------|
| sm | 640px | Large phones, small tablets |
| md | 768px | Tablets |
| lg | 1024px | Small laptops |
| xl | 1280px | Desktops |
| 2xl | 1536px | Large monitors |

**Mobile-first approach:**
- Default styles for mobile
- Add complexity at larger breakpoints
- Sidebar: hidden on mobile, visible lg+
- Tables: card view on mobile, table view md+
- Forms: single column sm, two column md+

---

## Appendix C: Database → UI Field Mapping

| Database Column | UI Display Label | Format |
|-----------------|------------------|--------|
| project_number | Project # | As-is (monospace) |
| client_name | Client | Link to client |
| project_status | Status | Badge component |
| start_date | Start Date | MMM D, YYYY |
| end_date | End Date | MMM D, YYYY |
| quoted_revenue | Quoted | $X,XXX.XX |
| recognized_revenue | Recognized | $X,XXX.XX |
| gross_margin_percent | Margin | XX.X% |
| equipment_type | Equipment Type | Title case |
| serial_number | Serial # | Monospace |
| created_at | Created | Relative (2 days ago) |
| updated_at | Updated | Relative |

---

*End of UI Specification Guide*
