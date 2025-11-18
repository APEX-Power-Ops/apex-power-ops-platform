VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "ThisWorkbook"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True

Option Explicit

' ================================================================================
' DATE COMPLETION SYSTEM WITH AUTO/MANUAL MODE TOGGLE
' ================================================================================
' SYSTEM DESIGN:
'
' AUTO MODE (Default - Normal Workflow):
'   - Status ? "COMPLETED" ? Auto-populate date (if empty)
'   - Status ? Not "COMPLETED" ? Auto-clear date (if auto-filled)
'   - This is the 99% use case
'
' MANUAL MODE (Exception Handling - Corrections Only):
'   - Auto-population SUSPENDED
'   - Auto-clearing SUSPENDED
'   - User can ONLY edit dates on rows where Status = "COMPLETED"
'   - Dates entered in Manual Mode are PERMANENTLY PRESERVED
'   - Used for: correcting completion dates, backdating, exceptions
'
' WORKBOOK BEHAVIOR:
'   - Opens in AUTO mode (default)
'   - Mode persists during session
'   - Mode toggle via Ribbon button
'   - Visual feedback: Status bar + button state
' ================================================================================

Private Const MODE_AUTO As String = "AUTO"
Private Const MODE_MANUAL As String = "MANUAL"
Private Const STATUS_COL As Long = 2    ' Column B = Status
Private Const DATE_COL As Long = 12     ' Column L = Date Completed
Private Const DATA_START_ROW As Long = 6 ' First data row

' ================================================================================
' WORKBOOK INITIALIZATION
' ================================================================================

Private Sub Workbook_Open()
    ' Initialize system to AUTO mode on workbook open
    SetDateMode MODE_AUTO
    UpdateStatusBar
End Sub

Private Sub Workbook_BeforeClose(Cancel As Boolean)
    ' Clean up status bar
    Application.StatusBar = False
End Sub

' ================================================================================
' MAIN CHANGE EVENT HANDLER
' ================================================================================

Private Sub Workbook_SheetChange(ByVal Sh As Object, ByVal Target As Range)
    ' Handles both Status column changes (auto-populate) and Date column changes (manual entry)
    
    Dim cell As Range
    Dim dateCell As Range
    Dim statusCell As Range
    Dim currentMode As String
    
    ' Skip system sheets
    If IsSystemSheet(Sh.Name) Then Exit Sub
    
    ' Get current mode
    currentMode = GetDateMode()
    
    Application.EnableEvents = False
    On Error GoTo Cleanup
    
    ' ===== HANDLE STATUS COLUMN CHANGES (Column B) =====
    If Not Intersect(Target, Sh.Columns(STATUS_COL)) Is Nothing Then
        
        If currentMode = MODE_AUTO Then
            ' AUTO MODE: Process status changes for auto-populate/clear
            For Each cell In Intersect(Target, Sh.Columns(STATUS_COL))
                If cell.row >= DATA_START_ROW Then
                    Set dateCell = Sh.Cells(cell.row, DATE_COL)
                    ProcessStatusChange cell, dateCell
                End If
            Next cell
        End If
        
        ' MANUAL MODE: Do nothing - auto behavior suspended
        
    End If
    
    ' ===== HANDLE DATE COLUMN CHANGES (Column L) =====
    If Not Intersect(Target, Sh.Columns(DATE_COL)) Is Nothing Then
        
        If currentMode = MODE_MANUAL Then
            ' MANUAL MODE: Validate that dates are only entered on COMPLETED rows
            Dim invalidEntry As Boolean
            Dim invalidRow As Long
            Dim invalidStatus As String
            
            For Each cell In Intersect(Target, Sh.Columns(DATE_COL))
                If cell.row >= DATA_START_ROW Then
                    Set statusCell = Sh.Cells(cell.row, STATUS_COL)
                    
                    ' Only allow date entry if row is COMPLETED
                    If UCase(Trim(CStr(statusCell.Value))) <> "COMPLETED" Then
                        ' Mark as invalid but don't undo yet
                        invalidEntry = True
                        invalidRow = cell.row
                        invalidStatus = CStr(statusCell.Value)
                        Exit For
                    Else
                        ' Valid manual entry - mark as manual (remove auto marker)
                        If Not IsEmpty(cell.Value) And cell.Value <> "" Then
                            ClearAutoFillMark cell
                        End If
                    End If
                End If
            Next cell
            
            ' If invalid entry detected, undo AFTER loop with events still disabled
            If invalidEntry Then
                Application.Undo
                Application.EnableEvents = True
                MsgBox "Manual dates can only be entered on COMPLETED rows." & vbCrLf & vbCrLf & _
                       "Row " & invalidRow & " status is: " & invalidStatus & vbCrLf & vbCrLf & _
                       "Please change status to COMPLETED first, or switch back to Auto Mode.", _
                       vbExclamation, "Manual Mode Protection"
                Exit Sub
            End If
            
        Else
            ' AUTO MODE: If user manually types a date, mark it as manual
            For Each cell In Intersect(Target, Sh.Columns(DATE_COL))
                If cell.row >= DATA_START_ROW Then
                    If Not IsEmpty(cell.Value) And cell.Value <> "" Then
                        ' User manually entered date in Auto mode - preserve it
                        ClearAutoFillMark cell
                    End If
                End If
            Next cell
        End If
        
    End If
    
