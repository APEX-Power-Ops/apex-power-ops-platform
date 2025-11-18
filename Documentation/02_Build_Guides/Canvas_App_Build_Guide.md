# RESA Power Field Tracker - Canvas App Build Guide

## Quick Start Overview

**What We're Building:**
A mobile-first Canvas app for field technicians to:
- View their assigned tasks
- Update task status
- Enter time/hours
- Add notes and photos
- Work offline when needed

**Build Time:** 2-3 hours for MVP
**Target Users:** Field technicians, project leads

---

## Phase 1: App Setup (15 minutes)

### Step 1: Create New Canvas App

1. Go to **https://make.powerapps.com**
2. Select your environment (top right)
3. Click **+ Create** → **Blank app** → **Blank canvas app**
4. Settings:
   - **Name**: RESA Power Field Tracker
   - **Format**: Phone (for mobile-first design)
   - **Orientation**: Portrait
   - Click **Create**

### Step 2: App Settings Configuration

1. Click **Settings** (gear icon) → **General**
   - ✅ Enable formula bar
   - ✅ Enable inline actions
   
2. **Settings** → **Display**
   - Orientation: Portrait
   - Scale to fit: On
   - Lock aspect ratio: On
   - Lock orientation: On

3. **Settings** → **Upcoming features**
   - ✅ Enable all experimental features (for better performance)

4. **Settings** → **Screen size + orientation**
   - Width: 375 (iPhone default)
   - Height: 667

---

## Phase 2: Data Connection (20 minutes)

### Option A: Connect to Excel (Quick Start)

**For immediate testing before Dataverse migration:**

1. Upload your Excel file to **OneDrive for Business** or **SharePoint**
2. In Power Apps Studio:
   - Click **Data** (database icon on left)
   - Click **+ Add data**
   - Search "Excel Online"
   - Select your file
   - Choose tables: **All_Tasks**, **All_Lists**, **Apparatus_List_w_Hours**

### Option B: Connect to Dataverse (Recommended)

**If you've already created Dataverse tables:**

1. Click **Data** → **+ Add data**
2. Search "Dataverse" or "Microsoft Dataverse"
3. Select your tables:
   - Tasks
   - Projects
   - Time Entries
   - Reference Lists (Status, Priority, etc.)

### Create Collections for Reference Data

Add this to **App.OnStart** (helps with performance and offline):

```javascript
// Load reference data into collections
ClearCollect(
    colStatus,
    Choices(Tasks.Status)  // If Dataverse
    // OR ['All_Lists'] if Excel - filter by STATUS KEY column
);

ClearCollect(
    colPriority,
    Choices(Tasks.Priority)
);

ClearCollect(
    colAvailability,
    Choices(Tasks.Availability)
);

// Set current user
Set(varCurrentUser, User());

// Initialize variables
Set(varSelectedTask, Blank());
Set(varShowTimeEntry, false);
Set(varFilterStatus, "All");
```

**To test**: Click the "..." menu next to App → **Run OnStart**

---

## Phase 3: Build Home Screen (30 minutes)

### Screen 1: HomeScreen

1. **Insert** → **New screen** → **Blank**
2. Rename to **"HomeScreen"**

### Add App Header

1. **Insert** → **Rectangle**
   - Name: **recHeader**
   - Properties:
     ```
     X: 0
     Y: 0
     Width: Parent.Width
     Height: 100
     Fill: RGBA(116, 39, 116, 1)  // RESA Power purple
     ```

2. **Insert** → **Label** (inside header)
   - Name: **lblAppTitle**
   - Properties:
     ```
     Text: "RESA Power"
     X: 20
     Y: 40
     Width: 200
     Font: Open Sans
     FontWeight: Bold
     Size: 24
     Color: White
     ```

3. **Insert** → **Label** (subtitle)
   - Name: **lblAppSubtitle**
   - Properties:
     ```
     Text: "Field Tracker"
     X: 20
     Y: 65
     Width: 200
     Size: 14
     Color: RGBA(255, 255, 255, 0.8)
     ```

