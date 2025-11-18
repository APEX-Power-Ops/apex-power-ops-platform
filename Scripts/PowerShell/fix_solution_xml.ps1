# Fix Solution.xml to include all root components

$solutionPath = "C:\RESA_Power_Build\RESAPowerProjectTracker\RESAPowerProjectTracker\src\Other\Solution.xml"
$customizationsPath = "C:\RESA_Power_Build\RESAPowerProjectTracker\RESAPowerProjectTracker\src\Other\Customizations.xml"

Write-Host "Reading customizations to identify components..." -ForegroundColor Cyan

# Read the customizations file to find all tables and choice fields
[xml]$customizations = Get-Content $customizationsPath

# Extract table names
$tables = $customizations.ImportExportXml.Entities.Entity | ForEach-Object { $_.EntityInfo.entity.Name }
Write-Host "Found $($tables.Count) tables" -ForegroundColor Green

# Extract global choice fields  
$optionsets = $customizations.ImportExportXml.optionsets.optionset | ForEach-Object { $_.Name }
Write-Host "Found $($optionsets.Count) global option sets" -ForegroundColor Green

# Read solution XML
[xml]$solution = Get-Content $solutionPath

# Create RootComponents node
$rootComponentsNode = $solution.ImportExportXml.SolutionManifest.SelectSingleNode("RootComponents")

# Remove existing empty node
$solution.ImportExportXml.SolutionManifest.RemoveChild($rootComponentsNode) | Out-Null

# Create new RootComponents with content
$newRootComponents = $solution.CreateElement("RootComponents")

# Add each table as root component (type=1 for entity)
foreach ($table in $tables) {
    $component = $solution.CreateElement("RootComponent")
    $component.SetAttribute("type", "1")
    $component.SetAttribute("schemaName", $table)
    $component.SetAttribute("behavior", "0")
    $newRootComponents.AppendChild($component) | Out-Null
}

# Add each global option set as root component (type=9 for optionset)
foreach ($optionset in $optionsets) {
    $component = $solution.CreateElement("RootComponent")
    $component.SetAttribute("type", "9")
    $component.SetAttribute("schemaName", $optionset)
    $component.SetAttribute("behavior", "0")
    $newRootComponents.AppendChild($component) | Out-Null
}

# Insert the new RootComponents node
$missingDeps = $solution.ImportExportXml.SolutionManifest.SelectSingleNode("MissingDependencies")
$solution.ImportExportXml.SolutionManifest.InsertBefore($newRootComponents, $missingDeps) | Out-Null

# Save the updated solution file
$solution.Save($solutionPath)

Write-Host "`nSolution.xml updated with $($tables.Count + $optionsets.Count) root components" -ForegroundColor Green
Write-Host "- $($tables.Count) tables" -ForegroundColor White
Write-Host "- $($optionsets.Count) global choice fields" -ForegroundColor White

Write-Host "`nTables included:" -ForegroundColor Cyan
$tables | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }

Write-Host "`nGlobal choices included:" -ForegroundColor Cyan
$optionsets | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
