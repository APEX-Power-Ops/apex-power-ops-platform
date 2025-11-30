# Estimator to Dataverse Import Automation
## Implementation Specification

**Version:** 2.0  
**Created:** November 27, 2025  
**Updated:** November 29, 2025  
**Approach:** ~~Office Scripts + Power Automate~~ → **VBA JSON Export**  
**Status:** ⚠️ DEPRECATED - See ESTIMATOR_FLOW_SPECIFICATION.md v3.0

---

## ⚠️ DEPRECATION NOTICE

This specification has been **superseded** by the simplified VBA JSON export approach.

**See:** [ESTIMATOR_FLOW_SPECIFICATION.md](./ESTIMATOR_FLOW_SPECIFICATION.md) (v3.0)

### Why This Was Deprecated
- Office Scripts had performance warnings with cell-by-cell reads
- Complex TypeScript debugging in browser environment
- SharePoint URL paths incompatible with some operations
- VBA macro approach is simpler, faster, and already working

### What Replaced It
- **VBA Macro:** `DataverseExport.bas` exports JSON file
- **Power Automate:** Simple flow parses JSON, creates Dataverse records
- **User Experience:** Click button → Save As → Done

---

## Historical Reference (Original Approach)

One-click button in Excel Estimator that sends quote data to Dataverse, creating a complete project hierarchy (Project → Scopes → Tasks → Apparatus) with all financial configuration.

**User Experience:**
1. User completes Estimator workbook as normal
2. Clicks "Send to Dataverse" button (Automate ribbon)
3. Sees progress indicator
4. Gets success message with link to new project in Power Apps

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXCEL ESTIMATOR                              │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │ Scope Sheets │ → │ Office Script │ → │ JSON Payload    │    │
│  │ (1-20)       │    │ (TypeScript)  │    │ (Structured)    │    │
│  └─────────────┘    └──────────────┘    └────────┬────────┘    │
└──────────────────────────────────────────────────┼──────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                     POWER AUTOMATE                               │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │ Receive JSON │ → │ Parse & Loop  │ → │ Dataverse CRUD  │    │
│  │ from Script  │    │ through data  │    │ Operations      │    │
│  └─────────────┘    └──────────────┘    └────────┬────────┘    │
└──────────────────────────────────────────────────┼──────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATAVERSE                                    │
│  ┌────────┐  ┌────────┐  ┌───────┐  ┌──────────┐  ┌──────────┐ │
│  │ Client │→│ Site   │→│Project│→│ Scopes   │→│ Apparatus│ │
│  └────────┘  └────────┘  └───────┘  └──────────┘  └──────────┘ │
│                                      ┌──────────────────┐       │
│                                      │ ScopeLaborDetail │       │
│                                      └──────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Office Script

### Script Purpose
Extract all relevant data from the Estimator workbook and format as JSON for Power Automate.

### Script Location
Save in Excel: Automate → New Script → "ExtractEstimatorData"

### Data Extraction Map

#### Project Header (Equipment_Reference Sheet)
| Cell/Range | JSON Field | Description |
|------------|------------|-------------|
| Workbook Name | `projectNumber` | Extract number (e.g., "434469") |
| User Input | `projectName` | From header or prompt |
| User Input | `clientName` | Lookup or create |
| User Input | `siteName` | Lookup or create |
| `M3` | `grandTotal` | Sum of all scope totals |

#### Scope Data (Per Active Scope Sheet)
| Cell | JSON Field | Description |
|------|------------|-------------|
| Sheet Name | `scopeName` | User-defined scope name |
| `C4` | `scopeType` | "MTS" or "ATS" |
| `J3` | `totalHours` | Total onsite hours |
| `P3` | `grandTotal` | Scope revenue total |
| `M4` | `multiplier` | Scope multiplier |
| `P4` | `adjustedTotal` | With margin applied |

#### Financial Sections (Per Scope - Columns L-P)
| Section | Rows | JSON Fields |
|---------|------|-------------|
| Offsite Labor | 6-9 | `offsiteLabor: { reportHours, projectMgmt, loadingPrep, total }` |
| Travel | 11-16 | `travel: { hours, perDiem, flights, carRental, misc, total }` |
| Outside Services | 18-23 | `outsideServices: { generatorRental, equipmentRental, oilSample, misc1, misc2, total }` |