4. **Insert** → **Icon** (User profile)
   - Icon: Person
   - Properties:
     ```
     X: Parent.Width - 60
     Y: 40
     Width: 40
     Height: 40
     Color: White
     OnSelect: Navigate(ProfileScreen, ScreenTransition.Cover)
     ```

### Add Quick Stats Cards

1. **Insert** → **Rectangle** (Container for stats)
   - Name: **recStatsContainer**
   - Properties:
     ```
     X: 10
     Y: recHeader.Y + recHeader.Height + 10
     Width: Parent.Width - 20
     Height: 120
     Fill: RGBA(245, 245, 245, 1)
     BorderRadius: 8
     ```

2. **Insert** → **Label** (My Tasks Count)
   - Name: **lblMyTasksCount**
   - Properties:
     ```
     Text: CountRows(
         Filter(
             Tasks,
             'Assigned To' = varCurrentUser.Email && 
             Status.Value <> "Completed"
         )
     )
     X: recStatsContainer.X + 20
     Y: recStatsContainer.Y + 20
     Size: 36
     FontWeight: Bold
     Color: RGBA(116, 39, 116, 1)
     ```

3. **Insert** → **Label** (Tasks label)
   ```
   Text: "My Open Tasks"
   X: lblMyTasksCount.X
   Y: lblMyTasksCount.Y + lblMyTasksCount.Height + 5
   Size: 14
   Color: RGBA(0, 0, 0, 0.6)
   ```

4. **Duplicate** the above for "Due Today" count:
   ```
   Text: CountRows(
       Filter(
           Tasks,
           'Assigned To' = varCurrentUser.Email && 
           DateValue(Text('Due Date')) = Today()
       )
   )
   X: Parent.Width / 2 + 10
   ```

### Add Quick Action Buttons

1. **Insert** → **Button**
   - Name: **btnViewTasks**
   - Properties:
     ```
     Text: "📋 View My Tasks"
     X: 10
     Y: recStatsContainer.Y + recStatsContainer.Height + 20
     Width: Parent.Width - 20
     Height: 60
     Fill: RGBA(0, 120, 212, 1)
     Color: White
     FontSize: 16
     BorderRadius: 8
     OnSelect: Navigate(TaskListScreen, ScreenTransition.Fade)
     ```

2. **Insert** → **Button** (Log Time)
   ```
   Text: "⏱️ Log Time"
   Y: btnViewTasks.Y + btnViewTasks.Height + 15
   Fill: RGBA(0, 176, 80, 1)
   OnSelect: Set(varShowTimeEntry, true); 
             Navigate(TimeEntryScreen, ScreenTransition.Cover)
   ```

3. **Insert** → **Button** (Search Projects)
   ```
   Text: "🔍 Search Projects"
   Y: [previous].Y + [previous].Height + 15
   Fill: RGBA(255, 192, 0, 1)
   Color: RGBA(0, 0, 0, 0.8)
   OnSelect: Navigate(ProjectSearchScreen, ScreenTransition.Fade)
   ```

### Add Recent Activity Section

1. **Insert** → **Label** (Section header)
   ```
   Text: "Recent Activity"
   X: 20
   Y: [last button].Y + [last button].Height + 30
   Size: 18
   FontWeight: Semibold
   ```

2. **Insert** → **Gallery** → **Blank vertical**
   - Name: **galRecentTasks**
   - Properties:
     ```
     Items: 
         SortByColumns(
             Filter(
                 Tasks,
                 'Assigned To' = varCurrentUser.Email
             ),
             "Modified On",
             Descending
         )
     X: 10
     Y: [section header].Y + [section header].Height + 10
     Width: Parent.Width - 20
     Height: Parent.Height - Y - 80
     TemplateSize: 80
     ```

