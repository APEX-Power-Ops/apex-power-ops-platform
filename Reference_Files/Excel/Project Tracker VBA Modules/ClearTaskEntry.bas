Attribute VB_Name = "ClearTaskEntry"
Option Explicit

Public Sub Clear_TaskEntry_KeepFormulas()
    Dim ws As Worksheet
    Dim rng As Range

    Set ws = ThisWorkbook.Worksheets("Task_Entry")
    Set rng = ws.Range("A2:H205")

    Application.ScreenUpdating = False

    ' Clear only constants (numbers, text, logicals, errors) — formulas are preserved.
    On Error Resume Next ' handles case where there are no constants in the range
    rng.SpecialCells(xlCellTypeConstants).ClearContents
    On Error GoTo 0

    Application.ScreenUpdating = True
End Sub

