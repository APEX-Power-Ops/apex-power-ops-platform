Attribute VB_Name = "PDFPrintView"

Option Explicit

Public SheetPicker_LastSelection As Collection

Private Const TEMPLATE_SHEET As String = "Print_Template"
Private Const TEMPLATE_PRINT_AREA As String = "$A$1:$H$46"  ' Updated per requirements
Private Const MAX_DATA_ROWS_PER_PAGE As Long = 38  ' CORRECTED: Rows 7-44 = 38 rows (rows 45-46 reserved for border)

Sub CreatePrintViews()
    On Error GoTo ErrorHandler
    Set SheetPicker_LastSelection = Nothing
    Load ufSelectSheets
    ufSelectSheets.Show vbModal
    
    If SheetPicker_LastSelection Is Nothing Or SheetPicker_LastSelection.count = 0 Then
        MsgBox "No sheets selected.", vbExclamation
        GoTo Cleanup
    End If
    
    Call ExportSheetsAsPDF_WithPagination(SheetPicker_LastSelection)
    
Cleanup:
    On Error Resume Next
    Unload ufSelectSheets
    Set SheetPicker_LastSelection = Nothing
    Exit Sub
    
ErrorHandler:
    MsgBox "Error: " & Err.Description, vbCritical
    Resume Cleanup
End Sub

Sub ExportSheetsAsPDF_WithPagination(selectedSheets As Collection)
    On Error GoTo ErrorHandler
    
    Dim wsTemplate As Worksheet
    Dim tempWB As Workbook
    Dim fileName As String
    Dim fileDialog As fileDialog
    Dim srcList As Collection
    Dim i As Long
    Dim pageCount As Long
    Dim firstSheetUsed As Boolean
    
    ' Get template sheet and force consistent setup
    Set wsTemplate = GetSheetOrFail(TEMPLATE_SHEET)
    
    ' Apply standard setup to template first
    Call EnforceStandardPageSetup(wsTemplate)
    
    ' Build source worksheet collection
    Set srcList = New Collection
    For i = 1 To selectedSheets.count
        Dim srcWS As Worksheet
        Set srcWS = FindWorksheetByCodeName(CStr(selectedSheets(i)))
        If Not srcWS Is Nothing Then srcList.Add srcWS
    Next i
    
    If srcList.count = 0 Then Exit Sub
    
    ' Get save location
    Set fileDialog = Application.fileDialog(msoFileDialogSaveAs)
    With fileDialog
        .Title = "Save PDF As"
        .InitialFileName = "Scope_Sheets_" & Format(Now, "yyyymmdd_hhmmss") & ".pdf"
        If .Show <> -1 Then Exit Sub
        fileName = .SelectedItems(1)
        If Right(fileName, 4) <> ".pdf" Then fileName = fileName & ".pdf"
    End With
    
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    
    ' Create temporary workbook
    Set tempWB = Application.Workbooks.Add(xlWBATWorksheet)
    firstSheetUsed = False
    pageCount = 0
    
    ' Process each selected sheet with pagination
    For i = 1 To srcList.count
        Set srcWS = srcList(i)
        Call ProcessSheetWithPagination(srcWS, wsTemplate, tempWB, pageCount, firstSheetUsed)
    Next i
    
    ' Export to PDF with basic parameters (compatible with all Excel versions)
    tempWB.ExportAsFixedFormat Type:=xlTypePDF, fileName:=fileName, _
        Quality:=xlQualityStandard, OpenAfterPublish:=True
    
    MsgBox "PDF exported with " & pageCount & " pages: " & fileName, vbInformation
    
Cleanup:
    On Error Resume Next
    If Not tempWB Is Nothing Then tempWB.Close SaveChanges:=False
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    Exit Sub

ErrorHandler:
    MsgBox "Export error: " & Err.Description, vbCritical
    Resume Cleanup
End Sub

