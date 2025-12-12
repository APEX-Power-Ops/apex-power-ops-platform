# RESA POWER - POWER PLATFORM CLI BUILD SCRIPT
## Automated Schema Creation Using pac CLI

**Generated:** November 10, 2025  
**Purpose:** Automate creation of Scope_Financial_Config and modifications to existing tables

---

## 📋 PREREQUISITES

### **Install Power Platform CLI**

**Windows (PowerShell):**
```powershell
# Install via winget
winget install --id Microsoft.PowerPlatformCLI

# Or via MSI installer
# Download from: https://aka.ms/PowerAppsCLI
```

**macOS:**
```bash
# Install via Homebrew
brew tap microsoft/powerplatform-cli  
brew install powerplatform-cli
```

**Verify Installation:**
```bash
pac --version
```

### **Authenticate to Your Environment**

```bash
# Connect to your environment
pac auth create --environment "https://orgXXXXXXXX.crm.dynamics.com"

# List available environments
pac env list

# Select your RESA Power TEST environment
pac env select --environment "RESA Power TEST"
```

---

## 🚀 AUTOMATED BUILD SCRIPTS

### **Script 1: Create Scope_Financial_Config Table**

Save as: `create_financial_config.ps1` (PowerShell) or `.sh` (Bash)

```powershell
#################################################################
# CREATE SCOPE FINANCIAL CONFIG TABLE
#################################################################

Write-Host "Creating Scope Financial Config table..." -ForegroundColor Cyan

# Create the table
pac table create `
  --display-name "Scope Financial Config" `
  --plural-name "Scope Financial Configs" `
  --description "Financial rate configuration for scopes" `
  --schema-name "ScopeFinancialConfig" `
  --ownership "UserOwned" `
  --has-activities true `
  --has-notes true

Write-Host "✓ Table created" -ForegroundColor Green

# Get the table logical name (will be cr950_scopefinancialconfig or similar)
$tableName = "cr950_scopefinancialconfig"

#################################################################
# ADD RELATIONSHIP COLUMN
#################################################################

Write-Host "Adding Scope lookup..." -ForegroundColor Cyan

pac column create `
  --table-name $tableName `
  --display-name "Scope" `
  --name "Scope" `
  --type "Lookup" `
  --related-table "cr950_scopes" `
  --required true

Write-Host "✓ Scope lookup added" -ForegroundColor Green

#################################################################
# ADD LABOR RATE COLUMNS (10 fields)
#################################################################

Write-Host "Adding labor rate columns..." -ForegroundColor Cyan

$laborRates = @(
    "Labor Rate",
    "Daily Commute Rate",
    "Mobilization Rate",
    "PM Office Rate",
    "Report Rate",
    "Travel Hours Rate",
    "Onsite LOTO Rate",
    "Onsite Miscellaneous Rate",
    "Onsite PM Rate",
    "Final Report Rate"
)

