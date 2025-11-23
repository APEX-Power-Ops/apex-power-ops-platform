VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "clsscopesheet"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit

Public WithEvents ScopeWorksheet As Worksheet
Attribute ScopeWorksheet.VB_VarHelpID = -1

Public Property Let SheetName(value As String)
    On Error Resume Next
    Set ScopeWorksheet = Worksheets(value)
    On Error GoTo 0
End Property

Public Property Set SheetObject(ws As Worksheet)
    Set ScopeWorksheet = ws
End Property

Private Sub ScopeWorksheet_Change(ByVal Target As Range)
    Dim formulaRanges As Range
    Dim schedulingRange As Range
    Dim cell As Range
    
    Application.EnableEvents = False
    
    ' ===== FORMULA RESTORATION RANGES =====
    Set formulaRanges = Union( _
        ScopeWorksheet.Range("D6:D488"), _
        ScopeWorksheet.Range("I6:I488"), _
        ScopeWorksheet.Range("J6:J488"), _
        ScopeWorksheet.Range("N6:N13"), _
        ScopeWorksheet.Range("N16:N18"), _
        ScopeWorksheet.Range("J3"), _
        ScopeWorksheet.Range("O3:P4"), _
        ScopeWorksheet.Range("M14:P14"), _
        ScopeWorksheet.Range("P6:P13"), _
        ScopeWorksheet.Range("M19:P19"), _
        ScopeWorksheet.Range("P16:P18"), _
        ScopeWorksheet.Range("P21:P26"), _
        ScopeWorksheet.Range("P28:P33") _
    )
    
    If Not Intersect(Target, formulaRanges) Is Nothing Then
        For Each cell In Intersect(Target, formulaRanges)
            RestoreSingleFormula cell
        Next cell
    End If
    
    ' ===== SCHEDULING CALCULATOR =====
    Set schedulingRange = ScopeWorksheet.Range("S3:U6")
    
    If Not Intersect(Target, schedulingRange) Is Nothing Then
        For Each cell In Intersect(Target, schedulingRange)
            Call CalculateSchedulingVariable(cell)
        Next cell
    End If
    
    Application.EnableEvents = True
End Sub

Private Sub RestoreSingleFormula(cell As Range)
    Dim row As Long
    row = cell.row
    
    Static notificationShown As Boolean
    If Not notificationShown Then
        Application.StatusBar = "Formula protection active"
        notificationShown = True
    End If
    
    Select Case cell.Address(False, False)
        ' ===== EQUIPMENT LOOKUP COLUMNS (D, I, J) =====
        Case "D" & row
            If row >= 6 And row <= 488 Then
                cell.Formula = "=IF(OR(E" & row & "="""",ISBLANK(E" & row & ")),"""",IF($C$4=""MTS"",XLOOKUP(E" & row & _
                              ",tblEquipment[Scope of Work],tblEquipment[MTS],0,0,1)," & _
                              "IF($C$4=""ATS"",XLOOKUP(E" & row & _
                              ",tblEquipment[Scope of Work],tblEquipment[ATS],0,0,1),""Job Type?"")))"
            End If
            
        Case "I" & row
            If row >= 6 And row <= 488 Then
                cell.Formula = "=IF(OR(C" & row & "="""",ISBLANK(C" & row & ")),"""",IF($C$4=""MTS"",XLOOKUP(E" & row & _
                              ",tblEquipment[Scope of Work],tblEquipment[MTS23],0,0,1)," & _
                              "IF($C$4=""ATS"",XLOOKUP(E" & row & _
                              ",tblEquipment[Scope of Work],tblEquipment[ATS25],0,0,1),""Job Type?"")))"
            End If
            
        Case "J" & row
            If row >= 6 And row <= 488 Then
                cell.Formula = "=IF(OR(C" & row & "="""",ISBLANK(C" & row & ")),"""",IFERROR(C" & row & "*I" & row & ",""""))"
            End If
            
        ' ===== GRAND TOTALS (Row 3-4) =====
        Case "J3": cell.Formula = "=SUMIF(J6:J488,""<>"",J6:J488)"
        Case "O3": cell.Formula = "=""0%"""
        Case "O4": cell.Formula = "=IFERROR((P4-P3)/P3,""0%"")"
        ' CORRECTED: P3 references P19 (not P18), P26 (not P25), P33 (not P32)
        Case "P3": cell.Formula = "=SUM(P14,P19,P26,P33)"
        Case "P4": cell.Formula = "=P3*M4*N4"
        
        ' ===== SECTION 1: BILLABLE ADDERS (Rows 6-13, Total Row 14) =====
        Case "N" & row
            If row >= 6 And row <= 13 Then
                cell.Formula = "=$J$3*M" & row
            End If
            
        Case "P6": cell.Formula = "=N6*O6"
        Case "P7": cell.Formula = "=N7*O7"
        Case "P8": cell.Formula = "=N8*O8"
        Case "P9": cell.Formula = "=N9*O9"
        Case "P10": cell.Formula = "=N10*O10"
        Case "P11": cell.Formula = "=N11*O11"
        ' CORRECTED: P12 uses O12 (not O13)
        Case "P12": cell.Formula = "=N12*O12"
        Case "P13": cell.Formula = "=N13*O13"
        
        ' ===== SECTION 1 TOTALS (Row 14) =====
        Case "M14": cell.Formula = "=SUM(M6:M13)"
        Case "N14": cell.Formula = "=SUM(N6:N13)"
        Case "O14": cell.Formula = "=IFERROR(P14/N14,""$0"")"
        Case "P14": cell.Formula = "=SUM(P6:P13)"
        
        ' ===== SECTION 2: ADDITIONAL ITEMS (Rows 16-18, Total Row 19) =====
        ' Row 15 is header
        Case "N" & row
            If row >= 16 And row <= 18 Then
                cell.Formula = "=$J$3*M" & row
            End If
            
        Case "P16": cell.Formula = "=N16*O16"
        Case "P17": cell.Formula = "=N17*O17"
        Case "P18": cell.Formula = "=N18*O18"
        
        ' ===== SECTION 2 TOTALS (Row 19) =====
        Case "M19": cell.Formula = "=SUM(M16:M18)"
        Case "N19": cell.Formula = "=SUM(N16:N18)"
        Case "O19": cell.Formula = "=IFERROR(P19/N19,""$0"")"
        Case "P19": cell.Formula = "=SUM(P16:P18)"
        
        ' ===== SECTION 3: EXPENSES (Rows 21-25, Total Row 26) =====
        ' Row 20 is header
        Case "P21": cell.Formula = "=M21*N21*O21"
        Case "P22": cell.Formula = "=M22*N22*O22"
        Case "P23": cell.Formula = "=M23*N23*O23"
        Case "P24": cell.Formula = "=M24*N24*O24"
        Case "P25": cell.Formula = "=M25*N25*O25"
        ' CORRECTED: P26 uses P21:P25 (not P21:P26 which would be circular)
        Case "P26": cell.Formula = "=SUM(P21:P25)"
        
        ' ===== SECTION 4: ADDITIONAL EXPENSES (Rows 28-32, Total Row 33) =====
        ' Row 27 is header
        Case "P28": cell.Formula = "=M28*N28*O28"
        Case "P29": cell.Formula = "=M29*N29*O29"
        Case "P30": cell.Formula = "=M30*N30*O30"
        Case "P31": cell.Formula = "=M31*N31*O31"
        Case "P32": cell.Formula = "=M32*N32*O32"
        ' CORRECTED: P33 uses P28:P32 (not P27:P31)
        Case "P33": cell.Formula = "=SUM(P28:P32)"
    End Select
