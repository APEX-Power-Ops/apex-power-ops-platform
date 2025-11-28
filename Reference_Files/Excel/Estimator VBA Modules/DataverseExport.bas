Attribute VB_Name = "DataverseExport"
'============================================================
' DATAVERSE EXPORT MODULE
' Purpose: Export Estimator workbook data to JSON format
'          for import into Dataverse via Power Automate or script
'
' Output: JSON file ready for Dataverse import
' Usage: Run ExportToDataverse from any Estimator workbook
'        that has a Dataverse_Import sheet filled in
'
' Created: November 27, 2025
' Version: 1.0
'============================================================

Option Explicit

' Constants for cell locations on scope sheets
Private Const TOTAL_HOURS_CELL As String = "J3"
Private Const MULTIPLIER_CELL As String = "M4"
Private Const GRAND_TOTAL_CELL As String = "P3"
Private Const JOB_TYPE_CELL As String = "C4"
Private Const APPARATUS_START_ROW As Long = 6
Private Const APPARATUS_END_ROW As Long = 488

' Financial section rows (verified from actual workbook)
Private Const ONSITE_TOTAL_ROW As Long = 14
Private Const OFFSITE_TOTAL_ROW As Long = 19
Private Const TRAVEL_TOTAL_ROW As Long = 26
Private Const OUTSIDE_SERVICES_TOTAL_ROW As Long = 33

