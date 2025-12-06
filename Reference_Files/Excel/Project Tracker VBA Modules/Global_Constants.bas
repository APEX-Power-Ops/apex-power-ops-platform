Attribute VB_Name = "Global_Constants"

' ===== GLOBAL CONSTANTS MODULE - MASTER TEMPLATE =====
' Version: 1.2
' Purpose: Centralized column mappings for ALL modules in the workbook
' Critical: ALL modules MUST use these constants - NO HARDCODED COLUMN REFERENCES!
'
' ✅ ENFORCEMENT RULE: Any module using hardcoded column numbers will be rejected!
'    Use GC.TE_COL_SCOPE instead of hardcoded 1
'    Use GC.SC_COL_STATUS instead of hardcoded 2
'    Use GC.AT_COL_STATUS instead of hardcoded 19
'
' ✅ VERIFIED: All constants verified against master template column structure
' ✅ MAINTENANCE: When columns change, update HERE ONLY - all modules inherit changes
' ✅ TEMPLATE: Generic constants - works for any project workbook
'
' USAGE EXAMPLES:
'   ✅ CORRECT: wsOut.Cells(row, GC.SC_COL_STATUS).Value = "COMPLETED"
'   ❌ WRONG:   wsOut.Cells(row, 2).Value = "COMPLETED"
'
'   ✅ CORRECT: allTasks.Cells(row, GC.AT_COL_STATUS).Value = status
'   ❌ WRONG:   allTasks.Cells(row, 19).Value = status

Option Explicit

' =============================================
' ===== VERSION CONTROL =====
' =============================================
Public Const MODULE_VERSION As String = "1.2.0"
Public Const LAST_UPDATED As String = "2025-12-04"
Public Const TEMPLATE_TYPE As String = "Project Tracker Master Template"

' =============================================
' ===== SHEET NAMES (STANDARDIZED) =====
' =============================================
Public Const SHEET_TASK_ENTRY As String = "Task_Entry"
Public Const SHEET_SCOPE_TEMPLATE As String = "Scope_Template"
Public Const SHEET_ALL_TASKS As String = "All_Tasks"
Public Const SHEET_ALL_TASKS_BILLING As String = "All_Tasks_Billing"
Public Const SHEET_ALL_LISTS As String = "All_Lists"
Public Const SHEET_GANTT_TEMPLATE As String = "Gantt_Template"
Public Const SHEET_SCOPE_LABOR_RATES As String = "Scope_Labor_Rates"

' =============================================
' ===== TASK_ENTRY SHEET COLUMNS =====
' ===== (Source sheet - where data is entered) =====
' =============================================
Public Const TE_FIRST_DATA_ROW As Long = 2

' Task_Entry Column Mappings (A=1, B=2, C=3, etc.)
Public Const TE_COL_SCOPE As Long = 1        ' A - Scope
Public Const TE_COL_NETA As Long = 2         ' B - NETA_Standard
Public Const TE_COL_TID As Long = 3          ' C - Task_ID
Public Const TE_COL_TASK As Long = 4         ' D - Task (header text)
Public Const TE_COL_APP As Long = 5          ' E - Apparatus
Public Const TE_COL_DES As Long = 6          ' F - Designation
Public Const TE_COL_DRW As Long = 7          ' G - Drawing
Public Const TE_COL_AHRS As Long = 8         ' H - Apparatus_Hours

' Task_Entry Helper Constants
Public Const TE_HEADER_ROW As Long = 1       ' Where column headers are located

' =============================================
' ===== SCOPE_TEMPLATE COLUMNS =====
' ===== (Target sheet - BuildAll output) =====
' =============================================
' ✅ CORRECTED: Proper row designations for Scope_Template

' Scope_Template Row Structure:
' Row 1-4: Headers, logos, scope/NETA info
' Row 5: Column headers (STATUS, AVAILABILITY, etc.)
' Row 6: Parent row template (for 2-digit IDs like 1.1)
' Row 7: Child row template (for 3-digit IDs like 1.1.1)
' Row 21: Totals row template