foreach ($rate in $laborRates) {
    $columnName = $rate -replace " ", ""
    
    pac column create `
      --table-name $tableName `
      --display-name $rate `
      --name $columnName `
      --type "Currency" `
      --precision 2 `
      --min-value 0 `
      --secured true
    
    Write-Host "  ✓ $rate" -ForegroundColor Gray
}

Write-Host "✓ All labor rate columns added" -ForegroundColor Green

#################################################################
# ADD PERCENTAGE COLUMNS (8 fields)
#################################################################

Write-Host "Adding percentage columns..." -ForegroundColor Cyan

$percentages = @(
    "Daily Commute Percent",
    "Mobilization Percent",
    "Onsite PM Percent",
    "Report Percent",
    "Travel Percent",
    "Onsite LOTO Percent",
    "Onsite Miscellaneous Percent",
    "PM Office Percent"
)

foreach ($pct in $percentages) {
    $columnName = $pct -replace " ", ""
    
    pac column create `
      --table-name $tableName `
      --display-name $pct `
      --name $columnName `
      --type "Decimal" `
      --precision 2 `
      --min-value 0 `
      --max-value 1 `
      --secured true
    
    Write-Host "  ✓ $pct" -ForegroundColor Gray
}

Write-Host "✓ All percentage columns added" -ForegroundColor Green

#################################################################
# ADD FIXED COST COLUMNS (2 fields)
#################################################################

Write-Host "Adding fixed cost columns..." -ForegroundColor Cyan

pac column create `
  --table-name $tableName `
  --display-name "Fixed Cost Travel" `
  --name "FixedCostTravel" `
  --type "Currency" `
  --precision 2 `
  --min-value 0 `
  --secured true

pac column create `
  --table-name $tableName `
  --display-name "Fixed Cost M&E" `
  --name "FixedCostME" `
  --type "Currency" `
  --precision 2 `
  --min-value 0 `
  --secured true

Write-Host "✓ Fixed cost columns added" -ForegroundColor Green

#################################################################
# ADD SCOPE MULTIPLIER
#################################################################

Write-Host "Adding Scope Multiplier..." -ForegroundColor Cyan

pac column create `
  --table-name $tableName `
  --display-name "Scope Multiplier" `
  --name "ScopeMultiplier" `
  --type "Decimal" `
  --precision 2 `
  --min-value 0 `
  --max-value 10 `
  --default-value 1.0 `
  --required true `
  --secured true

Write-Host "✓ Scope Multiplier added" -ForegroundColor Green

#################################################################
# ADD SOURCE ESTIMATE FIELD
#################################################################

Write-Host "Adding Source Estimate field..." -ForegroundColor Cyan

pac column create `
  --table-name $tableName `
  --display-name "Source Estimate" `
  --name "SourceEstimate" `
  --type "Text" `
  --max-length 200

Write-Host "✓ Source Estimate added" -ForegroundColor Green

#################################################################
# ADD CALCULATED COLUMNS
#################################################################

Write-Host "Adding calculated columns..." -ForegroundColor Cyan

# Note: Calculated column formulas must be added via UI
# CLI doesn't support formula syntax yet
# Manual step required after script runs

Write-Host "⚠️  Calculated columns must be added manually:" -ForegroundColor Yellow
Write-Host "   1. Total Percent Markup" -ForegroundColor Gray
Write-Host "   2. Blended Labor Rate" -ForegroundColor Gray
Write-Host "   3. Fixed Cost Per Hour" -ForegroundColor Gray
Write-Host "   4. Total Revenue Per Hour" -ForegroundColor Gray
Write-Host "   5. Break Even Hours" -ForegroundColor Gray
Write-Host "   6. Margin Percent" -ForegroundColor Gray

#################################################################
# COMPLETE
#################################################################

Write-Host ""
Write-Host "✅ SCOPE FINANCIAL CONFIG TABLE CREATED!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Add calculated columns manually (see formulas in master spec)"
Write-Host "2. Add Financial Config lookup to Scopes table"
Write-Host "3. Configure field-level security profiles"
Write-Host "4. Test with sample data"
```

---

### **Script 2: Add Task Lookup to Apparatus**

Save as: `add_task_lookup.ps1`

```powershell
Write-Host "Adding Task lookup to Apparatus table..." -ForegroundColor Cyan

pac column create `
  --table-name "cr950_apparatus" `
  --display-name "Task" `
  --name "Task" `
  --type "Lookup" `
  --related-table "cr950_tasks" `
  --required true `
  --delete-behavior "Restrict" `
  --assign-behavior "CascadeAll" `
  --share-behavior "CascadeAll" `
  --reparent-behavior "CascadeAll"

Write-Host "✓ Task lookup added to Apparatus" -ForegroundColor Green
```

---

### **Script 3: Add Date Columns to Apparatus**

Save as: `add_apparatus_dates.ps1`

```powershell
Write-Host "Adding date columns to Apparatus..." -ForegroundColor Cyan

# Date Started
pac column create `
  --table-name "cr950_apparatus" `
  --display-name "Date Started" `
  --name "DateStarted" `
  --type "DateTime" `
  --format "DateOnly" `
  --behavior "UserLocal"

# Date Completed
pac column create `
  --table-name "cr950_apparatus" `
  --display-name "Date Completed" `
  --name "DateCompleted" `
  --type "DateTime" `
  --format "DateOnly" `
  --behavior "UserLocal"

Write-Host "✓ Date columns added" -ForegroundColor Green
```

---

### **Script 4: Add Earned Revenue Fields to Apparatus**

Save as: `add_apparatus_revenue_fields.ps1`

```powershell
Write-Host "Adding earned revenue calculation fields to Apparatus..." -ForegroundColor Cyan

$tableName = "cr950_apparatus"

# Base Labor
pac column create --table-name $tableName --display-name "Base Labor $" --name "BaseLaborAmount" --type "Currency" --precision 2
Write-Host "  ✓ Base Labor $" -ForegroundColor Gray

# Time Adder Hours (Decimal)
$hourFields = @("Commute Hrs", "PM Hrs", "Report Hrs", "Travel Hrs", "Final Hrs")
foreach ($field in $hourFields) {
    $name = $field -replace " ", ""
    pac column create --table-name $tableName --display-name $field --name $name --type "Decimal" --precision 2
    Write-Host "  ✓ $field" -ForegroundColor Gray
}

# Time Adder Amounts (Currency)
$amountFields = @("Commute $", "PM $", "Report $", "Travel $", "Final $")
foreach ($field in $amountFields) {
    $name = ($field -replace " ", "") -replace '\$', 'Amount'
    pac column create --table-name $tableName --display-name $field --name $name --type "Currency" --precision 2
    Write-Host "  ✓ $field" -ForegroundColor Gray
}

# Fixed Costs
pac column create --table-name $tableName --display-name "Travel Fixed $" --name "TravelFixedAmount" --type "Currency" --precision 2
pac column create --table-name $tableName --display-name "ME Fixed $" --name "MEFixedAmount" --type "Currency" --precision 2
Write-Host "  ✓ Fixed cost fields" -ForegroundColor Gray

# Totals
pac column create --table-name $tableName --display-name "Total Variable $" --name "TotalVariableAmount" --type "Currency" --precision 2
pac column create --table-name $tableName --display-name "Total Fixed $" --name "TotalFixedAmount" --type "Currency" --precision 2
pac column create --table-name $tableName --display-name "Subtotal $" --name "SubtotalAmount" --type "Currency" --precision 2
pac column create --table-name $tableName --display-name "Total Billable $" --name "TotalBillableAmount" --type "Currency" --precision 2
Write-Host "  ✓ Total fields" -ForegroundColor Gray

# KEY METRIC
pac column create --table-name $tableName --display-name "Earned Revenue" --name "EarnedRevenue" --type "Currency" --precision 2 --secured true
Write-Host "  ✓ Earned Revenue (KEY METRIC)" -ForegroundColor Green

Write-Host "✓ All earned revenue fields added" -ForegroundColor Green
```

---

### **Script 5: Add Calculated Columns to Apparatus**

Save as: `add_apparatus_calculated.ps1`

```powershell
Write-Host "Adding calculated columns to Apparatus..." -ForegroundColor Cyan

# Note: These formulas must be entered via UI
# CLI creates the columns, formulas added manually

Write-Host "Creating calculated column placeholders..." -ForegroundColor Yellow
Write-Host "⚠️  Formulas must be added manually after creation" -ForegroundColor Yellow

Write-Host ""
Write-Host "Calculated columns to add via UI:" -ForegroundColor Cyan
Write-Host "1. Remaining Hours = [Apparatus Hours] - [Actual Hours]"
Write-Host "2. Percent Complete = If([Apparatus Hours] > 0, ([Actual Hours] / [Apparatus Hours]) * 100, 0)"
Write-Host "3. Days Since Completed = If(IsBlank([Date Completed]), 0, DateDiff([Date Completed], Today(), Days))"
Write-Host "4. Is Overdue = And(Not(IsBlank([Date Due])), [Date Due] < Today(), [Status] <> 'Complete')"
Write-Host "5. Revenue Per Hour = If([Apparatus Hours] > 0, [Earned Revenue] / [Apparatus Hours], 0)"
```

---

## 📖 USAGE INSTRUCTIONS

### **Step 1: Set Up Environment**

```powershell
# Open PowerShell as Administrator
# Navigate to your working directory
cd C:\RESA_Power_Build

# Authenticate
pac auth create

# Select environment
pac env select --environment "RESA Power TEST"
```

### **Step 2: Run Scripts in Order**

```powershell
# Script 1: Create Financial Config table (15 minutes)
.\create_financial_config.ps1

# Script 2: Add Task lookup (2 minutes)
.\add_task_lookup.ps1

# Script 3: Add dates (2 minutes)
.\add_apparatus_dates.ps1

# Script 4: Add revenue fields (5 minutes)
.\add_apparatus_revenue_fields.ps1

# Script 5: Review calculated column formulas
.\add_apparatus_calculated.ps1
```

### **Step 3: Manual Steps After Scripts**

1. **Add calculated columns** to Scope_Financial_Config (via UI)
2. **Add calculated columns** to Apparatus (via UI)
3. **Add rollup columns** to Tasks, Scopes, Projects (via UI - CLI doesn't support rollups yet)
4. **Configure field-level security** profiles
5. **Test with sample data**

---

## ⚠️ CLI LIMITATIONS

### **What CLI CAN Do:**
✅ Create tables  
✅ Add basic columns (text, number, currency, decimal, date)  
✅ Add lookup relationships  
✅ Set min/max values  
✅ Set precision  
✅ Enable field security flag  

### **What CLI CANNOT Do (Yet):**
❌ Add calculated columns with formulas  
❌ Add rollup columns with aggregations  
❌ Configure business rules  
❌ Set up cascade behaviors (limited support)  
❌ Configure global choice sync  

### **Workaround:**
Use CLI for bulk creation, then use UI for advanced features (calculated, rollup, business rules).

---

## 🔄 ALTERNATIVE: Python Script Using Dataverse Web API

If CLI doesn't work, I can generate Python script instead:

```python
# Uses requests library to call Dataverse Web API
# Can create tables, columns, relationships
# More control than CLI
# Requires: pip install requests msal
```

**Want me to generate the Python version?**

---

## ✅ VERIFICATION CHECKLIST

After running scripts, verify:

```
□ Scope_Financial_Config table exists
□ Has all 20+ rate/percentage columns
□ Scope lookup configured
□ All fields marked as secured

□ Apparatus table has Task lookup
□ Apparatus has Date Started/Completed
□ Apparatus has 17 earned revenue fields
□ Earned Revenue field marked as secured

□ No errors in solution checker
□ Can create test record in each table
□ Relationships navigate correctly
```

---

## 🆘 TROUBLESHOOTING

### **Error: "Table not found"**
```powershell
# List all tables to find correct logical name
pac table list

# Use the exact logical name from output
```

### **Error: "Authentication failed"**
```powershell
# Clear auth and re-authenticate
pac auth clear
pac auth create
```

### **Error: "Column already exists"**
```powershell
# Skip that column, continue with others
# Or delete column first:
pac column delete --table-name "tablename" --column-name "columnname"
```

### **Script runs but nothing created:**
- Check you're in correct environment
- Verify solution context
- Check security permissions (need System Administrator role)

---

## 📞 SUPPORT

If CLI approach doesn't work:
1. We can use Python + Dataverse Web API instead
2. We can use detailed manual UI guide
3. We can try solution import approach
4. We can do hybrid (some CLI, some manual)

**Let me know which approach works best!**
