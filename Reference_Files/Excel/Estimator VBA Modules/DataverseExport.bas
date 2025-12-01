Attribute VB_Name = "DataverseExport"
'============================================================
' DATAVERSE EXPORT MODULE
' Purpose: Export Estimator workbook data to JSON format
'          for import into Dataverse via Web App or Power Automate
'
' Output: JSON file + Clipboard copy
' Usage: Run ExportToDataverse from any Estimator workbook
'        that has a Dataverse_Import sheet filled in
'
' Created: November 27, 2025
' Updated: November 30, 2025 - Added clipboard copy option
' Version: 1.1
'============================================================

Option Explicit

' Windows API for clipboard
#If VBA7 Then
    Private Declare PtrSafe Function OpenClipboard Lib "user32" (ByVal hwnd As LongPtr) As Long
    Private Declare PtrSafe Function EmptyClipboard Lib "user32" () As Long
    Private Declare PtrSafe Function CloseClipboard Lib "user32" () As Long
    Private Declare PtrSafe Function SetClipboardData Lib "user32" (ByVal wFormat As Long, ByVal hMem As LongPtr) As LongPtr
    Private Declare PtrSafe Function GlobalAlloc Lib "kernel32" (ByVal wFlags As Long, ByVal dwBytes As LongPtr) As LongPtr
    Private Declare PtrSafe Function GlobalLock Lib "kernel32" (ByVal hMem As LongPtr) As LongPtr
    Private Declare PtrSafe Function GlobalUnlock Lib "kernel32" (ByVal hMem As LongPtr) As Long
    Private Declare PtrSafe Sub CopyMemory Lib "kernel32" Alias "RtlMoveMemory" (ByVal Destination As LongPtr, ByVal Source As String, ByVal Length As LongPtr)
#Else
    Private Declare Function OpenClipboard Lib "user32" (ByVal hwnd As Long) As Long
    Private Declare Function EmptyClipboard Lib "user32" () As Long
    Private Declare Function CloseClipboard Lib "user32" () As Long
    Private Declare Function SetClipboardData Lib "user32" (ByVal wFormat As Long, ByVal hMem As Long) As Long
    Private Declare Function GlobalAlloc Lib "kernel32" (ByVal wFlags As Long, ByVal dwBytes As Long) As Long
    Private Declare Function GlobalLock Lib "kernel32" (ByVal hMem As Long) As Long
    Private Declare Function GlobalUnlock Lib "kernel32" (ByVal hMem As Long) As Long
    Private Declare Sub CopyMemory Lib "kernel32" Alias "RtlMoveMemory" (ByVal Destination As Long, ByVal Source As String, ByVal Length As Long)
#End If

Private Const CF_TEXT = 1
Private Const GMEM_MOVEABLE = &H2

' Constants for cell locations on scope sheets
Private Const TOTAL_HOURS_CELL As String = "J3"
Private Const MULTIPLIER_CELL As String = "M4"
Private Const GRAND_TOTAL_CELL As String = "P3"
Private Const JOB_TYPE_CELL As String = "C4"
Private Const APPARATUS_START_ROW As Long = 6
Private Const APPARATUS_END_ROW As Long = 488

' Financial section rows
Private Const ONSITE_TOTAL_ROW As Long = 14
Private Const OFFSITE_TOTAL_ROW As Long = 19
Private Const TRAVEL_TOTAL_ROW As Long = 26
Private Const OUTSIDE_SERVICES_TOTAL_ROW As Long = 33

Public Sub ExportToDataverse()
    '============================================================
    ' Main entry point - builds JSON, copies to clipboard, optionally saves file
    '============================================================

    Dim metaSheet As Worksheet
    Dim json As String
    Dim response As VbMsgBoxResult

    On Error GoTo ErrorHandler

    ' Check for Dataverse_Import sheet
    On Error Resume Next
    Set metaSheet = ThisWorkbook.Worksheets("Dataverse_Import")
    On Error GoTo ErrorHandler

    If metaSheet Is Nothing Then
        MsgBox "ERROR: 'Dataverse_Import' sheet not found!" & vbCrLf & vbCrLf & _
               "Please create this sheet with project metadata before exporting.", _
               vbCritical, "Missing Metadata Sheet"
        Exit Sub
    End If

    ' Validate required fields
    If Not ValidateMetadata(metaSheet) Then Exit Sub

    ' Build JSON
    json = BuildExportJSON(metaSheet)

    ' Copy to clipboard first (always)
    CopyToClipboard json

    ' Ask user what they want to do
    response = MsgBox("JSON has been copied to clipboard!" & vbCrLf & vbCrLf & _
                      "You can now paste directly into the RESA Web App." & vbCrLf & vbCrLf & _
                      "Would you also like to save the JSON to a file?", _
                      vbYesNo + vbQuestion, "Export Complete")

    If response = vbYes Then
        SaveJSONToFile json, metaSheet
    End If

    ' Update status
    SetMetaValue metaSheet, "Import Status:", "Exported - Ready for Import"
    SetMetaValue metaSheet, "Last Import Date:", Format(Now, "yyyy-mm-dd hh:mm:ss")

    Exit Sub

