Attribute VB_Name = "Field_Workbook_Export"
'================== BULLETPROOF FIELD EXPORT MODULE - FINAL ==================
Option Explicit

Public Sub Create_Field_Workbook_Final()
    '=== Streamlined field export with all functionality preserved ===
    
    Dim wbMaster As Workbook, wbField As Workbook
    Dim fileName As String, filePath As Variant
    Dim tempPath As String, startTime As Double
    
    startTime = Timer
    Set wbMaster = ThisWorkbook
    
    ' Build filename
    fileName = GetProjectName() & "_Field_" & Format(Date, "yyyymmdd") & ".xlsx"
    
    ' Save master first
    wbMaster.Save
    
    ' Get save location from user
    filePath = Application.GetSaveAsFilename( _
        InitialFileName:=fileName, _
        FileFilter:="Excel Files (*.xlsx), *.xlsx", _
        Title:="Save Field Workbook As")
    
    If filePath = False Then
        MsgBox "Export cancelled.", vbInformation
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    
    ' Create temp XLSM copy
    tempPath = Replace(filePath, ".xlsx", "_temp.xlsm")
    wbMaster.SaveCopyAs tempPath
    
    ' Open and clean the copy
    Set wbField = Workbooks.Open(tempPath)
    
    ' STREAMLINE: Remove only truly unnecessary sheets
    Call RemoveFieldSheets(wbField)
    
    ' ADD NAVIGATION SHEETS
    Call CreateHomeSheet(wbField)
    Call CreateDashboard(wbField)
    Call CreateInstructions(wbField)
    
    ' POWER BI: Ensure data connection works
    Call ValidatePowerBIData(wbField)
    
    ' ORGANIZE: Set visibility (hide reference sheets)
    Call SetFieldVisibility(wbField)
    
    ' Save as XLSX (removes VBA)
    wbField.SaveAs fileName:=filePath, FileFormat:=xlOpenXMLWorkbook
    wbField.Close SaveChanges:=False
    
    ' Clean up temp file
    On Error Resume Next
    Kill tempPath
    On Error GoTo 0
    
    ' Reopen for user
    Set wbField = Workbooks.Open(filePath)
    
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    
    MsgBox "Field workbook created successfully!" & vbCrLf & vbCrLf & _
           "VISIBLE SHEETS:" & vbCrLf & _
           "• Home, Dashboard, Instructions" & vbCrLf & _
           "• All Scope sheets (PPM, GDB, RPP, etc.)" & vbCrLf & _
           "• All Gantt charts" & vbCrLf & vbCrLf & _
           "HIDDEN (but functional):" & vbCrLf & _
           "• All_Tasks, PowerBI_Data, Lists, Apparatus" & vbCrLf & vbCrLf & _
           "? All formulas and links preserved" & vbCrLf & _
           "? Power BI ready: Connect to PowerBI_Data table", _
           vbInformation, "Export Complete"
    
End Sub

Private Sub CreateHomeSheet(wb As Workbook)
    '=== Create navigation home page ===
    
    Dim ws As Worksheet
    
    On Error Resume Next
    Set ws = wb.Worksheets("Home")
    On Error GoTo 0
    
    If ws Is Nothing Then
        Set ws = wb.Worksheets.Add(Before:=wb.Worksheets(1))
        ws.Name = "Home"
    End If
    
    With ws
        .Cells.Clear
        
        ' Title
        .Range("C3:H4").Merge
        .Range("C3").Value = GetProjectName() & " - Field Workbook"
        .Range("C3").Font.Size = 18
        .Range("C3").Font.Bold = True
        .Range("C3").HorizontalAlignment = xlCenter
        
        ' Navigation links
        .Range("C7").Value = "QUICK ACCESS"
        .Range("C7").Font.Bold = True
        .Range("C7").Font.Size = 12
        
        ' Dashboard link
        .Range("C9:E9").Merge
        .Range("C9").Value = "?? Dashboard"
        .Hyperlinks.Add Anchor:=.Range("C9"), Address:="", SubAddress:="Dashboard!A1"
        .Range("C9").Interior.Color = RGB(217, 225, 242)
        .Range("C9").Borders.LineStyle = xlContinuous
        .Range("C9").HorizontalAlignment = xlCenter
        
        ' Instructions link
        .Range("C11:E11").Merge
        .Range("C11").Value = "?? Instructions"
        .Hyperlinks.Add Anchor:=.Range("C11"), Address:="", SubAddress:="Instructions!A1"
        .Range("C11").Interior.Color = RGB(255, 255, 200)
        .Range("C11").Borders.LineStyle = xlContinuous
        .Range("C11").HorizontalAlignment = xlCenter
        
        ' Data flow info
        .Range("C14").Value = "DATA FLOW STATUS:"
        .Range("C14").Font.Bold = True
        
        .Range("C15:F16").Merge
        .Range("C15").Value = "? All links active and auto-updating" & vbCrLf & _
                             "Scope Sheets ? All_Tasks ? PowerBI_Data"
        .Range("C15").Font.Color = RGB(0, 128, 0)
        .Range("C15").HorizontalAlignment = xlCenter
        .Range("C15").WrapText = True
        
        .Columns("C:H").AutoFit
    End With
    