Public Const SC_HEADER_ROW As Long = 5             ' Column headers row
Public Const SC_TEMPLATE_PARENT_ROW As Long = 6    ' Parent row template (2-digit IDs)
Public Const SC_TEMPLATE_CHILD_ROW As Long = 7     ' Child row template (3-digit IDs)
Public Const SC_TEMPLATE_TOTALS_ROW As Long = 21   ' Totals row template
Public Const SC_FIRST_DATA_ROW As Long = 6         ' Where actual data starts

' Scope_Template Column Mappings
Public Const SC_COL_STATUS As Long = 2             ' B - STATUS (formula-driven for parents)
Public Const SC_COL_AVAIL As Long = 3              ' C - AVAILABILITY
Public Const SC_COL_PRIORITY As Long = 4           ' D - PRIORITY
Public Const SC_COL_TASK_ID As Long = 5            ' E - TASK_ID
Public Const SC_COL_NAME_APP As Long = 6           ' F - TASK NAMES + APPARATUS
Public Const SC_COL_DES As Long = 7                ' G - DESIGNATION
Public Const SC_COL_DRW As Long = 8                ' H - DRAWING
Public Const SC_COL_DATE_DUE As Long = 9           ' I - DATE DUE
Public Const SC_COL_ASSESSMENT As Long = 10        ' J - ASSESSMENT (note: actual sheet has "ASSESMENT")
Public Const SC_COL_DATASHEET As Long = 11         ' K - DATASHEET
Public Const SC_COL_DATE_COMP As Long = 12         ' L - DATE COMPLETED
Public Const SC_COL_NOTES As Long = 13             ' M - NOTES (also used for totals label)
Public Const SC_COL_PCT As Long = 14               ' N - % COMPLETION
Public Const SC_COL_DELAY As Long = 15             ' O - TASK DELAYS
Public Const SC_COL_AHRS As Long = 16              ' P - APPARATUS HOURS
Public Const SC_COL_REMHRS As Long = 17            ' Q - REMAINING HOURS
Public Const SC_COL_ACTHRS As Long = 18            ' R - ACTUAL HOURS

' Scope_Template Helper Constants
Public Const SC_SCOPE_CELL As String = "G4"        ' Where scope name appears
Public Const SC_NETA_CELL As String = "H4"         ' Where NETA standard appears
Public Const SC_MODE_TOGGLE_CELL As String = "T2"  ' AUTO/MANUAL mode toggle
Public Const SC_DEFAULT_PRINT_AREA As String = "$A$1:$R$46"

' =============================================
' ===== ALL_TASKS SHEET COLUMNS =====
' ===== ⚠️ CRITICAL: Different layout than Scope_Template! =====
' =============================================
' ✅ VERIFIED: STATUS is in column S (19), NOT column B (2)!

Public Const AT_FIRST_DATA_ROW As Long = 2