End Sub

Private Sub CalculateSchedulingVariable(changedCell As Range)
    Dim row As Long
    Dim totalHours As Variant
    Dim techs As Variant
    Dim hoursPerDay As Variant
    Dim days As Variant
    Dim sCell As Range, tCell As Range, uCell As Range, rCell As Range
    Dim emptyCount As Integer
    
    row = changedCell.row
    
    ' Only process rows 3-6
    If row < 3 Or row > 6 Then Exit Sub
    
    ' Get the cells for this row
    Set rCell = ScopeWorksheet.Cells(row, "R")
    Set sCell = ScopeWorksheet.Cells(row, "S")
    Set tCell = ScopeWorksheet.Cells(row, "T")
    Set uCell = ScopeWorksheet.Cells(row, "U")
    
    ' Get values
    totalHours = rCell.value
    techs = sCell.value
    hoursPerDay = tCell.value
    days = uCell.value
    
    ' Check if total hours is available
    If IsEmpty(totalHours) Or Not IsNumeric(totalHours) Or totalHours = 0 Then
        Exit Sub
    End If
    
    ' Count empty cells
    emptyCount = 0
    If IsEmpty(techs) Or Not IsNumeric(techs) Then emptyCount = emptyCount + 1
    If IsEmpty(hoursPerDay) Or Not IsNumeric(hoursPerDay) Then emptyCount = emptyCount + 1
    If IsEmpty(days) Or Not IsNumeric(days) Then emptyCount = emptyCount + 1
    
    ' Only calculate if exactly one cell is empty
    If emptyCount <> 1 Then Exit Sub
    
    ' Calculate the missing variable
    If IsEmpty(techs) Or Not IsNumeric(techs) Then
        ' Calculate Techs = Total Hours / (Hours/Day × Days)
        If IsNumeric(hoursPerDay) And IsNumeric(days) And hoursPerDay > 0 And days > 0 Then
            sCell.value = Round(totalHours / (hoursPerDay * days), 2)
            sCell.Font.Color = RGB(0, 0, 255)
        End If
        
    ElseIf IsEmpty(hoursPerDay) Or Not IsNumeric(hoursPerDay) Then
        ' Calculate Hours/Day = Total Hours / (Techs × Days)
        If IsNumeric(techs) And IsNumeric(days) And techs > 0 And days > 0 Then
            tCell.value = Round(totalHours / (techs * days), 2)
            tCell.Font.Color = RGB(0, 0, 255)
        End If
        
    ElseIf IsEmpty(days) Or Not IsNumeric(days) Then
        ' Calculate Days = Total Hours / (Techs × Hours/Day)
        If IsNumeric(techs) And IsNumeric(hoursPerDay) And techs > 0 And hoursPerDay > 0 Then
            uCell.value = Round(totalHours / (techs * hoursPerDay), 2)
            uCell.Font.Color = RGB(0, 0, 255)
        End If
    End If
End Sub