End Sub

Private Sub CreateDashboard(wb As Workbook)
    '=== Create dashboard with live metrics ===
    
    Dim ws As Worksheet
    
    On Error Resume Next
    Set ws = wb.Worksheets("Dashboard")
    On Error GoTo 0
    
    If ws Is Nothing Then
        Set ws = wb.Worksheets.Add(After:=wb.Worksheets(1))
        ws.Name = "Dashboard"
    End If
    
    With ws
        .Cells.Clear
        
        ' Title
        .Range("B2:G3").Merge
        .Range("B2").Value = GetProjectName() & " - Live Dashboard"
        .Range("B2").Font.Size = 18
        .Range("B2").Font.Bold = True
        .Range("B2").HorizontalAlignment = xlCenter
        
        ' Key metrics section
        .Range("B5").Value = "PROJECT METRICS"
        .Range("B5").Font.Bold = True
        .Range("B5").Font.Size = 14
        
        ' Metrics table
        .Range("B7:C7").Value = Array("Metric", "Value")
        .Range("B7:C7").Font.Bold = True
        .Range("B7:C7").Interior.Color = RGB(217, 225, 242)
        
        ' Metrics with formulas
        .Range("B8").Value = "Total Tasks:"
        .Range("C8").formula = "=COUNTA(PowerBI_Data!B:B)-1"
        
        .Range("B9").Value = "Average Completion:"
        .Range("C9").formula = "=IFERROR(AVERAGE(PowerBI_Data!H:H),0)"
        .Range("C9").NumberFormat = "0%"
        
        .Range("B10").Value = "Total Quoted Hours:"
        .Range("C10").formula = "=IFERROR(SUM(PowerBI_Data!I:I),0)"
        .Range("C10").NumberFormat = "#,##0"
        
        .Range("B11").Value = "Remaining Hours:"
        .Range("C11").formula = "=IFERROR(SUM(PowerBI_Data!J:J),0)"
        .Range("C11").NumberFormat = "#,##0"
        
        .Range("B12").Value = "Actual Hours:"
        .Range("C12").formula = "=IFERROR(SUM(PowerBI_Data!K:K),0)"
        .Range("C12").NumberFormat = "#,##0"
        
        .Range("B13").Value = "Last Updated:"
        .Range("C13").formula = "=NOW()"
        .Range("C13").NumberFormat = "mm/dd/yyyy hh:mm"
        
        ' Format table
        .Range("B7:C13").Borders.LineStyle = xlContinuous
        
        ' Summary by scope
        .Range("E5").Value = "BY SCOPE"
        .Range("E5").Font.Bold = True
        .Range("E5").Font.Size = 14
        
        .Range("E7:G7").Value = Array("Scope", "Tasks", "Avg %")
        .Range("E7:G7").Font.Bold = True
        .Range("E7:G7").Interior.Color = RGB(217, 225, 242)
        
        ' Scope summaries
        .Range("E8").Value = "PPM"
        .Range("F8").formula = "=COUNTIF(PowerBI_Data!A:A,""PPM*"")"
        .Range("G8").formula = "=IFERROR(AVERAGEIF(PowerBI_Data!A:A,""PPM*"",PowerBI_Data!H:H),0)"
        .Range("G8").NumberFormat = "0%"
        
        .Range("E9").Value = "GDB"
        .Range("F9").formula = "=COUNTIF(PowerBI_Data!A:A,""GDB*"")"
        .Range("G9").formula = "=IFERROR(AVERAGEIF(PowerBI_Data!A:A,""GDB*"",PowerBI_Data!H:H),0)"
        .Range("G9").NumberFormat = "0%"
        
        .Range("E10").Value = "RPP"
        .Range("F10").formula = "=COUNTIF(PowerBI_Data!A:A,""RPP*"")"
        .Range("G10").formula = "=IFERROR(AVERAGEIF(PowerBI_Data!A:A,""RPP*"",PowerBI_Data!H:H),0)"
        .Range("G10").NumberFormat = "0%"
        
        .Range("E7:G10").Borders.LineStyle = xlContinuous
        
        .Columns("B:G").AutoFit
    End With
    
