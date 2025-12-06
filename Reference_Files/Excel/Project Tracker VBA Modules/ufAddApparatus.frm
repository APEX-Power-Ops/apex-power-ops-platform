VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} ufAddApparatus 
   Caption         =   "Add Apparatus"
   ClientHeight    =   3015
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   5760
   OleObjectBlob   =   "ufAddApparatus.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "ufAddApparatus"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private Sub UserForm_Initialize()
    ' Populate apparatus dropdown from Apparatus_List table
    Dim apparatusList As Range
    Dim cell As Range
    
    On Error Resume Next
    Set apparatusList = Range("Apparatus_List[Apparatus]")
    On Error GoTo 0
    
    ' Fallback to sheet if table not found
    If apparatusList Is Nothing Then
        Dim ws As Worksheet
        Set ws = ThisWorkbook.Worksheets("Apparatus_List_w_Hours")
        If Not ws Is Nothing Then
            Dim lastRow As Long
            lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).row
            Set apparatusList = ws.Range("A2:A" & lastRow)
        End If
    End If
    
    ' Populate ComboBox
    If Not apparatusList Is Nothing Then
        Me.cboApparatus.Clear
        For Each cell In apparatusList
            If Len(Trim(cell.Value)) > 0 Then
                Me.cboApparatus.AddItem cell.Value
            End If
        Next cell
    Else
        MsgBox "Could not find Apparatus_List!", vbExclamation
    End If
    
    ' Set defaults
    Me.txtQuantity.Value = "1"
    Me.cboApparatus.SetFocus
End Sub

Private Sub btnAdd_Click()
    Dim apparatus As String
    Dim qty As Long
    Dim ws As Worksheet
    Dim nextRow As Long
    Dim i As Long
    
    ' Validate
    apparatus = Trim(Me.cboApparatus.Value)
    If Len(apparatus) = 0 Then
        MsgBox "Please select an apparatus!", vbExclamation
        Me.cboApparatus.SetFocus
        Exit Sub
    End If
    
    If Not IsNumeric(Me.txtQuantity.Value) Or val(Me.txtQuantity.Value) < 1 Then
        MsgBox "Enter a valid quantity!", vbExclamation
        Me.txtQuantity.SetFocus
        Exit Sub
    End If
    qty = CLng(Me.txtQuantity.Value)
    
    ' Get Task_Entry sheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(Global_Constants.SHEET_TASK_ENTRY)
    If ws Is Nothing Then Set ws = ThisWorkbook.Worksheets("Task_Entry")
    On Error GoTo 0
    
    If ws Is Nothing Then
        MsgBox "Task_Entry sheet not found!", vbCritical
        Exit Sub
    End If
    
    ' Find first empty row using COUNTA (ignores validation/formatting)
    nextRow = Application.WorksheetFunction.CountA(ws.Columns(Global_Constants.TE_COL_APP)) + 1
    If nextRow < 2 Then nextRow = 2
    
    ' Insert apparatus
    Application.ScreenUpdating = False
    For i = 1 To qty
        ws.Cells(nextRow, Global_Constants.TE_COL_APP).Value = apparatus
        nextRow = nextRow + 1
    Next i
    Application.ScreenUpdating = True
    
    ' Feedback
    Me.lblStatus.Caption = "Added " & qty & "x " & apparatus
    Me.lblStatus.ForeColor = RGB(0, 128, 0)
    
    ' Reset for next entry
    Me.txtQuantity.Value = "1"
    Me.cboApparatus.SetFocus
End Sub

Private Sub btnClose_Click()
    Unload Me
End Sub
Private Sub spnQuantity_SpinUp()
    Dim currentVal As Long
    currentVal = val(Me.txtQuantity.Value)
    Me.txtQuantity.Value = currentVal + 1
End Sub

Private Sub spnQuantity_SpinDown()
    Dim currentVal As Long
    currentVal = val(Me.txtQuantity.Value)
    If currentVal > 1 Then Me.txtQuantity.Value = currentVal - 1
End Sub

Private Sub txtQuantity_KeyPress(ByVal KeyAscii As MSForms.ReturnInteger)
    ' Only allow numbers
    If Not (KeyAscii >= 48 And KeyAscii <= 57) Then KeyAscii = 0
End Sub
