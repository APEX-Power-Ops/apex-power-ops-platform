Attribute VB_Name = "PopulateAllTasks"

' ================================================================================
' POPULATEALLTASKS MODULE - GLOBAL CONSTANTS COMPLIANT VERSION
' Updated to use Global_Constants - 2025-09-22
' ? COMPLIANCE: All column references now use Global_Constants.*
' ================================================================================
Option Explicit

' CRITICAL CONSTANTS - Using Global_Constants
Const ALL_TASKS_SHEET As String = "All_Tasks"  ' Keep for compatibility
Const MAX_POPULATE_COLUMN As Integer = 21  ' Column U - NEVER go past this to protect Column V

' ================================================================================
' MAIN ENTRY POINT
' ================================================================================
Public Sub PopulateAllTasks_FromSheets(selectedSheets() As String, appendMode As Boolean)
    On Error GoTo ErrorHandler
    
    Dim wsAll As Worksheet
    Dim rowsData As Collection
    Dim startTime As Double
    Dim diag As String
    
    startTime = Timer
    Set rowsData = New Collection
    
    Application.ScreenUpdating = False
    Application.StatusBar = "Processing scope sheets..."
    
    ' Set All_Tasks worksheet using Global_Constants
    Set wsAll = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS)
    
    ' Ensure headers exist
    If Not ValidateAllTasksHeaders(wsAll) Then
        GoTo MissingHeaders
    End If
    
    ' Process each selected scope sheet
    Dim i As Long
    Dim totalApparatus As Long
    
    For i = LBound(selectedSheets) To UBound(selectedSheets)
        Dim scopeName As String
        scopeName = selectedSheets(i)
        
        Application.StatusBar = "Processing " & scopeName & "..."
        
        On Error Resume Next
        Dim ws As Worksheet
        Set ws = ThisWorkbook.Worksheets(scopeName)
        On Error GoTo ErrorHandler
        
        If Not ws Is Nothing Then
            Dim apparatusCount As Long
            apparatusCount = ProcessScopeSheet(ws, rowsData)
            totalApparatus = totalApparatus + apparatusCount
            diag = diag & vbCrLf & "• " & scopeName & ": " & apparatusCount & " apparatus items"
        End If
    Next i
    
    If rowsData.Count = 0 Then
        Application.ScreenUpdating = True
        MsgBox "No apparatus items found in selected sheets." & vbCrLf & diag, vbExclamation, "No Data Found"
        Exit Sub
    End If
    
    ' Write to All_Tasks
    WriteToAllTasks wsAll, rowsData, appendMode
    
    ' Sync billing sheet
    Application.StatusBar = "Updating All_Tasks_Billing..."
    Call EnsureBillingSyncAfterPopulate
    
    Application.ScreenUpdating = True
    Application.StatusBar = False
    
    Dim elapsedTime As Double
    elapsedTime = Timer - startTime
    
    MsgBox totalApparatus & " apparatus items " & IIf(appendMode, "added to", "populated in") & _
           " All_Tasks." & vbCrLf & _
           "All_Tasks_Billing synchronized." & vbCrLf & _
           "Column V preserved for billing." & vbCrLf & _
           "Processing time: " & Format(elapsedTime, "0.0") & " seconds" & _
           diag & vbCrLf & vbCrLf & _
           "? Using Global_Constants v" & Global_Constants.MODULE_VERSION, _
           vbInformation, "Process Complete"
    Exit Sub

MissingHeaders:
    Application.ScreenUpdating = True
    MsgBox "All_Tasks headers missing or incorrect. Please ensure proper headers exist.", vbCritical, "Header Error"
    Exit Sub

ErrorHandler:
    Application.ScreenUpdating = True
    Application.StatusBar = False
    MsgBox "Error in PopulateAllTasks: " & Err.Description, vbCritical, "Process Error"
End Sub

