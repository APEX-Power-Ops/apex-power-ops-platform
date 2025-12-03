# Add Missing Apparatus Fields for Revenue Recognition Flow
# Fields needed: cr950_datecompleted, cr950_delayhours, cr950_completion_status

param([switch]$WhatIf)

Write-Host "`n══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " Adding Missing Apparatus Fields for Revenue Recognition" -ForegroundColor Cyan  
Write-Host " Target: org7bdbc942.crm.dynamics.com" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

# Load environment
$envPath = "C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp\.env"
Get-Content $envPath | Where-Object { $_ -match "^[A-Z]" } | ForEach-Object {
    $parts = $_ -split "=", 2
    [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
}

# Authenticate
$tokenUrl = "https://login.microsoftonline.com/$env:AZURE_TENANT_ID/oauth2/v2.0/token"
$tokenBody = @{
    client_id = $env:AZURE_CLIENT_ID
    scope = "https://org7bdbc942.crm.dynamics.com/.default"
    client_secret = $env:AZURE_CLIENT_SECRET
    grant_type = "client_credentials"
}

try {
    $tokenResponse = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $tokenBody -ContentType "application/x-www-form-urlencoded"
    $headers = @{
        Authorization = "Bearer $($tokenResponse.access_token)"
        "OData-MaxVersion" = "4.0"
        "OData-Version" = "4.0"
        Accept = "application/json"
        "Content-Type" = "application/json; charset=utf-8"
    }
    Write-Host "✅ Authenticated" -ForegroundColor Green
} catch {
    Write-Host "❌ Auth failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$baseUrl = "https://org7bdbc942.crm.dynamics.com/api/data/v9.2"
$attrUrl = "$baseUrl/EntityDefinitions(LogicalName='cr950_apparatus')/Attributes"

# Field 1: Date Completed (DateTime)
Write-Host "`n➕ Field 1: cr950_datecompleted (DateTime)" -ForegroundColor Yellow
$field1 = @{
    "@odata.type" = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
    "AttributeType" = "DateTime"
    "AttributeTypeName" = @{ "Value" = "DateTimeType" }
    "Format" = "DateAndTime"
    "DateTimeBehavior" = @{ "Value" = "UserLocal" }
    "SchemaName" = "cr950_datecompleted"
    "RequiredLevel" = @{ "Value" = "None"; "CanBeChanged" = $true }
    "DisplayName" = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        "LocalizedLabels" = @(@{
            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
            "Label" = "Date Completed"
            "LanguageCode" = 1033
        })
    }
    "Description" = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        "LocalizedLabels" = @(@{
            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
            "Label" = "Date and time when apparatus work was completed"
            "LanguageCode" = 1033
        })
    }
}

if ($WhatIf) {
    Write-Host "   [WHATIF] Would create field" -ForegroundColor Gray
} else {
    try {
        $body = $field1 | ConvertTo-Json -Depth 10
        Invoke-RestMethod -Uri $attrUrl -Method Post -Headers $headers -Body $body | Out-Null
        Write-Host "   ✅ Created" -ForegroundColor Green
    } catch {
        $err = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($err) { Write-Host "   ❌ $($err.error.message)" -ForegroundColor Red }
        else { Write-Host "   ❌ $($_.Exception.Message)" -ForegroundColor Red }
    }
}

Start-Sleep -Seconds 2

# Field 2: Delay Hours (Decimal)
Write-Host "`n➕ Field 2: cr950_delayhours (Decimal)" -ForegroundColor Yellow
$field2 = @{
    "@odata.type" = "Microsoft.Dynamics.CRM.DecimalAttributeMetadata"
    "AttributeType" = "Decimal"
    "AttributeTypeName" = @{ "Value" = "DecimalType" }
    "Precision" = 2
    "MinValue" = 0
    "MaxValue" = 10000
    "SchemaName" = "cr950_delayhours"
    "RequiredLevel" = @{ "Value" = "None"; "CanBeChanged" = $true }
    "DisplayName" = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        "LocalizedLabels" = @(@{
            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
            "Label" = "Delay Hours"
            "LanguageCode" = 1033
        })
    }
    "Description" = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        "LocalizedLabels" = @(@{
            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
            "Label" = "Additional hours due to delays or scope changes"
            "LanguageCode" = 1033
        })
    }
}

if ($WhatIf) {
    Write-Host "   [WHATIF] Would create field" -ForegroundColor Gray
} else {
    try {
        $body = $field2 | ConvertTo-Json -Depth 10
        Invoke-RestMethod -Uri $attrUrl -Method Post -Headers $headers -Body $body | Out-Null
        Write-Host "   ✅ Created" -ForegroundColor Green
    } catch {
        $err = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($err) { Write-Host "   ❌ $($err.error.message)" -ForegroundColor Red }
        else { Write-Host "   ❌ $($_.Exception.Message)" -ForegroundColor Red }
    }
}

Start-Sleep -Seconds 2

# Field 3: Completion Status (Choice/Picklist)
Write-Host "`n➕ Field 3: cr950_completion_status (Choice)" -ForegroundColor Yellow
$field3 = @{
    "@odata.type" = "Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
    "AttributeType" = "Picklist"
    "AttributeTypeName" = @{ "Value" = "PicklistType" }
    "SchemaName" = "cr950_completion_status"
    "RequiredLevel" = @{ "Value" = "None"; "CanBeChanged" = $true }
    "DisplayName" = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        "LocalizedLabels" = @(@{
            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
            "Label" = "Completion Status"
            "LanguageCode" = 1033
        })
    }
    "Description" = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        "LocalizedLabels" = @(@{
            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
            "Label" = "Work completion status - triggers revenue recognition when Complete"
            "LanguageCode" = 1033
        })
    }
    "OptionSet" = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.OptionSetMetadata"
        "IsGlobal" = $false
        "OptionSetType" = "Picklist"
        "Options" = @(
            @{
                "Value" = 1
                "Label" = @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                    "LocalizedLabels" = @(@{
                        "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                        "Label" = "Planned"
                        "LanguageCode" = 1033
                    })
                }
            }
            @{
                "Value" = 2
                "Label" = @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                    "LocalizedLabels" = @(@{
                        "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                        "Label" = "Complete"
                        "LanguageCode" = 1033
                    })
                }
            }
        )
    }
}

if ($WhatIf) {
    Write-Host "   [WHATIF] Would create field" -ForegroundColor Gray
} else {
    try {
        $body = $field3 | ConvertTo-Json -Depth 15
        Invoke-RestMethod -Uri $attrUrl -Method Post -Headers $headers -Body $body | Out-Null
        Write-Host "   ✅ Created" -ForegroundColor Green
    } catch {
        $err = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($err) { Write-Host "   ❌ $($err.error.message)" -ForegroundColor Red }
        else { Write-Host "   ❌ $($_.Exception.Message)" -ForegroundColor Red }
    }
}

Write-Host "`n══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host " Done! Fields added to cr950_apparatus:" -ForegroundColor Green
Write-Host "   • cr950_datecompleted (DateTime)" -ForegroundColor White
Write-Host "   • cr950_delayhours (Decimal)" -ForegroundColor White
Write-Host "   • cr950_completion_status (Choice: 1=Planned, 2=Complete)" -ForegroundColor White
Write-Host "`n Flow trigger: cr950_completion_status eq 2" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════════`n" -ForegroundColor Green
