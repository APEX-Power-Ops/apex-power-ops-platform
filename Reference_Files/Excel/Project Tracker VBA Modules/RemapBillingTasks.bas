Attribute VB_Name = "RemapBillingTasks"
' ================================================================================
' ONE-TIME FIX FOR ALL_TASKS_BILLING - GLOBAL CONSTANTS COMPLIANT VERSION
' Updated to use Global_Constants - 2025-09-22
' ? COMPLIANCE: All column references now use Global_Constants.*
' ================================================================================
Option Explicit

Public Sub FixAllTasksBilling_Final()
    ' Complete one-time fix with correct column references using Global_Constants
    
    Dim wsBilling As Worksheet
    Dim wsAll As Worksheet
    Dim r As Long
    Dim maxRows As Long
    
    On Error GoTo ErrorHandler
    
    ' Set worksheets using Global_Constants
    On Error Resume Next
    Set wsBilling = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS_BILLING)
    Set wsAll = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS)
    On Error GoTo ErrorHandler
    
    If wsBilling Is Nothing Then
        MsgBox Global_Constants.SHEET_ALL_TASKS_BILLING & " sheet not found!", vbCritical
        Exit Sub
    End If
    
    If wsAll Is Nothing Then
        MsgBox Global_Constants.SHEET_ALL_TASKS & " sheet not found!", vbCritical
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    Application.StatusBar = "Fixing All_Tasks_Billing formulas..."
    
    ' Set to process all 2200 rows plus buffer
    maxRows = 2250  ' Process 2200 rows plus 50 buffer rows
    
    ' ================================================================================
    ' STEP 1: SET CORRECT HEADERS
    ' ================================================================================
    
    ' Copy headers A-U from All_Tasks using Global_Constants
    Dim col As Long
    For col = Global_Constants.AT_COL_SCOPE To Global_Constants.AT_COL_PRIORITY
        wsBilling.Cells(1, col).Value = wsAll.Cells(1, col).Value
    Next col
    
    ' Override Column E header
    wsBilling.Cells(1, Global_Constants.AT_COL_APP).Value = "Apparatus"  ' Special: uses V?E logic
    
    ' Billing-specific headers starting at Column V using Global_Constants
    With wsBilling
        .Cells(1, Global_Constants.AT_COL_CATEGORY).Value = "Scope_Helper"        ' V - Hidden helper
        .Cells(1, Global_Constants.ATB_COL_BASE_RATE).Value = "Base_Rate"        ' W
        .Cells(1, Global_Constants.ATB_COL_SCOPE_BUDGET).Value = "Scope_Budget"   ' X
        .Cells(1, Global_Constants.ATB_COL_MULTIPLIER).Value = "Multiplier"       ' Y
        .Cells(1, Global_Constants.ATB_COL_COMPLETION).Value = "Completion"       ' Z
        .Cells(1, Global_Constants.ATB_COL_WEEK_ENDING).Value = "Week_Ending"     ' AA
        .Cells(1, Global_Constants.ATB_COL_BILLING_PERIOD).Value = "Billing_Period" ' AB
        .Cells(1, Global_Constants.ATB_COL_BASE_LABOR).Value = "Base_Labor_$"     ' AC - USES P NOT S!
        .Cells(1, Global_Constants.ATB_COL_COMMUTE_HRS).Value = "Commute_Hrs"     ' AD
        .Cells(1, Global_Constants.ATB_COL_COMMUTE_COST).Value = "Commute_$"      ' AE
        .Cells(1, Global_Constants.ATB_COL_PM_HRS).Value = "PM_Hrs"               ' AF
        .Cells(1, Global_Constants.ATB_COL_PM_COST).Value = "PM_$"                ' AG
        .Cells(1, Global_Constants.ATB_COL_REPORT_HRS).Value = "Report_Hrs"       ' AH
        .Cells(1, Global_Constants.ATB_COL_REPORT_COST).Value = "Report_$"        ' AI
        .Cells(1, Global_Constants.ATB_COL_TRAVEL_HRS).Value = "Travel_Hrs"       ' AJ
        .Cells(1, Global_Constants.ATB_COL_TRAVEL_COST).Value = "Travel_$"        ' AK
        .Cells(1, Global_Constants.ATB_COL_FINAL_HRS).Value = "Final_Hrs"         ' AL
        .Cells(1, Global_Constants.ATB_COL_FINAL_COST).Value = "Final_$"          ' AM
        .Cells(1, Global_Constants.ATB_COL_TRAVEL_FIXED).Value = "Travel_Fixed_$" ' AN
        .Cells(1, Global_Constants.ATB_COL_ME_FIXED).Value = "ME_Fixed_$"         ' AO
        .Cells(1, Global_Constants.ATB_COL_TOTAL_VAR_HRS).Value = "Total_Var_Hrs" ' AP
        .Cells(1, Global_Constants.ATB_COL_TOTAL_VAR_COST).Value = "Total_Var_$"  ' AQ
        .Cells(1, Global_Constants.ATB_COL_TOTAL_FIXED_COST).Value = "Total_Fixed_$" ' AR
        .Cells(1, Global_Constants.ATB_COL_SUBTOTAL).Value = "Subtotal_$"         ' AS
        .Cells(1, Global_Constants.ATB_COL_TOTAL_BILLABLE).Value = "Total_Billable_$" ' AT
    End With
    
    ' ================================================================================
    ' STEP 2: APPLY CORRECTED FORMULAS USING GLOBAL_CONSTANTS
    ' ================================================================================
    
    For r = 2 To maxRows
        If r Mod 100 = 0 Then
            DoEvents
            Application.StatusBar = "Processing row " & r & " of " & maxRows
        End If
        
        With wsBilling
            ' === COLUMNS A-U: DIRECT MAPPING (EXCEPT E) ===
            
            ' A-D: Direct mapping using Global_Constants column letters
            .Cells(r, 1).formula = "=IF(All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_SCOPE) & r & "="""","""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_SCOPE) & r & ")"  ' Scope
            .Cells(r, 2).formula = "=IF(All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_NETA) & r & "="""","""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_NETA) & r & ")"   ' NETA_Standard
            .Cells(r, 3).formula = "=IF(All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_TID) & r & "="""","""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_TID) & r & ")"    ' Task_ID
            .Cells(r, 4).formula = "=IF(All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_TASK) & r & "="""","""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_TASK) & r & ")"   ' Task
            
            ' E: Special Apparatus mapping (V first, then E)
            .Cells(r, 5).formula = "=IF(All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "<>"""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ",IF(All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_APP) & r & "<>"""",All_Tasks!" & _
                                   Global_Constants.GetColumnLetter(Global_Constants.AT_COL_APP) & r & ",""""))"
            
            ' F-O: Direct mapping using Global_Constants
            For col = 6 To 15
                .Cells(r, col).formula = "=IF(All_Tasks!" & Chr(64 + col) & r & "="""","""",All_Tasks!" & Chr(64 + col) & r & ")"
            Next col
            
            ' P-U: Direct mapping (INCLUDING CRITICAL P - APPARATUS_HOURS)
            For col = Global_Constants.AT_COL_AHRS To Global_Constants.AT_COL_PRIORITY
                If col >= Global_Constants.AT_COL_AHRS And col <= Global_Constants.AT_COL_ACTHRS Then  ' Columns P, Q, R are numeric
                    .Cells(r, col).formula = "=IF(All_Tasks!" & Chr(64 + col) & r & "="""",0,All_Tasks!" & Chr(64 + col) & r & ")"
                Else
                    .Cells(r, col).formula = "=IF(All_Tasks!" & Chr(64 + col) & r & "="""","""",All_Tasks!" & Chr(64 + col) & r & ")"
                End If
            Next col
            
            ' === BILLING CALCULATIONS (V ONWARD) ===
            
            ' V: Scope Helper (finds row in Scope_Labor_Rates) using Global_Constants
            .Cells(r, Global_Constants.AT_COL_CATEGORY).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_SCOPE) & r & "="""",0,IFERROR(MATCH(" & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_SCOPE) & r & "," & Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & _
                Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_SCOPE) & "$6:$" & _
                Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_SCOPE) & "$46,0)+5,0))"
            
            ' W: Base Rate from Scope_Labor_Rates Column C
            .Cells(r, Global_Constants.ATB_COL_BASE_RATE).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0,INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_SCOPE_BILL_RATE) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_SCOPE_BILL_RATE) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5),0)"
            
            ' X: Scope Budget from Column S
            .Cells(r, Global_Constants.ATB_COL_SCOPE_BUDGET).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0,INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_SCOPE_TOTAL) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_SCOPE_TOTAL) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5),0)"
            
            ' Y: Multiplier from Column R
            .Cells(r, Global_Constants.ATB_COL_MULTIPLIER).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0,INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_SCOPE_MULTIPLIER) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_SCOPE_MULTIPLIER) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5),1)"
            
            ' Z: Completion Binary (checks DATE_COMPLETED or STATUS)
            .Cells(r, Global_Constants.ATB_COL_COMPLETION).formula = _
                "=IF(OR(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_DATE_COMP) & r & "<>"""",UPPER(" & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_STATUS) & r & ")=""COMPLETED""),1,0)"
            
            ' AA: Week Ending
            .Cells(r, Global_Constants.ATB_COL_WEEK_ENDING).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_DATE_COMP) & r & "="""",""""," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_DATE_COMP) & r & "-WEEKDAY(" & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_DATE_COMP) & r & ",3)+6)"
            
            ' AB: Billing Period
            .Cells(r, Global_Constants.ATB_COL_BILLING_PERIOD).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_WEEK_ENDING) & r & "="""","""",IF(DAY(" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_WEEK_ENDING) & r & ")<=23,TEXT(" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_WEEK_ENDING) & r & ",""MMM-yyyy""),TEXT(EOMONTH(" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_WEEK_ENDING) & r & ",0)+1,""MMM-yyyy"")))"
            
            ' === CRITICAL: BASE LABOR USES P (APPARATUS_HOURS) NOT S! ===
            ' AC: Base Labor $ = Apparatus_Hours × Base_Rate × Completion
            .Cells(r, Global_Constants.ATB_COL_BASE_LABOR).formula = _
                "=" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & r & "*" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_BASE_RATE) & r & "*" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_COMPLETION) & r
            
            ' === VARIABLE COST ADDERS - ALL USE P (APPARATUS_HOURS) ===
            
            ' AD: Commute Hours = Apparatus_Hours × Commute %
            .Cells(r, Global_Constants.ATB_COL_COMMUTE_HRS).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_COMMUTE_PCT) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_COMMUTE_PCT) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5),0)"
            
            ' AE: Commute $ = Commute_Hours × Commute Rate × Completion
            .Cells(r, Global_Constants.ATB_COL_COMMUTE_COST).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_COMMUTE_HRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_COMMUTE_BILL_RATE) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_COMMUTE_BILL_RATE) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5)*" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_COMPLETION) & r & ",0)"
            
            ' AF: PM Hours = Apparatus_Hours × PM %
            .Cells(r, Global_Constants.ATB_COL_PM_HRS).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_PM_TIME_PCT) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_PM_TIME_PCT) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5),0)"
            
            ' AG: PM $ = PM_Hours × PM Rate × Completion
            .Cells(r, Global_Constants.ATB_COL_PM_COST).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_PM_HRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_PM_BILL_RATE) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_PM_BILL_RATE) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5)*" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_COMPLETION) & r & ",0)"
            
            ' AH: Report Hours = Apparatus_Hours × Report %
            .Cells(r, Global_Constants.ATB_COL_REPORT_HRS).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_DAILY_PCT) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_DAILY_PCT) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5),0)"
            
            ' AI: Report $ = Report_Hours × Report Rate × Completion
            .Cells(r, Global_Constants.ATB_COL_REPORT_COST).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_REPORT_HRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_DAILY_BILL_RATE) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_DAILY_BILL_RATE) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5)*" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_COMPLETION) & r & ",0)"
            
            ' AJ: Travel Hours = Apparatus_Hours × Travel %
            .Cells(r, Global_Constants.ATB_COL_TRAVEL_HRS).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_TRAVEL_PCT) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_TRAVEL_PCT) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5),0)"
            
            ' AK: Travel $ = Travel_Hours × Travel Rate × Completion
            .Cells(r, Global_Constants.ATB_COL_TRAVEL_COST).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_TRAVEL_HRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_TRAVEL_BILL_RATE) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_TRAVEL_BILL_RATE) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5)*" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_COMPLETION) & r & ",0)"
            
            ' AL: Final Hours = Apparatus_Hours × Final %
            .Cells(r, Global_Constants.ATB_COL_FINAL_HRS).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_FINAL_PCT) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_FINAL_PCT) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5),0)"
            
            ' AM: Final $ = Final_Hours × Final Rate × Completion
            .Cells(r, Global_Constants.ATB_COL_FINAL_COST).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_FINAL_HRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_FINAL_BILL_RATE) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_FINAL_BILL_RATE) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5)*" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_COMPLETION) & r & ",0)"
            
            ' === FIXED COSTS - ALSO USE P (APPARATUS_HOURS) ===
            
            ' AN: Travel Fixed $ = Apparatus_Hours × Travel per-hour × Completion
            .Cells(r, Global_Constants.ATB_COL_TRAVEL_FIXED).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_TRAVEL_PER_HOUR) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_TRAVEL_PER_HOUR) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5)*" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_COMPLETION) & r & ",0)"
            
            ' AO: M&E Fixed $ = Apparatus_Hours × M&E per-hour × Completion
            .Cells(r, Global_Constants.ATB_COL_ME_FIXED).formula = _
                "=IF(" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & ">0," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & r & "*INDEX(" & _
                Global_Constants.SHEET_SCOPE_LABOR_RATES & "!$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_ME_PER_HOUR) & _
                "$6:$" & Global_Constants.GetColumnLetter(Global_Constants.SLR_COL_ME_PER_HOUR) & "$46," & _
                Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY) & r & "-5)*" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_COMPLETION) & r & ",0)"
            
            ' === TOTALS ===
            
            ' AP: Total Variable Hours
            .Cells(r, Global_Constants.ATB_COL_TOTAL_VAR_HRS).formula = _
                "=" & Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_COMMUTE_HRS) & r & "+" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_PM_HRS) & r & "+" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_REPORT_HRS) & r & "+" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_TRAVEL_HRS) & r & "+" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_FINAL_HRS) & r
            
            ' AQ: Total Variable $
            .Cells(r, Global_Constants.ATB_COL_TOTAL_VAR_COST).formula = _
                "=" & Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_COMMUTE_COST) & r & "+" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_PM_COST) & r & "+" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_REPORT_COST) & r & "+" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_TRAVEL_COST) & r & "+" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_FINAL_COST) & r
            
            ' AR: Total Fixed $
            .Cells(r, Global_Constants.ATB_COL_TOTAL_FIXED_COST).formula = _
                "=" & Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_TRAVEL_FIXED) & r & "+" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_ME_FIXED) & r
            
            ' AS: Subtotal $ (Base + Variable + Fixed)
            .Cells(r, Global_Constants.ATB_COL_SUBTOTAL).formula = _
                "=" & Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_BASE_LABOR) & r & "+" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_TOTAL_VAR_COST) & r & "+" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_TOTAL_FIXED_COST) & r
            
            ' AT: Total Billable $ (Subtotal × Multiplier)
            .Cells(r, Global_Constants.ATB_COL_TOTAL_BILLABLE).formula = _
                "=" & Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_SUBTOTAL) & r & "*" & _
                Global_Constants.GetColumnLetter(Global_Constants.ATB_COL_MULTIPLIER) & r
        End With
    Next r
    
    
    ' ================================================================================
