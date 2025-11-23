<#
.SYNOPSIS
    Updates PROJECT_CONTEXT.json with current project state

.DESCRIPTION
    Interactive script to update the PROJECT_CONTEXT.json file with:
    - Session information (timestamp, session ID)
    - Current status (ready to implement, in planning, blockers)
    - Critical facts discovered
    - Project metadata changes

.PARAMETER SessionTopic
    Brief description of current session (e.g., "Date Tracking Implementation")

.PARAMETER AddCriticalFact
    New critical fact to add to the criticalFacts array

.PARAMETER UpdateStatus
    Update the current status sections

.PARAMETER QuickUpdate
    Just update timestamp and sessionId without prompts

.EXAMPLE
    .\Update-ProjectContext.ps1 -SessionTopic "Revenue Rollups" -QuickUpdate

.EXAMPLE
    .\Update-ProjectContext.ps1 -AddCriticalFact "New field added: Revenue_Recognition_Date"

.EXAMPLE
    .\Update-ProjectContext.ps1 -UpdateStatus

.NOTES
    Author: RESA Power Project Team
    Created: November 19, 2025
    Version: 1.0
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$SessionTopic,

    [Parameter(Mandatory=$false)]
    [string]$AddCriticalFact,

    [Parameter(Mandatory=$false)]
    [switch]$UpdateStatus,

    [Parameter(Mandatory=$false)]
    [switch]$QuickUpdate,

    [Parameter(Mandatory=$false)]
    [string]$ProjectRoot = "C:\RESA_Power_Build"
)

# Colors for output
$colors = @{
    Header = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "White"
    Prompt = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "Info"
    )
    Write-Host $Message -ForegroundColor $colors[$Color]
}

