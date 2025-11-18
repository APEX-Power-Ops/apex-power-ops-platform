Attribute VB_Name = "Build_All"
' Updated to use Global_Constants DIRECTLY - 2025-09-22
' ? COMPLIANCE: NO LOCAL CONSTANTS - All references use Global_Constants.*

Option Explicit

' NO LOCAL CONSTANTS - Use Global_Constants directly


' ===== MAIN BUILD FUNCTION =====
Sub BuildAll()
    ' Get sheets using standardized names from Global_Constants
    Dim wsSrc As Worksheet, wsTpl As Worksheet, wsOut As Worksheet
    Set wsSrc = GetSheetStrict(Global_Constants.SHEET_TASK_ENTRY)
    Set wsTpl = GetSheetStrict(Global_Constants.SHEET_SCOPE_TEMPLATE)

    ' Get scope value from proper location using Global_Constants
    Dim scopeVal As String
    scopeVal = Trim(CStr(wsSrc.Cells(Global_Constants.TE_FIRST_DATA_ROW, Global_Constants.TE_COL_SCOPE).Value))
    If Len(scopeVal) = 0 Then
        MsgBox "Enter a Scope name in A2 first!", vbExclamation
        Exit Sub
    End If

    ' New sheet name
    Dim newName As String
    newName = SafeSheetName(scopeVal)
    If Len(newName) = 0 Then newName = "Scope_" & Format(Now, "yyyymmdd_hhnnss")

    Application.ScreenUpdating = False
    Application.DisplayAlerts = False

    ' Remove existing sheet if it exists
    Dim ex As Worksheet
    Set ex = GetSheet(ThisWorkbook, newName)
    If Not ex Is Nothing Then ex.Delete

    ' Clone the ENTIRE template
    wsTpl.Copy After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count)
    Set wsOut = ActiveSheet
    On Error Resume Next
    wsOut.Name = newName
    If Err.Number <> 0 Then
        Err.Clear
        wsOut.Name = Left(newName, 28) & "_" & Format(Now, "hhnnss")
    End If
    On Error GoTo 0

    ' Page setup
    On Error Resume Next
    Application.PrintCommunication = False
    With wsOut.PageSetup
        .Orientation = xlLandscape
        .PaperSize = xlPaperTabloid
        .Order = xlDownThenOver
        .CenterHorizontally = False
        .CenterVertically = False
        .Zoom = False
        .FitToPagesWide = 1
        .FitToPagesTall = False
    End With
    Application.PrintCommunication = True
    On Error GoTo 0

    ' Put SCOPE/NETA from Task_Entry into scope sheet header
    Dim netaTxt As String
    netaTxt = Trim(CStr(wsSrc.Cells(Global_Constants.TE_FIRST_DATA_ROW, Global_Constants.TE_COL_NETA).Value))
    
    With wsOut.Range(Global_Constants.SC_SCOPE_CELL)
        .Value = scopeVal
        .HorizontalAlignment = xlLeft
        On Error Resume Next: .InsertIndent 1: On Error GoTo 0
    End With
    With wsOut.Range(Global_Constants.SC_NETA_CELL)
        .Value = netaTxt
        .HorizontalAlignment = xlLeft
        On Error Resume Next: .InsertIndent 1: On Error GoTo 0
    End With

    ' Clear everything from row 8 onwards (keep headers and two template rows)
    wsOut.Rows("8:" & wsOut.Rows.Count).Delete
    
    ' IMPORTANT: Clear any content/formulas from the template rows (6 and 7)
    With wsOut.Rows(6)
        .ClearContents  ' This clears both values and formulas
    End With
    With wsOut.Rows(7)
        .ClearContents  ' This clears both values and formulas
    End With
    
    ' Start output at row 6 (will use row 6 for first parent, row 7+ for data)
    Dim outRow As Long: outRow = 6
    Dim lastRow As Long: lastRow = MaxLastDataRow(wsSrc, Global_Constants.TE_COL_TASK, Global_Constants.TE_COL_AHRS)

    Dim r As Long
    Dim srcTaskID As String, taskHdr As String, app As String, des As String, drw As String
    Dim ahrs As Variant
    Dim inGroup As Boolean: inGroup = False
    Dim firstDataRow As Long: firstDataRow = 6

    For r = Global_Constants.TE_FIRST_DATA_ROW To lastRow
        If CountNonBlank(wsSrc, r, Global_Constants.TE_COL_TASK, Global_Constants.TE_COL_AHRS) = 0 Then GoTo NextRow

        ' Read from Task_Entry
        srcTaskID = Trim(CStr(wsSrc.Cells(r, Global_Constants.TE_COL_TID).Value))
        taskHdr = Trim(CStr(wsSrc.Cells(r, Global_Constants.TE_COL_TASK).Value))
        app = Trim(CStr(wsSrc.Cells(r, Global_Constants.TE_COL_APP).Value))
        des = Trim(CStr(wsSrc.Cells(r, Global_Constants.TE_COL_DES).Value))
        drw = Trim(CStr(wsSrc.Cells(r, Global_Constants.TE_COL_DRW).Value))
        ahrs = wsSrc.Cells(r, Global_Constants.TE_COL_AHRS).Value

        ' PARENT row (Task text present) - uses row 6 template
        If Len(taskHdr) > 0 Then
            inGroup = True
            
            ' Need to insert a new row if not the first one
            If outRow > 6 Then
                ' Copy parent template format from row 6
                wsTpl.Rows(SC_TEMPLATE_PARENT_ROW).Copy
                wsOut.Rows(outRow).Insert Shift:=xlDown
            End If
            
            ' PRESERVE DATE FORMAT AND FILL COLOR from template
            Dim dateCompFormat As String
            Dim dateCompColor As Long
            dateCompFormat = wsOut.Cells(outRow, Global_Constants.SC_COL_DATE_COMP).NumberFormat
            On Error Resume Next
            dateCompColor = wsOut.Cells(outRow, Global_Constants.SC_COL_DATE_COMP).Interior.Color
            On Error GoTo 0
            
            ' Write parent row data
            With wsOut.Cells(outRow, Global_Constants.SC_COL_TASK_ID)
                .NumberFormat = "@"
                .Value = FirstTwoParts(srcTaskID)
            End With
            wsOut.Cells(outRow, Global_Constants.SC_COL_NAME_APP).Value = taskHdr
            
            ' Parent status formula
            wsOut.Cells(outRow, Global_Constants.SC_COL_STATUS).formula = _
                "=IF(AND(I" & outRow & "<>"""",N" & outRow & "<1,I" & outRow & "<TODAY()),""OVERDUE""," & _
                "IF(N" & outRow & "=1,""COMPLETED""," & _
                "IF(N" & outRow & "=0,""NOT STARTED""," & _
                "IF(AND(N" & outRow & ">0,N" & outRow & "<1),""IN PROGRESS"",""""))))"
            
            ' Parent date rollup formula
            wsOut.Cells(outRow, Global_Constants.SC_COL_DATE_DUE).formula = _
                "=IFERROR(IF(AGGREGATE(5,6,IF(LEFT(E" & (outRow + 1) & ":E200,LEN(E" & outRow & ")+1)=E" & outRow & "&""."",I" & (outRow + 1) & ":I200))>0,AGGREGATE(5,6,IF(LEFT(E" & (outRow + 1) & ":E200,LEN(E" & outRow & ")+1)=E" & outRow & "&""."",I" & (outRow + 1) & ":I200)),""""),"""")"
            
            ' Parent date completion - REAPPLY FORMAT AND COLOR AFTER FORMULA
            With wsOut.Cells(outRow, Global_Constants.SC_COL_DATE_COMP)
                .Clear
                .NumberFormat = dateCompFormat
                .Interior.Color = dateCompColor
                If wsOut.Range(Global_Constants.SC_MODE_TOGGLE_CELL).Value = "AUTO" Then
                    .formula = "=IF(B" & outRow & "=""COMPLETED"",NOW(),"""")"
                End If
            End With
            
            outRow = outRow + 1
        End If

        ' CHILD row (leaf) - uses row 7 template
        If inGroup And (Len(app & des & drw) > 0 Or Len(CStr(ahrs)) > 0) Then
            ' Copy child template format from row 7
            wsTpl.Rows(SC_TEMPLATE_CHILD_ROW).Copy
            wsOut.Rows(outRow).Insert Shift:=xlDown
            
            ' PRESERVE DATE FORMAT AND FILL COLOR from template
            dateCompFormat = wsOut.Cells(outRow, Global_Constants.SC_COL_DATE_COMP).NumberFormat
            On Error Resume Next
            dateCompColor = wsOut.Cells(outRow, Global_Constants.SC_COL_DATE_COMP).Interior.Color
            On Error GoTo 0

            ' Write child row data
            With wsOut.Cells(outRow, Global_Constants.SC_COL_TASK_ID)
                .NumberFormat = "@"
                .Value = srcTaskID
            End With

            wsOut.Cells(outRow, Global_Constants.SC_COL_NAME_APP).Value = app
            wsOut.Cells(outRow, Global_Constants.SC_COL_DES).Value = des
            wsOut.Cells(outRow, Global_Constants.SC_COL_DRW).Value = drw
            wsOut.Cells(outRow, Global_Constants.SC_COL_AHRS).Value = ahrs

            ' Child date completion - REAPPLY FORMAT AND COLOR AFTER FORMULA
            With wsOut.Cells(outRow, Global_Constants.SC_COL_DATE_COMP)
                .NumberFormat = dateCompFormat
                .Interior.Color = dateCompColor
                ' Leave empty - Worksheet_Change event will populate when status changes
            End With

            ' Child percentage formula
            wsOut.Cells(outRow, Global_Constants.SC_COL_PCT).formula = _
                "=IFERROR(IF(" & wsOut.Cells(outRow, Global_Constants.SC_COL_AHRS).Address(False, False) & ">0," & _
                "1-(" & wsOut.Cells(outRow, Global_Constants.SC_COL_REMHRS).Address(False, False) & "/" & _
                         wsOut.Cells(outRow, Global_Constants.SC_COL_AHRS).Address(False, False) & ")," & _
                "0),0)"

            outRow = outRow + 1
        End If
NextRow:
    Next r

    ' Header rollups
    Dim lastAnyRow As Long: lastAnyRow = outRow - 1
    Call BuildParentRollupFormulas(wsOut, firstDataRow, lastAnyRow)

    ' TOTALS band - completely clear the row first
    Dim totalsRow As Long: totalsRow = outRow
    
    ' Completely clear the totals row to remove any residual formulas/validation
    With wsOut.Rows(totalsRow)
        .ClearContents  ' This clears both values and formulas
        .Validation.Delete
        .Clear  ' This clears all formatting too
    End With
    
    ' Now copy only formatting from template
    wsTpl.Rows(SC_TEMPLATE_TOTALS_ROW).Copy
    wsOut.Rows(totalsRow).PasteSpecial xlPasteFormats
    Application.CutCopyMode = False

    ' Add TOTALS label and formulas
    With wsOut
        .Cells(totalsRow, Global_Constants.SC_COL_NOTES).Value = "TOTALS"
        Call BuildTotalsFormulas(wsOut, totalsRow, firstDataRow, lastAnyRow)
    End With

    ' Apply data validation - ONLY up to last data row (not including totals row)
    Call ApplyDataValidationToNewSheet(wsOut, lastAnyRow)
    
    ' Final cleanup: Ensure no validation exists on or after the totals row
    On Error Resume Next
    Dim cleanRow As Long
    For cleanRow = totalsRow To totalsRow + 10
        wsOut.Rows(cleanRow).Validation.Delete
    Next cleanRow
    On Error GoTo 0

    ' Clean up stray borders
    Call CleanupStrayBorders(wsOut, totalsRow)

    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    
    ' Add mode toggle button
    Call AddModeToggleButtonToSheet(wsOut)
    
    MsgBox "Scope sheet '" & newName & "' created successfully!" & vbCrLf & _
           "Row 5: Headers preserved" & vbCrLf & _
           "Row 6: Parent template used" & vbCrLf & _
           "Row 7: Child template used", vbInformation
End Sub

' ===== FIX EXISTING SHEETS FUNCTION =====
Sub FixExistingSheets()
    ' Updates all existing scope sheets to fix issues
    
    Dim ws As Worksheet
    Dim wsTpl As Worksheet
    Dim fixedCount As Long
    Dim errorCount As Long
    Dim skippedSheets As String
    Dim processedSheets As String
    Dim identifiedSheets As String
    
    ' Get template sheet
    Set wsTpl = GetSheet(ThisWorkbook, Global_Constants.SHEET_SCOPE_TEMPLATE)
    If wsTpl Is Nothing Then
        MsgBox "Error: " & Global_Constants.SHEET_SCOPE_TEMPLATE & " not found!", vbCritical
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    Debug.Print "========================================="
    Debug.Print "STARTING FixExistingSheets at " & Now
    Debug.Print "========================================="
    
    For Each ws In ThisWorkbook.Worksheets
        
        Debug.Print vbCrLf & "Checking: " & ws.Name
        
        ' Skip system sheets
        If ws.Name = Global_Constants.SHEET_TASK_ENTRY Or _
           ws.Name = Global_Constants.SHEET_ALL_TASKS Or _
           ws.Name = Global_Constants.SHEET_ALL_TASKS_BILLING Or _
           ws.Name = Global_Constants.SHEET_ALL_LISTS Or _
           ws.Name = Global_Constants.SHEET_GANTT_TEMPLATE Or _
           ws.Name = Global_Constants.SHEET_SCOPE_LABOR_RATES Then
            Debug.Print "  ? System sheet - skipping"
            GoTo NextSheet
        End If
        
        ' Check if this is a scope sheet
        If IsScopeSheetByContent(ws) Then
            identifiedSheets = identifiedSheets & ws.Name & ", "
            Debug.Print "  ? Identified as SCOPE SHEET - processing..."
            
            On Error Resume Next
            
            ' Apply all fixes
            Call FixSingleExistingSheetWithGlobalConstants(ws, wsTpl)
            
            If Err.Number = 0 Then
                fixedCount = fixedCount + 1
                processedSheets = processedSheets & ws.Name & vbCrLf
                Debug.Print "    SUCCESS - Sheet updated"
            Else
                errorCount = errorCount + 1
                skippedSheets = skippedSheets & ws.Name & " - Error: " & Err.Description & vbCrLf
                Debug.Print "    ERROR - " & Err.Description
                Err.Clear
            End If
            On Error GoTo 0
        End If
        
NextSheet:
    Next ws
    
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    
    Dim msg As String
    msg = "FixExistingSheets Complete!" & vbCrLf & vbCrLf
    msg = msg & "Successfully updated: " & fixedCount & " sheets" & vbCrLf
    
    If Len(processedSheets) > 0 Then
        msg = msg & vbCrLf & "Updated sheets:" & vbCrLf & processedSheets
    End If
    
    If errorCount > 0 Then
        msg = msg & vbCrLf & "Errors: " & errorCount & vbCrLf & skippedSheets
    End If
    
    MsgBox msg, vbInformation, "Scope Sheets Updated"
End Sub

' ===== TEST FUNCTION FOR VALIDATION CLEARING =====
Sub TestNuclearValidationClear()
    ' Test function to completely clear validation from active sheet
    
    Dim ws As Worksheet
    Set ws = ActiveSheet
    
    ' Show current state
    MsgBox "Testing validation clear on: " & ws.Name & vbCrLf & _
           "Click OK to proceed with nuclear clear", vbInformation
    
    ' NUCLEAR OPTION - Clear ALL validation from entire sheet
    On Error Resume Next
    ws.Cells.Validation.Delete
    On Error GoTo 0
    
    ' Find TOTALS row for reference
    Dim totalsRow As Long
    totalsRow = FindTotalsRow(ws)
    
    If totalsRow > 0 Then
        ' Extra aggressive cleanup from TOTALS row down
        On Error Resume Next
        ws.Range("A" & totalsRow & ":Z" & ws.Rows.Count).Validation.Delete
        On Error GoTo 0
        
        MsgBox "Nuclear clear complete!" & vbCrLf & _
               "TOTALS found at row: " & totalsRow & vbCrLf & _
               "All validation removed from entire sheet", vbInformation
    Else
        MsgBox "Nuclear clear complete!" & vbCrLf & _
               "No TOTALS row found" & vbCrLf & _
               "All validation removed from entire sheet", vbInformation
    End If
End Sub

' ===== POPULATE ALL_TASKS FUNCTION =====
Sub PopulateAllTasks()
    ' Populates All_Tasks sheet from all scope sheets
    
    Dim wsAllTasks As Worksheet, ws As Worksheet
    Dim lastRow As Long, currentRow As Long, targetRow As Long
    
    Set wsAllTasks = GetSheet(ThisWorkbook, Global_Constants.SHEET_ALL_TASKS)
    If wsAllTasks Is Nothing Then
        MsgBox "All_Tasks sheet not found!", vbCritical
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    
    ' Clear existing data (keep headers)
    lastRow = wsAllTasks.Cells(wsAllTasks.Rows.Count, Global_Constants.AT_COL_SCOPE).End(xlUp).row
    If lastRow > Global_Constants.AT_FIRST_DATA_ROW Then
        wsAllTasks.Rows(Global_Constants.AT_FIRST_DATA_ROW & ":" & lastRow).Delete
    End If
    
    targetRow = Global_Constants.AT_FIRST_DATA_ROW
    
    ' Loop through all scope sheets
    For Each ws In ThisWorkbook.Worksheets
        If IsScopeSheetByContent(ws) And ws.Name <> Global_Constants.SHEET_SCOPE_TEMPLATE Then
            ' Data starts at row 6 in scope sheets
            lastRow = ws.Cells(ws.Rows.Count, Global_Constants.SC_COL_TASK_ID).End(xlUp).row
            
            For currentRow = 6 To lastRow  ' Start from row 6 (first data row)
                Dim taskId As String
                taskId = Trim(CStr(ws.Cells(currentRow, Global_Constants.SC_COL_TASK_ID).Value))
                
                If Len(taskId) > 0 And taskId <> "TOTALS" Then
                    ' Copy data using correct column mapping
                    With wsAllTasks
                        .Cells(targetRow, Global_Constants.AT_COL_SCOPE).Value = ws.Range(Global_Constants.SC_SCOPE_CELL).Value
                        .Cells(targetRow, Global_Constants.AT_COL_NETA).Value = ws.Range(Global_Constants.SC_NETA_CELL).Value
                        .Cells(targetRow, Global_Constants.AT_COL_TID).Value = taskId
                        .Cells(targetRow, Global_Constants.AT_COL_TASK).Value = ws.Cells(currentRow, Global_Constants.SC_COL_NAME_APP).Value
                        .Cells(targetRow, Global_Constants.AT_COL_APP).Value = ws.Cells(currentRow, Global_Constants.SC_COL_NAME_APP).Value
                        .Cells(targetRow, Global_Constants.AT_COL_DES).Value = ws.Cells(currentRow, Global_Constants.SC_COL_DES).Value
                        .Cells(targetRow, Global_Constants.AT_COL_DRW).Value = ws.Cells(currentRow, Global_Constants.SC_COL_DRW).Value
                        .Cells(targetRow, Global_Constants.AT_COL_DATE_DUE).Value = ws.Cells(currentRow, Global_Constants.SC_COL_DATE_DUE).Value
                        .Cells(targetRow, Global_Constants.AT_COL_ASSESSMENT).Value = ws.Cells(currentRow, Global_Constants.SC_COL_ASSESSMENT).Value
                        .Cells(targetRow, Global_Constants.AT_COL_DATASHEET).Value = ws.Cells(currentRow, Global_Constants.SC_COL_DATASHEET).Value
                        .Cells(targetRow, Global_Constants.AT_COL_DATE_COMP).Value = ws.Cells(currentRow, Global_Constants.SC_COL_DATE_COMP).Value
                        .Cells(targetRow, Global_Constants.AT_COL_PCT).Value = ws.Cells(currentRow, Global_Constants.SC_COL_PCT).Value
                        .Cells(targetRow, Global_Constants.AT_COL_DELAY).Value = ws.Cells(currentRow, Global_Constants.SC_COL_DELAY).Value
                        .Cells(targetRow, Global_Constants.AT_COL_AHRS).Value = ws.Cells(currentRow, Global_Constants.SC_COL_AHRS).Value
                        .Cells(targetRow, Global_Constants.AT_COL_REMHRS).Value = ws.Cells(currentRow, Global_Constants.SC_COL_REMHRS).Value
                        .Cells(targetRow, Global_Constants.AT_COL_ACTHRS).Value = ws.Cells(currentRow, Global_Constants.SC_COL_ACTHRS).Value
                        .Cells(targetRow, Global_Constants.AT_COL_STATUS).Value = ws.Cells(currentRow, Global_Constants.SC_COL_STATUS).Value
                        .Cells(targetRow, Global_Constants.AT_COL_AVAIL).Value = ws.Cells(currentRow, Global_Constants.SC_COL_AVAIL).Value
                        .Cells(targetRow, Global_Constants.AT_COL_PRIORITY).Value = ws.Cells(currentRow, Global_Constants.SC_COL_PRIORITY).Value
                    End With
                    
                    targetRow = targetRow + 1
                End If
            Next currentRow
        End If
    Next ws
    
    Application.ScreenUpdating = True
    
    MsgBox "All_Tasks populated!" & vbCrLf & _
           "Processed " & (targetRow - Global_Constants.AT_FIRST_DATA_ROW) & " records.", vbInformation
End Sub

' ============================================================================
' HELPER FUNCTIONS
' ============================================================================

Private Function GetSheet(ByVal wb As Workbook, ByVal Name As String) As Worksheet
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = wb.Worksheets(Name)
    On Error GoTo 0
    Set GetSheet = ws
End Function

Private Function GetSheetStrict(ByVal Name As String) As Worksheet
    Dim ws As Worksheet
    Set ws = GetSheet(ThisWorkbook, Name)
    If ws Is Nothing Then Err.Raise vbObjectError + 513, , "Sheet not found: '" & Name & "'"
    Set GetSheetStrict = ws
End Function

Private Function SafeSheetName(ByVal s As String) As String
    Dim bad, j As Long
    bad = Array("\", "/", ":", "*", "?", """", "<", ">", "|", "[", "]")
    For j = LBound(bad) To UBound(bad)
        s = Replace(s, bad(j), "_")
    Next j
    s = Trim(s)
    If Len(s) = 0 Then s = "Scope"
    If Len(s) > 31 Then s = Left(s, 31)
    SafeSheetName = s
