# RESA Power Tracker - Desktop/Laptop Platform Strategy

## 🎯 Revised Architecture

### Primary Platform: **Laptop/Desktop**
- Field technicians use **laptops at job sites**
- Project managers use **desktop workstations**
- Mobile access as **secondary/optional**

### Recommended App Strategy

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  PRIMARY: Model-Driven App (Desktop-Optimized)         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • Full project management                             │
│  • Complete task tracking                              │
│  • Data entry forms                                    │
│  • Rich reporting & dashboards                         │
│  • All features accessible                             │
│                                                        │
│  SECONDARY: Canvas App (Tablet Layout)                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • Optional: Quick task updates                        │
│  • Optional: Time entry on mobile                      │
│  • Use ONLY if specific workflows need it              │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Why This Changes Everything

### ✅ Focus on Model-Driven App First

**Advantages for Laptop Use:**
- **Built-in data grids** - See 20+ tasks at once
- **Professional UI** - Looks like enterprise software
- **Keyboard shortcuts** - Tab, Enter, Ctrl+S work
- **Multi-tasking** - Multiple browser tabs open
- **Copy/paste friendly** - Between apps
- **Advanced filtering** - Complex queries built-in
- **Excel export** - Right-click → Export
- **Faster to build** - Less custom code needed
- **Better for data entry** - Full keyboard support
- **Responsive by default** - Works on any screen size

### Canvas App Becomes Optional

**Only build Canvas app if you need:**
- Custom workflows not possible in Model-Driven
- Specific mobile-only features (camera, GPS)
- Very specific UI requirements
- Touch-optimized interfaces (if using tablets)

**For laptop use, Model-Driven app is superior!**

---

## Revised Implementation Plan

### Phase 1: Model-Driven App (Primary) - 3-4 weeks

Build the full-featured desktop application:

#### Week 1: Data Foundation
```
✓ Create Dataverse tables
✓ Set up relationships
✓ Configure security roles
✓ Import existing data
```

#### Week 2: Model-Driven App Build
```
✓ Create app structure
✓ Design forms (Project, Task, Time Entry)
✓ Create views (Active Tasks, My Tasks, etc.)
✓ Add business process flows
✓ Configure dashboards
```

#### Week 3: Advanced Features
```
✓ Set up Power Automate workflows
✓ Configure command buttons
✓ Add business rules
✓ Create quick view forms
✓ Set up field-level security
```

#### Week 4: Testing & Polish
```
✓ User acceptance testing
✓ Performance optimization
✓ Training materials
✓ Go-live preparation
```

### Phase 2: Canvas App (Optional) - 1-2 weeks

**Only if specific needs identified, such as:**
- Mobile-only workflows (site photos, GPS check-in)
- Simplified data entry for specific tasks
- Touch-optimized interface for tablet use

---

## Model-Driven App Build Guide

### Step 1: Create the App (15 minutes)

1. Go to **https://make.powerapps.com**
2. Select your environment
3. Click **+ Create** → **Model-driven app**
4. Click **Modern app designer**
5. Settings:
   - **Name**: RESA Power Tracker
   - **Description**: Project and task management system
   - Click **Create**

### Step 2: Add Tables (5 minutes)

1. Click **+ Add page** → **Dataverse table**
2. Select tables:
   - ✅ Projects
   - ✅ Scopes
   - ✅ Tasks
   - ✅ Time Entries
   - ✅ Billing Lines
   - ✅ Apparatus
3. Click **Add**

### Step 3: Configure Navigation (10 minutes)

The site map structure:

```
Navigation:
├─ 📁 Projects
│  ├─ Active Projects
│  ├─ All Projects
│  ├─ My Projects
│  └─ Project Calendar
│
├─ ✓ Tasks
│  ├─ My Tasks
│  ├─ All Tasks
│  ├─ Overdue Tasks
│  ├─ By Status
│  └─ By Priority
│
├─ ⏱ Time & Billing
│  ├─ My Time Entries
│  ├─ All Time Entries
│  ├─ Pending Approvals
│  ├─ Billing Lines
│  └─ Weekly Summary
│
├─ 🔧 Resources
│  ├─ Apparatus Catalog
│  ├─ Team Members
│  └─ Equipment Schedule
│
└─ ⚙️ Administration
   ├─ Reference Data
   ├─ Labor Rates
   ├─ Security Roles
   └─ System Settings
```