function Get-CurrentTimestamp {
    return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Get-SessionId {
    param([string]$Topic)
    $date = (Get-Date).ToString("MMMdd").ToUpper()
    if ($Topic) {
        $cleanTopic = $Topic -replace '[^a-zA-Z0-9_]', '_'
        return "${date}_${cleanTopic}"
    }
    return "${date}_SESSION"
}

# Main script
Write-ColorOutput "`n=== PROJECT CONTEXT UPDATER ===" "Header"
Write-ColorOutput "Updating: PROJECT_CONTEXT.json`n" "Info"

# Check if file exists
$contextFile = Join-Path $ProjectRoot "PROJECT_CONTEXT.json"
if (-not (Test-Path $contextFile)) {
    Write-ColorOutput "ERROR: PROJECT_CONTEXT.json not found at: $contextFile" "Error"
    Write-ColorOutput "Expected location: $ProjectRoot\PROJECT_CONTEXT.json" "Warning"
    exit 1
}

# Read current context
try {
    $context = Get-Content $contextFile -Raw | ConvertFrom-Json
    Write-ColorOutput "✓ Loaded current context" "Success"
} catch {
    Write-ColorOutput "ERROR: Failed to parse PROJECT_CONTEXT.json: $_" "Error"
    exit 1
}

# Quick Update Mode
if ($QuickUpdate) {
    Write-ColorOutput "`nQUICK UPDATE MODE" "Header"
    
    $timestamp = Get-CurrentTimestamp
    $context.lastUpdated = $timestamp
    
    if ($SessionTopic) {
        $sessionId = Get-SessionId -Topic $SessionTopic
        $context.sessionId = $sessionId
        Write-ColorOutput "Session Topic: $SessionTopic" "Info"
    } else {
        $sessionId = Get-SessionId
        $context.sessionId = $sessionId
    }
    
    Write-ColorOutput "Updated: lastUpdated = $($context.lastUpdated)" "Success"
    Write-ColorOutput "Updated: sessionId = $($context.sessionId)" "Success"
    
    # Save and exit
    $context | ConvertTo-Json -Depth 10 | Set-Content $contextFile -Encoding UTF8
    Write-ColorOutput "`n✓ Context updated successfully!" "Success"
    exit 0
}

# Interactive Mode
Write-ColorOutput "Current Session: $($context.sessionId)" "Info"
Write-ColorOutput "Last Updated: $($context.lastUpdated)" "Info"
Write-ColorOutput ""

# Update basic info
Write-ColorOutput "=== UPDATE SESSION INFO ===" "Header"

if (-not $SessionTopic) {
    $SessionTopic = Read-Host "Enter session topic (or press Enter to skip)"
}

if ($SessionTopic) {
    $sessionId = Get-SessionId -Topic $SessionTopic
    $context.sessionId = $sessionId
    Write-ColorOutput "✓ Session ID: $($context.sessionId)" "Success"
}

$timestamp = Get-CurrentTimestamp
$context.lastUpdated = $timestamp
Write-ColorOutput "✓ Timestamp: $($context.lastUpdated)" "Success"

# Update version if changed
Write-ColorOutput "`n=== UPDATE VERSION (Current: $($context.project.version)) ===" "Header"
$newVersion = Read-Host "New version (or press Enter to keep current)"
if ($newVersion) {
    $context.project.version = $newVersion
    Write-ColorOutput "✓ Version updated to: $newVersion" "Success"
}

# Add critical facts
Write-ColorOutput "`n=== ADD CRITICAL FACTS ===" "Header"
Write-ColorOutput "Current critical facts:" "Info"
$context.criticalFacts | ForEach-Object { Write-ColorOutput "  - $_" "Info" }

if ($AddCriticalFact) {
    $context.criticalFacts += $AddCriticalFact
    Write-ColorOutput "✓ Added: $AddCriticalFact" "Success"
} else {
    Write-ColorOutput "`nAdd new critical fact? (y/n)" "Prompt"
    $addFact = Read-Host
    while ($addFact -eq 'y') {
        $newFact = Read-Host "Enter critical fact"
        if ($newFact) {
            $context.criticalFacts += $newFact
            Write-ColorOutput "✓ Added: $newFact" "Success"
        }
        Write-ColorOutput "Add another? (y/n)" "Prompt"
        $addFact = Read-Host
    }
}

# Update status
if ($UpdateStatus) {
    Write-ColorOutput "`n=== UPDATE STATUS ===" "Header"
    
    # Ready to Implement
    Write-ColorOutput "`nCurrent 'Ready to Implement' tasks:" "Info"
    $context.currentStatus.readyToImplement | ForEach-Object { 
        Write-ColorOutput "  - $($_.name) ($($_.timeEstimate))" "Info" 
    }
    
    Write-ColorOutput "`nUpdate 'Ready to Implement'? (y/n)" "Prompt"
    if ((Read-Host) -eq 'y') {
        Write-ColorOutput "Action: (a)dd, (r)emove, (s)kip" "Prompt"
        $action = Read-Host
        
        if ($action -eq 'a') {
            $taskName = Read-Host "Task name"
            $timeEst = Read-Host "Time estimate"
            $priority = Read-Host "Priority (HIGH/MEDIUM/LOW)"
            $value = Read-Host "Business value"
            $spec = Read-Host "Spec document path"
            
            $newTask = @{
                name = $taskName
                timeEstimate = $timeEst
                priority = $priority
                value = $value
                spec = $spec
            }
            
            $context.currentStatus.readyToImplement += $newTask
            Write-ColorOutput "✓ Added task: $taskName" "Success"
        }
        elseif ($action -eq 'r') {
            $index = Read-Host "Enter index to remove (0-based)"
            if ($index -match '^\d+$' -and [int]$index -lt $context.currentStatus.readyToImplement.Count) {
                $removed = $context.currentStatus.readyToImplement[[int]$index]
                $context.currentStatus.readyToImplement = @($context.currentStatus.readyToImplement | Where-Object { $_ -ne $removed })
                Write-ColorOutput "✓ Removed task: $($removed.name)" "Success"
            }
        }
    }
    
    # Blockers
    Write-ColorOutput "`nCurrent blockers:" "Info"
    if ($context.currentStatus.blockers.Count -eq 0) {
        Write-ColorOutput "  (none)" "Success"
    } else {
        $context.currentStatus.blockers | ForEach-Object { Write-ColorOutput "  - $_" "Warning" }
    }
    
    Write-ColorOutput "`nUpdate blockers? (y/n)" "Prompt"
    if ((Read-Host) -eq 'y') {
        Write-ColorOutput "Action: (a)dd, (r)emove, (c)lear all, (s)kip" "Prompt"
        $action = Read-Host
        
        if ($action -eq 'a') {
            $blocker = Read-Host "Enter blocker description"
            if ($blocker) {
                $context.currentStatus.blockers += $blocker
                Write-ColorOutput "✓ Added blocker: $blocker" "Warning"
            }
        }
        elseif ($action -eq 'r') {
            $index = Read-Host "Enter index to remove (0-based)"
            if ($index -match '^\d+$' -and [int]$index -lt $context.currentStatus.blockers.Count) {
                $removed = $context.currentStatus.blockers[[int]$index]
                $context.currentStatus.blockers = @($context.currentStatus.blockers | Where-Object { $_ -ne $removed })
                Write-ColorOutput "✓ Removed blocker" "Success"
            }
        }
        elseif ($action -eq 'c') {
            $context.currentStatus.blockers = @()
            Write-ColorOutput "✓ Cleared all blockers" "Success"
        }
    }
}

# Save updated context
Write-ColorOutput "`n=== SAVING CHANGES ===" "Header"

try {
    $jsonOutput = $context | ConvertTo-Json -Depth 10
    $jsonOutput | Set-Content $contextFile -Encoding UTF8
    Write-ColorOutput "✓ Context saved successfully!" "Success"
} catch {
    Write-ColorOutput "ERROR: Failed to save context: $_" "Error"
    exit 1
}

# Summary
Write-ColorOutput "`n=== SUMMARY ===" "Header"
Write-ColorOutput "Session ID: $($context.sessionId)" "Info"
Write-ColorOutput "Last Updated: $($context.lastUpdated)" "Info"
Write-ColorOutput "Version: $($context.project.version)" "Info"
Write-ColorOutput "Critical Facts: $($context.criticalFacts.Count)" "Info"
Write-ColorOutput "Ready to Implement: $($context.currentStatus.readyToImplement.Count)" "Info"
Write-ColorOutput "Blockers: $($context.currentStatus.blockers.Count)" "Info"

# Git commit prompt
Write-ColorOutput "`n=== GIT COMMIT ===" "Header"
Write-ColorOutput "Commit changes to Git? (y/n)" "Prompt"
if ((Read-Host) -eq 'y') {
    try {
        Set-Location $ProjectRoot
        git add PROJECT_CONTEXT.json
        
        $commitMsg = "chore: Update project context - $($context.sessionId)"
        git commit -m $commitMsg
        
        Write-ColorOutput "✓ Committed to Git" "Success"
        Write-ColorOutput "`nPush to remote? (y/n)" "Prompt"
        if ((Read-Host) -eq 'y') {
            git push public clean-main
            Write-ColorOutput "✓ Pushed to GitHub" "Success"
        }
    } catch {
        Write-ColorOutput "WARNING: Git operations failed: $_" "Warning"
    }
}

Write-ColorOutput "`n✓ Update complete!" "Success"
