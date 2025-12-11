# RESA Power - Report Generator Demo Prompt

> **Purpose:** Standalone v0.dev prompt for the automated report generation workflow  
> **Goal:** Demo the tech-friendly report creation process that eliminates manual bottlenecks  
> **Use Case:** Show how techs can generate professional branded PDFs directly from project data

---

## THE PROMPT (Copy Everything Below This Line)

```
Create an interactive report generation interface for RESA Power, an electrical testing company. This tool allows technicians to generate professional PDF reports from project data using templates.

## Tech Stack
- shadcn/ui components
- Tailwind CSS  
- Lucide React icons
- React useState for wizard navigation

## Layout

### Header Bar
- RESA Power logo (blue square with "R")
- Title: "Report Generator"
- User avatar dropdown in top right showing "Kole Ellertson"
- Breadcrumb: Dashboard > Reports > Create New

---

## MAIN VIEW: Reports Dashboard

### Stats Row (4 cards):
1. **Reports This Month**: 24
   - Subtext: "+8 from last month"
   - Green trend arrow

2. **Pending Review**: 3
   - Subtext: "Awaiting approval"
   - Amber color if > 0

3. **Avg Generation Time**: 2.1 min
   - Subtext: "From submit to PDF"

4. **Templates Available**: 4
   - Subtext: "ATS, MTS, IR, Combined"

### Action Bar:
- Large blue button: "Create New Report" with FileText icon
- Search input: "Search reports..."
- Filter dropdown: Report Type (All, ATS, MTS, IR)
- Filter dropdown: Status (All, Draft, Generated, Finalized)

### Reports Table:
Columns: Report #, Project, Client, Type, Created By, Status, Date, Actions

| Report # | Project | Client | Type | By | Status | Date | Actions |
|----------|---------|--------|------|-----|--------|------|---------|
| RPT-2024-0156 | Sundance TIAC | Stellar Energy | ATS | K. Ellertson | Finalized | 12/10 | ⋮ |
| RPT-2024-0155 | Main Campus Upgrade | State University | MTS | A. Smith | Pending | 12/10 | ⋮ |
| RPT-2024-0154 | Distribution Center | Amazon | ATS | K. Ellertson | Generated | 12/09 | ⋮ |
| RPT-2024-0153 | Hospital Wing C | Mercy Health | IR | M. Johnson | Finalized | 12/08 | ⋮ |
| RPT-2024-0152 | Data Center Phase 2 | Microsoft | Combined | K. Ellertson | Finalized | 12/07 | ⋮ |

Status Badges:
- Draft: gray-100 bg, gray-600 text
- Generated: blue-100 bg, blue-700 text
- Pending Review: amber-100 bg, amber-700 text
- Finalized: green-100 bg, green-700 text

Type Badges:
- ATS: blue-100 bg, blue-800 text (Acceptance Testing)
- MTS: green-100 bg, green-800 text (Maintenance Testing)
- IR: orange-100 bg, orange-800 text (Infrared/Thermal)
- Combined: purple-100 bg, purple-800 text

Row Actions Menu (three dots):
- View PDF
- Download
- Email to Client
- Duplicate
- Delete (if Draft)

---

## CREATE REPORT WIZARD (Modal/Slideout)

When "Create New Report" is clicked, show a multi-step wizard modal.

### Progress Indicator:
Horizontal stepper showing: 1. Select Project → 2. Report Details → 3. Review & Generate
- Current step: blue filled circle
- Completed: green checkmark
- Upcoming: gray outline circle

---

### STEP 1: Select Project

Header: "Step 1 of 3: Select Project"

Search Input:
- Placeholder: "Search by project name, client, or job number..."
- Magnifying glass icon

Recent Projects List (Cards):
Show 5 most recent projects as selectable cards:

Card 1 (Selected state - blue border):
```
┌─────────────────────────────────────────┐
│ ○ Sundance TIAC                         │
│   Stellar Energy                        │
│   Phoenix, AZ • Testing Complete        │
│   12 apparatus • Last updated 12/10     │
└─────────────────────────────────────────┘
```

Card 2:
```
┌─────────────────────────────────────────┐
│ ○ Main Campus Upgrade                   │
│   State University                      │
│   Denver, CO • In Progress              │
│   28 apparatus • Last updated 12/09     │
└─────────────────────────────────────────┘
```

Card 3:
```
┌─────────────────────────────────────────┐
│ ○ Data Center Expansion                 │
│   Microsoft                             │
│   Las Vegas, NV • Testing Complete      │
│   45 apparatus • Last updated 12/08     │
└─────────────────────────────────────────┘
```

Card 4:
```
┌─────────────────────────────────────────┐
│ ○ Hospital Wing C                       │
│   Mercy Health                          │
│   San Diego, CA • Testing Complete      │
│   8 apparatus • Last updated 12/07      │
└─────────────────────────────────────────┘
```

Card 5:
```
┌─────────────────────────────────────────┐
│ ○ Distribution Center                   │
│   Amazon                                │
│   Phoenix, AZ • In Progress             │
│   22 apparatus • Last updated 12/06     │
└─────────────────────────────────────────┘
```

Footer:
- "Cancel" link (left)
- "Next" button (right, blue, disabled until project selected)

---

### STEP 2: Report Details

Header: "Step 2 of 3: Report Details"

Show selected project info at top in a muted card:
```
┌─────────────────────────────────────────┐
│ 📁 Sundance TIAC • Stellar Energy      │
│    Phoenix, AZ                          │
└─────────────────────────────────────────┘
```

Form Fields:

**Report Type** (Required):
Dropdown with options:
- ATS - Acceptance Testing Specification
- MTS - Maintenance Testing Specification  
- IR - Infrared Thermography
- Combined - ATS + IR

**Report Date**:
Date picker, defaulted to today (December 11, 2025)

**Section Divider**: "── Client Information (Auto-filled) ──"

**Client Name**: 
- Read-only input showing "Stellar Energy"
- Small lock icon indicating auto-filled

**Site Name**:
- Read-only input showing "Sundance TIAC"

**Site Address**:
- Read-only input showing "4567 Industrial Blvd, Phoenix, AZ 85001"

**Section Divider**: "── Report Details ──"

**Attention To**:
- Text input, placeholder: "Recipient name"
- Suggested: "Terry Johnson" (pulled from client contacts)

**RE Line**:
- Text input, placeholder: "Subject line for report"
- Default value: "Acceptance Testing Report - Sundance TIAC"

**Project Description** (Optional):
- Textarea, 3 rows
- Placeholder: "Brief description of work performed..."

**Section Divider**: "── Equipment Selection ──"

**Select Equipment to Include**:
Checklist of apparatus from the project:

```
☑ ATS-1 - Main Switchgear - Eaton VCP-W
  Location: Building A, MCC Room | Status: ✓ Pass