Cleanup:
    Application.EnableEvents = True
End Sub

' ================================================================================
' STATUS CHANGE PROCESSING (AUTO MODE ONLY)
' ================================================================================

Private Sub ProcessStatusChange(statusCell As Range, dateCell As Range)
    ' Processes status changes for auto-populate/clear behavior
    ' Only called in AUTO MODE
    
    Dim wasManual As Boolean
    
    ' Check if date was manually entered
    wasManual = DateWasManuallyEntered(dateCell)
    
    If UCase(Trim(CStr(statusCell.Value))) = "COMPLETED" Then
        ' ===== STATUS IS COMPLETED =====
        
        If wasManual Then
            ' PRESERVE MANUAL DATE - do nothing
            ' This date was entered in Manual Mode or typed directly
            
        ElseIf IsEmpty(dateCell.Value) Or dateCell.Value = "" Or dateCell.Value = 0 Then
            ' CELL IS EMPTY - auto-fill with today's date
            dateCell.Value = Date
            MarkAsAutoFilled dateCell
        End If
        
    Else
        ' ===== STATUS IS NOT COMPLETED =====
        
        If wasManual Then
            ' PRESERVE MANUAL DATE - do nothing
            ' User wants to keep their manually entered date
            
        Else
            ' This was an auto-filled date - safe to clear
            If Not IsEmpty(dateCell.Value) Then
                dateCell.ClearContents
                ClearAutoFillMark dateCell
            End If
        End If
    End If
End Sub

' ================================================================================
' MODE MANAGEMENT
' ================================================================================

Public Sub SetDateMode(mode As String)
    ' Sets the current date mode (AUTO or MANUAL)
    ' Stores in CustomDocumentProperties for persistence
    
    On Error Resume Next
    ThisWorkbook.CustomDocumentProperties("DateCompletionMode").Delete
    On Error GoTo 0
    
    ThisWorkbook.CustomDocumentProperties.Add _
        Name:="DateCompletionMode", _
        LinkToContent:=False, _
        Type:=msoPropertyTypeString, _
        Value:=mode
    
    UpdateStatusBar
End Sub

Public Function GetDateMode() As String
    ' Gets the current date mode, defaults to AUTO if not set
    
    On Error Resume Next
    GetDateMode = ThisWorkbook.CustomDocumentProperties("DateCompletionMode").Value
    
    If GetDateMode = "" Or Err.Number <> 0 Then
        GetDateMode = MODE_AUTO
    End If
    
    On Error GoTo 0
End Function

Public Sub ToggleDateMode()
    ' Toggles between AUTO and MANUAL modes
    ' Called by ribbon button
    
    Dim currentMode As String
    Dim newMode As String
    Dim msg As String
    
    currentMode = GetDateMode()
    
    If currentMode = MODE_AUTO Then
        newMode = MODE_MANUAL
        msg = "MANUAL MODE ACTIVATED" & vbCrLf & vbCrLf & _
              "Auto-population is SUSPENDED." & vbCrLf & _
              "You can now manually edit dates on COMPLETED rows." & vbCrLf & vbCrLf & _
              "Use this mode to:" & vbCrLf & _
              "  • Correct completion dates" & vbCrLf & _
              "  • Backdate entries" & vbCrLf & _
              "  • Handle exceptions" & vbCrLf & vbCrLf & _
              "Switch back to Auto Mode when done."
    Else
        newMode = MODE_AUTO
        msg = "AUTO MODE ACTIVATED" & vbCrLf & vbCrLf & _
              "Normal workflow restored." & vbCrLf & _
              "Dates will auto-populate/clear based on status." & vbCrLf & vbCrLf & _
              "All manually-entered dates are preserved."
    End If
    
    SetDateMode newMode
    MsgBox msg, vbInformation, "Date Mode Changed"