3. **Inside gallery**, add:
   
   **Rectangle (background):**
   ```
   Width: Parent.TemplateWidth - 10
   Height: Parent.TemplateHeight - 10
   Fill: White
   BorderRadius: 8
   ```
   
   **Label (Task name):**
   ```
   Text: ThisItem.'Task Name'
   X: 15
   Y: 10
   Width: Parent.TemplateWidth - 100
   Size: 14
   FontWeight: Semibold
   ```
   
   **Label (Project):**
   ```
   Text: ThisItem.Project.Name  // Lookup field
   Y: [task name].Y + [task name].Height + 5
   Size: 12
   Color: Gray
   ```
   
   **Icon (Status indicator):**
   ```
   Icon: Icon.Circle
   X: Parent.TemplateWidth - 40
   Y: (Parent.TemplateHeight - Height) / 2
   Color: 
       Switch(
           ThisItem.Status.Value,
           "Completed", RGBA(0, 176, 80, 1),
           "In Progress", RGBA(255, 192, 0, 1),
           "Overdue", RGBA(192, 0, 0, 1),
           RGBA(200, 200, 200, 1)
       )
   ```
   
   **OnSelect (entire gallery):**
   ```
   Set(varSelectedTask, ThisItem);
   Navigate(TaskDetailScreen, ScreenTransition.Cover)
   ```

---

## Phase 4: Task List Screen (30 minutes)

### Screen 2: TaskListScreen

1. **Insert** → **New screen** → **Blank**
2. Rename to **"TaskListScreen"**

### Add Header with Back Button

1. Copy **recHeader** from HomeScreen (Ctrl+C, Ctrl+V)

2. **Insert** → **Icon** (Back arrow)
   - Icon: **Back**
   - Properties:
     ```
     X: 10
     Y: 45
     Width: 30
     Height: 30
     Color: White
     OnSelect: Back()
     ```

3. Update **lblAppTitle**:
   ```
   Text: "My Tasks"
   X: 50
   ```

### Add Filter Buttons

1. **Insert** → **Rectangle** (Filter container)
   ```
   Name: recFilterBar
   X: 0
   Y: recHeader.Height
   Width: Parent.Width
   Height: 50
   Fill: White
   ```

2. **Insert** → **Button** (All filter)
   - Name: **btnFilterAll**
   ```
   Text: "All"
   X: 10
   Y: recFilterBar.Y + 10
   Width: (Parent.Width - 50) / 4
   Height: 30
   Fill: If(varFilterStatus = "All", 
            RGBA(116, 39, 116, 1), 
            RGBA(240, 240, 240, 1))
   Color: If(varFilterStatus = "All", White, Black)
   BorderRadius: 15
   OnSelect: Set(varFilterStatus, "All")
   ```

3. **Duplicate** for other filters (Not Started, In Progress, Completed):
   ```
   // Position them horizontally
   X: btnFilterAll.X + btnFilterAll.Width + 10
   OnSelect: Set(varFilterStatus, "In Progress")  // Change per button
   ```

### Add Task List Gallery

1. **Insert** → **Gallery** → **Blank vertical**
   - Name: **galTasks**
   ```
   Items: 
       SortByColumns(
           Filter(
               Tasks,
               'Assigned To' = varCurrentUser.Email &&
               (
                   varFilterStatus = "All" ||
                   Status.Value = varFilterStatus
               )
           ),
           "Due Date",
           Ascending
       )
   X: 0
   Y: recFilterBar.Y + recFilterBar.Height
   Width: Parent.Width
   Height: Parent.Height - Y
   TemplateSize: 100
   ```

### Design Gallery Template

Inside **galTasks**, add:

1. **Rectangle (Card background)**
   ```
   Width: Parent.TemplateWidth - 20
   Height: Parent.TemplateHeight - 10
   X: 10
   Y: 5
   Fill: White
   BorderRadius: 8
   BorderThickness: 1
   BorderColor: RGBA(220, 220, 220, 1)
   ```

2. **Rectangle (Left accent bar - priority indicator)**
   ```
   Width: 5
   Height: Parent.TemplateHeight - 10
   X: 10
   Y: 5
   Fill: 
       Switch(
           ThisItem.Priority.Value,
           "High", RGBA(192, 0, 0, 1),
           "Medium", RGBA(255, 192, 0, 1),
           "Low", RGBA(0, 176, 80, 1),
           RGBA(200, 200, 200, 1)
       )
   BorderRadius: 8 // Match card radius
   ```