ErrorHandler:
    MsgBox "Error: " & Err.Description, vbCritical, "Export Failed"
End Sub

Public Sub ExportToClipboardOnly()
    '============================================================
    ' Quick export - clipboard only, no file save dialog
    '============================================================

    Dim metaSheet As Worksheet
    Dim json As String

    On Error GoTo ErrorHandler

    Set metaSheet = ThisWorkbook.Worksheets("Dataverse_Import")
    If metaSheet Is Nothing Then
        MsgBox "Dataverse_Import sheet not found!", vbExclamation
        Exit Sub
    End If

    If Not ValidateMetadata(metaSheet) Then Exit Sub

    json = BuildExportJSON(metaSheet)
    CopyToClipboard json

    MsgBox "JSON copied to clipboard!" & vbCrLf & vbCrLf & _
           "Open the RESA Web App and paste into the import page.", _
           vbInformation, "Ready to Paste"

    SetMetaValue metaSheet, "Import Status:", "Exported to Clipboard"
    SetMetaValue metaSheet, "Last Import Date:", Format(Now, "yyyy-mm-dd hh:mm:ss")

    Exit Sub

ErrorHandler:
    MsgBox "Error: " & Err.Description, vbCritical, "Export Failed"
End Sub

Private Sub CopyToClipboard(text As String)
    '============================================================
    ' Copy text to Windows clipboard using API
    '============================================================

    Dim hGlobalMemory As LongPtr
    Dim lpGlobalMemory As LongPtr
    Dim hClipMemory As LongPtr

    ' Allocate global memory
    hGlobalMemory = GlobalAlloc(GMEM_MOVEABLE, Len(text) + 1)
    lpGlobalMemory = GlobalLock(hGlobalMemory)

    ' Copy string to global memory
    CopyMemory lpGlobalMemory, text, Len(text) + 1
    GlobalUnlock hGlobalMemory

    ' Set clipboard data
    OpenClipboard 0&
    EmptyClipboard
    SetClipboardData CF_TEXT, hGlobalMemory
    CloseClipboard
End Sub

Private Sub SaveJSONToFile(json As String, metaSheet As Worksheet)
    '============================================================
    ' Save JSON to file with Save As dialog
    '============================================================

    Dim outputPath As String
    Dim fileNum As Integer
    Dim defaultFilename As String
    Dim initialPath As String

    defaultFilename = SanitizeFilename(GetMetaValue(metaSheet, "Job #")) & "_" & _
                      "DATAVERSE_IMPORT_" & Format(Now, "yyyymmdd_hhmmss") & ".json"

    initialPath = Environ("USERPROFILE") & "\Documents\" & defaultFilename

    outputPath = Application.GetSaveAsFilename( _
        InitialFileName:=initialPath, _
        FileFilter:="JSON Files (*.json), *.json", _
        Title:="Save Dataverse Export")

    If outputPath = "False" Or outputPath = "" Then Exit Sub

    fileNum = FreeFile
    Open outputPath For Output As #fileNum
    Print #fileNum, json
    Close #fileNum

    MsgBox "File saved to:" & vbCrLf & outputPath, vbInformation, "File Saved"
End Sub