Public Sub ExportToDataverse()
    '============================================================
    ' Main entry point - validates metadata and exports JSON
    '============================================================
    
    Dim metaSheet As Worksheet
    Dim outputPath As String
    Dim fileNum As Integer
    Dim json As String
    
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
    
    ' Determine output path
    Dim basePath As String
    If Len(ThisWorkbook.Path) = 0 Or InStr(ThisWorkbook.Path, "https://") > 0 Then
        basePath = Environ("USERPROFILE") & "\Desktop"
    Else
        basePath = ThisWorkbook.Path
    End If
    
    ' Create output file with timestamp
    outputPath = basePath & "\" & _
                 SanitizeFilename(GetMetaValue(metaSheet, "Job #")) & "_" & _
                 "DATAVERSE_IMPORT_" & Format(Now, "yyyymmdd_hhmmss") & ".json"
    
    fileNum = FreeFile
    Open outputPath For Output As #fileNum
    Print #fileNum, json
    Close #fileNum
    
    ' Update import status on metadata sheet
    SetMetaValue metaSheet, "Import Status:", "Exported - Ready for Import"
    SetMetaValue metaSheet, "Last Import Date:", Format(Now, "yyyy-mm-dd hh:mm:ss")
    
    MsgBox "Export Complete!" & vbCrLf & vbCrLf & _
           "JSON file saved to:" & vbCrLf & outputPath & vbCrLf & vbCrLf & _
           "Next Steps:" & vbCrLf & _
           "1. Open Power Automate" & vbCrLf & _
           "2. Run the Dataverse Import flow" & vbCrLf & _
           "3. Select this JSON file", _
           vbInformation, "Export Complete"
    
    ' Open file location
    Shell "explorer.exe /select,""" & outputPath & """", vbNormalFocus
    
    Exit Sub
    
ErrorHandler:
    If fileNum > 0 Then Close #fileNum
    MsgBox "Error: " & Err.Description, vbCritical, "Export Failed"
End Sub

Private Function ValidateMetadata(metaSheet As Worksheet) As Boolean
    '============================================================
    ' Validate required metadata fields are filled in
    '============================================================
    
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
    '============================================================
    ' Find a label in column A and return value from column B
    '============================================================
    
    Dim cell As Range
    Dim searchRange As Range
    
    Set searchRange = metaSheet.Range("A:A")
    Set cell = searchRange.Find(What:=labelText, LookIn:=xlValues, LookAt:=xlWhole)
    
    If Not cell Is Nothing Then
        GetMetaValue = Trim(CStr(cell.Offset(0, 1).Value))
    Else
        GetMetaValue = ""
    End If
End Function

Private Sub SetMetaValue(metaSheet As Worksheet, labelText As String, newValue As String)
    '============================================================
    ' Find a label in column A and set value in column B
    '============================================================
    
    Dim cell As Range
    Dim searchRange As Range
    
    Set searchRange = metaSheet.Range("A:A")
    Set cell = searchRange.Find(What:=labelText, LookIn:=xlValues, LookAt:=xlWhole)
    
    If Not cell Is Nothing Then
        cell.Offset(0, 1).Value = newValue
    End If
End Sub

Private Function BuildExportJSON(metaSheet As Worksheet) As String
    '============================================================
    ' Build complete JSON structure for Dataverse import
    '============================================================
    
    Dim json As String
    Dim scopesJson As String
    Dim i As Integer
    Dim scopeCount As Integer
    
    ' Start JSON object
    json = "{" & vbCrLf
    
    ' Metadata section
    json = json & "  ""metadata"": {" & vbCrLf
    json = json & "    ""exportDate"": """ & Format(Now, "yyyy-mm-ddThh:mm:ss") & """," & vbCrLf
    json = json & "    ""workbookName"": """ & EscapeJSON(ThisWorkbook.Name) & """," & vbCrLf
    json = json & "    ""version"": ""1.0""" & vbCrLf
    json = json & "  }," & vbCrLf
    
    ' Client section
    json = json & "  ""client"": {" & vbCrLf
    json = json & "    ""name"": """ & EscapeJSON(GetMetaValue(metaSheet, "Client:")) & """" & vbCrLf
    json = json & "  }," & vbCrLf
    
    ' Site section
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
    
    ' Project section
    json = json & "  ""project"": {" & vbCrLf
    json = json & "    ""name"": """ & EscapeJSON(GetMetaValue(metaSheet, "Project:")) & """," & vbCrLf
    json = json & "    ""projectNumber"": """ & EscapeJSON(GetMetaValue(metaSheet, "Job #:")) & """," & vbCrLf
    json = json & "    ""projectLead"": """ & EscapeJSON(GetMetaValue(metaSheet, "Project Lead:")) & """," & vbCrLf
    json = json & "    ""businessUnit"": """ & EscapeJSON(GetMetaValue(metaSheet, "Business Unit:")) & """," & vbCrLf
    json = json & "    ""startDate"": """ & FormatDateISO(GetMetaValue(metaSheet, "Project Start Date:")) & """," & vbCrLf
    json = json & "    ""quoteDate"": """ & FormatDateISO(GetMetaValue(metaSheet, "Quote Date:")) & """," & vbCrLf
    json = json & "    ""quoteRevision"": """ & EscapeJSON(GetMetaValue(metaSheet, "Quote Revision:")) & """" & vbCrLf
    json = json & "  }," & vbCrLf
    
    ' Scopes section
    json = json & "  ""scopes"": [" & vbCrLf
    
    scopeCount = 0
    scopesJson = ""
    
    For i = 1 To 20
        Dim scopeJson As String
        scopeJson = BuildScopeJSON(i)
        If Len(scopeJson) > 0 Then
            If scopeCount > 0 Then
                scopesJson = scopesJson & "," & vbCrLf
            End If
            scopesJson = scopesJson & scopeJson
            scopeCount = scopeCount + 1
        End If
    Next i
    
    json = json & scopesJson & vbCrLf
    json = json & "  ]," & vbCrLf
    
    ' Summary section
    json = json & "  ""summary"": {" & vbCrLf
    json = json & "    ""totalScopes"": " & scopeCount & "," & vbCrLf
    json = json & "    ""grandTotal"": " & GetGrandTotal() & vbCrLf
    json = json & "  }" & vbCrLf
    
    json = json & "}"
    
    BuildExportJSON = json
End Function

Private Function BuildScopeJSON(scopeIndex As Integer) As String
    '============================================================
    ' Build JSON for a single scope sheet
    '============================================================
    
    Dim ws As Worksheet
    Dim totalHours As Variant
    Dim json As String
    
    ' Get scope sheet
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
    
    ' Check if scope has data
    totalHours = ws.Range(TOTAL_HOURS_CELL).Value
    If Not IsNumeric(totalHours) Or totalHours = 0 Then
        BuildScopeJSON = ""
        Exit Function
    End If
    
    ' Build scope JSON
    json = "    {" & vbCrLf
    json = json & "      ""scopeIndex"": " & scopeIndex & "," & vbCrLf
    json = json & "      ""name"": """ & EscapeJSON(ws.Name) & """," & vbCrLf
    json = json & "      ""scopeType"": """ & EscapeJSON(CStr(ws.Range(JOB_TYPE_CELL).Value)) & """," & vbCrLf
    json = json & "      ""totalHours"": " & FormatNumber(totalHours) & "," & vbCrLf
    json = json & "      ""multiplier"": " & FormatNumber(ws.Range(MULTIPLIER_CELL).Value) & "," & vbCrLf
    json = json & "      ""quotedAmount"": " & FormatNumber(ws.Range(GRAND_TOTAL_CELL).Value) & "," & vbCrLf
    
    ' Financial sections
    json = json & "      ""financials"": {" & vbCrLf
    json = json & "        ""onsiteLaborTotal"": " & FormatNumber(ws.Range("P" & ONSITE_TOTAL_ROW).Value) & "," & vbCrLf
    json = json & "        ""offsiteLaborTotal"": " & FormatNumber(ws.Range("P" & OFFSITE_TOTAL_ROW).Value) & "," & vbCrLf
    json = json & "        ""travelTotal"": " & FormatNumber(ws.Range("P" & TRAVEL_TOTAL_ROW).Value) & "," & vbCrLf
    json = json & "        ""outsideServicesTotal"": " & FormatNumber(ws.Range("P" & OUTSIDE_SERVICES_TOTAL_ROW).Value) & vbCrLf
    json = json & "      }," & vbCrLf
    
    ' Apparatus array
    json = json & "      ""apparatus"": [" & vbCrLf
    json = json & BuildApparatusJSON(ws) & vbCrLf
    json = json & "      ]" & vbCrLf
    json = json & "    }"
    
    BuildScopeJSON = json
End Function

Private Function BuildApparatusJSON(ws As Worksheet) As String
    '============================================================
    ' Build JSON array of apparatus from scope sheet
    '============================================================
    
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
        
        ' Check for data row (has equipment type and quantity > 0)
        If Len(equipType) > 0 And IsNumeric(qty) And qty > 0 Then
            If apparatusCount > 0 Then
                json = json & "," & vbCrLf
            End If
            
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
    '============================================================
    ' Get grand total from Equipment Reference sheet
    '============================================================
    
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
    '============================================================
    ' Escape special characters for JSON
    '============================================================
    
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
    '============================================================
    ' Format number for JSON (no currency symbols, null for empty)
    '============================================================
    
    If IsEmpty(val) Or val = "" Then
        FormatNumber = "0"
    ElseIf IsNumeric(val) Then
        FormatNumber = Format(CDbl(val), "0.00")
    Else
        FormatNumber = "0"
    End If
End Function

Private Function FormatDateISO(val As String) As String
    '============================================================
    ' Format date as ISO string, return empty if invalid
    '============================================================
    
    On Error Resume Next
    If IsDate(val) Then
        FormatDateISO = Format(CDate(val), "yyyy-mm-dd")
    Else
        FormatDateISO = ""
    End If
    On Error GoTo 0
End Function

Private Function SanitizeFilename(str As String) As String
    '============================================================
    ' Remove invalid filename characters
    '============================================================
    
    Dim result As String
    Dim i As Long
    Dim c As String
    
    result = ""
    For i = 1 To Len(str)
        c = Mid(str, i, 1)
        If c Like "[A-Za-z0-9_-]" Then
            result = result & c
        End If
    Next i
    
    SanitizeFilename = result
End Function

Public Sub QuickValidate()
    '============================================================
    ' Quick validation - check metadata without full export
    '============================================================
    
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
    
    ' Count active scopes
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
            If IsNumeric(totalHours) And totalHours > 0 Then
                scopeCount = scopeCount + 1
            End If
        End If
    Next i
    
    ' Display validation summary
    Dim msg As String
    msg = "VALIDATION SUMMARY" & vbCrLf & vbCrLf
    msg = msg & "Metadata Sheet: Found" & vbCrLf
    msg = msg & "Client: " & GetMetaValue(metaSheet, "Client:") & vbCrLf
    msg = msg & "Project: " & GetMetaValue(metaSheet, "Project:") & vbCrLf
    msg = msg & "Job #: " & GetMetaValue(metaSheet, "Job #:") & vbCrLf
    msg = msg & "Business Unit: " & GetMetaValue(metaSheet, "Business Unit:") & vbCrLf
    msg = msg & vbCrLf
    msg = msg & "Active Scopes Found: " & scopeCount & vbCrLf
    msg = msg & "Grand Total: " & FormatCurrency(CDbl(GetGrandTotal()), 2)
    
    MsgBox msg, vbInformation, "Quick Validation"
End Sub