End Function

Private Function MaxLastDataRow(ByVal ws As Worksheet, ByVal firstCol As Long, ByVal lastCol As Long) As Long
    Dim c As Long, m As Long, r As Long
    For c = firstCol To lastCol
        r = ws.Cells(ws.Rows.Count, c).End(xlUp).row
        If r > m Then m = r
    Next c
    MaxLastDataRow = m
End Function

Private Function CountNonBlank(ByVal ws As Worksheet, ByVal rowN As Long, ByVal firstCol As Long, ByVal lastCol As Long) As Long
    CountNonBlank = Application.WorksheetFunction.CountA(ws.Range(ws.Cells(rowN, firstCol), ws.Cells(rowN, lastCol)))
End Function

Private Function FirstTwoParts(ByVal s As String) As String
    Dim p As Long, q As Long
    p = InStr(1, s, ".")
    If p = 0 Then
        FirstTwoParts = s
        Exit Function
    End If
    q = InStr(p + 1, s, ".")
    If q = 0 Then
        FirstTwoParts = s
    Else
        FirstTwoParts = Left(s, q - 1)
    End If
End Function

Private Function IsScopeSheetByContent(ws As Worksheet) As Boolean
    ' Special handling for Scope_Template
    If ws.Name = Global_Constants.SHEET_SCOPE_TEMPLATE Then
        IsScopeSheetByContent = True
        Exit Function
    End If
    
    ' Check by CodeName pattern
    If Left(ws.codeName, 6) = "Scope_" Then
        IsScopeSheetByContent = True
        Exit Function
    End If
    
    On Error Resume Next
    
    ' Check for key headers in row 5 (the actual header row)
    Dim hasTaskID As Boolean, hasStatus As Boolean, hasPct As Boolean
    
    Dim taskIDHeader As String
    taskIDHeader = UCase$(Trim$(CStr(ws.Cells(SC_HEADER_ROW, Global_Constants.SC_COL_TASK_ID).Value)))
    hasTaskID = (InStr(taskIDHeader, "TASK") > 0 And InStr(taskIDHeader, "ID") > 0)
    
    Dim statusHeader As String
    statusHeader = UCase$(Trim$(CStr(ws.Cells(SC_HEADER_ROW, Global_Constants.SC_COL_STATUS).Value)))
    hasStatus = (InStr(statusHeader, "STATUS") > 0)
    
    Dim pctHeader As String
    pctHeader = UCase$(Trim$(CStr(ws.Cells(SC_HEADER_ROW, Global_Constants.SC_COL_PCT).Value)))
    hasPct = (InStr(pctHeader, "COMPLETION") > 0 Or InStr(pctHeader, "%") > 0)
    
    ' Also check for scope name in G4
    Dim hasScopeCell As Boolean
    hasScopeCell = (Len(Trim$(CStr(ws.Range(Global_Constants.SC_SCOPE_CELL).Value))) > 0)
    
    On Error GoTo 0
    
    ' Need at least 3 out of 4 indicators
    Dim score As Long: score = 0
    If hasTaskID Then score = score + 1
    If hasStatus Then score = score + 1
    If hasPct Then score = score + 1
    If hasScopeCell Then score = score + 1
    
    IsScopeSheetByContent = (score >= 3)
