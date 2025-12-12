/**
 * ⚠️ DEPRECATED - November 29, 2025
 * 
 * This Office Script approach has been replaced by VBA macro export.
 * See: Reference_Files/Excel/Estimator VBA Modules/DataverseExport.bas
 * 
 * Reasons for deprecation:
 * - Performance warnings with cell-by-cell reads
 * - Complex debugging in browser environment  
 * - SharePoint URL paths incompatible with some operations
 * 
 * The VBA macro exports JSON directly, which Power Automate then imports.
 * See: Documentation/06_Implementation_Guides/ESTIMATOR_FLOW_SPECIFICATION.md
 */

/**
 * Office Script: Parse RESA Estimator Excel File
 * 
 * This script extracts project data from the Estimator workbook format
 * for use in Power Automate flows to create Dataverse records.
 * 
 * Output: JSON object with project, scopes, and apparatus data
 */

interface ProjectData {
  projectName: string;
  projectNumber: string;
  clientName: string;
  clientContact: string;
  location: string;
  address: string;
  estimatorName: string;
  estimateDate: string;
  poNumber: string;
  totalHours: number;
  totalAmount: number;
}

interface ApparatusItem {
  quantity: number;
  netaCode: string;
  apparatusType: string;
  designation: string;
  drawingNumber: string;
  hours: number;
  rate: number;
  amount: number;
}

interface ScopeData {
  scopeName: string;
  scopeNumber: number;
  sheetName: string;
  apparatus: ApparatusItem[];
  totalHours: number;
  totalAmount: number;
}

interface EstimatorOutput {
  project: ProjectData;
  scopes: ScopeData[];
  extractedAt: string;
  sourceFile: string;
}

function main(workbook: ExcelScript.Workbook): EstimatorOutput {
  const output: EstimatorOutput = {
    project: extractProjectData(workbook),
    scopes: extractAllScopes(workbook),
    extractedAt: new Date().toISOString(),
    sourceFile: workbook.getName()
  };
  
  // Log the output so we can see it in the Office Scripts panel
  console.log("=== ESTIMATOR EXTRACTION RESULTS ===");
  console.log(JSON.stringify(output, null, 2));
  console.log(`Project: ${output.project.projectName} (${output.project.projectNumber})`);
  console.log(`Scopes found: ${output.scopes.length}`);
  output.scopes.forEach(s => {
    console.log(`  - ${s.sheetName}: ${s.apparatus.length} apparatus items`);
  });
  
  return output;
}

/**
 * Extract project header data from the Dataverse_Import sheet
 */
