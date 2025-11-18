# Power Apps Quick Reference - Cheat Sheet

## 🚀 Most Common Formulas

### Navigation
```javascript
// Go to screen
Navigate(TaskListScreen, ScreenTransition.Fade)

// Go back
Back()

// Go back multiple screens
Back(Back())
```

### Variables
```javascript
// Set global variable
Set(varTaskID, 123)

// Set multiple variables at once
Set(varName, "John"); Set(varAge, 30)

// Clear variable
Set(varName, Blank())

// Context variable (screen-specific)
UpdateContext({locVar: "value"})
```

### Collections
```javascript
// Create collection
ClearCollect(colTasks, Tasks)

// Add to collection
Collect(colTasks, {Name: "New Task"})

// Remove from collection
Remove(colTasks, ThisItem)

// Clear collection
Clear(colTasks)

// Update item in collection
Patch(colTasks, LookUp(colTasks, ID = 123), {Status: "Done"})
```

### Filter & Sort
```javascript
// Filter by current user
Filter(Tasks, 'Assigned To' = User().Email)

// Multiple conditions (AND)
Filter(Tasks, Status = "Active" && Priority = "High")

// Multiple conditions (OR)
Filter(Tasks, Status = "Active" || Status = "Pending")

// Sort ascending
SortByColumns(Tasks, "Due Date", Ascending)

// Sort descending
SortByColumns(Tasks, "Modified On", Descending)

// Search in text
Filter(Tasks, txtSearch.Text in 'Task Name')
```

### Dates
```javascript
// Today's date
Today()

// Current date & time
Now()

// Add days
DateAdd(Today(), 7, Days)

// Subtract days
DateAdd(Today(), -7, Days)

// Format date
Text(Today(), "mm/dd/yyyy")
Text(Now(), "[$-en-US]mmm dd, yyyy hh:mm AM/PM")

// Date difference
DateDiff(StartDate, EndDate, Days)

// Check if overdue
DateValue('Due Date') < Today()

// Week ending (Friday)
DateAdd(Today(), (6 - Weekday(Today())) mod 7, Days)
```

### Text & Strings
```javascript
// Concatenate
"Hello " & varName & "!"
Concatenate("Hello ", varName, "!")

// Upper/Lower case
Upper("hello")  // HELLO
Lower("HELLO")  // hello

// Length
Len("Hello")  // 5

// Substring
Mid("Hello World", 7, 5)  // "World"

// Replace
Substitute("Hello World", "World", "PowerApps")

// Check if blank
IsBlank(txtInput.Text)

// Default if blank
If(IsBlank(txtName.Text), "Unknown", txtName.Text)
```

### Numbers
```javascript
// Sum
Sum(Tasks, Hours)

// Count
CountRows(Tasks)
Count(Tasks, Hours)  // Count non-blank

// Average
Average(Tasks, Hours)

// Max/Min
Max(Tasks, Hours)
Min(Tasks, Hours)

// Round
Round(12.567, 2)  // 12.57
RoundUp(12.1, 0)  // 13
RoundDown(12.9, 0)  // 12

// Convert text to number
Value("123")
```

### Conditional Logic
```javascript
// If statement
If(varAge >= 18, "Adult", "Minor")

// Nested If
If(
    varScore >= 90, "A",
    If(varScore >= 80, "B",
       If(varScore >= 70, "C", "F")
    )
)

// Switch (cleaner than nested If)
Switch(
    varStatus,
    "Active", "✓",
    "Pending", "⏱",
    "Completed", "✅",
    "❓"  // Default
)
```

### Patch (Save Data)
```javascript
// Update existing record
Patch(
    Tasks,
    LookUp(Tasks, ID = varTaskID),
    {
        Status: "Completed",
        'Completion Date': Today()
    }
)

// Create new record
Patch(
    Tasks,
    Defaults(Tasks),
    {
        'Task Name': txtTaskName.Text,
        'Created By': User(),
        'Created On': Now()
    }
)

// Multiple updates
Patch(
    Tasks,
    LookUp(Tasks, ID = varTaskID),
    {
        Status: ddStatus.Selected,
        'Percent Complete': sldrPercent.Value,
        Notes: txtNotes.Text
    }
)
```

