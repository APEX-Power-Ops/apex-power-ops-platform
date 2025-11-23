Attribute VB_Name = "FormulaPersistance"

Option Explicit

Dim ScopeSheets(1 To 20) As New clsscopesheet

Sub SetTextFormatting()
    On Error Resume Next
    With Equipment_Reference.Range("B3:C486")
        .NumberFormat = "@"
        Application.EnableEvents = False
        .NumberFormat = "General"
        .NumberFormat = "@"
        Application.EnableEvents = True
    End With
    On Error GoTo 0
End Sub

Sub EnforceEquipmentTextFormat(Target As Range)
    If Not Intersect(Target, Equipment_Reference.Range("B3:C486")) Is Nothing Then
        Application.EnableEvents = False
        Target.NumberFormat = "@"
        Application.EnableEvents = True
    End If
End Sub

Sub InitializeScopeSheets()
    Call RestoreAllFormulas(Scope1)
    Call RestoreAllFormulas(Scope2)
    Call RestoreAllFormulas(Scope3)
    Call RestoreAllFormulas(Scope4)
    Call RestoreAllFormulas(Scope5)
    Call RestoreAllFormulas(Scope6)
    Call RestoreAllFormulas(Scope7)
    Call RestoreAllFormulas(Scope8)
    Call RestoreAllFormulas(Scope9)
    Call RestoreAllFormulas(Scope10)
    Call RestoreAllFormulas(Scope11)
    Call RestoreAllFormulas(Scope12)
    Call RestoreAllFormulas(Scope13)
    Call RestoreAllFormulas(Scope14)
    Call RestoreAllFormulas(Scope15)
    Call RestoreAllFormulas(Scope16)
    Call RestoreAllFormulas(Scope17)
    Call RestoreAllFormulas(Scope18)
    Call RestoreAllFormulas(Scope19)
    Call RestoreAllFormulas(Scope20)
    
End Sub

Sub QuickCheckAndRestore()
    Dim ws As Worksheet
    Dim needsRestore As Boolean
    Dim i As Integer
    
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False
    
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
        
        needsRestore = False
        If ws.Range("D6").Formula = "" Then needsRestore = True
        If ws.Range("I6").Formula = "" Then needsRestore = True
        If ws.Range("J6").Formula = "" Then needsRestore = True
        If ws.Range("J3").Formula = "" Then needsRestore = True
        If ws.Range("P14").Formula = "" Then needsRestore = True
        
        If needsRestore Then
            Call RestoreAllFormulas(ws)
        End If
    Next i
    
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    Application.EnableEvents = True
End Sub

Sub InitializeScopeEventHandlers()
    On Error Resume Next
    Set ScopeSheets(1).SheetObject = Scope1
    Set ScopeSheets(2).SheetObject = Scope2
    Set ScopeSheets(3).SheetObject = Scope3
    Set ScopeSheets(4).SheetObject = Scope4
    Set ScopeSheets(5).SheetObject = Scope5
    Set ScopeSheets(6).SheetObject = Scope6
    Set ScopeSheets(7).SheetObject = Scope7
    Set ScopeSheets(8).SheetObject = Scope8
    Set ScopeSheets(9).SheetObject = Scope9
    Set ScopeSheets(10).SheetObject = Scope10
    Set ScopeSheets(11).SheetObject = Scope11
    Set ScopeSheets(12).SheetObject = Scope12
    Set ScopeSheets(13).SheetObject = Scope13
    Set ScopeSheets(14).SheetObject = Scope14
    Set ScopeSheets(15).SheetObject = Scope15
    Set ScopeSheets(16).SheetObject = Scope16
    Set ScopeSheets(17).SheetObject = Scope17
    Set ScopeSheets(18).SheetObject = Scope18
    Set ScopeSheets(19).SheetObject = Scope19
    Set ScopeSheets(20).SheetObject = Scope20
    
    On Error GoTo 0
End Sub

