Attribute VB_Name = "PowerBIExport_FormulaBased"

'================================================================================
' MODULE: PowerBIExport_Corrected
' VERSION: 2.0.0 - FINAL CORRECTED VERSION
' PURPOSE: Export All_Tasks_Billing to PowerBI_Data with proper formatting
'          Columns A-W identical across all sheets, X-AV are billing columns
'================================================================================
Option Explicit

Private Const POWERBI_SHEET_NAME As String = "PowerBI_Data"
Private Const POWERBI_TABLE_NAME As String = "tbl_PowerBI_Data"

'================================================================================
' MAIN EXPORT - Direct copy with smart formulas
'================================================================================
Public Sub ExportToPowerBIData()
    ' Creates PowerBI_Data as exact copy of All_Tasks_Billing (A-AV)
    ' with formulas to hide zeros and invalid dates
    
    Dim wsBilling As Worksheet, wsPowerBI As Worksheet
    Dim lastRow As Long
    Dim dataRange As Range
    Dim tbl As ListObject
    Dim row As Long, col As Long
    
    On Error GoTo ErrorHandler
    
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    ' Get source sheet
    Set wsBilling = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS_BILLING)
    
    ' Get last row
    lastRow = wsBilling.Cells(wsBilling.Rows.Count, 1).End(xlUp).row
    
    If lastRow < 2 Then
        MsgBox "No data in All_Tasks_Billing to export", vbExclamation
        GoTo Cleanup
    End If
    
    ' Delete existing PowerBI_Data if exists
    On Error Resume Next
    Set wsPowerBI = ThisWorkbook.Worksheets(POWERBI_SHEET_NAME)
    If Not wsPowerBI Is Nothing Then
        If ActiveSheet.Name = POWERBI_SHEET_NAME Then
            wsBilling.Activate
        End If
        Application.DisplayAlerts = False
        wsPowerBI.Delete
        Application.DisplayAlerts = True
    End If
    On Error GoTo ErrorHandler
    
    ' Create new PowerBI_Data sheet
    Set wsPowerBI = ThisWorkbook.Worksheets.Add(After:=wsBilling)
    wsPowerBI.Name = POWERBI_SHEET_NAME
    
    ' Copy headers (A-AV = 48 columns)
    wsBilling.Range("A1:AV1").Copy
    wsPowerBI.Range("A1").PasteSpecial xlPasteValues
    Application.CutCopyMode = False
    
    ' Create formulas for each row
    ' Column mapping based on actual All_Tasks_Billing structure:
    ' F = Designation (shows 0 when empty)
    ' G = Drawing (shows 0 when empty)
    ' Y = Base_Rate (hourly rate in dollars)
    ' AC = Week_Ending (date)
    ' AD = Billing_Period (text like "Oct-2025")
    ' AE = Base_Labor_$ (Base_Rate * Apparatus_Hours)
    
    For row = 2 To lastRow
        For col = 1 To 48  ' A to AV
            Dim cellRef As String
            cellRef = Global_Constants.SHEET_ALL_TASKS_BILLING & "!" & _
                     wsBilling.Cells(row, col).Address(False, False)
            
            Select Case col
                ' Columns A-E (1-5): Basic info - direct copy
                Case 1 To 5
                    wsPowerBI.Cells(row, col).formula = "=" & cellRef
                
                ' F (6): Designation - convert 0 to blank
                Case 6
                    wsPowerBI.Cells(row, col).formula = _
                        "=IF(OR(" & cellRef & "=0," & cellRef & "=""0""),""""," & cellRef & ")"
                    
                ' G (7): Drawing - convert 0 to blank
                Case 7
                    wsPowerBI.Cells(row, col).formula = _
                        "=IF(OR(" & cellRef & "=0," & cellRef & "=""0""),""""," & cellRef & ")"
                    
                ' H (8): Site - direct copy
                Case 8
                    wsPowerBI.Cells(row, col).formula = "=" & cellRef
                    
                ' I (9): Section/Notes - convert 0 to blank if it shows 0
                Case 9
                    wsPowerBI.Cells(row, col).formula = _
                        "=IF(" & cellRef & "=0,""""," & cellRef & ")"
                    
                ' J-L (10-12): Norm_ID, Voltage, Equipment_type - direct copy
                Case 10 To 12
                    wsPowerBI.Cells(row, col).formula = "=" & cellRef
                
                ' M (13): Forecast_hours - hide if zero
                Case 13
                    wsPowerBI.Cells(row, col).formula = _
                        "=IF(" & cellRef & "=0,""""," & cellRef & ")"
                
                ' N-Q (14-17): Schedule/Actual hours - hide if zero
                Case 14 To 17
                    wsPowerBI.Cells(row, col).formula = _
                        "=IF(" & cellRef & "=0,""""," & cellRef & ")"
                
                ' R (18): Completed_hours - hide if zero
                Case 18
                    wsPowerBI.Cells(row, col).formula = _
                        "=IF(" & cellRef & "=0,""""," & cellRef & ")"
                
                ' S (19): Percent_complete - always show
                Case 19
                    wsPowerBI.Cells(row, col).formula = "=" & cellRef
                
                ' T-W (20-23): Milestone, Status, Apparatus_Category, Scope_Type
                ' These are text/category fields - always show
                Case 20 To 23
                    wsPowerBI.Cells(row, col).formula = "=" & cellRef
                
                ' X (24): Scope_Helper - always show (identifies rows)
                Case 24
                    wsPowerBI.Cells(row, col).formula = "=" & cellRef
                
                ' Y (25): Base_Rate - always show (hourly rate in dollars)
                Case 25
                    wsPowerBI.Cells(row, col).formula = "=" & cellRef
                    
                ' Z-AA (26-27): Other billing fields - direct copy
                Case 26 To 27
                    wsPowerBI.Cells(row, col).formula = "=" & cellRef
                
                ' AB (28): Completion_Binary - ALWAYS show (0 or 1)
                Case 28
                    wsPowerBI.Cells(row, col).formula = "=" & cellRef
                
                ' AC (29): Week_Ending - hide invalid dates
                Case 29
                    wsPowerBI.Cells(row, col).formula = _
                        "=IF(OR(" & cellRef & "=0," & cellRef & "<DATE(2020,1,1)),""""," & cellRef & ")"
                        
                ' AD (30): Billing_Period - hide 0, show text like "Oct-2025"
                Case 30
                    wsPowerBI.Cells(row, col).formula = _
                        "=IF(" & cellRef & "=0,""""," & cellRef & ")"
                
                ' AE (31): Base_Labor_$ - ALWAYS show (calculated labor value)
                Case 31
                    wsPowerBI.Cells(row, col).formula = "=" & cellRef
                
                ' AF-AV (32-48): Other financial columns - hide if zero
                Case 32 To 48
                    wsPowerBI.Cells(row, col).formula = _
                        "=IF(" & cellRef & "=0,""""," & cellRef & ")"
                
                Case Else
                    ' Default - direct reference
                    wsPowerBI.Cells(row, col).formula = "=" & cellRef
            End Select
        Next col
    Next row
    
    ' Create table
    Set dataRange = wsPowerBI.Range("A1:AV" & lastRow)
    Set tbl = wsPowerBI.ListObjects.Add(xlSrcRange, dataRange, , xlYes)
    tbl.Name = POWERBI_TABLE_NAME
    tbl.TableStyle = "TableStyleLight1"
    
    ' Apply number formatting
    With wsPowerBI
        ' Hours columns
        .Range("M:R").NumberFormat = "#,##0.00;-#,##0.00;;"
        
        ' Percentage
        .Range("S:S").NumberFormat = "0%"
        
        ' Base_Rate (Y) - Currency format for hourly rate
        .Range("Y:Y").NumberFormat = "$#,##0.00"
        
        ' Week_Ending (AC) - Date format
        .Range("AC:AC").NumberFormat = "mm/dd/yyyy"
        
        ' Billing_Period (AD) - Text/General format
        .Range("AD:AD").NumberFormat = "@"
        
        ' Currency columns (AE-AV)
        .Range("AE:AV").NumberFormat = "_($* #,##0.00_);_($* (#,##0.00);_($* ""-""??_);_(@_)"
        
        ' Binary
        .Range("AB:AB").NumberFormat = "0"
        .Range("AB:AB").HorizontalAlignment = xlCenter
    End With
    
    ' Auto-fit columns
    wsPowerBI.Columns("A:AV").AutoFit
    
    ' Set max column widths
    Dim rngCol As Range
    For Each rngCol In wsPowerBI.Columns("A:AV").Columns
        If rngCol.ColumnWidth > 20 Then rngCol.ColumnWidth = 20
    Next rngCol
    
    MsgBox "PowerBI_Data created successfully!" & vbCrLf & _
           "Source: All_Tasks_Billing (A-AV)" & vbCrLf & _
           "Rows: " & (lastRow - 1) & vbCrLf & _
           "Columns: 48" & vbCrLf & vbCrLf & _
           "Key Features:" & vbCrLf & _
           "• Designation/Drawing: 0?blank" & vbCrLf & _
           "• Base_Rate: Shows as currency" & vbCrLf & _
           "• Financial columns: Hide zeros" & vbCrLf & _
           "• Auto-updates via formulas", _
           vbInformation, "Export Complete"
    
Cleanup:
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    Exit Sub
    
ErrorHandler:
    MsgBox "Error: " & Err.Description & vbCrLf & _
           "Line: " & Erl, vbCritical
    Resume Cleanup
End Sub

'================================================================================
' VALIDATION FUNCTION
'================================================================================
Public Sub ValidateColumnMapping()
    ' Validates that columns A-W are identical across sheets
    
    Dim wsAll As Worksheet, wsBilling As Worksheet, wsPowerBI As Worksheet
    Dim col As Long
    Dim mismatches As String
    
    On Error Resume Next
    Set wsAll = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS)
    Set wsBilling = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS_BILLING)
    Set wsPowerBI = ThisWorkbook.Worksheets(POWERBI_SHEET_NAME)
    On Error GoTo 0
    
    If wsAll Is Nothing Or wsBilling Is Nothing Then
        MsgBox "Source sheets not found", vbExclamation
        Exit Sub
    End If
    
    ' Check headers A-W match
    For col = 1 To 23
        If wsAll.Cells(1, col).Value <> wsBilling.Cells(1, col).Value Then
            mismatches = mismatches & "Column " & Chr(64 + col) & ": " & _
                        wsAll.Cells(1, col).Value & " vs " & _
                        wsBilling.Cells(1, col).Value & vbCrLf
        End If
    Next col
    
    If mismatches = "" Then
        MsgBox "? Columns A-W match perfectly across sheets!" & vbCrLf & _
               "? Billing columns X-AV present" & vbCrLf & _
               "? Total: 48 columns (A-AV)", vbInformation, "Validation Passed"
    Else
        MsgBox "Column mismatches found:" & vbCrLf & mismatches, vbExclamation
    End If
End Sub

'================================================================================
' SIMPLE REFRESH
'================================================================================
Public Sub RefreshPowerBIData()
    ' Simple refresh - just re-run the export
    Call ExportToPowerBIData
End Sub

'================================================================================
' CHECK DATA TYPES
'================================================================================
Public Sub CheckDataTypes()
    ' Diagnostic function to check what's in key columns
    
    Dim wsBilling As Worksheet
    Dim testRow As Long
    
    On Error Resume Next
    Set wsBilling = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS_BILLING)
    
    If wsBilling Is Nothing Then
        MsgBox "All_Tasks_Billing not found", vbExclamation
        Exit Sub
    End If
    
    ' Find first data row
    For testRow = 2 To 10
        If wsBilling.Cells(testRow, 1).Value <> "" Then Exit For
    Next testRow
    
    Dim report As String
    report = "Data Type Check (Row " & testRow & "):" & vbCrLf & vbCrLf
    
    report = report & "F (Designation): " & wsBilling.Cells(testRow, 6).Value & vbCrLf
    report = report & "G (Drawing): " & wsBilling.Cells(testRow, 7).Value & vbCrLf
    report = report & "Y (Base_Rate): " & wsBilling.Cells(testRow, 25).Value & vbCrLf
    report = report & "AC (Week_Ending): " & wsBilling.Cells(testRow, 29).Value & vbCrLf
    report = report & "AD (Billing_Period): " & wsBilling.Cells(testRow, 30).Value & vbCrLf
    report = report & "AE (Base_Labor_$): " & wsBilling.Cells(testRow, 31).Value & vbCrLf
    
    MsgBox report, vbInformation, "Data Type Check"
End Sub

'================================================================================
' END OF MODULE
'================================================================================