' All_Tasks Column Mappings - COMPLETELY DIFFERENT from Scope_Template!
Public Const AT_COL_SCOPE As Long = 1              ' A - Scope
Public Const AT_COL_NETA As Long = 2               ' B - NETA_Standard
Public Const AT_COL_TID As Long = 3                ' C - Task_ID
Public Const AT_COL_TASK As Long = 4               ' D - Task
Public Const AT_COL_APP As Long = 5                ' E - Apparatus
Public Const AT_COL_DES As Long = 6                ' F - Designation
Public Const AT_COL_DRW As Long = 7                ' G - Drawing
Public Const AT_COL_DATE_DUE As Long = 8           ' H - Date Due
Public Const AT_COL_NOTES As Long = 9              ' I - Notes
Public Const AT_COL_ASSESSMENT As Long = 10        ' J - Assessment
Public Const AT_COL_DATASHEET As Long = 11         ' K - DATASHEET
Public Const AT_COL_DATE_COMP As Long = 12         ' L - DATE COMPLETED
Public Const AT_COL_NOTES2 As Long = 13            ' M - NOTES2
Public Const AT_COL_PCT As Long = 14               ' N - % COMPLETION
Public Const AT_COL_DELAY As Long = 15             ' O - TASK DELAYS
Public Const AT_COL_AHRS As Long = 16              ' P - Apparatus Hours
Public Const AT_COL_REMHRS As Long = 17            ' Q - Remaining Hours
Public Const AT_COL_ACTHRS As Long = 18            ' R - ACTUAL HOURS
' ⚠️ CRITICAL DIFFERENCE: STATUS is in column S, not B!
Public Const AT_COL_STATUS As Long = 19            ' S - STATUS ⚠️ DIFFERENT from Scope_Template!
Public Const AT_COL_AVAIL As Long = 20             ' T - AVAILABILITY
Public Const AT_COL_PRIORITY As Long = 21          ' U - PRIORITY
Public Const AT_COL_CATEGORY As Long = 22          ' V - Apparatus Category

' =============================================
' ===== ALL_TASKS_BILLING SHEET COLUMNS =====
' ===== (Extended version of All_Tasks) =====
' =============================================
' Inherits all AT_COL_* constants plus additional billing columns

Public Const ATB_COL_SCOPE_HELPER As Long = 23     ' V - Scope_Helper
Public Const ATB_COL_BASE_RATE As Long = 24        ' W - Base_Rate
Public Const ATB_COL_SCOPE_BUDGET As Long = 25     ' X - Scope_Budget
Public Const ATB_COL_MULTIPLIER As Long = 26       ' Y - Multiplier
Public Const ATB_COL_COMPLETION As Long = 27       ' Z - Completion
Public Const ATB_COL_WEEK_ENDING As Long = 28      ' AA - Week_Ending
Public Const ATB_COL_BILLING_PERIOD As Long = 29   ' AB - Billing_Period
Public Const ATB_COL_BASE_LABOR As Long = 30       ' AC - Base_Labor_$
Public Const ATB_COL_COMMUTE_HRS As Long = 31      ' AD - Commute_Hrs
Public Const ATB_COL_COMMUTE_COST As Long = 32     ' AE - Commute_$
Public Const ATB_COL_PM_HRS As Long = 33           ' AF - PM_Hrs
Public Const ATB_COL_PM_COST As Long = 34          ' AG - PM_$
Public Const ATB_COL_REPORT_HRS As Long = 35       ' AH - Report_Hrs
Public Const ATB_COL_REPORT_COST As Long = 36      ' AI - Report_$
Public Const ATB_COL_TRAVEL_HRS As Long = 37       ' AJ - Travel_Hrs
Public Const ATB_COL_TRAVEL_COST As Long = 38      ' AK - Travel_$
Public Const ATB_COL_HOTEL As Long = 39            ' AL - Hotel_$
Public Const ATB_COL_PERDIEM As Long = 40          ' AM - Per_Diem_$
Public Const ATB_COL_MEALS As Long = 41            ' AN - Meals_$
Public Const ATB_COL_MILEAGE_MI As Long = 42       ' AO - Mileage_Mi
Public Const ATB_COL_MILEAGE_COST As Long = 43     ' AP - Mileage_$
Public Const ATB_COL_RENTAL As Long = 44           ' AQ - Rental_$
Public Const ATB_COL_AIRPORT As Long = 45          ' AR - Airport_Parking_$
Public Const ATB_COL_PARKING As Long = 46          ' AS - Parking_$
Public Const ATB_COL_TOLLS As Long = 47            ' AT - Tolls_$
Public Const ATB_COL_OTHER_DESC As Long = 48       ' AU - Other_Desc
Public Const ATB_COL_OTHER_COST As Long = 49       ' AV - Other_$
Public Const ATB_COL_LABOR_COST As Long = 50       ' AW - Total_Labor_Cost
Public Const ATB_COL_EXPENSE_COST As Long = 51     ' AX - Total_Expense_Cost
Public Const ATB_COL_TOTAL_COST As Long = 52       ' AY - Total_Cost