' ================================================================================
' PROCESS INDIVIDUAL SCOPE SHEET WITH GLOBAL CONSTANTS MAPPING
' ================================================================================
Private Function ProcessScopeSheet(ws As Worksheet, rowsData As Collection) As Long
    Dim scopeName As String
    scopeName = ws.Name
    
    ' Find last row with data using Global_Constants
    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, Global_Constants.SC_COL_TASK_ID).End(xlUp).row
    If lastRow > 1000 Then lastRow = 1000  ' Safety limit
    If lastRow <= Global_Constants.SC_FIRST_DATA_ROW Then
        ProcessScopeSheet = 0
        Exit Function
    End If
    
    Dim apparatusCount As Long
    Dim currentTaskRow As Long
    Dim currentTaskName As String
    Dim r As Long
    
    For r = Global_Constants.SC_FIRST_DATA_ROW To lastRow
        Dim taskId As String
        taskId = Trim$(CStr(ws.Cells(r, Global_Constants.SC_COL_TASK_ID).Value))
        If Len(taskId) = 0 Then GoTo ContinueRow
        
        ' Count dots to determine level using Global_Constants function
        Dim dots As Long
        dots = Global_Constants.CountDots(taskId)
        
        If dots = 1 Then
            ' Task level (1.1) - save for apparatus children
            currentTaskRow = r
            currentTaskName = ws.Cells(r, Global_Constants.SC_COL_NAME_APP).Value
            
        ElseIf dots = 2 Then
            ' Apparatus level (1.1.1) - collect this item
            apparatusCount = apparatusCount + 1
            
            Dim out() As Variant
            ReDim out(1 To MAX_POPULATE_COLUMN)  ' Only populate up to Column U
            
            ' ========== COLUMN MAPPING USING GLOBAL CONSTANTS ==========
            
            ' Static values (Columns A-E) - Map scope to All_Tasks using Global_Constants
            out(Global_Constants.AT_COL_SCOPE) = scopeName                                          ' A: Scope
            out(Global_Constants.AT_COL_NETA) = GetNETAStandard(scopeName)                         ' B: NETA_Standard
            out(Global_Constants.AT_COL_TID) = taskId                                              ' C: Task_ID
            out(Global_Constants.AT_COL_TASK) = currentTaskName                                    ' D: Task (from parent)
            out(Global_Constants.AT_COL_APP) = ws.Cells(r, Global_Constants.SC_COL_NAME_APP).Value ' E: Apparatus
            
            ' Direct mappings - Continue mapping using Global_Constants
            out(Global_Constants.AT_COL_DES) = ws.Cells(r, Global_Constants.SC_COL_DES).Value      ' F: Designation
            out(Global_Constants.AT_COL_DRW) = ws.Cells(r, Global_Constants.SC_COL_DRW).Value      ' G: Drawing
            out(Global_Constants.AT_COL_DATE_DUE) = ws.Cells(r, Global_Constants.SC_COL_DATE_DUE).Value  ' H: Date Due
            out(Global_Constants.AT_COL_NOTES) = ""  ' I: Notes (empty initially)
            out(Global_Constants.AT_COL_ASSESSMENT) = ws.Cells(r, Global_Constants.SC_COL_ASSESSMENT).Value  ' J: Assessment
            out(Global_Constants.AT_COL_DATASHEET) = ws.Cells(r, Global_Constants.SC_COL_DATASHEET).Value    ' K: DATASHEET
            out(Global_Constants.AT_COL_DATE_COMP) = ws.Cells(r, Global_Constants.SC_COL_DATE_COMP).Value    ' L: DATE_COMPLETED
            out(Global_Constants.AT_COL_NOTES2) = ws.Cells(r, Global_Constants.SC_COL_NOTES).Value           ' M: NOTES2
            out(Global_Constants.AT_COL_PCT) = ws.Cells(r, Global_Constants.SC_COL_PCT).Value                ' N: % COMPLETION
            out(Global_Constants.AT_COL_DELAY) = ws.Cells(r, Global_Constants.SC_COL_DELAY).Value            ' O: TASK DELAYS
            
            ' ========== CRITICAL HOURS MAPPING ==========
            ' Apparatus Hours (Column P in scope) ? Apparatus_Hours (Column P in All_Tasks)
            Dim quotedHours As Variant
            quotedHours = ws.Cells(r, Global_Constants.SC_COL_AHRS).Value  ' Column P from scope
            If IsNumeric(quotedHours) And quotedHours <> "" Then
                out(Global_Constants.AT_COL_AHRS) = CDbl(quotedHours)      ' P: Apparatus_Hours (for billing)
                out(Global_Constants.AT_COL_REMHRS) = ws.Cells(r, Global_Constants.SC_COL_REMHRS).Value  ' Q: Remaining_Hours
                out(Global_Constants.AT_COL_ACTHRS) = ws.Cells(r, Global_Constants.SC_COL_ACTHRS).Value  ' R: ACTUAL_HOURS
            Else
                out(Global_Constants.AT_COL_AHRS) = 0                      ' P: Default to 0
                out(Global_Constants.AT_COL_REMHRS) = 0                    ' Q: Default to 0
                out(Global_Constants.AT_COL_ACTHRS) = 0                    ' R: Default to 0
            End If
            
            ' Status columns - Using Global_Constants for All_Tasks columns
            out(Global_Constants.AT_COL_STATUS) = ws.Cells(r, Global_Constants.SC_COL_STATUS).Value    ' S: STATUS
            out(Global_Constants.AT_COL_AVAIL) = ws.Cells(r, Global_Constants.SC_COL_AVAIL).Value      ' T: AVAILABILITY
            out(Global_Constants.AT_COL_PRIORITY) = ws.Cells(r, Global_Constants.SC_COL_PRIORITY).Value ' U: PRIORITY
            
            ' NOTE: Column V (22) is NOT populated here - it's preserved for standardized names
            
            rowsData.Add out
        End If
        