Sub RunCompleteSetup()
    Dim response As VbMsgBoxResult
    Dim ws As Worksheet
    
    response = MsgBox("This will restore ALL formulas in ALL Scope sheets." & vbCrLf & _
                     "This may take 30-60 seconds." & vbCrLf & vbCrLf & _
                     "Only run if formulas are missing or broken." & vbCrLf & vbCrLf & _
                     "Continue?", vbYesNo + vbQuestion, "Full Formula Restore")
    
    If response = vbYes Then
        Application.ScreenUpdating = False
        Application.Calculation = xlCalculationManual
        Application.StatusBar = "Restoring formulas... Please wait..."
        
        On Error Resume Next
        For Each ws In ThisWorkbook.Worksheets
            ws.Unprotect Password:=""
        Next ws
        On Error GoTo 0
        
        Call SetTextFormatting
        Call InitializeScopeSheets
        Call InitializeScopeEventHandlers
        
        On Error Resume Next
        For Each ws In ThisWorkbook.Worksheets
            ws.Unprotect Password:=""
        Next ws
        On Error GoTo 0
        
        Application.StatusBar = False
        Application.Calculation = xlCalculationAutomatic
        Application.ScreenUpdating = True
        
        MsgBox "Setup Complete! All formulas restored.", vbInformation
    End If
End Sub

Sub RestoreAllFormulas(ws As Worksheet)
    Application.EnableEvents = False
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    With ws
        ' ===== EQUIPMENT LOOKUP COLUMNS =====
        If .Range("D6").Formula = "" Or .Range("I6").Formula = "" Or .Range("J6").Formula = "" Then
            RestoreColumnDFormulas ws
            RestoreColumnIFormulas ws
            RestoreColumnJFormulas ws
        End If
        
        ' ===== GRAND TOTALS (Row 3-4) =====
        ' CORRECTED: P3 uses P19 (not P18), P26 (not P25), P33 (not P32)
        If .Range("J3").Formula = "" Then .Range("J3").Formula = "=SUMIF(J6:J488,""<>"",J6:J488)"
        If .Range("O3").Formula = "" Then .Range("O3").Formula = "=""0%"""
        If .Range("O4").Formula = "" Then .Range("O4").Formula = "=IFERROR((P4-P3)/P3,""0%"")"
        If .Range("P3").Formula = "" Then .Range("P3").Formula = "=SUM(P14,P19,P26,P33)"
        If .Range("P4").Formula = "" Then .Range("P4").Formula = "=P3*M4*N4"
        
        ' ===== SECTION 1: BILLABLE ADDERS (Rows 6-13) =====
        ' Data rows 6-13, Total row 14
        If .Range("N6").Formula = "" Then
            .Range("N6").Formula = "=$J$3*M6"
            .Range("N7").Formula = "=$J$3*M7"
            .Range("N8").Formula = "=$J$3*M8"
            .Range("N9").Formula = "=$J$3*M9"
            .Range("N10").Formula = "=$J$3*M10"
            .Range("N11").Formula = "=$J$3*M11"
            .Range("N12").Formula = "=$J$3*M12"
            .Range("N13").Formula = "=$J$3*M13"
        End If
        
        ' CORRECTED: P12 uses O12 (not O13)
        If .Range("P6").Formula = "" Then
            .Range("P6").Formula = "=N6*O6"
            .Range("P7").Formula = "=N7*O7"
            .Range("P8").Formula = "=N8*O8"
            .Range("P9").Formula = "=N9*O9"
            .Range("P10").Formula = "=N10*O10"
            .Range("P11").Formula = "=N11*O11"
            .Range("P12").Formula = "=N12*O12"
            .Range("P13").Formula = "=N13*O13"
        End If
        
        ' ===== SECTION 1 TOTALS (Row 14) =====
        If .Range("M14").Formula = "" Then .Range("M14").Formula = "=SUM(M6:M13)"
        If .Range("N14").Formula = "" Then .Range("N14").Formula = "=SUM(N6:N13)"
        If .Range("O14").Formula = "" Then .Range("O14").Formula = "=IFERROR(P14/N14,""$0"")"
        If .Range("P14").Formula = "" Then .Range("P14").Formula = "=SUM(P6:P13)"
        
        ' ===== SECTION 2: ADDITIONAL ITEMS (Rows 16-18) =====
        ' Row 15 is header, Rows 16-18 are data, Row 19 is total
        If .Range("N16").Formula = "" Then
            .Range("N16").Formula = "=$J$3*M16"
            .Range("N17").Formula = "=$J$3*M17"
            .Range("N18").Formula = "=$J$3*M18"
        End If
        
        If .Range("P16").Formula = "" Then
            .Range("P16").Formula = "=N16*O16"
            .Range("P17").Formula = "=N17*O17"
            .Range("P18").Formula = "=N18*O18"
        End If
        
        ' ===== SECTION 2 TOTALS (Row 19) =====
        ' CORRECTED: All formulas check correct cell (M19, N19, O19, P19)
        If .Range("M19").Formula = "" Then .Range("M19").Formula = "=SUM(M16:M18)"
        If .Range("N19").Formula = "" Then .Range("N19").Formula = "=SUM(N16:N18)"
        If .Range("O19").Formula = "" Then .Range("O19").Formula = "=IFERROR(P19/N19,""$0"")"
        If .Range("P19").Formula = "" Then .Range("P19").Formula = "=SUM(P16:P18)"
        
        ' ===== SECTION 3: EXPENSES (Rows 21-26) =====
        ' Row 20 is header, Rows 21-25 are data, Row 26 is total
        If .Range("P21").Formula = "" Then
            .Range("P21").Formula = "=M21*N21*O21"
            .Range("P22").Formula = "=M22*N22*O22"
            .Range("P23").Formula = "=M23*N23*O23"
            .Range("P24").Formula = "=M24*N24*O24"
            .Range("P25").Formula = "=M25*N25*O25"
            ' CORRECTED: P26 uses P21:P25 (not P21:P26 which would be circular)
            .Range("P26").Formula = "=SUM(P21:P25)"
        End If
        
        ' ===== SECTION 4: ADDITIONAL EXPENSES (Rows 28-33) =====
        ' Row 27 is header, Rows 28-32 are data, Row 33 is total
        If .Range("P28").Formula = "" Then
            .Range("P28").Formula = "=M28*N28*O28"
            .Range("P29").Formula = "=M29*N29*O29"
            .Range("P30").Formula = "=M30*N30*O30"
            .Range("P31").Formula = "=M31*N31*O31"
            .Range("P32").Formula = "=M32*N32*O32"
            ' CORRECTED: P33 uses P28:P32 (not P27:P31)
            .Range("P33").Formula = "=SUM(P28:P32)"
        End If
    End With
    
    Application.EnableEvents = True
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
End Sub