Private Function ValidateMetadata(metaSheet As Worksheet) As Boolean
    Dim missingFields As String
    missingFields = ""

    If Len(Trim(GetMetaValue(metaSheet, "Client:"))) = 0 Then
        missingFields = missingFields & "- Client" & vbCrLf
    End If

    If Len(Trim(GetMetaValue(metaSheet, "Project:"))) = 0 Then
        missingFields = missingFields & "- Project" & vbCrLf
    End If

    If Len(Trim(GetMetaValue(metaSheet, "Job #:"))) = 0 Then
        missingFields = missingFields & "- Job #" & vbCrLf
    End If

    If Len(missingFields) > 0 Then
        MsgBox "Please fill in required fields on Dataverse_Import sheet:" & vbCrLf & vbCrLf & _
               missingFields, vbExclamation, "Missing Required Fields"
        ValidateMetadata = False
    Else
        ValidateMetadata = True
    End If
End Function

Private Function GetMetaValue(metaSheet As Worksheet, labelText As String) As String
    Dim cell As Range
    Set cell = metaSheet.Range("A:A").Find(What:=labelText, LookIn:=xlValues, LookAt:=xlWhole)

    If Not cell Is Nothing Then
        GetMetaValue = Trim(CStr(cell.Offset(0, 1).Value))
    Else
        GetMetaValue = ""
    End If
End Function

Private Sub SetMetaValue(metaSheet As Worksheet, labelText As String, newValue As String)
    Dim cell As Range
    Set cell = metaSheet.Range("A:A").Find(What:=labelText, LookIn:=xlValues, LookAt:=xlWhole)

    If Not cell Is Nothing Then
        cell.Offset(0, 1).Value = newValue
    End If
End Sub