End Sub

Public Sub SetAutoMode()
    ' Explicitly sets AUTO mode (for ribbon dropdown)
    If GetDateMode() <> MODE_AUTO Then
        SetDateMode MODE_AUTO
        MsgBox "Auto Mode activated - normal workflow restored.", vbInformation
    End If
End Sub

Public Sub SetManualMode()
    ' Explicitly sets MANUAL mode (for ribbon dropdown)
    If GetDateMode() <> MODE_MANUAL Then
        SetDateMode MODE_MANUAL
        MsgBox "Manual Mode activated - you can now override dates on COMPLETED rows.", vbInformation
    End If
End Sub

Private Sub UpdateStatusBar()
    ' Updates status bar to show current mode
    
    Dim currentMode As String
    currentMode = GetDateMode()
    
    If currentMode = MODE_MANUAL Then
        Application.StatusBar = "?? Date Mode: MANUAL - Override Active"
    Else
        Application.StatusBar = "Date Mode: Auto"
    End If
End Sub

Public Function GetModeForRibbon() As String
    ' Returns formatted mode name for ribbon button display
    Dim currentMode As String
    currentMode = GetDateMode()
    
    If currentMode = MODE_MANUAL Then
        GetModeForRibbon = "?? Manual Mode"
    Else
        GetModeForRibbon = "?? Auto Mode"
    End If
End Function

' ================================================================================
' HELPER FUNCTIONS - Manual vs Auto Detection
' ================================================================================

Private Function DateWasManuallyEntered(dateCell As Range) As Boolean
    ' Determines if a date was manually entered vs auto-filled
    
    ' METHOD 1: Check for auto-fill marker
    If HasAutoFillMarker(dateCell) Then
        DateWasManuallyEntered = False
        Exit Function
    End If
    
    ' METHOD 2: Check if cell has a formula
    If dateCell.HasFormula Then
        DateWasManuallyEntered = False
        Exit Function
    End If
    
    ' METHOD 3: Check if cell is empty
    If IsEmpty(dateCell.Value) Or dateCell.Value = "" Then
        DateWasManuallyEntered = False
        Exit Function
    End If
    
    ' METHOD 4: Check time component (dates with time = manual)
    If IsDate(dateCell.Value) Then
        Dim dt As Date
        dt = CDate(dateCell.Value)
        If dt - Int(dt) <> 0 Then
            DateWasManuallyEntered = True
            Exit Function
        End If
    End If
    
    ' METHOD 5: Has date but no auto marker = assume manual (preserve user data)
    If IsDate(dateCell.Value) And dateCell.Value <> 0 Then
        DateWasManuallyEntered = True
    Else
        DateWasManuallyEntered = False
    End If
End Function

Private Function HasAutoFillMarker(dateCell As Range) As Boolean
    ' Checks if cell has hidden [AUTO] marker
    On Error Resume Next
    
    If Not dateCell.Comment Is Nothing Then
        HasAutoFillMarker = (InStr(dateCell.Comment.Text, "[AUTO]") > 0)
    Else
        HasAutoFillMarker = False
    End If
    
    On Error GoTo 0
End Function

Private Sub MarkAsAutoFilled(dateCell As Range)
    ' Marks cell as auto-filled with hidden comment
    On Error Resume Next
    dateCell.Comment.Delete
    dateCell.AddComment "[AUTO]"
    dateCell.Comment.Visible = False
    On Error GoTo 0
End Sub

Private Sub ClearAutoFillMark(dateCell As Range)
    ' Removes auto-fill marker (marks as manual)
    On Error Resume Next
    dateCell.Comment.Delete
    On Error GoTo 0
End Sub

' ================================================================================
' SYSTEM SHEET DETECTION
' ================================================================================