**To configure:**
1. Click **Navigation** in left panel
2. Click **+ New group**
3. Add group name: "Projects"
4. Click **+ New subarea**
5. Select table: Projects
6. Choose view: Active Projects
7. Repeat for all sections

### Step 4: Design Project Form (30 minutes)

1. Go to **Tables** → **Projects** → **Forms**
2. Click **Main form** or create new
3. Form layout:

#### Tab 1: General Information
```
┌─────────────────────────────────────────────────┐
│  General Information                            │
├─────────────────────────────────────────────────┤
│                                                 │
│  Client: [_______________]  Job #: [_______]    │
│  Project: [_____________________________]       │
│  Status: [Active ▼]        Priority: [High ▼]  │
│  Start Date: [mm/dd/yyyy]  End Date: [mm/dd]   │
│  Project Lead: [Select user ▼]                 │
│                                                 │
├─ Site Information ─────────────────────────────┤
│                                                 │
│  Address: [_____________________________]       │
│  City: [___________] State: [__] Zip: [____]   │
│  Contact: [_______________] Phone: [________]   │
│  Email: [_____________________________]         │
│                                                 │
└─────────────────────────────────────────────────┘
```

#### Tab 2: Scopes (Subgrid)
```
┌─────────────────────────────────────────────────┐
│  Scopes                              [+ New]    │
├─────────────────────────────────────────────────┤
│ Scope Name  │ NETA Std │ Budget │ Actual │ %  │
├─────────────┼──────────┼────────┼────────┼────┤
│ Scope_1     │ ATS      │ 120.0  │ 85.5   │ 71%│
│ Scope_2     │ MTS      │ 40.0   │ 12.0   │ 30%│
│ Scope_3     │ ATS      │ 200.0  │ 0.0    │ 0% │
└─────────────────────────────────────────────────┘
```

#### Tab 3: Tasks (Subgrid)
```
┌─────────────────────────────────────────────────┐
│  Tasks                               [+ New]    │
├─────────────────────────────────────────────────┤
│ Task Name        │Status│ Due Date │ Hours │ % │
├──────────────────┼──────┼──────────┼───────┼───┤
│ Install Breaker  │ IP   │11/15/2025│ 12.5  │65%│
│ Visual Inspect   │ NS   │11/20/2025│ 3.0   │ 0%│
│ Test Protection  │ IP   │11/18/2025│ 8.0   │40%│
└─────────────────────────────────────────────────┘
```

#### Tab 4: Timeline & Notes
```
Built-in timeline shows:
- Task status changes
- Notes added
- Files attached
- Emails sent
- Approvals
```

#### Tab 5: Related
```
- Time Entries (rollup)
- Billing Lines (rollup)
- Documents (SharePoint)
- Team Members
```

**To configure tabs:**
1. In form designer, click **+ Component** → **1-column tab**
2. Rename tab: "General Information"
3. Drag fields from right panel onto form
4. Click **+ Component** → **Subgrid** for Scopes and Tasks
5. Configure subgrid:
   - Table: Scopes
   - View: Active Scopes
   - Relationship: Project to Scopes

### Step 5: Design Task Form (30 minutes)

```
┌───────────────────────────────────────────────────┐
│  Task Details                                     │
├───────────────────────────────────────────────────┤
│                                                   │
│  Task Name: [_____________________________]       │
│  Project: [Alpha Upgrade Project          ▼]     │
│  Scope: [Scope 1                          ▼]     │
│  Apparatus: [1200A Breaker                ▼]     │
│  Designation: [BKR-001]  Drawing: [DWG-123]      │
│                                                   │
├─ Status & Progress ──────────────────────────────┤
│                                                   │
│  Status: [In Progress    ▼]  Priority: [High ▼] │
│  Availability: [Ready    ▼]                       │
│  Assigned To: [John Smith ▼]                     │
│                                                   │
│  % Complete: [━━━━●━━━━━━━] 65%                 │
│                                                   │
│  Due Date: [11/15/2025]                          │
│  Date Completed: [__________]                    │
│                                                   │
├─ Hours ──────────────────────────────────────────┤
│                                                   │
│  Quoted Hours:    15.0                           │
│  Actual Hours:    9.5                            │
│  Remaining Hours: 5.5                            │
│                                                   │
├─ Assessment ─────────────────────────────────────┤
│                                                   │
│  Assessment: [Acceptable ▼]                      │
│  Task Delays: [_____________________________]    │
│  Notes: [____________________________________]   │
│         [____________________________________]   │
│                                                   │
└───────────────────────────────────────────────────┘

[Tabs Below]
Time Entries | Billing | Datasheet | Related | Timeline
```