☑ ATS-2 - Generator Transfer Switch - ASCO 7000
  Location: Building A, Generator Room | Status: ✓ Pass

☑ ATS-3 - Distribution Panel DP-1 - Square D
  Location: Building B, Electrical Room | Status: ✓ Pass

☐ ATS-4 - Emergency Lighting Panel - Cutler-Hammer
  Location: Building B, Mechanical Room | Status: ⏳ Pending

☑ ATS-5 - UPS System - Eaton 9395
  Location: Building A, Data Room | Status: ✓ Pass
```

Helper text: "Only equipment with 'Pass' status can be included in final reports"

**Select All / Deselect All** toggle link

**Section Divider**: "── Prepared By ──"

**Employee**:
Dropdown showing:
- Kole Ellertson (selected, current user)
- Austin Smith
- Mike Johnson
- Sarah Williams

Preview of signature below dropdown:
```
┌─────────────────────────────────────────┐
│ Signature Preview:                      │
│ [Cursive signature image placeholder]   │
│ Kole Ellertson                          │
│ Power Systems Technician                │
│ RESA Power - Phoenix Services           │
└─────────────────────────────────────────┘
```

Footer:
- "Back" button (left, outline style)
- "Next" button (right, blue)

---

### STEP 3: Review & Generate

Header: "Step 3 of 3: Review & Generate"

Two-column layout:

**Left Column (60%): Report Preview**

Mockup of the report cover page:
```
┌─────────────────────────────────────────┐
│                                         │
│         [RESA Power Logo]               │
│                                         │
│    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━       │
│                                         │
│      ACCEPTANCE TESTING REPORT          │
│                                         │
│    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━       │
│                                         │
│         Stellar Energy                  │
│         Sundance TIAC                   │
│         Phoenix, Arizona                │
│                                         │
│         December 11, 2025               │
│                                         │
│    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━       │
│                                         │
│         Prepared By:                    │
│         RESA Power                      │
│         Phoenix Services                │
│                                         │
└─────────────────────────────────────────┘
```

Page navigation: "Page 1 of 12" with prev/next arrows

**Right Column (40%): Summary & Options**

**Report Summary Card:**
- Report Type: ATS - Acceptance Testing
- Client: Stellar Energy
- Site: Sundance TIAC
- Date: December 11, 2025
- Equipment: 4 items
- Prepared By: Kole Ellertson

**Sections to Include:**
Checkboxes (all checked by default):
- ☑ Cover Page
- ☑ Summary Letter
- ☑ Scope of Work
- ☑ Results & Recommendations
- ☑ Equipment Summary Table
- ☑ Individual Test Data Sheets
- ☐ Thermal Images (grayed out - "No IR data available")
- ☐ Appendix A: NETA Standards Reference

**Output Format:**
Radio buttons:
- ● PDF (Recommended)
- ○ PDF + Word (.docx)

**Notes:**
Textarea for internal notes (not included in report)

Footer:
- "Back" button (left, outline)
- "Generate Report" button (right, blue, with FileText icon)

Loading state when clicked:
- Button shows spinner: "Generating..."
- Progress text below: "Creating PDF... This takes about 2 minutes"

---

### STEP 4: Success State

Replace wizard content with success message:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│              ✓                                          │
│         (large green checkmark in circle)               │
│                                                         │
│         Report Generated Successfully!                  │
│                                                         │
│    ─────────────────────────────────────────────────   │
│                                                         │
│    Report Number: RPT-2024-0157                         │
│    File: Stellar_Energy_Sundance_TIAC_ATS.pdf          │
│    Size: 2.4 MB (12 pages)                             │
│    Generated: December 11, 2025 at 2:34 PM             │
│                                                         │
│    ─────────────────────────────────────────────────   │
│                                                         │
│    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│    │ 👁 Preview  │  │ ⬇ Download │  │ ✉ Email    │   │
│    └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                         │
│    ─────────────────────────────────────────────────   │
│                                                         │
│    Status: Generated                                    │
│    Next Step: Submit for manager review                │
│                                                         │
│    [Submit for Review]     [Create Another Report]     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

Preview button opens PDF in new tab
Download button triggers file download
Email button opens email composition modal

---

## EMAIL MODAL (When "Email" clicked)

```
┌─────────────────────────────────────────────────────────┐
│ Email Report                                     [X]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  To: [terry.johnson@stellarenergy.com        ]         │
│       (auto-populated from client contact)              │
│                                                         │
│  CC: [                                        ]         │
│                                                         │
│  Subject:                                               │
│  [RESA Power - Acceptance Testing Report - Sundance   ]│
│                                                         │
│  Message:                                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Dear Terry,                                     │   │
│  │                                                 │   │
│  │ Please find attached the Acceptance Testing    │   │
│  │ Report for the Sundance TIAC project.         │   │
│  │                                                 │   │
│  │ If you have any questions, please don't        │   │
│  │ hesitate to contact us.                        │   │
│  │                                                 │   │
│  │ Best regards,                                   │   │
│  │ Kole Ellertson                                  │   │
│  │ RESA Power                                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Attachment:                                            │
│  📎 Stellar_Energy_Sundance_TIAC_ATS.pdf (2.4 MB)      │
│                                                         │
│                           [Cancel]  [Send Email]       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## DECISION CALLOUTS

