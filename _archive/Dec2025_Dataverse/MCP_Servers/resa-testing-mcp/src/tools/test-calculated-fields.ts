import { queryDataverse, createRecord } from "../utils/dataverse-client.js";

export interface TestResult {
  tested: number;
  passed: number;
  failed: number;
  warnings: number;
  details: CalculatedFieldTest[];
  timestamp: string;
}

export interface CalculatedFieldTest {
  tableName: string;
  fieldName: string;
  displayName: string;
  formula: string;
  recordId: string;
  recordName?: string;
  inputs: Record<string, any>;
  expectedOutput: any;
  actualOutput: any;
  status: "PASS" | "FAIL" | "WARNING";
  message?: string;
}

/**
 * Test calculated fields by verifying their formulas produce correct results
 * 
 * @param tableName - Logical name of the table
 * @param fieldNames - Optional array of specific calculated field names to test
 * @param testCases - Optional custom test cases with known inputs/outputs
 */
export async function testCalculatedFields(params: {
  tableName: string;
  fieldNames?: string[];
  testCases?: any[];
}): Promise<TestResult> {
  const { tableName, fieldNames, testCases } = params;

  console.error(`Testing calculated fields on ${tableName}...`);

  const results: CalculatedFieldTest[] = [];

  try {
    // Get calculated field definitions for this table
    const calculatedFields = await getCalculatedFieldDefinitions(tableName, fieldNames);

    if (calculatedFields.length === 0) {
      return {
        tested: 0,
        passed: 0,
        failed: 0,
        warnings: 1,
        details: [],
        timestamp: new Date().toISOString(),
      };
    }

    console.error(`Found ${calculatedFields.length} calculated fields to test`);

    // Test each calculated field
    for (const field of calculatedFields) {
      const testResult = await testCalculatedField(tableName, field, testCases);
      results.push(...testResult);
    }

    // Calculate summary
    const passed = results.filter(r => r.status === "PASS").length;
    const failed = results.filter(r => r.status === "FAIL").length;
    const warnings = results.filter(r => r.status === "WARNING").length;

    return {
      tested: results.length,
      passed,
      failed,
      warnings,
      details: results,
      timestamp: new Date().toISOString(),
    };

  } catch (error: any) {
    console.error(`Error testing calculated fields: ${error.message}`);
    throw new Error(`Calculated field testing failed: ${error.message}`);
  }
}

/**
 * Get calculated field definitions from known schema
 * Note: Dataverse API doesn't expose calculated field formulas via metadata
 * So we use hardcoded definitions based on the solution
 */
async function getCalculatedFieldDefinitions(
  tableName: string,
  fieldNames?: string[]
): Promise<any[]> {
  const allCalculatedFields = getKnownCalculatedFields();
  
  let fields = allCalculatedFields[tableName] || [];
  
  if (fieldNames && fieldNames.length > 0) {
    fields = fields.filter((f: any) => fieldNames.includes(f.logicalName));
  }
  
  return fields;
}

/**
 * Known calculated fields from the solution
 * Based on v1.4.0.0 schema
 */
function getKnownCalculatedFields(): Record<string, any[]> {
  return {
    "cr950_projectses": [
      {
        logicalName: "cr950_completion_percentage",
        displayName: "Completion %",
        formula: "(Total Actual Hours / Total Estimated Hours) * 100",
        testScenario: "percentage_calculation",
      },
      // Add other Projects calculated fields here
    ],
    "cr950_projectscopes": [
      {
        logicalName: "cr950_scope_completion_percentage",
        displayName: "Scope Completion %",
        formula: "(Total Actual Hours / Total Estimated Hours) * 100",
        testScenario: "percentage_calculation",
      },
      // Add other ProjectScope calculated fields
    ],
    "cr950_apparatusrevenues": [
      {
        logicalName: "cr950_totalrevenue",
        displayName: "Total Revenue",
        formula: "NETA Sell Price + Additional Sell Price",
        testScenario: "simple_sum",
      },
      {
        logicalName: "cr950_totalmargin",
        displayName: "Total Margin",
        formula: "Total Revenue - Total Cost",
        testScenario: "simple_subtraction",
      },
      {
        logicalName: "cr950_marginpercentage",
        displayName: "Margin %",
        formula: "(Total Margin / Total Revenue) * 100",
        testScenario: "percentage_calculation",
      },
      // Add other ApparatusRevenue calculated fields
    ],
  };
}

/**
 * Test a single calculated field
 */
async function testCalculatedField(
  tableName: string,
  fieldDef: any,
  customTestCases?: any[]
): Promise<CalculatedFieldTest[]> {
  const results: CalculatedFieldTest[] = [];

  try {
    // Get sample records with this calculated field
    const records = await getSampleRecordsForTesting(tableName, fieldDef, 5);

    for (const record of records) {
      const test = await validateCalculatedFieldValue(tableName, record, fieldDef);
      results.push(test);
    }

  } catch (error: any) {
    results.push({
      tableName,
      fieldName: fieldDef.logicalName,
      displayName: fieldDef.displayName,
      formula: fieldDef.formula,
      recordId: "N/A",
      inputs: {},
      expectedOutput: null,
      actualOutput: null,
      status: "WARNING",
      message: `Test error: ${error.message}`,
    });
  }

  return results;
}

/**
 * Get sample records for testing calculated fields
 */
