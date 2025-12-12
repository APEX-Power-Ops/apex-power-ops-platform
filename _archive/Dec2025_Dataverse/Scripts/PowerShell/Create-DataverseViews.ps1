#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Creates standard views for RESA Power Project Tracker tables
.DESCRIPTION
    Generates views via Dataverse Web API for Projects, Scopes, Apparatus, Clients, Sites
.NOTES
    Created: November 27, 2025
    Run from: C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp
#>

# Load environment from .env file (in MCP server directory)
$envFile = "C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
        }
    }
} else {
    Write-Host "❌ .env file not found at: $envFile" -ForegroundColor Red
    exit 1
}

$DataverseUrl = $env:DATAVERSE_URL
$TenantId = $env:AZURE_TENANT_ID
$ClientId = $env:AZURE_CLIENT_ID
$ClientSecret = $env:AZURE_CLIENT_SECRET

Write-Host "🚀 RESA Power View Generator" -ForegroundColor Cyan
Write-Host "   Environment: $DataverseUrl`n"

# Get access token
function Get-DataverseToken {
    $tokenUrl = "https://login.microsoftonline.com/$TenantId/oauth2/v2.0/token"
    $body = @{
        client_id     = $ClientId
        scope         = "$DataverseUrl/.default"
        client_secret = $ClientSecret
        grant_type    = "client_credentials"
    }
    
    $response = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
    return $response.access_token
}

# Create a saved query (view)
function New-DataverseView {
    param(
        [string]$Token,
        [string]$EntityLogicalName,
        [string]$ViewName,
        [string]$Description,
        [string]$FetchXml,
        [string]$LayoutXml,
        [int]$QueryType = 0  # 0 = Public View
    )
    
    $headers = @{
        "Authorization" = "Bearer $Token"
        "OData-MaxVersion" = "4.0"
        "OData-Version" = "4.0"
        "Content-Type" = "application/json"
        "Accept" = "application/json"
        "Prefer" = "return=representation"
    }
    
    $body = @{
        name = $ViewName
        description = $Description
        returnedtypecode = $EntityLogicalName
        fetchxml = $FetchXml
        layoutxml = $LayoutXml
        querytype = $QueryType
    } | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod -Uri "$DataverseUrl/api/data/v9.2/savedqueries" -Method Post -Headers $headers -Body $body
        Write-Host "   ✅ Created: $ViewName" -ForegroundColor Green
        return $response
    }
    catch {
        $err = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($err.error.message -match "already exists") {
            Write-Host "   ⏭️  Exists: $ViewName" -ForegroundColor Yellow
        } else {
            Write-Host "   ❌ Failed: $ViewName - $($err.error.message)" -ForegroundColor Red
        }
    }
}

# Get token
Write-Host "🔐 Authenticating..." -ForegroundColor Cyan
$token = Get-DataverseToken
Write-Host "   ✅ Token acquired`n"

# ============================================================
# PROJECTS VIEWS
# ============================================================
Write-Host "📋 Creating Projects Views..." -ForegroundColor Cyan

# Active Projects View
$fetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical">
  <entity name="cr950_projects">
    <attribute name="cr950_project_name" />
    <attribute name="cr950_job_number" />
    <attribute name="cr950_client" />
    <attribute name="cr950_site" />
    <attribute name="cr950_percent_complete" />
    <attribute name="cr950_total_apparatus_count" />
    <attribute name="cr950_total_apparatus_hours" />
    <attribute name="cr950_start_date" />
    <attribute name="cr950_target_completion_date" />
    <attribute name="cr950_projectsid" />
    <order attribute="cr950_project_name" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@