End Sub

Private Sub CreateInstructions(wb As Workbook)
    '=== Create instructions sheet ===
    
    Dim ws As Worksheet
    
    On Error Resume Next
    Set ws = wb.Worksheets("Instructions")
    On Error GoTo 0
    
    If ws Is Nothing Then
        Set ws = wb.Worksheets.Add(After:=wb.Worksheets(2))
        ws.Name = "Instructions"
    End If
    
    With ws
        .Cells.Clear
        
        .Range("B2").Value = "FIELD WORKBOOK INSTRUCTIONS"
        .Range("B2").Font.Size = 16
        .Range("B2").Font.Bold = True
        
        .Range("B4:G22").Value = "FIELD DATA ENTRY:" & vbCrLf & vbCrLf & _
            "SCOPE SHEETS (PPM01, GDB01, RPP's, etc.):" & vbCrLf & _
            "• Column N: Enter % Completion (0-100)" & vbCrLf & _
            "• Column Q: Enter Remaining Hours" & vbCrLf & _
            "• Column R: Enter Actual Hours" & vbCrLf & _
            "• Column L: Enter Completion Date" & vbCrLf & vbCrLf & _
            "AUTOMATIC UPDATES:" & vbCrLf & _
            "• Gantt charts update from scope sheets" & vbCrLf & _
            "• All_Tasks aggregates all scope data (hidden)" & vbCrLf & _
            "• PowerBI_Data pulls from All_Tasks (hidden)" & vbCrLf & _
            "• Dashboard shows live metrics" & vbCrLf & vbCrLf & _
            "POWER BI CONNECTION:" & vbCrLf & _
            "• Connect to: PowerBI_Data table" & vbCrLf & _
            "• The sheet is hidden but accessible" & vbCrLf & _
            "• To unhide: Right-click any tab ? Unhide" & vbCrLf & vbCrLf & _
            "SAVE FREQUENTLY:" & vbCrLf & _
            "• Press Ctrl+S after entering data" & vbCrLf & _
            "• All formulas and links are preserved"
        
        .Range("B4:G22").WrapText = True
        .Range("B4:G22").VerticalAlignment = xlTop
        .Range("B4:G22").Interior.Color = RGB(255, 255, 240)
        .Range("B4:G22").Borders.LineStyle = xlContinuous
        
        .Columns("B:G").AutoFit
        .Rows("4:22").AutoFit
    End With
    
End Sub

Private Sub RemoveFieldSheets(wb As Workbook)
    '=== Remove ONLY sheets that are truly not needed ===
    
    Dim ws As Worksheet
    Application.DisplayAlerts = False
    
    For Each ws In wb.Worksheets
        Select Case ws.Name
            ' Remove ONLY these specific sheets
            Case "Task_Entry", "Project_Form", "Config", _
                 "Metadata", "All_Scripts"
                ws.Delete
                
            ' Keep ALL reference sheets:
            ' - All_Tasks (aggregation)
            ' - Apparatus List w Hours (lookups)
            ' - List (dropdowns)
            ' - PowerBI_Data (BI connection)
                
            ' Remove template sheets
            Case Else
                If InStr(ws.Name, "Template") > 0 Then
                    ws.Delete
                End If
        End Select
    Next ws
    
    Application.DisplayAlerts = True
End Sub