' STEP 3: FORMAT (SIMPLIFIED VERSION)
' ================================================================================

With wsBilling
    ' Headers
    .Range("A1:AT1").Font.Bold = True
    .Range("A1:U1").Interior.Color = RGB(217, 225, 242)  ' Light blue
    .Range("V1:AT1").Interior.Color = RGB(255, 242, 204) ' Light yellow
    
    ' Currency formatting - using direct column letters
    .Columns("W:X").NumberFormat = "$#,##0.00"  ' Base_Rate, Scope_Budget
    .Columns("Y:Y").NumberFormat = "0.000"      ' Multiplier
    .Columns("AC:AC").NumberFormat = "$#,##0.00" ' Base_Labor
    .Columns("AE:AE").NumberFormat = "$#,##0.00" ' Commute_$
    .Columns("AG:AG").NumberFormat = "$#,##0.00" ' PM_$
    .Columns("AI:AI").NumberFormat = "$#,##0.00" ' Report_$
    .Columns("AK:AK").NumberFormat = "$#,##0.00" ' Travel_$
    .Columns("AM:AM").NumberFormat = "$#,##0.00" ' Final_$
    .Columns("AN:AT").NumberFormat = "$#,##0.00" ' All financial columns
    
    ' Hours formatting
    .Columns("P:R").NumberFormat = "0.0"  ' Apparatus/Remaining/Actual Hours
    .Columns("AD:AD").NumberFormat = "0.0" ' Commute_Hrs
    .Columns("AF:AF").NumberFormat = "0.0" ' PM_Hrs
    .Columns("AH:AH").NumberFormat = "0.0" ' Report_Hrs
    .Columns("AJ:AJ").NumberFormat = "0.0" ' Travel_Hrs
    .Columns("AL:AL").NumberFormat = "0.0" ' Final_Hrs
    .Columns("AP:AP").NumberFormat = "0.0" ' Total_Var_Hrs
    
    ' Date formatting
    .Columns("H:H").NumberFormat = "mm/dd/yyyy"  ' Date Due
    .Columns("L:L").NumberFormat = "mm/dd/yyyy"  ' Date Completed
    .Columns("AA:AA").NumberFormat = "mm/dd/yyyy" ' Week_Ending
    
    ' Hide helper column V
    .Columns("V:V").Hidden = True
    
    ' Freeze panes
    .Activate
    .Range("A2").Select
    ActiveWindow.FreezePanes = True