$layoutXml = @"
<grid name="resultset" object="10066" jump="cr950_project_name" select="1" icon="1" preview="1">
  <row name="result" id="cr950_projectsid">
    <cell name="cr950_project_name" width="200" />
    <cell name="cr950_job_number" width="100" />
    <cell name="cr950_client" width="150" />
    <cell name="cr950_site" width="150" />
    <cell name="cr950_percent_complete" width="80" />
    <cell name="cr950_total_apparatus_count" width="80" />
    <cell name="cr950_total_apparatus_hours" width="100" />
    <cell name="cr950_start_date" width="100" />
    <cell name="cr950_target_completion_date" width="100" />
  </row>
</grid>
"@

New-DataverseView -Token $token -EntityLogicalName "cr950_projects" `
    -ViewName "Active Projects" `
    -Description "All active projects with key metrics" `
    -FetchXml $fetchXml -LayoutXml $layoutXml

# Projects by Client View
$fetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical">
  <entity name="cr950_projects">
    <attribute name="cr950_project_name" />
    <attribute name="cr950_job_number" />
    <attribute name="cr950_client" />
    <attribute name="cr950_percent_complete" />
    <attribute name="cr950_total_apparatus_count" />
    <attribute name="cr950_contract_value" />
    <attribute name="cr950_projectsid" />
    <order attribute="cr950_client" />
    <order attribute="cr950_project_name" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@

$layoutXml = @"
<grid name="resultset" object="10066" jump="cr950_project_name" select="1" icon="1" preview="1">
  <row name="result" id="cr950_projectsid">
    <cell name="cr950_client" width="150" />
    <cell name="cr950_project_name" width="200" />
    <cell name="cr950_job_number" width="100" />
    <cell name="cr950_percent_complete" width="80" />
    <cell name="cr950_total_apparatus_count" width="80" />
    <cell name="cr950_contract_value" width="120" />
  </row>
</grid>
"@

New-DataverseView -Token $token -EntityLogicalName "cr950_projects" `
    -ViewName "Projects by Client" `
    -Description "Projects grouped by client" `
    -FetchXml $fetchXml -LayoutXml $layoutXml

# ============================================================
# SCOPES VIEWS
# ============================================================
Write-Host "`n📋 Creating Scope Views..." -ForegroundColor Cyan

$fetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical">
  <entity name="cr950_projectscope">
    <attribute name="cr950_scope_name" />
    <attribute name="cr950_project" />
    <attribute name="cr950_testing_standard" />
    <attribute name="cr950_percent_complete" />
    <attribute name="cr950_total_apparatus_count" />
    <attribute name="cr950_total_apparatus_hours" />
    <attribute name="cr950_total_completed_hours" />
    <attribute name="cr950_projectscopeid" />
    <order attribute="cr950_project" />
    <order attribute="cr950_scope_name" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@

$layoutXml = @"
<grid name="resultset" object="10067" jump="cr950_scope_name" select="1" icon="1" preview="1">
  <row name="result" id="cr950_projectscopeid">
    <cell name="cr950_project" width="180" />
    <cell name="cr950_scope_name" width="150" />
    <cell name="cr950_testing_standard" width="100" />
    <cell name="cr950_percent_complete" width="80" />
    <cell name="cr950_total_apparatus_count" width="80" />
    <cell name="cr950_total_apparatus_hours" width="100" />
    <cell name="cr950_total_completed_hours" width="100" />
  </row>
</grid>
"@

New-DataverseView -Token $token -EntityLogicalName "cr950_projectscope" `
    -ViewName "All Scopes" `
    -Description "All project scopes with progress metrics" `
    -FetchXml $fetchXml -LayoutXml $layoutXml

# ============================================================
# APPARATUS VIEWS
# ============================================================
Write-Host "`n📋 Creating Apparatus Views..." -ForegroundColor Cyan

# All Apparatus View
$fetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical">
  <entity name="cr950_apparatus">
    <attribute name="cr950_apparatus_designation" />
    <attribute name="cr950_project" />
    <attribute name="cr950_scope" />
    <attribute name="cr950_labor_hours" />
    <attribute name="cr950_actual_hours" />
    <attribute name="cr950_completion_status" />
    <attribute name="cr950_datecompleted" />
    <attribute name="cr950_apparatusid" />
    <order attribute="cr950_project" />
    <order attribute="cr950_scope" />
    <order attribute="cr950_apparatus_designation" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@

