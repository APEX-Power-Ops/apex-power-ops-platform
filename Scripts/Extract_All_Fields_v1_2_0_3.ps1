# Complete Field Extraction Script for v1.2.0.3
# Extracts ALL custom fields from customizations.xml with full details

$xmlPath = "C:\RESA_Power_Build\Solution_Exports\v1.2.0.3\customizations.xml"
$outputPath = "C:\RESA_Power_Build\Documentation\05_Reviews_Analysis\FIELD_EXTRACTION_RAW.txt"

Write-Output "Loading v1.2.0.3 customizations.xml..."
[xml]$xml = Get-Content -Path $xmlPath -Encoding UTF8

Write-Output "Extracting entities..."
$entities = $xml.ImportExportXml.Entities.Entity

$output = @()
$output += "=" * 80
$output += "v1.2.0.3 COMPLETE FIELD EXTRACTION"
$output += "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$output += "=" * 80
$output += ""

$totalFields = 0

foreach ($entity in $entities) {
    $entityName = $entity.Name.InnerText
    $output += ""
    $output += "=" * 80
    $output += "ENTITY: $entityName"
    $output += "=" * 80
    $output += ""
    
    # Get all custom attributes (cr950_ prefix)
    $attributes = $entity.EntityInfo.entity.attributes.attribute | Where-Object { 
        $_.LogicalName -like 'cr950_*' 
    }
    
    if ($attributes) {
        $fieldCount = @($attributes).Count
        $totalFields += $fieldCount
        $output += "Total Custom Fields: $fieldCount"
        $output += ""
        
        $fieldNum = 1
        foreach ($attr in $attributes) {
            $output += "-" * 80
            $output += "FIELD #$fieldNum : $($attr.LogicalName)"
            $output += "-" * 80
            
            # Display Name
            if ($attr.displaynames.displayname) {
                $displayName = $attr.displaynames.displayname | Where-Object { $_.languagecode -eq '1033' }
                if ($displayName) {
                    $output += "Display Name: $($displayName.description)"
                }
            }
            
            # Description
            if ($attr.Descriptions.Description) {
                $desc = $attr.Descriptions.Description | Where-Object { $_.languagecode -eq '1033' }
                if ($desc -and $desc.description) {
                    $output += "Description: $($desc.description)"
                }
            }
            
            # Type
            $output += "Type: $($attr.Type)"
            
            # Required Level
            if ($attr.RequiredLevel) {
                $output += "Required: $($attr.RequiredLevel)"
            }
            
            # Format (for specific types)
            if ($attr.Format) {
                $output += "Format: $($attr.Format)"
            }
            
            # Precision (for decimal/money)
            if ($attr.Precision) {
                $output += "Precision: $($attr.Precision)"
            }
            
            # Min/Max (for number/decimal)
            if ($attr.MinValue) {
                $output += "Min Value: $($attr.MinValue)"
            }
            if ($attr.MaxValue) {
                $output += "Max Value: $($attr.MaxValue)"
            }
            
            # Max Length (for string)
            if ($attr.MaxLength) {
                $output += "Max Length: $($attr.MaxLength)"
            }
            
            # IME Mode (for string)
            if ($attr.ImeMode) {
                $output += "IME Mode: $($attr.ImeMode)"
            }
            
            # Lookup Target (for lookup fields)
            if ($attr.LookupTargets) {
                $output += "Lookup Target: $($attr.LookupTargets)"
            }
            if ($attr.Target) {
                $output += "Target Entity: $($attr.Target)"
            }
            
            # Option Set (for picklist/choice)
            if ($attr.optionset) {
                $output += "Option Set:"
                foreach ($option in $attr.optionset.Options.option) {
                    $optLabel = $option.labels.label | Where-Object { $_.languagecode -eq '1033' }
                    if ($optLabel) {
                        $output += "  - $($option.value): $($optLabel.description)"
                    }
                }
            }
            
            # Calculated Field
            if ($attr.IsCustomizable -eq 'false' -or $attr.SourceType -eq '1') {
                $output += "Calculated: Yes"
            }
            
            # Formula (if present)
            if ($attr.FormulaDefinition) {
                $output += "Formula: $($attr.FormulaDefinition)"
            }
            
            # Rollup (if present)
            if ($attr.IsRollupField -eq 'true') {
                $output += "Rollup: Yes"
                if ($attr.RollupState) {
                    $output += "Rollup State: $($attr.RollupState)"
                }
            }
            
            $output += ""
            $fieldNum++
        }
    } else {
        $output += "No custom fields found."
        $output += ""
    }
}

$output += ""
$output += "=" * 80
$output += "SUMMARY"
$output += "=" * 80
$output += "Total Entities: $($entities.Count)"
$output += "Total Custom Fields: $totalFields"
$output += ""

# Write to file
$output | Out-File -FilePath $outputPath -Encoding UTF8

Write-Output ""
Write-Output "Extraction complete!"
Write-Output "Total Entities: $($entities.Count)"
Write-Output "Total Custom Fields: $totalFields"
Write-Output "Output saved to: $outputPath"
Write-Output ""