Private Function BuildExportJSON(metaSheet As Worksheet) As String
    Dim json As String
    Dim scopesJson As String
    Dim i As Integer
    Dim scopeCount As Integer

    json = "{" & vbCrLf

    ' Metadata
    json = json & "  ""metadata"": {" & vbCrLf
    json = json & "    ""exportDate"": """ & Format(Now, "yyyy-mm-ddThh:mm:ss") & """," & vbCrLf
    json = json & "    ""workbookName"": """ & EscapeJSON(ThisWorkbook.Name) & """," & vbCrLf
    json = json & "    ""version"": ""1.1""" & vbCrLf
    json = json & "  }," & vbCrLf

    ' Client
    json = json & "  ""client"": {" & vbCrLf
    json = json & "    ""name"": """ & EscapeJSON(GetMetaValue(metaSheet, "Client:")) & """" & vbCrLf
    json = json & "  }," & vbCrLf

    ' Site
    json = json & "  ""site"": {" & vbCrLf
    json = json & "    ""name"": """ & EscapeJSON(GetMetaValue(metaSheet, "Project:")) & """," & vbCrLf
    json = json & "    ""address"": """ & EscapeJSON(GetMetaValue(metaSheet, "Site Address:")) & """," & vbCrLf
    json = json & "    ""city"": """ & EscapeJSON(GetMetaValue(metaSheet, "Site City:")) & """," & vbCrLf
    json = json & "    ""state"": """ & EscapeJSON(GetMetaValue(metaSheet, "Site State:")) & """," & vbCrLf
    json = json & "    ""zipCode"": """ & EscapeJSON(GetMetaValue(metaSheet, "Site Zip Code:")) & """," & vbCrLf
    json = json & "    ""contactName"": """ & EscapeJSON(GetMetaValue(metaSheet, "Site Contact:")) & """," & vbCrLf
    json = json & "    ""contactPhone"": """ & EscapeJSON(GetMetaValue(metaSheet, "Site Contact Phone #:")) & """," & vbCrLf
    json = json & "    ""contactEmail"": """ & EscapeJSON(GetMetaValue(metaSheet, "Contact Email Address:")) & """" & vbCrLf
    json = json & "  }," & vbCrLf

    ' Project
    json = json & "  ""project"": {" & vbCrLf
    json = json & "    ""name"": """ & EscapeJSON(GetMetaValue(metaSheet, "Project:")) & """," & vbCrLf
    json = json & "    ""projectNumber"": """ & EscapeJSON(GetMetaValue(metaSheet, "Job #:")) & """," & vbCrLf
    json = json & "    ""projectLead"": """ & EscapeJSON(GetMetaValue(metaSheet, "Project Lead:")) & """," & vbCrLf
    json = json & "    ""businessUnit"": """ & EscapeJSON(GetMetaValue(metaSheet, "Business Unit:")) & """," & vbCrLf
    json = json & "    ""startDate"": """ & FormatDateISO(GetMetaValue(metaSheet, "Project Start Date:")) & """," & vbCrLf
    json = json & "    ""quoteDate"": """ & FormatDateISO(GetMetaValue(metaSheet, "Quote Date:")) & """," & vbCrLf
    json = json & "    ""quoteRevision"": """ & EscapeJSON(GetMetaValue(metaSheet, "Quote Revision:")) & """" & vbCrLf
    json = json & "  }," & vbCrLf

    ' Scopes
    json = json & "  ""scopes"": [" & vbCrLf

    scopeCount = 0
    scopesJson = ""

    For i = 1 To 20
        Dim scopeJson As String
        scopeJson = BuildScopeJSON(i)
        If Len(scopeJson) > 0 Then
            If scopeCount > 0 Then scopesJson = scopesJson & "," & vbCrLf
            scopesJson = scopesJson & scopeJson
            scopeCount = scopeCount + 1
        End If
    Next i

    json = json & scopesJson & vbCrLf
    json = json & "  ]," & vbCrLf

    ' Summary
    json = json & "  ""summary"": {" & vbCrLf
    json = json & "    ""totalScopes"": " & scopeCount & "," & vbCrLf
    json = json & "    ""grandTotal"": " & GetGrandTotal() & vbCrLf
    json = json & "  }" & vbCrLf

    json = json & "}"

    BuildExportJSON = json
End Function

Private Function BuildScopeJSON(scopeIndex As Integer) As String
    Dim ws As Worksheet
    Dim totalHours As Variant
    Dim json As String

    On Error Resume Next
    Select Case scopeIndex
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
    On Error GoTo 0

    If ws Is Nothing Then
        BuildScopeJSON = ""
        Exit Function
    End If

    totalHours = ws.Range(TOTAL_HOURS_CELL).Value
    If Not IsNumeric(totalHours) Or totalHours = 0 Then
        BuildScopeJSON = ""
        Exit Function
    End If

    json = "    {" & vbCrLf
    json = json & "      ""scopeIndex"": " & scopeIndex & "," & vbCrLf
    json = json & "      ""name"": """ & EscapeJSON(ws.Name) & """," & vbCrLf
    json = json & "      ""scopeType"": """ & EscapeJSON(CStr(ws.Range(JOB_TYPE_CELL).Value)) & """," & vbCrLf
    json = json & "      ""totalHours"": " & FormatNumber(totalHours) & "," & vbCrLf
    json = json & "      ""multiplier"": " & FormatNumber(ws.Range(MULTIPLIER_CELL).Value) & "," & vbCrLf
    json = json & "      ""quotedAmount"": " & FormatNumber(ws.Range(GRAND_TOTAL_CELL).Value) & "," & vbCrLf

    json = json & "      ""financials"": {" & vbCrLf
    json = json & "        ""onsiteLaborTotal"": " & FormatNumber(ws.Range("P" & ONSITE_TOTAL_ROW).Value) & "," & vbCrLf
    json = json & "        ""offsiteLaborTotal"": " & FormatNumber(ws.Range("P" & OFFSITE_TOTAL_ROW).Value) & "," & vbCrLf
    json = json & "        ""travelTotal"": " & FormatNumber(ws.Range("P" & TRAVEL_TOTAL_ROW).Value) & "," & vbCrLf
    json = json & "        ""outsideServicesTotal"": " & FormatNumber(ws.Range("P" & OUTSIDE_SERVICES_TOTAL_ROW).Value) & vbCrLf
    json = json & "      }," & vbCrLf

    json = json & "      ""apparatus"": [" & vbCrLf
    json = json & BuildApparatusJSON(ws) & vbCrLf
    json = json & "      ]" & vbCrLf
    json = json & "    }"

    BuildScopeJSON = json
End Function

Private Function BuildApparatusJSON(ws As Worksheet) As String
    Dim i As Long
    Dim qty As Variant
    Dim equipType As String
    Dim hours As Variant
    Dim totalHrs As Variant
    Dim json As String
    Dim apparatusCount As Long
    Dim currentSection As String

    json = ""
    apparatusCount = 0
    currentSection = "General"

    For i = APPARATUS_START_ROW To APPARATUS_END_ROW
        equipType = Trim(CStr(ws.Range("E" & i).Value))

        ' Check for section headers (bold text without quantity)
        If Len(equipType) > 0 And ws.Range("E" & i).Font.Bold Then
            If Not IsNumeric(ws.Range("C" & i).Value) Or ws.Range("C" & i).Value = 0 Then
                currentSection = equipType
            End If
        End If

        qty = ws.Range("C" & i).Value
        hours = ws.Range("I" & i).Value
        totalHrs = ws.Range("J" & i).Value

        If Len(equipType) > 0 And IsNumeric(qty) And qty > 0 Then
            If apparatusCount > 0 Then json = json & "," & vbCrLf

            json = json & "        {" & vbCrLf
            json = json & "          ""row"": " & i & "," & vbCrLf
            json = json & "          ""section"": """ & EscapeJSON(currentSection) & """," & vbCrLf
            json = json & "          ""quantity"": " & CInt(qty) & "," & vbCrLf
            json = json & "          ""equipmentType"": """ & EscapeJSON(equipType) & """," & vbCrLf
            json = json & "          ""hoursPerUnit"": " & FormatNumber(hours) & "," & vbCrLf
            json = json & "          ""totalHours"": " & FormatNumber(totalHrs) & vbCrLf
            json = json & "        }"

            apparatusCount = apparatusCount + 1
        End If
    Next i

    BuildApparatusJSON = json
End Function

Private Function GetGrandTotal() As String
    Dim ws As Worksheet
    Dim total As Variant

    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("Equipment Reference")
    If Not ws Is Nothing Then
        total = ws.Range("M3").Value
        If IsNumeric(total) Then
            GetGrandTotal = FormatNumber(total)
            Exit Function
        End If
    End If
    On Error GoTo 0

    GetGrandTotal = "0"
End Function

Private Function EscapeJSON(str As String) As String
    Dim result As String
    result = str
    result = Replace(result, "\", "\\")
    result = Replace(result, """", "\""")
    result = Replace(result, vbCr, "\r")
    result = Replace(result, vbLf, "\n")
    result = Replace(result, vbTab, "\t")
    EscapeJSON = result
End Function

Private Function FormatNumber(val As Variant) As String
    If IsEmpty(val) Or val = "" Then
        FormatNumber = "0"
    ElseIf IsNumeric(val) Then
        FormatNumber = Format(CDbl(val), "0.00")
    Else
        FormatNumber = "0"
    End If
End Function

Private Function FormatDateISO(val As String) As String
    On Error Resume Next
    If IsDate(val) Then
        FormatDateISO = Format(CDate(val), "yyyy-mm-dd")
    Else
        FormatDateISO = ""
    End If
    On Error GoTo 0
End Function

Private Function SanitizeFilename(str As String) As String
    Dim result As String
    Dim i As Long
    Dim c As String

    result = ""
    For i = 1 To Len(str)
        c = Mid(str, i, 1)
        If c Like "[A-Za-z0-9_-]" Then result = result & c
    Next i

    SanitizeFilename = result
End Function

Public Sub QuickValidate()
    Dim metaSheet As Worksheet
    Dim scopeCount As Integer
    Dim i As Integer
    Dim ws As Worksheet
    Dim totalHours As Variant

    On Error Resume Next
    Set metaSheet = ThisWorkbook.Worksheets("Dataverse_Import")
    On Error GoTo 0

    If metaSheet Is Nothing Then
        MsgBox "Dataverse_Import sheet not found!", vbExclamation
        Exit Sub
    End If

    scopeCount = 0
    For i = 1 To 20
        On Error Resume Next
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
        On Error GoTo 0

        If Not ws Is Nothing Then
            totalHours = ws.Range(TOTAL_HOURS_CELL).Value
            If IsNumeric(totalHours) And totalHours > 0 Then scopeCount = scopeCount + 1
        End If
    Next i

    Dim msg As String
    msg = "VALIDATION SUMMARY" & vbCrLf & vbCrLf
    msg = msg & "Client: " & GetMetaValue(metaSheet, "Client:") & vbCrLf
    msg = msg & "Project: " & GetMetaValue(metaSheet, "Project:") & vbCrLf
    msg = msg & "Job #: " & GetMetaValue(metaSheet, "Job #:") & vbCrLf
    msg = msg & "Active Scopes: " & scopeCount & vbCrLf
    msg = msg & "Grand Total: " & FormatCurrency(CDbl(GetGrandTotal()), 2)

    MsgBox msg, vbInformation, "Quick Validation"
End Sub
