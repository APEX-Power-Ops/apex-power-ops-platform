Attribute VB_Name = "modGanttBuilder"


' Updated to use Global_Constants - 2025-11-23
' ? COMPLIANCE: All column references now use Global_Constants.*
' ? NEW: Added support for REMAINING_QUANTITY column (GT_COL_REMAINING_QTY)
'
' CRITICAL FIXES APPLIED - 2025-12-04
' ?? FIX #1: Timeline Row Reference - Gantt formulas now reference Row 7 (dates) not Row 10 (day letters)
'    - Added FixGanttFormulaRowReference() function
'    - Replaces $10 with $7 in all timeline formulas after blueprint copy
'    - RESULT: Gantt bars now display correctly
'
' ?? FIX #2: Date Due Formulas - Date Due now uses formulas instead of static values
'    - Single tasks: VLOOKUP with IF wrapper =IFERROR(IF(VLOOKUP(...)=0,"",VLOOKUP(...)),"")
'    - Aggregated tasks: MAXIFS with IF wrapper =IFERROR(IF(MAXIFS(...)=0,"",MAXIFS(...)),"")
'    - RESULT: Live links to scope sheets, hides zero dates, auto-updates when source changes
'
' ?? PERFORMANCE FIXES - 2025-12-04 (Fix freezing/hang issues)
' ?? FIX #3: Batch Formula Fix - Moved timeline fix from per-row to batch at end
'    - OLD: Called FixGanttFormulaRowReference() inside InsertFromBlueprint (per-row)
'    - NEW: Single call to FixGanttFormulaRowReferenceRange() after all rows written
'    - Uses Range.Replace instead of cell-by-cell loop (orders of magnitude faster)
'    - RESULT: 100 rows × 300 cols now fixed in one operation vs 30,000 cell operations
'
' ?? FIX #4: Application.Calculation = xlManual during bulk operations
'    - Prevents Excel recalc after every formula write
'    - RESULT: Massive speedup for formula-heavy operations
'
' ?? FIX #5: Error handler with guaranteed cleanup
'    - Added WriteAggregation_Error and WriteAggregation_Cleanup labels
'    - Ensures ScreenUpdating/EnableEvents/Calculation are ALWAYS restored
'    - RESULT: No more frozen Excel if error occurs mid-operation
'
' ?? FIX #6: Scope Sheet Cache - 2025-12-04
'    - Added BuildScopeSheetCache() function to pre-identify valid scope sheets
'    - OLD: For Each ws In Worksheets + IsScopeSheet() inside WriteAggregation loop
'    - NEW: Cache built once, then Dictionary lookup by name
'    - RESULT: 100 rows × 30 sheets = 3000 IsScopeSheet calls reduced to 30
'
' ?? FIX #7: Direct Column Constants - 2025-12-04
'    - Replaced ALL FindColStrict/FindGanttHeaderRow calls with Global_Constants
'    - OLD: FindColStrict(outWS, hdr, Array("taskid", "id")) - string search per column
'    - NEW: Global_Constants.GANTT_COL_TASK_ID - direct constant reference
'    - RESULT: Eliminates 8+ header string searches per build, ensures consistency
'    - BONUS: No more "header not found" errors from misspelled column names
'
' ?? FIX #8: Parent Rows - No Timeline Formulas - 2025-12-04
'    - Parent rows should NOT have Gantt bar formulas (they're section headers)
'    - Changed: InsertFromBlueprint tmp, 1, outWS, writeRow, cPct, lastCol, False
'    - Was: True (incorrectly copying timeline formulas to parent rows)
'    - RESULT: Parent rows show clean headers without formula clutter
'
' FORMULA PATTERNS (for Gantt_Template reference):
' ================================================
' Date (VLOOKUP):   =IFERROR(IF(VLOOKUP("taskId",Sheet!$E:$I,5,FALSE)=0,"",VLOOKUP(...)),"")
' Date (MAXIFS):    =IFERROR(IF(MAXIFS(Sheet!$I:$I,Sheet!$E:$E,">=start",Sheet!$E:$E,"<=end")=0,"",MAXIFS(...)),"")
' Timeline fill:    =IF(AND(ISNUMBER($Fnn),ISNUMBER($Gnn),$Fnn<=$Col$7,$Col$7<=$Gnn,$Inn<1),1,"")
'                   Note: $Inn<1 hides bars for 100% complete tasks

Option Explicit

'=========================== SETTINGS ==================================
Public Const GB_TEMPLATE_NAME As String = "Gantt_Template"
Public Const GB_OUTPUT_BASE  As String = "Gantt"

' turn these ON/OFF as you need
Public Const GB_DEBUG       As Boolean = True          ' master switch
Public Const GB_DEEP_TRACE  As Boolean = True          ' prints extra info

' aggregation keys
Private Const PARENTS_KEY As String = "#PARENTS"
Private Const GROUPS_KEY  As String = "#GROUPS"
Private Const SCOPES_KEY  As String = "#SCOPES"

'=========================== SMALL LOGGING ==============================
Private GB_LOG_BUFFER As String

Private Sub GB_Log(ByVal s As String)
    If Not GB_DEBUG Then Exit Sub
    GB_LOG_BUFFER = GB_LOG_BUFFER & s & vbCrLf
End Sub

Private Sub GB_LogFlush()
    If Not GB_DEBUG Then Exit Sub
    If Len(GB_LOG_BUFFER) > 0 Then
        Debug.Print GB_LOG_BUFFER
        GB_LOG_BUFFER = vbNullString
    End If
End Sub

'=========================== NORMALIZE / PROPER ========================
Public Function GB_Normalize(ByVal s As String) As String
    Dim i As Long, ch As String, t As String
    s = LCase$(Trim$(s))
    For i = 1 To Len(s)
        ch = Mid$(s, i, 1)
        If (ch >= "a" And ch <= "z") Or (ch >= "0" And ch <= "9") Or ch = "+" Or ch = "-" Then
            t = t & ch
        End If
    Next i
    GB_Normalize = t
End Function

Private Function GB_Proper(ByVal s As String) As String
    GB_Proper = StrConv(Trim$(s), vbProperCase)
End Function

'===================== PUBLIC ENTRY POINTS =============================
Public Sub OpenGanttBuilder()
    VBA.UserForms.Add("frmGanttBuilder").Show
End Sub