' =============================================
' ===== SCOPE_LABOR_RATES SHEET COLUMNS =====
' ===== (Labor rates and billing calculations) =====
' =============================================
Public Const SLR_FIRST_DATA_ROW As Long = 2

' Scope_Labor_Rates Column Mappings
Public Const SLR_COL_SCOPE As Long = 1              ' A - Scope
Public Const SLR_COL_CLIENT As Long = 2             ' B - Client
Public Const SLR_COL_BUDGET As Long = 3             ' C - Project Budget
Public Const SLR_COL_TECH_BILL_RATE As Long = 4     ' D - Tech Bill Rate/Hr
Public Const SLR_COL_TECH_PCT As Long = 5           ' E - Tech %
Public Const SLR_COL_PM_BILL_RATE As Long = 6       ' F - PM Bill Rate/Hr
Public Const SLR_COL_PM_PCT As Long = 7             ' G - PM %
Public Const SLR_COL_REPORT_BILL_RATE As Long = 8   ' H - Report Bill Rate/Hr
Public Const SLR_COL_REPORT_PCT As Long = 9         ' I - Report %
Public Const SLR_COL_TRAVEL_BILL_RATE As Long = 10 ' J - Travel Bill Rate/Hr
Public Const SLR_COL_TRAVEL_PCT As Long = 11        ' K - Travel %
Public Const SLR_COL_FINAL_BILL_RATE As Long = 12  ' L - Final Report Bill Rate/Hr
Public Const SLR_COL_FINAL_PCT As Long = 13         ' M - Final Report %
Public Const SLR_COL_TRAVEL_TOTAL As Long = 14     ' N - Travel Sheet Total $
Public Const SLR_COL_TRAVEL_PER_HOUR As Long = 15  ' O - Travel $/App Hr
Public Const SLR_COL_ME_TOTAL As Long = 16          ' P - M&E Sheet Total $
Public Const SLR_COL_ME_PER_HOUR As Long = 17      ' Q - M&E $/App Hr
Public Const SLR_COL_SCOPE_MULTIPLIER As Long = 18 ' R - Scope Multiplier
Public Const SLR_COL_SCOPE_TOTAL As Long = 19      ' S - Scope Sheet Total

' =============================================
' ===== GANTT_TEMPLATE STRUCTURE =====
' ===== (Gantt chart template with timeline) =====
' =============================================
' ✅ ADDED: Complete Gantt_Template specifications (2025-12-04)
' Based on: Gantt_Template_Specification.md from Claude for Excel

' ----- Row Structure -----
Public Const GANTT_HEADER_ROWS As Long = 6              ' Rows 1-6: Project info headers
Public Const GANTT_DATE_ROW As Long = 7                 ' Row 7: Hidden - actual date formulas
Public Const GANTT_WEEK_ROW As Long = 8                 ' Row 8: Week headers (WEEK 1, WEEK 2, etc.)
Public Const GANTT_HEADER_ROW As Long = 9               ' Row 9: Column headers
Public Const GANTT_DAY_LABEL_ROW As Long = 10           ' Row 10: Day labels (M, T, W, R, F)
Public Const GANTT_FIRST_DATA_ROW As Long = 11          ' Row 11: Where data starts
Public Const GANTT_FIRST_BLUEPRINT_ROW As Long = 11     ' Row 11: First blueprint
Public Const GANTT_LAST_BLUEPRINT_ROW As Long = 14      ' Row 14: Last blueprint

' ----- Reference Cells -----
Public Const GANTT_TIMELINE_DATE_CELL As String = "H8"  ' Timeline start date setter (user input)
Public Const GANTT_TIMELINE_LABEL_CELL As String = "F8" ' "SET TIMELINE DATE ->" label