Private Sub ProcessSheetWithPagination(srcSheet As Worksheet, templateSheet As Worksheet, targetWB As Workbook, ByRef pageCount As Long, ByRef firstSheetUsed As Boolean)
    Dim lastDataRow As Long
    Dim currentDataRow As Long
    Dim pageNum As Long
    Dim totalDataRows As Long
    
    ' Find last meaningful data row with improved detection
    lastDataRow = GetLastMeaningfulDataRow(srcSheet)
    
    ' If no meaningful data found, skip this sheet
    If lastDataRow < 5 Then Exit Sub
    
    ' Calculate actual data rows (excluding headers)
    totalDataRows = CountMeaningfulDataRows(srcSheet, 6, lastDataRow)
    
    ' IMPROVED: Use actual data count for single page decision
    ' Most sheets should fit on one page even with spacing
    If totalDataRows <= 36 Then  ' CORRECTED: Conservative threshold for 38-row max
        Call CreateSinglePageWithTemplateFormatting(srcSheet, templateSheet, targetWB, lastDataRow, pageCount, firstSheetUsed)
        Exit Sub
    End If
    
    ' Multi-page processing needed
    currentDataRow = 6 ' Start at row 6 (first actual data row after column headers in row 5)
    pageNum = 1
    
    Do While currentDataRow <= lastDataRow
        Dim endRow As Long
        Dim dataRowsOnPage As Long
        Dim searchRow As Long
        Dim destRowEstimate As Long
        
        ' Start with conservative limit
        dataRowsOnPage = 0
        endRow = currentDataRow
        destRowEstimate = 7  ' Starting position on template
        
        ' IMPROVED: Keep adding data rows until we hit the page limit
        ' Account for actual template positioning
        For searchRow = currentDataRow To lastDataRow
            If HasMeaningfulData(srcSheet, searchRow) Then
                dataRowsOnPage = dataRowsOnPage + 1
                endRow = searchRow
                destRowEstimate = destRowEstimate + 1
                
                ' SAFETY: Stop if we would exceed template row 44
                ' (leaving rows 45-46 as buffer for border)
                If destRowEstimate > 44 Then
                    ' Back up to previous data row
                    dataRowsOnPage = dataRowsOnPage - 1
                    ' Find previous data row
                    Dim prevRow As Long
                    For prevRow = endRow - 1 To currentDataRow Step -1
                        If HasMeaningfulData(srcSheet, prevRow) Then
                            endRow = prevRow
                            Exit For
                        End If
                    Next prevRow
                    Exit For
                End If
                
                ' Also stop at reasonable data count (38 max rows: 7-44)
                If dataRowsOnPage >= 38 Then  ' CORRECTED: Match MAX_DATA_ROWS_PER_PAGE
                    Exit For
                End If
            End If
        Next searchRow
        
        ' Find optimal break point if needed
        If dataRowsOnPage >= 36 Then  ' CORRECTED: Adjusted threshold for 38-row max
            endRow = FindOptimalBreakPoint(srcSheet, currentDataRow, endRow)
        End If
        
        ' Create the page
        Call CreatePageWithTemplateFormatting(srcSheet, templateSheet, targetWB, currentDataRow, endRow, pageNum > 1, pageCount, srcSheet.Name & "_Page" & pageNum, firstSheetUsed)
        
        ' Move to next data row after endRow
        currentDataRow = endRow + 1
        pageNum = pageNum + 1
        
        ' Safety break
        If pageNum > 50 Then
            MsgBox "Safety break: Too many pages for sheet " & srcSheet.Name, vbExclamation
            Exit Do
        End If
    Loop
End Sub

Private Sub CreateSinglePageWithTemplateFormatting(srcSheet As Worksheet, templateSheet As Worksheet, targetWB As Workbook, lastRow As Long, ByRef pageCount As Long, ByRef firstSheetUsed As Boolean)
    ' Start from row 6 (first data row after headers) for single page processing
    Call CreatePageWithTemplateFormatting(srcSheet, templateSheet, targetWB, 6, lastRow, False, pageCount, SafeSheetName(srcSheet.Name), firstSheetUsed)
