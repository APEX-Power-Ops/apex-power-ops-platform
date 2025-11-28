# Create Test Data for RESA Power Project Tracker
# Run this script to populate Dataverse with test records for rollup validation

param(
    [string]$Environment = "https://org99cd6c6e.crm.dynamics.com"
)

Write-Host "`n=== RESA Power Test Data Creation ===" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "⚠️  Note: Using Claude Desktop with resa-dataverse-mcp is recommended" -ForegroundColor Yellow
Write-Host "This script uses PAC CLI which may have table name issues`n" -ForegroundColor Yellow

# Get credentials interactively
Write-Host "Authenticate to Dataverse..." -ForegroundColor Gray
$credential = Get-Credential -Message "Enter your Dataverse credentials (Jason.Swenson@resapower.com)"

if (-not $credential) {
    Write-Host "❌ Authentication cancelled" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Credentials obtained`n" -ForegroundColor Green

# Function to create record using PAC CLI
function Create-Record {
    param(
        [string]$TableName,
        [hashtable]$Data
    )
    
    # Convert hashtable to JSON
    $json = $Data | ConvertTo-Json -Compress
    
    Write-Host "Creating $TableName record..." -ForegroundColor Gray
    
    # Use PAC data create command
    $result = pac data create --entity-logical-name $TableName --data $json 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        # Extract ID from result (format: "Record created with ID: guid")
        if ($result -match "ID: ([a-f0-9-]+)") {
            $id = $matches[1]
            Write-Host "  ✅ Created: $id" -ForegroundColor Green
            return $id
        }
        Write-Host "  ✅ Created (ID not captured)" -ForegroundColor Green
        return $null
    } else {
        Write-Host "  ❌ Failed: $result" -ForegroundColor Red
        return $null
    }
}

# Step 1: Create Business Unit (Location)
Write-Host "`n--- Step 1: Business Unit ---" -ForegroundColor Cyan
$businessUnitId = Create-Record -TableName "cr950_businessunit" -Data @{
    "cr950_name" = "Phoenix Test Office"
    "cr950_code" = "PHX-TEST"
}

if (-not $businessUnitId) {
    Write-Host "⚠️  Skipping Business Unit (may already exist or not required)" -ForegroundColor Yellow
}

# Step 2: Create Client
Write-Host "`n--- Step 2: Client ---" -ForegroundColor Cyan
$clientId = Create-Record -TableName "cr950_client" -Data @{
    "cr950_name" = "Test Hospital"
    "cr950_accountnumber" = "TEST-2025-001"
}

if (-not $clientId) {
    Write-Host "❌ Client creation failed - cannot continue" -ForegroundColor Red
    exit 1
}

# Step 3: Create Site
Write-Host "`n--- Step 3: Site ---" -ForegroundColor Cyan
$siteData = @{
    "cr950_name" = "Main Campus - Test"
    "cr950_address" = "123 Test Street"
    "cr950_city" = "Phoenix"
    "cr950_state" = "AZ"
}

# Add client lookup if ID was captured
if ($clientId) {
    $siteData["cr950_client@odata.bind"] = "/cr950_clients($clientId)"
}

$siteId = Create-Record -TableName "cr950_site" -Data $siteData

if (-not $siteId) {
    Write-Host "❌ Site creation failed - cannot continue" -ForegroundColor Red
    exit 1
}

# Step 4: Create Project
Write-Host "`n--- Step 4: Project ---" -ForegroundColor Cyan
$projectData = @{
    "cr950_name" = "Hospital Switchgear Testing - Test Data"
    "cr950_projectnumber" = "PHX-2025-TEST001"
    "cr950_description" = "Test project for rollup field validation"
}

# Add lookups if IDs were captured
if ($clientId) {
    $projectData["cr950_client@odata.bind"] = "/cr950_clients($clientId)"
}
if ($siteId) {
    $projectData["cr950_site@odata.bind"] = "/cr950_sites($siteId)"
}
if ($businessUnitId) {
    $projectData["cr950_location@odata.bind"] = "/cr950_businessunits($businessUnitId)"
}

$projectId = Create-Record -TableName "cr950_projects" -Data $projectData

if (-not $projectId) {
    Write-Host "❌ Project creation failed - cannot continue" -ForegroundColor Red
    exit 1
}

# Step 5: Create Scope
Write-Host "`n--- Step 5: Project Scope ---" -ForegroundColor Cyan
$scopeData = @{
    "cr950_name" = "Main Distribution Panels"
    "cr950_scopenumber" = "S01"
    "cr950_description" = "Test scope for rollup validation"
}

if ($projectId) {
    $scopeData["cr950_project@odata.bind"] = "/cr950_projectses($projectId)"
}

$scopeId = Create-Record -TableName "cr950_projectscope" -Data $scopeData

if (-not $scopeId) {
    Write-Host "❌ Scope creation failed - cannot continue" -ForegroundColor Red
    exit 1
}

# Step 6: Create Tasks
Write-Host "`n--- Step 6: Tasks ---" -ForegroundColor Cyan

$task1Data = @{
    "cr950_name" = "Switchgear - Building A"
    "cr950_description" = "Test task 1"
}
if ($projectId) { $task1Data["cr950_project@odata.bind"] = "/cr950_projectses($projectId)" }
if ($scopeId) { $task1Data["cr950_projectscope@odata.bind"] = "/cr950_projectscopes($scopeId)" }

$task1Id = Create-Record -TableName "cr950_tasks" -Data $task1Data

$task2Data = @{
    "cr950_name" = "Switchgear - Building B"
    "cr950_description" = "Test task 2"
}
if ($projectId) { $task2Data["cr950_project@odata.bind"] = "/cr950_projectses($projectId)" }
if ($scopeId) { $task2Data["cr950_projectscope@odata.bind"] = "/cr950_projectscopes($scopeId)" }

$task2Id = Create-Record -TableName "cr950_tasks" -Data $task2Data

$task3Data = @{
    "cr950_name" = "Switchgear - Building C"
    "cr950_description" = "Test task 3"
}
if ($projectId) { $task3Data["cr950_project@odata.bind"] = "/cr950_projectses($projectId)" }
if ($scopeId) { $task3Data["cr950_projectscope@odata.bind"] = "/cr950_projectscopes($scopeId)" }

$task3Id = Create-Record -TableName "cr950_tasks" -Data $task3Data

# Step 7: Create Apparatus with Dates
Write-Host "`n--- Step 7: Apparatus (with dates for rollup validation) ---" -ForegroundColor Cyan

$apparatusCount = 0

# Create 3 apparatus per task with varying dates
$tasks = @(
    @{ Id = $task1Id; Name = "Task 1" },
    @{ Id = $task2Id; Name = "Task 2" },
    @{ Id = $task3Id; Name = "Task 3" }
)

$baseDate = Get-Date "2025-12-01"

foreach ($task in $tasks) {
    if (-not $task.Id) { continue }
    
    for ($i = 1; $i -le 3; $i++) {
        $apparatusData = @{
            "cr950_name" = "Breaker $($task.Name)-$i"
            "cr950_apparatusnumber" = "BRK-$($task.Name)-$i"
            "cr950_anticipatedstartdate" = ($baseDate.AddDays($i)).ToString("yyyy-MM-dd")
            "cr950_actualstartdate" = ($baseDate.AddDays($i + 1)).ToString("yyyy-MM-dd")
        }
        
        # Mark some as complete
        if ($i -le 2) {
            $apparatusData["cr950_datecompleted"] = ($baseDate.AddDays($i + 5)).ToString("yyyy-MM-dd")
        }
        
        # Add lookups
        if ($projectId) { $apparatusData["cr950_project@odata.bind"] = "/cr950_projectses($projectId)" }
        if ($scopeId) { $apparatusData["cr950_projectscope@odata.bind"] = "/cr950_projectscopes($scopeId)" }
        $apparatusData["cr950_task@odata.bind"] = "/cr950_taskses($($task.Id))"
        
        $apparatusId = Create-Record -TableName "cr950_apparatus" -Data $apparatusData
        
        if ($apparatusId) { $apparatusCount++ }
    }
}

# Summary
Write-Host "`n=== Test Data Creation Complete ===" -ForegroundColor Cyan
Write-Host "Created:" -ForegroundColor Yellow
Write-Host "  • 1 Business Unit (Location)" -ForegroundColor White
Write-Host "  • 1 Client" -ForegroundColor White
Write-Host "  • 1 Site" -ForegroundColor White
Write-Host "  • 1 Project" -ForegroundColor White
Write-Host "  • 1 Scope" -ForegroundColor White
Write-Host "  • 3 Tasks" -ForegroundColor White
Write-Host "  • $apparatusCount Apparatus (with dates)" -ForegroundColor White

Write-Host "`n⏱️  Wait 2-3 minutes for rollup calculations..." -ForegroundColor Yellow
Write-Host "Then query the tables to verify rollup fields populated.`n" -ForegroundColor Gray

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Wait for rollup calculations (check System Jobs)" -ForegroundColor White
Write-Host "2. Query Tasks table to see date rollups" -ForegroundColor White
Write-Host "3. Query Scope table to see aggregated rollups" -ForegroundColor White
Write-Host "4. Query Project table to see top-level rollups`n" -ForegroundColor White
