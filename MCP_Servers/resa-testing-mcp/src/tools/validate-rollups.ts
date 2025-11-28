import { queryDataverse, queryMetadata, getRecord } from "../utils/dataverse-client.js";
import _ from "lodash";

export interface ValidationResult {
  status: "PASS" | "FAIL" | "WARNING";
  tableName: string;
  recordsTested: number;
  fields: FieldValidationResult[];
  summary: {
    passed: number;
    failed: number;
    warnings: number;
  };
  timestamp: string;
}

export interface FieldValidationResult {
  fieldName: string;
  displayName: string;
  recordId: string;
  recordName?: string;
  expected: number | null;
  actual: number | null;
  variance: number;
  percentageOff: number;
  status: "PASS" | "FAIL" | "WARNING";
  details?: string;
}

/**
 * Validate rollup fields by comparing system-calculated values vs manual calculations
 * 
 * This tool:
 * 1. Queries rollup field metadata from Dataverse
 * 2. Fetches sample records with rollup fields
 * 3. Manually calculates expected values by querying related records
 * 4. Compares system values vs manual calculations
 * 5. Reports PASS/FAIL with variance details
 * 
 * @param tableName - Logical name of the table (e.g., 'cr950_projectscopes')
 * @param fieldNames - Optional array of specific rollup field names to test
 * @param sampleSize - Number of records to test (default: 5)
 * @param compareManual - Whether to manually calculate expected values (default: true)
 */
export async function validateRollupFields(params: {
  tableName: string;
  fieldNames?: string[];
  sampleSize?: number;
  compareManual?: boolean;
}): Promise<ValidationResult> {
  const { tableName, fieldNames, sampleSize = 5, compareManual = true } = params;
  
  console.error(`Validating rollup fields on ${tableName}...`);
  
  try {
    // 1. Get rollup field metadata
    const rollupFields = await getRollupFieldMetadata(tableName, fieldNames);
    
    if (rollupFields.length === 0) {
      return {
        status: "WARNING",
        tableName,
        recordsTested: 0,
        fields: [],
        summary: { passed: 0, failed: 0, warnings: 1 },
        timestamp: new Date().toISOString(),
      };
    }
    
    console.error(`Found ${rollupFields.length} rollup fields to validate`);
    
    // 2. Get sample records (only records with state=0, active)
    const records = await getSampleRecords(tableName, rollupFields, sampleSize);
    
    if (records.length === 0) {
      return {
        status: "WARNING",
        tableName,
        recordsTested: 0,
        fields: [],
        summary: { passed: 0, failed: 0, warnings: 1 },
        timestamp: new Date().toISOString(),
      };
    }
    
    console.error(`Testing ${records.length} records`);
    
    // 3. Validate each rollup field on each record
    const results: FieldValidationResult[] = [];
    
    for (const record of records) {
      for (const rollupField of rollupFields) {
        const validation = await validateSingleRollup(
          tableName,
          record,
          rollupField,
          compareManual
        );
        results.push(validation);
      }
    }
    
    // 4. Calculate summary
    const passed = results.filter(r => r.status === "PASS").length;
    const failed = results.filter(r => r.status === "FAIL").length;
    const warnings = results.filter(r => r.status === "WARNING").length;
    
    const overallStatus = failed > 0 ? "FAIL" : (warnings > 0 ? "WARNING" : "PASS");
    
    return {
      status: overallStatus,
      tableName,
      recordsTested: records.length,
      fields: results,
      summary: { passed, failed, warnings },
      timestamp: new Date().toISOString(),
    };
    
  } catch (error: any) {
    console.error(`Validation error: ${error.message}`);
    throw new Error(`Rollup field validation failed: ${error.message}`);
  }
}

/**
 * Get rollup field metadata from Dataverse
 */
async function getRollupFieldMetadata(
  tableName: string,
  fieldNames?: string[]
): Promise<any[]> {
  try {
    // Query entity metadata with attributes
    const metadata = await queryMetadata(
      `EntityDefinitions(LogicalName='${tableName}')?$expand=Attributes($filter=AttributeTypeName/Value eq 'RollupType')`
    );
    
    let rollupFields = metadata.Attributes || [];
    
    // Filter by specific field names if provided
    if (fieldNames && fieldNames.length > 0) {
      rollupFields = rollupFields.filter((attr: any) =>
        fieldNames.includes(attr.LogicalName)
      );
    }
    
    return rollupFields;
  } catch (error: any) {
    console.error(`Error getting rollup metadata: ${error.message}`);
    return [];
  }
}

/**
 * Get sample records for testing
 */
async function getSampleRecords(
  tableName: string,
  rollupFields: any[],
  sampleSize: number
): Promise<any[]> {
  // Build select clause with rollup field names and primary key
  const fieldNames = rollupFields.map((f: any) => f.LogicalName).join(",");
  const primaryKeyField = getPrimaryKeyField(tableName);
  const nameField = getNameField(tableName);
  
  const select = `${primaryKeyField},${nameField},${fieldNames}`;
  
  // Only get active records (statecode eq 0)
  const filter = "statecode eq 0";
  
  try {
    return await queryDataverse(tableName, select, filter, sampleSize);
  } catch (error: any) {
    console.error(`Error querying sample records: ${error.message}`);
    return [];
  }
}

/**
 * Validate a single rollup field on a single record
 */