End Function

' NEW HELPER: Find the TOTALS row in a worksheet
Private Function FindTotalsRow(ws As Worksheet) As Long
    Dim currentRow As Long
    Dim maxRow As Long
    maxRow = ws.Cells(ws.Rows.Count, SC_COL_TASK_ID).End(xlUp).row
    
    ' Look for "TOTALS" in the NOTES column
    For currentRow = 6 To maxRow + 10
        If UCase(Trim(ws.Cells(currentRow, SC_COL_NOTES).Value)) = "TOTALS" Then
            FindTotalsRow = currentRow
            Exit Function
        End If
    Next currentRow
    
    ' If not found, return 0
    FindTotalsRow = 0
End Function

' NEW HELPER: Remove validation from totals row down
Private Sub RemoveValidationFromTotalsDown(ws As Worksheet, totalsRow As Long)
    On Error Resume Next
    
    ' Clear validation from totals row down to row 100
    ' This matches the behavior in BuildAll
    Dim cleanRow As Long
    For cleanRow = totalsRow To totalsRow + 100
        ws.Rows(cleanRow).Validation.Delete
    Next cleanRow
    
    ' Alternative: Clear entire range at once (faster)
    ws.Range("A" & totalsRow & ":Z" & (totalsRow + 100)).Validation.Delete
    
    On Error GoTo 0
