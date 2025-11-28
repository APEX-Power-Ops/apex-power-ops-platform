Attribute VB_Name = "DataverseMappingVerification"
'============================================================
' DATAVERSE MAPPING VERIFICATION MODULE
' Purpose: Extract and document all data from Estimator workbook
'          to verify cell locations before building automation
'
' Output: Text file with structured data for review
' Usage: Run ExportMappingVerification from any Estimator workbook
'
' Created: November 27, 2025
'============================================================

Option Explicit

Public Sub ExportMappingVerification()
    '============================================================
    ' Main entry point - exports all workbook data for verification
    '============================================================
    
    Dim outputPath As String
    Dim fileNum As Integer
    Dim ws As Worksheet
    Dim i As Integer
    
    On Error GoTo ErrorHandler
    
    ' Handle cloud/unsaved workbooks - use Desktop as fallback
    Dim basePath As String
    If Len(ThisWorkbook.Path) = 0 Or InStr(ThisWorkbook.Path, "https://") > 0 Then
        basePath = Environ("USERPROFILE") & "\Desktop"
    Else
        basePath = ThisWorkbook.Path
    End If
    
    ' Create output file
    outputPath = basePath & "\" & _
                 Replace(ThisWorkbook.Name, ".xlsm", "") & _
                 "_MAPPING_VERIFICATION_" & Format(Now, "yyyymmdd_hhmmss") & ".txt"
    
    fileNum = FreeFile
    Open outputPath For Output As #fileNum
    
    ' Header
    Print #fileNum, "============================================================"
    Print #fileNum, "ESTIMATOR TO DATAVERSE MAPPING VERIFICATION"
    Print #fileNum, "============================================================"
    Print #fileNum, "Workbook: " & ThisWorkbook.Name
    Print #fileNum, "Path: " & ThisWorkbook.FullName
    Print #fileNum, "Generated: " & Format(Now, "yyyy-mm-dd hh:mm:ss")
    Print #fileNum, ""
    
    '------------------------------------------------------------
    ' SECTION 1: PROJECT HEADER INFO
    '------------------------------------------------------------
    Print #fileNum, "============================================================"
    Print #fileNum, "SECTION 1: PROJECT HEADER (-> cr950_projects)"
    Print #fileNum, "============================================================"
    Print #fileNum, ""
    
    ' Extract project number from filename
    Print #fileNum, "Project Number (from filename): " & ExtractProjectNumber(ThisWorkbook.Name)
    Print #fileNum, "  -> Maps to: cr950_projectnumber"
    Print #fileNum, ""
    
    '------------------------------------------------------------
    ' SECTION 2: EQUIPMENT REFERENCE SHEET
    '------------------------------------------------------------
    Print #fileNum, "============================================================"
    Print #fileNum, "SECTION 2: EQUIPMENT REFERENCE SHEET"
    Print #fileNum, "============================================================"
    Print #fileNum, ""
    
    Call ExportEquipmentReference(fileNum)
    
    '------------------------------------------------------------
    ' SECTION 3: SCOPE SHEETS (1-20)
    '------------------------------------------------------------
    Print #fileNum, "============================================================"
    Print #fileNum, "SECTION 3: SCOPE SHEETS (-> cr950_projectscopes)"
    Print #fileNum, "============================================================"
    Print #fileNum, ""
    
    For i = 1 To 20
        Call ExportScopeSheet(fileNum, i)
    Next i
    
    '------------------------------------------------------------
    ' SECTION 4: SUMMARY
    '------------------------------------------------------------
    Print #fileNum, "============================================================"
    Print #fileNum, "SECTION 4: MAPPING SUMMARY"
    Print #fileNum, "============================================================"
    Print #fileNum, ""
    Call ExportMappingSummary(fileNum)
    
    Close #fileNum
    
    MsgBox "Mapping verification exported to:" & vbCrLf & vbCrLf & outputPath, vbInformation, "Export Complete"
    
    ' Open the file
    Shell "notepad.exe """ & outputPath & """", vbNormalFocus
    
    Exit Sub
    
ErrorHandler:
    If fileNum > 0 Then Close #fileNum
    MsgBox "Error: " & Err.Description, vbCritical, "Export Failed"
End Sub

Private Sub ExportEquipmentReference(fileNum As Integer)
    '============================================================
    ' Export Equipment Reference sheet data
    '============================================================
    
    Dim ws As Worksheet
    Dim i As Long
    Dim scopeName As String
    Dim scopeTotal As Variant
    
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("Equipment Reference")
    On Error GoTo 0
    
    If ws Is Nothing Then
        Print #fileNum, "ERROR: Equipment Reference sheet not found!"
        Print #fileNum, ""
        Exit Sub
    End If
    
    ' Grand Total
    Print #fileNum, "GRAND TOTAL (all scopes):"
    Print #fileNum, "  Cell M3 Value: " & ws.Range("M3").Value
    Print #fileNum, "  -> Maps to: Project-level total (informational)"
    Print #fileNum, ""
    
    ' Scope Sheet Names and Totals (L4:M23)
    Print #fileNum, "SCOPE SHEET LIST (L4:L23) and TOTALS (M4:M23):"
    Print #fileNum, "  Row | Sheet Name (Col L) | Total (Col M)"
    Print #fileNum, "  ----|--------------------|--------------"
    
    For i = 4 To 23
        scopeName = CStr(ws.Range("L" & i).Value)
        scopeTotal = ws.Range("M" & i).Value
        
        If Len(Trim(scopeName)) > 0 Then
            Print #fileNum, "  " & Format(i, "00") & "  | " & Left(scopeName & String(18, " "), 18) & " | " & FormatCurrency(scopeTotal, 2)
        End If
    Next i
    Print #fileNum, ""
    
    ' Equipment Table Summary
    Print #fileNum, "EQUIPMENT TABLE (tblEquipment):"
    Print #fileNum, "  Location: B3:F486"
    Print #fileNum, "  Hours Used Column: H"
    
    Dim equipCount As Long
    equipCount = 0
    For i = 3 To 486
        If Len(Trim(CStr(ws.Range("E" & i).Value))) > 0 Then
            equipCount = equipCount + 1
        End If
    Next i
    Print #fileNum, "  Equipment Types Found: " & equipCount
    Print #fileNum, "  -> Maps to: cr950_apparatustypemaster (reference table)"
    Print #fileNum, ""
    
    ' Total Onsite Hours Summary (R3:R8)
    Print #fileNum, "TOTAL ONSITE HOURS SUMMARY (R3:R8):"
    For i = 3 To 8
        If IsNumeric(ws.Range("R" & i).Value) And ws.Range("R" & i).Value > 0 Then
            Print #fileNum, "  R" & i & ": " & ws.Range("R" & i).Value & " hours"
        End If
    Next i
    Print #fileNum, ""
End Sub

Private Sub ExportScopeSheet(fileNum As Integer, scopeIndex As Integer)
    '============================================================
    ' Export individual scope sheet data
    '============================================================
    
    Dim ws As Worksheet
    Dim totalHours As Variant
    Dim grandTotal As Variant
    Dim scopeType As String
    Dim i As Long
    Dim apparatusCount As Long
    
    ' Get scope sheet by code name pattern
    On Error Resume Next
    Select Case scopeIndex
        Case 1: Set ws = Scope1
        Case 2: Set ws = Scope2
        Case 3: Set ws = Scope3
        Case 4: Set ws = Scope4
        Case 5: Set ws = Scope5
        Case 6: Set ws = Scope6
        Case 7: Set ws = Scope7
        Case 8: Set ws = Scope8
        Case 9: Set ws = Scope9
        Case 10: Set ws = Scope10
        Case 11: Set ws = Scope11
        Case 12: Set ws = Scope12
        Case 13: Set ws = Scope13
        Case 14: Set ws = Scope14
        Case 15: Set ws = Scope15
        Case 16: Set ws = Scope16
        Case 17: Set ws = Scope17
        Case 18: Set ws = Scope18
        Case 19: Set ws = Scope19
        Case 20: Set ws = Scope20
    End Select
    On Error GoTo 0
    
    If ws Is Nothing Then Exit Sub
    
    ' Check if scope has data
    totalHours = ws.Range("J3").Value
    If Not IsNumeric(totalHours) Or totalHours = 0 Then Exit Sub
    
    Print #fileNum, "------------------------------------------------------------"
    Print #fileNum, "SCOPE " & scopeIndex & ": " & ws.Name
    Print #fileNum, "  VBA CodeName: Scope" & scopeIndex
    Print #fileNum, "------------------------------------------------------------"
    Print #fileNum, ""
    
    ' Header Info
    Print #fileNum, "SCOPE HEADER:"
    Print #fileNum, "  A1 (Project Name): " & ws.Range("A1").Value
    Print #fileNum, "  C4 (Job Type): " & ws.Range("C4").Value
    Print #fileNum, "    -> Maps to: cr950_scopetype (MTS/ATS choice)"
    Print #fileNum, ""
    
    ' Totals
    Print #fileNum, "SCOPE TOTALS:"
    Print #fileNum, "  J3 (Total Onsite Hours): " & ws.Range("J3").Value
    Print #fileNum, "    -> Maps to: cr950_totalestimatedhours"
    Print #fileNum, "  M4 (Multiplier): " & ws.Range("M4").Value
    Print #fileNum, "    -> Maps to: cr950_multiplier"
    Print #fileNum, "  P3 (Grand Total): " & FormatCurrency(ws.Range("P3").Value, 2)
    Print #fileNum, "    -> Maps to: cr950_quotedamount"
    Print #fileNum, "  P4 (Adjusted Total): " & FormatCurrency(ws.Range("P4").Value, 2)
    Print #fileNum, ""
    
    ' Financial Sections
    Print #fileNum, "FINANCIAL SECTIONS (-> cr950_scopelabordetails):"
    Call ExportFinancialSection(fileNum, ws)
    
    ' Apparatus Data
    Print #fileNum, "APPARATUS DATA (-> cr950_apparatus via cr950_tasks):"
    apparatusCount = 0
    
    Print #fileNum, "  Row | Qty | Equipment Type (Col E) | Hours (Col I) | Total (Col J)"
    Print #fileNum, "  ----|-----|------------------------|---------------|-------------"
    
    For i = 6 To 100  ' First 100 rows for verification (not all 488)
        Dim qty As Variant
        Dim equipType As String
        Dim hours As Variant
        Dim totalHrs As Variant
        
        qty = ws.Range("C" & i).Value
        equipType = Trim(CStr(ws.Range("E" & i).Value))
        hours = ws.Range("I" & i).Value
        totalHrs = ws.Range("J" & i).Value
        
        ' Check for data row (has equipment type and quantity > 0)
        If Len(equipType) > 0 And IsNumeric(qty) And qty > 0 Then
            apparatusCount = apparatusCount + CInt(qty)
            Print #fileNum, "  " & Format(i, "000") & " | " & Format(qty, "00") & "  | " & _
                           Left(equipType & String(22, " "), 22) & " | " & _
                           Format(hours, "0.00") & String(9, " ") & " | " & Format(totalHrs, "0.00")
        ElseIf Len(equipType) > 0 And ws.Range("E" & i).Font.Bold Then
            ' Section header
            Print #fileNum, "  " & Format(i, "000") & " | -- | [SECTION: " & equipType & "]"
        End If
    Next i
    
    Print #fileNum, ""
    Print #fileNum, "  Total Apparatus Records to Create: " & apparatusCount
    Print #fileNum, "    -> Each qty=N creates N apparatus records"
    Print #fileNum, ""
End Sub

Private Sub ExportFinancialSection(fileNum As Integer, ws As Worksheet)
    '============================================================
    ' Export financial section with row discovery
    '============================================================
    
    Dim i As Long
    Dim label As String
    Dim foundSections As String
    
    ' Scan columns L-P for financial section headers and data
    ' Looking for patterns: "Offsite Labor", "Travel", "Outside Services"
    
    Print #fileNum, ""
    Print #fileNum, "  Scanning Columns L-P for financial data..."
    Print #fileNum, ""
    
    For i = 1 To 40  ' Scan first 40 rows
        label = Trim(CStr(ws.Range("L" & i).Value))
        
        ' Check for section headers or data
        If Len(label) > 0 Then
            Dim colM As Variant, colN As Variant, colO As Variant, colP As Variant
            colM = ws.Range("M" & i).Value
            colN = ws.Range("N" & i).Value
            colO = ws.Range("O" & i).Value
            colP = ws.Range("P" & i).Value
            
            ' Format output
            If InStr(1, label, "Total", vbTextCompare) > 0 Or _
               InStr(1, label, "Labor", vbTextCompare) > 0 Or _
               InStr(1, label, "Travel", vbTextCompare) > 0 Or _
               InStr(1, label, "Services", vbTextCompare) > 0 Or _
               InStr(1, label, "Report", vbTextCompare) > 0 Or _
               InStr(1, label, "Project", vbTextCompare) > 0 Or _
               InStr(1, label, "Hotel", vbTextCompare) > 0 Or _
               InStr(1, label, "Flight", vbTextCompare) > 0 Or _
               InStr(1, label, "Car", vbTextCompare) > 0 Or _
               InStr(1, label, "Generator", vbTextCompare) > 0 Or _
               InStr(1, label, "Equipment", vbTextCompare) > 0 Or _
               InStr(1, label, "Oil", vbTextCompare) > 0 Or _
               InStr(1, label, "Misc", vbTextCompare) > 0 Or _
               InStr(1, label, "Loading", vbTextCompare) > 0 Then
                
                Print #fileNum, "  Row " & Format(i, "00") & " | L: " & Left(label & String(25, " "), 25) & _
                               " | M: " & FormatValue(colM) & _
                               " | N: " & FormatValue(colN) & _
                               " | O: " & FormatValue(colO) & _
                               " | P: " & FormatValue(colP)
            End If
        End If
    Next i
    
    Print #fileNum, ""
End Sub

Private Sub ExportMappingSummary(fileNum As Integer)
    '============================================================
    ' Export summary of mappings for verification
    '============================================================
    
    Print #fileNum, "DATAVERSE TABLE MAPPING REFERENCE:"
    Print #fileNum, ""
    Print #fileNum, "  cr950_projects (Projects)"
    Print #fileNum, "    - cr950_name: From A1 of first scope sheet"
    Print #fileNum, "    - cr950_projectnumber: From workbook filename"
    Print #fileNum, "    - cr950_clientid: User selection/lookup"
    Print #fileNum, "    - cr950_siteid: User selection/lookup"
    Print #fileNum, ""
    Print #fileNum, "  cr950_projectscopes (Scopes)"
    Print #fileNum, "    - cr950_name: Scope sheet name"
    Print #fileNum, "    - cr950_projectid: Parent project"
    Print #fileNum, "    - cr950_scopetype: C4 (MTS/ATS)"
    Print #fileNum, "    - cr950_quotedamount: P3"
    Print #fileNum, "    - cr950_totalestimatedhours: J3"
    Print #fileNum, "    - cr950_multiplier: M4"
    Print #fileNum, ""
    Print #fileNum, "  cr950_scopelabordetails (Financial Config)"
    Print #fileNum, "    - cr950_projectscopeid: Parent scope"
    Print #fileNum, "    - cr950_onsitelaborhours: J3"
    Print #fileNum, "    - cr950_offsitelabortotal: Financial section totals"
    Print #fileNum, "    - cr950_traveltotal: Travel section total"
    Print #fileNum, "    - cr950_outsideservicestotal: Outside Services total"
    Print #fileNum, ""
    Print #fileNum, "  cr950_tasks (Tasks)"
    Print #fileNum, "    - cr950_name: Equipment type category"
    Print #fileNum, "    - cr950_projectscopeid: Parent scope"
    Print #fileNum, "    - cr950_projectid: Parent project"
    Print #fileNum, ""
    Print #fileNum, "  cr950_apparatus (Apparatus)"
    Print #fileNum, "    - cr950_name: Equipment designation"
    Print #fileNum, "    - cr950_taskid: Parent task"
    Print #fileNum, "    - cr950_apparatushours: Column I value"
    Print #fileNum, "    - cr950_apparatustypemasterid: Lookup to master"
    Print #fileNum, ""
    Print #fileNum, "============================================================"
    Print #fileNum, "END OF VERIFICATION REPORT"
    Print #fileNum, "============================================================"
End Sub

Private Function ExtractProjectNumber(filename As String) As String
    '============================================================
    ' Extract project number from filename (e.g., "434469" from "434469 REV6...")
    '============================================================
    
    Dim i As Long
    Dim result As String
    
    result = ""
    For i = 1 To Len(filename)
        If IsNumeric(Mid(filename, i, 1)) Then
            result = result & Mid(filename, i, 1)
        ElseIf Len(result) > 0 Then
            Exit For  ' Stop at first non-numeric after finding numbers
        End If
    Next i
    
    ExtractProjectNumber = result
End Function

Private Function FormatValue(val As Variant) As String
    '============================================================
    ' Format value for display
    '============================================================
    
    If IsEmpty(val) Or val = "" Then
        FormatValue = "      "
    ElseIf IsNumeric(val) Then
        If val >= 100 Then
            FormatValue = Format(val, "$#,##0")
        ElseIf val >= 1 Then
            FormatValue = Format(val, "0.00")
        Else
            FormatValue = Format(val, "0.0%")
        End If
        FormatValue = Left(FormatValue & String(6, " "), 6)
    Else
        FormatValue = Left(CStr(val) & String(6, " "), 6)
    End If
End Function
