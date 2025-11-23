Attribute VB_Name = "SumIfsbySheet"
'============================================================
' SumIfsbySheet - With Sheet Multiplier (M4), Row Highlighting, and Smart Sorting
' Silent operation (error messages only)
' Sorts tblEquipment by Column H (Total Hours) DESCENDING - Most used equipment on top!
'============================================================
Public Sub UpdateSumsBySheet()
    Dim equipRefWS As Worksheet
    Dim ws As Worksheet
    Dim criteriaRange As Range
    Dim criteriaCell As Range
    Dim criteriaValue As String
    Dim i As Long
    Dim lastRow As Long
    Dim sumTotal As Double
    Dim j As Long
    Dim tbl As ListObject
    Dim sheetMultiplier As Double
    Dim rowQty As Double
    Dim highlightRange As Range
    
    On Error GoTo ErrorHandler
    
    ' Use CodeName
    Set equipRefWS = Equipment_Reference
    
    ' Get the table reference
    Set tbl = equipRefWS.ListObjects("tblEquipment")
    
    ' Clear existing sums in column H
    equipRefWS.Range("H3:H486").ClearContents
    
    ' Clear existing highlighting in B:F
    equipRefWS.Range("B3:F486").Interior.ColorIndex = xlNone
    
    ' Set the criteria range - use table's Scope of Work column
    Set criteriaRange = tbl.ListColumns("Scope of Work").DataBodyRange
    
    ' Loop through each criteria cell
    For Each criteriaCell In criteriaRange
        If Not IsEmpty(criteriaCell) Then
            criteriaValue = CStr(criteriaCell.value)
            sumTotal = 0
            
            ' Use CodeNames directly - break-proof!
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
                
                ' Get the sheet multiplier from M4
                sheetMultiplier = 1 ' Default to 1 if not numeric
                If IsNumeric(ws.Range("M4").value) Then
                    sheetMultiplier = CDbl(ws.Range("M4").value)
                End If
                
                ' Find last row
                lastRow = ws.Cells(ws.Rows.count, "E").End(xlUp).row
                
                If lastRow > 5 Then ' Assuming row 5 is headers
                    For j = 6 To lastRow
                        If Not IsEmpty(ws.Cells(j, "E")) Then
                            If StrComp(CStr(ws.Cells(j, "E").value), criteriaValue, vbTextCompare) = 0 Then
                                If IsNumeric(ws.Cells(j, "C").value) Then
                                    ' Get the row quantity
                                    rowQty = CDbl(ws.Cells(j, "C").value)
                                    ' Multiply by sheet multiplier and add to sum
                                    sumTotal = sumTotal + (rowQty * sheetMultiplier)
                                End If
                            End If
                        End If
                    Next j
                End If
            Next i
            
            ' Write sum to column H in same row as criteria
            equipRefWS.Cells(criteriaCell.row, "H").value = sumTotal
            
            ' Highlight the row B:F if sum is greater than zero
            If sumTotal > 0 Then
                Set highlightRange = equipRefWS.Range("B" & criteriaCell.row & ":F" & criteriaCell.row)
                With highlightRange.Interior
                    .Color = RGB(255, 242, 204) ' Light yellow/cream color
                    .Pattern = xlSolid
                End With
            End If
        End If
    Next criteriaCell
    
    ' Sort by Column H (Total Hours) DESCENDING - Highest usage on top!
    Call SortByTotalHours(equipRefWS, tbl)
    
    ' No success message - silent operation
    Exit Sub
    
ErrorHandler:
    MsgBox "Error: " & Err.Description, vbCritical
End Sub

Private Sub SortByTotalHours(equipRefWS As Worksheet, tbl As ListObject)
    '============================================================
    ' Sorts tblEquipment by Column H (Total Hours) DESCENDING
    ' Most-used equipment appears at the top
    ' Items with 0 hours sink to the bottom
    '============================================================
    On Error GoTo SortError
    
    Dim sortRange As Range
    
    ' Define the sort range - table plus column H (which is outside the table)
    ' We'll sort the entire data area including column H
    Set sortRange = equipRefWS.Range("B2:H486")  ' B2 includes header, H486 includes totals
    
    ' Clear any existing sort
    equipRefWS.Sort.SortFields.Clear
    
    ' Sort by Column H (Total Hours) - Descending (largest on top)
    equipRefWS.Sort.SortFields.Add2 _
        Key:=equipRefWS.Range("H3:H486"), _
        SortOn:=xlSortOnValues, _
        Order:=xlDescending, _
        DataOption:=xlSortNormal
    
    ' Apply the sort
    With equipRefWS.Sort
        .SetRange sortRange
        .Header = xlYes
        .MatchCase = False
        .Orientation = xlTopToBottom
        .SortMethod = xlPinYin
        .Apply
    End With
    
    Exit Sub
    
SortError:
    ' If sort fails, continue silently (don't break the main function)
    Exit Sub
End Sub
