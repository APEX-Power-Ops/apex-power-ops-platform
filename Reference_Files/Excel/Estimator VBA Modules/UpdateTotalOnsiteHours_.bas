Attribute VB_Name = "UpdateTotalOnsiteHours_"
'============================================================
' UPDATE TOTAL ONSITE HOURS - With Bidirectional Calculator Setup
' Silent operation (error messages only)
'============================================================
Public Sub UpdateTotalOnsiteHours()
    Dim equipRefWS As Worksheet
    Dim ws As Worksheet
    Dim i As Integer
    Dim rowNum As Integer
    Dim totalHours As Double
    Dim scopeValue As Variant
    Dim countNonZero As Integer
    
    On Error GoTo ErrorHandler
    
    ' Use CodeName for Equipment Reference
    Set equipRefWS = Equipment_Reference
    
    ' ========================================
    ' PART 1: Calculate Total Onsite Hours
    ' ========================================
    For rowNum = 3 To 8
        totalHours = 0
        countNonZero = 0
        
        ' Sum from all 20 scope sheets using CodeNames
        For i = 1 To 20
            Select Case i
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
            
            ' Get value from R3 of each scope sheet
            scopeValue = ws.Range("R3").value
            
            ' Add to total if numeric and not empty string
            If scopeValue <> "" Then
                If IsNumeric(scopeValue) Then
                    If CDbl(scopeValue) <> 0 Then
                        totalHours = totalHours + CDbl(scopeValue)
                        countNonZero = countNonZero + 1
                    End If
                End If
            End If
        Next i
        
        ' Write total to Equipment Reference
        equipRefWS.Cells(rowNum, "R").value = totalHours
    Next rowNum
    
    ' ========================================
    ' PART 2: Set Up Bidirectional Calculator Formulas
    ' ========================================
    
    ' U3:U4 - Days to Complete = R / (S * T)
    equipRefWS.Range("U3").Formula = "=IFERROR(R3/(S3*T3),"""")"
    equipRefWS.Range("U4").Formula = "=IFERROR(R4/(S4*T4),"""")"
    
    ' T5:T6 - Hours/Day = R / (S * U)
    equipRefWS.Range("T5").Formula = "=IFERROR(R5/(S5*U5),"""")"
    equipRefWS.Range("T6").Formula = "=IFERROR(R6/(S6*U6),"""")"
    
    ' S7:S8 - # Techs/Day = R / (T * U)
    equipRefWS.Range("S7").Formula = "=IFERROR(R7/(T7*U7),"""")"
    equipRefWS.Range("S8").Formula = "=IFERROR(R8/(T8*U8),"""")"
    
    ' No success message - silent operation
    Exit Sub
    
ErrorHandler:
    MsgBox "Error: " & Err.Description & vbCrLf & _
           "Error Number: " & Err.Number, vbCritical, "Update Error"
End Sub


'============================================================
' SETUP ONLY FORMULAS - Just set up the calculator formulas
'============================================================
Public Sub SetupBidirectionalCalculatorFormulas()
    Dim equipRefWS As Worksheet
    
    On Error GoTo ErrorHandler
    Set equipRefWS = Equipment_Reference
    
    ' U3:U4 - Days to Complete = R / (S * T)
    equipRefWS.Range("U3").Formula = "=IFERROR(R3/(S3*T3),"""")"
    equipRefWS.Range("U4").Formula = "=IFERROR(R4/(S4*T4),"""")"
    
    ' T5:T6 - Hours/Day = R / (S * U)
    equipRefWS.Range("T5").Formula = "=IFERROR(R5/(S5*U5),"""")"
    equipRefWS.Range("T6").Formula = "=IFERROR(R6/(S6*U6),"""")"
    
    ' S7:S8 - # Techs/Day = R / (T * U)
    equipRefWS.Range("S7").Formula = "=IFERROR(R7/(T7*U7),"""")"
    equipRefWS.Range("S8").Formula = "=IFERROR(R8/(T8*U8),"""")"
    
    ' No success message - silent operation
    Exit Sub
    
ErrorHandler:
    MsgBox "Error: " & Err.Description, vbCritical
End Sub


'============================================================
' DIAGNOSTIC: Show what values are being read
' (Diagnostic should show messages - kept as-is)
'============================================================
Public Sub DiagnoseTotalOnsiteHours()
    Dim equipRefWS As Worksheet
    Dim ws As Worksheet
    Dim i As Integer
    Dim scopeValue As Variant
    Dim reportMsg As String
    Dim totalSum As Double
    Dim sheetCount As Integer
    
    On Error GoTo ErrorHandler
    Set equipRefWS = Equipment_Reference
    
    reportMsg = "TOTAL ONSITE HOURS DIAGNOSTIC" & vbCrLf & String(50, "=") & vbCrLf & vbCrLf
    
    totalSum = 0
    sheetCount = 0
    
    For i = 1 To 20
        Select Case i
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
        
        scopeValue = ws.Range("R3").value
        
        If scopeValue = "" Then
            ' Skip empty values
        ElseIf IsNumeric(scopeValue) Then
            If CDbl(scopeValue) <> 0 Then
                reportMsg = reportMsg & ws.Name & " (Scope" & i & "): " & Format(scopeValue, "0.00") & vbCrLf
                totalSum = totalSum + CDbl(scopeValue)
                sheetCount = sheetCount + 1
            End If
        Else
            reportMsg = reportMsg & ws.Name & ": [Invalid - " & TypeName(scopeValue) & "]" & vbCrLf
        End If
    Next i
    
    reportMsg = reportMsg & vbCrLf & String(50, "-") & vbCrLf
    reportMsg = reportMsg & "Sheets with values: " & sheetCount & vbCrLf
    reportMsg = reportMsg & "TOTAL: " & Format(totalSum, "0.00") & vbCrLf & vbCrLf
    reportMsg = reportMsg & "Equipment Reference R3 current value: " & equipRefWS.Range("R3").value
    
    ' Check if calculator formulas are in place
    reportMsg = reportMsg & vbCrLf & vbCrLf & "Calculator Formulas Status:" & vbCrLf
    reportMsg = reportMsg & "  U3: " & IIf(Left(equipRefWS.Range("U3").Formula, 8) = "=IFERROR", "? OK", "? Missing") & vbCrLf
    reportMsg = reportMsg & "  T6: " & IIf(Left(equipRefWS.Range("T6").Formula, 8) = "=IFERROR", "? OK", "? Missing") & vbCrLf
    reportMsg = reportMsg & "  S8: " & IIf(Left(equipRefWS.Range("S8").Formula, 8) = "=IFERROR", "? OK", "? Missing")
    
    MsgBox reportMsg, vbInformation, "Diagnostic Report"
    
    Exit Sub
    
ErrorHandler:
    MsgBox "Error during diagnostics: " & Err.Description, vbCritical
End Sub


