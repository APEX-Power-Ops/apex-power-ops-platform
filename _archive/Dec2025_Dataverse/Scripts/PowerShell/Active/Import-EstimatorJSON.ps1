# Import Estimator JSON to Dataverse (V2 Schema)
param([string]$JsonPath = "", [switch]$WhatIf = $false)

# Load credentials from environment or .env file
$script:Config = @{
    TenantId = $env:RESA_TENANT_ID ?? "270d5723-4b30-4f3b-b9cb-6527be741b42"
    ClientId = $env:RESA_CLIENT_ID ?? "9df3350f-b3b4-47c4-97b5-499a8b02acc7"
    ClientSecret = $env:RESA_CLIENT_SECRET  # Set via environment variable
    DataverseUrl = $env:RESA_DATAVERSE_URL ?? "https://org99cd6c6e.crm.dynamics.com"
}

# Validate credentials
if (-not $script:Config.ClientSecret) {
    Write-Host "ERROR: RESA_CLIENT_SECRET environment variable not set." -ForegroundColor Red
    Write-Host "Set it with: `$env:RESA_CLIENT_SECRET = 'your-secret-here'" -ForegroundColor Yellow
    exit 1
}

$script:Tables = @{
    Client = "cr950_clients"; Site = "cr950_sites"; Project = "cr950_projects"
    Scope = "cr950_scopes"; Task = "cr950_tasks"; Apparatus = "cr950_apparatuses"
    ScopeLaborDetail = "cr950_scopelabordetails"
}

function Connect-DV {
    Write-Host "
=== RESA Estimator Import (V2 Schema) ===" -ForegroundColor Cyan
    $body = @{ grant_type = "client_credentials"; client_id = $script:Config.ClientId; client_secret = $script:Config.ClientSecret; resource = $script:Config.DataverseUrl }
    try {
        $t = Invoke-RestMethod -Uri "https://login.microsoftonline.com/$($script:Config.TenantId)/oauth2/token" -Method Post -Body $body
        $script:Token = $t.access_token
        $script:BaseUrl = "$($script:Config.DataverseUrl)/api/data/v9.2"
        $script:Headers = @{ Authorization = "Bearer $($script:Token)"; "Content-Type" = "application/json"; "Prefer" = "return=representation" }
        Write-Host "  Connected!" -ForegroundColor Green
        return $true
    } catch { Write-Host "  Connection failed: $($_.Exception.Message)" -ForegroundColor Red; return $false }
}

function Find-OrCreate-Client([string]$Name) {
    Write-Host "
[CLIENT] $Name" -ForegroundColor Cyan
    $f = "cr950_clientname eq '$($Name -replace "'","''")'"
    try { $r = Invoke-RestMethod -Uri "$($script:BaseUrl)/$($script:Tables.Client)?$filter=$f" -Headers $script:Headers; if ($r.value.Count -gt 0) { Write-Host "  Found: $($r.value[0].cr950_clientid)" -ForegroundColor Gray; return $r.value[0].cr950_clientid } } catch {}
    if ($WhatIf) { Write-Host "  [WHATIF] Would create" -ForegroundColor Yellow; return "WHATIF-CLIENT" }
    try { $r = Invoke-RestMethod -Uri "$($script:BaseUrl)/$($script:Tables.Client)" -Headers $script:Headers -Method Post -Body (@{cr950_clientname=$Name;cr950_clientactive=$true}|ConvertTo-Json); Write-Host "  Created: $($r.cr950_clientid)" -ForegroundColor Green; return $r.cr950_clientid } catch { Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red; return $null }
}

function Find-OrCreate-Site([string]$Name, [string]$ClientId, $D) {
    Write-Host "
[SITE] $Name" -ForegroundColor Cyan
    $f = "cr950_sitename eq '$($Name -replace "'","''")'"
    try { $r = Invoke-RestMethod -Uri "$($script:BaseUrl)/$($script:Tables.Site)?$filter=$f" -Headers $script:Headers; if ($r.value.Count -gt 0) { Write-Host "  Found: $($r.value[0].cr950_siteid)" -ForegroundColor Gray; return $r.value[0].cr950_siteid } } catch {}
    if ($WhatIf) { Write-Host "  [WHATIF] Would create" -ForegroundColor Yellow; return "WHATIF-SITE" }
    $rec = @{cr950_sitename=$Name;cr950_siteactive=$true}
    if ($ClientId -and $ClientId -notlike "WHATIF*") { $rec["cr950_SiteClient@odata.bind"] = "/$($script:Tables.Client)($ClientId)" }
    if ($D.address) { $rec["cr950_siteaddress"] = $D.address }
    if ($D.city) { $rec["cr950_sitecity"] = $D.city }
    if ($D.state) { $rec["cr950_sitestate"] = $D.state }
    if ($D.zipCode) { $rec["cr950_sitezip"] = $D.zipCode }
    if ($D.contactName) { $rec["cr950_sitecontactname"] = $D.contactName }
    if ($D.contactPhone) { $rec["cr950_sitecontactphone"] = $D.contactPhone }
    if ($D.contactEmail) { $rec["cr950_sitecontactemail"] = $D.contactEmail }
    try { $r = Invoke-RestMethod -Uri "$($script:BaseUrl)/$($script:Tables.Site)" -Headers $script:Headers -Method Post -Body ($rec|ConvertTo-Json -Depth 5); Write-Host "  Created: $($r.cr950_siteid)" -ForegroundColor Green; return $r.cr950_siteid } catch { Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red; return $null }
}