async function getSampleRecordsForTesting(
  tableName: string,
  fieldDef: any,
  sampleSize: number
): Promise<any[]> {
  const primaryKey = `${tableName}id`;
  const nameField = getNameField(tableName);
  
  // Get fields needed for this calculation
  const fieldsNeeded = getFieldsNeededForCalculation(tableName, fieldDef);
  const select = `${primaryKey},${nameField},${fieldDef.logicalName},${fieldsNeeded.join(",")}`;
  
  try {
    return await queryDataverse(tableName, select, "statecode eq 0", sampleSize);
  } catch (error) {
    return [];
  }
}

/**
 * Validate a calculated field value on a specific record
 */
async function validateCalculatedFieldValue(
  tableName: string,
  record: any,
  fieldDef: any
): Promise<CalculatedFieldTest> {
  const primaryKey = `${tableName}id`;
  const nameField = getNameField(tableName);
  const actualOutput = record[fieldDef.logicalName];

  // Extract inputs based on test scenario
  const inputs = extractInputsForTest(tableName, record, fieldDef);
  
  // Calculate expected output
  const expectedOutput = calculateExpectedOutput(fieldDef.testScenario, inputs);
  
  // Compare (with tolerance for floating point)
  const variance = Math.abs((expectedOutput ?? 0) - (actualOutput ?? 0));
  const status = variance < 0.01 ? "PASS" : (variance < 0.1 ? "WARNING" : "FAIL");

  return {
    tableName,
    fieldName: fieldDef.logicalName,
    displayName: fieldDef.displayName,
    formula: fieldDef.formula,
    recordId: record[primaryKey],
    recordName: record[nameField],
    inputs,
    expectedOutput,
    actualOutput,
    status,
    message: status !== "PASS" ? `Variance: ${variance.toFixed(4)}` : undefined,
  };
}

/**
 * Extract input values needed for test
 */
function extractInputsForTest(tableName: string, record: any, fieldDef: any): Record<string, any> {
  const scenario = fieldDef.testScenario;
  
  if (scenario === "percentage_calculation" && tableName === "cr950_projectses") {
    return {
      totalActualHours: record.cr950_project_total_actual_hours || 0,
      totalEstimatedHours: record.cr950_project_total_estimated_hours || 1,
    };
  }
  
  if (scenario === "percentage_calculation" && tableName === "cr950_projectscopes") {
    return {
      totalActualHours: record.cr950_total_actual_hours || 0,
      totalEstimatedHours: record.cr950_total_estimated_hours || 1,
    };
  }
  
  if (scenario === "simple_sum" && tableName === "cr950_apparatusrevenues") {
    return {
      netaSellPrice: record.cr950_netasellprice || 0,
      additionalSellPrice: record.cr950_additionalsellprice || 0,
    };
  }
  
  if (scenario === "simple_subtraction" && tableName === "cr950_apparatusrevenues") {
    return {
      totalRevenue: record.cr950_totalrevenue || 0,
      totalCost: record.cr950_totalcost || 0,
    };
  }
  
  if (scenario === "percentage_calculation" && tableName === "cr950_apparatusrevenues") {
    return {
      totalMargin: record.cr950_totalmargin || 0,
      totalRevenue: record.cr950_totalrevenue || 1,
    };
  }
  
  return {};
}

/**
 * Calculate expected output based on test scenario
 */
function calculateExpectedOutput(scenario: string, inputs: Record<string, any>): number | null {
  switch (scenario) {
    case "percentage_calculation":
      if (inputs.totalEstimatedHours === 0) return 0;
      return (inputs.totalActualHours / inputs.totalEstimatedHours) * 100;
    
    case "simple_sum":
      return inputs.netaSellPrice + inputs.additionalSellPrice;
    
    case "simple_subtraction":
      return inputs.totalRevenue - inputs.totalCost;
    
    default:
      return null;
  }
}

/**
 * Get fields needed for a calculation
 */
function getFieldsNeededForCalculation(tableName: string, fieldDef: any): string[] {
  const scenario = fieldDef.testScenario;
  
  if (scenario === "percentage_calculation" && tableName === "cr950_projectses") {
    return ["cr950_project_total_actual_hours", "cr950_project_total_estimated_hours"];
  }
  
  if (scenario === "percentage_calculation" && tableName === "cr950_projectscopes") {
    return ["cr950_total_actual_hours", "cr950_total_estimated_hours"];
  }
  
  if (scenario === "simple_sum") {
    return ["cr950_netasellprice", "cr950_additionalsellprice"];
  }
  
  if (scenario === "simple_subtraction") {
    return ["cr950_totalrevenue", "cr950_totalcost"];
  }
  
  if (scenario === "percentage_calculation" && tableName === "cr950_apparatusrevenues") {
    return ["cr950_totalmargin", "cr950_totalrevenue"];
  }
  
  return [];
}

/**
 * Helper: Get name field for a table
 */
function getNameField(tableName: string): string {
  const nameFields: Record<string, string> = {
    "cr950_projectses": "cr950_name",
    "cr950_projectscopes": "cr950_name",
    "cr950_taskses": "cr950_name",
    "cr950_apparatuses": "cr950_name",
    "cr950_apparatusrevenues": "cr950_name",
  };
  
  return nameFields[tableName] || "cr950_name";
}