3. **Label (Task name)**
   ```
   Text: ThisItem.'Task Name'
   X: 25
   Y: 15
   Width: Parent.TemplateWidth - 120
   Size: 15
   FontWeight: Semibold
   Color: Black
   ```

4. **Label (Apparatus/Equipment)**
   ```
   Text: ThisItem.Apparatus.Name
   X: 25
   Y: [task name].Y + [task name].Height + 5
   Size: 12
   Color: RGBA(0, 0, 0, 0.6)
   ```

5. **Label (Due date)**
   ```
   Text: "Due: " & Text(ThisItem.'Due Date', "mm/dd/yyyy")
   X: 25
   Y: [apparatus].Y + [apparatus].Height + 5
   Size: 11
   Color: If(
       DateValue(Text(ThisItem.'Due Date')) < Today(),
       RGBA(192, 0, 0, 1),  // Red if overdue
       RGBA(0, 0, 0, 0.6)
   )
   ```

6. **Icon (Status badge)**
   ```
   Icon: 
       Switch(
           ThisItem.Status.Value,
           "Completed", Icon.CheckBadge,
           "In Progress", Icon.Clock,
           "Overdue", Icon.Warning,
           Icon.Circle
       )
   X: Parent.TemplateWidth - 50
   Y: 20
   Size: 24
   Color: 
       Switch(
           ThisItem.Status.Value,
           "Completed", RGBA(0, 176, 80, 1),
           "In Progress", RGBA(255, 192, 0, 1),
           "Overdue", RGBA(192, 0, 0, 1),
           RGBA(200, 200, 200, 1)
       )
   ```

7. **Label (Hours remaining)**
   ```
   Text: ThisItem.'Remaining Hours' & " hrs"
   X: Parent.TemplateWidth - 80
   Y: [status icon].Y + [status icon].Height + 5
   Size: 11
   Color: RGBA(0, 0, 0, 0.6)
   ```

8. **Gallery OnSelect**:
   ```
   Set(varSelectedTask, ThisItem);
   Navigate(TaskDetailScreen, ScreenTransition.Cover)
   ```

### Add Search Box (Optional)

1. **Insert** → **Text input**
   ```
   Name: txtSearch
   X: 10
   Y: recFilterBar.Y + recFilterBar.Height + 10
   Width: Parent.Width - 20
   HintText: "🔍 Search tasks..."
   ```

2. Update **galTasks.Items** to include search:
   ```
   SortByColumns(
       Filter(
           Tasks,
           'Assigned To' = varCurrentUser.Email &&
           (
               varFilterStatus = "All" ||
               Status.Value = varFilterStatus
           ) &&
           (
               IsBlank(txtSearch.Text) ||
               txtSearch.Text in 'Task Name' ||
               txtSearch.Text in Apparatus.Name
           )
       ),
       "Due Date",
       Ascending
   )
   ```

---

## Phase 5: Task Detail Screen (45 minutes)

### Screen 3: TaskDetailScreen

1. **Insert** → **New screen** → **Blank**
2. Rename to **"TaskDetailScreen"**

### Add Header

Copy header from TaskListScreen, update:
```
lblAppTitle.Text: "Task Details"
```

### Add Scrollable Form Container

1. **Insert** → **Vertical gallery** (acts as scrollable container)
   ```
   Name: galTaskDetail
   Items: [varSelectedTask]  // Single item
   X: 0
   Y: recHeader.Height
   Width: Parent.Width
   Height: Parent.Height - recHeader.Height - 80  // Leave space for button
   TemplateSize: 800  // Allow scrolling
   ```

### Inside Gallery Template, Add Form Sections:

**Section 1: Task Information**

1. **Label (Section header)**
   ```
   Text: "Task Information"
   X: 20
   Y: 20
   FontWeight: Semibold
   Size: 16
   ```

2. **Label (Task Name label)**
   ```
   Text: "Task:"
   X: 20
   Y: [section header].Y + [section header].Height + 15
   Size: 12
   Color: Gray
   ```