**Add Command Bar Buttons:**
1. **Log Time** - Quick time entry
2. **Mark Complete** - Update status to completed
3. **Upload Datasheet** - Attach file
4. **Email PM** - Send notification

### Step 6: Create Essential Views (45 minutes)

#### My Open Tasks View
```
Columns: Task Name | Project | Status | Priority | Due Date | % Complete | Hours Remaining
Filter: Assigned To = Current User AND Status ≠ Completed
Sort: Due Date (ascending)
```

#### Overdue Tasks View
```
Columns: Task Name | Project | Assigned To | Due Date | Days Overdue | Status
Filter: Due Date < Today AND Status ≠ Completed
Sort: Due Date (ascending)
Color: Red text for overdue items
```

#### Active Projects View
```
Columns: Project Name | Client | Job # | Status | Start Date | Project Lead | Total Hours
Filter: Status = Active
Sort: Start Date (descending)
```

#### Weekly Time Entries View
```
Columns: Date | Task | Project | Hours | Labor Type | Submitted | Approved
Filter: Week Ending = This Week
Group By: Date
```

**To create views:**
1. Go to **Tables** → **Tasks** → **Views**
2. Click **+ New view**
3. Name: "My Open Tasks"
4. Select columns from right panel
5. Click **Edit filters**
6. Add filter: `Assigned To` equals `Current User`
7. Add filter: `Status` does not equal `Completed`
8. Click **Sort by** → Select `Due Date` → Ascending
9. **Save** and **Publish**

### Step 7: Add Business Process Flow (20 minutes)

**Task Completion Process:**
```
[Assigned] → [In Progress] → [Review] → [Completed]
    ↓            ↓              ↓           ↓
  Assign      Log Time      Get Approval  Close
  Due Date    Update %      Upload Docs   Final Notes
```

**To create:**
1. In solution, click **+ New** → **Automation** → **Process** → **Business Process Flow**
2. Name: Task Completion Process
3. Entity: Task
4. Add stages:
   - Stage 1: Assigned
     - Data Step: Due Date (required)
     - Data Step: Assigned To (required)
   - Stage 2: In Progress
     - Data Step: % Complete
     - Data Step: Log Hours
   - Stage 3: Review
     - Data Step: Upload Datasheet
     - Data Step: Assessment
   - Stage 4: Completed
     - Data Step: Date Completed
     - Data Step: Final Notes

### Step 8: Create Dashboards (30 minutes)

#### Project Overview Dashboard

**Layout:**
```
┌────────────────────┬────────────────────┬────────────────────┐
│   Active Projects  │   Tasks This Week  │   Hours This Month │
│        24          │        156         │       1,247        │
└────────────────────┴────────────────────┴────────────────────┘

┌─────────────────────────────────┬──────────────────────────────┐
│  Projects by Status             │  Tasks by Priority           │
│  ▰▰▰▰▰▰▰ Active (18)           │  ▰▰▰ High (45)              │
│  ▰▰▰ On Hold (4)               │  ▰▰▰▰ Medium (67)           │
│  ▰ Completed (2)               │  ▰▰ Low (44)                │
└─────────────────────────────────┴──────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│  My Upcoming Tasks                                            │
│  • Install Breaker Switch - Due: 11/15/2025 (3 days)         │
│  • Visual Inspection - Due: 11/18/2025 (6 days)              │
│  • Test Protection Relay - Due: 11/20/2025 (8 days)          │
└───────────────────────────────────────────────────────────────┘

┌─────────────────────────────────┬──────────────────────────────┐
│  Hours: Quoted vs Actual        │  Project Timeline            │
│  [Bar chart showing variance]   │  [Gantt-style timeline]      │
└─────────────────────────────────┴──────────────────────────────┘
```