Sub RestoreColumnDFormulas(ws As Worksheet)
    Dim i As Long
    Dim formulas() As Variant
    
    Application.EnableEvents = False
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    ReDim formulas(1 To 483, 1 To 1)
    
    For i = 1 To 483
        formulas(i, 1) = "=IF(OR(E" & (i + 5) & "="""",ISBLANK(E" & (i + 5) & ")),"""",IF($C$4=""MTS"",XLOOKUP(E" & (i + 5) & _
                        ",tblEquipment[Scope of Work],tblEquipment[MTS],0,0,1)," & _
                        "IF($C$4=""ATS"",XLOOKUP(E" & (i + 5) & _
                        ",tblEquipment[Scope of Work],tblEquipment[ATS],0,0,1),""Job Type?"")))"
    Next i
    
    ws.Range("D6:D488").Formula = formulas
    
    Application.EnableEvents = True
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
End Sub

Sub RestoreColumnIFormulas(ws As Worksheet)
    Dim i As Long
    Dim formulas() As Variant
    
    Application.EnableEvents = False
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    ReDim formulas(1 To 483, 1 To 1)
    
    For i = 1 To 483
        formulas(i, 1) = "=IF(OR(C" & (i + 5) & "="""",ISBLANK(C" & (i + 5) & ")),"""",IF($C$4=""MTS"",XLOOKUP(E" & (i + 5) & _
                        ",tblEquipment[Scope of Work],tblEquipment[MTS23],0,0,1)," & _
                        "IF($C$4=""ATS"",XLOOKUP(E" & (i + 5) & _
                        ",tblEquipment[Scope of Work],tblEquipment[ATS25],0,0,1),""Job Type?"")))"
    Next i
    
    ws.Range("I6:I488").Formula = formulas
    
    Application.EnableEvents = True
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
End Sub

Sub RestoreColumnJFormulas(ws As Worksheet)
    Dim i As Long
    Dim formulas() As Variant
    
    Application.EnableEvents = False
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    ReDim formulas(1 To 483, 1 To 1)
    
    For i = 1 To 483
        formulas(i, 1) = "=IF(OR(C" & (i + 5) & "="""",ISBLANK(C" & (i + 5) & ")),"""",IFERROR(C" & (i + 5) & "*I" & (i + 5) & ",""""))"
    Next i
    
    ws.Range("J6:J488").Formula = formulas
    
    Application.EnableEvents = True
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
End Sub