### Form Functions
```javascript
// Submit form
SubmitForm(frmTask)

// New form
NewForm(frmTask)

// Edit form
EditForm(frmTask)

// Reset form
ResetForm(frmTask)

// Check if valid
frmTask.Valid

// Get form values
frmTask.Updates

// Get last submitted record
frmTask.LastSubmit
```

### Notifications
```javascript
// Success
Notify("Saved successfully!", NotificationType.Success)

// Error
Notify("An error occurred", NotificationType.Error)

// Warning
Notify("Please review", NotificationType.Warning)

// Info (default)
Notify("Task updated")

// With duration (milliseconds)
Notify("Saved!", NotificationType.Success, 2000)
```

### User Info
```javascript
// Current user email
User().Email

// Current user full name
User().FullName

// Current user image
User().Image
```

---

## 🎨 Common UI Formulas

### Visibility
```javascript
// Show/hide based on variable
Visible: varShowForm

// Show if not blank
Visible: !IsBlank(varSelectedTask)

// Show if collection has items
Visible: CountRows(colTasks) > 0

// Show for specific status
Visible: varStatus = "Active"
```

### Enable/Disable
```javascript
// Disable if blank
DisplayMode: If(IsBlank(txtInput.Text), DisplayMode.Disabled, DisplayMode.Edit)

// Disable while loading
DisplayMode: If(varIsLoading, DisplayMode.Disabled, DisplayMode.Edit)

// Disable if invalid
Disabled: !frmTask.Valid
```

### Colors
```javascript
// Status-based
Fill: Switch(
    ThisItem.Status,
    "Active", RGBA(0, 176, 80, 1),
    "Pending", RGBA(255, 192, 0, 1),
    "Inactive", RGBA(192, 0, 0, 1),
    RGBA(200, 200, 200, 1)
)

// Alternate row colors in gallery
Fill: If(Mod(ThisItem.Value, 2) = 0, 
    RGBA(245, 245, 245, 1), 
    White
)

// Hover effect
Fill: If(Self.Pressed, 
    RGBA(0, 90, 158, 1),
    If(Self.Hover, RGBA(0, 100, 180, 1), RGBA(0, 120, 212, 1))
)
```

### Positioning
```javascript
// Center horizontally
X: (Parent.Width - Self.Width) / 2

// Center vertically
Y: (Parent.Height - Self.Height) / 2

// Full width with padding
Width: Parent.Width - 40

// Responsive width (half screen)
Width: Parent.Width / 2 - 15

// Stack vertically
Y: PreviousControl.Y + PreviousControl.Height + 10
```

---

## 🔧 Gallery Formulas

### Items
```javascript
// Basic filter
Items: Filter(Tasks, Status = "Active")

// With sort
Items: SortByColumns(
    Filter(Tasks, Status = "Active"),
    "Due Date", Ascending
)

// With search
Items: Filter(
    Tasks,
    txtSearch.Text in 'Task Name' || 
    txtSearch.Text in Description
)

// Current user only
Items: Filter(Tasks, 'Assigned To' = User().Email)

// Multiple filters
Items: Filter(
    Tasks,
    Status = ddStatusFilter.Selected.Value &&
    'Assigned To' = User().Email &&
    Year('Due Date') = Year(Today())
)

// Limit results (performance)
Items: FirstN(
    SortByColumns(Filter(Tasks, ...), "Date", Descending),
    100
)
```

### Gallery Navigation
```javascript
// OnSelect (entire gallery)
Set(varSelectedItem, ThisItem);
Navigate(DetailScreen, ScreenTransition.Cover)

// OnSelect (specific item)
Button.OnSelect: 
    Set(varSelectedTask, ThisItem);
    Navigate(TaskDetailScreen)
```