End Sub

' ============================================================================
' DATA VALIDATION FUNCTIONS
' ============================================================================

Private Sub ApplyDataValidationToNewSheet(ws As Worksheet, lastDataRow As Long)
    ' Apply validation to newly created sheet
    ' This is called by BuildAll after creating a new scope sheet
    
    ' Apply validation only to actual data rows (6 to lastDataRow)
    If lastDataRow >= 6 Then  ' Only apply if we have data rows
        Call ApplyStatusValidationWithGlobalConstants(ws, 6, lastDataRow)
        Call ApplyAvailabilityValidationWithGlobalConstants(ws, 6, lastDataRow)
        Call ApplyPriorityValidationWithGlobalConstants(ws, 6, lastDataRow)
        Call ApplyDateDueValidationWithGlobalConstants(ws, 6, lastDataRow)
        Call ApplyAssessmentValidationWithGlobalConstants(ws, 6, lastDataRow)
        Call ApplyDatasheetValidationWithGlobalConstants(ws, 6, lastDataRow)
    End If
End Sub

' UPDATED: Main function for fixing existing sheets
Private Sub FixSingleExistingSheetWithGlobalConstants(ws As Worksheet, wsTpl As Worksheet)
    ' Apply all fixes to an existing scope sheet
    
    ' First, find the TOTALS row
    Dim totalsRow As Long
    totalsRow = FindTotalsRow(ws)
    
    ' Apply fixes
    Call FixDateCompletionFormulasWithGlobalConstants(ws)
    Call ApplyDataValidationToExistingSheetWithGlobalConstants(ws)
    Call UpdateParentStatusFormulasWithGlobalConstants(ws)
    Call UpdatePercentageAndRollupFormulasWithGlobalConstants(ws)
    
    ' CRITICAL: Remove validation from totals row down (matching BuildAll behavior)
    If totalsRow > 0 Then
        Call RemoveValidationFromTotalsDown(ws, totalsRow)
    End If
    
    Call AddModeToggleButtonToSheet(ws)