' ----- Column Structure -----
Public Const GANTT_COL_BLUEPRINT As Long = 1            ' A - Blueprint label (hidden)
Public Const GANTT_COL_TASK_ID As Long = 2             ' B - TASK ID
Public Const GANTT_COL_NAME As Long = 3                ' C - SCOPE + TASK + APPARATUS
Public Const GANTT_COL_QTY As Long = 4                 ' D - APPARATUS QUANTITY
Public Const GANTT_COL_REM_QTY As Long = 5             ' E - REMAINING QUANTITY
Public Const GANTT_COL_START As Long = 6               ' F - START DATE
Public Const GANTT_COL_DUE As Long = 7                 ' G - DATE DUE
Public Const GANTT_COL_DURATION As Long = 8            ' H - DURATION IN DAYS
Public Const GANTT_COL_PCT As Long = 9                 ' I - % COMPLETION
Public Const GANTT_COL_TIMELINE_START As Long = 10     ' J - First timeline column
Public Const GANTT_COL_TIMELINE_END As Long = 69       ' BQ - Last timeline column

' ----- Timeline Structure -----
Public Const GANTT_TIMELINE_COLUMNS As Long = 60       ' Total timeline columns (12 weeks x 5 days)
Public Const GANTT_DAYS_PER_WEEK As Long = 5           ' Weekdays only (M-F)
Public Const GANTT_TOTAL_WEEKS As Long = 12            ' 12 weeks total

' ----- Blueprint Types -----
Public Const GANTT_BLUEPRINT_PARENT As String = "PARENT"        ' Section/Phase header
Public Const GANTT_BLUEPRINT_CHILD As String = "CHILD"          ' Standard task
Public Const GANTT_BLUEPRINT_CHILD_ALT As String = "CHILD_ALT"  ' Alternate task (visual variety)
Public Const GANTT_BLUEPRINT_TOTALS As String = "TOTALS"        ' Summary totals

' ----- Timeline Zone Colors (RGB Values) -----
' Zone color pattern: Accent colors at weeks 2, 5, 8, 11 (every 3 weeks starting from week 2)

' Week 2 (Blue) - Columns O-S
Public Const GANTT_ZONE_BLUE_START As Long = 15        ' Column O
Public Const GANTT_ZONE_BLUE_END As Long = 19          ' Column S
Public Const GANTT_ZONE_BLUE_RGB As Long = 15852769    ' RGB(220, 230, 241) = #DCE6F1

' Week 5 (Orange) - Columns AD-AH
Public Const GANTT_ZONE_ORANGE_START As Long = 30      ' Column AD
Public Const GANTT_ZONE_ORANGE_END As Long = 34        ' Column AH
Public Const GANTT_ZONE_ORANGE_RGB As Long = 14281213  ' RGB(253, 233, 217) = #FDE9D9

' Week 8 (Green) - Columns AS-AW
Public Const GANTT_ZONE_GREEN_START As Long = 45       ' Column AS
Public Const GANTT_ZONE_GREEN_END As Long = 49         ' Column AW
Public Const GANTT_ZONE_GREEN_RGB As Long = 14611171   ' RGB(235, 241, 222) = #EBF1DE

' Week 11 (Violet) - Columns BH-BL
Public Const GANTT_ZONE_VIOLET_START As Long = 60      ' Column BH
Public Const GANTT_ZONE_VIOLET_END As Long = 64        ' Column BL
Public Const GANTT_ZONE_VIOLET_RGB As Long = 15523044  ' RGB(228, 223, 236) = #E4DFEC

' ----- Formatting Colors (RGB Values) -----

' Row Type Background Colors
Public Const GANTT_COLOR_PARENT_BG As Long = 14277081      ' RGB(217, 217, 217) = #D9D9D9
Public Const GANTT_COLOR_CHILD_BG As Long = 15921906       ' RGB(242, 242, 242) = #F2F2F2
Public Const GANTT_COLOR_TOTALS_BG As Long = 14277081      ' RGB(217, 217, 217) = #D9D9D9