3. **Label (Task Name value)**
   ```
   Text: varSelectedTask.'Task Name'
   X: 20
   Y: [label].Y + [label].Height + 5
   Width: Parent.TemplateWidth - 40
   Size: 18
   FontWeight: Semibold
   Wrap: true
   ```

4. **Repeat pattern** for:
   - Project (lookup)
   - Scope
   - Apparatus
   - Designation
   - Drawing

**Section 2: Status Update**

1. **Label (Section header)**
   ```
   Text: "Status"
   Y: [previous section end] + 30
   ```

2. **Dropdown**
   - Name: **ddStatus**
   ```
   Items: colStatus
   DefaultSelectedItems: LookUp(colStatus, Value = varSelectedTask.Status.Value)
   X: 20
   Y: [section header].Y + [section header].Height + 10
   Width: Parent.TemplateWidth - 40
   ```

3. **Slider (Percent complete)**
   - Name: **sldrPercentComplete**
   ```
   Min: 0
   Max: 100
   Default: varSelectedTask.'Percent Complete'
   X: 20
   Y: ddStatus.Y + ddStatus.Height + 30
   Width: Parent.TemplateWidth - 40
   HandleSize: 20
   ```

4. **Label (Percent display)**
   ```
   Text: Round(sldrPercentComplete.Value, 0) & "%"
   X: 20
   Y: sldrPercentComplete.Y - 25
   Size: 14
   FontWeight: Semibold
   ```

**Section 3: Hours**

1. **Label (Section header)**
   ```
   Text: "Hours"
   Y: [slider].Y + [slider].Height + 30
   ```

2. **Label (Quoted hours - read only)**
   ```
   Text: "Quoted: " & varSelectedTask.'Quoted Hours' & " hrs"
   ```

3. **Label (Actual hours - read only)**
   ```
   Text: "Actual: " & varSelectedTask.'Actual Hours' & " hrs"
   ```

4. **Label (Remaining)**
   ```
   Text: "Remaining: " & varSelectedTask.'Remaining Hours' & " hrs"
   Color: If(varSelectedTask.'Remaining Hours' < 0, Red, Black)
   ```

**Section 4: Notes**

1. **Label (Section header)**
   ```
   Text: "Notes"
   Y: [hours section end] + 30
   ```

2. **Text input (multiline)**
   - Name: **txtNotes**
   ```
   Mode: TextMode.MultiLine
   Default: varSelectedTask.Notes
   X: 20
   Y: [section header].Y + [section header].Height + 10
   Width: Parent.TemplateWidth - 40
   Height: 120
   HintText: "Add notes about this task..."
   ```

**Section 5: Photo Upload**

1. **Label (Section header)**
   ```
   Text: "Datasheet Photo"
   Y: txtNotes.Y + txtNotes.Height + 30
   ```

2. **Add picture control**
   - Name: **addPhoto**
   ```
   X: 20
   Y: [section header].Y + [section header].Height + 10
   Width: Parent.TemplateWidth - 40
   Height: 200
   ```

### Add Action Buttons (Bottom of screen)

1. **Rectangle (Button bar background)**
   ```
   X: 0
   Y: Parent.Height - 80
   Width: Parent.Width
   Height: 80
   Fill: White
   BorderThickness: 1
   BorderColor: RGBA(220, 220, 220, 1)
   ```

2. **Button (Save changes)**
   - Name: **btnSave**
   ```
   Text: "💾 Save Changes"
   X: 10
   Y: Parent.Height - 70
   Width: (Parent.Width - 30) / 2
   Height: 50
   Fill: RGBA(0, 120, 212, 1)
   Color: White
   BorderRadius: 8
   OnSelect:
       Patch(
           Tasks,
           LookUp(Tasks, ID = varSelectedTask.ID),
           {
               Status: ddStatus.Selected,
               'Percent Complete': sldrPercentComplete.Value,
               Notes: txtNotes.Text,
               'Modified On': Now()
           }
       );
       Notify("Task updated successfully!", NotificationType.Success);
       Back()
   ```