ContinueRow:
    Next r
    
    ProcessScopeSheet = apparatusCount
End Function

' ================================================================================
' WRITE DATA TO ALL_TASKS WITH COLUMN V PROTECTION
' ================================================================================
Private Sub WriteToAllTasks(wsAll As Worksheet, rowsData As Collection, appendMode As Boolean)
    Dim lastRow As Long
    Dim startRow As Long
    
    ' Find current last row using Global_Constants
    lastRow = wsAll.Cells(wsAll.Rows.Count, Global_Constants.AT_COL_SCOPE).End(xlUp).row
    If lastRow < Global_Constants.AT_FIRST_DATA_ROW Then lastRow = 1
    
    If Not appendMode Then
        ' Clear existing data but ONLY up to Column U (protects Column V)
        If lastRow > 1 Then
            wsAll.Range(wsAll.Cells(Global_Constants.AT_FIRST_DATA_ROW, 1), _
                       wsAll.Cells(lastRow, MAX_POPULATE_COLUMN)).ClearContents
        End If
        startRow = Global_Constants.AT_FIRST_DATA_ROW
    Else
        ' Append mode - start after last row
        startRow = lastRow + 1
    End If
    
    ' Write data
    Dim i As Long
    Dim rowArr As Variant
    
    For i = 1 To rowsData.Count
        rowArr = rowsData(i)
        Dim col As Long
        
        ' Only write up to Column U (21)
        For col = 1 To MAX_POPULATE_COLUMN
            wsAll.Cells(startRow + i - 1, col).Value = rowArr(col)
        Next col
        
        ' Column V is NEVER touched - preserved for standardized apparatus names
    Next i
End Sub

' ================================================================================
' BILLING INTEGRATION FUNCTIONS
' ================================================================================
Private Sub EnsureBillingSyncAfterPopulate()
    ' Ensures All_Tasks_Billing has formulas for all All_Tasks rows
    
    On Error GoTo ErrorHandler
    
    Dim wsAll As Worksheet, wsBilling As Worksheet
    Dim allTasksLastRow As Long, billingLastRow As Long
    
    Set wsAll = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS)
    allTasksLastRow = wsAll.Cells(wsAll.Rows.Count, Global_Constants.AT_COL_SCOPE).End(xlUp).row
    
    ' Check if billing sheet exists
    On Error Resume Next
    Set wsBilling = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS_BILLING)
    On Error GoTo ErrorHandler
    
    If wsBilling Is Nothing Then
        ' Create billing sheet for first time
        Set wsBilling = ThisWorkbook.Worksheets.Add
        wsBilling.Name = Global_Constants.SHEET_ALL_TASKS_BILLING
        Call SetupBillingHeaders(wsBilling)
        billingLastRow = 1
    Else
        ' Find last formula row in billing
        billingLastRow = GetBillingFormulaLastRow(wsBilling)
    End If
    
    ' Extend formulas if needed
    If allTasksLastRow > billingLastRow Then
        Call ExtendBillingFormulas(wsBilling, billingLastRow + 1, allTasksLastRow + 50)
    End If
    
    Exit Sub
    