Private Sub ValidatePowerBIData(wb As Workbook)
    '=== Ensure PowerBI_Data properly links to All_Tasks ===
    
    Dim wsPBI As Worksheet, wsAllTasks As Worksheet
    Dim lastRow As Long, r As Long
    
    ' Verify All_Tasks exists
    On Error Resume Next
    Set wsAllTasks = wb.Worksheets("All_Tasks")
    On Error GoTo 0
    
    If wsAllTasks Is Nothing Then
        MsgBox "All_Tasks sheet not found - PowerBI_Data cannot be created", 48
        Exit Sub
    End If
    
    ' Delete and recreate PowerBI_Data for clean setup
    Application.DisplayAlerts = False
    On Error Resume Next
    wb.Worksheets("PowerBI_Data").Delete
    On Error GoTo 0
    Application.DisplayAlerts = True
    
    ' Create fresh PowerBI_Data sheet
    Set wsPBI = wb.Worksheets.Add(After:=wb.Worksheets(wb.Worksheets.Count))
    wsPBI.Name = "PowerBI_Data"
    
    ' Find actual last row in All_Tasks
    lastRow = wsAllTasks.Cells(wsAllTasks.Rows.Count, "E").End(xlUp).row
    If lastRow < 2 Then lastRow = 100 ' Minimum 100 rows
    
    With wsPBI
        ' Add headers
        .Range("A1:L1").Value = Array("Scope", "Task_ID", "Task", _
            "Apparatus", "Status", "Date_Due", "Date_Completed", _
            "Pct_Complete", "Quoted_Hours", "Remaining_Hours", _
            "Actual_Hours", "Last_Updated")
        
        ' Format headers
        .Range("A1:L1").Font.Bold = True
        .Range("A1:L1").Interior.Color = RGB(217, 225, 242)
        
        ' Add formulas linking to All_Tasks
        For r = 2 To lastRow
            .Cells(r, 1).formula = "=IFERROR(All_Tasks!D" & r & ","""")"  ' Scope
            .Cells(r, 2).formula = "=IFERROR(All_Tasks!E" & r & ","""")"  ' Task_ID
            .Cells(r, 3).formula = "=IFERROR(All_Tasks!F" & r & ","""")"  ' Task
            .Cells(r, 4).formula = "=IFERROR(All_Tasks!G" & r & ","""")"  ' Apparatus
            .Cells(r, 5).formula = "=IFERROR(All_Tasks!K" & r & ","""")"  ' Status
            .Cells(r, 6).formula = "=IFERROR(All_Tasks!I" & r & ","""")"  ' Date_Due
            .Cells(r, 7).formula = "=IFERROR(All_Tasks!L" & r & ","""")"  ' Date_Completed
            .Cells(r, 8).formula = "=IFERROR(All_Tasks!N" & r & ",0)"     ' Pct_Complete
            .Cells(r, 9).formula = "=IFERROR(All_Tasks!O" & r & ",0)"     ' Quoted_Hours
            .Cells(r, 10).formula = "=IFERROR(All_Tasks!Q" & r & ",0)"    ' Remaining_Hours
            .Cells(r, 11).formula = "=IFERROR(All_Tasks!R" & r & ",0)"    ' Actual_Hours
            .Cells(r, 12).Value = Now()                                   ' Last_Updated
        Next r
        
        ' Force calculation
        .Calculate
        
        ' Create table for Power BI
        On Error Resume Next
        Dim tbl As ListObject
        Set tbl = .ListObjects.Add(xlSrcRange, .Range("A1:L" & lastRow), , xlYes)
        tbl.Name = "PowerBIData"
        tbl.TableStyle = "TableStyleMedium2"
        On Error GoTo 0
        
        ' Format columns
        .Columns("H").NumberFormat = "0%"
        .Columns("I:K").NumberFormat = "#,##0"
        .Columns("A:L").AutoFit
    End With
    
End Sub

Private Sub SetFieldVisibility(wb As Workbook)
    '=== Hide all reference sheets, show only working sheets ===
    
    Dim ws As Worksheet
    
    For Each ws In wb.Worksheets
        Select Case ws.Name
            
            ' VISIBLE navigation sheets
            Case "Home", "Dashboard", "Instructions"
                ws.Visible = xlSheetVisible
                
            ' HIDDEN reference sheets (preserve all functionality)
            Case "All_Tasks", "List", "PowerBI_Data", "Apparatus List w Hours"
                ws.Visible = xlSheetHidden
                
            ' VISIBLE field sheets (scope and Gantt)
            Case Else
                ' Show all scope and Gantt sheets
                ws.Visible = xlSheetVisible
                
        End Select
    Next ws
    
    ' Activate Home sheet
    On Error Resume Next
    wb.Sheets("Home").Activate
    wb.Sheets("Home").Range("A1").Select
    On Error GoTo 0
    
End Sub

Private Function GetProjectName() As String
    '=== Extract project name from workbook filename ===
    Dim projectName As String
    projectName = ThisWorkbook.Name
    projectName = Replace(projectName, ".xlsm", "")
    projectName = Replace(projectName, ".xlsx", "")
    If InStr(projectName, " - ") > 0 Then
        projectName = Left(projectName, InStr(projectName, " - ") - 1)
    End If
    GetProjectName = Trim(projectName)
End Function