3. **Button (Log time)**
   ```
   Text: "⏱️ Log Time"
   X: btnSave.X + btnSave.Width + 10
   Y: btnSave.Y
   Width: btnSave.Width
   Height: btnSave.Height
   Fill: RGBA(0, 176, 80, 1)
   OnSelect:
       Set(varTimeEntryTask, varSelectedTask);
       Navigate(TimeEntryScreen, ScreenTransition.Cover)
   ```

---

## Phase 6: Time Entry Screen (30 minutes)

### Screen 4: TimeEntryScreen

1. **Insert** → **New screen** → **Blank**
2. Rename to **"TimeEntryScreen"**

### Add Header

```
lblAppTitle.Text: "Log Time"
```

### Add Form

1. **Edit form** component
   - Name: **frmTimeEntry**
   ```
   DataSource: 'Time Entries'  // Your time entry table
   Item: Blank()  // New entry
   X: 0
   Y: recHeader.Height + 20
   Width: Parent.Width
   Height: Parent.Height - recHeader.Height - 100
   ```

2. **Configure form fields**:
   - Click **Edit fields** in properties pane
   - Add fields:
     - **Task** (Lookup to Tasks)
     - **Date** (Date picker)
     - **Hours** (Number input)
     - **Labor Type** (Dropdown: Base, Travel, PM, etc.)
     - **Notes** (Text multiline)

3. **Customize field defaults**:
   
   In form's **OnVisible**:
   ```
   NewForm(frmTimeEntry);
   // Set defaults if coming from task detail
   If(
       !IsBlank(varTimeEntryTask),
       Patch(frmTimeEntry.Updates, {
           Task: varTimeEntryTask,
           Date: Today(),
           'Week Ending': 
               DateAdd(Today(), (6 - Weekday(Today())) mod 7, Days)
       })
   )
   ```

### Add Submit Button

```
Name: btnSubmitTime
Text: "✓ Submit Time Entry"
X: 10
Y: Parent.Height - 80
Width: Parent.Width - 20
Height: 60
Fill: RGBA(0, 176, 80, 1)
Color: White
FontSize: 16
BorderRadius: 8
OnSelect:
    If(
        frmTimeEntry.Valid,
        SubmitForm(frmTimeEntry);
        Notify("Time entry logged successfully!", NotificationType.Success);
        Back(),
        Notify("Please fill in all required fields", NotificationType.Error)
    )
```

### Add Form Success/Error Handling

**frmTimeEntry.OnSuccess**:
```
Notify("Time entry saved!", NotificationType.Success);
Set(varTimeEntryTask, Blank());
Back()
```

**frmTimeEntry.OnFailure**:
```
Notify("Error saving time entry: " & frmTimeEntry.Error, NotificationType.Error)
```

---

## Phase 7: Offline Capability (20 minutes)

### Enable Offline Mode

1. **App.OnStart** - Add offline collections:
   ```
   // Load tasks for offline use
   ClearCollect(
       colOfflineTasks,
       Filter(
           Tasks,
           'Assigned To' = varCurrentUser.Email &&
           Status.Value <> "Completed"
       )
   );
   
   // Load time entries (last 30 days)
   ClearCollect(
       colOfflineTimeEntries,
       Filter(
           'Time Entries',
           'Created By' = varCurrentUser &&
           Date >= DateAdd(Today(), -30)
       )
   );
   
   // Set connectivity flag
   Set(varIsOnline, Connection.Connected);
   ```

2. **Update gallery Items formulas** to use collections when offline:
   ```
   // TaskListScreen - galTasks.Items
   If(
       varIsOnline,
       // Online - use live data
       SortByColumns(Filter(Tasks, ...), "Due Date", Ascending),
       // Offline - use cached collection
       SortByColumns(Filter(colOfflineTasks, ...), "Due Date", Ascending)
   )
   ```

3. **Update Save button** to queue changes when offline:
   ```
   If(
       varIsOnline,
       // Online - save directly
       Patch(Tasks, LookUp(Tasks, ID = varSelectedTask.ID), {...}),
       // Offline - save to collection and sync later
       Collect(colPendingUpdates, {
           TaskID: varSelectedTask.ID,
           Status: ddStatus.Selected.Value,
           PercentComplete: sldrPercentComplete.Value,
           Notes: txtNotes.Text,
           Timestamp: Now()
       });
       Notify("Saved offline. Will sync when connected.", NotificationType.Warning)
   )
   ```

