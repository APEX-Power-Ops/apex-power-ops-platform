# New Tables for v1.6.0.0 - NETA Checklists

## Import Order
1. `10_NETA_Test_Template.csv` - No dependencies
2. `11_Apparatus_Test_Checklist.csv` - Requires: NETA Test Template, Apparatus
3. `12_Apparatus_Submission.csv` - Requires: Apparatus

---

## Table 10: NETA Test Template

**Create table with:** "Create new table" during import

| CSV Column | Dataverse Type | Required | Notes |
|------------|----------------|----------|-------|
| Test Description | **Primary Column** (Text 500) | Yes | Main display field |
| NETA Section | Single line text (20) | Yes | e.g., "7.6.3" |
| Equipment Type | Single line text (200) | Yes | e.g., "Circuit Breakers, Vacuum, MV" |
| Test Type | Choice | Yes | Create choice: Visual/Mechanical, Electrical |
| Test Number | Single line text (10) | Yes | e.g., "A.1", "B.3" |
| NETA Standard | Choice | Yes | Create choice: ATS (Acceptance), MTS (Maintenance) |
| Is Optional | Yes/No | Yes | Default: No |
| Requires Value | Yes/No | Yes | Default: No |
| Sort Order | Whole number | No | Display sequence |
| Active | Yes/No | Yes | Default: Yes |

**After import:** No additional setup needed

---

## Table 11: Apparatus Test Checklist

**Create table with:** "Create new table" during import

| CSV Column | Dataverse Type | Required | Notes |
|------------|----------------|----------|-------|
| Name | **Primary Column** (Text 100) | Yes | Auto-format: "{Test Number} - {Apparatus}" |
| Apparatus | Lookup | Yes | FK to Apparatus table |
| Test Template | Lookup | Yes | FK to NETA Test Template table |
| Status | Choice | Yes | Create: Not Started, Complete, N/A, Failed |
| Is Complete | Yes/No | Yes | Default: No |
| Recorded Value | Single line text (100) | No | For measurements |
| Notes | Multiple lines text | No | Tech notes |
| Completed By | Lookup | No | FK to User |
| Completed Date | Date and time | No | When marked complete |

**After import:** 
- Create lookup relationship to Apparatus
- Create lookup relationship to NETA Test Template
- Create lookup relationship to User (for Completed By)

---

## Table 12: Apparatus Submission

**Create table with:** "Create new table" during import

| CSV Column | Dataverse Type | Required | Notes |
|------------|----------------|----------|-------|
| Name | **Primary Column** (Text 100) | Yes | Auto-format: "Submission - {Apparatus}" |
| Apparatus | Lookup | Yes | FK to Apparatus table |
| Submitted By | Lookup | Yes | FK to User |
| Submitted Date | Date and time | Yes | When submitted |
| Review Status | Choice | Yes | Create: Pending, Approved, Rejected, Returned |
| Reviewed By | Lookup | No | FK to User |
| Reviewed Date | Date and time | No | When reviewed |
| Rejection Reason | Multiple lines text | No | If rejected |
| Tests Complete | Whole number | No | Count at submission |
| Tests Total | Whole number | No | Total tests |

**After import:**
- Create lookup relationship to Apparatus
- Create lookup relationships to User (Submitted By, Reviewed By)

---

## Choices to Create (if not auto-created during import)

### Test Type
- Visual/Mechanical
- Electrical

### NETA Standard  
- ATS (Acceptance)
- MTS (Maintenance)

### Checklist Status (for Apparatus Test Checklist)
- Not Started
- Complete
- N/A
- Failed

### Review Status (for Apparatus Submission)
- Pending
- Approved
- Rejected
- Returned for Revision

---

## After All Tables Created

### Add fields to existing Apparatus table:
| Display Name | Type | Notes |
|--------------|------|-------|
| Checklist Status | Choice | Not Started, In Progress, Submitted, Approved, Rejected |
| Submitted Date | Date and time | When submitted for review |
| Approval Date | Date and time | When approved |

### Add fields to existing Apparatus Type Master table:
| Display Name | Type | Notes |
|--------------|------|-------|
| NETA ATS Section | Single line text (20) | e.g., "7.6.3" |
| NETA MTS Section | Single line text (20) | e.g., "7.6.3" |
| Voltage Class | Choice | LV, MV, HV |

---

## Table 07: Estimators (for Power Automate Flow)

**Purpose:** Tracks Excel estimator workbooks imported via Power Automate from SharePoint folder structure.

**Creation Method:** Run PowerShell script `Scripts\PowerShell\Active\Create-EstimatorsTable.ps1`

| CSV Column | Dataverse Field | Type | Required | Notes |
|------------|-----------------|------|----------|-------|
| Name | cr950_name | **Primary Column** (Text 200) | Yes | Display name - typically project name |
| Client | cr950_client | Lookup | Yes | FK to Clients table |
| Project_Name | cr950_projectname | Single line text (200) | Yes | Project name from folder path |
| Estimate_Date | cr950_estimatedate | Date only | Yes | Date from filename (_YYYYMMDD_) |
| Current_Revision | cr950_currentrevision | Whole number | Yes | Revision from filename (_Rev#) |
| Estimator_File_URL | cr950_estimator_file_url | URL | Yes | Full SharePoint URL to file |
| Filename | cr950_filename | Single line text (500) | Yes | Original filename with extension |
| Status | cr950_status | Choice | Yes | Draft, Quoted, Awarded, Converted, Rejected, On Hold |
| Converted_to_Project | cr950_convertedtoproject | Yes/No | No | Default: No |
| Project | cr950_project | Lookup | No | FK to Projects (after conversion) |
| Last_Modified | cr950_lastmodified | Date and time | No | Last update timestamp |
| Notes | cr950_notes | Multiple lines (4000) | No | Free text notes |

### Status Choice Values
| Value | Label |
|-------|-------|
| 864340000 | Draft |
| 864340001 | Quoted |
| 864340002 | Awarded |
| 864340003 | Converted |
| 864340004 | Rejected |
| 864340005 | On Hold |

### After PowerShell Creation:
1. Open Power Apps Maker Portal
2. Navigate to Tables > Estimators
3. Add **Client** lookup column:
   - Related Table: Clients (cr950_clients)
   - Schema Name: cr950_client
4. Add **Project** lookup column:
   - Related Table: Projects (cr950_projectses)
   - Schema Name: cr950_project
5. Save and Publish

### Related Documents:
- `Documentation\06_Implementation_Guides\ESTIMATOR_FLOW_SPECIFICATION.md`
- `Scripts\PowerShell\Active\Create-EstimatorsTable.ps1`