End Sub

Private Sub CreatePageWithTemplateFormatting(srcSheet As Worksheet, templateSheet As Worksheet, targetWB As Workbook, startRow As Long, endRow As Long, isSubsequentPage As Boolean, ByRef pageCount As Long, pageName As String, ByRef firstSheetUsed As Boolean)
    Dim tmpWS As Worksheet
    
    ' Use first sheet or create new one
    If Not firstSheetUsed Then
        Set tmpWS = targetWB.Worksheets(1)
        firstSheetUsed = True
        
        ' COMPLETE template preservation - copy everything
        templateSheet.Cells.Copy
        tmpWS.Cells.PasteSpecial Paste:=xlPasteAllUsingSourceTheme
        Application.CutCopyMode = False
        
    Else
        ' For subsequent pages, create exact copy of template sheet
        templateSheet.Copy After:=targetWB.Sheets(targetWB.Sheets.count)
        Set tmpWS = targetWB.Sheets(targetWB.Sheets.count)
    End If
    
    ' Set name
    tmpWS.Name = pageName
    
    ' FORCE consistent page setup for every sheet
    Call EnforceStandardPageSetup(tmpWS)
    
    ' Copy source sheet headers A1:G4 ONLY (preserving template row 5)
    tmpWS.Range("A1:G4").value = srcSheet.Range("A1:G4").value
    
    ' EXPLICITLY preserve template row 5 by re-copying it from template
    templateSheet.Range("A5:H5").Copy
    tmpWS.Range("A5:H5").PasteSpecial Paste:=xlPasteAll
    Application.CutCopyMode = False
    
    ' Clear only data area (A6:H44) - preserve row 5 AND rows 45-46 (bottom border)
    tmpWS.Range("A6:H44").ClearContents  ' CORRECTED: Stop at row 44, preserve 45-46
    
    ' Handle data copying WITH spacing preservation
    If Not isSubsequentPage Then
        ' First page: Copy all data starting from row 6 onward to template row 7 (keeping row 6 blank)
        Call CopyDataWithSpacing(srcSheet, tmpWS, 6, endRow, 7)
    Else
        ' Subsequent pages: Copy all data starting at row 7 (keeping row 6 blank)
        Call CopyDataWithSpacing(srcSheet, tmpWS, startRow, endRow, 7)
    End If
    
    ' Final page setup enforcement
    Call EnforceStandardPageSetup(tmpWS)
    
    pageCount = pageCount + 1
End Sub

Private Sub EnforceStandardPageSetup(ws As Worksheet)
    ' FORCE consistent page setup for every single page
    With ws.PageSetup
        ' Print area and orientation
        .PrintArea = TEMPLATE_PRINT_AREA
        .Orientation = xlPortrait
        
        ' Margins (enforced consistently)
        .LeftMargin = Application.InchesToPoints(0.7)
        .RightMargin = Application.InchesToPoints(0.7)
        .TopMargin = Application.InchesToPoints(0.75)
        .BottomMargin = Application.InchesToPoints(0.75)
        .HeaderMargin = Application.InchesToPoints(0.3)
        .FooterMargin = Application.InchesToPoints(0.3)
        
        ' Centering and scaling
        .CenterHorizontally = True
        .CenterVertically = False
        .Zoom = False
        .FitToPagesWide = 1
        .FitToPagesTall = 1
        
        ' Print quality and options
        .PrintQuality = 600
        .Draft = False
        .BlackAndWhite = False
        
        ' Headers and footers (clear them to prevent conflicts)
        .LeftHeader = ""
        .CenterHeader = ""
        .RightHeader = ""
        .LeftFooter = ""
        .CenterFooter = ""
        .RightFooter = ""
    End With
End Sub

