Attribute VB_Name = "modDateModeRibbon"
Option Explicit

' ================================================================================
' SIMPLIFIED RIBBON INTEGRATION - SINGLE TOGGLE BUTTON
' ================================================================================
' This module provides callbacks for a simple single-click toggle button
' No split button, no dropdown menu - just one clean toggle
' ================================================================================

' ================================================================================
' MODULE-LEVEL VARIABLES
' ================================================================================

' Store reference to ribbon for refreshing button label/icon
Public myRibbon As IRibbonUI

' ================================================================================
' RIBBON BUTTON CALLBACKS
' ================================================================================

' This is called when the ribbon loads
Public Sub OnRibbonLoad(ribbon As IRibbonUI)
    Set myRibbon = ribbon
End Sub

' Main toggle button callback
Public Sub OnToggleDateMode(control As IRibbonControl)
    ' Called when user clicks the toggle button
    ToggleDateMode
    
    ' Refresh ribbon to update button label and icon
    If Not myRibbon Is Nothing Then
        myRibbon.Invalidate
    End If
End Sub

' Check date status button callback
Public Sub OnCheckDateStatus(control As IRibbonControl)
    CheckDateStatus
End Sub

' Get button label dynamically based on current mode
Public Sub GetButtonLabel(control As IRibbonControl, ByRef returnedVal)
    returnedVal = GetModeForRibbon()
End Sub

' Get button image based on current mode
Public Sub GetButtonImage(control As IRibbonControl, ByRef returnedVal)
    If GetDateMode() = "MANUAL" Then
        returnedVal = "EditRelationship"  ' Orange pencil icon for Manual
    Else
        returnedVal = "CalendarInsert"    ' Calendar icon for Auto
    End If
End Sub

' ================================================================================
' WRAPPER FUNCTIONS (Called from ThisWorkbook or ribbon callbacks)
' ================================================================================

Public Sub ToggleDateMode()
    ' Public wrapper that calls ThisWorkbook.ToggleDateMode
    ThisWorkbook.ToggleDateMode
End Sub

Public Sub CheckDateStatus()
    ' Public wrapper for date status check
    ThisWorkbook.CheckDateStatus
End Sub

Public Function GetDateMode() As String
    ' Public wrapper for getting mode
    GetDateMode = ThisWorkbook.GetDateMode()
End Function

Public Function GetModeForRibbon() As String
    ' Returns formatted mode name for ribbon button display
    Dim currentMode As String
    currentMode = GetDateMode()
    
    If currentMode = "MANUAL" Then
        GetModeForRibbon = "Manual Mode"
    Else
        GetModeForRibbon = "Auto Mode"
    End If
End Function

' ================================================================================
' ALTERNATIVE: ADD TO QUICK ACCESS TOOLBAR (No XML Needed)
' ================================================================================

Public Sub AddModeButtonToRibbon()
    ' This creates a button in the Add-Ins tab programmatically
    ' Run this macro once to add the button
    
    On Error Resume Next
    
    Dim cbButton As CommandBarButton
    
    ' Remove existing button if present
    Application.CommandBars("Worksheet Menu Bar").Controls("Toggle Date Mode").Delete
    
    ' Add new button
    Set cbButton = Application.CommandBars("Worksheet Menu Bar").Controls.Add(Type:=msoControlButton)
    
    With cbButton
        .Caption = "Toggle Date Mode"
        .OnAction = "ToggleDateMode"
        .Style = msoButtonIconAndCaption
        .FaceId = 1976  ' Circular arrow icon
        .TooltipText = "Toggle between Auto and Manual date modes"
    End With
    
    MsgBox "Date Mode button added to toolbar!", vbInformation
    
End Sub

' ================================================================================
' KEYBOARD SHORTCUT IMPLEMENTATION
' ================================================================================

Public Sub SetupKeyboardShortcut()
    ' Assigns Ctrl+Shift+D as keyboard shortcut for mode toggle
    ' Run this macro once to set up the shortcut
    
    Application.OnKey "^+D", "ToggleDateMode"
    
    MsgBox "Keyboard shortcut assigned!" & vbCrLf & vbCrLf & _
           "Press Ctrl+Shift+D to toggle Date Mode", vbInformation
End Sub
