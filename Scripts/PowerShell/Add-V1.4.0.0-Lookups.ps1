# Add v1.4.0.0 Lookup Relationships
# Created: November 22, 2025
# Purpose: Create 9 lookup relationships for new tables via Dataverse Web API
# Reference: V1_4_0_0_ROADMAP_AND_PRIORITIES.md - Priority 1A

<#
.SYNOPSIS
    Creates 9 lookup relationships for v1.4.0.0 tables
.DESCRIPTION
    Adds the following lookups:
    1. Sites → Clients
    2. Quotes → Clients
    3. Quotes → Sites
    4. Projects → Clients
    5. Projects → Sites
    6. Resource Assignments → Projects
    7. Resource Assignments → Employees
    8. Equipment → Employees (optional)
    9. Equipment → Projects (optional)
.EXAMPLE
    .\Add-V1.4.0.0-Lookups.ps1
#>

# Import shared functions
. "$PSScriptRoot\Dataverse-Functions.ps1"

# Connect to Dataverse
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  v1.4.0.0 Lookup Relationships Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$token = Connect-Dataverse
if (-not $token) {
    Write-Host "❌ Failed to connect to Dataverse. Exiting." -ForegroundColor Red
    exit 1
}

# Define all lookup relationships to create
$lookups = @(
    @{
        Number = 1
        ReferencingEntity = "cr950_site"
        ReferencingAttribute = "cr950_client"
        ReferencedEntity = "cr950_client"
        ReferencedAttribute = "cr950_clientid"
        SchemaName = "cr950_client_site"
        DisplayName = "Client"
        Description = "Link sites to owning clients"
        IsRequired = $true
        CascadeDelete = "Restrict"  # Prevent deleting client if sites exist
    },
    @{
        Number = 2
        ReferencingEntity = "cr950_quote"
        ReferencingAttribute = "cr950_client"
        ReferencedEntity = "cr950_client"
        ReferencedAttribute = "cr950_clientid"
        SchemaName = "cr950_client_quote"
        DisplayName = "Client"
        Description = "Track which client requested quote"
        IsRequired = $true
        CascadeDelete = "Restrict"
    },
    @{
        Number = 3
        ReferencingEntity = "cr950_quote"
        ReferencingAttribute = "cr950_site"
        ReferencedEntity = "cr950_site"
        ReferencedAttribute = "cr950_siteid"
        SchemaName = "cr950_site_quote"
        DisplayName = "Site"
        Description = "Link quote to specific work location"
        IsRequired = $false  # Quote might be for multiple sites or TBD
        CascadeDelete = "Restrict"
    },
    @{
        Number = 4
        ReferencingEntity = "cr950_projects"
        ReferencingAttribute = "cr950_client"
        ReferencedEntity = "cr950_client"
        ReferencedAttribute = "cr950_clientid"
        SchemaName = "cr950_client_project"
        DisplayName = "Client"
        Description = "Link project to customer"
        IsRequired = $true
        CascadeDelete = "Restrict"
    },
    @{
        Number = 5
        ReferencingEntity = "cr950_projects"
        ReferencingAttribute = "cr950_site"
        ReferencedEntity = "cr950_site"
        ReferencedAttribute = "cr950_siteid"
        SchemaName = "cr950_site_project"
        DisplayName = "Site"
        Description = "Link project to work location"
        IsRequired = $false  # Some projects might span multiple sites
        CascadeDelete = "Restrict"
    },
    @{
        Number = 6
        ReferencingEntity = "cr950_resourceassignment"
        ReferencingAttribute = "cr950_project"
        ReferencedEntity = "cr950_projects"
        ReferencedAttribute = "cr950_projectsid"
        SchemaName = "cr950_project_resourceassignment"
        DisplayName = "Project"
        Description = "Link staffing to projects"
        IsRequired = $true
        CascadeDelete = "Cascade"  # Remove assignments if project deleted
    },
    @{
        Number = 7
        ReferencingEntity = "cr950_resourceassignment"
        ReferencingAttribute = "cr950_employee"
        ReferencedEntity = "cr950_employee"
        ReferencedAttribute = "cr950_employeeid"
        SchemaName = "cr950_employee_resourceassignment"
        DisplayName = "Employee"
        Description = "Link assignments to specific employees"
        IsRequired = $true
        CascadeDelete = "Restrict"  # Prevent deleting employee with active assignments
    },
    @{
        Number = 8
        ReferencingEntity = "cr950_equipment"
        ReferencingAttribute = "cr950_assignedto"
        ReferencedEntity = "cr950_employee"
        ReferencedAttribute = "cr950_employeeid"
        SchemaName = "cr950_employee_equipment_assignedto"
        DisplayName = "Assigned To"
        Description = "Track who currently has equipment (optional)"
        IsRequired = $false
        CascadeDelete = "RemoveLink"  # Clear assignment but keep equipment
    },
    @{
        Number = 9
        ReferencingEntity = "cr950_equipment"
        ReferencingAttribute = "cr950_currentproject"
        ReferencedEntity = "cr950_projects"
        ReferencedAttribute = "cr950_projectsid"
        SchemaName = "cr950_project_equipment_currentproject"
        DisplayName = "Current Project"
        Description = "Track equipment usage on projects (optional)"
        IsRequired = $false
        CascadeDelete = "RemoveLink"  # Clear assignment but keep equipment
    }
)

