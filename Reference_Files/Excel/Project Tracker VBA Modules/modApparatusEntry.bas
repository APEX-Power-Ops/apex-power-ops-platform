Attribute VB_Name = "modApparatusEntry"
' ============================================================================
' modApparatusEntry - Quick Apparatus Entry Module
' ============================================================================
' Purpose: Provides quick apparatus entry for Task_Entry sheet
' Version: 1.0
' Date: 2025-11-25
' ============================================================================
' USAGE:
'   Call ShowApparatusEntry to open the entry form
'   Or use QuickAddApparatus for direct insertion without form
' ============================================================================

Option Explicit

' ============================================================================
' MAIN ENTRY POINT - Call this from a button
' ============================================================================

Public Sub ShowApparatusEntry()
    ' Shows the Apparatus Entry UserForm
    ufAddApparatus.Show vbModeless
End Sub

' ============================================================================
' ALTERNATIVE: Quick Add without UserForm (for macro/button use)
' ============================================================================

Public Sub QuickAddApparatus()
    ' Quick input method using InputBox - no UserForm needed
    Dim apparatus As String
    Dim qtyStr As String
    Dim qty As Long
    Dim ws As Worksheet
    Dim nextRow As Long
    Dim i As Long
    
    ' Get Task_Entry sheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(Global_Constants.SHEET_TASK_ENTRY)
    If ws Is Nothing Then Set ws = ThisWorkbook.Worksheets("Task_Entry")
    On Error GoTo 0
    
    If ws Is Nothing Then
        MsgBox "Task_Entry sheet not found!", vbCritical
        Exit Sub
    End If
    
    ' Get apparatus selection
    apparatus = GetApparatusFromList()
    If Len(apparatus) = 0 Then Exit Sub
    
    ' Get quantity
    qtyStr = InputBox("How many '" & apparatus & "' to add?", "Quantity", "1")
    If Len(qtyStr) = 0 Then Exit Sub
    
    If Not IsNumeric(qtyStr) Or val(qtyStr) < 1 Then
        MsgBox "Invalid quantity!", vbExclamation
        Exit Sub
    End If
    qty = CLng(qtyStr)
    
    ' Find next empty row
    nextRow = ws.Cells(ws.Rows.Count, Global_Constants.TE_COL_APP).End(xlUp).row + 1
    If nextRow < Global_Constants.TE_FIRST_DATA_ROW Then
        nextRow = Global_Constants.TE_FIRST_DATA_ROW
    End If
    
    ' Insert apparatus
    Application.ScreenUpdating = False
    For i = 1 To qty
        ws.Cells(nextRow, Global_Constants.TE_COL_APP).Value = apparatus
        nextRow = nextRow + 1
    Next i
    Application.ScreenUpdating = True
    
    MsgBox "Added " & qty & "x " & apparatus, vbInformation
End Sub