function Create-Project([string]$SiteId, [string]$ClientId, $D) {
    Write-Host "
[PROJECT] $($D.name) ($($D.projectNumber))" -ForegroundColor Cyan
    if ($WhatIf) { Write-Host "  [WHATIF] Would create" -ForegroundColor Yellow; return "WHATIF-PROJECT" }
    $rec = @{cr950_projectname=$D.name;cr950_projectstatus="New";cr950_projectactive=$true}
    if ($D.projectNumber) { $rec["cr950_projectnumber"] = $D.projectNumber }
    if ($SiteId -and $SiteId -notlike "WHATIF*") { $rec["cr950_ProjectSite@odata.bind"] = "/$($script:Tables.Site)($SiteId)" }
    if ($ClientId -and $ClientId -notlike "WHATIF*") { $rec["cr950_ProjectClient@odata.bind"] = "/$($script:Tables.Client)($ClientId)" }
    try { $r = Invoke-RestMethod -Uri "$($script:BaseUrl)/$($script:Tables.Project)" -Headers $script:Headers -Method Post -Body ($rec|ConvertTo-Json -Depth 5); Write-Host "  Created: $($r.cr950_projectid)" -ForegroundColor Green; return $r.cr950_projectid } catch { Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red; return $null }
}

function Create-Scope([string]$ProjectId, $D) {
    Write-Host "
  [SCOPE $($D.scopeIndex)] $($D.name)" -ForegroundColor Magenta
    if ($WhatIf) { Write-Host "    [WHATIF] Would create" -ForegroundColor Yellow; return "WHATIF-SCOPE" }
    $rec = @{cr950_scopename=$D.name;cr950_scopenumber="$($D.scopeIndex)";cr950_scopetype=$D.scopeType;cr950_scopestatus="Pending";cr950_scopeactive=$true}
    if ($ProjectId -and $ProjectId -notlike "WHATIF*") { $rec["cr950_ScopeProject@odata.bind"] = "/$($script:Tables.Project)($ProjectId)" }
    try { $r = Invoke-RestMethod -Uri "$($script:BaseUrl)/$($script:Tables.Scope)" -Headers $script:Headers -Method Post -Body ($rec|ConvertTo-Json -Depth 5); Write-Host "    Created: $($r.cr950_scopeid)" -ForegroundColor Green; return $r.cr950_scopeid } catch { Write-Host "    Failed: $($_.Exception.Message)" -ForegroundColor Red; return $null }
}

function Create-ScopeLaborDetail([string]$ScopeId, [string]$ScopeName, $D) {
    Write-Host "    [LABOR] Financial config" -ForegroundColor Gray
    if ($WhatIf) { Write-Host "      [WHATIF] Would create" -ForegroundColor Yellow; return "WHATIF-LABOR" }
    $fin = $D.financials
    $rec = @{cr950_scopelaborname="$ScopeName - Labor Config";cr950_scopelabortotalhours=[decimal]$D.totalHours;cr950_scopelabormultiplier=[decimal]$(if($D.multiplier){$D.multiplier}else{1.0});cr950_scopelaborquotedamount=[decimal]$D.quotedAmount;cr950_scopelaborsource="ESTIMATOR";cr950_scopelaboractive=$true}
    if ($ScopeId -and $ScopeId -notlike "WHATIF*") { $rec["cr950_ScopeLaborScope@odata.bind"] = "/$($script:Tables.Scope)($ScopeId)" }
    if ($fin) {
        if ($null -ne $fin.onsiteLaborTotal) { $rec["cr950_scopelaboronsitetotal"] = [decimal]$fin.onsiteLaborTotal }
        if ($null -ne $fin.offsiteLaborTotal) { $rec["cr950_scopelaboroffsitetotal"] = [decimal]$fin.offsiteLaborTotal }
        if ($null -ne $fin.travelTotal) { $rec["cr950_scopelabortraveltotal"] = [decimal]$fin.travelTotal }
        if ($null -ne $fin.outsideServicesTotal) { $rec["cr950_scopelaboroutsidetotal"] = [decimal]$fin.outsideServicesTotal }
    }
    try { $r = Invoke-RestMethod -Uri "$($script:BaseUrl)/$($script:Tables.ScopeLaborDetail)" -Headers $script:Headers -Method Post -Body ($rec|ConvertTo-Json -Depth 5); Write-Host "      Created: $($r.cr950_scopelabordetailid)" -ForegroundColor Green; return $r.cr950_scopelabordetailid } catch { Write-Host "      Failed: $($_.Exception.Message)" -ForegroundColor Red; return $null }
}