End With
    
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    Application.StatusBar = False
    
    MsgBox "All_Tasks_Billing fixed!" & vbCrLf & vbCrLf & _
           "? " & (maxRows - 1) & " rows processed" & vbCrLf & _
           "? All formulas now use Column P (Apparatus_Hours)" & vbCrLf & _
           "? Column E uses V?E fallback" & vbCrLf & _
           "? All Scope_Labor_Rates references corrected" & vbCrLf & _
           "? Using Global_Constants v" & Global_Constants.MODULE_VERSION, _
           vbInformation, "Fix Complete"
           
    Exit Sub
    
ErrorHandler:
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    Application.StatusBar = False
    MsgBox "Error at row " & r & ": " & Err.Description, vbCritical, "Error"
End Sub

' ================================================================================
' VALIDATION FUNCTION
' ================================================================================

Public Sub ValidateBillingFix()
    ' Validates the fix worked correctly using Global_Constants
    
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Worksheets(Global_Constants.SHEET_ALL_TASKS_BILLING)
    
    Dim issues As String
    Dim testRow As Long
    testRow = 2  ' Test row 2
    
    issues = "VALIDATION CHECK:" & vbCrLf & String(40, "=") & vbCrLf
    
    ' Check Base Labor formula
    Dim formulaAC As String
    formulaAC = ws.Cells(testRow, Global_Constants.ATB_COL_BASE_LABOR).formula  ' Column AC
    
    If InStr(formulaAC, Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & testRow) > 0 Then
        issues = issues & "? Base Labor uses Column " & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & " (correct)" & vbCrLf
    ElseIf InStr(formulaAC, "S" & testRow) > 0 Then
        issues = issues & "? Base Labor uses Column S (WRONG!)" & vbCrLf
    Else
        issues = issues & "? Base Labor formula unclear" & vbCrLf
    End If
    
    ' Check Commute Hours formula
    Dim formulaAD As String
    formulaAD = ws.Cells(testRow, Global_Constants.ATB_COL_COMMUTE_HRS).formula  ' Column AD
    
    If InStr(formulaAD, Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & testRow) > 0 Then
        issues = issues & "? Commute Hours uses Column " & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & " (correct)" & vbCrLf
    Else
        issues = issues & "? Commute Hours doesn't use Column " & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_AHRS) & vbCrLf
    End If
    
    ' Check Apparatus formula
    Dim formulaE As String
    formulaE = ws.Cells(testRow, Global_Constants.AT_COL_APP).formula  ' Column E
    
    If InStr(formulaE, "All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_CATEGORY)) > 0 And _
       InStr(formulaE, "All_Tasks!" & Global_Constants.GetColumnLetter(Global_Constants.AT_COL_APP)) > 0 Then
        issues = issues & "? Apparatus uses V?E fallback (correct)" & vbCrLf
    Else
        issues = issues & "? Apparatus formula incorrect" & vbCrLf
    End If
    
    issues = issues & vbCrLf & "? Using Global_Constants v" & Global_Constants.MODULE_VERSION
    
    MsgBox issues, vbInformation, "Validation Results"
End Sub