#### Apparatus Data (Per Scope - Columns C-J, Rows 6-488)
| Column | JSON Field | Description |
|--------|------------|-------------|
| C | `quantity` | Number of units |
| D | `netaHours` | Hours per unit (formula result) |
| E | `apparatusType` | Equipment type name |
| F | `designation` | Equipment designation |
| G | `drawingNumber` | Drawing reference |
| I | `baseHours` | Base hours lookup |
| J | `totalHours` | Qty × Hours |

### Office Script Code

```typescript
/**
 * ExtractEstimatorData
 * Extracts quote data from Estimator workbook for Dataverse import
 */
function main(workbook: ExcelScript.Workbook): EstimatorData {
  
  // Initialize result object
  let result: EstimatorData = {
    projectNumber: extractProjectNumber(workbook.getName()),
    projectName: "",  // Will prompt or read from cell
    clientName: "",   // Will prompt or read from cell
    siteName: "",     // Will prompt or read from cell
    grandTotal: 0,
    scopes: []
  };

  // Get Equipment Reference sheet for totals
  const equipRef = workbook.getWorksheet("Equipment Reference");
  if (equipRef) {
    result.grandTotal = equipRef.getRange("M3").getValue() as number || 0;
  }

  // Process each scope sheet (Scope1 through Scope20)
  for (let i = 1; i <= 20; i++) {
    const scopeSheet = getWorksheetByCodeName(workbook, `Scope${i}`);
    if (!scopeSheet) continue;

    const scopeData = extractScopeData(scopeSheet);
    if (scopeData && scopeData.totalHours > 0) {
      result.scopes.push(scopeData);
    }
  }

  return result;
}

/**
 * Extract project number from workbook filename
 */
function extractProjectNumber(filename: string): string {
  // Match pattern like "434469" at start of filename
  const match = filename.match(/^(\d+)/);
  return match ? match[1] : "";
}

/**
 * Get worksheet by VBA CodeName (stored in sheet properties)
 * Note: Office Scripts can't access CodeName directly, 
 * so we'll use naming convention or position
 */
function getWorksheetByCodeName(workbook: ExcelScript.Workbook, codeName: string): ExcelScript.Worksheet | null {
  // Workaround: Use sheet index based on known structure
  // Scope1 = index 2, Scope2 = index 3, etc. (after Equipment_Reference and Print_Template)
  const scopeIndex = parseInt(codeName.replace("Scope", ""));
  const sheets = workbook.getWorksheets();
  
  // Find by position or iterate to find by characteristics
  // This may need adjustment based on actual workbook structure
  for (const sheet of sheets) {
    // Check if sheet has scope characteristics (J3 has hours, C4 has MTS/ATS)
    const j3Value = sheet.getRange("J3").getValue();
    const c4Value = sheet.getRange("C4").getValue();
    
    if (typeof j3Value === "number" && 
        (c4Value === "MTS" || c4Value === "ATS")) {
      // This looks like a scope sheet
      // Additional logic to match to specific scope index
    }
  }
  
  return null; // Placeholder
}

/**
 * Extract all data from a single scope sheet
 */
function extractScopeData(sheet: ExcelScript.Worksheet): ScopeData | null {
  const totalHours = sheet.getRange("J3").getValue() as number || 0;
  
  // Skip empty scopes
  if (totalHours === 0) return null;

  let scope: ScopeData = {
    scopeName: sheet.getName(),
    scopeType: sheet.getRange("C4").getValue() as string || "MTS",
    totalHours: totalHours,
    grandTotal: sheet.getRange("P3").getValue() as number || 0,
    multiplier: sheet.getRange("M4").getValue() as number || 1,
    adjustedTotal: sheet.getRange("P4").getValue() as number || 0,
    financials: extractFinancials(sheet),
    apparatus: extractApparatus(sheet)
  };

  return scope;
}

/**
 * Extract financial sections from scope sheet
 */
function extractFinancials(sheet: ExcelScript.Worksheet): FinancialData {
  return {
    offsiteLabor: {
      reportHoursPercent: sheet.getRange("M6").getValue() as number || 0,
      reportHoursRate: sheet.getRange("O6").getValue() as number || 0,
      reportHoursTotal: sheet.getRange("P6").getValue() as number || 0,
      projectMgmtPercent: sheet.getRange("M7").getValue() as number || 0,
      projectMgmtRate: sheet.getRange("O7").getValue() as number || 0,
      projectMgmtTotal: sheet.getRange("P7").getValue() as number || 0,
      loadingPrepPercent: sheet.getRange("M8").getValue() as number || 0,
      loadingPrepRate: sheet.getRange("O8").getValue() as number || 0,
      loadingPrepTotal: sheet.getRange("P8").getValue() as number || 0,
      total: sheet.getRange("P9").getValue() as number || 0
    },
    travel: {
      hoursUnits: sheet.getRange("M11").getValue() as number || 0,
      hoursCost: sheet.getRange("N11").getValue() as number || 0,
      hoursTotal: sheet.getRange("P11").getValue() as number || 0,
      perDiemUnits: sheet.getRange("M12").getValue() as number || 0,
      perDiemCost: sheet.getRange("N12").getValue() as number || 0,
      perDiemTotal: sheet.getRange("P12").getValue() as number || 0,
      flightsUnits: sheet.getRange("M13").getValue() as number || 0,
      flightsCost: sheet.getRange("N13").getValue() as number || 0,
      flightsTotal: sheet.getRange("P13").getValue() as number || 0,
      carRentalUnits: sheet.getRange("M14").getValue() as number || 0,
      carRentalCost: sheet.getRange("N14").getValue() as number || 0,
      carRentalTotal: sheet.getRange("P14").getValue() as number || 0,
      miscUnits: sheet.getRange("M15").getValue() as number || 0,
      miscCost: sheet.getRange("N15").getValue() as number || 0,
      miscTotal: sheet.getRange("P15").getValue() as number || 0,
      total: sheet.getRange("P16").getValue() as number || 0
    },
    outsideServices: {
      generatorUnits: sheet.getRange("M18").getValue() as number || 0,
      generatorCost: sheet.getRange("N18").getValue() as number || 0,
      generatorTotal: sheet.getRange("P18").getValue() as number || 0,
      equipmentRentalUnits: sheet.getRange("M19").getValue() as number || 0,
      equipmentRentalCost: sheet.getRange("N19").getValue() as number || 0,
      equipmentRentalTotal: sheet.getRange("P19").getValue() as number || 0,
      oilSampleUnits: sheet.getRange("M20").getValue() as number || 0,
      oilSampleCost: sheet.getRange("N20").getValue() as number || 0,
      oilSampleTotal: sheet.getRange("P20").getValue() as number || 0,
      misc1Units: sheet.getRange("M21").getValue() as number || 0,
      misc1Cost: sheet.getRange("N21").getValue() as number || 0,
      misc1Total: sheet.getRange("P21").getValue() as number || 0,
      misc2Units: sheet.getRange("M22").getValue() as number || 0,
      misc2Cost: sheet.getRange("N22").getValue() as number || 0,
      misc2Total: sheet.getRange("P22").getValue() as number || 0,
      total: sheet.getRange("P23").getValue() as number || 0
    }
  };
}

/**
 * Extract apparatus list from scope sheet
 */
function extractApparatus(sheet: ExcelScript.Worksheet): ApparatusData[] {
  let apparatus: ApparatusData[] = [];
  
  // Scan rows 6-488 for equipment data
  const dataRange = sheet.getRange("C6:J488");
  const values = dataRange.getValues();
  
  for (let row = 0; row < values.length; row++) {
    const qty = values[row][0];        // Column C
    const netaHours = values[row][1];  // Column D
    const type = values[row][2];       // Column E
    const designation = values[row][3]; // Column F
    const drawing = values[row][4];    // Column G
    // Column H skipped
    const baseHours = values[row][6];  // Column I
    const totalHours = values[row][7]; // Column J
    
    // Skip empty rows
    if (!type || type === "" || type === 0) continue;
    
    // Skip section headers (bold text, no quantity)
    if (!qty && type && typeof type === "string") {
      // This might be a section header - could track for grouping
      continue;
    }
    
    // Valid apparatus row
    if (qty && qty > 0) {
      apparatus.push({
        quantity: qty as number,
        apparatusType: type as string,
        designation: designation as string || "",
        drawingNumber: drawing as string || "",
        hoursPerUnit: baseHours as number || 0,
        totalHours: totalHours as number || 0
      });
    }
  }
  
  return apparatus;
}

// Type Definitions
interface EstimatorData {
  projectNumber: string;
  projectName: string;
  clientName: string;
  siteName: string;
  grandTotal: number;
  scopes: ScopeData[];
}

interface ScopeData {
  scopeName: string;
  scopeType: string;
  totalHours: number;
  grandTotal: number;
  multiplier: number;
  adjustedTotal: number;
  financials: FinancialData;
  apparatus: ApparatusData[];
}

interface FinancialData {
  offsiteLabor: {
    reportHoursPercent: number;
    reportHoursRate: number;
    reportHoursTotal: number;
    projectMgmtPercent: number;
    projectMgmtRate: number;
    projectMgmtTotal: number;
    loadingPrepPercent: number;
    loadingPrepRate: number;
    loadingPrepTotal: number;
    total: number;
  };
  travel: {
    hoursUnits: number;
    hoursCost: number;
    hoursTotal: number;
    perDiemUnits: number;
    perDiemCost: number;
    perDiemTotal: number;
    flightsUnits: number;
    flightsCost: number;
    flightsTotal: number;
    carRentalUnits: number;
    carRentalCost: number;
    carRentalTotal: number;
    miscUnits: number;
    miscCost: number;
    miscTotal: number;
    total: number;
  };
  outsideServices: {
    generatorUnits: number;
    generatorCost: number;
    generatorTotal: number;
    equipmentRentalUnits: number;
    equipmentRentalCost: number;
    equipmentRentalTotal: number;
    oilSampleUnits: number;
    oilSampleCost: number;
    oilSampleTotal: number;
    misc1Units: number;
    misc1Cost: number;
    misc1Total: number;
    misc2Units: number;
    misc2Cost: number;
    misc2Total: number;
    total: number;
  };
}

interface ApparatusData {
  quantity: number;
  apparatusType: string;
  designation: string;
  drawingNumber: string;
  hoursPerUnit: number;
  totalHours: number;
}
```