function extractProjectData(workbook: ExcelScript.Workbook): ProjectData {
  // First try Dataverse_Import sheet - this is the structured data sheet
  let headerSheet = workbook.getWorksheet("Dataverse_Import");
  
  // Default values if we can't find data
  const project: ProjectData = {
    projectName: "",
    projectNumber: "",
    clientName: "",
    clientContact: "",
    location: "",
    address: "",
    estimatorName: "",
    estimateDate: "",
    poNumber: "",
    totalHours: 0,
    totalAmount: 0
  };
  
  if (headerSheet) {
    // Read the Dataverse_Import sheet - data is in A:B columns
    const dataRange = headerSheet.getRange("A1:B25");
    const values = dataRange.getValues();
    
    // Parse the key-value pairs
    for (let row = 0; row < values.length; row++) {
      const label = String(values[row][0]).toLowerCase().trim();
      const value = String(values[row][1] || "").trim();
      
      if (label.includes("client")) {
        project.clientName = value;
      }
      if (label === "project:" || label === "project") {
        project.projectName = value;
      }
      if (label.includes("job #") || label.includes("job#")) {
        project.projectNumber = value;
      }
      if (label.includes("site address")) {
        project.address = value;
      }
      if (label.includes("site city") || label.includes("site state") || label.includes("site zip")) {
        // Append city, state, zip to location
        if (project.location) {
          project.location += ", " + value;
        } else {
          project.location = value;
        }
      }
      if (label.includes("site contact") && !label.includes("phone") && !label.includes("email")) {
        project.clientContact = value;
      }
      if (label.includes("project lead")) {
        project.estimatorName = value;
      }
      if (label.includes("quote date")) {
        project.estimateDate = value;
      }
    }
    
    console.log(`Found Dataverse_Import sheet - extracted project: ${project.projectName} (${project.projectNumber})`);
  } else {
    // Fallback: try to extract from filename
    const filename = workbook.getName();
    // Pattern: "434469 REV6 - Garney Central Mesa Reuse..."
    const match = filename.match(/^(\d+)\s+.*?-\s+(.+?)\s*\(/);
    if (match) {
      project.projectNumber = match[1];
      project.projectName = match[2].trim();
    }
    console.log(`No Dataverse_Import sheet - extracted from filename: ${project.projectName} (${project.projectNumber})`);
  }
  
  return project;
}

/**
 * Extract all scope sheets from workbook
 */
function extractAllScopes(workbook: ExcelScript.Workbook): ScopeData[] {
  const scopes: ScopeData[] = [];
  const sheets = workbook.getWorksheets();
  
  // Skip known non-scope sheets - add Equipment Reference and Dataverse
  const skipSheets = ["Summary", "Cover", "Project Info", "Header", "Instructions", 
                      "Print_Template", "Master", "Rates", "Settings", "Lookup",
                      "Equipment Reference", "Dataverse", "Import"];
  
  let scopeNumber = 1;
  
  for (const sheet of sheets) {
    const sheetName = sheet.getName();
    
    // Skip utility sheets
    if (skipSheets.some(skip => sheetName.toLowerCase().includes(skip.toLowerCase()))) {
      continue;
    }
    
    // Only process sheets that look like scope sheets (contain NETA or ATS or PSS)
    if (!sheetName.includes("NETA") && !sheetName.includes("PSS") && 
        !sheetName.includes("ATS") && !sheetName.includes("Scope")) {
      continue;
    }
    
    // Check if this looks like a scope sheet (has equipment data)
    const scopeData = extractScopeData(sheet, scopeNumber);
    
    if (scopeData && scopeData.apparatus.length > 0) {
      scopes.push(scopeData);
      scopeNumber++;
    }
  }
  
  return scopes;
}

/**
 * Extract equipment data from a single scope sheet
 * Based on actual Estimator layout from VBA module:
 *   Column C = Quantity
 *   Column E = Equipment Type  
 *   Column I = Hours per unit
 *   Column J = Total Hours
 *   Data starts at row 6
 */
function extractScopeData(sheet: ExcelScript.Worksheet, scopeNumber: number): ScopeData | null {
  const scopeData: ScopeData = {
    scopeName: sheet.getName(),
    scopeNumber: scopeNumber,
    sheetName: sheet.getName(),
    apparatus: [],
    totalHours: 0,
    totalAmount: 0
  };
  
  // Get scope-level totals from fixed cells
  const totalHoursCell = sheet.getRange("J3").getValue();
  const quotedAmountCell = sheet.getRange("P3").getValue();
  const scopeTypeCell = sheet.getRange("C4").getValue();
  
  scopeData.totalHours = Number(totalHoursCell) || 0;
  scopeData.totalAmount = Number(quotedAmountCell) || 0;
  
  // If no hours, this scope is empty
  if (scopeData.totalHours === 0) {
    return null;
  }
  
  // Read apparatus data from rows 6-100 (first 100 for performance)
  // Full range is 6-488 but Power Automate can handle the key items
  const dataRange = sheet.getRange("C6:J100");
  const values = dataRange.getValues();
  
  for (let row = 0; row < values.length; row++) {
    const rowData = values[row];
    
    // Column mapping (0-indexed from column C):
    // C=0 (Qty), D=1, E=2 (Type), F=3, G=4, H=5, I=6 (Hours), J=7 (Total)
    const qty = Number(rowData[0]) || 0;  // Column C
    const equipType = String(rowData[2] || "").trim();  // Column E
    const hoursPerUnit = Number(rowData[6]) || 0;  // Column I
    const totalHrs = Number(rowData[7]) || 0;  // Column J
    
    // Skip empty rows
    if (qty === 0 || !equipType) continue;
    
    // Skip section headers (bold text would show as qty=0 but we filter above)
    
    const apparatus: ApparatusItem = {
      quantity: qty,
      netaCode: "",  // NETA code not in this column layout
      apparatusType: equipType,
      designation: "",  // Would need additional column
      drawingNumber: "",
      hours: hoursPerUnit,
      rate: 0,
      amount: totalHrs
    };
    
    scopeData.apparatus.push(apparatus);
  }
  
  return scopeData;
}