Private Function GetApparatusFromList() As String
    ' Shows a list selection dialog for apparatus
    Dim apparatusList As Range
    Dim apparatusArray() As String
    Dim cell As Range
    Dim i As Long
    Dim selection As String
    
    On Error Resume Next
    Set apparatusList = Range("Apparatus_List[Apparatus]")
    On Error GoTo 0
    
    If apparatusList Is Nothing Then
        ' Fallback to sheet
        Dim ws As Worksheet
        Set ws = ThisWorkbook.Worksheets("Apparatus_List_w_Hours")
        If Not ws Is Nothing Then
            Dim lastRow As Long
            lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).row
            Set apparatusList = ws.Range("A2:A" & lastRow)
        End If
    End If
    
    If apparatusList Is Nothing Then
        GetApparatusFromList = InputBox("Enter apparatus name:", "Apparatus")
        Exit Function
    End If
    
    ' Build numbered list for selection
    ReDim apparatusArray(1 To apparatusList.Cells.Count)
    i = 1
    For Each cell In apparatusList
        If Len(Trim(cell.Value)) > 0 Then
            apparatusArray(i) = cell.Value
            i = i + 1
        End If
    Next cell
    
    ' Check if any items were found
    If i = 1 Then
        ' No apparatus found - fall back to manual input
        GetApparatusFromList = InputBox("Enter apparatus name:", "Apparatus")
        Exit Function
    End If
    
    ReDim Preserve apparatusArray(1 To i - 1)
    
    ' Use InputBox with hint (simple approach)
    Dim hint As String
    hint = "Enter apparatus name or number:" & vbCrLf & vbCrLf
    
    ' Show first 20 items as hint
    For i = 1 To WorksheetFunction.Min(20, UBound(apparatusArray))
        hint = hint & i & ". " & apparatusArray(i) & vbCrLf
    Next i
    If UBound(apparatusArray) > 20 Then
        hint = hint & "... (" & UBound(apparatusArray) - 20 & " more)"
    End If
    
    selection = InputBox(hint, "Select Apparatus")
    
    If Len(selection) = 0 Then
        GetApparatusFromList = ""
    ElseIf IsNumeric(selection) Then
        If CLng(selection) >= 1 And CLng(selection) <= UBound(apparatusArray) Then
            GetApparatusFromList = apparatusArray(CLng(selection))
        Else
            GetApparatusFromList = selection
        End If
    Else
        GetApparatusFromList = selection
    End If
End Function

' ============================================================================
' DIRECT INSERT FUNCTION - For use by other modules or buttons
' ============================================================================

Public Sub InsertApparatusRows(apparatus As String, qty As Long)
    ' Inserts apparatus directly into Task_Entry
    ' Can be called from other modules or worksheet buttons
    
    Dim ws As Worksheet
    Dim nextRow As Long
    Dim i As Long
    
    If Len(apparatus) = 0 Or qty < 1 Then Exit Sub
    
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(Global_Constants.SHEET_TASK_ENTRY)
    If ws Is Nothing Then Set ws = ThisWorkbook.Worksheets("Task_Entry")
    On Error GoTo 0
    
    If ws Is Nothing Then Exit Sub
    
    ' Find next empty row
    nextRow = ws.Cells(ws.Rows.Count, Global_Constants.TE_COL_APP).End(xlUp).row + 1
    If nextRow < Global_Constants.TE_FIRST_DATA_ROW Then
        nextRow = Global_Constants.TE_FIRST_DATA_ROW
    End If
    
    ' Insert
    Application.ScreenUpdating = False
    For i = 1 To qty
        ws.Cells(nextRow, Global_Constants.TE_COL_APP).Value = apparatus
        nextRow = nextRow + 1
    Next i
    Application.ScreenUpdating = True
End Sub

' ============================================================================
' HELPER: Get apparatus list as array (for ComboBox population)
' ============================================================================

Public Function GetApparatusArray() As Variant
    ' Returns array of apparatus names for populating controls
    Dim apparatusList As Range
    Dim result() As String
    Dim cell As Range
    Dim i As Long
    
    On Error Resume Next
    Set apparatusList = Range("Apparatus_List[Apparatus]")
    On Error GoTo 0
    
    If apparatusList Is Nothing Then
        Dim ws As Worksheet
        Set ws = ThisWorkbook.Worksheets("Apparatus_List_w_Hours")
        If Not ws Is Nothing Then
            Dim lastRow As Long
            lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).row
            Set apparatusList = ws.Range("A2:A" & lastRow)
        End If
    End If
    
    If apparatusList Is Nothing Then
        GetApparatusArray = Array()
        Exit Function
    End If
    
    ReDim result(1 To apparatusList.Cells.Count)
    i = 1
    For Each cell In apparatusList
        If Len(Trim(cell.Value)) > 0 Then
            result(i) = cell.Value
            i = i + 1
        End If
    Next cell
    
    If i > 1 Then
        ReDim Preserve result(1 To i - 1)
        GetApparatusArray = result
    Else
        GetApparatusArray = Array()
    End If
End Function