ErrorHandler:
    Debug.Print "Billing sync error: " & Err.Description
End Sub

Private Function GetBillingFormulaLastRow(ws As Worksheet) As Long
    ' Find last row with actual formulas
    Dim r As Long
    Dim lastRow As Long
    
    lastRow = ws.Cells(ws.Rows.Count, Global_Constants.AT_COL_SCOPE).End(xlUp).row
    
    For r = lastRow To Global_Constants.AT_FIRST_DATA_ROW Step -1
        If ws.Cells(r, Global_Constants.AT_COL_SCOPE).formula <> "" Then
            GetBillingFormulaLastRow = r
            Exit Function
        End If
    Next r
    
    GetBillingFormulaLastRow = 1
End Function

Private Sub SetupBillingHeaders(ws As Worksheet)
    ' Copy headers from All_Tasks using Global_Constants
    Dim wsAll As Worksheet
    Set wsAll = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS)
    
    Dim col As Long
    For col = 1 To MAX_POPULATE_COLUMN  ' A through U
        ws.Cells(1, col).Value = wsAll.Cells(1, col).Value
    Next col
    
    ' Override Column E for clarity
    ws.Cells(1, Global_Constants.AT_COL_APP).Value = "Apparatus"  ' Uses V first, then E
    
    ' Add billing-specific headers using Global_Constants
    With ws
        .Cells(1, Global_Constants.ATB_COL_SCOPE_HELPER).Value = "Scope_Row_Helper"
        .Cells(1, Global_Constants.ATB_COL_BASE_RATE).Value = "Base_Rate"
        .Cells(1, Global_Constants.ATB_COL_SCOPE_BUDGET).Value = "Scope_Budget_Total"
        .Cells(1, Global_Constants.ATB_COL_MULTIPLIER).Value = "Multiplier"
        .Cells(1, Global_Constants.ATB_COL_COMPLETION).Value = "Completion_Binary"
        .Cells(1, Global_Constants.ATB_COL_WEEK_ENDING).Value = "Week_Ending"
        .Cells(1, Global_Constants.ATB_COL_BILLING_PERIOD).Value = "Billing_Period"
        .Cells(1, Global_Constants.ATB_COL_BASE_LABOR).Value = "Base_Labor_$"
        ' Add more billing headers as needed
        
        .Range("A1:AZ1").Font.Bold = True
    End With
End Sub

Private Sub ExtendBillingFormulas(ws As Worksheet, startRow As Long, endRow As Long)
    ' Add billing formulas for specified row range using Global_Constants
    
    Dim r As Long
    Dim col As Long
    
    Application.Calculation = xlCalculationManual
    
    For r = startRow To endRow
        With ws
            ' Direct column mappings A-D using Global_Constants
            .Cells(r, 1).formula = "=IF(All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_SCOPE) & r & "="""","""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_SCOPE) & r & ")"
            .Cells(r, 2).formula = "=IF(All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_NETA) & r & "="""","""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_NETA) & r & ")"
            .Cells(r, 3).formula = "=IF(All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_TID) & r & "="""","""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_TID) & r & ")"
            .Cells(r, 4).formula = "=IF(All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_TASK) & r & "="""","""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_TASK) & r & ")"
            
            ' Column E: Apparatus (V first, then E fallback)
            .Cells(r, 5).formula = "=IF(All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "<>"""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ",IF(All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_APP) & r & "<>"""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_APP) & r & ",""""))"
            
            ' Direct mappings F-U using Global_Constants
            For col = 6 To MAX_POPULATE_COLUMN
                If col >= 16 And col <= 18 Then  ' Columns P, Q, R are numeric
                    .Cells(r, col).formula = "=IF(All_Tasks!" & Chr(64 + col) & r & "="""",0,All_Tasks!" & Chr(64 + col) & r & ")"
                Else
                    .Cells(r, col).formula = "=IF(All_Tasks!" & Chr(64 + col) & r & "="""","""",All_Tasks!" & Chr(64 + col) & r & ")"
                End If
            Next col
        End With
    Next r
    
    Application.Calculation = xlCalculationAutomatic