' ENHANCED: Copy data while preserving spacing but optimizing for consolidation
Private Sub CopyDataWithSpacing(srcSheet As Worksheet, destSheet As Worksheet, srcStartRow As Long, srcEndRow As Long, destStartRow As Long)
    Dim srcRow As Long, destRow As Long
    Dim consecutiveEmptyRows As Long
    
    destRow = destStartRow
    consecutiveEmptyRows = 0
    
    For srcRow = srcStartRow To srcEndRow
        ' Check if this row has meaningful data
        If HasMeaningfulData(srcSheet, srcRow) Then
            ' Copy the row with data
            Call CopyRowWithCleanup(srcSheet, destSheet, srcRow, destRow)
            destRow = destRow + 1
            consecutiveEmptyRows = 0
        Else
            ' This is an empty row - be selective about copying
            consecutiveEmptyRows = consecutiveEmptyRows + 1
            
            ' IMPROVED: Only copy empty rows that provide meaningful spacing
            ' Skip multiple consecutive empty rows to save space
            If consecutiveEmptyRows <= 1 Then
                ' Copy single empty row for spacing, but not at the start of a new page
                If srcRow > srcStartRow Or destRow > destStartRow Then
                    Call CopyRowWithCleanup(srcSheet, destSheet, srcRow, destRow)
                    destRow = destRow + 1
                End If
            End If
            ' Skip additional consecutive empty rows to consolidate better
        End If
        
        ' CRITICAL: Don't exceed row 44 (rows 45-46 are bottom border)
        If destRow > 44 Then Exit For
    Next srcRow
End Sub

Private Sub CopyRowWithCleanup(srcSheet As Worksheet, destSheet As Worksheet, srcRow As Long, destRow As Long)
    Dim col As Long
    Dim cellValue As Variant
    Dim srcCell As Range
    Dim destCell As Range
    Dim isHeaderRow As Boolean
    
    ' Detect if this is a section header row (has bold text in column E, typically)
    isHeaderRow = srcSheet.Cells(srcRow, 5).Font.Bold And _
                  Len(Trim(CStr(srcSheet.Cells(srcRow, 5).value))) > 0 And _
                  Trim(CStr(srcSheet.Cells(srcRow, 3).value)) = ""  ' No QTY value
    
    For col = 1 To 8 ' Columns A to H (full range)
        Set srcCell = srcSheet.Cells(srcRow, col)
        Set destCell = destSheet.Cells(destRow, col)
        
        cellValue = srcCell.value
        
        ' Clean up the value
        If IsError(cellValue) Or CStr(cellValue) = "#N/A" Or CStr(cellValue) = "#NULL!" Then
            destCell.value = ""
        Else
            destCell.value = cellValue
        End If
        
        ' Apply font properties with enhanced preservation
        With destCell.Font
            .Name = "Calibri"                    ' Enforce Calibri font
            .Bold = srcCell.Font.Bold            ' Retain bold state from source
            .Size = srcCell.Font.Size            ' Retain font size from source
            
            ' ENHANCED: Font color handling
            If isHeaderRow Then
                ' Header rows: Preserve ALL formatting including white text for masked zeros
                .Color = srcCell.Font.Color
            ElseIf col = 4 Then
                ' Column D (NETA#): Preserve source color (allows white masking of zeros)
                .Color = srcCell.Font.Color
            Else
                ' Check if source has white font (indicating masked value)
                If srcCell.Font.Color = RGB(255, 255, 255) Or srcCell.Font.Color = vbWhite Then
                    ' Preserve white font for masked values
                    .Color = srcCell.Font.Color
                Else
                    ' All other columns: Enforce black font
                    .Color = RGB(0, 0, 0)
                End If
            End If
        End With
    Next col
End Sub