4. **Add sync function** (call when connection restored):
   ```
   // Create button or auto-trigger
   ForAll(
       colPendingUpdates,
       Patch(
           Tasks,
           LookUp(Tasks, ID = TaskID),
           {
               Status: Status,
               'Percent Complete': PercentComplete,
               Notes: Notes
           }
       )
   );
   Clear(colPendingUpdates);
   Notify("All changes synced!", NotificationType.Success)
   ```

---

## Phase 8: Polish & Performance (15 minutes)

### Add Loading Indicators

1. **Create variable** in App.OnStart:
   ```
   Set(varIsLoading, false);
   ```

2. **Add spinner** to each screen:
   ```
   // Insert → Icon → Loading spinner
   Name: icnLoading
   Visible: varIsLoading
   X: (Parent.Width - Width) / 2
   Y: (Parent.Height - Height) / 2
   Color: RGBA(116, 39, 116, 1)
   ```

3. **Show spinner during data operations**:
   ```
   // Before Patch/Submit
   Set(varIsLoading, true);
   
   // After Patch/Submit (in OnSuccess/OnFailure)
   Set(varIsLoading, false);
   ```

### Add Empty State Messages

```
// In galTasks, add a label outside gallery
Name: lblEmptyState
Visible: CountRows(galTasks.AllItems) = 0
Text: "No tasks found. Try adjusting your filters."
X: (Parent.Width - Width) / 2
Y: (Parent.Height - Height) / 2
Align: Center
Size: 14
Color: Gray
```

### Add Error Boundaries

Wrap critical operations in **IfError()**:
```
IfError(
    // Try to load data
    ClearCollect(colTasks, Filter(Tasks, ...)),
    // On error, show notification
    Notify("Error loading tasks. Please try again.", NotificationType.Error);
    Clear(colTasks)
)
```

### Optimize Gallery Performance

1. **Limit Items shown**:
   ```
   Items: FirstN(
       Filter(...),
       100  // Only show first 100
   )
   ```

2. **Use delegation** - avoid:
   - `Filter` on non-delegable columns
   - `Search` on large datasets
   - Complex formulas in gallery items

3. **Enable gallery optimization**:
   - Properties → **Data** → ✅ Enable gallery optimization

---

## Phase 9: Testing Checklist

### Functionality Tests

- [ ] App launches successfully
- [ ] Home screen displays correct task counts
- [ ] Task list filters work (All, In Progress, etc.)
- [ ] Task detail screen loads selected task
- [ ] Status dropdown updates correctly
- [ ] Percent slider works smoothly
- [ ] Notes save properly
- [ ] Photo upload works (if implemented)
- [ ] Time entry form submits successfully
- [ ] Back navigation works on all screens
- [ ] Search functionality works
- [ ] Offline mode collects data
- [ ] Pending changes sync when online

### Mobile Tests

- [ ] Test on iOS device
- [ ] Test on Android device
- [ ] Portrait orientation locked
- [ ] Buttons are thumb-friendly (48+ px)
- [ ] Text is readable (14+ px)
- [ ] Forms work with mobile keyboard
- [ ] Camera/photo picker works
- [ ] Touch gestures work (tap, swipe, scroll)

### Performance Tests

- [ ] App loads in <3 seconds
- [ ] Galleries scroll smoothly
- [ ] No lag when typing
- [ ] Data saves in <2 seconds
- [ ] Search responds quickly

---

## Phase 10: Publish & Share

### Publish the App

1. Click **Publish** button (top right)
2. Click **Publish this version**
3. Add **release notes**: "Initial field tracker release - v1.0"
4. Click **Publish**

### Share with Users

1. Click **Share** button
2. Enter user emails or security group
3. Select permission: **User** (can use app, not edit)
4. ✅ **Send email invitation**
5. Click **Share**

### Generate App Link

1. After sharing, copy the **Web link**
2. Share this link via:
   - Email
   - Teams
   - SharePoint page
   - QR code (for easy mobile access)