Add a collapsible section at the bottom of the main dashboard:

```
┌─────────────────────────────────────────────────────────┐
│ 📋 Questions for Stakeholder Review            [▼]     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ PERMISSIONS                                             │
│ • Who can generate reports? (Any tech, or project-    │
│   assigned only)                                        │
│ • Manager approval required before finalizing?         │
│ • Can techs email reports directly to clients?         │
│                                                         │
│ TEMPLATES                                               │
│ • Templates customizable per client?                   │
│ • Who can edit/create templates? (Admin only?)         │
│ • Different cover pages per location?                  │
│                                                         │
│ WORKFLOW                                                │
│ • Version history needed for revisions?                │
│ • Batch generation for multi-site projects?            │
│ • Integration with document management system?         │
│                                                         │
│ DELIVERY                                                │
│ • Auto-email option when finalized?                    │
│ • Client portal for self-service download?             │
│ • Physical print/mail workflow needed?                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## STYLING

Colors:
- Primary Blue: #1e40af
- Success Green: #22c55e
- Warning Amber: #f59e0b
- Background: #f8fafc
- Cards: white with shadow-sm

Typography:
- Headers: font-semibold
- Body: Inter or system font
- Monospace for report numbers

Cards:
- rounded-lg
- White background
- shadow-sm
- p-6 padding

Make the wizard feel professional and efficient - this tool eliminates a major bottleneck in the current workflow where Jason manually creates every report.
```

---

## How to Use This Demo

### Generate in v0.dev
1. Go to [v0.dev](https://v0.dev)
2. Paste the entire prompt above
3. Wait for generation
4. Click through the wizard steps

### Key Things to Demo
1. **Project selection** - Easy search, recent projects shown
2. **Auto-population** - Client/site info pulled automatically
3. **Equipment selection** - Checkbox list from project data
4. **Signature integration** - Employee signature shown
5. **PDF preview** - See what you're generating
6. **One-click email** - Send directly to client

### Follow-up Prompts for Iteration
- "Add a template selection step before report details"
- "Show a revision history panel on the dashboard"
- "Add batch report generation for multiple projects"
- "Create a manager approval workflow view"

---

## Integration with Main Demo

This Report Generator is also included in the main role-based demo prompt (`ROLE_DEMO_PROMPT.md`). Use this standalone version for:
- Focused discussion on report workflow specifically
- Deeper iteration on the generation process
- Showing to stakeholders who only care about this feature

---

*Version: 1.0 | December 2025*