function Create-Task([string]$ScopeId, [string]$TaskName, [int]$Seq) {
    Write-Host "      [TASK $Seq] $TaskName" -ForegroundColor Gray
    if ($WhatIf) { Write-Host "        [WHATIF] Would create" -ForegroundColor Yellow; return "WHATIF-TASK" }
    $rec = @{cr950_taskname=$TaskName;cr950_tasksequence=$Seq;cr950_taskstatus="Pending";cr950_taskactive=$true}
    if ($ScopeId -and $ScopeId -notlike "WHATIF*") { $rec["cr950_TaskScope@odata.bind"] = "/$($script:Tables.Scope)($ScopeId)" }
    try { $r = Invoke-RestMethod -Uri "$($script:BaseUrl)/$($script:Tables.Task)" -Headers $script:Headers -Method Post -Body ($rec|ConvertTo-Json -Depth 5); return $r.cr950_taskid } catch { Write-Host "        Failed: $($_.Exception.Message)" -ForegroundColor Red; return $null }
}

function Create-Apparatus([string]$TaskId, $A, [int]$Seq) {
    if ($WhatIf) { return }
    $rec = @{cr950_apparatusname=$A.equipmentType;cr950_apparatustype=$A.equipmentType;cr950_apparatussection=$A.section;cr950_apparatusquantity=[int]$A.quantity;cr950_apparatushoursperunit=[decimal]$A.hoursPerUnit;cr950_apparatustotalhours=[decimal]$A.totalHours;cr950_apparatussequence=$Seq;cr950_apparatusstatus="Pending";cr950_apparatusactive=$true}
    if ($A.row) { $rec["cr950_apparatusrow"] = [int]$A.row }
    if ($TaskId -and $TaskId -notlike "WHATIF*") { $rec["cr950_ApparatusTask@odata.bind"] = "/$($script:Tables.Task)($TaskId)" }
    try { Invoke-RestMethod -Uri "$($script:BaseUrl)/$($script:Tables.Apparatus)" -Headers $script:Headers -Method Post -Body ($rec|ConvertTo-Json -Depth 5) | Out-Null } catch { Write-Host "        App failed: $($_.Exception.Message)" -ForegroundColor Red }
}

function Import-Data($Data) {
    $clientId = Find-OrCreate-Client -Name $Data.client.name
    if (-not $clientId) { Write-Host "Client failed. Aborting." -ForegroundColor Red; return }
    $siteId = Find-OrCreate-Site -Name $Data.site.name -ClientId $clientId -D $Data.site
    if (-not $siteId) { Write-Host "Site failed. Aborting." -ForegroundColor Red; return }
    $projectId = Create-Project -SiteId $siteId -ClientId $clientId -D $Data.project
    if (-not $projectId) { Write-Host "Project failed. Aborting." -ForegroundColor Red; return }
    
    $sc = 0; $ld = 0; $tc = 0; $ac = 0
    foreach ($scope in $Data.scopes) {
        $scopeId = Create-Scope -ProjectId $projectId -D $scope
        $sc++
        if ($scopeId) {
            $laborId = Create-ScopeLaborDetail -ScopeId $scopeId -ScopeName $scope.name -D $scope
            if ($laborId) { $ld++ }
            if ($scope.apparatus -and $scope.apparatus.Count -gt 0) {
                $sections = $scope.apparatus | Group-Object -Property section
                $ts = 1
                foreach ($section in $sections) {
                    $taskId = Create-Task -ScopeId $scopeId -TaskName $section.Name -Seq $ts
                    $tc++; $ts++; $as = 1
                    foreach ($app in $section.Group) { Create-Apparatus -TaskId $taskId -A $app -Seq $as; $ac++; $as++ }
                }
            }
        }
    }
    Write-Host "
======================================" -ForegroundColor Cyan
    Write-Host "IMPORT COMPLETE" -ForegroundColor Green
    Write-Host "  Scopes: $sc  Labor Details: $ld" -ForegroundColor White
    Write-Host "  Tasks: $tc  Apparatus: $ac" -ForegroundColor White
    Write-Host "======================================
" -ForegroundColor Cyan
}

if ($WhatIf) { Write-Host "
*** WHAT-IF MODE ***
" -ForegroundColor Yellow }
$json = $null
if ($JsonPath -and (Test-Path $JsonPath)) { Write-Host "Loading: $JsonPath" -ForegroundColor Gray; $json = Get-Content $JsonPath -Raw | ConvertFrom-Json }
else { try { $c = Get-Clipboard -Raw; if ($c -and $c.Trim().StartsWith("{")) { $json = $c | ConvertFrom-Json; Write-Host "Loaded from clipboard" -ForegroundColor Gray } } catch {} }
if (-not $json) { Write-Host "
Usage: .\Import-EstimatorJSON.ps1 -JsonPath 'file.json' [-WhatIf]" -ForegroundColor Yellow; exit 1 }
Write-Host "
JSON: $($json.client.name) / $($json.site.name) / $($json.project.name) ($($json.project.projectNumber)) - $($json.scopes.Count) scopes" -ForegroundColor White
if (Connect-DV) { Import-Data -Data $json }