**To create:**
1. In app designer, click **+ Add page** → **Dashboard**
2. Click **Create new dashboard**
3. Name: Project Overview
4. Click **+ Add component**
5. Add charts:
   - **Card**: CountRows of Active Projects
   - **Pie chart**: Tasks grouped by Status
   - **Bar chart**: Projects by Client
   - **Line chart**: Hours logged over time
   - **List**: My upcoming tasks (view)

### Step 9: Add Business Rules (15 minutes)

**Example: Auto-calculate Remaining Hours**

1. Go to **Tables** → **Tasks** → **Business rules**
2. Click **+ New business rule**
3. Name: Calculate Remaining Hours
4. Add condition: `Quoted Hours` or `Actual Hours` changes
5. Add action: Set `Remaining Hours` = `Quoted Hours` - `Actual Hours`
6. Add action: If `Remaining Hours` < 0, set `Status` = "Over Budget"

**Example: Require Assessment on Completion**

1. Condition: `Status` changes to "Completed"
2. Action: Set `Assessment` to Business Required
3. Action: Set `Date Completed` to Business Recommended

**Example: Auto-notify PM when Overdue**

1. Condition: `Due Date` < Today AND `Status` ≠ "Completed"
2. Action: Show error message "Task is overdue"
3. Trigger: Power Automate flow (notification)

---

## Desktop UX Optimizations

### Keyboard Shortcuts (Built-in)

```
Tab             Navigate fields
Shift+Tab       Navigate backwards
Enter           Submit form
Ctrl+S          Save record
Ctrl+N          New record
Ctrl+D          Delete record
Escape          Close dialog
Alt+N           Next record
Alt+P           Previous record
F11             Refresh
```

### Right-Click Menus (Built-in)

- Export to Excel
- Email a link
- Run report
- Assign to me
- Copy link
- Open in new window

### Multi-Column Layouts

For desktop, use **2-3 column forms**:

