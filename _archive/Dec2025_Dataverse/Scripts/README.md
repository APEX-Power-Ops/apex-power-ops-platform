# RESA Power Build - Scripts Directory
**Last Updated**: November 23, 2025

## 📁 Folder Structure

### **PowerShell/**
Organized into three categories:

#### **Active/** - Current Use Scripts
Scripts actively used in current development:
- \Test-DataverseConnection.ps1\ - Verify Dataverse API connectivity
- \Test-MCPAuthentication.ps1\ - Verify MCP server authentication  
- \Update-Documentation-Environments.ps1\ - Batch documentation updater
- \Verify-ApparatusDateFields.ps1\ - Date field verification tool
- \Update-ProjectContext.ps1\ - Update PROJECT_CONTEXT.json
- \Field_Creation_Manual_Guide.ps1\ - Field creation reference
- \Fix-API-Permissions-Guide.ps1\ - API permission troubleshooting
- \Import-DataverseTables.ps1\ - Data import utility
- \Implement-KPIFields.ps1\ - KPI field implementation

#### **Archive/** - Completed Tasks
Scripts from finished implementation tasks:
- \Add-V1.4.0.0-Lookups.ps1\ - v1.4.0.0 lookup relationships (COMPLETED)
- \Add-DateTrackingFields.ps1\ - Date tracking fields (COMPLETED)
- \Create-FinancialSummaryTables.ps1\ - Financial tables (COMPLETED)
- \Create-NewDataverseTables.ps1\ - 6 new tables (COMPLETED)
- \Add_Future_Proofing_Fields.ps1\ - Future proofing (COMPLETED)
- \Delete-RollupFieldContainers.ps1\ - Cleanup utility (COMPLETED)
- Others...

#### **Root Level** - Core Libraries
- \Dataverse-Functions.ps1\ - Shared PowerShell functions library

#### **Rollup Scripts/** - Upcoming Implementation
Rollup field implementation scripts for v1.5.0.0:
- \Add-RollupFields-FullyConfigured.ps1\
- \Add-RollupFields.ps1\
- \Create-RollupFields-Complete.ps1\
- \Create-RollupFields-Guide.md\
- \KPI_FIELDS_README.md\

### **Python/**
- \migrate_data.py\ - Data migration utility

### **Archived/**
Old scripts from previous iterations

---

## 🔧 Usage Guidelines

### **Active Scripts**
- All scripts use current environment: \org99cd6c6e.crm.dynamics.com\
- All scripts use current credentials: RESA-Dev-MCP-Access
- Test scripts before running against live data
- Update headers with last tested date

### **Archive Scripts**
- Preserved for reference and rollback
- May contain outdated environment URLs
- Do not use without reviewing/updating

### **Adding New Scripts**
1. Place in \Active/\ if for current work
2. Place in \Archive/\ if task is complete
3. Add proper header with purpose, date, prerequisites
4. Update this README if adding new categories

---

## 📋 Script Maintenance

### **When to Archive**
- Task completed and verified in production
- Script no longer needed for current development
- Superseded by newer implementation

### **When to Keep Active**
- Used for ongoing development
- Part of testing/verification workflow
- Reusable utility script

### **Cleanup Schedule**
- Monthly: Review Active scripts
- Quarterly: Review Archive (delete if >6 months old)
- Update README with organizational changes

---

## 🚀 Current Environment (Nov 23, 2025)

**Dataverse Environment**:
- URL: https://org99cd6c6e.crm.dynamics.com
- Org ID: e550d661-edc7-f011-8729-000d3a33a005
- Tenant: 270d5723-4b30-4f3b-b9cb-6527be741b42
- Client ID: 9df3350f-b3b4-47c4-97b5-499a8b02acc7
- App: RESA-Dev-MCP-Access

**Solution Version**: v1.4.0.0 (16 tables, 291+ fields)

---

**Created**: November 23, 2025  
**Next Review**: December 23, 2025