$layoutXml = @"
<grid name="resultset" object="10068" jump="cr950_apparatus_designation" select="1" icon="1" preview="1">
  <row name="result" id="cr950_apparatusid">
    <cell name="cr950_apparatus_designation" width="250" />
    <cell name="cr950_project" width="150" />
    <cell name="cr950_scope" width="120" />
    <cell name="cr950_labor_hours" width="80" />
    <cell name="cr950_actual_hours" width="80" />
    <cell name="cr950_completion_status" width="100" />
    <cell name="cr950_datecompleted" width="100" />
  </row>
</grid>
"@

New-DataverseView -Token $token -EntityLogicalName "cr950_apparatus" `
    -ViewName "All Apparatus" `
    -Description "All apparatus with status and hours" `
    -FetchXml $fetchXml -LayoutXml $layoutXml

# Pending Work View (Not Started)
$fetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical">
  <entity name="cr950_apparatus">
    <attribute name="cr950_apparatus_designation" />
    <attribute name="cr950_project" />
    <attribute name="cr950_scope" />
    <attribute name="cr950_labor_hours" />
    <attribute name="cr950_anticipatedstart" />
    <attribute name="cr950_apparatusid" />
    <order attribute="cr950_anticipatedstart" />
    <order attribute="cr950_project" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
      <condition attribute="cr950_completion_status" operator="null" />
      <condition attribute="cr950_actualstart" operator="null" />
    </filter>
  </entity>
</fetch>
"@

$layoutXml = @"
<grid name="resultset" object="10068" jump="cr950_apparatus_designation" select="1" icon="1" preview="1">
  <row name="result" id="cr950_apparatusid">
    <cell name="cr950_apparatus_designation" width="280" />
    <cell name="cr950_project" width="150" />
    <cell name="cr950_scope" width="120" />
    <cell name="cr950_labor_hours" width="100" />
    <cell name="cr950_anticipatedstart" width="100" />
  </row>
</grid>
"@

New-DataverseView -Token $token -EntityLogicalName "cr950_apparatus" `
    -ViewName "Pending Work" `
    -Description "Apparatus not yet started" `
    -FetchXml $fetchXml -LayoutXml $layoutXml

# In Progress View
$fetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical">
  <entity name="cr950_apparatus">
    <attribute name="cr950_apparatus_designation" />
    <attribute name="cr950_project" />
    <attribute name="cr950_scope" />
    <attribute name="cr950_labor_hours" />
    <attribute name="cr950_actual_hours" />
    <attribute name="cr950_actualstart" />
    <attribute name="cr950_apparatusid" />
    <order attribute="cr950_actualstart" descending="true" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
      <condition attribute="cr950_actualstart" operator="not-null" />
      <condition attribute="cr950_datecompleted" operator="null" />
    </filter>
  </entity>
</fetch>
"@

$layoutXml = @"
<grid name="resultset" object="10068" jump="cr950_apparatus_designation" select="1" icon="1" preview="1">
  <row name="result" id="cr950_apparatusid">
    <cell name="cr950_apparatus_designation" width="280" />
    <cell name="cr950_project" width="150" />
    <cell name="cr950_scope" width="120" />
    <cell name="cr950_labor_hours" width="80" />
    <cell name="cr950_actual_hours" width="80" />
    <cell name="cr950_actualstart" width="100" />
  </row>
</grid>
"@