Private Function IsSystemSheet(sheetName As String) As Boolean
    ' Returns True for system sheets that should be skipped
    Select Case sheetName
        Case "Scope_Template", "Task_Entry", "All_Tasks", "All_Tasks_Billing", _
             "Equipment Reference", "Apparatus_List_w_Hours", "Scope_Labor_Rates", _
             "Gantt_Template", "Project_Form", "All_Lists", "PowerBI_Data"
            IsSystemSheet = True
        Case Else
            IsSystemSheet = False
    End Select
End Function

' ================================================================================
' DIAGNOSTIC TOOLS
' ================================================================================

Public Sub CheckDateStatus()
    ' Shows detailed status of selected date cell
    
    Dim cell As Range
    Dim msg As String
    Dim statusCell As Range
    
    If Selection Is Nothing Or Selection.Cells.Count > 1 Then
        MsgBox "Please select a single date cell.", vbExclamation
        Exit Sub
    End If
    
    Set cell = Selection.Cells(1, 1)
    
    If cell.Column <> DATE_COL Then
        MsgBox "Please select a cell in column L (Date Completed).", vbExclamation
        Exit Sub
    End If
    
    Set statusCell = cell.Worksheet.Cells(cell.row, STATUS_COL)
    
    msg = "DATE STATUS REPORT" & vbCrLf & String(50, "=") & vbCrLf & vbCrLf
    msg = msg & "Cell: " & cell.Address & vbCrLf
    msg = msg & "Row: " & cell.row & vbCrLf
    msg = msg & "Status: " & statusCell.Value & vbCrLf
    msg = msg & "Date Value: " & cell.Value & vbCrLf & vbCrLf
    
    msg = msg & "CURRENT MODE: " & GetDateMode() & vbCrLf & vbCrLf
    
    If IsEmpty(cell.Value) Or cell.Value = "" Then
        msg = msg & "Date Status: EMPTY" & vbCrLf
        msg = msg & "Will auto-fill when status = COMPLETED (in Auto Mode)"
    ElseIf DateWasManuallyEntered(cell) Then
        msg = msg & "Date Status: MANUALLY ENTERED ?" & vbCrLf
        msg = msg & "This date is PROTECTED and will NOT be overwritten" & vbCrLf
        msg = msg & "Preserves across status changes"
    Else
        msg = msg & "Date Status: AUTO-FILLED" & vbCrLf
        msg = msg & "Will be cleared if status changes away from COMPLETED"
    End If
    
    MsgBox msg, vbInformation, "Date Status Check"
End Sub

Public Sub ShowModeHelp()
    ' Displays help information about Auto/Manual modes
    
    Dim msg As String
    
    msg = "DATE COMPLETION MODE HELP" & vbCrLf & String(50, "=") & vbCrLf & vbCrLf
    
    msg = msg & "AUTO MODE (Default)" & vbCrLf
    msg = msg & "--------------------" & vbCrLf
    msg = msg & "• Normal workflow - use 99% of the time" & vbCrLf
    msg = msg & "• Status ? COMPLETED: Auto-populate date" & vbCrLf
    msg = msg & "• Status ? Other: Auto-clear date" & vbCrLf
    msg = msg & "• Hands-free date tracking" & vbCrLf & vbCrLf
    
    msg = msg & "MANUAL MODE (Override)" & vbCrLf
    msg = msg & "--------------------" & vbCrLf
    msg = msg & "• For corrections and exceptions" & vbCrLf
    msg = msg & "• Auto-population SUSPENDED" & vbCrLf
    msg = msg & "• Can edit dates on COMPLETED rows only" & vbCrLf
    msg = msg & "• Manually entered dates are preserved" & vbCrLf & vbCrLf
    
    msg = msg & "TYPICAL USE CASE:" & vbCrLf
    msg = msg & "1. Row auto-filled with today's date" & vbCrLf
    msg = msg & "2. Realize it was completed yesterday" & vbCrLf
    msg = msg & "3. Switch to Manual Mode" & vbCrLf
    msg = msg & "4. Correct the date" & vbCrLf
    msg = msg & "5. Switch back to Auto Mode" & vbCrLf
    msg = msg & "6. Corrected date stays locked" & vbCrLf & vbCrLf
    
    msg = msg & "Current Mode: " & GetDateMode()
    
    MsgBox msg, vbInformation, "Mode Help"
End Sub