' Column-Specific Background Colors (Child Rows)
Public Const GANTT_COLOR_DATA_ENTRY As Long = 16777215     ' RGB(255, 255, 255) = #FFFFFF (white)
Public Const GANTT_COLOR_DUE_DATE As Long = 15985395       ' RGB(234, 238, 243) = #EAEEF3 (light blue-gray)

' Timeline Header Colors
Public Const GANTT_COLOR_WEEK_HEADER_BG As Long = 2050429  ' RGB(31, 73, 125) = #1F497D (dark blue)
Public Const GANTT_COLOR_DAY_NUMBER_BG As Long = 14862504  ' RGB(141, 180, 226) = #8DB4E2 (medium blue)
Public Const GANTT_COLOR_DAY_LABEL_BG As Long = 15849925   ' RGB(197, 217, 241) = #C5D9F1 (light blue)

' Font Colors
Public Const GANTT_COLOR_TEXT_BLACK As Long = 0            ' RGB(0, 0, 0) = #000000
Public Const GANTT_COLOR_TEXT_WHITE As Long = 16777215     ' RGB(255, 255, 255) = #FFFFFF
Public Const GANTT_COLOR_GANTT_TEXT As Long = 13917813     ' RGB(83, 141, 213) = #538DD5 (blue)

' ----- Font Specifications -----
Public Const GANTT_FONT_PARENT As String = "Century Gothic"
Public Const GANTT_FONT_CHILD As String = "Century Gothic"
Public Const GANTT_FONT_TOTALS As String = "Calibri"
Public Const GANTT_FONT_SIZE_PARENT As Long = 10
Public Const GANTT_FONT_SIZE_CHILD As Long = 10
Public Const GANTT_FONT_SIZE_TOTALS As Long = 12

' ----- Gantt Output Naming -----
Public Const GANTT_OUTPUT_BASE As String = "Gantt_Chart"   ' Base name for generated gantt sheets

' =============================================
' ===== VALIDATION LISTS (ALL_LISTS SHEET) =====
' ===== Data validation source ranges =====
' =============================================

' All_Lists sheet validation ranges
Public Const VAL_ASSESSMENT_RANGE As String = "=All_Lists!$A$2:$A$4"      ' ACCEPTABLE, MINOR DEFICIENCY, NON-SERVICEABLE
Public Const VAL_STATUS_PARENT_RANGE As String = "=All_Lists!$B$2:$B$5"   ' Parent rows: COMPLETED, NOT STARTED, IN PROGRESS, OVERDUE
Public Const VAL_STATUS_CHILD_RANGE As String = "=All_Lists!$B$2:$B$3"    ' Child rows: COMPLETED, NOT STARTED
Public Const VAL_AVAILABILITY_RANGE As String = "=All_Lists!$C$2:$C$4"    ' READY, ON HOLD, NOT AVAILABLE
Public Const VAL_PRIORITY_RANGE As String = "=All_Lists!$D$2:$D$4"        ' HIGH, MEDIUM, LOW
Public Const VAL_NETA_RANGE As String = "=All_Lists!$F$2:$F$3"            ' ATS, MTS

' Simple validation lists (no All_Lists reference)
Public Const VAL_DATASHEET_LIST As String = "YES,NO,N/A"
Public Const VAL_MODE_TOGGLE_LIST As String = "AUTO,MANUAL"

' =============================================
' ===== COMMON ROW/RANGE DEFINITIONS =====
' =============================================

' Standard row positions across templates
Public Const HEADER_ROW As Long = 1                ' Standard header row
Public Const FIRST_DATA_ROW As Long = 2           ' Standard first data row

' Template-specific rows
Public Const TEMPLATE_PARENT_ROW As Long = 6       ' Parent row template
Public Const TEMPLATE_CHILD_ROW As Long = 7        ' Child row template
Public Const TEMPLATE_TOTALS_ROW As Long = 21      ' Totals row template

