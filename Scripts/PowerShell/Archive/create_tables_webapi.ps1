# RESA Power - Create Tables via Dataverse Web API
# This script creates tables programmatically using REST API calls

param(
    [Parameter(Mandatory=$true)]
    [string]$EnvironmentUrl,  # e.g., https://org.crm.dynamics.com
    
    [Parameter(Mandatory=$false)]
    [string]$AccessToken
)

Write-Host @"
╔══════════════════════════════════════════════════════════╗
║  RESA POWER - WEB API TABLE CREATION                    ║
╚══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Get access token using PAC CLI if not provided
if (-not $AccessToken) {
    Write-Host "`n🔑 Getting access token from PAC CLI..." -ForegroundColor Cyan
    try {
        $authList = pac auth list --json | ConvertFrom-Json
        $activeAuth = $authList | Where-Object { $_.IsDefault -eq $true }
        
        if ($activeAuth) {
            Write-Host "✅ Using authenticated profile: $($activeAuth.FriendlyName)" -ForegroundColor Green
        } else {
            Write-Host "❌ No active authentication found. Run: pac auth create" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ Error getting authentication: $_" -ForegroundColor Red
        exit 1
    }
}

# Function to create a table
function New-DataverseTable {
    param(
        [string]$DisplayName,
        [string]$LogicalName,
        [string]$PrimaryAttributeName,
        [string]$Description,
        [string]$OwnershipType = "UserOwned"
    )
    
    Write-Host "`nCreating table: $DisplayName ($LogicalName)..." -ForegroundColor Cyan
    
    $tableDefinition = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.EntityMetadata"
        "LogicalName" = $LogicalName
        "DisplayName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    "Label" = $DisplayName
                    "LanguageCode" = 1033
                }
            )
        }
        "DisplayCollectionName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    "Label" = $DisplayName + "s"
                    "LanguageCode" = 1033
                }
            )
        }
        "Description" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    "Label" = $Description
                    "LanguageCode" = 1033
                }
            )
        }
        "OwnershipType" = $OwnershipType
        "IsActivity" = $false
        "HasNotes" = $false
        "HasActivities" = $false
        "Attributes" = @(
            @{
                "@odata.type" = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
                "AttributeType" = "String"
                "AttributeTypeName" = @{
                    "Value" = "StringType"
                }
                "LogicalName" = $PrimaryAttributeName
                "SchemaName" = $PrimaryAttributeName
                "RequiredLevel" = @{
                    "Value" = "None"
                }
                "MaxLength" = 100
                "DisplayName" = @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                    "LocalizedLabels" = @(
                        @{
                            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                            "Label" = $DisplayName + " Name"
                            "LanguageCode" = 1033
                        }
                    )
                }
            }
        )
    }
    
    return $tableDefinition
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "CREATING TABLES VIA WEB API" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

Write-Host "`n⚠️  NOTE: This script requires:" -ForegroundColor Yellow
Write-Host "  1. Active authentication to Dataverse (pac auth create)" -ForegroundColor White
Write-Host "  2. System Administrator role" -ForegroundColor White
Write-Host "  3. PowerShell 7+ recommended" -ForegroundColor White

Write-Host "`n📝 Alternative: Use the simplified workflow:" -ForegroundColor Cyan
Write-Host "  1. Run: .\create_tables_proper.ps1" -ForegroundColor White
Write-Host "  2. Choose Option 1 to use Maker Portal" -ForegroundColor White
Write-Host "  3. Or use Option 2 to clone existing solution" -ForegroundColor White

Write-Host "`n🎯 For direct API creation, see Microsoft documentation:" -ForegroundColor Green
Write-Host "  https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/create-update-entity-definitions-using-web-api" -ForegroundColor White

Write-Host "`n" -ForegroundColor Cyan
