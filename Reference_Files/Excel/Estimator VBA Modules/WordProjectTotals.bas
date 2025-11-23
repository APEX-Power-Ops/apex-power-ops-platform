Attribute VB_Name = "WordProjectTotals"
'============================================================
' WordProjectTotals - With Dynamic Blue Fill
' Silent operation (error messages only)
'============================================================
Public Sub RefreshProjectTotals()
    Dim equipRefWS As Worksheet
    Dim printTemplateWS As Worksheet
    Dim sourceRow As Long
    Dim destRow As Long
    Dim lValue As Variant
    Dim mValue As Variant
    Dim totalRowsCopied As Long
    Dim userChoice As VbMsgBoxResult
    Dim updateSheetNames As Boolean
    Dim updateTotals As Boolean
    Dim lastFilledRow As Long
    Dim bottomBorderRow As Long
    
    ' Use CodeNames
    On Error GoTo ErrorHandler
    Set equipRefWS = Equipment_Reference
    Set printTemplateWS = Print_Template
    On Error GoTo 0
    
    ' Ask user what they want to update
    userChoice = MsgBox("What would you like to update?" & vbCrLf & vbCrLf & _
                       "YES = Update both Sheet Names and $ Totals" & vbCrLf & _
                       "NO = Update only $ Totals" & vbCrLf & _
                       "CANCEL = Cancel operation", _
                       vbYesNoCancel + vbQuestion, "Update Project Totals")
    
    ' Handle user choice
    Select Case userChoice
        Case vbYes
            updateSheetNames = True
            updateTotals = True
        Case vbNo
            updateSheetNames = False
            updateTotals = True
        Case vbCancel
            Exit Sub
    End Select
    
    ' Clear existing data based on choice
    If updateTotals Then
        printTemplateWS.Range("R13:S33").ClearContents
    End If
    
    If updateSheetNames Then
        printTemplateWS.Range("L14:Q33").ClearContents
    End If
    
    ' Clear all blue fill in the potential border area
    printTemplateWS.Range("K13:T35").Interior.ColorIndex = xlNone
    
    ' Handle row 3 special case
    If updateTotals Then
        mValue = equipRefWS.Cells(3, "M").value
        If IsNumeric(mValue) Or IsEmpty(mValue) Then
            printTemplateWS.Range("R13:S13").value = mValue
        End If
    End If
    
    destRow = 13
    totalRowsCopied = 0
    
    ' Loop through source range L4:M23
    For sourceRow = 4 To 23
        mValue = equipRefWS.Cells(sourceRow, "M").value
        
        If Not IsEmpty(mValue) Then
            If IsNumeric(mValue) Then
                If CDbl(mValue) <> 0 Then
                    destRow = destRow + 1
                    
                    ' Update sheet names if requested
                    If updateSheetNames Then
                        lValue = equipRefWS.Cells(sourceRow, "L").value
                        
                        If destRow >= 14 And destRow <= 23 Then
                            printTemplateWS.Range("L" & destRow & ":Q" & destRow).value = "  " & lValue
                        Else
                            printTemplateWS.Range("L" & destRow & ":Q" & destRow).value = lValue
                        End If
                    End If
                    
                    ' Update totals if requested
                    If updateTotals Then
                        printTemplateWS.Range("R" & destRow & ":S" & destRow).value = mValue
                    End If
                    
                    totalRowsCopied = totalRowsCopied + 1
                End If
            End If
        End If
    Next sourceRow
    
    ' Store the last filled row for border formatting
    lastFilledRow = destRow
    bottomBorderRow = lastFilledRow + 1
    
    ' Apply dynamic blue fill to create visual border effect
    ' Left column border
    With printTemplateWS.Range("K13:K" & bottomBorderRow).Interior
        .Color = RGB(0, 112, 192)
        .Pattern = xlSolid
    End With
    
    ' Right column border
    With printTemplateWS.Range("T13:T" & bottomBorderRow).Interior
        .Color = RGB(0, 112, 192)
        .Pattern = xlSolid
    End With
    
    ' Bottom row border
    With printTemplateWS.Range("K" & bottomBorderRow & ":T" & bottomBorderRow).Interior
        .Color = RGB(0, 112, 192)
        .Pattern = xlSolid
    End With
    
    ' No success message - silent operation
    Exit Sub
    
ErrorHandler:
    MsgBox "Error: " & Err.Description, vbCritical
End Sub

Private Function ListSheetNames() As String
    Dim ws As Worksheet
    Dim sheetList As String
    
    For Each ws In ThisWorkbook.Worksheets
        sheetList = sheetList & ws.Name & ", "
    Next ws
    
    If Len(sheetList) > 2 Then
        sheetList = Left(sheetList, Len(sheetList) - 2)
    End If
    
    ListSheetNames = sheetList
End Function
