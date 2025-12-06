VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} ufPopulateAllTasks 
   Caption         =   "Get_All_Tasks"
   ClientHeight    =   3015
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   4560
   OleObjectBlob   =   "ufPopulateAllTasks.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "ufPopulateAllTasks"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
' Track last clicked item for shift+click range selection
Private lastClickedIndex As Long


Private Sub UserForm_Initialize()
    Dim ws As Worksheet
    lstSheets.Clear
    lastClickedIndex = -1  ' Initialize tracking
    
    For Each ws In ThisWorkbook.Worksheets
        ' Show the sheet's tab name (not code name)
        ' Exclude All_Tasks itself from selection
        If UCase$(ws.Name) <> UCase$("All_Tasks") Then
            lstSheets.AddItem ws.Name
        End If
    Next ws
End Sub

Private Sub lstSheets_MouseDown(ByVal Button As Integer, ByVal Shift As Integer, ByVal X As Single, ByVal Y As Single)
    ' Handle Shift+Click for range selection
    Dim clickedIndex As Long
    Dim i As Long, startIdx As Long, endIdx As Long
    
    ' Get the index of the clicked item
    clickedIndex = lstSheets.ListIndex
    
    If clickedIndex = -1 Then Exit Sub ' No item clicked
    
    ' Check if Shift key is held down (Shift = 1)
    If Shift = 1 And lastClickedIndex >= 0 And lastClickedIndex <> clickedIndex Then
        ' Shift+Click detected - select range
        startIdx = Application.Min(lastClickedIndex, clickedIndex)
        endIdx = Application.Max(lastClickedIndex, clickedIndex)
        
        ' Select all items in the range
        For i = startIdx To endIdx
            lstSheets.Selected(i) = True
        Next i
        
    Else
        ' Normal click - just update last clicked index
        lastClickedIndex = clickedIndex
    End If
End Sub

Private Sub lstSheets_Click()
    ' Update last clicked index for normal clicks
    If lstSheets.ListIndex >= 0 Then lastClickedIndex = lstSheets.ListIndex
End Sub

Private Sub cmdPopulate_Click()
    Dim sel() As String
    Dim i As Long, n As Long
    Dim appendMode As Boolean

    ' Count selections
    For i = 0 To lstSheets.ListCount - 1
        If lstSheets.Selected(i) Then n = n + 1
    Next i
    If n = 0 Then
        MsgBox "Please select at least one sheet.", vbExclamation, "No Selection"
        Exit Sub
    End If

    ' Show confirmation if many sheets selected
    If n > 5 Then
        If MsgBox("You've selected " & n & " sheets. This may take a few moments to process." & vbCrLf & _
                  "Continue?", vbQuestion + vbYesNo, "Confirm Processing") = vbNo Then
            Exit Sub
        End If
    End If
    
    ' Ask user about append vs replace mode
    Dim modeChoice As VbMsgBoxResult
    modeChoice = MsgBox("How would you like to handle existing data in All_Tasks?" & vbCrLf & vbCrLf & _
                       "Yes = ADD to existing data (append)" & vbCrLf & _
                       "No = REPLACE all existing data" & vbCrLf & _
                       "Cancel = Cancel operation", _
                       vbYesNoCancel + vbQuestion, "Data Mode Selection")
    
    Select Case modeChoice
        Case vbYes
            appendMode = True
        Case vbNo
            appendMode = False
        Case vbCancel
            Exit Sub
    End Select

    ReDim sel(1 To n)
    Dim k As Long: k = 1
    For i = 0 To lstSheets.ListCount - 1
        If lstSheets.Selected(i) Then
            sel(k) = CStr(lstSheets.List(i))
            k = k + 1
        End If
    Next i

    Me.Hide
    PopulateAllTasks_FromSheets_WithBillingSync sel, appendMode
    Unload Me
End Sub

Private Sub cmdCancel_Click()
    Unload Me
End Sub

' ================================================================================
' USERFORM COMPATIBILITY WRAPPER
' ================================================================================

Public Sub PopulateAllTasks_FromSheets_WithBillingSync(selectedSheets() As String, appendMode As Boolean)
    ' Wrapper for userform compatibility
    ' Billing sync happens automatically inside PopulateAllTasks_FromSheets
    
    Call PopulateAllTasks_FromSheets(selectedSheets, appendMode)
End Sub