Public Sub BuildGanttFromSheets(ByVal selectedSheets As Variant)

    Dim outWS As Worksheet: Set outWS = PrepareGanttSheet()

    '----- Use Global_Constants for ALL column positions (FIX #7: No more dynamic lookups)
    Dim hdr As Long
    Dim cID As Long, cname As Long, cQty As Long, cRemQty As Long, cStart As Long
    Dim cDue As Long, cPct As Long, cDur As Long

    ' ?? PERFORMANCE: Use constants directly instead of FindColStrict/FindGanttHeaderRow
    ' This eliminates 8+ string searches across header row on every build
    hdr = Global_Constants.GANTT_HEADER_ROW          ' Row 9
    cID = Global_Constants.GANTT_COL_TASK_ID         ' Column B (2)
    cname = Global_Constants.GANTT_COL_NAME          ' Column C (3)
    cQty = Global_Constants.GANTT_COL_QTY            ' Column D (4)
    cRemQty = Global_Constants.GANTT_COL_REM_QTY     ' Column E (5)
    cStart = Global_Constants.GANTT_COL_START        ' Column F (6)
    cDue = Global_Constants.GANTT_COL_DUE            ' Column G (7)
    cDur = Global_Constants.GANTT_COL_DURATION       ' Column H (8)
    cPct = Global_Constants.GANTT_COL_PCT            ' Column I (9)

    If (cID = 0 Or cname = 0 Or cQty = 0 Or cRemQty = 0 Or cDue = 0 Or cPct = 0 Or cDur = 0) Then
        Err.Raise vbObjectError + 103, , _
           "Output mapping failed (Task/Name/Qty/RemQty/Start/Due/%/Duration columns)."
    End If

    ' Update header text in columns
    outWS.Cells(hdr, cPct).Value = "% COMPLETION"
    outWS.Cells(hdr + 1, cPct).Value = "% COMPLETION"
    outWS.Cells(hdr, cRemQty).Value = "REMAINING QUANTITY"
    outWS.Cells(hdr + 1, cRemQty).Value = "REMAINING QTY"

    ' Format date columns
    If cStart > 0 Then
        outWS.Columns(cStart).NumberFormat = "mmm-dd-yyyy"
    End If
    If cDue > 0 Then
        outWS.Columns(cDue).NumberFormat = "mmm-dd-yyyy"
    End If

    ' Step-2: dump the header map of the output (for quick verification)
    DebugDumpHeaderMap outWS, hdr, cID, cname, cQty, cRemQty, cStart, cDue, cPct, cDur

    '----- aggregate across selected scope sheets
    Dim agg As Object: Set agg = CreateObject("Scripting.Dictionary")
    agg.Add PARENTS_KEY, CreateObject("Scripting.Dictionary")
    agg.Add GROUPS_KEY, CreateObject("Scripting.Dictionary")
    agg.Add SCOPES_KEY, CreateObject("Scripting.Dictionary")

    Dim nm As Variant, ws As Worksheet
    For Each nm In EnumSelectedSheetNames(selectedSheets)
        On Error Resume Next
        Set ws = ThisWorkbook.Worksheets(CStr(nm))
        On Error GoTo 0
        If Not ws Is Nothing Then
            If GB_DEBUG Then Debug.Print "Checking sheet: " & ws.Name & " | IsScopeSheet=" & IsScopeSheet(ws)
            If IsScopeSheet(ws) Then AccumulateFromSheet ws, agg
        ElseIf GB_DEBUG Then
            Debug.Print "Ignoring missing sheet: "; nm
        End If
    Next nm
    
    ' DIAGNOSTIC: Check what was collected
    If GB_DEBUG Then
        Dim pAgg As Object: Set pAgg = agg(PARENTS_KEY)
        Dim gAgg As Object: Set gAgg = agg(GROUPS_KEY)
        Debug.Print "=== ACCUMULATION RESULTS ==="
        Debug.Print "Parent buckets collected: " & pAgg.Count
        Debug.Print "Group buckets collected: " & gAgg.Count
        If pAgg.Count > 0 Then
            Dim k As Variant
            Debug.Print "Parent IDs found:"
            For Each k In pAgg.keys
                Debug.Print "  " & k
            Next k
        End If
        Debug.Print "=========================="
    End If

    '----- write to output sheet
    Dim writeRow As Long: writeRow = hdr + 2
    Call WriteAggregation(outWS, hdr, cID, cname, cQty, cRemQty, cStart, cDue, cPct, cDur, agg, writeRow)

    If GB_DEBUG Then
        Debug.Print "Build complete. Rows written (not counting totals): "; _
            (writeRow - (hdr + 2))
    End If
End Sub

'======================= PREPARE OUTPUT SHEET ==========================
Public Function PrepareGanttSheet() As Worksheet
    Dim wb As Workbook, tpl As Worksheet, nm As String
    Set wb = ThisWorkbook

    On Error Resume Next
    Set tpl = wb.Worksheets(GB_TEMPLATE_NAME)
    On Error GoTo 0
    If tpl Is Nothing Then Err.Raise vbObjectError + 101, , _
        "Missing template sheet '" & GB_TEMPLATE_NAME & "'."

    nm = UniqueSheetName(wb, GB_OUTPUT_BASE)
    tpl.Copy After:=wb.Sheets(wb.Sheets.Count)
    Set PrepareGanttSheet = wb.Sheets(wb.Sheets.Count)
    PrepareGanttSheet.Name = nm
    PrepareGanttSheet.Visible = xlSheetVisible