End Sub

Private Sub FixDateCompletionFormulasWithGlobalConstants(ws As Worksheet)
    ' Fix date completion formulas and preserve formatting and color
    Dim currentRow As Long
    Dim maxRow As Long
    maxRow = ws.Cells(ws.Rows.Count, Global_Constants.SC_COL_TASK_ID).End(xlUp).row
    
    ' Get the date format and color from the template
    Dim dateCompFormat As String
    Dim dateCompColorParent As Long
    Dim dateCompColorChild As Long
    
    On Error Resume Next
    Dim wsTpl As Worksheet
    Set wsTpl = GetSheet(ThisWorkbook, Global_Constants.SHEET_SCOPE_TEMPLATE)
    If Not wsTpl Is Nothing Then
        ' Get format and color from parent template row
        dateCompFormat = wsTpl.Cells(SC_TEMPLATE_PARENT_ROW, Global_Constants.SC_COL_DATE_COMP).NumberFormat
        dateCompColorParent = wsTpl.Cells(SC_TEMPLATE_PARENT_ROW, Global_Constants.SC_COL_DATE_COMP).Interior.Color
        dateCompColorChild = wsTpl.Cells(SC_TEMPLATE_CHILD_ROW, Global_Constants.SC_COL_DATE_COMP).Interior.Color
    Else
        ' Use default date format if template not accessible
        dateCompFormat = "mm/dd/yyyy"
        dateCompColorParent = RGB(255, 255, 255) ' White
        dateCompColorChild = RGB(255, 255, 255) ' White
    End If
    On Error GoTo 0
    
    ' Ensure mode toggle exists
    If ws.Range(Global_Constants.SC_MODE_TOGGLE_CELL).Value = "" Then
        ws.Range(Global_Constants.SC_MODE_TOGGLE_CELL).Value = "AUTO"
    End If
    
    ' Start from row 6 (first data row)
    For currentRow = 6 To maxRow
        Dim taskId As String
        taskId = Trim(CStr(ws.Cells(currentRow, Global_Constants.SC_COL_TASK_ID).Value))
        
        If Len(taskId) > 0 And taskId <> "TOTALS" Then
            If CountDots(taskId) = 1 Then
                ' Parent row - apply all parent formulas
                With ws.Cells(currentRow, Global_Constants.SC_COL_DATE_COMP)
                    .NumberFormat = dateCompFormat
                    .Interior.Color = dateCompColorParent
                    .formula = "=IF(" & GetColumnLetter(Global_Constants.SC_COL_STATUS) & currentRow & "=""COMPLETED"",NOW(),"""")"
                End With
                
                ' Parent Date Due rollup formula
                ws.Cells(currentRow, Global_Constants.SC_COL_DATE_DUE).formula = _
                    "=IFERROR(IF(AGGREGATE(5,6,IF(LEFT(E" & (currentRow + 1) & ":E200,LEN(E" & currentRow & ")+1)=E" & currentRow & "&""."",I" & (currentRow + 1) & ":I200))>0,AGGREGATE(5,6,IF(LEFT(E" & (currentRow + 1) & ":E200,LEN(E" & currentRow & ")+1)=E" & currentRow & "&""."",I" & (currentRow + 1) & ":I200)),""""),"""")"
                
                ' Parent Status formula
                ws.Cells(currentRow, Global_Constants.SC_COL_STATUS).formula = _
                    "=IF(AND(I" & currentRow & "<>"""",N" & currentRow & "<1,I" & currentRow & "<TODAY()),""OVERDUE""," & _
                    "IF(N" & currentRow & "=1,""COMPLETED""," & _
                    "IF(N" & currentRow & "=0,""NOT STARTED""," & _
                    "IF(AND(N" & currentRow & ">0,N" & currentRow & "<1),""IN PROGRESS"",""""))))"
                
            ElseIf CountDots(taskId) > 1 Then
                ' Child row - only apply date completion formula
                With ws.Cells(currentRow, Global_Constants.SC_COL_DATE_COMP)
                    .NumberFormat = dateCompFormat
                    .Interior.Color = dateCompColorChild
                    .formula = "=IF($T$2=""AUTO"",IF(B" & currentRow & "=""COMPLETED"",NOW(),""""),"""")"
                End With
            End If
        End If
    Next currentRow
End Sub

' UPDATED: Apply validation to existing sheet with proper limits
Private Sub ApplyDataValidationToExistingSheetWithGlobalConstants(ws As Worksheet)
    ' Apply data validation to existing sheet
    Dim maxRow As Long
    Dim totalsRow As Long
    
    maxRow = ws.Cells(ws.Rows.Count, SC_COL_TASK_ID).End(xlUp).row
    
    ' Find the TOTALS row to ensure we don't apply validation to it or beyond
    totalsRow = FindTotalsRow(ws)
    
    ' If TOTALS row found and it's before maxRow, use it as the limit
    If totalsRow > 0 And totalsRow < maxRow Then
        maxRow = totalsRow - 1
    End If
    
    ' Only apply if we have data rows
    If maxRow >= 6 Then
        Call ApplyStatusValidationWithGlobalConstants(ws, 6, maxRow)
        Call ApplyAvailabilityValidationWithGlobalConstants(ws, 6, maxRow)
        Call ApplyPriorityValidationWithGlobalConstants(ws, 6, maxRow)
        Call ApplyDateDueValidationWithGlobalConstants(ws, 6, maxRow)
        Call ApplyAssessmentValidationWithGlobalConstants(ws, 6, maxRow)
        Call ApplyDatasheetValidationWithGlobalConstants(ws, 6, maxRow)
    End If
End Sub

' Individual validation functions with input messages

Private Sub ApplyStatusValidationWithGlobalConstants(ws As Worksheet, startRow As Long, endRow As Long)
    Dim currentRow As Long
    Dim taskId As String
    
    On Error Resume Next
    
    For currentRow = startRow To endRow
        taskId = Trim(CStr(ws.Cells(currentRow, SC_COL_TASK_ID).Value))
        
        If Len(taskId) > 0 And UCase(taskId) <> "TOTALS" Then
            If CountDots(taskId) = 1 Then
                ' Parent rows - no validation (formula controlled)
                ws.Cells(currentRow, SC_COL_STATUS).Validation.Delete
            ElseIf CountDots(taskId) > 1 Then
                ' Child rows - apply validation with input message
                With ws.Cells(currentRow, SC_COL_STATUS).Validation
                    .Delete
                    .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, _
                         Formula1:=VAL_STATUS_CHILD_RANGE
                    .IgnoreBlank = True
                    .InCellDropdown = True
                    .InputTitle = "Task Status"
                    .InputMessage = "Select the current status of this task"
                    .ErrorTitle = "Invalid Status"
                    .ErrorMessage = "Please select a valid status from the list"
                    .ShowInput = True
                    .ShowError = True
                End With
            End If
        End If
    Next currentRow
    
    On Error GoTo 0
End Sub

Private Sub ApplyAvailabilityValidationWithGlobalConstants(ws As Worksheet, startRow As Long, endRow As Long)
    On Error Resume Next
    
    ' Only apply to rows with actual task IDs (not TOTALS)
    Dim currentRow As Long
    For currentRow = startRow To endRow
        Dim taskId As String
        taskId = Trim(CStr(ws.Cells(currentRow, SC_COL_TASK_ID).Value))
        
        If Len(taskId) > 0 And UCase(taskId) <> "TOTALS" Then
            With ws.Cells(currentRow, SC_COL_AVAIL).Validation
                .Delete
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, _
                     Formula1:=VAL_AVAILABILITY_RANGE
                .IgnoreBlank = True
                .InCellDropdown = True
                .InputTitle = "Resource Availability"
                .InputMessage = "Select the assigned resource from the list"
                .ErrorTitle = "Invalid Resource"
                .ErrorMessage = "Please select a valid resource from the list"
                .ShowInput = True
                .ShowError = True
            End With
        End If
    Next currentRow
    
    On Error GoTo 0
End Sub

Private Sub ApplyPriorityValidationWithGlobalConstants(ws As Worksheet, startRow As Long, endRow As Long)
    On Error Resume Next
    
    ' Only apply to rows with actual task IDs (not TOTALS)
    Dim currentRow As Long
    For currentRow = startRow To endRow
        Dim taskId As String
        taskId = Trim(CStr(ws.Cells(currentRow, SC_COL_TASK_ID).Value))
        
        If Len(taskId) > 0 And UCase(taskId) <> "TOTALS" Then
            With ws.Cells(currentRow, SC_COL_PRIORITY).Validation
                .Delete
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, _
                     Formula1:=VAL_PRIORITY_RANGE
                .IgnoreBlank = True
                .InCellDropdown = True
                .InputTitle = "Task Priority"
                .InputMessage = "Select the priority level (High/Medium/Low)"
                .ErrorTitle = "Invalid Priority"
                .ErrorMessage = "Please select High, Medium, or Low"
                .ShowInput = True
                .ShowError = True
            End With
        End If
    Next currentRow
    
    On Error GoTo 0
End Sub

Private Sub ApplyDateDueValidationWithGlobalConstants(ws As Worksheet, startRow As Long, endRow As Long)
    On Error Resume Next
    
    ' Only apply to child rows (parent rows have rollup formula)
    Dim currentRow As Long
    For currentRow = startRow To endRow
        Dim taskId As String
        taskId = Trim(CStr(ws.Cells(currentRow, SC_COL_TASK_ID).Value))
        
        If Len(taskId) > 0 And UCase(taskId) <> "TOTALS" And CountDots(taskId) > 1 Then
            ' Only apply to child rows
            With ws.Cells(currentRow, SC_COL_DATE_DUE).Validation
                .Delete
                .Add Type:=xlValidateDate, AlertStyle:=xlValidAlertStop, _
                     Operator:=xlGreaterEqual, Formula1:="=TODAY()"
                .IgnoreBlank = True
                .InputTitle = "Due Date"
                .InputMessage = "Enter the task due date (must be today or later)"
                .ErrorTitle = "Invalid Date"
                .ErrorMessage = "Due date must be today or a future date"
                .ShowInput = True
                .ShowError = True
            End With
        End If
    Next currentRow
    
    On Error GoTo 0
End Sub

Private Sub ApplyAssessmentValidationWithGlobalConstants(ws As Worksheet, startRow As Long, endRow As Long)
    On Error Resume Next
    
    ' Only apply to rows with actual task IDs (not TOTALS)
    Dim currentRow As Long
    For currentRow = startRow To endRow
        Dim taskId As String
        taskId = Trim(CStr(ws.Cells(currentRow, SC_COL_TASK_ID).Value))
        
        If Len(taskId) > 0 And UCase(taskId) <> "TOTALS" Then
            With ws.Cells(currentRow, SC_COL_ASSESSMENT).Validation
                .Delete
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, _
                     Formula1:=VAL_ASSESSMENT_RANGE
                .IgnoreBlank = True
                .InCellDropdown = True
                .InputTitle = "Assessment Status"
                .InputMessage = "Select Yes or No for assessment requirement"
                .ErrorTitle = "Invalid Assessment"
                .ErrorMessage = "Please select Yes or No"
                .ShowInput = True
                .ShowError = True
            End With
        End If
    Next currentRow
    
    On Error GoTo 0
End Sub

Private Sub ApplyDatasheetValidationWithGlobalConstants(ws As Worksheet, startRow As Long, endRow As Long)
    On Error Resume Next
    
    ' Only apply to rows with actual task IDs (not TOTALS)
    Dim currentRow As Long
    For currentRow = startRow To endRow
        Dim taskId As String
        taskId = Trim(CStr(ws.Cells(currentRow, SC_COL_TASK_ID).Value))
        
        If Len(taskId) > 0 And UCase(taskId) <> "TOTALS" Then
            With ws.Cells(currentRow, SC_COL_DATASHEET).Validation
                .Delete
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, _
                     Formula1:=VAL_DATASHEET_LIST
                .IgnoreBlank = True
                .InCellDropdown = True
                .InputTitle = "Datasheet Requirement"
                .InputMessage = "Select Yes or No for datasheet requirement"
                .ErrorTitle = "Invalid Datasheet"
                .ErrorMessage = "Please select Yes or No"
                .ShowInput = True
                .ShowError = True
            End With
        End If
    Next currentRow
    
    On Error GoTo 0
End Sub

' ============================================================================
' ROLLUP AND FORMULA FUNCTIONS
' ============================================================================

Private Sub UpdateParentStatusFormulasWithGlobalConstants(ws As Worksheet)
    Dim currentRow As Long
    Dim maxRow As Long
    maxRow = ws.Cells(ws.Rows.Count, Global_Constants.SC_COL_TASK_ID).End(xlUp).row
    
    For currentRow = 6 To maxRow  ' Start from row 6
        Dim taskId As String
        taskId = Trim(CStr(ws.Cells(currentRow, Global_Constants.SC_COL_TASK_ID).Value))
        
        If Len(taskId) > 0 And CountDots(taskId) = 1 Then
            ' Parent row - update status formula
            ws.Cells(currentRow, Global_Constants.SC_COL_STATUS).formula = _
                "=IF(AND(I" & currentRow & "<>"""",N" & currentRow & "<1,I" & currentRow & "<TODAY()),""OVERDUE""," & _
                "IF(N" & currentRow & "=1,""COMPLETED""," & _
                "IF(N" & currentRow & "=0,""NOT STARTED""," & _
                "IF(AND(N" & currentRow & ">0,N" & currentRow & "<1),""IN PROGRESS"",""""))))"
        End If
    Next currentRow
End Sub

Private Sub UpdatePercentageAndRollupFormulasWithGlobalConstants(ws As Worksheet)
    Dim currentRow As Long
    Dim maxRow As Long
    maxRow = ws.Cells(ws.Rows.Count, Global_Constants.SC_COL_TASK_ID).End(xlUp).row
    
    Application.Calculation = xlCalculationManual
    
    For currentRow = 6 To maxRow  ' Start from row 6
        Dim taskId As String
        taskId = Trim(CStr(ws.Cells(currentRow, Global_Constants.SC_COL_TASK_ID).Value))
        
        If Len(taskId) > 0 And taskId <> "TOTALS" Then
            If CountDots(taskId) = 1 Then
                ' Parent row - setup rollup formulas
                Call BuildParentRollupForRow(ws, currentRow)
            ElseIf CountDots(taskId) > 1 Then
                ' Child row - percentage formula
                ws.Cells(currentRow, Global_Constants.SC_COL_PCT).formula = _
                    "=IFERROR(IF(" & ws.Cells(currentRow, Global_Constants.SC_COL_AHRS).Address(False, False) & ">0," & _
                    "1-(" & ws.Cells(currentRow, Global_Constants.SC_COL_REMHRS).Address(False, False) & "/" & _
                             ws.Cells(currentRow, Global_Constants.SC_COL_AHRS).Address(False, False) & ")," & _
                    "0),0)"
            End If
        End If
    Next currentRow
    
    Application.Calculation = xlCalculationAutomatic
End Sub

Private Sub BuildParentRollupFormulas(ws As Worksheet, startRow As Long, endRow As Long)
    Dim currentRow As Long
    
    For currentRow = startRow To endRow
        Dim taskId As String
        taskId = Trim(CStr(ws.Cells(currentRow, Global_Constants.SC_COL_TASK_ID).Value))
        
        If Len(taskId) > 0 And CountDots(taskId) = 1 Then
            Call BuildParentRollupForRow(ws, currentRow)
        End If
    Next currentRow
End Sub

Private Sub BuildParentRollupForRow(ws As Worksheet, parentRow As Long)
    Dim childStart As Long, childEnd As Long
    childStart = parentRow + 1
    childEnd = childStart
    
    Dim maxRow As Long
    maxRow = ws.Cells(ws.Rows.Count, Global_Constants.SC_COL_TASK_ID).End(xlUp).row
    
    ' Find end of child block
    Do While childEnd <= maxRow
        Dim curId As String
        curId = Trim(CStr(ws.Cells(childEnd, Global_Constants.SC_COL_TASK_ID).Value))
        If Len(curId) = 0 Or curId = "TOTALS" Then Exit Do
        If CountDots(curId) <= 1 Then Exit Do
        childEnd = childEnd + 1
    Loop
    childEnd = childEnd - 1
    
    If childEnd >= childStart Then
        ' Setup parent rollup formulas
        ws.Cells(parentRow, Global_Constants.SC_COL_DELAY).formula = _
            "=SUM(" & GetColumnLetter(Global_Constants.SC_COL_DELAY) & childStart & ":" & GetColumnLetter(Global_Constants.SC_COL_DELAY) & childEnd & ")"
        ws.Cells(parentRow, Global_Constants.SC_COL_AHRS).formula = _
            "=SUM(" & GetColumnLetter(Global_Constants.SC_COL_AHRS) & childStart & ":" & GetColumnLetter(Global_Constants.SC_COL_AHRS) & childEnd & ")"
        ws.Cells(parentRow, Global_Constants.SC_COL_REMHRS).formula = _
            "=SUM(" & GetColumnLetter(Global_Constants.SC_COL_REMHRS) & childStart & ":" & GetColumnLetter(Global_Constants.SC_COL_REMHRS) & childEnd & ")"
        ws.Cells(parentRow, Global_Constants.SC_COL_ACTHRS).formula = _
            "=SUM(" & GetColumnLetter(Global_Constants.SC_COL_ACTHRS) & childStart & ":" & GetColumnLetter(Global_Constants.SC_COL_ACTHRS) & childEnd & ")"
        
        ' Parent percentage from rolled-up values
        ws.Cells(parentRow, Global_Constants.SC_COL_PCT).formula = _
            "=IFERROR(IF(" & GetColumnLetter(Global_Constants.SC_COL_AHRS) & parentRow & ">0," & _
            "1-(" & GetColumnLetter(Global_Constants.SC_COL_REMHRS) & parentRow & "/" & _
            GetColumnLetter(Global_Constants.SC_COL_AHRS) & parentRow & "),0),0)"
    End If
End Sub

Private Sub BuildTotalsFormulas(ws As Worksheet, totalsRow As Long, startRow As Long, endRow As Long)
    ' Build SUMIF formulas to only sum parent rows (Task IDs with exactly 1 dot)
    ' This avoids double-counting since parent rows already contain child sums
    
    ' Build the criteria range for Task_ID column
    Dim taskIdRange As String
    taskIdRange = GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & startRow & ":" & _
                  GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & endRow
    
    ' Build sum ranges for each column
    Dim sumRangeO As String, sumRangeP As String, sumRangeQ As String, sumRangeR As String
    sumRangeO = GetColumnLetter(Global_Constants.SC_COL_DELAY) & startRow & ":" & GetColumnLetter(Global_Constants.SC_COL_DELAY) & endRow
    sumRangeP = GetColumnLetter(Global_Constants.SC_COL_AHRS) & startRow & ":" & GetColumnLetter(Global_Constants.SC_COL_AHRS) & endRow
    sumRangeQ = GetColumnLetter(Global_Constants.SC_COL_REMHRS) & startRow & ":" & GetColumnLetter(Global_Constants.SC_COL_REMHRS) & endRow
    sumRangeR = GetColumnLetter(Global_Constants.SC_COL_ACTHRS) & startRow & ":" & GetColumnLetter(Global_Constants.SC_COL_ACTHRS) & endRow
    
    With ws
        ' Use SUMPRODUCT to sum only parent rows (those with exactly 1 dot in Task_ID)
        ' Formula counts dots and only sums rows where dot count = 1
        
        ' Task Delays - sum only parent rows
        .Cells(totalsRow, Global_Constants.SC_COL_DELAY).formula = _
            "=SUMPRODUCT((" & sumRangeO & ")*(LEN(" & taskIdRange & ")-LEN(SUBSTITUTE(" & taskIdRange & ",""."",""""))=1))"
        
        ' Apparatus Hours - sum only parent rows
        .Cells(totalsRow, Global_Constants.SC_COL_AHRS).formula = _
            "=SUMPRODUCT((" & sumRangeP & ")*(LEN(" & taskIdRange & ")-LEN(SUBSTITUTE(" & taskIdRange & ",""."",""""))=1))"
        
        ' Remaining Hours - sum only parent rows
        .Cells(totalsRow, Global_Constants.SC_COL_REMHRS).formula = _
            "=SUMPRODUCT((" & sumRangeQ & ")*(LEN(" & taskIdRange & ")-LEN(SUBSTITUTE(" & taskIdRange & ",""."",""""))=1))"
        
        ' Actual Hours - sum only parent rows
        .Cells(totalsRow, Global_Constants.SC_COL_ACTHRS).formula = _
            "=SUMPRODUCT((" & sumRangeR & ")*(LEN(" & taskIdRange & ")-LEN(SUBSTITUTE(" & taskIdRange & ",""."",""""))=1))"
        
        ' Totals percentage - based on totaled parent values
        .Cells(totalsRow, Global_Constants.SC_COL_PCT).formula = _
            "=IFERROR(IF(" & GetColumnLetter(Global_Constants.SC_COL_AHRS) & totalsRow & ">0," & _
            "1-" & GetColumnLetter(Global_Constants.SC_COL_REMHRS) & totalsRow & "/" & _
            GetColumnLetter(Global_Constants.SC_COL_AHRS) & totalsRow & ",0),0)"
    End With
End Sub

Private Sub CleanupStrayBorders(ws As Worksheet, totalsRow As Long)
    On Error Resume Next
    Dim clearFromRow As Long: clearFromRow = totalsRow + 1
    If clearFromRow <= ws.Rows.Count Then
        ws.Range("A" & clearFromRow & ":XFD" & ws.Rows.Count).Borders.LineStyle = xlNone
    End If
    ws.Range("S1:XFD" & (totalsRow + 10)).Borders.LineStyle = xlNone
    ws.Range("A" & (totalsRow + 1) & ":R" & (totalsRow + 20)).Borders.LineStyle = xlNone
    On Error GoTo 0
End Sub

Private Sub AddModeToggleButtonToSheet(ws As Worksheet)
    Dim existingBtn As Shape
    On Error Resume Next
    Set existingBtn = ws.Shapes("ModeToggleBtn")
    On Error GoTo 0
    
    If Not existingBtn Is Nothing Then Exit Sub
    
    On Error Resume Next
    Dim btn As Shape
    Set btn = ws.Shapes.AddShape(msoShapeRectangle, 1100, 10, 120, 30)
    
    If Not btn Is Nothing Then
        With btn
            .Name = "ModeToggleBtn"
            .TextFrame2.TextRange.Text = "Toggle Mode"
            .Fill.ForeColor.RGB = RGB(70, 130, 180)
            .TextFrame2.TextRange.Font.Fill.ForeColor.RGB = RGB(255, 255, 255)
            .TextFrame2.TextRange.Font.Size = 10
            .OnAction = "ToggleDateCompletionMode"
        End With
    End If
    On Error GoTo 0
End Sub

' Mode toggle function
Sub ToggleDateCompletionMode()
    Dim ws As Worksheet
    Set ws = ActiveSheet
    
    Dim currentMode As String
    currentMode = UCase(Trim(CStr(ws.Range(Global_Constants.SC_MODE_TOGGLE_CELL).Value)))
    
    If currentMode = "AUTO" Then
        ws.Range(Global_Constants.SC_MODE_TOGGLE_CELL).Value = "MANUAL"
    Else
        ws.Range(Global_Constants.SC_MODE_TOGGLE_CELL).Value = "AUTO"
    End If
    
    MsgBox "Switched to " & ws.Range(Global_Constants.SC_MODE_TOGGLE_CELL).Value & " mode!", vbInformation
End Sub

' ============================================================================
' UTILITY FUNCTIONS
' ============================================================================
' These are local copies since VBA doesn't allow calling functions from other modules with module prefix

Private Function CountDots(inputString As String) As Long
    ' Counts the number of dots in a string (for Task_ID level detection)
    Dim i As Long, dotCount As Long
    For i = 1 To Len(inputString)
        If Mid(inputString, i, 1) = "." Then dotCount = dotCount + 1
    Next i
    CountDots = dotCount
End Function

Private Function GetColumnLetter(columnNumber As Long) As String
    ' Converts column number to Excel column letter (1=A, 2=B, etc.)
    GetColumnLetter = Replace(Cells(1, columnNumber).Address(True, False), "$1", "")
End Function



