Attribute VB_Name = "PowerBIExportEnhanced"

' Enhanced PowerBI_LightExport Module with Billing Integration
' Updated to use Global_Constants - 2025-09-22
' ? COMPLIANCE: All column references now use Global_Constants.*

Option Explicit

Public Sub Quick_PowerBI_Export_WithBilling()
    '=== Export with billing data for VP dashboard ===
    
    Dim wsAll As Worksheet, wsBilling As Worksheet, wsPBI As Worksheet
    Dim wsHistory As Worksheet, wsSummary As Worksheet
    Dim startTime As Double
    Dim lastRow As Long, lastCol As Long
    
    startTime = Timer
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    ' Verify sheets exist
    On Error Resume Next
    Set wsAll = ThisWorkbook.Sheets(Global_Constants.SHEET_ALL_TASKS)
    Set wsBilling = ThisWorkbook.Sheets(Global_Constants.SHEET_ALL_TASKS_BILLING)
    Set wsHistory = ThisWorkbook.Sheets("Billing_History")
    Set wsSummary = ThisWorkbook.Sheets("Weekly_Billing_Summary")
    On Error GoTo 0
    
    If wsAll Is Nothing Then
        MsgBox Global_Constants.SHEET_ALL_TASKS & " sheet not found.", vbExclamation
        GoTo Cleanup
    End If
    
    If wsBilling Is Nothing Then
        MsgBox Global_Constants.SHEET_ALL_TASKS_BILLING & " sheet not found. Run PopulateAllTasksBilling first.", vbExclamation
        GoTo Cleanup
    End If
    
    ' Check for data
    lastRow = wsAll.Cells(wsAll.Rows.Count, Global_Constants.AT_COL_TID).End(xlUp).row
    If lastRow <= 1 Then
        MsgBox Global_Constants.SHEET_ALL_TASKS & " appears empty.", vbExclamation
        GoTo Cleanup
    End If
    
    ' Create/Clear PowerBI_Data sheet
    On Error Resume Next
    Set wsPBI = ThisWorkbook.Sheets("PowerBI_Data")
    If wsPBI Is Nothing Then
        Set wsPBI = ThisWorkbook.Sheets.Add(After:=wsAll)
        wsPBI.Name = "PowerBI_Data"
    Else
        wsPBI.Cells.Clear
    End If
    On Error GoTo 0
    
    ' === SECTION 1: Task & Apparatus Data ===
    ' Copy All_Tasks data as values
    lastCol = wsAll.Cells(1, wsAll.Columns.Count).End(xlToLeft).Column
    Dim dataArray As Variant
    dataArray = wsAll.Range(wsAll.Cells(1, 1), wsAll.Cells(lastRow, lastCol)).Value
    wsPBI.Range(wsPBI.Cells(1, 1), wsPBI.Cells(lastRow, lastCol)).Value = dataArray
    
    ' Apply Apparatus_Category mapping using Global_Constants
    wsPBI.Range(wsPBI.Cells(1, Global_Constants.AT_COL_APP), _
                wsPBI.Cells(lastRow, Global_Constants.AT_COL_APP)).Value = _
        wsPBI.Range(wsPBI.Cells(1, Global_Constants.AT_COL_CATEGORY), _
                    wsPBI.Cells(lastRow, Global_Constants.AT_COL_CATEGORY)).Value
    wsPBI.Cells(1, Global_Constants.AT_COL_APP).Value = "Apparatus"
    wsPBI.Columns(Global_Constants.AT_COL_CATEGORY).Delete
    lastCol = lastCol - 1
    
    ' === SECTION 2: Add Billing Columns ===
    If Not wsBilling Is Nothing Then
        Dim billingLastRow As Long
        billingLastRow = wsBilling.Cells(wsBilling.Rows.Count, Global_Constants.AT_COL_SCOPE).End(xlUp).row
        
        ' Add key billing columns
        With wsPBI
            .Cells(1, lastCol + 1).Value = "Week_Ending"
            .Cells(1, lastCol + 2).Value = "Billing_Period"
            .Cells(1, lastCol + 3).Value = "Base_Labor_$"
            .Cells(1, lastCol + 4).Value = "Total_Adders_$"
            .Cells(1, lastCol + 5).Value = "Total_Earned_$"
            .Cells(1, lastCol + 6).Value = "Billed_Flag"
            .Cells(1, lastCol + 7).Value = "Billed_Amount"
            .Cells(1, lastCol + 8).Value = "Earned_Not_Billed"
        End With
        
        ' Copy billing data using Global_Constants
        If billingLastRow > 1 Then
            ' Week Ending
            wsPBI.Range(wsPBI.Cells(2, lastCol + 1), wsPBI.Cells(lastRow, lastCol + 1)).Value = _
                wsBilling.Range(wsBilling.Cells(2, Global_Constants.ATB_COL_WEEK_ENDING), _
                               wsBilling.Cells(lastRow, Global_Constants.ATB_COL_WEEK_ENDING)).Value
            
            ' Billing Period
            wsPBI.Range(wsPBI.Cells(2, lastCol + 2), wsPBI.Cells(lastRow, lastCol + 2)).Value = _
                wsBilling.Range(wsBilling.Cells(2, Global_Constants.ATB_COL_BILLING_PERIOD), _
                               wsBilling.Cells(lastRow, Global_Constants.ATB_COL_BILLING_PERIOD)).Value
            
            ' Base Labor
            wsPBI.Range(wsPBI.Cells(2, lastCol + 3), wsPBI.Cells(lastRow, lastCol + 3)).Value = _
                wsBilling.Range(wsBilling.Cells(2, Global_Constants.ATB_COL_BASE_LABOR), _
                               wsBilling.Cells(lastRow, Global_Constants.ATB_COL_BASE_LABOR)).Value
            
            ' Total Variable Costs (Adders)
            wsPBI.Range(wsPBI.Cells(2, lastCol + 4), wsPBI.Cells(lastRow, lastCol + 4)).Value = _
                wsBilling.Range(wsBilling.Cells(2, Global_Constants.ATB_COL_TOTAL_VAR_COST), _
                               wsBilling.Cells(lastRow, Global_Constants.ATB_COL_TOTAL_VAR_COST)).Value
            
            ' Total Billable
            wsPBI.Range(wsPBI.Cells(2, lastCol + 5), wsPBI.Cells(lastRow, lastCol + 5)).Value = _
                wsBilling.Range(wsBilling.Cells(2, Global_Constants.ATB_COL_TOTAL_BILLABLE), _
                               wsBilling.Cells(lastRow, Global_Constants.ATB_COL_TOTAL_BILLABLE)).Value
            
            ' Process billed flags (if history columns exist)
            Dim r As Long
            For r = 2 To lastRow
                If wsBilling.Cells(r, Global_Constants.ATB_COL_TOTAL_BILLABLE).Value > 0 Then
                    wsPBI.Cells(r, lastCol + 6).Value = "No"  ' Default to not billed
                    wsPBI.Cells(r, lastCol + 7).Value = 0
                    wsPBI.Cells(r, lastCol + 8).Value = wsPBI.Cells(r, lastCol + 5).Value
                Else
                    wsPBI.Cells(r, lastCol + 6).Value = ""
                    wsPBI.Cells(r, lastCol + 7).Value = 0
                    wsPBI.Cells(r, lastCol + 8).Value = 0
                End If
            Next r
        End If
        
        lastCol = lastCol + 8
    End If
    
    ' === SECTION 3: Add Summary Metrics ===
    With wsPBI
        .Cells(1, lastCol + 1).Value = "Data_Quality"
        .Cells(1, lastCol + 2).Value = "Last_Refresh"
        .Cells(1, lastCol + 3).Value = "Row_ID"
        
        For r = 2 To lastRow
            ' Data quality = percentage of filled cells
            .Cells(r, lastCol + 1).Value = Application.CountA(.Range(.Cells(r, 1), .Cells(r, lastCol))) / lastCol
            .Cells(r, lastCol + 2).Value = Now()
            .Cells(r, lastCol + 3).Value = "ROW_" & Format(r - 1, "00000")
        Next r
    End With
    
    ' === SECTION 4: Create KPI Summary Table ===
    Dim kpiRow As Long
    kpiRow = wsPBI.Cells(wsPBI.Rows.Count, Global_Constants.AT_COL_SCOPE).End(xlUp).row + 5
    
    With wsPBI
        .Cells(kpiRow, 1).Value = "KPI_SUMMARY"
        .Cells(kpiRow, 1).Font.Bold = True
        .Cells(kpiRow, 1).Interior.Color = RGB(11, 83, 148)
        .Cells(kpiRow, 1).Font.Color = RGB(255, 255, 255)
        
        kpiRow = kpiRow + 1
        .Cells(kpiRow, 1).Value = "Metric"
        .Cells(kpiRow, 2).Value = "Value"
        .Range(.Cells(kpiRow, 1), .Cells(kpiRow, 2)).Font.Bold = True
        
        ' Calculate KPIs using Global_Constants column letters
        kpiRow = kpiRow + 1
        .Cells(kpiRow, 1).Value = "Total Tasks"
        .Cells(kpiRow, 2).formula = "=COUNTA(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_SCOPE) & _
                                    "2:" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_SCOPE) & lastRow & ")"
        
        kpiRow = kpiRow + 1
        .Cells(kpiRow, 1).Value = "Completed Tasks"
        .Cells(kpiRow, 2).formula = "=COUNTIF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_DATE_COMP) & _
                                    "2:" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_DATE_COMP) & lastRow & ",""<>"")"
        
        kpiRow = kpiRow + 1
        .Cells(kpiRow, 1).Value = "Total Quoted Hours"
        .Cells(kpiRow, 2).formula = "=SUM(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & _
                                    "2:" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & lastRow & ")"
    End With
    
    ' Clean all headers for Power BI
    Dim col As Long
    For col = 1 To wsPBI.Cells(1, wsPBI.Columns.Count).End(xlToLeft).Column
        wsPBI.Cells(1, col).Value = CleanHeader(CStr(wsPBI.Cells(1, col).Value))
    Next col
    
    ' Create Excel tables
    On Error Resume Next
    ' Main data table
    wsPBI.ListObjects.Add(xlSrcRange, wsPBI.Range(wsPBI.Cells(1, 1), wsPBI.Cells(lastRow, lastCol + 3)), , xlYes).Name = "PowerBIData"
    wsPBI.ListObjects("PowerBIData").TableStyle = "TableStyleMedium2"
    On Error GoTo 0
    
Cleanup:
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    
    If Not wsPBI Is Nothing Then
        MsgBox "PowerBI export complete with billing data!" & vbCrLf & _
               "Records: " & lastRow - 1 & vbCrLf & _
               "Using Global_Constants v" & Global_Constants.MODULE_VERSION, vbInformation
    End If
End Sub

Private Function CleanHeader(header As String) As String
    '=== Remove spaces and special characters ===
    Dim clean As String
    clean = header
    clean = Replace(clean, " ", "_")
    clean = Replace(clean, "%", "Pct")
    clean = Replace(clean, "-", "_")
    clean = Replace(clean, "(", "")
    clean = Replace(clean, ")", "")
    clean = Replace(clean, "/", "_")
    clean = Replace(clean, "#", "Num")
    clean = Replace(clean, "&", "And")
    clean = Replace(clean, "+", "_")
    clean = Replace(clean, ".", "")
    clean = Replace(clean, ":", "")
    clean = Replace(clean, "$", "Dollar")
    CleanHeader = clean
End Function