New-DataverseView -Token $token -EntityLogicalName "cr950_apparatus" `
    -ViewName "In Progress" `
    -Description "Apparatus currently being worked" `
    -FetchXml $fetchXml -LayoutXml $layoutXml

# Completed View
$fetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical">
  <entity name="cr950_apparatus">
    <attribute name="cr950_apparatus_designation" />
    <attribute name="cr950_project" />
    <attribute name="cr950_scope" />
    <attribute name="cr950_labor_hours" />
    <attribute name="cr950_actual_hours" />
    <attribute name="cr950_datecompleted" />
    <attribute name="cr950_apparatus_assessment" />
    <attribute name="cr950_apparatusid" />
    <order attribute="cr950_datecompleted" descending="true" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
      <condition attribute="cr950_datecompleted" operator="not-null" />
    </filter>
  </entity>
</fetch>
"@

$layoutXml = @"
<grid name="resultset" object="10068" jump="cr950_apparatus_designation" select="1" icon="1" preview="1">
  <row name="result" id="cr950_apparatusid">
    <cell name="cr950_apparatus_designation" width="250" />
    <cell name="cr950_project" width="150" />
    <cell name="cr950_scope" width="120" />
    <cell name="cr950_labor_hours" width="80" />
    <cell name="cr950_actual_hours" width="80" />
    <cell name="cr950_datecompleted" width="100" />
    <cell name="cr950_apparatus_assessment" width="100" />
  </row>
</grid>
"@

New-DataverseView -Token $token -EntityLogicalName "cr950_apparatus" `
    -ViewName "Completed" `
    -Description "All completed apparatus" `
    -FetchXml $fetchXml -LayoutXml $layoutXml

# ============================================================
# CLIENTS VIEW
# ============================================================
Write-Host "`n📋 Creating Client Views..." -ForegroundColor Cyan

$fetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical">
  <entity name="cr950_client">
    <attribute name="cr950_name" />
    <attribute name="cr950_clientid" />
    <order attribute="cr950_name" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@

$layoutXml = @"
<grid name="resultset" object="10069" jump="cr950_name" select="1" icon="1" preview="1">
  <row name="result" id="cr950_clientid">
    <cell name="cr950_name" width="300" />
  </row>
</grid>
"@

New-DataverseView -Token $token -EntityLogicalName "cr950_client" `
    -ViewName "All Clients" `
    -Description "All clients alphabetically" `
    -FetchXml $fetchXml -LayoutXml $layoutXml

# ============================================================
# SITES VIEW
# ============================================================
Write-Host "`n📋 Creating Site Views..." -ForegroundColor Cyan

$fetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical">
  <entity name="cr950_site">
    <attribute name="cr950_name" />
    <attribute name="cr950_client" />
    <attribute name="cr950_address" />
    <attribute name="cr950_city" />
    <attribute name="cr950_state" />
    <attribute name="cr950_sitecontactemail" />
    <attribute name="cr950_siteid" />
    <order attribute="cr950_client" />
    <order attribute="cr950_name" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@

$layoutXml = @"
<grid name="resultset" object="10070" jump="cr950_name" select="1" icon="1" preview="1">
  <row name="result" id="cr950_siteid">
    <cell name="cr950_name" width="200" />
    <cell name="cr950_client" width="150" />
    <cell name="cr950_address" width="180" />
    <cell name="cr950_city" width="100" />
    <cell name="cr950_state" width="60" />
    <cell name="cr950_sitecontactemail" width="180" />
  </row>
</grid>
"@

New-DataverseView -Token $token -EntityLogicalName "cr950_site" `
    -ViewName "All Sites" `
    -Description "All sites with client and address" `
    -FetchXml $fetchXml -LayoutXml $layoutXml

# ============================================================
# SUMMARY
# ============================================================
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "✅ VIEW GENERATION COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host @"

Views Created:
  Projects:
    - Active Projects
    - Projects by Client
  
  Scopes:
    - All Scopes
  
  Apparatus:
    - All Apparatus
    - Pending Work
    - In Progress
    - Completed
  
  Clients:
    - All Clients
  
  Sites:
    - All Sites

Next: Open Power Apps and verify views appear in each table.
      You may need to publish customizations.

"@ -ForegroundColor White