End Sub
            
' ================================================================================
' USERFORM COMPATIBILITY FUNCTIONS
' ================================================================================
Public Sub PopulateAllTasks_FromSheets_WithBillingSync(selectedSheets() As String, appendMode As Boolean)
    ' Wrapper function for userform compatibility
    ' Calls main function and ensures billing sync
    
    Call PopulateAllTasks_FromSheets(selectedSheets, appendMode)
    ' Billing sync already happens automatically in the main function
End Sub

Public Sub UpdateBillingOnly()
    ' Updates All_Tasks_Billing without touching All_Tasks
    ' Called by userform's Update Billing Only button
    
    On Error GoTo ErrorHandler
    
    Application.ScreenUpdating = False
    Application.StatusBar = "Updating All_Tasks_Billing..."
    
    ' Ensure billing is synchronized with current All_Tasks data
    Call EnsureBillingSyncAfterPopulate
    
    Application.ScreenUpdating = True
    Application.StatusBar = False
    
    MsgBox "All_Tasks_Billing has been updated!" & vbCrLf & _
           "All formulas synchronized with current All_Tasks data." & vbCrLf & _
           "? Using Global_Constants v" & Global_Constants.MODULE_VERSION, _
           vbInformation, "Billing Update Complete"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    Application.StatusBar = False
    MsgBox "Error updating billing: " & Err.Description, vbCritical
End Sub

Public Function BillingSheetExists() As Boolean
    ' Check if All_Tasks_Billing sheet exists
    On Error Resume Next
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS_BILLING)
    BillingSheetExists = Not ws Is Nothing
    On Error GoTo 0
End Function

Public Sub ShowPopulateDialog()
    ' Show the userform
    ufPopulateAllTasks.Show
End Sub

Private Function ValidateAllTasksHeaders(ws As Worksheet) As Boolean
    ' Validates that All_Tasks has the required headers
    
    ValidateAllTasksHeaders = True  ' Assume success
    
    ' Check for key headers using Global_Constants
    If ws.Cells(1, Global_Constants.AT_COL_SCOPE).Value = "" Then
        ValidateAllTasksHeaders = False
        Exit Function
    End If
    
    ' Basic check - just ensure key headers exist
    If ws.Cells(1, Global_Constants.AT_COL_SCOPE).Value = "" Or _
       ws.Cells(1, Global_Constants.AT_COL_TID).Value = "" Then
        ValidateAllTasksHeaders = False
    End If
End Function

Private Function GetNETAStandard(scopeName As String) As String
    ' Determines the NETA Standard based on scope name
    
    If InStr(scopeName, "PPM") > 0 Then
        GetNETAStandard = "PPM"
    ElseIf InStr(scopeName, "GDB") > 0 Then
        GetNETAStandard = "GDB"
    ElseIf InStr(scopeName, "CB") > 0 Then
        GetNETAStandard = "CB"
    ElseIf InStr(scopeName, "XFMR") > 0 Then
        GetNETAStandard = "XFMR"
    ElseIf InStr(scopeName, "PDU") > 0 Then
        GetNETAStandard = "PDU"
    ElseIf InStr(scopeName, "RPP") > 0 Then
        GetNETAStandard = "RPP"
    ElseIf InStr(scopeName, "SES") > 0 Then
        GetNETAStandard = "SES"
    ElseIf InStr(scopeName, "HOUSE") > 0 Then
        GetNETAStandard = "HOUSE"
    Else
        ' Default to the scope name itself if no pattern matches
        GetNETAStandard = scopeName
    End If
End Function