### Script Notes

**Cell References Need Validation:** The financial section row numbers (6-9, 11-16, 18-23) are based on the screenshots. Need to verify against actual template.

**Scope Sheet Identification:** Office Scripts can't access VBA CodeNames. Will need workaround:
- Option A: Rely on sheet naming convention
- Option B: Check for scope characteristics (J3 has number, C4 has MTS/ATS)
- Option C: Use sheet position (less reliable if user reorders)

---

## Phase 2: Power Automate Flow

### Flow Name
`Estimator-to-Dataverse-Import`

### Trigger
"Run a script from Power Automate" → Excel Online (Business)

### Flow Steps

```
1. TRIGGER: Run Script
   └─ Workbook: [Selected file in OneDrive/SharePoint]
   └─ Script: ExtractEstimatorData
   └─ Output: JSON (EstimatorData)

2. PARSE JSON
   └─ Content: Script output
   └─ Schema: [EstimatorData interface converted to JSON schema]

3. CONDITION: Check if project already exists
   └─ List rows: cr950_projectses
   └─ Filter: cr950_projectnumber eq 'projectNumber'
   └─ If exists → Terminate with message "Project already imported"

4. INITIALIZE VARIABLES
   └─ ProjectId (string)
   └─ ScopeIds (array)
   └─ ErrorLog (array)

5. LOOKUP OR CREATE CLIENT
   └─ List rows: cr950_clients
   └─ Filter: cr950_name eq 'clientName'
   └─ If not found → Add row to cr950_clients
   └─ Store ClientId

6. LOOKUP OR CREATE SITE
   └─ List rows: cr950_sites
   └─ Filter: cr950_name eq 'siteName' AND cr950_clientid eq ClientId
   └─ If not found → Add row to cr950_sites
   └─ Store SiteId

7. CREATE PROJECT
   └─ Add row: cr950_projectses
   └─ Fields:
      - cr950_name: projectName
      - cr950_projectnumber: projectNumber
      - cr950_clientid: ClientId
      - cr950_siteid: SiteId
      - cr950_quotedamount: grandTotal
      - cr950_projectstatus: "Quoted" (or appropriate choice)
   └─ Store ProjectId

8. LOOP: For Each Scope
   └─ Apply to each: scopes array
   
   8.1 CREATE SCOPE
       └─ Add row: cr950_projectscopeses
       └─ Fields:
          - cr950_name: scopeName
          - cr950_projectid: ProjectId
          - cr950_scopetype: scopeType (MTS/ATS choice)
          - cr950_quotedamount: grandTotal
          - cr950_totalestimatedhours: totalHours
          - cr950_multiplier: multiplier
       └─ Store ScopeId
   
   8.2 CREATE SCOPE LABOR DETAIL
       └─ Add row: cr950_scopelabordetails
       └─ Fields:
          - cr950_projectscopeid: ScopeId
          - cr950_onsitelaborhours: totalHours
          - cr950_offsitelabortotal: financials.offsiteLabor.total
          - cr950_traveltotal: financials.travel.total
          - cr950_outsideservicestotal: financials.outsideServices.total
          - [Additional financial fields as mapped]
   
   8.3 GROUP APPARATUS BY TYPE
       └─ Compose: Group apparatus array by apparatusType
       └─ Creates task groupings
   
   8.4 LOOP: For Each Task Group
       └─ Apply to each: grouped apparatus types
       
       8.4.1 CREATE TASK
             └─ Add row: cr950_taskses
             └─ Fields:
                - cr950_name: [apparatus type group name]
                - cr950_projectscopeid: ScopeId
                - cr950_projectid: ProjectId
             └─ Store TaskId
       
       8.4.2 LOOP: For Each Apparatus in Group
             └─ Apply to each: apparatus items
             
             8.4.2.1 CREATE APPARATUS (expand by quantity)
                     └─ Apply to each: 1 to quantity
                     └─ Add row: cr950_apparatus
                     └─ Fields:
                        - cr950_name: designation OR "type #N"
                        - cr950_taskid: TaskId
                        - cr950_projectscopeid: ScopeId
                        - cr950_projectid: ProjectId
                        - cr950_apparatushours: hoursPerUnit
                        - cr950_apparatustypemasterid: [Lookup by type name]

9. COMPOSE: Success Response
   └─ ProjectId
   └─ ProjectUrl: [Deep link to Power Apps record]
   └─ ScopesCreated: count
   └─ ApparatusCreated: count

10. RESPOND TO POWER APP (or Script)
    └─ Return success message with project link
```