' CRITICAL FIX: Updated with correct column mapping
Private Function HasMeaningfulData(ws As Worksheet, row As Long) As Boolean
    Dim col As Long
    Dim cellValue As Variant
    Dim qtyText As String
    Dim netaText As String
    Dim typeText As String
    
    ' CORRECTED COLUMN MAPPING:
    ' Column A = White border (skip)
    ' Column B = Blue border (skip)
    ' Column C = QTY
    ' Column D = NETA#
    ' Column E = Apparatus Type
    ' Column F = Designation
    ' Column G = Dwg#
    ' Column H = Blue border (skip)
    
    ' Get values from the CORRECT columns
    qtyText = Trim(CStr(ws.Cells(row, 3).value))   ' Column C - QTY
    netaText = Trim(CStr(ws.Cells(row, 4).value))  ' Column D - NETA#
    typeText = Trim(CStr(ws.Cells(row, 5).value))  ' Column E - Apparatus Type
    
    ' PRIORITY CHECK: Bold section headers (no QTY, but bold text in column E)
    If Len(typeText) > 0 And ws.Cells(row, 5).Font.Bold And Len(qtyText) = 0 Then
        ' This is a section header like "SLD -Medium-Voltage - Core"
        HasMeaningfulData = True
        Exit Function
    End If
    
    ' Check if row has equipment data
    ' Option 1: Has a quantity number in column C (including blank QTY for tests)
    If Len(qtyText) > 0 And IsNumeric(qtyText) Then
        If Val(qtyText) > 0 Then
            HasMeaningfulData = True
            Exit Function
        End If
    End If
    
    ' Option 2: Has NETA code in column D (IMPORTANT: includes tests without QTY)
    If Len(netaText) > 0 Then
        ' Accept any NETA code (7.x format or test descriptions)
        If InStr(netaText, "7.") > 0 Or _
           InStr(1, netaText, "Ground", vbTextCompare) > 0 Or _
           InStr(1, netaText, "Test", vbTextCompare) > 0 Then
            HasMeaningfulData = True
            Exit Function
        End If
    End If
    
    ' Option 3: Has equipment type in column E (including tests)
    If Len(typeText) > 2 Then
        If InStr(1, typeText, "Switchboard", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Breaker", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Transformer", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Panel", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Generator", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Ground", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Arrestor", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Meter", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Relay", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Transfer", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Current", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Control", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Potential", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Switch", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Resistance", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Test", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Conductor", vbTextCompare) > 0 Or _
           InStr(1, typeText, "SLD", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Voltage", vbTextCompare) > 0 Or _
           InStr(1, typeText, "Medium", vbTextCompare) > 0 Then
            HasMeaningfulData = True
            Exit Function
        End If
    End If
    
    ' Also check column F for designation codes
    Dim designText As String
    designText = Trim(CStr(ws.Cells(row, 6).value))  ' Column F - Designation
    If Len(designText) > 0 Then
        If InStr(designText, "USB") > 0 Or _
           InStr(designText, "COP") > 0 Or _
           InStr(designText, "E01") > 0 Or _
           InStr(designText, "E02") > 0 Or _
           InStr(designText, "Distribution") > 0 Or _
           InStr(designText, "Generator") > 0 Or _
           InStr(designText, "Grounding") > 0 Then
            HasMeaningfulData = True
            Exit Function
        End If
    End If
    
    HasMeaningfulData = False
End Function

Private Function CountMeaningfulDataRows(ws As Worksheet, startRow As Long, endRow As Long) As Long
    Dim row As Long
    Dim count As Long
    
    count = 0
    For row = startRow To endRow
        If HasMeaningfulData(ws, row) Then
            count = count + 1
        End If
    Next row
    
    CountMeaningfulDataRows = count
End Function

Private Function GetLastMeaningfulDataRow(ws As Worksheet) As Long
    Dim row As Long
    Dim lastRow As Long
    Dim actualLastRow As Long
    
    ' Find the actual last row with any data in the worksheet
    actualLastRow = ws.Cells(ws.Rows.count, 1).End(xlUp).row
    
    ' Expand search range to handle sparse data
    Dim searchRange As Long
    searchRange = Application.Max(actualLastRow, 1000)  ' Search much further
    
    lastRow = 0
    
    ' Work backwards to find last meaningful data
    For row = searchRange To 5 Step -1
        If HasMeaningfulData(ws, row) Then
            lastRow = row
            Exit For
        End If
    Next row
    
    GetLastMeaningfulDataRow = lastRow
End Function

Private Function FindWorksheetByCodeName(codeName As String) As Worksheet
    Dim ws As Worksheet
    For Each ws In ThisWorkbook.Worksheets
        If ws.codeName = codeName Then
            Set FindWorksheetByCodeName = ws
            Exit Function
        End If
    Next ws
    Set FindWorksheetByCodeName = Nothing
End Function

Private Function FindOptimalBreakPoint(ws As Worksheet, startRow As Long, maxEndRow As Long) As Long
    Dim row As Long
    Dim minBreakRow As Long
    Dim bestBreakRow As Long
    Dim gapSize As Long
    Dim lastDataRow As Long
    
    minBreakRow = startRow + 5 ' Minimum rows per page
    bestBreakRow = maxEndRow ' Default to maximum consolidation
    
    ' SPECIAL CHECK: Are there distant final items (like grounding tests)?
    ' Check if there's meaningful data beyond a large gap
    lastDataRow = 0
    gapSize = 0
    
    For row = maxEndRow To minBreakRow Step -1
        If HasMeaningfulData(ws, row) Then
            lastDataRow = row
            Exit For
        Else
            gapSize = gapSize + 1
        End If
    Next row
    
    ' If we found a huge gap (>15 empty rows) but there's more data beyond maxEndRow
    If gapSize > 15 And maxEndRow < 500 Then
        ' Check if there's data beyond this gap
        Dim beyondDataCount As Long
        beyondDataCount = CountMeaningfulDataRows(ws, maxEndRow + 1, maxEndRow + 50)
        
        ' If there are only a few rows beyond (like 2 grounding tests), DON'T break here
        If beyondDataCount > 0 And beyondDataCount <= 5 Then
            ' Force inclusion by not breaking at the gap
            FindOptimalBreakPoint = maxEndRow
            Exit Function
        End If
    End If
    
    ' Standard logic: Look for smaller gaps as break points
    For row = maxEndRow To minBreakRow Step -1
        If Not HasMeaningfulData(ws, row) Then
            ' Found an empty row - potential break point
            
            ' Check if this leaves too few items stranded
            Dim remainingAfterBreak As Long
            remainingAfterBreak = CountMeaningfulDataRows(ws, row + 1, ws.Rows.count)
            
            If remainingAfterBreak > 0 And remainingAfterBreak <= 3 Then
                ' Don't break here if it orphans just a few rows
                ' Just skip to next iteration (can't use Continue For in VBA)
            Else
                ' This is a good break point
                bestBreakRow = row - 1
                Exit For
            End If
        End If
    Next row
    
    FindOptimalBreakPoint = bestBreakRow
End Function

Private Function GetSheetOrFail(nameOrCodeName As String) As Worksheet
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(nameOrCodeName)
    On Error GoTo 0
    If Not ws Is Nothing Then
        Set GetSheetOrFail = ws
        Exit Function
    End If
    
    Err.Raise vbObjectError + 513, , "Sheet '" & nameOrCodeName & "' not found."
End Function

Private Function SafeSheetName(s As String) As String
    Dim bad As Variant, i As Long
    bad = Array("\", "/", ":", "*", "?", """", "<", ">", "|", "[", "]")
    For i = LBound(bad) To UBound(bad)
        s = Replace$(s, bad(i), "_")
    Next i
    If Len(s) = 0 Then s = "Sheet"
    If Len(s) > 31 Then s = Left$(s, 31)
    SafeSheetName = s
End Function