# Function to create a lookup relationship
function Add-LookupRelationship {
    param($Lookup)
    
    Write-Host "`n[$($Lookup.Number)/9] Creating: $($Lookup.ReferencingEntity).$($Lookup.ReferencingAttribute) → $($Lookup.ReferencedEntity)" -ForegroundColor Yellow
    Write-Host "    Schema Name: $($Lookup.SchemaName)" -ForegroundColor Gray
    Write-Host "    Display Name: $($Lookup.DisplayName)" -ForegroundColor Gray
    Write-Host "    Required: $($Lookup.IsRequired)" -ForegroundColor Gray
    Write-Host "    Cascade Delete: $($Lookup.CascadeDelete)" -ForegroundColor Gray
    
    # Build the lookup attribute definition
    $lookupAttribute = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.LookupAttributeMetadata"
        SchemaName = $Lookup.ReferencingAttribute
        DisplayName = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            LocalizedLabels = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    Label = $Lookup.DisplayName
                    LanguageCode = 1033
                }
            )
        }
        Description = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            LocalizedLabels = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    Label = $Lookup.Description
                    LanguageCode = 1033
                }
            )
        }
        RequiredLevel = @{
            Value = if ($Lookup.IsRequired) { "ApplicationRequired" } else { "None" }
            CanBeChanged = $true
            ManagedPropertyLogicalName = "canmodifyrequirementlevelsettings"
        }
        AttributeTypeName = @{
            Value = "LookupType"
        }
    } | ConvertTo-Json -Depth 10
    
    # Build the relationship definition
    $relationship = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata"
        SchemaName = $Lookup.SchemaName
        ReferencedEntity = $Lookup.ReferencedEntity
        ReferencedAttribute = $Lookup.ReferencedAttribute
        ReferencingEntity = $Lookup.ReferencingEntity
        CascadeConfiguration = @{
            Assign = "NoCascade"
            Delete = $Lookup.CascadeDelete
            Merge = "NoCascade"
            Reparent = "NoCascade"
            Share = "NoCascade"
            Unshare = "NoCascade"
        }
        AssociatedMenuConfiguration = @{
            Behavior = "UseCollectionName"
            Group = "Details"
            Label = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                LocalizedLabels = @(
                    @{
                        "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                        Label = $Lookup.DisplayName
                        LanguageCode = 1033
                    }
                )
            }
            Order = 10000
        }
        Lookup = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.LookupAttributeMetadata"
            SchemaName = $Lookup.ReferencingAttribute
            DisplayName = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                LocalizedLabels = @(
                    @{
                        "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                        Label = $Lookup.DisplayName
                        LanguageCode = 1033
                    }
                )
            }
        }
    } | ConvertTo-Json -Depth 10
    
    try {
        # Create the relationship (which also creates the lookup field)
        $url = "$($script:DataverseConfig.DataverseUrl)/api/data/$($script:DataverseConfig.ApiVersion)/RelationshipDefinitions"
        
        $response = Invoke-RestMethod `
            -Uri $url `
            -Headers $script:DataverseHeaders `
            -Method Post `
            -Body $relationship
        
        Write-Host "✅ Relationship created successfully!" -ForegroundColor Green
        
        # If relationship creation succeeded, the lookup field was created automatically
        Write-Host "   Lookup field: $($Lookup.ReferencingEntity).$($Lookup.ReferencingAttribute)" -ForegroundColor Green
        Write-Host "   Relationship: $($Lookup.SchemaName)" -ForegroundColor Green
        
        return $true
    }
    catch {
        $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
        $errorMessage = $errorDetails.error.message
        
        if ($errorMessage -like "*already exists*" -or $errorMessage -like "*duplicate*") {
            Write-Host "⚠️  Relationship already exists - skipping" -ForegroundColor Yellow
            return $true
        }
        else {
            Write-Host "❌ Failed to create relationship" -ForegroundColor Red
            Write-Host "   Error: $errorMessage" -ForegroundColor Red
            return $false
        }
    }
}

# Create all lookups
Write-Host "`nCreating 9 lookup relationships..." -ForegroundColor Cyan
Write-Host "This will establish the data model for v1.4.0.0`n" -ForegroundColor Cyan

$successCount = 0
$failCount = 0
$skipCount = 0

foreach ($lookup in $lookups) {
    $result = Add-LookupRelationship -Lookup $lookup
    
    if ($result) {
        $successCount++
    }
    else {
        $failCount++
    }
    
    Start-Sleep -Milliseconds 500  # Brief pause between API calls
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Lookup Relationships Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Created: $successCount" -ForegroundColor Green
Write-Host "❌ Failed: $failCount" -ForegroundColor Red
Write-Host "`nTotal: 9 relationships" -ForegroundColor Cyan

if ($failCount -eq 0) {
    Write-Host "`n🎉 All lookups created successfully!" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Verify relationships in Power Apps maker portal" -ForegroundColor Gray
    Write-Host "2. Test cascade behaviors" -ForegroundColor Gray
    Write-Host "3. Add lookup fields to forms" -ForegroundColor Gray
    Write-Host "4. Create views using new relationships" -ForegroundColor Gray
}
else {
    Write-Host "`n⚠️  Some lookups failed. Review errors above." -ForegroundColor Yellow
    Write-Host "Manually create failed lookups in Power Apps maker portal." -ForegroundColor Gray
}

Write-Host "`n✅ Script complete!`n" -ForegroundColor Green