### Flow Error Handling

```
SCOPE: Try-Catch Pattern

TRY:
  └─ All creation steps in a Scope action
  └─ Configure to continue on error

CATCH (Run After = Failed/Skipped/TimedOut):
  └─ Append to ErrorLog variable
  └─ Continue to next item

FINALLY:
  └─ If ErrorLog is not empty
     └─ Send notification email with errors
     └─ Return partial success message
```

---

## Phase 3: Button Integration

### Adding the Button

1. Open Estimator workbook in Excel (Online or Desktop)
2. Go to **Automate** tab
3. Click **Automate a Task** or **Create Flow**
4. Search for "Run script"
5. Select the ExtractEstimatorData script
6. Configure the flow connection
7. Save flow
8. Button appears in workbook

### Alternative: Ribbon Button (VBA Trigger)

If native button doesn't meet UX needs, add VBA button that:
1. Saves workbook to OneDrive/SharePoint location
2. Triggers Power Automate via HTTP webhook
3. Displays status message

```vba
Sub SendToDataverse()
    ' Save to SharePoint first
    ThisWorkbook.Save
    
    ' Trigger Power Automate via HTTP
    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")
    
    Dim webhookUrl As String
    webhookUrl = "[Power Automate HTTP trigger URL]"
    
    Dim payload As String
    payload = "{""workbookPath"": """ & ThisWorkbook.FullName & """}"
    
    http.Open "POST", webhookUrl, False
    http.setRequestHeader "Content-Type", "application/json"
    http.send payload
    
    If http.Status = 200 Then
        MsgBox "Successfully sent to Dataverse!", vbInformation
    Else
        MsgBox "Error: " & http.responseText, vbCritical
    End If
End Sub
```