### Gallery Pagination
```javascript
// Show more button
Visible: CountRows(galTasks.AllItems) = 100

OnSelect: 
    Set(varPageSize, varPageSize + 50)

galTasks.Items:
    FirstN(Filter(...), varPageSize)
```

---

## ⚡ Performance Tips

### Delegation
```javascript
// ✅ GOOD - Delegable
Filter(Tasks, Status = "Active")
Search(Tasks, txtSearch.Text, "TaskName")

// ❌ BAD - Non-delegable
Filter(Tasks, Year('Due Date') = 2025)  // Year() not delegable
Filter(Tasks, Len('Task Name') > 10)    // Len() not delegable

// Fix: Use calculated column in data source
// OR limit results with FirstN()
FirstN(Filter(...), 500)
```

### Collections vs Direct
```javascript
// ✅ Use collections for:
- Reference data (dropdown lists)
- Offline scenarios
- Data used across multiple screens
- Complex calculations done once

// ✅ Use direct connections for:
- Large datasets
- Real-time data
- Data that changes frequently
```

### Optimize Galleries
```javascript
// 1. Enable gallery optimization
Properties → Data → ✅ Optimize gallery performance

// 2. Limit items shown
Items: FirstN(Filter(...), 100)

// 3. Avoid complex formulas in gallery items
// BAD:
Text: CountRows(Filter(Tasks, Project = ThisItem.ID))

// GOOD:
Add a calculated column or rollup field in data source

// 4. Use collections for dropdown data
// BAD: Dropdown.Items: Choices(Tasks.Status)
// GOOD: Dropdown.Items: colStatusChoices
```

---

## 🐛 Common Errors & Fixes

### "Delegation Warning"
**Problem**: Formula can't be delegated, may not return all results
**Fix**: 
- Use FirstN() to limit results
- Move complex logic to data source
- Use collections for small datasets
```javascript
// Before:
Filter(Tasks, Len('Task Name') > 10)

// After:
FirstN(Filter(Tasks, 'Name Length' > 10), 500)
// Add 'Name Length' calculated field in data source
```

### "Name isn't valid"
**Problem**: Column name has spaces or special characters
**Fix**: Use single quotes
```javascript
// Wrong: Tasks.Assigned To
// Right: Tasks.'Assigned To'
```

### "Invalid argument type"
**Problem**: Type mismatch (text vs number, etc.)
**Fix**: Use Value() or Text() to convert
```javascript
// Wrong: "Hours: " & varHours
// Right: "Hours: " & Text(varHours)

// Wrong: If(txtAge.Text > 18)
// Right: If(Value(txtAge.Text) > 18)
```

### "Expected record value"
**Problem**: Trying to access property of null/blank
**Fix**: Check with IsBlank() first
```javascript
// Wrong: varSelectedTask.Name
// Right: If(IsBlank(varSelectedTask), "", varSelectedTask.Name)
```

### Gallery Not Showing Data
**Fix**:
```javascript
// 1. Check Items formula (no red errors)
// 2. Remove filters temporarily
Items: Tasks  // Test without filters

// 3. Check if data source connected
// 4. Check template size (not 0)
// 5. Check fill color (not same as background)
```

### Form Not Saving
**Fix**:
```javascript
// 1. Check frmTask.Valid before submit
If(frmTask.Valid, SubmitForm(frmTask))

// 2. Check required fields filled
// 3. Check OnSuccess/OnFailure for errors
OnFailure: Notify(frmTask.Error, NotificationType.Error)

// 4. For Patch, check field names exact
Patch(Tasks, {..., 'Field Name': value})  // Use quotes!
```

### Slow Performance
**Fix**:
```javascript
// 1. Use FirstN() to limit gallery items
Items: FirstN(Filter(...), 50)

// 2. Move collections to App.OnStart
App.OnStart: ClearCollect(colStatus, Choices(Tasks.Status))

// 3. Avoid complex formulas in gallery
// Put in variables instead

// 4. Optimize images (<100KB)
// 5. Remove nested galleries
```

