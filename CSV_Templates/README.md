# CSV Import Templates

## Templates (Import Order)

1. `00_Locations_Template.csv` - Business units/locations
2. `01_Projects_Template.csv` - Project records
3. `02_Scopes_Template.csv` - Project scopes (with NETA_Standard)
4. `03_Tasks_Template.csv` - REFERENCE ONLY (manual creation)
5. `04_Apparatus_Template.csv` - Individual equipment
6. `04_Apparatus_Type_Master.csv` - Equipment types (import first!)
7. `05_Scope_Financial_Config_Template.csv` - RESTRICTED (PM/Admin only)
8. `06_Apparatus_Revenue_Template.csv` - Usually auto-generated

## Usage
1. Copy template to `../Import_Data/`
2. Fill with your data
3. Validate before import
4. Import to Dataverse

## Important Notes
- `03_Tasks_Template.csv` - Do NOT import! Manual creation only.
- `02_Scopes_Template.csv` - NETA_Standard column is REQUIRED
- Financial templates (05, 06) - Restricted access

See `../Documentation/04_Data_Migration/README_CSV_TEMPLATES.md` for details.