---

## Phase 4: Dataverse Record Creation Sequence

### Order of Operations (Critical)

Records must be created in dependency order:

```
1. Client (if new)
   └─ No dependencies
   
2. Site (if new)
   └─ Requires: ClientId
   
3. Project
   └─ Requires: ClientId, SiteId
   
4. For each Scope:
   │
   ├─ 4a. ProjectScope
   │      └─ Requires: ProjectId
   │
   ├─ 4b. ScopeLaborDetail
   │      └─ Requires: ScopeId
   │
   └─ 4c. For each Task:
          │
          ├─ 4c-i. Task
          │        └─ Requires: ScopeId, ProjectId
          │
          └─ 4c-ii. For each Apparatus:
                    └─ Apparatus
                       └─ Requires: TaskId, ScopeId, ProjectId
```

### Lookup vs Create Logic

| Entity | Logic |
|--------|-------|
| Client | Lookup by name → Create if not found |
| Site | Lookup by name + client → Create if not found |
| Project | Always create (check duplicate by project number first) |
| Scope | Always create |
| ScopeLaborDetail | Always create (1:1 with scope) |
| Task | Always create (grouped by apparatus type) |
| Apparatus | Always create (expand quantity to N records) |
| ApparatusTypeMaster | Lookup only (never create) |