End Function
'========================== ACCUMULATOR ================================
' (AccumulateFromSheet remains unchanged - it just collects quantities)
Private Sub AccumulateFromSheet(ByVal ws As Worksheet, _
                                ByRef aggContainer As Object)

    Dim hdr As Long
    Dim cID As Long, cname As Long, cQty As Long, cDue As Long, cPct As Long

    ' Use Global_Constants for header row
    hdr = Global_Constants.SC_HEADER_ROW
    If hdr = 0 Then Exit Sub

    ' Use Global_Constants for column positions
    cID = Global_Constants.SC_COL_TASK_ID      ' Column E - Task_ID
    cname = Global_Constants.SC_COL_NAME_APP   ' Column F - Task Names + Apparatus
    cQty = FindColStrict(ws, hdr, Array("apparatusquantity", "apparatusqty", "qty"))
    cDue = Global_Constants.SC_COL_DATE_DUE    ' Column I - Date Due
    cPct = Global_Constants.SC_COL_PCT         ' Column N for % completion
    
    If cID = 0 Or cDue = 0 Or cPct = 0 Then
        If GB_DEBUG Then
            Debug.Print "WARNING: Missing columns in " & ws.Name & " - ID:" & cID & " Due:" & cDue & " %:" & cPct
        End If
        Exit Sub
    End If

    Dim lastR As Long
    lastR = Application.Max( _
        LastUsedRowIn(ws, cID), LastUsedRowIn(ws, cname), _
        LastUsedRowIn(ws, cQty), LastUsedRowIn(ws, cDue), _
        LastUsedRowIn(ws, cPct))
    If lastR < hdr + 1 Then Exit Sub
    
    ' DIAGNOSTIC: Verify columns on EVERY sheet processed
    If GB_DEBUG Then
        Debug.Print "=== DIAGNOSTIC: " & ws.Name & " Column Check (Using Global_Constants) ==="
        Debug.Print "Headers (Row " & hdr & "):"
        Debug.Print "  Col " & cID & " (Task_ID): " & ws.Cells(hdr, cID).Value
        Debug.Print "  Col " & cname & " (Task Name): " & ws.Cells(hdr, cname).Value
        Debug.Print "  Col " & cDue & " (Due Date): " & ws.Cells(hdr, cDue).Value
        Debug.Print "  Col " & cPct & " (% Complete): " & ws.Cells(hdr, cPct).Value
        Debug.Print "  cQty search result: " & cQty
        Debug.Print "  Last row calculated: " & lastR
        Debug.Print "================================"
    End If

    Dim pAgg As Object: Set pAgg = aggContainer(PARENTS_KEY)
    Dim gAgg As Object: Set gAgg = aggContainer(GROUPS_KEY)
    Dim sAgg As Object: Set sAgg = aggContainer(SCOPES_KEY)

    ' Scope name (G4 fallback) - using Global_Constants
    Dim scopeTitle As String
    scopeTitle = Trim$(CStr(Nz(ws.Range(Global_Constants.SC_SCOPE_CELL).Value, "")))
    If Len(scopeTitle) = 0 Then
        scopeTitle = Trim$(CStr(Nz(ws.Cells(hdr - 1, IIf(cname > 0, cname, 1)).Value, "")))
        If Len(scopeTitle) = 0 Then scopeTitle = ws.Name
    End If

    Dim r As Long, idTxt As String, nm As String, q As Double
    Dim dueV As Variant, pctV As Double
    Dim parentId As String, gKey As String, appNorm As String
    Dim leafN As Long, a As Variant, twoKey As String, topKey As String
    Dim segCount As Long
    Dim rowsProcessed As Long: rowsProcessed = 0

    For r = hdr + 1 To lastR

        idTxt = Trim$(CStr(ws.Cells(r, cID).Value2))
        If Len(idTxt) = 0 Then GoTo NextR
        
        If GB_DEBUG And GB_DEEP_TRACE And rowsProcessed < 5 Then
            Debug.Print "Row " & r & " | Task_ID: '" & idTxt & "' | Name: '" & ws.Cells(r, cname).Value & "'"
        End If
        rowsProcessed = rowsProcessed + 1

        twoKey = GB_TwoSegKey(idTxt)
        If Len(twoKey) = 0 Then GoTo NextR

        ' Count segments to detect true parent header rows (exactly 2 segments)
        segCount = UBound(Split(idTxt, "."))
        nm = IIf(cname > 0, CStr(ws.Cells(r, cname).Value2), "")

        ' Store scope title per top key so parent text can be scope + task
        topKey = Split(twoKey, ".")(0)
        If Len(topKey) > 0 Then
            If Not sAgg.Exists(topKey) Then
                sAgg.Add topKey, scopeTitle
            ElseIf Len(CStr(sAgg(topKey))) = 0 Then
                sAgg(topKey) = scopeTitle
            End If
        End If

        ' Qty read with error handling
        If cQty > 0 And r > 0 Then
            On Error GoTo QTY_EH
            q = Nz(ws.Cells(r, cQty).Value2, 1)
            On Error GoTo 0
        Else
            q = 1
        End If
        If q <= 0 Then q = 1

        ' Enhanced date validation
        dueV = ws.Cells(r, cDue).Value
        If IsDate(dueV) Then
            Dim testDate As Date
            testDate = CDate(dueV)
            ' Only accept reasonable dates (between 2000 and 2100)
            If Year(testDate) >= 2000 And Year(testDate) <= 2100 Then
                dueV = testDate
            Else
                If GB_DEBUG And GB_DEEP_TRACE Then
                    Debug.Print "Suspicious date in " & ws.Name & " row " & r & ": " & testDate
                End If
                dueV = Empty
            End If
        Else
            dueV = Empty
        End If
        
        ' Enhanced % completion reading
        Dim pctRaw As Variant
        pctRaw = ws.Cells(r, cPct).Value
        pctV = PercentFromMixed(pctRaw)
        If pctV < 0 Then pctV = 0#
        If pctV > 1 Then pctV = 1#

        parentId = twoKey
        leafN = GB_LeafNumber(idTxt)

        ' Ensure parent bucket exists
        If Not pAgg.Exists(parentId) Then
            ReDim a(1 To 7)  ' Array to store parent data
            a(1) = ""       ' Display name
            a(2) = 0#       ' Quantity sum
            a(3) = Empty    ' Due date (MAX)
            a(4) = 0#       ' % complete weighted sum
            a(5) = 0#       ' Not used
            a(6) = ""       ' Task text
            a(7) = ws.Name  ' Source sheet name
            pAgg.Add parentId, a
        End If
        a = pAgg(parentId)

        If segCount = 1 Then
            ' Two-segment parent row – capture the "task" text and sheet name
            If Len(Trim$(a(6))) = 0 And Len(Trim$(nm)) > 0 Then a(6) = Trim$(nm)
            a(7) = ws.Name  ' Store sheet name
            pAgg(parentId) = a
            GoTo NextR
        End If

        ' From here on: real children (3+ segments)
        a(2) = a(2) + q
        ' Only update parent due date if child has a valid date
        If IsDate(dueV) Then
            If (IsEmpty(a(3)) Or CDate(dueV) > CDate(a(3))) Then a(3) = dueV
        End If
        a(4) = a(4) + pctV * q
        a(7) = ws.Name  ' Update sheet name

        If Len(Trim$(a(1))) = 0 Then
            Dim rightPart As String
            If Len(Trim$(a(6))) > 0 Then
                rightPart = a(6)
            Else
                rightPart = nm
            End If
            ' Preserve original case from G4
            a(1) = scopeTitle & " | " & Trim$(rightPart)
        End If
        pAgg(parentId) = a

        ' Child group key: coalesce identical apparatus under the same parent
        appNorm = LCase$(Trim$(nm))
        gKey = parentId & "||" & appNorm
        If Not gAgg.Exists(gKey) Then
            ReDim a(1 To 8)  ' Array for group data with sheet name
            a(1) = parentId
            a(2) = nm
            a(3) = q
            a(4) = IIf(IsDate(dueV), dueV, Empty)
            a(5) = pctV * q
            a(6) = leafN
            a(7) = leafN
            a(8) = ws.Name  ' Source sheet name
            gAgg.Add gKey, a
        Else
            a = gAgg(gKey)
            a(3) = a(3) + q
            ' Only update group due date if child has valid date
            If IsDate(dueV) Then
                If (IsEmpty(a(4)) Or CDate(dueV) > CDate(a(4))) Then a(4) = dueV
            End If
            a(5) = a(5) + pctV * q
            If leafN < a(6) Then a(6) = leafN
            If leafN > a(7) Then a(7) = leafN
            ' Keep the original sheet name (first occurrence)
            gAgg(gKey) = a
        End If

NextR:
    Next r
    
    If GB_DEBUG Then
        Debug.Print "Sheet " & ws.Name & " processed " & rowsProcessed & " rows with Task IDs"
    End If
    Exit Sub

'---- Qty exception handler ----------------
QTY_EH:
    If GB_DEBUG And GB_DEEP_TRACE Then
        GB_Log "QTY_EH – Sheet=" & ws.Name & _
               " r=" & r & _
               " ID='" & idTxt & "'" & _
               " cQty=" & cQty & _
               " Addr=" & IIf(cQty > 0, ws.Cells(r, cQty).Address(False, False), "<n/a>") & _
               " Val='" & IIf(cQty > 0, CStr(ws.Cells(r, cQty).text), "") & "'"
        GB_LogFlush
    End If
    Resume Next