### Add to Teams (Optional)

1. Open Teams
2. Click **+ Add a tab**
3. Search **Power Apps**
4. Select your app
5. Pin to channel

---

## Quick Reference: Essential Formulas

### Filter Current User's Tasks
```javascript
Filter(
    Tasks,
    'Assigned To' = User().Email &&
    Status.Value <> "Completed"
)
```

### Count Overdue Tasks
```javascript
CountRows(
    Filter(
        Tasks,
        'Assigned To' = User().Email &&
        DateValue(Text('Due Date')) < Today() &&
        Status.Value <> "Completed"
    )
)
```

### Color Based on Status
```javascript
Switch(
    ThisItem.Status.Value,
    "Completed", RGBA(0, 176, 80, 1),      // Green
    "In Progress", RGBA(255, 192, 0, 1),   // Yellow
    "Overdue", RGBA(192, 0, 0, 1),         // Red
    RGBA(200, 200, 200, 1)                 // Gray default
)
```

### Save with Validation
```javascript
If(
    !IsBlank(ddStatus.Selected) && !IsBlank(txtNotes.Text),
    Patch(
        Tasks,
        LookUp(Tasks, ID = varSelectedTask.ID),
        {
            Status: ddStatus.Selected,
            'Percent Complete': sldrPercentComplete.Value,
            Notes: txtNotes.Text,
            'Modified On': Now()
        }
    );
    Notify("Saved successfully!", NotificationType.Success);
    Back(),
    Notify("Please complete all fields", NotificationType.Warning)
)
```

### Format Date Nicely
```javascript
Text(ThisItem.'Due Date', "[$-en-US]mmm dd, yyyy")
// Output: "Nov 07, 2025"
```

### Calculate Week Ending Date (Friday)
```javascript
DateAdd(
    Today(), 
    (6 - Weekday(Today())) mod 7, 
    Days
)
```

---

## Troubleshooting Common Issues

### Issue: Gallery not showing data
**Solution**: 
- Check data source connection
- Verify Filter formula
- Check delegation warnings (yellow triangles)
- Test with: `Items: Tasks` (no filter)

### Issue: Patch not saving
**Solution**:
- Check field names match exactly (case-sensitive)
- Verify user has write permission
- Check for required fields
- Use `frmTimeEntry.Updates` to see what's being sent

### Issue: App too slow
**Solution**:
- Use `FirstN()` to limit gallery items
- Move complex calculations to variables
- Use collections for reference data
- Enable gallery optimization

### Issue: Offline mode not working
**Solution**:
- Check `Connection.Connected` value
- Verify collections are populated in OnStart
- Test with airplane mode on device
- Check for delegation issues in Filter

---

## Next Steps

### Immediate (Today)
1. ✅ Build MVP with Home, Task List, Task Detail screens
2. ✅ Test with sample data
3. ✅ Share with 2-3 pilot users

### Week 1
1. Add Time Entry screen
2. Implement offline mode
3. Add photo upload
4. Gather user feedback

### Week 2
1. Add Project Search screen
2. Implement advanced filters
3. Add Profile/Settings screen
4. Polish UI based on feedback

### Week 3
1. Connect to Model-Driven app
2. Set up Power Automate notifications
3. Create user documentation
4. Full team rollout

---

## Resources & Support

### Power Apps Formulas Reference
- https://learn.microsoft.com/en-us/power-platform/power-fx/formula-reference

### Power Apps Community
- https://powerusers.microsoft.com/t5/Power-Apps-Community/ct-p/PowerApps1

### Video Tutorials
- Shane Young: https://youtube.com/@ShaneYoungCloud
- April Dunnam: https://youtube.com/@AprilDunnam

### Get Help
- Power Apps in-product help (? icon)
- Copilot in Power Apps (for formula help)
- Post questions in Power Apps Community

---

**You're ready to build!** 🚀

Start with the HomeScreen, then TaskListScreen, then TaskDetailScreen. Each should take 20-30 minutes. Test frequently as you build.

*Created: November 7, 2025*
*Version: 1.0*
*For: RESA Power Field Tracker Canvas App*