---

## Phase 5: Error Handling Strategy

### Validation Before Submit

Office Script validates:
- [ ] At least one scope has data (totalHours > 0)
- [ ] Project number extracted from filename
- [ ] Required fields present

### Flow Error Handling

| Error Type | Handling |
|------------|----------|
| Duplicate project number | Terminate with clear message |
| Client/Site not found & can't create | Log error, continue |
| Dataverse API failure | Retry 3x, then log and continue |
| Apparatus type not in master | Create apparatus without type link, log warning |

### Rollback Strategy

**Option A: No Rollback (Recommended)**
- Create what you can
- Log failures
- User fixes in Power Apps
- Simpler to implement

**Option B: Full Rollback**
- Track all created record IDs
- On failure, delete all created records
- Complex, more API calls

### User Feedback

| Outcome | Message |
|---------|---------|
| Full success | "✅ Project created! [View in Power Apps]" |
| Partial success | "⚠️ Project created with warnings. Check email for details." |
| Failure | "❌ Import failed: [reason]. No records created." |

---

## Implementation Checklist

### Pre-Implementation
- [ ] Confirm workbook lives in OneDrive/SharePoint
- [ ] Verify user has Power Automate license
- [ ] Validate cell references against actual template
- [ ] Document ApparatusTypeMaster lookup values

### Phase 1: Office Script
- [ ] Create new script in Excel
- [ ] Implement ExtractEstimatorData function
- [ ] Test with sample workbook
- [ ] Validate JSON output

### Phase 2: Power Automate
- [ ] Create new flow
- [ ] Add Excel script trigger
- [ ] Build Dataverse creation steps
- [ ] Add error handling
- [ ] Test end-to-end

### Phase 3: Integration
- [ ] Add button to workbook template
- [ ] Test with real data
- [ ] Document for users
- [ ] Deploy to production

### Post-Implementation
- [ ] Monitor for errors
- [ ] Gather user feedback
- [ ] Iterate on improvements

---

## Appendix A: Dataverse Table Reference

| Table | Logical Name | Entity Set Name |
|-------|--------------|-----------------|
| Clients | cr950_client | cr950_clients |
| Sites | cr950_site | cr950_sites |
| Projects | cr950_projects | cr950_projectses |
| Project Scopes | cr950_projectscope | cr950_projectscopeses |
| Scope Labor Detail | cr950_scopelabordetail | cr950_scopelabordetails |
| Tasks | cr950_tasks | cr950_taskses |
| Apparatus | cr950_apparatus | cr950_apparatuses |
| Apparatus Type Master | cr950_apparatustypemaster | cr950_apparatustypemasters |

---

## Appendix B: Cell Reference Map

### Equipment Reference Sheet
| Cell | Content |
|------|---------|
| M3 | Grand Total (all scopes) |
| L4:L23 | Scope sheet names |
| M4:M23 | Scope totals (INDIRECT formulas) |

### Scope Sheets (1-20)
| Cell | Content |
|------|---------|
| A1 | Project name (header) |
| C4 | Job Type (MTS/ATS) |
| J3 | Total onsite hours |
| M4 | Scope multiplier |
| P3 | Grand total |
| P4 | Adjusted total |
| C6:J488 | Apparatus data rows |
| L6:P23 | Financial sections |

---

## Appendix C: JSON Schema for Power Automate

```json
{
  "type": "object",
  "properties": {
    "projectNumber": { "type": "string" },
    "projectName": { "type": "string" },
    "clientName": { "type": "string" },
    "siteName": { "type": "string" },
    "grandTotal": { "type": "number" },
    "scopes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "scopeName": { "type": "string" },
          "scopeType": { "type": "string" },
          "totalHours": { "type": "number" },
          "grandTotal": { "type": "number" },
          "multiplier": { "type": "number" },
          "adjustedTotal": { "type": "number" },
          "financials": { "type": "object" },
          "apparatus": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "quantity": { "type": "integer" },
                "apparatusType": { "type": "string" },
                "designation": { "type": "string" },
                "drawingNumber": { "type": "string" },
                "hoursPerUnit": { "type": "number" },
                "totalHours": { "type": "number" }
              }
            }
          }
        }
      }
    }
  }
}
```

---

*Document End*
