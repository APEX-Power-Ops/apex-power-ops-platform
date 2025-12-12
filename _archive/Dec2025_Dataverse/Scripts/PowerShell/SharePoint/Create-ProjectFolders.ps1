<#
.SYNOPSIS
    Creates standardized project folder structure in SharePoint
    
.DESCRIPTION
    This script creates the standard project folder hierarchy in SharePoint
    when a new project is initiated. Can be called from Power Automate
    via HTTP trigger or run directly with parameters.
    
.PARAMETER SiteUrl
    SharePoint site URL
    
.PARAMETER ProjectNumber
    Project number for folder naming
    
.PARAMETER ProjectName
    Project name (optional, for folder description)
    
.EXAMPLE
    .\Create-ProjectFolders.ps1 -SiteUrl "https://tenant.sharepoint.com/sites/PhoenixProjects" -ProjectNumber "434469"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$SiteUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$ProjectNumber,
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectName = ""
)

# Install PnP.PowerShell if not present
# Install-Module -Name PnP.PowerShell -Scope CurrentUser -Force

# Standard project folder structure
$FolderStructure = @(
    "/Projects/$ProjectNumber",
    "/Projects/$ProjectNumber/01_Estimator",
    "/Projects/$ProjectNumber/02_Quotes",
    "/Projects/$ProjectNumber/03_Contracts",
    "/Projects/$ProjectNumber/04_Field_Data",
    "/Projects/$ProjectNumber/04_Field_Data/Photos",
    "/Projects/$ProjectNumber/04_Field_Data/Test_Reports",
    "/Projects/$ProjectNumber/04_Field_Data/DTAX_Files",
    "/Projects/$ProjectNumber/05_Datasheets",
    "/Projects/$ProjectNumber/06_Reports",
    "/Projects/$ProjectNumber/06_Reports/Draft",
    "/Projects/$ProjectNumber/06_Reports/Final",
    "/Projects/$ProjectNumber/07_Invoicing",
    "/Projects/$ProjectNumber/08_Correspondence"
)

function New-ProjectFolderStructure {
    param(
        [string]$SiteUrl,
        [string]$ProjectNumber,
        [string]$ProjectName
    )
    
    Write-Host "Creating folder structure for project: $ProjectNumber" -ForegroundColor Cyan
    
    try {
        # Connect to SharePoint (will prompt for auth or use cached credentials)
        Connect-PnPOnline -Url $SiteUrl -Interactive
        
        $createdFolders = @()
        $errors = @()
        
        foreach ($folder in $FolderStructure) {
            try {
                # Check if folder exists
                $existingFolder = Get-PnPFolder -Url "Shared Documents$folder" -ErrorAction SilentlyContinue
                
                if ($existingFolder) {
                    Write-Host "  ⚠️ Already exists: $folder" -ForegroundColor Yellow
                } else {
                    # Create folder
                    Add-PnPFolder -Name (Split-Path $folder -Leaf) -Folder "Shared Documents$(Split-Path $folder -Parent)"
                    Write-Host "  ✅ Created: $folder" -ForegroundColor Green
                    $createdFolders += $folder
                }
            }
            catch {
                # If parent doesn't exist, create recursively
                $parts = $folder.TrimStart('/').Split('/')
                $currentPath = ""
                
                foreach ($part in $parts) {
                    $currentPath = "$currentPath/$part"
                    try {
                        $existingFolder = Get-PnPFolder -Url "Shared Documents$currentPath" -ErrorAction SilentlyContinue
                        if (-not $existingFolder) {
                            Add-PnPFolder -Name $part -Folder "Shared Documents$(Split-Path $currentPath -Parent)"
                            Write-Host "  ✅ Created: $currentPath" -ForegroundColor Green
                            $createdFolders += $currentPath
                        }
                    }
                    catch {
                        Write-Host "  ❌ Error creating $currentPath : $_" -ForegroundColor Red
                        $errors += $currentPath
                    }
                }
            }
        }
        
        # Return result object
        $result = @{
            ProjectNumber = $ProjectNumber
            SiteUrl = $SiteUrl
            FoldersCreated = $createdFolders.Count
            Errors = $errors.Count
            ProjectFolderUrl = "$SiteUrl/Shared Documents/Projects/$ProjectNumber"
            Success = ($errors.Count -eq 0)
        }
        
        Write-Host "`n✅ Folder structure complete!" -ForegroundColor Green
        Write-Host "   Project folder: $($result.ProjectFolderUrl)" -ForegroundColor Cyan
        
        return $result
    }
    catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
        throw
    }
    finally {
        Disconnect-PnPOnline -ErrorAction SilentlyContinue
    }
}

# Alternative: Use Graph API (for Power Automate HTTP action)
function New-ProjectFolderStructure-Graph {
    param(
        [string]$SiteId,
        [string]$DriveId,
        [string]$ProjectNumber,
        [string]$AccessToken
    )
    
    $headers = @{
        "Authorization" = "Bearer $AccessToken"
        "Content-Type" = "application/json"
    }
    
    $baseUrl = "https://graph.microsoft.com/v1.0/sites/$SiteId/drives/$DriveId/root"
    
    foreach ($folder in $FolderStructure) {
        $folderPath = $folder.TrimStart('/')
        
        try {
            $body = @{
                "name" = Split-Path $folderPath -Leaf
                "folder" = @{}
                "@microsoft.graph.conflictBehavior" = "fail"
            } | ConvertTo-Json
            
            $parentPath = Split-Path $folderPath -Parent
            if ($parentPath) {
                $url = "$baseUrl`:/$parentPath`:/children"
            } else {
                $url = "$baseUrl/children"
            }
            
            Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body
            Write-Host "  ✅ Created: $folder" -ForegroundColor Green
        }
        catch {
            if ($_.Exception.Response.StatusCode -eq 409) {
                Write-Host "  ⚠️ Already exists: $folder" -ForegroundColor Yellow
            } else {
                Write-Host "  ❌ Error: $_" -ForegroundColor Red
            }
        }
    }
}

# Execute if run directly
if ($SiteUrl -and $ProjectNumber) {
    New-ProjectFolderStructure -SiteUrl $SiteUrl -ProjectNumber $ProjectNumber -ProjectName $ProjectName
}