```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│  Column 1           │  Column 2           │  Column 3           │
│  • Client           │  • Status           │  • Budget Info      │
│  • Project Name     │  • Priority         │  • Hours Summary    │
│  • Job Number       │  • Dates            │  • Cost Summary     │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

**To configure:**
1. In form designer, insert **3-column section**
2. Drag fields into appropriate columns
3. Use **Quick view forms** for related data

### Data Density

Show **more information on screen**:
- Increase rows per page: 50-100
- Use subgrids liberally
- Multi-level filters
- Column sorting
- Quick edit in grid

### Browser Tabs Workflow

Users can open multiple tabs:
- Tab 1: Project list
- Tab 2: Specific project form
- Tab 3: Task details
- Tab 4: Time entry
- Tab 5: Dashboard

---

## Integration with Field Laptops

### Offline Capability

1. **Enable Offline Profile**
   - Settings → Mobile offline
   - Select tables to sync
   - Configure sync filters
   - Set sync frequency

2. **Users Open in Edge/Chrome**
   - App caches data
   - Works without internet
   - Syncs when reconnected

### SharePoint Integration

Store documents on field laptop:
```
Project Folder Structure:
├─ Job_12345_Alpha_Project/
│  ├─ Datasheets/
│  │  ├─ BKR-001_datasheet.pdf
│  │  └─ MOT-005_datasheet.pdf
│  ├─ Drawings/
│  ├─ Reports/
│  └─ Photos/
```

**Link to Model-Driven App:**
1. Add **Document Library** subgrid to Project form
2. Automatically sync to SharePoint
3. Access from any device

### Print Forms

Users can print forms directly:
- Right-click record → Print
- Creates PDF
- Formatted professionally

---

## Recommended Timeline (Laptop-Focused)

### Week 1: Model-Driven App Core
- Create all tables in Dataverse
- Import existing data
- Build basic forms
- Create essential views
- Set up security

### Week 2: Model-Driven App Advanced
- Add business process flows
- Create dashboards
- Configure business rules
- Add command buttons
- Polish UI

### Week 3: Integration & Automation
- Connect SharePoint for documents
- Set up Power Automate notifications
- Configure offline sync
- Test on field laptops
- Create Power BI reports

### Week 4: Testing & Rollout
- UAT with field technicians
- UAT with project managers
- Training sessions
- Documentation
- Go-live support

**Total Time: 4 weeks for full platform**

---

## Why This Approach is Better

### Model-Driven App Advantages

| Feature | Model-Driven | Canvas |
|---------|--------------|--------|
| **Data Grids** | ✅ Built-in, rich | ❌ Manual build |
| **Keyboard Nav** | ✅ Full support | ⚠️ Limited |
| **Multi-tab** | ✅ Native | ❌ N/A |
| **Copy/Paste** | ✅ Easy | ⚠️ Complex |
| **Export Excel** | ✅ Right-click | ❌ Manual |
| **Print** | ✅ Built-in | ⚠️ Custom |
| **Complex Forms** | ✅ Easy | ⚠️ Time-consuming |
| **Bulk Edit** | ✅ Built-in | ❌ N/A |
| **Advanced Filter** | ✅ Built-in | ⚠️ Custom |
| **Build Time** | ✅ Faster | ⚠️ Slower |
| **Maintenance** | ✅ Easier | ⚠️ More work |

### For Your Scenario:

**✅ Perfect for:**
- Technicians with laptops
- Data entry heavy work
- Multiple related tables
- Professional appearance
- Enterprise workflows

**❌ Canvas App Only If:**
- Need very specific UI
- Mobile-first requirements
- Touch-optimized needed
- Custom workflows

---

## Quick Start Command

Since Model-Driven is your primary app:

### Today: Create Model-Driven App (1 hour)

1. **Create app** (5 min)
   - make.powerapps.com → Model-driven app → Modern designer

2. **Add tables** (5 min)
   - Add Projects, Tasks, Time Entries

3. **Configure navigation** (10 min)
   - Set up menu groups

4. **Customize main form** (20 min)
   - Edit Project and Task forms

5. **Create views** (15 min)
   - My Tasks, Active Projects

6. **Publish** (5 min)
   - Save and publish

**You'll have a working app in 1 hour!**

---

## Canvas App - If Still Needed

### When to Add Canvas App:

**Scenario 1: Mobile Supplement**
- PM needs to check status from phone
- Quick approve time entries
- View dashboard on tablet

**Scenario 2: Simplified Data Entry**
- One specific workflow
- Touch-optimized for tablet
- Kiosk mode

**Scenario 3: Custom Features**
- Barcode scanning for equipment
- GPS check-in at site
- Photo markup
- Signature capture

### Recommended Canvas Approach

If you do build Canvas app:
- **Format**: Tablet (1366x768), not Phone
- **Purpose**: Supplement Model-Driven, not replace
- **Embed**: Can embed Canvas app IN Model-Driven app
- **Focus**: 2-3 specific workflows only

---

## Updated Success Metrics

### End of Week 1:
- ✅ Model-Driven app created
- ✅ Can view Projects and Tasks
- ✅ Can create new records
- ✅ 3-5 views working
- ✅ Tested on laptop

### End of Week 2:
- ✅ All forms customized
- ✅ Business rules active
- ✅ Dashboards showing
- ✅ 5 users testing

### End of Week 3:
- ✅ Power Automate notifications
- ✅ SharePoint connected
- ✅ Offline mode tested
- ✅ Power BI reports

### End of Week 4:
- ✅ Full team trained
- ✅ Production deployment
- ✅ Support process
- ✅ Success metrics tracked

---

## Bottom Line

**For laptop-based field work:**

🎯 **Build Model-Driven App FIRST** (and possibly ONLY)
- Faster to build
- More powerful for data entry
- Better for desktop use
- Professional appearance
- Less maintenance

🤔 **Consider Canvas App later** IF:
- Specific mobile needs identified
- Model-Driven can't handle workflow
- Custom UI absolutely required

**You'll save weeks of development time and get a better result!**

---

*Strategy Version: 2.0 - Desktop Optimized*
*Updated: November 7, 2025*
*For: RESA Power Laptop Platform*