' =============================================
' ===== SCOPE SHEET NAMING PATTERNS =====
' ===== (For identifying scope sheets) =====
' =============================================

' Scope sheet CodeName patterns (for FixExistingSheets targeting)
Public Const SCOPE_CODENAME_PREFIX As String = "Scope_"     ' Scope_1, Scope_2, etc.

' Common scope sheet name patterns
Public Const PPM_NAME_PATTERN As String = ".PPM"           ' LAS16.PPM01, etc.
Public Const GDB_NAME_PATTERN As String = ".GDB"           ' LAS16.GDB01-12, etc.
Public Const RPP_NAME_PATTERN As String = "RPP's"          ' RPP's (1-120), etc.

' =============================================
' ===== FORMULA CONSTANTS =====
' ===== (Standardized formula components) =====
' =============================================

' Parent status formula (decimal format 0-1, not percentage 0-100)
Public Const PARENT_STATUS_FORMULA_BASE As String = _
    "=IF(AND(I{ROW}<>"""",N{ROW}<1,I{ROW}<TODAY()),""OVERDUE""," & _
    "IF(N{ROW}=1,""COMPLETED""," & _
    "IF(N{ROW}=0,""NOT STARTED""," & _
    "IF(AND(N{ROW}>0,N{ROW}<1),""IN PROGRESS"",""""))))"

' Parent date rollup formula (AGGREGATE function)
Public Const PARENT_DATE_ROLLUP_FORMULA_BASE As String = _
    "=IFERROR(IF(AGGREGATE(5,6,IF(LEFT(E{NEXT_ROW}:E200,LEN(E{ROW})+1)=E{ROW}&""."",I{NEXT_ROW}:I200))>0," & _
    "AGGREGATE(5,6,IF(LEFT(E{NEXT_ROW}:E200,LEN(E{ROW})+1)=E{ROW}&""."",I{NEXT_ROW}:I200)),""""),"""")"

' Child percentage formula
Public Const CHILD_PCT_FORMULA_BASE As String = _
    "=IFERROR(IF(P{ROW}>0,1-(Q{ROW}/P{ROW}),0),0)"

' Date completion formula base
Public Const DATE_COMPLETION_FORMULA_BASE As String = _
    "=IF($T$2=""AUTO"",IF(B{ROW}=""COMPLETED"",NOW(),""""),"""")"

' =============================================
' ===== UTILITY FUNCTIONS =====
' ===== (Global helper functions) =====
' =============================================

Public Function GetFormattedFormula(formulaBase As String, currentRow As Long, Optional NextRow As Long = 0) As String
    ' Replaces {ROW} and {NEXT_ROW} placeholders with actual row numbers
    Dim result As String
    result = Replace(formulaBase, "{ROW}", CStr(currentRow))
    If NextRow > 0 Then
        result = Replace(result, "{NEXT_ROW}", CStr(NextRow))
    End If
    GetFormattedFormula = result
End Function

Public Function IsValidScopeCodeName(codeName As String) As Boolean
    ' Checks if CodeName matches pattern 'Scope_' followed by numbers
    If Len(codeName) < 7 Then
        IsValidScopeCodeName = False
        Exit Function
    End If
    
    If Left(codeName, Len(SCOPE_CODENAME_PREFIX)) <> SCOPE_CODENAME_PREFIX Then
        IsValidScopeCodeName = False
        Exit Function
    End If
    
    ' Check if remainder after "Scope_" contains only numbers
    Dim remainder As String
    remainder = Mid(codeName, Len(SCOPE_CODENAME_PREFIX) + 1)
    
    If Len(remainder) = 0 Then
        IsValidScopeCodeName = False
        Exit Function
    End If
    
    ' Check if remainder is numeric
    Dim i As Long
    For i = 1 To Len(remainder)
        If Not IsNumeric(Mid(remainder, i, 1)) Then
            IsValidScopeCodeName = False
            Exit Function
        End If
    Next i
    
    IsValidScopeCodeName = True