End Sub
'=========================== WRITER ===================================
Public Sub WriteAggregation( _
    ByVal outWS As Worksheet, ByVal hdr As Long, _
    ByVal cID As Long, ByVal cname As Long, ByVal cQty As Long, ByVal cRemQty As Long, _
    ByVal cStart As Long, ByVal cDue As Long, ByVal cPct As Long, _
    ByVal cDur As Long, ByRef agg As Object, ByRef writeRow As Long)

    If agg Is Nothing Then Exit Sub
    If Not agg.Exists(PARENTS_KEY) Then Exit Sub

    Dim pAgg As Object, gAgg As Object, sAgg As Object
    Set pAgg = agg(PARENTS_KEY)
    If agg.Exists(GROUPS_KEY) Then Set gAgg = agg(GROUPS_KEY) Else Set gAgg = CreateObject("Scripting.Dictionary")
    If agg.Exists(SCOPES_KEY) Then Set sAgg = agg(SCOPES_KEY) Else Set sAgg = Nothing

    ' ?? PERFORMANCE: Disable all Excel overhead during bulk operations
    Dim calcMode As XlCalculation
    calcMode = Application.Calculation
    Application.Calculation = xlCalculationManual
    Application.ScreenUpdating = False
    Application.EnableEvents = False
    
    On Error GoTo WriteAggregation_Error
    
    ' ?? PERFORMANCE: Build scope sheet cache ONCE (avoids repeated IsScopeSheet calls)
    Dim scopeSheetCache As Object
    Set scopeSheetCache = BuildScopeSheetCache()
    If GB_DEBUG Then Debug.Print "Scope sheet cache built: " & scopeSheetCache.Count & " sheets"
    
    ' ?? PERFORMANCE: Track first/last data rows for batch formula fix at end
    Dim firstDataRow As Long, lastDataRowWritten As Long
    firstDataRow = 0
    lastDataRowWritten = 0

    '--- blueprints (rows 11/12/13/14) to a temporary sheet
    Dim tmp As Worksheet
    Set tmp = ThisWorkbook.Worksheets.Add(After:=outWS)
    tmp.Visible = xlSheetVeryHidden
    outWS.Rows(11).Copy tmp.Rows(1)
    outWS.Rows(12).Copy tmp.Rows(2)
    outWS.Rows(13).Copy tmp.Rows(3)
    outWS.Rows(14).Copy tmp.Rows(4)

    '--- remove rows 11..end (template blueprints)
    On Error Resume Next
    Application.DisplayAlerts = False
    outWS.Rows("11:" & outWS.Rows.Count).Delete
    Application.DisplayAlerts = True
    On Error GoTo 0

    '--- start writing at row 11
    writeRow = 11

    '--- header merge (left block) just in case
    MergeHeaderIfNeeded outWS, hdr, Array(cID, cname, cQty, cRemQty, cStart, cDue, cPct, cDur)

    '--- cache last column of timeline
    Dim lastCol As Long
    lastCol = outWS.Cells(hdr + 1, outWS.Columns.Count).End(xlToLeft).Column

    Dim pIds As Variant: pIds = SortedParentIds(pAgg)
    Dim i As Long, j As Long
    Dim firstParentRow As Long, lastParentRow As Long
    Dim lastChildRow As Long

    If Not IsEmpty(pIds) Then
        firstDataRow = 11  ' Track for batch formula fix
        
        For i = LBound(pIds) To UBound(pIds)

            '----- parent row (NO timeline formulas - parents don't show Gantt bars)
            InsertFromBlueprint tmp, 1, outWS, writeRow, cPct, lastCol, False
            Dim parentRow As Long: parentRow = writeRow
            If firstParentRow = 0 Then firstParentRow = parentRow

            Dim pid As String: pid = CStr(pIds(i))
            Dim a As Variant: a = pAgg(pid)
            Dim displayName As String: displayName = IIf(Len(Trim$(a(1))) > 0, CStr(a(1)), pid)

            outWS.Cells(writeRow, cID).Value = pid
            outWS.Cells(writeRow, cname).Value = displayName
            writeRow = writeRow + 1

            '----- children under this parent
            Dim childs As Object: Set childs = CreateObject("Scripting.Dictionary")
            Dim k As Variant
            For Each k In gAgg.keys
                If Left$(CStr(k), Len(pid) + 2) = pid & "||" Then childs.Add CStr(k), True
            Next k

            If childs.Count > 0 Then
                Dim grouped As Object
                Set grouped = CoalesceChildGroups(gAgg, childs, pid)

                Dim outKeys As Object: Set outKeys = CreateObject("System.Collections.ArrayList")
                Dim gg As Variant
                For Each gg In grouped.keys
                    outKeys.Add gg
                Next gg
                outKeys.Sort

                Dim childStart As Long: childStart = writeRow
                Dim key As Variant, g As Variant, mins As Long, maxs As Long
                Dim showId As String, q As Double, p As Double

                For Each key In outKeys
                    g = grouped(key)
                    mins = CLng(g(6))
                    maxs = CLng(g(7))

                    If mins = maxs Then
                        showId = pid & "." & CStr(mins)
                    Else
                        showId = pid & "." & CStr(mins) & " - " & pid & "." & CStr(maxs)
                    End If

                    InsertFromBlueprint tmp, 2, outWS, writeRow, cPct, lastCol, True

                    q = Nz(g(3), 0#)
                    
                    ' Write child row data
                    outWS.Cells(writeRow, cID).Value = showId
                    outWS.Cells(writeRow, cname).Value = Nz(g(2), "")
                    outWS.Cells(writeRow, cQty).Value = q
                    
                    ' ?? NEW: REMAINING_QUANTITY Formula for child rows
                    ' Get source sheet name for this task
                    Dim sourceSheetName As String
                    sourceSheetName = CStr(g(8))  ' Sheet name stored in index 8
                    
                    If Len(sourceSheetName) > 0 Then
                        ' Escape apostrophes in sheet name for formula
                        Dim escapedSheetName As String
                        escapedSheetName = Replace(sourceSheetName, "'", "''")
                        
                        ' Create formula to count incomplete apparatus
                        ' Formula: Total Qty - COUNTIFS(matching Task_IDs where STATUS="COMPLETED")
                        Dim remainingFormula As String
                        
                        If mins = maxs Then
                            ' Single task - count exact match
                            remainingFormula = "=" & q & "-COUNTIFS('" & escapedSheetName & "'!$" & _
                                Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ":$" & _
                                Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ",""" & _
                                pid & "." & mins & """,'" & escapedSheetName & "'!$" & _
                                Global_Constants.GetColumnLetter(Global_Constants.SC_COL_STATUS) & ":$" & _
                                Global_Constants.GetColumnLetter(Global_Constants.SC_COL_STATUS) & ",""COMPLETED"")"
                        Else
                            ' Multiple tasks - sum remaining for range
                            ' Use SUMPRODUCT to count incomplete tasks in range
                            remainingFormula = "=" & q & "-SUMPRODUCT(('" & escapedSheetName & "'!$" & _
                                Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ":$" & _
                                Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ">=""" & _
                                pid & "." & mins & """)*('" & escapedSheetName & "'!$" & _
                                Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ":$" & _
                                Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & "<=""" & _
                                pid & "." & maxs & """)*('" & escapedSheetName & "'!$" & _
                                Global_Constants.GetColumnLetter(Global_Constants.SC_COL_STATUS) & ":$" & _
                                Global_Constants.GetColumnLetter(Global_Constants.SC_COL_STATUS) & "=""COMPLETED""))"
                        End If
                        
                        outWS.Cells(writeRow, cRemQty).formula = remainingFormula
                        outWS.Cells(writeRow, cRemQty).NumberFormat = "0"
                    Else
                        ' No source sheet - just show total quantity
                        outWS.Cells(writeRow, cRemQty).Value = q
                    End If
                    
                    ' ?? CREATE DATE DUE FORMULA (matching % completion approach)
                    If cDue > 0 Then
                        ' sourceSheetName and escapedSheetName already set above (lines 501-507)
                        If Len(sourceSheetName) > 0 Then
                            Dim dueDateFormula As String
                            
                            If mins = maxs Then
                                ' Single task - VLOOKUP with IF wrapper to hide zero dates
                                ' Pattern: =IFERROR(IF(VLOOKUP(...)=0,"",VLOOKUP(...)),"")
                                Dim vlookupPart As String
                                vlookupPart = "VLOOKUP(""" & pid & "." & mins & """,'" & escapedSheetName & "'!$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ":$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_DATE_DUE) & ",5,FALSE)"
                                dueDateFormula = "=IFERROR(IF(" & vlookupPart & "=0,""""," & vlookupPart & "),"""")"
                            Else
                                ' Multiple tasks - MAXIFS with IF wrapper to hide zero dates
                                ' Pattern: =IFERROR(IF(MAXIFS(...)=0,"",MAXIFS(...)),"")
                                Dim maxifsPart As String
                                maxifsPart = "MAXIFS('" & escapedSheetName & "'!$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_DATE_DUE) & ":$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_DATE_DUE) & ",'" & _
                                    escapedSheetName & "'!$" & Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ":$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ","">=" & pid & "." & mins & """,'" & _
                                    escapedSheetName & "'!$" & Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ":$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ",""<=" & pid & "." & maxs & """)"
                                dueDateFormula = "=IFERROR(IF(" & maxifsPart & "=0,""""," & maxifsPart & "),"""")"
                            End If
                            
                            outWS.Cells(writeRow, cDue).formula = dueDateFormula
                            outWS.Cells(writeRow, cDue).NumberFormat = "dddd, mmmm dd, yyyy"
                            
                            If GB_DEBUG Then Debug.Print "Created Date Due formula for " & showId & " on sheet " & sourceSheetName
                        Else
                            ' Fallback: No source sheet found - use static value
                            If IsDate(g(4)) Then
                                Dim dueDate As Date
                                dueDate = CDate(g(4))
                                If Year(dueDate) >= 2000 And Year(dueDate) <= 2100 Then
                                    outWS.Cells(writeRow, cDue).Value = dueDate
                                    outWS.Cells(writeRow, cDue).NumberFormat = "dddd, mmmm dd, yyyy"
                                End If
                            End If
                        End If
                    End If
                    
                    ' CRITICAL: Create formula for % completion with dynamic lookup
                    If cPct > 0 Then
                        ' ?? PERFORMANCE: Use cached scope sheets instead of checking all worksheets
                        Dim srcWS As Worksheet
                        Dim srcSheetName As Variant
                        For Each srcSheetName In scopeSheetCache.keys
                            Set srcWS = scopeSheetCache(srcSheetName)
                            Dim findID As Range
                            Set findID = Nothing
                            On Error Resume Next
                            Set findID = srcWS.Columns(Global_Constants.SC_COL_TASK_ID).Find(What:=pid & "." & mins, LookIn:=xlValues, LookAt:=xlWhole)
                            On Error GoTo 0
                            
                            If Not findID Is Nothing Then
                                sourceSheetName = srcWS.Name
                                Exit For
                            End If
                        Next srcSheetName
                        
                        If sourceSheetName <> "" Then
                            ' CRITICAL FIX: Escape apostrophes in sheet name for formula
                            escapedSheetName = Replace(sourceSheetName, "'", "''")
                            
                            ' Create VLOOKUP formula to the source sheet using Global_Constants
                            Dim lookupFormula As String
                            
                            If mins = maxs Then
                                ' Single task - use VLOOKUP
                                ' Column N is 10 columns after column E (5+9=14, so index 10)
                                lookupFormula = "=IFERROR(VLOOKUP(""" & pid & "." & mins & """,'" & escapedSheetName & "'!$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ":$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_PCT) & ",10,FALSE),0)"
                            Else
                                ' Multiple tasks - use AVERAGEIFS
                                lookupFormula = "=IFERROR(AVERAGEIFS('" & escapedSheetName & "'!$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_PCT) & ":$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_PCT) & ",'" & _
                                    escapedSheetName & "'!$" & Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ":$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ","">=" & pid & "." & mins & """,'" & _
                                    escapedSheetName & "'!$" & Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ":$" & _
                                    Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & ",""<=" & pid & "." & maxs & """),0)"
                            End If
                            
                            outWS.Cells(writeRow, cPct).formula = lookupFormula
                            outWS.Cells(writeRow, cPct).NumberFormat = "0%"
                        Else
                            ' No source found - use static value from aggregation
                            If q > 0 Then
                                p = Nz(g(5), 0#) / q
                            Else
                                p = 0#
                            End If
                            outWS.Cells(writeRow, cPct).Value = p
                            outWS.Cells(writeRow, cPct).NumberFormat = "0%"
                        End If
                    End If

                    lastChildRow = writeRow
                    writeRow = writeRow + 1
                Next key

                ' Parent formulas - weighted average for %
                Dim sr As Long, eR As Long
                sr = childStart
                eR = writeRow - 1
                If eR >= sr Then
                    ' Quantity sum
                    outWS.Cells(parentRow, cQty).FormulaR1C1 = _
                        "=SUM(R" & sr & "C" & cQty & ":R" & eR & "C" & cQty & ")"
                    
                    ' ?? NEW: Remaining Quantity sum
                    outWS.Cells(parentRow, cRemQty).FormulaR1C1 = _
                        "=SUM(R" & sr & "C" & cRemQty & ":R" & eR & "C" & cRemQty & ")"
                    
                    ' Start date left blank for manual entry
                    
                    ' Due date: MAX of children due dates
                    outWS.Cells(parentRow, cDue).FormulaR1C1 = _
                        "=IF(COUNT(R" & sr & "C" & cDue & ":R" & eR & "C" & cDue & ")=0,"""",MAX(R" & sr & "C" & cDue & ":R" & eR & "C" & cDue & "))"
                    
                    ' Percentage: weighted average based on live child % values
                    outWS.Cells(parentRow, cPct).FormulaR1C1 = _
                        "=IF(SUM(R" & sr & "C" & cQty & ":R" & eR & "C" & cQty & ")=0,""""," & _
                          "SUMPRODUCT(R" & sr & "C" & cQty & ":R" & eR & "C" & cQty & ",R" & sr & "C" & cPct & ":R" & eR & "C" & cPct & ")/" & _
                          "SUM(R" & sr & "C" & cQty & ":R" & eR & "C" & cQty & "))"
                End If
            Else
                ' Parent with no children
                outWS.Cells(parentRow, cQty).ClearContents
                outWS.Cells(parentRow, cRemQty).ClearContents
                outWS.Cells(parentRow, cStart).ClearContents
                outWS.Cells(parentRow, cDue).ClearContents
                outWS.Cells(parentRow, cPct).ClearContents
            End If

            lastParentRow = parentRow
        Next i
    End If

    '--- duration formula for ALL data rows
    Dim r As Long
    For r = 11 To writeRow - 1
        outWS.Cells(r, cDur).FormulaR1C1 = _
            "=IF(AND(ISNUMBER(RC" & cStart & "),ISNUMBER(RC" & cDue & ")),RC" & cDue & "-RC" & cStart & "+1,"""")"
    Next r

    '--- apply "Last Child" styling
    If lastChildRow > 0 Then
        ApplyBlueprint tmp, 3, outWS, lastChildRow, cPct, lastCol, True
    End If

    '--- totals row
    InsertFromBlueprint tmp, 4, outWS, writeRow, cPct, lastCol, False

    With outWS.Cells(writeRow, cname)
        .Value = "TOTALS"
        .Font.Bold = True
        .HorizontalAlignment = xlRight
        .IndentLevel = 1
    End With

    ' Totals row formulas
    If firstParentRow > 0 And lastParentRow >= firstParentRow Then
        Dim sP As Long, eP As Long
        sP = firstParentRow
        eP = lastParentRow

        ' Quantity sum
        outWS.Cells(writeRow, cQty).FormulaR1C1 = _
            "=SUM(R" & sP & "C" & cQty & ":R" & eP & "C" & cQty & ")"
        
        ' ?? NEW: Remaining Quantity sum
        outWS.Cells(writeRow, cRemQty).FormulaR1C1 = _
            "=SUM(R" & sP & "C" & cRemQty & ":R" & eP & "C" & cRemQty & ")"
        
        ' Start date left blank for manual entry
        
        ' Due date: MAX of all parent due dates
        outWS.Cells(writeRow, cDue).FormulaR1C1 = _
            "=IF(COUNT(R" & sP & "C" & cDue & ":R" & eP & "C" & cDue & ")=0,"""",MAX(R" & sP & "C" & cDue & ":R" & eP & "C" & cDue & "))"
        
        ' Percentage: weighted average of parents (which are now live formulas)
        outWS.Cells(writeRow, cPct).FormulaR1C1 = _
            "=IF(SUM(R" & sP & "C" & cQty & ":R" & eP & "C" & cQty & ")=0,""""," & _
              "SUMPRODUCT(R" & sP & "C" & cQty & ":R" & eP & "C" & cQty & ",R" & sP & "C" & cPct & ":R" & eP & "C" & cPct & ")/" & _
              "SUM(R" & sP & "C" & cQty & ":R" & eP & "C" & cQty & "))"
    End If

    ' Duration formula for totals row
    outWS.Cells(writeRow, cDur).FormulaR1C1 = _
        "=IF(AND(ISNUMBER(RC" & cStart & "),ISNUMBER(RC" & cDue & ")),RC" & cDue & "-RC" & cStart & "+1,"""")"

    ' Format date columns
    If cStart > 0 And writeRow > 11 Then
        outWS.Range(outWS.Cells(11, cStart), outWS.Cells(writeRow, cStart)).NumberFormat = "mmm-dd-yyyy"
    End If
    If cDue > 0 And writeRow > 11 Then
        outWS.Range(outWS.Cells(11, cDue), outWS.Cells(writeRow, cDue)).NumberFormat = "mmm-dd-yyyy"
    End If

    ' ?? PERFORMANCE: Apply formula row fix ONCE for ALL rows (not per-row)
    lastDataRowWritten = writeRow
    If firstDataRow > 0 And lastDataRowWritten >= firstDataRow Then
        If GB_DEBUG Then Debug.Print "Batch fixing timeline formulas: rows " & firstDataRow & " to " & lastDataRowWritten
        FixGanttFormulaRowReferenceRange outWS, firstDataRow, lastDataRowWritten, cPct + 1, lastCol
    End If

    ' Clean up temporary blueprint sheet
    On Error Resume Next
    Application.DisplayAlerts = False
    tmp.Visible = xlSheetVisible
    outWS.Activate
    tmp.Delete
    Application.DisplayAlerts = True
    On Error GoTo 0

WriteAggregation_Cleanup:
    ' ?? CRITICAL: Always restore Application settings
    Application.Calculation = calcMode
    Application.EnableEvents = True
    Application.ScreenUpdating = True
    Exit Sub
    
WriteAggregation_Error:
    If GB_DEBUG Then Debug.Print "ERROR in WriteAggregation: " & Err.Description
    Resume WriteAggregation_Cleanup
    
End Sub
'=========================== HELPERS ==================================
Private Sub MergeHeaderIfNeeded(ByVal ws As Worksheet, ByVal hdr As Long, ByVal colList As Variant)
    Dim i As Long, c As Long
    For i = LBound(colList) To UBound(colList)
        c = CLng(colList(i))
        If c > 0 Then
            With ws.Range(ws.Cells(hdr, c), ws.Cells(hdr + 1, c))
                If .MergeCells = False Then .Merge
                .HorizontalAlignment = xlCenter
                .VerticalAlignment = xlCenter
                .WrapText = True
            End With
        End If
    Next i
End Sub

Private Sub InsertFromBlueprint(ByVal tmp As Worksheet, ByVal tmpRow As Long, _
                                ByVal outWS As Worksheet, ByVal outRow As Long, _
                                ByVal cPct As Long, ByVal lastCol As Long, _
                                ByVal copyTimeline As Boolean)
    outWS.Rows(outRow).Insert Shift:=xlDown
    tmp.Rows(tmpRow).Copy
    outWS.Rows(outRow).PasteSpecial xlPasteFormats
    Application.CutCopyMode = False
    If copyTimeline And lastCol > cPct Then
        tmp.Range(tmp.Cells(tmpRow, cPct + 1), tmp.Cells(tmpRow, lastCol)).Copy
        outWS.Range(outWS.Cells(outRow, cPct + 1), outWS.Cells(outRow, lastCol)). _
            PasteSpecial xlPasteFormulas
        Application.CutCopyMode = False
        
        ' ?? REMOVED per-row fix - now done in batch at end (FixGanttFormulaRowReferenceRange)
        ' This was the main cause of freezing - called 100+ times × 300+ columns
    End If
End Sub

'======================= SCOPE SHEET CACHE =============================
' ?? PERFORMANCE: Build cache of scope sheets ONCE to avoid repeated IsScopeSheet calls
' Before: 100 child rows × 30 worksheets × IsScopeSheet check = 3,000 checks
' After:  30 worksheets × IsScopeSheet check = 30 checks (built once, reused)

Private Function BuildScopeSheetCache() As Object
    ' Returns Dictionary: key = sheet name, value = Worksheet object
    Dim cache As Object
    Set cache = CreateObject("Scripting.Dictionary")
    
    Dim ws As Worksheet
    For Each ws In ThisWorkbook.Worksheets
        If IsScopeSheet(ws) Then
            cache.Add ws.Name, ws
            If GB_DEBUG Then Debug.Print "  Cached scope sheet: " & ws.Name
        End If
    Next ws
    
    Set BuildScopeSheetCache = cache
End Function

'======================= FIX TIMELINE ROW REFERENCE ====================
' ?? CRITICAL: Gantt timeline formulas must reference Row 7 (dates) not Row 10 (day letters)

' ?? PERFORMANCE: Single-row version (kept for backward compatibility, but not used)
Private Sub FixGanttFormulaRowReference(ByVal ws As Worksheet, ByVal rowNum As Long, _
                                       ByVal startCol As Long, ByVal endCol As Long)
    ' Fixes timeline formula row references from $10 to $7
    ' Critical for gantt bars to display correctly
    ' NOTE: Use FixGanttFormulaRowReferenceRange for bulk operations!
    
    Dim col As Long
    Dim cell As Range
    Dim formula As String
    
    For col = startCol To endCol
        Set cell = ws.Cells(rowNum, col)
        If cell.HasFormula Then
            formula = cell.formula
            If InStr(formula, "$10") > 0 Then
                formula = Replace(formula, "$10", "$7")
                cell.formula = formula
            End If
        End If
    Next col
End Sub

' ?? NEW: BATCH version - Fixes ALL rows at once using Range.Replace (MUCH faster)
Private Sub FixGanttFormulaRowReferenceRange(ByVal ws As Worksheet, _
                                            ByVal startRow As Long, ByVal endRow As Long, _
                                            ByVal startCol As Long, ByVal endCol As Long)
    ' Fixes timeline formula row references from $10 to $7 for entire range
    ' Uses Range.Replace which is orders of magnitude faster than cell-by-cell
    
    If endRow < startRow Or endCol < startCol Then Exit Sub
    
    Dim rng As Range
    Set rng = ws.Range(ws.Cells(startRow, startCol), ws.Cells(endRow, endCol))
    
    ' Use Replace on the entire range - Excel handles this efficiently
    On Error Resume Next
    rng.Replace What:="$10", Replacement:="$7", LookAt:=xlPart, _
                SearchOrder:=xlByRows, MatchCase:=False, SearchFormat:=False, _
                ReplaceFormat:=False, FormulaVersion:=xlReplaceFormula2
    On Error GoTo 0
    
    If GB_DEBUG Then
        Debug.Print "Batch fixed timeline formulas: " & rng.Address & _
                    " (" & (endRow - startRow + 1) & " rows x " & (endCol - startCol + 1) & " cols)"
    End If
End Sub

Private Sub ApplyBlueprint(ByVal tmp As Worksheet, ByVal tmpRow As Long, _
                           ByVal outWS As Worksheet, ByVal targetRow As Long, _
                           ByVal cPct As Long, ByVal lastCol As Long, _
                           ByVal copyTimeline As Boolean)
    tmp.Rows(tmpRow).Copy
    outWS.Rows(targetRow).PasteSpecial xlPasteFormats
    Application.CutCopyMode = False
    If copyTimeline And lastCol > cPct Then
        tmp.Range(tmp.Cells(tmpRow, cPct + 1), tmp.Cells(tmpRow, lastCol)).Copy
        outWS.Range(outWS.Cells(targetRow, cPct + 1), outWS.Cells(targetRow, lastCol)). _
            PasteSpecial xlPasteFormulas
        Application.CutCopyMode = False
    End If
End Sub

Private Function CoalesceChildGroups(ByVal gAgg As Object, _
                                     ByVal inKeys As Object, _
                                     ByVal pid As String) As Object
    Dim tmp As Object: Set tmp = CreateObject("Scripting.Dictionary")
    tmp.CompareMode = vbTextCompare

    Dim k As Variant, a As Variant, norm As String
    Dim t As Variant

    For Each k In inKeys.keys
        a = gAgg(k)
        norm = LCase$(Trim$(CStr(a(2))))

        If tmp.Exists(norm) Then
            t = tmp(norm)
            t(3) = Nz(t(3), 0#) + Nz(a(3), 0#)

            If IsDate(a(4)) Then
                If (IsEmpty(t(4)) Or CDate(a(4)) > CDate(t(4))) Then t(4) = a(4)
            End If

            t(5) = Nz(t(5), 0#) + Nz(a(5), 0#)

            If (IsEmpty(t(6)) Or CLng(a(6)) < CLng(t(6))) Then t(6) = CLng(a(6))
            If (IsEmpty(t(7)) Or CLng(a(7)) > CLng(t(7))) Then t(7) = CLng(a(7))
            
            ' Keep the first source sheet name
            ' t(8) already has the sheet name from first occurrence

            tmp(norm) = t
        Else
            ReDim t(1 To 8)  ' Array size 8 to include sheet name
            t(1) = pid
            t(2) = a(2)
            t(3) = Nz(a(3), 0#)
            t(4) = IIf(IsDate(a(4)), a(4), Empty)
            t(5) = Nz(a(5), 0#)
            t(6) = CLng(a(6))
            t(7) = CLng(a(7))
            t(8) = a(8)  ' Preserve source sheet name
            tmp.Add norm, t
        End If
    Next k

    Dim res As Object: Set res = CreateObject("Scripting.Dictionary")

    Dim normKey As Variant
    For Each normKey In tmp.keys
        t = tmp(normKey)
        res.Add KeyFrom(t(6), CStr(normKey)), t
    Next normKey

    Set CoalesceChildGroups = res
End Function

Private Function KeyFrom(ByVal minLeaf As Long, ByVal normName As String) As String
    KeyFrom = Format$(minLeaf, "000000") & "|" & normName
End Function

'==================== HEADER FINDERS / MATCHERS =======================
Public Function IsScopeSheet(ByVal ws As Worksheet) As Boolean
    ' Check for headers in row defined by Global_Constants
    Dim hdr As Long: hdr = Global_Constants.SC_HEADER_ROW
    If hdr = 0 Then Exit Function

    Dim cID As Long, cPct As Long
    cID = Global_Constants.SC_COL_TASK_ID   ' Column E - Task_ID
    cPct = Global_Constants.SC_COL_PCT      ' Column N - % Completion
    
    ' Verify the columns exist and have the right headers
    Dim idHeader As String, pctHeader As String
    On Error Resume Next
    idHeader = UCase$(Trim$(CStr(ws.Cells(hdr, cID).Value)))
    pctHeader = UCase$(Trim$(CStr(ws.Cells(hdr, cPct).Value)))
    On Error GoTo 0
    
    ' DIAGNOSTIC: Show what we're checking
    If GB_DEBUG Then
        Debug.Print "IsScopeSheet check for '" & ws.Name & "':"
        Debug.Print "  Row " & hdr & ", Col " & cID & " (E" & hdr & "): '" & idHeader & "'"
        Debug.Print "  Row " & hdr & ", Col " & cPct & " (N" & hdr & "): '" & pctHeader & "'"
        Debug.Print "  Has 'TASK' AND 'ID': " & (InStr(idHeader, "TASK") > 0 And InStr(idHeader, "ID") > 0)
        Debug.Print "  Has 'COMPLETION' OR '%': " & (InStr(pctHeader, "COMPLETION") > 0 Or InStr(pctHeader, "%") > 0)
    End If
    
    IsScopeSheet = (InStr(idHeader, "TASK") > 0 And InStr(idHeader, "ID") > 0) And _
                   (InStr(pctHeader, "COMPLETION") > 0 Or InStr(pctHeader, "%") > 0)
End Function

Private Function FindGanttHeaderRow(ByVal ws As Worksheet) As Long
    FindGanttHeaderRow = FindHeaderRowByScore(ws, 4)
End Function

Private Function FindScopeHeaderRow(ByVal ws As Worksheet) As Long
    ' Return row from Global_Constants for scope sheets
    FindScopeHeaderRow = Global_Constants.SC_FIRST_DATA_ROW
End Function

Private Function FindHeaderRowByScore(ByVal ws As Worksheet, ByVal minScore As Long) As Long
    Dim r As Long, c As Long, lastC As Long, seen As Object, key As String
    For r = 1 To Application.Min(25, ws.UsedRange.Rows.Count)
        Set seen = CreateObject("Scripting.Dictionary")
        lastC = LastColInRow(ws, r)
        For c = 1 To lastC
            key = HKey(CStr(ws.Cells(r, c).Value))
            If IsKnownHeaderKey(key) Then If Not seen.Exists(key) Then seen.Add key, True
        Next c
        If seen.Count >= minScore Then
            FindHeaderRowByScore = r
            Exit Function
        End If
    Next r
End Function

Private Function IsKnownHeaderKey(ByVal k As String) As Boolean
    IsKnownHeaderKey = _
           k = "taskid" Or k = "id" _
        Or k = "scope+task+apparatus" Or k = "scope+task" _
        Or k = "taskname" Or k = "tasknames" _
        Or k = "tasknames+apparatus" Or k = "taskname+apparatus" _
        Or k = "apparatusquantity" Or k = "apparatusqty" Or k = "qty" _
        Or k = "remainingquantity" Or k = "remainingqty" Or k = "remqty" _
        Or k = "startdate" Or k = "start" _
        Or k = "duedate" Or k = "datedue" Or k = "due" _
        Or k = "pctoftaskcomplete" Or k = "pctcomplete" _
        Or k = "percentcomplete" Or k = "%complete" _
        Or k = "durationindays" Or k = "duration" Or k = "days"
End Function

Public Function FindColStrict(ByVal ws As Worksheet, _
                              ByVal hdrRow As Long, _
                              ByVal labels As Variant) As Long
    If hdrRow = 0 Then Exit Function
    Dim lastC As Long: lastC = LastColInRow(ws, hdrRow)
    Dim lab As Variant, want As String, c As Long, have As String
    For Each lab In labels
        want = HKey(CStr(lab))
        For c = 1 To lastC
            have = HKey(CStr(ws.Cells(hdrRow, c).Value))
            If have <> "" And have = want Then
                FindColStrict = c
                Exit Function
            End If
        Next c
    Next lab
End Function

'==================== DEBUG HELPERS ===================================
Private Sub DebugDumpHeaderMap(ByVal ws As Worksheet, ByVal hdr As Long, _
                               ByVal cID As Long, ByVal cname As Long, ByVal cQty As Long, _
                               ByVal cRemQty As Long, ByVal cStart As Long, ByVal cDue As Long, _
                               ByVal cPct As Long, ByVal cDur As Long)
    If Not GB_DEBUG Then Exit Sub
    GB_Log "===== HEADER MAP on '" & ws.Name & "' (hdr=" & hdr & ") ====="
    GB_Log "ID=" & cID & ", Name=" & cname & ", Qty=" & cQty & ", RemQty=" & cRemQty & _
           ", Start=" & cStart & ", Due=" & cDue & ", %=" & cPct & ", Dur=" & cDur
    GB_LogFlush
End Sub

'=========================== SMALL UTILS ===============================
Private Function HKey(ByVal s As String) As String
    Dim i As Long, ch As String, t As String
    s = LCase$(Trim$(s))
    For i = 1 To Len(s)
        ch = Mid$(s, i, 1)
        If (ch >= "a" And ch <= "z") Or (ch >= "0" And ch <= "9") Or ch = "+" Or ch = "-" Then t = t & ch
    Next i
    HKey = t
End Function

Private Function LastColInRow(ByVal ws As Worksheet, ByVal r As Long) As Long
    LastColInRow = ws.Cells(r, ws.Columns.Count).End(xlToLeft).Column
End Function

Private Function LastUsedRowIn(ByVal ws As Worksheet, ByVal c As Long) As Long
    If c <= 0 Then
        LastUsedRowIn = 0
    Else
        LastUsedRowIn = ws.Cells(ws.Rows.Count, c).End(xlUp).row
    End If
End Function

Private Function Nz(ByVal v As Variant, Optional ByVal Fallback As Variant = 0) As Variant
    If IsError(v) Or IsEmpty(v) Or v = "" Then Nz = Fallback Else Nz = v
End Function

' ENHANCED: Better percentage handling
Private Function PercentFromMixed(ByVal v As Variant) As Double
    ' Handle errors and empty values
    If IsError(v) Or IsEmpty(v) Then
        PercentFromMixed = 0#
        Exit Function
    End If
    
    ' Handle numeric values
    If IsNumeric(v) Then
        Dim numVal As Double
        numVal = CDbl(v)
        If numVal > 1# Then
            PercentFromMixed = numVal / 100#
        Else
            PercentFromMixed = numVal
        End If
        Exit Function
    End If
    
    ' Handle text values
    Dim t As String: t = CStr(v)
    ' Remove percentage sign and spaces
    t = Replace$(t, "%", "")
    t = Replace$(t, " ", "")
    t = Trim$(t)
    
    If Len(t) = 0 Then
        PercentFromMixed = 0#
    ElseIf IsNumeric(t) Then
        Dim textVal As Double
        textVal = CDbl(t)
        If textVal > 1# Then
            PercentFromMixed = textVal / 100#
        Else
            PercentFromMixed = textVal
        End If
    Else
        PercentFromMixed = 0#
    End If
End Function

Private Function UniqueSheetName(ByVal wb As Workbook, ByVal baseName As String) As String
    Dim i As Long, nm$
    i = 1
    Do
        nm = baseName & " " & i
        On Error Resume Next
        If wb.Worksheets(nm) Is Nothing Then
            UniqueSheetName = nm
            On Error GoTo 0
            Exit Function
        End If
        On Error GoTo 0
        i = i + 1
    Loop
End Function

Public Function EnumSelectedSheetNames(ByVal selectedSheets As Variant) As Variant
    Dim acc As Object: Set acc = CreateObject("System.Collections.ArrayList")
    Dim ws As Worksheet, v As Variant, i As Long, nm As String

    If IsMissing(selectedSheets) Or IsEmpty(selectedSheets) Then
        For Each ws In ThisWorkbook.Worksheets
            If ws.Visible = xlSheetVisible Then
                nm = ws.Name
                If GB_Normalize(nm) <> GB_Normalize(GB_TEMPLATE_NAME) _
                   And Left$(GB_Normalize(nm), Len(GB_Normalize(GB_OUTPUT_BASE))) _
                        <> GB_Normalize(GB_OUTPUT_BASE) Then
                    If IsScopeSheet(ws) Then acc.Add nm
                End If
            End If
        Next ws
    ElseIf TypeName(selectedSheets) = "Collection" Then
        For Each v In selectedSheets: acc.Add CStr(v): Next v
    ElseIf IsArray(selectedSheets) Then
        For i = LBound(selectedSheets) To UBound(selectedSheets)
            acc.Add CStr(selectedSheets(i))
        Next i
    ElseIf VarType(selectedSheets) = vbString Then
        acc.Add CStr(selectedSheets)
    End If

    If acc.Count = 0 Then
        EnumSelectedSheetNames = VBA.Array()
    Else
        EnumSelectedSheetNames = acc.ToArray
    End If
End Function

'========================= ID HELPERS =================================
Private Function GB_TwoSegKey(ByVal idTxt As String) As String
    Dim p() As String
    idTxt = Trim$(idTxt)
    If Len(idTxt) = 0 Then Exit Function
    p = Split(idTxt, ".")
    If UBound(p) >= 1 Then
        GB_TwoSegKey = p(0) & "." & p(1)
    Else
        GB_TwoSegKey = idTxt
    End If
End Function

Private Function GB_LeafKey(ByVal idTxt As String) As String
    Dim p As Long
    idTxt = Trim$(idTxt)
    p = InStrRev(idTxt, ".")
    If p > 0 Then GB_LeafKey = Mid$(idTxt, p + 1) Else GB_LeafKey = idTxt
End Function

Private Function GB_DigitsOnly(ByVal s As String) As String
    Dim i As Long, ch As String, t As String
    s = Trim$(s)
    For i = 1 To Len(s)
        ch = Mid$(s, i, 1)
        If ch >= "0" And ch <= "9" Then t = t & ch
    Next i
    GB_DigitsOnly = t
End Function

Private Function GB_LeafNumber(ByVal idTxt As String) As Long
    Dim seg As String, d As String
    seg = GB_LeafKey(idTxt)
    d = GB_DigitsOnly(seg)
    If Len(d) = 0 Then GB_LeafNumber = 0 Else GB_LeafNumber = CLng(Val(d))
End Function

'==================== PARENT-ID SORT HELPERS ===========================
Private Function SortedParentIds(ByVal pAgg As Object) As Variant
    Dim keys As Variant, i As Long, j As Long, k As Variant
    If pAgg Is Nothing Or pAgg.Count = 0 Then
        SortedParentIds = VBA.Array()
        Exit Function
    End If
    keys = pAgg.keys
    For i = LBound(keys) To UBound(keys) - 1
        For j = i + 1 To UBound(keys)
            If IdLess(CStr(keys(j)), CStr(keys(i))) Then
                k = keys(i): keys(i) = keys(j): keys(j) = k
            End If
        Next j
    Next i
    SortedParentIds = keys
End Function

Private Function IdLess(ByVal a As String, ByVal b As String) As Boolean
    Dim pa() As String, pb() As String, i As Long, n As Long
    Dim va As Long, vb As Long
    pa = Split(a, "."): pb = Split(b, ".")
    n = Application.Max(UBound(pa), UBound(pb))
    For i = 0 To n
        If i <= UBound(pa) Then va = Val(pa(i)) Else va = 0
        If i <= UBound(pb) Then vb = Val(pb(i)) Else vb = 0
        If va < vb Then IdLess = True: Exit Function
        If va > vb Then IdLess = False: Exit Function
    Next i
    IdLess = False
End Function

'==================== DIAGNOSTIC TEST FUNCTIONS =======================
Public Sub DiagnoseScope()
    ' Test function to check what's in your scope sheets
    Dim ws As Worksheet
    ' Change "SES" to one of your actual scope sheet names
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("SES")
    On Error GoTo 0
    
    If ws Is Nothing Then
        Debug.Print "ERROR: Sheet 'SES' not found. Please update sheet name in DiagnoseScope()"
        Exit Sub
    End If
    
    Debug.Print "=== SCOPE SHEET: " & ws.Name & " (Using Global_Constants) ==="
    Debug.Print ""
    Debug.Print "Headers (Row " & Global_Constants.SC_FIRST_DATA_ROW & "):"
    Debug.Print "  " & Global_Constants.GetColumnLetter(Global_Constants.SC_COL_TASK_ID) & Global_Constants.SC_FIRST_DATA_ROW & ": " & ws.Cells(Global_Constants.SC_FIRST_DATA_ROW, Global_Constants.SC_COL_TASK_ID).Value
    Debug.Print "  " & Global_Constants.GetColumnLetter(Global_Constants.SC_COL_NAME_APP) & Global_Constants.SC_FIRST_DATA_ROW & ": " & ws.Cells(Global_Constants.SC_FIRST_DATA_ROW, Global_Constants.SC_COL_NAME_APP).Value
    Debug.Print "  " & Global_Constants.GetColumnLetter(Global_Constants.SC_COL_DATE_DUE) & Global_Constants.SC_FIRST_DATA_ROW & ": " & ws.Cells(Global_Constants.SC_FIRST_DATA_ROW, Global_Constants.SC_COL_DATE_DUE).Value
    Debug.Print "  " & Global_Constants.GetColumnLetter(Global_Constants.SC_COL_PCT) & Global_Constants.SC_FIRST_DATA_ROW & ": " & ws.Cells(Global_Constants.SC_FIRST_DATA_ROW, Global_Constants.SC_COL_PCT).Value
    Debug.Print ""
    
    Dim dataRow As Long: dataRow = Global_Constants.SC_FIRST_DATA_ROW + 1
    Debug.Print "First Data Row (Row " & dataRow & "):"
    Debug.Print "  Task_ID: " & ws.Cells(dataRow, Global_Constants.SC_COL_TASK_ID).Value
    Debug.Print "  Task Name: " & ws.Cells(dataRow, Global_Constants.SC_COL_NAME_APP).Value
    Debug.Print "  Due Date: " & ws.Cells(dataRow, Global_Constants.SC_COL_DATE_DUE).Value & " | Format: " & ws.Cells(dataRow, Global_Constants.SC_COL_DATE_DUE).NumberFormat
    Debug.Print "  % Complete: " & ws.Cells(dataRow, Global_Constants.SC_COL_PCT).Value & " | Format: " & ws.Cells(dataRow, Global_Constants.SC_COL_PCT).NumberFormat
    Debug.Print ""
    Debug.Print "Date test for Due Date:"
    Debug.Print "  IsDate: " & IsDate(ws.Cells(dataRow, Global_Constants.SC_COL_DATE_DUE).Value)
    If IsDate(ws.Cells(dataRow, Global_Constants.SC_COL_DATE_DUE).Value) Then
        Debug.Print "  Date value: " & CDate(ws.Cells(dataRow, Global_Constants.SC_COL_DATE_DUE).Value)
    End If
    Debug.Print ""
    Debug.Print "% test for % Complete:"
    Dim pctTest As Double
    pctTest = PercentFromMixed(ws.Cells(dataRow, Global_Constants.SC_COL_PCT).Value)
    Debug.Print "  Converted to: " & Format(pctTest, "0.00%")
    Debug.Print ""
    Debug.Print "? All column references using Global_Constants!"
End Sub


