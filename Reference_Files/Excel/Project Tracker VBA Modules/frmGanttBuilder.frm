VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmGanttBuilder 
   Caption         =   "UserForm1"
   ClientHeight    =   2625
   ClientLeft      =   -120
   ClientTop       =   -540
   ClientWidth     =   3900
   OleObjectBlob   =   "frmGanttBuilder.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "frmGanttBuilder"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

' ===== INITIALISE =====
Private Sub UserForm_Initialize()
    Dim ws As Worksheet
    Dim nm As String

    lstSheets.Clear

    ' List ALL visible worksheets except the template and prior Gantt outputs
    For Each ws In ThisWorkbook.Worksheets
        If ws.Visible = xlSheetVisible Then
            nm = ws.Name

            If modGanttBuilder.GB_Normalize(nm) <> _
               modGanttBuilder.GB_Normalize(modGanttBuilder.GB_TEMPLATE_NAME) _
               And _
               Left$(modGanttBuilder.GB_Normalize(nm), _
                     Len(modGanttBuilder.GB_Normalize(modGanttBuilder.GB_OUTPUT_BASE))) _
                        <> modGanttBuilder.GB_Normalize(modGanttBuilder.GB_OUTPUT_BASE) Then
                lstSheets.AddItem nm
            End If
        End If
    Next ws

    If lstSheets.ListCount = 0 Then
        Me.Caption = "Gantt Builder – No sheets detected. Click Build to create a blank Gantt."
    Else
        Me.Caption = "Gantt Builder"
    End If
End Sub


' ===== SELECT/DESELECT ALL =====
Private Sub chkAll_Click()
    Dim i As Long
    For i = 0 To lstSheets.ListCount - 1
        lstSheets.Selected(i) = chkAll.Value
    Next i
End Sub


' ===== BUILD BUTTON =====
Private Sub btnBuild_Click()
    Dim picks As New Collection
    Dim i As Long, nm As String

    ' collect selected sheet names
    For i = 0 To lstSheets.ListCount - 1
        If lstSheets.Selected(i) Then
            nm = CStr(lstSheets.List(i))
            picks.Add nm
        End If
    Next i

    ' If none selected, pass Empty so the builder will use all valid sheets
    If picks.Count = 0 Then
        modGanttBuilder.BuildGanttFromSheets Empty
    Else
        modGanttBuilder.BuildGanttFromSheets picks
    End If

    Unload Me
End Sub