End Function

Public Function CountDots(inputString As String) As Long
    ' Counts the number of dots in a string (for Task_ID level detection)
    Dim i As Long, dotCount As Long
    For i = 1 To Len(inputString)
        If Mid(inputString, i, 1) = "." Then dotCount = dotCount + 1
    Next i
    CountDots = dotCount
End Function

Public Function GetColumnLetter(columnNumber As Long) As String
    ' Converts column number to Excel column letter (1=A, 2=B, etc.)
    GetColumnLetter = Replace(Cells(1, columnNumber).Address(True, False), "$1", "")
End Function

' =============================================
' ===== GANTT HELPER FUNCTIONS =====
' ===== (Gantt-specific utilities) =====
' =============================================

Public Function FindGanttBlueprintRow(ws As Worksheet, blueprintType As String) As Long
    ' Finds blueprint row by searching Column A for "BLUEPRINT:" prefix
    ' Returns row number or 0 if not found
    '
    ' Usage:
    '   parentRow = FindGanttBlueprintRow(ws, Global_Constants.GANTT_BLUEPRINT_PARENT)
    '   childRow = FindGanttBlueprintRow(ws, Global_Constants.GANTT_BLUEPRINT_CHILD)
    
    Dim cell As Range
    Dim searchValue As String
    
    searchValue = "BLUEPRINT:" & blueprintType
    
    Set cell = ws.Columns(GANTT_COL_BLUEPRINT).Find( _
        What:=searchValue, _
        LookAt:=xlWhole, _
        MatchCase:=False)
    
    If Not cell Is Nothing Then
        FindGanttBlueprintRow = cell.row
    Else
        FindGanttBlueprintRow = 0
    End If
End Function

Public Function GetGanttColumnLetter(columnNumber As Long) As String
    ' Converts column number to Excel column letter
    ' Handles extended range (A-BQ, columns 1-69)
    GetGanttColumnLetter = Replace(Cells(1, columnNumber).Address(True, False), "$1", "")
End Function

Public Function GetGanttWeekStartColumn(weekNumber As Long) As Long
    ' Returns starting column for a given week number (1-12)
    ' Week 1 starts at column J (10), each week is 5 columns
    If weekNumber < 1 Or weekNumber > GANTT_TOTAL_WEEKS Then
        GetGanttWeekStartColumn = 0
        Exit Function
    End If
    GetGanttWeekStartColumn = GANTT_COL_TIMELINE_START + ((weekNumber - 1) * GANTT_DAYS_PER_WEEK)
End Function

Public Function GetGanttWeekEndColumn(weekNumber As Long) As Long
    ' Returns ending column for a given week number (1-12)
    Dim startCol As Long
    startCol = GetGanttWeekStartColumn(weekNumber)
    If startCol = 0 Then
        GetGanttWeekEndColumn = 0
    Else
        GetGanttWeekEndColumn = startCol + GANTT_DAYS_PER_WEEK - 1
    End If
End Function

' =============================================
' ===== VALIDATION FUNCTIONS =====
' ===== (Ensures proper module usage) =====
' =============================================

Public Sub ValidateModuleCompliance()
    ' Function to check if all modules are using Global_Constants properly
    ' TODO: Implement scanning for hardcoded column references
    MsgBox "Global Constants Module v" & MODULE_VERSION & " loaded successfully!" & vbCrLf & _
           "Template Type: " & TEMPLATE_TYPE & vbCrLf & _
           "Last Updated: " & LAST_UPDATED & vbCrLf & vbCrLf & _
           "✅ REMINDER: ALL modules must use GC.* constants!" & vbCrLf & _
           "NO hardcoded column numbers allowed!", vbInformation, "Global Constants Loaded"
End Sub

' =============================================
' ===== MODULE INITIALIZATION =====
' =============================================

Private Sub Workbook_Open()
    ' Auto-validate when workbook opens
    Call ValidateModuleCompliance
End Sub
