VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} ufSelectSheets 
   Caption         =   "Select Sheets to Print"
   ClientHeight    =   3015
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   4560
   OleObjectBlob   =   "ufSelectSheets.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "ufSelectSheets"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False


Private Sub UserForm_Initialize()
    Debug.Print "UserForm_Initialize START"

    With lstSheets
        .Clear
        .ColumnCount = 2
        .ColumnWidths = "150 pt;0 pt"
        .MultiSelect = fmMultiSelectMulti
    End With

    Dim ws As Worksheet
    Dim foundCount As Integer
    foundCount = 0

    For Each ws In ThisWorkbook.Worksheets
        If Left(ws.codeName, 5) = "Scope" Then
            lstSheets.AddItem ws.Name
            lstSheets.List(lstSheets.ListCount - 1, 1) = ws.codeName
            Debug.Print "Added to list: " & ws.Name & " (" & ws.codeName & ")"
            foundCount = foundCount + 1
        End If
    Next ws

    Debug.Print "UserForm_Initialize END - " & foundCount & " sheets loaded"
End Sub

Private Sub cmdOK_Click()
    Debug.Print "cmdOK_Click START"

    Set SheetPicker_LastSelection = New Collection

    Dim i As Integer
    For i = 0 To lstSheets.ListCount - 1
        If lstSheets.Selected(i) Then
            SheetPicker_LastSelection.Add lstSheets.List(i, 1)
            Debug.Print "Selected: " & lstSheets.List(i, 0) & " -> " & lstSheets.List(i, 1)
        End If
    Next i

    Debug.Print "Selection transfer complete - Count: " & SheetPicker_LastSelection.count

    If SheetPicker_LastSelection.count > 0 Then
        Debug.Print "cmdOK_Click - Validation passed, hiding form"
        Me.Hide
    Else
        MsgBox "Please select at least one sheet.", vbExclamation
    End If

    Debug.Print "cmdOK_Click END"
End Sub

Private Sub cmdCancel_Click()
    Set SheetPicker_LastSelection = Nothing
    Me.Hide
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    Debug.Print "UserForm_QueryClose - CloseMode: " & CloseMode
    If CloseMode = vbFormControlMenu Then
        Set SheetPicker_LastSelection = Nothing
    End If
End Sub