async function validateSingleRollup(
  tableName: string,
  record: any,
  rollupField: any,
  compareManual: boolean
): Promise<FieldValidationResult> {
  const fieldName = rollupField.LogicalName;
  const displayName = rollupField.DisplayName?.UserLocalizedLabel?.Label || fieldName;
  const actualValue = record[fieldName];
  const recordId = record[getPrimaryKeyField(tableName)];
  const recordName = record[getNameField(tableName)];
  
  // If manual calculation not requested, just report current value
  if (!compareManual) {
    return {
      fieldName,
      displayName,
      recordId,
      recordName,
      expected: null,
      actual: actualValue,
      variance: 0,
      percentageOff: 0,
      status: "PASS",
      details: "Manual calculation skipped",
    };
  }
  
  try {
    // Calculate expected value based on rollup definition
    const expectedValue = await calculateExpectedRollup(tableName, recordId, rollupField);
    
    // Handle null/undefined values
    const actual = actualValue ?? 0;
    const expected = expectedValue ?? 0;
    
    // Calculate variance
    const variance = Math.abs(actual - expected);
    const percentageOff = expected !== 0 ? (variance / Math.abs(expected)) * 100 : 0;
    
    // Determine status (tolerance: 0.01 for rounding)
    let status: "PASS" | "FAIL" | "WARNING" = "PASS";
    if (variance > 0.01) {
      status = variance > 0.1 ? "FAIL" : "WARNING";
    }
    
    return {
      fieldName,
      displayName,
      recordId,
      recordName,
      expected,
      actual,
      variance,
      percentageOff,
      status,
      details: status === "PASS" ? undefined : `Variance: ${variance.toFixed(2)}`,
    };
    
  } catch (error: any) {
    return {
      fieldName,
      displayName,
      recordId,
      recordName,
      expected: null,
      actual: actualValue,
      variance: 0,
      percentageOff: 0,
      status: "WARNING",
      details: `Calculation error: ${error.message}`,
    };
  }
}

/**
 * Calculate expected rollup value manually
 * This is table-specific logic based on known rollup definitions
 */
async function calculateExpectedRollup(
  tableName: string,
  recordId: string,
  rollupField: any
): Promise<number | null> {
  const fieldName = rollupField.LogicalName;
  
  // Table-specific rollup calculations
  // Based on MANUAL_ROLLUP_FIELD_CREATION_GUIDE.md
  
  if (tableName === "cr950_projectscopes") {
    return await calculateProjectScopeRollup(recordId, fieldName);
  } else if (tableName === "cr950_projectses") {
    return await calculateProjectRollup(recordId, fieldName);
  } else if (tableName === "cr950_apparatus") {
    return await calculateApparatusRollup(recordId, fieldName);
  }
  
  // Unknown table/field combination
  return null;
}

/**
 * Calculate ProjectScope rollup fields
 */
async function calculateProjectScopeRollup(
  scopeId: string,
  fieldName: string
): Promise<number | null> {
  // Get all tasks for this scope
  const tasks = await queryDataverse(
    "cr950_taskses",
    "cr950_tasksid,cr950_estimatedhours,cr950_actualhours",
    `_cr950_scope_value eq ${scopeId} and statecode eq 0`
  );
  
  switch (fieldName) {
    case "cr950_total_estimated_hours":
      return _.sumBy(tasks, (t: any) => t.cr950_estimatedhours || 0);
    
    case "cr950_total_actual_hours":
      return _.sumBy(tasks, (t: any) => t.cr950_actualhours || 0);
    
    case "cr950_total_apparatus_count":
      // Count apparatus across all tasks
      const apparatusCounts = await Promise.all(
        tasks.map(async (task: any) => {
          const apparatus = await queryDataverse(
            "cr950_apparatuses",
            "cr950_apparatusid",
            `_cr950_task_value eq ${task.cr950_tasksid} and statecode eq 0`
          );
          return apparatus.length;
        })
      );
      return _.sum(apparatusCounts);
    
    default:
      return null;
  }
}

/**
 * Calculate Project rollup fields
 */
async function calculateProjectRollup(
  projectId: string,
  fieldName: string
): Promise<number | null> {
  // Get all scopes for this project
  const scopes = await queryDataverse(
    "cr950_projectscopes",
    "cr950_projectscopeid,cr950_total_estimated_hours,cr950_total_actual_hours",
    `_cr950_project_value eq ${projectId} and statecode eq 0`
  );
  
  switch (fieldName) {
    case "cr950_project_total_estimated_hours":
      return _.sumBy(scopes, (s: any) => s.cr950_total_estimated_hours || 0);
    
    case "cr950_project_total_actual_hours":
      return _.sumBy(scopes, (s: any) => s.cr950_total_actual_hours || 0);
    
    default:
      return null;
  }
}

/**
 * Calculate Apparatus rollup fields (if any exist)
 */
async function calculateApparatusRollup(
  apparatusId: string,
  fieldName: string
): Promise<number | null> {
  // Apparatus currently has no rollup fields in v1.4.0.0
  // This is placeholder for future rollups
  return null;
}

/**
 * Helper: Get primary key field name for a table
 */
function getPrimaryKeyField(tableName: string): string {
  // Dataverse convention: {tablename}id
  return `${tableName}id`;
}

/**
 * Helper: Get name field for a table
 */
function getNameField(tableName: string): string {
  // Most tables use cr950_name, but some vary
  const nameFields: Record<string, string> = {
    "cr950_projectses": "cr950_name",
    "cr950_projectscopes": "cr950_name",
    "cr950_taskses": "cr950_name",
    "cr950_apparatuses": "cr950_name",
  };
  
  return nameFields[tableName] || "cr950_name";
}
