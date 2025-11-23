Attribute VB_Name = "RefreshSheetNamesTotals"

Function GetSheetNames() As Variant
    Dim sheetList(1 To 20, 1 To 1) As String
    
    On Error GoTo ErrorHandler
    
    ' Use VBA code names to get actual sheet names
    sheetList(1, 1) = Scope1.Name
    sheetList(2, 1) = Scope2.Name
    sheetList(3, 1) = Scope3.Name
    sheetList(4, 1) = Scope4.Name
    sheetList(5, 1) = Scope5.Name
    sheetList(6, 1) = Scope6.Name
    sheetList(7, 1) = Scope7.Name
    sheetList(8, 1) = Scope8.Name
    sheetList(9, 1) = Scope9.Name
    sheetList(10, 1) = Scope10.Name
    sheetList(11, 1) = Scope11.Name
    sheetList(12, 1) = Scope12.Name
    sheetList(13, 1) = Scope13.Name
    sheetList(14, 1) = Scope14.Name
    sheetList(15, 1) = Scope15.Name
    sheetList(16, 1) = Scope16.Name
    sheetList(17, 1) = Scope17.Name
    sheetList(18, 1) = Scope18.Name
    sheetList(19, 1) = Scope19.Name
    sheetList(20, 1) = Scope20.Name
    
    GetSheetNames = sheetList
    Exit Function
    
ErrorHandler:
    MsgBox "Error in GetSheetNames: " & Err.Description, vbCritical
    GetSheetNames = sheetList
End Function

Sub RefreshSheetNameList()
    Dim SheetNames As Variant
    Dim i As Integer
    Dim OutputSheet As Worksheet
    Dim OutputStartCell As Range
    
    On Error GoTo ErrorHandler
    
    ' Use VBA code name for Equipment Reference
    Set OutputSheet = Equipment_Reference
    Set OutputStartCell = OutputSheet.Range("L4")
    
    ' Turn off calculation temporarily to prevent errors
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False
    
    ' Clear ONLY column L for 20 rows (L4:L23)
    OutputSheet.Range("L4:L23").ClearContents
    
    ' Get sheet names
    SheetNames = GetSheetNames()
    
    ' Output the 20 sheet names to column L
    For i = 1 To 20
        OutputStartCell.Cells(i, 1).value = SheetNames(i, 1)
    Next i
    
    ' Set M3 to SUM of M4:M23 (the TOTAL row)
    OutputSheet.Range("M3").Formula = "=SUM(M4:M23)"
    
    ' Restore/verify column M formulas for rows 4-23
    For i = 4 To 23
        OutputSheet.Range("M" & i).Formula = "=IFERROR(INDIRECT(""'"" & L" & i & " & ""'!P4""),"""")"
    Next i
    
    ' Re-enable calculation and events
    Application.Calculation = xlCalculationAutomatic
    Application.EnableEvents = True
    
    ' Force recalculation of the INDIRECT formulas
    OutputSheet.Range("M3:M23").Calculate
    
    ' No success message - silent operation
    Exit Sub
    
ErrorHandler:
    MsgBox "Error: " & Err.Description, vbCritical
    Application.Calculation = xlCalculationAutomatic
    Application.EnableEvents = True
End Sub