---

## 📱 Mobile Best Practices

### Touch Targets
```javascript
// Minimum size
Height: 48
Width: 48

// Spacing between
Padding: 8
```

### Responsive Sizing
```javascript
// Relative to screen
Width: Parent.Width * 0.9

// Fixed with min/max
Width: Max(300, Min(Parent.Width - 40, 600))
```

### Keyboard Handling
```javascript
// Move controls up when keyboard shows
Y: If(txtInput.Focused, 100, 400)

// Or use scrollable container (gallery)
```

---

## 🔐 Security Formulas

### Filter by Current User
```javascript
Filter(Tasks, 'Assigned To' = User().Email)

Filter(Projects, Owner.Email = User().Email)
```

### Hide Sensitive Data
```javascript
// Show salary only to managers
Visible: User().Email in ["manager@company.com", "hr@company.com"]
```

### Disable Editing for Non-Owners
```javascript
DisplayMode: If(
    ThisItem.'Created By'.Email = User().Email,
    DisplayMode.Edit,
    DisplayMode.View
)
```

---

## 🎯 Pro Tips

### 1. Use Consistent Naming
```javascript
// Variables
varTaskID        // Global variable
locTaskID        // Local (context) variable
colTasks         // Collection

// Controls
galTasks         // Gallery
txtTaskName      // Text input
lblTitle         // Label
btnSave          // Button
ddStatus         // Dropdown
```

### 2. Comment Your Complex Formulas
```javascript
// Calculate billable hours
// Formula: Base hours * (1 + overtime rate) + travel
varBillableHours: 
    varBaseHours * (1 + varOTRate) + varTravelHours
```

### 3. Use Defaults() for New Records
```javascript
Patch(
    Tasks,
    Defaults(Tasks),  // Gets default values
    {
        'Task Name': txtName.Text
        // Other fields...
    }
)
```

### 4. Test Formulas in Label
```javascript
// Add temporary label to test formulas
Text: CountRows(Filter(Tasks, Status = "Active"))
// Check if result is what you expect
```

### 5. Handle Errors Gracefully
```javascript
IfError(
    // Try this
    ClearCollect(colTasks, Tasks),
    // If error, do this
    Notify("Could not load tasks", NotificationType.Error);
    Set(varHasError, true)
)
```

---

## 📋 Pre-Flight Checklist

Before publishing, verify:

- [ ] All galleries load in <2 seconds
- [ ] No delegation warnings (or FirstN() used)
- [ ] All buttons have OnSelect actions
- [ ] All forms have OnSuccess/OnFailure handlers
- [ ] Loading indicators shown during saves
- [ ] Error messages are user-friendly
- [ ] Required fields clearly marked
- [ ] All screens have back navigation
- [ ] Tested on actual mobile device
- [ ] Color contrast meets accessibility standards
- [ ] Touch targets ≥ 48px
- [ ] Text size ≥ 14px

---

## 🆘 Quick Fixes

### App Won't Load
1. Check data source connections
2. Look for red errors in formulas
3. Check App.OnStart for errors
4. Try: File → Settings → Remove unused dependencies

### Can't Save Data
1. Check table permissions in Dataverse
2. Verify required fields filled
3. Check field name spelling (case-sensitive)
4. Use frmTask.Error to see error message

### Slow Gallery Scrolling
1. Reduce TemplateSize if too large
2. Use FirstN() to limit items
3. Simplify formulas in gallery items
4. Enable gallery optimization in settings

### Data Not Refreshing
1. Add: Refresh(Tasks) in OnVisible
2. Or use: Navigate(Screen, ScreenTransition.None)
3. For galleries: Reset(galTasks)

---

**Print this page and keep it handy while building!** 🖨️

*Quick Reference Version: 1.0*
*Last Updated: November 7, 2025*
